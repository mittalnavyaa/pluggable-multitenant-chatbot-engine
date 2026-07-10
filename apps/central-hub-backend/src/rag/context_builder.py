"""Consolidates retrieved document chunks into formatted markdown structures."""

from typing import List
from langchain_core.documents import Document

class ContextBuilder:
    """Assembles retrieved LangChain documents into a single structured context block."""

    @staticmethod
    def build_context(documents: List[Document]) -> str:
        """
        Builds a structured string containing chunk contents, metadata, and headings.
        Preserves retrieval order.
        """
        if not documents:
            return ""

        context_parts = []
        for idx, doc in enumerate(documents):
            meta = doc.metadata or {}
            
            # Retrieve fields with fallbacks
            title = meta.get("source_filename") or "Untitled Document"
            page = meta.get("page_number") or 1
            section = meta.get("section_title") or "Root"
            chunk_id = meta.get("chunk_id") or str(idx)
            headings = meta.get("parent_headings") or {}

            # Construct parent hierarchy string
            hierarchy = ""
            if isinstance(headings, dict) and headings:
                # E.g. {"h1": "Intro", "h2": "Background"} -> "Intro > Background"
                hierarchy = " > ".join(str(val) for val in headings.values() if val)
            elif isinstance(headings, list) and headings:
                hierarchy = " > ".join(str(h) for h in headings if h)
            elif isinstance(headings, str) and headings:
                hierarchy = headings

            # Formulate layout header
            header = f"[Chunk {idx + 1}] Source: {title} | Section: {section} | Page: {page} | Chunk ID: {chunk_id}"
            if hierarchy:
                header += f" | Hierarchy: {hierarchy}"

            # Assemble paragraph block
            part = f"{header}\nContent:\n{doc.page_content.strip()}"
            context_parts.append(part)

        return "\n\n---\n\n".join(context_parts)
