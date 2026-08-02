"""Unit tests for lcats.analysis.corpus.cli.infer_story_title."""

import pathlib
import unittest

from lcats.analysis.corpus import cli


class TestInferStoryTitle(unittest.TestCase):
    """Tests for cli.infer_story_title."""

    def test_bucket_layout_falls_back_to_directory_slug(self):
        data = {}
        path = pathlib.Path("collection/my_story/story.json")
        self.assertEqual(cli.infer_story_title(data, path), "my_story")

    def test_bucket_layout_prefers_directory_slug_over_name_field(self):
        """Regression test for Decision 2 of PROP-LCATS-STORY-BUCKET-LAYOUT:
        the directory slug is the primary identifier for a canonical
        story.json file, even when a (mutable, non-unique) name field is
        also present -- metadata must not override it."""
        data = {"name": "Mutable Metadata Title"}
        path = pathlib.Path("collection/my_story/story.json")
        self.assertEqual(cli.infer_story_title(data, path), "my_story")

    def test_bucket_layout_prefers_directory_slug_over_metadata_name(self):
        data = {"metadata": {"name": "Mutable Metadata Title"}}
        path = pathlib.Path("collection/my_story/story.json")
        self.assertEqual(cli.infer_story_title(data, path), "my_story")

    def test_data_argument_is_entirely_ignored(self):
        """Regression test for Decision 4 (dual-layout retraction):
        infer_story_title no longer has any conditional flat-vs-bucket
        logic -- it always returns the parent directory slug, regardless
        of story data content."""
        data = {"name": "Anything At All", "metadata": {"name": "Also Anything"}}
        path = pathlib.Path("collection/my_story/story.json")
        self.assertEqual(cli.infer_story_title(data, path), "my_story")

    def test_returns_parent_directory_name_regardless_of_leaf_filename(self):
        """infer_story_title no longer branches on the leaf filename at
        all -- every discoverable file is a bucket file post-retraction, so
        the parent directory name is returned unconditionally."""
        data = {}
        path = pathlib.Path("collection/my_story/anything.json")
        self.assertEqual(cli.infer_story_title(data, path), "my_story")


if __name__ == "__main__":
    unittest.main()
