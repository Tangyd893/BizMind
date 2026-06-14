"""Text chunking — recursive character split with token-aware sizing.

For P1 we use a simple paragraph-based splitter with configurable
child_size / child_overlap. Parent-child linking is a P2 enhancement.
"""

import re
from dataclasses import dataclass, field

from app.config import get_settings


@dataclass
class Chunk:
    text: str
    index: int
    parent_index: int | None = None


@dataclass
class ChunkResult:
    chunks: list[Chunk]
    parent_chunks: list[Chunk] = field(default_factory=list)


def _split_paragraphs(text: str) -> list[str]:
    """Split text into paragraphs on double-newline boundaries."""
    # Normalize line endings
    text = re.sub(r"\r\n|\r", "\n", text)
    paragraphs = re.split(r"\n\s*\n", text)
    return [p.strip() for p in paragraphs if p.strip()]


def _merge_paragraphs(paragraphs: list[str], max_chars: int, overlap_chars: int) -> list[str]:
    """Merge paragraphs into chunks of roughly max_chars."""
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for para in paragraphs:
        para_len = len(para)
        if current and current_len + para_len > max_chars:
            chunks.append("\n\n".join(current))
            # Overlap: keep last paragraph(s) up to overlap_chars
            overlap_text = ""
            for p in reversed(current):
                if len(overlap_text) + len(p) <= overlap_chars:
                    overlap_text = p + ("\n\n" + overlap_text if overlap_text else "")
                else:
                    break
            if overlap_text:
                current = [overlap_text]
                current_len = len(overlap_text)
            else:
                current = []
                current_len = 0
        current.append(para)
        current_len += para_len

    if current:
        chunks.append("\n\n".join(current))

    return chunks


def chunk_document(text: str, parent_chunk_size: int | None = None) -> ChunkResult:
    """Split document text into searchable child chunks and optional parent chunks.

    Child chunks are used for vector search; parent chunks provide context
    for LLM generation (P2 enhancement).
    """
    settings = get_settings()
    # Rough token→char mapping: ~4 chars per token for English, ~2 for CJK
    # We use 3 as a middle-ground multiplier
    char_multiplier = 3
    child_max = settings.chunk_size * char_multiplier
    child_overlap = settings.chunk_overlap * char_multiplier

    paragraphs = _split_paragraphs(text)
    child_texts = _merge_paragraphs(paragraphs, child_max, child_overlap)

    child_chunks = [
        Chunk(text=t, index=i) for i, t in enumerate(child_texts)
    ]

    parent_chunks: list[Chunk] = []
    if parent_chunk_size:
        parent_max = parent_chunk_size * char_multiplier
        parent_texts = _merge_paragraphs(paragraphs, parent_max, 0)
        parent_chunks = [
            Chunk(text=t, index=i) for i, t in enumerate(parent_texts)
        ]

    return ChunkResult(chunks=child_chunks, parent_chunks=parent_chunks)
