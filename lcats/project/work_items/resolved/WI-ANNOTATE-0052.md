---
resolution: Merged via https://github.com/xenotaur/LCATS/pull/248 (merge commit 6756195849484991d1386cff33abe799b723b571). survey_collection now validates genre.json/scenes.json content (parse, shape, required-key type) and blocks promotion of a malformed sidecar.
blocked_reason: null
blocked: false
id: WI-ANNOTATE-0052
title: Validate sidecar content in lcats promote's release gate
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
depends_on:
  - WI-ANNOTATE-0051
blocked_by: []
expected_actions:
  - edit_file
  - run_tests
  - create_pr
forbidden_actions:
  - force_push
  - delete_branch
  - implement_specials_audit_sidecar
acceptance:
  - survey_collection (or a sibling function it calls) validates genre.json/scenes.json content, not just each story's body for mojibake
  - A malformed sidecar causes the collection to be blocked from promotion, the same way a mojibake finding does
  - lrh validate reports 0 errors
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
artifacts_expected:
  - lcats/src/lcats/analysis/corpus/promote.py
---

## Summary

Extend `lcats promote`'s `survey_collection` release gate to validate
`genre.json`/`scenes.json` sidecar content, not just each story's body
for mojibake, so a malformed sidecar blocks promotion instead of being
silently copied to `corpora/`.

## Problem / Context

`survey_collection` (`lcats/src/lcats/analysis/corpus/promote.py:70-125`)
today only reads each story's `body` field for mojibake scanning — it
has no concept of validating a sidecar's own content before promotion.
Once WI-ANNOTATE-0051 lands, story buckets will contain
`genre.json`/`scenes.json` sidecars whose correctness `promote` cannot
currently verify; a malformed sidecar would be wholesale-copied to
`corpora/` via `_copy_collection`'s `shutil.copytree`
(`promote.py:172-176`) with no gate at all.

`PROP-WORLDCON-FAST-PATH-ANNOTATION`'s Design Decision 4 (user
decision, recorded 2026-08-05) chose to extend `promote`'s gate rather
than trust `lcats annotate` alone to have validated its own output —
`promote` is the actual release gate to `corpora/`.

### Duplication search
- In-repo: No existing sidecar-content validation anywhere in
  `promote.py` or elsewhere.
- Sibling repos: None identified.
- External libraries: None identified — expected to be plain parse/shape
  checks, not a schema-validation library (per the proposal's Non-Goals).
- Recommendation: Proceed.

### Demand search
- Work items: None found requesting this directly beyond this item's own
  workstream.
- Proposals: `PROP-WORLDCON-FAST-PATH-ANNOTATION`'s Design Decision 4
  requests exactly this.
- Backlog: No matching entry.
- Recommendation: Proceed.

## Scope

- Extend `survey_collection` (or add a sibling function it calls) to
  check each story bucket's `genre.json`/`scenes.json` — if present —
  for basic validity (parses as JSON, has the expected top-level shape).
- A malformed sidecar becomes a blocking finding, same severity class as
  a mojibake finding.
- Depth of validation is parse/shape-level, not full schema validation
  (no new dependency, per the proposal's Non-Goals).

## Required Changes

1. In `lcats/src/lcats/analysis/corpus/promote.py`, add sidecar-content
   validation to `survey_collection`'s per-story loop (or a helper it
   calls), checking `genre.json`/`scenes.json` when present in a story's
   bucket directory.
2. Extend `BlockingFinding` (or add a parallel finding type) to
   represent a malformed-sidecar finding distinctly from a mojibake
   finding, so `CollectionSurveyResult` reporting stays clear about
   which kind of problem blocked promotion.
3. Add unit tests: a clean collection with valid sidecars promotes; a
   collection with a malformed `genre.json`/`scenes.json` is blocked and
   reported, not silently copied.

## Non-Goals

- Does not adopt a schema-validation library — parse/shape checks only.
- Does not validate the specials/mojibake audit sidecar — that sidecar
  doesn't exist yet (deferred per the proposal's Decision 1).
- Does not change `lcats survey`'s separate CLI-level exclusion-policy
  inconsistency — `WS-SPECIALS-CLEANUP`'s scope.

## Acceptance Criteria

- A collection with a malformed `genre.json` or `scenes.json` is
  blocked from promotion and reported in `CollectionSurveyResult`.
- A collection with valid (or absent) sidecars promotes exactly as
  before this change.
- `lrh validate` reports 0 errors.

## Validation

- `scripts/version tools`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh validate`

## Risk Notes

- Must not change behavior for collections with no sidecars at all
  (today's normal case) — validation only applies when a sidecar file is
  present.

## Dependencies / Order

Depends on WI-ANNOTATE-0051 (needs the real sidecar shape to validate
against). WI-ANNOTATE-0054 depends on this item.

## Related Workstream and Designs

- Workstream: `project/workstreams/proposed/WS-WORLDCON-FAST-PATH-ANNOTATION.md`
- Design: `project/design/proposals/adopted/worldcon-fast-path-annotation/00_proposal.md`
  (Design Decision 4)
