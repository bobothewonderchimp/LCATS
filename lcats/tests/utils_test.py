"""Unit tests for the utils package."""

import unittest
from unittest.mock import patch

from lcats import utils


class TestPprint(unittest.TestCase):
    """Unit tests for the pprint function."""

    @patch('builtins.print')
    def test_pprint_basic(self, mock_print):
        """Test that a simple paragraph is wrapped correctly."""
        text = "This is a simple paragraph that should wrap correctly."
        utils.pprint(text, width=20)

        # Verify that the printed output was wrapped to the specified width
        expected_calls = [
            ((),),
            (('This is a simple\nparagraph that\nshould wrap\ncorrectly.',),),
            ((),)
        ]
        mock_print.assert_has_calls(expected_calls, any_order=False)

    @patch('builtins.print')
    def test_pprint_multiple_paragraphs(self, mock_print):
        """Test that multiple paragraphs are wrapped separately."""
        text = "First paragraph.\n\nSecond paragraph."
        utils.pprint(text, width=20)

        # Verify each paragraph is wrapped separately
        expected_calls = [
            ((),),  # Extra newline before printing
            (('First paragraph.',),),
            ((),),  # Newline after first paragraph
            (('Second paragraph.',),),
            ((),)  # Newline after second paragraph
        ]
        mock_print.assert_has_calls(expected_calls, any_order=False)


class TestSm(unittest.TestCase):
    """Unit tests for the sm function."""

    def test_sm_within_limit(self):
        """Test that a short text is not shortened."""
        text = "Short text"
        limit = 20
        result = utils.sm(text, limit=limit)
        self.assertEqual(result, text)
        self.assertLess(len(result), limit)

    def test_sm_exceeds_limit(self):
        """Test that a long text is shortened."""
        text = "This is a very long text that exceeds the specified limit for display."
        limit = 20
        result = utils.sm(text, limit=limit)
        expected_result = "This is ... display."
        self.assertEqual(result, expected_result)
        self.assertEqual(len(result), limit)

    def test_sm_exactly_limit(self):
        """Test that a text exactly at the limit is not shortened."""
        text = "Exact limit text here"
        result = utils.sm(text, limit=len(text))
        self.assertEqual(result, text)

    def test_sm_with_short_limit(self):
        """The cutoff for the prefix and suffix should be one plus the spacer length."""
        text = "A somewhat long text"
        spacer = "..."
        too_short = len(spacer) + 1
        with self.assertRaises(ValueError):
            utils.sm(text, limit=too_short, spacer=spacer)
        self.assertEqual(
            utils.sm(text, limit=too_short + 1, spacer=spacer), "A...t")

    def test_sm_custom_spacer(self):
        text = "Another long text that should be shortened."
        limit = 25
        result = utils.sm(text, limit=limit, spacer="---")
        expected_result = "Another lon--- shortened."
        self.assertEqual(result, expected_result)
        self.assertEqual(len(result), limit)


if __name__ == '__main__':
    unittest.main()
