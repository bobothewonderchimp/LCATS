"""Unit tests for lcats.analysis.corpus.cli.infer_story_title."""

import pathlib
import unittest

from lcats.analysis.corpus import cli


class TestInferStoryTitle(unittest.TestCase):
    """Tests for cli.infer_story_title."""

    def test_uses_name_field_when_present(self):
        data = {"name": "Explicit Title"}
        path = pathlib.Path("collection/story.json")
        self.assertEqual(cli.infer_story_title(data, path), "Explicit Title")

    def test_uses_metadata_name_when_top_level_name_absent(self):
        data = {"metadata": {"name": "Metadata Title"}}
        path = pathlib.Path("collection/story.json")
        self.assertEqual(cli.infer_story_title(data, path), "Metadata Title")

    def test_flat_layout_falls_back_to_file_stem(self):
        data = {}
        path = pathlib.Path("collection/my_story.json")
        self.assertEqual(cli.infer_story_title(data, path), "my_story")

    def test_bucket_layout_falls_back_to_directory_slug(self):
        data = {}
        path = pathlib.Path("collection/my_story/story.json")
        self.assertEqual(cli.infer_story_title(data, path), "my_story")

    def test_blank_name_field_falls_back(self):
        data = {"name": "   "}
        path = pathlib.Path("collection/my_story/story.json")
        self.assertEqual(cli.infer_story_title(data, path), "my_story")


if __name__ == "__main__":
    unittest.main()
