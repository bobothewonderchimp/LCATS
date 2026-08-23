"""Tests for deterministic Suvin novum adjudication helpers."""

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
                "novelty",
                "cognition",
                "hegemony",
                "reader",
                "consequence",
                "knight-criterion",
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


def _knight_decisions() -> tuple[knight.CriterionAdjudication, ...]:
    return tuple(
        knight.CriterionAdjudication(
            criterion_id=criterion_id,
            status="present" if criterion_id == "criterion_1" else "absent",
            materiality="central" if criterion_id == "criterion_1" else None,
            supporting_evidence_ids=(
                ("knight-criterion",) if criterion_id == "criterion_1" else ()
            ),
        )
        for criterion_id in models.KNIGHT_CRITERION_IDS
    )


class NovumAdjudicationTest(unittest.TestCase):
    def test_builds_conjunctive_novum_without_additive_score(self):
        analysis = novum.build_analysis(
            analysis_id="suvin-1",
            story_hash="story-hash",
            evidence_set=_evidence_set(),
            candidates=(
                novum.CandidateAdjudication(
                    candidate_id="novum-1",
                    description="A cognitively validated storyworld change.",
                    novelty=novum.DimensionAdjudication(
                        status="present",
                        supporting_evidence_ids=("novelty",),
                    ),
                    cognitive_validation=novum.DimensionAdjudication(
                        status="present",
                        supporting_evidence_ids=("cognition",),
                    ),
                    narrative_hegemony=novum.DimensionAdjudication(
                        status="present",
                        supporting_evidence_ids=("hegemony",),
                    ),
                ),
                novum.CandidateAdjudication(
                    candidate_id="incidental-tech",
                    description="Technology appears but does not govern the story.",
                    novelty=novum.DimensionAdjudication(
                        status="present",
                        supporting_evidence_ids=("novelty",),
                    ),
                    cognitive_validation=novum.DimensionAdjudication(
                        status="present",
                        supporting_evidence_ids=("cognition",),
                    ),
                    narrative_hegemony=novum.DimensionAdjudication(status="absent"),
                ),
            ),
            provenance=_provenance(models.SUVIN_RUBRIC_VERSION),
            dominant_novum_id="novum-1",
        )
        data = analysis.to_dict()

        self.assertTrue(data["candidates"][0]["qualified_novum"])
        self.assertFalse(data["candidates"][1]["qualified_novum"])
        self.assertNotIn("score", data["candidates"][0])
        self.assertNotIn("probability", data["candidates"][0])

    def test_estrangement_is_separate_and_character_reaction_optional(self):
        candidate = novum.CandidateAdjudication(
            candidate_id="novum-1",
            description="A validated novum with reader-facing estrangement.",
            novelty=novum.DimensionAdjudication(
                status="present",
                supporting_evidence_ids=("novelty",),
            ),
            cognitive_validation=novum.DimensionAdjudication(
                status="present",
                supporting_evidence_ids=("cognition",),
            ),
            narrative_hegemony=novum.DimensionAdjudication(
                status="present",
                supporting_evidence_ids=("hegemony",),
            ),
            estrangement=novum.EstrangementAdjudication(
                reader_facing_evidence_ids=("reader",),
                storyworld_consequence_evidence_ids=("consequence",),
            ),
        ).to_candidate(_evidence_set())

        self.assertTrue(candidate.qualified_novum)
        self.assertEqual((), candidate.estrangement.character_reaction_evidence)
        self.assertEqual(1, len(candidate.estrangement.reader_facing_evidence))

    def test_rejects_systems_with_unqualified_candidates(self):
        with self.assertRaisesRegex(ValueError, "qualified candidates"):
            novum.build_analysis(
                analysis_id="suvin-1",
                story_hash="story-hash",
                evidence_set=_evidence_set(),
                candidates=(
                    novum.CandidateAdjudication(
                        candidate_id="incidental-tech",
                        description="An unqualified candidate.",
                        novelty=novum.DimensionAdjudication(
                            status="present",
                            supporting_evidence_ids=("novelty",),
                        ),
                        cognitive_validation=novum.DimensionAdjudication(
                            status="present",
                            supporting_evidence_ids=("cognition",),
                        ),
                        narrative_hegemony=novum.DimensionAdjudication(status="absent"),
                    ),
                ),
                provenance=_provenance(models.SUVIN_RUBRIC_VERSION),
                novum_systems=(
                    novum.NovumSystemAdjudication(
                        system_id="system-1",
                        candidate_ids=("incidental-tech", "missing"),
                    ),
                ),
            )

    def test_rejects_mismatched_evidence_set_story_hash(self):
        with self.assertRaisesRegex(ValueError, "story_hash"):
            novum.build_analysis(
                analysis_id="suvin-1",
                story_hash="other-story-hash",
                evidence_set=_evidence_set(),
                candidates=(
                    novum.CandidateAdjudication(
                        candidate_id="novum-1",
                        description="A cognitively validated storyworld change.",
                        novelty=novum.DimensionAdjudication(
                            status="present",
                            supporting_evidence_ids=("novelty",),
                        ),
                        cognitive_validation=novum.DimensionAdjudication(
                            status="present",
                            supporting_evidence_ids=("cognition",),
                        ),
                        narrative_hegemony=novum.DimensionAdjudication(
                            status="present",
                            supporting_evidence_ids=("hegemony",),
                        ),
                    ),
                ),
                provenance=_provenance(models.SUVIN_RUBRIC_VERSION),
            )

    def test_plans_bounded_follow_up_for_ambiguous_dimensions(self):
        candidates = (
            novum.CandidateAdjudication(
                candidate_id="novum-1",
                description="An uncertain candidate.",
                novelty=novum.DimensionAdjudication(status="ambiguous"),
                cognitive_validation=novum.DimensionAdjudication(
                    status="not_assessable"
                ),
                narrative_hegemony=novum.DimensionAdjudication(status="absent"),
            ),
        )

        requests = novum.plan_follow_up(candidates, max_requests=1)

        self.assertEqual(1, len(requests))
        self.assertEqual("novelty", requests[0].dimension)
        self.assertEqual("novum-1", requests[0].candidate_id)

    def test_rejects_invalid_follow_up_status(self):
        candidates = (
            novum.CandidateAdjudication(
                candidate_id="novum-1",
                description="A typo in a dimension status.",
                novelty=novum.DimensionAdjudication(status="uncertain"),
                cognitive_validation=novum.DimensionAdjudication(status="absent"),
                narrative_hegemony=novum.DimensionAdjudication(status="absent"),
            ),
        )

        with self.assertRaisesRegex(ValueError, "decision state"):
            novum.plan_follow_up(candidates)

    def test_follow_up_cap_does_not_suppress_later_status_validation(self):
        candidates = (
            novum.CandidateAdjudication(
                candidate_id="novum-1",
                description="A capped candidate with a later typo.",
                novelty=novum.DimensionAdjudication(status="ambiguous"),
                cognitive_validation=novum.DimensionAdjudication(status="uncertain"),
                narrative_hegemony=novum.DimensionAdjudication(status="absent"),
            ),
        )

        with self.assertRaisesRegex(ValueError, "decision state"):
            novum.plan_follow_up(candidates, max_requests=1)
        with self.assertRaisesRegex(ValueError, "decision state"):
            novum.plan_follow_up(candidates, max_requests=0)

    def test_suvin_failure_does_not_force_knight_failure(self):
        failure = models.FailureRecord(
            stage="suvin_novum",
            kind="pipeline_failure",
            message="Suvin adjudication failed.",
        )
        suvin_analysis = novum.failed_analysis(
            analysis_id="suvin-failed",
            story_hash="story-hash",
            evidence_set_id="evidence-set-1",
            provenance=_provenance(models.SUVIN_RUBRIC_VERSION),
            failure=failure,
        )
        knight_analysis = knight.build_analysis(
            analysis_id="knight-complete",
            story_hash="story-hash",
            evidence_set=_evidence_set(),
            decisions=_knight_decisions(),
            provenance=_provenance(models.KNIGHT_RUBRIC_VERSION),
        )
        envelope = models.ScienceFictionSidecarEnvelope(
            lcats_id="collection/story",
            story_path="collection/story/story.json",
            story_hash="story-hash",
            evidence_sets=(_evidence_set(),),
            knight_analyses=(knight_analysis,),
            suvin_novum_analyses=(suvin_analysis,),
            partial_success=models.PartialSuccessRecord(
                completed_stages=("knight",),
                failed_stages=(failure,),
            ),
        )

        self.assertEqual("complete", knight_analysis.status)
        self.assertEqual("failed", suvin_analysis.status)
        self.assertTrue(envelope.validate().valid)


if __name__ == "__main__":
    unittest.main()
