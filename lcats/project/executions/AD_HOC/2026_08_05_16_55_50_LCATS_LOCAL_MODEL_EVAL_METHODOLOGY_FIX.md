---
execution_id: 2026_08_05_16_55_50_LCATS_LOCAL_MODEL_EVAL_METHODOLOGY_FIX
prompt_id: PROMPT(AD_HOC:LCATS_LOCAL_MODEL_EVAL_METHODOLOGY_FIX)[2026-08-05T16:54:31+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/LCATS/pull/223
commit: b40a352f
created_at: 2026-08-05T16:55:50+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/LCATS/pull/223
session_transcript: claude-app:6d988910-ee4a-4ccc-af0b-2fb13d91ddc5
---

# Summary

Follow-up to PR #219 (PROP-ERW-LOCAL-MODEL-EVALUATION): the user asked
whether the benchmark harness itself was setting `qwen3:8b` (and even
`claude-opus-4-8`) up to fail, calling out oversized benchmark input as
"critically important" since it would produce both inaccurate results and
unnecessarily expensive calls. Reviewed the actual prompts/call structure
grounded in repo code and Ollama's own logs/config, found and fixed two
real problems, and re-ran the benchmark to test the corrected hypotheses.

# Result

Findings (all grounded in file:line citations or live inspection, not
speculation):

1. **Wrong input size** (`experimental/model_comparison/common/harness.py`
   previously): fed `entity_extractor.py`'s tool-schema call the entire
   ~7,300-word story, though its own system prompt says "a segment of a
   story" and the real pipeline (`run_pilot.py`) never passes more than
   one segment. Fixed via a new `common/generate_sample_segment.py` (runs
   the real stage-1 segmenter once, one real Anthropic call) producing
   `common/sample_segment.json` (a real ~600-word `dramatic_sequel`
   segment), now the fixed benchmark input.
2. **Wrong sampling temperature**: harness sent `temperature=0.2`
   (`entity_extractor.py`'s Anthropic/OpenAI-tuned default) to every
   candidate. `ollama show qwen3:8b --parameters` reports Ollama's own
   bundled default as `temperature=0.6/top_k=20/top_p=0.95`, matching
   Qwen3's official Hugging Face model card recommendation, which warns
   against near-greedy decoding causing "endless repetitions."
   `ollama_qwen3_8b/benchmark.py` now overrides `temperature=0.6`.
3. Also fixed: `BenchmarkResult` never captured raw model text
   (undiagnosable failures without a live rerun) - added
   `raw_output_preview`. `DEFAULT_MAX_TOKENS` retuned 16384→8192 (4096,
   the extractor's own factory default, truncated even Opus on the
   smaller segment).
4. A third candidate cause (Ollama `tool_choice` forced-function-name
   gaps, per community GitHub reports) was investigated but not
   reproduced across 3 fixed-methodology runs - left as an open question,
   not claimed fixed.
5. Corrected an earlier session's "Qwen3 thinking mode" hypothesis
   (already merged into the proposal) - `ollama show qwen3:8b --modelfile`
   shows Ollama uses a proper Qwen3-aware template, not a broken generic
   one, so that hypothesis is retracted as unsupported, not confirmed.

Re-ran `ollama_qwen3_8b` 3 consecutive times against the corrected
methodology: all 3 succeeded (74.4s/1477 tokens/11 entities, 100.3s/2318/
13, 105.7s/2301/14), vs. `claude-opus-4-8`'s 49.3s/5439/21 on the
identical segment - qwen3:8b now succeeds consistently at ~1.5-2.2x
Opus's latency, reversing the original "1 failure, 1 slow success"
verdict. `PROP-ERW-LOCAL-MODEL-EVALUATION` updated with a dated "Decision
3 update" section; recommendation to hold the current default model is
unchanged but now rests on materially stronger evidence. Original
whole-story results kept as `results_fullstory_*.json`, not deleted.

# Validation

- `python -m pytest tests/llm_tests/ -q` - 40 passed.
- `black --check` / `ruff check` clean, using the CI-pinned versions
  (`black==25.11.0`, `ruff==0.15.0` from `.github/workflows/lint.yml`) -
  the ambient environment had drifted to newer versions.
- `lrh validate` - 0 errors, no new warnings attributable to this PR's
  files.
- 3 real, non-simulated re-runs against the corrected methodology (not a
  dry run); all outputs committed as evidence.

# Follow-up

Same open items as PR #219's follow-up, refined:
- Investigate the residual Ollama `tool_choice` forced-function-name gap
  further if it recurs (not reproduced in 3 runs here, not ruled out).
- Add a `qwen3:30b-a3b` (MoE) candidate to test whether a larger local
  model narrows the entity-recall gap (11-14 vs. Opus's 21).
- Extend `common/harness.py` to the genre-detection/segmentation stages -
  still the evidence needed to assess the hybrid-pipeline hypothesis.
- Quality (precision/recall against ground truth) comparison, not just
  call-success/entity-count - explicitly out of scope here (see the
  proposal's Non-Goals).
