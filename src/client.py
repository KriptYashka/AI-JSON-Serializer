import asyncio
import logging
from typing import Any

import httpx

from src.config import settings
from src.errors import ERROR_MAP, OpenRouterError
from src.models import ChatRequest, ChatResponse, Choice, Message, ModelInfo, TokenUsage

logger = logging.getLogger(__name__)


class OpenRouterClient:
    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key or settings.api_key
        if not self._api_key:
            raise OpenRouterError(
                "OPENROUTER_API_KEY не задан. "
                "Укажите его в .env или config.ini"
            )

        self._base_url = settings.base_url
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            timeout=settings.timeout,
        )

    async def chat_completion(
        self,
        request: ChatRequest,
        *,
        max_retries: int = 3,
    ) -> ChatResponse:
        payload = request.model_dump(exclude_none=True)
        data = await self._request("POST", "/chat/completions", json=payload, max_retries=max_retries)
        return self._parse_chat_response(data)

    async def list_models(self, *, max_retries: int = 2) -> list[ModelInfo]:
        data = await self._request("GET", "/models", max_retries=max_retries)
        return [ModelInfo(**m) for m in data.get("data", [])]

    @staticmethod
    def _parse_chat_response(data: dict[str, Any]) -> ChatResponse:
        choices = [
            Choice(
                index=c["index"],
                message=Message(**c["message"]),
                finish_reason=c.get("finish_reason", "stop"),
            )
            for c in data.get("choices", [])
        ]

        usage_raw = data.get("usage")
        usage = TokenUsage(**usage_raw) if usage_raw else None

        return ChatResponse(
            id=data["id"],
            model=data["model"],
            choices=choices,
            usage=usage,
        )

    @staticmethod
    def _extract_error_detail(response: httpx.Response) -> str:
        try:
            body = response.json()
            return body.get("error", {}).get("message", response.text)
        except Exception:
            return response.text

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        max_retries: int = 3,
    ) -> dict[str, Any]:
        last_error: Exception | None = None

        for attempt in range(max_retries + 1):
            try:
                response = await self._client.request(method, path, json=json)

                if response.is_success:
                    return response.json()

                error_cls = ERROR_MAP.get(response.status_code, OpenRouterError)
                detail = self._extract_error_detail(response)
                raise error_cls(detail)

            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                last_error = exc
                if attempt < max_retries:
                    wait = 1.5 ** attempt
                    logger.warning("Попытка %d: %s. Повтор через %.1fс…", attempt + 1, exc, wait)
                    await asyncio.sleep(wait)
                else:
                    raise OpenRouterError(f"Сеть недоступна после {max_retries + 1} попыток") from exc

            except OpenRouterError:
                raise

            except Exception as exc:
                raise OpenRouterError(f"Неожиданная ошибка: {exc}") from exc

        raise OpenRouterError("Не удалось выполнить запрос") from last_error

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> "OpenRouterClient":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()
