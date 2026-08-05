---
resolution: "Implemented and merged via https://github.com/xenotaur/LCATS/pull/220 (squash commit 5460f440b8e1772b74ba3c3ddb7a583162e7d2cc)."
blocked_reason: null
blocked: false
id: WI-EXPERIMENTS-0046
title: Fix stem-collision bug in check_segmentation_reliability.py's result caching
type: deliverable
status: resolved
priority: high
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
  - modify_run_pilot_script
acceptance:
  - "check_segmentation_reliability.py's per-story result path/cache key is derived from both the collection name and the story's directory slug, not path.stem alone -- two different collections sharing a story slug must not collide"
  - "File discovery uses the canonical story-file selector (discovery.find_json_files), not a raw rglob('*.json'), so bucket sidecar files (analysis.json etc.) are never sampled as if they were stories"
  - "The cached record's own story_id field matches the same collection-qualified value"
  - "A new regression test proves two distinct stories -- including two different collections sharing the same story slug -- no longer collide onto the same output/cache file, that a bucket sidecar file is never treated as a sampled story, and that single-story behavior is unchanged"
  - "lrh validate reports 0 errors"
required_evidence:
  - manual_review
  - test_output
  - lrh_validate
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
`lcats/project/design/backlog.md`).

**Two additional gaps found via review of this work item's own creation
PR, before any implementation was written, and folded into scope below
rather than left for implementation-time surprise:**

1. The directory slug alone is not sufficient. `--data-dir` defaults to
   `corpora` -- the whole multi-collection corpus root -- and
   `select_files` (line 149) does `pathlib.Path(args.data_dir).rglob("*.json")`
   across every collection at once. The governing proposal's Decision 2
   only guarantees a directory slug is unique *per collection*
   ("already unique per collection today"), not globally, so
   `<collection-a>/foo/story.json` and `<collection-b>/foo/story.json`
   would still collide under a plain `path.parent.name` key. The cache
   key must include the collection name too.
2. `rglob("*.json")` is not the canonical selector this repo's own
   discovery layer settled on. Per Decision 3 of the same proposal, a
   bucket directory can hold non-story sidecar JSON (`analysis.json`,
   `scenes.json`, etc.), and `discovery.find_json_files` already exists
   specifically to select only the canonical `story.json` and exclude
   sidecars. `rglob("*.json")` has no such filter, so a sidecar file can
   be sampled as if it were an independent story -- and after the
   collection-qualified key fix above, a sidecar's parent directory is
   the *same* as its real story's, so it would also collide with (and
   potentially overwrite) the real story's cache entry. This work item's
   original Non-Goals incorrectly asserted this discovery logic was
   "already correct" -- it wasn't checked against sidecar-file behavior
   before that claim was made.

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
  bug -- P0, silent data corruption" in `lcats/project/design/backlog.md`. This
  work item is created specifically to resolve that entry.
- Recommendation: Offer to remove/mark-resolved the matching
  `backlog.md` entry once this work item's creation PR is confirmed (not
  auto-closed).

## Scope

- Fix the per-story result/cache file naming in
  `check_segmentation_reliability.py` so distinct stories never collide
  onto the same output file -- including two different collections that
  happen to share a story slug.
- Switch this script's file discovery from a raw `rglob("*.json")` to
  the canonical story-file selector (`discovery.find_json_files`), so
  bucket sidecar files are never sampled as if they were stories.
- Add a regression test proving both fixes.

## Required Changes

1. In `check_segmentation_reliability.py`, replace the
   `path.stem`-derived result path (`output_dir / f"{path.stem}.json"`)
   with one that includes both the collection name and the story's
   bucket directory slug -- e.g. nesting by collection
   (`output_dir / path.parent.parent.name / f"{path.parent.name}.json"`)
   -- so two different collections sharing a story slug cannot collide.
   This matches `PROP-LCATS-STORY-BUCKET-LAYOUT` Decision 2 (directory
   slug is the per-*collection* identity), extended with the
   collection-qualification this script's own multi-collection
   `--data-dir` scan requires.
2. Update the cached record's own `story_id` field (currently
   `path.stem`) to reflect the same collection-qualified identity.
3. Replace `select_files`'s `pathlib.Path(args.data_dir).rglob("*.json")`
   (line 149) with `discovery.find_json_files([args.data_dir])` (see
   `lcats/src/lcats/datasets/torchdata.py` for the same call shape
   against a single directory), so sidecar JSON files inside a bucket
   directory are never selected as candidate stories. Import
   `lcats.analysis.corpus.discovery`.
4. Create
   `experiments/03_cross_segment_relation_pilot/check_segmentation_reliability_test.py`
   (matching the existing `run_pilot_test.py` sibling-test convention:
   `sys.path.insert` + module import + `unittest.TestCase`, run via
   `python -m pytest experiments/03_cross_segment_relation_pilot/check_segmentation_reliability_test.py`)
   asserting: two distinct stories in two different collections sharing
   the same story slug produce two distinct, non-colliding result files;
   a bucket sidecar file (e.g. `analysis.json`) is never selected as a
   sampled story; a single-story run's existing behavior is unchanged.

## Non-Goals

- Does not touch `run_pilot.py` or any other script in
  `experiments/03_cross_segment_relation_pilot/` -- separate scope,
  tracked under `WI-PIPELINE-0040`/`0041`.
- Does not change this script's overall persistence/caching *approach*
  (still one result file per identifier, still checked for existence
  before reprocessing) -- only the identifier derivation and the file
  selector it's built on.
- Does not add a `--story-list`-path identity fix beyond what the
  collection-qualified key already provides -- an explicit story list
  passed via `--story-list` is assumed to already resolve to real bucket
  paths under some collection root.
- Does not fix the unrelated non-recursive glob bugs in
  `run_comparison.py`/`smoke_test.py` -- a separate backlog item, to be
  scoped next.
- Does not touch the two flagged notebooks -- a separate backlog item.

## Acceptance Criteria

- The per-story result/cache path in `check_segmentation_reliability.py`
  is derived from both the collection name and the story's bucket
  directory slug, not `path.stem` and not the directory slug alone.
- File discovery uses `discovery.find_json_files`, not a raw
  `rglob("*.json")`.
- The cached record's own `story_id` field matches the same
  collection-qualified value.
- A new regression test proves: two stories in different collections
  sharing a story slug produce distinct result files; a bucket sidecar
  file is never sampled as a story; single-story behavior is unchanged.
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
- The collection-qualified key assumes the canonical bucket layout
  (`<collection>/<story>/story.json`, two levels below the scanned
  root); if this script is ever pointed at a non-bucket input, the
  identifier would be wrong in a different way -- out of scope here
  since dual-layout support is already fully retracted repo-wide.
- Switching file discovery from `rglob("*.json")` to
  `discovery.find_json_files` changes which files are eligible for
  `random.Random(args.seed).shuffle(files)`'s sample -- a bucket sidecar
  file that was previously (incorrectly) eligible will no longer appear,
  so a seeded sample computed before this fix is not reproducible after
  it. This is a correctness improvement, not a regression, but worth
  noting since this script's whole design goal is a stable, reproducible
  sample.
