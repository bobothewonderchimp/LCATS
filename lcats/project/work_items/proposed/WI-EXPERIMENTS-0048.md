---
resolution: null
blocked_reason: null
blocked: false
id: WI-EXPERIMENTS-0048
title: Fix hardcoded flat-layout paths in the two extract-scenes/clean-corpus notebooks
type: deliverable
status: proposed
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
  - "12_extract_scenes.ipynb's SAMPLE_OF_10/SAMPLE_OF_100 are generated via a seeded random.sample(json_stories, N) call, not hardcoded literal flat-layout paths"
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
  `SAMPLE_OF_100` with a live, seeded `random.sample(json_stories, N)`
  call.
- Update `13_clean_corpus.ipynb`'s `missing_stories` to the confirmed
  real bucket paths for the same two stories.
- Do not touch `rename_and_fix_json_files`'s behavior or defaults.
- Do not regenerate or re-run either notebook's existing saved cell
  outputs wholesale -- edit source cells only.

## Required Changes

1. In `12_extract_scenes.ipynb`, replace the
   `SAMPLE_OF_10 = pathify([...])` and `SAMPLE_OF_100 = pathify([...])`
   cells with `SAMPLE_OF_10 = random.Random(42).sample(json_stories, 10)`
   / `SAMPLE_OF_100 = random.Random(42).sample(json_stories, 100)` (a
   fixed seed preserves the original lists' reproducibility intent;
   `json_stories` from cell 25 is already correctly bucket-aware).
2. In `13_clean_corpus.ipynb`, update `missing_stories` (cell 45) to
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
  generated via a seeded `random.sample(json_stories, N)` call, not
  hardcoded literal flat-layout paths.
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
