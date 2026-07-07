# Architecture & Integration Audit Report

This report presents a comprehensive audit of the pluggable multi-tenant chatbot engine repository across frontend, backend, database, Celery, MinIO, Docker, and API layers.

---

## :white_check_mark: Fully Implemented

* **Object Storage Services**: `upload_file` and `download_file_to_temp` in [storage_service.py](file:///c:/Users/navya/Desktop/pluggable-multitenant-chatbot-engine/apps/central-hub-backend/src/services/storage_service.py) execute MinIO uploads/downloads and handle local filesystem temp cleanups.
* **Qdrant Initialization**: Cosine distance collection mapping and multi-tenant key payload indexes (`product_id` and `bot_id`) are idempotently configured in [qdrant_service.py](file:///c:/Users/navya/Desktop/pluggable-multitenant-chatbot-engine/apps/central-hub-backend/src/services/qdrant_service.py).
* **Ingestion Worker**: Asynchronous Celery background orchestration is wired inside [celery_app.py](file:///c:/Users/navya/Desktop/pluggable-multitenant-chatbot-engine/apps/central-hub-backend/src/celery_app.py) with automatic exponential backoff retry.
* **Extraction Engine**: Text extraction classes (`PDFExtractor`, `DOCXExtractor`, `TXTExtractor`) and automated format resolution in `ExtractorFactory` exist under `bot/document-processing/extractors/`.
* **Markdown Sanitization**: Prompt templates (`system_prompt.md`, `cleaning_prompt.md`) and completions parsing logic exist under `bot/document-processing/pipeline/`.

---

## :large_yellow_circle: Partially Implemented

* **Backend DB Models**: [bot.py](file:///c:/Users/navya/Desktop/pluggable-multitenant-chatbot-engine/apps/central-hub-backend/src/models/bot.py) and [document_registry.py](file:///c:/Users/navya/Desktop/pluggable-multitenant-chatbot-engine/apps/central-hub-backend/src/models/document_registry.py) are defined, but the other models (`internal_product.py`, `bot_settings.py`) are empty files.
* **Frontend Dashboard Pages**: Branding, Products, Keys, and Uploads pages are visually designed under `dashboard/pages/`, but they are currently hydrated with **mock hardcoded data** inside `hooks/useEnterpriseDashboardData.js`.
* **Upload Ingestion Router**: [upload.py](file:///c:/Users/navya/Desktop/pluggable-multitenant-chatbot-engine/apps/central-hub-backend/src/routers/upload.py) successfully commits records and enqueues background tasks, but has no active authentication verification.
* **Auth Middleware**: [auth.py](file:///c:/Users/navya/Desktop/pluggable-multitenant-chatbot-engine/apps/central-hub-backend/src/middleware/auth.py) exists but is fully commented out.

---

## :x: Missing Integrations

> [!WARNING]
> **1. API URL Base Route Mismatch**
> * **Frontend**: `uploadService.ts` and `pipelineService.ts` execute fetch queries targeting `/uploads` (e.g. `POST /uploads` and `GET /uploads/{jobId}`).
> * **Backend**: `upload.py` declares prefix `/api/v1/documents` (e.g. `POST /api/v1/documents/upload` and `GET /api/v1/documents/{job_id}/status`).
> * *Impact*: Frontend API calls result in HTTP 404 errors as backend prefixes do not align.

> [!WARNING]
> **2. Missing Bot ID Selection in Upload UI**
> * **Frontend**: The upload dropzone and hook (`useUpload.ts`) submit `FormData` with only the file appended. They do not pass `bot_id`.
> * **Backend**: `upload.py` expects a valid UUID query/form field `bot_id` and raises HTTP 422 Unprocessable Entity if it is omitted.

> [!WARNING]
> **3. Status Response Field Schema Mismatch**
> * **Frontend**: `usePipeline.ts` maps fields: `progress`, `current_step`, `estimated_time`, `output_file`, `logs`, and `timeline`.
> * **Backend**: `StatusResponse` (in `schemas/upload.py`) only defines `job_id` and `status`.

---

## :arrows_counterclockwise: Existing Code That Should Be Reused

* **File Storage Helpers**: [storage_service.py](file:///c:/Users/navya/Desktop/pluggable-multitenant-chatbot-engine/apps/central-hub-backend/src/services/storage_service.py) helpers for uploading and downloading objects.
* **Document Processing package**: Extractor configurations and sanitizers under `bot/document-processing`.

---

## :warning: Duplicate Implementations

None.

---

## :broom: Dead Code / Unused Files

* **Empty Database Models**: `analytics.py`, `bot_settings.py`, `chat_session.py`, `internal_product.py`, `message.py` under `apps/central-hub-backend/src/models/`.
* **Unused Config**: `vite.config.ts` (Vite dev servers are explicitly configured to run via `vite.config.mjs` in `package.json`).

---

## :memo: TODOs Already Present

* **`src/middleware/auth.py`**: JWT validation and DB token checks.
* **`src/celery_app.py`**: Downstream chunking, embedding generation, and Qdrant ingestion stages.

---

## :dart: Recommended Next Tasks (Priority Order)

1. **Route Realignment**: Update backend router prefix or Vite proxy settings to map `/uploads` to `/api/v1/documents`.
2. **Bot Context Hydration**: Add product/bot selectors in the frontend upload interface to pass `bot_id` with files.
3. **Database Models Integration**: Implement the relational DB model schemas (e.g. `InternalProduct`).
4. **Enhanced Status API Schema**: Expand `StatusResponse` in backend schemas to support `progress`, `logs`, and `timeline` data formats.
5. **Real-Data Hydration**: Replace frontend mock lists with fetch calls querying actual postgres database entries.

---

## :clipboard: Estimated Completion Percentage

* **Asynchronous Ingestion Worker**: **100%**
* **Unified End-to-End Pipeline (Dashboard to Qdrant)**: **75%**

---

## :pushpin: Suggested Git Commits

* `feat: realign upload router prefixes and proxies`
* `feat: introduce bot selection in upload user interface`
* `feat: implement internal products database entity mapping`
