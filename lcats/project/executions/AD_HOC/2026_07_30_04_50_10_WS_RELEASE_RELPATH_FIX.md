---
execution_id: 2026_07_30_04_50_10_WS_RELEASE_RELPATH_FIX
prompt_id: PROMPT(AD_HOC:WS_RELEASE_RELPATH_FIX)[2026-07-30T04:49:58-04:00]
work_item: AD_HOC
status: landed
rerun_of: 
pr: https://github.com/xenotaur/LCATS/pull/194
commit: 81c49aa16dde05e081d782579c0b7b0a7cd10262
agent: claude_app
instruction_source: chat
session_transcript: claude-app:b47ed180-afb4-4b2b-893c-74cda0271c0f
created_at: 2026-07-30T04:50:10-04:00
---

# Summary

Fix an off-by-one relative-path bug in
`lcats-pypi-release-readiness/README.md`'s link to `WS-RELEASE.md`. From
that file's location, 3 levels of `../` only reaches
`lcats/project/design/workstreams/proposed/...`, which doesn't exist; 4
levels are needed to reach `lcats/project/workstreams/proposed/
WS-RELEASE.md`. Same class of bug chatgpt-codex-connector caught in PR
#192's sibling file (`lcats-pipeline-checkpointing/README.md`). Also swept
the rest of `lcats/project/` for the same relative-link pattern; found no
other instances.

# Result

PR #194 opened, reviewed (no unresolved threads), and merged via
`gh pr merge 194 --merge --match-head-commit
eccffe78e356c01fd09fd61c05eea30c8bc267e3` on explicit in-session
authorization. Merge commit: `81c49aa16dde05e081d782579c0b7b0a7cd10262`.

CHAIN-NOTE: cycles=0; stops=0; gates=[merge]; friction=none; note="No
primary execution record existed for this ad-hoc fix; backfilled here.
Confirm-fixes found zero unresolved threads, so Steps 3-7 of
/lrh-confirm-fixes were skipped straight to the readiness report per its
own skip rule."

# Validation

- Verified the off-by-one directly with `ls` from the file's directory:
  3 `../` fails, 4 `../` resolves
- `lrh validate` from `lcats/`: 0 errors (47 pre-existing warnings
  unrelated to this change)
- CI (test, coverage, lint) all green on the merged commit
- `lrh request review_response` and `lrh github threads --mode raw
  --state all`: zero unresolved threads

# Follow-up

None.
