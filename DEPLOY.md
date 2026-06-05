# Деплой Telegram-бота на Ubuntu 24.04 через Docker и GitHub Actions

Схема такая же, как у `stal-analogs-storage`:

1. GitHub Actions собирает Docker image.
2. Image публикуется в GitHub Container Registry: `ghcr.io/<owner>/<repo>`.
3. Workflow подключается к серверу по SSH.
4. На сервере запускается `docker compose pull && docker compose up -d`.

Секреты бота (`TELEGRAM_BOT_TOKEN`, `API_TOKEN`) хранятся только на сервере в `.env`.

Список разрешённых пользователей (`TELEGRAM_ALLOWED_USER_IDS`) задаётся в GitHub Secret и при каждом деплое автоматически записывается в `.env` на сервере. Бот отклоняет все запросы от Telegram-пользователей, чей numeric `user_id` не входит в этот список.

## 1. Подготовить сервер

Если сервер уже подготовлен для `stal-analogs-storage`, Docker и пользователь `deploy` у вас, скорее всего, уже есть. Тогда переходите сразу к разделу 2.

Для нового сервера подключитесь к Ubuntu 24.04:

```bash
ssh root@YOUR_SERVER_IP
```

Поставьте Docker:

```bash
apt update && apt upgrade -y
apt install -y ca-certificates curl gnupg ufw
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu noble stable" > /etc/apt/sources.list.d/docker.list
apt update
apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
systemctl enable --now docker
```

Создайте пользователя для деплоя:

```bash
adduser deploy
usermod -aG docker deploy
mkdir -p /home/deploy/.ssh
nano /home/deploy/.ssh/authorized_keys
chown -R deploy:deploy /home/deploy/.ssh
chmod 700 /home/deploy/.ssh
chmod 600 /home/deploy/.ssh/authorized_keys
```

В `authorized_keys` вставьте публичный SSH-ключ, приватную часть которого добавите в GitHub Secret `SSH_KEY`.

## 2. Создать директорию бота

```bash
su - deploy
mkdir -p /home/deploy/stal-analogs-manager-bot
cd /home/deploy/stal-analogs-manager-bot
```

Создайте `.env`:

```bash
nano .env
```

Минимальный пример:

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_ALLOWED_USER_IDS=123456789,987654321
API_TOKEN=replace-with-the-same-token-as-storage-api
API_BASE_URL=http://stal-analogs-storage-api:8000
REQUEST_TIMEOUT_SECONDS=30
LONG_REQUEST_TIMEOUT_SECONDS=300
```

`TELEGRAM_ALLOWED_USER_IDS` в `.env` на сервере можно не заполнять вручную: при деплое workflow перезапишет это значение из GitHub Secret. Для локального запуска укажите список в `.env` сами (см. `.env.example`).

Чтобы узнать numeric `user_id` пользователя Telegram, попросите его написать боту [@userinfobot](https://t.me/userinfobot) или [@getmyid_bot](https://t.me/getmyid_bot) — в ответ придёт числовой идентификатор вида `123456789`.

Важно: бот подключается к API через docker-сеть `stal-analogs-storage` (см. `docker-compose.yml`). Сначала должен быть запущен `stal-analogs-storage` — он создаёт сеть. URL `http://stal-analogs-storage-api:8000` — это `container_name` API-контейнера, порт на хосте (`APP_HOST=127.0.0.1`) для бота не нужен.

Бот ничего сам не хранит: контекст диалога (сессии, история, прикреплённые файлы) живёт на стороне `stal-analogs-storage` (SQLite + MinIO). Бот лишь передаёт `user_id` пользователя в API и поддерживает команду `/new` для сброса контекста. Команда регистрируется автоматически на старте бота через `set_my_commands`, никаких дополнительных шагов на сервере не требуется.

## 3. Настроить GitHub Secrets

В репозитории бота откройте `Settings -> Secrets and variables -> Actions -> New repository secret` и добавьте:

```text
SSH_HOST=YOUR_SERVER_IP
SSH_USER=deploy
SSH_KEY=<private ssh key>
SSH_PORT=22
DEPLOY_PATH=/home/deploy/stal-analogs-manager-bot
TELEGRAM_ALLOWED_USER_IDS=123456789,987654321
```

`TELEGRAM_ALLOWED_USER_IDS` — обязательный secret: comma-separated список numeric Telegram user ID, которым разрешён доступ к боту. Чтобы добавить или убрать пользователя, обновите secret и запустите деплой (push в `main`/`master` или `Run workflow`).

Секреты приложения (`TELEGRAM_BOT_TOKEN`, `API_TOKEN`) в GitHub добавлять не нужно: они лежат на сервере в `.env`.

## 4. Запустить первый деплой

Смержите изменения в `main` или `master`, либо запустите workflow вручную:

```text
GitHub -> Actions -> CI/CD -> Run workflow
```

После успешного workflow проверьте сервер:

```bash
cd /home/deploy/stal-analogs-manager-bot
docker compose ps
docker compose logs -f bot
```

Если контейнер работает, но healthcheck показывает `unhealthy`, проверьте доступность backend API из контейнера:

```bash
docker compose exec bot python -c "import os, urllib.request; req=urllib.request.Request(os.environ['API_BASE_URL'].rstrip('/') + '/health', headers={'Authorization': 'Bearer ' + os.environ['API_TOKEN']}); print(urllib.request.urlopen(req, timeout=5).read().decode())"
```

Ожидаемый результат от API:

```json
{ "status": "ok", "version": "0.1.0" }
```

Также убедитесь, что в Telegram у бота появилась команда `/new` (рядом со `/start` и `/help`). Если меню команд не обновилось, перезапустите бота:

```bash
docker compose restart bot
```

Быстрый smoke-тест контекста: напишите боту что-то, потом отправьте `/new` — он должен ответить «Начат новый диалог. Прошлый контекст очищен.» После этого следующий запрос не должен ссылаться на предыдущий.

Проверка whitelist: пользователь из списка должен получать обычные ответы бота; пользователь вне списка — сообщение «У вас нет доступа к этому боту...». В логах для отказа будет строка `Доступ запрещён | user_id=...`.

## 5. Полезные команды

```bash
cd /home/deploy/stal-analogs-manager-bot
docker compose ps
docker compose logs -f bot
docker compose restart bot
docker compose pull && docker compose up -d
docker image prune -f
```

## 6. Локальная проверка Docker

На машине разработчика можно проверить сборку:

```bash
docker build -t stal-analogs-manager-bot:local .
docker compose up -d
docker compose logs -f bot
```

Перед локальным запуском через compose создайте `.env` по примеру из `.env.example`. Сначала поднимите `stal-analogs-storage` (`docker compose up -d`), затем бота. Если backend запущен на хосте без Docker, используйте `API_BASE_URL=http://host.docker.internal:8000` и добавьте в compose `extra_hosts: ["host.docker.internal:host-gateway"]`.
