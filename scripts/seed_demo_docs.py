#!/usr/bin/env python3
"""Import demo documents into BizMind (idempotent by content hash).

Usage:
    cd backend && uv run python ../scripts/seed_demo_docs.py
    docker compose exec backend uv run python /app/scripts/seed_demo_docs.py
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import os
import sys
from pathlib import Path

DEMO_ROOT = Path(__file__).resolve().parent.parent / "data" / "demo_docs"
ALLOWED_SUFFIXES = {".md", ".markdown", ".pdf"}
DEMO_TENANT = "Demo Corp"
DEMO_EMAIL = "demo@bizmind.local"
DEMO_PASSWORD = "DemoPass123!"


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


async def _seed() -> int:
    from sqlalchemy import select

    from app.db.session import AsyncSessionLocal
    from app.models import Document, Tenant, User
    from app.services.auth_service import _hash_password
    from app.services.document_service import upload_document
    from app.services.indexing_service import run_indexing

    print("Seeding BizMind demo data...")

    async with AsyncSessionLocal() as session:
        # 1. Create or get Demo Corp tenant
        result = await session.execute(
            select(Tenant).where(Tenant.name == DEMO_TENANT)
        )
        tenant = result.scalar_one_or_none()
        if tenant is None:
            tenant = Tenant(name=DEMO_TENANT)
            session.add(tenant)
            await session.flush()
            print(f"  Created tenant: {DEMO_TENANT}")
        else:
            print(f"  Tenant already exists: {DEMO_TENANT}")

        # 2. Create or get demo user
        result = await session.execute(
            select(User).where(User.email == DEMO_EMAIL)
        )
        user = result.scalar_one_or_none()
        if user is None:
            user = User(
                tenant_id=tenant.id,
                email=DEMO_EMAIL,
                password_hash=_hash_password(DEMO_PASSWORD),
            )
            session.add(user)
            await session.flush()
            print(f"  Created user: {DEMO_EMAIL} (password: {DEMO_PASSWORD})")
        else:
            print(f"  User already exists: {DEMO_EMAIL}")
        await session.commit()

        # 3. Upload and index demo files
        files = discover_demo_files(DEMO_ROOT)
        if not files:
            print(f"No demo files found under {DEMO_ROOT}", file=sys.stderr)
            return 1

        print(f"  Found {len(files)} demo file(s)")

        for path in files:
            rel = path.relative_to(DEMO_ROOT)
            content_hash = file_content_hash(path)

            # Check if already indexed
            result = await session.execute(
                select(Document).where(
                    Document.tenant_id == tenant.id,
                    Document.content_hash == content_hash,
                )
            )
            if result.scalar_one_or_none() is not None:
                print(f"    SKIP {rel} (already indexed)")
                continue

            # Read file as binary
            content = path.read_bytes()
            filename = path.name
            ext = path.suffix.lower()

            mime_map = {".md": "text/markdown", ".markdown": "text/markdown", ".pdf": "application/pdf"}
            mime_type = mime_map.get(ext, "text/plain")

            # Save to storage
            settings_path = os.environ.get("STORAGE_PATH", "./data/uploads")
            os.makedirs(settings_path, exist_ok=True)
            import time
            safe_name = f"{int(time.time())}_{filename}"
            dest = os.path.join(settings_path, safe_name)
            with open(dest, "wb") as f:
                f.write(content)

            # Create DB record
            doc = Document(
                tenant_id=tenant.id,
                owner_id=user.id,
                filename=filename,
                mime_type=mime_type,
                storage_path=dest,
                content_hash=content_hash,
            )
            session.add(doc)
            await session.commit()
            await session.refresh(doc)

            print(f"    UPLOAD {rel} -> {doc.id}")
            await run_indexing(str(doc.id))
            print(f"    INDEX {rel} done")

    print("Seed complete!")
    return 0


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
        print("Dry run complete. Run without --dry-run to index.")
        return 0

    return asyncio.run(_seed())


if __name__ == "__main__":
    raise SystemExit(main())
