"""
Phase 9 tests — RAG pipeline.

Tests the full stack: document processing → chunking → embedding → retrieval → RAG query.
Uses the real sentence-transformers model (cached locally after first download).
"""

import io
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.services.document_service import extract_text, chunk_text
from app.services.embedding_service import embed_single, cosine_similarity
from app.services.vector_store import LocalVectorStore, VectorChunk

# ── Unit tests: text extraction ───────────────────────────────────────────

class TestTextExtraction:
    def test_extract_txt(self):
        text = b"Hello world. This is a test document."
        pages = extract_text(text, "test.txt")
        assert len(pages) == 1
        assert "Hello world" in pages[0][0]
        assert pages[0][1] == 0  # page 0 for txt

    def test_extract_md(self):
        text = b"# Header\n\nSome content here."
        pages = extract_text(text, "test.md")
        assert len(pages) == 1
        assert "Header" in pages[0][0]

    def test_unsupported_type_raises(self):
        with pytest.raises(ValueError, match="Unsupported"):
            extract_text(b"data", "test.xlsx")


# ── Unit tests: chunking ──────────────────────────────────────────────────

class TestChunking:
    def test_short_text_single_chunk(self):
        text = "This is a short sentence. Another short one."
        chunks = chunk_text(text)
        assert len(chunks) == 1
        assert chunks[0]["content"] == text.strip() or text.strip() in chunks[0]["content"]

    def test_long_text_multiple_chunks(self):
        # 10,000 characters → should produce multiple chunks
        text = ("This is a sentence that is repeated many times to create a long text. " * 150)
        chunks = chunk_text(text)
        assert len(chunks) >= 3

    def test_chunk_size_respected(self):
        text = "Short sentence. " * 200
        chunks = chunk_text(text)
        for chunk in chunks:
            assert len(chunk["content"]) <= 2500  # allow slight overflow at sentence boundaries

    def test_chunks_have_required_fields(self):
        chunks = chunk_text("Hello world. How are you today?")
        for chunk in chunks:
            assert "content" in chunk
            assert "page" in chunk


# ── Unit tests: embeddings ────────────────────────────────────────────────

class TestEmbeddings:
    def test_embedding_has_correct_dimension(self):
        vec = embed_single("Hello world")
        assert len(vec) == 384

    def test_similar_texts_have_high_similarity(self):
        v1 = embed_single("The cat sat on the mat.")
        v2 = embed_single("A cat was sitting on a mat.")
        score = cosine_similarity(v1, v2)
        assert score > 0.7

    def test_dissimilar_texts_have_low_similarity(self):
        v1 = embed_single("Python is a programming language.")
        v2 = embed_single("The stock market fell 3% today.")
        score = cosine_similarity(v1, v2)
        assert score < 0.5

    def test_identical_texts_score_near_1(self):
        v1 = embed_single("Exact same text")
        v2 = embed_single("Exact same text")
        score = cosine_similarity(v1, v2)
        assert score > 0.99


# ── Unit tests: vector store ──────────────────────────────────────────────

