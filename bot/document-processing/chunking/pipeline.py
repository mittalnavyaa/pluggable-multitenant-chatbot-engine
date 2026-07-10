"""Semantic chunking orchestrator pipeline."""

import logging
from typing import List
from chunking.config import ChunkingConfig
from chunking.chunk_models import SemanticChunk, MarkdownElement
from chunking.markdown_parser import MarkdownParser
from chunking.hierarchy_builder import HierarchyBuilder
from chunking.semantic_splitter import SemanticSplitter
from chunking.token_optimizer import TokenOptimizer
from chunking.metadata_builder import MetadataBuilder
from src.services.embedding_service import EmbeddingService

logger = logging.getLogger("chunking_pipeline")

class SemanticChunkingPipeline:
    """Orchestrates parsing, splitting, token optimization, and enrichment stages."""

    def __init__(self, config: ChunkingConfig | None = None, embedding_service: EmbeddingService | None = None) -> None:
        self.config = config or ChunkingConfig()
        self.parser = MarkdownParser()
        self.hierarchy_builder = HierarchyBuilder()
        self.splitter = SemanticSplitter(self.config, embedding_service)
        self.optimizer = TokenOptimizer(self.config)
        self.metadata_builder = MetadataBuilder()

    def run(
        self,
        markdown_text: str,
        platform_id: str,
        document_id: str,
        job_id: str,
        source_filename: str,
        correlation_id: str = "",
        bot_id: str = None
    ) -> list[SemanticChunk]:
        """Runs the multi-stage document parsing and semantic splitting pipeline."""
        logger.info(f"Starting semantic chunking pipeline for document: {document_id}")

        # 1. Structural Markdown Parsing
        elements = self.parser.parse(markdown_text)
        if not elements:
            return []

        # 2. Dynamic Semantic Distance Splitting (grouped under headings)
        grouped_elements = []
        for element in elements:
            # Skip empty elements
            if not element.text.strip():
                continue

            # We don't split headings, code blocks, tables, or lists semantically
            if element.type in ("heading_1", "heading_2", "heading_3", "code_block", "table", "list"):
                grouped_elements.append({
                    "text": element.text,
                    "h1": element.h1,
                    "h2": element.h2,
                    "h3": element.h3,
                    "type": element.type,
                    "page_start": element.page_start,
                    "page_end": element.page_end
                })
            else:
                # Paragraph or Blockquote -> split semantically
                semantic_splits = self.splitter.split(element.text)
                for split_text in semantic_splits:
                    grouped_elements.append({
                        "text": split_text,
                        "h1": element.h1,
                        "h2": element.h2,
                        "h3": element.h3,
                        "type": element.type,
                        "page_start": element.page_start,
                        "page_end": element.page_end
                    })

        # 3. Group and Optimize small sections
        optimized_groups = self.optimizer.optimize_groups(grouped_elements)

        # 4. Token boundaries check & splitting oversized blocks
        final_chunks = []
        chunk_idx = 0

        for block in optimized_groups:
            block_text = block["text"]
            h1 = block["h1"]
            h2 = block["h2"]
            h3 = block["h3"]

            parent_headings = {
                "h1": h1,
                "h2": h2,
                "h3": h3
            }
            section_title = h3 or h2 or h1 or "Root"

            # Check if block exceeds max token limit
            split_texts = self.optimizer.split_oversized_text(block_text)

            for txt in split_texts:
                tok_count = self.optimizer.count_tokens(txt)
                char_count = len(txt)

                # Formulate metadata
                meta = self.metadata_builder.build(
                    platform_id=platform_id,
                    document_id=document_id,
                    job_id=job_id,
                    chunk_index=chunk_idx,
                    parent_headings=parent_headings,
                    source_file=source_filename,
                    section_title=section_title,
                    token_count=tok_count,
                    character_count=char_count,
                    page_start=block.get("page_start", 1),
                    page_end=block.get("page_end", 1),
                    element_type=block.get("type", "paragraph"),
                    correlation_id=correlation_id
                )
                if bot_id:
                    meta["bot_id"] = bot_id

                chunk = SemanticChunk(
                    text=txt,
                    chunk_index=chunk_idx,
                    parent_headings=parent_headings,
                    section_title=section_title,
                    token_count=tok_count,
                    character_count=char_count,
                    metadata=meta
                )
                final_chunks.append(chunk)
                chunk_idx += 1

        logger.info(f"Chunking pipeline complete. Generated {len(final_chunks)} chunks.")
        return final_chunks
