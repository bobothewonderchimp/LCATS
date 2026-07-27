---
execution_id: 2026_07_27_12_42_58_ERW_PIPELINE_STRUCTURED_OUTPUT_RELIABILITY_AUDIT
prompt_id: PROMPT(AD_HOC:ERW_PIPELINE_STRUCTURED_OUTPUT_RELIABILITY_AUDIT)[2026-07-27T12:41:56-04:00]
work_item: AD_HOC
status: landed
rerun_of:
pr:
commit:
agent: claude_app
instruction_source: chat session (post-mortem sweep after PR #166/#167/#168 fixed two live crashes)
session_transcript: pending
created_at: 2026-07-27T12:42:58-04:00
---

# Summary

Captured a broader structured-output reliability audit as a finding
document, per user direction: don't fix yet, don't run this through PR
review/confirm/merge (work is still in flight - the real pilot run is
executing with the default Opus model), just ground and record what was
found so it can seed a properly-scoped work item/workstream/design
proposal once that run completes.

# Result

Wrote `project/audits/2026-07-27-erw-pipeline-structured-output-reliability-audit.md`,
covering four categories of findings, each grounded with `file:line`
citations verified via `git show origin/main:<path>`:

- Category A: 7 tool schemas (6 in `event_role_world/`, 1 in
  `corpus/assess.py`) missing Anthropic's `strict: true`/
  `additionalProperties: false`.
- Category B: 11 unguarded array-item `.get()` call sites across the same 6
  ERW extractors, sharing the identical pattern that produced PR #168's
  real `AttributeError` crash.
- Category C: 3 extractors (`scene_analysis.py`'s segmentation and
  semantics extractors, `story_analysis.py`'s doc-classification
  extractor) using no tool schema at all - confirmed segmentation is the
  live cause of the pilot's 65% exclusion rate on a cheaper model. Also
  documented why naively adding `tool_schema=` to
  `scene_analysis.make_segment_extractor` would break its other real
  caller, `story_processors.py:76,142`.
- Category D: `processor.py`'s hardcoded model
  (`process_segments()`, no override param) and its stringification of
  structured `api_error` into plain text (discarding
  `should_abort_batch`/`category`/`can_retry`) across all 5 of its passes.

Committed directly to `main` (no PR) per user instruction to skip the
review cycle for this capture step.

# Validation

- `lrh validate` - 0 errors, 43 pre-existing unrelated warnings (audits/
  is not a validated node type, so this file itself isn't schema-checked,
  but validation was still run to confirm no other regression).
- No code changes were made; this is a documentation-only finding.

# Follow-up

- `session_transcript: pending` should be updated to `claude-app:<session-id>`
  after this session ends.
- Per the audit's own "Next steps" section: revisit once the in-progress
  Opus pilot run finishes, discuss scope, then create the actual work
  item(s)/workstream/design proposal - not done as part of this record.
