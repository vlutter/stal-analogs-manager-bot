import logging

from telegram.ext import Application

from config import settings

logger = logging.getLogger(__name__)


class BotRunner:
    def __init__(self) -> None:
        """Инициализирует раннер и определяет, включен ли бот по токену."""
        self.application: Application | None = None
        self.enabled = bool(settings.telegram_bot_token.strip())

    async def start(self) -> None:
        """Запускает Telegram-бота и стартует long polling, если бот включен."""
        if not self.enabled:
            logger.info("Telegram bot disabled: TELEGRAM_BOT_TOKEN is empty.")
            return

        from bot.application import build_application

        self.application = build_application()
        await self.application.initialize()
        await self.application.start()
        if self.application.updater is None:
            logger.warning("Telegram bot updater is not available. Polling was not started.")
            return
        await self.application.updater.start_polling()
        logger.info("Telegram bot polling started.")

    async def stop(self) -> None:
        """Останавливает polling и корректно завершает приложение бота."""
        if not self.application:
            return
        if self.application.updater is not None:
            await self.application.updater.stop()
        await self.application.stop()
        await self.application.shutdown()
        logger.info("Telegram bot stopped.")

