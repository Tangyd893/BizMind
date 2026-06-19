"""Tests for eval_service — dataset loading and eval run listing."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.eval_service import _load_dataset, list_eval_runs, get_eval_run


class TestLoadDataset:
    """Tests for _load_dataset."""

    def test_load_valid_jsonl(self, tmp_path, monkeypatch):
        """Should parse a valid JSONL file."""
        jsonl_path = tmp_path / "golden_qa.jsonl"
        jsonl_path.write_text(
            '{"question": "Q1", "expected_answer": "A1"}\n'
            '{"question": "Q2", "expected_answer": "A2"}\n',
            encoding="utf-8",
        )

        # Override storage_path so dataset is resolved relative to tmp_path
        from app.config import get_settings
        monkeypatch.setattr(get_settings(), "storage_path", str(tmp_path))

        result = _load_dataset()
        assert len(result) == 2
        assert result[0]["question"] == "Q1"
        assert result[1]["expected_answer"] == "A2"

    def test_load_empty_file(self, tmp_path, monkeypatch):
        """Empty file → empty list."""
        jsonl_path = tmp_path / "golden_qa.jsonl"
        jsonl_path.write_text("", encoding="utf-8")

        from app.config import get_settings
        monkeypatch.setattr(get_settings(), "storage_path", str(tmp_path))

        result = _load_dataset()
        assert result == []

    def test_load_missing_file(self, tmp_path, monkeypatch):
        """Missing file → empty list."""
        from app.config import get_settings
        monkeypatch.setattr(get_settings(), "storage_path", str(tmp_path))

        result = _load_dataset()
        assert result == []

    def test_load_with_custom_name_existing_file(self, tmp_path):
        """Custom dataset name that points to an existing file."""
        custom_path = tmp_path / "custom_qa.jsonl"
        custom_path.write_text(
            '{"question": "C1", "answer": "CA1"}\n',
            encoding="utf-8",
        )

        result = _load_dataset(name=str(custom_path))
        assert len(result) == 1
        assert result[0]["question"] == "C1"

    def test_load_with_custom_name_nonexistent_file(self, tmp_path, monkeypatch):
        """Custom name that doesn't exist → falls back to default, then empty."""
        from app.config import get_settings
        monkeypatch.setattr(get_settings(), "storage_path", str(tmp_path))

        result = _load_dataset(name="nonexistent_file.jsonl")
        assert result == []

    def test_load_skips_blank_lines(self, tmp_path, monkeypatch):
        """Blank lines in JSONL are skipped."""
        jsonl_path = tmp_path / "golden_qa.jsonl"
        jsonl_path.write_text(
            '{"question": "Q1", "expected_answer": "A1"}\n'
            '\n'
            '{"question": "Q2", "expected_answer": "A2"}\n',
            encoding="utf-8",
        )

        from app.config import get_settings
        monkeypatch.setattr(get_settings(), "storage_path", str(tmp_path))

        result = _load_dataset()
        assert len(result) == 2
