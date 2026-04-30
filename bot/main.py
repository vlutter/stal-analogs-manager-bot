from time import perf_counter
import logging

from bot.application import build_application
from bot.logging_setup import setup_logging

logger = logging.getLogger(__name__)


def main() -> None:
    """Точка входа для запуска бота в режиме polling."""
    setup_logging()
    start_ts = perf_counter()
    logger.info("Запуск Telegram-бота в режиме polling...")
    app = build_application()
    app.run_polling(close_loop=False)
    elapsed = perf_counter() - start_ts
    logger.info("Polling остановлен. Время работы: %.2f c", elapsed)


if __name__ == "__main__":
    main()

