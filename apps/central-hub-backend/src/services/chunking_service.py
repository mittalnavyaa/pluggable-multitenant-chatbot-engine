import re

class ChunkingService:
    """Service that handles semantic splitting of Markdown text into chunks."""

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_markdown(self, markdown_text: str) -> list[dict]:
        """
        Splits Markdown text by paragraph transitions and returns a list of
        structured dictionaries with chunks and page numbers.
        """
        paragraphs = re.split(r'\n\n+', markdown_text)
        chunks = []
        current_chunk = []
        current_length = 0
        page_number = 1

        for para in paragraphs:
            # Dynamically look for any page markers inserted during extraction
            page_match = re.search(r'(?:Page|page)\s+(\d+)', para)
            if page_match:
                page_number = int(page_match.group(1))

            para_len = len(para)
            if current_length + para_len > self.chunk_size and current_chunk:
                chunks.append({
                    "text": "\n\n".join(current_chunk),
                    "page_number": page_number
                })
                # Retain sliding window overlap
                overlap_len = 0
                new_chunk = []
                for p in reversed(current_chunk):
                    if overlap_len + len(p) < self.chunk_overlap:
                        new_chunk.insert(0, p)
                        overlap_len += len(p)
                    else:
                        break
                current_chunk = new_chunk
                current_length = sum(len(p) for p in current_chunk)

            current_chunk.append(para)
            current_length += para_len

        if current_chunk:
            chunks.append({
                "text": "\n\n".join(current_chunk),
                "page_number": page_number
            })

        return chunks
