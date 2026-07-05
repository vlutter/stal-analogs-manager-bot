# STAL Analogs Manager Bot

Telegram-бот — тонкий клиент к backend API [`stal-analogs-storage`](https://github.com/stal/stal-analogs-storage). Пользователь пишет задачу обычным текстом или прикрепляет файл; бот передаёт запрос в AI-агент на сервере и показывает результат. Данные в Google Sheets сохраняются только после подтверждения предпросмотра.

Руководство для пользователей бота — в [`GUIDE.md`](GUIDE.md). Инструкция по деплою — в [`DEPLOY.md`](DEPLOY.md).

## Что умеет бот

- Произвольные команды на естественном языке через `POST /agent/command` (поиск, CRUD маппингов и моделей техники, извлечение из файлов)
- Загрузка файлов (Excel, CSV, PDF, изображения) с извлечением связок `STAL → аналоги` и при необходимости `STAL → модели техники`
- Поиск STAL по модели техники и просмотр моделей по STAL-коду
- Глубокий поиск по файлу через уже сохранённые артикулы в базе
- Предпросмотр массовых изменений (аналоги и модели) с подтверждением «применить» / «отменить» и правкой текстом; XLSX с двумя листами при >20 записей
- Сброс контекста диалога командой `/new` (`POST /agent/session/reset`)
- Inline-обучалка (`/help`) с разделами по сценариям
- Whitelist Telegram user_id — доступ только разрешённым пользователям

Контекст сессии (история, прикреплённые файлы, активный предпросмотр) хранится на стороне backend, не в боте.

## Быстрый старт (локально)

1. Создайте и активируйте виртуальное окружение (Python 3.12+).
2. Установите зависимости:

```bash
pip install -r requirements.txt
```

3. Создайте `.env` на основе `.env.example`:

```env
TELEGRAM_BOT_TOKEN=ваш_токен_бота
TELEGRAM_ALLOWED_USER_IDS=123456789,987654321
API_TOKEN=ваш_bearer_токен_для_api
API_BASE_URL=http://127.0.0.1:8000
REQUEST_TIMEOUT_SECONDS=30
LONG_REQUEST_TIMEOUT_SECONDS=300
```

`TELEGRAM_ALLOWED_USER_IDS` — comma-separated список numeric Telegram user ID. Узнать свой ID можно через [@userinfobot](https://t.me/userinfobot).

4. Запустите backend `stal-analogs-storage` по адресу из `API_BASE_URL`.
5. Запустите бота:

```bash
python bot.py
```

## Быстрый старт (Docker)

```bash
docker build -t stal-analogs-manager-bot:local .
docker compose up -d
docker compose logs -f bot
```

Compose подключается к внешней docker-сети `stal-analogs-storage` (создаётся при запуске storage). Сначала поднимите storage, затем бота. Подробности — в [`DEPLOY.md`](DEPLOY.md).

## Деплой

Публикация через GitHub Actions → GitHub Container Registry → Docker Compose на Ubuntu 24.04 описана в [`DEPLOY.md`](DEPLOY.md).

## Архитектура

Бот не содержит бизнес-логики маппингов — только transport/UI и HTTP-клиент к API.

```text
Telegram update
      │
      ▼
enforce_whitelist (group -2)
      │
      ▼
ConversationHandler
  /start, /help, /new
  текст и файлы → menu_agent_command
      │
      ▼
ApiClient.command()  ──►  POST /agent/command  (stal-analogs-storage)
      │
      ▼
Форматирование ответа, предпросмотр ingest (аналоги + модели; XLSX с двумя листами при >20 записей)
```

### Уровни

- **Transport/UI**: хендлеры Telegram, клавиатуры, форматирование ответов
- **Application wiring**: `build_application()`, `ConversationHandler`, whitelist, логирование
- **Infrastructure**: `ApiClient`, настройки (`pydantic-settings`), retry для Telegram API

### Карта файлов

```text
stal-analogs-manager-bot/
├─ bot.py                      # совместимый entrypoint; делегирует запуск в bot/main.py
├─ api_client.py               # async HTTP-клиент: /health, /agent/command, /agent/session/reset
├─ config.py                   # настройки из env (токены, whitelist, таймауты)
├─ Dockerfile
├─ docker-compose.yml
├─ bot/
│  ├─ main.py                  # polling entrypoint
│  ├─ application.py           # build_application(), ConversationHandler, маршрутизация
│  ├─ constants.py             # кнопки обучалки и ID состояний
│  ├─ keyboards.py             # inline-клавиатура /help
│  ├─ logging_setup.py         # консоль + ротационный logs/bot.log
│  ├─ runner.py                  # BotRunner для программного старта/остановки
│  ├─ handlers/
│  │  ├─ common.py             # /start, /help, fallback, post_init (set_my_commands), лог апдейтов
│  │  ├─ agent_command.py      # текст и файлы → фоновый вызов /agent/command
│  │  ├─ session.py            # /new → сброс сессии на backend
│  │  └─ ingest.py             # предпросмотр ingest и генерация XLSX
│  └─ services/
│     ├─ access.py             # whitelist по TELEGRAM_ALLOWED_USER_IDS
│     ├─ context.py            # доступ к ApiClient из bot_data
│     ├─ errors.py             # единый ответ при ApiError
│     ├─ telegram_markup.py    # отправка форматированных сообщений
│     ├─ telegram_retry.py     # retry при сбоях Telegram API
│     ├─ text_formatters.py    # приветствие, help, форматирование ответов агента
│     └─ parsing.py            # parse_list(), unique_keep_order()
└─ logs/
   └─ bot.log
```

## Как проходит запрос

1. `bot.py` передаёт управление в `bot/main.py`.
2. `build_application()` создаёт `Application`, кладёт `ApiClient` в `bot_data`, регистрирует whitelist и `ConversationHandler`.
3. Текст или файл попадает в `menu_agent_command`:
   - бот сразу отвечает «Думаю...»;
   - долгий вызов `ApiClient.command()` выполняется в фоне через `create_task`;
   - результат форматируется и отправляется отдельным сообщением.
4. Для ingest/deep extraction бот показывает предпросмотр аналогов и моделей техники (и XLSX с листами «Аналоги» / «Модели техники» при большом объёме); подтверждение и правки снова идут через `/agent/command`.

## Навигация по коду

| Задача | Файл |
| --- | --- |
| Whitelist и отказ в доступе | `bot/services/access.py` |
| Команды `/start`, `/help`, регистрация меню бота | `bot/handlers/common.py` |
| Обработка текста и файлов | `bot/handlers/agent_command.py` |
| Сброс сессии `/new` | `bot/handlers/session.py` |
| Предпросмотр ingest и XLSX | `bot/handlers/ingest.py` |
| Тексты обучалки | `bot/services/text_formatters.py`, `bot/keyboards.py` |
| HTTP-контракт с backend | `api_client.py` |
| Новое состояние или маршрут | `bot/application.py`, `bot/constants.py` |

## Как добавить новую функцию

1. Если нужен новый endpoint — добавьте метод в `api_client.py`.
2. Обработайте новый тип ответа в `agent_command.py` или `text_formatters.py`.
3. При необходимости расширьте обучалку в `text_formatters.py` / `keyboards.py`.
4. Проверьте поток вручную в Telegram.

Большинство пользовательских сценариев добавляются на стороне backend-агента; изменения в боте нужны, когда меняется формат ответа или UI (новый тип вложения, особое форматирование).

## Логи и диагностика

- Логи пишутся в консоль и в `logs/bot.log` (в Docker — volume `bot_logs`).
- `bot/handlers/common.py` логирует входящие апдейты (группа `-1`).
- Отказы whitelist логируются как `Доступ запрещён | user_id=...`.
- Healthcheck контейнера проверяет `GET /health` backend API.

## Команды запуска и проверки

Запуск:

```bash
python bot.py
```

Проверка синтаксиса:

```bash
python -m compileall bot.py bot api_client.py config.py
```
