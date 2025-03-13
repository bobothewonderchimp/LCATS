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
        """Test that a custom spacer is used for the shortened text."""
        text = "Another long text that should be shortened."
        limit = 25
        result = utils.sm(text, limit=limit, spacer="---")
        expected_result = "Another lon--- shortened."
        self.assertEqual(result, expected_result)
        self.assertEqual(len(result), limit)


class TestExtractFencedCodeBlocks(unittest.TestCase):
    """Unit tests for the extract_fenced_code_blocks function."""

    def test_no_code_blocks(self):
        """Test behavior when there's no triple-backtick code fence."""
        text = "Here is some text with no code fences."
        blocks = utils.extract_fenced_code_blocks(text)
        self.assertEqual(
            len(blocks), 0, "Should return an empty list for no code fences.")

    def test_single_code_block_no_lang(self):
        """Test extraction of one code block with no specified language."""
        text = """
Here is a fence:

```
some code here print("No language specified")
```

Done.
"""
        blocks = utils.extract_fenced_code_blocks(text)
        self.assertEqual(
            len(blocks), 1, "Should detect exactly one code block.")
        self.assertEqual(blocks[0][0], '',
                         "Language should be empty if not specified.")
        self.assertIn(
            'some code here', blocks[0][1], "Extracted code content should match what's inside the fence.")

    def test_single_code_block_with_lang(self):
        """Test extraction of one code block with an explicit language."""
        text = """
Pre-text

```python
def hello_world():
    print("Hello from Python")
```
Post-text """
        blocks = utils.extract_fenced_code_blocks(text)
        self.assertEqual(
            len(blocks), 1, "Should detect exactly one code block.")
        self.assertEqual(blocks[0][0], 'python',
                         "Language should be 'python'.")
        self.assertIn(
            'hello_world', blocks[0][1], "Function name should be present in extracted code.")

    def test_multiple_code_blocks(self):
        """Test extraction of multiple code blocks (some with language, some without)."""
        text = """
```json
{ "foo": "bar" }
```
Regular text

```plaintext
Here is just plain text in a block
```

And then one more:

```
System.out.println("No language specified here either");
```
"""
        blocks = utils.extract_fenced_code_blocks(text)
        self.assertEqual(
            len(blocks), 3, "Should extract three code blocks in total.")

        # Check 1st block (json)
        self.assertEqual(blocks[0][0], 'json',
                         "First block language should be 'json'.")
        self.assertIn('"bar"', blocks[0][1],
                      "Should contain 'bar' in JSON code.")

        # Check 2nd block (plaintext)
        self.assertEqual(blocks[1][0], 'plaintext',
                         "Second block language should be 'plaintext'.")
        self.assertIn('plain text in a block',
                      blocks[1][1], "Should contain 'plain text in a block'.")

        # Check 3rd block (no language)
        self.assertEqual(
            blocks[2][0], '', "Third block should have an empty language label.")
        self.assertIn('System.out.println',
                      blocks[2][1], "Should contain Java-style println statement.")

    def test_empty_code_block(self):
        """Test extraction when the code fence has no content."""
        text = """
```python
```
"""
        blocks = utils.extract_fenced_code_blocks(text)
        self.assertEqual(
            len(blocks), 1, "Should still detect one code block even if empty.")
        self.assertEqual(blocks[0][0], 'python',
                         "Language should be 'python'.")
        self.assertEqual(blocks[0][1].strip(), '',
                         "Code snippet should be empty.")

    def test_inline_backticks_are_ignored(self):
        """Test that single or double backticks inline do not affect extraction."""
        text = "We have inline `code` here, and ``some more`` there, but no fences."
        blocks = utils.extract_fenced_code_blocks(text)
        self.assertEqual(len(
            blocks), 0, "Inline single/double backticks should not be treated as fenced blocks.")

    def test_partial_fence(self):
        """Test that partial fences (missing triple backticks) do not extract anything."""
        text = """
We have something like: ``python code missing the ending backticks

just text """
        blocks = utils.extract_fenced_code_blocks(text)
        self.assertEqual(
            len(blocks), 0, "Incomplete fence should not be treated as valid code blocks.")


if __name__ == '__main__':
    unittest.main()
