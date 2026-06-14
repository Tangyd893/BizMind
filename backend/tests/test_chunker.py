"""Tests for chunker module — no DB required."""

from app.rag.chunker import _merge_paragraphs, _split_paragraphs, chunk_document


class TestSplitParagraphs:
    def test_single_paragraph(self):
        result = _split_paragraphs("Hello world")
        assert result == ["Hello world"]

    def test_multiple_paragraphs(self):
        text = "First paragraph.\n\nSecond paragraph.\n\nThird."
        result = _split_paragraphs(text)
        assert len(result) == 3
        assert result[0] == "First paragraph."

    def test_empty_string(self):
        assert _split_paragraphs("") == []
        assert _split_paragraphs("\n\n\n") == []

    def test_windows_line_endings(self):
        text = "Line one.\r\n\r\nLine two."
        result = _split_paragraphs(text)
        assert len(result) == 2
        assert result[0] == "Line one."


class TestMergeParagraphs:
    def test_small_paragraphs_merged(self):
        paras = ["a", "b", "c"]
        result = _merge_paragraphs(paras, max_chars=10, overlap_chars=0)
        assert len(result) == 1

    def test_large_paragraphs_split(self):
        paras = ["a" * 50, "b" * 50, "c" * 50]
        result = _merge_paragraphs(paras, max_chars=60, overlap_chars=0)
        assert len(result) >= 2

    def test_overlap(self):
        paras = ["a" * 40, "b" * 40, "c" * 40]
        result = _merge_paragraphs(paras, max_chars=50, overlap_chars=30)
        assert all(r for r in result)


class TestChunkDocument:
    def test_basic_document(self):
        text = "This is a simple document.\n\nIt has multiple paragraphs.\n\nThe last one."
        result = chunk_document(text)
        assert len(result.chunks) >= 1

    def test_empty_document(self):
        result = chunk_document("")
        assert result.chunks == []
