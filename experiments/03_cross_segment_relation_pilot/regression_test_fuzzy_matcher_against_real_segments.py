"""WI-SEGMENT-0102: regression-test WI-SEGMENT-0072's unmodified
strict_local_fuzzy policy against every real, already-correctly-aligned
segment discovered in the repo.

This is a non-regression / no-op-invariance check, not a recovery-rate
measurement: for each real segment where the current exact/normalized
matcher already finds the correct (start_char, end_char), does the
looser strict_local_fuzzy policy ever produce a DIFFERENT match? A
"yes" is a stop condition (WI-SEGMENT-0059), not a tuning invitation.

Reuses `evaluate_near_miss_fuzzy_matching.accepted_match`/
`candidate_matches` completely unmodified - this script only discovers
real data, validates it as genuine ground truth, and calls the existing
policy. No production code or matcher parameters are touched.

DISCOVERY
---------
A repo-wide search (not just the two locations WI-SEGMENT-0102 was
originally scoped around) found real segment-schema data
(start_par_id/end_par_id/start_exact/end_exact/start_char/end_char) in:

- experiments/03_cross_segment_relation_pilot/results/segmentation_reliability/
  (WI-EVENT-0096's 17-story cohort)
- experiments/03_cross_segment_relation_pilot/results/segmentation_reliability_reworded_prompt/
  (WI-SEGMENT-0101's reworded-prompt run over the same cohort)
- experiments/03_cross_segment_relation_pilot/results/segmentation_paragraph_misnumbering_diagnostics/replay_fixture/
  (WI-SEGMENT-0071's replay fixture)
- lcats/experimental/annotation_feasibility_trial/source/trial/*/scenes.json
  (WI-ANNOTATE-0054's real trial output, story text co-located as
  story.json in the same directory)

Two other locations that matched a naive '"start_char"' grep were
checked and excluded: model_tiering_eval's `start_char` fields are
always `null` (stage-2/genre data, not segment offsets), and
science_fiction_analysis_trial's `evidence_sets[].records[].anchor` is a
different schema entirely (evidence-anchor spans, not segments) built
from `"backend": "fake"` synthetic fixture data, not real API output.

VALIDATION (why `outcome: included` alone is not enough)
---------------------------------------------------------
Per WI-SEGMENT-0102's own Problem/Context (the_secret_of_kralitz__kuttner
overlap case), every discovered segment is checked for (a) overlap with
another segment in the same story and (b) a start_exact/end_exact anchor
reused by another segment in the same story, before being trusted as
ground truth. A THIRD check was added after real data demanded it
(discovered during this item's own execution, not anticipated in the
WI's original acceptance criteria): the claimed
[start_par_id, end_par_id] paragraph window must actually CONTAIN the
segment's own recorded [start_char, end_char). Three stories in
annotation_feasibility_trial (love_of_life, story_of_keesh, brown_wolf -
the exact stories WI-SEGMENT-0059 named as pre-fix paragraph-collapse
casualties) have every segment's start_par_id/end_par_id stuck at (1, 1)
regardless of the segment's real character span, a symptom of the
single-newline paragraph-collapse bug WI-SEGMENT-0059 fixed. Some of
these segments' char spans do not even overlap each other, so overlap
detection alone would not catch them - but their paragraph metadata is
still corrupted, and using them as "ground truth" would search a
nonsensical window. This is reported as its own explicit finding, not
silently absorbed into the overlap-exclusion count.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
from typing import Any, Dict, List, Tuple

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "lcats" / "src"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import evaluate_near_miss_fuzzy_matching as fuzzy  # noqa: E402
from lcats.analysis import story_analysis  # noqa: E402
from lcats.analysis import text_segmenter  # noqa: E402

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
CORPORA_ROOT = REPO_ROOT / "corpora"

REQUIRED_SEGMENT_FIELDS = (
    "start_par_id",
    "end_par_id",
    "start_exact",
    "end_exact",
    "start_char",
    "end_char",
)


def _is_real_segment(seg: Any) -> bool:
    if not isinstance(seg, dict):
        return False
    for field in REQUIRED_SEGMENT_FIELDS:
        if field not in seg:
            return False
    return isinstance(seg.get("start_char"), int) and isinstance(
        seg.get("end_char"), int
    )


def _segments_from_parsed_output(parsed_output: Any) -> List[Dict[str, Any]]:
    if isinstance(parsed_output, dict):
        candidate = parsed_output.get("segments")
    elif isinstance(parsed_output, list):
        candidate = parsed_output
    else:
        candidate = None
    if not isinstance(candidate, list):
        return []
    return [seg for seg in candidate if _is_real_segment(seg)]


def _story_text_from_corpora(story_id: str) -> str | None:
    path = CORPORA_ROOT / story_id / "story.json"
    if not path.exists():
        return None
    data = json.loads(path.read_text("utf-8"))
    return text_segmenter.canonicalize_text(
        story_analysis.coerce_text(data.get("body", ""))
    )


def discover_sources() -> List[Tuple[str, str, str, List[Dict[str, Any]]]]:
    """Return (source_label, story_id, story_text, segments) tuples for
    every real, `outcome: included` story discovered across all known
    real-data locations. Deduplicates by story_id - a story committed to
    more than one location (e.g. peace_manoeuvres__davis, present in both
    segmentation_reliability and the replay_fixture) is only used once,
    keeping the first discovered copy, so its real segments are not
    double-counted as independent evidence."""
    found: Dict[str, Tuple[str, str, str, List[Dict[str, Any]]]] = {}

    reliability_dirs = [
        REPO_ROOT
        / "experiments/03_cross_segment_relation_pilot/results/segmentation_reliability",
        REPO_ROOT
        / "experiments/03_cross_segment_relation_pilot/results/segmentation_reliability_reworded_prompt",
        REPO_ROOT
        / "experiments/03_cross_segment_relation_pilot/results/segmentation_paragraph_misnumbering_diagnostics/replay_fixture",
    ]
    for base in reliability_dirs:
        if not base.exists():
            continue
        for f in sorted(base.rglob("*.json")):
            try:
                data = json.loads(f.read_text("utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if not isinstance(data, dict) or data.get("outcome") != "included":
                continue
            story_id = data.get("story_id")
            if not story_id or story_id in found:
                continue
            segments = _segments_from_parsed_output(data.get("parsed_output"))
            if not segments:
                continue
            text = _story_text_from_corpora(story_id)
            if text is None:
                continue
            found[story_id] = (
                str(base.relative_to(REPO_ROOT)),
                story_id,
                text,
                segments,
            )

    trial_base = (
        REPO_ROOT / "lcats/experimental/annotation_feasibility_trial/source/trial"
    )
    if trial_base.exists():
        for story_dir in sorted(trial_base.iterdir()):
            if not story_dir.is_dir():
                continue
            scenes_path = story_dir / "scenes.json"
            story_path = story_dir / "story.json"
            if not scenes_path.exists() or not story_path.exists():
                continue
            story_id = f"annotation_feasibility_trial/{story_dir.name}"
            if story_id in found:
                continue
            try:
                scenes_data = json.loads(scenes_path.read_text("utf-8"))
                story_data = json.loads(story_path.read_text("utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            segments = [
                seg
                for seg in scenes_data.get("segments") or []
                if _is_real_segment(seg)
            ]
            if not segments:
                continue
            text = text_segmenter.canonicalize_text(
                story_analysis.coerce_text(story_data.get("body", ""))
            )
            found[story_id] = (
                "annotation_feasibility_trial/source/trial",
                story_id,
                text,
                segments,
            )

    return list(found.values())


def validate_controls(
    text: str, segments: List[Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Return (valid, excluded) - excluded entries carry a 'reason'."""
    _, index_meta = text_segmenter.paragraph_text_indexer(text)
    para_spans = index_meta["para_spans"]
    n = len(para_spans)

    by_span = sorted(segments, key=lambda s: (s["start_char"], s["end_char"]))
    overlapping_ids = set()
    for i in range(len(by_span) - 1):
        a, b = by_span[i], by_span[i + 1]
        if a["end_char"] > b["start_char"]:
            overlapping_ids.add(id(a))
            overlapping_ids.add(id(b))

    anchor_counts: Dict[str, int] = {}
    for seg in segments:
        for anchor_field in ("start_exact", "end_exact"):
            anchor = seg.get(anchor_field) or ""
            if anchor:
                anchor_counts[anchor] = anchor_counts.get(anchor, 0) + 1
    reused_anchor_ids = set()
    for seg in segments:
        for anchor_field in ("start_exact", "end_exact"):
            anchor = seg.get(anchor_field) or ""
            if anchor and anchor_counts.get(anchor, 0) > 1:
                reused_anchor_ids.add(id(seg))

    valid: List[Dict[str, Any]] = []
    excluded: List[Dict[str, Any]] = []
    for seg in segments:
        reasons = []
        if id(seg) in overlapping_ids:
            reasons.append("overlaps an adjacent segment in the same story")
        if id(seg) in reused_anchor_ids:
            reasons.append("shares a start_exact/end_exact anchor with another segment")

        sp, ep = seg["start_par_id"], seg["end_par_id"]
        if (
            isinstance(sp, int)
            and isinstance(ep, int)
            and not isinstance(sp, bool)
            and not isinstance(ep, bool)
        ):
            sp_c = max(1, min(sp, n)) - 1
            ep_c = max(1, min(ep, n)) - 1
            if ep_c < sp_c:
                ep_c = sp_c
            lo, hi = para_spans[sp_c][0], para_spans[ep_c][1]
            if not (lo <= seg["start_char"] and seg["end_char"] <= hi):
                reasons.append(
                    "paragraph window derived from start_par_id/end_par_id does not "
                    "contain the segment's own recorded (start_char, end_char) - "
                    "likely pre-WI-SEGMENT-0059 collapsed-paragraph data"
                )
        else:
            reasons.append("start_par_id/end_par_id missing or malformed")

        if reasons:
            excluded.append({"segment_id": seg.get("segment_id"), "reasons": reasons})
        else:
            valid.append(seg)

    return valid, excluded


