from functools import lru_cache
from pathlib import Path

_PROMPTS_DIR = Path(__file__).parent / "prompts"


@lru_cache
def load_prompt(name: str) -> str:
    """Load a versioned prompt file, e.g. `load_prompt("writing_feedback_v1")`.

    Prompts are files, not inline strings, so they're inspectable/diffable on
    their own and a new version can be added (`_v2.md`) without touching code.
    """
    return (_PROMPTS_DIR / f"{name}.md").read_text(encoding="utf-8").strip()
