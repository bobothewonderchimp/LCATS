---
execution_id: 2026_08_07_03_48_21_WS_PILOT_COST_SUSTAINABILITY_CLOSEOUT_NOTE
prompt_id: PROMPT(AD_HOC:WS_PILOT_COST_SUSTAINABILITY_CLOSEOUT_NOTE)[2026-08-07T03:48:09+00:00]
work_item: AD_HOC
status: landed
rerun_of: 2026_08_07_03_44_15_WS_PILOT_COST_SUSTAINABILITY_CONFIRM
pr: https://github.com/xenotaur/LCATS/pull/234
commit: f5fda70f6c5dd8c581a1be8a7e3a35e22e7bf8e5
agent: claude_app
instruction_source: https://github.com/xenotaur/LCATS/pull/234
session_transcript: claude-app:6a2dbae2-adca-4a2a-92fe-2e95d3b2a4e0
created_at: 2026-08-07T03:48:21+00:00
---

# Summary

Closeout for PR #234, which created `WS-PILOT-COST-SUSTAINABILITY`, the
governing workstream for the already-adopted
`PROP-LCATS-PILOT-COST-SUSTAINABILITY`. Merged as
`f5fda70f6c5dd8c581a1be8a7e3a35e22e7bf8e5`, squash merge, confirmed as
`main`'s real tip via the GitHub API.

# Result

- PR #234 merged clean (`mergeStateStatus: CLEAN`) after one
  review/fix round plus two further independent-subagent-caught fixes:
  1. Round 1 (Codex, formal threads): stale "not yet governed by a
     workstream" claim in the proposal-set README, and the workstream's
     own Demand search wrongly claiming no matching `backlog.md`
     entries when two existed — both fixed.
  2. Independent subagent pass 1: found a real, pre-existing stale
     backlog entry ("ERW pipeline audit's Category E ... never
     promoted") not touched by the PR's diff but directly contradicted
     by it — fixed with a strikethrough + resolution note.
  3. Independent subagent pass 2: caught an overclaim in that same fix
     ("in progress" for a workstream whose actual status is
     `proposed`/`planned`) — corrected.
  4. Independent subagent pass 3 (final): reviewed the complete diff
     (5 files, 299 lines) and reported CLEAN.
- **CHAIN-NOTE (process correction, this is the material finding for
  this closeout):** this session initially lapsed back into retriggering
  billed GitHub bot reviews directly (`@codex review`, `@copilot review`)
  on this PR, despite a standing memory (confirmed three prior times:
  PRs #206, #207, #209) to prefer independent subagent review instead.
  The user caught this mid-round and reframed it as a broader,
  fleet-wide cost policy ("we have been moving to this across the agent
  fleet due to unexpected GitHub Action costs"), not just a
  session-local preference. Two bot retriggers had already been sent
  before the correction (Codex responded once, clean, on `8c88d753`;
  Copilot never responded and was not re-triggered after the
  correction). All subsequent rounds (2 fix-finding passes + 1 final
  clean pass) used independent `Agent` subagent calls instead, per the
  corrected approach. The standing memory
  (`feedback_prefer_subagent_review_over_github_bots.md`) was updated
  in-session to record this as a fourth confirmation and to note the
  fleet-wide framing.
- cycles=1; stops=0; gates=[merge]; friction=one self-corrected process
  lapse (billed-bot retrigger), otherwise clean single round.
- Confirmed `main`'s real tip via
  `gh api repos/xenotaur/LCATS/commits/main --jq '.sha'` ==
  `f5fda70f6c5dd8c581a1be8a7e3a35e22e7bf8e5`, matching the reported
  merge commit exactly.

# Validation

- `lrh validate` (from `lcats/`) — 0 errors (unchanged baseline warning
  count, 79).
- `gh pr view 234 --json state,mergedAt,mergeCommit` confirmed
  `state: MERGED`.
- GitHub API confirmed `main`'s tip matches the merge commit (see
  above) — single, non-stacked workstream-creation PR, no propagation
  gap applies.

# Follow-up

- Governing workstream `WS-PILOT-COST-SUSTAINABILITY` is now `status:
  proposed`, `stage: planned`, `work_items: []`. Natural next step:
  `/lrh-work-item` for WI 1 (targeted test harness on `run_pilot.py`),
  since WI 2-4 (prompt-caching, Batch API, model-tiering evaluations)
  all depend on it per the proposal's own sequencing.
- No other deferred work from this PR's review rounds.
