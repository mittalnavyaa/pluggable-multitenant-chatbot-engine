"""Text splitting, mathematical, and tokenization utilities."""

import re
import tiktoken
import logging

logger = logging.getLogger("chunking_utils")

def split_into_sentences(text: str) -> list[str]:
    """Splits a body of text into sentences, preserving punctuation and abbreviations."""
    if not text.strip():
        return []
    
    # First, split by period, question mark, or exclamation mark followed by whitespace
    raw_splits = re.split(r'(\.|\?|!)(?=\s|$)', text)
    
    sentences = []
    i = 0
    # Re-group sentence texts with their matched punctuation marks
    while i < len(raw_splits):
        segment = raw_splits[i].strip()
        if not segment:
            i += 1
            continue
        if i + 1 < len(raw_splits):
            punct = raw_splits[i + 1]
            segment += punct
            i += 2
        else:
            i += 1
        sentences.append(segment)

    # Merge splits that were incorrectly broken at standard abbreviations
    abbreviations = {"e.g.", "i.e.", "mr.", "mrs.", "dr.", "st.", "vs.", "prof."}
    merged_sentences = []
    
    for sentence in sentences:
        if merged_sentences:
            prev_sentence = merged_sentences[-1]
            words = prev_sentence.split()
            if words:
                last_word = words[-1].lower()
                # If the last word of the previous sentence is an abbreviation, merge them
                if last_word in abbreviations:
                    merged_sentences[-1] = prev_sentence + " " + sentence
                    continue
        merged_sentences.append(sentence)
            
    return merged_sentences

def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    """Computes cosine similarity between two numeric vectors."""
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    
    dot_product = sum(x * y for x, y in zip(v1, v2))
    norm_v1 = sum(x * x for x in v1) ** 0.5
    norm_v2 = sum(x * x for x in v2) ** 0.5
    
    if norm_v1 == 0 or norm_v2 == 0:
        return 0.0
        
    return dot_product / (norm_v1 * norm_v2)

class TiktokenTokenizer:
    """TIKTOKEN wrapper for counting tokens using cl100k_base or other encodings."""

    def __init__(self, encoding_name: str = "cl100k_base") -> None:
        try:
            self.encoder = tiktoken.get_encoding(encoding_name)
            self.use_fallback = False
        except Exception as e:
            logger.warning(f"Failed to load tiktoken encoding '{encoding_name}': {e}. Using fallback tokenizer.")
            self.use_fallback = True

    def count_tokens(self, text: str) -> int:
        """Returns the number of tokens in the given text."""
        if self.use_fallback:
            # Fallback estimation
            return len(text.split())
        return len(self.encoder.encode(text, disallowed_special=()))

    def encode(self, text: str) -> list[int]:
        """Encodes text to token IDs."""
        if self.use_fallback:
            return list(range(len(text.split())))
        return self.encoder.encode(text, disallowed_special=())

    def decode(self, tokens: list[int]) -> str:
        """Decodes token IDs back to text string."""
        if self.use_fallback:
            return " "
        return self.encoder.decode(tokens)
