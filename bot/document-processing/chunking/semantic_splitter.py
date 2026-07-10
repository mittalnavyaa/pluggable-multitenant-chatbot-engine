"""Semantic distance sentence splitter utilizing local vector embeddings."""

import logging
from chunking.config import ChunkingConfig
from chunking.utils import split_into_sentences, cosine_similarity
from src.services.embedding_service import EmbeddingService

logger = logging.getLogger("semantic_splitter")

class SemanticSplitter:
    """Splits text into semantically cohesive groups of sentences using vector similarities."""

    def __init__(self, config: ChunkingConfig, embedding_service: EmbeddingService | None = None) -> None:
        self.config = config
        self.embedding_service = embedding_service or EmbeddingService()

    def split(self, text: str) -> list[str]:
        """Splits a single block of text into semantic sentence groups."""
        sentences = split_into_sentences(text)
        if not sentences:
            return []
        if len(sentences) == 1:
            return [sentences[0]]

        # Generate embeddings for each sentence in a single batch call
        try:
            if hasattr(self.embedding_service, "generate_embeddings"):
                embeddings = self.embedding_service.generate_embeddings(sentences)
            else:
                embeddings = [self.embedding_service.generate_embedding(s) for s in sentences]
        except Exception as e:
            logger.error(f"Failed to generate sentence embeddings: {e}. Falling back to paragraph.")
            return [text]

        groups = []
        current_group = [sentences[0]]

        for i in range(1, len(sentences)):
            sim = cosine_similarity(embeddings[i-1], embeddings[i])
            
            # Check breakpoint threshold
            is_breakpoint = sim < self.config.semantic_threshold
            
            # Constraints
            too_small = len(current_group) < self.config.min_group_size
            too_large = len(current_group) >= self.config.max_group_size
            
            if (is_breakpoint and not too_small) or too_large:
                groups.append(" ".join(current_group))
                current_group = [sentences[i]]
            else:
                current_group.append(sentences[i])

        if current_group:
            groups.append(" ".join(current_group))

        logger.info(f"Semantically split text into {len(groups)} sentence groups.")
        return groups
