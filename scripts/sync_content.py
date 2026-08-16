"""Sync course content from `content/` into the database.

Usage:
    uv run python -m scripts.sync_content
"""

import asyncio
from pathlib import Path

from app.core.db import async_session_factory
from app.services.content_loader import ContentLoaderService

# Relative to the current working directory (repo root), not resolved to an
# absolute path, so the `content_path` stored on each lesson stays portable
# between local dev and the Docker container (both run this from repo root).
CONTENT_DIR = Path("content")


async def main() -> None:
    async with async_session_factory() as session:
        lessons = await ContentLoaderService(session).sync_directory(CONTENT_DIR)
    for lesson in lessons:
        print(f"synced: {lesson.slug}")


if __name__ == "__main__":
    asyncio.run(main())
