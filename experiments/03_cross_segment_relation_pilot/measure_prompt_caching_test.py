"""Unit tests for measure_prompt_caching.py.

Not part of the installed lcats package (lives under experiments/, not
lcats/src/lcats/), so not discovered by lcats' scripts/test - run
explicitly:

    python -m unittest experiments/03_cross_segment_relation_pilot/measure_prompt_caching_test.py
"""

from __future__ import annotations

import json
import pathlib
import sys
import tempfile
import types
import unittest

from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import measure_prompt_caching  # noqa: E402 - see sys.path.insert above

from lcats.llm import backend as llm_backend  # noqa: E402


class _FixedResponseBackend:
    """Returns one fixed BackendResponse for every complete() call,
    carrying real cache-field values so _RecordingBackend's own
    pass-through/recording logic can be verified independently of the
    real pipeline's segmentation/extraction machinery."""

    def __init__(self, cache_read: int, cache_creation: int):
        self._cache_read = cache_read
        self._cache_creation = cache_creation

    def complete(self, **kwargs):
        return llm_backend.BackendResponse(
            text="",
            tool_result={},
            model="fake-1.0",
            input_tokens=100,
            output_tokens=10,
            cache_creation_input_tokens=self._cache_creation,
            cache_read_input_tokens=self._cache_read,
            raw=None,
        )


class TestRecordingBackend(unittest.TestCase):
    """_RecordingBackend is the one genuinely new piece of logic this
    work item adds - a thin, real (not fake-backend-only) wrapper. Test
    it directly, independent of the real pipeline."""

    def test_records_every_call_in_order_with_real_cache_fields(self):
        inner = _FixedResponseBackend(cache_read=512, cache_creation=0)
        recorder = measure_prompt_caching._RecordingBackend(inner)

        recorder.complete(system="s1", messages=[], model="m", tool={"name": "tool_a"})
        recorder.complete(system="s2", messages=[], model="m", tool={"name": "tool_b"})

        self.assertEqual(len(recorder.calls), 2)
        self.assertEqual(recorder.calls[0]["tool_name"], "tool_a")
        self.assertEqual(recorder.calls[1]["tool_name"], "tool_b")
        for call in recorder.calls:
            self.assertEqual(call["input_tokens"], 100)
            self.assertEqual(call["output_tokens"], 10)
            self.assertEqual(call["cache_read_input_tokens"], 512)
            self.assertEqual(call["cache_creation_input_tokens"], 0)

    def test_delegates_the_real_response_through_unchanged(self):
        inner = _FixedResponseBackend(cache_read=0, cache_creation=200)
        recorder = measure_prompt_caching._RecordingBackend(inner)

        response = recorder.complete(system="s", messages=[], model="m")

        self.assertIsInstance(response, llm_backend.BackendResponse)
        self.assertEqual(response.cache_creation_input_tokens, 200)

    def test_a_present_zero_cache_read_is_recorded_as_zero_not_none(self):
        """A real cache miss (cache_read_input_tokens=0, present) must be
        distinguishable from caching not being in use at all (None) -
        the whole point of surfacing these fields (WI-PILOT-0057)."""
        inner = _FixedResponseBackend(cache_read=0, cache_creation=50)
        recorder = measure_prompt_caching._RecordingBackend(inner)

        recorder.complete(system="s", messages=[], model="m")

        self.assertEqual(recorder.calls[0]["cache_read_input_tokens"], 0)
        self.assertIsNotNone(recorder.calls[0]["cache_read_input_tokens"])


