# Document Processing Pipeline

## Purpose

This project contains the first two stages of an enterprise document processing pipeline:

1. **Phase 1 - Text Extraction:** extract raw text from PDF, DOCX, and TXT files.
2. **Phase 2 - AI Sanitization:** convert extracted raw text into clean, structured Markdown using an LLM provider.

The current implementation does not include embeddings, Qdrant, chunking, Redis, Celery, backend APIs, frontend code, or object storage.

## Architecture

The pipeline is intentionally modular:

- `extractors/` contains the existing Phase 1 extraction utilities.
- `llm/` contains provider abstractions and the default Groq provider.
- `prompts/` contains reusable prompt templates for Markdown cleaning.
- `pipeline/` coordinates sanitization and Markdown file writing.
- `models/` contains shared result contracts.
- `config/` loads runtime settings from environment variables and `.env`.
- `output/` stores generated Markdown files.
- `tests/` validates extraction and sanitization behavior.

## Pipeline Flow

```text
PDF/DOCX/TXT
    -> ExtractorFactory
    -> ExtractionResult.raw_text
    -> MarkdownSanitizer
    -> LLM Provider
    -> CleanMarkdownResult
    -> output/<source_file>.md
```

## Folder Structure

```text
document-processing/
├── config/
│   ├── __init__.py
│   ├── env.py
│   └── settings.py
├── exceptions/
│   ├── __init__.py
│   └── extraction_exceptions.py
├── examples/
│   └── run_extractor.py
├── extractors/
│   ├── __init__.py
│   ├── base_extractor.py
│   ├── docx_extractor.py
│   ├── extractor_factory.py
│   ├── pdf_extractor.py
│   └── txt_extractor.py
├── llm/
│   ├── __init__.py
│   ├── base_provider.py
│   ├── groq_provider.py
│   └── provider_factory.py
├── models/
│   ├── __init__.py
│   ├── clean_markdown_result.py
│   └── extraction_result.py
├── output/
│   └── README.md
├── pipeline/
│   ├── __init__.py
│   ├── markdown_writer.py
│   └── sanitizer.py
├── prompts/
│   ├── cleaning_prompt.md
│   ├── examples.md
│   └── system_prompt.md
├── tests/
│   ├── test_docx.py
│   ├── test_factory.py
│   ├── test_pdf.py
│   ├── test_prompts.py
│   ├── test_sanitizer.py
│   └── test_txt.py
├── .env.example
├── README.md
└── requirements.txt
```

## Installation

From inside `document-processing/`:

```bash
pip install -r requirements.txt
```

## Configuration

Create a `.env` file from `.env.example`:

```bash
copy .env.example .env
```

Configure the values:

```text
GROQ_API_KEY=<your-groq-api-key>
LLM_PROVIDER=groq
LLM_MODEL=llama-3.3-70b-versatile
TIMEOUT=60
TEMPERATURE=0
```

API keys must come from environment variables or `.env`. Credentials are never hardcoded.

## Supported Formats

| Format | Extension | Phase 1 Extractor |
| --- | --- | --- |
| PDF | `.pdf` | `PDFExtractor` |
| Microsoft Word | `.docx` | `DOCXExtractor` |
| Plain Text | `.txt` | `TXTExtractor` |

## Example Usage

```python
from extractors.extractor_factory import ExtractorFactory
from pipeline.sanitizer import MarkdownSanitizer

extractor = ExtractorFactory.create("employee_handbook.pdf")
extraction_result = extractor.extract("employee_handbook.pdf")

sanitizer = MarkdownSanitizer()
markdown_result = sanitizer.sanitize(extraction_result)

if markdown_result.success:
    print(markdown_result.markdown)
else:
    print(markdown_result.errors)
```

Generated Markdown is automatically saved to `output/<source_file_name>.md`.

## CleanMarkdownResult Format

```python
CleanMarkdownResult(
    success=True,
    markdown="# Leave Policy\n\nEmployees may apply...",
    processing_time=1.274211,
    provider="groq",
    model="llama-3.3-70b-versatile",
    warnings=[],
    errors=[],
)
```

## Sanitization Behavior

The LLM prompt instructs the provider to:

- Remove page numbers, repeated headers, repeated footers, scanning artifacts, OCR garbage, and unnecessary whitespace.
- Preserve original meaning and all factual information.
- Preserve headings, tables, bullet lists, numbered lists, and hierarchy where possible.
- Produce Markdown only.
- Never hallucinate, invent information, or summarize.

## Error Handling

The sanitizer returns failed `CleanMarkdownResult` objects for empty extraction results, unsuccessful extraction results, provider failures, timeouts, and invalid API keys. Provider-level errors are represented with explicit LLM exception classes.

## Testing

Run all tests from inside `document-processing/`:

```bash
python -m pytest -q
```

The Phase 2 tests use fake providers and do not call Groq. They cover normal documents, messy OCR text, repeated headers, repeated footers, large documents, empty documents, provider failures, timeouts, invalid API keys, and prompt constraints.

## Future Integration Notes

The LLM provider interface is designed so additional providers can be added later without changing the sanitizer pipeline. Future implementations can add OpenAI, Gemini, or Ollama by implementing `BaseLLMProvider` and registering the provider in `ProviderFactory`.

Downstream phases such as Markdown chunking, embeddings, Qdrant indexing, queues, APIs, and frontend integrations should consume `CleanMarkdownResult.markdown` after this phase completes.

## Running the Complete Pipeline

Run the full extraction and LLM sanitization flow with one command from inside `document-processing/`:

```bash
python -m examples.run_pipeline tests/sample_files/sample.pdf
python -m examples.run_pipeline tests/sample_files/sample.docx
python -m examples.run_pipeline tests/sample_files/sample.txt
```

The runner validates the file, selects the correct extractor through `ExtractorFactory`, prints extraction statistics, passes the `ExtractionResult` into `MarkdownSanitizer`, saves the cleaned Markdown in `output/`, prints the output path, and exits with a success or error code.

Before running LLM sanitization, configure `.env` with a valid `GROQ_API_KEY`. Use `--quiet-logs` if you want only the formatted pipeline output:

```bash
python -m examples.run_pipeline tests/sample_files/sample.txt --quiet-logs
```
