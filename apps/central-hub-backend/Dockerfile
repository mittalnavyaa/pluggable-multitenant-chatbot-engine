FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY apps/central-hub-backend/requirements.txt /tmp/backend-requirements.txt
COPY bot/document-processing/requirements.txt /tmp/document-processing-requirements.txt

RUN pip install --upgrade pip \
    && pip install -r /tmp/backend-requirements.txt \
    && pip install -r /tmp/document-processing-requirements.txt

COPY apps/central-hub-backend /app/apps/central-hub-backend
COPY bot/document-processing /app/bot/document-processing

WORKDIR /app/apps/central-hub-backend

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
