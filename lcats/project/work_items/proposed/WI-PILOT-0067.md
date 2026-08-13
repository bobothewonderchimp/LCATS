---
id: WI-PILOT-0067
title: Run pilot API/output stability gate
type: evaluation
status: proposed
priority: high
owner: unassigned
contributors: []
assigned_agents: []
related_focus:
  - FOCUS-WORLDCON-2026
related_roadmap: []
related_workstreams:
  - WS-PILOT-IMPROVEMENTS
related_design:
  - lcats/project/workstreams/proposed/WS-PILOT-IMPROVEMENTS.md
  - lcats/project/design/proposals/proposed/lcats-pilot-improvements/00_proposal.md
  - lcats/project/design/proposals/adopted/lcats-pilot-cost-sustainability/00_proposal.md
  - lcats/project/audits/2026-07-27-erw-pipeline-structured-output-reliability-audit.md
  - lcats/project/design/backlog.md
depends_on:
  - WI-PILOT-0051
blocked_by: []
blocked: false
blocked_reason: null
resolution: null
expected_actions:
  - create_file
  - edit_file
  - run_tests
  - create_report
  - create_pr
forbidden_actions:
  - force_push
  - delete_branch
  - run_real_llm_calls_without_explicit_approval
  - run_unbounded_full_corpus_pilot
  - implement_prompt_caching_adoption
  - implement_model_tiering_adoption
  - implement_batch_api_adoption
  - tune_prompts_after_negative_gate_result
  - default_enable_prompt_caching
  - default_enable_model_tiering
acceptance:
  - A bounded real stability run uses the WI-PILOT-0051 fixture set for end-to-end pilot output and separately exercises real genre detection for the same two fixture stories against validated genre ground truth
  - Before any real Anthropic call, the run plan reports model choices, story count, expected call count, expected artifacts, and a cost estimate, then receives explicit in-session human approval
  - The stability report records completion, artifact well-formedness, schema/truncation/fatal-error status, semantic review, predeclared quality thresholds, intended-purpose fit, and actual spend
  - A negative result stops downstream adoption work and is reported as a valid gate failure with the named failure mode; the implementor does not tune prompts or retry to manufacture a pass
  - lrh validate reports 0 errors, and scripts/format, scripts/lint, and scripts/test report 0 failures if code or experiment helpers are changed
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
  - validation_output
artifacts_expected:
  - experiments/03_cross_segment_relation_pilot/results/stability_gate/
  - experiments/03_cross_segment_relation_pilot/results/stability_gate/stability_gate_report.md
  - experiments/03_cross_segment_relation_pilot/results/stability_gate/stability_gate_results.json
  - experiments/03_cross_segment_relation_pilot/results/stability_gate/pilot_stories.jsonl
  - experiments/03_cross_segment_relation_pilot/results/stability_gate/pilot_usage.jsonl
  - experiments/03_cross_segment_relation_pilot/results/stability_gate/pilot_summary.json
---

## Summary

Run the first bounded real API/output stability gate for the ERW
cross-segment relation pilot before any follow-on prompt-caching,
model-tiering, Batch API, or run-mode adoption work proceeds.

## Problem / Context

`WS-PILOT-IMPROVEMENTS` requires a stability gate before downstream cost
and ergonomics improvements: the pilot must prove it can complete on real
Anthropic calls, produce well-formed artifacts, make semantic sense, meet a
quality bar, serve its intended research purpose, and do so at bounded cost.
The current `WI-PILOT-0051` fixture set is the right first bounded story set
for this gate: it contains two short real stories and validated genre ground
truth, keeping spend small while still exercising the existing end-to-end
harness. Because targeted fixture mode receives fixture genre labels instead
of invoking genre detection, this work item must add a separate real
genre-detection check for the same two stories against
`fixtures/genre_ground_truth.json`.

### Duplication search

- In-repo: No existing work item implements this stability gate. Related but
  not duplicate: `WI-PILOT-0051` created the targeted fixture harness, while
  `WI-PILOT-0057`, `WI-PILOT-0058`, and `WI-PILOT-0060` measured individual
  cost levers.
- Sibling repos: None identified.
- External libraries: None identified. This is an LCATS pilot validation and
  reporting gate over existing pipeline behavior, not a third-party
  capability.
- Recommendation: Proceed.

### Demand search

- Work items: No proposed work item currently implements the gate.
- Proposals: `PROP-LCATS-PILOT-IMPROVEMENTS` requests this exact prerequisite
  gate before downstream adoption work.
- Workstreams: `WS-PILOT-IMPROVEMENTS` lists this as the first work item and
  makes it the first exit criterion.
- Backlog: Related backlog demand exists for minimum-cost validation and
  pilot cost visibility; this gate should report whether those entries are
  closed, revised, or still deferred after the run.
- Recommendation: Proceed.

## Scope

- Use the existing `WI-PILOT-0051` fixture set as the bounded end-to-end
  story set: `fixtures/king_of_the_hill` and
  `fixtures/five_o_clock_tea_farce`.
- Separately run real genre detection for the same two fixture stories and
  compare against
  `experiments/03_cross_segment_relation_pilot/fixtures/genre_ground_truth.json`.
- Run the real pilot path only after fake/dry validation and explicit
  in-session approval of the model, story count, expected call count,
  artifact list, and cost estimate.
