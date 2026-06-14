#!/usr/bin/env python3
"""Import demo documents into BizMind (idempotent by content hash).

Usage:
    cd backend && uv run python ../scripts/seed_demo_docs.py
    docker compose exec backend uv run python /app/scripts/seed_demo_docs.py
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

DEMO_ROOT = Path(__file__).resolve().parent.parent / "data" / "demo_docs"
ALLOWED_SUFFIXES = {".md", ".markdown", ".pdf"}


def file_content_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def discover_demo_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    files: list[Path] = []
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.suffix.lower() in ALLOWED_SUFFIXES:
            if path.name.upper() == "DISCLAIMER.MD":
                continue
            files.append(path)
    return files


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed BizMind demo documents")
    parser.add_argument("--dry-run", action="store_true", help="List files only, do not index")
    parser.add_argument("--demo-root", type=Path, default=DEMO_ROOT)
    args = parser.parse_args()

    files = discover_demo_files(args.demo_root)
    if not files:
        print(f"No demo files found under {args.demo_root}", file=sys.stderr)
        return 1

    print(f"Found {len(files)} demo file(s):")
    for path in files:
        rel = path.relative_to(args.demo_root)
        digest = file_content_hash(path)
        print(f"  - {rel}  sha256={digest[:12]}...")

    if args.dry_run:
        print("Dry run complete. Wire DocumentService.index in P1-06.")
        return 0

    # P1-06: call DocumentService.upload_and_index for each file (tenant Demo Corp)
    print("Indexing not implemented yet — complete task P1-06/P1-11.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
