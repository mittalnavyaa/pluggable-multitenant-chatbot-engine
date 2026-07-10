# Express Mock Server

A minimal Node.js / Express server demonstrating how to integrate the
`@envoy/chatbot-backend-sdk` into a host application backend.

---

## What This Server Does

| Responsibility | Implementation |
| :--- | :--- |
| Load environment variables | `dotenv` reads `.env` on startup |
| Initialize the Backend SDK | `createChatbotSDK()` with credentials from env vars |
| Validate chat requests | `sdk.getMiddleware().requestMiddleware` on the chat route |
| Serve mock branding | `GET /api/v1/products/:productId` returns realistic branding JSON |
| Serve mock chat responses | `POST /api/v1/chat` returns a `ChatResponse` JSON object |
| Serve mock SSE streaming | `GET /api/v1/chat/stream` streams token-by-token SSE chunks |
| Serve the HTML demo | Static file serving from `html-demo/` |

---

## Prerequisites

- Node.js 18 or higher
- The widget bundle must be built: `cd packages/chatbot-ui && pnpm build`

---

## Setup

```bash
# 1. Navigate to this folder
cd ai-mock-integration/express-server

# 2. Install dependencies
npm install

# 3. Create your .env file
cp .env.example .env

# 4. (Optional) Edit .env if you want to point at a real backend
#    The defaults work for local mock testing without any changes.

# 5. Start the server
npm start
```

The server starts on `http://localhost:3000`.

---

## Development Mode (Auto-Restart)

```bash
npm run dev
```

Uses Node's built-in `--watch` flag (Node 18+). The server restarts automatically
when `server.js` changes.

---

## Endpoints

### `GET /health`

Returns server status. Use this to verify the server is running.

```bash
curl http://localhost:3000/health
```

```json
{
  "status": "healthy",
  "timestamp": "2025-01-01T00:00:00.000Z",
  "version": "1.0.0",
  "server": "envoy-mock-express",
  "sdk_initialized": true
}
```

---

### `GET /api/v1/products/:productId`

Returns branding configuration for a product. The widget calls this on startup.

```bash
curl http://localhost:3000/api/v1/products/tensor
```

Supported product IDs in this mock: `tensor`, `admissions`

For any other ID, returns a 404 error.

---

### `POST /api/v1/chat`

Accepts a chat message and returns a bot response.
The SDK's `requestMiddleware` validates the payload before the handler runs.

```bash
curl -X POST http://localhost:3000/api/v1/chat \
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
    "timestamp": "2025-01-01T00:00:00.000Z"
  }
}
```

---

### `GET /api/v1/chat/stream?bot_id=...&prompt=...`

Streams a bot response as Server-Sent Events. The widget calls this when
`streamingResponses` is enabled in the branding feature flags.

```bash
curl -N "http://localhost:3000/api/v1/chat/stream?bot_id=tensor&prompt=Hello"
```

```
data: {"event":"text","text":"H"}
data: {"event":"text","text":"e"}
data: {"event":"text","text":"l"}
...
data: {"event":"done","message_id":"msg_1234567890"}
```

---

## How the SDK Is Integrated

```javascript
// 1. Import and instantiate
const { createChatbotSDK } = require('@envoy/chatbot-backend-sdk');
const sdk = createChatbotSDK({
  apiBase:       process.env.CHATBOT_API_BASE,
  apiKey:        process.env.CHATBOT_API_KEY,
  productId:     process.env.CHATBOT_PRODUCT_ID,
  signingSecret: process.env.CHATBOT_SIGNING_SECRET,
});

// 2. Get middleware
const middleware = sdk.getMiddleware();

// 3. Register on your route
app.post('/api/v1/chat', middleware.requestMiddleware, (req, res) => {
  // req.body.bot_id and req.body.prompt are guaranteed valid here
});
```

---

## Environment Variables

See `.env.example` for the full list with descriptions.

| Variable | Required | Default | Description |
| :--- | :--- | :--- | :--- |
| `PORT` | No | `3000` | Server port |
| `NODE_ENV` | No | `development` | Environment name |
| `CHATBOT_API_BASE` | Yes | — | Core backend URL |
| `CHATBOT_API_KEY` | Yes | — | Platform API key |
| `CHATBOT_PRODUCT_ID` | Yes | — | Tenant product ID |
| `CHATBOT_SIGNING_SECRET` | Yes | — | HMAC signing secret |
