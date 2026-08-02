---
resolution: null
blocked_reason: null
blocked: false
id: WI-EXPERIMENTS-0046
title: Fix stem-collision bug in check_segmentation_reliability.py's result caching
type: deliverable
status: proposed
owner: unassigned
contributors: []
assigned_agents: []
related_focus:
  - FOCUS-WORLDCON-2026
related_roadmap: []
related_workstreams: []
related_design:
  - project/design/backlog.md
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
  - modify_run_pilot_py
  - change_file_discovery_logic
acceptance:
  - "check_segmentation_reliability.py's per-story result path/cache key is derived from the story's directory slug (path.parent.name), not path.stem"
  - "The cached record's own story_id field matches the same directory-slug value"
  - "A new regression test proves two distinct stories no longer collide onto the same output/cache file, and single-story behavior is unchanged"
  - "lrh validate reports 0 errors"
required_evidence:
  - manual_review
  - test_output
artifacts_expected:
  - experiments/03_cross_segment_relation_pilot/check_segmentation_reliability.py
  - experiments/03_cross_segment_relation_pilot/check_segmentation_reliability_test.py
---

# Work Item: Fix stem-collision bug in check_segmentation_reliability.py's result caching

## Summary

Fix `check_segmentation_reliability.py`'s per-story output/cache file
naming, which currently derives the filename from `path.stem` -- the
literal string `"story"` for every bucket-layout file -- causing every
story after the first to silently reuse the first story's cached result
instead of processing its own.

## Problem / Context

Under the per-story bucket-directory layout
(`<collection>/<story>/story.json`, adopted via
`PROP-LCATS-STORY-BUCKET-LAYOUT`), every story's leaf filename is the same
reserved `story.json`, so `pathlib.Path.stem` is `"story"` for every file
-- not a usable per-story identifier.
`experiments/03_cross_segment_relation_pilot/check_segmentation_reliability.py:193`
still keys its per-story result cache off `path.stem`:
`result_path = output_dir / f"{path.stem}.json"`. After the first story
writes `output_dir/story.json`, every subsequent story hits the
cache-check (`if result_path.exists(): cached = ...`) and silently reuses
story #1's cached result as its own -- including a `story_id` field also
collapsed to `"story"`. The script completes normally and prints what
looks like real per-story progress; there is no exception, no non-zero
exit code, and no warning. This was flagged in the governing proposal's
own Non-Goals as a stem-collision output-naming bug, deliberately
deferred as a separate follow-on, and confirmed re-present and re-traced
in detail during a 2026-08-02 backlog audit (see
`project/design/backlog.md`).

### Duplication search
- In-repo: No existing implementation found. Two adopted design proposals
  (`lcats-pipeline-checkpointing/00_proposal.md`,
  `lcats-story-bucket-layout/00_proposal.md`) reference this script in
  passing but neither implements a fix.
- Sibling repos: None identified.
- External libraries: None identified -- internal script-specific bug fix.
- Recommendation: Proceed.

### Demand search
- Work items: Found: `WI-PIPELINE-0041` -- explicitly excludes this exact
  fix ("Does not change `check_segmentation_reliability.py`'s existing,
  narrower persistence approach"). Confirms this is a deliberately
  deferred gap, not overlapping scope.
- Proposals: None found.
- Backlog: Found: "`check_segmentation_reliability.py`'s stem-collision
  bug -- P0, silent data corruption" in `project/design/backlog.md`. This
  work item is created specifically to resolve that entry.
- Recommendation: Offer to remove/mark-resolved the matching
  `backlog.md` entry once this work item's creation PR is confirmed (not
  auto-closed).

## Scope

- Fix the per-story result/cache file naming in
  `check_segmentation_reliability.py` so distinct stories never collide
  onto the same output file.
- Add a regression test proving the fix.
- Do not touch this script's file *discovery* (the existing
  `rglob("*.json")` at line 149 is correct and untouched).

## Required Changes

1. In `check_segmentation_reliability.py`, replace the
   `path.stem`-derived result path (`output_dir / f"{path.stem}.json"`)
   with one derived from the story's bucket directory slug
   (`path.parent.name`), matching the identity convention established by
   `PROP-LCATS-STORY-BUCKET-LAYOUT` Decision 2 (directory slug, not leaf
   filename, is the stable per-story identifier).
2. Update the cached record's own `story_id` field (currently also
   `path.stem`) to the same directory-slug value, so cached records are
   self-consistent with the new file naming.
3. Create
   `experiments/03_cross_segment_relation_pilot/check_segmentation_reliability_test.py`
   (matching the existing `run_pilot_test.py` sibling-test convention:
   `sys.path.insert` + module import + `unittest.TestCase`, run via
   `python -m pytest experiments/03_cross_segment_relation_pilot/check_segmentation_reliability_test.py`)
   asserting: two distinct stories under bucket-layout fixtures produce
   two distinct, non-colliding result files with correct per-story
   content; a single-story run's existing behavior is unchanged.

## Non-Goals

- Does not touch this script's file discovery (`rglob("*.json")`) --
  already correct.
- Does not touch `run_pilot.py` or any other script in
  `experiments/03_cross_segment_relation_pilot/` -- separate scope,
  tracked under `WI-PIPELINE-0040`/`0041`.
- Does not change this script's overall persistence/caching *approach*
  (still one result file per identifier, still checked for existence
  before reprocessing) -- only the identifier derivation.
- Does not fix the unrelated non-recursive glob bugs in
  `run_comparison.py`/`smoke_test.py` -- a separate backlog item, to be
  scoped next.
- Does not touch the two flagged notebooks -- a separate backlog item.

## Acceptance Criteria

- The per-story result/cache path in `check_segmentation_reliability.py`
  is derived from `path.parent.name` (the story's bucket directory
  slug), not `path.stem`.
- The cached record's own `story_id` field matches the same
  directory-slug value.
- A new regression test proves two distinct stories no longer collide
  onto the same output/cache file, and that existing single-story
  behavior is unchanged.
- `lrh validate` reports 0 errors.
- `python -m pytest experiments/03_cross_segment_relation_pilot/check_segmentation_reliability_test.py`
  passes.

## Validation

- `scripts/version tools`
- `lrh validate`
- `python -m pytest experiments/03_cross_segment_relation_pilot/check_segmentation_reliability_test.py`
- `python -m pytest tests/`

## Risk Notes

- Changing the cache-key format means any *existing* cached result files
  (if a prior real run exists anywhere, though none was found in-repo)
  would no longer be recognized as cache hits under the new key -- this
  is intentional and correct (the old cache was silently wrong), but
  worth calling out explicitly so a real run isn't surprised by a
  "cache miss" on files it expects to find.
- `path.parent.name` assumes the canonical bucket layout
  (`<collection>/<story>/story.json`); if this script is ever pointed at
  a non-bucket input, the identifier would be wrong in a different way --
  out of scope here since dual-layout support is already fully retracted
  repo-wide.
