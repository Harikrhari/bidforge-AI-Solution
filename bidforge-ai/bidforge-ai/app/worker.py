"""ARQ background worker for ingestion and long drafting jobs."""
import os

from arq.connections import RedisSettings


async def ingest_document(ctx, tenant_id: str, path: str) -> dict:
    # TODO: parse (Docling) -> chunk -> hash -> embed new chunks -> insert into chunks table
    return {"tenant_id": tenant_id, "path": path, "status": "queued"}


class WorkerSettings:
    functions = [ingest_document]
    redis_settings = RedisSettings.from_dsn(os.getenv("REDIS_URL", "redis://localhost:6379"))
