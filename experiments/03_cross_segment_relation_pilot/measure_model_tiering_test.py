"""Tests for WI-PILOT-0060's bounded model-tiering measurement script."""

from __future__ import annotations

import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import measure_model_tiering  # noqa: E402 - see sys.path.insert above


class TestMeasureModelTiering(unittest.TestCase):
    def test_dry_run_comparison_is_limited_to_two_stages_per_model(self):
        report = measure_model_tiering.run_comparison(
            baseline_model="baseline-model",
            candidate_model="candidate-model",
            fixture_root=measure_model_tiering._fixtures_dir(),
            dry_run=True,
        )

        self.assertEqual(
            report["stories"],
            ["fixtures__five_o_clock_tea_farce", "fixtures__king_of_the_hill"],
        )
        self.assertEqual(report["runs"]["baseline"]["calls"], 4)
        self.assertEqual(report["runs"]["candidate"]["calls"], 4)
        self.assertEqual(
            [call["tool_name"] for call in report["runs"]["baseline"]["backend_calls"]],
            [
                "record_story_assessment",
                "record_segments",
                "record_story_assessment",
                "record_segments",
            ],
        )
        self.assertEqual(
            {
                call["requested_model"]
                for call in report["runs"]["candidate"]["backend_calls"]
            },
            {"candidate-model"},
        )

    def test_pricing_returns_none_for_unverified_model(self):
        self.assertIsNone(
            measure_model_tiering._compute_cost_usd(
                input_tokens=10, output_tokens=3, model="unknown-model"
            )
        )

    def test_known_pricing_uses_input_and_output_rates(self):
        cost = measure_model_tiering._compute_cost_usd(
            input_tokens=1_000_000,
            output_tokens=1_000_000,
            model="claude-haiku-4-5-20251001",
        )

        self.assertEqual(cost, 6.0)


if __name__ == "__main__":
    unittest.main()
