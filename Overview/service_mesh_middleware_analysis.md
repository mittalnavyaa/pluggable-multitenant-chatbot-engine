# Internal Service Mesh Middleware Analysis

This report contains a comprehensive analysis and implementation plan for building the authentication middleware within the centralized chatbot backend.

---

## Relevant Files and Code Responsibilities

### 1. `apps/central-hub-backend/src/middleware/auth.py`
* **Relevance**: Houses the HTTP middleware intercepting FastAPI requests.
* **Responsibility**: Inspects request headers, extracts internal service tokens, handles hashing, validates token active statuses, and scopes product contexts.
* **Action**: Modify (currently acts as an empty stub/placeholder).

### 2. `apps/central-hub-backend/src/main.py`
* **Relevance**: Entrypoint of the central hub application.
* **Responsibility**: Registers the middleware globally using `app.middleware("http")(authenticate_request)`.
* **Action**: Reference only.

### 3. `apps/central-hub-backend/src/models/internal_product.py`
* **Relevance**: Database ORM model representing registered products.
* **Responsibility**: Maps columns such as `internal_service_token_hash` and `is_active` (status).
* **Action**: Reference only.

### 4. `apps/central-hub-backend/src/database/database.py`
* **Relevance**: Database session provider.
* **Responsibility**: Yields sessions for verifying tokens against the postgres tables.
* **Action**: Reference only.

### 5. `packages/chatbot-backend-sdk/src/client.js`
* **Relevance**: Client SDK used to issue HTTP calls.
* **Responsibility**: Attaches the necessary headers to downstream HTTP requests.
* **Action**: Reference only.

---

## Request Verification Lifecycle Flow

```
Backend SDK client call
        ↓
HTTP Request with X-Internal-Service-Token header
        ↓
FastAPI HTTP Middleware intercept (auth.py)
        ↓
Token Extraction (Header lookup)
        ↓
Compute SHA-256 / Hash value of token
        ↓
PostgreSQL Registry Lookup (internal_product model)
        ↓
Verify Product is Active (is_active == True)
        ↓
Inject Context (Attach resolved UUID to request.state.product_id)
        ↓
Allow request to proceed to RAG Engine
```

---

## Authentication Mechanism Analysis

* **Token Transmission**: Passed via the request headers using `X-Internal-Service-Token` as defined in `request-response-contracts.md`.
* **First Interceptor**: The ASGI middleware `authenticate_request` in `auth.py` intercepts requests first.
* **Framework Extension**: Extend the ASGI `http` middleware pattern.
* **Database Session Retrieval**: Instantiated per request:
  ```python
  from src.database.database import SessionLocal
  db = SessionLocal()
  try:
      # Perform lookup
  finally:
      db.close()
  ```

---

## Request Context Storage

* **Downstream Scope Context**: Resolved identities must be attached to the request state:
  ```python
  request.state.product_id = product.id
  ```
  This request state is then readable by FastAPI endpoint route functions using `request.state.product_id`.

---

## SDK Integration

* **Contract matching**: The SDK client `client.js` generates requests targeting `/api/v1/...` and must append `X-Internal-Service-Token` headers. The central backend auth filter verifies this exact header, validating service-to-service communication.

---

## Dependency Graph

```
Backend SDK Call
      ↓
HTTP Request (with X-Internal-Service-Token)
      ↓
FastAPI Router
      ↓
Authentication Middleware (auth.py)
      ↓
Token Hash Resolution (hashlib)
      ↓
PostgreSQL Query (internal_products table)
      ↓
inject context (request.state.product_id)
      ↓
RAG Ingestion / Retrieval Engine
```

---

## Implementation Roadmap

To implement the service mesh middleware, update the files in this order:

1. **`apps/central-hub-backend/src/middleware/auth.py`**
   * **Purpose**: Implement the token validation logic.
   * **Modifications**: Extract `X-Internal-Service-Token`, hash it, lookup PostgreSQL, verify product is active, and register product context in request state. Return `401` on missing/invalid tokens, and `403` if inactive.
   * **Dependencies**: `src/database/database.py` (for DB sessions) and `src/models/internal_product.py` (for database lookup).
