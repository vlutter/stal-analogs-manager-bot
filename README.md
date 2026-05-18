# STAL Analogs Manager Bot

Telegram-бот для управления соответствиями `STAL -> аналоги` через API проекта `stal-analogs-storage`.

## Что умеет бот

- Добавление нового маппинга (`POST /mappings`)
- Обновление существующего маппинга (`PATCH /mappings/{stal_code}`, `append=true`)
- Удаление одного или нескольких маппингов (`DELETE /mappings/{stal_code}`)
- Удаление конкретных артикулов из маппинга (`GET /mappings/{stal_code}` + `PATCH ... append=false`)
- Загрузка файла и ingest через `/agent/ingest-file` с отчетом по изменениям
- Глубокий поиск по файлу через `/agent/deep-extraction`: бот ищет не только прямые STAL-соответствия в файле, но и непрямые связи через уже сохраненные артикулы в базе
- Поиск STAL по аналогу (`GET /search`)
- Поиск аналогов по STAL (`GET /search/by-stal`)
- Произвольные команды в `/agent/command` (включая обычное извлечение и глубокий поиск с вложенным файлом)

## Быстрый старт

1. Создайте и активируйте виртуальное окружение.
2. Установите зависимости:

```bash
pip install -r requirements.txt
```

3. Создайте `.env` (можно на основе `.env.example`) и заполните:

```env
TELEGRAM_BOT_TOKEN=ваш_токен_бота
API_BASE_URL=http://127.0.0.1:8000
REQUEST_TIMEOUT_SECONDS=30
LONG_REQUEST_TIMEOUT_SECONDS=300
```

4. Запустите бота:

```bash
python bot.py
```

Важно: API-сервис `stal-analogs-storage` должен быть запущен отдельно по адресу из `API_BASE_URL`.

## Архитектура проекта

Проект разделен на 3 уровня:

- **Transport/UI**: Telegram-хендлеры, клавиатуры, переходы по состояниям
- **Application wiring**: сборка `Application`, `ConversationHandler`, регистрация роутов
- **Infrastructure**: HTTP-клиент к API, настройки, логирование

### Карта файлов

```text
stal-analogs-manager-bot/
├─ bot.py                      # совместимый entrypoint; делегирует запуск в bot/main.py
├─ api_client.py               # async HTTP-клиент к backend API + нормализация ошибок ApiError
├─ config.py                   # загрузка настроек из env через pydantic-settings
├─ bot/
│  ├─ main.py                  # основной запуск polling
│  ├─ application.py           # build_application(), ConversationHandler и маршрутизация
│  ├─ constants.py             # кнопки Telegram и ID состояний ConversationHandler
│  ├─ keyboards.py             # конструкторы reply-клавиатур
│  ├─ logging_setup.py         # настройка консольного и файлового логирования
│  ├─ runner.py                # BotRunner для программного старта/остановки (если нужно интегрировать)
│  ├─ handlers/
│  │  ├─ common.py             # /start, /menu, fallback, лог входящих апдейтов, post_init
│  │  ├─ agent_command.py      # универсальная команда пользователя + загрузка вложений
│  │  ├─ mappings.py           # add/update/delete/delete_aliases сценарии
│  │  ├─ search.py             # поиск по аналогу и по STAL
│  │  └─ ingest.py             # сценарий загрузки файла и отчет по ingest
│  └─ services/
│     ├─ context.py            # доступ к ApiClient из context.application.bot_data
│     ├─ parsing.py            # parse_list(), unique_keep_order()
│     ├─ text_formatters.py    # greeting и форматирование ответов
│     └─ errors.py             # единый ответ пользователю при ApiError
└─ logs/
   └─ bot.log                  # ротационный файл логов
```

## Как проходит запрос: от Telegram до API

1. `bot.py` передает управление в `bot/main.py`.
2. `bot/main.py` поднимает логирование и создает приложение через `build_application()`.
3. `bot/application.py`:
   - создает `Application`,
   - кладет `ApiClient` в `application.bot_data["api_client"]`,
   - регистрирует `ConversationHandler` со всеми state-driven сценариями.
4. Нужный хендлер в `bot/handlers/*`:
   - валидирует ввод пользователя,
   - вызывает методы `ApiClient` через `bot/services/context.py`,
   - для произвольных agent-команд быстро подтверждает получение запроса и продолжает долгую обработку в фоне,
   - формирует ответ и переводит пользователя в нужное состояние.

## Навигация по хендлерам (куда идти с задачей)

- Изменение main-меню/кнопок: `bot/constants.py`, `bot/keyboards.py`
- Добавить/изменить state и маршрутизацию: `bot/application.py`
- Логика CRUD маппингов: `bot/handlers/mappings.py`
- Поисковые сценарии: `bot/handlers/search.py`
- Ingest и обработка загруженного файла: `bot/handlers/ingest.py`
- NLP/agent-команды: `bot/handlers/agent_command.py` + `bot/services/text_formatters.py`
- HTTP-контракты с backend API: `api_client.py`

## Как добавить новую функцию без поломок

Рекомендуемый порядок:

1. Добавить кнопку и/или новое состояние в `bot/constants.py`.
2. Реализовать хендлер в соответствующем файле `bot/handlers/*` (или создать новый модуль по фиче).
3. Подключить хендлер в `bot/application.py` (entry point/state/fallback).
4. Если нужен новый API-вызов, добавить метод в `api_client.py`.
5. Проверить пользовательский поток вручную в Telegram.

## Логи и диагностика

- Логи пишутся и в консоль, и в `logs/bot.log`.
- `bot/handlers/common.py` логирует входящие апдейты до обработки бизнес-хендлеров (группа `-1`).
- Ошибки API для пользователя унифицированы через `bot/services/errors.py`.

## Команды запуска и проверки

Запуск:

```bash
python bot.py
```

Проверка синтаксиса:

```bash
python -m compileall bot.py bot
```
