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
from io import BytesIO
from pathlib import Path

import yaml
from pydub import AudioSegment

from app.integrations.tts.factory import get_tts_provider
from app.integrations.tts.provider import TTSProvider
from app.services.content_loader import PLACEMENT_BANK_DIR_NAME

CONTENT_DIR = Path("content")
AUDIO_DIR = CONTENT_DIR / "audio"

NOTE_PLACEHOLDER_MARKERS = ("Audio recording pending", "Аудиозапись появится позже")
SRC_HASH_RE = re.compile(r"#\s*src-hash:\s*([0-9a-f]+)")
TURN_RE = re.compile(r"([A-Z]):\s*")

# Every authored lesson dialogue uses exactly two speaker letters, A and B
# (confirmed by scanning all of content/**/*.yaml) — a fixed two-voice map
# is enough, no need for a per-lesson or per-speaker-count scheme. See
# docs/decisions.md, 2026-08-25 live-feedback round. Swapped 2026-08-28
# after the user reported the original A=af_heart/B=am_adam pairing sounded
# gender-reversed on actual playback.
DIALOGUE_VOICES = {"A": "am_adam", "B": "af_heart"}
DEFAULT_DIALOGUE_VOICE = DIALOGUE_VOICES["A"]
SILENCE_BETWEEN_TURNS_MS = 300


@dataclass
class Stats:
    generated: int = 0
    skipped: int = 0


def text_hash(text: str) -> str:
    return hashlib.sha256(text.strip().encode()).hexdigest()[:8]


def split_into_turns(text: str) -> list[tuple[str, str]]:
    """Splits a "A: ... — B: ... — A: ..." transcript into (speaker, text)
    turns, keeping the speaker labels so each turn can be synthesized in
    that speaker's own voice.

    Splitting on the `X:` label itself, rather than on the " — " turn
    separator, matters: a turn's own text can contain a literal em dash
    ("...my friend Mark — he's a doctor") that isn't a speaker change.
    """
    text = re.sub(r"^Transcript\s*[—-]\s*", "", text.strip())
    parts = TURN_RE.split(text)
    turns: list[tuple[str, str]] = []
    for i in range(1, len(parts), 2):
        speaker = parts[i]
        spoken = re.sub(r"\s*—\s*$", "", parts[i + 1].strip())
        spoken = re.sub(r"\s+", " ", spoken).strip()
        if spoken:
            turns.append((speaker, spoken))
    return turns


async def synthesize_dialogue(provider: TTSProvider, turns: list[tuple[str, str]]) -> bytes:
    """Synthesizes each turn in its speaker's own voice and splices the
    results into one mp3, with a short silence between turns."""
    combined = AudioSegment.empty()
    silence = AudioSegment.silent(duration=SILENCE_BETWEEN_TURNS_MS)
    for i, (speaker, text) in enumerate(turns):
        voice = DIALOGUE_VOICES.get(speaker, DEFAULT_DIALOGUE_VOICE)
        audio_bytes = await provider.synthesize(text, voice=voice)
        combined += AudioSegment.from_file(BytesIO(audio_bytes), format="mp3")
        if i < len(turns) - 1:
            combined += silence

    buffer = BytesIO()
    # Match Kokoro's own default mp3 bitrate — pydub's export default (32k)
    # is a noticeable quality drop from what the user already praised.
    combined.export(buffer, format="mp3", bitrate="128k")
    return buffer.getvalue()


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


async def process_lesson_file(
    provider: TTSProvider, path: Path, stats: Stats, *, force: bool = False
) -> None:
    raw_text = path.read_text()
    data = yaml.safe_load(raw_text)
    listening_blocks = [b for b in data.get("blocks", []) if b.get("type") == "listening"]
    if not listening_blocks:
        return

    slug = data["lesson"]["slug"]
    transcript = listening_blocks[0]["content"]["transcript"]
    turns = split_into_turns(transcript)
    current_hash = text_hash("|".join(f"{speaker}:{text}" for speaker, text in turns))
    audio_path = AUDIO_DIR / f"{slug}.mp3"

    lines = raw_text.splitlines(keepends=True)
    # A listening_comprehension exercise item (if authored) has its own
    # `audio_url:` line earlier in the file, reusing the same audio — start
    # the search after the `listening` block's own header so that one, not
    # the exercise's copy, is what gets tracked/rewritten.
    listening_header_index = _find_index(lines, lambda line: line.strip() == "- type: listening")
    audio_line_index = None
    try:
        audio_line_index = _find_index(
            lines,
            lambda line: line.lstrip().startswith("audio_url:"),
            start=listening_header_index,
        )
    except ValueError:
        pass

    existing_hash = (
        _existing_hash(lines[audio_line_index]) if audio_line_index is not None else None
    )
    if not force and existing_hash == current_hash and audio_path.exists():
        stats.skipped += 1
        return

    audio_bytes = await synthesize_dialogue(provider, turns)
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
            start=listening_header_index,
        )
    new_line = (
        f'{" " * _line_indent(lines[target_index])}audio_url: "/audio/{slug}.mp3"'
        f"  # src-hash: {current_hash}\n"
    )
    lines[target_index] = new_line
    path.write_text("".join(lines))
    stats.generated += 1
    print(f"generated: {slug}")


async def process_placement_bank(
    provider: TTSProvider, path: Path, stats: Stats, *, force: bool = False
) -> None:
    data = yaml.safe_load(path.read_text())
    listening_items = [item for item in data["items"] if item.get("skill") == "listening"]

    for item in listening_items:
        slug = item["slug"]
        turns = split_into_turns(item["prompt"]["passage"])
        current_hash = text_hash("|".join(f"{speaker}:{text}" for speaker, text in turns))
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
        if not force and existing_hash == current_hash and audio_path.exists():
            stats.skipped += 1
            continue

        audio_bytes = await synthesize_dialogue(provider, turns)
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


async def main(only: list[str] | None, *, force: bool = False) -> None:
    provider = get_tts_provider()
    stats = Stats()

    for content_path in sorted(CONTENT_DIR.rglob("*.yaml")):
        if content_path.parent.name == PLACEMENT_BANK_DIR_NAME:
            continue
        if only and not any(slug in content_path.stem for slug in only):
            continue
        await process_lesson_file(provider, content_path, stats, force=force)

    bank_path = CONTENT_DIR / PLACEMENT_BANK_DIR_NAME / "bank.yaml"
    if bank_path.exists() and not only:
        await process_placement_bank(provider, bank_path, stats, force=force)

    print(f"done: {stats.generated} generated, {stats.skipped} already up to date")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--only",
        nargs="+",
        help="Only process lesson files whose slug contains one of these substrings",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Regenerate even if the tracked hash already matches (e.g. after a voice-mapping "
        "change, which doesn't affect the transcript hash)",
    )
    args = parser.parse_args()
    asyncio.run(main(args.only, force=args.force))
