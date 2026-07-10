import hashlib
import numpy as np

class EmbeddingService:
    """Service that computes text vector embeddings."""

    def __init__(self, dimension: int = 1536):
        self.dimension = dimension
        self._cache = {}

    def generate_embedding(self, text: str) -> list[float]:
        """
        Generates a deterministic unit vector representation of the text.
        
        TODO:
        - Replace this mock implementation with the configured production embedding model (e.g., OpenAI/HuggingFace).
        - Do not hardcode another embedding provider.
        """
        if text in self._cache:
            return self._cache[text]

        # Determine seed from text digest to ensure reproducibility
        h = hashlib.md5(text.encode('utf-8')).digest()
        np.random.seed(int.from_bytes(h[:4], byteorder='big'))
        
        # Generate raw random vector
        vector = np.random.uniform(-1.0, 1.0, self.dimension)
        
        # Normalize vector to unit length for robust cosine distance computations
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
            
        result = vector.tolist()
        self._cache[text] = result
        return result
