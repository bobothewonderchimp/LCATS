"""One-time fixture generator: run REAL stage-1 segmentation once and cache
one real segment as sample_segment.json, so every candidate's benchmark.py
tests stage-3 entity extraction against a realistic-sized input instead of
an entire story.

Why this exists: harness.py used to hand entity_extractor.py's tool-schema
call the ENTIRE story body (~7,300 words for the default sample story),
while its own system prompt describes the input as "a segment of a story"
(see entity_extractor.py's ENTITY_SYSTEM_PROMPT/ENTITY_USER_PROMPT_TEMPLATE).
The real pipeline (run_pilot.py's _run_erw_extraction) only ever passes one
scene/sequel segment - coarse-grained but still a fraction of a whole story
per scene_analysis.py's "prefer FEWER, LARGER segments" rubric - to this
same extractor. Benchmarking against the wrong input size inflates cost/
latency for every candidate (undermining the cost comparison this harness
exists to make) and gives a smaller/weaker local model a harder, more
diffuse task than it will actually face in production.

Re-running real segmentation via an LLM call on every benchmark run would
be non-reproducible and add real cost to what should be a cheap, repeatable
check - so this script runs the real segmenter (scene_analysis.make_segment_extractor,
the exact same stage-1 extractor/alignment/validation path run_pilot.py
uses) ONCE against the harness's existing DEFAULT_SAMPLE_STORY, picks one
representative dramatic_scene/dramatic_sequel segment, and writes its
already-aligned text to sample_segment.json. Regenerate only if
DEFAULT_SAMPLE_STORY changes.

Usage (from anywhere, makes one real, billable Anthropic API call):
    python lcats/experimental/model_comparison/common/generate_sample_segment.py
"""

from __future__ import annotations

import json
import pathlib
import sys

_HERE = pathlib.Path(__file__).resolve().parent
_MODEL_COMPARISON = _HERE.parent
_LCATS_SRC = _MODEL_COMPARISON.parent / "src"
for _path in (_LCATS_SRC, _MODEL_COMPARISON):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from lcats.analysis import scene_analysis  # noqa: E402
from lcats.llm import anthropic_backend  # noqa: E402
from lcats.utils.secrets import load_secrets  # noqa: E402

from common import harness  # noqa: E402

MODEL = "claude-opus-4-8"
OUTPUT_PATH = _HERE / "sample_segment.json"

# Prefer a real dramatic_scene/dramatic_sequel (the types the real pipeline
# actually runs entity/event/relation/discourse extraction on - see
# run_pilot.py's _run_erw_extraction, which slices body[start_char:end_char]
# for every returned segment regardless of type, but "other"/very short
# narrative_scene segments are less representative of a typical call).
_PREFERRED_TYPES = ("dramatic_scene", "dramatic_sequel")


def _pick_segment(segments: list) -> dict:
    """Pick one aligned, moderate-length segment closest to a few hundred words."""
    aligned = [
        s
        for s in segments
        if s.get("start_char") is not None and s.get("end_char") is not None
    ]
    if not aligned:
        raise RuntimeError("Segmentation produced no aligned segments to pick from.")
    preferred = [s for s in aligned if s.get("segment_type") in _PREFERRED_TYPES]
    candidates = preferred or aligned

    def word_count(seg: dict) -> int:
        return seg["end_char"] - seg["start_char"]

    # Closest to a 1000-character segment (~150-200 words) - representative
    # of a single coarse scene/sequel, not a whole story.
    return min(candidates, key=lambda s: abs(word_count(s) - 1000))


def main() -> None:
    load_secrets()
    story_name, story_body = harness.load_sample_story()

    backend = anthropic_backend.AnthropicBackend()
    extractor = scene_analysis.make_segment_extractor(backend)
    extractor.default_model = MODEL
    extractor.max_tokens = 16384

    result = extractor.extract(story_body, model_name=MODEL)
    if result.get("api_error"):
        raise RuntimeError(f"Segmentation failed: {result['api_error']}")

    segments = result["extracted_output"]
    chosen = _pick_segment(segments)
    segment_text = story_body[chosen["start_char"] : chosen["end_char"]]

    fixture = {
        "source_story": story_name,
        "segment_id": chosen.get("segment_id"),
        "segment_type": chosen.get("segment_type"),
        "summary": chosen.get("summary"),
        "word_count": len(segment_text.split()),
        "char_count": len(segment_text),
        "body": segment_text,
    }
    OUTPUT_PATH.write_text(json.dumps(fixture, indent=2) + "\n", encoding="utf-8")
    print(
        f"Wrote {OUTPUT_PATH} ({fixture['word_count']} words, {fixture['segment_type']})"
    )


if __name__ == "__main__":
    main()
