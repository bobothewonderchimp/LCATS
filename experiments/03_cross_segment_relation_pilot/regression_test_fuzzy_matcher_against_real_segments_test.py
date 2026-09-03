from __future__ import annotations

import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "lcats" / "src"))

import regression_test_fuzzy_matcher_against_real_segments as m  # noqa: E402
from lcats.analysis import text_segmenter  # noqa: E402

STORY_TEXT = (
    "Alpha bravo charlie delta echo foxtrot golf hotel.\n\n"
    "India juliet kilo lima mike november oscar papa.\n\n"
    "Quebec romeo sierra tango uniform victor whiskey.\n\n"
    'Xray, "yankee," zulu said quietly to the room.\n'
)


def _para_spans(text=STORY_TEXT):
    canonical = text_segmenter.canonicalize_text(text)
    _, index_meta = text_segmenter.paragraph_text_indexer(canonical)
    return canonical, index_meta["para_spans"]


def _segment(seg_id, sp, ep, start_exact, end_exact, start_char, end_char):
    return {
        "segment_id": seg_id,
        "start_par_id": sp,
        "end_par_id": ep,
        "start_exact": start_exact,
        "end_exact": end_exact,
        "start_char": start_char,
        "end_char": end_char,
    }


class IsRealSegmentTest(unittest.TestCase):
    def test_rejects_non_segment_shaped_dicts(self):
        self.assertFalse(m._is_real_segment({"foo": "bar"}))
        self.assertFalse(m._is_real_segment("not a dict"))
        self.assertFalse(m._is_real_segment(None))

    def test_rejects_null_offsets(self):
        seg = _segment(1, 1, 1, "a", "b", None, None)
        self.assertFalse(m._is_real_segment(seg))

    def test_accepts_a_well_formed_segment(self):
        seg = _segment(1, 1, 1, "Alpha bravo", "hotel.", 0, 50)
        self.assertTrue(m._is_real_segment(seg))


class ValidateControlsTest(unittest.TestCase):
    def test_non_overlapping_non_reused_segment_is_valid(self):
        text, para_spans = _para_spans()
        segs = [
            _segment(1, 1, 1, "Alpha bravo", "hotel.", 0, 50),
            _segment(2, 2, 2, "India juliet", "papa.", 52, 100),
        ]
        valid, excluded = m.validate_controls(text, segs)
        self.assertEqual(len(valid), 2)
        self.assertEqual(excluded, [])

    def test_overlapping_segments_are_both_excluded(self):
        text, para_spans = _para_spans()
        segs = [
            _segment(1, 1, 1, "Alpha bravo", "foxtrot golf hotel.", 0, 50),
            _segment(2, 1, 1, "delta echo", "hotel.", 20, 50),
        ]
        valid, excluded = m.validate_controls(text, segs)
        self.assertEqual(len(valid), 0)
        self.assertEqual(len(excluded), 2)
        self.assertTrue(
            all(
                "overlaps an adjacent segment" in r
                for ex in excluded
                for r in ex["reasons"]
            )
        )

    def test_reused_anchor_across_segments_is_excluded(self):
        text, para_spans = _para_spans()
        segs = [
            _segment(1, 1, 1, "Alpha bravo", "hotel.", 0, 50),
            _segment(2, 2, 2, "hotel.", "papa.", 52, 100),
        ]
        valid, excluded = m.validate_controls(text, segs)
        # segment 1's end_exact ("hotel.") equals segment 2's start_exact -
        # both segments touching that shared string are excluded.
        excluded_ids = {ex["segment_id"] for ex in excluded}
        self.assertIn(1, excluded_ids)
        self.assertIn(2, excluded_ids)

    def test_paragraph_window_not_containing_char_offsets_is_excluded(self):
        """The real love_of_life/story_of_keesh/brown_wolf failure mode:
        start_par_id/end_par_id claim paragraph 1, but the real char span
        is far outside paragraph 1's own bounds - a symptom of the
        pre-WI-SEGMENT-0059 paragraph-collapse bug."""
        text, para_spans = _para_spans()
        seg = _segment(1, 1, 1, "Xray", "zulu said quietly to the room.", 150, 199)
        valid, excluded = m.validate_controls(text, [seg])
        self.assertEqual(valid, [])
        self.assertEqual(len(excluded), 1)
        self.assertTrue(any("does not contain" in r for r in excluded[0]["reasons"]))

    def test_bool_par_id_is_excluded_as_malformed(self):
        text, para_spans = _para_spans()
        seg = _segment(1, True, 1, "Alpha bravo", "hotel.", 0, 51)
        valid, excluded = m.validate_controls(text, [seg])
        self.assertEqual(valid, [])
        self.assertIn("malformed", excluded[0]["reasons"][0])


class CheckSegmentTest(unittest.TestCase):
    def test_exact_anchor_agrees_with_recorded_offsets(self):
        text, para_spans = _para_spans()
        policy = m.load_default_policy()
        seg = _segment(1, 1, 1, "Alpha bravo charlie", "foxtrot golf hotel.", 0, 50)
        report = m.check_segment(para_spans, text, policy, seg)
        self.assertTrue(report["start"]["agrees"])
        self.assertTrue(report["end"]["agrees"])
        self.assertFalse(report["start"]["required_fuzzy_tolerance"])

    def test_out_of_range_par_id_is_clamped_not_a_crash(self):
        """Regression test for a real bug caught during this item's own
        execution: check_segment must clamp start_par_id/end_par_id the
        same way validate_controls does, or an out-of-range value raises
        IndexError instead of being handled."""
        text, para_spans = _para_spans()
        policy = m.load_default_policy()
        seg = _segment(1, 1, 999, "Alpha bravo", "hotel.", 0, 50)
        report = m.check_segment(para_spans, text, policy, seg)
        self.assertIn("start", report)
        self.assertIn("end", report)

    def test_anchor_with_internal_punctuation_can_fail_to_match(self):
        """Documents the real WI-SEGMENT-0102 finding: candidate_matches'
        token-ngram regex joins tokens with \\s+ only, so an anchor whose
        real text has punctuation (not just whitespace) between its last
        few tokens can fail to generate any candidate at all - a false
        negative (safe), not a false accept, but a real, common
        robustness gap in real prose (dialogue, exclamations)."""
        punctuated_text = "Alpha bravo charlie.\n\n" '"Yankee," zulu said, quietly.\n'
        text, para_spans = _para_spans(punctuated_text)
        policy = m.load_default_policy()
        seg = _segment(1, 2, 2, '"Yankee,"', "quietly.", 22, len(text))
        report = m.check_segment(para_spans, text, policy, seg)
        # This anchor's tokens ("Yankee", "zulu", "said", "quietly") are
        # separated by a comma in the real text but only \s+ in the
        # reconstructed regex - accepted_match finds nothing.
        self.assertFalse(report["end"]["fuzzy_matched"])


if __name__ == "__main__":
    unittest.main()
