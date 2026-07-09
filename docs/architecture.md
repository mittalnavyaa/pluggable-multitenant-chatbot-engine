# Architecture

High-level architecture of the Envoy pluggable multi-tenant chatbot engine.

---

## System Overview

```
┌──────────────────────────────────────────────────────────────────────────┐
│  Customer Website (any domain)                                           │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  <envoy-chatbot> Web Component                                  │    │
│  │  (@envoy/chatbot-ui)                                            │    │
│  │                                                                 │    │
│  │  • Shadow DOM isolated                                          │    │
│  │  • Fetches branding on mount                                    │    │
│  │  • Sends messages via fetch()                                   │    │
│  │  • Reads SSE streaming responses                                │    │
│  └─────────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────────┘
                              │
                              │  HTTP (browser → host server)
                              ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  Customer Host Server (Express / FastAPI / any framework)                │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  @envoy/chatbot-backend-sdk middleware                          │    │
│  │                                                                 │    │
│  │  • Validates request payload                                    │    │
│  │  • Signs request with HMAC-SHA256                               │    │
│  │  • Injects X-Envoy-* security headers                           │    │
│  │  • Forwards to core backend                                     │    │
│  │  • Pipes SSE stream back to browser                             │    │
│  └─────────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────────┘
                              │
                              │  HTTPS + HMAC-signed headers (server → server)
                              ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  Core Backend (apps/central-hub-backend)                                 │
│                                                                          │
│  FastAPI ──▶ Auth Middleware ──▶ Chat Router ──▶ RAG Pipeline            │
│                                                        │                 │
│                                              ┌─────────┴──────────┐     │
│                                              ▼                    ▼     │
│                                         Qdrant               Groq LLM   │
│                                      (vector store)         (generation) │
│                                              │                    │     │
│                                              └─────────┬──────────┘     │
│                                                        ▼                 │
│                                              SSE stream response         │
│                                                                          │
│  PostgreSQL ── Product registry, bot settings, document metadata         │
│  Redis      ── Celery task queue, session cache                          │
│  MinIO      ── Raw document file storage                                 │
│  Celery     ── Async document processing workers                         │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Package Architecture

### `@envoy/chatbot-ui`

The frontend widget. A single Web Component that can be embedded in any website.

Key files:
- `src/index.ts` — `EnvoyChatbot` class extending `HTMLElement`
- `src/branding/branding-store.ts` — Fetches and caches branding config
- `src/branding/branding-validator.ts` — Validates and sanitizes branding data
- `src/branding/css-variable-mapper.ts` — Maps branding to CSS custom properties

Build output: `dist/chatbot-ui.js` (UMD bundle, self-contained with styles)

### `@envoy/chatbot-backend-sdk`

The Node.js proxy SDK. Installed in the customer's host server.

Key files:
- `src/sdk.ts` — `ChatbotSDK` class, validates options, exposes client and middleware
- `src/middleware/index.ts` — Express-compatible middleware (validate, sign, proxy)
- `src/client/index.ts` — HTTP client with retry and timeout logic
- `src/utils/crypto.ts` — HMAC-SHA256 signing and verification

### `@envoy/shared-contracts`

Shared TypeScript interfaces and validation logic used by all layers.

Key files:
- `src/types/index.ts` — `ChatRequest`, `ChatResponse`, `StreamingChunk`, `WidgetBrandingConfig`, etc.
- `src/validation/index.ts` — `PayloadValidator` class
- `API_SPECIFICATION.md` — Authoritative API reference

### `@envoy/security`

Standalone cryptographic utilities for zero-trust server-to-server verification.

Key files:
- `src/canonical-request/index.ts` — Deterministic request serialization
- `src/signing/index.ts` — HMAC-SHA256 signature generation
- `src/verification/index.ts` — Signature verification with replay attack prevention

---

## Multi-Tenancy Model

Each customer product is a **tenant** identified by a `product_id`.

```
internal_products table
├── id (UUID)
├── product_id (string, e.g. "tensor", "admissions")
├── product_name
├── ui_theme_config (JSONB — branding configuration)
└── internal_service_token_hash
```

Tenant isolation is enforced at every layer:
- Widget: `data-bot-id` attribute identifies the tenant
- SDK: `productId` option is injected into every request header
- Core backend: Qdrant queries are filtered by `product_id` payload field
- Security: Signature verification asserts tenant ID matches payload

---

## Security Model

```
Browser (untrusted zone)
  └── Widget sends plain HTTP requests
  └── No API keys or secrets in browser

Host Server (trusted zone)
  └── SDK injects X-Envoy-API-Key
  └── SDK computes HMAC-SHA256 signature
  └── SDK injects X-Envoy-Signature, X-Envoy-Timestamp, X-Envoy-Nonce

Core Backend (trusted zone)
  └── Verifies timestamp is within 5-minute window
  └── Verifies nonce has not been used before (replay prevention)
  └── Verifies HMAC signature using constant-time comparison
  └── Rejects any request that fails verification
```

See `packages/security/SECURITY_SPECIFICATION.md` for the full cryptographic specification.

---

## Request Flow

1. Browser widget sends `GET /api/v1/products/:botId` → host server returns branding
2. User sends message → widget calls `GET /api/v1/chat/stream?bot_id=...&prompt=...`
3. Host server SDK middleware validates payload
4. SDK signs request with HMAC-SHA256 and injects security headers
5. SDK forwards signed request to core backend
6. Core backend verifies signature
7. Core backend queries Qdrant for relevant document chunks
8. Core backend calls LLM with context + user prompt
9. LLM response streams back as SSE chunks
10. SDK pipes SSE stream back to browser
11. Widget renders each token as it arrives

---

## Data Flow

```
User prompt
    │
    ▼
Widget (browser)
    │  plain HTTP
    ▼
Host Server SDK
    │  HMAC-signed HTTP
    ▼
Core Backend
    │
    ├──▶ PostgreSQL (product config, session data)
    ├──▶ Qdrant (vector similarity search → relevant chunks)
    └──▶ LLM API (generate response from chunks + prompt)
              │
              ▼
         SSE stream
              │
    ◀─────────┘
Host Server (pipes stream)
    │
    ◀─────────
Widget (renders tokens)
```
