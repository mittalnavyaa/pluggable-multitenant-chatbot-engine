import re
from chunking.pipeline import SemanticChunkingPipeline
from chunking.config import ChunkingConfig

class ChunkingService:
    """Service that handles semantic splitting of Markdown text into chunks."""

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        # Convert character sizes to approximate token budgets (1 token ≈ 4 characters)
        self.chunk_size = chunk_size // 4
        self.chunk_overlap = chunk_overlap // 4

    def chunk_markdown(self, markdown_text: str) -> list[dict]:
        """
        Splits Markdown text using default pipeline parameters for backwards compatibility.
        """
        return self.chunk_markdown_advanced(
            markdown_text=markdown_text,
            platform_id="default-platform",
            document_id="00000000-0000-0000-0000-000000000000",
            job_id="00000000-0000-0000-0000-000000000000",
            source_filename="document.txt"
        )

    def chunk_markdown_advanced(
        self,
        markdown_text: str,
        platform_id: str,
        document_id: str,
        job_id: str,
        source_filename: str,
        correlation_id: str = ""
    ) -> list[dict]:
        """
        Splits Markdown text using hierarchical structural and semantic chunking.
        """
        config = ChunkingConfig(
            chunk_size=self.chunk_size,
            overlap_size=self.chunk_overlap
        )
        pipeline = SemanticChunkingPipeline(config=config)
        chunks = pipeline.run(
            markdown_text=markdown_text,
            platform_id=platform_id,
            document_id=document_id,
            job_id=job_id,
            source_filename=source_filename,
            correlation_id=correlation_id
        )
        return [chunk.to_dict() for chunk in chunks]
