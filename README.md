# PromptLab — LLM Evaluation & Prompt Engineering Platform

A full-stack platform for designing, testing, and evaluating LLM prompts across multiple strategies (zero-shot, few-shot, RAG, structured output, safety).

## Project Structure

```
promptlab/
├── backend/          # FastAPI backend
│   └── app/
│       ├── api/      # Route handlers
│       ├── core/     # Config, DB, logging, security
│       ├── models/   # ORM models
│       ├── schemas/  # Pydantic schemas
│       ├── services/ # LLM integrations
│       └── prompts/  # Prompt templates by strategy
├── frontend/         # React/Next.js frontend
│   └── src/
│       ├── components/
│       ├── hooks/
│       ├── pages/
│       ├── services/
│       └── utils/
├── evaluation/       # Evaluation datasets & experiment results
├── rag/              # RAG document store
└── docs/             # Documentation
```

## Getting Started

1. Copy `.env.example` to `.env` and fill in your API keys.
2. Run the stack with Docker Compose:

```bash
docker compose up --build
```

## Tech Stack

- **Backend**: Python · FastAPI · SQLAlchemy
- **Frontend**: React / Next.js
- **Vector Store**: ChromaDB
- **Containerization**: Docker / Docker Compose

## License

MIT
