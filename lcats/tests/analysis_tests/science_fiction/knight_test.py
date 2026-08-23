"""Tests for deterministic Knight adjudication helpers."""

import unittest

from lcats.analysis.science_fiction import evidence
from lcats.analysis.science_fiction import knight
from lcats.analysis.science_fiction import models
from lcats.analysis.science_fiction import novum


def _evidence_record(evidence_id: str) -> evidence.EvidenceRecord:
    return evidence.EvidenceRecord(
        evidence_id=evidence_id,
        evidence_type="storyworld_change",
        quote=f"Quote for {evidence_id}.",
        anchor=evidence.EvidenceAnchor(
            paragraph_ids=("p0001",),
            start_char=0,
            end_char=10,
        ),
        paraphrase=f"Paraphrase for {evidence_id}.",
        confidence=0.9,
        provenance=(evidence.EvidenceProvenance(source="fixture"),),
    )


def _evidence_set() -> evidence.EvidenceSet:
    return evidence.EvidenceSet(
        evidence_set_id="evidence-set-1",
        story_hash="story-hash",
        records=tuple(
            _evidence_record(evidence_id)
            for evidence_id in (
                "criterion_1",
                "criterion_2",
                "candidate-novelty",
                "candidate-cognition",
                "candidate-hegemony",
            )
        ),
        quarantined=(),
        conflicts=(),
    )


def _provenance(rubric_version: str) -> models.ProvenanceRecord:
    return models.ProvenanceRecord(
        run_id=f"run-{rubric_version}",
        rubric_version=rubric_version,
    )


class KnightAdjudicationTest(unittest.TestCase):
    def test_builds_seven_independent_criteria_without_threshold(self):
        decisions = tuple(
            knight.CriterionAdjudication(
                criterion_id=criterion_id,
                status=(
                    "present"
                    if criterion_id in {"criterion_1", "criterion_2"}
                    else "absent"
                ),
                materiality=(
                    "central"
                    if criterion_id in {"criterion_1", "criterion_2"}
                    else None
                ),
                supporting_evidence_ids=(
                    (criterion_id,)
                    if criterion_id in {"criterion_1", "criterion_2"}
                    else ()
                ),
                rationale=f"{criterion_id} decision.",
            )
            for criterion_id in reversed(models.KNIGHT_CRITERION_IDS)
        )

        analysis = knight.build_analysis(
            analysis_id="knight-1",
            story_hash="story-hash",
            evidence_set=_evidence_set(),
            decisions=decisions,
            provenance=_provenance(models.KNIGHT_RUBRIC_VERSION),
        )
        data = analysis.to_dict()

        self.assertEqual(
            models.KNIGHT_CRITERION_IDS[0], analysis.criteria[0].criterion_id
        )
        self.assertEqual(2, analysis.interval.definite_count)
        self.assertEqual(2, analysis.interval.possible_count)
        self.assertEqual(7, len(analysis.criteria))
        self.assertNotIn("threshold", data)
        self.assertNotIn("probability", data)

    def test_rejects_missing_evidence_ids_before_sidecar_validation(self):
        decisions = tuple(
            knight.CriterionAdjudication(
                criterion_id=criterion_id,
                status="present" if criterion_id == "criterion_1" else "absent",
                materiality="central" if criterion_id == "criterion_1" else None,
                supporting_evidence_ids=(
                    ("missing-evidence",) if criterion_id == "criterion_1" else ()
                ),
            )
            for criterion_id in models.KNIGHT_CRITERION_IDS
        )

        with self.assertRaisesRegex(ValueError, "evidence ids do not exist"):
            knight.build_analysis(
                analysis_id="knight-1",
                story_hash="story-hash",
                evidence_set=_evidence_set(),
                decisions=decisions,
                provenance=_provenance(models.KNIGHT_RUBRIC_VERSION),
            )

    def test_plans_bounded_follow_up_for_ambiguous_criteria(self):
        decisions = tuple(
            knight.CriterionAdjudication(
                criterion_id=criterion_id,
                status=(
                    "ambiguous"
                    if criterion_id in {"criterion_1", "criterion_2"}
                    else "absent"
                ),
                materiality=(
                    "substantial"
                    if criterion_id in {"criterion_1", "criterion_2"}
                    else None
                ),
            )
            for criterion_id in models.KNIGHT_CRITERION_IDS
        )

        requests = knight.plan_follow_up(decisions, max_requests=1)

        self.assertEqual(1, len(requests))
        self.assertEqual("criterion_1", requests[0].criterion_id)
        self.assertEqual(3, requests[0].max_evidence_records)

    def test_rejects_invalid_follow_up_status(self):
        decisions = tuple(
            knight.CriterionAdjudication(
                criterion_id=criterion_id,
                status="not_assessible" if criterion_id == "criterion_1" else "absent",
            )
            for criterion_id in models.KNIGHT_CRITERION_IDS
        )

        with self.assertRaisesRegex(ValueError, "decision state"):
            knight.plan_follow_up(decisions)

    def test_knight_failure_does_not_force_suvin_failure(self):
        failure = models.FailureRecord(
            stage="knight",
            kind="pipeline_failure",
            message="Knight adjudication failed.",
        )
        knight_analysis = knight.failed_analysis(
            analysis_id="knight-failed",
            story_hash="story-hash",
            evidence_set_id="evidence-set-1",
            provenance=_provenance(models.KNIGHT_RUBRIC_VERSION),
            failure=failure,
        )
        suvin_analysis = novum.build_analysis(
            analysis_id="suvin-complete",
            story_hash="story-hash",
            evidence_set=_evidence_set(),
            candidates=(
                novum.CandidateAdjudication(
                    candidate_id="novum-1",
                    description="A candidate novum governs the story.",
                    novelty=novum.DimensionAdjudication(
                        status="present",
                        supporting_evidence_ids=("candidate-novelty",),
                    ),
                    cognitive_validation=novum.DimensionAdjudication(
                        status="present",
                        supporting_evidence_ids=("candidate-cognition",),
                    ),
                    narrative_hegemony=novum.DimensionAdjudication(
                        status="present",
                        supporting_evidence_ids=("candidate-hegemony",),
                    ),
                ),
            ),
            provenance=_provenance(models.SUVIN_RUBRIC_VERSION),
            dominant_novum_id="novum-1",
        )

        envelope = models.ScienceFictionSidecarEnvelope(
            lcats_id="collection/story",
            story_path="collection/story/story.json",
            story_hash="story-hash",
            evidence_sets=(_evidence_set(),),
            knight_analyses=(knight_analysis,),
            suvin_novum_analyses=(suvin_analysis,),
            partial_success=models.PartialSuccessRecord(
                completed_stages=("suvin_novum",),
                failed_stages=(failure,),
            ),
        )

        self.assertEqual("failed", knight_analysis.status)
        self.assertEqual("complete", suvin_analysis.status)
        self.assertTrue(envelope.validate().valid)


if __name__ == "__main__":
    unittest.main()
