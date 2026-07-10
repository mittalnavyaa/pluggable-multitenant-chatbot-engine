"""Enforces token boundaries, groups small sections, and splits oversized blocks with overlap."""

import logging
from typing import List, Dict, Any
from chunking.config import ChunkingConfig
from chunking.utils import TiktokenTokenizer, split_into_sentences
from chunking.chunk_models import MarkdownElement

logger = logging.getLogger("token_optimizer")

class TokenOptimizer:
    """Enforces token budget limits, handles merges, and splits oversized sections recursively."""

    def __init__(self, config: ChunkingConfig) -> None:
        self.config = config
        self.tokenizer = TiktokenTokenizer(config.tokenizer_name)

    def count_tokens(self, text: str) -> int:
        return self.tokenizer.count_tokens(text)

    def optimize_groups(self, groups_with_meta: list[dict]) -> list[dict]:
        """
        Combines contiguous small semantic groups belonging to the same heading section.
        Each dictionary contains {"text": text, "h1": h1, "h2": h2, "h3": h3, "type": type, "page_start": page_start, "page_end": page_end}.
        """
        optimized = []
        if not groups_with_meta:
            return []

        current_block = []
        current_tokens = 0
        current_headings = None
        current_types = []
        current_page_starts = []
        current_page_ends = []

        for item in groups_with_meta:
            item_text = item["text"]
            item_tokens = self.count_tokens(item_text)
            headings = (item["h1"], item["h2"], item["h3"])

            # If headings change, or adding this item exceeds target chunk_size, flush current block
            if current_headings is not None and (headings != current_headings or current_tokens + item_tokens > self.config.chunk_size):
                if current_block:
                    block_type = current_types[0] if len(set(current_types)) == 1 else "paragraph"
                    optimized.append({
                        "text": "\n\n".join(current_block),
                        "h1": current_headings[0],
                        "h2": current_headings[1],
                        "h3": current_headings[2],
                        "type": block_type,
                        "page_start": min(current_page_starts) if current_page_starts else 1,
                        "page_end": max(current_page_ends) if current_page_ends else 1
                    })
                current_block = [item_text]
                current_tokens = item_tokens
                current_headings = headings
                current_types = [item.get("type", "paragraph")]
                current_page_starts = [item.get("page_start", 1)]
                current_page_ends = [item.get("page_end", 1)]
            else:
                if current_headings is None:
                    current_headings = headings
                current_block.append(item_text)
                current_tokens += item_tokens
                current_types.append(item.get("type", "paragraph"))
                current_page_starts.append(item.get("page_start", 1))
                current_page_ends.append(item.get("page_end", 1))

        if current_block:
            block_type = current_types[0] if len(set(current_types)) == 1 else "paragraph"
            optimized.append({
                "text": "\n\n".join(current_block),
                "h1": current_headings[0],
                "h2": current_headings[1],
                "h3": current_headings[2],
                "type": block_type,
                "page_start": min(current_page_starts) if current_page_starts else 1,
                "page_end": max(current_page_ends) if current_page_ends else 1
            })

        return optimized

    def split_oversized_text(self, text: str) -> list[str]:
        """
        Splits text that exceeds max_token_limit using sentence boundaries and overlapping.
        Falls back to word boundaries if sentences are still too large.
        """
        tokens = self.tokenizer.encode(text)
        if len(tokens) <= self.config.max_token_limit:
            return [text]

        # Try splitting by sentence boundaries first
        sentences = split_into_sentences(text)
        chunks = []
        current_chunk_sentences = []
        current_chunk_tokens = 0

        for sentence in sentences:
            sent_tokens = self.count_tokens(sentence)
            # If a single sentence exceeds the maximum token limit, split it by words
            if sent_tokens > self.config.max_token_limit:
                # Flush existing chunk
                if current_chunk_sentences:
                    chunks.append(" ".join(current_chunk_sentences))
                    current_chunk_sentences = []
                    current_chunk_tokens = 0
                
                # Split this sentence by words
                words = sentence.split()
                word_chunk = []
                word_chunk_tokens = 0
                for word in words:
                    w_tokens = self.count_tokens(word) + 1
                    if word_chunk_tokens + w_tokens > self.config.max_token_limit:
                        chunks.append(" ".join(word_chunk))
                        # Retain overlap of overlap_size words/tokens
                        overlap_words = []
                        overlap_tokens = 0
                        for w in reversed(word_chunk):
                            w_tok = self.count_tokens(w) + 1
                            if overlap_tokens + w_tok < self.config.overlap_size:
                                overlap_words.insert(0, w)
                                overlap_tokens += w_tok
                            else:
                                break
                        word_chunk = overlap_words
                        word_chunk_tokens = overlap_tokens

                    word_chunk.append(word)
                    word_chunk_tokens += w_tokens

                if word_chunk:
                    chunks.append(" ".join(word_chunk))
                continue

            # Check if adding sentence violates budget limit
            if current_chunk_tokens + sent_tokens > self.config.max_token_limit:
                chunks.append(" ".join(current_chunk_sentences))
                
                # Overlap logic
                overlap_sentences = []
                overlap_tokens = 0
                for s in reversed(current_chunk_sentences):
                    s_tokens = self.count_tokens(s)
                    if overlap_tokens + s_tokens < self.config.overlap_size:
                        overlap_sentences.insert(0, s)
                        overlap_tokens += s_tokens
                    else:
                        break
                current_chunk_sentences = overlap_sentences
                current_chunk_tokens = overlap_tokens

            current_chunk_sentences.append(sentence)
            current_chunk_tokens += sent_tokens

        if current_chunk_sentences:
            chunks.append(" ".join(current_chunk_sentences))

        return chunks
