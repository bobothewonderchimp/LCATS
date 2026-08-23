---
execution_id: 2026_08_23_05_23_34_WI_EVENT_0030_GENRE_EXTENSION_COST_GATE_REVIEW
prompt_id: PROMPT(AD_HOC:WI_EVENT_0030_GENRE_EXTENSION_COST_GATE_REVIEW)[2026-08-23T05:22:59+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/LCATS/pull/367
commit: 5be417de
agent: claude_app
instruction_source: https://github.com/xenotaur/LCATS/pull/367
session_transcript: claude-app:e8e46d5d-35d3-4ccc-9cba-137bd31bf3a5
created_at: 2026-08-23T05:23:34+00:00
---

# Summary

Address six open review comments on PR #367 (8-genre pilot extension,
max_tokens fix confirmation, retry-gap finding, formal-gate reconciliation
on WI-EVENT-0030). No primary implementation execution record exists for
this PR - this is the first execution record authored against it.

# Result

Two P1s, two P2s, and two stale-reference findings, all confirmed real
before fixing (not accepted from review text alone):

**P1 - per-model max_tokens ceiling (chatgpt-codex-connector):**
`_ERW_MAX_TOKENS` was applied uniformly regardless of backend/model.
Independently confirmed via
`lcats/experimental/model_comparison/wi_llm_0059/run_frontier_paired.py:51-55`
that gpt-4o's real hard maximum is 16384 completion tokens (a quoted real
API rejection already in the repo) - well below the 32768 this PR's prior
commit set unconditionally, which would make every `--backend openai`
call fail before extraction. Added `_max_tokens_for_model()` and
`_MAX_TOKENS_CEILING_BY_MODEL_PREFIX` (same prefix-match convention as
this project's existing pricing dicts in `run_census.py`/
`run_prefilter.py`), wired into `_build_erw_extractors` so each stage's
own resolved model gets its own correct cap.

**P1 - default stratified-scan mode uses wrong methodology
(chatgpt-codex-connector):** confirmed by reading `build_stratified_sample()`
directly: the default (no `--story`/`--story-list`) mode still
independently classifies each candidate via a fresh `assess_story()`
call, not WI-EVENT-0030's required validated-manifest exact-match
selection, and has no per-genre cap. Extending `GENRES` to 8 for this
mode would have made a `--sample-size` run against adventure (only 6
stories exist corpus-wide) exit incomplete. Split into a new
`_STRATIFIED_SCAN_GENRES` (kept at the original 4 genres) for this scan
mode specifically, distinct from `GENRES` (all 8), which now scopes only
to `--story`/`--story-list` targeted mode's `--genre` choices, manifest
validation, and output aggregation - the mode this PR's own real cost-gate
testing actually exercised and verified.

**P2 (chatgpt-codex-connector) + P2 (copilot-pull-request-reviewer) -
same underlying gap, two angles:** adventure's docstring-claimed cap
wasn't implemented in code. Resolved by the `_STRATIFIED_SCAN_GENRES`
split above (adventure is now simply absent from the default scan mode's
strata, not present-but-uncapped); updated the module docstring to
describe both modes' real, now-accurate scope and each mode's respective
responsibility for the exact-match/cap requirements.

**Stale reference (copilot-pull-request-reviewer) x2:** fixed
`WI-EVENT-0030.md`'s `run_pilot.py:184` citation (symbol name instead,
per the reviewer's own suggestion - line numbers are fragile) and the
now-outdated "16384" reference in
`lcats/experimental/model_comparison/common/harness.py`'s historical
comment (updated to note the value changed, PR #367, without erasing the
original historical narrative).

# Validation

- `scripts/format --check --diff`, `scripts/lint` - clean
- `scripts/test` - 1856 tests, OK (36 -> 44 in `run_pilot_test.py`
  specifically: 8 new tests covering `_max_tokens_for_model()`'s per-model
  ceilings, `_build_erw_extractors`'s per-stage application, and
  `_STRATIFIED_SCAN_GENRES`'s scope)
- `lrh validate` - 0 errors, 187 warnings (pre-existing baseline,
  unrelated)
- Both P1 findings independently re-verified against real evidence before
  fixing: read `run_frontier_paired.py:51-55`'s quoted API rejection
  directly, and read `build_stratified_sample()`'s own source to confirm
  it uses independent `assess_story()` classification, not the validated
  manifest

# Follow-up

- Suggest running `/lrh-confirm-fixes` (inlined as `/lrh-land` Step 5)
  against the current HEAD to verify these fixes and resolve the review
  threads before merge.
- A real, separately-scoped follow-up remains: extending
  `build_stratified_sample()` itself to read WI-GENRE-0004's validated
  manifest and cap adventure explicitly, so the default scan mode can
  also support all 8 genres correctly - not implemented here, per the
  module docstring's own note.
- `session_transcript` above uses the host session ID with its `local_`
  prefix stripped; update if a more durable pointer becomes available.
