import os
import random
import logging
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)

SENTENCES = [
    "The chunking service splits text at paragraph boundaries.",
    "Embeddings are generated using a pre-trained language model.",
    "Each document is assigned a unique identifier before being stored.",
    "Metadata is attached to every chunk to support downstream filtering.",
    "The pipeline validates every chunk against a configurable set of rules.",
    "Configuration values are loaded from environment variables at startup.",
    "The worker queue processes jobs asynchronously to avoid blocking the API.",
    "Search results are ranked by cosine similarity to the query embedding.",
    "Authentication tokens expire after a configurable time-to-live period.",
    "Rate limiting is enforced per API key to prevent abuse.",
    "Logs are written to stdout in a structured JSON format.",
    "The health-check endpoint returns a 200 status when all dependencies are reachable.",
    "Database migrations are applied automatically on service startup.",
    "Retrieval quality is measured using precision and recall metrics.",
    "The system processes incoming requests and routes them to the appropriate handler.",
]

SECTIONS = [
    "System Overview", "Configuration", "Installation", "Deployment",
    "Monitoring", "Security", "API Reference", "Authentication",
    "Data Ingestion", "Processing Pipeline", "Storage Layer", "Query Engine",
    "Caching Strategy", "Security Model", "Observability", "Disaster Recovery",
    "Capacity Planning", "API Gateway", "Service Mesh", "CI/CD Workflow",
]

LONG_DOC_SECTIONS = [
    "Data Ingestion", "Processing Pipeline", "Storage Layer", "Query Engine",
    "Caching Strategy", "Security Model", "Observability", "Disaster Recovery",
    "Capacity Planning", "API Gateway", "Service Mesh", "CI/CD Workflow",
]


def _pick(rng: random.Random, items: list, n: int = 1):
    return [rng.choice(items) for _ in range(n)]


def _sentences(rng: random.Random, n: int) -> str:
    return " ".join(_pick(rng, SENTENCES, n))


