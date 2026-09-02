---
resolution: null
blocked_reason: null
blocked: false
id: WI-SEGMENT-0106
title: Investigate combining paragraph-boundary prompt fix with window-widening
type: investigation
status: proposed
priority: medium
owner: unassigned
contributors: []
assigned_agents: []
related_focus:
  - FOCUS-WORLDCON-2026
related_roadmap: []
related_workstreams:
  - WS-PILOT-IMPROVEMENTS
related_design:
  - lcats/project/design/segmentation-paragraph-boundary-truncation-investigation.md
  - lcats/project/design/segmentation-paragraph-boundary-prompt-consistency-investigation.md
  - lcats/project/work_items/resolved/WI-SEGMENT-0098.md
  - lcats/project/work_items/resolved/WI-SEGMENT-0101.md
  - lcats/project/work_items/resolved/WI-SEGMENT-0059.md
depends_on:
  - WI-SEGMENT-0098
  - WI-SEGMENT-0101
blocked_by: []
expected_actions:
  - create_file
  - edit_file
  - run_tests
  - create_pr
forbidden_actions:
  - implement_production_prompt_change
  - implement_window_widening
  - spend_api_budget_without_approval
  - force_push
  - delete_branch
acceptance:
  - "Both stories that regressed under WI-SEGMENT-0101's reworded prompt (mass_quantities/the_last_days_of_l_a__smith, ohenry-whirligigs/girl) are root-caused with a stated verdict - genuine new confusion introduced by the reworded instruction, or ordinary run-to-run stochastic variance - grounded in their actual committed reworded-prompt output, not speculation"
  - "A margin-sizing analysis reports the full distribution of overshoot sizes (in characters) needed to recover every currently-available real anchor-level overshoot instance across both WI-SEGMENT-0098's baseline data and WI-SEGMENT-0101's reworded-prompt data (21 real instances as of this item's filing, ranging 4-5,345 characters) - not just a single min/max/typical number, since the real distribution has a long tail a fixed small margin would not cover"
  - "A simulated combined-fix pass applies a hypothetical widened end-boundary window (sized per the margin analysis) to WI-SEGMENT-0101's already-committed real reworded-prompt output and reports: how many of the remaining anchor-level overshoot instances it would recover, and whether it would ever accept a match outside the model's claimed window that is not the correct one (a false-accept risk) - using the exact same strict exact/typography/whitespace/case-tolerant match criteria text_segmenter._locate_anchor_span already uses, never a looser fuzzy search"
  - "A plain recommendation is stated: implement a combined-fix deliverable WI now, defer pending a larger real sample, or reject the combined approach - grounded in the findings above, not asserted"
  - "No production code (scene_analysis.py, text_segmenter.py) or prompt text is changed by this item - investigation and simulation only"
  - "No new real API spend - this item's entire analysis is performed against already-committed real data from WI-SEGMENT-0098 and WI-SEGMENT-0101"
  - "lrh validate reports 0 errors"
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
artifacts_expected:
  - lcats/project/design/segmentation-combined-boundary-fix-feasibility.md
---

# Work Item: WI-SEGMENT-0106

## Summary

`WI-SEGMENT-0098` recommended a code-side end-boundary search-window
widening for paragraph-boundary overshoot failures, but never
implemented it or sized the margin. `WI-SEGMENT-0101` separately tested
a prompt-side fix (deriving `end_par_id`/`start_par_id` from anchor
location instead of independent judgment) and found it directionally
positive but incomplete: anchor-level overshoot dropped from 12/350 to
9/321, with 2 stories showing new overshoot that hadn't appeared under
the unmodified prompt. Neither investigation resolved whether combining
both mitigations is worth implementing. This item answers that -
entirely by analyzing data both prior items already collected and
committed, with no new real API spend.

## Problem / Context

Three open questions block a combined-implementation decision, all
answerable from already-committed real data:

1. **Two stories regressed under the reworded prompt with no
   explanation on record.**
   `mass_quantities/the_last_days_of_l_a__smith` (segment 7: end
   overshoot 93 chars at window `[21030, 22624]`, real match
   `[22626, 22717]`; segment 11: end overshoot 209 chars at window
   `[32451, 34775]`, real match `[34777, 34984]`) and
   `ohenry-whirligigs/girl` (segment 2: end overshoot 170 chars at
   window `[943, 2373]`, real match `[2376, 2543]`) both show overshoot
   under `WI-SEGMENT-0101`'s reworded prompt that did not appear under
   the unmodified production prompt on the same cohort. `WI-SEGMENT-0101`
   explicitly left this unresolved, citing the single-run/model-
   stochasticity limitation, and did not investigate further.
2. **The window-widening margin was never sized against real data.**
   `WI-SEGMENT-0098`'s original 6 cases all needed only 1-2 paragraphs of
   margin, but that investigation explicitly flagged the sample as too
   thin to trust as representative. The combined real dataset now
   available (`WI-SEGMENT-0098`'s baseline + `WI-SEGMENT-0101`'s
   reworded-prompt residuals) has 21 real anchor-level overshoot
   instances with `overshoot_chars` values ranging from 4 to 5,345 -
   spot-checked directly from the committed
   `paragraph_boundary_overshoot_baseline.json`/`_reworded.json`
   artifacts - a spread wide enough that a single small fixed margin
   would clearly miss the tail.
