# Internal Dashboard Frontend

## Purpose

This folder contains the frontend-only layout for the internal multi-product AI chatbot management dashboard. It does not connect to backend APIs yet and does not modify backend, document-processing, or ingestion code.

The dashboard is built for enterprise-owned products:

| Product |
| --- |
| Tensor |
| Admissions Portal |
| Internal Support |
| HR Portal |
| Placement Cell |
| Website Analyzer |
| Knowledge Base |

## Folder Structure

| Path | Purpose |
| --- | --- |
| `DashboardApp.jsx` | Main dashboard composition and page routing state |
| `index.js` | Public exports for embedding the dashboard into an application shell |
| `components/` | Reusable presentation components |
| `pages/` | Page-level layouts for each dashboard route |
| `layouts/` | Shared dashboard shell layout |
| `hooks/` | Frontend data access boundary for current layout data and future API integration |
| `types/` | JSDoc typedefs for branding and status models |
| `styles/` | Dashboard CSS for responsive enterprise UI styling |
| `uploads/README.md` | Upload pipeline module analysis, API fallback notes, and polling documentation |

## Components

| Component | Role |
| --- | --- |
| `Sidebar` | Primary navigation for dashboard pages |
| `TopNavbar` | Page title and global search placement |
| `StatsCard` | Operational metric display |
| `ProductCard` | Product summary with status, logo, theme preview, created date, and details action |
| `ThemePreview` | Visual preview of `branding_config` colors, typography, labels, and welcome message |
| `StatusBadge` | Consistent status treatment for products, services, tokens, and embeddings |
| `KeyCard` | Masked API key lifecycle card with rotate, disable, and generate actions |
| `BrandForm` | Branding editor layout for JSONB-backed fields |
| `SettingsCard` | Infrastructure and runtime setting summary |
| `DocumentTable` | Uploaded and markdown document inventory |
| `SearchBar` | Accessible search input used across pages |
| `Pagination` | Standard pagination controls |
| `Breadcrumb` | Page location context |
| `components/upload/*` | Drag-and-drop upload, upload cards, pipeline tracker, timeline, progress, history, loading, empty, retry, and details modal components |

## Pages

| Page | Role |
| --- | --- |
| `Dashboard` | Shows total products, active products, inactive products, uploaded documents, markdown files, recent activity, Qdrant status, PostgreSQL status, and LLM status |
| `Products` | Displays product cards with status, product name, theme preview, widget title, logo, created date, and details action |
| `ProductDetails` | Shows product information, branding JSON, service token status, theme preview, and widget preview |
| `Branding` | Provides editable fields for primary color, accent color, background, text, font, widget title, launcher label, welcome message, logo, border radius, spacing, and preview |
| `Uploads` | Provides drag-and-drop multi-file upload, local validation, retry/remove actions, mock upload submission, live pipeline polling, status timeline, processing logs, and upload history |
| `ApiKeys` | Displays masked key records only; plaintext service tokens are never shown |
| `Documents` | Lists uploaded files, markdown files, chunk count, embedding status, upload date, owner, and classification |
| `Settings` | Shows Database, Qdrant, LLM, Storage, Environment, and System Version cards |

## Future Backend API Connection

`hooks/useEnterpriseDashboardData.js` is the current data boundary. Future API integration should replace the internal arrays in that hook with authenticated calls to central hub backend endpoints.

Expected future mappings:

| UI Data | Future Source |
| --- | --- |
| Products | `internal_products` records |
| Branding | `internal_products.branding_config` |
| API key status | Token management endpoint that returns masked key metadata only |
| Documents | Document ingestion and markdown output metadata |
| Embedding status | Qdrant ingestion status and document-processing state |
| Settings | Health endpoints for PostgreSQL, Qdrant, LLM gateway, storage, and runtime environment |

Plaintext API keys must never be returned to this dashboard. Generate and rotate flows should display a newly generated secret only once in a secured administrative workflow, then store only a hash server-side.

## Upload Pipeline Module

The upload pipeline implementation lives in `pages/Uploads.tsx`, `components/upload/`, `hooks/useUpload.ts`, `hooks/usePipeline.ts`, `hooks/usePolling.ts`, `services/uploadService.ts`, `services/pipelineService.ts`, `types/upload.ts`, and `styles/upload.css`.

Repository inspection found no implemented backend multipart upload endpoint, no polling/status endpoint, no MinIO/S3 integration, and no worker queue. The module therefore attempts future endpoints first and automatically falls back to mock services:

| Service | Future Endpoint | Current Behavior |
| --- | --- | --- |
| `uploadService.ts` | `POST /uploads` | Validates files and creates a mock `job_id` if the endpoint is unavailable |
| `pipelineService.ts` | `GET /uploads/{job_id}` | Polls the endpoint and simulates pipeline state if unavailable |

Polling stops when a job reaches `ready`, `failed`, or `cancelled`. The UI states align with the current document-processing pipeline: text extraction, AI formatting through `MarkdownSanitizer`, Markdown generation, and ready-for-future-embedding output.

## Branding JSON Consumption

Every product has a `branding` object matching the PostgreSQL JSONB schema documented in `docs/company-branding-schema.md`.

The UI consumes these fields directly:

| JSONB Field | UI Usage |
| --- | --- |
| `primaryColor` | Logo mark, widget header, primary brand accents |
| `secondaryColor` | Theme palette preview |
| `accentColor` | Theme palette preview and secondary accents |
| `backgroundColor` | Theme preview background |
| `surfaceColor` | Widget and panel surfaces |
| `textColor` | Primary preview text |
| `mutedTextColor` | Supporting text |
| `successColor`, `warningColor`, `errorColor` | Future status token mapping |
| `fontFamily` | Editable branding field and future widget typography |
| `widgetTitle` | Product cards, theme preview, and widget preview |
| `launcherLabel` | Theme preview launcher label |
| `welcomeMessage` | Theme preview and widget preview |
| `logoUrl` | Product logo metadata |
| `borderRadius` | Theme preview and widget preview shape |
| `spacing` | Editable layout token |

Products customize only values inside the approved schema. They should not rename fields, remove required fields, or introduce product-specific alternatives without first updating the shared schema documentation and validation rules.

## PostgreSQL JSONB to UI Mapping

`internal_products.branding_config` should be returned by future product APIs as a JSON object. The dashboard should pass that object into `ThemePreview`, `BrandForm`, `ProductCard`, and `ProductDetails`.

Recommended API shape:

```json
{
  "product_id": "admissions",
  "product_name": "Admissions Portal",
  "is_active": true,
  "branding_config": {
    "primaryColor": "#0F766E",
    "accentColor": "#F59E0B",
    "widgetTitle": "Admissions Help Desk",
    "launcherLabel": "Open Admissions Help Desk"
  }
}
```

The frontend should normalize backend snake_case fields to component-friendly names at the hook boundary, keeping components simple and reusable.
