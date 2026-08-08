---
execution_id: 2026_08_08_05_27_38_PORT_ANNOTATE_ERROR_FINDING_INTO_WI_LLM_0058
prompt_id: PROMPT(AD_HOC:PORT_ANNOTATE_ERROR_FINDING_INTO_WI_LLM_0058)[2026-08-08T05:27:03+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/LCATS/pull/263
commit: 83c06cacb40486bcbc0d0bac42114fafc10cc36c
created_at: 2026-08-08T05:27:38+00:00
agent: claude_app
instruction_source: user request (compare WI-LLM-0058 vs WI-ASSESS-0060, port finding, abandon redundant item)
session_transcript: claude-app:d95251cd-5bda-40d3-a06e-d330bc6e2921
---

# Summary

Ported a real, code-verified finding from `WI-ASSESS-0060`'s review
round into the already-merged, broader `WI-LLM-0058`, as the first
step before abandoning `WI-ASSESS-0060` as redundant.

# Result

Detailed side-by-side comparison of `WI-LLM-0058` (merged PR #257) and
`WI-ASSESS-0060` (open PR #258) confirmed `WI-LLM-0058` is a strict
superset: consolidated 44-story evidence (both `WI-ASSESS-0051`'s
20-story sample and `WI-ANNOTATE-0054`'s 24-story trial), a root-cause
hypothesis requirement, two fix candidates (schema reordering and
output sanitization — the latter matching `WI-ASSESS-0060` exactly), a
go/no-go recommendation for `WI-ASSESS-0051`'s ~$435 full run, and
frontmatter-level `depends_on` wiring already live on `main`
(`WI-ASSESS-0051.md:19-20`).

One real gap: `WI-ASSESS-0060`'s own review round verified (against
`annotate.py:160-169`) that using `AssessmentResult.error` as the
sanitization fix's failure channel would make `_annotate_genre` drop
`genre.json` entirely for any corrupted-`secondary_genre` story —
`WI-LLM-0058`'s text didn't warn against this. Ported into
`WI-LLM-0058`'s Required Changes, Risk Notes, and frontmatter
`acceptance:` list (kept in sync per the file's own convention), plus
a corresponding test requirement.

# Validation

- `lrh validate` — 0 errors (2 pre-existing-class warnings for
  `owner: unassigned`, same as before this edit).
- Re-verified the `annotate.py:160-169` citation directly against the
  current file before porting the finding, not just copied from memory.

# Follow-up

Next: abandon `WI-ASSESS-0060` (move to `abandoned/`, `resolution:`
citing this comparison) and close PR #258 without merging.
