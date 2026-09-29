"""Hybrid RAG retriever: pgvector + Postgres full-text, fused with RRF, then reranked."""
import asyncpg
import litellm

from app.domain.models import Evidence

HYBRID_SQL = """
WITH vec AS (
  SELECT id, content, source, 1 - (embedding <=> $2::vector) AS score
  FROM chunks WHERE tenant_id = $1
  ORDER BY embedding <=> $2::vector LIMIT 40
), kw AS (
  SELECT id, content, source,
         ts_rank(tsv, plainto_tsquery('english', $3)) AS score
  FROM chunks WHERE tenant_id = $1 AND tsv @@ plainto_tsquery('english', $3)
  ORDER BY score DESC LIMIT 40
)
SELECT id, content, source, SUM(1.0 / (60 + rnk)) AS rrf
FROM (
  SELECT *, ROW_NUMBER() OVER (ORDER BY score DESC) AS rnk FROM vec
  UNION ALL
  SELECT *, ROW_NUMBER() OVER (ORDER BY score DESC) AS rnk FROM kw
) u GROUP BY id, content, source ORDER BY rrf DESC LIMIT 50;
"""


class PgVectorRetriever:
    def __init__(self, pool: asyncpg.Pool, embed_model: str, rerank_model: str):
        self.pool, self.embed_model, self.rerank_model = pool, embed_model, rerank_model

    async def search(self, tenant_id: str, query: str, k: int = 8) -> list[Evidence]:
        emb = (await litellm.aembedding(model=self.embed_model, input=[query])).data[0]["embedding"]
        async with self.pool.acquire() as con:
            rows = await con.fetch(HYBRID_SQL, tenant_id, str(emb), query)
        if not rows:
            return []
        ranked = await litellm.arerank(model=self.rerank_model, query=query,
                                       documents=[r["content"] for r in rows], top_n=k)
        return [Evidence(chunk_id=str(rows[x.index]["id"]), text=rows[x.index]["content"],
                         source=rows[x.index]["source"], score=x.relevance_score)
                for x in ranked.results]
