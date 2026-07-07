# Document Processing API Server

Exposes the `document-processing` pipeline over HTTP so the dashboard frontend
can upload files and poll live pipeline status.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/uploads` | Submit a file for processing. Returns `{ job_id, status }`. |
| `GET` | `/uploads/{job_id}` | Poll pipeline status, progress, logs, and timeline. |
| `GET` | `/uploads/{job_id}/download` | Download the finished Markdown file. |
| `GET` | `/health` | Health check. |

## Setup

### 1. Install dependencies

From inside `bot/document-processing/`:

```bash
pip install -r requirements.txt
```

### 2. Configure the LLM key

```bash
copy .env.example .env
```

Edit `.env` and set your Groq API key:

```
GROQ_API_KEY=<your-groq-api-key>
LLM_PROVIDER=groq
LLM_MODEL=llama-3.3-70b-versatile
TIMEOUT=60
TEMPERATURE=0
```

### 3. Start the server

```bash
uvicorn api:app --reload --port 8000
```

The API is now available at `http://localhost:8000`.

## Connect the dashboard

In `dashboard/.env` (copy from `.env.example`):

```
VITE_UPLOAD_API_BASE_URL=http://localhost:8000/uploads
```

Restart the Vite dev server after changing `.env`.

## Pipeline flow

```
POST /uploads  (multipart file)
    → validate extension + size
    → save to temp file
    → background thread:
        → ExtractorFactory  →  ExtractionResult  (Phase 1)
        → MarkdownSanitizer →  CleanMarkdownResult (Phase 2, Groq LLM)
        → save output/<name>.md
    → job status updated at each step

GET /uploads/{job_id}
    → returns live status, progress 0-100, logs[], timeline[]

GET /uploads/{job_id}/download
    → streams output/<name>.md when status == "ready"
```

## Pipeline statuses

| Status | Meaning |
|--------|---------|
| `queued` | Job accepted, waiting to start |
| `uploading` | File transfer in progress |
| `uploaded` | File staged for processing |
| `extracting_text` | Phase 1 — PDF/DOCX/TXT extraction |
| `ai_formatting` | Phase 2 — Groq LLM sanitization |
| `generating_markdown` | Writing output Markdown file |
| `ready` | Complete — download available |
| `failed` | Pipeline error — see `error_message` |

## Notes

- Job state is held in memory. Restarting the server clears all jobs.
- The `output/` directory is created automatically next to `api.py`.
- CORS is open (`allow_origins=["*"]`). Restrict this in production.
