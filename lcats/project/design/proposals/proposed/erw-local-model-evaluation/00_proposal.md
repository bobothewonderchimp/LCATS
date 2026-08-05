---
id: PROP-ERW-LOCAL-MODEL-EVALUATION
type: design_proposal
title: Local/Hybrid Model Evaluation Infrastructure for the Event-Role-World Pipeline
status: proposed
created_on: 2026-08-05
updated_on: 2026-08-05
implementation_status: partial
implemented_by: []
supersedes: []
superseded_by: null
related_design:
  - lcats/project/audits/2026-07-27-erw-pipeline-structured-output-reliability-audit.md
  - lcats/project/design/backlog.md
  - lcats/experiments/03_cross_segment_relation_pilot/run_pilot.py
  - lcats/experimental/model_comparison/README.md
  - lcats/project/design/proposals/adopted/lcats-pipeline-checkpointing/00_proposal.md
---

## Summary

This proposal promotes the audit's deferred Category E ("local model
options") to a real design decision. It adopts (a) reusing the existing
`LLMBackend` Protocol plus a `base_url` addition to `OpenAIBackend` -
rather than a new backend class - as how any OpenAI-compatible local
runtime (Ollama, vLLM, LM Studio) plugs into the pipeline, and (b) a
checked-in benchmarking harness (`lcats/experimental/model_comparison/`)
as the durable, reusable way to evaluate model/runtime candidates against
the pipeline's real tool-schema calls going forward. Based on one real
spike run against that harness, it explicitly recommends **against**
changing `run_pilot.py`'s default model yet - the sole local candidate
tested so far failed outright - and defines the narrow next evaluation
steps required before a hybrid (local-for-cheap-stages,
frontier-for-extraction) pipeline can be seriously considered.

## Background / Motivation

`experiments/03_cross_segment_relation_pilot/run_pilot.py` defaults to
`claude-opus-4-8` via `lcats.llm.anthropic_backend.AnthropicBackend` for
every stage: genre detection, scene/sequel segmentation, and the four ERW
extractor calls (entity/event/relation/discourse) plus a story-level
cross-segment-relation pass. Real runs have cost $10-40+ each, which is
not sustainable for a script meant to be run repeatedly during iteration,
let alone for the full 5-10-per-genre research runs it exists to
eventually support.

`project/audits/2026-07-27-erw-pipeline-structured-output-reliability-audit.md`'s
Category E raised this cost concern and specifically flagged local models
as an unvalidated cost-reduction lever: a colleague's report (Kenny, using
Ollama for conversational Llama 3/Gemma use, not coding/structured
extraction) that local models "historically had much weaker/inconsistent
tool-calling and structured-output support than Anthropic's or OpenAI's
mature APIs." The audit's own recommendation was "a cheap, targeted spike
- run one story through the actual tool-schema path against a local
Ollama model - before investing further, rather than assuming it's a
viable cost-reduction lever untested." `project/design/backlog.md`'s "ERW
pipeline audit's Category E ... never promoted to a proposal" entry left
this unscoped pending that spike. `WI-PIPELINE-0041`
(`lcats-pipeline-checkpointing`, adopted and resolved) already addressed
the audit's separate checkpointing/resumability gap; this proposal
addresses the remaining local-model piece only.

This session ran that spike for real (not simulated) - see Design
Decisions below - and it produced a concrete, actionable result: the one
local candidate tested failed the exact call the pipeline depends on.

## Prior Art Check

### Duplication search
- In-repo: No existing local-model backend or benchmarking harness found.
  `src/lcats/llm/openai_backend.py` already existed (OpenAI chat
  completions adapter) and is directly reusable for any OpenAI-compatible
  local runtime once given a `base_url` override - see Design Decision 1.
- Sibling repos: None identified.
- External libraries: None identified as a wholesale replacement -
  Ollama/vLLM/LM Studio are runtimes to point the existing abstraction at,
  not libraries that replace `LLMBackend` itself.
- Recommendation: Proceed.

### Demand search
- Work items: None found requesting this directly; `WI-EVENT-0032`/
  `WI-EVENT-0033` cover tool-schema hardening (Categories A-D of the same
  audit), not local-model evaluation.
- Proposals: None found.
- Backlog: Found - `project/design/backlog.md`'s "ERW pipeline audit's
  Category E (cost/checkpointing/local-model options) never promoted to a
  proposal" entry (P3) directly requests this. This proposal satisfies its
  local-model portion (the checkpointing portion is already resolved via
  `PROP-LCATS-PIPELINE-CHECKPOINTING`).
- Recommendation: Offer to close/update that backlog entry once this
  proposal is adopted.

## Design Decisions

### Decision 1: How a local/OpenAI-compatible runtime plugs into the pipeline

