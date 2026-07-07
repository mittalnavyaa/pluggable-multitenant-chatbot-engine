# Central Hub Backend

## Setup

docker compose up -d

## PostgreSQL

Port: 5432

Database: chatbot_db

## Qdrant

Port: 6333

Dashboard:

http://localhost:6333/dashboard

## Celery

celery -A src.celery_app:celery_app worker --loglevel=info -P solo

## Redis

docker exec -it chatbot-redis redis-cli

## Start Backend

uvicorn src.main:app --reload
