---
resolution: null
blocked_reason: null
blocked: false
id: WI-SEGMENT-0102
title: Regression-test the fuzzy near-miss matcher against currently-correct real segments
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
  - WS-PILOT-IMPROVEMENTS
related_design:
  - lcats/project/design/segmentation-near-miss-fuzzy-matching-evaluation.md
  - lcats/project/work_items/resolved/WI-SEGMENT-0072.md
  - lcats/project/work_items/resolved/WI-SEGMENT-0099.md
depends_on: []
blocked_by: []
expected_actions:
  - create_file
  - edit_file
  - run_tests
  - create_pr
forbidden_actions:
  - implement_production_fuzzy_matcher
  - lower_wi_segment_0072_thresholds
  - weaken_exact_grounding
  - reintroduce_full_document_fallback
  - force_push
  - delete_branch
acceptance:
  - "Every real segment across all currently-committed, successfully-aligned real segmentation outputs (experiments/03_cross_segment_relation_pilot/results/segmentation_reliability/, .../segmentation_paragraph_misnumbering_diagnostics/replay_fixture/, and any other committed real output discovered during this item's own inventory) is run through the unmodified strict_local_fuzzy policy from WI-SEGMENT-0072, bounded to each segment's own [start_par_id, end_par_id) window"
  - "For each real segment, the policy's accepted match (if any) is compared against the already-recorded correct (start_char, end_char); any case where the fuzzy match differs from, or is more permissive than, the current exact/normalized result is reported explicitly, not silently absorbed"
  - "A written report states the total real-segment count tested, the number where fuzzy matching agreed exactly with the current result, and any disagreements found, with a plain safe/unsafe verdict for this specific check"
  - "No production alignment behavior is changed; WI-SEGMENT-0072's frozen adoption thresholds are neither invoked nor altered by this item - this is a distinct, complementary safety check, not a step toward clearing that gate"
  - "lrh validate reports 0 errors"
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
artifacts_expected:
  - lcats/project/design/segmentation-fuzzy-match-regression-safety-check.md
  - experiments/03_cross_segment_relation_pilot/
---

# Work Item: WI-SEGMENT-0102

## Summary

`WI-SEGMENT-0072`'s `strict_local_fuzzy` policy has only ever been
evaluated against 4 hand-built decoys plus (after `WI-SEGMENT-0099`) 4
known real near-miss positives. The evaluation's own design doc names an
explicit, still-open gap: "The policy has not been tested against
currently-correct included stories, so it does not yet prove that adding
fuzzy matching would leave existing successful alignments untouched."
Real, already-committed data exists to close this cheaply and
immediately - dozens of real segments where the current exact/normalized
matcher already succeeds - with no API spend needed. This item runs the
existing, unmodified policy against every one of them and confirms it
reproduces the exact same span the current matcher already found: a
non-regression / no-op-invariance check, not a recovery-rate measurement.

## Problem / Context

The instance-level acceptance gate (edit distance, similarity ratio,
contiguous-run ratio, uniqueness margin - see
`experiments/03_cross_segment_relation_pilot/evaluate_near_miss_fuzzy_matching.py:169-204`)
has only ever been checked against a tiny, curated set of known-good and
known-bad examples. It has never been checked against the much larger,
real, already-successful population: segments where the exact/normalized
matcher already finds the correct span today. If loosening the matcher to
accept near-misses ever caused it to prefer a *different*, merely-similar
span over the currently-correct exact one on any of these, that would be
a silent regression in exactly the kind of case `WI-SEGMENT-0059`
established must never happen - and nothing currently checks for it.

This data already exists, committed, with no fresh API spend required:

- `experiments/03_cross_segment_relation_pilot/results/segmentation_reliability/`
  (the `WI-EVENT-0096` 17-story baseline cohort): 7 of 17 stories
  completed with `outcome: included` (i.e. every segment aligned
  successfully), totaling at least 56 real segments with real,
  already-correct `(start_char, end_char)` values.
