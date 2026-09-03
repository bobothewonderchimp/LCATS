# Segmentation fuzzy-match regression safety check (WI-SEGMENT-0102)

## Purpose

`WI-SEGMENT-0072` proposed a `strict_local_fuzzy` policy
(`experiments/03_cross_segment_relation_pilot/evaluate_near_miss_fuzzy_matching.py`)
as a candidate near-miss recovery mechanism for anchor matching, but froze
its adoption pending further evidence — the policy and its thresholds are
not used in production and this item does not change that.

This item asks a narrower, complementary question: for every real segment
where the *current* production matcher
(`text_segmenter._locate_anchor_span` / `align_segment`) already finds the
correct `(start_char, end_char)`, does `strict_local_fuzzy` ever produce a
**different** answer? Per `WI-SEGMENT-0059`'s standing principle, a
disagreement here is a stop condition, not a tuning invitation — this is a
non-regression / no-op-invariance check, not a recovery-rate measurement.

The implementation, `experiments/03_cross_segment_relation_pilot/
regression_test_fuzzy_matcher_against_real_segments.py`, calls
`evaluate_near_miss_fuzzy_matching.accepted_match` and `candidate_matches`
completely unmodified. No production code or `WI-SEGMENT-0072`'s frozen
thresholds are touched.

## Real-data inventory

