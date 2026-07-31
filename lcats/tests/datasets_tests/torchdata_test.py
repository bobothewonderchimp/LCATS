"""Unit tests for lcats.datasets.torchdata.JsonDataset."""

import json
import os
import tempfile
import unittest

from lcats.datasets import torchdata


class TestJsonDataset(unittest.TestCase):
    """Tests for JsonDataset's dual-layout file discovery."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        import shutil

        shutil.rmtree(self.tmp)

    def _write(self, relpath, data):
        path = os.path.join(self.tmp, relpath)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f)
        return path

    def test_finds_flat_story(self):
        self._write("collection/story1.json", {"name": "Flat1"})
        dataset = torchdata.JsonDataset(root_dir=self.tmp)
        self.assertEqual(len(dataset), 1)
        self.assertEqual(dataset[0]["name"], "Flat1")

    def test_finds_nested_bucket_story(self):
        self._write("collection/story1/story.json", {"name": "Bucket1"})
        dataset = torchdata.JsonDataset(root_dir=self.tmp)
        self.assertEqual(len(dataset), 1)
        self.assertEqual(dataset[0]["name"], "Bucket1")

    def test_ignores_sidecar_json_in_bucket_dir(self):
        self._write("collection/story1/story.json", {"name": "Bucket1"})
        self._write("collection/story1/analysis.json", {"unrelated": "data"})
        dataset = torchdata.JsonDataset(root_dir=self.tmp)
        self.assertEqual(len(dataset), 1)

    def test_subdirectory_argument_scopes_search(self):
        self._write("collectionA/story1.json", {"name": "A1"})
        self._write("collectionB/story2.json", {"name": "B1"})
        dataset = torchdata.JsonDataset(root_dir=self.tmp, subdirectory="collectionA")
        self.assertEqual(len(dataset), 1)
        self.assertEqual(dataset[0]["name"], "A1")


if __name__ == "__main__":
    unittest.main()