- `experiments/03_cross_segment_relation_pilot/results/segmentation_paragraph_misnumbering_diagnostics/replay_fixture/`
  (`WI-SEGMENT-0071`'s real replay fixture): a second, independent real
  dataset with `start_char`/`end_char` already present.
- Other committed real segmentation output may exist elsewhere in the
  repo; this item's own Required Changes include a full inventory rather
  than assuming these two locations are exhaustive.

### Duplication search

- In-repo: `WI-SEGMENT-0072` built the `strict_local_fuzzy` policy and
  its evaluator; `WI-SEGMENT-0099` extended its positive-case corpus.
  Neither tests the policy against currently-correct real segments - both
  explicitly limit themselves to a small curated positive/decoy fixture.
  No existing work item runs this specific regression check.
- Sibling repos: None identified.
- External libraries: Not applicable - reuses LCATS's own evaluator
  (`evaluate_near_miss_fuzzy_matching.py`) and matching logic.
- Recommendation: Proceed; this is a genuinely uncovered gap, already
  named in the existing design doc but never acted on.

### Demand search

- Work items: The gap is explicitly named in
  `lcats/project/design/segmentation-near-miss-fuzzy-matching-evaluation.md`'s
  own "Unresolved Risks" section, but no work item currently addresses
  it. Surfaced directly by user-driven design discussion in this session
  (Option 4 of a design exploration into false-positive validation
  methodology for relaxed fuzzy matching).
- Proposals: None identified.
- Backlog: No matching entry found.
- Recommendation: Proceed.

## Scope

- Inventory all committed real segmentation output in the repo that
  contains successfully-aligned segments with real `start_char`/`end_char`
  values (not limited to the two locations named above - confirm via a
  repo-wide search, not an assumption).
- For each such real segment, recompute the `strict_local_fuzzy` policy's
  accepted match (reusing `evaluate_near_miss_fuzzy_matching.py`'s
  existing `accepted_match`/`candidate_matches` functions unmodified)
  against that segment's own `[start_par_id, end_par_id)` window.
- Compare the policy's result against the already-recorded correct span
  for every case; report exact agreement, any disagreement, and any case
  where the fuzzy policy accepts a match the exact matcher would not have
  found unaided (even if it happens to agree with the correct span) as a
  distinct observation worth noting.
- Report results in a new design doc with a plain safe/unsafe verdict for
  this specific check; do not fold this into `WI-SEGMENT-0072`'s
  frozen-threshold framework, since it answers a different question
  (does relaxing disturb what already works, not does relaxing recover
  enough near-misses).

## Required Changes

1. Write a small analysis script (not a permanent pipeline component)
   that discovers all committed real segmentation output files with
   successfully-aligned segments (real `start_char`/`end_char` present,
   no `alignment_error`), across the full repo, not just the two
   locations already known.
2. For each discovered real segment, call
   `evaluate_near_miss_fuzzy_matching.accepted_match` (or equivalent,
   reusing its existing policy/candidate-generation code unmodified)
   against that segment's own paragraph-range window, and compare the
   result to the segment's already-recorded `(start_char, end_char)`.
3. Aggregate and report: total real segments tested, count where the
   fuzzy policy's result matches the existing correct span exactly, count
   of any disagreements (with full detail on each), and count of any
   segments where the fuzzy policy accepted a broader/different candidate
   set than the exact matcher needed.
4. Write
   `lcats/project/design/segmentation-fuzzy-match-regression-safety-check.md`
   with methodology, the full inventory of real data used, results, and a
   plain safe/unsafe verdict.
5. Add a regression test (or note why one is not warranted, if the
   analysis script itself is the durable check) so this safety property
   can be re-verified after any future change to `strict_local_fuzzy` or
   its evaluator.

## Non-Goals

- Does not implement production fuzzy matching, regardless of this item's
  result.
- Does not lower, redefine, or otherwise interact with `WI-SEGMENT-0072`'s
  frozen adoption thresholds (10+ positives, 20+ decoys, 90%+ recovery, 0
  false positives) - this item answers a different question and does not
  count toward or against that gate.
- Does not spend any real API budget - all data used is already committed
  real output.
- Does not modify `strict_local_fuzzy`'s policy parameters or the
  evaluator's existing logic - reuses them exactly as-is.

## Acceptance Criteria

(see frontmatter `acceptance:` above)

## Validation

- lrh validate
- test_output

## Risk Notes

- **This item measures a different property than `WI-SEGMENT-0072`'s
  existing gate.** "Does relaxing matching disturb currently-correct
  cases" and "does relaxing matching recover enough real near-misses" are
  independent questions; a clean result here does not imply readiness to
  adopt fuzzy matching in production, and should not be reported or
  interpreted as such.
- **A disagreement found here is a stop condition, not a tuning
  invitation** - consistent with `WI-SEGMENT-0072`'s and
  `WI-SEGMENT-0059`'s established posture toward false positives and
  silent wrong matches.
- **The real-segment inventory should not be assumed complete from the
  two locations named in this item's Problem/Context** - the Required
  Changes explicitly call for a fresh, repo-wide discovery pass rather
  than trusting this item's own preliminary count.

## Related Workstream and Designs

- Workstream: `lcats/project/workstreams/proposed/WS-PILOT-IMPROVEMENTS.md`
- Design: `lcats/project/design/segmentation-near-miss-fuzzy-matching-evaluation.md`
  (names the gap this item closes)
- Work item: `lcats/project/work_items/resolved/WI-SEGMENT-0072.md`
  (owns the policy and frozen thresholds this item does not alter)
- Work item: `lcats/project/work_items/resolved/WI-SEGMENT-0099.md`
  (most recent extension of the evaluation corpus this item complements)