Acceptance criterion 1 required a repo-wide discovery pass, not reliance on
the two locations named in the WI's original scope. A `grep -rl
'"start_char"' --include="*.json" .` search surfaced more candidates than
expected; each was individually inspected against the real segment schema
(`start_par_id`/`end_par_id`/`start_exact`/`end_exact`/`start_char`/
`end_char`) before being trusted.

**Included** (4 locations, story text resolved from `corpora/<id>/story.json`
or a co-located `story.json`):

| Source | Stories | Segments | Provenance |
|---|---|---|---|
| `experiments/03_cross_segment_relation_pilot/results/segmentation_reliability/` | 7 | 56 | `WI-EVENT-0096`'s 17-story cohort (real API output, `outcome: included` only) |
| `.../segmentation_reliability_reworded_prompt/` | 3 | 29 | `WI-SEGMENT-0101`'s reworded-prompt ablation, same cohort |
| `.../segmentation_paragraph_misnumbering_diagnostics/replay_fixture/` | 1 | 18 | `WI-SEGMENT-0071`'s replay fixture |
| `lcats/experimental/annotation_feasibility_trial/source/trial/*/scenes.json` | 24 | 177 | `WI-ANNOTATE-0054`'s real trial output |

Total discovered: **280 segments across 35 stories** (deduplicated by
`story_id` — a story present in more than one location, e.g.
`peace_manoeuvres__davis` in both `segmentation_reliability` and the replay
fixture, is counted once, using the first-discovered copy, so its segments
are not double-counted as independent evidence).

**Excluded after inspection** (not real narrative-segment data):

- `experiments/03_cross_segment_relation_pilot/results/model_tiering_eval/
  model_tiering_comparison.json` — its `start_char` fields are always
  `null` (stage-2/genre-detection metadata).
- `lcats/experimental/science_fiction_analysis_trial/results/
  worldcon_spike/...` — a different schema
  (`evidence_sets[].records[].anchor.{start_char,end_char,paragraph_ids}`
  for literary-theory evidence spans, not narrative segments), and built
  from `"backend": "fake"` synthetic fixture data per its own `provenance`
  field, not real API output.
- `lcats/experimental/model_comparison/ollama_gpt_oss_20b/` — entity/genre
  data, no segment schema at all.

## Ground-truth validation (why "included" alone is not enough)

Per the WI's own Problem/Context (`the_secret_of_kralitz__kuttner` segments
4 and 5 both ending at char 13102), an `outcome: included` label does not
guarantee non-overlapping or correct boundaries. Three checks are applied
before a segment is trusted as ground truth:

1. **Overlap** — sorted by `(start_char, end_char)`, any adjacent pair
   where `a.end_char > b.start_char` excludes both.
2. **Reused anchor** — a `start_exact`/`end_exact` string shared by more
   than one segment in the same story excludes every segment touching it.
3. **Paragraph-window containment** (added during this item's own
   execution, not anticipated in the original acceptance criteria) — the
   window `[start_par_id, end_par_id]` (inclusive, clamped) must actually
   *contain* the segment's own recorded `(start_char, end_char)`.

Check 3 was necessary, not optional: `love_of_life`, `story_of_keesh`, and
`brown_wolf` in `annotation_feasibility_trial` — the exact three stories
`WI-SEGMENT-0059` named as pre-fix paragraph-collapse casualties — have
every segment's `start_par_id`/`end_par_id` stuck at `(1, 1)` regardless of
the segment's real character span, a residual symptom of the single-newline
paragraph-collapse bug `WI-SEGMENT-0059` fixed in production. Some of these
segments' character spans do not even overlap each other, so overlap
detection alone would not have caught them. Their paragraph metadata is
still corrupted, so using them as ground truth would search a nonsensical
window; they are excluded as a distinct, explicit finding rather than
folded silently into the overlap count.

**Exclusion breakdown** (23 total, out of 280 discovered):

| Reason | Count |
|---|---|
| Overlaps an adjacent segment | 11 |
| Reused start_exact/end_exact anchor | 2 |
| Paragraph window does not contain recorded char span | 19 |

(Reasons are not mutually exclusive per segment — the 23 total is the
count of *segments excluded*, not the sum of the reason column, since some
segments trip more than one check.)

**257 segments validated as genuine ground truth.**

## Results

For each of the 257 validated segments, `start_exact` and `end_exact` are
evaluated independently against `strict_local_fuzzy`, and the result is
compared to the segment's own recorded `start_char`/`end_char`.

| Outcome | Count |
|---|---|
| Agree exactly on both anchors | 145 |
| Disagreement (either anchor) | 112 |

The 112 disagreements are **not one kind of finding** — decomposing by
whether `accepted_match` found a candidate at all:

| Disagreement type | Count | Safety implication |
|---|---|---|
| No candidate found (`fuzzy_matched: False`) | 105 | Safe — a false negative, not a false accept. `strict_local_fuzzy` never disagrees with production by producing a *wrong* span here; it simply finds nothing. |
| Wrong offset (candidate found, differs from recorded) | 7 | **The real safety-relevant finding** — see below. |

### The 7 wrong-offset cases: a genuine, narrow disagreement

All 7 wrong-offset cases are off by exactly **1 character**, all on the
`end_exact` side, across `ohenry-whirligigs/girl` and three
`annotation_feasibility_trial` Sherlock Holmes stories
(`red_headed_league` ×3, `scandal_in_bohemia` ×2) plus one `start_exact`
case in `speckled_band`. Every case has `required_fuzzy_tolerance: True`,
meaning `strict_local_fuzzy` needed genuine edit-distance tolerance (not a
byte-exact hit) to find these — the disagreement is exactly the same class
`WI-SEGMENT-0059` warned about: two independently-implemented anchor
matchers (`_locate_anchor_span`'s typography/whitespace/case-tolerant exact
match vs. `candidate_matches`' own separately-implemented boundary
scoring) computing a slightly different exact boundary for the same
typography-normalized text (trailing curly-quote/punctuation boundary
disagreements, consistent with prior findings on this same normalization
edge in this project).

**This is 7 real cases out of 257 (2.7%) — small, but not zero, and this
item's own acceptance criteria require reporting it explicitly rather than
absorbing it into a blanket verdict.**

### The 105 no-match cases: a distinct, previously-undocumented robustness gap

Decomposing the 105 no-match disagreements by root cause (checked directly
against `candidate_matches`' real behavior, not inferred):

| Root cause | Count |
|---|---|
| Anchor has fewer than 3 word-tokens | 15 |
| Anchor has ≥3 tokens, but real text has punctuation (not just whitespace) between the last few tokens | 65 |
| Other (not further categorized — likely additional typography-normalization or multi-paragraph-span cases) | 25 |

Two distinct, previously-undiscovered structural limitations in
`WI-SEGMENT-0072`'s frozen `candidate_matches` account for the large
majority of these:

1. **Punctuation-blind n-gram reconstruction.** `candidate_matches`
   rebuilds a candidate regex by joining word-tokens with `\s+`
   (whitespace) only. Real prose — especially dialogue — very commonly has
   punctuation (commas, quotation marks) between an anchor's last few
   words (e.g. `'"Yes, dear," sighed Mater.'`,
   `'"Hands up!" shouted one. "You\'re my prisoner!" cried the other.'`).
   Because the reconstructed pattern requires only whitespace between
   tokens, it fails to match text that actually has intervening
   punctuation, and `candidate_matches` returns **zero candidates** —
   confirmed for 65 of the 105 no-match cases by rebuilding each anchor's
   pattern with `\W+` (any non-word run) in place of `\s+` and confirming
   it *does* match the same window.
2. **Minimum 3-token requirement.** `candidate_matches` only builds n-grams
   of width 5, 4, or 3 tokens (`for width in (5, 4, 3)`). An anchor with
   fewer than 3 word-tokens (e.g. `"Everybody was."`, `"DON CHANNING."`)
   never has a 3-gram to build, so the n-gram list stays empty and zero
   candidates are ever generated — regardless of whether the anchor is an
   exact substring of the window. This was independently discovered while
   diagnosing this item's own regression-test fixture (see the
   `regression_test_fuzzy_matcher_against_real_segments_test.py`
   `test_exact_anchor_agrees_with_recorded_offsets` case, which initially
   failed for exactly this reason before its anchor was widened to 3+
   tokens).

Both are **false negatives, not false accepts** — `strict_local_fuzzy`
never proposes a wrong span in these cases, it simply proposes none. This
makes them safe with respect to `WI-SEGMENT-0059`'s "never silently produce
a plausible-but-wrong span" principle, but they represent a large,
previously-undocumented robustness gap: 105 of 257 validated segments
(≈41%) have at least one anchor for which this policy would get **no help
at all**, if it were ever used as a recovery mechanism, independent of its
threshold tuning.

## Verdict

**Not a blanket "safe."** Per this item's own acceptance criteria:

- No production alignment behavior is changed by this item, and
  `WI-SEGMENT-0072`'s frozen thresholds are neither invoked nor altered —
  this check does not clear that gate and was never intended to.
- **A genuine, if narrow, disagreement exists**: 7 of 257 validated real
  segments (2.7%) show `strict_local_fuzzy` disagreeing with the current
  correct result by exactly 1 character, always on a typography-normalized
  boundary requiring real edit-distance tolerance to find. This is the
  same class of two-matchers-disagree risk `WI-SEGMENT-0059` treats as a
  stop condition. It does not block this item (no production behavior
  changed), but it is evidence against ever adopting `strict_local_fuzzy`
  without first resolving this boundary-computation discrepancy between
  the two independently-implemented matchers.
- **Separately, and more significantly**: `candidate_matches` has at least
  two previously-undocumented structural limitations (punctuation-blind
  token-joining, and a hard 3-token minimum) that make it unable to
  propose *any* candidate for a large fraction of real anchors — a
  robustness gap distinct from, and arguably more consequential than,
  `WI-SEGMENT-0072`'s known threshold-tuning questions. This does not
  compromise safety (false negative, not false accept) but materially
  limits the policy's usefulness as a near-miss recovery mechanism in its
  current form, independent of threshold choice.

## Regression coverage

`regression_test_fuzzy_matcher_against_real_segments_test.py` (11 tests)
covers `_is_real_segment`, all three `validate_controls` checks (including
a synthetic reproduction of the `love_of_life`-shaped paragraph-collapse
scenario), and `check_segment`'s exact-agreement path, its
out-of-range-`par_id` clamp (a real bug caught and fixed during this item's
own execution), and the punctuation-causes-no-match case documented above.
Re-run this suite after any future change to `strict_local_fuzzy` or its
evaluator to re-verify this safety property still holds.
