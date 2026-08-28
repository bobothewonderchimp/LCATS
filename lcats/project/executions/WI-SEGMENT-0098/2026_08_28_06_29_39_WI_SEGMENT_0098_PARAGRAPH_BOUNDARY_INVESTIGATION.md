---
execution_id: 2026_08_28_06_29_39_WI_SEGMENT_0098_PARAGRAPH_BOUNDARY_INVESTIGATION
prompt_id: PROMPT(WI-SEGMENT-0098:WI_SEGMENT_0098_PARAGRAPH_BOUNDARY_INVESTIGATION)[2026-08-28T06:21:34+00:00]
work_item: WI-SEGMENT-0098
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/LCATS/pull/403
commit: ed1b122e
agent: claude_app
instruction_source: lcats/project/work_items/proposed/WI-SEGMENT-0098.md
session_transcript: claude-app:e8e46d5d-35d3-4ccc-9cba-137bd31bf3a5
created_at: 2026-08-28T06:29:39+00:00
---

# Summary

Executed `WI-SEGMENT-0098`: root-caused all 6 real cases from
`WI-EVENT-0096`'s measurement where the model's claimed segmentation
anchor is recoverable but lands outside its claimed paragraph-range
search window.

# Result

For each of the 6 cases, called `_locate_anchor_span` (the real
production function, unmodified) against the whole canonicalized
document to find the true anchor location, then checked it against
`para_spans` to determine the real paragraph number.

**Finding: all 6 cases show the same direction of error** - the real
text always falls in a paragraph after the claimed `end_par_id`, never
before. 5/6 off by exactly 1 paragraph; 1/6 (`the_medici_boots__swet`)
off by 2, with a distinct identifiable cause (an empty/zero-length
paragraph in the source between the claimed and real paragraph).

Directly inspected the `[P####]`-marked boundary text for 3 of the 6
cases (`easy_money__sinclair`, `the_guardians__cox`,
`the_medici_boots__swet`) - confirmed `text_segmenter`'s own paragraph
numbering is correct and internally consistent in every case (using the
exact function that built the model's own input). The pattern is a
model-side attribution error at natural narrative-continuity boundaries
(two short consecutive paragraphs continuing one beat, or a paragraph
that ends mid-sentence), not a code-side indexing disagreement.

Wrote `lcats/project/design/segmentation-paragraph-boundary-truncation-investigation.md`
with the full per-case table, 3 detailed boundary inspections, the
model-side/code-side categorization with supporting evidence, and a
recommendation: a narrowly-scoped end-boundary-only search-window
widening is the most promising direction, but sizing needs a broader
real sample than these 6 cases - not implemented here, per this item's
own `forbidden_actions`. Opened PR #403 (branch
`xenotaur/spike/wi-segment-0098-paragraph-boundary-investigation`,
commit `ed1b122e`).

# Validation

- `lrh validate` - 0 errors, 247 warnings (pre-existing baseline)

# Follow-up

- If a follow-on implementation WI is filed for the recommended
  end-boundary widening, it should be a `deliverable` depending on this
  investigation, sized against a predeclared broader real sample, and
  validated against both these 6 failing cases and a control set of
  currently-passing alignments.
- The empty-paragraph secondary finding (whether
  `build_paragraph_index` should skip assigning markers to zero-length
  paragraphs) is a separate, smaller question worth evaluating
  independently of the main end-boundary-widening question.
- `WI-SEGMENT-0099` remains separately scoped and unexecuted.
