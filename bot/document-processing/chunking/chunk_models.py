"""Data models for Markdown elements and semantic chunks."""

from dataclasses import dataclass, field
from typing import Dict, Any

@dataclass
class MarkdownElement:
    """Represents a structural element parsed from Markdown."""
    type: str  # heading_1, heading_2, heading_3, paragraph, table, list, blockquote, code_block
    text: str
    h1: str | None = None
    h2: str | None = None
    h3: str | None = None
    page_start: int = 1
    page_end: int = 1

@dataclass
class SemanticChunk:
    """Represents a final semantically split, token-optimized document chunk."""
    text: str
    chunk_index: int
    parent_headings: Dict[str, str | None]
    section_title: str
    token_count: int
    character_count: int
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "page_number": self.metadata.get("page_number", 1), # Compatibility with existing downstream code
            "metadata": {
                **self.metadata,
                "chunk_index": self.chunk_index,
                "parent_headings": self.parent_headings,
                "section_title": self.section_title,
                "token_count": self.token_count,
                "character_count": self.character_count
            }
        }
