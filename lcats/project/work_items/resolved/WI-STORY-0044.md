---
resolution: "Part A implemented and merged in PR #205 (commit 8b579954). Part B (dual-layout retraction) split out to WI-STORY-0045, tracked separately, blocked on a real production corpora/ migration."
blocked_reason: null
blocked: false
id: WI-STORY-0044
title: Converge tests/fixtures/docs onto bucket layout and validate end-to-end
type: deliverable
status: resolved
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
  - lcats/docs/reference/corpus-promotion.md
  - lcats/docs/reference/gather-overrides.md
depends_on:
  - WI-STORY-0042
  - WI-STORY-0043
blocked_by: []
expected_actions:
  - edit_file
  - run_tests
  - create_pr
forbidden_actions:
  - force_push
  - delete_branch
  - run_real_gather_or_promote
  - retract_dual_layout_without_confirmed_corpus_migration
acceptance:
  - corpus_package_test.py, corpus_survey_test.py, corpus_surveyor_test.py, stories_test.py, and cli_test.py are normalized to the bucket layout (fixtures, identifier/path assertions, filename expectations, CLI example strings)
  - corpus-promotion.md and gather-overrides.md are updated if their examples reference flat paths
  - An explicit end-to-end gather-then-promote validation pass runs successfully against a representative (non-production) corpora tree, confirming Stage 2's standing zero-story-count promote validation works end-to-end
  - Dual-layout retraction (Part B) is implemented as a distinct, separately-gated action with an explicit checklist confirmation that the tracked corpora/ snapshot has actually been migrated -- Part A must be able to land and merge independently of Part B
  - lrh validate reports 0 errors
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
artifacts_expected:
  - lcats/tests/analysis_tests/corpus_package_test.py
  - lcats/tests/analysis_tests/corpus_survey_test.py
  - lcats/tests/analysis_tests/corpus_surveyor_test.py
  - lcats/tests/stories_test.py
  - lcats/src/lcats/cli.py
  - lcats/tests/cli_test.py
  - lcats/docs/reference/corpus-promotion.md
  - lcats/docs/reference/gather-overrides.md
---

## Summary

Converge LCATS's tests, fixtures, and docs onto the per-story bucket
layout, validate the migration end-to-end against a representative
corpus, and retract dual-layout support as a separately-gated follow-up
once the tracked corpus content is confirmed migrated. Final stage (3 of
3) in `WS-STORY-BUCKET-LAYOUT`.

## Problem / Context

This implements Decision 4 (dual-layout window duration) and Decision 6's
validation requirement, as refined by PR #197's review: Stage 3 ships in
**two parts, not one merge**. Part A — convergence work (fixtures, tests,
docs, confirming Stage 2's standing promote validation) — lands with
dual-layout read support still active. Part B — a distinct follow-up —
retracts dual-layout support, but only after the tracked `corpora/`
snapshot (currently 1,868 flat files, 0 nested `story.json`, confirmed via
`git ls-files corpora/`) is actually migrated via a separate `lcats
gather` + `lcats promote` run. Retracting flat-layout reads before that
real migration would make `survey`/`stats`/`assess` stop discovering the
release snapshot entirely.

### Duplication search
- In-repo: No existing implementation.
- Sibling repos: None identified.
- External libraries: None applicable.
- Recommendation: Proceed.

### Demand search
- Work items: None found — `PROP-LCATS-STORY-BUCKET-LAYOUT` and
  `WS-STORY-BUCKET-LAYOUT` are the request.
- Proposals: `PROP-LCATS-STORY-BUCKET-LAYOUT`'s Implementation Plan names
  Stage 3 as this item's scope.
- Backlog: No matching entries.
- Recommendation: Proceed.

## Scope

- Normalize the 5 listed test files to the bucket layout.
- Update reference docs if they reference flat paths.
- Run an explicit end-to-end gather-then-promote validation pass
  (representative corpora, not production).
- Implement dual-layout retraction as a distinct, separately-gated
  action — not automatic, not blocking Part A.
- Does not touch Stage 1 or Stage 2 decisions.

## Required Changes

**Part A — Convergence:**
1. Update `lcats/tests/analysis_tests/corpus_package_test.py` —
   fixtures/assertions writing/reading `story.json` directly, exact
   filename/path assertions.
2. Update `lcats/tests/analysis_tests/corpus_survey_test.py` —
   `story_file == "story.json"` assertions, path fields, rendered output
   basenames.
3. Update `lcats/tests/analysis_tests/corpus_surveyor_test.py` —
   remaining explicit filename/path expectations.
4. Update `lcats/tests/stories_test.py` and gatherer tests — direct
   `*.json` file paths, output-path assertions.
5. Update `lcats/src/lcats/cli.py` help examples and `lcats/tests/cli_test.py`
   — `lcats survey data/ ...`-style example strings.
6. Update `lcats/docs/reference/corpus-promotion.md` and
   `lcats/docs/reference/gather-overrides.md` if their examples reference
   flat paths.
7. Run and document an explicit end-to-end gather-then-promote validation
   pass against a representative (non-production) corpora tree.

**Part B — Dual-layout retraction (gated, separate):**
8. Retract Stage 1's dual-layout read support, executed only after an
   explicit checklist confirmation that the tracked `corpora/` snapshot
   has been migrated via a real `lcats gather` + `lcats promote` run. If
   that hasn't happened when Part A is otherwise ready, Part A lands on
   its own; Part B is deferred, not blocking.

## Non-Goals

- Does not perform the actual production `lcats gather` + `lcats promote`
  run migrating real corpus content — a separate, release-time human
  action Part B depends on but does not include.
- Does not touch `lcats gather` incrementality/checkpointing,
  `notebooks/`, or `experiments/` — deferred in the governing proposal's
  own Non-Goals.
- Does not revisit Stage 1 or Stage 2 decisions — only convergence and
  retraction.

## Acceptance Criteria

(see frontmatter `acceptance:` above)

## Validation

- `scripts/version tools`
- `lrh validate`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- Explicit end-to-end gather-then-promote validation pass against
  representative (not production) corpora

## Risk Notes

- Part A and Part B being merged into one PR would recreate exactly the
  sequencing bug PR #197's review caught — the two parts must be
  separable, with Part B's gate genuinely blocking, not just documented.
- The end-to-end validation pass must use a representative corpora tree,
  not the real 1,868-file production snapshot — running it for real is
  Part B's own precondition, not something this item performs.

## Dependencies / Order

Depends on `WI-STORY-0042` (merged, PR #198) and `WI-STORY-0043` (PR #200,
not yet merged) — convergence tests need to target the final read/write
behavior both stages establish. Should not start implementation before
Stage 2 lands.

## Related Workstream and Designs

- Workstream: `project/workstreams/proposed/WS-STORY-BUCKET-LAYOUT.md`
- Design: `project/design/proposals/proposed/lcats-story-bucket-layout/00_proposal.md`
