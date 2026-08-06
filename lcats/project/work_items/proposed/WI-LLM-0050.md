---
resolution: null
blocked_reason: null
blocked: false
id: WI-LLM-0050
title: Extend the local-model benchmark harness to genre-detection and segmentation stages
type: evaluation
status: proposed
owner: unassigned
contributors: []
assigned_agents: []
related_focus: []
related_roadmap: []
related_workstreams: []
related_design:
  - lcats/project/design/proposals/proposed/erw-local-model-evaluation/00_proposal.md
  - lcats/experimental/model_comparison/README.md
  - experiments/03_cross_segment_relation_pilot/run_pilot.py
depends_on: []
blocked_by: []
expected_actions:
  - create_file
  - edit_file
  - create_pr
forbidden_actions:
  - force_push
  - delete_branch
  - merge_pr
acceptance:
  - "common/harness.py gains at least one new run_*() function covering genre detection or scene/sequel segmentation, reusing the real production call path (corpus_assess.assess_story / scene_analysis.make_segment_extractor), not a synthetic schema"
  - "At least one local candidate (e.g. ollama_qwen3_8b) run against the new stage(s), with real, committed results.json"
  - "PROP-ERW-LOCAL-MODEL-EVALUATION's hybrid-pipeline hypothesis (Decision 3) is explicitly re-assessed against this new evidence, not left as an open question"
artifacts_expected:
  - lcats/experimental/model_comparison/common/harness.py (extended)
  - lcats/experimental/model_comparison/*/results.json (per-candidate, per this harness's existing convention)
  - lcats/project/design/proposals/proposed/erw-local-model-evaluation/00_proposal.md (updated with new evidence)
required_evidence:
  - lrh_validate
  - test_output
  - manual_review
---

## Summary

Extend `lcats/experimental/model_comparison/common/harness.py` to cover
the ERW pipeline's genre-detection and/or scene-sequel-segmentation
stages (in addition to the existing stage-3 entity-extraction coverage),
and run at least one local candidate against them. This is the evidence
`PROP-ERW-LOCAL-MODEL-EVALUATION` names as still needed to actually
assess its hybrid-pipeline hypothesis (a cheap local model for
lighter/simpler stages, a frontier model retained for extraction).

## Problem / Context

`PROP-ERW-LOCAL-MODEL-EVALUATION`'s Design Decisions repeatedly note that
entity-extraction results alone - the only stage this harness currently
covers - do not settle whether a hybrid pipeline is viable, because
genre detection and segmentation are "comparatively simple
classification/structuring tasks that might tolerate a smaller local
model fine" (the user's own framing when scoping the original
investigation), unlike the harder extraction stages. Without this
extension, the proposal's hybrid-pipeline recommendation stays
permanently "plausible but unproven." Named as follow-on item #2 in the
proposal's Implementation Plan.

### Prior Art Check

**Duplication search:** In-repo, `common/harness.py` only covers stage-3
entity extraction (`run_entity_extraction()`). The real call paths this
work item would reuse already exist and are proven in production:
`lcats.analysis.corpus.assess.assess_story` (genre detection) and
`lcats.analysis.scene_analysis.make_segment_extractor` (segmentation,
already used once in this session by
`common/generate_sample_segment.py` to produce the fixed entity-
extraction test segment). No sibling repos or external libraries
considered. Recommendation: proceed, reusing these existing extractors
rather than building new ones.

**Demand search:** `PROP-ERW-LOCAL-MODEL-EVALUATION`'s Implementation
Plan directly requests this as follow-on item #2, and its Non-Goals
section explicitly disclaims current coverage of these stages.
Recommendation: this work item satisfies that request.

## Scope

- Add at least one new `run_*()` function to `common/harness.py` (e.g.
  `run_genre_detection()` and/or `run_segmentation()`), following
  `run_entity_extraction()`'s existing shape: build the real extractor,
  run it against real input, return a `BenchmarkResult`-shaped record
  (success, latency, tokens, raw-output preview on failure).
- Genre detection: reuse `corpus_assess.assess_story()` in detect mode
  against the existing sample story
  (`corpora/sherlock/five_orange_pips/story.json`).
- Segmentation: reuse `scene_analysis.make_segment_extractor()` against
  the same story (this is exactly what
  `common/generate_sample_segment.py` already does once to produce the
  entity-extraction fixture - this work item promotes that into a
  first-class, benchmarked stage rather than a one-off fixture step).
- Run at least one existing local candidate (e.g. `ollama_qwen3_8b`)
  against the new stage(s), with appropriate per-stage `temperature`/
  `max_tokens` (do not assume the entity-extraction stage's tuned values
  transfer).
- Update `PROP-ERW-LOCAL-MODEL-EVALUATION`'s Decision 3 (or a follow-on
  amendment) with the new evidence and an explicit hybrid-pipeline
  verdict - do not leave the hypothesis open after this evidence exists.

## Required Changes

- `common/harness.py` extended with new stage coverage.
- New/extended candidate `benchmark.py` files exercising the new
  stage(s).
- Committed `results*.json` for the new stage(s).
- `PROP-ERW-LOCAL-MODEL-EVALUATION` updated with the resulting
  hybrid-pipeline assessment.

## Non-Goals

- Does not cover event/relation/discourse extraction or the
  cross-segment-relation pass - those remain as hard as entity
  extraction and are not the "comparatively simple" stages this item
  targets.
- Does not change `run_pilot.py`'s actual pipeline configuration - stays
  benchmark-only pending the hybrid-pipeline verdict this item produces.
- Does not add new local-model candidates - reuses existing ones
  (`anthropic_opus`, `ollama_qwen3_8b`, and `WI-LLM-0049`'s
  `ollama_qwen3_30b_a3b` if that item lands first).

## Acceptance Criteria

- `common/harness.py` gains at least one new stage-coverage function
  reusing the real production extractor(s), not a synthetic schema.
- At least one local candidate run against the new stage(s), with real,
  committed `results.json`.
- `PROP-ERW-LOCAL-MODEL-EVALUATION`'s Decision 3 is explicitly
  re-assessed against this new evidence.

## Validation

- `python -m pytest tests/llm_tests/ -q`
- `black --check experimental/model_comparison` (CI-pinned version)
- `ruff check experimental/model_comparison` (CI-pinned version)
- `lrh validate`
- Real benchmark run(s) against the new stage(s) for at least one
  candidate

## Risk Notes

- Genre detection and segmentation prompts are shaped differently from
  entity extraction (segmentation in particular uses a much larger,
  more complex tool schema with GACD/ERAC classification - see
  `scene_analysis.py`'s `SCENE_SEQUEL_SYSTEM_PROMPT`) - a local model
  passing entity extraction is not evidence it will pass segmentation;
  treat as an independent test, not an inference from `WI-LLM-0049`'s
  results.

## Dependencies / Order

- Not blocked by `WI-LLM-0049`, but benefits from it if that item lands
  first (a wider set of local candidates to test the new stage(s)
  against).
