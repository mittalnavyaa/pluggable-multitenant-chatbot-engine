"""Heading hierarchy formatting and builder utilities."""

from typing import Dict
from chunking.chunk_models import MarkdownElement

class HierarchyBuilder:
    """Manages document hierarchy context formatting."""

    def build_parent_headings(self, element: MarkdownElement) -> Dict[str, str | None]:
        """Creates a standardized dictionary of headings context."""
        return {
            "h1": element.h1,
            "h2": element.h2,
            "h3": element.h3
        }

    def get_section_title(self, element: MarkdownElement) -> str:
        """Returns the most immediate active heading title or 'Root'."""
        if element.h3:
            return element.h3
        if element.h2:
            return element.h2
        if element.h1:
            return element.h1
        return "Root"
