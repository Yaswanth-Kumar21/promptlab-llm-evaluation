# PromptLab

**LLM Prompt Engineering, Evaluation, RAG & AI Safety Platform**

A production-quality portfolio project demonstrating the complete prompt engineering lifecycle:

**Design → Test → Evaluate → Analyse → Refine → Retest**

Built to target entry-level and junior Prompt Engineer positions.

---

## Why I Built This

Most LLM demos are ChatGPT clones. This project is different — it treats prompt engineering
as a **software engineering discipline** with version control, systematic evaluation,
reproducible experiments, and safety testing.

PromptLab lets me answer interview questions like:
- "How did you evaluate your prompts?"
- "How did you compare prompt versions?"
- "How did you defend against hallucination?"
- "How did you test for prompt injection?"

---

## Features

| Feature | Status | Phase |
|---|---|---|
| Prompt Playground | 🔜 | Phase 4 |
| Zero-shot / Few-shot / Structured prompting | 🔜 | Phase 5 |
| Prompt Versioning & Comparison | 🔜 | Phase 6 |
| Evaluation Engine (accuracy, relevance, tone, safety) | 🔜 | Phase 7 |
| Safety Lab (injection, hallucination, bias) | 🔜 | Phase 8 |
| RAG Pipeline (ChromaDB + embeddings) | 🔜 | Phase 9 |
| Multi-provider (OpenAI, Gemini, Mistral, Anthropic) | 🔜 | Phase 10 |
| Dashboard & Charts | 🔜 | Phase 11 |
| AI Job Application Analyzer | 🔜 | Phase 12 |
| Knowledge Base | ✅ | Phase 1 |
| FastAPI + Swagger | ✅ | Phase 1 |
| Health & Provider endpoints | ✅ | Phase 1 |
| React + TailwindCSS frontend | ✅ | Phase 1 |
| Structured logging | ✅ | Phase 1 |
| SQLite / PostgreSQL database layer | ✅ | Phase 1 |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      FRONTEND                               │
│           React 18 + Vite + TailwindCSS                     │
│                  localhost:5173                              │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP/REST (Axios, proxied by Vite)
┌──────────────────────▼──────────────────────────────────────┐
│                    BACKEND API                              │
│             FastAPI + Uvicorn + Pydantic                    │
│                  localhost:8000                              │
│  ┌───────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │ Prompt Service│  │  RAG Service  │  │Evaluation Engine│  │
│  └──────┬────────┘  └──────┬───────┘  └───────┬─────────┘  │
│         │                  │                   │             │
│  ┌──────▼────────┐  ┌──────▼───────┐  ┌───────▼─────────┐  │
│  │ LLM Providers │  │  ChromaDB    │  │   SQLite / PG   │  │
│  │  (abstracted) │  │ (vector store│  │  (experiments,  │  │
│  │               │  │  + embeddings│  │   evaluations)  │  │
│  │ openai        │  └──────────────┘  └─────────────────┘  │
│  │ anthropic     │                                           │
│  │ gemini        │                                           │
│  │ mistral       │                                           │
│  │ mock ✅       │                                           │
│  └───────────────┘                                           │
└─────────────────────────────────────────────────────────────┘
```

---

## Prompt Engineering Techniques

### Zero-Shot
Ask the model to perform a task with no examples. Relies entirely on pre-trained knowledge.
Best for simple, well-defined tasks. Used as a baseline before trying few-shot.

### Few-Shot
Provide 2–10 labelled input/output examples in the prompt so the model learns the pattern
in-context. Significantly improves accuracy on niche or format-sensitive tasks.

### Role Prompting
Assign a persona: `"You are an expert technical recruiter with 10 years experience."`
Shapes vocabulary, tone, and the depth of domain knowledge the model applies.

### Structured Prompting
Force machine-readable output (JSON, YAML, Markdown tables) with explicit schemas.
Every structured output is validated with Pydantic. JSON parse failures are detected,
recorded, and optionally repaired.

### Constraint-Based Prompting
Add explicit rules: `"Reply in exactly 3 bullet points. Each bullet must be under 20 words.
Do not introduce information not present in the source."`

---

## LLM Fundamentals

### Tokens
The basic unit an LLM processes — roughly 4 characters or ¾ of a word (GPT tokeniser).
All API billing and context limits are measured in tokens.

### Context Window
The maximum number of tokens the model can "see" at once (input + output combined).
GPT-4o: 128k tokens. Claude 3: 200k tokens. Overflow silently truncates content.

### Temperature
Controls output randomness. `0` = deterministic, best for factual/structured tasks.
`0.7` = balanced default. `>1.0` = chaotic, rarely useful in production.

---

## Evaluation Methodology

Each LLM response is evaluated on up to 7 dimensions:

| Metric | Method | Notes |
|---|---|---|
| Accuracy | Exact match + semantic similarity | Deterministic where possible |
| Relevance | Keyword + semantic checks | No LLM judge in Phase 7 |
| Tone | Rule-based tone classifiers | Deterministic |
| Consistency | Run same prompt 3× and measure variance | Actual repeated calls |
| JSON Validity | Pydantic schema validation | Fully deterministic |
| Groundedness | Check claims against source chunks | Semi-deterministic |
| Safety | Rule-based injection/harm detection | Deterministic baseline |

**Limitation:** LLM-as-judge is used only where deterministic methods are insufficient.
All LLM-judge evaluations are explicitly labelled. Scores are only reported from actual
test runs — never fabricated.

---

## RAG Architecture

```
Document upload (PDF / TXT / MD)
        │
        ▼
  Text extraction (pypdf / plain text)
        │
        ▼
  Chunking (~500 tokens, 50-token overlap)
        │
        ▼
  Embedding (all-MiniLM-L6-v2, local — no API key needed)
        │
        ▼
  ChromaDB (persisted vector store)
        │
    Query time
        │
        ▼
  Embed question → cosine similarity search → top-k chunks
        │
        ▼
  Prompt construction:
    [system prompt]
    <context>
      chunk_1 (source: doc.pdf, chunk_04)
      chunk_2 (source: doc.pdf, chunk_07)
    </context>
    Question: [user question]
        │
        ▼
  LLM response with source citations
```

**Security note:** Retrieved document chunks are treated as untrusted data.
Explicit `<context>` delimiters prevent indirect prompt injection.

---

## Safety

### Prompt Injection
User input and retrieved documents are treated as untrusted. Injected content is
wrapped in explicit delimiters. A dedicated attack dataset tests common injection
patterns. Results are shown in the Safety Lab.

### Hallucination
Test cases include questions where the context does *not* contain the answer.
The model is instructed to say "I don't have enough information" rather than guess.
Detection is automated but imperfect — human review is needed for high-stakes tasks.

### Bias
Controlled test cases compare outputs for otherwise identical inputs where only a
non-job-relevant demographic attribute differs. A bias score is computed. Results
include the disclaimer: *"Bias evaluation is experimental and does not constitute
a comprehensive fairness audit."*

---

## Experiments

*(To be filled in with actual results from Phase 7 onwards.)*

Example experiment format:
```
Task: Summarise a technical article
Prompt V1: "Summarise this."
Prompt V2: "Summarise in 5 bullet points."
Prompt V3: Role + constraints + format

Result: V3 scored 23 points higher on relevance than V1.
Why: Explicit format constraints reduced verbosity. Role priming
     improved technical vocabulary.
```

---

## Screenshots

*(To be added after Phase 4 UI is complete.)*

---

## Installation

### Prerequisites
- Python 3.11+
- Node.js 20+
- Git

### 1. Clone
```bash
git clone https://github.com/Yaswanth-Kumar21/promptlab-llm-evaluation.git
cd promptlab-llm-evaluation
```

### 2. Backend
```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Frontend
```bash
cd ../frontend
npm install
```

---

## Environment Variables

```bash
cp .env.example .env
```

Minimum required for development (mock provider — no API key needed):
```env
APP_ENV=development
DEFAULT_PROVIDER=mock
DATABASE_URL=sqlite:///./promptlab.db
```

To use a real provider, add its key:
```env
OPENAI_API_KEY=sk-...
```

**Never commit `.env` to version control.**

---

## Running Locally

### Backend
```bash
cd backend
.venv\Scripts\activate          # Windows
uvicorn app.main:app --reload   # http://localhost:8000
```

### Frontend
```bash
cd frontend
npm run dev                     # http://localhost:5173
```

Vite proxies `/api/*` → `http://localhost:8000/api/*` automatically.

---

## Testing

```bash
cd backend
python -m pytest -v
```

Tests use HTTPX's async test client against the ASGI app — no real server or API keys needed.

---

## API Documentation

With the backend running, open:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

Key endpoints:
```
GET  /api/health          Backend health check
GET  /api/providers       List configured LLM providers
GET  /api/prompts         List prompts (Phase 4)
POST /api/prompts/run     Run a prompt (Phase 4)
POST /api/experiments/run Run an experiment (Phase 6)
POST /api/evaluations/run Run evaluation (Phase 7)
POST /api/documents/upload Upload RAG document (Phase 9)
POST /api/rag/query       RAG query with citations (Phase 9)
```

---

## Deployment

### Backend (Render / Railway / Fly.io)
```bash
# Set environment variables in dashboard (never in code)
# Build command:
pip install -r requirements.txt
# Start command:
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### Frontend (Vercel)
```bash
# Set VITE_API_URL=https://your-backend.render.com in Vercel env vars
npm run build
# Vercel auto-detects Vite
```

### Database (Production)
Replace SQLite with PostgreSQL:
```env
DATABASE_URL=postgresql://user:password@host:5432/promptlab
```
Run migrations: `alembic upgrade head`

**Note:** LLM API keys cost money in production. The mock provider is free and
works without any external service.

---

## Limitations

- **LLM nondeterminism:** The same prompt can produce different outputs across runs.
  Evaluation scores will vary slightly. This is expected and documented.
- **Imperfect evaluation:** Automated metrics approximate human judgement. They
  are useful for relative comparison, not absolute quality measurement.
- **LLM-as-judge:** When an LLM evaluates another LLM's output, it inherits the
  same biases and errors. Results are treated as heuristic signals, not ground truth.
- **Hallucination detection:** Rule-based checks and context grounding reduce but
  do not eliminate hallucination. Human review is required for high-stakes tasks.
- **Provider differences:** Different models interpret the same prompt differently.
  Evaluation scores are not directly comparable across providers.
- **Token counting:** Some providers don't return token usage in every response.
  Missing counts are shown as `—` rather than fabricated.

---

## Future Improvements

- Replace ChromaDB with pgvector for unified PostgreSQL storage
- Human feedback loop for evaluation labelling (thumbs up/down)
- OpenTelemetry tracing for LLM call observability
- CI/CD pipeline that runs evaluation on every prompt change
- Cost tracker (tokens × price per token per provider)
- Prompt diff viewer (character-level diff between versions)
- Export experiments to CSV / JSONL for offline analysis

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, Vite, TailwindCSS, Recharts, Axios |
| Backend | FastAPI, Uvicorn, Pydantic v2, SQLAlchemy |
| Database | SQLite (dev) / PostgreSQL (prod) |
| Vector DB | ChromaDB |
| Embeddings | sentence-transformers (local, no API key) |
| LLM providers | OpenAI, Anthropic, Gemini, Mistral, Mock |
| Testing | pytest, pytest-asyncio, httpx |
| Logging | structlog |

---

*Built by Yaswanth Kumar — Final-year B.Tech CSE (AI & ML)*
