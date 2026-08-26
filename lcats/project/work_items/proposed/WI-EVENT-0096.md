---
resolution: null
blocked_reason: null
blocked: false
id: WI-EVENT-0096
title: Measure live segmentation exclusion-rate improvement from WI-EVENT-0033's schema hardening
type: evaluation
status: proposed
priority: medium
owner: unassigned
contributors: []
assigned_agents: []
related_focus:
  - FOCUS-WORLDCON-2026
related_roadmap: []
related_workstreams:
  - WS-EVENT-STRUCTURED-OUTPUT-RELIABILITY
related_design:
  - project/audits/2026-07-27-erw-pipeline-structured-output-reliability-audit.md
  - project/work_items/proposed/WI-EVENT-0033.md
depends_on:
  - WI-EVENT-0033
blocked_by: []
expected_actions:
  - create_file
  - edit_file
  - run_tests
  - create_pr
forbidden_actions:
  - modify_scene_analysis_extractor
  - implement_new_architecture
  - run_real_llm_calls_without_explicit_approval
  - force_push
  - delete_branch
acceptance:
  - "Before any real API spend, the executor presents the selected model (claude-haiku-4-5-20251001, matching the original measurement), sample size/genre spread, expected call-count/cost estimate, and output location, and receives explicit in-session human approval"
  - "A fresh stratified sample of similar size to the original 17-story measurement (WI-EVENT-0033's cited 11/17, 65% parsing_error rate) is built and run through make_segment_extractor alone (not the full ERW pipeline) - the original sample's exact story IDs were never committed to the repo, so this is explicitly the 'equivalent smoke sample' path WI-EVENT-0033's own acceptance criteria already anticipated, not a deviation from it"
  - "The sample explicitly includes the western genre, which had zero included stories in the original measurement"
  - "The new parsing_error exclusion rate is computed directly from real extract() results (not estimated or assumed) and reported alongside the original 65% (11/17) for direct comparison"
  - "Raw per-story results (story_id, extraction_error, parsed_output presence) and a summary are saved as committed data under lcats/experimental/segmentation_schema_verification/ (small sample - single-call-per-story data, not experiments/-scale) so the measurement is independently checkable, not just narrated"
  - "WI-EVENT-0033.md is updated with the real measured result in its Risk Notes/resolution - if the exclusion rate dropped meaningfully, WI-EVENT-0033 is moved to resolved/ with a resolution citing the before/after; if not, the finding is reported plainly and WI-EVENT-0033 stays proposed with the gap documented, per this project's practice of not forcing a pass"
  - "scripts/test passes with no new failures"
  - "lrh validate reports 0 errors"
required_evidence:
  - test_output
  - lrh_validate
  - manual_review
artifacts_expected:
  - lcats/experimental/segmentation_schema_verification/
  - project/work_items/proposed/WI-EVENT-0033.md
---

# Work Item: WI-EVENT-0096

## Summary

