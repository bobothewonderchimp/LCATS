"""Bounded, explicitly-approved real measurement of Anthropic prompt
caching against the WI-PILOT-0051 fixture set (WI-PILOT-0057, Decision 3
of PROP-LCATS-PILOT-COST-SUSTAINABILITY).

Runs the real entity/event/relation/discourse extraction sequence
(experiments/03_cross_segment_relation_pilot's own run_pilot.py machinery,
unmodified) over the fixture set twice - once with prompt caching enabled,
once without - recording every real call's cache_creation_input_tokens/
cache_read_input_tokens/input_tokens/output_tokens via _RecordingBackend,
a thin wrapper around any LLMBackend. Segmentation runs once and is
checkpointed (WI-PIPELINE-0040/0041), so it is not re-billed for the
second (disabled) comparison run.

_RecordingBackend preserves the real per-segment interleaved call order
(entity -> event_anchor -> relation -> discourse per segment, across
every segment/story) that lcats.analysis.event_role_world.processor
naturally produces - not an artificially same-extractor-grouped
sequence, which would overstate any real cache-hit rate given the
5-minute cache TTL (see the governing work item's own Risk Notes).

**Requires real, paid Anthropic API calls when run without --dry-run.**
Do not run against the real API without explicit, in-session human
approval - see WI-PILOT-0057's own forbidden_actions
(run_real_llm_calls_without_explicit_approval). --dry-run exercises the
full wiring with a FakeBackend at zero cost, for validating this script
itself before any real spend.

Usage:
    python measure_prompt_caching.py --dry-run
    python measure_prompt_caching.py --output-dir results/caching_eval
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

from typing import Any, Dict, List, Optional

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import run_pilot  # noqa: E402 - see sys.path.insert above

from lcats.utils import checkpoint  # noqa: E402


class _RecordingBackend:
    """Wraps any LLMBackend, recording every complete() call's
    BackendResponse fields in real chronological order.

    Delegates the actual call through unchanged - this is purely an
    observer, not a behavior change, so it is safe to wrap either a real
    backend or a FakeBackend for testing.
    """

    def __init__(self, inner: Any):
        self._inner = inner
        self.calls: List[Dict[str, Any]] = []

    def complete(self, **kwargs: Any):
        response = self._inner.complete(**kwargs)
        tool = kwargs.get("tool") or {}
        self.calls.append(
            {
                "tool_name": tool.get("name"),
                "model": response.model,
                "input_tokens": response.input_tokens,
                "output_tokens": response.output_tokens,
                "cache_creation_input_tokens": response.cache_creation_input_tokens,
                "cache_read_input_tokens": response.cache_read_input_tokens,
            }
        )
        return response


_DRY_RUN_SEGMENT_RESULT = {
    "segments": [
        {
            "segment_id": 1,
            "segment_type": "narrative_scene",
            "start_par_id": 1,
            "end_par_id": 1,
            "start_exact": "",
            "end_exact": "",
            "start_prefix": "",
            "end_suffix": "",
            "start_char": 0,
            "end_char": 1,
            "summary": "dry-run placeholder segment",
            "cohesion": {"time": "", "place": "", "characters": []},
            "gacd": None,
            "erac": None,
            "reason": "dry-run",
            "confidence": 0.5,
        }
    ]
}


class _DryRunFakeBackend:
    """Zero-cost stand-in for the real Anthropic backend under --dry-run.

    A plain FakeBackend(tool_result={}) fails segmentation's own hard
    "produced no segments" check (run_pilot._segment_story), so this
    returns a fixed single-segment result specifically for the
    "record_segments" tool call, and an empty-but-schema-tolerant result
    for every other call - real extraction stages handle an empty
    tool_result as "nothing found", not an error. Dispatches on the
    requested tool's name rather than call order/count, so a checkpoint
    hit on a later comparison run (which skips the segmentation call
    entirely - see run_pilot._segment_story_cached) can't shift which
    call this fake thinks is "the segmentation call".
    """

    def complete(self, **kwargs: Any):
        from lcats.llm import backend as llm_backend

        tool = kwargs.get("tool") or {}
        is_segment_call = tool.get("name") == "record_segments"
        tool_result = _DRY_RUN_SEGMENT_RESULT if is_segment_call else {}
        return llm_backend.BackendResponse(
            text="",
            tool_result=tool_result,
            model="fake-1.0",
            input_tokens=5,
            output_tokens=2,
            cache_creation_input_tokens=None,
            cache_read_input_tokens=None if is_segment_call else 0,
            raw=None,
        )


def _fixtures_dir() -> pathlib.Path:
    return pathlib.Path(__file__).resolve().parent / "fixtures"


def _fixture_stories() -> List[pathlib.Path]:
    """The WI-PILOT-0051 fixture set's committed stories, in a fixed,
    reproducible order (sorted by name) - not the manifest file, which
    also carries genre labels this measurement doesn't need."""
    return sorted(_fixtures_dir().glob("*/story.json"))


