"""Shared single-stage benchmark harness reused by every candidate/*/benchmark.py.

Each candidate directory (anthropic_opus/, ollama_qwen3_8b/, ...) builds its
own LLMBackend and calls run_entity_extraction() with it, so adding a new
model to compare means adding one new directory, not touching this file.

Deliberately narrow scope for now: one ERW stage (entity extraction, stage 3
of the Event-Role-World pipeline - see
experiments/03_cross_segment_relation_pilot/run_pilot.py), one fixed sample
story, one tool-schema call. This is the same call shape
run_pilot.py's real pipeline makes (JSONPromptExtractor.extract() via
lcats.analysis.event_role_world.entity_extractor.make_entity_extractor()),
so a "does this backend/model handle our actual tool schema" answer here
transfers directly - it is not a synthetic/toy schema. Widening to more
stages (segmentation, event/relation/discourse, cross-segment) or more
stories is a straightforward extension once single-stage numbers justify it.
"""

from __future__ import annotations

import dataclasses
import json
import pathlib
import sys
import time

from typing import Any, Dict, Optional

# Path bootstrap - allow running `python <candidate>/benchmark.py` directly
# without a prior `pip install -e .`, matching
# experiments/03_cross_segment_relation_pilot/run_pilot.py's convention.
_LCATS_SRC = pathlib.Path(__file__).resolve().parents[3] / "src"
if str(_LCATS_SRC) not in sys.path:
    sys.path.insert(0, str(_LCATS_SRC))

from lcats.analysis.event_role_world import entity_extractor as erw_entity  # noqa: E402
from lcats.llm import backend as llm_backend  # noqa: E402

# Fixed sample story for now - a real, moderately dense Sherlock Holmes
# mystery (multiple named entities, aliases, an investigator/culprit/victim
# structure) already used elsewhere in this repo's pilots. Keeping this
# fixed (rather than randomly sampled) makes benchmark.py runs across
# different candidates directly comparable.
DEFAULT_SAMPLE_STORY = (
    pathlib.Path(__file__).resolve().parents[3].parent
    / "corpora"
    / "sherlock"
    / "five_orange_pips"
    / "story.json"
)

# Same ceiling run_pilot.py uses for the real pipeline (see its
# _ERW_MAX_TOKENS) - a smaller default risks TruncatedResponseError on a
# content-dense story before any candidate even gets to answer the "did the
# JSON come back well-formed" question this harness is for.
DEFAULT_MAX_TOKENS = 16384


@dataclasses.dataclass
class BenchmarkResult:
    """One candidate's outcome for one stage/story - written to results.json."""

    candidate: str
    backend_kind: str
    model: str
    story_name: str
    stage: str
    success: bool
    latency_seconds: float
    input_tokens: int = 0
    output_tokens: int = 0
    entity_count: Optional[int] = None
    error_type: Optional[str] = None
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return dataclasses.asdict(self)


def load_sample_story(path: pathlib.Path = DEFAULT_SAMPLE_STORY) -> tuple:
    """Return (story_name, story_body) from a story.json ({name, body, metadata})."""
    data = json.loads(path.read_text(encoding="utf-8"))
    return data["name"], data["body"]


def run_entity_extraction(
    *,
    candidate: str,
    backend_kind: str,
    backend: llm_backend.LLMBackend,
    model: str,
    story_path: pathlib.Path = DEFAULT_SAMPLE_STORY,
    max_tokens: int = DEFAULT_MAX_TOKENS,
) -> BenchmarkResult:
    """Run the real ERW stage-3 entity extractor's tool-schema call once.

    Uses the same make_entity_extractor()/extract() path run_pilot.py's real
    pipeline uses - the only things a candidate substitutes are `backend`
    and `model`.
    """
    story_name, story_body = load_sample_story(story_path)

    extractor = erw_entity.make_entity_extractor(backend)
    extractor.default_model = model
    extractor.max_tokens = max_tokens

    start = time.monotonic()
    try:
        result = extractor.extract(story_body, model_name=model)
    except Exception as exc:  # noqa: BLE001 - benchmark harness records, not raises
        latency = time.monotonic() - start
        return BenchmarkResult(
            candidate=candidate,
            backend_kind=backend_kind,
            model=model,
            story_name=story_name,
            stage="entity_extraction",
            success=False,
            latency_seconds=latency,
            error_type=type(exc).__name__,
            error_message=str(exc),
        )
    latency = time.monotonic() - start

    api_error = result.get("api_error")
    parsed = result.get("extracted_output") or result.get("parsed_output") or {}
    entities = parsed.get("entities") if isinstance(parsed, dict) else None
    usage = result.get("usage") or {}

    # A tool call can come back schema-conformant enough to avoid api_error
    # (parses as JSON, no truncation) while still not matching
    # ENTITY_TOOL_SCHEMA - e.g. "entities" missing or not a list. That is
    # exactly the local-runtime tool-schema unreliability this harness
    # exists to catch, so it must not read as success.
    schema_error = None
    if api_error is None and not isinstance(entities, list):
        schema_error = "malformed_tool_result"

    return BenchmarkResult(
        candidate=candidate,
        backend_kind=backend_kind,
        model=model,
        story_name=story_name,
        stage="entity_extraction",
        success=api_error is None and schema_error is None,
        latency_seconds=latency,
        input_tokens=usage.get("input_tokens", 0) or 0,
        output_tokens=usage.get("output_tokens", 0) or 0,
        entity_count=len(entities) if isinstance(entities, list) else None,
        error_type=(api_error or {}).get("code") if api_error else schema_error,
        error_message=(
            (api_error or {}).get("message")
            if api_error
            else (
                "Tool result parsed but 'entities' was missing or not a "
                f"list (got {type(entities).__name__ if entities is not None else 'None'})."
                if schema_error
                else None
            )
        ),
    )


def save_result(result: BenchmarkResult, candidate_dir: pathlib.Path) -> pathlib.Path:
    """Write result.to_dict() to <candidate_dir>/results.json, return the path."""
    out_path = candidate_dir / "results.json"
    out_path.write_text(json.dumps(result.to_dict(), indent=2) + "\n", encoding="utf-8")
    return out_path
