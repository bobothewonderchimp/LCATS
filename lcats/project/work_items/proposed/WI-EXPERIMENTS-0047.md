---
resolution: null
blocked_reason: null
blocked: false
id: WI-EXPERIMENTS-0047
title: Fix non-recursive file discovery in run_comparison.py and smoke_test.py
type: deliverable
status: proposed
priority: medium
owner: unassigned
contributors: []
assigned_agents: []
related_focus:
  - FOCUS-WORLDCON-2026
related_roadmap: []
related_workstreams: []
related_design:
  - lcats/project/design/backlog.md
depends_on: []
blocked_by: []
expected_actions:
  - edit_file
  - create_file
  - run_tests
  - create_pr
forbidden_actions:
  - force_push
  - delete_branch
  - modify_check_segmentation_reliability_script
  - modify_assess_story_title_fallback
acceptance:
  - "run_comparison.py's story_files selection uses discovery.iter_collection_story_files, not corpus_dir.iterdir() filtered by suffix"
  - "smoke_test.py's _actual_sample uses the same selector, not corpus_dir.glob('*.json')"
  - "Both scripts correctly find real bucket-layout story files (<collection>/<story>/story.json) under a single collection directory"
  - "run_comparison.py's per-story progress print no longer shows the literal string \"story.json\" for every story"
  - "A new regression test proves both scripts find bucket-layout stories correctly, and that the prior flat-layout-only behavior is gone"
  - "lrh validate reports 0 errors"
required_evidence:
  - manual_review
  - test_output
  - lrh_validate
artifacts_expected:
  - experiments/02_llm_backend_comparison/run_comparison.py
  - experiments/02_llm_backend_comparison/smoke_test.py
  - experiments/02_llm_backend_comparison/run_comparison_test.py
---

# Work Item: Fix non-recursive file discovery in run_comparison.py and smoke_test.py

## Summary

Fix `run_comparison.py` and `smoke_test.py`'s non-recursive file
selection (`corpus_dir.iterdir()` filtered by suffix, and
`corpus_dir.glob("*.json")` respectively), which currently finds zero
files against any real bucket-layout collection since a collection's
immediate children are now story *directories*, not `.json` files.

## Problem / Context

Both scripts assume the retracted flat `<collection>/<story>.json`
layout when selecting story files from a single collection directory
(`--corpus-dir` / `data/lovecraft`, `data/london`). Re-verified
2026-08-02 directly against current code: `run_comparison.py:57` does
`sorted(f for f in corpus_dir.iterdir() if f.suffix == ".json")`; under
bucket layout this finds **zero** files, but `run()` explicitly checks
`if not story_files:` and exits 1 with a clear (if confusingly worded)
error -- this fails **loud**, not silently, contrary to how earlier
notes framed it. `smoke_test.py:109`'s `corpus_dir.glob("*.json")` has
the same bug and propagates the same loud failure through `_run_leg` ->
`run_comparison.run()`, correctly reporting `FAILED`/
`Smoke test INCOMPLETE`. Also found while re-reading the full script:
`run_comparison.py:82`'s progress print
(`f"assessing {story_path.name} ..."`) would show the literal string
`"story.json"` for every story once file selection is fixed -- the same
leaf-filename-collapse issue as the identity problem elsewhere, but
purely cosmetic here (log readability, not correctness) -- fixed in the
same pass since it's directly adjacent to the line being changed.

### Duplication search
- In-repo: No existing implementation found. Two adopted design
  proposals (`lcats-packaging-modernization/00_proposal.md`,
  `lcats-story-bucket-layout/00_proposal.md`) reference these scripts in
  passing but neither fixes this.
- Sibling repos: None identified.
- External libraries: None identified -- internal script-specific bug fix.
- Recommendation: Proceed.

### Demand search
- Work items: Found: `WI-EXPERIMENTS-0046`'s own Non-Goals explicitly
  defers this exact fix ("a separate backlog item, to be scoped next").
- Proposals: None found.
- Backlog: Found: "Non-recursive glob bugs in two experiment scripts"
  in `lcats/project/design/backlog.md`. This work item is created
  specifically to resolve that entry.
- Recommendation: Offer to remove/mark-resolved the matching
  `backlog.md` entry once this work item's creation PR is confirmed (not
  auto-closed).

## Scope

- Fix file selection in both scripts to correctly find bucket-layout
  story files under a single collection directory.
- Fix the resulting cosmetic progress-print issue in `run_comparison.py`.
- Add a regression test.
- Do not touch `check_segmentation_reliability.py`
  (`WI-EXPERIMENTS-0046`'s territory) or `assess_story`'s title-fallback
  (separate, tiny backlog item).

## Required Changes

1. In `run_comparison.py`, replace
   `sorted(f for f in corpus_dir.iterdir() if f.suffix == ".json")`
   with `sorted(discovery.iter_collection_story_files(corpus_dir))` (the
   canonical single-collection selector -- matches this call shape
   exactly, since both scripts scan one named collection directory, not
   a multi-collection root). Import `lcats.analysis.corpus.discovery`.
2. In the same file, change the per-story progress print to use a real
   per-story identifier (e.g. `story_path.parent.name`) instead of
   `story_path.name`.
3. In `smoke_test.py`, replace `sorted(corpus_dir.glob("*.json"))` in
   `_actual_sample` with the same
   `discovery.iter_collection_story_files(corpus_dir)` call.
4. Create `experiments/02_llm_backend_comparison/run_comparison_test.py`
   (matching the existing `run_pilot_test.py`/
   `check_segmentation_reliability_test.py` sibling-test convention)
   asserting: both scripts find real bucket-layout story files under a
   fixture collection directory; the old flat-layout assumption is gone
   (a flat `.json` file alongside a real bucket story is not found).

## Non-Goals

- Does not touch `check_segmentation_reliability.py` --
  `WI-EXPERIMENTS-0046`'s territory.
- Does not fix `assess_story`'s error-path title fallback or
  `compare_results.py`'s similar fallback -- separate, tiny backlog
  items.
- Does not touch the two flagged notebooks -- a separate backlog item.
- Does not change either script's overall CLI interface or output
  format -- only file selection and the one cosmetic print.

## Acceptance Criteria

- `run_comparison.py`'s story-file selection uses
  `discovery.iter_collection_story_files`, not
  `corpus_dir.iterdir()` filtered by suffix.
- `smoke_test.py`'s `_actual_sample` uses the same selector, not
  `corpus_dir.glob('*.json')`.
- Both scripts correctly find real bucket-layout story files under a
  single collection directory.
- `run_comparison.py`'s per-story progress print no longer shows the
  literal string `"story.json"` for every story.
- A new regression test proves both scripts find bucket-layout stories
  correctly, and that the prior flat-layout-only behavior is gone.
- `lrh validate` reports 0 errors.

## Validation

- `scripts/version tools`
- `lrh validate`
- `python -m pytest experiments/02_llm_backend_comparison/run_comparison_test.py`
- `python -m pytest tests/`

## Risk Notes

- `iter_collection_story_files` applies only one level of nesting
  relative to the directory it's given -- matches both scripts' existing
  "one collection directory in, its stories out" usage exactly, no
  behavior change beyond correctness.
- Neither script currently has any test coverage at all (confirmed: no
  `run_comparison_test.py`/`smoke_test_test.py` exist today), so this
  regression test is new coverage, not a modification to existing tests.
