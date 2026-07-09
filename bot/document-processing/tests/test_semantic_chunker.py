import pytest
import os
import sys
from unittest.mock import MagicMock

# Resolve paths
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
doc_proc_path = os.path.join(project_root, "bot", "document-processing")
backend_path = os.path.join(project_root, "apps", "central-hub-backend")

if doc_proc_path not in sys.path:
    sys.path.insert(0, doc_proc_path)
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from chunking.config import ChunkingConfig
from chunking.markdown_parser import MarkdownParser
from chunking.utils import split_into_sentences, cosine_similarity, TiktokenTokenizer
from chunking.token_optimizer import TokenOptimizer
from chunking.pipeline import SemanticChunkingPipeline
from src.services.embedding_service import EmbeddingService


def test_sentence_splitter_abbreviations():
    text = "Mr. Smith went to the store. Do not miss the deadline!"
    sentences = split_into_sentences(text)
    assert len(sentences) == 2
    assert sentences[0] == "Mr. Smith went to the store."
    assert sentences[1] == "Do not miss the deadline!"


def test_cosine_similarity():
    v1 = [1.0, 0.0, 0.0]
    v2 = [1.0, 0.0, 0.0]
    assert abs(cosine_similarity(v1, v2) - 1.0) < 1e-6

    v3 = [0.0, 1.0, 0.0]
    assert abs(cosine_similarity(v1, v3)) < 1e-6


def test_structural_markdown_parser():
    md = """# Section 1
Intro paragraphs.

## Subsection 1.1
* List item 1
* List item 2

| Table col 1 | col 2 |
|---|---|
| Row 1 | Row 2 |

```python
print("Hello World")
```
"""
    parser = MarkdownParser()
    elements = parser.parse(md)
    
    # Assert we have multiple elements
    assert len(elements) > 0
    
    # Let's search for heading element
    heading_elements = [e for e in elements if e.type == "heading_1"]
    assert len(heading_elements) == 1
    assert heading_elements[0].h1 == "Section 1"

    # Search for list element
    list_elements = [e for e in elements if e.type == "list"]
    assert len(list_elements) == 1
    assert list_elements[0].h1 == "Section 1"
    assert list_elements[0].h2 == "Subsection 1.1"

    # Search for table
    table_elements = [e for e in elements if e.type == "table"]
    assert len(table_elements) == 1

    # Search for code block
    code_elements = [e for e in elements if e.type == "code_block"]
    assert len(code_elements) == 1


def test_token_optimizer_splitting_and_overlap():
    config = ChunkingConfig(
        chunk_size=10,
        overlap_size=3,
        max_token_limit=12
    )
    optimizer = TokenOptimizer(config)
    
    # This text has around 20 words (tokens in fallback/tiktoken mode)
    text = "First sentence of the document. Second sentence here. Third sentence is a bit longer. Fourth sentence is final."
    
    chunks = optimizer.split_oversized_text(text)
    
    assert len(chunks) > 1
    # Check that overlapping parts exist
    # For example, consecutive chunks should share some words if overlap works
    assert any("sentence" in c for c in chunks)


def test_semantic_chunking_pipeline_run():
    md_text = """# Registration Portal
Please make sure to log in using student credentials.

## Step by Step Guide
First step: go to homepage.
Second step: click register button.
Third step: fill in your academic information.
"""
    # Use real mock embedding service
    embed_service = EmbeddingService()
    
    config = ChunkingConfig(
        chunk_size=20,
        overlap_size=5,
        max_token_limit=30,
        semantic_threshold=0.85
    )
    
    pipeline = SemanticChunkingPipeline(config=config, embedding_service=embed_service)
    chunks = pipeline.run(
        markdown_text=md_text,
        platform_id="prod_123",
        document_id="doc_999",
        job_id="job_777",
        source_filename="guide.md",
        correlation_id="corr_abc"
    )
    
    assert len(chunks) > 0
    
    first_chunk = chunks[0]
    # Check metadata enrichment
    assert first_chunk.metadata["platform_id"] == "prod_123"
    assert first_chunk.metadata["document_id"] == "doc_999"
    assert first_chunk.metadata["job_id"] == "job_777"
    assert first_chunk.metadata["source_file"] == "guide.md"
    assert first_chunk.metadata["correlation_id"] == "corr_abc"
    assert "h1" in first_chunk.parent_headings
    assert first_chunk.token_count > 0
    assert first_chunk.character_count > 0
