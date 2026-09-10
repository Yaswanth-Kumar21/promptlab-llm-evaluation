"""
DocumentService — extracts text, chunks it, and stores chunks in the vector store.

Supported file types: PDF, TXT, MD

Chunking strategy:
  - Target: ~500 tokens (~2000 characters)
  - Overlap: ~50 tokens (~200 characters) to prevent answers splitting at boundaries
  - Split preference: sentence boundaries when possible
"""

import re
import uuid
from pathlib import Path
from typing import List, Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.logging import get_logger
from app.models.document import Document, DocumentChunk
from app.services.embedding_service import embed_texts
from app.services.vector_store import VectorChunk, get_vector_store

logger = get_logger(__name__)

CHUNK_SIZE = 2000       # characters (~500 tokens)
CHUNK_OVERLAP = 200     # characters (~50 tokens)


# ── Text extraction ───────────────────────────────────────────────────────

def extract_text(file_bytes: bytes, filename: str) -> List[Tuple[str, int]]:
    """
    Extract text from a file. Returns list of (text, page_number) tuples.
    Page number is 1-indexed for PDFs; 0 for TXT/MD (no page concept).

    SECURITY: file_bytes comes from an uploaded file — treat as untrusted.
    We extract text only; we do not execute any embedded scripts.
    """
    suffix = Path(filename).suffix.lower()

    if suffix == ".pdf":
        return _extract_pdf(file_bytes)
    elif suffix in (".txt", ".md"):
        text = file_bytes.decode("utf-8", errors="replace")
        return [(text, 0)]
    else:
        raise ValueError(f"Unsupported file type: {suffix}")


def _extract_pdf(file_bytes: bytes) -> List[Tuple[str, int]]:
    """Extract text page-by-page from a PDF."""
    try:
        import io
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(file_bytes))
        pages = []
        for i, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            if text.strip():
                pages.append((text, i + 1))
        return pages
    except Exception as e:
        logger.warning("pdf_extraction_failed", error=str(e))
        # Return empty rather than crash
        return []


# ── Chunking ──────────────────────────────────────────────────────────────

def chunk_text(text: str, page: int = 0) -> List[dict]:
    """
    Split text into overlapping chunks.
    Returns list of dicts: {content, page, char_start, char_end}
    """
    # Prefer sentence boundaries
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())

    chunks = []
    current = ""
    char_pos = 0

    for sentence in sentences:
        if not sentence.strip():
            continue

        # If adding this sentence keeps us under limit, add it
        if len(current) + len(sentence) + 1 <= CHUNK_SIZE:
            current = (current + " " + sentence).strip()
        else:
            # Save current chunk if non-empty
            if current:
                chunks.append({
                    "content": current,
                    "page": page,
                    "char_start": char_pos,
                    "char_end": char_pos + len(current),
                })
                # Overlap: keep the last CHUNK_OVERLAP characters
                overlap_start = max(0, len(current) - CHUNK_OVERLAP)
                char_pos += len(current) - CHUNK_OVERLAP
                current = current[overlap_start:].strip() + " " + sentence
            else:
                # Single sentence larger than chunk size — split by characters
                for j in range(0, len(sentence), CHUNK_SIZE - CHUNK_OVERLAP):
                    chunk_content = sentence[j: j + CHUNK_SIZE]
                    if chunk_content.strip():
                        chunks.append({
                            "content": chunk_content,
                            "page": page,
                            "char_start": char_pos,
                            "char_end": char_pos + len(chunk_content),
                        })
                        char_pos += CHUNK_SIZE - CHUNK_OVERLAP
                current = ""

    if current.strip():
        chunks.append({
            "content": current,
            "page": page,
            "char_start": char_pos,
            "char_end": char_pos + len(current),
        })

    return chunks


# ── Full pipeline ─────────────────────────────────────────────────────────

async def process_document(
    document_id: str,
    filename: str,
    file_bytes: bytes,
    db: AsyncSession,
) -> int:
    """
    Full pipeline: extract → chunk → embed → store in vector DB + SQLite.
    Returns number of chunks created.

    Updates the Document record status throughout.
    """
    # Mark as processing
    doc_result = await db.execute(select(Document).where(Document.id == document_id))
    doc = doc_result.scalar_one_or_none()
    if not doc:
        raise ValueError(f"Document {document_id} not found")

    doc.status = "processing"
    await db.flush()

    try:
        # 1. Extract
        pages = extract_text(file_bytes, filename)
        if not pages:
            doc.status = "failed"
            doc.error_message = "No text could be extracted from this file."
            await db.flush()
            return 0

        # 2. Chunk all pages
        all_chunks = []
        for page_text, page_num in pages:
            page_chunks = chunk_text(page_text, page=page_num)
            all_chunks.extend(page_chunks)

        if not all_chunks:
            doc.status = "failed"
            doc.error_message = "File contained no usable text after chunking."
            await db.flush()
            return 0

        # 3. Embed all chunks in one batch
        texts = [c["content"] for c in all_chunks]
        logger.info("embedding_chunks", document_id=document_id, count=len(texts))
        embeddings = embed_texts(texts)

        # 4. Save to SQLite + vector store
        vector_chunks = []
        for i, (chunk_data, embedding) in enumerate(zip(all_chunks, embeddings)):
            chunk_id = str(uuid.uuid4())

            # SQLite record
            db_chunk = DocumentChunk(
                id=chunk_id,
                document_id=document_id,
                chunk_index=i,
                content=chunk_data["content"],
                page_number=chunk_data["page"] or None,
                chroma_id=chunk_id,
                token_count=len(chunk_data["content"]) // 4,
            )
            db.add(db_chunk)

            # Vector store record
            vector_chunks.append(VectorChunk(
                id=chunk_id,
                document_id=document_id,
                chunk_index=i,
                content=chunk_data["content"],
                embedding=embedding,
                metadata={
                    "filename": filename,
                    "page": chunk_data["page"],
                    "chunk_index": i,
                },
            ))

        get_vector_store().upsert(vector_chunks)

        # 5. Update document record
        doc.status = "ready"
        doc.chunk_count = len(all_chunks)
        await db.flush()

        logger.info(
            "document_processed",
            document_id=document_id,
            filename=filename,
            chunks=len(all_chunks),
        )
        return len(all_chunks)

    except Exception as e:
        doc.status = "failed"
        doc.error_message = str(e)[:500]
        await db.flush()
        logger.error("document_processing_failed", document_id=document_id, error=str(e))
        raise
