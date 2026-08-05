---
execution_id: 2026_08_05_19_10_51_WORLDCON_FAST_PATH_ANNOTATION
prompt_id: PROMPT(AD_HOC:WORLDCON_FAST_PATH_ANNOTATION)[2026-08-05T19:08:01+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/LCATS/pull/226
commit: edb8ace9
created_at: 2026-08-05T19:10:51+00:00
agent: claude_app
instruction_source: lcats/project/design/proposals/proposed/worldcon-fast-path-annotation/00_proposal.md
session_transcript: pending
---

# Summary

Drafted `PROP-WORLDCON-FAST-PATH-ANNOTATION`, a design proposal for a new
`lcats annotate` command that runs the mature `lcats assess` (genre) and
`scene_analysis` (scene/sequel segmentation) extractors over a small
per-genre story subset, writing `genre.json`/`scenes.json` sidecars plus
a per-bucket `README.md`, with `lcats promote` validating and copying
them to `corpora/`. Deliberately routes around the ERW event/relation
extractor per a parallel session's cost/reliability finding.

# Result

- Verified the brief's technical claims directly against the codebase
  before drafting: confirmed `assess.py:328`'s hardcoded
  `max_tokens=2048`, `scene_analysis.py`'s missing `max_tokens` override,
  `promote.py`'s `_copy_collection` wholesale-copy behavior, and the
  `survey_collection`/`corpus_survey.py` exclusion-policy split.
- Corrected one stale claim: `check_segmentation_reliability.py`'s
  stem-collision bug (originally flagged as an open risk) was already
  fixed and merged same-day via PR #220 (`WI-EXPERIMENTS-0046`) — cited
  as landed precedent instead.
- Surfaced a previously-unscoped, directly relevant bug via the demand
  search: `lcats stats` uses the broad `find_corpus_stories` selector
  instead of `find_json_files`, which this proposal's own new sidecars
  would silently miscount as stories. Folded a fix into the proposal's
  implementation plan (Decision 7) rather than leaving it as a landmine.
- Ran the two-decision confirm gate with the user (audit sidecar scope,
  promote validation approach) via `AskUserQuestion` before drafting the
  full proposal body, per the skill's confirm-before-write step.
- Incorporated user feedback noting `PROP-LCATS-PILOT-COST-SUSTAINABILITY`
  is under active review and may land soon, and that
  `PROP-ERW-LOCAL-MODEL-EVALUATION` is a parallel local-model fallback
  effort — both recorded as related-but-independent context, not
  dependencies.
- Wrote `project/design/proposals/proposed/worldcon-fast-path-annotation/00_proposal.md`,
  branched off `origin/main` (this worktree's local branch had fallen
  behind by two merged PRs, #222/#223), committed, pushed, and opened
  PR #226.

# Validation

- `lrh validate` — 0 errors/warnings on the new proposal file (repo-wide
  pre-existing warnings unrelated to this change were left as-is).
- `lrh prompt check-execution --slug worldcon-fast-path-annotation
  --work-item AD_HOC --project-root .` — confirmed no prior record before
  minting.

# Follow-up

- Run `/lrh-review-response` on PR #226 as review comments arrive, then
  `/lrh-confirm-fixes` before merge, then `/lrh-closeout` after merge to
  land this execution record.
- Once adopted, scope work items per the Implementation Plan section
  (two bug fixes, `lcats annotate`, `lcats promote` sidecar validation,
  `lcats stats` selector fix, the actual per-genre run) — likely a
  companion `/lrh-workstream`, mirroring
  `PROP-LCATS-PIPELINE-CHECKPOINTING` → `WS-PIPELINE-CHECKPOINTING`.
- Step 7 (8-genre expansion) remains gated on `WI-ASSESS-0031` landing in
  its parallel session.
