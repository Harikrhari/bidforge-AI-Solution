"""Dependency-injection wiring (composition root). Only this file knows concrete adapters."""
import os
from dataclasses import dataclass
from functools import lru_cache

import asyncpg
from fastapi import Header, HTTPException

from app.infrastructure.guardrails import Guardrails
from app.infrastructure.llm_router import LLMRouter
from app.infrastructure.parser import DoclingParser
from app.infrastructure.pgvector_retriever import PgVectorRetriever
from app.orchestration.bid_graph import build_graph

EMBED_MODEL = os.getenv("EMBED_MODEL", "voyage/voyage-3-lite")
RERANK_MODEL = os.getenv("RERANK_MODEL", "cohere/rerank-english-v3.0")
_pool: asyncpg.Pool | None = None


@dataclass
class Tenant:
    id: str
    plan: str


async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(os.environ["DATABASE_URL"], min_size=1, max_size=10)
    return _pool


def build_retriever(pool=None) -> PgVectorRetriever:
    return PgVectorRetriever(pool, EMBED_MODEL, RERANK_MODEL)


async def get_graph():
    llm = LLMRouter()
    return build_graph(llm, build_retriever(await get_pool()), Guardrails(llm))


@lru_cache
def get_parser() -> DoclingParser:
    return DoclingParser()


async def current_tenant(authorization: str = Header(...)) -> Tenant:
    # TODO: verify JWT with your auth provider (Clerk/Auth0) and read tenant claims.
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing bearer token")
    return Tenant(id="demo-tenant", plan="pro")


async def check_quota() -> None:
    # TODO: enforce per-tenant token/draft budgets from Redis counters.
    return None
