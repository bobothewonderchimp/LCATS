---
resolution: null
blocked_reason: null
blocked: false
id: WI-STORY-0043
title: Migrate LCATS story write paths to the bucket layout
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
  - lcats/docs/reference/gather-overrides.md
  - lcats/docs/reference/corpus-promotion.md
depends_on:
  - WI-STORY-0042
blocked_by: []
expected_actions:
  - edit_file
  - run_tests
  - create_pr
forbidden_actions:
  - force_push
  - delete_branch
  - implement_stage_3
  - run_real_gather_or_promote
acceptance:
  - DataGatherer.ensure (lcats/src/lcats/gatherers/downloaders.py:216) writes <collection>/<story>/story.json
  - parser.gather_story() (lcats/src/lcats/gatherers/parser.py:1468-1476) writes the same bucket layout for the mass-quantities collection, with its own tests updated
  - The overrides story_id derivation (downloaders.py:249) uses the canonical story name (directory slug), not a re-derivation from the new leaf filename, so per-story overrides no longer collapse onto one key
  - output.py gains a new story_dir/story_slug column with a concrete, documented name; story_file/story_identifier semantics are not silently repurposed
  - promote.py's survey_collection/promote_collections reject a story_count==0 collection as a standing, always-on check (not a one-time step)
  - New/updated tests cover all of the above
  - lrh validate reports 0 errors
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
artifacts_expected:
  - lcats/src/lcats/gatherers/downloaders.py
  - lcats/src/lcats/gatherers/parser.py
  - lcats/src/lcats/analysis/corpus/output.py
  - lcats/src/lcats/analysis/corpus/promote.py
  - lcats/tests
---

## Summary

Migrate LCATS's story write paths to the per-story bucket layout
(`<collection>/<story>/story.json`), fix the gather-overrides
identity-collapse bug, update output identifier semantics, and add
standing zero-story-count rejection to `lcats promote`. Stage 2 of 3 in
`WS-STORY-BUCKET-LAYOUT`.

## Problem / Context

This implements four of `PROP-LCATS-STORY-BUCKET-LAYOUT`'s design
decisions. **Decision 8** (two writer sites, not one): `DataGatherer.ensure`
(`downloaders.py:216`) is the primary writer, but `parser.gather_story()`
(`parser.py:1468-1476`) independently constructs and writes to a flat path
for the mass-quantities/single-stories collection (via
`mass_quantities/gatherer.py:40-54`) — found during proposal PR review
(PR #196) by `chatgpt-codex-connector`. **Decision 7**: the gather-time
overrides mechanism keys per-story fixes by filename stem
(`gather-overrides.md`), derived at `downloaders.py:249` as
`story_id=os.path.splitext(filename)[0]` — must thread the canonical story
name through instead of re-deriving it post-migration. **Decision 5**:
`output.py:105-106`/`180-184` use `file_path.name`/`story_file` for
identity, non-unique post-migration — needs a new column. **Decision 6**:
`promote.py:56-59`'s `CollectionSurveyResult.clean` treats a zero-story
collection as clean, letting `_copy_collection` copy it wholesale — needs a
standing rejection, not a one-time check.

### Duplication search
- In-repo: No existing implementation of any of these four fixes.
- Sibling repos: None identified.
- External libraries: None applicable.
- Recommendation: Proceed.

### Demand search
- Work items: None found — `PROP-LCATS-STORY-BUCKET-LAYOUT` and
  `WS-STORY-BUCKET-LAYOUT` are the request; Decision 8 specifically
  originates from PR #196's review.
- Proposals: `PROP-LCATS-STORY-BUCKET-LAYOUT`'s Implementation Plan names
  Stage 2 as this item's scope.
- Backlog: No matching entries.
- Recommendation: Proceed.

## Scope

- Migrate both writer sites (`DataGatherer.ensure`, `parser.gather_story()`)
  to the bucket layout.
- Fix the overrides `story_id` derivation.
- Add the `story_dir`/`story_slug` output column.
- Add standing zero-story-count rejection to `lcats promote`.
- Update/add tests for all of the above.
- Assumes Stage 1's dual-layout-tolerant discovery (`WI-STORY-0042`)
  already exists.

## Required Changes

1. Migrate `DataGatherer.ensure` (`downloaders.py:216`) to write
   `<collection>/<story>/story.json`.
2. Migrate `parser.gather_story()` (`parser.py:1468-1476`) to the same
   bucket layout; update its own tests (mass-quantities collection).
3. Fix the `story_id` derivation at `downloaders.py:249` to use the
   canonical story name (directory slug), not a re-derivation from the new
   leaf filename.
4. Add a `story_dir`/`story_slug` column to `output.py`'s TSV/human output
   schema; keep `story_file` for the literal leaf filename (now low-value
   but non-breaking).
5. Add zero-story-count rejection to `promote.py`'s
   `survey_collection`/`promote_collections` as a standing, always-on
   check.
6. Add/update tests for all of the above.

## Non-Goals

- Does not touch Stage 1's read-path/discovery work (already done,
  `WI-STORY-0042`).
- Does not touch tests/fixtures/docs convergence or dual-layout
  retraction — Stage 3.
- Does not perform the actual production `lcats gather` + `lcats promote`
  run migrating real corpus content — a separate, release-time human
  action.
- Does not touch `lcats gather` incrementality/checkpointing,
  `notebooks/`, or `experiments/` — deferred in the governing proposal's
  own Non-Goals.
- Does not finalize the `story_dir`/`story_slug` column name or TSV schema
  version-bump policy beyond what's needed to ship Decision 5 — the
  proposal's Open Questions defer full bikeshedding, but this item must
  pick and document a concrete name.
- Does not change the overrides *file format* itself (directory-slug
  keying vs. filename-stem keying) — a call-site fix per Decision 7, not a
  schema change to `lcats/gatherers/overrides/<collection>.json`.

## Acceptance Criteria

(see frontmatter `acceptance:` above)

## Validation

- `scripts/version tools`
- `lrh validate`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`

## Risk Notes

- Two writer sites (not one) means a partial fix — migrating only
  `DataGatherer.ensure` — would leave the mass-quantities collection
  silently producing flat files that Stage 3's canonical-only discovery
  then omits, exactly as PR #196's review found.
- The `story_id` fix must thread the canonical name through, not re-derive
  it — a re-derivation bug here is easy to reintroduce accidentally in a
  refactor, since it's the same shape as the already-fixed Decision 2 bug
  from Stage 1.
- `promote.py`'s standing zero-story check must not itself become the
  layout-drift point — verify it triggers on a collection with genuinely
  zero canonical stories, not one merely mid-migration.

## Dependencies / Order

Depends on `WI-STORY-0042` (Stage 1) — writer migration assumes
dual-layout-tolerant discovery already exists, so this item should not
start implementation before Stage 1 lands.

## Related Workstream and Designs

- Workstream: `project/workstreams/proposed/WS-STORY-BUCKET-LAYOUT.md`
- Design: `project/design/proposals/proposed/lcats-story-bucket-layout/00_proposal.md`
- Reference: `lcats/docs/reference/gather-overrides.md`,
  `lcats/docs/reference/corpus-promotion.md`
