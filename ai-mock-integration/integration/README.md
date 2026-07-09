# Integration Overview

This folder documents the end-to-end integration between the three layers of the
Envoy chatbot platform.

---

## The Three Layers

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: Frontend Widget                                   │
│  Package:  @envoy/chatbot-ui                                │
│  File:     packages/chatbot-ui/dist/chatbot-ui.js           │
│  Element:  <envoy-chatbot>                                  │
│  Tech:     Web Components, Shadow DOM, SSE streaming        │
└─────────────────────────────────────────────────────────────┘
                          │
                          │  HTTP requests from browser
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 2: Host Server + Backend SDK                         │
│  Package:  @envoy/chatbot-backend-sdk                       │
│  Demo:     ai-mock-integration/express-server/server.js     │
│            ai-mock-integration/fastapi-server/app.py        │
│  Tech:     Express / FastAPI, HMAC-SHA256 signing           │
└─────────────────────────────────────────────────────────────┘
                          │
                          │  Signed HTTP requests (server-to-server)
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 3: Core RAG Engine                                   │
│  App:      apps/central-hub-backend                         │
│  Tech:     FastAPI, PostgreSQL, Qdrant, Redis, Celery       │
└─────────────────────────────────────────────────────────────┘
```

---

## What Each Layer Does

### Layer 1 — Frontend Widget

The widget is a self-contained Web Component. It:

- Renders a floating launcher button and expandable chat window
- Fetches branding configuration from the host server on startup
- Applies colors, fonts, layout, and feature flags dynamically
- Sends user messages to the host server
- Reads SSE streaming responses and renders them token by token
- Fires custom events that the host page can listen to
- Stores conversation history in `localStorage`

The widget has **no knowledge of API keys, signing secrets, or the core backend**.
It only knows the host server URL.

### Layer 2 — Host Server + Backend SDK

The host server is **your application**. It sits between the browser and the core
backend. It:

- Receives chat requests from the widget
- Validates the request payload using SDK middleware
- Signs the request with HMAC-SHA256 using your signing secret
- Forwards the signed request to the core backend
- Pipes the response (or SSE stream) back to the widget

The Backend SDK handles all of this. You only need to call `createChatbotSDK()`
and register the middleware.

### Layer 3 — Core RAG Engine

The core backend is the AI engine. It:

- Verifies the HMAC signature on every incoming request
- Queries the Qdrant vector store for relevant document chunks
- Calls the LLM (Groq/Llama) to generate a response
- Streams the response back as SSE chunks

---

## Running the Full Stack Locally

### Option A — Mock servers (no Docker required)

This uses the mock Express server instead of the real core backend.
Responses are simulated but the integration pattern is identical.

```bash
# Terminal 1: Build and watch the widget
cd packages/chatbot-ui
pnpm build

# Terminal 2: Start the Express mock server
cd ai-mock-integration/express-server
npm install
cp .env.example .env
npm start

# Browser: Open the demo
http://localhost:3000
```

### Option B — Full stack with real core backend

This connects to the real AI engine.

```bash
# Terminal 1: Start all infrastructure
docker compose up -d

# Terminal 2: Build the widget
cd packages/chatbot-ui && pnpm build

# Terminal 3: Start the Express host server
cd ai-mock-integration/express-server
# Edit .env: set CHATBOT_API_BASE=http://localhost:8000
npm start

# Browser: Open the demo
http://localhost:3000
```

---

## Key Files Reference

| File | Layer | Purpose |
| :--- | :--- | :--- |
| `packages/chatbot-ui/src/index.ts` | 1 | Widget Web Component implementation |
| `packages/chatbot-ui/src/branding/branding-store.ts` | 1 | Fetches and stores branding config |
| `packages/chatbot-backend-sdk/src/sdk.ts` | 2 | SDK entry point |
| `packages/chatbot-backend-sdk/src/middleware/index.ts` | 2 | Express middleware (validate, sign, proxy) |
| `packages/chatbot-backend-sdk/src/utils/crypto.ts` | 2 | HMAC-SHA256 signing |
| `packages/shared-contracts/src/types/index.ts` | 1+2+3 | Shared TypeScript interfaces |
| `packages/security/src/verification/index.ts` | 3 | Signature verification |
| `ai-mock-integration/express-server/server.js` | 2 | Mock Express host server |
| `ai-mock-integration/fastapi-server/app.py` | 2 | Mock FastAPI host server |
| `ai-mock-integration/html-demo/index.html` | 1 | Mock website embedding the widget |

---

## Security Boundary

The security boundary is between Layer 1 and Layer 2.

```
Browser (untrusted)          │  Server (trusted)
─────────────────────────────┼──────────────────────────────
Widget sends plain requests  │  SDK signs requests with HMAC
No API keys in browser       │  API keys in environment vars
No signing secrets in browser│  Signing secrets in environment vars
```

The browser **never** sees the API key or signing secret. These are injected
server-side by the SDK middleware before forwarding to the core backend.

See `packages/security/SECURITY_SPECIFICATION.md` for the full cryptographic specification.
