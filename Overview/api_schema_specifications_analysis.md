# API & Schema Specifications Analysis

This report contains a comprehensive analysis and mapping of files contributing to the relational database schema, Qdrant payload contracts, and API requests/response schemas.

---

## Relevant Files and Code Responsibilities

### 1. `docker/postgres/init.sql`
* **Relevance**: Source of truth for raw PostgreSQL DDL schemas.
* **Responsibility**: Defines database schema (tables, foreign keys, unique constraints, data types, indexes).
* **Defines**: Database Schema.
* **Action**: Document only.

### 2. `apps/central-hub-backend/src/models/`
* **Relevance**: Contains Python ORM mappings to Postgres.
* **Files**: `internal_product.py`, `bot.py`, `document_registry.py`.
* **Responsibility**: Maps relational tables to Python models, verifying fields and types.
* **Defines**: Database Schema.
* **Action**: Document only.

### 3. `apps/central-hub-backend/src/schemas/upload.py`
* **Relevance**: Pydantic data schemas.
* **Responsibility**: Defines serialization/deserialization DTOs (`UploadResponse` and `StatusResponse`) used by FastAPI to validate route inputs/outputs.
* **Defines**: API Schema (Request/Response models).
* **Action**: Document only.

### 4. `apps/central-hub-backend/src/routers/upload.py`
* **Relevance**: API router paths.
* **Responsibility**: Declares paths, query parameters (`bot_id`), path parameters (`job_id`), response schemas, and endpoint request methods (`POST /api/v1/documents/upload`, `GET /api/v1/documents/{job_id}/status`).
* **Defines**: API Specification & Validation Rules.
* **Action**: Document only.

### 5. `apps/central-hub-backend/src/middleware/auth.py`
* **Relevance**: Gateway interceptor.
* **Responsibility**: Validates request headers (`X-Internal-Service-Token`), maps active states, and attachment of scoped product context.
* **Defines**: Authentication Contract & Error Responses.
* **Action**: Document only.

### 6. `bot/docs/`
* **Relevance**: Core architectural specification folders.
* **Files**:
  - `database-schema.md`: Documents relational schema layout.
  - `qdrant-payload-schema.md`: Documents Qdrant metadata schema parameters (`product_id`, `bot_id`, etc.).
  - `request-response-contracts.md`: Defines frontend/backend communication parameters and payload specifications.
  - `api-specification.md`: Documents API routes and HTTP codes.
* **Defines**: Documentation, Metadata Contracts, and API Contracts.
* **Action**: Reference only (gaps to be addressed during documentation compilation).

---

## API Router & Endpoint Specifications

### 1. File Ingest Endpoint
* **Path**: `/api/v1/documents/upload`
* **HTTP Method**: `POST`
* **Request Payload**: Multipart Form data: `file: UploadFile`, `bot_id: str` (form field or query parameter).
* **Response Payload**: `UploadResponse` (`job_id: str`, `status: str`).
* **Authentication**: Service token required in headers (`X-Internal-Service-Token`).
* **Validations**: Valid UUID or string (resolved to deterministic UUID); file stream extraction.

### 2. Status Inquiry Endpoint
* **Path**: `/api/v1/documents/{job_id}/status`
* **HTTP Method**: `GET`
* **Path Parameter**: `job_id: str` (source UUID).
* **Response Payload**: `StatusResponse` (`job_id: str`, `status: str`).
* **Authentication**: Implicit or session context (depends on design).
* **Validations**: Valid UUID format check.

---

## Qdrant Metadata & Vector Schema

The Qdrant metadata schema specifies how embedded document chunks are stored:

* **Collection Name**: `internal_chatbot_documents`
* **Distance Metric**: `Cosine`
* **HNSW Configuration**: `m=0`, `payload_m=16`
* **Payload Fields**:
  - `product_id`: `keyword` type, marked `is_tenant=True` (tenant clustering).
  - `bot_id`: `keyword` type, marked `is_tenant=True` (subgraph partition).
  - `document_id`: `keyword` type (identifies source file).
  - `source`: `keyword` type (URI or path references).
  - `title`: `text` type (source headers).
  - `created_at`: `datetime` type.
  - `chunk_index`: `integer` type.

---

## Authentication Contract Flow

```
@company-scope/chatbot-backend-sdk
        ↓ (appends X-Internal-Service-Token header)
FastAPI Routing (main.py)
        ↓
Auth Middleware intercept (auth.py)
        ↓ (hashes token & verifies in postgres registry)
RAG Ingestion / Retrieval Engine (passes request.state.product_id context)
```

---

## Feature Dependency Graph

```
Backend SDK (client.js)
      ↓
API Router (upload.py)
      ↓
Request Schema (Pydantic validator)
      ↓
Authentication Middleware (auth.py)
      ↓
PostgreSQL Registry (internal_products table lookup)
      ↓
RAG Engine (with resolved product_id context)

               +

Ingestion Workflow (ingestion_service.py)
      ↓
Qdrant Metadata Schema (qdrant_service.py)
      ↓
HNSW & Payload index (is_tenant=True)
      ↓
Vector Database (qdrant_client)
```

---

## Documentation Compilation Roadmap

To generate final specifications, extract info from the following source files:

1. **Relational Database Dictionary**
   * *Sources*: `docker/postgres/init.sql`, `src/models/*.py`, `bot/docs/database-schema.md`.
2. **API Specification & Request/Response Models**
   * *Sources*: `src/routers/upload.py`, `src/schemas/upload.py`, `bot/docs/api-specification.md`.
3. **Authentication Contract**
   * *Sources*: `src/middleware/auth.py`, `bot/docs/security.md`, `bot/docs/request-response-contracts.md`.
4. **Qdrant Metadata Contract**
   * *Sources*: `src/services/qdrant_service.py`, `bot/docs/qdrant-payload-schema.md`.
5. **Configuration Schema & Settings**
   * *Sources*: `src/init_qdrant.py`, `src/database/database.py`, `src/celery_app.py`, `.env.example`.
