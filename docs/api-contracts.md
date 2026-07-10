# API Contracts

This document is the developer-facing summary of the API contracts used across
the Envoy platform. The authoritative machine-readable specification lives in
`packages/shared-contracts/API_SPECIFICATION.md`.

---

## Overview

All communication between the widget, host server, and core backend follows
these contracts. The TypeScript interfaces are defined in
`packages/shared-contracts/src/types/index.ts` and are shared across all layers.

---

## Endpoints

### `GET /api/v1/products/:productId`

Fetches branding configuration for a product. Called by the widget on startup.

**Request:**

```
GET /api/v1/products/tensor
```

**Response (`200 OK`):**

```json
{
  "id": "tensor",
  "product_id": "tensor",
  "name": "Tensor Assistant",
  "ui_theme_config": {
    "colors":       { "primaryColor": "#2563EB", ... },
    "typography":   { "fontFamily": "Inter, sans-serif", ... },
    "layout":       { "chatWidth": "380px", "chatHeight": "520px", ... },
    "assets":       { "companyLogo": "", ... },
    "content":      { "widgetTitle": "Tensor Assistant", "welcomeMessage": "...", ... },
    "featureFlags": { "streamingResponses": true, "conversationHistory": true, ... }
  },
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-01-01T00:00:00Z"
}
```

---

### `POST /api/v1/chat`

Sends a chat message. Returns a complete bot response (non-streaming).

**Request body (`ChatRequest`):**

```json
{
  "bot_id":          "tensor",
  "conversation_id": "conv_a1b2c3",
  "prompt":          "How do I sync the knowledge base?",
  "stream":          false,
  "metadata":        {}
}
```

**Response body (`ChatResponse`):**

```json
{
  "success": true,
  "message": {
    "id":              "msg_8f8a12bc",
    "conversation_id": "conv_a1b2c3",
    "sender":          "bot",
    "text":            "To synchronize the knowledge base...",
    "timestamp":       "2025-01-01T10:45:00Z"
  }
}
```

---

### `GET /api/v1/chat/stream`

Streams a bot response as Server-Sent Events.

**Request:**

```
GET /api/v1/chat/stream?bot_id=tensor&prompt=Hello
```

**Response (`text/event-stream`):**

```
data: {"event":"text","text":"Hello"}

data: {"event":"text","text":" there"}

data: {"event":"done","message_id":"msg_123"}
```

**Chunk types (`StreamingChunk`):**

| Type | Shape | Meaning |
| :--- | :--- | :--- |
| `StreamingTextChunk` | `{"event":"text","text":"..."}` | A token of the response |
| `StreamingDoneChunk` | `{"event":"done","message_id":"..."}` | Stream complete |
| `StreamingErrorChunk` | `{"event":"error","error":"..."}` | Stream error |

---

### `GET /health`

Health check endpoint.

**Response:**

```json
{
  "status": "healthy",
  "timestamp": "2025-01-01T10:45:00Z",
  "version": "1.0.0"
}
```

---

## Required HTTP Headers

Headers injected by the Backend SDK on every proxied request to the core backend:

| Header | Required | Description |
| :--- | :--- | :--- |
| `Content-Type` | Yes | `application/json` (or `text/event-stream` for SSE) |
| `X-Envoy-API-Key` | Yes | Platform API key |
| `X-Envoy-Product-ID` | Yes | Tenant product ID |
| `X-Envoy-Signature` | Yes | HMAC-SHA256 signature of the request payload |
| `X-Envoy-Timestamp` | Yes | Unix epoch milliseconds. Must be within 5 minutes of server time. |
| `X-Envoy-Nonce` | Yes | 16-byte random hex. Each nonce can only be used once. |
| `X-Correlation-ID` | No | Optional trace ID for request lifecycle logging |

---

## Error Response Schema (`APIErrorResponse`)

All errors across all services use this unified structure:

```json
{
  "success": false,
  "error": {
    "code":           "BAD_REQUEST",
    "message":        "Parameter 'prompt' is required.",
    "details":        { "parameter": "prompt" },
    "correlation_id": "req-trace-91b3-abc",
    "timestamp":      "2025-01-01T10:45:00Z",
    "retryable":      false
  }
}
```

**Error codes:**

| Code | HTTP Status | Meaning |
| :--- | :--- | :--- |
| `BAD_REQUEST` | 400 | Missing or invalid request parameter |
| `UNAUTHORIZED` | 401 | Missing or invalid signature headers |
| `FORBIDDEN` | 403 | Signature verification failed |
| `NOT_FOUND` | 404 | Product or resource not found |
| `TIMEOUT` | 504 | Gateway timeout connecting to core backend |
| `SERVICE_UNAVAILABLE` | 503 | Core backend is unreachable |

---

## TypeScript Interfaces

All interfaces are exported from `@envoy/shared-contracts`:

```typescript
import {
  ChatRequest,
  ChatResponse,
  ChatMessage,
  StreamingChunk,
  StreamingTextChunk,
  StreamingDoneChunk,
  StreamingErrorChunk,
  WidgetInitRequest,
  WidgetInitResponse,
  WidgetBrandingConfig,
  HealthResponse,
  APIErrorResponse,
  APIErrorBlock,
} from '@envoy/shared-contracts';
```

---

## Validation

The `PayloadValidator` class in `@envoy/shared-contracts` provides runtime validation:

```typescript
import { PayloadValidator } from '@envoy/shared-contracts';

// Validate a chat request
const validated = PayloadValidator.validateChatRequest(req.body);

// Validate a widget init request
const init = PayloadValidator.validateWidgetInitRequest(req.query);

// Validate a color string
const isValid = PayloadValidator.validateColorString('#2563eb'); // true
```

---

## Sample Payloads

See `ai-mock-integration/configs/` for complete sample JSON files:

- `sample-branding.json` — Complete branding response
- `sample-chat-response.json` — JSON and SSE response shapes
- `sample-widget-config.json` — Widget configuration reference
