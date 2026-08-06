---
resolution: null
blocked_reason: null
blocked: false
id: WI-ANNOTATE-0054
title: Run lcats annotate over a per-genre subset and collect statistics
type: evaluation
status: proposed
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
  - WI-ANNOTATE-0052
  - WI-ANNOTATE-0053
blocked_by: []
expected_actions:
  - run_tests
  - create_report
  - create_pr
forbidden_actions:
  - force_push
  - delete_branch
  - implement_erw_extraction
acceptance:
  - lcats annotate has been run against a small subset of stories across all 4 current VALID_GENRES
  - Output sidecars (genre.json, scenes.json, README.md) validated by hand against a sample
  - Per-genre statistics collected and reported
  - lrh validate reports 0 errors
required_evidence:
  - manual_review
  - lrh_validate
  - validation_output
artifacts_expected:
  - A stats report or notebook summarizing per-genre results
---

## Summary

Run `lcats annotate` over a small per-genre subset of stories across
the current 4 `VALID_GENRES` (science fiction, horror, western,
romance), validate the output, and collect per-genre statistics —
delivering the first real dataset slice for the Worldcon 2026 paper via
the fast-path annotation pipeline.

## Problem / Context

This is the final item in `WS-WORLDCON-FAST-PATH-ANNOTATION`'s planned
sequence, closing the loop from `PROP-WORLDCON-FAST-PATH-ANNOTATION`'s
original motivation: a real, usable dataset for the paper within ~10
days, using the mature parts of the pipeline (genre detection,
scene/sequel segmentation) rather than the too-slow/costly/unreliable
ERW extractor. It depends on all three preceding deliverable items
(WI-ANNOTATE-0051/0052/0053) — the command, its promote-side validation,
and the stats-selector fix — since a real, paid run should not proceed
against code with known truncation, corpus-root, or stats-corruption
bugs still open.

Expansion to the full 8-genre Worldcon target is explicitly out of
scope here — `WI-ASSESS-0031` (4→8 genre extension) is being worked in
a separate, parallel session, and this item works with today's 4
genres, per the proposal's own Step 7 gating.

### Duplication search
- In-repo: No existing per-genre annotation run or stats report for
  this pipeline.
- Sibling repos: None identified.
- External libraries: None applicable.
- Recommendation: Proceed.

### Demand search
- Work items: `WI-ASSESS-0031` is related (future 8-genre expansion) but
  explicitly not a prerequisite for this item's current-4-genre scope.
- Proposals: `PROP-WORLDCON-FAST-PATH-ANNOTATION`'s plan Steps 6 and 8
  request exactly this run and stats collection.
- Backlog: No matching entry.
- Recommendation: Proceed.

## Scope

- Select a small subset of stories per genre (exact selection criteria
  left to this item's own implementation — an explicit Open Question in
  both the proposal and workstream).
- Run `lcats annotate` against that subset.
- Manually validate a sample of the output sidecars.
- Collect and report per-genre statistics (e.g. distribution of scene
  counts, genre-confidence scores, any exclusions/failures).

## Required Changes

1. Decide and document the story-subset selection criteria (count per
   genre, selection method).
2. Run `lcats annotate` against the selected subset.
3. Manually inspect a sample of the resulting `genre.json`/`scenes.json`/
   `README.md` output for correctness.
4. Produce a stats report (format left to implementation — could reuse
   `lcats stats` output plus custom per-genre aggregation, or a small
   script/notebook) summarizing results across the 4 genres.
5. Record real run cost/timing, following this project's convention of
   surfacing cost data (see `PROP-LCATS-PIPELINE-CHECKPOINTING`'s
   motivation around `run_pilot.py`'s prior cost-visibility gaps).

## Non-Goals

- Does not implement the 8-genre expansion — gated on `WI-ASSESS-0031`
  landing in its own parallel session.
- Does not touch ERW event/relation extraction.
- Does not implement the specials/mojibake audit sidecar.

## Acceptance Criteria

- `lcats annotate` has been run successfully against a subset spanning
  all 4 current `VALID_GENRES`.
- Sample output validated by hand, not just assumed correct from a
  clean exit code.
- A per-genre statistics report/artifact exists and is committed
  alongside this item's execution record.
- `lrh validate` reports 0 errors.

## Validation

- `scripts/version tools`
- `lrh validate`
- Manual review of a sample of generated sidecars

## Risk Notes

- This is the first real paid run of the new pipeline — budget for
  possible retries/failures even after WI-ANNOTATE-0050's fixes, and
  checkpoint-resume (WI-ANNOTATE-0051) should make a partial-failure
  resume cheap rather than requiring a full restart.
- Keep the subset genuinely small for this first run — full-corpus scale
  is separate, later work, not this item's scope.

## Dependencies / Order

Depends on WI-ANNOTATE-0051, WI-ANNOTATE-0052, and WI-ANNOTATE-0053 —
the command, its promote-side validation, and the stats-selector fix
must all land first. This is the last item in
`WS-WORLDCON-FAST-PATH-ANNOTATION`'s planned sequence.

## Related Workstream and Designs

- Workstream: `project/workstreams/proposed/WS-WORLDCON-FAST-PATH-ANNOTATION.md`
- Design: `project/design/proposals/adopted/worldcon-fast-path-annotation/00_proposal.md`
  (Implementation Plan, Step 5; original plan Steps 6 and 8)

## Open Questions

- Exact story-subset selection criteria (count per genre, sampling
  method) — left to this item's own implementation, per the proposal's
  own Open Questions.
- Exact stats report format — left to this item's own implementation.
