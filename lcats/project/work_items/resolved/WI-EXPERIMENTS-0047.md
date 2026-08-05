---
resolution: "Implemented and merged via https://github.com/xenotaur/LCATS/pull/222 (squash commit 262cbed5d0f6e262f0a33e1a8355c0c36decfd78)."
blocked_reason: null
blocked: false
id: WI-EXPERIMENTS-0047
title: Fix non-recursive file discovery in run_comparison.py and smoke_test.py
type: deliverable
status: resolved
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
  - "smoke_test.py's _RUNS point at the always-present corpora/lovecraft and corpora/london, not lcats/data/lovecraft and lcats/data/london, which do not exist without a prior lcats gather run"
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

**One additional gap found via review of this work item's own creation
PR, before any implementation was written:** `smoke_test.py`'s `_RUNS`
config (lines 93-103) points `corpus_dir` at
`_LCATS_ROOT / "data/lovecraft"` and `_LCATS_ROOT / "data/london"`
(`_LCATS_ROOT` = the `lcats/` directory, line 183). `data/` is the
gitignored, regenerable working cache -- it does not exist at all in a
fresh checkout until someone runs a real `lcats gather`. Fixing the
file-selector bug alone would not make the smoke test runnable: without
`data/lovecraft` existing at all, `run_comparison.run()`'s own
`if not corpus_dir.is_dir(): return 1` check fails first, for a
different, pre-existing reason unrelated to the bucket-layout bug. The
real, always-present, tracked collections for these two genres are
`corpora/lovecraft` and `corpora/london` (repo root, confirmed present).
Since either corpus source serves the smoke test's actual purpose
(sanity-checking the assess pipeline against a small real sample)
equally well, this work item also repoints `_RUNS` at the tracked
`corpora/` snapshot, so the documented smoke test invocation
(`python experiments/02_llm_backend_comparison/smoke_test.py`) actually
works out of the box in any checkout, not just one where `lcats gather`
has already been run.

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
- Fix `smoke_test.py`'s configured corpus roots so the documented
  invocation actually runs against the always-present tracked `corpora/`
  snapshot, not the gitignored, gather-populated `data/` directory.
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
4. In `smoke_test.py`, change `_RUNS`'s `corpus_subdir` values from
   `"data/lovecraft"`/`"data/london"` to `"lovecraft"`/`"london"`, and
   change line 183's `corpus_dir = _LCATS_ROOT / run_cfg["corpus_subdir"]`
   to resolve against `_REPO_ROOT / "corpora" / run_cfg["corpus_subdir"]`
   instead (`_REPO_ROOT` is already defined at line 42), so the smoke
   test runs against the tracked, always-present `corpora/lovecraft` and
   `corpora/london` collections.
5. Create `experiments/02_llm_backend_comparison/run_comparison_test.py`
   (matching the existing `run_pilot_test.py` sibling-test convention --
   `check_segmentation_reliability_test.py` is planned by
   `WI-EXPERIMENTS-0046` but does not exist yet, so it is not itself a
   precedent to match) asserting: both scripts find real bucket-layout
   story files under a fixture collection directory; the old
   flat-layout assumption is gone (a flat `.json` file alongside a real
   bucket story is not found).

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
- `smoke_test.py`'s `_RUNS` point at `corpora/lovecraft`/`corpora/london`,
  not `lcats/data/lovecraft`/`lcats/data/london`.
- Both scripts correctly find real bucket-layout story files under a
  single collection directory.
- Running `python experiments/02_llm_backend_comparison/smoke_test.py`
  in a fresh checkout (no prior `lcats gather` run) reaches the
  file-discovery step -- i.e. it no longer fails at the
  `corpus_dir.is_dir()` precondition check for a missing `data/`
  directory.
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
- Repointing `smoke_test.py` from `data/` to `corpora/` changes which
  corpus content the smoke test exercises (the promoted release
  snapshot instead of a live-gathered working copy). This is an
  intentional trade for actually being runnable out of the box; the
  smoke test's purpose (sanity-checking the assess pipeline against a
  small real sample) is served equally well by either source.
