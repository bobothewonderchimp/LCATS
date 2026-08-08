# Annotation feasibility trial: stats report

`lcats annotate` run against the 24-story subset in `subset_manifest.md` (3 stories x 8 `VALID_GENRES`). `provisional_genre` is the hand-picked guess used to build the subset (no paid API call); `detected_genre` is `lcats annotate`'s actual output, compared here for feasibility signal, not as a ground-truth accuracy benchmark (the provisional guess itself is informal).

## Run

- Real API run: `claude-opus-4-8`, 24 stories, real time **17m39s** (`time lcats annotate --source experimental/annotation_feasibility_trial/source`).
- Genre-detection call token totals: 380,268 input / 9,634 output. Exact USD cost not computed here (no pricing constant lives in this repo -- checking the Anthropic Console billing dashboard for the run window is more reliable than a hand-typed price-per-token figure that could go stale).
- Scene-segmentation call token usage for **this specific run** is not available: at the time this run executed, `_annotate_scenes` (`annotate.py`) discarded the token usage `JSONPromptExtractor.extract()` already returns, so `scenes.json` stored only `segments`/`segment_count`/`model`. Fixed in this same PR (`annotate.py` now records `input_tokens`/`output_tokens` in `scenes.json`, matching `genre.json`) -- every future run will have complete data. Deliberately not re-running this trial's already-good segmentation results solely to backfill token counts for this report -- that would spend real API budget for reporting completeness alone, against this item's own Risk Notes to keep this first run small.
- `lcats promote`'s `survey_collection` gate: **clean** (0 mojibake findings, 0 malformed-sidecar findings across all 24 stories) -- this checks JSON validity and required-field shape only. It does not catch either data quality finding below: neither corrupted `secondary_genre` text nor overlapping scene `start_char`/`end_char` offsets change a sidecar's required-key shape.

## Data quality finding: scene-segmentation offset corruption (most severe finding in this run)

**3/24 stories have single-paragraph source text** (`text_segmenter.paragraph_text_indexer` finds no blank-line paragraph breaks at all -- the whole story collapses into one `[P0001]` block), and **all 3 of those show corrupted scene segmentation**: 2 with overlapping segment offsets, the rest degenerate (a single segment spanning the entire story, no real segmentation at all). Unlike the `secondary_genre` finding below, this corrupts the actual `start_char`/`end_char` fields downstream consumers would use to slice the story text -- a real correctness defect, not a cosmetic one.

**Root cause, traced to `text_segmenter.py`:** `build_paragraph_index` splits only on a literal blank line (`\n\n`); a story formatted with single-newline paragraph breaks (all 3 affected stories here are from `corpora/london`) collapses to `n_paragraphs=1`, so every segment's `start_par_id`/`end_par_id` is forced to 1 and `align_segment`'s search range becomes the *entire document* for every segment. When `find_anchor_in_range` then fails to locate a segment's `end_exact` text verbatim (`align_segment`, `text_segmenter.py` around line 146), the function silently falls back to `hi` -- the end of the search range, i.e. end-of-document -- instead of raising an alignment error. The result is a spurious full-document-length segment that overlaps every segment after it, with no `alignment_error` or `validation_error` raised to catch it (verified: `annotate.py`'s existing alignment/validation-error rejection did not fire for any of these 3 stories).

Affected stories:

- `love_of_life`: 121,396 overlapping chars across 13 segments
- `story_of_keesh`: 2,626 overlapping chars across 5 segments
- `brown_wolf`: degenerate: 1 segment spanning the entire story

