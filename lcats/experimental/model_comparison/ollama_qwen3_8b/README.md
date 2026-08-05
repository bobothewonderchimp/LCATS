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
(same schema, same story, same `max_tokens=16384` ceiling as
`../anthropic_opus/`) against the local model. No API cost once the model
is pulled. Writes `results.json` in this directory (the most recent run;
see `results_run1_failed.json`/`results_run2_succeeded.json` for the two
real runs behind the numbers below).

## What this tests

Whether Ollama's grammar-constrained JSON-schema decoding (XGrammar-backed
since Ollama 0.3+) actually produces a valid, schema-conformant
`extract_entities` tool call for a real, content-dense story - the same
question Categories A-C of
`project/audits/2026-07-27-erw-pipeline-structured-output-reliability-audit.md`
raised for hosted backends, now asked of a local one. A local model
excelling at conversational chat but failing this call (empty/malformed
`tool_result`, wrong entity count, hallucinated schema fields) would rule
it out for the pipeline's extraction stages specifically, even if it's fine
for lighter stages like genre detection.

## Actual results (two runs, identical input)

- **Run 1: failed.** `finish_reason='stop'` with no tool call at all,
  despite `tool_choice` forcing `extract_entities` - Ollama's logs show
  ~3699 output tokens generated (likely chain-of-thought "thinking"
  content) over ~259s before stopping without ever calling the tool.
- **Run 2: succeeded**, but took **1727s (~29 minutes)** - ~8.5x
  `../anthropic_opus/`'s 202s - generating 7996 output tokens before
  finally producing a valid call (20 entities, vs. `claude-opus-4-8`'s
  28).

Same model, same story, same schema, two different outcomes: `qwen3:8b`
via Ollama is not just slower than the frontier baseline, it is
*unreliable* on this exact call shape. See
`project/design/proposals/proposed/erw-local-model-evaluation/00_proposal.md`
Decision 3 for the resulting recommendation (hold the current default;
Qwen3's default "thinking" mode is the leading suspect and worth testing
with `think: false` before drawing further conclusions).
