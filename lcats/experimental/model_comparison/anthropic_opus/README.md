# anthropic_opus

Frontier-model baseline candidate for `model_comparison/` - `claude-opus-4-8`
via `lcats.llm.anthropic_backend.AnthropicBackend`, the pipeline's current
default (see `experiments/03_cross_segment_relation_pilot/run_pilot.py`).

## Setup

```bash
python setup.py
```

Checks the `anthropic` package is installed and `ANTHROPIC_API_KEY` is set
(env var or `.secrets/anthropic_api_keys.env`). Makes no API calls.

## Run

```bash
python benchmark.py
```

Makes **one real, billable** Anthropic API call: the ERW pipeline's actual
stage-3 entity-extraction tool-schema call
(`lcats.analysis.event_role_world.entity_extractor`) against
`corpora/sherlock/five_orange_pips/story.json`, with `max_tokens=16384`
(the same ceiling `run_pilot.py` uses). At claude-opus-4-8 pricing this is
expected to cost well under $0.50 for a single ~7K-word story - confirm
current pricing before running if cost-sensitive.

Writes `results.json` in this directory. See `../benchmark_summary.py` to
compare against other candidates.
