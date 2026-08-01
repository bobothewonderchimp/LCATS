---
resolution: null
blocked_reason: null
blocked: false
id: WI-STORY-0045
title: Retract dual-layout story discovery support once corpora/ migration is confirmed
type: deliverable
status: proposed
priority: medium
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
depends_on:
  - WI-STORY-0044
blocked_by: []
expected_actions:
  - edit_file
  - run_tests
  - create_pr
forbidden_actions:
  - force_push
  - delete_branch
  - retract_dual_layout_without_confirmed_corpus_migration
  - run_real_gather_or_promote
acceptance:
  - An explicit, dated checklist confirmation is recorded (in this WI's execution record) that the production corpora/ snapshot has been migrated to bucket layout via a real lcats gather + lcats promote run, verified by 0 remaining flat *.json files under corpora/ (git ls-files corpora/ shows only story.json leaves) -- this must happen and be confirmed BEFORE any code in this WI is touched
  - discovery.py's selectors (iter_collection_story_files, find_json_files) no longer accept a flat <story>.json at the collection root -- only <story>/story.json is valid; the reserved-filename warning/skip logic becomes unreachable and is removed
  - infer_story_title's flat-file .stem fallback is removed; only the bucket-directory-slug path remains meaningful
  - Representative flat-layout positive test cases across discovery_test.py, stories_test.py, corpus_cli_test.py, torchdata_test.py are converted to negative tests asserting rejection of flat-layout input, so a later regression cannot silently restore the retracted compatibility; redundant flat-layout fixtures are removed, not just left passing incidentally
  - find_corpus_stories (the broad recursive JSON finder used for corpus-wide stats) is explicitly confirmed out of scope -- it is not part of the flat/bucket duality and is unaffected
  - lrh validate reports 0 errors
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
artifacts_expected:
  - lcats/src/lcats/analysis/corpus/discovery.py
  - lcats/src/lcats/analysis/corpus/cli.py
  - lcats/tests/analysis_tests/discovery_test.py
  - lcats/tests/stories_test.py
  - lcats/tests/analysis_tests/corpus_cli_test.py
  - lcats/tests/datasets_tests/torchdata_test.py
---

## Summary

Retracts Stage 1's dual-layout read tolerance (flat
`<collection>/<story>.json` support) from LCATS's story discovery code,
once -- and only once -- the real production `corpora/` snapshot has been
confirmed migrated to the bucket layout via an actual `lcats gather` +
`lcats promote` run. Final piece of `PROP-LCATS-STORY-BUCKET-LAYOUT`'s
expand-contract migration (Decision 4). Part B, gated, of what was
originally scoped as WI-STORY-0044's Stage 3.

## Problem / Context

