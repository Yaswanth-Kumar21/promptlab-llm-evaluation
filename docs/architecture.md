# PromptLab — Architecture

## Overview

PromptLab is a full-stack web application with a clean separation between:
1. A React single-page application (frontend)
2. A FastAPI REST API (backend)
3. A provider-agnostic LLM abstraction layer
4. A pluggable vector store (ChromaDB → pgvector path)
5. A relational database (SQLite → PostgreSQL path)

---

## Layer Diagram

```
Browser
  │
  │  HTTP (Axios)
  ▼
React SPA (Vite, port 5173)
  │
  │  /api/* (proxied in dev, VITE_API_URL in prod)
  ▼
FastAPI Application (Uvicorn, port 8000)
  │
  ├─── app/api/         ← Route handlers (thin — validate input, call service)
  ├─── app/services/    ← Business logic
  │     ├─ prompt_service.py      ← Prompt CRUD, version management
  │     ├─ evaluation_service.py  ← Scoring engine
  │     ├─ safety_service.py      ← Injection / bias / hallucination checks
  │     ├─ rag_service.py         ← Retrieval pipeline
  │     ├─ embedding_service.py   ← Embedding abstraction
  │     ├─ document_service.py    ← File parsing and chunking
  │     └─ llm/
  │           ├─ base.py          ← BaseLLMProvider ABC
  │           ├─ mock_provider.py ← Local deterministic mock (no API key)
  │           ├─ openai_provider.py
  │           ├─ anthropic_provider.py
  │           ├─ gemini_provider.py
  │           └─ mistral_provider.py
  │
  ├─── app/models/      ← SQLAlchemy ORM models
  ├─── app/schemas/     ← Pydantic request/response models
  └─── app/core/        ← Config, DB engine, logging, security
        ├─ config.py    ← Settings (pydantic-settings, reads .env)
        ├─ database.py  ← Async SQLAlchemy engine + session factory
        ├─ logging.py   ← structlog configuration
        └─ security.py  ← Input validation, file checks
```

---

## Database Schema (Simplified)

```
prompts
  id, name, description, category, tags, created_at, updated_at

prompt_versions
  id, prompt_id (FK), version_number, system_prompt,
  user_prompt_template, provider, model, temperature,
  max_tokens, notes, author, is_best, created_at

experiments
  id, prompt_id (FK), prompt_version_id (FK),
  system_prompt, user_prompt, provider, model, temperature,
  response, input_tokens, output_tokens, latency_ms,
  dataset_name, test_case_id, passed, error, created_at

evaluation_results
  id, experiment_id (FK), metric, score, passed,
  reason, evidence, evaluation_method, created_at

documents
  id, filename, original_filename, file_type, file_size,
  status, error_message, chunk_count, created_at

document_chunks
  id, document_id, chunk_index, content, page_number,
  chroma_id, token_count, created_at
```

---

## LLM Provider Abstraction

All providers implement `BaseLLMProvider`:

```python
class BaseLLMProvider(ABC):
    @abstractmethod
    async def generate(self, request: LLMRequest) -> LLMResponse: ...

    @abstractmethod
    async def generate_structured(
        self, request: LLMRequest, schema: type[BaseModel]
    ) -> LLMResponse: ...

    @abstractmethod
    def count_tokens(self, text: str) -> int: ...

    @abstractmethod
    async def health_check(self) -> bool: ...
```

The `PromptService` receives a provider instance via dependency injection.
Swapping providers requires zero changes to business logic.

---

## Vector Store Abstraction

ChromaDB is used in Phase 1–9. The `EmbeddingService` wraps it behind an
interface so it can be replaced with pgvector or Pinecone later.

```python
class BaseVectorStore(ABC):
    async def upsert(self, chunks: list[ChunkWithEmbedding]) -> None: ...
    async def search(self, query_embedding: list[float], k: int) -> list[SearchResult]: ...
    async def delete(self, document_id: str) -> None: ...
```

---

## Request Lifecycle

```
HTTP request
  → CORS middleware (allow frontend origins)
  → request_middleware (attach request_id, start timer)
  → Route handler (FastAPI path operation)
  → Pydantic validation (automatic — returns 422 on bad input)
  → Service function call
  → LLM provider call (if needed)
  → Database write (experiment + evaluation results)
  → Pydantic response serialisation
  → request_middleware (log latency, add X-Request-ID header)
  → HTTP response
```

---

## Security Decisions

| Concern | Decision |
|---|---|
| API keys | Environment variables only. Never in DB. Never in responses. |
| Stack traces | Caught in middleware. Client sees generic message + request_id. |
| File uploads | Extension + MIME type + size validation. Stored outside web root. |
| Injected documents | Wrapped in explicit `<context>` delimiters to prevent indirect injection. |
| Input length | Max 32,000 characters enforced before LLM call. |
| CORS | Explicit origin allowlist from `CORS_ORIGINS` env var. |

---

## Development vs Production Differences

| Concern | Development | Production |
|---|---|---|
| Database | SQLite (zero setup) | PostgreSQL (set DATABASE_URL) |
| Logging | Console pretty-print | JSON (for log aggregators) |
| SQL echo | Enabled | Disabled |
| DB init | `init_db()` at startup | `alembic upgrade head` |
| Vite proxy | Active | Not needed (VITE_API_URL set) |
