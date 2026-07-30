---
execution_id: 2026_07_29_21_33_47_SEGMENTATION_RELIABILITY_CHECK_BACKFILL
prompt_id: PROMPT(AD_HOC:SEGMENTATION_RELIABILITY_CHECK_BACKFILL)[2026-07-29T21:33:39-04:00]
work_item: AD_HOC
status: landed
rerun_of: 
pr: https://github.com/xenotaur/LCATS/pull/189
commit: b517a9c6
agent: claude_app
instruction_source: user request in-session (design discussion on run_pilot.py's persistence/resume gaps, followed by "please write the ~40 line measurement script... as a PR")
session_transcript: claude-app:6a2dbae2-adca-4a2a-92fe-2e95d3b2a4e0
created_at: 2026-07-29T21:33:47-04:00
---

# Summary

**POST-HOC BACKFILL, reconstructed at land time — not a fabricated
instruction-phase record.** `experiments/03_cross_segment_relation_pilot/check_segmentation_reliability.py`
was authored and PR #189 opened directly, outside the `/lrh-implement`
skill chain, so no primary implementation prompt ID was minted at the
time. This record documents that original authorship for traceability.
The PR's separate review-response round already has its own record
(`2026_07_29_20_12_36_SEGMENTATION_RELIABILITY_CHECK_REVIEW.md`,
`rerun_of` left blank there for the same reason — no primary record
existed yet when it was created).

The script measures WI-EVENT-0033's remaining acceptance criterion (has
schema-hardening `make_segment_extractor` reduced the 65% segmentation
exclusion rate observed live during WI-EVENT-0030 dogfooding?) without
running the frozen `run_pilot.py`. `run_story()` early-returns on a
segmentation failure before entering the Event-Role-World pipeline, so
this needs ~1 LLM call per story (~20 total) instead of the several
hundred a `run_pilot.py --sample-size 5` run costs.

# Result

- `check_segmentation_reliability.py` created in `experiments/` (an
  explicitly interim tool, to be cleaned up once the separately-scoped
  pipelining/persistence work lands) with a usage docstring and run
  command at the top, as requested.
- One review round (6 comments from `chatgpt-codex-connector`), covered
  fully by `2026_07_29_20_12_36_SEGMENTATION_RELIABILITY_CHECK_REVIEW.md`:
  a genuine cohort-mismatch limitation (added `--story-list` +
  word-count-distribution reporting + honest documentation), a
  non-functional "resume" claim (fixed to actually skip
  already-persisted stories), a missing `should_abort_batch` check
  (fixed), unguarded file I/O (fixed), a wrong exclusion-rate
  denominator (fixed), and a mischaracterized "raw LLM output" field
  (fixed to persist both `raw_output` and `extracted_output` under
  their real names).
- The script still needs a real API key to actually run — that has not
  happened in this environment; the WI-EVENT-0033 acceptance criterion
  remains open pending that live run.

CHAIN-NOTE: cycles=1; stops=0; gates=[merge]; friction=no primary record was minted for the original authorship, requiring this backfill; note="6 review comments, all confirmed valid against the code before fixing; one required a real-exception-based test-harness redesign after the first attempt patched the wrong code path (_classify_api_error wasn't actually reached by the empty_tool_result branch)"

# Validation

See `2026_07_29_20_12_36_SEGMENTATION_RELIABILITY_CHECK_REVIEW.md`'s
Validation section for the full test/lint/`lrh validate` evidence
(1505-test suite, black/ruff clean, 0 `lrh validate` errors) and the
fake-backend harness results (resume, `should_abort_batch`, file-I/O
guards all verified end-to-end at zero API cost).

# Follow-up

- Someone with real API credentials needs to run
  `check_segmentation_reliability.py` and report the resulting
  exclusion rate against the 11/17 (65%) baseline, to actually close
  WI-EVENT-0033's remaining acceptance criterion.
- The separately-discussed pipelining/persistence design proposal
  (Option A from the earlier options analysis) is still not started —
  this script (Option D's "C now") was deliberately the smaller,
  immediate half of that decision, not a substitute for it.
