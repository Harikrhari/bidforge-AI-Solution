"""Semantic cache (cache-aside). Replace linear scan with RediSearch/pgvector at scale."""
import hashlib
import json

import litellm
import numpy as np
from redis.asyncio import Redis


class SemanticCache:
    def __init__(self, redis: Redis, embed_model: str, threshold: float = 0.95):
        self.r, self.model, self.t = redis, embed_model, threshold

    async def _emb(self, text: str) -> np.ndarray:
        v = (await litellm.aembedding(model=self.model, input=[text])).data[0]["embedding"]
        v = np.array(v, dtype=np.float32)
        return v / np.linalg.norm(v)

    async def get(self, tenant_id: str, prompt: str) -> str | None:
        exact = await self.r.get(f"c:{tenant_id}:{hashlib.sha256(prompt.encode()).hexdigest()}")
        if exact:
            return exact.decode()
        q = await self._emb(prompt)
        for key in await self.r.lrange(f"cidx:{tenant_id}", 0, 500):
            item = json.loads(await self.r.get(key) or "{}")
            if item and float(np.dot(q, np.array(item["v"]))) >= self.t:
                return item["answer"]
        return None

    async def set(self, tenant_id: str, prompt: str, value: str) -> None:
        h = hashlib.sha256(prompt.encode()).hexdigest()
        v = (await self._emb(prompt)).tolist()
        await self.r.set(f"c:{tenant_id}:{h}", value, ex=86400 * 30)
        await self.r.set(f"s:{tenant_id}:{h}", json.dumps({"v": v, "answer": value}), ex=86400 * 30)
        await self.r.lpush(f"cidx:{tenant_id}", f"s:{tenant_id}:{h}")
