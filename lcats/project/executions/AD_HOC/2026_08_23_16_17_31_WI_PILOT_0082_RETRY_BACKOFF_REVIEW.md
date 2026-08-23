---
execution_id: 2026_08_23_16_17_31_WI_PILOT_0082_RETRY_BACKOFF_REVIEW
prompt_id: PROMPT(AD_HOC:WI_PILOT_0082_RETRY_BACKOFF_REVIEW)[2026-08-23T16:17:24+00:00]
work_item: AD_HOC
status: landed
rerun_of: 
pr: https://github.com/xenotaur/LCATS/pull/368
commit: 05203f45
agent: claude_app
instruction_source: https://github.com/xenotaur/LCATS/pull/368
session_transcript: claude-app:e8e46d5d-35d3-4ccc-9cba-137bd31bf3a5
created_at: 2026-08-23T16:17:31+00:00
---

# Summary

Address three open review comments on PR #368 (bounded retry-with-backoff
for `JSONPromptExtractor`, WI-PILOT-0082). No primary implementation
execution record exists for this PR - `grep -rl "pull/368"
project/executions/` returned no matches - this is the first execution
record authored against it.

# Result

All three findings (`copilot-pull-request-reviewer`) confirmed real
before fixing:

**No validation on `max_retries`/`retry_backoff_seconds`:** confirmed by
reading `__init__` directly - negative `max_retries` silently disables
retries (`attempt=0 >= -1` is always `True`), and negative
`retry_backoff_seconds` raises `ValueError` from `time.sleep()` deep
inside a retry attempt rather than at construction. Added explicit
`ValueError` checks in `__init__` for both.

**`_complete_with_retry()` double-normalizes on `max_retries=0`:**
confirmed by reading `_complete_with_retry()` and `extract()`'s `except`
block together - with the default `max_retries=0`, an exception was
still passed through `_normalize_api_error()` once inside
`_complete_with_retry()` (to check `can_retry`) and again in `extract()`,
making the docstring's "identical to calling `backend.complete` directly"
claim inaccurate. Added a fast path: `max_retries<=0` calls
`self.backend.complete(**kwargs)` directly with no classification
overhead, verified by a new test that mocks `_normalize_api_error` and
asserts it is called exactly once (by `extract()`, not twice).

**`_RetryThenSucceedBackend.complete()` used a generic `**kwargs`
signature:** confirmed by reading the test double next to
`_RaisingBackend`/`FakeBackend` - it could hide a call-contract mistake
in how `JSONPromptExtractor` invokes `backend.complete()`. Aligned its
signature to the same keyword-only
`system/messages/model/temperature/max_tokens/tool` contract as the
other backend doubles.

# Validation

- `scripts/format --check --diff` - clean (216 files unchanged)
- `scripts/lint` - clean
- `scripts/test` - 2011 tests, OK; `llm_extractor_test.py` specifically -
  94 tests, OK (3 new tests added for the negative-value validation and
  the fast-path/single-normalization behavior; existing retry tests
  unaffected by the signature alignment)
- All three findings independently re-verified against real repo state
  before fixing: read `__init__`'s stored-params block, read
  `_complete_with_retry()`/`extract()`'s except block together to confirm
  the double-normalization, and read `_RetryThenSucceedBackend` next to
  `_RaisingBackend` to confirm the signature mismatch

# Follow-up

- Suggest running `/lrh-confirm-fixes` (inlined as `/lrh-land` Step 5)
  against the current HEAD to verify these fixes and resolve the review
  threads before merge.
- `session_transcript` above uses the host session ID with its `local_`
  prefix stripped; update if a more durable pointer becomes available.
