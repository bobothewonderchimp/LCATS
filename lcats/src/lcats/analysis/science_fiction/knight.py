"""Deterministic Knight adjudication helpers.

This module consumes shared neutral evidence and builds the versioned
``KnightAnalysis`` contract records. It intentionally does not define a
Knight pass threshold, genre label, or probability.
"""

from __future__ import annotations

import dataclasses

from lcats.analysis.science_fiction import evidence
from lcats.analysis.science_fiction import models


@dataclasses.dataclass(frozen=True)
class CriterionAdjudication:
    """One proposed decision for a Knight criterion."""

    criterion_id: str
    status: str
    materiality: str | None = None
    supporting_evidence_ids: tuple[str, ...] = ()
    counterevidence_ids: tuple[str, ...] = ()
    rationale: str = ""
    confidence: float | None = None

    def to_criterion(
        self, evidence_set: evidence.EvidenceSet
    ) -> models.KnightCriterion:
        """Convert the adjudication to a contract criterion."""

        _require_evidence_ids(evidence_set, self.supporting_evidence_ids)
        _require_evidence_ids(evidence_set, self.counterevidence_ids)
        return models.KnightCriterion(
            criterion_id=self.criterion_id,
            status=self.status,
            materiality=self.materiality,
            supporting_evidence=_references(
                evidence_set.evidence_set_id, self.supporting_evidence_ids
            ),
            counterevidence=_references(
                evidence_set.evidence_set_id, self.counterevidence_ids
            ),
            rationale=self.rationale,
            confidence=self.confidence,
        )


@dataclasses.dataclass(frozen=True)
class KnightFollowUpRequest:
    """A bounded request for additional criterion-specific evidence."""

    criterion_id: str
    reason: str
    max_evidence_records: int = 3

    def __post_init__(self) -> None:
        if self.criterion_id not in models.KNIGHT_CRITERION_IDS:
            raise ValueError("criterion_id must identify a Knight criterion")
        if not self.reason:
            raise ValueError("reason must be non-empty")
        if self.max_evidence_records < 1:
            raise ValueError("max_evidence_records must be positive")


def build_analysis(
    *,
    analysis_id: str,
    story_hash: str,
    evidence_set: evidence.EvidenceSet,
    decisions: tuple[CriterionAdjudication, ...],
    provenance: models.ProvenanceRecord,
    status: str = "complete",
    failures: tuple[models.FailureRecord, ...] = (),
) -> models.KnightAnalysis:
    """Build an independent Knight analysis from seven criterion decisions."""

    _require_story_hash(story_hash, evidence_set)
    criteria = tuple(
        decision.to_criterion(evidence_set) for decision in _order_decisions(decisions)
    )
    return models.KnightAnalysis(
        analysis_id=analysis_id,
        story_hash=story_hash,
        evidence_set_id=evidence_set.evidence_set_id,
        criteria=criteria,
        provenance=provenance,
        status=status,
        failures=failures,
    )


def failed_analysis(
    *,
    analysis_id: str,
    story_hash: str,
    evidence_set_id: str,
    provenance: models.ProvenanceRecord,
    failure: models.FailureRecord,
) -> models.KnightAnalysis:
    """Build a failed Knight analysis without affecting Suvin analysis."""

    criteria = tuple(
        models.KnightCriterion(
            criterion_id=criterion_id,
            status="not_assessable",
            rationale="Knight adjudication did not complete.",
        )
        for criterion_id in models.KNIGHT_CRITERION_IDS
    )
    return models.KnightAnalysis(
        analysis_id=analysis_id,
        story_hash=story_hash,
        evidence_set_id=evidence_set_id,
        criteria=criteria,
        provenance=provenance,
        status="failed",
        failures=(failure,),
    )


def plan_follow_up(
    decisions: tuple[CriterionAdjudication, ...],
    *,
    max_requests: int = 7,
    max_evidence_records: int = 3,
) -> tuple[KnightFollowUpRequest, ...]:
    """Plan bounded retrieval for uncertain or unassessable criteria."""

    if max_requests < 0:
        raise ValueError("max_requests must be non-negative")
    ordered_decisions = _order_decisions(decisions)
    for decision in ordered_decisions:
        _require_decision_status(decision.status)
    requests: list[KnightFollowUpRequest] = []
    for decision in ordered_decisions:
        if len(requests) >= max_requests:
            break
        if decision.status in {"ambiguous", "not_assessable"}:
            requests.append(
                KnightFollowUpRequest(
                    criterion_id=decision.criterion_id,
                    reason=f"{decision.status} Knight criterion needs evidence review",
                    max_evidence_records=max_evidence_records,
                )
            )
    return tuple(requests)


def _order_decisions(
    decisions: tuple[CriterionAdjudication, ...],
) -> tuple[CriterionAdjudication, ...]:
    by_id = {decision.criterion_id: decision for decision in decisions}
    if set(by_id) != set(models.KNIGHT_CRITERION_IDS) or len(by_id) != len(decisions):
        raise ValueError("Knight adjudication requires seven unique criteria")
    return tuple(by_id[criterion_id] for criterion_id in models.KNIGHT_CRITERION_IDS)


def _references(
    evidence_set_id: str, evidence_ids: tuple[str, ...]
) -> tuple[models.EvidenceReference, ...]:
    return tuple(
        models.EvidenceReference(evidence_set_id=evidence_set_id, evidence_id=item)
        for item in evidence_ids
    )


def _require_evidence_ids(
    evidence_set: evidence.EvidenceSet, evidence_ids: tuple[str, ...]
) -> None:
    available_ids = {record.evidence_id for record in evidence_set.records}
    missing_ids = set(evidence_ids) - available_ids
    if missing_ids:
        raise ValueError(f"evidence ids do not exist: {sorted(missing_ids)!r}")


def _require_decision_status(status: str) -> None:
    if status not in models.DECISION_STATES:
        raise ValueError("status must be a decision state")


def _require_story_hash(story_hash: str, evidence_set: evidence.EvidenceSet) -> None:
    if story_hash != evidence_set.story_hash:
        raise ValueError("story_hash must match evidence_set.story_hash")