def preflight_prefix_token_counts(model: str) -> Dict[str, int]:
    """Count each ERW extractor's tools+system prefix token size via the
    Anthropic SDK's free (non-generation) count_tokens endpoint, before
    any real measurement call - a prefix below Anthropic's minimum
    cacheable-prefix length makes a zero cache_read_input_tokens result
    the *correct*, expected outcome, not a signal to investigate further
    (WI-PILOT-0057, Required Change 3).

    Still a real, live API call (network + auth), even though it is not
    a billed generation call - do not call this without the same
    explicit human approval real measurement calls require.
    """
    import anthropic

    client = anthropic.Anthropic()
    # backend=None: only .system_prompt/.tool_schema are read below: no
    # extractor.complete()/.extract() call is made, so no real backend
    # instance is needed to build these extractor objects.
    extractors = run_pilot._build_erw_extractors(None, model)
    counts: Dict[str, int] = {}
    for name, extractor in extractors.items():
        if extractor.tool_schema is None:
            continue
        tool = {**extractor.tool_schema, "cache_control": {"type": "ephemeral"}}
        result = client.messages.count_tokens(
            model=model,
            system=[
                {
                    "type": "text",
                    "text": extractor.system_prompt,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            tools=[tool],
            messages=[{"role": "user", "content": "x"}],
        )
        counts[name] = result.input_tokens
    return counts


def _segment_and_extract(
    story_path: pathlib.Path,
    backend: Any,
    model: str,
    roots: checkpoint.CheckpointRoots,
) -> Dict[str, Any]:
    """Segment (checkpointed) then run the real ERW extraction sequence
    for one fixture story, returning run_pilot._run_erw_extraction's own
    result dict. Reuses run_pilot's real, unmodified per-story pipeline
    pieces (WI-PILOT-0057 does not reimplement extraction logic)."""
    story = json.loads(story_path.read_text(encoding="utf-8"))
    body = story["body"]
    story_id = run_pilot._story_identity(story_path)

    segments, seg_error, _seg_usage = run_pilot._segment_story_cached(
        story_path, body, backend, model, "anthropic", roots
    )
    if seg_error:
        raise RuntimeError(f"{story_path}: segmentation failed: {seg_error}")

    extractors = run_pilot._build_erw_extractors(backend, model)
    nlp_backend = run_pilot._make_nlp_backend("fake")
    return run_pilot._run_erw_extraction(
        body, segments, extractors, nlp_backend, "fake", story_id
    )


def run_comparison(
    *,
    model: str,
    working_root: pathlib.Path,
    source_root: pathlib.Path,
    dry_run: bool,
    stories: Optional[List[pathlib.Path]] = None,
    backend_factory: Optional[Any] = None,
) -> Dict[str, Any]:
    """Run the real (or fake, under a caller-supplied backend_factory)
    comparison and return a JSON-serializable report: per-run call lists
    plus a summary.

    stories/backend_factory are injectable so tests can point this at a
    small synthetic fixture with a fully-known fake response sequence,
    without touching the real committed WI-PILOT-0051 fixture set (whose
    real segment counts a naive single-response FakeBackend cannot
    satisfy - segmentation and each extraction stage need distinct,
    schema-appropriate tool_results).
    """
    roots = checkpoint.resolve_roots(working_root, source_root=source_root)
    stories = stories if stories is not None else _fixture_stories()
    if not stories:
        raise RuntimeError(f"No fixture stories found under {_fixtures_dir()}")

    report: Dict[str, Any] = {
        "model": model,
        "stories": [s.name for s in stories],
        "runs": {},
    }

    for label, enable_caching in (
        ("caching_disabled", False),
        ("caching_enabled", True),
    ):
        if backend_factory is not None:
            inner = backend_factory(enable_caching)
            run_model = model
        elif dry_run:
            inner = _DryRunFakeBackend()
            run_model = "fake-1.0"
        else:
            from lcats.llm import anthropic_backend

            inner = anthropic_backend.AnthropicBackend(
                enable_prompt_caching=enable_caching
            )
            run_model = model

        recorder = _RecordingBackend(inner)
        for story_path in stories:
            _segment_and_extract(story_path, recorder, run_model, roots)

        report["runs"][label] = {
            "enable_prompt_caching": enable_caching,
            "calls": recorder.calls,
            "total_input_tokens": sum(c["input_tokens"] for c in recorder.calls),
            "total_output_tokens": sum(c["output_tokens"] for c in recorder.calls),
            "total_cache_creation_input_tokens": sum(
                c["cache_creation_input_tokens"] or 0 for c in recorder.calls
            ),
            "total_cache_read_input_tokens": sum(
                c["cache_read_input_tokens"] or 0 for c in recorder.calls
            ),
        }

    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="claude-opus-4-8")
    parser.add_argument(
        "--output-dir",
        default=str(
            pathlib.Path(__file__).resolve().parent / "results" / "caching_eval"
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Exercise the full wiring with a FakeBackend at zero cost - "
            "does NOT make any real API calls. Omit this flag only with "
            "explicit human approval for real, paid Anthropic API calls."
        ),
    )
    args = parser.parse_args()

    output_dir = pathlib.Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not args.dry_run:
        # Preflight, per Required Change 3: a prefix below Anthropic's
        # minimum cacheable length makes a later zero cache_read result
        # expected, not a signal something is wrong - record it
        # alongside the measurement, not just print-and-discard it.
        prefix_token_counts = preflight_prefix_token_counts(args.model)
        print(
            "Preflight tools+system prefix token counts (before any real measurement call):"
        )
        for name, count in prefix_token_counts.items():
            print(f"  {name}: {count} tokens")
    else:
        prefix_token_counts = None

    report = run_comparison(
        model=args.model,
        working_root=output_dir,
        source_root=_fixtures_dir(),
        dry_run=args.dry_run,
    )
    report["preflight_prefix_token_counts"] = prefix_token_counts

    report_path = output_dir / "caching_comparison.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Wrote comparison report to {report_path}")
    for label, run in report["runs"].items():
        print(
            f"  {label}: {len(run['calls'])} calls, "
            f"input={run['total_input_tokens']}, "
            f"output={run['total_output_tokens']}, "
            f"cache_creation={run['total_cache_creation_input_tokens']}, "
            f"cache_read={run['total_cache_read_input_tokens']}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
