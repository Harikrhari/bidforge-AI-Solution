from collections.abc import AsyncIterator
from typing import Protocol

from pydantic import BaseModel

from app.domain.models import Evidence


class LLMPort(Protocol):
    async def complete(self, task: str, system: str, prompt: str,
                       schema: type[BaseModel] | None = None) -> str | BaseModel: ...
    def stream(self, task: str, system: str, prompt: str) -> AsyncIterator[str]: ...


class RetrieverPort(Protocol):
    async def search(self, tenant_id: str, query: str, k: int = 8) -> list[Evidence]: ...


class CachePort(Protocol):
    async def get(self, tenant_id: str, prompt: str) -> str | None: ...
    async def set(self, tenant_id: str, prompt: str, value: str) -> None: ...


class ParserPort(Protocol):
    async def parse(self, data: bytes) -> str: ...