class TestRunComparisonDryRun(unittest.TestCase):
    """End-to-end wiring check using the CLI's own zero-cost dry-run
    fake (_DryRunFakeBackend) against the real, committed WI-PILOT-0051
    fixture set - proves the full segment -> extract -> record -> report
    pipeline runs without error, and that the checkpoint-reuse design
    (segmentation billed once, not twice, across the two comparison
    arms) actually behaves as documented."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.output_dir = pathlib.Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_dry_run_produces_a_report_with_both_arms(self):
        report = measure_prompt_caching.run_comparison(
            model="claude-opus-4-8",
            working_root=self.output_dir,
            source_root=measure_prompt_caching._fixtures_dir(),
            dry_run=True,
        )

        self.assertIn("caching_disabled", report["runs"])
        self.assertIn("caching_enabled", report["runs"])
        self.assertFalse(report["runs"]["caching_disabled"]["enable_prompt_caching"])
        self.assertTrue(report["runs"]["caching_enabled"]["enable_prompt_caching"])

    def test_segmentation_checkpoint_is_reused_across_both_arms(self):
        """The second arm to run must make fewer real backend calls than
        the first, by exactly one segmentation call per story - proving
        _segment_story_cached's checkpoint is actually shared across
        both comparison runs, not re-paid for twice."""
        report = measure_prompt_caching.run_comparison(
            model="claude-opus-4-8",
            working_root=self.output_dir,
            source_root=measure_prompt_caching._fixtures_dir(),
            dry_run=True,
        )

        num_stories = len(report["stories"])
        first_arm_calls = len(report["runs"]["caching_disabled"]["calls"])
        second_arm_calls = len(report["runs"]["caching_enabled"]["calls"])
        self.assertEqual(first_arm_calls - second_arm_calls, num_stories)

    def test_report_is_json_serializable_and_written_to_disk(self):
        measure_prompt_caching.run_comparison(
            model="claude-opus-4-8",
            working_root=self.output_dir,
            source_root=measure_prompt_caching._fixtures_dir(),
            dry_run=True,
        )
        # run_comparison itself doesn't write the file - main() does -
        # so directly verify the report round-trips through json.dumps,
        # matching what main() does with it.
        report = measure_prompt_caching.run_comparison(
            model="claude-opus-4-8",
            working_root=self.output_dir,
            source_root=measure_prompt_caching._fixtures_dir(),
            dry_run=True,
        )
        json.dumps(report)  # must not raise


class TestPreflightPrefixTokenCounts(unittest.TestCase):
    """preflight_prefix_token_counts (Required Change 3) - mocked, since
    count_tokens is still a real, live API call even though it's free/
    non-generation; this test never touches the network."""

    def test_counts_every_extractor_with_a_tool_schema(self):
        stub_client = types.SimpleNamespace(
            messages=types.SimpleNamespace(
                count_tokens=lambda **kwargs: types.SimpleNamespace(input_tokens=42)
            )
        )
        with patch("anthropic.Anthropic", return_value=stub_client):
            counts = measure_prompt_caching.preflight_prefix_token_counts(
                "claude-opus-4-8"
            )

        # run_pilot._build_erw_extractors builds entity/event/relation/
        # discourse/story_relation - all five carry a tool_schema.
        self.assertEqual(
            set(counts.keys()),
            {"entity", "event", "relation", "discourse", "story_relation"},
        )
        for count in counts.values():
            self.assertEqual(count, 42)

    def test_sends_cache_control_on_both_system_and_tool(self):
        captured_calls = []

        def _fake_count_tokens(**kwargs):
            captured_calls.append(kwargs)
            return types.SimpleNamespace(input_tokens=10)

        stub_client = types.SimpleNamespace(
            messages=types.SimpleNamespace(count_tokens=_fake_count_tokens)
        )
        with patch("anthropic.Anthropic", return_value=stub_client):
            measure_prompt_caching.preflight_prefix_token_counts("claude-opus-4-8")

        self.assertGreater(len(captured_calls), 0)
        for call in captured_calls:
            self.assertEqual(call["system"][0]["cache_control"], {"type": "ephemeral"})
            self.assertEqual(call["tools"][0]["cache_control"], {"type": "ephemeral"})


if __name__ == "__main__":
    unittest.main()
