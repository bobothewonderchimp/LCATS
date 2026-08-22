---
id: WI-GENRE-0076
title: Teach lcats annotate append-mode genre-sidecar writes
type: deliverable
status: proposed
priority: medium
owner: unassigned
contributors: []
assigned_agents: []
related_focus:
  - FOCUS-WORLDCON-2026
related_roadmap:
  - ROADMAP-CORE
related_workstreams:
  - WS-GENRE-EVIDENCE-SIDECARS
related_design:
  - project/design/proposals/proposed/genre-evidence-sidecars/00_proposal.md
  - project/work_items/resolved/WI-GENRE-0003.md
  - project/work_items/resolved/WI-GENRE-0004.md
  - lcats/src/lcats/analysis/corpus/genre_sidecar.py
  - lcats/src/lcats/analysis/corpus/annotate.py
depends_on: []
blocked_by: []
blocked: false
blocked_reason: null
resolution: null
expected_actions:
  - edit_file
  - run_tests
  - create_pr
forbidden_actions:
  - force_push
  - delete_branch
  - modify_lcats_promote
  - implement_local_model_assessment_source
  - implement_human_adjudication_ui
acceptance:
  - "lcats annotate, when a valid genre-sidecar-v1 genre.json already exists for a story, appends a new assessment to its assessments[] list rather than overwriting the file"
  - "lcats annotate, when a legacy flat genre.json exists for a story (per genre_sidecar.is_legacy_flat_sidecar()), converts it to the append-only genre-sidecar-v1 shape first, preserving its existing evidence, then appends"
  - "lcats annotate's existing create-fresh behavior is unchanged when no genre.json exists yet for a story"
  - "Every write goes through genre_sidecar.validate_sidecar() before being committed to disk; a sidecar that would fail validation is refused, not written"
  - "The append path preserves annotate.py's existing checkpoint-safe/atomic write conventions (_atomic_write_text/_write_json), not a new less-safe write path"
  - "Both model-sourced and human-sourced assessment records can be appended through the new code path, even if only the model path is exercised in this item's own real validation"
  - "annotate.py's existing behavior for scenes.json and README.md writes is unchanged"
  - "scripts/test passes with no new failures"
  - "lrh validate reports 0 errors"
required_evidence:
  - test_output
  - lrh_validate
  - manual_review
artifacts_expected:
  - lcats/src/lcats/analysis/corpus/annotate.py
  - lcats/tests/analysis_tests/annotate_test.py
---

# Work Item: WI-GENRE-0076

## Summary

Teach `lcats annotate` to append a new genre assessment to an existing
`genre.json` `genre-sidecar-v1` sidecar instead of overwriting it, and to
convert a legacy flat sidecar to the append-only shape when one is found.
This is Step 7 of `PROP-GENRE-EVIDENCE-SIDECARS`'s Implementation Plan.

## Problem / Context