**Not fixed here** -- `align_segment`/`build_paragraph_index` are shared library code in `text_segmenter.py`, used by other callers beyond `lcats annotate` (`story_processors.py`, `run_pilot.py`, `notebooks/12_extract_scenes.ipynb` per `scene_analysis.py`'s own docstring) -- a fix needs its own design and test coverage against all of those callers, not a quick patch mid-review for an evaluation-only work item. Recommend a dedicated follow-up work item: (1) handle single-newline paragraph formatting in `build_paragraph_index`, and (2) make `align_segment` return alignment failure (not a full-range fallback) when an anchor search genuinely fails, so `annotate.py`'s existing `alignment_error` rejection can catch it instead of silently writing a corrupted `scenes.json`.

## Data quality finding: secondary_genre corruption

**10/24 stories (42%) have a corrupted `secondary_genre` value** -- instead of a genre tag, the field contains leaked tool-call-syntax fragments (e.g. `</antml="secondary_genre">`, `<parameter name="specials_verdict">`).

Traced during hand validation of this run's output (not a synthetic test): confirmed this is not a parsing bug in `lcats`'s own code (`anthropic_backend.py` reads the Anthropic SDK's already-parsed native `tool_use.input` dict -- the corruption is present in the value the model itself wrote for that field), and not prompt injection from the story text or the tool schema (`assess.py`'s `ASSESSMENT_TOOL` and system prompts contain no such tags). No other field -- `detected_genre`, `summary`, `issues`, `specials_verdict`, scene segmentation -- shows this corruption in this run; it is scoped entirely to `secondary_genre`, and the garbage consistently appears right at that field's boundary with the next schema field, `specials_verdict`. This looks like an intermittent `claude-opus-4-8` structured-output reliability issue at that specific field boundary, not a defect in this pipeline's own code.

**Practical impact:** `secondary_genre` is not currently trustworthy as-is and should not be used downstream (e.g. for the paper) without either re-running affected stories or adding output sanitization. `detected_genre` and the rest of the sidecar output are unaffected.

Recommend a follow-up work item to add output validation/sanitization for free-text tool-result fields (detect and strip or reject responses containing this pattern, matching how `_annotate_scenes` already rejects malformed segmentation output) -- not implemented here, out of this evaluation-only item's scope.

Affected stories:

- `a_martian_odyssey__weinbaum`: `</antml：parameter> / <parameter name="specials_verdict">author_intentional`
- `a_city_near_centaurus__doede`: `</antml name="secondary_genre">`
- `one_touch_of_nature`: `</antml="parameter> / <parameter name="specials_verdict">none`
- `scandal_in_bohemia`: `</antml":parameter> / <parameter name="specials_verdict">author_intentional`
- `red_headed_league`: `</antml="secondary_genre">`
- `speckled_band`: `</antmlial> / <parameter name="specials_verdict">author_intentional`
- `the_sheriff_and_his_partner__harris`: `</antml name="secondary_genre">`
- `chaparral_christmas_gift`: `</antml：parameter> / <parameter name="specials_verdict">author_intentional`
- `springtime_a_la_carte`: `</antml=parameter> / <parameter name="specials_verdict">author_intentional`
- `service_of_love`: `</antml=parameter> / <parameter name="specials_verdict">author_intentional`

## Per-genre summary

| provisional_genre | agreement | avg confidence | avg scene count |
|---|---|---|---|
| adventure | 3/3 | 0.72 | 6.3 |
| fantasy | 3/3 | 0.90 | 6.7 |
| horror | 3/3 | 0.97 | 11.7 |
| humor | 3/3 | 0.83 | 6.7 |
| mystery | 3/3 | 0.98 | 7.3 |
| romance | 3/3 | 0.74 | 5.7 |
| science fiction | 3/3 | 0.97 | 6.7 |
| western | 2/3 | 0.90 | 8.0 |

**Overall: 23/24 provisional/detected genre agreement.** Average confidence 0.88 (range 0.55-0.99); average scene count 7.4.

## Per-story detail

| story | provisional | detected | secondary | confidence | scenes |
|---|---|---|---|---|---|
| brown_wolf | adventure | adventure | animal story | 0.55 | 1 **(offsets corrupted, see above)** |
| love_of_life | adventure | adventure | survival | 0.85 | 13 **(offsets corrupted, see above)** |
| story_of_keesh | adventure | adventure | children's | 0.75 | 5 **(offsets corrupted, see above)** |
| hansel_and_gretel | fantasy | fantasy | children's fairy tale | 0.90 | 9 |
| rapunzel | fantasy | fantasy | fairy tale / children's | 0.85 | 4 |
| snow_white_and_rose_red | fantasy | fantasy | children's fairy tale | 0.95 | 7 |
| the_call_of_cthulhu | horror | horror | cosmic horror / weird fiction | 0.98 | 9 |
| the_colour_out_of_space | horror | horror | science fiction (cosmic/weird) | 0.95 | 11 |
| the_dunwich_horror | horror | horror | weird fiction / cosmic horror | 0.99 | 15 |
| crowned_heads | humor | humor | romance | 0.75 | 8 |
| extricating_young_gussie | humor | humor | comedy of manners | 0.95 | 8 |
| one_touch_of_nature | humor | humor | *(corrupted, see above)* | 0.80 | 4 |
| red_headed_league | mystery | mystery | *(corrupted, see above)* | 0.98 | 7 |
| scandal_in_bohemia | mystery | mystery | *(corrupted, see above)* | 0.97 | 6 |
| speckled_band | mystery | mystery | *(corrupted, see above)* | 0.98 | 9 |
| gift_of_the_magi | romance | romance | Christmas/holiday | 0.75 | 5 |
| service_of_love | romance | romance | *(corrupted, see above)* | 0.72 | 6 |
| springtime_a_la_carte | romance | romance | *(corrupted, see above)* | 0.75 | 6 |
| 2_b_r_0_2_b__vonnegut | science fiction | science fiction | dystopian satire | 0.95 | 4 |
| a_city_near_centaurus__doede | science fiction | science fiction | *(corrupted, see above)* | 0.97 | 6 |
| a_martian_odyssey__weinbaum | science fiction | science fiction | *(corrupted, see above)* | 0.99 | 10 |
| chaparral_christmas_gift | western | western | *(corrupted, see above)* | 0.92 | 7 |
| the_cowboy_and_the_lady_and_her_pa_b_a_story_of_a__cobb | western | humor **(mismatch)** | western | 0.82 | 9 |
| the_sheriff_and_his_partner__harris | western | western | *(corrupted, see above)* | 0.95 | 8 |

## Mismatches

- **the_cowboy_and_the_lady_and_her_pa_b_a_story_of_a__cobb**: provisional=`western`, detected=`humor` (secondary: western, confidence 0.82)

## Observations

- **Most important finding**: scene-segmentation offsets are unreliable for 3/24 stories in this run (see above) -- a real correctness defect with a diagnosed root cause in shared library code, not model flakiness. Any future larger run should treat single-newline-formatted source text as a known risk until `text_segmenter.py` is fixed.
- All 24 stories produced non-empty `genre.json`, `scenes.json`, and `README.md` sidecars, and passed `lcats promote`'s formal release-gate validation (`survey_collection`) with zero findings -- that gate checks shape, not segmentation correctness.
- Confidence and secondary-genre fields surfaced real nuance, not just a bare label -- e.g. `brown_wolf` (Jack London) came back `adventure` at only 0.55 confidence with secondary genre `animal story`, a fair characterization of a story that resists a clean single-genre label.
- One genuine genre mismatch (see Mismatches) reflects real genre ambiguity in the source text, not a pipeline defect -- that story's `secondary_genre` (uncorrupted) named the provisional guess, suggesting the divergence is a close call rather than a wrong answer.
- See 'Data quality finding' above for a separate, more serious issue: `secondary_genre` corruption in 42% of stories.