class TestVectorStore:
    def test_upsert_and_search(self, tmp_path):
        store = LocalVectorStore(persist_dir=str(tmp_path))
        v1 = embed_single("Python programming language features")
        v2 = embed_single("Machine learning with scikit-learn")

        store.upsert([
            VectorChunk(id="c1", document_id="d1", chunk_index=0,
                        content="Python programming language features", embedding=v1,
                        metadata={"filename": "python.txt", "page": 0}),
            VectorChunk(id="c2", document_id="d1", chunk_index=1,
                        content="Machine learning with scikit-learn", embedding=v2,
                        metadata={"filename": "ml.txt", "page": 0}),
        ])

        query = embed_single("What are features of Python?")
        results = store.search(query, k=2)

        assert len(results) == 2
        # The most relevant result should be about Python
        assert "Python" in results[0].chunk.content

    def test_delete_document(self, tmp_path):
        store = LocalVectorStore(persist_dir=str(tmp_path))
        v = embed_single("test content")
        store.upsert([
            VectorChunk(id="c1", document_id="doc_to_delete", chunk_index=0,
                        content="test", embedding=v, metadata={}),
        ])
        assert store.count_for_document("doc_to_delete") == 1

        store.delete_document("doc_to_delete")
        assert store.count_for_document("doc_to_delete") == 0

    def test_persistence(self, tmp_path):
        store1 = LocalVectorStore(persist_dir=str(tmp_path))
        v = embed_single("persistent content")
        store1.upsert([
            VectorChunk(id="c1", document_id="d1", chunk_index=0,
                        content="persistent content", embedding=v, metadata={}),
        ])
        assert store1.count() == 1

        # Load fresh instance from same path
        store2 = LocalVectorStore(persist_dir=str(tmp_path))
        assert store2.count() == 1


# ── API integration tests ─────────────────────────────────────────────────

@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_rag_status(client):
    resp = await client.get("/api/rag/status")
    assert resp.status_code == 200
    body = resp.json()
    assert "total_chunks" in body
    assert "store_type" in body


@pytest.mark.asyncio
async def test_rag_query_no_documents(client):
    """RAG query with empty store returns a helpful message, not 500."""
    resp = await client.post("/api/rag/query", json={
        "question": "What is the refund policy?",
        "provider": "mock",
        "top_k": 3,
    })
    assert resp.status_code == 200
    # Either an actual answer (if demo doc was loaded) or an empty-store message
    body = resp.json()
    assert "answer" in body
    assert "sources" in body


@pytest.mark.asyncio
async def test_document_upload_txt(client):
    """Upload a TXT file and verify it's processed."""
    content = b"""WidgetCo Policy: Digital goods are non-refundable once downloaded.
The company was founded in 2021. CEO is Sarah Park.
API rate limit for free tier is 100 requests per minute."""

    resp = await client.post(
        "/api/documents/upload",
        files={"file": ("policy.txt", io.BytesIO(content), "text/plain")},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "ready"
    assert body["chunk_count"] >= 1
    assert body["document_id"]

    return body["document_id"]


@pytest.mark.asyncio
async def test_document_list(client):
    resp = await client.get("/api/documents")
    assert resp.status_code == 200
    body = resp.json()
    assert "documents" in body
    assert "total" in body


@pytest.mark.asyncio
async def test_rag_full_pipeline(client):
    """Upload a document then query it."""
    content = b"The capital of France is Paris. The Eiffel Tower is 330 meters tall. France joined the EU in 1957."
    upload = await client.post(
        "/api/documents/upload",
        files={"file": ("france.txt", io.BytesIO(content), "text/plain")},
    )
    assert upload.status_code == 201
    doc_id = upload.json()["document_id"]

    # Query with document filter
    resp = await client.post("/api/rag/query", json={
        "question": "What is the capital of France?",
        "provider": "mock",
        "top_k": 3,
        "document_id": doc_id,
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["chunks_retrieved"] >= 1
    assert len(body["sources"]) >= 1
    assert body["sources"][0]["filename"] == "france.txt"


@pytest.mark.asyncio
async def test_document_delete(client):
    content = b"Temporary document to be deleted."
    upload = await client.post(
        "/api/documents/upload",
        files={"file": ("temp.txt", io.BytesIO(content), "text/plain")},
    )
    doc_id = upload.json()["document_id"]

    del_resp = await client.delete(f"/api/documents/{doc_id}")
    assert del_resp.status_code == 204

    get_resp = await client.get(f"/api/documents/{doc_id}")
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_upload_invalid_type_rejected(client):
    resp = await client.post(
        "/api/documents/upload",
        files={"file": ("malware.exe", io.BytesIO(b"MZ\x90\x00"), "application/octet-stream")},
    )
    assert resp.status_code == 415
