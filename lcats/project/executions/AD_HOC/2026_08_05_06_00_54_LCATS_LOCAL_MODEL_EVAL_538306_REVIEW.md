---
execution_id: 2026_08_05_06_00_54_LCATS_LOCAL_MODEL_EVAL_538306_REVIEW
prompt_id: PROMPT(AD_HOC:LCATS_LOCAL_MODEL_EVAL_538306_REVIEW)[2026-08-05T05:22:32+00:00]
work_item: AD_HOC
status: landed
rerun_of: 2026_08_05_04_48_32_ERW_LOCAL_MODEL_EVALUATION
pr: https://github.com/xenotaur/LCATS/pull/219
commit: 98ae706b09ee1d9d406e92ec8ba3c6beed2ba18a
created_at: 2026-08-05T06:00:54+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/LCATS/pull/219
session_transcript: claude-app:6d988910-ee4a-4ccc-af0b-2fb13d91ddc5
---

# Summary

Address open review comments on PR #219 (`PROP-ERW-LOCAL-MODEL-EVALUATION`
+ local-model benchmark infra), fetched via `lrh request review_response`.

# Result

Three findings from Codex and Copilot, all triaged as present/valid/
feasible and fixed:

1. `common/harness.py`'s success check only looked at `api_error`, so a
   tool call that parsed but didn't match `ENTITY_TOOL_SCHEMA` (e.g. no
   `entities` list) would still record `success: true`. Fixed by also
   requiring `entities` to be a list; added a `schema_error` code/message
   path for this case.
2. `ollama_qwen3_8b/setup.py` accepted any `qwen3:*`-prefixed tag as
   satisfying the prerequisite check, but `benchmark.py` always requests
   the exact `qwen3:8b`. Fixed to require an exact tag match.
3. Same file's `installed` set was built from `m.get("name")` without
   filtering, so a payload entry missing `"name"` would put `None` into
   the set and crash the subsequent membership check. Fixed by filtering
   to entries with a truthy `name` first.

Re-ran `ollama_qwen3_8b/benchmark.py` against the fixed harness to verify
end-to-end - it produced a genuinely new, decision-relevant result: this
run **succeeded** (20 entities) but took 1727s (~29 minutes), vs. the
first run's outright failure and vs. `claude-opus-4-8`'s 202s baseline.
Same model/story/schema, two different outcomes on identical input. With
the user's explicit approval, updated `PROP-ERW-LOCAL-MODEL-EVALUATION`'s
Decision 3 (and the candidate's own README) to reflect both runs and
sharpen the framing from "qwen3:8b failed" to "qwen3:8b is unreliable
and, even when it works, ~8.5x slower" - the recommendation to hold the
current default is unchanged, but the evidence text is now accurate.
Preserved both raw runs as `results_run1_failed.json`/
`results_run2_succeeded.json` since a candidate's single `results.json`
only reflects the latest run.

# Validation

- `python -m pytest tests/llm_tests/ -q` - 40 passed.
- `black --check` / `ruff check` clean on `experimental/model_comparison`.
- `lrh validate` - no new errors attributable to this PR's files.
- Real (non-simulated) rerun of `ollama_qwen3_8b/benchmark.py` against
  the fixed harness - not a synthetic test of the fix.

# Follow-up

- Same as the primary record's follow-up: retry with Ollama's `think`
  parameter disabled (now doubly motivated - it's the leading suspect for
  both the failure and the ~29-minute latency), add a `qwen3:30b-a3b`
  candidate, extend the harness to genre-detection/segmentation stages.
