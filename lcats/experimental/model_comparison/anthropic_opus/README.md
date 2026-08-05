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
(`lcats.analysis.event_role_world.entity_extractor`) against a real
~600-word scene/sequel segment (`../common/sample_segment.json`, drawn from
`corpora/sherlock/five_orange_pips/story.json` - see
`../common/generate_sample_segment.py`), with `max_tokens=8192`. At
claude-opus-4-8 pricing this is expected to cost a few cents - confirm
current pricing before running if cost-sensitive.

Earlier runs of this candidate sent the model the *entire* story instead
of a single segment (see `results_fullstory_baseline.json`) - fixed as of
this candidate's current `benchmark.py`/`../common/harness.py`, since
`entity_extractor.py`'s own system prompt describes its input as "a
segment of a story" and the real pipeline (`run_pilot.py`) never calls
this stage with a whole story. Feeding the wrong input size inflated cost
and latency for every candidate, not just weaker ones.

Writes `results.json` in this directory. See `../benchmark_summary.py` to
compare against other candidates.
