from pydantic_settings import BaseSettings


class BotSettings(BaseSettings):
    telegram_bot_token: str = ""
    api_base_url: str = "http://127.0.0.1:8000"
    request_timeout_seconds: float = 30.0

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = BotSettings()
