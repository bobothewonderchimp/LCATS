---
resolution: "Implemented and merged via PR #236 (commit 80638298): assess_story() gained an overridable max_tokens (default 4096, was hardcoded 2048) with a new --max-tokens CLI flag; make_segment_extractor() gained an overridable max_tokens (default 16384, was silently inheriting the library's bare 4096). Real-API dogfood run against the corpus's longest story (264KB, ~93K input tokens) directly observed the 8192-to-16384 truncation-to-success transition for segmentation and confirmed assess_story clean at 4096 - not just unit-test coverage of the override mechanism. Also surfaced an unrelated, pre-existing ASSESSMENT_TOOL schema bug (blocks all real lcats assess calls), deliberately not fixed here and flagged as a separate follow-up task. See execution record project/executions/WI-ANNOTATE-0050/2026_08_07_03_11_35_WI_ANNOTATE_0050.md."
blocked_reason: null
blocked: false
id: WI-ANNOTATE-0050
title: Fix max_tokens truncation in assess_story and make_segment_extractor
type: deliverable
status: resolved
owner: unassigned
contributors: []
assigned_agents: []
related_focus:
  - FOCUS-WORLDCON-2026
related_roadmap:
  - ROADMAP-CORE
related_workstreams:
  - WS-WORLDCON-FAST-PATH-ANNOTATION
related_design:
  - project/design/proposals/adopted/worldcon-fast-path-annotation/00_proposal.md
depends_on: []
blocked_by: []
expected_actions:
  - edit_file
  - run_tests
  - create_pr
forbidden_actions:
  - force_push
  - delete_branch
  - implement_lcats_annotate
acceptance:
  - assess_story's backend.complete call no longer hardcodes max_tokens=2048; the value is overridable (parameter or raised default)
  - make_segment_extractor accepts/uses a higher max_tokens than JSONPromptExtractor's bare 4096 default
  - Both fixes are verified against at least one real story that previously truncated under the old ceiling
  - lrh validate reports 0 errors
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
artifacts_expected:
  - lcats/src/lcats/analysis/corpus/assess.py
  - lcats/src/lcats/analysis/scene_analysis.py
---

## Summary

Fix two live truncation bugs that block `lcats annotate` (WI-ANNOTATE-0051)
from running successfully at even small scale: `assess_story`'s
hardcoded `max_tokens=2048`, and `make_segment_extractor`'s missing
`max_tokens` override.

## Problem / Context

`lcats/src/lcats/analysis/corpus/assess.py:328` calls `backend.complete(...,
max_tokens=2048, ...)` inside `assess_story()` with no way to override
it — confirmed to truncate on longer/messier real candidate stories
during this session's design work.

`lcats/src/lcats/analysis/scene_analysis.py`'s `make_segment_extractor()`
(around line 326) constructs `llm_extractor.JSONPromptExtractor(backend,
...)` without passing `max_tokens`, so it silently inherits
`JSONPromptExtractor.__init__`'s bare `max_tokens: int = 4096` default
(`lcats/src/lcats/analysis/llm_extractor.py:69`) — also confirmed to truncate
on real corpus stories. An earlier draft of
`PROP-WORLDCON-FAST-PATH-ANNOTATION` mistakenly claimed a working
override already existed, stranded inside
`experiments/03_cross_segment_relation_pilot/run_pilot.py`'s
`_segment_story()`; a PR #226 review round corrected this — no such
override exists anywhere in the codebase today. The nearest existing
precedent for this override pattern is that same file's
`_build_erw_extractors()`, which sets `extractor.max_tokens =
_ERW_MAX_TOKENS` post-construction on the five ERW extractors (not
segmentation).

Both fixes must land before `lcats annotate` (WI-ANNOTATE-0051) is built
on top of these extractors, or the new command will reproduce both
failures immediately.

### Duplication search
- In-repo: No existing fix for either ceiling. `_build_erw_extractors`'s
  override is the closest pattern to imitate, but applies to different
  extractors.
- Sibling repos: None identified.
- External libraries: None applicable — this is a call-site parameter
  fix, not a library gap.
- Recommendation: Proceed.

### Demand search
- Work items: None found requesting this fix directly prior to this
  item.
- Proposals: `PROP-WORLDCON-FAST-PATH-ANNOTATION`'s Design Decision 5
  requests exactly this fix.
- Backlog: No matching entry in `project/design/backlog.md`.
- Recommendation: Proceed.

## Scope

- Add a `max_tokens` override to `assess_story()`'s `backend.complete`
  call in `assess.py`.
- Add a `max_tokens` parameter (or raised default) to
  `make_segment_extractor()` in `scene_analysis.py`, passed through to
  `JSONPromptExtractor`'s constructor.
- Verify both fixes against real story input that previously truncated.

## Required Changes

1. `lcats/src/lcats/analysis/corpus/assess.py`: change `assess_story`'s
   `backend.complete(..., max_tokens=2048, ...)` (line 328) to accept an
   overridable value — either a new `max_tokens` parameter on
   `assess_story`/`assess_collection` threaded through to this call, or
   a raised module-level default if no caller-level override is needed.
2. `lcats/src/lcats/analysis/scene_analysis.py`: change `make_segment_extractor`
   to accept a `max_tokens` parameter (default higher than the library's
   bare 4096) and pass it to `llm_extractor.JSONPromptExtractor(backend,
   ..., max_tokens=max_tokens)`.
3. Add or extend tests exercising both call sites with the new
   parameter/default.
4. Manually verify against at least one real story from `corpora/` that
   previously failed under the old ceiling for each extractor.

## Non-Goals

- Does not build `lcats annotate` itself — that is WI-ANNOTATE-0051,
  which depends on this item.
- Does not change the ERW extractors' `_ERW_MAX_TOKENS` — already fixed
  in `run_pilot.py`.
- Does not add retry/backoff logic for truncation errors — out of scope,
  per `PROP-LCATS-PIPELINE-CHECKPOINTING`'s own deferral of retry policy.

## Acceptance Criteria

- `assess_story`'s `max_tokens` is no longer hardcoded at 2048 with no
  override path.
- `make_segment_extractor` no longer silently inherits the bare 4096
  default with no way to raise it.
- Both changes verified against at least one real story each that
  previously truncated.
- `lrh validate` reports 0 errors.

## Validation

- `scripts/version tools`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh validate`

## Risk Notes

- Raising `max_tokens` increases per-call cost; keep the raise
  proportionate to the observed truncation cases rather than maximal.
- `assess_story`'s fix must not change behavior for callers that don't
  need a higher ceiling (default should stay reasonable).

## Dependencies / Order

No dependencies — this is the first item in `WS-WORLDCON-FAST-PATH-ANNOTATION`'s
sequencing; WI-ANNOTATE-0051 depends on it.

## Related Workstream and Designs

- Workstream: `project/workstreams/proposed/WS-WORLDCON-FAST-PATH-ANNOTATION.md`
- Design: `project/design/proposals/adopted/worldcon-fast-path-annotation/00_proposal.md`
  (Design Decision 5)
