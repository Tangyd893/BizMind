"""Text chunking — Parent-Child strategy per ADR-003.

Child chunks (512 tokens) → indexed in Qdrant for search.
Parent chunks (2048 tokens) → used as LLM context after retrieval.
Child → Parent linking via text overlap matching.
"""

import re
from dataclasses import dataclass

from app.config import get_settings


@dataclass
class Chunk:
    text: str
    index: int
    parent_index: int | None = None


@dataclass
class ChunkResult:
    chunks: list[Chunk]         # child chunks for search
    parent_chunks: list[Chunk]  # parent chunks for context


def _split_paragraphs(text: str) -> list[str]:
    """Split text into paragraphs on double-newline boundaries."""
    text = re.sub(r"\r\n|\r", "\n", text)
    paragraphs = re.split(r"\n\s*\n", text)
    return [p.strip() for p in paragraphs if p.strip()]


def _merge_paragraphs(paragraphs: list[str], max_chars: int, overlap_chars: int) -> list[str]:
    """Merge paragraphs into chunks of roughly max_chars, with optional overlap."""
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for para in paragraphs:
        para_len = len(para)
        if current and current_len + para_len > max_chars:
            chunks.append("\n\n".join(current))
            if overlap_chars > 0:
                # Keep last paragraphs up to overlap_chars for sliding window
                overlap_text = ""
                for p in reversed(current):
                    if len(overlap_text) + len(p) <= overlap_chars:
                        overlap_text = p + ("\n\n" + overlap_text if overlap_text else "")
                    else:
                        break
                current = [overlap_text] if overlap_text else []
                current_len = len(overlap_text) if overlap_text else 0
            else:
                current = []
                current_len = 0
        current.append(para)
        current_len += para_len

    if current:
        chunks.append("\n\n".join(current))

    return chunks


def _find_parent(child_text: str, parents: list[str]) -> int | None:
    """Find which parent chunk contains the child text (best overlap match)."""
    best_idx = None
    best_score = 0
    for i, parent in enumerate(parents):
        # Simple overlap: count common words
        child_words = set(child_text.lower().split())
        parent_words = set(parent.lower().split())
        if child_words:
            score = len(child_words & parent_words) / len(child_words)
            if score > best_score:
                best_score = score
                best_idx = i
    return best_idx


def chunk_document(text: str) -> ChunkResult:
    """Split document into child chunks (for search) and parent chunks (for context).

    Per ADR-003:
    - Child chunks: ~512 tokens (1536 chars), overlap 64 tokens (192 chars)
    - Parent chunks: ~2048 tokens (6144 chars), no overlap
    - Each child is linked to its best-matching parent via parent_index
    """
    settings = get_settings()
    # ~3 chars per token (middle-ground between English 4 and CJK 2)
    CHAR_SCALE = 3

    child_max = settings.chunk_size * CHAR_SCALE
    child_overlap = settings.chunk_overlap * CHAR_SCALE
    parent_max = getattr(settings, "parent_chunk_size", 2048) * CHAR_SCALE

    paragraphs = _split_paragraphs(text)
    if not paragraphs:
        return ChunkResult(chunks=[], parent_chunks=[])

    # Generate parent chunks (larger, no overlap)
    parent_texts = _merge_paragraphs(paragraphs, parent_max, 0)
    parent_chunks = [Chunk(text=t, index=i) for i, t in enumerate(parent_texts)]

    # Generate child chunks (smaller, with overlap)
    child_texts = _merge_paragraphs(paragraphs, child_max, child_overlap)
    child_chunks = []
    for i, ct in enumerate(child_texts):
        parent_idx = _find_parent(ct, parent_texts)
        child_chunks.append(Chunk(text=ct, index=i, parent_index=parent_idx))

    return ChunkResult(chunks=child_chunks, parent_chunks=parent_chunks)
