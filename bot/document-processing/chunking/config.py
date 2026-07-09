"""Runtime configuration for semantic chunking controls."""

import os
from dataclasses import dataclass

@dataclass
class ChunkingConfig:
    """Holds configuration parameters for structural and semantic splitting."""
    chunk_size: int = 400            # Target chunk size in tokens
    overlap_size: int = 50          # Overlap size in tokens
    max_token_limit: int = 512       # Maximum token threshold
    semantic_threshold: float = 0.7  # Cosine similarity breakpoint threshold
    min_group_size: int = 1          # Min sentences per semantic group
    max_group_size: int = 8          # Max sentences per semantic group
    heading_depth: int = 3           # Heading hierarchy parsing depth (H1, H2, H3)
    tokenizer_name: str = "cl100k_base" # Embedding-compatible tokenizer (tiktoken)

    @classmethod
    def from_env(cls) -> "ChunkingConfig":
        return cls(
            chunk_size=int(os.getenv("CHUNK_SIZE", "400")),
            overlap_size=int(os.getenv("CHUNK_OVERLAP", "50")),
            max_token_limit=int(os.getenv("MAX_TOKEN_LIMIT", "512")),
            semantic_threshold=float(os.getenv("SEMANTIC_THRESHOLD", "0.7")),
            min_group_size=int(os.getenv("MIN_SEMANTIC_GROUP_SIZE", "1")),
            max_group_size=int(os.getenv("MAX_SEMANTIC_GROUP_SIZE", "8")),
            heading_depth=int(os.getenv("HEADING_DEPTH", "3")),
            tokenizer_name=os.getenv("TOKENIZER_NAME", "cl100k_base")
        )
