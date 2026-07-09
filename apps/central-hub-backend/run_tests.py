"""
Pipeline Testing & Evaluation Framework — entry point.

Usage:
    python run_tests.py
    python run_tests.py --no-questions
    python run_tests.py --seed 123 --total 20
    python run_tests.py --types markdown faq table
"""
import argparse
import logging
import os
import sys
import time

# Allow running from the backend root without installing the package
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pipeline_testing.config import (
    DEFAULT_CONFIG, SAMPLE_DOCUMENTS_DIR, OUTPUTS_DIR,
)
from pipeline_testing.generators.doc_generator import SyntheticDocumentGenerator
from pipeline_testing.validators.chunk_validator import ChunkValidator
from pipeline_testing.validators.integrity_validator import IntegrityValidator
from pipeline_testing.evaluation.question_generator import EvaluationQuestionGenerator
from pipeline_testing.evaluation.dataset_builder import EvaluationDatasetBuilder
from pipeline_testing.reports.reporter import PipelineTestReporter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


def _distribute(total: int, types: list) -> dict:
    """Distribute total documents across types as evenly as possible."""
    base, remainder = divmod(total, len(types))
    counts = {t: base for t in types}
    for t in types[:remainder]:
        counts[t] += 1
    return counts


def _load_chunking_service(cfg):
    try:
        from src.services.chunking_service import ChunkingService
        return ChunkingService(
            chunk_size=cfg.chunking.chunk_size,
            chunk_overlap=cfg.chunking.chunk_overlap,
        )
    except ImportError:
        logger.warning("ChunkingService not importable — using fallback splitter")
        return None


def _fallback_chunk(text: str, chunk_size: int = 1000, overlap: int = 200):
    """Simple paragraph-based fallback chunker."""
    import re
    paragraphs = [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]
    chunks, buf, page = [], "", 1
    for para in paragraphs:
        if "Page " in para:
            import re as _re
            m = _re.search(r"Page (\d+)", para)
            if m:
                page = int(m.group(1))
        if len(buf) + len(para) + 2 > chunk_size and buf:
            chunks.append({"text": buf.strip(), "page_number": page})
            buf = buf[-overlap:] + "\n\n" + para
        else:
            buf = (buf + "\n\n" + para).strip() if buf else para
    if buf.strip():
        chunks.append({"text": buf.strip(), "page_number": page})
    return chunks


def run(args=None):
    parser = argparse.ArgumentParser(description="Run pipeline tests")
    parser.add_argument("--no-questions", action="store_true",
                        help="Skip LLM question generation")
    parser.add_argument("--seed", type=int, default=None,
                        help="Random seed for document generation")
    parser.add_argument("--total", type=int, default=None,
                        help="Total number of documents to generate")
    parser.add_argument("--types", nargs="+", default=None,
                        help="Document types to include")
    opts = parser.parse_args(args)

    cfg = DEFAULT_CONFIG

    if opts.seed is not None:
        cfg.generator.random_seed = opts.seed
    if opts.total is not None:
        cfg.generator.total_documents = opts.total
    if opts.types is not None:
        cfg.generator.enabled_types = opts.types
    if opts.no_questions:
        cfg.question_gen.enabled = False

    # ------------------------------------------------------------------ #
    #  1. Generate / load sample documents                                 #
    # ------------------------------------------------------------------ #
    os.makedirs(SAMPLE_DOCUMENTS_DIR, exist_ok=True)
    os.makedirs(OUTPUTS_DIR, exist_ok=True)

    type_counts = _distribute(cfg.generator.total_documents,
                               cfg.generator.enabled_types)
    generator = SyntheticDocumentGenerator(seed=cfg.generator.random_seed)

    docs: list[tuple[str, str, str]] = []  # (doc_id, doc_type, content)
    for doc_type, count in type_counts.items():
        for i in range(count):
            doc_id, content = generator.generate(doc_type, i)
            path = generator.save(doc_id, content, SAMPLE_DOCUMENTS_DIR)
            docs.append((doc_id, doc_type, content, path))

    logger.info("Generated %d documents across %d types",
                len(docs), len(type_counts))

    # ------------------------------------------------------------------ #
    #  2. Chunk each document                                              #
    # ------------------------------------------------------------------ #
    chunking_service = _load_chunking_service(cfg)

    def chunk(text: str) -> list:
        if chunking_service:
            raw = chunking_service.chunk_markdown(text)
            # Normalise: SemanticChunkingPipeline returns dicts with 'text'/'page_number'
            result = []
            for c in raw:
                if isinstance(c, dict):
                    result.append({
                        "text": c.get("text", c.get("content", "")),
                        "page_number": c.get("page_number", 1),
                    })
                else:
                    result.append({"text": str(c), "page_number": 1})
            return result
        return _fallback_chunk(text, cfg.chunking.chunk_size, cfg.chunking.chunk_overlap)

    # ------------------------------------------------------------------ #
    #  3. Validate + integrity check                                       #
    # ------------------------------------------------------------------ #
    chunk_validator = ChunkValidator(
        max_chunk_size=cfg.validation.max_chunk_size,
        min_chunk_size=cfg.validation.min_chunk_size,
        chunk_size=cfg.chunking.chunk_size,
        chunk_overlap=cfg.chunking.chunk_overlap,
    )
    integrity_validator = IntegrityValidator()

    validation_results = []
    integrity_results = []

    # ------------------------------------------------------------------ #
    #  4. Build evaluation dataset                                         #
    # ------------------------------------------------------------------ #
    question_gen = None
    if cfg.question_gen.enabled and cfg.question_gen.api_key:
        question_gen = EvaluationQuestionGenerator(
            api_key=cfg.question_gen.api_key,
            model=cfg.question_gen.model,
            temperature=cfg.question_gen.temperature,
            timeout=cfg.question_gen.timeout,
            questions_per_chunk=cfg.question_gen.questions_per_chunk,
        )

    dataset_builder = EvaluationDatasetBuilder(
        question_generator=question_gen,
        max_chunks_per_doc=cfg.question_gen.max_chunks_per_doc,
    )

    start = time.time()

    for doc_id, doc_type, content, source_path in docs:
        chunks = chunk(content)

        val_report = chunk_validator.validate(doc_id, content, chunks)
        validation_results.append(val_report.to_dict())

        int_report = integrity_validator.validate(doc_id, content, chunks)
        integrity_results.append(int_report.to_dict())

        dataset_builder.add_document(doc_id, doc_type, source_path, chunks)

    elapsed = time.time() - start

    # ------------------------------------------------------------------ #
    #  5. Save outputs                                                     #
    # ------------------------------------------------------------------ #
    reporter = PipelineTestReporter(json_indent=cfg.report.json_indent)
    report = reporter.build_report(validation_results, integrity_results, elapsed)

    report_path = os.path.join(OUTPUTS_DIR, "pipeline_test_report.json")
    dataset_json_path = os.path.join(OUTPUTS_DIR, "evaluation_dataset.json")
    dataset_csv_path = os.path.join(OUTPUTS_DIR, "evaluation_dataset_summary.csv")

    reporter.save(report, report_path)
    dataset_builder.save_json(dataset_json_path, indent=cfg.report.json_indent)
    dataset_builder.save_csv(dataset_csv_path)

    reporter.print_summary(report)
    return report


if __name__ == "__main__":
    run()
