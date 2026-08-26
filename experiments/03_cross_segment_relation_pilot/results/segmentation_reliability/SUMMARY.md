# WI-EVENT-0096 measurement: segmentation schema-hardening effect

**Real API run, 2026-08-26.** `claude-haiku-4-5-20251001`, 17 real LLM
calls, actual cost **$0.59** (225,626 input tokens, 73,483 output tokens -
measured directly from each story's recorded `usage`, not estimated).

## Cohort

The exact original 17-story baseline cohort from
`experiments/03_cross_segment_relation_pilot/results/pilot_stories.jsonl`
(5 science fiction, 5 horror, 2 western, 5 romance), resolved to current
`corpora/` paths via `resolve_baseline_story_list.py`. Not a fresh or
substitute sample.

## Headline result

| | Baseline (pre-fix) | This run (post-fix, PR #188) |
|---|---|---|
| Exclusion rate (any cause) | 11/17 (65%) | **10/17 (59%)** |
| Exclusion cause | 11/11 `parsing_error` (100%) | 0/10 `parsing_error` (0%); 10/10 `alignment_error` (100%) |

**The schema-hardening fix worked exactly as designed for its target
failure mode**: `parsing_error` - the JSON-parse failures the
`tool_schema=` retrofit exists to eliminate - dropped from 11/17 to
**zero**. Every model response now parses as valid, schema-conformant
JSON.

**But overall segmentation reliability barely moved (65% -> 59%,
a 6-point improvement), because a different, pre-existing failure mode
was already present underneath and is now fully exposed.** All 10
new-run exclusions are `alignment_error: "anchor text not found in story
text"` - the exact near-miss-anchor category `WI-SEGMENT-0069`
investigated and `WI-SEGMENT-0072` evaluated (fuzzy-matching) and
deliberately declined to fix, due to false-positive risk. The model
successfully parses and returns a full segment list (e.g.
`lovecraft/the_haunter_of_the_dark` returned 13 well-formed segments),
but one segment's anchor text fails to align against the real story text,
and the whole story is excluded as a result - not a parsing failure at
all, a distinct alignment failure that `parsing_error`-based reporting
would have hidden entirely (per this item's own review-round correction:
`parsing_error` is `None` unconditionally on the `tool_schema` path, so a
naive comparison would have shown a false 0%-improvement-impossible or
100%-improvement result depending on which side of the tautology was
read).

## One real regression, reported plainly

`wintry_peacock_from_the_new_decameron_volume_iii__lawrence` (romance)
was **included** in the original baseline and is **excluded** in this
run (`alignment_error`, segment_id=9). This is not noise to explain away:
a story that previously made it through the pipeline no longer does,
under the "improved" code. Per-genre detail:

| Genre | Baseline included | This run included | Note |
|---|---|---|---|
| science fiction | 1/5 | 1/5 | unchanged |
| horror | 1/5 | 2/5 | improved |
| western | 0/2 | 1/2 | improved - no longer zero |
| romance | 4/5 | 3/5 | **regressed** - `wintry_peacock...` flipped from included to excluded |

## Conclusion

`WI-EVENT-0033`'s schema-hardening fix is confirmed to have eliminated
its named failure mode (`parsing_error`) completely, verified with real
data. It did not meaningfully improve the pipeline's overall segmentation
exclusion rate, because a different, already-known, already-deferred
failure mode (near-miss anchor alignment) was the larger and previously
partially-masked contributor. Per this project's practice of not forcing
a pass on a smaller-than-expected improvement, `WI-EVENT-0033` is not
being resolved by this measurement alone - see its own Risk Notes for the
updated real evidence and the resulting recommendation.

## Raw data

One JSON file per story under this directory (mirroring `corpora/`'s
`<collection>/<slug>.json` layout), each containing `outcome`,
`llm_call_made`, `word_count`, `segment_count`, `raw_output`,
`parsed_output`, `extracted_output`, `api_error`, `extraction_error`, and
`usage` (real `input_tokens`/`output_tokens`).
