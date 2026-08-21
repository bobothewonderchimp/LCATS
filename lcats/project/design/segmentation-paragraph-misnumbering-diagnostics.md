# Segmentation Paragraph-Misnumbering Diagnostics

Date: 2026-08-21

Related work:

- `WI-SEGMENT-0069` classified the original segmentation alignment failures.
- `WI-SEGMENT-0070` fixed marker leakage and quote/dash typography mismatches,
  but explicitly left paragraph misnumbering out of scope.
- `WI-SEGMENT-0071` requested this diagnostic report.

## Summary

The post-`WI-SEGMENT-0070` state does not support a production fix for
paragraph misnumbering yet. A fresh six-story post-fix rerun of the previously
known paragraph-misnumbering stories produced four alignment failures: one
`paragraph_misnumbering_large_margin`, one
`paragraph_misnumbering_narrow_margin`, and two
`anchor_absent_from_document`; the other two stories aligned successfully.
The historical six-case sample remains useful for source-text diagnostics, but
the fresh run shows the category is not stable enough to justify a narrow
repair.

Recommendation: defer implementation. Do not widen the search range, restore
full-document fallback, or add a heuristic paragraph repair until a later run
accumulates more misnumbering examples or a larger dedicated sample is
explicitly approved.

## Method

One bounded Anthropic run was made after explicit approval on 2026-08-21:
six segmentation-only calls with `claude-haiku-4-5-20251001`, one for each
story that `WI-SEGMENT-0069` had previously classified as paragraph
misnumbering. No ERW extractor calls were made.

The fresh records were written per story under a local scratch output directory
named `segmentation_reliability_wi_segment_0071_workspace_key` by
`check_segmentation_reliability.py`, which persists each result immediately
and includes `parsed_output` for alignment failures. The first attempt used the
worktree-local Anthropic key and failed with `401 authentication_error`; that
auth-failed directory was discarded as non-evidence. The successful run used
the newer key from the main Workspace LCATS `.secrets/` directory.
A distilled durable summary is committed at
`experiments/03_cross_segment_relation_pilot/results/segmentation_paragraph_misnumbering_diagnostics/post_wi_segment_0070_six_story_sample.json`.
A sanitized exact replay fixture preserving the `parsed_output` needed by
`classify_story()` is committed under
`experiments/03_cross_segment_relation_pilot/results/segmentation_paragraph_misnumbering_diagnostics/replay_fixture/`.

The diagnostic pass also reused the real `WI-SEGMENT-0069` classifications
recorded in `segmentation-alignment-failure-categories.md` and recomputed
paragraph position, density, boundary, and paragraph-shape metrics against the
committed source stories under `corpora/`.

The reproducible code path is
`experiments/03_cross_segment_relation_pilot/classify_alignment_failures.py`
with `--known-paragraph-diagnostics`. That path does not change production
alignment behavior; it only reads existing JSON and corpus text.

An older local post-fix smoke directory from `WI-SEGMENT-0070` was checked
first, but its alignment-error records did not retain `parsed_output`; it was
not used for the classification counts below.

## Counts

### Historical WI-SEGMENT-0069 Counts

`WI-SEGMENT-0069` found 21 alignment-error failures in its 30-story live smoke
test. The paragraph-misnumbering categories in that historical run were:

| Category | Count | Share of alignment errors |
|---|---:|---:|
| `paragraph_misnumbering_large_margin` | 4 | 19% |
| `paragraph_misnumbering_narrow_margin` | 2 | 10% |
| Combined paragraph misnumbering | 6 | 29% |

### Fresh Post-WI-SEGMENT-0070 Six-Story Rerun

The fresh rerun targeted exactly those six historical paragraph-misnumbering
stories. Its outcomes were:

| Outcome | Count |
|---|---:|
| `included` | 2 |
| `paragraph_misnumbering_large_margin` | 1 |
| `paragraph_misnumbering_narrow_margin` | 1 |
| `anchor_absent_from_document` | 2 |

The four fresh alignment failures classified from captured `parsed_output` and
source text were:

| Story | Fresh outcome | Cited example |
|---|---|---|
| `love_among_the_robots__mcdowell` | `paragraph_misnumbering_narrow_margin` | `segment_id=3`, `end_exact` beginning `"He returned the book to his pocket..."`, claimed char range `[10573, 15791]`, real position `15793`, margin `2` chars |
| `the_spinster_1905__hichens` | `paragraph_misnumbering_large_margin` | `segment_id=3`, `end_exact` beginning `"There were lights in the inn..."`, claimed char range `[4283, 8848]`, real position `11170`, margin `2322` chars |
| `no_charge_for_alterations__gold` | `anchor_absent_from_document` | `segment_id=17`, `end_exact` beginning `"Finished, they left the three uroariously [sic] drunk..."`; the quoted anchor was not found anywhere in source text because the source says "uproariously" |
| `way_of_a_rebel__miller` | `anchor_absent_from_document` | `segment_id=2`, `start_exact` beginning `"Mitch Laskell switched off the short wave set..."`; the quoted anchor was not found anywhere in source text |

`the_last_days_of_l_a__smith` and `peace_manoeuvres__davis` aligned
successfully in the fresh run. The fresh result therefore does not show a
stable per-story paragraph-misnumbering failure mode.

## Diagnostic Rows

The following historical rows are generated from committed source text by
`known_paragraph_misnumbering_diagnostics()`.

