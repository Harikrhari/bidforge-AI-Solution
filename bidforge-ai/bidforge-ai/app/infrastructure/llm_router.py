"""LLM router (Strategy pattern) via LiteLLM: cheapest model that passes evals per task."""
import litellm
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential

ROUTES = {
    "extract": "anthropic/claude-haiku-4-5-20251001",
    "score": "anthropic/claude-haiku-4-5-20251001",
    "judge": "anthropic/claude-haiku-4-5-20251001",
    "draft": "anthropic/claude-sonnet-5-5",
}
FALLBACK = "anthropic/claude-haiku-4-5-20251001"


class LLMRouter:
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def complete(self, task, system, prompt, schema: type[BaseModel] | None = None):
        model = ROUTES.get(task, FALLBACK)
        resp = await litellm.acompletion(
            model=model,
            messages=[
                {"role": "system", "content": system},  # stable prefix -> prompt caching
                {"role": "user", "content": prompt},
            ],
            response_format=schema,
            fallbacks=[FALLBACK],
            max_tokens=4000,
        )
        text = resp.choices[0].message.content
        return schema.model_validate_json(text) if schema else text

    async def stream(self, task, system, prompt):
        resp = await litellm.acompletion(
            model=ROUTES.get(task, FALLBACK), stream=True, max_tokens=4000,
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": prompt}],
        )
        async for chunk in resp:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta
