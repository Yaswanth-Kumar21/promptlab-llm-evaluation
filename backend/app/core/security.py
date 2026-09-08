"""
Security utilities.

Phase 1 scope:
  - Input sanitisation helpers
  - File-type validation
  - Safe error response construction (never leaking stack traces)

Authentication (JWT / API keys) is scaffolded here but intentionally left
minimal for Phase 1 — it will be expanded in later phases.
"""

import os
import re
from pathlib import Path
from typing import Optional

from fastapi import HTTPException, status

# ── Allowed file types for document upload ────────────────────────────────────
ALLOWED_EXTENSIONS: set[str] = {".pdf", ".txt", ".md"}
ALLOWED_MIME_TYPES: set[str] = {
    "application/pdf",
    "text/plain",
    "text/markdown",
}


def validate_upload_file(
    filename: str,
    content_type: Optional[str],
    file_size: int,
    max_bytes: int,
) -> None:
    """
    Raise HTTPException if the uploaded file fails validation.

    Checks:
      1. File extension is in the allowed list.
      2. Content-type is in the allowed list (when provided).
      3. File size does not exceed the configured limit.
    """
    suffix = Path(filename).suffix.lower()

    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=(
                f"File type '{suffix}' is not supported. "
                f"Allowed types: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
            ),
        )

    if content_type and content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"MIME type '{content_type}' is not supported.",
        )

    if file_size > max_bytes:
        max_mb = max_bytes / (1024 * 1024)
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds the maximum allowed size of {max_mb:.0f} MB.",
        )


def sanitise_prompt_input(text: str, max_length: int = 32_000) -> str:
    """
    Basic input sanitisation for prompt text.

    - Strips leading/trailing whitespace.
    - Enforces a maximum character length to prevent oversized payloads.
    - Does NOT strip legitimate special characters (needed for prompts).

    NOTE: This is not an injection defence — see safety_service.py for that.
    """
    text = text.strip()
    if not text:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Prompt text cannot be empty.",
        )
    if len(text) > max_length:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Prompt text exceeds the maximum length of {max_length} characters.",
        )
    return text


def safe_filename(filename: str) -> str:
    """
    Return a filesystem-safe version of an uploaded filename.
    Removes path traversal characters and limits length.
    """
    # Keep only alphanumeric, dash, underscore, dot
    name = re.sub(r"[^\w\-.]", "_", Path(filename).name)
    # Prevent hidden files
    name = name.lstrip(".")
    # Limit length
    return name[:200] or "upload"
