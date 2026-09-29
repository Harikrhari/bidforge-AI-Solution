# BidForge AI

AI copilot that finds tenders/RFPs a small business can win, scores them, and drafts a
compliant, cited proposal. Built with FastAPI, RAG on Postgres pgvector, LangGraph, MCP,
LLM routing and Evals.

*Created by Claude Architect Harikrishnan Rajaram*

Full design document: [docs/Product_Development_AI.docx](docs/Product_Development_AI.docx)

## Quick start
```bash
cp .env.example .env        # add your API keys
docker compose up --build
curl -H "Authorization: Bearer dev" -F "file=@tender.pdf" http://localhost:8000/v1/tenders/analyze
```

## Layout (clean architecture)
- `app/domain` – entities and rules (no framework imports)
- `app/application` – ports (interfaces)
- `app/infrastructure` – adapters: LLM router, pgvector retriever, cache, guardrails, parser
- `app/orchestration` – LangGraph bid workflow
- `app/interface` – FastAPI API and MCP server
- `evals` – quality gate