`WI-GENRE-0003`/`WI-GENRE-0004` defined and exercised the `genre-sidecar-v1`
append-only schema (`lcats.analysis.corpus.genre_sidecar`,
`SCHEMA_VERSION = "genre-sidecar-v1"`) with real, validated evidence - 146
real records in `experiments/05_metadata_genre_prefilter/results/full_scan/validation_results.jsonl`.
But `lcats annotate` (`lcats/src/lcats/analysis/corpus/annotate.py`) never
imports or calls `genre_sidecar` anywhere in production code - confirmed via
`grep -rn "genre_sidecar" lcats/src/lcats/analysis/corpus/annotate.py`,
which returns nothing (the only "genre_sidecar" string matches anywhere
near `annotate.py` are unrelated test method names in
`annotate_test.py`/`promote_test.py` that happen to contain the phrase).
`annotate.py`'s existing `genre.json` handling
(`_annotate_genre()`/`annotate_story()`) writes the older, pre-workstream
single-object format. There is currently no way to add a second assessment
(a different model's opinion, a human review) to an existing sidecar
without hand-written one-off code or an outright overwrite that discards
prior evidence.

### Duplication search
- In-repo: No existing append-mode genre-sidecar write path in
  `annotate.py` - confirmed via the grep above.
- Sibling repos: None identified.
- External libraries: None - native LCATS corpus-annotation logic.
- Recommendation: Proceed.

### Demand search
- Work items: `WI-GENRE-0003` (resolved) defined the schema this item
  wires in; `WI-GENRE-0004` (resolved) produced real assessment records in
  this same shape, currently experiment-local only. No other work item
  covers wiring the schema into `lcats annotate`.
- Proposals: `PROP-GENRE-EVIDENCE-SIDECARS` requests this directly as
  Implementation Plan Step 7.
- Workstreams: `WS-GENRE-EVIDENCE-SIDECARS` lists this as its own next
  step; still `status: proposed`, not yet closed.
- Backlog: No matching entry found in `project/design/backlog.md`.
- Recommendation: Proceed.

## Scope

- Extend `lcats annotate`'s genre-writing path so that an existing valid
  `genre-sidecar-v1` sidecar gets a new assessment appended to
  `assessments[]`, not overwritten.
- Handle the legacy-flat-sidecar case: convert to the v1 shape first
  (preserving existing evidence), then append.
- Preserve unchanged behavior when no `genre.json` exists yet.
- Reuse `genre_sidecar.validate_sidecar()` before every write.
- Preserve `annotate.py`'s existing atomic-write conventions.

## Required Changes

1. **`lcats/src/lcats/analysis/corpus/annotate.py`**: extend
   `_annotate_genre()`/`annotate_story()` (or add new functions alongside
   them, implementer's choice, justified against the existing code shape)
   to detect an existing `genre.json`, branch on
   `genre_sidecar.validate_sidecar()` (valid v1 → append) vs.
   `genre_sidecar.is_legacy_flat_sidecar()` (legacy → convert, then append)
   vs. neither (create fresh, unchanged from today). Both model-labeled
   and human-labeled assessment records must be constructible through
   whatever new function(s) this adds - check `genre_sidecar.py`'s
   `_is_model_assessment_label()`/`_validate_model_run_identity()` for
   what distinguishes them.
2. **`lcats/tests/analysis_tests/annotate_test.py`**: add tests covering:
   append to an existing valid v1 sidecar; convert-then-append for a
   legacy flat sidecar; unchanged create-fresh behavior; refusal of a
   write that would fail `validate_sidecar()`; atomic-write behavior
   preserved (no partial/corrupt file on a simulated failure); and
   confirmation `scenes.json`/`README.md` writes are unaffected. Where
   useful, replay real records from
   `experiments/05_metadata_genre_prefilter/results/full_scan/validation_results.jsonl`
   as fixtures rather than only synthetic examples.

## Non-Goals

- Does not touch `lcats promote` or any corpora-promotion mechanism - that
  is a separate work item (`WI-GENRE-0075`), no dependency either
  direction.
- Does not implement the local-model (`gpt-oss:20b`) assessment source
  (Implementation Plan Step 8) or human-review/adjudication UI (Step 9) -
  this item only needs the append *mechanism* to exist and be exercised by
  at least the model-assessment path.
- Does not change existing `scenes.json`/`README.md` write behavior.

## Acceptance Criteria

(see frontmatter `acceptance:` above)

## Validation

- `scripts/version tools`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh validate`

## Risk Notes

- Getting the atomic-write/checkpoint-safety property wrong here is worse
  than doing nothing - a half-written append could corrupt real evidence
  a researcher depends on. Reuse `annotate.py`'s existing
  `_atomic_write_text()`/`_write_json()` helpers rather than writing a new
  path from scratch.
- Do not let "append mode" quietly become "always append, never validate"
  - every write must still go through `genre_sidecar.validate_sidecar()`
  first, exactly as `WI-GENRE-0004`'s real validation run already does.

## Dependencies / Order

No `depends_on`. No dependency relationship with `WI-GENRE-0075` or
`WI-GENRE-0077` in either direction; may proceed in parallel with
`WI-GENRE-0075`.

## Related Workstream and Designs

- Workstream: `project/workstreams/proposed/WS-GENRE-EVIDENCE-SIDECARS.md`
- Design: `project/design/proposals/proposed/genre-evidence-sidecars/00_proposal.md`
