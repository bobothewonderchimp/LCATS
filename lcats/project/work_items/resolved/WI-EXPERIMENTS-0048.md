---
resolution: "Implemented and merged via https://github.com/xenotaur/LCATS/pull/225 (squash commit 37c277c3d0057e6237da45112a1481ce0ab37926)."
blocked_reason: null
blocked: false
id: WI-EXPERIMENTS-0048
title: Fix hardcoded flat-layout paths in the two extract-scenes/clean-corpus notebooks
type: deliverable
status: resolved
priority: low
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
  - create_pr
forbidden_actions:
  - force_push
  - delete_branch
  - modify_rename_and_fix_json_files_behavior
  - regenerate_notebook_outputs_wholesale
acceptance:
  - "12_extract_scenes.ipynb's SAMPLE_OF_10/SAMPLE_OF_100 are generated via a seeded random.sample() call over the canonical bucket-only selector (discovery.find_json_files), not the broad json_stories (which can include sidecar JSON) and not hardcoded literal flat-layout paths"
  - "13_clean_corpus.ipynb's missing_stories points at the real, current bucket-layout paths for the same two stories"
  - "Neither notebook's remaining literal path examples reference the retracted flat <collection>/<story>.json layout"
  - "lrh validate reports 0 errors"
required_evidence:
  - manual_review
  - lrh_validate
artifacts_expected:
  - lcats/notebooks/12_extract_scenes.ipynb
  - lcats/notebooks/13_clean_corpus.ipynb
---

# Work Item: Fix hardcoded flat-layout paths in the two extract-scenes/clean-corpus notebooks

## Summary

Fix hardcoded flat-layout literal paths in `12_extract_scenes.ipynb` and
`13_clean_corpus.ipynb`, both stale since the bucket-layout migration.

## Problem / Context

Re-verified 2026-08-02 directly against current notebook content (not
just backlog notes): `12_extract_scenes.ipynb`'s `SAMPLE_OF_10`/
`SAMPLE_OF_100` (cells 48-49) are hardcoded absolute flat-layout paths
(e.g. `/Users/centaur/.../corpora/massQuantities/the_crystal_ray.json`)
-- both stale in path *shape* and in the `massQuantities` casing (real
collection name is `mass_quantities`). These feed
`corpus_surveyor.process_files`, which catches per-file errors
gracefully (`except Exception` in `processing.py`'s `process_file`)
rather than crashing, so a run would report every sampled story as
`status: "error"` without halting.

**Scoping finding, verified before drafting:** manually rewriting all
~110 of these paths would be error-prone -- checking two of
`13_clean_corpus.ipynb`'s equivalent stale paths against the real corpus
found that `mass_quantities` bucket directory names now carry an
author-disambiguation suffix not present in the old flat filename
(`give_back_a_world` -> `give_back_a_world__gallun`;
`george_walker_at_suez` -> `george_walker_at_suez__trollope`), confirmed
via direct directory listing. `12_extract_scenes.ipynb` already contains
the right fix, just commented out: cell 25's
`json_stories = corpus_surveyor.find_corpus_stories(CORPORA_ROOT)`
already works correctly against the real bucket layout (confirmed: it's
a direct re-export of `discovery.find_corpus_stories`, layout-agnostic),
and cell 47 has commented-out code (`random.sample(json_stories, 100)`)
showing the original intent was a regenerable sample, not permanently
frozen literals.

**One additional gap found via review of this work item's own creation
PR, before any implementation was written:** `json_stories` (cell 25) is
`corpus_surveyor.find_corpus_stories(CORPORA_ROOT)`, a direct re-export
of `discovery.find_corpus_stories` -- the *broad* recursive finder that
includes every `.json` file, not just canonical `story.json` (confirmed
against `discovery.py:13-51`). It happens to work correctly *today* only
because the real `corpora/` tree currently has zero sidecar files
(confirmed earlier this session). The original scope (drawing
`SAMPLE_OF_10`/`SAMPLE_OF_100` from `json_stories` via `random.sample`)
would have made these samples depend on that broad selector for the
first time -- previously the hardcoded literals were always manually
curated, genuine story files, never sidecars. If a bucket sidecar
(`analysis.json` etc.) is ever added, this code would start silently
sampling it as if it were an independent story. Fixed by drawing the
sample from `discovery.find_json_files([CORPORA_ROOT])` instead (the
canonical, sidecar-excluding selector already established across this
codebase), as a separate variable -- not by changing `json_stories`
itself, which cell 27's `compute_corpus_stats(json_stories)` also
depends on and is out of this work item's scope to touch.

`13_clean_corpus.ipynb`'s `missing_stories` (cell 45, only 2 specific
paths, not a bulk sample) is updated directly to the confirmed real
bucket paths, preserving the same two specific stories.

