# RAG Documents

Place documents here to use with the RAG pipeline.

Supported formats: `.pdf`, `.txt`, `.md`

Maximum file size: 10 MB (configurable via `MAX_UPLOAD_SIZE_MB` in `.env`)

---

## How to use

1. Navigate to **RAG Lab** in the PromptLab UI
2. Click **Upload Document**
3. Select a PDF, TXT, or Markdown file
4. Wait for status to change from `processing` → `ready`
5. Use the **Query** tab to ask questions

---

## What happens to your document

1. Text is extracted (pypdf for PDF, plain read for TXT/MD)
2. Text is split into ~500-token chunks with 50-token overlap
3. Each chunk is embedded using `all-MiniLM-L6-v2` (local, no API key needed)
4. Chunks are stored in ChromaDB at `./chroma_data/`
5. Metadata (filename, page, chunk index) is stored in SQLite

---

## Security note

Uploaded documents may contain untrusted content.
PromptLab wraps all retrieved chunks in `<context>` delimiters to prevent
indirect prompt injection. See `docs/safety.md` for details.

---

## .gitignore

PDF, TXT, and MD files in this directory are excluded from version control
(see root `.gitignore`) to avoid committing private documents.
Only this README is tracked.
