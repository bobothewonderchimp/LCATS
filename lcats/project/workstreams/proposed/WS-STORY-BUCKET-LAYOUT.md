---
id: WS-STORY-BUCKET-LAYOUT
kind: planning_node
title: Per-Story Bucket Directory Layout Migration for LCATS Corpus Storage
status: proposed
stage: designed
origin: design_review
summary: "Deliver PROP-LCATS-STORY-BUCKET-LAYOUT's staged expand-contract migration from flat per-collection story files to per-story bucket directories, across three stages: read-path compatibility, write-path migration, and convergence-and-validation."
related_focus:
  - FOCUS-WORLDCON-2026
related_roadmap: []
related_design:
  - lcats/project/design/proposals/proposed/lcats-story-bucket-layout/00_proposal.md
  - lcats/project/design/flat_story_layout_migration_impact_report.md
  - lcats/project/design/proposals/adopted/lcats-pipeline-checkpointing/00_proposal.md
work_items:
  - WI-STORY-0042
  - WI-STORY-0043
  - WI-STORY-0044
exit_criteria:
  - "Stage 1 (read-path compatibility) lands: discovery/identity logic is dual-layout-tolerant (Decisions 2-3), with a canonical story-file selector and dual-layout tests, writer output unchanged"
  - "Stage 2 (write-path migration) lands: DataGatherer.ensure and parser.gather_story() both write <collection>/<story>/story.json (Decision 8); overrides story_id derivation fixed (Decision 7); output identifier semantics updated with new story_dir/story_slug column (Decision 5); lcats promote itself rejects zero-story-count collections (Decision 6)"
  - "Stage 3 convergence work lands: tests/fixtures/docs normalized to the new layout, with an explicit end-to-end gather-then-promote validation pass confirmed"
  - Dual-layout retraction (Decision 4) lands as its own follow-up, only after the tracked corpora/ snapshot is confirmed migrated via a separate gather-then-promote action
  - All work items resolved and lrh validate reports 0 errors
---

# Workstream: Per-Story Bucket Directory Layout Migration for LCATS Corpus Storage

## Purpose

This workstream delivers `PROP-LCATS-STORY-BUCKET-LAYOUT`
(`lcats/project/design/proposals/proposed/lcats-story-bucket-layout/00_proposal.md`),
a staged expand-contract migration from LCATS's flat per-collection story
storage (`data/<collection>/<story>.json`) to per-story bucket directories
(`data/<collection>/<story>/story.json`). It coordinates the three
implementation stages the proposal defines, and tracks the
review-discovered fixes (the mass-quantities writer site, the
gather-overrides identity site, and standing promotion validation) through
to closeout.

## Scope

- Stage 1 — Read-path compatibility: dual-layout-tolerant discovery/identity
  logic, a canonical story-file selector, dual-layout tests
  (Decisions 2-3).
- Stage 2 — Write-path migration: `DataGatherer.ensure` and
  `parser.gather_story()` (Decision 8) both migrate to the bucket layout;
  overrides `story_id` fix (Decision 7); output identifier semantics
  (Decision 5); standing zero-story-count rejection in `lcats promote`
  (Decision 6).
- Stage 3 — Convergence and validation: tests/fixtures/docs normalized to
  the new layout; explicit end-to-end gather-then-promote validation pass;
  dual-layout retraction as a distinct, separately-gated follow-up
  (Decision 4).
- Land each work item through the standard LRH execution lifecycle
  (`/lrh-implement` → `/lrh-review-response` → `/lrh-confirm-fixes` →
  `/lrh-closeout`).

## Prior Art Check

### Duplication search
- In-repo: No existing implementation. `PROP-LCATS-STORY-BUCKET-LAYOUT`
  itself already ran this search in full — no code implements the
  migration; `flat_story_layout_migration_impact_report.md` is the audit
  that motivated it.
- Sibling repos: None identified.
- External libraries: None applicable — internal storage-layout
  convention. Approach follows Martin Fowler's Parallel Change
  (expand-contract) pattern, per the proposal.
- Recommendation: Proceed.

### Demand search
- Work items: None found in `project/work_items/proposed/` referencing
  this migration.
- Proposals: `PROP-LCATS-STORY-BUCKET-LAYOUT` requests this workstream
  directly — its own Implementation Plan recommends a workstream given its
  3-stage, multi-PR scope.
- Backlog: No `project/design/backlog.md` exists in this repo.
- Recommendation: Proceed.

## Work Items

- **WI-STORY-0042** — Make story discovery/identity dual-layout-compatible:
  canonical story-file selector, dual-layout tests, no writer changes yet
  (Decisions 2-3).
- **WI-STORY-0043** — Migrate write paths to the bucket layout:
  `DataGatherer.ensure` and `parser.gather_story()` (Decision 8, the
  mass-quantities collection's writer, found during proposal review); fix
  the overrides `story_id` derivation (Decision 7); update output
  identifier semantics (Decision 5); add standing zero-story-count
  rejection to `lcats promote` (Decision 6).
- **WI-STORY-0044** — Convergence: normalize tests/fixtures/docs to the
  new layout, run an explicit end-to-end gather-then-promote validation
  pass, and land dual-layout retraction (Decision 4) as its own follow-up
  once the tracked `corpora/` snapshot is confirmed migrated.

## Exit Criteria

(see frontmatter `exit_criteria:` above)

## Non-Goals

- Does not implement `lcats gather` incremental/restartable checkpointing —
  `PROP-LCATS-PIPELINE-CHECKPOINTING`'s own deferred, separately-scoped
  future work.
- Does not fix hardcoded flat-layout paths in
  `lcats/notebooks/12_extract_scenes.ipynb` and `13_clean_corpus.ipynb` —
  a needed, lower-urgency follow-on, scoped separately.
- Does not fix the non-recursive glob bugs in
  `experiments/02_llm_backend_comparison/run_comparison.py` and
  `smoke_test.py`, or the stem-collision output-naming bug in
  `experiments/03_cross_segment_relation_pilot/check_segmentation_reliability.py` —
  real bugs, more pressing than the notebooks (silent failure mode), but
  still a separate follow-on so they're fixed once against the final
  layout.
- Does not decide whether `notebooks/` and `experiments/` implementation
  code should be librarized into the installable package with unit test
  coverage — a separate, larger architecture question.
- Does not perform the actual production `lcats gather` + `lcats promote`
  run migrating real corpus content — a release-time human action, not a
  workstream deliverable.

## Open Questions

- Exact `story_dir`/`story_slug` column name and TSV schema version-bump
  policy — deferred to Stage 2 work-item scoping.
- Whether the overrides file format itself should key by directory slug or
  whether Decision 7's call-site fix is sufficient — deferred to Stage 2
  work-item scoping.
- Relative priority and timing between the deferred `experiments/` fix and
  `notebooks/` fix — deferred to future scoping, after this workstream
  lands.
