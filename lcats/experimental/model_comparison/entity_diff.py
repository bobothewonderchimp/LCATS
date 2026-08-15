"""Diff extracted entity identities across benchmark candidate results.

Usage examples:

    python lcats/experimental/model_comparison/entity_diff.py \
      anthropic_opus/results.json ollama_qwen3_8b/results.json

    python lcats/experimental/model_comparison/entity_diff.py

With no arguments, compares every ``*/results.json`` file under this
directory. The script is read-only and makes no LLM calls.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
from dataclasses import dataclass, field
from typing import Any, Iterable

_HERE = pathlib.Path(__file__).resolve().parent
_WHITESPACE = re.compile(r"\s+")


@dataclass(frozen=True)
class EntityIdentity:
    """Normalized entity identity used for set comparisons."""

    normalized_name: str
    entity_type: str = field(compare=False)
    display_name: str = field(compare=False)


@dataclass(frozen=True)
class CandidateEntities:
    """Entities loaded from one candidate result file."""

    candidate: str
    path: pathlib.Path
    entities: frozenset[EntityIdentity]
    comparable: bool = True
    not_comparable_reason: str = ""


def normalize_name(name: str) -> str:
    """Normalize a model-produced entity name for coarse set comparison."""
    return _WHITESPACE.sub(" ", name.strip()).casefold()


def _candidate_name(path: pathlib.Path, row: dict[str, Any]) -> str:
    return str(row.get("candidate") or path.parent.name)


def _entity_identity(entity: Any) -> EntityIdentity | None:
    if isinstance(entity, dict):
        raw_name = entity.get("canonical_name") or entity.get("name") or entity.get("entity")
        raw_type = entity.get("entity_type") or entity.get("type") or ""
    elif isinstance(entity, str):
        raw_name = entity
        raw_type = ""
    else:
        return None

    if not isinstance(raw_name, str) or not raw_name.strip():
        return None

    entity_type = raw_type.strip() if isinstance(raw_type, str) else ""
    display_name = _WHITESPACE.sub(" ", raw_name.strip())
    return EntityIdentity(
        normalized_name=normalize_name(display_name),
        entity_type=entity_type,
        display_name=display_name,
    )


def load_candidate_entities(path: pathlib.Path) -> CandidateEntities:
    """Load one candidate results file into a normalized entity set."""
    row = json.loads(path.read_text(encoding="utf-8"))
    entities = row.get("entities")
    if not isinstance(entities, list):
        success = row.get("success")
        error_type = row.get("error_type")
        if success is False and error_type:
            reason = f"not comparable: {error_type}"
        elif success is False:
            reason = "not comparable: benchmark failed"
        else:
            reason = "stale result: rerun benchmark to populate `entities`"
        return CandidateEntities(
            candidate=_candidate_name(path, row),
            path=path,
            entities=frozenset(),
            comparable=False,
            not_comparable_reason=reason,
        )

    identities = {
        identity for entity in entities if (identity := _entity_identity(entity)) is not None
    }
    return CandidateEntities(
        candidate=_candidate_name(path, row),
        path=path,
        entities=frozenset(identities),
    )


def default_result_paths() -> list[pathlib.Path]:
    """Return all candidate entity benchmark result files."""
    return sorted(_HERE.glob("*/results.json"))


def _format_entities(entities: Iterable[EntityIdentity]) -> str:
    formatted = []
    for entity in sorted(
        entities, key=lambda item: (item.normalized_name, item.entity_type, item.display_name)
    ):
        suffix = f" [{entity.entity_type}]" if entity.entity_type else ""
        formatted.append(f"{entity.display_name}{suffix}")
    return ", ".join(formatted) if formatted else "-"


def build_report(candidates: list[CandidateEntities]) -> str:
    """Build a human-readable entity-diff report."""
    if not candidates:
        return "No candidate results supplied."

    comparable_candidates = [candidate for candidate in candidates if candidate.comparable]
    not_comparable_candidates = [
        candidate for candidate in candidates if not candidate.comparable
    ]

    lines = ["# Entity Diff", ""]
    lines.append(
        "Normalization: entity names are stripped, internal whitespace is "
        "collapsed, and names are case-folded. Entity type is displayed "
        "when present but is not part of the comparison key."
    )
    lines.append("")
    lines.append("| Candidate | Entities | Source |")
    lines.append("|---|---:|---|")
    for candidate in candidates:
        source = f"`{candidate.path}`"
        if candidate.comparable:
            lines.append(f"| {candidate.candidate} | {len(candidate.entities)} | {source} |")
        else:
            reason = candidate.not_comparable_reason
            lines.append(f"| {candidate.candidate} | n/a | {source} ({reason}) |")

    if not_comparable_candidates:
        lines.extend(["", "## Not Comparable", ""])
        for candidate in not_comparable_candidates:
            lines.append(f"- {candidate.candidate}: {candidate.not_comparable_reason}")

    if len(comparable_candidates) < 2:
        lines.extend(
            [
                "",
                "Entity diff requires at least two comparable result files.",
            ]
        )
        return "\n".join(lines).rstrip() + "\n"

    entity_sets = [candidate.entities for candidate in comparable_candidates]
    common = set.intersection(*(set(entity_set) for entity_set in entity_sets))
    union = set.union(*(set(entity_set) for entity_set in entity_sets))

    lines.extend(["", "## Shared By All", "", _format_entities(common), ""])
    lines.extend(["## Candidate-Only Entities", ""])
    for candidate in comparable_candidates:
        other_sets = [
            set(other.entities) for other in comparable_candidates if other is not candidate
        ]
        other_entities = set.union(*other_sets) if other_sets else set()
        only = set(candidate.entities) - other_entities
        lines.append(f"### {candidate.candidate}")
        lines.append("")
        lines.append(_format_entities(only))
        lines.append("")

    lines.extend(["## Missing Per Candidate", ""])
    for candidate in comparable_candidates:
        missing = union - set(candidate.entities)
        lines.append(f"### {candidate.candidate}")
        lines.append("")
        lines.append(_format_entities(missing))
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Diff entity identities across model-comparison results.json files."
    )
    parser.add_argument(
        "results",
        nargs="*",
        type=pathlib.Path,
        help="Candidate results.json files. Defaults to every */results.json.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    paths = args.results or default_result_paths()
    candidates = [load_candidate_entities(path) for path in paths]
    print(build_report(candidates), end="")


if __name__ == "__main__":
    main()
