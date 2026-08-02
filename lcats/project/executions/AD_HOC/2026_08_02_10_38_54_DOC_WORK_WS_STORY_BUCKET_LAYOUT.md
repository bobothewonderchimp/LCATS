---
execution_id: 2026_08_02_10_38_54_DOC_WORK_WS_STORY_BUCKET_LAYOUT
prompt_id: PROMPT(AD_HOC:DOC_WORK_WS_STORY_BUCKET_LAYOUT)[2026-08-02T10:24:14-04:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/LCATS/pull/209
commit: 431c785abcb5a2521d74e6c3399f0bff173851e2
created_at: 2026-08-02T10:38:54-04:00
agent: claude_app
instruction_source: WS-STORY-BUCKET-LAYOUT
session_transcript: claude-app:ca0e8b20-2e3a-44f3-90b6-c506f3b98336
---

# Summary

Ran `/lrh-doc-work` against `WS-STORY-BUCKET-LAYOUT` (closed 2026-08-02) as
the work reference -- the user's own framing was "let's document the
bucket migration." Updated user-facing docs to reflect the completed
per-story bucket-directory migration (WI-STORY-0042-0045, plus the PR
#208 masking-bug follow-up).

# Result

- `docs/tutorials/quickstart.md`: fixed 2 stale example paths
  (`corpora/sherlock/boscombe_valley.json` -> `.../boscombe_valley/story.json`)
  -- verified the flat path no longer exists in the real, tracked
  `corpora/` tree, and the bucket path does. Added a stale-content notice
  on both "expected output" blocks rather than fabricating new output.
- `docs/reference/prepare-corpora-release.md`: same fix for 2 illustrative
  flat-path examples (`data/mass_quantities/deny_the_slake__wilson.json`
  -> `.../deny_the_slake__wilson/story.json`).
- New `docs/explanation/story-bucket-layout.md`: an Explanation-quadrant
  doc grounded directly in the adopted proposal's 8 decisions, covering
  why the bucket layout exists (identity, discovery predicate, sidecar
  support) and the staged expand-contract migration approach. No prior
  doc explained this as a concept.
- `docs/index.md`: linked the new Explanation doc under the Diataxis map.
- Surveyed all 10 files under `docs/` plus the corpus-analysis subsystem
  README (cross-referenced from docs); confirmed `corpus-promotion.md`,
  `cli-commands.md`, `gather-overrides.md`, `run-assess.md`, and others
  needed no changes (already directory-level-only examples, or already
  updated during earlier WI doc sweeps).
- Presented the full plan at the confirm gate, including one judgment
  call: both stale examples' claimed mojibake findings no longer
  reproduce (verified: zero mojibake findings anywhere in the real
  `corpora/` tree), but this is caused by a separate, already-closed
  workstream (`WS-SPECIALS-CLEANUP`), not this migration. User chose to
  scope this run to the path fix + stale-content notice only, and file
  the fuller example rework to `project/design/backlog.md` as its own
  follow-up (landed ahead of this PR, commit on `main`).
- Flagged, but did not fix (unrelated, out of scope): `corpus-promotion.md`'s
  "One-time manual cleanup" section describes a step
  (`git rm -r corpora/ohenry corpora/wilde`) that appears already
  completed in the real repo -- a candidate for a future doc-audit pass.

# Validation

- `python3 -m pytest tests/` -- 1565 passed (doc-only change, no
  regressions; 2 more than the 1563 baseline, from PR #208's own new
  tests).
- `lrh validate` -- 0 errors, 60 pre-existing warnings.
- Every relative link in new/edited docs verified to resolve.
- `scripts/lint`/`scripts/format` -- not applicable (no Python files
  touched); the wrapper scripts fail on the same pre-existing,
  already-confirmed-unrelated tool-version-pin skew as prior sessions.

# Follow-up

- `status` is `in_progress`; update to `landed` via `/lrh-closeout` after
  PR #209 merges.
- Backlog item for the fuller mojibake-example rework already landed on
  `main` ahead of this PR -- see `project/design/backlog.md`.
- Flagged doc-audit candidate (`corpus-promotion.md`'s stale one-time
  cleanup section) not tracked anywhere yet; not added to backlog.md
  since it's a minor, low-urgency structural nit rather than a
  functional gap.