class SyntheticDocumentGenerator:
    def __init__(self, seed: int = 42):
        self.rng = random.Random(seed)

    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #

    def generate(self, doc_type: str, index: int) -> Tuple[str, str]:
        """Return (document_id, markdown_content)."""
        method = getattr(self, f"_gen_{doc_type}", None)
        if method is None:
            raise ValueError(f"Unknown document type: {doc_type}")
        content = method(index)
        return f"{doc_type}_{index}", content

    def generate_all(self, type_counts: Dict[str, int]) -> List[Tuple[str, str]]:
        docs = []
        for doc_type, count in type_counts.items():
            for i in range(count):
                docs.append(self.generate(doc_type, i))
        return docs

    def save(self, doc_id: str, content: str, output_dir: str) -> str:
        os.makedirs(output_dir, exist_ok=True)
        path = os.path.join(output_dir, f"{doc_id}.md")
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        logger.debug("Saved %s", path)
        return path

    # ------------------------------------------------------------------ #
    #  Document type generators                                            #
    # ------------------------------------------------------------------ #

    def _gen_markdown(self, index: int) -> str:
        titles = ["System Overview", "Integration Handbook", "Developer Guide",
                  "Operations Manual", "Architecture Notes"]
        title = titles[index % len(titles)]
        sections = self.rng.sample(SECTIONS, k=min(6, len(SECTIONS)))
        lines = [f"# {title}", ""]
        for sec in sections[:3]:
            lines += [f"## {sec}", "", _sentences(self.rng, 3), "",
                      f"### {'Details' if index % 2 == 0 else 'Examples'}", "",
                      _sentences(self.rng, 2),
                      f"Use **{sec.lower()}** carefully.",
                      f"The `{sec.lower().replace(' ', '_')}_config` value must be set before starting.",
                      ""]
        return "\n".join(lines)

    def _gen_long_document(self, index: int) -> str:
        lines = [
            "# Comprehensive Technical Reference", "",
            "This document provides an exhaustive reference for all system components. "
            "It is intentionally long to exercise multi-chunk behaviour in the pipeline.",
            "",
        ]
        for sec in LONG_DOC_SECTIONS:
            lines += [f"## {sec}", "", _sentences(self.rng, 7), "",
                      _sentences(self.rng, 7), "",
                      f"### {sec} — Implementation Notes", "",
                      _sentences(self.rng, 5), ""]
        return "\n".join(lines)

    def _gen_short_document(self, index: int) -> str:
        titles = ["Quick Note", "Memo", "Summary", "Briefing"]
        title = titles[index % len(titles)]
        return f"# {title}\n\n{_sentences(self.rng, 2)}\n"

    def _gen_table(self, index: int) -> str:
        return (
            "# Data Reference Tables\n\n"
            f"{_sentences(self.rng, 2)}\n\n"
            "## Service Inventory\n\n"
            "| Service | Port | Protocol | Status |\n"
            "|---------|------|----------|--------|\n"
            "| api-gateway | 8080 | HTTP/2 | active |\n"
            "| auth-service | 9000 | gRPC | active |\n"
            "| chunking-worker | 5672 | AMQP | active |\n"
            "| vector-store | 6333 | HTTP | active |\n"
            "| postgres | 5432 | TCP | active |\n\n"
            "## Configuration Keys\n\n"
            "| Key | Default | Required | Description |\n"
            "|-----|---------|----------|-------------|\n"
            "| `CHUNK_SIZE` | 1000 | No | Maximum characters per chunk |\n"
            "| `CHUNK_OVERLAP` | 200 | No | Overlap window in characters |\n"
            "| `GROQ_API_KEY` | — | Yes | API key for Groq LLM provider |\n"
            "| `LLM_MODEL` | llama-3.3-70b-versatile | No | Model identifier |\n"
            "| `LOG_LEVEL` | INFO | No | Logging verbosity |\n"
        )

    def _gen_list(self, index: int) -> str:
        features = [
            "MinIO object storage", "Celery async task queue",
            "PostgreSQL metadata persistence", "Markdown chunking with sliding-window overlap",
            "Vector embedding generation", "Document ingestion via REST API",
            "Qdrant vector store integration", "JWT-based authentication",
        ]
        self.rng.shuffle(features)
        chosen = features[:5]
        intro = _sentences(self.rng, 2)
        items = "\n\n".join(f"- {f}" for f in chosen)
        return (
            f"# Feature Checklist\n\n{intro}\n\n"
            "## Completed Features\n\n"
            f"{items}\n\n"
            "## Pending Tasks\n\n"
            "1. Implement rate limiting\n\n"
            "2. Add OpenTelemetry tracing\n\n"
            "3. Write integration tests\n\n"
            "4. Set up staging environment\n\n"
            "## Sub-feature Breakdown\n\n"
            "- Chunking\n"
            "  - Paragraph splitting\n"
            "  - Overlap window\n"
            "  - Page detection\n\n"
            "- Validation\n"
            "  - Size checks\n"
            "  - Header preservation\n"
            "  - Unicode safety\n"
        )

    def _gen_code_block(self, index: int) -> str:
        return (
            "# Code Examples\n\n"
            "The following snippets demonstrate common integration patterns.\n\n"
            "## Python — Chunking Service\n\n"
            "```python\n"
            "from src.services.chunking_service import ChunkingService\n\n"
            "service = ChunkingService(chunk_size=1000, chunk_overlap=200)\n"
            "chunks = service.chunk_markdown(markdown_text)\n"
            "for chunk in chunks:\n"
            "    print(chunk['text'][:80], chunk['page_number'])\n"
            "```\n\n"
            "## SQL — Schema Definition\n\n"
            "```sql\n"
            "CREATE TABLE document_registry (\n"
            "    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),\n"
            "    bot_id      UUID NOT NULL REFERENCES bots(id),\n"
            "    filename    TEXT NOT NULL,\n"
            "    status      TEXT NOT NULL DEFAULT 'PENDING',\n"
            "    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()\n"
            ");\n"
            "```\n\n"
            "## JSON — API Payload\n\n"
            "```json\n"
            '{\n'
            '  "document_id": "d1e2f3a4-b5c6-7890-abcd-ef1234567890",\n'
            '  "status": "COMPLETED",\n'
            '  "chunks": 12,\n'
            '  "page_count": 3\n'
            '}\n'
            "```"
        )

    def _gen_json(self, index: int) -> str:
        return (
            "# API Response Schema\n\n"
            "The service returns the following JSON structure on success.\n\n"
            "```json\n"
            "{\n"
            '  "job_id": "550e8400-e29b-41d4-a716-446655440000",\n'
            '  "status": "QUEUED",\n'
            '  "document": {\n'
            '    "filename": "handbook.pdf",\n'
            '    "size_bytes": 204800,\n'
            '    "hash": "sha256:abcdef1234567890"\n'
            "  },\n"
            '  "pipeline": {\n'
            '    "chunk_size": 1000,\n'
            '    "chunk_overlap": 200,\n'
            '    "total_chunks": null\n'
            "  }\n"
            "}\n"
            "```"
        )

    def _gen_yaml(self, index: int) -> str:
        return (
            "# Service Configuration\n\n"
            "Copy the block below into your `.env` or `config.yaml`.\n\n"
            "```yaml\n"
            "app:\n"
            "  name: central-hub-backend\n"
            "  version: 1.0.0\n"
            "  log_level: INFO\n\n"
            "chunking:\n"
            "  chunk_size: 1000\n"
            "  chunk_overlap: 200\n\n"
            "llm:\n"
            "  provider: groq\n"
            "  model: llama-3.3-70b-versatile\n"
            "  temperature: 0\n"
            "  timeout: 60\n\n"
            "database:\n"
            "  host: localhost\n"
            "  port: 5432\n"
            "  name: chatbot_db\n"
            "```"
        )

    def _gen_sql(self, index: int) -> str:
        return (
            "# Database Schema\n\n"
            "The following DDL and DML statements initialise the core tables.\n\n"
            "```sql\n"
            "-- Bots table\n"
            "CREATE TABLE bots (\n"
            "    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),\n"
            "    name       TEXT NOT NULL UNIQUE,\n"
            "    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()\n"
            ");\n\n"
            "-- Document registry\n"
            "CREATE TABLE document_registry (\n"
            "    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),\n"
            "    bot_id            UUID NOT NULL REFERENCES bots(id) ON DELETE CASCADE,\n"
            "    filename          TEXT NOT NULL,\n"
            "    storage_path      TEXT NOT NULL,\n"
            "    document_hash     TEXT NOT NULL UNIQUE,\n"
            "    processing_status TEXT NOT NULL DEFAULT 'PENDING',\n"
            "    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()\n"
            ");\n\n"
            "-- Seed data\n"
            "INSERT INTO bots (name) VALUES ('support-bot'), ('sales-bot');\n\n"
            "-- Query example\n"
            "SELECT d.filename, d.processing_status, b.name AS bot_name\n"
            "FROM   document_registry d\n"
            "JOIN   bots b ON b.id = d.bot_id\n"
            "WHERE  d.processing_status = 'COMPLETED'\n"
            "ORDER  BY d.created_at DESC\n"
            "LIMIT  20;\n"
            "```"
        )

    def _gen_faq(self, index: int) -> str:
        qa_pool = [
            ("What happens if chunking fails?",
             "The Celery worker marks the document status as `FAILED` and logs the error. "
             "The document can be resubmitted via the API."),
            ("What is the default chunk size?",
             "The default chunk size is 1000 characters. This can be overridden via the `CHUNK_SIZE` environment variable."),
            ("Which LLM providers are supported?",
             "Currently Groq is the only supported provider. The model defaults to "
             "`llama-3.3-70b-versatile` and can be changed via `LLM_MODEL`."),
            ("How do I run the pipeline tests?",
             "From the `apps/central-hub-backend/` directory run `python run_tests.py`. "
             "Use `--no-questions` to skip LLM calls for a fast offline run."),
            ("Is Unicode content supported?",
             "Yes. The chunker preserves all Unicode characters including CJK, Arabic, and Latin-extended scripts."),
            ("How does the overlap window work?",
             "The chunker retains the last N characters of the previous chunk at the start of the next chunk, "
             "where N is controlled by `CHUNK_OVERLAP` (default 200). "
             "This ensures context is not lost at chunk boundaries."),
            ("How are documents stored?",
             "Uploaded files are stored in MinIO object storage. "
             "Metadata and processing status are tracked in PostgreSQL."),
            ("What is the default chunk size?",
             "The default chunk size is 1000 characters. This can be overridden via the `CHUNK_SIZE` environment variable."),
        ]
        self.rng.shuffle(qa_pool)
        chosen = qa_pool[:6]
        lines = ["# Frequently Asked Questions", ""]
        for q, a in chosen:
            lines += [f"### {q}", "", a, ""]
        return "\n".join(lines)

    def _gen_ocr_like(self, index: int) -> str:
        garbled = [
            "The pipellne validates every chunk agalnst a configurable set of rules.",
            "The system processes lncomlng requests and routes tbem to tbe appropriate handler.",
            "The health-check endpolnt returns a 200 status when all dependencies are reachable.",
            "Rate limitlng is enforced per API key to prevent abuse.",
            "Logs are written to stdout ln a structured JSON format.",
            "Configuration values are loaded from environment variables at startup.",
            "Search results are ranked by coslne similarity to tbe query embeddlng.",
            "The worker queue processes jobs asynchronously to avoid blocklng tbe API.",
            "The chunklng service splits text at paragraph boundaries.",
        ]
        p1 = " ".join(self.rng.sample(garbled, k=min(5, len(garbled))))
        p2 = " ".join(self.rng.sample(garbled, k=min(3, len(garbled))))
        p3 = " ".join(self.rng.sample(garbled, k=min(3, len(garbled))))
        return (
            "SCANNED  DOCUMENT  —  PAGE  1\n\n"
            "This  is  a  simulated  OCR  extraction  from  a  scanned  PDF.\n"
            "Irregular   spacing   and   ligature   substitutions   are   common.\n\n"
            f"{p1}\n\n"
            "Page 2\n\n"
            f"{p2}\n\n"
            "Some  words  may  be  garbled:  recieve,  occured,  teh  sytem.\n"
            "Numbers  can  be  misread:  0  vs  O,  1  vs  l,  5  vs  S.\n\n"
            f"{p3}\n"
        )

    def _gen_multilingual(self, index: int) -> str:
        es_sentences = [
            "El sistema procesa documentos en múltiples idiomas.",
            "La configuración se carga desde variables de entorno al iniciar el servicio.",
            "Cada fragmento recibe un identificador único antes de ser almacenado.",
            "La calidad de recuperación se mide con métricas de precisión y exhaustividad.",
        ]
        fr_sentences = [
            "Le système traite les documents entrants et les achemine vers le gestionnaire approprié.",
            "Les valeurs de configuration sont chargées depuis les variables d'environnement au démarrage.",
            "Chaque document reçoit un identifiant unique avant d'être stocké.",
            "La qualité de récupération est mesurée à l'aide de métriques de précision et de rappel.",
        ]
        en_intro = _sentences(self.rng, 3)
        es_body = " ".join(self.rng.sample(es_sentences, k=4))
        fr_body = " ".join(self.rng.sample(fr_sentences, k=4))
        mixed = _sentences(self.rng, 3)
        return (
            "# Multilingual Content Sample\n\n"
            "This document contains paragraphs in English, Spanish, and French to verify "
            "that the chunking pipeline handles Unicode correctly.\n\n"
            f"## English\n\n{en_intro}\n\n"
            f"## Español\n\n{es_body}\n\n"
            f"## Français\n\n{fr_body}\n\n"
            f"## Mixed Summary\n\n{mixed}\n"
        )
