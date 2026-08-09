"""Unit tests for lcats.analysis.corpus.annotate."""

import json
import pathlib
import tempfile
import unittest

from lcats.analysis.corpus import annotate
from lcats.utils import checkpoint

_GENRE_TOOL_RESULT = {
    "verdict": "include",
    "wellformed": True,
    "detected_genre": "science fiction",
    "detected_genre_confidence": 0.9,
    "genre_verdict": "detected",
    "specials_verdict": "none",
    "summary": "A story about a dragon.",
    "issues": [],
    "exclude_reason": "",
    "genre_suggestion": "",
    "secondary_genre": "",
}

_SEGMENT_TOOL_RESULT = {
    "segments": [
        {
            "segment_id": 1,
            "segment_type": "narrative_scene",
            "start_par_id": 1,
            "end_par_id": 1,
            # Deliberately empty: this fixture is reused across tests with
            # different story bodies ("Once upon a time there was a
            # dragon.", "A dragon story.", etc.). Empty anchors fall back
            # to paragraph bounds unconditionally (align_segment's
            # existing, unaffected contract) -- a hardcoded non-empty
            # anchor matching only one body used to silently "work" for
            # all of them under the old lenient fallback (a genuinely
            # unresolvable anchor fell back to paragraph bounds too, not
            # just an empty one); WI-SEGMENT-0059 correctly rejects that
            # case now, so this fixture must not rely on it.
            "start_exact": "",
            "end_exact": "",
            "start_prefix": "",
            "end_suffix": "",
            "start_char": None,
            "end_char": None,
            "summary": "A dragon appears.",
            "cohesion": {
                "time": "once upon a time",
                "place": "unspecified",
                "characters": ["dragon"],
            },
            "gacd": None,
            "erac": None,
            "reason": "Establishes setting.",
            "confidence": 0.8,
        }
    ]
}


class _DualToolFakeBackend:
    """Test double dispatching on tool["name"] -- annotate_story calls
    both assess_story (record_story_assessment) and make_segment_extractor
    (record_segments) through the same backend, so a single fixed
    tool_result (what FakeBackend provides) can't serve both.

    fail_genre_calls_after, if set, makes the Nth-and-later genre call
    return tool_result=None (assess_story's own "no tool result" failure
    path), for testing stale-sidecar-removal on a failed recompute.
    """

    def __init__(self, fail_genre_calls_after=None):
        self.calls = []
        self.fail_genre_calls_after = fail_genre_calls_after
        self._genre_call_count = 0

    def complete(
        self, *, system, messages, model, temperature=0.2, max_tokens=4096, tool=None
    ):
        from lcats.llm import backend as backend_module

        self.calls.append({"tool_name": tool["name"] if tool else None, "model": model})
        if tool and tool["name"] == "record_story_assessment":
            self._genre_call_count += 1
            if (
                self.fail_genre_calls_after is not None
                and self._genre_call_count > self.fail_genre_calls_after
            ):
                result = None
            else:
                result = _GENRE_TOOL_RESULT
        elif tool and tool["name"] == "record_segments":
            result = _SEGMENT_TOOL_RESULT
        else:
            result = None
        return backend_module.BackendResponse(
            text="",
            tool_result=result,
            model=model,
            input_tokens=0,
            output_tokens=0,
            raw=None,
        )


def _write_story(collection_dir: pathlib.Path, name: str, body: str) -> pathlib.Path:
    bucket_dir = collection_dir / name
    bucket_dir.mkdir(parents=True, exist_ok=True)
    story_path = bucket_dir / "story.json"
    story_path.write_text(
        json.dumps({"name": name, "body": body, "metadata": {}}),
        encoding="utf-8",
    )
    return story_path


class StoryItemIdTest(unittest.TestCase):
    def test_combines_collection_and_story(self):
        self.assertEqual(
            "sherlock__blue_carbuncle",
            annotate.story_item_id("sherlock", "blue_carbuncle"),
        )


class ErrorMessageTest(unittest.TestCase):
    """Regression coverage: str()-ing a structured api_error dict produces
    noisy Python-repr output and discards the clean message field (review
    finding, PR #241)."""

    def test_extracts_message_from_dict_error(self):
        error = {"status": 429, "code": "quota_exceeded", "message": "No credits."}
        self.assertEqual("No credits.", annotate._error_message(error))

    def test_falls_back_to_str_for_plain_string_error(self):
        self.assertEqual(
            "alignment failed: x", annotate._error_message("alignment failed: x")
        )