Decision 4 of the governing proposal chose a staged expand-contract
pattern (Fowler's Parallel Change) specifically to avoid a hard cutover.
Stages 1-3 (`WI-STORY-0042`, `WI-STORY-0043`, `WI-STORY-0044`) landed the
"expand" phase -- dual-layout read support, bucket-layout writes, and
convergence -- while carefully preserving flat-layout reads throughout.
Retracting that tolerance before the real `corpora/` content is migrated
would make `survey`/`stats`/`assess` stop discovering the release
snapshot entirely (per `WI-STORY-0044`'s own Risk Notes). As of the
governing proposal, `corpora/` has 1,868 flat files and 0 nested
`story.json` -- the real migration is a distinct, human, release-time
action no WI in this workstream performs.

### Duplication search
- In-repo: No existing implementation of this retraction.
- Sibling repos: None identified.
- External libraries: None applicable.
- Recommendation: Proceed (once unblocked).

### Demand search
- Work items: None found — this is the explicit final stage named in
  `PROP-LCATS-STORY-BUCKET-LAYOUT`'s own Implementation Plan and in
  `WI-STORY-0044`'s Non-Goals (which explicitly deferred it as "a
  separately-gated action").
- Proposals: `PROP-LCATS-STORY-BUCKET-LAYOUT` Decision 4 requests exactly
  this.
- Backlog: `WS-STORY-BUCKET-LAYOUT`'s own exit criterion 4 names this
  work directly.
- Recommendation: Proceed (once unblocked).

## Scope

- Verify and record the migration-confirmation checklist (the hard gate).
- Remove flat-layout tolerance from `discovery.py`'s selectors.
- Remove the now-dead flat-file fallback in `infer_story_title`.
- Remove flat-layout-specific tests and fixtures.
- Does not perform the actual production migration itself.
- Does not touch `find_corpus_stories` or any writer code (already
  bucket-only since Stage 2).

## Required Changes

1. Before touching any code: confirm via `git ls-files corpora/` (or
   equivalent) that the real production `corpora/` snapshot contains 0
   flat story files -- every story is `<collection>/<story>/story.json`.
   Record this confirmation, with the date and evidence, in this work
   item's execution record.
2. Simplify `discovery.iter_collection_story_files` and
   `discovery.find_json_files` (`lcats/src/lcats/analysis/corpus/discovery.py`)
   to require the bucket layout exclusively -- a flat `<story>.json` at a
   collection root is no longer a valid story source. The reserved-name
   warning/skip logic for a flat file literally named `story.json`
   becomes unreachable dead code once flat files aren't accepted at all,
   and should be removed rather than left in place.
3. Remove `infer_story_title`'s flat-file `.stem` fallback
   (`lcats/src/lcats/analysis/corpus/cli.py`) -- once flat files are no
   longer discoverable, that branch is unreachable.
4. Convert representative flat-layout positive test cases in
   `discovery_test.py`, `stories_test.py`, `corpus_cli_test.py`, and
   `torchdata_test.py` into negative tests asserting the selectors and
   downstream consumers now reject or ignore flat-layout input -- do not
   simply delete all flat-layout coverage, or a later regression could
   silently restore the compatibility this item exists to remove. Remove
   the remaining, now-redundant flat-layout fixtures/cases.
5. Update any remaining docs/comments that describe dual-layout tolerance
   as current behavior.

## Non-Goals

- Does not perform the actual production `lcats gather` + `lcats promote`
  run migrating real corpus content -- a separate, release-time human
  action this item depends on but does not include.
- Does not touch `discovery.find_corpus_stories` -- a separate, broad
  recursive JSON finder used for corpus-wide stats, not part of the
  flat/bucket duality this item retracts.
- Does not touch writer code (`DataGatherer.ensure`, `parser.gather_story()`)
  -- already bucket-only since `WI-STORY-0043`.
- Does not touch `notebooks/` or `experiments/`.

## Acceptance Criteria

(see frontmatter `acceptance:` above)

## Validation

- `scripts/version tools`
- `lrh validate`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`

## Risk Notes

- The single biggest risk is the ordering itself: retracting before the
  real migration is confirmed would silently break discovery of the
  entire release corpus, since `survey`/`stats`/`assess` would no longer
  find any story in a still-flat `corpora/` tree. The acceptance
  criteria's first item (an explicit, dated, verified checklist
  confirmation) exists specifically to make this an unmissable, checkable
  gate rather than a prose-only promise -- per the project convention
  that WS/WI exit criteria need an actual recorded artifact, not just
  deferral language.
- This item may sit blocked for an extended, indefinite period -- the
  real production migration is scheduled at the project's discretion, not
  this workstream's. Do not treat a long blocked duration as a signal to
  proceed early.

## Dependencies / Order

Depends on `WI-STORY-0044` (Stage 3 Part A, convergence) having landed --
it has, via PR #205. Blocked on the real production `corpora/` migration
described above, which has not happened as of this work item's creation.

## Related Workstream and Designs

- Workstream: `project/workstreams/proposed/WS-STORY-BUCKET-LAYOUT.md`
- Design: `project/design/proposals/proposed/lcats-story-bucket-layout/00_proposal.md`
