# FastAPI Mock Server

A minimal Python / FastAPI server demonstrating the same integration pattern
as the Express mock server, for teams whose host application is built in Python.

---

## What This Server Does

| Responsibility | Implementation |
| :--- | :--- |
| Load environment variables | `python-dotenv` reads `.env` on startup |
| Validate chat requests | Pydantic `ChatRequest` model validates automatically |
| HMAC request signing | `sign_request()` helper reproduces the Node.js SDK algorithm in Python |
| Serve mock branding | `GET /api/v1/products/{product_id}` returns realistic branding JSON |
| Serve mock chat responses | `POST /api/v1/chat` returns a `ChatResponse` JSON object |
| Serve mock SSE streaming | `GET /api/v1/chat/stream` streams token-by-token via `StreamingResponse` |
| Interactive API docs | FastAPI auto-generates Swagger UI at `/docs` |

---

## Prerequisites

- Python 3.11 or higher
- pip

---

## Setup

```bash
# 1. Navigate to this folder
cd ai-mock-integration/fastapi-server

# 2. Create a virtual environment (recommended)
python -m venv venv

# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create your .env file
cp .env.example .env

# 5. Start the server
python app.py
```

The server starts on `http://localhost:8001`.

---

## Alternative: Start with uvicorn directly

```bash
uvicorn app:app --host 0.0.0.0 --port 8001 --reload
```

---

## Interactive API Documentation

FastAPI automatically generates interactive API docs:

```
http://localhost:8001/docs       ← Swagger UI
http://localhost:8001/redoc      ← ReDoc
```

---

## Endpoints

### `GET /health`

```bash
curl http://localhost:8001/health
```

```json
{
  "status": "healthy",
  "timestamp": "2025-01-01T00:00:00+00:00",
  "version": "1.0.0",
  "server": "envoy-mock-fastapi"
}
```

---

### `GET /api/v1/products/{product_id}`

```bash
curl http://localhost:8001/api/v1/products/tensor
```

Supported product IDs in this mock: `tensor`, `admissions`

---

### `POST /api/v1/chat`

```bash
curl -X POST http://localhost:8001/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"bot_id":"tensor","conversation_id":"conv_1","prompt":"Hello!","stream":false}'
```

```json
{
  "success": true,
  "message": {
    "id": "msg_1234567890",
    "conversation_id": "conv_1",
    "sender": "bot",
    "text": "Hello! I am the Envoy AI assistant...",
    "timestamp": "2025-01-01T00:00:00+00:00"
  }
}
```

---

### `GET /api/v1/chat/stream?bot_id=...&prompt=...`

```bash
curl -N "http://localhost:8001/api/v1/chat/stream?bot_id=tensor&prompt=Hello"
```

```
data: {"event": "text", "text": "H"}
data: {"event": "text", "text": "e"}
...
data: {"event": "done", "message_id": "msg_1234567890"}
```

---

## Using This Server With the HTML Demo

The HTML demo (`html-demo/index.html`) points to `http://localhost:3000` by default
(the Express server). To use the FastAPI server instead:

1. Start the FastAPI server on port 8001
2. Edit `html-demo/index.html` and change `data-api-base` to `http://localhost:8001`

```html
<envoy-chatbot
  data-bot-id="tensor"
  data-api-base="http://localhost:8001"
></envoy-chatbot>
```

---

## HMAC Signing in Python

The `sign_request()` function in `app.py` reproduces the same HMAC-SHA256 algorithm
used by the Node.js SDK. The canonical message format is:

```
{timestamp}.{nonce}.{payload}
```

This matches `computeSignature()` in `packages/chatbot-backend-sdk/src/utils/crypto.ts`.

---

## Environment Variables

See `.env.example` for the full list with descriptions.

| Variable | Required | Default | Description |
| :--- | :--- | :--- | :--- |
| `PORT` | No | `8001` | Server port |
| `ENVIRONMENT` | No | `development` | Environment name |
| `CHATBOT_API_KEY` | Yes | — | Platform API key |
| `CHATBOT_PRODUCT_ID` | Yes | — | Tenant product ID |
| `CHATBOT_SIGNING_SECRET` | Yes | — | HMAC signing secret |
