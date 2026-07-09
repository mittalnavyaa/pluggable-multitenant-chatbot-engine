import os
from dataclasses import dataclass, field
from typing import List

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SAMPLE_DOCUMENTS_DIR = os.path.join(BASE_DIR, "sample_documents")
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")


@dataclass
class GeneratorConfig:
    total_documents: int = 50
    random_seed: int = 42
    enabled_types: List[str] = field(default_factory=lambda: [
        "markdown", "long_document", "short_document", "table", "list",
        "code_block", "json", "yaml", "sql", "faq", "ocr_like", "multilingual",
    ])


@dataclass
class ChunkingConfig:
    chunk_size: int = 1000
    chunk_overlap: int = 200


@dataclass
class ValidationConfig:
    check_empty_chunks: bool = True
    check_chunk_size: bool = True
    check_chunk_overlap: bool = True
    check_duplicate_chunks: bool = True
    check_page_number_validation: bool = True
    check_max_chunk_size: bool = True
    check_min_chunk_size: bool = True
    check_header_preservation: bool = True
    check_markdown_preservation: bool = True
    check_table_preservation: bool = True
    check_code_block_preservation: bool = True
    check_list_preservation: bool = True
    check_unicode_preservation: bool = True
    max_chunk_size: int = 1200
    min_chunk_size: int = 10


@dataclass
class QuestionGenConfig:
    enabled: bool = True
    questions_per_chunk: int = 3
    max_chunks_per_doc: int = 5
    api_key: str = field(default_factory=lambda: os.getenv("GROQ_API_KEY", ""))
    model: str = field(default_factory=lambda: os.getenv("LLM_MODEL", "llama-3.3-70b-versatile"))
    provider: str = field(default_factory=lambda: os.getenv("LLM_PROVIDER", "groq"))
    timeout: int = field(default_factory=lambda: int(os.getenv("TIMEOUT", "60")))
    temperature: float = field(default_factory=lambda: float(os.getenv("TEMPERATURE", "0")))


@dataclass
class ReportConfig:
    json_indent: int = 2


@dataclass
class PipelineTestConfig:
    generator: GeneratorConfig = field(default_factory=GeneratorConfig)
    chunking: ChunkingConfig = field(default_factory=ChunkingConfig)
    validation: ValidationConfig = field(default_factory=ValidationConfig)
    question_gen: QuestionGenConfig = field(default_factory=QuestionGenConfig)
    report: ReportConfig = field(default_factory=ReportConfig)


DEFAULT_CONFIG = PipelineTestConfig()
