---
execution_id: 2026_07_30_14_28_49_WS_STORY_BUCKET_LAYOUT
prompt_id: PROMPT(AD_HOC:WS_STORY_BUCKET_LAYOUT)[2026-07-30T14:06:20-04:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/LCATS/pull/197
commit: b8ba3490
created_at: 2026-07-30T14:28:49-04:00
agent: claude_app
instruction_source: lcats/project/workstreams/proposed/WS-STORY-BUCKET-LAYOUT.md
session_transcript: claude-app:ca0e8b20-2e3a-44f3-90b6-c506f3b98336
---

# Summary

Created `WS-STORY-BUCKET-LAYOUT`, the workstream coordinating the 3-stage
implementation of `PROP-LCATS-STORY-BUCKET-LAYOUT` (merged via PR #196),
following this session's design and review work on the underlying
proposal.

# Result

- Wrote `lcats/project/workstreams/proposed/WS-STORY-BUCKET-LAYOUT.md` with
  frontmatter and full body (Purpose, Scope, Prior Art Check, Work Items,
  Exit Criteria, Non-Goals, Open Questions), mirroring the sibling
  `WS-PIPELINE-CHECKPOINTING` workstream's structure and depth.
- Scope tracks the proposal's 3 stages verbatim: read-path compatibility
  (Decisions 2-3), write-path migration (Decisions 5-8, including the
  review-discovered `parser.gather_story()` writer site and the standing
  `lcats promote` zero-story-count rejection), and convergence-and-validation
  (Decision 4's two-part retraction gating).
- `work_items: []` — none created yet; offered as a follow-on per the
  skill's Step 11.
- `related_focus: [FOCUS-WORLDCON-2026]` — LCATS's only active focus
  ("story analysis pipeline foundations"), genuinely thematically connected
  (corpus storage foundations), not invented for the sake of a non-empty
  field.
- Non-Goals explicitly cross-reference the proposal's four excluded
  follow-ons (gather incrementality, notebook fixes, experiment fixes,
  librarize-and-test investigation) so none get silently assumed in-scope.

# Validation

- `lrh validate` -> 0 errors, 51 pre-existing warnings (unrelated
  `OWNER_ROLE_INSUFFICIENT`/`OWNER_NOT_IN_CONTRIBUTORS` items; none
  reference the new workstream).

# Follow-up

- Offer to create the 3 stage work items via `/lrh-work-item` once this
  workstream PR is confirmed/merged.