| Story | Bucket | n_par | Paragraphs / 1k chars | Claimed pars | Claimed char offsets | Real par | Real char | Drift | Near boundary? | Multi-line pars |
|---|---|---:|---:|---|---|---:|---:|---:|---|---:|
| `love_among_the_robots__mcdowell` | large_margin | 302 | 7.75 | `[7, 51]` | `[1306, 6255]` | 59 | 7920 | +8 | no | 194 |
| `the_last_days_of_l_a__smith` | large_margin | 193 | 4.88 | `[121, 144]` | `[23251, 28127]` | 119 | 22930 | -2 | yes | 138 |
| `the_spinster_1905__hichens` | large_margin | 162 | 7.13 | `[44, 75]` | `[4210, 8848]` | 91 | 10713 | +16 | no | 75 |
| `way_of_a_rebel__miller` | large_margin | 110 | 4.08 | `[5, 8]` | `[1986, 3693]` | 30 | 8787 | +22 | no | 93 |
| `no_charge_for_alterations__gold` | narrow_margin | 341 | 7.25 | `[52, 87]` | `[9053, 12984]` | 50 | 8929 | -2 | yes | 207 |
| `peace_manoeuvres__davis` | narrow_margin | 208 | 5.82 | `[37, 86]` | `[6349, 14764]` | 87 | 14766 | +1 | yes | 132 |

`Drift` is measured in paragraphs from the nearest claimed range edge:
positive means the real anchor paragraph is later than the claimed range;
negative means it is earlier.

## Hypotheses Tested

### Offset Drift

The historical failures do not look like one fixed offset. The real paragraph
is later than the claimed range in four cases (`+1`, `+8`, `+16`, `+22`) and
earlier in two cases (`-2`, `-2`). The two overcount cases are both near misses,
while the larger failures are all undercounts.

The fresh rerun weakens the offset hypothesis further: only two of the six
stories reproduced as paragraph-misnumbering cases at all, and one historical
large-margin story (`love_among_the_robots__mcdowell`) reproduced only as a
narrow two-character boundary miss in the fresh run.

This supports a weak lead: if any fix ever becomes viable, it probably cannot
be a single global paragraph offset. It would need local evidence from the
story's own markers or adjacent anchors.

### Paragraph Density

Paragraph density ranges from 4.08 to 7.75 paragraphs per 1,000 characters.
Both large-margin and narrow-margin cases appear at both ends of that range:

- `way_of_a_rebel__miller`: 4.08 paragraphs / 1k chars, large margin, drift
  `+22`.
- `the_last_days_of_l_a__smith`: 4.88 paragraphs / 1k chars, large margin by
  character margin, but only `-2` paragraphs from the nearest edge.
- `peace_manoeuvres__davis`: 5.82 paragraphs / 1k chars, narrow, `+1`.
- `love_among_the_robots__mcdowell`: 7.75 paragraphs / 1k chars, large,
  `+8`.

No monotonic density relationship is visible in the historical six cases. This
does not rule out density effects; it rules out treating density alone as enough
evidence for a repair.

### Boundary Off-by-One

Only one historical case is exactly off by one paragraph:
`peace_manoeuvres__davis` claimed through paragraph 86, while the real anchor
starts at paragraph 87. Three cases are near-boundary misses if `abs(drift) <=
2`: `peace_manoeuvres__davis`, `the_last_days_of_l_a__smith`, and
`no_charge_for_alterations__gold`.

The fresh rerun adds one two-character near-boundary case
(`love_among_the_robots__mcdowell`), but the same run also includes a
2,322-character large-margin case and two anchor-absent failures. That mix is
not enough to justify a local boundary expansion.

That is enough to make a boundary-expansion idea tempting, but not enough to
make it safe:

- The three remaining cases are far outside a one- or two-paragraph expansion.
- Expanding the search window changes behavior for all segments, including
  currently-correct ones.
- `WI-SEGMENT-0059` already established that broad fallback behavior can
  produce silently wrong overlapping boundaries.

Therefore, a boundary expansion is not recommended without distribution data
showing both recovery rate and false-positive risk.

### Prompt / Marker Interpretation

All six historical stories contain many multi-line paragraphs after deterministic
paragraph indexing: 75 to 207 multi-line paragraphs per story. This is
consistent with the qualitative lead noted in backlog: model-visible paragraph
markers may wrap dialogue or other line-heavy blocks that do not feel like a
single paragraph to a human reader.

The observation is not sufficient as a cause:

- Every known case has many multi-line paragraphs, but this report does not
  have a matched successful-control cohort with the same story mix.
- Direction is inconsistent: four undercounts, two overcounts.
- The largest undercount (`way_of_a_rebel__miller`, `+22`) and an overcount
  near miss (`the_last_days_of_l_a__smith`, `-2`) both have high multi-line
  counts.

This remains the best lead for future sampling, not a fix design.

## Recommendation

Defer paragraph-misnumbering implementation.

A safe fix is not supported by this evidence. The fresh post-fix sample
reproduced paragraph misnumbering in only two of the six targeted stories, and
the historical source-text diagnostics reject the simplest fixes:

- Do not apply a global paragraph offset: drift is inconsistent.
- Do not widen the range by one or two paragraphs: it would miss half the
  examples and affects all currently-correct alignments.
- Do not restore full-document fallback: prior work found that unsafe.
- Do not tune prompts or retry calls until a preferred result appears: that
  would not address the alignment risk directly.

Stop condition for this category: leave paragraph misnumbering as an explicit
known limitation until either:

1. a future already-approved smoke run organically captures substantially more
   paragraph-misnumbering examples with `parsed_output`, or
2. a separate WI authorizes a larger bounded sample specifically to estimate
   recovery and false-positive rates for a concrete candidate repair.

If follow-on work is created later, its first deliverable should be an
evaluation design, not production code. It should include a matched successful
control set, keep `parsed_output`, and predeclare false-positive thresholds
before any real API spend.
