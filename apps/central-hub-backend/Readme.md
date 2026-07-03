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

## Start Backend

uvicorn src.main:app --reload