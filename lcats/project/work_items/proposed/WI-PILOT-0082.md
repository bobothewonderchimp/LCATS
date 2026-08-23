---
resolution: null
blocked_reason: null
blocked: false
id: WI-PILOT-0082
title: Add bounded retry-with-backoff for transient LLM API errors
type: operation
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
  - lcats/project/workstreams/proposed/WS-PILOT-IMPROVEMENTS.md
  - lcats/project/design/proposals/proposed/lcats-pilot-improvements/00_proposal.md
  - lcats/project/audits/2026-07-27-erw-pipeline-structured-output-reliability-audit.md
  - lcats/project/work_items/resolved/WI-PILOT-0067.md
  - lcats/project/work_items/proposed/WI-EVENT-0030.md
depends_on: []
blocked_by: []
expected_actions:
  - create_pr
forbidden_actions:
  - modify_event_role_world_extractor
  - implement_prompt_caching_adoption
  - implement_model_tiering_adoption
  - implement_batch_api_adoption
  - force_push
  - delete_branch
acceptance:
  - "JSONPromptExtractor gains opt-in max_retries/retry_backoff_seconds constructor parameters, defaulting to 0/no-op so every existing caller's behavior is byte-for-byte unchanged unless it explicitly opts in"
  - "A retryable failure (server overload, rate limit - the existing _classify_api_error can_retry=True categories) that succeeds within max_retries attempts is fully recovered - the caller sees a successful result, not an api_error"
  - "A non-retryable failure (auth, quota, context-length, truncated-output) never retries regardless of max_retries, and propagates on the first attempt exactly as before this change"
  - "Retry delay follows exponential backoff (retry_backoff_seconds * 2^attempt), verified by asserting the actual sleep call sequence, not just that retries happened"
  - "When retries are exhausted, the final exception flows into the exact same api_error result shape a non-retried failure already produces - retry exhaustion is not a new caller-visible failure mode"
  - "All new behavior is verified with mocked backends only - no real LLM calls are made as part of this work item"
  - "scripts/test passes with no new failures"
  - "lrh validate reports 0 errors"
required_evidence:
  - test_output
  - lrh_validate
artifacts_expected:
  - lcats/src/lcats/analysis/llm_extractor.py
  - lcats/tests/analysis_tests/llm_extractor_test.py
---

# Work Item: WI-PILOT-0082

## Summary

Add a bounded, opt-in retry-with-backoff wrapper around
`JSONPromptExtractor`'s backend call, so a transient API error (server
overload, rate limit) doesn't permanently exclude a story from a real
pilot run the way it does today. Backend-level fix, verified entirely with
mocked backends - no real LLM spend.

## Problem / Context

A real `WI-EVENT-0030` cost-gate run (2026-08-22/23) hit two transient
failures that permanently excluded stories from the sample: an Anthropic
`overloaded_error` during `event_anchor` extraction, and a network read
timeout during `discourse` extraction. Both hit a genre (fantasy) that had
been 100% reliable in every earlier test that session ran - these were not
data-quality or model-capability problems, just bad luck on the API call.

Investigation found `JSONPromptExtractor._classify_api_error`
(`lcats/src/lcats/analysis/llm_extractor.py:168-247`) already *labels*
both failure classes `can_retry: True`, but nothing in the codebase acts on
that label - `extract()`'s `except Exception` just returns the classified
error dict (`llm_extractor.py:406-431` as of that investigation). A
separate `Stage.retries` skeleton exists at `lcats/pipeline.py:87-98` but
has zero importers anywhere in `lcats/src` or `experiments/` - dead code,
not wired into the ERW pipeline or any pilot script. The 2026-07-27
reliability audit (`lcats/project/audits/2026-07-27-erw-pipeline-structured-output-reliability-audit.md:442-490`)
already flagged that skeleton as "a fine ordering/retry skeleton... worth
reviving... not as-is," recommending it be built out properly rather than
reused directly - this item does that at the extractor/backend layer
instead, which is lower and more reusable (every caller of
`JSONPromptExtractor`, not just one pilot script).

### Duplication search
- In-repo: `lcats/pipeline.py`'s `Stage.retries` is the only existing retry
  mechanism in the codebase, confirmed unused (zero importers) and flagged
  by the reliability audit as not fit to reuse as-is (flat 0.5s sleep, no
  exception-type filtering - would retry non-retryable errors too).
  `_classify_api_error`'s `can_retry` labeling is real, tested
  infrastructure this item builds on rather than duplicates.
- Sibling repos: None identified.
- External libraries: None identified.
- Recommendation: Proceed, extending the existing classifier rather than
  building new retryability logic.

### Demand search
- Work items: Surfaced directly by real evidence recorded in
  `WI-EVENT-0030.md`'s Risk Notes (2026-08-22/23 real cost-gate testing).
  `WI-PILOT-0067`'s own stability-gate failure
  (`experiments/03_cross_segment_relation_pilot/results/stability_gate/stability_gate_report.md`)
  was a different, deterministic failure mode (segmentation alignment, not
  transient) and is not addressed or blocked by this item - confirmed by
  reading `WI-PILOT-0067.md`'s `forbidden_actions`, which name
  `implement_prompt_caching_adoption`/`implement_model_tiering_adoption`/
  `implement_batch_api_adoption` specifically, not retry logic.
