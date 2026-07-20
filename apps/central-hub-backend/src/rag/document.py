"""Internal document model replacing LangChain Document dependency."""

from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass
class Document:
    """
    Internal data model representing a retrieved text segment and its metadata.
    Replaces langchain_core.documents.Document.
    """
    page_content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
