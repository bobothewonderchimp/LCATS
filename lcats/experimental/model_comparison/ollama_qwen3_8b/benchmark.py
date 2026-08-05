"""Local-model candidate: qwen3:8b served by Ollama's OpenAI-compatible API.

Run setup.py first - it confirms Ollama is running and the model is pulled.
This candidate is free to run repeatedly (no per-call API cost) once the
model is downloaded once.

Uses lcats.llm.openai_backend.OpenAIBackend pointed at Ollama's
OpenAI-compatible endpoint via base_url - no separate backend class needed
(see lcats/src/lcats/llm/openai_backend.py's base_url parameter).

Usage:
    python lcats/experimental/model_comparison/ollama_qwen3_8b/benchmark.py
"""

from __future__ import annotations

import pathlib
import sys

_HERE = pathlib.Path(__file__).resolve().parent
_MODEL_COMPARISON = _HERE.parent
sys.path.insert(0, str(_MODEL_COMPARISON))

from common import harness  # noqa: E402
from lcats.llm import openai_backend  # noqa: E402

MODEL = "qwen3:8b"
OLLAMA_BASE_URL = "http://localhost:11434/v1"

# `ollama show qwen3:8b --parameters` reports Ollama's own bundled default
# for this model as temperature=0.6, top_k=20, top_p=0.95 - matching
# Qwen3's official model card recommendation for thinking-mode inference
# (https://huggingface.co/Qwen/Qwen3-8B), which also explicitly warns:
# "Do NOT use greedy decoding, as it can lead to performance degradation
# and endless repetitions." harness.DEFAULT_TEMPERATURE (0.2, inherited
# from entity_extractor.py's Anthropic/OpenAI-tuned default) is much
# closer to greedy than to that recommendation, so this candidate
# overrides it back to Qwen3's own documented value instead of silently
# inheriting a setting tuned for a different model family.
TEMPERATURE = 0.6


def main() -> None:
    # Ollama's OpenAI-compatible endpoint ignores the API key but the SDK
    # still requires a non-empty string.
    backend = openai_backend.OpenAIBackend(api_key="ollama", base_url=OLLAMA_BASE_URL)
    result = harness.run_entity_extraction(
        candidate="ollama_qwen3_8b",
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
