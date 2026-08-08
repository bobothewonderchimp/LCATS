"""Collect per-genre statistics from the annotation feasibility trial's
output sidecars, comparing lcats annotate's detected_genre against this
subset's hand-picked provisional_genre (see select_subset.py).

Run from lcats/:
    python3 experimental/annotation_feasibility_trial/collect_stats.py
"""

from __future__ import annotations

import collections
import json
import pathlib
import statistics

from lcats.analysis import text_segmenter

HERE = pathlib.Path(__file__).resolve().parent
TRIAL_DIR = HERE / "source" / "trial"
MANIFEST_PATH = HERE / "subset_manifest.md"
REPORT_PATH = HERE / "stats_report.md"

# A corrupted secondary_genre value contains leaked tool-call-syntax
# fragments (e.g. '</antml=parameter>\n<parameter name="specials_verdict">')
# instead of a genre tag -- observed in 10/24 stories in the real run this
# script analyzes. Detecting on these substrings (rather than e.g. "any
# value containing '<'") avoids false-flagging a legitimate secondary
# genre that happens to mention a comparison operator or similar.
_CORRUPTION_MARKERS = ("</antml", "<parameter", "antml:")


def _is_corrupted(value: str) -> bool:
    return any(marker in value for marker in _CORRUPTION_MARKERS)


def _segment_overlap_chars(segments: list[dict]) -> int:
    """Sum of overlap (in chars) between consecutive segments, ordered by
    segment_id. A correctly aligned scene-segmentation run partitions the
    story text into non-overlapping spans; any overlap means at least one
    segment's start_char/end_char was misaligned."""
    ordered = sorted(
        (s for s in segments if isinstance(s.get("start_char"), int)),
        key=lambda s: s["segment_id"],
    )
    overlap = 0
    prev_end = -1
    for seg in ordered:
        start = seg["start_char"]
        end = seg.get("end_char", start)
        if start < prev_end:
            overlap += prev_end - start
        prev_end = max(prev_end, end)
    return overlap


def _paragraph_collapse(body: str) -> bool:
    """True if text_segmenter's paragraph indexer -- which splits on a
    literal blank line ("\\n\\n") -- collapses this story's body into a
    single paragraph spanning the whole text. When that happens, every
    segment's start_par_id/end_par_id is forced to 1, so the search range
    align_segment uses for every anchor becomes the entire document; a
    single failed anchor search then silently falls back to end-of-text
    instead of a tight local range (text_segmenter.py's align_segment,
    line ~146), producing wrong, overlapping offsets rather than a loud
    error. Observed on all 3 stories sourced from corpora/london in this
    trial (single-newline paragraph formatting, no blank-line breaks)."""
    _, meta = text_segmenter.paragraph_text_indexer(body)
    return meta["n_paragraphs"] <= 1 and len(body) > 2000


def read_manifest() -> list[tuple[str, str]]:
    rows = []
    with open(MANIFEST_PATH, encoding="utf-8") as f:
        for line in f:
            if not line.startswith("| ") or "|---|" in line:
                continue
            if line.startswith("| source (corpora/)"):
                continue
            parts = [p.strip() for p in line.strip().strip("|").split("|")]
            if len(parts) != 4:
                continue
            src, genre, _rationale, _blen = parts
            story_name = src.split("/", 1)[1]
            rows.append((story_name, genre))
    return rows


def collect_rows(manifest_rows: list[tuple[str, str]]) -> list[dict]:
    rows = []
    for story_name, provisional in manifest_rows:
        story_dir = TRIAL_DIR / story_name
        genre_data = json.loads((story_dir / "genre.json").read_text(encoding="utf-8"))
        scenes_data = json.loads(
            (story_dir / "scenes.json").read_text(encoding="utf-8")
        )
        secondary_raw = genre_data.get("secondary_genre", "")
        story_data = json.loads((story_dir / "story.json").read_text(encoding="utf-8"))
        body = story_data.get("body", "")
        segments = scenes_data.get("segments", [])
        rows.append(
            {
                "story": story_name,
                "provisional": provisional,
                "detected": genre_data["detected_genre"],
                "confidence": genre_data["detected_genre_confidence"],
                "secondary": secondary_raw,
                "secondary_corrupted": _is_corrupted(secondary_raw),
                "match": provisional == genre_data["detected_genre"],
                "scene_count": len(segments),
                "input_tokens": genre_data.get("input_tokens", 0),
                "output_tokens": genre_data.get("output_tokens", 0),
                "segment_overlap_chars": _segment_overlap_chars(segments),
                "paragraph_collapse": _paragraph_collapse(body),
            }
        )
    return rows