- Produce a stability report that evaluates completion, artifact
  well-formedness, semantic sense, quality thresholds, intended-purpose fit,
  and actual spend.

## Required Changes

1. Define the stability-gate run plan in a committed report or helper
   artifact before real spend. The plan must name the bounded story set, the
   model(s), expected call count, estimated cost, expected output files,
   semantic-review procedure, and pass/fail thresholds.
2. Verify the run path without real spend first, using existing dry-run or
   fake-backend coverage where available. If a helper script is added for the
   gate, add focused tests for its parsing/reporting behavior before real API
   calls.
3. Before any real Anthropic call, show the human operator the run plan and
   obtain explicit in-session approval. The work item itself is not that
   approval.
4. Run the end-to-end targeted pilot against the two fixture stories and
   preserve the generated `pilot_stories.jsonl`, `pilot_usage.jsonl`, and
   `pilot_summary.json` under
   `experiments/03_cross_segment_relation_pilot/results/stability_gate/`.
5. Run a separate real genre-detection check for the same two stories against
   validated ground truth, because targeted fixture mode does not invoke the
   genre-detection stage.
6. Validate artifacts mechanically: JSON/JSONL parseability, expected story
   count, required top-level fields, usage rows for touched stages, absence
   of fatal run errors, schema/malformed-output signals, and truncation/error
   markers.
7. Perform and record semantic review against the source stories. At minimum,
   review segmentation plausibility, core entity/event/relation/discourse
   support, any cross-segment relation claims, genre-detection correctness,
   and whether the output is useful for inspecting cross-segment relation
   density.
8. Record a clear pass/fail recommendation. A fail result must name the
   blocking failure mode and stop downstream adoption work; do not tune
   prompts, change defaults, or retry repeatedly within this work item to
   obtain a pass.

## Non-Goals

- Do not implement prompt-caching adoption. That is a later
  `WS-PILOT-IMPROVEMENTS` item if this gate passes.
- Do not implement genre/segmentation model-tiering adoption. That is a later
  item if this gate passes.
- Do not implement Batch API adoption or checkpointing retrofit.
- Do not change pilot defaults merely because prior cost evaluations produced
  go recommendations.
- Do not run a full-corpus or unbounded real pilot.
- Do not treat a negative result as a reason to tune prompts or rerun until
  the gate passes; report the measured failure.

## Acceptance Criteria

- The bounded story set is the two-story `WI-PILOT-0051` fixture set, and
  genre detection is separately exercised on those same stories against
  validated ground truth.
- The committed run plan includes predeclared thresholds before real spend:
  100% fixture-story completion, parseable output artifacts, no fatal pilot
  errors, no schema-invalid or truncation-marked final artifacts, genre
  correctness against validated ground truth, source-supported semantic
  output, and an explicit intended-purpose verdict.
- Real Anthropic calls are made only after explicit in-session approval of
  model choices, story count, expected call count, artifact list, and
  estimated cost.
- The final report records actual spend, generated artifacts, mechanical
  validation results, semantic-review results, pass/fail conclusion, and any
  named blocker.
- A fail result stops downstream adoption work and is considered a complete
  outcome for this item.

## Validation

- `scripts/version tools`
- `lrh validate`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- Dry-run or fake-backend validation of the stability-gate command/reporting
  path before real spend
- Explicitly-approved real stability-gate run against the two fixture stories
- Artifact parser/validator output for `pilot_stories.jsonl`,
  `pilot_usage.jsonl`, `pilot_summary.json`, and the genre-detection result
  file

## Risk Notes

- The `WI-PILOT-0051` fixture set is intentionally tiny. Passing this gate
  proves the pilot is no longer obviously producing a null result on the
  bounded harness; it is not a statistically robust quality estimate for
  large research runs.
- Targeted fixture mode bypasses genre detection by design, so a fixture-only
  run would not satisfy `WS-PILOT-IMPROVEMENTS`'s explicit genre-detection
  coverage criterion. The separate real genre-detection check is required.
- Real API spend is necessary for this gate, but it must remain bounded and
  separately approved. The expected spend should be much closer to the prior
  fixture-set runs than to the historical $67.54 broad pilot failures.
- Existing checkpoints can mask real calls or stale behavior. The run plan
  must state whether checkpoints are cleared, isolated under a fresh output
  directory, or intentionally reused, and why that choice preserves the
  gate's evidentiary value.
- A negative result is useful evidence. It should block downstream adoption
  until a separate follow-on WI names and fixes the failure mode.

## Dependencies / Order

This item depends on `WI-PILOT-0051`, which created the targeted harness and
fixture set. It is the first work item under `WS-PILOT-IMPROVEMENTS`; prompt
caching, model tiering, Batch API, and user-facing run-mode adoption should
not start until this gate has landed with a pass result or a separate human
decision explicitly changes the workstream sequence.

## Related Workstream and Designs

- Workstream: `lcats/project/workstreams/proposed/WS-PILOT-IMPROVEMENTS.md`
- Proposal:
  `lcats/project/design/proposals/proposed/lcats-pilot-improvements/00_proposal.md`
- Prior evaluation proposal:
  `lcats/project/design/proposals/adopted/lcats-pilot-cost-sustainability/00_proposal.md`
- Fixture harness: `WI-PILOT-0051`
