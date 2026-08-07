"""Dogfood check for assess_story() against a real Anthropic API call.

Regression check for the ASSESSMENT_TOOL schema fix: Anthropic's strict
tool-schema mode rejects `minimum`/`maximum` on `number`-type properties,
which previously caused every real (non-fake-backend) `assess_story()` call
to fail with a 400 (see git blame on assess.py's detected_genre_confidence
property). This script exercises the real AnthropicBackend end to end so
that regression is caught by more than unit tests, which use FakeBackend
and don't validate against Anthropic's real schema constraints.

Requires ANTHROPIC_API_KEY (env var or <repo_root>/.secrets/anthropic_api_keys.env,
i.e. the repo root's .secrets/, not lcats/.secrets/ - see
lcats/docs/secrets-setup.md). Makes one real API call.
"""

from __future__ import annotations

import argparse
import os
import pathlib
import sys

_LCATS_SRC = pathlib.Path(__file__).resolve().parents[2] / "src"
if str(_LCATS_SRC) not in sys.path:
    sys.path.insert(0, str(_LCATS_SRC))

from lcats.utils import secrets  # noqa: E402

_DEFAULT_STORY = (
    pathlib.Path(__file__).resolve().parents[3]
    / "corpora"
    / "lovecraft"
    / "the_case_of_charles_dexter_ward"
    / "story.json"
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "story_path",
        type=pathlib.Path,
        nargs="?",
        default=_DEFAULT_STORY,
        help=f"Corpus story JSON to assess (default: {_DEFAULT_STORY})",
    )
    parser.add_argument(
        "--genre", default="", help="Claimed genre (default: detect-only mode)"
    )
    parser.add_argument("--max-tokens", type=int, default=16384)
    args = parser.parse_args()

    secrets.load_secrets()
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print(
            "FAIL: ANTHROPIC_API_KEY not set. Export it, or add it to "
            "<repo_root>/.secrets/anthropic_api_keys.env (see lcats/docs/secrets-setup.md)."
        )
        return 1

    from lcats.analysis.corpus import assess
    from lcats.llm import anthropic_backend

    backend = anthropic_backend.AnthropicBackend()
    result = assess.assess_story(
        args.story_path,
        genre=args.genre,
        backend=backend,
        max_tokens=args.max_tokens,
    )

    print(f"story: {args.story_path}")
    print(f"verdict: {result.verdict}")
    print(f"detected_genre: {result.detected_genre}")
    print(f"detected_genre_confidence: {result.detected_genre_confidence}")
    print(f"error: {result.error}")

    if result.error:
        print("FAIL: assess_story() returned an error.")
        return 1

    print("OK: real API call to assess_story() succeeded.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