Options considered:
- A new `OllamaBackend` class - explicit, but duplicates nearly all of
  `OpenAIBackend`'s translation logic (Ollama's `/v1/chat/completions`
  endpoint is OpenAI-compatible), and would need a sibling for every other
  OpenAI-compatible local server (vLLM, LM Studio) that shows up.
- Extend `OpenAIBackend` with an optional `base_url` constructor
  parameter, defaulting to `None` (unchanged, real OpenAI API behavior).

**Chosen: extend `OpenAIBackend` with `base_url`.** One local runtime
already satisfies the "point an existing OpenAI-shaped client at a
different host" case for every OpenAI-API-compatible server (confirmed for
Ollama in this session; vLLM and LM Studio advertise the same
compatibility). No new class, no new Protocol implementation, no new
tests beyond confirming the parameter forwards correctly. Implemented in
this session: `src/lcats/llm/openai_backend.py`'s `OpenAIBackend.__init__`
now accepts `base_url`, with a covering test
(`tests/llm_tests/openai_backend_test.py::test_constructor_forwards_base_url`).
`strict: true` tool-schema forwarding (`tool.get("strict", False)` into
the OpenAI function schema) was already present and required no change.

### Decision 2: Where evaluation infrastructure lives and how it's shaped

Options considered:
- Inline, ad-hoc scripts written per-evaluation and discarded - fast but
  not reusable, and this exact "should we trust a cheaper model" question
  will recur every time a new model family ships.
- `lcats/notebooks/` - this repo's existing convention for exploratory
  `.ipynb` work, but not meant to be re-run as a checked, comparable suite.
- `lcats/KMo/` - a collaborator's separate test code; wrong owner/purpose
  for pipeline-internal benchmarking.
- A new `lcats/experimental/` directory (following the `experimental/`
  convention used by large codebases for real, runnable code not yet
  ready for production dependency status), with one subdirectory per
  candidate model/backend, a shared harness module, and a summary script.

**Chosen: `lcats/experimental/model_comparison/`,** built in this session:
- `common/harness.py` - shared logic that runs the ERW pipeline's actual
  stage-3 entity-extraction tool-schema call
  (`lcats.analysis.event_role_world.entity_extractor.make_entity_extractor`,
  the same strict schema and `extract()` call path `run_pilot.py` uses,
  not a synthetic schema) against a fixed sample story
  (`corpora/sherlock/five_orange_pips/story.json`), and records
  success/failure, latency, token counts, and entity count to
  `results.json`.
- One directory per candidate (`anthropic_opus/`, `ollama_qwen3_8b/`),
  each with `README.md` (setup/cost/what a good-or-bad result means),
  `setup.py` (prerequisite check only - never downloads/installs
  anything itself), and `benchmark.py` (builds that candidate's
  `LLMBackend` and calls the shared harness).
- `benchmark_summary.py` - aggregates every candidate's `results.json`
  into one comparison table.

Adding a new candidate model or runtime means adding one new directory
following this shape, not writing a new one-off script each time.

### Decision 3: Whether to change `run_pilot.py`'s default model now

Options considered:
- Switch the default to a local model for at least the cheaper stages
  (genre detection, segmentation) now, based on general local-model
  tool-calling improvements found in the landscape survey.
- Hold the current default (`claude-opus-4-8`) and treat this proposal as
  infrastructure-only, pending more evaluation.

**Chosen: hold the current default.** The real spike run in this session
(candidate `ollama_qwen3_8b`, model `qwen3:8b` served by Ollama 0.32.5 on
an Apple M1 Max/32GB Mac, via `OpenAIBackend(base_url="http://localhost:11434/v1")`)
**failed**: despite `tool_choice` forcing the `extract_entities` function,
the response came back with `finish_reason='stop'` and no tool call at
all. Ollama's server logs show it generated 3699 output tokens (most
likely Qwen3's default chain-of-thought "thinking" content) over ~252
seconds before stopping without ever invoking the tool. The
`claude_opus` baseline candidate, run against the identical call in the
same session, succeeded (202s latency, 14385 input / 7941 output tokens,
28 entities extracted).

This is one data point on the hardest stage (entity extraction, not the
"comparatively simple" genre-detection/segmentation stages flagged as
better hybrid candidates) for one model at one size, with one untested
and likely-relevant confound (Qwen3's "thinking" mode was not disabled -
Ollama's `think` API parameter is a plausible one-line fix not yet
tried). It is real evidence that the audit's flagged concern is not
hypothetical on this pipeline's actual call shape, but it is not enough
evidence to justify a pipeline-wide or even single-stage default change.
The hybrid-pipeline hypothesis (cheap local model for genre
detection/segmentation, frontier model retained for
entity/event/relation/discourse extraction and the cross-segment pass) is
still plausible and consistent with this result, but unproven - it needs
its own spike (a local model tested against the genre-detection or
segmentation stage specifically) before being adopted, not inferred from
a failure on a different, harder stage.

