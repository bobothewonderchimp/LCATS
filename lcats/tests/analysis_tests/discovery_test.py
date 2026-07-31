"""Unit tests for lcats.analysis.corpus.discovery."""

import pathlib
import unittest

from lcats.utils import test_utils
from lcats.analysis.corpus import discovery


class TestIterCollectionStoryFiles(test_utils.TestCaseWithData):
    """Unit tests for discovery.iter_collection_story_files."""

    def setUp(self):
        super().setUp()
        self.root = pathlib.Path(self.test_temp_dir) / "collection"
        self.root.mkdir()

    def _write(self, relpath):
        p = self.root / relpath
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("{}", encoding="utf-8")
        return p

    def test_finds_flat_story_any_name(self):
        p = self._write("story1.json")
        found = list(discovery.iter_collection_story_files(self.root))
        self.assertEqual(found, [p])

    def test_finds_nested_bucket_story(self):
        p = self._write("story1/story.json")
        found = list(discovery.iter_collection_story_files(self.root))
        self.assertEqual(found, [p])

    def test_mixed_flat_and_bucket(self):
        flat = self._write("flat_story.json")
        bucket = self._write("bucket_story/story.json")
        found = set(discovery.iter_collection_story_files(self.root))
        self.assertEqual(found, {flat, bucket})

    def test_ignores_sidecar_json_in_bucket_dir(self):
        self._write("story1/story.json")
        self._write("story1/analysis.json")
        found = list(discovery.iter_collection_story_files(self.root))
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0].name, "story.json")

    def test_skips_subdir_without_canonical_file(self):
        self._write("empty_dir/notes.txt")
        found = list(discovery.iter_collection_story_files(self.root))
        self.assertEqual(found, [])

    def test_ignores_non_json_flat_files(self):
        self._write("readme.txt")
        found = list(discovery.iter_collection_story_files(self.root))
        self.assertEqual(found, [])

    def test_does_not_recurse_past_one_level(self):
        self._write("a/b/story.json")
        found = list(discovery.iter_collection_story_files(self.root))
        self.assertEqual(found, [])

    def test_nonexistent_dir_yields_nothing(self):
        found = list(discovery.iter_collection_story_files(self.root / "nonexistent"))
        self.assertEqual(found, [])


class TestFindJsonFiles(test_utils.TestCaseWithData):
    """Unit tests for discovery.find_json_files."""

    def setUp(self):
        super().setUp()
        self.root = pathlib.Path(self.test_temp_dir) / "corpus"
        self.root.mkdir()

    def _write(self, relpath):
        p = self.root / relpath
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("{}", encoding="utf-8")
        return p

    def test_finds_flat_story_at_collection_root(self):
        p = self._write("fantasy/story1.json")
        found = list(discovery.find_json_files([self.root]))
        self.assertIn(p, found)

    def test_finds_nested_bucket_story(self):
        p = self._write("fantasy/story1/story.json")
        found = list(discovery.find_json_files([self.root]))
        self.assertIn(p, found)

    def test_ignores_sidecar_json_in_bucket_dir(self):
        self._write("fantasy/story1/story.json")
        sidecar = self._write("fantasy/story1/analysis.json")
        found = list(discovery.find_json_files([self.root]))
        self.assertNotIn(sidecar, found)

    def test_mixed_layout_across_collections(self):
        flat = self._write("fantasy/story1.json")
        bucket = self._write("horror/story2/story.json")
        found = set(discovery.find_json_files([self.root]))
        self.assertEqual(found, {flat, bucket})

    def test_single_json_file_path_is_yielded(self):
        p = self._write("standalone.json")
        found = list(discovery.find_json_files([p]))
        self.assertEqual(found, [p])

    def test_nonexistent_directory_is_skipped_with_warning(self):
        found = list(discovery.find_json_files([self.root / "nonexistent"]))
        self.assertEqual(found, [])

    def test_works_when_pointed_directly_at_collection_dir(self):
        p = self._write("fantasy/story1.json")
        found = list(discovery.find_json_files([self.root / "fantasy"]))
        self.assertEqual(found, [p])

    def test_works_when_pointed_directly_at_story_bucket_dir(self):
        p = self._write("fantasy/story1/story.json")
        found = list(discovery.find_json_files([self.root / "fantasy" / "story1"]))
        self.assertEqual(found, [p])


if __name__ == "__main__":
    unittest.main()