Close `WI-EVENT-0033`'s one outstanding acceptance criterion: a live
re-run against real API calls to measure whether its schema-hardening fix
(`SEGMENT_TOOL_SCHEMA` via `tool_schema=`, PR #188, merged 2026-07-29)
actually reduced the 65% (11/17) `parsing_error` segmentation-exclusion
rate observed before the fix, with the `western` genre stratum
particularly affected (zero included stories). That criterion was
explicitly left unverified at PR #188's merge time for lack of API
credentials in that environment, not skipped by oversight - the PR's own
description names it as the one remaining gap.

## Problem / Context

The 2026-07-27 ERW pipeline audit
(`project/audits/2026-07-27-erw-pipeline-structured-output-reliability-audit.md:238-245`)
found `scene_analysis.py`'s Stage 1 segmentation extractor
(`make_segment_extractor`) was the pipeline's actual, currently-blocking
reliability problem: with `claude-haiku-4-5-20251001` in a real user run,
11 of 17 sampled stories (65%) were excluded with
`extraction_error="parsing_error"`, and the `western` stratum had zero
included stories as a result. `WI-EVENT-0033` retrofitted this extractor
(plus `make_semantics_extractor` and `make_doc_classification_extractor`)
to use a `tool_schema=` structured-output call instead of unconstrained
`json_object` mode, per `lcats.llm.tool_schema.strict_tool_schema()`. That
work merged via PR #188 (commit `9cb37549`), but its own final commit
message states plainly: "Not verified in this environment... the
acceptance criterion requiring a live re-run against the sampled story
set that saw the 65% exclusion rate, to report the new rate... needs
whoever has credentials to run it for real before this item is considered
fully closed." `WI-EVENT-0033.md` itself was deliberately left
`status: proposed` for exactly this reason, not moved to `resolved/`.

The original 17-story sample's exact story IDs were never committed to
the repo - no `pilot_stories.jsonl` or equivalent artifact survives from
that run (confirmed via `find`/`grep` across `experiments/` and
`project/audits/`, no story-ID list found). `WI-EVENT-0033.md`'s own
acceptance criteria already anticipated this ("verified by re-running the
same sampled story set (**or an equivalent smoke sample**)"), so this
item builds a fresh equivalent sample rather than blocking on an
unrecoverable original.

### Duplication search

- In-repo: No other work item performs this measurement.
  `WI-EVENT-0033.md` names this exact gap in its own acceptance criteria
  but has not executed it - this item is that criterion's execution
  vehicle, filed separately (see Demand search) rather than by reopening
  `WI-EVENT-0033` directly.
- Sibling repos: None identified.
- External libraries: None identified.
- Recommendation: Proceed.

### Demand search

- Work items: `WI-EVENT-0033.md`'s own acceptance criteria and PR #188's
  merge commit message both name this exact deliverable as outstanding.
  Filed as a separate, `depends_on`-linked evaluation item (rather than
  reopening `WI-EVENT-0033` directly) so the measurement has its own
  traceable execution record, bounded real-API cost gate, and PR -
  following this session's established pattern for `WI-EVENT-0030`'s own
  cost-gate sub-runs (`WI-EVENT-0078`/`0079`/`0080`).
- Proposals: None identified beyond the governing ERW extractor proposal,
  which already names `json_object` mode as the pattern being replaced.
- Backlog: No matching entry found.
- Recommendation: Proceed.

## Scope

- Build a fresh stratified sample of similar size to the original
  17-story measurement, spanning all 8 `VALID_GENRES`, explicitly
  including `western` (the stratum with zero included stories
  originally).
- Run `make_segment_extractor` alone (Stage 1 segmentation only, not the
  full Event-Role-World pipeline) against that sample using
  `claude-haiku-4-5-20251001`, matching the original measurement's model
  so the comparison is apples-to-apples.
- Follow this project's established two-step real-cost-gate discipline:
  present the selected sample, model, and expected cost/call-count
  estimate; wait for explicit in-session approval; then run.
- Compute the new `parsing_error` exclusion rate directly from real
  `extract()` results and report it alongside the original 65% (11/17).
- Save raw per-story results and a summary as committed data under
  `lcats/experimental/segmentation_schema_verification/` - this sample is
  small (one extraction call per story, not a full pipeline run), so
  `lcats/experimental/` is the right scale, not the top-level
  `experiments/` directory reserved for larger pilot-scale work.
- Update `WI-EVENT-0033.md` with the real measured outcome, and resolve
  it if the result supports that.

## Required Changes

1. Build the stratified sample (reusing `WI-GENRE-0004`'s validated
   genre-balanced manifest, `experiments/05_metadata_genre_prefilter/results/full_scan/validation_results.jsonl`,
   the same source `WI-EVENT-0030` already draws from) and present it,
   the model, and the expected cost/call-count estimate to the user for
   explicit approval before any spend.
2. After approval, run `make_segment_extractor` against the approved
   sample and capture each story's `extraction_error` /
   `parsed_output`/`extracted_output` presence.
3. Write raw results (one record per story: story ID, genre,
   `extraction_error`, whether `parsed_output` was populated) and a
   summary (old vs. new exclusion rate, per-genre breakdown, explicit
   `western` callout) to `lcats/experimental/segmentation_schema_verification/`.
4. Update `WI-EVENT-0033.md`: populate its Risk Notes with the real
   measured before/after, and either move it to `resolved/` with a
   `resolution:` field citing the measurement, or leave it `proposed`
   with the gap stated plainly if the improvement is smaller than
   expected.
5. Add or update test coverage only if this item's own new tooling (e.g.
   a small sample-runner script, if one is written) needs it - no changes
   to `scene_analysis.py`/`story_analysis.py` are in scope (already
   merged via PR #188).

## Non-Goals

- Does not modify `scene_analysis.py`'s or `story_analysis.py`'s schemas
  or extractors - `WI-EVENT-0033`'s schema-hardening code is already
  merged (PR #188); this item measures its real-world effect only.
- Does not re-run `make_semantics_extractor` or
  `make_doc_classification_extractor` - both were unmeasured in the
  original 2026-07-27 audit too (no live failure rate to compare
  against), and `WI-EVENT-0033.md`'s own Risk Notes already flag this as
  a separate, unmeasured risk, not something this item resolves.
- Does not attempt to recover or reconstruct the original 17-story
  sample's exact story IDs - confirmed unrecoverable; an equivalent fresh
  sample is used instead, per `WI-EVENT-0033.md`'s own acceptance
  criteria wording.
- Does not spend any real API budget without an explicit, presented,
  approved cost estimate first.

## Acceptance Criteria

(see frontmatter `acceptance:` above)

## Validation

- scripts/format --check --diff
- scripts/lint
- scripts/test
- lrh validate

## Risk Notes

- **Sample non-equivalence risk:** a freshly built stratified sample is
  not literally the same stories as the original run, so a residual
  difference in results could reflect sample variance rather than the
  schema fix's real effect. Mitigated by keeping the sample size and
  genre spread comparable, and by reporting the result honestly rather
  than treating a small sample as decisive either way.
- **Directionally negative result is a valid outcome.** If the measured
  exclusion rate does not improve meaningfully, that is reported plainly
  in `WI-EVENT-0033.md` rather than forced into a "resolved" state -
  matching this project's own established practice (e.g.
  `WI-EVENT-0080.md`'s acceptance criteria, `WI-PILOT-0082.md`'s Risk
  Notes).
- **Real API spend requires the same bounded-approval discipline** this
  session already used for `WI-EVENT-0030`'s cost-gate sub-runs - no
  spend without a presented estimate and explicit go-ahead.

## Related Workstream and Designs

- Workstream: `project/workstreams/proposed/WS-EVENT-STRUCTURED-OUTPUT-RELIABILITY.md`
- Work item: `project/work_items/proposed/WI-EVENT-0033.md` - the item
  whose outstanding acceptance criterion this item executes
- Audit: `project/audits/2026-07-27-erw-pipeline-structured-output-reliability-audit.md`
