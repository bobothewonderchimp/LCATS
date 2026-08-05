"""Print a comparison table across every candidate/results.json in this directory.

Usage (from anywhere, no install required):

    python lcats/experimental/model_comparison/benchmark_summary.py

Run each candidate's own benchmark.py first (see that candidate's README.md)
- this script only aggregates and prints, it makes no LLM calls itself.
"""

from __future__ import annotations

import json
import pathlib

_HERE = pathlib.Path(__file__).resolve().parent

_COLUMNS = (
    ("candidate", 20),
    ("model", 24),
    ("success", 8),
    ("latency_seconds", 10),
    ("input_tokens", 12),
    ("output_tokens", 13),
    ("entity_count", 13),
    ("error_type", 20),
)


def _load_results() -> list:
    rows = []
    for results_file in sorted(_HERE.glob("*/results.json")):
        try:
            rows.append(json.loads(results_file.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError) as exc:
            rows.append(
                {
                    "candidate": results_file.parent.name,
                    "error_type": f"unreadable: {exc}",
                }
            )
    return rows


def _format_cell(row: dict, key: str) -> str:
    value = row.get(key)
    if value is None:
        return "-"
    if key == "latency_seconds" and isinstance(value, (int, float)):
        return f"{value:.1f}"
    return str(value)


def main() -> None:
    rows = _load_results()
    if not rows:
        print(
            f"No results.json found under {_HERE}. "
            "Run a candidate's benchmark.py first, e.g.:\n"
            f"  python {_HERE / 'anthropic_opus' / 'benchmark.py'}"
        )
        return

    header = "  ".join(name.ljust(width) for name, width in _COLUMNS)
    print(header)
    print("-" * len(header))
    for row in rows:
        print(
            "  ".join(_format_cell(row, name).ljust(width) for name, width in _COLUMNS)
        )


if __name__ == "__main__":
    main()
