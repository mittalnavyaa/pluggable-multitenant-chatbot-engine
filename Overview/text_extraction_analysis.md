# Text Extraction Utilities Analysis

This report contains a comprehensive analysis and mapping of files contributing to document parsing, raw text extraction, background celery execution, and downstream pipeline flows.

---

## Relevant Files and Code Responsibilities

### 1. `bot/document-processing/extractors/`
* **Relevance**: Core document parsing engines.
* **Files**:
  - `base_extractor.py`: Defines the class interface, logging boundaries, execution timing, and error handling.
  - `pdf_extractor.py`: Implements text extraction using `pdfplumber` with a robust fallback to `PyPDF2`.
  - `docx_extractor.py`: Implements text extraction using `python-docx` for `.docx` word files.
  - `txt_extractor.py`: Implements extraction from plain text `.txt` files.
  - `extractor_factory.py`: Determines and returns the appropriate extractor class based on file extension.
* **Responsibility**: Validate local files and extract raw text.
* **Action**: Reference/Extend when adding loaders or other document extensions.

### 2. `bot/document-processing/utils/file_validator.py`
* **Relevance**: Ingestion security.
* **Responsibility**: Checks if files exist, checks size boundaries, and validates file formats to reject malicious uploads.
* **Action**: Reference only.

### 3. `bot/document-processing/models/extraction_result.py`
* **Relevance**: Ingestion data models.
* **Responsibility**: Acts as a DTO holding parsing outcomes (`success`, `file_path`, `raw_text`, `page_count`, `processing_time`, `errors`).
* **Action**: Reference only.

### 4. `apps/central-hub-backend/src/celery_app.py`
* **Relevance**: Ingestion task queue worker.
* **Responsibility**: Runs background tasks. The worker task `process_document` acts as the coordinator that fetches files from storage and triggers the extraction engines.
* **Action**: Reference/Modify (place code inside the placeholder task to execute the parsing pipeline).

### 5. `apps/central-hub-backend/src/services/storage_service.py`
* **Relevance**: Object storage boundary.
* **Responsibility**: Interacts with MinIO. Exposes functions to stream or download file streams.
* **Action**: Reference/Modify (add `download_file` to fetch files locally for parsing).

---

## Document Ingestion & Extraction Flow

```
Manager uploads file (FastAPI endpoint /upload)
        ↓
File saved to MinIO bucket (storage_path = bot_<bot_id>/<uuid>_filename)
        ↓
Insert metadata in document_registry table (processing_status = 'QUEUED')
        ↓
Enqueue background task process_document(document_id, bot_id, storage_path)
        ↓
Celery Ingestion Worker picks up task
        ↓
Download file from MinIO to a temporary directory
        ↓
Invoke ExtractorFactory.create(local_temp_path)
        ↓
Call extractor.extract(local_temp_path) -> Returns ExtractionResult (raw text)
        ↓
Pass raw text to AI cleaning pipeline (e.g. LLM formatting)
        ↓
Generate Markdown, Chunking, Embedding, and Index in Qdrant
```

---

## Downstream AI Pipeline Integration

The downstream pipeline consumes the extracted raw text as follows:

```
Raw Document File
        ↓
Text Extraction (extractors/)
        ↓
AI Cleaning & Formatting (LLM/Regex normalizer)
        ↓
Markdown generation
        ↓
Text Chunking (splitting by headers/sections)
        ↓
Embedding Generation (generating vector representations)
        ↓
Qdrant Vector DB Ingestion (with product_id and bot_id filters)
```

---

## Error and Exception Handling

The extractors define clear custom exceptions:
* `PasswordProtectedFileError`: Caught and logged when PDFs are encrypted.
* `CorruptedFileError`: Caught and logged when files cannot be parsed.
* `UnsupportedFileTypeError`: Raised by the factory when extensions are not supported.

Failures are stored in `ExtractionResult.errors` list and logged. In a production pipeline, these errors propagate back to update `document_registry.processing_status` to `'FAILED'` with logs stored.

---

## Feature Dependency Graph

```
FastAPI Router (upload.py)
      ↓
MinIO Storage Ingest (storage_service.py)
      ↓
Postgres Metadata Record (ingestion_service.py)
      ↓
Celery Queue (celery_app.py)
      ↓
Ingestion Worker (process_document)
      ↓
Extractor Factory (extractor_factory.py)
      ↓
Document Parser (pdf/docx/txt_extractor.py)
      ↓
ExtractionResult (raw text retrieved)
      ↓
AI Pipeline / Chunking / Indexing
```

---

## Implementation Roadmap

To connect the backend queue to these extraction utilities, update/create files in this order:

1. **`apps/central-hub-backend/requirements.txt`**
   * *Purpose*: Include extraction libraries in the backend runtime.
   * *Modifications*: Add `pdfplumber`, `PyPDF2`, `python-docx`.
2. **`apps/central-hub-backend/src/services/storage_service.py`**
   * *Purpose*: Provide local file download capabilities.
   * *Modifications*: Implement `download_file_to_temp(storage_path)` to retrieve files from MinIO and write them to a local temp file.
3. **`apps/central-hub-backend/src/celery_app.py`**
   * *Purpose*: Connect the Celery worker task to the extractors.
   * *Modifications*: Integrate `ExtractorFactory` inside `process_document`, call the appropriate parser, and print or forward the extracted text to downstream functions.
