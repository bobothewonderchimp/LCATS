"""Tests for experimental model-comparison diagnostic helpers."""

from __future__ import annotations

import pathlib
import sys
import unittest

_MODEL_COMPARISON = (
    pathlib.Path(__file__).resolve().parents[2] / "experimental" / "model_comparison"
)
sys.path.insert(0, str(_MODEL_COMPARISON))

from common import harness  # noqa: E402
from lcats.llm import fake_backend  # noqa: E402


class TestModelComparisonDiagnostics(unittest.TestCase):
    def test_segment_anchor_diagnostics_reads_pre_alignment_wrapper(self):
        parsed_output = {
            "segments": [
                {
                    "segment_id": 1,
                    "segment_type": "dramatic_scene",
                    "start_par_id": 1,
                    "end_par_id": 1,
                    "start_exact": "The old machine",
                    "end_exact": "not in story",
                    "summary": "A machine appears.",
                }
            ]
        }

        diagnostics = harness.summarize_segment_anchor_diagnostics(
            parsed_output, "The old machine hummed."
        )

        self.assertEqual(len(diagnostics), 1)
        self.assertEqual(diagnostics[0]["segment_id"], 1)
        self.assertEqual(diagnostics[0]["start_exact"], "The old machine")
        self.assertTrue(diagnostics[0]["start_exact_found"])
        self.assertEqual(diagnostics[0]["end_exact"], "not in story")
        self.assertFalse(diagnostics[0]["end_exact_found"])

    def test_entity_grounding_reports_raw_and_grounded_counts(self):
        backend = fake_backend.FakeBackend(
            tool_result={
                "entities": [
                    {
                        "entity_id": "e1",
                        "canonical_name": "the machine",
                        "entity_type": "machine_or_artifact",
                        "mentions": [
                            {
                                "mention_id": "m1",
                                "text": "the machine",
                                "quote": "old machine",
                            }
                        ],
                    },
                    {
                        "entity_id": "e2",
                        "canonical_name": "the ghost",
                        "entity_type": "abstract_force",
                        "mentions": [
                            {
                                "mention_id": "m2",
                                "text": "ghost",
                                "quote": "not in the segment",
                            }
                        ],
                    },
                ]
            },
            input_tokens=10,
            output_tokens=20,
        )
        segment_path = pathlib.Path(self.id()).with_suffix(".json")
        segment_path.write_text(
            (
                "{\n"
                '  "source_story": "fixture",\n'
                '  "segment_id": 1,\n'
                '  "segment_type": "dramatic_scene",\n'
                '  "body": "The old machine hummed."\n'
                "}\n"
            ),
            encoding="utf-8",
        )
        self.addCleanup(segment_path.unlink)

        result = harness.run_entity_extraction_with_grounding(
            candidate="test",
            backend_kind="fake",
            backend=backend,
            model="fake-1.0",
            segment_path=segment_path,
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["raw_entity_count"], 2)
        self.assertEqual(result["grounded_entity_count"], 1)
        self.assertEqual(result["grounded_mention_count"], 1)
        self.assertEqual(result["input_tokens"], 10)
        self.assertEqual(result["output_tokens"], 20)


if __name__ == "__main__":
    unittest.main()
