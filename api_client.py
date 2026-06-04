from __future__ import annotations

import logging
from dataclasses import dataclass, field
from time import perf_counter
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class ApiError(Exception):
    pass


@dataclass
class ApiClient:
    base_url: str
    api_token: str
    timeout_seconds: float = 30.0
    long_timeout_seconds: float = 300.0
    _client: httpx.AsyncClient | None = field(default=None, init=False, repr=False)

    @property
    def _auth_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_token}"}

    def _ensure_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self.timeout_seconds,
                trust_env=False,
                headers=self._auth_headers,
            )
        return self._client

    async def aclose(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        timeout_seconds: float | None = None,
    ) -> Any:
        url = f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"
        started = perf_counter()
        logger.info("API запрос -> %s %s | params=%s", method, url, params)
        try:
            timeout = timeout_seconds if timeout_seconds is not None else self.timeout_seconds
            client = self._ensure_client()
            response = await client.request(
                method,
                url,
                json=json,
                data=data,
                files=files,
                params=params,
                timeout=timeout,
            )
        except httpx.HTTPError as exc:
            elapsed_ms = (perf_counter() - started) * 1000
            logger.exception("API ошибка соединения <- %s %s | %.1f ms | %s", method, url, elapsed_ms, exc)
            raise ApiError(f"Не удалось подключиться к API: {exc}") from exc

        elapsed_ms = (perf_counter() - started) * 1000
        logger.info("API ответ <- %s %s | status=%s | %.1f ms", method, url, response.status_code, elapsed_ms)
        if response.status_code >= 400:
            detail = None
            try:
                body = response.json()
                detail = body.get("detail")
            except ValueError:
                detail = response.text
            logger.warning(
                "API вернуло ошибку <- %s %s | status=%s | detail=%s",
                method,
                url,
                response.status_code,
                detail,
            )
            raise ApiError(f"API вернуло ошибку {response.status_code}: {detail or 'unknown error'}")

        if response.headers.get("content-type", "").startswith("application/json"):
            return response.json()
        return response.text

    async def health(self) -> dict[str, Any]:
        return await self._request("GET", "/health")

    async def command(
        self,
        message: str,
        user_id: str,
        filename: str | None = None,
        file_bytes: bytes | None = None,
    ) -> dict[str, Any]:
        files = {"file": (filename or "uploaded.file", file_bytes)} if file_bytes is not None else None
        return await self._request(
            "POST",
            "/agent/command",
            data={"message": message, "user_id": user_id},
            files=files,
            timeout_seconds=self.long_timeout_seconds,
        )

    async def reset_session(self, user_id: str) -> dict[str, Any]:
        return await self._request(
            "POST",
            "/agent/session/reset",
            data={"user_id": user_id},
        )
