# LLM Sanitization Prompt Architecture Analysis

This report contains a comprehensive analysis and mapping of files contributing to LLM prompts, provider integrations, sanitization workers, and Markdown conversion workflows.

---

## Relevant Files and Code Responsibilities

### 1. `bot/document-processing/prompts/`
* **Relevance**: Prompts storage directory.
* **Files**:
  - `system_prompt.md`: Implements the instruction scope for cleaning assistant rules (preserves context hierarchy, removes page numbers, footers/headers, scanners, and layout noise).
  - `cleaning_prompt.md`: Implements formatting rules, converting raw layouts into valid Markdown layout.
  - `examples.md`: Provides few-shot inline context guidelines.
* **Responsibility**: System and user prompt template resources.
* **Action**: Reference only.

### 2. `bot/document-processing/llm/`
* **Relevance**: Core LLM connectors.
* **Files**:
  - `base_provider.py`: Defines the `BaseLLMProvider` interface and custom LLM errors (`LLMProviderError`, `LLMAuthenticationError`, `LLMTimeoutError`).
  - `groq_provider.py`: Connects to Groq completions REST endpoint and parses the outputs.
  - `provider_factory.py`: Instantiates the configured provider class.
* **Responsibility**: Communicate with LLM endpoints and return normalized markdown strings.
* **Action**: Reference only.

### 3. `bot/document-processing/pipeline/`
* **Relevance**: Document formatting orchestrators.
* **Files**:
  - `sanitizer.py`: Houses the `MarkdownSanitizer` class.
  - `markdown_writer.py`: Writes cleaned Markdown output strings to files.
* **Responsibility**: Coordinate document pipeline inputs and write output results to local folders.
* **Action**: Reference only.

---

## AI Ingestion & Sanitization Trace Flow

```
Raw text extracted (via Extractors)
        ↓
Background Worker triggers sanitization task
        ↓
Load system_prompt.md & cleaning_prompt.md templates
        ↓
Submit raw text + prompts to LLM Provider (via GroqProvider)
        ↓
LLM cleans layout artifacts & converts text to structured Markdown
        ↓
Cleaned Markdown returned to Sanitizer
        ↓
Save output markdown file (via MarkdownWriter)
        ↓
Pass Markdown file to semantic chunking service
        ↓
Embed chunks & index vectors in Qdrant
```

---

## Prompt Architecture & Management

* **Storage Location**: Template files are stored under [bot/document-processing/prompts/](file:///c:/Users/navya/Desktop/pluggable-multitenant-chatbot-engine/bot/document-processing/prompts/) as static Markdown (`.md`) resources.
* **Prompt Loading**: The `MarkdownSanitizer` dynamically reads templates from file paths using `_load_prompt("file_name.md")`. This maintains a clean separation between instructions and Python logic.

---

## Configuration Settings

Settings are loaded dynamically through:
* **`model`**: Target completion model.
* **`temperature`**: Set to low values (typically `0.0` or `0.1`) to ensure strict deterministic formatting without hallucinations.
* **`timeout`**: Request duration thresholds to trigger retry logic if completions stall.

---

## Error Handling & Exception propagation

* **Custom Errors**: The sanitization pipeline handles custom LLM connection, auth, and timeout issues mapping them inside `CleanMarkdownResult.errors`.
* **Trace tracking**: Errors are captured by loggers, updating downstream database records accordingly.

---

## Feature Dependency Graph

```
Text Ingestion Task (celery_app.py)
        ↓
Markdown Sanitizer (sanitizer.py)
   │
   ├─► Load Templates (prompts/system_prompt.md)
   │
   ├─► Provider Loader (provider_factory.py)
   │         ↓
   │   Groq Client (groq_provider.py)
   │         ↓
   │   Completions Endpoint API Call
   │
   └─► Markdown Output Write (markdown_writer.py)
             ↓
       Semantic Chunking Engine
```

---

## Ingestion Pipeline Integration Roadmap

To integrate the sanitization pipeline into the background Celery ingestion workflow:

1. **`apps/central-hub-backend/src/celery_app.py`**
   * *Purpose*: Orchestrate document ingestion tasks.
   * *Modifications*: Update `process_document` task to import `MarkdownSanitizer`, run extraction, invoke `sanitize(extraction_result)`, and forward clean Markdown to chunking and Qdrant.
   * *Dependencies*: `src/services/storage_service.py` (download local copy) and `bot/document-processing/pipeline/sanitizer.py` (sanitization engine).
