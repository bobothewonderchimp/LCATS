"""Deterministic Suvin novum adjudication helpers.

This module builds ``SuvinNovumAnalysis`` records from shared evidence while
preserving the novelty, cognitive validation, and narrative hegemony
conjunction. Estrangement remains separate navigation/evidence, not a required
qualification dimension.
"""

from __future__ import annotations

import dataclasses

from lcats.analysis.science_fiction import evidence
from lcats.analysis.science_fiction import models

NOVUM_DIMENSION_NAMES = (
    "novelty",
    "cognitive_validation",
    "narrative_hegemony",
)


@dataclasses.dataclass(frozen=True)
class DimensionAdjudication:
    """One novelty, cognition, or hegemony decision."""

    status: str
    supporting_evidence_ids: tuple[str, ...] = ()
    counterevidence_ids: tuple[str, ...] = ()
    rationale: str = ""
    confidence: float | None = None

    def to_decision(
        self, evidence_set: evidence.EvidenceSet
    ) -> models.NovumDimensionDecision:
        """Convert the adjudication to a contract dimension decision."""

        _require_evidence_ids(evidence_set, self.supporting_evidence_ids)
        _require_evidence_ids(evidence_set, self.counterevidence_ids)
        return models.NovumDimensionDecision(
            status=self.status,
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
class EstrangementAdjudication:
    """Evidence for estrangement, kept separate from novum qualification."""

    reader_facing_evidence_ids: tuple[str, ...] = ()
    storyworld_consequence_evidence_ids: tuple[str, ...] = ()
    character_reaction_evidence_ids: tuple[str, ...] = ()
    rationale: str = ""

    def to_profile(
        self, evidence_set: evidence.EvidenceSet
    ) -> models.EstrangementProfile:
        """Convert the adjudication to an estrangement profile."""

        _require_evidence_ids(evidence_set, self.reader_facing_evidence_ids)
        _require_evidence_ids(evidence_set, self.storyworld_consequence_evidence_ids)
        _require_evidence_ids(evidence_set, self.character_reaction_evidence_ids)
        return models.EstrangementProfile(
            reader_facing_evidence=_references(
                evidence_set.evidence_set_id, self.reader_facing_evidence_ids
            ),
            storyworld_consequence_evidence=_references(
                evidence_set.evidence_set_id,
                self.storyworld_consequence_evidence_ids,
            ),
            character_reaction_evidence=_references(
                evidence_set.evidence_set_id, self.character_reaction_evidence_ids
            ),
            rationale=self.rationale,
        )


@dataclasses.dataclass(frozen=True)
class CandidateAdjudication:
    """A candidate novum with independent N/C/H decisions."""

    candidate_id: str
    description: str
    novelty: DimensionAdjudication
    cognitive_validation: DimensionAdjudication
    narrative_hegemony: DimensionAdjudication
    estrangement: EstrangementAdjudication = dataclasses.field(
        default_factory=EstrangementAdjudication
    )
    evidence_ids: tuple[str, ...] = ()

    def to_candidate(self, evidence_set: evidence.EvidenceSet) -> models.NovumCandidate:
        """Convert the adjudication to a contract candidate."""

        _require_evidence_ids(evidence_set, self.evidence_ids)
        return models.NovumCandidate(
            candidate_id=self.candidate_id,
            description=self.description,
            novelty=self.novelty.to_decision(evidence_set),
            cognitive_validation=self.cognitive_validation.to_decision(evidence_set),
            narrative_hegemony=self.narrative_hegemony.to_decision(evidence_set),
            estrangement=self.estrangement.to_profile(evidence_set),
            evidence=_references(evidence_set.evidence_set_id, self.evidence_ids),
        )


@dataclasses.dataclass(frozen=True)
class NovumSystemAdjudication:
    """A proposed system made of qualified interacting novum candidates."""

    system_id: str
    candidate_ids: tuple[str, ...]
    rationale: str = ""

    def to_system(self) -> models.NovumSystem:
        """Convert the adjudication to a contract novum system."""

        return models.NovumSystem(
            system_id=self.system_id,
            candidate_ids=self.candidate_ids,
            rationale=self.rationale,
        )


@dataclasses.dataclass(frozen=True)
class NovumFollowUpRequest:
    """A bounded request for candidate-dimension evidence."""

    candidate_id: str
    dimension: str
    reason: str
    max_evidence_records: int = 3

    def __post_init__(self) -> None:
        if not self.candidate_id:
            raise ValueError("candidate_id must be non-empty")
        if self.dimension not in NOVUM_DIMENSION_NAMES:
            raise ValueError("dimension must be a Suvin N/C/H dimension")
        if not self.reason:
            raise ValueError("reason must be non-empty")
        if self.max_evidence_records < 1:
            raise ValueError("max_evidence_records must be positive")


def build_analysis(
    *,
    analysis_id: str,
    story_hash: str,
    evidence_set: evidence.EvidenceSet,
    candidates: tuple[CandidateAdjudication, ...],
    provenance: models.ProvenanceRecord,
    dominant_novum_id: str | None = None,
    novum_systems: tuple[NovumSystemAdjudication, ...] = (),
    status: str = "complete",
    failures: tuple[models.FailureRecord, ...] = (),
) -> models.SuvinNovumAnalysis:
    """Build an independent Suvin analysis from candidate decisions."""

    _require_story_hash(story_hash, evidence_set)
    candidate_records = tuple(
        candidate.to_candidate(evidence_set) for candidate in candidates
    )
    system_records = tuple(system.to_system() for system in novum_systems)
    return models.SuvinNovumAnalysis(
        analysis_id=analysis_id,
        story_hash=story_hash,
        evidence_set_id=evidence_set.evidence_set_id,
        candidates=candidate_records,
        provenance=provenance,
        dominant_novum_id=dominant_novum_id,
        novum_systems=system_records,
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
) -> models.SuvinNovumAnalysis:
    """Build a failed Suvin analysis without affecting Knight analysis."""

    return models.SuvinNovumAnalysis(
        analysis_id=analysis_id,
        story_hash=story_hash,
        evidence_set_id=evidence_set_id,
        candidates=(),
        provenance=provenance,
        status="failed",
        failures=(failure,),
    )


def plan_follow_up(
    candidates: tuple[CandidateAdjudication, ...],
    *,
    max_requests: int = 9,
    max_evidence_records: int = 3,
) -> tuple[NovumFollowUpRequest, ...]:
    """Plan bounded retrieval for uncertain candidate dimensions."""

    if max_requests < 0:
        raise ValueError("max_requests must be non-negative")
    for candidate in candidates:
        for dimension_name in NOVUM_DIMENSION_NAMES:
            dimension = getattr(candidate, dimension_name)
            _require_decision_status(dimension.status)
    requests: list[NovumFollowUpRequest] = []
    for candidate in candidates:
        for dimension_name in NOVUM_DIMENSION_NAMES:
            if len(requests) >= max_requests:
                return tuple(requests)
            dimension = getattr(candidate, dimension_name)
            if dimension.status in {"ambiguous", "not_assessable"}:
                requests.append(
                    NovumFollowUpRequest(
                        candidate_id=candidate.candidate_id,
                        dimension=dimension_name,
                        reason=(
                            f"{dimension.status} Suvin dimension needs "
                            "evidence review"
                        ),
                        max_evidence_records=max_evidence_records,
                    )
                )
    return tuple(requests)


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
