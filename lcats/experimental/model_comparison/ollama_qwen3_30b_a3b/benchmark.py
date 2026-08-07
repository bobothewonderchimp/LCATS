"""Local-model candidate: qwen3:30b-a3b served by Ollama's OpenAI-compatible API.

A mixture-of-experts model (~30B total / ~3B active parameters) - the
"quality tier" candidate named in PROP-ERW-LOCAL-MODEL-EVALUATION's
landscape survey, tested here against the same real segment/schema
anthropic_opus and ollama_qwen3_8b already use, to see whether it
narrows ollama_qwen3_8b's entity-recall gap (11-14 vs. claude-opus-4-8's
21) at a still-acceptable latency.

Run setup.py first - it confirms Ollama is running and the model is
pulled. This candidate is free to run repeatedly (no per-call API cost)
once the model is downloaded once.

Uses lcats.llm.openai_backend.OpenAIBackend pointed at Ollama's
OpenAI-compatible endpoint via base_url - no separate backend class needed
(see lcats/src/lcats/llm/openai_backend.py's base_url parameter).

Usage:
    python lcats/experimental/model_comparison/ollama_qwen3_30b_a3b/benchmark.py
"""

from __future__ import annotations

import pathlib
import sys

_HERE = pathlib.Path(__file__).resolve().parent
_MODEL_COMPARISON = _HERE.parent
sys.path.insert(0, str(_MODEL_COMPARISON))

from common import harness  # noqa: E402
from lcats.llm import openai_backend  # noqa: E402

MODEL = "qwen3:30b-a3b"
OLLAMA_BASE_URL = "http://localhost:11434/v1"

# `ollama show qwen3:30b-a3b --parameters` (checked at implementation
# time) reports the same temperature=0.6/top_k=20/top_p=0.95 bundled
# default as the 8B dense model - Qwen3's official sampling
# recommendation (https://huggingface.co/Qwen/Qwen3-8B) applies
# uniformly across the family's thinking-mode variants, dense and MoE
# alike, not just the 8B size. See ollama_qwen3_8b/benchmark.py's
# identical comment for the full rationale (why not the pipeline's
# default 0.2).
TEMPERATURE = 0.6


def main() -> None:
    # Ollama's OpenAI-compatible endpoint ignores the API key but the SDK
    # still requires a non-empty string.
    backend = openai_backend.OpenAIBackend(api_key="ollama", base_url=OLLAMA_BASE_URL)
    result = harness.run_entity_extraction(
        candidate="ollama_qwen3_30b_a3b",
        backend_kind="openai_compatible_local",
        backend=backend,
        model=MODEL,
        temperature=TEMPERATURE,
    )
    out_path = harness.save_result(result, _HERE)
    print(f"Wrote {out_path}")
    print(result.to_dict())


if __name__ == "__main__":
    main()
