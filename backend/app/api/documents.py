"""
Document management endpoints — Phase 9.

POST /api/documents/upload   Upload a document for RAG indexing
GET  /api/documents          List all documents
GET  /api/documents/{id}     Get document status + chunk count
DELETE /api/documents/{id}   Delete a document and its vectors
"""

import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.logging import get_logger
from app.core.security import validate_upload_file, safe_filename
from app.models.document import Document
from app.schemas.rag import DocumentOut, DocumentUploadResponse
from app.services.document_service import process_document
from app.services.vector_store import get_vector_store

router = APIRouter()
logger = get_logger(__name__)


@router.post(
    "/documents/upload",
    response_model=DocumentUploadResponse,
    summary="Upload a document for RAG",
    description="""
Upload a PDF, TXT, or Markdown file to build a searchable knowledge base.

**Pipeline:** upload → extract text → chunk → embed → store in vector DB

The document is processed synchronously (suitable for demos and small files).
For large files (>5MB), expect 5-30 seconds processing time.

**Security:** Uploaded content is treated as untrusted data. It is never
executed. Only text is extracted.
""",
    tags=["Documents"],
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
) -> DocumentUploadResponse:
    # Read file content
    file_bytes = await file.read()
    file_size = len(file_bytes)

    # Validate
    validate_upload_file(
        filename=file.filename or "upload",
        content_type=file.content_type,
        file_size=file_size,
        max_bytes=settings.max_upload_size_bytes,
    )

    safe_name = safe_filename(file.filename or "upload")
    file_type = Path(safe_name).suffix.lower().lstrip(".")

    # Create DB record
    document_id = str(uuid.uuid4())
    doc = Document(
        id=document_id,
        filename=safe_name,
        original_filename=file.filename or "upload",
        file_type=file_type,
        file_size=file_size,
        status="pending",
    )
    db.add(doc)
    await db.flush()

    logger.info("document_upload_start", document_id=document_id, filename=safe_name, size=file_size)

    # Process: extract → chunk → embed → store
    try:
        chunk_count = await process_document(
            document_id=document_id,
            filename=safe_name,
            file_bytes=file_bytes,
            db=db,
        )
        message = f"Successfully processed {chunk_count} chunks."
    except Exception as e:
        chunk_count = 0
        message = f"Processing failed: {type(e).__name__}: {str(e)[:200]}"
        logger.error("document_upload_failed", document_id=document_id, error=str(e))

    # Refresh status from DB
    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one()

    return DocumentUploadResponse(
        document_id=document_id,
        filename=safe_name,
        status=doc.status,
        chunk_count=doc.chunk_count,
        message=message,
    )


@router.get(
    "/documents",
    summary="List all documents",
    tags=["Documents"],
)
async def list_documents(db: AsyncSession = Depends(get_db)) -> dict:
    result = await db.execute(
        select(Document).order_by(Document.created_at.desc())
    )
    docs = result.scalars().all()
    store = get_vector_store()

    return {
        "documents": [
            {
                "id": d.id,
                "filename": d.filename,
                "original_filename": d.original_filename,
                "file_type": d.file_type,
                "file_size": d.file_size,
                "status": d.status,
                "chunk_count": d.chunk_count,
                "error_message": d.error_message or None,
                "created_at": d.created_at.isoformat() if d.created_at else None,
            }
            for d in docs
        ],
        "total": len(docs),
        "total_chunks_in_store": store.count(),
    }


@router.get(
    "/documents/{document_id}",
    summary="Get document status",
    tags=["Documents"],
)
async def get_document(document_id: str, db: AsyncSession = Depends(get_db)) -> dict:
    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document '{document_id}' not found.")

    store = get_vector_store()
    return {
        "id": doc.id,
        "filename": doc.filename,
        "original_filename": doc.original_filename,
        "file_type": doc.file_type,
        "file_size": doc.file_size,
        "status": doc.status,
        "chunk_count": doc.chunk_count,
        "chunks_in_store": store.count_for_document(document_id),
        "error_message": doc.error_message or None,
        "created_at": doc.created_at.isoformat() if doc.created_at else None,
    }


@router.delete(
    "/documents/{document_id}",
    summary="Delete a document and its vectors",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Documents"],
)
async def delete_document(document_id: str, db: AsyncSession = Depends(get_db)) -> None:
    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document '{document_id}' not found.")

    # Remove from vector store
    get_vector_store().delete_document(document_id)

    # Remove from DB (cascades to chunks)
    await db.delete(doc)
    logger.info("document_deleted", document_id=document_id)
