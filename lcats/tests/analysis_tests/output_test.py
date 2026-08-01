"""Unit tests for lcats.analysis.corpus.output."""

import pathlib
import unittest

from lcats.analysis.corpus import models
from lcats.analysis.corpus import output


class TestStoryDirValue(unittest.TestCase):
    """Tests for output.story_dir_value."""

    def test_canonical_bucket_file_returns_parent_name(self):
        path = pathlib.Path("collection/my_story/story.json")
        self.assertEqual("my_story", output.story_dir_value(path))

    def test_flat_file_returns_empty_string(self):
        path = pathlib.Path("collection/my_story.json")
        self.assertEqual("", output.story_dir_value(path))


class TestTsvColumns(unittest.TestCase):
    """Tests for the TSV_COLUMNS schema."""

    def test_story_dir_is_appended_at_the_end(self):
        self.assertEqual("story_dir", output.TSV_COLUMNS[-1])

    def test_empty_tsv_row_includes_story_dir(self):
        row = output.empty_tsv_row()
        self.assertIn("story_dir", row)
        self.assertEqual("", row["story_dir"])


class TestParseSpecialCharacterRows(unittest.TestCase):
    """Tests for output.parse_special_character_rows's story_dir population."""

    def test_bucket_file_populates_story_dir(self):
        tsv_output = "U+00A9\t©\tCOPYRIGHT SIGN\t1\t2\tctx\tlikely_good\tliteral"
        path = pathlib.Path("collection/my_story/story.json")

        rows = output.parse_special_character_rows(tsv_output, path, "Title")

        self.assertEqual(1, len(rows))
        self.assertEqual("my_story", rows[0]["story_dir"])
        self.assertEqual("story.json", rows[0]["story_file"])

    def test_flat_file_leaves_story_dir_empty(self):
        tsv_output = "U+00A9\t©\tCOPYRIGHT SIGN\t1\t2\tctx\tlikely_good\tliteral"
        path = pathlib.Path("collection/my_story.json")

        rows = output.parse_special_character_rows(tsv_output, path, "Title")

        self.assertEqual(1, len(rows))
        self.assertEqual("", rows[0]["story_dir"])


class TestFindingToRow(unittest.TestCase):
    """Tests for output.finding_to_row's story_dir population."""

    def test_bucket_file_populates_story_dir(self):
        finding = models.Finding(
            kind="start-contamination",
            severity="warning",
            span=(0, 10),
            evidence={"line": "By Author"},
            message="Likely author line at start of story.",
        )
        path = pathlib.Path("collection/my_story/story.json")

        row = output.finding_to_row(path, "Title", "boundary-contamination", finding)

        self.assertEqual("my_story", row["story_dir"])


class TestCleanRow(unittest.TestCase):
    """Tests for output.clean_row's story_dir population."""

    def test_bucket_file_populates_story_dir(self):
        path = pathlib.Path("collection/my_story/story.json")

        row = output.clean_row(path, "Title")

        self.assertEqual("my_story", row["story_dir"])

    def test_flat_file_leaves_story_dir_empty(self):
        path = pathlib.Path("collection/my_story.json")

        row = output.clean_row(path, "Title")

        self.assertEqual("", row["story_dir"])


if __name__ == "__main__":
    unittest.main()
