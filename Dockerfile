FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN addgroup --system appuser \
    && adduser --system --ingroup appuser --home /home/appuser appuser

COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY api_client.py config.py bot.py ./
COPY bot ./bot

RUN python -m compileall api_client.py config.py bot.py bot

RUN mkdir -p /app/logs \
    && chown -R appuser:appuser /app

USER appuser

HEALTHCHECK --interval=60s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import os, urllib.request; token=os.environ['API_TOKEN']; base=os.environ.get('API_BASE_URL', 'http://127.0.0.1:8000').rstrip('/'); req=urllib.request.Request(base + '/health', headers={'Authorization': 'Bearer ' + token}); urllib.request.urlopen(req, timeout=5).read()" || exit 1

CMD ["python", "bot.py"]
