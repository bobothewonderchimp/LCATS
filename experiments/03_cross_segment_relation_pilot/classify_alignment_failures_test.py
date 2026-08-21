"""Unit tests for classify_alignment_failures.py.

Not part of the installed lcats package (lives under experiments/, not
lcats/src/lcats/) -- run explicitly:

    python -m pytest experiments/03_cross_segment_relation_pilot/classify_alignment_failures_test.py
"""

from __future__ import annotations

import json
import pathlib
import sys
import tempfile
import unittest
import collections

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import classify_alignment_failures  # noqa: E402 - see sys.path.insert above


def _write_story(data_dir: pathlib.Path, collection: str, slug: str, body: str) -> None:
    story_dir = data_dir / collection / slug
    story_dir.mkdir(parents=True)
    (story_dir / "story.json").write_text(
        json.dumps({"name": slug, "author": "Test Author", "body": body}),
        encoding="utf-8",
    )


class TestClassifyStory(unittest.TestCase):
    def test_anchor_absent_from_document(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = pathlib.Path(tmp) / "corpora"
            _write_story(
                data_dir,
                "coll",
                "story_one",
                "Paragraph one.\n\nParagraph two, the real text here.\n\nParagraph three.",
            )
            record = {
                "story_id": "coll/story_one",
                "outcome": "alignment_error:alignment failed: ValueError('alignment failed for segment_id=1: anchor text not found in story text')",
                "parsed_output": {
                    "segments": [
                        {
                            "segment_id": 1,
                            "start_par_id": 2,
                            "end_par_id": 2,
                            "start_exact": "This text was never in the story at all.",
                            "end_exact": "",
                        }
                    ]
                },
            }
            category, details = classify_alignment_failures.classify_story(
                record, data_dir
            )
            self.assertEqual(category, "anchor_absent_from_document")
            self.assertEqual(len(details), 1)

    def test_paragraph_misnumbering_reports_real_span(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = pathlib.Path(tmp) / "corpora"
            _write_story(
                data_dir,
                "coll",
                "story_two",
                "Para one.\n\nPara two.\n\nThe real anchor text lives here in para three.",
            )
            record = {
                "story_id": "coll/story_two",
                "outcome": "alignment_error:alignment failed: ValueError('alignment failed for segment_id=1: anchor text not found in story text')",
                "parsed_output": {
                    "segments": [
                        {
                            "segment_id": 1,
                            # Claims paragraph 1, but the anchor is really in
                            # paragraph 3 -- a mis-numbering case.
                            "start_par_id": 1,
                            "end_par_id": 1,
                            "start_exact": "The real anchor text lives here",
                            "end_exact": "",
                        }
                    ]
                },
            }
            category, details = classify_alignment_failures.classify_story(
                record, data_dir
            )
            self.assertIn(
                category,
                (
                    "paragraph_misnumbering_large_margin",
                    "paragraph_misnumbering_narrow_margin",
                ),
            )
            self.assertIn("found_outside_claimed_range", details[0])

    def test_end_exact_before_resolved_start_is_not_silently_accepted(self):
        """Review finding, PR #320: align_segment resolves start_exact
        against [lo, hi) first, then searches end_exact only from that
        resolved start position onward ([s_idx, hi), not [lo, hi) again)
        -- so a segment whose end_exact text occurs BEFORE its (correctly
        resolved) start_exact within the claimed paragraph range is a
        real alignment failure, not a reproducible success. Checking both
        anchors independently against the full [lo, hi) range would
        wrongly find end_exact "in range" and report
        no_anchor_failure_reproduced for a story whose real alignment
        genuinely failed, corrupting the category counts."""
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = pathlib.Path(tmp) / "corpora"
            body = (
                "END marker text. Then some filler words padding this out. "
                "START marker text really here."
            )
            _write_story(data_dir, "coll", "story_four", body)
            record = {
                "story_id": "coll/story_four",
                "outcome": "alignment_error:alignment failed: ValueError('alignment failed for segment_id=1: anchor text not found in story text')",
                "parsed_output": {
                    "segments": [
                        {
                            "segment_id": 1,
                            "start_par_id": 1,
                            "end_par_id": 1,
                            "start_exact": "START marker text really here.",
                            "end_exact": "END marker text.",
                        }
                    ]
                },
            }
            category, _ = classify_alignment_failures.classify_story(record, data_dir)
            self.assertNotEqual(category, "no_anchor_failure_reproduced")

    def test_no_parsed_output_captured(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = pathlib.Path(tmp) / "corpora"
            record = {
                "story_id": "coll/story_three",
                "outcome": "alignment_error:alignment failed: ...",
                "parsed_output": None,
            }
            category, _ = classify_alignment_failures.classify_story(record, data_dir)
            self.assertEqual(category, "no_parsed_output_captured")

    def test_missing_story_json_degrades_gracefully(self):
        """Review finding, PR #320: a story.json that's gone missing since
        the smoke test ran (or a malformed story_id) must not crash the
        whole batch report -- it should degrade to a diagnostic category
        for that one story, like every other malformed-input case here."""
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = pathlib.Path(tmp) / "corpora"
            data_dir.mkdir(parents=True)
            record = {
                "story_id": "coll/story_never_written",
                "outcome": "alignment_error:alignment failed: ValueError('alignment failed for segment_id=1: anchor text not found in story text')",
                "parsed_output": {
                    "segments": [
                        {
                            "segment_id": 1,
                            "start_par_id": 1,
                            "end_par_id": 1,
                            "start_exact": "anything",
                            "end_exact": "",
                        }
                    ]
                },
            }
            category, details = classify_alignment_failures.classify_story(
                record, data_dir
            )
            self.assertEqual(category, "story_file_unreadable")
            self.assertEqual(len(details), 1)

    def test_load_story_text_error_includes_story_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = pathlib.Path(tmp) / "corpora"
            data_dir.mkdir(parents=True)
            with self.assertRaisesRegex(
                ValueError,
                "could not load story_id 'coll/story_never_written'.*story.json",
            ):
                classify_alignment_failures._load_story_text(
                    data_dir, "coll/story_never_written"
                )

    def test_paragraph_misnumbering_diagnostics_report_nearest_edge_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = pathlib.Path(tmp) / "corpora"
            body = "One.\n\nTwo.\n\nThree anchor here.\n\nFour."
            _write_story(data_dir, "coll", "story_five", body)
            real_pos = body.index("Three anchor here")
            row = classify_alignment_failures.diagnose_paragraph_misnumbering_case(
                {
                    "story_id": "coll/story_five",
                    "category": "paragraph_misnumbering_narrow_margin",
                    "start_par_id": 1,
                    "end_par_id": 2,
                    "real_pos": real_pos,
                    "margin_chars": 2,
                },
                data_dir,
            )
            self.assertEqual(row["real_par_id"], 3)
            self.assertEqual(row["nearest_edge_drift_pars"], 1)
            self.assertTrue(row["boundary_off_by_one"])
            self.assertTrue(row["boundary_near_miss"])

    def test_paragraph_misnumbering_diagnostics_count_multi_line_paragraphs(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = pathlib.Path(tmp) / "corpora"
            body = (
                "Plain paragraph.\n\n"
                "A line.\nB line.\nC line.\nD line.\n\n"
                "Real anchor paragraph."
            )
            _write_story(data_dir, "coll", "story_six", body)
            row = classify_alignment_failures.diagnose_paragraph_misnumbering_case(
                {
                    "story_id": "coll/story_six",
                    "category": "paragraph_misnumbering_large_margin",
                    "start_par_id": 1,
                    "end_par_id": 1,
                    "real_pos": body.index("Real anchor paragraph"),
                    "margin_chars": 15,
                },
                data_dir,
            )
            self.assertEqual(row["multi_line_paragraphs"], 1)
            self.assertFalse(row["boundary_off_by_one"])
            self.assertTrue(row["boundary_near_miss"])

    def test_committed_wi_segment_0071_replay_fixture_reproduces_counts(self):
        repo_root = pathlib.Path(__file__).resolve().parents[2]
        fixture_dir = (
            repo_root
            / "experiments"
            / "03_cross_segment_relation_pilot"
            / "results"
            / "segmentation_paragraph_misnumbering_diagnostics"
            / "replay_fixture"
        )
        data_dir = repo_root / "corpora"
        counts = collections.Counter()
        for result_path in sorted(fixture_dir.glob("*/*.json")):
            record = json.loads(result_path.read_text("utf-8"))
            outcome = record.get("outcome", "")
            if outcome.startswith("alignment_error:"):
                category, _ = classify_alignment_failures.classify_story(
                    record, data_dir
                )
                counts[category] += 1
            else:
                counts[outcome] += 1
        self.assertEqual(
            counts,
            {
                "anchor_absent_from_document": 2,
                "included": 2,
                "paragraph_misnumbering_large_margin": 1,
                "paragraph_misnumbering_narrow_margin": 1,
            },
        )


if __name__ == "__main__":
    unittest.main()