def load_default_policy() -> fuzzy.Policy:
    """Load WI-SEGMENT-0072's frozen strict_local_fuzzy policy from its
    own committed fixture, unmodified - never redefined here, per
    WI-SEGMENT-0102's forbidden_actions."""
    fixture = json.loads(pathlib.Path(fuzzy.DEFAULT_FIXTURE).read_text("utf-8"))
    return fuzzy._policy_from_fixture(fixture)


def check_segment(
    para_spans: List[tuple], text: str, policy: fuzzy.Policy, seg: Dict[str, Any]
) -> Dict[str, Any]:
    # Clamp identically to validate_controls's own window computation
    # (and to text_segmenter.align_segment's real clamping) - a segment
    # that passed validation was checked against this same clamped
    # window, so re-deriving it here must match exactly, not just
    # subtract 1 from the raw (possibly out-of-range) par_id values.
    n = len(para_spans)
    sp = max(1, min(seg["start_par_id"], n)) - 1
    ep = max(1, min(seg["end_par_id"], n)) - 1
    if ep < sp:
        ep = sp
    lo, hi = para_spans[sp][0], para_spans[ep][1]

    report: Dict[str, Any] = {"segment_id": seg.get("segment_id")}
    for anchor_field, offset_field, side in (
        ("start_exact", "start_char", "start"),
        ("end_exact", "end_char", "end"),
    ):
        anchor = seg.get(anchor_field) or ""
        expected = seg[offset_field]
        match = fuzzy.accepted_match(text, anchor, lo, hi, policy)
        if match is None:
            report[side] = {"fuzzy_matched": False, "agrees": None}
            continue
        actual = match.start if side == "start" else match.end
        # Per acceptance criterion 2: report even an exact-offset AGREEMENT
        # as a distinct observation when the fuzzy policy needed its own
        # tolerance (edit_distance > 0, or the matched text isn't a
        # byte-exact substring at that position) to find it - the exact
        # matcher already in production would not have accepted this same
        # candidate on its own, even though the offset happens to agree.
        exact_hit = match.edit_distance == 0 and text[match.start : match.end] == anchor
        report[side] = {
            "fuzzy_matched": True,
            "fuzzy_offset": actual,
            "expected_offset": expected,
            "agrees": actual == expected,
            "required_fuzzy_tolerance": not exact_hit,
        }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    policy = load_default_policy()
    sources = discover_sources()
    total_segments = 0
    total_excluded = 0
    exclusion_reasons: Dict[str, int] = {}
    total_valid = 0
    total_agree_both = 0
    total_required_fuzzy_tolerance = 0
    disagreements: List[Dict[str, Any]] = []
    fuzzy_tolerance_cases: List[Dict[str, Any]] = []
    per_source: Dict[str, Any] = {}

    for source_label, story_id, text, segments in sources:
        valid, excluded = validate_controls(text, segments)
        total_segments += len(segments)
        total_excluded += len(excluded)
        for ex in excluded:
            for reason in ex["reasons"]:
                exclusion_reasons[reason] = exclusion_reasons.get(reason, 0) + 1

        _, index_meta = text_segmenter.paragraph_text_indexer(text)
        para_spans = index_meta["para_spans"]

        story_checks = []
        for seg in valid:
            total_valid += 1
            check = check_segment(para_spans, text, policy, seg)
            both_agree = check["start"].get("agrees") and check["end"].get("agrees")
            if both_agree:
                total_agree_both += 1
            else:
                disagreements.append({"story_id": story_id, **check})
            if any(
                check.get(side, {}).get("required_fuzzy_tolerance")
                for side in ("start", "end")
            ):
                total_required_fuzzy_tolerance += 1
                fuzzy_tolerance_cases.append({"story_id": story_id, **check})
            story_checks.append(check)

        per_source.setdefault(source_label, []).append(
            {
                "story_id": story_id,
                "total_segments": len(segments),
                "excluded": len(excluded),
                "exclusion_detail": excluded,
                "validated": len(valid),
                "checks": story_checks,
            }
        )

    result = {
        "total_segments_discovered": total_segments,
        "total_excluded": total_excluded,
        "exclusion_reasons": exclusion_reasons,
        "total_validated": total_valid,
        "total_agree_both_anchors": total_agree_both,
        "total_disagreements": len(disagreements),
        "disagreements": disagreements,
        "total_required_fuzzy_tolerance": total_required_fuzzy_tolerance,
        "fuzzy_tolerance_cases": fuzzy_tolerance_cases,
        "per_source": per_source,
    }

    output = json.dumps(result, indent=2)
    if args.output:
        pathlib.Path(args.output).write_text(output + "\n", encoding="utf-8")
    print(
        f"Discovered {total_segments} real segments across {len(sources)} stories; "
        f"{total_excluded} excluded as invalid controls; "
        f"{total_valid} validated; "
        f"{total_agree_both} agree exactly on both anchors; "
        f"{len(disagreements)} disagreements"
    )
    if not args.output:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
