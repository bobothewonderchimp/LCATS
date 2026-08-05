---
execution_id: 2026_08_05_04_48_32_ERW_LOCAL_MODEL_EVALUATION
prompt_id: PROMPT(AD_HOC:ERW_LOCAL_MODEL_EVALUATION)[2026-08-05T04:46:31+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/LCATS/pull/219
commit: 770f5068
created_at: 2026-08-05T04:48:32+00:00
agent: claude_app
instruction_source: project/design/proposals/proposed/erw-local-model-evaluation/00_proposal.md
session_transcript: pending
---

# Summary

Evaluate local/hybrid LLM options for `run_pilot.py`'s Event-Role-World
pipeline (currently `claude-opus-4-8`-only, $10-40+ per real run), per
the user's request and the audit's deferred Category E
(`project/audits/2026-07-27-erw-pipeline-structured-output-reliability-audit.md`,
`project/design/backlog.md`'s "never promoted to a proposal" entry).
Scope: survey the current runtime/model landscape, ground it in a real
spike (not benchmark claims alone), and capture the resulting decision as
a `/lrh-proposal`.

# Result

- Surveyed current local-model runtimes (Ollama, vLLM, MLX, llama.cpp) and
  model families (Qwen3, Gemma 4, Llama 4) via web search; flagged most
  "2026 benchmark" search results as unreliable SEO-farm content and
  relied on it only for landscape orientation, not decision evidence.
- Added `base_url` support to `OpenAIBackend`
  (`src/lcats/llm/openai_backend.py`) so any OpenAI-compatible local
  runtime plugs into the existing `LLMBackend` Protocol without a new
  backend class. Covered by
  `tests/llm_tests/openai_backend_test.py::test_constructor_forwards_base_url`.
- Built a reusable benchmark harness at
  `lcats/experimental/model_comparison/` (per the user's explicit
  redirect mid-session to build checked-in infrastructure rather than
  inline one-off code): `common/harness.py` runs the pipeline's real
  stage-3 entity-extraction tool-schema call
  (`lcats.analysis.event_role_world.entity_extractor`) against a fixed
  sample story, with `anthropic_opus`/`ollama_qwen3_8b` candidate
  directories (`setup.py`/`benchmark.py`/`README.md` each) and
  `benchmark_summary.py` to compare `results.json` outputs.
- Installed Ollama (`brew install ollama`) and pulled `qwen3:8b` (~5.2GB)
  on this session's M1 Max/32GB Mac, with explicit user permission
  obtained before both the install and the one billable Anthropic call.
- Ran the real spike: `anthropic_opus` (`claude-opus-4-8`) succeeded —
  202s latency, 14385 input / 7941 output tokens, 28 entities.
  `ollama_qwen3_8b` (`qwen3:8b`) **failed** — `finish_reason='stop'` with
  no tool call at all despite `tool_choice` forcing `extract_entities`;
  Ollama's server logs show ~3699 output tokens generated (likely mostly
  Qwen3's default chain-of-thought "thinking" content) before stopping.
  Both results committed as `results.json` in each candidate's directory.
- Wrote and opened `PROP-ERW-LOCAL-MODEL-EVALUATION`
  (`project/design/proposals/proposed/erw-local-model-evaluation/00_proposal.md`),
  recommending the current default model be held (one local candidate
  tested, and it failed) while defining narrow next evaluation steps.

# Validation

- `python -m pytest tests/llm_tests/ -q` — 40 passed.
- `black --check` / `ruff check` clean on all new/changed files.
- `lrh validate` — no new errors attributable to this PR's files (grepped
  output for the new proposal's id/slug: none).
- Real, non-simulated spike run against both candidates (not a dry run);
  outputs committed as evidence (`results.json` files).

# Follow-up

- Retry `ollama_qwen3_8b` with Ollama's `think` parameter disabled to
  isolate whether "thinking" mode consuming the output budget caused the
  observed failure.
- Add a `qwen3:30b-a3b` (MoE) candidate to test a higher-quality local
  tier against the same stage.
- Extend `common/harness.py` to cover the genre-detection and
  segmentation stages — needed to actually test the hybrid-pipeline
  hypothesis (local for cheap stages, frontier for extraction), which
  this session's entity-extraction-only failure does not settle either
  way.
- No evaluation of the Kubuntu Focus/discrete-NVIDIA hardware profile —
  not available in this session.
