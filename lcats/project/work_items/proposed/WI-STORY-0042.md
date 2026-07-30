---
resolution: null
blocked_reason: null
blocked: false
id: WI-STORY-0042
title: Make LCATS story discovery and identity dual-layout-compatible
type: deliverable
status: proposed
priority: high
owner: unassigned
contributors: []
assigned_agents: []
related_focus:
  - FOCUS-WORLDCON-2026
related_roadmap: []
related_workstreams:
  - WS-STORY-BUCKET-LAYOUT
related_design:
  - lcats/project/design/proposals/proposed/lcats-story-bucket-layout/00_proposal.md
  - lcats/project/design/flat_story_layout_migration_impact_report.md
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
  - modify_datagatherer_writer
  - implement_stage_2
acceptance:
  - A canonical story-file selector utility exists, recognizing both a flat <story>.json file and a nested <story>/story.json file as valid story sources
  - Corpora.get_corpora (lcats/src/lcats/stories.py:51-52) uses the selector instead of raw os.listdir + endswith(".json")
  - find_json_files/find_corpus_stories (lcats/src/lcats/analysis/corpus/discovery.py:65) applies a canonical-filename predicate (story.json only) while remaining dual-layout tolerant, per Decision 3
  - infer_story_title (lcats/src/lcats/analysis/corpus/cli.py:53) derives identity from directory slug when present, not raw file_path.stem, per Decision 2
  - New dual-layout tests cover both flat-file and nested-bucket fixtures for all of the above
  - No changes to DataGatherer's writer output or any other writer behavior
  - lrh validate reports 0 errors
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
artifacts_expected:
  - lcats/src/lcats/analysis/corpus/discovery.py
  - lcats/src/lcats/stories.py
  - lcats/src/lcats/analysis/corpus/cli.py
  - lcats/tests/stories_test.py
  - lcats/tests/analysis_tests/corpus_surveyor_test.py
---

## Summary

Make LCATS's story discovery and identity logic dual-layout-compatible —
tolerating both the current flat `data/<collection>/<story>.json` layout
and the future `data/<collection>/<story>/story.json` bucket layout —
without changing any writer output. Stage 1 of 3 in
`WS-STORY-BUCKET-LAYOUT`'s staged expand-contract migration.

## Problem / Context

`flat_story_layout_migration_impact_report.md`'s audit and
`PROP-LCATS-STORY-BUCKET-LAYOUT` found discovery/identity logic hard-coded
to the flat layout in multiple places, producing collapsed or broken
identifiers once a bucket layout exists. This item implements Decision 2
(canonical identity = directory slug, not `file_path.stem`, which collapses
to the literal string `"story"` once files move to `<story>/story.json`)
and Decision 3 (discovery predicate = canonical filename `story.json` only,
not broad `*.json` schema-sniffing).

### Duplication search
- In-repo: No existing implementation. `WI-OVERRIDES-0018` mentions the
  bucket layout only as a forward-compatibility note and explicitly
  excludes implementing the migration itself.
- Sibling repos: None identified.
- External libraries: None applicable.
- Recommendation: Proceed.

### Demand search
- Work items: None found requesting this specifically —
  `PROP-LCATS-STORY-BUCKET-LAYOUT` and `WS-STORY-BUCKET-LAYOUT` are the
  request.
- Proposals: `PROP-LCATS-STORY-BUCKET-LAYOUT`'s own Implementation Plan
  names Stage 1 as this item's scope.
- Backlog: No matching entries.
- Recommendation: Proceed.

## Scope

- Add a single canonical story-file selector utility, recognizing both
  flat and nested-bucket story sources.
- Update `Corpora.get_corpora`, `find_json_files`/`find_corpus_stories`,
  and `infer_story_title` to use it.
- Add dual-layout tests for all of the above.
- Do not touch any writer (`DataGatherer`, `parser.gather_story()`) —
  that's Stage 2.

## Required Changes

1. Create the canonical story-file selector utility (location TBD during
   implementation — likely alongside
   `lcats/src/lcats/analysis/corpus/discovery.py`).
2. Update `lcats/src/lcats/stories.py:51-52` (`Corpora.get_corpora`) to use
   the selector instead of raw `os.listdir` + `endswith(".json")`.
3. Update `lcats/src/lcats/analysis/corpus/discovery.py:65`
   (`find_json_files`) to apply the canonical-filename predicate while
   remaining dual-layout tolerant.
4. Update `lcats/src/lcats/analysis/corpus/cli.py:53`
   (`infer_story_title`) to derive identity from directory slug when
   present, not raw `file_path.stem`.
5. Add dual-layout tests (flat + nested-bucket fixtures) to
   `lcats/tests/stories_test.py` and
   `lcats/tests/analysis_tests/corpus_surveyor_test.py`.

## Non-Goals

- Does not change `DataGatherer.ensure` or `parser.gather_story()` writer
  behavior — Stage 2 (next work item).
- Does not fix the gather-overrides `story_id` derivation bug — Stage 2,
  Decision 7.
- Does not add the `story_dir`/`story_slug` output column — Stage 2,
  Decision 5.
- Does not add standing zero-story-count rejection to `lcats promote` —
  Stage 2, Decision 6.
- Does not touch tests/fixtures/docs convergence or dual-layout
  retraction — Stage 3.
- Does not touch `lcats gather` incrementality, `notebooks/`, or
  `experiments/` — deferred in the governing proposal's own Non-Goals.

## Acceptance Criteria

(see frontmatter `acceptance:` above)

## Validation

- `scripts/version tools`
- `lrh validate`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`

## Risk Notes

- The canonical-filename predicate (Decision 3) must not accidentally
  exclude legitimate flat-layout stories during the dual-layout window —
  worth an explicit fixture mixing both layouts in one collection.
- `infer_story_title`'s directory-slug derivation needs a defined fallback
  for genuinely flat files (no enclosing story directory) — must not
  regress current flat-layout title behavior.

## Dependencies / Order

No dependencies — this item should land first; Stage 2 depends on it (the
writer migration assumes dual-layout-tolerant discovery already exists).

## Related Workstream and Designs

- Workstream: `project/workstreams/proposed/WS-STORY-BUCKET-LAYOUT.md`
- Design: `project/design/proposals/proposed/lcats-story-bucket-layout/00_proposal.md`
