---
resolution: null
blocked_reason: null
blocked: false
id: WI-ANNOTATE-0053
title: Fix lcats stats file-discovery selector
type: deliverable
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
  - project/design/backlog.md
depends_on: []
blocked_by: []
expected_actions:
  - edit_file
  - run_tests
  - create_pr
forbidden_actions:
  - force_push
  - delete_branch
acceptance:
  - run_stats uses discovery.find_json_files instead of discovery.find_corpus_stories
  - A regression test asserts sidecar files (genre.json, scenes.json) are excluded from stats output
  - lrh validate reports 0 errors
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
artifacts_expected:
  - src/lcats/analysis/corpus/cli.py
---

## Summary

Fix `lcats stats`'s file-discovery selector: `run_stats` currently uses
the broad `discovery.find_corpus_stories` instead of the canonical
`discovery.find_json_files`, which `survey`/`assess` already use — a
pre-existing, previously-unscoped bug that WI-ANNOTATE-0051's new
sidecars would silently trigger for the first time.

## Problem / Context

`src/lcats/analysis/corpus/cli.py:376-402`'s `run_stats` calls
`discovery.find_corpus_stories(directory, ignore_dir_names=("cache",),
sort=True)` (line 387) — the broad recursive JSON finder — rather than
the canonical-only selector (`discovery.find_json_files`) that `lcats
survey` and `lcats assess` both use. This was confirmed as a real, P1,
silent bug in `project/design/backlog.md` on 2026-08-02, with a
recommended fix already noted there but no work item filed for it
until now.

Today's `corpora/` tree happens to contain zero sidecar JSON files, so
the bug is latent. Once WI-ANNOTATE-0051's `lcats annotate` starts
writing `genre.json`/`scenes.json` sidecars into bucket directories,
`lcats stats` will silently start counting those sidecars as additional
stories, corrupting exactly the per-genre statistics
`WS-WORLDCON-FAST-PATH-ANNOTATION`'s final run (WI-ANNOTATE-0054) needs.
This item exists to close that gap before it can be triggered by this
workstream's own output.

### Duplication search
- In-repo: No existing fix. `survey`/`assess` already use the correct
  selector (`find_json_files`) as the pattern to follow.
- Sibling repos: None identified.
- External libraries: None applicable.
- Recommendation: Proceed.

### Demand search
- Work items: None found requesting this fix directly prior to this
  item.
- Proposals: `PROP-WORLDCON-FAST-PATH-ANNOTATION`'s Prior Art Check
  (Demand search) surfaced this exact bug and recommended folding a fix
  into this workstream.
- Backlog: `project/design/backlog.md`, "`lcats stats` uses the wrong
  (broad) story-file selector — P1, silent" — this item resolves that
  entry.
- Recommendation: Proceed; mark the backlog entry resolved once this
  item lands.

## Scope

- Switch `run_stats`'s file-discovery call from
  `discovery.find_corpus_stories` to `discovery.find_json_files`.
- Add a regression test proving sidecar files are excluded from stats
  output.
- Update `project/design/backlog.md`'s matching entry to resolved.

## Required Changes

1. `src/lcats/analysis/corpus/cli.py:387`: replace
   `discovery.find_corpus_stories(directory, ignore_dir_names=("cache",),
   sort=True)` with `discovery.find_json_files([directory])` (or the
   equivalent call signature `find_json_files` actually exposes — verify
   against its current definition before wiring the call).
2. Add a test fixture with a collection containing both `story.json`
   files and at least one sidecar (`genre.json`/`scenes.json`), asserting
   `compute_corpus_stats` only counts the `story.json` files.
3. Mark the matching `project/design/backlog.md` entry resolved, per this
   project's convention for closing out backlog items.

## Non-Goals

- Does not change `lcats survey`'s separate exclusion-policy
  inconsistency (`DEFAULT_EXCLUDED_CHARS` vs. `excluded=set()`) —
  `WS-SPECIALS-CLEANUP`'s scope.
- Does not change `find_corpus_stories` itself — it may still be the
  correct selector for other call sites; this item only fixes
  `run_stats`'s specific misuse of it.

## Acceptance Criteria

- `run_stats` uses `discovery.find_json_files`, not
  `discovery.find_corpus_stories`.
- A regression test demonstrates a sidecar file is excluded from
  `lcats stats` output.
- `project/design/backlog.md`'s matching entry is marked resolved.
- `lrh validate` reports 0 errors.

## Validation

- `scripts/version tools`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh validate`

## Risk Notes

- Verify `find_json_files`'s actual call signature before wiring —
  earlier proposal drafts in this workstream have already had one
  factual mis-citation corrected during review; don't repeat that
  pattern here.

## Dependencies / Order

No dependencies on the other 4 items — can be worked in parallel with
WI-ANNOTATE-0051/0052. WI-ANNOTATE-0054 depends on this item.

## Related Workstream and Designs

- Workstream: `project/workstreams/proposed/WS-WORLDCON-FAST-PATH-ANNOTATION.md`
- Design: `project/design/proposals/adopted/worldcon-fast-path-annotation/00_proposal.md`
  (Design Decision 7)
- Backlog: `project/design/backlog.md`
