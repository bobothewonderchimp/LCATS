---
execution_id: 2026_08_26_15_28_32_SEGMENTATION_ALIGNMENT_FOLLOWUP_SCOPING
prompt_id: PROMPT(AD_HOC:SEGMENTATION_ALIGNMENT_FOLLOWUP_SCOPING)[2026-08-26T15:24:47+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/LCATS/pull/399
commit: 677b89e8
agent: claude_app
instruction_source: "user request in-session (\"Let's file three work items: case-insensitivity, paragraph-range-boundary, and edit-distance tolerance...\")"
session_transcript: claude-app:e8e46d5d-35d3-4ccc-9cba-137bd31bf3a5
created_at: 2026-08-26T15:28:32+00:00
---

# Summary

Filed three follow-up work items from direct forensic analysis of
`WI-EVENT-0096`'s 10 real post-fix segmentation `alignment_error`
failures - not from the user's original hypothesis alone, but from
actually reading each real anchor against the real source text and
categorizing the true root cause per case, which turned out more varied
than "mostly case/whitespace/punctuation."

# Result

Analyzed all 10 real failures from
`experiments/03_cross_segment_relation_pilot/results/segmentation_reliability/`
directly (loading each story's real text, computing `para_spans`, and
diffing the claimed anchor against the real source at the byte level).
Found 3 distinct categories, not one:

- 2/10 pure case-only near-misses (`what`/`What`, `the`/`The`) -> filed as
  `WI-SEGMENT-0097` (deliverable): extend `_locate_anchor_span`'s existing
  deterministic typography-normalization fallback with `re.IGNORECASE`.
- 5/10 anchors that match the source exactly, just outside the claimed
  paragraph range (one by only 2 characters) -> filed as `WI-SEGMENT-0098`
  (investigation): root-cause whether this is a model-side paragraph
  miscount or a code-side indexing disagreement, before any fix.
- 2/10 genuine word-level near-misses in otherwise-correct anchors
  ("Martina Evers" vs real "Martha Evers" - a content substitution;
  "gratefuly" vs real "gratefully" - a spelling typo) -> filed as
  `WI-SEGMENT-0099` (evaluation): extend `WI-SEGMENT-0072`'s deferred
  fuzzy-matching evaluation corpus with these 2 real positives and report
  against its own frozen adoption thresholds, without lowering them.
- 1/10 (`the_voice_in_the_fog__leverage` end_exact) has a real curly-quote
  typography difference that, on inspection, should already be handled by
  the existing normalizer but still fails for a reason not fully
  diagnosed in this session - not filed separately; whoever picks up
  `WI-SEGMENT-0097` should re-check this case too since it may share the
  same root cause once case-insensitivity is added, or may reveal a
  second latent gap in the existing fallback.

This finding was presented to the user before filing (the real
20%/50%/20%/10% split, not the ~100% the initial hypothesis implied) and
the three-way split was explicitly requested in response. Opened PR #399
(branch `xenotaur/chore/segmentation-alignment-followup-scoping`, commit
`677b89e8`).

# Validation

- `lrh validate` - 0 errors, 245 warnings (pre-existing baseline)

# Follow-up

- The unresolved `the_voice_in_the_fog__leverage` end_exact case (noted
  above) should be re-checked once `WI-SEGMENT-0097` lands, in case it's
  the same root cause or a second latent gap.
- All three new WIs are `status: proposed`, unowned, and not yet executed.
- Offering to add these three WIs to `WS-PILOT-IMPROVEMENTS.md`'s
  `work_items:` list is a candidate follow-up, not yet actioned pending
  user confirmation.
