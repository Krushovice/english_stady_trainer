from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from app.models.lesson_block import BlockType
from app.schemas.content import LessonFile

CONTENT_DIR = Path(__file__).resolve().parent.parent.parent / "content"


def _lesson_files() -> list[Path]:
    return sorted(CONTENT_DIR.rglob("*.yaml"))


def test_content_directory_has_at_least_one_lesson() -> None:
    assert _lesson_files()


@pytest.mark.parametrize("path", _lesson_files(), ids=lambda p: p.stem)
def test_lesson_file_matches_schema(path: Path) -> None:
    raw = yaml.safe_load(path.read_text())
    lesson_file = LessonFile.model_validate(raw)

    assert lesson_file.lesson.slug
    assert lesson_file.blocks


def test_making_small_talk_covers_every_block_type() -> None:
    path = CONTENT_DIR / "b1" / "small-talk" / "making-small-talk.yaml"
    raw = yaml.safe_load(path.read_text())
    lesson_file = LessonFile.model_validate(raw)

    block_types = {block.type for block in lesson_file.blocks}
    assert block_types == set(BlockType)


def test_invalid_block_type_is_rejected() -> None:
    with pytest.raises(ValidationError):
        LessonFile.model_validate(
            {
                "level": {"code": "B1", "order_index": 3},
                "module": {"slug": "x", "title": "X", "order_index": 1},
                "lesson": {"slug": "x", "title": "X", "order_index": 1},
                "blocks": [{"type": "not-a-real-type", "order_index": 1, "content": {}}],
            }
        )
