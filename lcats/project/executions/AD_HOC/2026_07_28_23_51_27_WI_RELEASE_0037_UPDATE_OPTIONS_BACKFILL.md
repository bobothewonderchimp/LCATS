---
execution_id: 2026_07_28_23_51_27_WI_RELEASE_0037_UPDATE_OPTIONS_BACKFILL
prompt_id: PROMPT(AD_HOC:WI_RELEASE_0037_UPDATE_OPTIONS_BACKFILL)[2026-07-28T23:51:19-04:00]
work_item: AD_HOC
status: landed
rerun_of: 
pr: https://github.com/xenotaur/LCATS/pull/182
commit: 188592d0f62bb6c9e5d1bd0a72db8e4b0d24ef4a
created_at: 2026-07-28T23:51:27-04:00
agent: claude_app
instruction_source: https://github.com/xenotaur/LCATS/pull/182
session_transcript: claude-app:784bb58f-7dfc-4a15-b52e-ce882a3b1ba7
---

# Summary

**POST-HOC BACKFILL**, reconstructed at land time (closeout of PR #182),
not a fabricated instruction-phase record. Documents PR #182's original
work: updating `project/work_items/proposed/WI-RELEASE-0037.md` in this
same session/conversation, in direct response to the user's requests to
explain and then deepen the Option A/B/C tradeoff analysis. This edit
was made directly via the Edit tool, not through `/lrh-work-item` or
`/lrh-implement`, so no primary record existed until this backfill.

# Result

Revised `WI-RELEASE-0037`'s Problem/Context, Scope, Required Changes,
Acceptance Criteria, and Risk Notes to incorporate: (1) confirmation
that the LCATS maintainer has contacted upstream about a gutenbergpy
release schedule (Option A), plus the `setup.cfg: version = 0.3.6`
unreleased-bump signal as a mildly encouraging data point; (2) PyPI's
direct-dependency rejection mechanism grounded in the actual
`pypi/warehouse` source (`warehouse/forklift/metadata.py`); (3)
correction that both Option B (vendor) and Option C
(re-fork-and-publish) require forking gutenbergpy's cache-construction
dependency closure — not a small patch — since `GutenbergCache.create()`
hardcodes its parser/cache-writer with no extension point; (4) Option
C-specific detail on legacy packaging, dated dependencies, and the need
for a second release pipeline; and (5) a new Open Questions section
(maintainer response pending, fork PyPI name availability unconfirmed).
The WI itself remains in `proposed/` — this PR delivered a planning
content revision, not implementation. Two subsequent execution records
(`2026_07_28_23_42_59_WI_RELEASE_0037_UPDATE_OPTIONS_REVIEW`,
`2026_07_28_23_47_57_WI_RELEASE_0037_UPDATE_OPTIONS_CONFIRM`) document
the review round that followed (Copilot + Codex, both caught real
issues — including an incomplete vendoring file list this record's own
author had just written) and are now also `landed`.

CHAIN-NOTE: cycles=1; stops=0; gates=[merge]; friction=none; note="two bot reviewers again posted sequentially (Copilot then Codex, ~30s apart this time) rather than together, consistent with PR #180's pattern"

# Validation

- `lrh validate` — 0 errors at time of PR merge
- CI (`test`, `coverage`, `lint`) green on merge commit `188592d0f62bb6c9e5d1bd0a72db8e4b0d24ef4a`

# Follow-up

- `WI-RELEASE-0037` remains open in `proposed/` — the vendor/fork/wait
  decision itself, and its implementation, are still future work.
- Sibling work item `WI-RELEASE-0038` (version tooling) remains a
  separate, independent PR not covered by this record.
