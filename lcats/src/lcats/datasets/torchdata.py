"""Basic JSON dataset loader."""

import os
import json
from torch.utils.data import Dataset

from lcats.analysis.corpus import discovery

# TODO(centaur): Do this in a more principled way.
DEFAULT_ROOT_DIR = "data"


class JsonDataset(Dataset):
    def __init__(self, root_dir=DEFAULT_ROOT_DIR, subdirectory=None):
        # Gather data in the subdirectory or the specified root.
        if subdirectory:
            self.data_dir = os.path.join(root_dir, subdirectory)
        else:
            self.data_dir = root_dir

        # Gather canonical story files (flat or per-story-bucket layout, per
        # Decision 3 of PROP-LCATS-STORY-BUCKET-LAYOUT) in the specified
        # directory and its subdirectories, via the same selector discovery.py
        # uses -- so this dataset stays in sync with the rest of the corpus
        # tooling instead of re-implementing its own traversal.
        self.file_paths = [
            str(path) for path in discovery.find_json_files([self.data_dir])
        ]

    def __len__(self):
        return len(self.file_paths)

    def __getitem__(self, idx):
        file_path = self.file_paths[idx]
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