- Proposals: `PROP-LCATS-PILOT-IMPROVEMENTS` scopes "run-mode ergonomics"
  as this workstream's territory (`WS-PILOT-IMPROVEMENTS.md`'s own
  summary) - this item is exactly that category.
- Backlog: No matching entry found.
- Recommendation: Proceed, filed under `WS-PILOT-IMPROVEMENTS` per that
  workstream's own explicit ownership of "run ergonomics" (its Non-Goals
  in `WS-PILOT-CROSS-SEGMENT-DENSITY.md:109-110` name this territory
  explicitly as *not* that workstream's to implement).

## Scope

- Add `max_retries: int = 0` and `retry_backoff_seconds: float = 1.0`
  constructor parameters to `JSONPromptExtractor`.
- Wrap the backend `complete()` call in a retry loop that reuses
  `_normalize_api_error`'s existing classification: retry only when
  `can_retry: True`, up to `max_retries` additional attempts, with
  exponential backoff between attempts.
- Verify entirely with mocked backends (a raise-N-times-then-succeed stub,
  following the existing `_RaisingBackend` test-helper pattern) - no real
  LLM calls, matching this project's practice of testing the actual named
  mechanism (retry control flow) rather than a real-money proxy.
- Do not wire this into `run_pilot.py`'s CLI or `experiments/03_cross_segment_relation_pilot/`'s
  extractor construction as part of this item - that's a separate,
  smaller follow-up once this lands, to keep this item's own diff focused
  and its acceptance criteria cleanly testable without touching the pilot
  script or its own test suite.

## Required Changes

1. `lcats/src/lcats/analysis/llm_extractor.py`: add `max_retries`/
   `retry_backoff_seconds` constructor parameters (default 0/1.0), a
   `_complete_with_retry()` method wrapping `self.backend.complete()` with
   the retry loop described above, and swap `extract()`'s direct
   `self.backend.complete(...)` call site for it.
2. `lcats/tests/analysis_tests/llm_extractor_test.py`: add a
   `_RetryThenSucceedBackend` test helper and a `TestCompleteWithRetry`
   test class covering: default (`max_retries=0`) behavior is unchanged
   and makes no delay; a retryable error recovered within budget; backoff
   delay sequence (asserted via mocked `time.sleep` call args, not just
   call count); retry exhaustion falling through to the existing
   `api_error` result shape; a non-retryable error never retrying.

## Non-Goals

- Does not wire `max_retries`/`retry_backoff_seconds` into
  `run_pilot.py` or any experiment script's own CLI/extractor
  construction - a real pilot run opting into retries is a separate,
  follow-on item.
- Does not implement prompt caching, model tiering, or Batch API adoption
  - those remain `WS-PILOT-IMPROVEMENTS`' other, separately-gated work
  (`WI-PILOT-0067`'s own resolution: blocked pending follow-on
  segmentation/fixture issues, which this item does not touch).
- Does not modify the Event-Role-World extractor package
  (`lcats/src/lcats/analysis/event_role_world/`) - `llm_extractor.py` and
  its tests are outside that package.
- Does not retry the `empty_response`/`empty_tool_result` cases (a
  successful-but-empty response, not an exception) - those are already
  marked `can_retry: True` by the existing classifier but are a different
  code path this item's exception-based retry loop doesn't naturally
  cover; worth a separate follow-up, not conflated with this fix.
- Does not spend any real API budget - all verification is mocked.

## Acceptance Criteria

(see frontmatter `acceptance:` above)

## Validation

- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh validate`

## Risk Notes

- **Scope creep risk, deliberately fenced off:** `_normalize_api_error`'s
  retryability classification is currently message-text-based (string
  matching "overloaded", "rate limit", etc.) rather than keyed off typed
  SDK exception classes - fragile, but pre-existing and out of this
  item's scope to fix. This item only acts on the existing classification,
  it does not change how errors are classified.
- **This is additive, not a behavior change for existing callers.**
  Default `max_retries=0` makes `_complete_with_retry()` identical to a
  direct `self.backend.complete()` call - zero risk to any code that
  doesn't explicitly opt in.
- If mocked-test verification here doesn't cleanly pass, the correct
  outcome is to report that as a valid negative result (this project's own
  established practice, e.g. `WI-EVENT-0080.md`'s acceptance criteria) -
  not to force a pass.

## Related Workstream and Designs

- Workstream: `lcats/project/workstreams/proposed/WS-PILOT-IMPROVEMENTS.md`
- Work item: `lcats/project/work_items/resolved/WI-PILOT-0067.md` - confirmed
  its blocking failure mode is unrelated to this item's scope
- Work item: `lcats/project/work_items/proposed/WI-EVENT-0030.md` - the real
  evidence that surfaced this gap