class AnnotateStoryTest(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        self.tmp_path = pathlib.Path(self._tmpdir.name)
        self.source_root = self.tmp_path / "data"
        self.checkpoint_dir = self.tmp_path / "checkpoints"
        self.source_root.mkdir()
        self.roots = checkpoint.resolve_roots(
            working_root=self.checkpoint_dir, source_root=self.source_root
        )

    def test_writes_genre_and_scenes_sidecars(self):
        story_path = _write_story(
            self.source_root / "collection_a",
            "story_one",
            "Once upon a time there was a dragon.",
        )
        backend = _DualToolFakeBackend()

        result = annotate.annotate_story(
            story_path,
            collection_name="collection_a",
            backend=backend,
            model="fake-model",
            roots=self.roots,
        )

        self.assertTrue(result.clean)
        bucket_dir = story_path.parent
        genre_data = json.loads((bucket_dir / "genre.json").read_text(encoding="utf-8"))
        self.assertEqual("science fiction", genre_data["detected_genre"])
        scenes_data = json.loads(
            (bucket_dir / "scenes.json").read_text(encoding="utf-8")
        )
        self.assertEqual(1, scenes_data["segment_count"])
        # scenes.json carries the same cost-visibility fields genre.json
        # already does, sourced from JSONPromptExtractor.extract()'s own
        # "usage" dict rather than left unrecorded (review finding, PR
        # #253).
        self.assertIn("input_tokens", scenes_data)
        self.assertIn("output_tokens", scenes_data)

    def test_writes_readme_summarizing_sidecars(self):
        story_path = _write_story(
            self.source_root / "collection_a", "story_one", "A dragon story."
        )
        backend = _DualToolFakeBackend()

        annotate.annotate_story(
            story_path,
            collection_name="collection_a",
            backend=backend,
            model="fake-model",
            roots=self.roots,
        )

        readme = (story_path.parent / "README.md").read_text(encoding="utf-8")
        self.assertIn("science fiction", readme)
        self.assertIn("segment_count", readme)

    def test_second_call_with_same_config_skips_api_calls(self):
        """Checkpoint hit: a resumed run under an unchanged config must not
        repeat the paid LLM calls."""
        story_path = _write_story(
            self.source_root / "collection_a", "story_one", "A dragon story."
        )
        backend = _DualToolFakeBackend()

        annotate.annotate_story(
            story_path,
            collection_name="collection_a",
            backend=backend,
            model="fake-model",
            roots=self.roots,
        )
        first_call_count = len(backend.calls)
        self.assertEqual(2, first_call_count)  # one genre call, one scenes call

        annotate.annotate_story(
            story_path,
            collection_name="collection_a",
            backend=backend,
            model="fake-model",
            roots=self.roots,
        )

        self.assertEqual(first_call_count, len(backend.calls))

    def test_changed_body_invalidates_checkpoint(self):
        """A corrected story must not silently serve a stale cache -- the
        fingerprint must hash the actual input, not just model config."""
        story_path = _write_story(
            self.source_root / "collection_a", "story_one", "First version."
        )
        backend = _DualToolFakeBackend()
        annotate.annotate_story(
            story_path,
            collection_name="collection_a",
            backend=backend,
            model="fake-model",
            roots=self.roots,
        )
        first_call_count = len(backend.calls)

        story_path.write_text(
            json.dumps(
                {
                    "name": "story_one",
                    "body": "A completely different revised story.",
                    "metadata": {},
                }
            ),
            encoding="utf-8",
        )
        annotate.annotate_story(
            story_path,
            collection_name="collection_a",
            backend=backend,
            model="fake-model",
            roots=self.roots,
        )

        self.assertGreater(len(backend.calls), first_call_count)

    def test_resumed_sidecar_rewritten_from_checkpoint_data(self):
        """Deleting the sidecar file (simulating an interrupted
        materialization step) must not force a re-paid API call -- the
        checkpoint's own stored data is the source of truth for re-writing
        it."""
        story_path = _write_story(
            self.source_root / "collection_a", "story_one", "A dragon story."
        )
        backend = _DualToolFakeBackend()
        annotate.annotate_story(
            story_path,
            collection_name="collection_a",
            backend=backend,
            model="fake-model",
            roots=self.roots,
        )
        call_count = len(backend.calls)
        (story_path.parent / "genre.json").unlink()

        annotate.annotate_story(
            story_path,
            collection_name="collection_a",
            backend=backend,
            model="fake-model",
            roots=self.roots,
        )

        self.assertEqual(call_count, len(backend.calls))
        self.assertTrue((story_path.parent / "genre.json").is_file())

    def test_stale_genre_sidecar_removed_when_recompute_fails(self):
        """A failed recompute must not leave a stale genre.json from a
        prior, differently-configured run in place -- the bucket would
        otherwise silently mix a new-config scenes.json with an
        old-config genre.json (review finding, PR #241)."""
        story_path = _write_story(
            self.source_root / "collection_a", "story_one", "A dragon story."
        )
        backend = _DualToolFakeBackend(fail_genre_calls_after=1)
        annotate.annotate_story(
            story_path,
            collection_name="collection_a",
            backend=backend,
            model="fake-model",
            roots=self.roots,
        )
        self.assertTrue((story_path.parent / "genre.json").is_file())

        # A body change invalidates the checkpoint, forcing a real
        # recompute -- which this backend is configured to fail.
        story_path.write_text(
            json.dumps(
                {"name": "story_one", "body": "A different story now.", "metadata": {}}
            ),
            encoding="utf-8",
        )
        result = annotate.annotate_story(
            story_path,
            collection_name="collection_a",
            backend=backend,
            model="fake-model",
            roots=self.roots,
        )

        self.assertFalse(result.clean)
        self.assertIsNotNone(result.genre_error)
        self.assertFalse((story_path.parent / "genre.json").exists())


class AnnotateCollectionTest(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        self.tmp_path = pathlib.Path(self._tmpdir.name)
        self.source_root = self.tmp_path / "data"
        self.checkpoint_dir = self.tmp_path / "checkpoints"
        self.source_root.mkdir()
        self.roots = checkpoint.resolve_roots(
            working_root=self.checkpoint_dir, source_root=self.source_root
        )

    def test_annotates_every_story_in_collection(self):
        collection_dir = self.source_root / "collection_a"
        _write_story(collection_dir, "story_one", "First story.")
        _write_story(collection_dir, "story_two", "Second story.")
        backend = _DualToolFakeBackend()

        results = annotate.annotate_collection(
            collection_dir, backend=backend, model="fake-model", roots=self.roots
        )

        self.assertEqual(2, len(results))
        self.assertTrue(all(r.clean for r in results))

    def test_missing_collection_raises_instead_of_silently_succeeding(self):
        """A missing/empty collection must not let `lcats annotate
        <collection>` appear to succeed while doing nothing (review
        finding, PR #241)."""
        missing_dir = self.source_root / "does_not_exist"
        backend = _DualToolFakeBackend()

        with self.assertRaises(annotate.EmptyCollectionError):
            annotate.annotate_collection(
                missing_dir, backend=backend, model="fake-model", roots=self.roots
            )

    def test_empty_collection_directory_raises(self):
        empty_dir = self.source_root / "empty_collection"
        empty_dir.mkdir()
        backend = _DualToolFakeBackend()

        with self.assertRaises(annotate.EmptyCollectionError):
            annotate.annotate_collection(
                empty_dir, backend=backend, model="fake-model", roots=self.roots
            )


class AnnotateCollectionsTest(unittest.TestCase):
    """Regression coverage for the corpus-root vs. per-collection selector
    bug (review finding, PR #226): iterating a multi-collection root must
    process every collection, not silently yield nothing."""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        self.tmp_path = pathlib.Path(self._tmpdir.name)
        self.source_root = self.tmp_path / "data"
        self.checkpoint_dir = self.tmp_path / "checkpoints"
        self.source_root.mkdir()
        _write_story(self.source_root / "collection_a", "story_one", "Story A1.")
        _write_story(self.source_root / "collection_b", "story_one", "Story B1.")
        self.roots = checkpoint.resolve_roots(
            working_root=self.checkpoint_dir, source_root=self.source_root
        )

    def test_annotates_every_collection_under_root_by_default(self):
        backend = _DualToolFakeBackend()

        results = annotate.annotate_collections(
            self.source_root, backend=backend, model="fake-model", roots=self.roots
        )

        self.assertEqual({"collection_a", "collection_b"}, set(results.keys()))
        self.assertEqual(1, len(results["collection_a"]))
        self.assertEqual(1, len(results["collection_b"]))

    def test_collection_names_filters_to_requested_subset(self):
        backend = _DualToolFakeBackend()

        results = annotate.annotate_collections(
            self.source_root,
            backend=backend,
            model="fake-model",
            roots=self.roots,
            collection_names=["collection_a"],
        )

        self.assertEqual({"collection_a"}, set(results.keys()))
