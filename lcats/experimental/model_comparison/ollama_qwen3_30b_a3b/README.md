# ollama_qwen3_30b_a3b

Local-model candidate for `model_comparison/` - `qwen3:30b-a3b`, a
mixture-of-experts model (~30B total / ~3B active parameters) served
locally by [Ollama](https://ollama.com), driven through the existing
`lcats.llm.openai_backend.OpenAIBackend` (via its `base_url` parameter,
pointed at Ollama's OpenAI-compatible `/v1` endpoint) rather than a new
backend class - same mechanism as `../ollama_qwen3_8b/`.

The "quality tier" candidate named in
`../../../project/design/proposals/proposed/erw-local-model-evaluation/00_proposal.md`'s
landscape survey: `ollama_qwen3_8b` (the "cheap tier" candidate) succeeds
consistently on the real stage-3 entity-extraction call but extracts
fewer entities than `../anthropic_opus/` (11-14 vs. 21 on the identical
segment). This candidate tests whether the larger MoE model narrows that
gap at a still-acceptable latency.

## Setup

```bash
brew install ollama          # if not already installed
ollama serve                 # or open the Ollama app
ollama pull qwen3:30b-a3b    # ~18-20GB download - confirm current size first
python setup.py              # verifies the above
```

## Run

```bash
python benchmark.py
```

Runs the ERW pipeline's real stage-3 entity-extraction tool-schema call
against the same real ~600-word segment (`../common/sample_segment.json`)
`anthropic_opus` and `ollama_qwen3_8b` use, at `temperature=0.6`
(confirmed via `ollama show qwen3:30b-a3b --parameters` to match Qwen3's
official sampling recommendation, same as `ollama_qwen3_8b`). No API
cost once the model is pulled. Writes `results.json` in this directory
(the most recent run; see `results_run1.json`/`results_run2.json` etc.
for the individual real runs behind the numbers below, following
`ollama_qwen3_8b`'s convention of keeping every run's raw output rather
than only the latest).

A single local-model run is not decision-grade evidence - see
`../ollama_qwen3_8b/README.md`'s "Methodology fix" section and this
repo's own `feedback_local_model_single_run_not_decision_grade` finding
(`qwen3:8b`'s first run against this harness failed outright, while an
identical rerun succeeded at ~8.5x the frontier baseline's latency).
This candidate is run at least twice for the same reason.

## Actual results

**3 real `benchmark.py` runs (`results_run1.json` through `results_run3.json`):**

| Run | Result | Latency | Output tokens | Entities |
|---|---|---|---|---|
| 1 | success (structurally) | 192.1s | 6808 | **1** |
| 2 | **truncated failure** | 218.1s | 8192 (hit ceiling) | - |
| 3 | success (structurally) | 148.2s | 6540 | **1** |

For comparison, on the identical segment: `../anthropic_opus/` succeeds
in 49.3s with 21 entities; `../ollama_qwen3_8b/` succeeds consistently
(3/3) in 74-106s with 11-14 entities.

**This is a real, unexpected, and somewhat concerning finding, not just
a slower/lower-quality result:** the hypothesis this candidate was meant
to test - that a larger MoE model would narrow `qwen3:8b`'s entity-recall
gap - is **not supported**. `qwen3:30b-a3b` is *less* reliable than the
smaller dense model on this exact call, not more. 2 of 3 runs technically
"succeeded" (no `api_error`, a schema-conformant tool call) but returned
essentially empty results - inspecting the actual tool-call arguments for
one of these runs (not saved as a committed artifact, a direct
`extractor.extract()` call outside `benchmark.py`'s normal path, done to
diagnose the pattern) showed the model calling `extract_entities` with a
single field literally named `segment` containing the entire input text
echoed back verbatim - not populating the `entities` array the schema
requires at all. A separate, similarly ad-hoc diagnostic call (also not
committed) did succeed with a full, correct 13+-entity list in 158s,
confirming the model *can* do the task correctly - it just does so
inconsistently, more so than `qwen3:8b` at the same settings
(`temperature=0.6`, confirmed via `ollama show qwen3:30b-a3b
--parameters` to match Qwen3's own official recommendation, ruling out
the same temperature-mismatch root cause that explained `qwen3:8b`'s
earlier unreliability - see PR #223).

**Interpretation, not conclusively diagnosed here:** this looks like a
different failure mode than `qwen3:8b`'s original (Ollama's `tool_choice`
forcing possibly not being honored, per `WI-LLM-0051`) - here the tool
*is* being called, just with wrong or minimal arguments some of the
time. Root-causing this (thinking-mode budget exhaustion producing a
"give up and echo the input" fallback? a MoE-routing-specific
instability at this quantization? something else?) is out of this work
item's scope - see `WI-LLM-0051` for the adjacent, still-open
`tool_choice`-reliability investigation, and consider filing a follow-on
item specifically for this "succeeds but returns near-empty results"
failure mode if it recurs.

**Bottom line:** on this evidence, `qwen3:30b-a3b` should **not** be
treated as a drop-in "quality tier" upgrade over `qwen3:8b` - it is both
slower (148-218s vs. 74-106s) and less reliable in this session's 3 real
runs. `qwen3:8b` remains the more dependable local candidate tested so
far.
