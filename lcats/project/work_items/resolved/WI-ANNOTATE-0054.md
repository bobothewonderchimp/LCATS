---
resolution: Merged via https://github.com/xenotaur/LCATS/pull/253 (merge commit d6ba49203f2c7952df37954bcfc0fb9415e9c399). Ran lcats annotate over a 24-story subset (3 per genre x 8 VALID_GENRES), validated output by hand, and produced a per-genre stats report. Surfaced two real data-quality findings, both documented with recommended follow-up work items rather than fixed in this evaluation-only item: (1) ~42% secondary_genre corruption in assess.py's genre-detection output, and (2) scene-segmentation offset corruption in text_segmenter.py affecting all 3 corpora/london stories in the trial.
blocked_reason: null
blocked: false
id: WI-ANNOTATE-0054
title: Run lcats annotate over a per-genre subset and collect statistics
type: evaluation
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
  - project/work_items/resolved/WI-ASSESS-0031.md
  - project/work_items/resolved/WI-STATS-0049.md
depends_on:
  - WI-ANNOTATE-0051
  - WI-ANNOTATE-0052
  - WI-STATS-0049
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
  - lcats annotate has been run against a small subset of stories across all 8 current VALID_GENRES
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
all 8 current `VALID_GENRES` (science fiction, horror, humor, western,
romance, mystery, fantasy, adventure), validate the output, and collect
per-genre statistics — delivering the first real dataset slice for the
Worldcon 2026 paper via the fast-path annotation pipeline.

## Problem / Context

This is the final item in `WS-WORLDCON-FAST-PATH-ANNOTATION`'s planned
sequence, closing the loop from `PROP-WORLDCON-FAST-PATH-ANNOTATION`'s
original motivation: a real, usable dataset for the paper within ~10
days, using the mature parts of the pipeline (genre detection,
scene/sequel segmentation) rather than the too-slow/costly/unreliable
ERW extractor. It depends on WI-ANNOTATE-0051 (the command) and
WI-ANNOTATE-0052 (its promote-side validation), plus the `lcats stats`
selector fix — since a real, paid run should not proceed against code
with known truncation, corpus-root, or stats-corruption bugs still
open. The selector fix itself landed as `WI-STATS-0049` (PR #238), from
a concurrent session, before this workstream's own `WI-ANNOTATE-0053`
was started; `WI-ANNOTATE-0053` was abandoned as redundant and this
item's dependency retargeted to `WI-STATS-0049` directly.

`WI-ASSESS-0031` (4→8 genre extension) — originally a parallel,
in-progress effort this workstream's Step 7 was gated on — landed via
PR #224 and closed out before this work item was drafted (confirmed via
`assess.VALID_GENRES` on `main`, which now lists all 8 target genres:
science fiction, horror, humor, western, romance, mystery, fantasy,
adventure). That gate is therefore already satisfied: this item covers
all 8 genres directly rather than deferring 4 of them to a later
expansion (review finding, PR #233 — an earlier draft of this item
scoped only the original 4 genres, based on the state of `main` at the
time the proposal/workstream were drafted, which had since gone stale
by the time this item was written).

### Duplication search
- In-repo: No existing per-genre annotation run or stats report for
  this pipeline.
- Sibling repos: None identified.
- External libraries: None applicable.
- Recommendation: Proceed.

### Demand search
- Work items: `WI-ASSESS-0031` (resolved) is the reason this item's
  scope covers 8 genres rather than 4 — no further action needed there.
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
   script/notebook) summarizing results across all 8 genres.
5. Record real run cost/timing, following this project's convention of
   surfacing cost data (see `PROP-LCATS-PIPELINE-CHECKPOINTING`'s
   motivation around `run_pilot.py`'s prior cost-visibility gaps).

## Non-Goals

- Does not touch ERW event/relation extraction.
- Does not implement the specials/mojibake audit sidecar.
- Does not attempt full-corpus-scale annotation — this item is a small,
  bounded first run across all 8 genres, not the eventual full dataset.

## Acceptance Criteria

- `lcats annotate` has been run successfully against a subset spanning
  all 8 current `VALID_GENRES`.
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

Depends on WI-ANNOTATE-0051, WI-ANNOTATE-0052, and WI-STATS-0049 (the
`lcats stats` selector fix, landed independently — see Problem/Context)
— the command, its promote-side validation, and the stats-selector fix
must all land first. This is the last item in
`WS-WORLDCON-FAST-PATH-ANNOTATION`'s planned sequence.

## Related Workstream and Designs

- Workstream: `project/workstreams/proposed/WS-WORLDCON-FAST-PATH-ANNOTATION.md`
- Design: `project/design/proposals/adopted/worldcon-fast-path-annotation/00_proposal.md`
  (Implementation Plan, Step 5; original plan Steps 6 and 8)
- Resolved: `project/work_items/resolved/WI-ASSESS-0031.md` (4→8 genre
  extension; the reason this item's scope is 8 genres, not 4)

## Open Questions

- Exact story-subset selection criteria (count per genre, sampling
  method) — left to this item's own implementation, per the proposal's
  own Open Questions.
- Exact stats report format — left to this item's own implementation.