Also examined `13_clean_corpus.ipynb`'s `rename_and_fix_json_files`
(cell 29, `ext: str = ".json"` default) -- its purpose (repairing messy
flat filenames via basename validation) is now largely moot since every
canonical filename is uniformly `story.json` (which trivially passes its
basename-validity check), but it isn't actively broken or crashing. Left
untouched -- a Non-Goal, not a bug.

### Duplication search
- In-repo: No existing implementation found. One docstring
  cross-reference in `lcats/src/lcats/analysis/scene_analysis.py:304`
  (mentions `12_extract_scenes.ipynb` for context, no fix).
- Sibling repos: None identified.
- External libraries: None identified -- internal notebook fix.
- Recommendation: Proceed.

### Demand search
- Work items: None found.
- Proposals: None found.
- Backlog: Found: "Hardcoded flat-layout paths in two notebooks" in
  `lcats/project/design/backlog.md`. This work item is created
  specifically to resolve that entry.
- Recommendation: Offer to remove/mark-resolved the matching
  `backlog.md` entry once this work item's creation PR is confirmed (not
  auto-closed).

## Scope

- Replace `12_extract_scenes.ipynb`'s hardcoded `SAMPLE_OF_10`/
  `SAMPLE_OF_100` with a live, seeded sample drawn from the canonical,
  sidecar-excluding selector (`discovery.find_json_files`).
- Update `13_clean_corpus.ipynb`'s `missing_stories` to the confirmed
  real bucket paths for the same two stories.
- Do not touch `rename_and_fix_json_files`'s behavior or defaults, or
  `json_stories`'s existing broad-selector definition (cell 25, also
  used by `compute_corpus_stats` -- out of scope to change here).
- Do not regenerate or re-run either notebook's existing saved cell
  outputs wholesale -- edit source cells only.

## Required Changes

1. In `12_extract_scenes.ipynb`, add
   `from lcats.analysis.corpus import discovery` to the existing
   `lcats.analysis` import cell (cell 8).
2. In the same notebook, add a new cell (near cell 25, alongside
   `json_stories`) computing
   `canonical_story_files = list(discovery.find_json_files([CORPORA_ROOT]))`
   -- a separate variable, not a replacement for `json_stories`.
3. Replace the `SAMPLE_OF_10 = pathify([...])` and
   `SAMPLE_OF_100 = pathify([...])` cells with
   `SAMPLE_OF_10 = random.Random(42).sample(canonical_story_files, 10)`
   / `SAMPLE_OF_100 = random.Random(42).sample(canonical_story_files, 100)`
   (a fixed seed preserves the original lists' reproducibility intent).
4. In `13_clean_corpus.ipynb`, update `missing_stories` (cell 45) to
   `[CORPORA_ROOT / 'mass_quantities/george_walker_at_suez__trollope/story.json', CORPORA_ROOT / 'mass_quantities/give_back_a_world__gallun/story.json']`.

## Non-Goals

- Does not change `rename_and_fix_json_files`'s `ext` default or
  scanning behavior.
- Does not touch `experiments/` scripts -- separate, already-scoped work
  items (`WI-EXPERIMENTS-0046`/`0047`).
- Does not re-execute either notebook or regenerate saved cell outputs.
- Does not address the notebooks/experiments librarization question --
  a separate, decision-only backlog item.

## Acceptance Criteria

- `12_extract_scenes.ipynb`'s `SAMPLE_OF_10`/`SAMPLE_OF_100` are
  generated via a seeded `random.sample()` call over the canonical
  `discovery.find_json_files` selector (a new `canonical_story_files`
  variable, not the broad `json_stories`), not hardcoded literal
  flat-layout paths.
- `13_clean_corpus.ipynb`'s `missing_stories` points at the real,
  current bucket-layout paths for the same two stories.
- Neither notebook's remaining literal path examples reference the
  retracted flat `<collection>/<story>.json` layout.
- `lrh validate` reports 0 errors.

## Validation

- `scripts/version tools`
- `lrh validate`
- Manual: open both notebooks, confirm the edited cells' source no
  longer contains flat-layout literal paths

## Risk Notes

- Switching `SAMPLE_OF_10`/`SAMPLE_OF_100` to a live seeded sample means
  the *specific* sampled stories will differ from the original frozen
  list (different corpus content, same collection universe) -- acceptable
  since the notebook's own commented-out code shows this was always
  meant to be a representative sample, not specific curated stories.
- Per `AGENTS.md`, this is a deliberate, judgment-carrying notebook edit,
  not a routine one -- scoped narrowly to the confirmed-stale path
  literals only.
