"""
LocalVectorStore — JSON-file backed vector store.

Stores embeddings as a JSON file so they persist across restarts
without requiring ChromaDB (which needs a C++ compiler on Windows).

The interface matches what ChromaDB/pgvector would expose, so swapping
is a single-file change.

Structure of the store file (chroma_data/vectors.json):
{
  "chunks": [
    {
      "id": "uuid",
      "document_id": "uuid",
      "chunk_index": 0,
      "content": "text...",
      "embedding": [0.1, 0.2, ...],
      "metadata": { "filename": "doc.pdf", "page": 1 }
    }
  ]
}

Performance note: This is suitable for development and demos.
For production with 10,000+ chunks, use pgvector or ChromaDB.
"""

import json
import os
import uuid
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass, field, asdict

import numpy as np

from app.core.config import settings
from app.core.logging import get_logger
from app.services.embedding_service import cosine_similarity

logger = get_logger(__name__)


@dataclass
class VectorChunk:
    id: str
    document_id: str
    chunk_index: int
    content: str
    embedding: List[float]
    metadata: dict = field(default_factory=dict)


@dataclass
class SearchResult:
    chunk: VectorChunk
    score: float   # cosine similarity, higher = more relevant


class LocalVectorStore:
    """
    Thread-safe (single-process) JSON vector store.
    """

    def __init__(self, persist_dir: Optional[str] = None):
        self._dir = Path(persist_dir or settings.chroma_persist_dir)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._path = self._dir / "vectors.json"
        self._chunks: List[VectorChunk] = []
        self._load()

    # ── Persistence ───────────────────────────────────────────────────────

    def _load(self):
        if self._path.exists():
            try:
                with open(self._path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._chunks = [VectorChunk(**c) for c in data.get("chunks", [])]
                logger.info("vector_store_loaded", count=len(self._chunks))
            except Exception as e:
                logger.warning("vector_store_load_failed", error=str(e))
                self._chunks = []
        else:
            self._chunks = []

    def _save(self):
        try:
            with open(self._path, "w", encoding="utf-8") as f:
                json.dump({"chunks": [asdict(c) for c in self._chunks]}, f)
        except Exception as e:
            logger.error("vector_store_save_failed", error=str(e))

    # ── Write operations ──────────────────────────────────────────────────

    def upsert(self, chunks: List[VectorChunk]):
        """Add or replace chunks. Existing chunks with same id are replaced."""
        existing_ids = {c.id for c in chunks}
        self._chunks = [c for c in self._chunks if c.id not in existing_ids]
        self._chunks.extend(chunks)
        self._save()
        logger.info("vector_store_upsert", count=len(chunks), total=len(self._chunks))

    def delete_document(self, document_id: str) -> int:
        """Remove all chunks for a document. Returns number deleted."""
        before = len(self._chunks)
        self._chunks = [c for c in self._chunks if c.document_id != document_id]
        deleted = before - len(self._chunks)
        self._save()
        logger.info("vector_store_delete", document_id=document_id, deleted=deleted)
        return deleted

    # ── Search ────────────────────────────────────────────────────────────

    def search(
        self,
        query_embedding: List[float],
        k: int = 5,
        document_id: Optional[str] = None,
    ) -> List[SearchResult]:
        """
        Return the top-k most similar chunks by cosine similarity.

        Args:
            query_embedding: embedded query vector
            k:               number of results to return
            document_id:     if set, restrict search to one document
        """
        candidates = self._chunks
        if document_id:
            candidates = [c for c in candidates if c.document_id == document_id]

        if not candidates:
            return []

        scored = [
            SearchResult(chunk=c, score=cosine_similarity(query_embedding, c.embedding))
            for c in candidates
        ]
        scored.sort(key=lambda x: x.score, reverse=True)
        return scored[:k]

    # ── Stats ─────────────────────────────────────────────────────────────

    def count(self) -> int:
        return len(self._chunks)

    def count_for_document(self, document_id: str) -> int:
        return sum(1 for c in self._chunks if c.document_id == document_id)

    def list_documents(self) -> List[str]:
        return list({c.document_id for c in self._chunks})


# ── Singleton ─────────────────────────────────────────────────────────────
_store: Optional[LocalVectorStore] = None


def get_vector_store() -> LocalVectorStore:
    """Return the module-level singleton vector store."""
    global _store
    if _store is None:
        _store = LocalVectorStore()
    return _store