### Landscape context (not itself decision-grade evidence)

A web survey (Aug 2026) of runtimes and models informs which candidates to
add next, but most "2026 benchmark" search results were SEO-farm content
with suspiciously precise, unverifiable numbers - treated as orientation
only, not cited as justification for any decision above:

- Ollama and vLLM both have first-class OpenAI-compatible tool-calling
  support; Ollama additionally does grammar-constrained JSON-schema
  decoding (XGrammar-backed since 0.3+) - the closest local analogue to
  `strict: true`, though this session's spike shows constrained decoding
  alone did not stop the model from simply never calling the tool.
- MLX (`mlx-lm`, Apple-Silicon-native) has native tool-calling support
  too, and several OpenAI-compatible-server wrappers exist for it - an
  unexplored alternative to Ollama on Apple Silicon specifically.
- Qwen3 ships Ollama-library sizes from 0.6b to 235b; `30b-a3b` (a
  mixture-of-experts model, ~30B total/~3B active parameters) is a
  plausible "quality tier" candidate for extraction-grade stages, not yet
  tested. Similar tiers exist for Gemma 4 and Llama 4.
- The two target hardware profiles differ meaningfully: Apple Silicon
  unified memory (tested here, M1 Max/32GB) versus a Kubuntu Focus
  laptop's discrete NVIDIA GPU (not available in this session - untested,
  and its VRAM-bound sweet spot likely differs from the Mac's).

## Non-Goals

- Does not change `run_pilot.py`'s default model or add a `--backend
  local`/similar flag - see Decision 3.
- Does not implement a fix for the observed `qwen3:8b` failure (e.g.
  disabling Ollama's `think` parameter) - flagged as the immediate next
  step, not done here.
- Does not evaluate the Kubuntu Focus/NVIDIA hardware profile - not
  available in this session.
- Does not extend the benchmark harness to the genre-detection,
  segmentation, event/relation/discourse, or cross-segment-relation
  stages - only stage-3 entity extraction is covered so far.
- Does not perform a quality (precision/recall against ground truth)
  comparison - the harness currently only checks call success and a crude
  entity-count sanity signal, not correctness of what was extracted.

## Implementation Plan

Already done in this session (this PR):
1. `OpenAIBackend.base_url` support + test
   (`src/lcats/llm/openai_backend.py`,
   `tests/llm_tests/openai_backend_test.py`).
2. `lcats/experimental/model_comparison/` harness, `anthropic_opus` and
   `ollama_qwen3_8b` candidates, `benchmark_summary.py`.
3. One real spike run per candidate (results committed as each
   candidate's `results.json`).

Follow-on work (proposed as separate work items once this proposal is
adopted - offered at the end of this skill run):
1. Retry `ollama_qwen3_8b` with Ollama's `think` parameter disabled, to
   isolate whether "thinking" mode consuming the output budget was the
   actual cause of the observed failure.
2. Add an `ollama_qwen3_30b_a3b` candidate (MoE, higher quality ceiling)
   to test whether a larger local model clears the same bar.
3. Extend `common/harness.py` to cover the genre-detection and
   segmentation stages, and add a candidate run against those - this is
   the evidence needed to actually assess the hybrid-pipeline hypothesis,
   which entity-extraction failure alone does not settle either way.
4. Only after (1)-(3) produce a passing local candidate on at least one
   stage: revisit Decision 3 in a follow-on proposal or amendment.

## Cross-References

- `lcats/project/audits/2026-07-27-erw-pipeline-structured-output-reliability-audit.md`
  (Category E, this proposal's origin)
- `lcats/project/design/backlog.md` ("ERW pipeline audit's Category E ...
  never promoted to a proposal")
- `lcats/experimental/model_comparison/README.md` (the harness this
  proposal documents)
- `lcats/experiments/03_cross_segment_relation_pilot/run_pilot.py` (the
  pipeline this evaluation targets)

## Open Questions

- Does Ollama's `think: false` API parameter actually resolve the
  observed `qwen3:8b` failure, or is there a deeper tool-choice-forcing
  gap in Ollama's OpenAI-compatibility layer? (Next spike, see
  Implementation Plan #1.)
- Is MLX (native Apple Silicon) meaningfully more reliable than
  Ollama/llama.cpp for this pipeline's tool-schema calls? Not yet tested.
- What is the actual VRAM-bound model-size sweet spot on the Kubuntu Focus
  hardware profile? Not testable in this session; needs a run on that
  machine.
