"""Batch-generates real audio for lesson `listening` blocks and the
placement-bank's listening items, via the configured TTS provider —
writing the resulting `audio_url` back into the source YAML content files
so it survives the next `sync_content` run (same "additive JSON field"
pattern already used for `summary_ru`, see docs/decisions.md).

Idempotent: each inserted `audio_url` line carries a `# src-hash: <hash>`
comment of the transcript it was generated from. A rerun only regenerates
entries whose transcript changed since the comment was written.

Not a test — this calls a real external TTS provider and writes files
under content/. Run manually:

    docker compose up -d tts
    uv run python -m scripts.generate_audio [--only SLUG [SLUG ...]]
"""

import argparse
import asyncio
import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

import yaml

from app.integrations.tts.factory import get_tts_provider
from app.integrations.tts.provider import TTSProvider
from app.services.content_loader import PLACEMENT_BANK_DIR_NAME

CONTENT_DIR = Path("content")
AUDIO_DIR = CONTENT_DIR / "audio"

NOTE_PLACEHOLDER_MARKERS = ("Audio recording pending", "Аудиозапись появится позже")
SRC_HASH_RE = re.compile(r"#\s*src-hash:\s*([0-9a-f]+)")


@dataclass
class Stats:
    generated: int = 0
    skipped: int = 0


def text_hash(text: str) -> str:
    return hashlib.sha256(text.strip().encode()).hexdigest()[:8]


def clean_for_speech(text: str) -> str:
    """Turns an authored dialogue transcript into plain narration text.

    Kokoro is a single-voice synthesizer, so "A: ... B: ..." speaker labels
    would just be read aloud as literal letters — stripped instead, with the
    turn separator ("A: ... — B: ...") replaced by a sentence break.
    """
    text = re.sub(r"^Transcript\s*[—-]\s*", "", text.strip())
    text = re.sub(r"\b[A-Z]:\s*", "", text)
    text = text.replace(" — ", ". ")
    return re.sub(r"\s+", " ", text).strip()


def _find_index(lines: list[str], predicate, start: int = 0) -> int:
    for i in range(start, len(lines)):
        if predicate(lines[i]):
            return i
    raise ValueError(f"no matching line found from index {start}")


def _line_indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _existing_hash(line: str) -> str | None:
    match = SRC_HASH_RE.search(line)
    return match.group(1) if match else None


async def process_lesson_file(provider: TTSProvider, path: Path, stats: Stats) -> None:
    raw_text = path.read_text()
    data = yaml.safe_load(raw_text)
    listening_blocks = [b for b in data.get("blocks", []) if b.get("type") == "listening"]
    if not listening_blocks:
        return

    slug = data["lesson"]["slug"]
    transcript = listening_blocks[0]["content"]["transcript"]
    speech_text = clean_for_speech(transcript)
    current_hash = text_hash(speech_text)
    audio_path = AUDIO_DIR / f"{slug}.mp3"

    lines = raw_text.splitlines(keepends=True)
    audio_line_index = None
    try:
        audio_line_index = _find_index(lines, lambda line: line.lstrip().startswith("audio_url:"))
    except ValueError:
        pass

    existing_hash = (
        _existing_hash(lines[audio_line_index]) if audio_line_index is not None else None
    )
    if existing_hash == current_hash and audio_path.exists():
        stats.skipped += 1
        return

    audio_bytes = await provider.synthesize(speech_text)
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    audio_path.write_bytes(audio_bytes)

    target_index = audio_line_index
    if target_index is None:
        target_index = _find_index(
            lines,
            lambda line: (
                line.lstrip().startswith("note:")
                and any(marker in line for marker in NOTE_PLACEHOLDER_MARKERS)
            ),
        )
    new_line = (
        f'{" " * _line_indent(lines[target_index])}audio_url: "/audio/{slug}.mp3"'
        f"  # src-hash: {current_hash}\n"
    )
    lines[target_index] = new_line
    path.write_text("".join(lines))
    stats.generated += 1
    print(f"generated: {slug}")


async def process_placement_bank(provider: TTSProvider, path: Path, stats: Stats) -> None:
    data = yaml.safe_load(path.read_text())
    listening_items = [item for item in data["items"] if item.get("skill") == "listening"]

    for item in listening_items:
        slug = item["slug"]
        speech_text = clean_for_speech(item["prompt"]["passage"])
        current_hash = text_hash(speech_text)
        audio_path = AUDIO_DIR / f"{slug}.mp3"

        # Re-read from disk every iteration: an earlier item in this same
        # loop may have inserted a line and shifted everything below it.
        lines = path.read_text().splitlines(keepends=True)
        item_index = _find_index(lines, lambda line, slug=slug: line.strip() == f"- slug: {slug}")
        prompt_index = _find_index(lines, lambda line: line.strip() == "prompt:", start=item_index)
        audio_line_index = (
            prompt_index + 1 if lines[prompt_index + 1].lstrip().startswith("audio_url:") else None
        )
        existing_hash = (
            _existing_hash(lines[audio_line_index]) if audio_line_index is not None else None
        )
        if existing_hash == current_hash and audio_path.exists():
            stats.skipped += 1
            continue

        audio_bytes = await provider.synthesize(speech_text)
        AUDIO_DIR.mkdir(parents=True, exist_ok=True)
        audio_path.write_bytes(audio_bytes)

        child_indent = _line_indent(lines[prompt_index + 1])
        new_line = (
            f'{" " * child_indent}audio_url: "/audio/{slug}.mp3"  # src-hash: {current_hash}\n'
        )
        if audio_line_index is not None:
            lines[audio_line_index] = new_line
        else:
            lines.insert(prompt_index + 1, new_line)
        path.write_text("".join(lines))
        stats.generated += 1
        print(f"generated: {slug}")


async def main(only: list[str] | None) -> None:
    provider = get_tts_provider()
    stats = Stats()

    for content_path in sorted(CONTENT_DIR.rglob("*.yaml")):
        if content_path.parent.name == PLACEMENT_BANK_DIR_NAME:
            continue
        if only and not any(slug in content_path.stem for slug in only):
            continue
        await process_lesson_file(provider, content_path, stats)

    bank_path = CONTENT_DIR / PLACEMENT_BANK_DIR_NAME / "bank.yaml"
    if bank_path.exists() and not only:
        await process_placement_bank(provider, bank_path, stats)

    print(f"done: {stats.generated} generated, {stats.skipped} already up to date")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--only",
        nargs="+",
        help="Only process lesson files whose slug contains one of these substrings",
    )
    args = parser.parse_args()
    asyncio.run(main(args.only))
