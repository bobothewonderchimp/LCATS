"""Shared single-stage benchmark harness reused by every candidate/*/benchmark.py.

Each candidate directory (anthropic_opus/, ollama_qwen3_8b/, ...) builds its
own LLMBackend and calls run_entity_extraction() with it, so adding a new
model to compare means adding one new directory, not touching this file.

Deliberately narrow scope for now: one ERW stage (entity extraction, stage 3
of the Event-Role-World pipeline - see
experiments/03_cross_segment_relation_pilot/run_pilot.py), one fixed sample
segment, one tool-schema call. This is the same call shape run_pilot.py's
real pipeline makes (JSONPromptExtractor.extract() via
lcats.analysis.event_role_world.entity_extractor.make_entity_extractor()),
so a "does this backend/model handle our actual tool schema" answer here
transfers directly - it is not a synthetic/toy schema. Widening to more
stages (segmentation, event/relation/discourse, cross-segment) or more
stories is a straightforward extension once single-stage numbers justify it.

Uses a REAL, single scene/sequel segment (see sample_segment.json,
generated once by generate_sample_segment.py from the real stage-1
segmenter) rather than a whole story - entity_extractor's own system
prompt describes its input as "a segment of a story"
(entity_extractor.py's ENTITY_SYSTEM_PROMPT), and the real pipeline
(run_pilot.py's _run_erw_extraction) only ever passes one segment to this
extractor, never a full story. Benchmarking against the wrong input size
inflated cost/latency for every candidate and gave a smaller/weaker local
model a harder, more diffuse task than it will ever actually face.
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

# A real, single scene/sequel segment - see this module's docstring and
# generate_sample_segment.py. Regenerate only if DEFAULT_SAMPLE_STORY
# (below) changes.
DEFAULT_SAMPLE_SEGMENT = pathlib.Path(__file__).resolve().parent / "sample_segment.json"

# The whole story generate_sample_segment.py drew DEFAULT_SAMPLE_SEGMENT
# from - kept only for that regeneration step, not used as benchmark input
# directly (see the module docstring for why a whole story is the wrong
# input size for this stage).
DEFAULT_SAMPLE_STORY = (
    pathlib.Path(__file__).resolve().parents[3].parent
    / "corpora"
    / "sherlock"
    / "five_orange_pips"
    / "story.json"
)

# A middle ground: entity_extractor.make_entity_extractor()'s own factory
# default (4096) turned out too low even for claude-opus-4-8 on a real
# ~600-word segment - confirmed live, it truncated
# (TruncatedResponseError) with entities/mentions/quotes still mid-
# generation - which is exactly why run_pilot.py raises it to 16384 in
# the first place (its own comment: "JSONPromptExtractor's own default
# (4096) is far below what a content-dense segment can need"). But
# 16384 (run_pilot.py's _ERW_MAX_TOKENS, tuned for whole-story-sized
# input) let one local-model run ramble for ~29 minutes before finally
# emitting a tool call on the old, oversized whole-story input this
# harness used to send. 8192 is a segment-appropriate middle ground,
# confirmed sufficient for both candidates on the real sample segment.
DEFAULT_MAX_TOKENS = 8192

# entity_extractor.py's own factory default. Appropriate for Anthropic/
# OpenAI's mature structured-output paths, but well below Qwen3's own
# officially recommended sampling settings (temperature 0.6 thinking /
# 0.7 non-thinking - see https://huggingface.co/Qwen/Qwen3-8B) and below
# Ollama's own bundled Modelfile default for qwen3:8b (`ollama show
# qwen3:8b --parameters` on this machine reports temperature 0.6, top_k
# 20, top_p 0.95, i.e. Ollama already ships the model card's own
# recommendation - our request's explicit `temperature=0.2` was
# overriding a better-tuned default). Qwen3's model card explicitly warns
# against near-greedy decoding: "Do NOT use greedy decoding, as it can
# lead to performance degradation and endless repetitions." Candidates
# for models with their own documented sampling recommendation should
# override this via `temperature=` rather than inherit the pipeline's
# Anthropic/OpenAI-tuned default.
DEFAULT_TEMPERATURE = 0.2

# Truncated in results.json so a failed/malformed run can be diagnosed
# after the fact without needing a live rerun (the prior version of this
# harness discarded raw model output entirely).
_RAW_OUTPUT_PREVIEW_CHARS = 4000


@dataclasses.dataclass
class BenchmarkResult:
    """One candidate's outcome for one stage/segment - written to results.json."""

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
    raw_output_preview: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return dataclasses.asdict(self)


def load_sample_story(path: pathlib.Path = DEFAULT_SAMPLE_STORY) -> tuple:
    """Return (story_name, story_body) from a story.json ({name, body, metadata}).

    Only used by generate_sample_segment.py to regenerate
    DEFAULT_SAMPLE_SEGMENT - not used as direct benchmark input, see this
    module's docstring.
    """
    data = json.loads(path.read_text(encoding="utf-8"))
    return data["name"], data["body"]


def load_sample_segment(path: pathlib.Path = DEFAULT_SAMPLE_SEGMENT) -> tuple:
    """Return (label, segment_text) from a sample_segment.json fixture.

    `label` combines the source story name and segment type/id for
    result readability, e.g. "Sherlock Holmes - The Five Orange Pips
    [segment 3, dramatic_sequel]".
    """
    data = json.loads(path.read_text(encoding="utf-8"))
    label = (
        f"{data['source_story']} "
        f"[segment {data['segment_id']}, {data['segment_type']}]"
    )
    return label, data["body"]


def run_entity_extraction(
    *,
    candidate: str,
    backend_kind: str,
    backend: llm_backend.LLMBackend,
    model: str,
    segment_path: pathlib.Path = DEFAULT_SAMPLE_SEGMENT,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    temperature: float = DEFAULT_TEMPERATURE,
) -> BenchmarkResult:
    """Run the real ERW stage-3 entity extractor's tool-schema call once.

    Uses the same make_entity_extractor()/extract() path run_pilot.py's real
    pipeline uses - the only things a candidate substitutes are `backend`,
    `model`, and optionally `temperature` (see DEFAULT_TEMPERATURE's
    docstring - override this for models with their own documented
    sampling recommendation).
    """
    story_name, segment_text = load_sample_segment(segment_path)

    extractor = erw_entity.make_entity_extractor(backend)
    extractor.default_model = model
    extractor.max_tokens = max_tokens
    extractor.temperature = temperature

    start = time.monotonic()
    try:
        result = extractor.extract(segment_text, model_name=model)
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
    raw_output = result.get("raw_output") or ""

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
        raw_output_preview=(raw_output[:_RAW_OUTPUT_PREVIEW_CHARS] or None),
    )


def save_result(result: BenchmarkResult, candidate_dir: pathlib.Path) -> pathlib.Path:
    """Write result.to_dict() to <candidate_dir>/results.json, return the path."""
    out_path = candidate_dir / "results.json"
    out_path.write_text(json.dumps(result.to_dict(), indent=2) + "\n", encoding="utf-8")
    return out_path
