---
execution_id: 2026_08_05_21_12_33_WORLDCON_FAST_PATH_ANNOTATION_REVIEW
prompt_id: PROMPT(AD_HOC:WORLDCON_FAST_PATH_ANNOTATION_REVIEW)[2026-08-05T21:12:26+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 2026_08_05_19_10_51_WORLDCON_FAST_PATH_ANNOTATION
pr: https://github.com/xenotaur/LCATS/pull/226
commit: a9c69ea02408898795931a6578fc41992a2f9c86
created_at: 2026-08-05T21:12:33+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/LCATS/pull/226
session_transcript: claude-app:d95251cd-5bda-40d3-a06e-d330bc6e2921
---

# Summary

Address open review comments on PR #226, fetched via `lrh request
review_response`.

# Result

2 comments, both from bots, both triaged as present/valid/feasible and
fixed by editing the proposal text (this PR only adds a design proposal
document, not code, so "fixing" means correcting the proposal's design
decisions and their evidence trail):

1. (`chatgpt-codex-connector`, P2) Decision 6 originally said `lcats
   annotate` would iterate story buckets via
   `discovery.iter_collection_story_files` without qualification.
   Verified against `discovery.py`: that selector only checks the
   immediate children of the path it's given for a `story.json` — called
   directly against a multi-collection corpus root (`data/`/`corpora/`),
   it silently yields nothing, since a root's immediate children are
   collections, not story buckets. Fixed by rewriting Decision 6 to
   require `lcats annotate` to enumerate collection directories first
   and call `iter_collection_story_files` once per collection — verified
   this exactly mirrors `promote.py`'s existing `promote_collections`,
   which already drives `survey_collection` the same way.
2. (`copilot-pull-request-reviewer`) Decision 5 claimed a one-line
   `max_tokens` override for the segmentation extractor was "stranded"
   inside `run_pilot.py`'s `_segment_story()`. Verified directly against
   the current `experiments/03_cross_segment_relation_pilot/run_pilot.py`:
   `_segment_story()` has no `max_tokens` override at all — the claim was
   simply wrong. The only existing override precedent in that file is
   `_build_erw_extractors`'s `extractor.max_tokens = _ERW_MAX_TOKENS`,
   which applies to the five ERW extractors, not segmentation. Fixed
   Decision 5 to state the fix must be written fresh in
   `scene_analysis.py`, following that override-pattern precedent rather
   than "lifting" a fix that doesn't exist.

No exceptions (Unaddressed/Partial/Ambiguous/Problematic) — both
comments resolved by the above edits.

# Validation

- `lrh validate` — 0 errors/warnings on the changed file.
- `scripts/format --check --diff` — clean (markdown-only change, no
  formatter drift).
- Both fixes independently re-verified against the actual source files
  (`discovery.py`, `promote.py`, `run_pilot.py`) before editing, not just
  taken on the reviewer's word.

# Follow-up

None — both findings were fully resolved in the proposal text.
