"""Validate Golden QA dataset."""

import json
from pathlib import Path

GOLDEN_PATH = Path(__file__).resolve().parents[2] / "data" / "golden_qa.jsonl"
REQUIRED_TYPES = {"single_hop", "multi_hop", "rejection"}
REQUIRED_CATEGORIES = {"his", "erp", "workpal"}


def test_golden_qa_has_minimum_entries() -> None:
    items = _load()
    assert len(items) >= 20, f"expected >= 20 entries, got {len(items)}"


def test_golden_qa_schema_and_coverage() -> None:
    items = _load()
    types_seen: set[str] = set()
    categories_seen: set[str] = set()
    for item in items:
        assert "id" in item and "question" in item and "expected_answer" in item
        assert item["category"] in REQUIRED_CATEGORIES
        types_seen.add(item["type"])
        categories_seen.add(item["category"])
    assert REQUIRED_TYPES <= types_seen
    assert categories_seen == REQUIRED_CATEGORIES


def _load() -> list[dict]:
    rows: list[dict] = []
    with GOLDEN_PATH.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows
