# ollama_qwen3_8b

Local-model candidate for `model_comparison/` - `qwen3:8b` served locally by
[Ollama](https://ollama.com), driven through the existing
`lcats.llm.openai_backend.OpenAIBackend` (via its `base_url` parameter,
pointed at Ollama's OpenAI-compatible `/v1` endpoint) rather than a new
backend class.

Sized for ~8GB of RAM/VRAM headroom - the "cheap tier" candidate a hybrid
pipeline (local model for genre detection/segmentation, frontier model for
extraction) would use. See `../ollama_qwen3_30b_a3b/` (not yet built) for
the "quality tier" MoE candidate sized for extraction-grade stages.

## Setup

```bash
brew install ollama
ollama serve            # or open the Ollama app
ollama pull qwen3:8b    # ~5GB download
python setup.py         # verifies the above
```

## Run

```bash
python benchmark.py
```

Runs the ERW pipeline's real stage-3 entity-extraction tool-schema call
against a real ~600-word scene/sequel segment (`../common/sample_segment.json`
- see `../common/generate_sample_segment.py` for how it was produced),
`temperature=0.6` (Qwen3's own recommended value - see "Methodology fix"
below), `max_tokens=8192`. No API cost once the model is pulled. Writes
`results.json` in this directory (the most recent run; see
`results_segment_run1.json`/`run2.json`/`run3.json` for three real runs
against the corrected methodology, and `results_fullstory_run1_failed.json`/
`results_fullstory_run2_succeeded.json` for the two runs against the prior,
oversized whole-story input - kept for transparency, not representative of
current results).

## What this tests

Whether Ollama's grammar-constrained JSON-schema decoding (XGrammar-backed
since Ollama 0.3+) actually produces a valid, schema-conformant
`extract_entities` tool call for a real story segment - the same question
Categories A-C of
`project/audits/2026-07-27-erw-pipeline-structured-output-reliability-audit.md`
raised for hosted backends, now asked of a local one. A local model
excelling at conversational chat but failing this call (empty/malformed
`tool_result`, wrong entity count, hallucinated schema fields) would rule
it out for the pipeline's extraction stages specifically, even if it's fine
for lighter stages like genre detection.

## Methodology fix (this candidate's first two runs were measuring the wrong thing)

The first two runs against this candidate (`results_fullstory_run1_failed.json`,
`results_fullstory_run2_succeeded.json`) sent the model the **entire**
~7,300-word source story instead of a single segment, at
`temperature=0.2` - a setting inherited from `entity_extractor.py`'s
Anthropic/OpenAI-tuned default, well below Qwen3's own official
recommendation (0.6 thinking-mode / 0.7 non-thinking - see
[Qwen3-8B's model card](https://huggingface.co/Qwen/Qwen3-8B), which
explicitly warns **"Do NOT use greedy decoding, as it can lead to
performance degradation and endless repetitions"**) and below Ollama's
own bundled default for this model (`ollama show qwen3:8b --parameters`
reports `temperature 0.6, top_k 20, top_p 0.95` - i.e. our own explicit
`temperature=0.2` was overriding an already-correct default). Both
issues are fixed as of this candidate's current `benchmark.py`/`../common/harness.py`.

## Actual results

**Fixed methodology (real segment, `temperature=0.6`), 3 runs:**

| Run | Result | Latency | Output tokens | Entities |
|---|---|---|---|---|
| 1 | success | 74.4s | 1477 | 11 |
| 2 | success | 100.3s | 2318 | 13 |
| 3 | success | 105.7s | 2301 | 14 |

`../anthropic_opus/` on the identical segment: success, 49.3s, 5439
output tokens, 21 entities. So on the corrected methodology, `qwen3:8b`
succeeds consistently (3/3) at roughly **1.5-2.2x** Opus's latency, with
lower recall (11-14 vs. 21 entities - not evaluated for precision here,
see Non-Goals) - a real cost/latency tradeoff, not the outright
unreliability the prior methodology suggested.

**Prior methodology (whole story, `temperature=0.2`), for comparison -
not representative of current results:**

- Run 1: **failed** - `finish_reason='stop'` with no tool call at all,
  despite `tool_choice` forcing `extract_entities`.
- Run 2: **succeeded**, but took 1727s (~29 minutes) generating 7996
  output tokens before finally producing a valid call.

This reversal is itself the finding: the original "qwen3:8b is
unreliable" conclusion in
`project/design/proposals/proposed/erw-local-model-evaluation/00_proposal.md`
was substantially an artifact of benchmarking against the wrong input
size and an unsuited sampling temperature, not a stable property of the
model. See that proposal's "Update" section for the corrected
conclusion. One remaining, unfixed candidate cause of the *original*
run 1's total non-call: community reports on Ollama's own GitHub
(e.g. [issue #4386](https://github.com/ollama/ollama/issues/4386))
describe gaps in how Ollama's OpenAI-compatible `tool_choice` forces a
specific function name - not reproduced across 3 fixed-methodology runs
here, but not ruled out as a residual risk either.
