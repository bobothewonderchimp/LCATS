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

## Setup (not yet run - explicit opt-in)

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
is pulled. Writes `results.json` in this directory.

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
