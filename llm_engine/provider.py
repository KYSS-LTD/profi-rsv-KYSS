import os

import httpx
from openai import AsyncOpenAI
from pydantic import BaseModel

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


class LLMProvider:
    """Вызов LLM через OpenRouter (OpenAI-совместимый API) или локальный Ollama.

    .structured(prompt, schema) — нативный structured output (response_format=Pydantic),
      нужен нодам (в т.ч. для гарантии Literal[ростер]/Literal[task_ids]).
    .complete(system, user) — сырой текст, как у Алексея (для совместимости).

    Конфиг через env: LLM_PROVIDER (api/local), LLM_MODEL, OPENROUTER_API_KEY,
    OPENROUTER_BASE_URL, OLLAMA_BASE_URL, HTTP_PROXY.
    """

    def __init__(
        self,
        mode: str = "api",
        model: str = "deepseek/deepseek-v4-flash",
        api_key: str | None = None,
        proxy: str | None = None,
        temperature: float = 0.0,
    ):
        self.mode = mode
        self.model = model
        self.temperature = temperature

        proxy = proxy or os.getenv("HTTP_PROXY")
        http_client = httpx.AsyncClient(proxy=proxy) if proxy else None

        if mode in ("api", "openrouter"):
            self.client = AsyncOpenAI(
                base_url=os.getenv("OPENROUTER_BASE_URL", OPENROUTER_BASE_URL),
                api_key=api_key or os.getenv("OPENROUTER_API_KEY"),
                http_client=http_client,
            )
        elif mode == "local":
            # Ollama через OpenAI-совместимый endpoint
            self.client = AsyncOpenAI(
                base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1"),
                api_key="ollama",
                http_client=http_client,
            )
        else:
            raise ValueError(f"Неподдерживаемый режим: {mode}. Используйте 'api' (OpenRouter) или 'local'.")

    async def structured(self, prompt: str, schema: type[BaseModel]) -> BaseModel:
        completion = await self.client.beta.chat.completions.parse(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.temperature,
            response_format=schema,
        )
        return completion.choices[0].message.parsed

    async def complete(self, system: str, user: str, **kwargs) -> str:
        resp = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=kwargs.get("temperature", self.temperature),
            max_tokens=kwargs.get("max_tokens", 1024),
        )
        return resp.choices[0].message.content
