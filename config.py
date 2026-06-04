from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode


class BotSettings(BaseSettings):
    telegram_bot_token: str = ""
    telegram_allowed_user_ids: Annotated[list[int], NoDecode] = []
    telegram_connect_timeout_seconds: float = 30.0
    telegram_read_timeout_seconds: float = 30.0
    telegram_write_timeout_seconds: float = 30.0
    telegram_pool_timeout_seconds: float = 30.0
    telegram_retry_attempts: int = 3
    telegram_retry_delay_seconds: float = 2.0
    api_token: str
    api_base_url: str = "http://127.0.0.1:8000"
    request_timeout_seconds: float = 30.0
    long_request_timeout_seconds: float = 300.0

    @field_validator("telegram_allowed_user_ids", mode="before")
    @classmethod
    def parse_telegram_allowed_user_ids(cls, value: object) -> list[int]:
        if value is None or value == "":
            return []
        if isinstance(value, list):
            return [int(item) for item in value]
        return [
            int(part.strip())
            for part in str(value).split(",")
            if part.strip()
        ]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = BotSettings()
