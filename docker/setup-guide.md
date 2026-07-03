## Database Setup

1. Install Docker Desktop
2. From the project root, run:

docker compose up -d

3. Verify PostgreSQL:

docker exec -it chatbot-postgres psql -U chatbot -d chatbot_db

4. Inside PostgreSQL:

\dt

Expected tables:
- internal_products
- bots
- document_registry
- bot_settings
- chat_sessions
- messages
- analytics

5. Verify Qdrant:

Open:
http://localhost:6333/dashboard

or

http://localhost:6333