3. **No one has checked whether the two fixes interact safely together.**
   Applying a widened window on top of the already-reworded prompt's
   output has never been simulated, so it's unknown whether a combined
   fix would recover the residual 9/321 anchor-level failures, or
   whether widening risks a false-accept (a match outside the model's
   claimed window that isn't actually the correct location) on any of
   the 162 already-checked reworded-prompt segments.

### Duplication search

- In-repo: `WI-SEGMENT-0098` and `WI-SEGMENT-0101` are the direct
  predecessors; neither combines the two mitigations or sizes the
  margin. `WI-SEGMENT-0059` documents the standing safety principle
  (never silently accept a wrong-but-plausible match) this item's
  simulation must respect. No existing item performs this specific
  combined-feasibility analysis.
- Sibling repos: None identified.
- External libraries: Not applicable - reuses
  `text_segmenter._locate_anchor_span` and the existing overshoot
  measurement tooling from `WI-SEGMENT-0101` unmodified.
- Recommendation: Proceed.

### Demand search

- Work items: Surfaced directly from `WI-SEGMENT-0101`'s own closeout
  follow-up note and a user-driven design discussion in this session. No
  existing work item covers this combined-feasibility question.
- Proposals: None identified.
- Backlog: No matching entry found.
- Recommendation: Proceed.

## Scope

- Root-cause the 2 regressed stories by reading their real committed
  `parsed_output` (both baseline and reworded) directly, alongside the
  real story text, to determine whether the reworded prompt introduced a
  genuine new confusion or the regression is ordinary sampling noise.
- Gather every real anchor-level overshoot instance currently available
  (both `WI-SEGMENT-0098`'s baseline data and `WI-SEGMENT-0101`'s
  reworded-prompt data) and report the full distribution of
  `overshoot_chars` needed to recover each one.
- Simulate a widened end-boundary window against `WI-SEGMENT-0101`'s
  already-committed reworded-prompt output: for each currently-failing
  anchor, would a window widened by the sized margin recover it using
  the same strict match criteria; for each currently-*passing* segment,
  does the widened window ever produce a different, wrong match.
- State a plain go/defer/reject recommendation.
- Do not implement the prompt change, the window-widening code, or spend
  any new real API budget.

## Required Changes

1. Write a small analysis script (not a permanent pipeline component)
   that loads `mass_quantities/the_last_days_of_l_a__smith` and
   `ohenry-whirligigs/girl`'s real committed reworded-prompt
   `parsed_output`, locates the relevant segments' anchors in the real
   story text, and reports a root-cause verdict for each with supporting
   evidence (not just the offsets already known - inspect the actual
   anchor text and surrounding context).
2. Aggregate all real `overshoot_chars` values from
   `experiments/03_cross_segment_relation_pilot/results/paragraph_boundary_overshoot_baseline.json`
   and `..._reworded.json` (or freshly regenerate them from the
   underlying committed result directories if either has drifted) into a
   single distribution; report percentiles or a full sorted list, not
   just min/max.
3. Write a simulation function that, given a margin size, re-checks every
   segment in `WI-SEGMENT-0101`'s reworded-prompt results with the end
   boundary widened by that margin (still using
   `text_segmenter._locate_anchor_span`'s existing strict matching, never
   a fuzzy/looser search), and reports: newly-recovered anchor count,
   and any segment where the widened window's accepted match differs
   from what the strict same-window search already found (a potential
   false-accept signal).
4. Write
   `lcats/project/design/segmentation-combined-boundary-fix-feasibility.md`
   with the root-cause findings, the margin distribution, the simulation
   results, and a plain recommendation.
5. If a combined-implementation WI is recommended, note that as a
   follow-up - do not file or implement it as part of this item.

## Non-Goals

- Does not implement the prompt-side fix in production
  (`scene_analysis.py`) or the code-side window-widening
  (`text_segmenter.py`) - simulation and analysis only.
- Does not spend any real API budget - all analysis reuses already-
  committed real data from `WI-SEGMENT-0098` and `WI-SEGMENT-0101`.
- Does not loosen the match criteria used anywhere in this analysis -
  the simulation must use the same strict exact/typography/whitespace/
  case-tolerant matching production already uses, never a fuzzy
  similarity threshold.
- Does not decide the combined-implementation question by itself if the
  evidence remains inconclusive - "defer, need a larger sample" is an
  acceptable and expected outcome, not a failure of this item.

## Acceptance Criteria

(see frontmatter `acceptance:` above)

## Validation

- lrh validate
- test_output

## Risk Notes

- **This item's own honesty bar matters more than a clean-sounding
  conclusion.** Both parent investigations already flagged their
  evidence as thin; this item's job is to state plainly whether combining
  them clears a higher bar or merely restates the same thinness with
  extra steps - not to manufacture confidence the data doesn't support.
- **The false-accept check in the simulation is the safety-critical
  part.** Per `WI-SEGMENT-0059`, a widened window that ever silently
  prefers a wrong match over the correct one is a stop condition for
  recommending implementation, not a tuning parameter to adjust past.
- **Root-causing the 2 regressions might turn up nothing conclusive**
  given only one real trace per story - if so, say that plainly rather
  than forcing a confident-sounding explanation.

## Related Workstream and Designs

- Workstream: `lcats/project/workstreams/proposed/WS-PILOT-IMPROVEMENTS.md`
- Design: `lcats/project/design/segmentation-paragraph-boundary-truncation-investigation.md`
  (`WI-SEGMENT-0098`'s original window-widening recommendation)
- Design: `lcats/project/design/segmentation-paragraph-boundary-prompt-consistency-investigation.md`
  (`WI-SEGMENT-0101`'s reworded-prompt ablation and its unresolved
  regressions)
- Work item: `lcats/project/work_items/resolved/WI-SEGMENT-0059.md`
  (the standing safety principle this item's simulation must respect)
