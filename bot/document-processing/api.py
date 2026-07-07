"""FastAPI server exposing the document-processing pipeline to the dashboard frontend.

Endpoints
---------
POST /uploads
    Accept a file upload, validate it, run extraction + LLM sanitization in a
    background thread, and return a job_id immediately.

GET /uploads/{job_id}
    Return the current pipeline status, progress, logs, and timeline for a job.

GET /uploads/{job_id}/download
    Stream the finished Markdown file back to the caller.

Run
---
    python -m uvicorn api:app --reload --port 8000
"""

from __future__ import annotations

import re
import tempfile
import threading
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from config.settings import Settings
from extractors.extractor_factory import ExtractorFactory
from llm.base_provider import LLMAuthenticationError
from pipeline.sanitizer import MarkdownSanitizer
from pipeline.markdown_writer import MarkdownWriter
from utils.logger import get_logger

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(title="Document Processing API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = get_logger("api")

# Resolve paths relative to this file so the server works from any cwd
_BASE_DIR = Path(__file__).parent
_PROMPTS_DIR = _BASE_DIR / "prompts"
_OUTPUT_DIR = _BASE_DIR / "output"

# ---------------------------------------------------------------------------
# In-memory job store
# ---------------------------------------------------------------------------

PIPELINE_STEPS = [
    "queued",
    "uploading",
    "uploaded",
    "extracting_text",
    "ai_formatting",
    "generating_markdown",
    "ready",
]

STEP_LABELS: dict[str, str] = {
    "queued":               "Queued",
    "uploading":            "Uploading",
    "uploaded":             "Uploaded",
    "extracting_text":      "Extracting Text",
    "ai_formatting":        "AI Formatting",
    "generating_markdown":  "Generating Markdown",
    "ready":                "Ready",
    "failed":               "Failed",
    "cancelled":            "Cancelled",
}


@dataclass
class JobState:
    job_id: str
    file_name: str
    status: str = "queued"
    progress: int = 0
    current_step: str = "Queued"
    estimated_time: str = "Calculating..."
    output_file: str | None = None
    error_message: str | None = None
    logs: list[str] = field(default_factory=list)
    timeline: list[dict[str, Any]] = field(default_factory=list)
    output_path: Path | None = None


_jobs: dict[str, JobState] = {}
_jobs_lock = threading.Lock()


def _get_job(job_id: str) -> JobState | None:
    with _jobs_lock:
        return _jobs.get(job_id)


def _set_step(job: JobState, step: str, log_line: str) -> None:
    index = PIPELINE_STEPS.index(step) if step in PIPELINE_STEPS else len(PIPELINE_STEPS) - 1
    total = len(PIPELINE_STEPS) - 1
    progress = int((index / total) * 100) if step != "ready" else 100
    remaining = total - index
    estimated = "Complete" if step == "ready" else f"{max(remaining * 8, 6)} seconds"
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    for item in job.timeline:
        item_step = item["step"]
        if item_step not in PIPELINE_STEPS:
            continue
        item_index = PIPELINE_STEPS.index(item_step)
        if item_step == step:
            item["state"] = "complete" if step == "ready" else "active"
            item["timestamp"] = now_iso
        elif item_index < index:
            item["state"] = "complete"

    job.status = step
    job.progress = progress
    job.current_step = STEP_LABELS.get(step, step)
    job.estimated_time = estimated
    job.logs.append(log_line)
    logger.info("job_step", extra={"job_id": job.job_id, "step": step})


def _build_initial_timeline() -> list[dict[str, Any]]:
    return [
        {"step": s, "label": STEP_LABELS[s], "timestamp": "", "state": "pending"}
        for s in PIPELINE_STEPS
    ]


def _to_markdown_name(source_file_name: str) -> str:
    stem = Path(source_file_name).stem.strip().lower()
    cleaned = re.sub(r"[^a-z0-9]+", "_", stem).strip("_") or "document"
    return f"{cleaned}.md"


def _fail_job(job: JobState, step: str, message: str) -> None:
    job.status = "failed"
    job.progress = 0
    job.current_step = "Failed"
    job.error_message = message
    job.logs.append(f"Error: {message}")
    for item in job.timeline:
        if item["step"] == step:
            item["state"] = "failed"


# ---------------------------------------------------------------------------
# Background pipeline worker
# ---------------------------------------------------------------------------

def _run_pipeline(job_id: str, tmp_path: Path, original_name: str) -> None:
    with _jobs_lock:
        job = _jobs[job_id]

    _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    try:
        # Validate LLM config first
        try:
            settings = Settings.from_env()
            if not settings.groq_api_key:
                _fail_job(job, "ai_formatting", "GROQ_API_KEY is not set in .env")
                return
        except Exception as exc:
            _fail_job(job, "ai_formatting", f"Configuration error: {exc}")
            return

        _set_step(job, "uploading", "Source file transfer in progress.")
        _set_step(job, "uploaded", "Source file staged for document-processing pipeline.")
        _set_step(job, "extracting_text", "Extracting text from document.")

        extractor = ExtractorFactory.create(tmp_path)
        extraction_result = extractor.extract(tmp_path)

        if not extraction_result.success:
            _fail_job(job, "extracting_text", "; ".join(extraction_result.errors))
            return

        job.logs.append(
            f"Extracted {extraction_result.word_count} words, "
            f"{extraction_result.character_count} characters "
            f"from {extraction_result.page_count} page(s) "
            f"in {extraction_result.processing_time:.2f}s."
        )

        _set_step(job, "ai_formatting", "AI sanitization via Groq LLM.")

        writer = MarkdownWriter(_OUTPUT_DIR)
        try:
            sanitizer = MarkdownSanitizer(writer=writer, prompts_dir=_PROMPTS_DIR)
        except LLMAuthenticationError as exc:
            _fail_job(job, "ai_formatting", f"LLM authentication failed: {exc}")
            return

        markdown_result = sanitizer.sanitize(extraction_result)

        if not markdown_result.success:
            _fail_job(job, "ai_formatting", "; ".join(markdown_result.errors))
            return

        job.logs.append(
            f"LLM sanitization completed via {markdown_result.provider} "
            f"({markdown_result.model}) in {markdown_result.processing_time:.2f}s."
        )
        for w in markdown_result.warnings:
            job.logs.append(f"Warning: {w}")

        _set_step(job, "generating_markdown", "Writing clean Markdown output.")

        md_name = _to_markdown_name(original_name)
        output_path = _OUTPUT_DIR / md_name
        job.output_path = output_path
        job.logs.append(f"Markdown saved to output/{md_name}.")

        _set_step(job, "ready", "Markdown output is ready.")
        job.output_file = md_name

        logger.info("pipeline_completed", extra={"job_id": job_id, "output": md_name})

    except Exception as exc:
        job.status = "failed"
        job.progress = 0
        job.current_step = "Failed"
        job.error_message = str(exc)
        job.logs.append(f"Unexpected pipeline error: {exc}")
        logger.exception("pipeline_unexpected_error", extra={"job_id": job_id, "error": str(exc)})
    finally:
        try:
            tmp_path.unlink(missing_ok=True)
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.post("/uploads", status_code=202)
async def submit_upload(file: UploadFile):
    original_name = file.filename or "document"
    extension = Path(original_name).suffix.lower()

    if extension not in {".pdf", ".docx", ".txt"}:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported file type '{extension}'. Accepted: .pdf, .docx, .txt",
        )

    with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as tmp:
        content = await file.read()
        if not content:
            raise HTTPException(status_code=422, detail="Empty files cannot be uploaded.")
        tmp.write(content)
        tmp_path = Path(tmp.name)

    job_id = f"job_{uuid.uuid4().hex[:12]}"
    job = JobState(
        job_id=job_id,
        file_name=original_name,
        timeline=_build_initial_timeline(),
    )
    job.logs.append("Upload job accepted.")

    with _jobs_lock:
        _jobs[job_id] = job

    t = threading.Thread(target=_run_pipeline, args=(job_id, tmp_path, original_name), daemon=True)
    t.start()

    logger.info("job_created", extra={"job_id": job_id, "file": original_name})
    return {"job_id": job_id, "status": "queued"}


@app.get("/uploads/{job_id}")
def get_pipeline_status(job_id: str):
    job = _get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")
    return {
        "job_id": job.job_id,
        "status": job.status,
        "progress": job.progress,
        "current_step": job.current_step,
        "estimated_time": job.estimated_time,
        "output_file": job.output_file,
        "error_message": job.error_message,
        "logs": job.logs,
        "timeline": job.timeline,
    }


@app.get("/uploads/{job_id}/download")
def download_output(job_id: str):
    job = _get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")
    if job.status != "ready" or job.output_path is None:
        raise HTTPException(status_code=409, detail="Output is not ready yet.")
    if not job.output_path.exists():
        raise HTTPException(status_code=404, detail="Output file not found on disk.")
    return FileResponse(
        path=str(job.output_path),
        media_type="text/markdown",
        filename=job.output_path.name,
    )


@app.get("/health")
def health():
    return {"status": "ok"}
