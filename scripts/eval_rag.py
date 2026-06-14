#!/usr/bin/env python3
"""Run RAGAS evaluation against golden_qa.jsonl.

Usage:
    cd backend && uv run python ../scripts/eval_rag.py --mode both --dry-run
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

GOLDEN_QA_PATH = Path(__file__).resolve().parent.parent / "data" / "golden_qa.jsonl"


def load_golden_qa(path: Path) -> list[dict]:
    items: list[dict] = []
    with path.open(encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            items.append(json.loads(line))
    return items


def main() -> int:
    parser = argparse.ArgumentParser(description="BizMind RAGAS evaluation")
    parser.add_argument("--mode", choices=["baseline", "agent", "both"], default="both")
    parser.add_argument("--dataset", type=Path, default=GOLDEN_QA_PATH)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    if not args.dataset.exists():
        print(f"Dataset not found: {args.dataset}", file=sys.stderr)
        return 1

    items = load_golden_qa(args.dataset)
    print(f"Loaded {len(items)} golden QA items from {args.dataset}")
    print(f"Mode: {args.mode}")

    if args.dry_run:
        categories = sorted({item.get("category", "?") for item in items})
        print(f"Categories: {', '.join(categories)}")
        return 0

    print("RAGAS batch runner not implemented yet — complete in P4.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
