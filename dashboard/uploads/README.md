# Upload Pipeline Module

## Repository Analysis

Before implementing this module, the repository was inspected for backend upload APIs, status APIs, storage, workers, document-processing integration, upload UI, and dashboard routing.

| Area | Finding | Implementation Decision |
| --- | --- | --- |
| Backend upload APIs | No implemented FastAPI upload endpoint was found in `apps/central-hub-backend/src`; only documentation references `POST /documents/upload` | Do not duplicate backend APIs; create frontend-ready mock upload service |
| Polling/status APIs | No implemented `GET /uploads/{job_id}` or job status endpoint was found | Create mock polling service matching the expected future API shape |
| Object storage | No MinIO or S3 client integration was found; document-processing README says object storage is not included | Keep storage out of frontend implementation |
| Async workers | No Celery, RQ, Redis, worker, or queue runtime was found; document-processing README says queues are not included | Model the pipeline as UI state only |
| Document-processing integration | `bot/document-processing` includes PDF, DOCX, TXT extraction and AI Markdown sanitization as a local pipeline | Align pipeline states with existing extraction and Markdown sanitization phases |
| Upload components | No existing upload UI components were found | Add isolated reusable upload components |
| Dashboard routing | Existing dashboard routing is local React state in `DashboardApp.jsx` and `Sidebar.jsx` | Add an `Uploads` page to the existing local route map |

## Folder Structure

| Path | Purpose |
| --- | --- |
| `components/upload/` | Upload-specific reusable UI components |
| `hooks/useUpload.ts` | File selection, validation, upload submission, retry, and active file state |
| `hooks/usePipeline.ts` | Pipeline status loading and polling orchestration |
| `hooks/usePolling.ts` | Reusable polling primitive |
| `services/uploadService.ts` | Upload API boundary with automatic mock fallback |
| `services/pipelineService.ts` | Pipeline status API boundary with automatic mock fallback |
| `types/upload.ts` | TypeScript interfaces for files, jobs, pipeline states, and API responses |
| `pages/Uploads.tsx` | Page-level composition for upload, pipeline tracking, and history |
| `styles/upload.css` | Enterprise light-theme upload module styles |
| `utils/uploadFormatting.ts` | File size and timestamp formatting helpers |

## Component Responsibilities

| Component | Responsibility |
| --- | --- |
| `DropZone` | Drag-and-drop and click-to-browse file selection |
| `UploadButton` | Standard upload action button |
| `UploadCard` | Selected file card with name, extension, size, upload time, remove, retry, and upload action |
| `UploadList` | Renders selected upload cards and empty state |
| `PipelineTracker` | Displays current step, progress, status badge, estimated time, timeline, and logs |
| `ProgressBar` | Accessible progress indicator |
| `Timeline` | Ordered visual pipeline state history |
| `StatusBadge` | Upload and pipeline status display |
| `DetailsModal` | Detailed job payload review |
| `UploadHistoryTable` | Tabular upload history |
| `RetryButton` | Retry action for failed uploads |
| `EmptyState` | Empty list messaging |
| `LoadingState` | Polling and loading feedback |

## API Integration

The services are intentionally isolated so the UI does not change when real backend APIs become available.

Expected future endpoints:

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/uploads` | Submit one or more files and return a `job_id` |
| `GET` | `/uploads/{job_id}` | Return pipeline status, progress, current step, estimate, output file, errors, logs, and timeline |

Current implementation attempts the real endpoint first. If the endpoint is unavailable, the service falls back to mock behavior.

## Mock Fallback

`uploadService.ts` creates a realistic mock job ID after validating PDF, DOCX, and TXT files.

`pipelineService.ts` simulates:

1. Queued
2. Uploading
3. Uploaded
4. Extracting Text
5. AI Formatting
6. Generating Markdown
7. Ready

The mock response follows the expected future response shape:

```json
{
  "job_id": "job_admissions-policy-2026-pdf_1783330200000",
  "status": "extracting_text",
  "progress": 56,
  "current_step": "Extracting Text",
  "estimated_time": "24 seconds",
  "output_file": null,
  "error_message": null,
  "logs": [],
  "timeline": []
}
```

## Polling Flow

`usePipeline` calls `usePolling` while a job is active. Polling stops automatically when status is:

| Terminal Status |
| --- |
| `ready` |
| `failed` |
| `cancelled` |

## Document-Processing Pipeline Connection

The frontend state machine maps directly to Nishant's existing `bot/document-processing` flow:

| UI State | Existing Pipeline Alignment |
| --- | --- |
| `extracting_text` | `ExtractorFactory` with PDF, DOCX, and TXT extractors |
| `ai_formatting` | `MarkdownSanitizer` and LLM provider |
| `generating_markdown` | `MarkdownWriter` writing clean Markdown output |
| `ready` | Markdown output is ready for future chunking and embedding |

The current frontend does not invoke the Python pipeline. A future backend worker should call the document-processing module and expose job status through `GET /uploads/{job_id}`.

## Reused Backend APIs

No implemented backend upload or polling APIs were available to reuse.

The documented `POST /documents/upload` contract in `bot/docs/api-specification.md` accepts JSON document content, not browser multipart file upload, and no FastAPI route implementation was found. This module therefore avoids duplicating it and uses isolated frontend services.

## Mock Services Created

| Service | Purpose |
| --- | --- |
| `uploadService.ts` | Validates selected files, attempts `POST /uploads`, and falls back to mock job creation |
| `pipelineService.ts` | Attempts `GET /uploads/{job_id}` and falls back to simulated pipeline status |
