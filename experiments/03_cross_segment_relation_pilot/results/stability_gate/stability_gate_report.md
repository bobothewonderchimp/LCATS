# WI-PILOT-0067 Stability Gate Report

## Predeclared Run Plan

- Mode: real run
- Model: `claude-opus-4-8`
- Story count: 2 validated, well-formed fixture stories
- Story set: `king_of_the_hill`, `unwelcomed_visitor`
- Expected real call count: about 12-22 Anthropic calls (2 genre-detect + 2 segmentation + 4 ERW calls per segment + up to 1 cross-segment relation call per story)
- Expected artifacts: `pilot_stories.jsonl`, `pilot_usage.jsonl`, `pilot_summary.json`, `genre_detection_results.json`, `stability_gate_results.json`, `stability_gate_report.md`
- Checkpoint policy: isolate the run under `results/stability_gate/`; stage fingerprints include model/backend/input state, so dry-run fake checkpoints do not satisfy the real Opus run.

## Predeclared Thresholds

- `fixture_story_completion_rate`: `1.0`
- `parseable_artifacts`: `True`
- `fatal_pilot_errors`: `0`
- `schema_invalid_or_truncation_marked_final_artifacts`: `0`
- `genre_correctness_rate`: `1.0`
- `source_supported_semantic_output`: `True`
- `intended_purpose_fit`: `True`

## Mechanical Results

- Mechanical pass: `False`
- Completed stories: 1/2
- Genre correctness: 2/2
- Independent well-formedness pass: 1/2
- Fatal pilot errors: 0
- Schema/truncation-marked final artifacts: 0
- Total input/output tokens: 34077 / 19025
- Actual spend: $0.6460

## Genre Detection

- `fixtures__king_of_the_hill`: expected `science fiction`, detected `science fiction`, correct `True`
- `fixtures__unwelcomed_visitor`: expected `science fiction`, detected `science fiction`, correct `True`

## Validation Errors

- 1 story row(s) were excluded
- fixtures__unwelcomed_visitor: missing usage stages ['discourse', 'entity', 'event_anchor', 'relation', 'surface_feature']
- 1 genre-detection result(s) failed

Blocking failure modes:

- `fixtures__unwelcomed_visitor` did not complete the pipeline. The
  segmentation stage wrote a failure checkpoint:
  `alignment failed for segment_id=2: anchor text not found in story text`.
- `fixtures__king_of_the_hill` completed the pipeline, but the separate real
  genre-detection/well-formedness check returned `wellformed: false` and
  `verdict: review`, judging the fixture to read as an excerpt with missing
  prior context.

## Semantic Review

- Status: `reviewed_fail`
- Source-supported semantic output: `False`
- Intended-purpose fit: `False`

The completed `fixtures__king_of_the_hill` output is broadly useful for
inspection: it identifies the station/bombardier-board scene, Peter, Joan,
the Joint Chiefs, ULTIMAC, and relations around the gun, tape, station-captain
test, and possible dud bombs. It also reports four strong cross-segment
relations plus two weakly inferred relations.

That partial success does not satisfy the gate. The gate required both
well-formed fixture stories to complete with source-supported output and
explicit genre/well-formedness coverage. One story failed segmentation, and
the other story was independently flagged as not well-formed.

## Recommendation

`fail_no_go`

Downstream prompt-caching, model-tiering, Batch API, and run-mode adoption
work should remain blocked until a separate follow-on work item fixes the
fixture/pipeline failure mode and reruns a newly predeclared gate. No prompt
tuning, threshold loosening, or repeated retry was performed in this work item.
