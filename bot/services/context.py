from telegram.ext import ContextTypes

from api_client import ApiClient


def get_api(context: ContextTypes.DEFAULT_TYPE) -> ApiClient:
    """Достает API-клиент из `bot_data` текущего приложения."""
    return context.application.bot_data["api_client"]