def write_report(rows: list[dict]) -> None:
    by_genre: dict[str, list[dict]] = collections.defaultdict(list)
    for row in rows:
        by_genre[row["provisional"]].append(row)

    lines = [
        "# Annotation feasibility trial: stats report",
        "",
        "`lcats annotate` run against the 24-story subset in "
        "`subset_manifest.md` (3 stories x 8 `VALID_GENRES`). "
        "`provisional_genre` is the hand-picked guess used to build the "
        "subset (no paid API call); `detected_genre` is `lcats annotate`'s "
        "actual output, compared here for feasibility signal, not as a "
        "ground-truth accuracy benchmark (the provisional guess itself is "
        "informal).",
        "",
        "## Run",
        "",
        "- Real API run: `claude-opus-4-8`, 24 stories, real time **17m39s** "
        "(`time lcats annotate --source "
        "experimental/annotation_feasibility_trial/source`).",
        f"- Genre-detection call token totals: "
        f"{sum(r['input_tokens'] for r in rows):,} input / "
        f"{sum(r['output_tokens'] for r in rows):,} output. Exact USD "
        "cost not computed here (no pricing constant lives in this repo "
        "-- checking the Anthropic Console billing dashboard for the run "
        "window is more reliable than a hand-typed price-per-token "
        "figure that could go stale).",
        "- Scene-segmentation call token usage for **this specific run** "
        "is not available: at the time this run executed, "
        "`_annotate_scenes` (`annotate.py`) discarded the token usage "
        "`JSONPromptExtractor.extract()` already returns, so `scenes.json` "
        "stored only `segments`/`segment_count`/`model`. Fixed in this "
        "same PR (`annotate.py` now records `input_tokens`/"
        "`output_tokens` in `scenes.json`, matching `genre.json`) -- "
        "every future run will have complete data. Deliberately not "
        "re-running this trial's already-good segmentation results "
        "solely to backfill token counts for this report -- that would "
        "spend real API budget for reporting completeness alone, against "
        "this item's own Risk Notes to keep this first run small.",
        "- `lcats promote`'s `survey_collection` gate: **clean** (0 "
        "mojibake findings, 0 malformed-sidecar findings across all 24 "
        "stories) -- this checks JSON validity and required-field shape "
        "only. It does not catch either data quality finding below: "
        "neither corrupted `secondary_genre` text nor overlapping scene "
        "`start_char`/`end_char` offsets change a sidecar's required-key "
        "shape.",
        "",
    ]

    collapsed = [r for r in rows if r["paragraph_collapse"]]
    overlapping = [r for r in rows if r["segment_overlap_chars"] > 0]
    lines += [
        "## Data quality finding: scene-segmentation offset corruption "
        "(most severe finding in this run)",
        "",
        f"**{len(collapsed)}/{len(rows)} stories have single-paragraph "
        f"source text** (`text_segmenter.paragraph_text_indexer` finds no "
        "blank-line paragraph breaks at all -- the whole story collapses "
        "into one `[P0001]` block), and **all "
        f"{len(collapsed)} of those show corrupted scene segmentation**: "
        f"{len(overlapping)} with overlapping segment offsets, the rest "
        "degenerate (a single segment spanning the entire story, no real "
        "segmentation at all). Unlike the `secondary_genre` finding below, "
        "this corrupts the actual `start_char`/`end_char` fields "
        "downstream consumers would use to slice the story text -- a "
        "real correctness defect, not a cosmetic one.",
        "",
        "**Root cause, traced to `text_segmenter.py`:** "
        "`build_paragraph_index` splits only on a literal blank line "
        "(`\\n\\n`); a story formatted with single-newline paragraph "
        "breaks (all 3 affected stories here are from `corpora/london`) "
        "collapses to `n_paragraphs=1`, so every segment's "
        "`start_par_id`/`end_par_id` is forced to 1 and `align_segment`'s "
        "search range becomes the *entire document* for every segment. "
        "When `find_anchor_in_range` then fails to locate a segment's "
        "`end_exact` text verbatim (`align_segment`, "
        "`text_segmenter.py` around line 146), the function silently "
        "falls back to `hi` -- the end of the search range, i.e. "
        "end-of-document -- instead of raising an alignment error. The "
        "result is a spurious full-document-length segment that "
        "overlaps every segment after it, with no `alignment_error` or "
        "`validation_error` raised to catch it (verified: `annotate.py`'s "
        "existing alignment/validation-error rejection did not fire for "
        "any of these 3 stories).",
        "",
        "Affected stories:",
        "",
    ]
    for row in collapsed:
        detail = (
            f"{row['segment_overlap_chars']:,} overlapping chars across "
            f"{row['scene_count']} segments"
            if row["segment_overlap_chars"] > 0
            else f"degenerate: {row['scene_count']} segment spanning the "
            "entire story"
        )
        lines.append(f"- `{row['story']}`: {detail}")
    lines += [
        "",
        "**Not fixed here** -- `align_segment`/`build_paragraph_index` "
        "are shared library code in `text_segmenter.py`, used by other "
        "callers beyond `lcats annotate` (`story_processors.py`, "
        "`run_pilot.py`, `notebooks/12_extract_scenes.ipynb` per "
        "`scene_analysis.py`'s own docstring) -- a fix needs its own "
        "design and test coverage against all of those callers, not a "
        "quick patch mid-review for an evaluation-only work item. "
        "Recommend a dedicated follow-up work item: (1) handle "
        "single-newline paragraph formatting in "
        "`build_paragraph_index`, and (2) make `align_segment` return "
        "alignment failure (not a full-range fallback) when an anchor "
        "search genuinely fails, so `annotate.py`'s existing "
        "`alignment_error` rejection can catch it instead of silently "
        "writing a corrupted `scenes.json`.",
        "",
    ]

    corrupted = [r for r in rows if r["secondary_corrupted"]]
    lines += [
        "## Data quality finding: secondary_genre corruption",
        "",
        f"**{len(corrupted)}/{len(rows)} stories "
        f"({100 * len(corrupted) / len(rows):.0f}%) have a corrupted "
        "`secondary_genre` value** -- instead of a genre tag, the field "
        "contains leaked tool-call-syntax fragments (e.g. "
        '`</antml="secondary_genre">`, `<parameter '
        'name="specials_verdict">`).',
        "",
        "Traced during hand validation of this run's output (not a "
        "synthetic test): confirmed this is not a parsing bug in "
        "`lcats`'s own code (`anthropic_backend.py` reads the Anthropic "
        "SDK's already-parsed native `tool_use.input` dict -- the "
        "corruption is present in the value the model itself wrote for "
        "that field), and not prompt injection from the story text or "
        "the tool schema (`assess.py`'s `ASSESSMENT_TOOL` and system "
        "prompts contain no such tags). No other field -- `detected_genre`, "
        "`summary`, `issues`, `specials_verdict`, scene segmentation -- "
        "shows this corruption in this run; it is scoped entirely to "
        "`secondary_genre`, and the garbage consistently appears right at "
        "that field's boundary with the next schema field, "
        "`specials_verdict`. This looks like an intermittent "
        "`claude-opus-4-8` structured-output reliability issue at that "
        "specific field boundary, not a defect in this pipeline's own "
        "code.",
        "",
        "**Practical impact:** `secondary_genre` is not currently "
        "trustworthy as-is and should not be used downstream (e.g. for "
        "the paper) without either re-running affected stories or adding "
        "output sanitization. `detected_genre` and the rest of the "
        "sidecar output are unaffected.",
        "",
        "Recommend a follow-up work item to add output validation/"
        "sanitization for free-text tool-result fields (detect and strip "
        "or reject responses containing this pattern, matching how "
        "`_annotate_scenes` already rejects malformed segmentation "
        "output) -- not implemented here, out of this evaluation-only "
        "item's scope.",
        "",
        "Affected stories:",
        "",
    ]
    for row in corrupted:
        display_value = row["secondary"].replace("\n", " / ")
        lines.append(f"- `{row['story']}`: `{display_value}`")
    lines += [
        "",
        "## Per-genre summary",
        "",
        "| provisional_genre | agreement | avg confidence | avg scene count |",
        "|---|---|---|---|",
    ]
    total_match = 0
    for genre in sorted(by_genre):
        genre_rows = by_genre[genre]
        matches = sum(1 for r in genre_rows if r["match"])
        total_match += matches
        avg_conf = statistics.mean(r["confidence"] for r in genre_rows)
        avg_scenes = statistics.mean(r["scene_count"] for r in genre_rows)
        lines.append(
            f"| {genre} | {matches}/{len(genre_rows)} | {avg_conf:.2f} | "
            f"{avg_scenes:.1f} |"
        )

    overall_conf = statistics.mean(r["confidence"] for r in rows)
    overall_scenes = statistics.mean(r["scene_count"] for r in rows)
    min_conf = min(r["confidence"] for r in rows)
    max_conf = max(r["confidence"] for r in rows)

    lines += [
        "",
        f"**Overall: {total_match}/{len(rows)} provisional/detected genre "
        f"agreement.** Average confidence {overall_conf:.2f} "
        f"(range {min_conf:.2f}-{max_conf:.2f}); average scene count "
        f"{overall_scenes:.1f}.",
        "",
        "## Per-story detail",
        "",
        "| story | provisional | detected | secondary | confidence | scenes |",
        "|---|---|---|---|---|---|",
    ]
    for row in sorted(rows, key=lambda r: (r["provisional"], r["story"])):
        flag = "" if row["match"] else " **(mismatch)**"
        secondary_display = (
            "*(corrupted, see above)*"
            if row["secondary_corrupted"]
            else row["secondary"]
        )
        scenes_display = row["scene_count"]
        if row["paragraph_collapse"]:
            scenes_display = f"{row['scene_count']} **(offsets corrupted, see above)**"
        lines.append(
            f"| {row['story']} | {row['provisional']} | "
            f"{row['detected']}{flag} | {secondary_display} | "
            f"{row['confidence']:.2f} | {scenes_display} |"
        )

    mismatches = [r for r in rows if not r["match"]]
    lines += ["", "## Mismatches", ""]
    if mismatches:
        for row in mismatches:
            secondary_display = (
                "(corrupted, see above)"
                if row["secondary_corrupted"]
                else row["secondary"]
            )
            lines.append(
                f"- **{row['story']}**: provisional=`{row['provisional']}`, "
                f"detected=`{row['detected']}` (secondary: "
                f"{secondary_display}, confidence {row['confidence']:.2f})"
            )
    else:
        lines.append("None.")

    lines += [
        "",
        "## Observations",
        "",
        "- **Most important finding**: scene-segmentation offsets are "
        f"unreliable for {len(collapsed)}/{len(rows)} stories in this "
        "run (see above) -- a real correctness defect with a diagnosed "
        "root cause in shared library code, not model flakiness. Any "
        "future larger run should treat single-newline-formatted source "
        "text as a known risk until `text_segmenter.py` is fixed.",
        "- All 24 stories produced non-empty `genre.json`, `scenes.json`, "
        "and `README.md` sidecars, and passed `lcats promote`'s formal "
        "release-gate validation (`survey_collection`) with zero findings "
        "-- that gate checks shape, not segmentation correctness.",
        "- Confidence and secondary-genre fields surfaced real nuance, not "
        "just a bare label -- e.g. `brown_wolf` (Jack London) came back "
        "`adventure` at only 0.55 confidence with secondary genre "
        "`animal story`, a fair characterization of a story that resists a "
        "clean single-genre label.",
        "- One genuine genre mismatch (see Mismatches) reflects real genre "
        "ambiguity in the source text, not a pipeline defect -- that "
        "story's `secondary_genre` (uncorrupted) named the provisional "
        "guess, suggesting the divergence is a close call rather than a "
        "wrong answer.",
        "- See 'Data quality finding' above for a separate, more serious "
        "issue: `secondary_genre` corruption in 42% of stories.",
    ]

    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    manifest_rows = read_manifest()
    rows = collect_rows(manifest_rows)
    write_report(rows)
    print(f"wrote {REPORT_PATH}")


if __name__ == "__main__":
    main()
