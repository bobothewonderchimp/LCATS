# Event-Role-World pipeline structured-output reliability audit — LCATS

- Prompt ID used: `PROMPT(AD_HOC:ERW_PIPELINE_STRUCTURED_OUTPUT_RELIABILITY_AUDIT)[2026-07-27T12:41:56-04:00]`
- Audit date: 2026-07-27
- Scope: every LLM-structured-output call site reachable from WI-EVENT-0030's
  pilot run (`experiments/03_cross_segment_relation_pilot/run_pilot.py`),
  looked at broadly rather than narrowly — triggered by two real crashes hit
  during live dogfooding (PR #167, PR #168), but this pass goes past just
  those two sites to the whole surface.
- Status: **finding only, no fix yet**. Written to capture and ground the
  issues while WI-EVENT-0030's real run (currently in progress with the
  default Opus model, after switching off Haiku) finishes, per user
  direction: revisit this file once that run completes, discuss, and only
  then spin up the actual work item(s)/workstream/design proposal - not
  going through PR review/confirm/merge for this capture step since the
  work is still in flight.
- Not yet acted on: WI-EVENT-0030 has `forbidden_actions:
  modify_event_role_world_extractor`, which blocks Categories A/B/D below
  (anything inside `lcats/lcats/analysis/event_role_world/`) from being
  fixed inside that work item. Category C's `scene_analysis.py`/
  `story_analysis.py` sites are outside that constraint, but were also left
  unfixed pending this broader look, per user request to scope a properly
  unconstrained work item/workstream instead of another caller-side
  workaround.

## 1. Summary

Two real crashes during WI-EVENT-0030 dogfooding (`ValueError` on non-JSON
model output in segmentation, PR #167; `AttributeError` on a malformed
tool-result array item in `relation_extractor.build_relations`, PR #168)
turned out to be instances of two broader, systemic gaps rather than
one-off bugs:

1. None of the LLM structured-output tool schemas in this codebase set
   Anthropic's `strict: true` (which requires `additionalProperties: false`
   on every object) - so none of them get the schema-conformance guarantee
   Anthropic's own docs describe as the actual fix for exactly this class
   of failure.
2. Three extractors use no tool schema at all (fully unconstrained
   `json_object`-mode JSON-in-text), the least reliable output mode - one
   of which (`scene_analysis.make_segment_extractor`) is the confirmed,
   live cause of the pilot's 65% segmentation exclusion rate with a cheaper
   model.
3. Every one of the six Event-Role-World tool-schema extractors shares the
   identical unguarded-array-item pattern that produced PR #168's crash -
   only one has actually crashed so far, but the same latent risk exists in
   eleven call sites across six files.
4. `processor.py` (blocked from editing by this work item) has two related
   gaps of its own: a hardcoded model with no override, and structured API
   error information (`should_abort_batch`/`category`/`can_retry`)
   discarded into a plain string before it reaches any caller.

PR #166/#167/#168 fixed the two crashes that were actually hit, via
runtime overrides in `run_pilot.py` (the only file WI-EVENT-0030 permits
editing for ERW-adjacent behavior). This audit is the enumeration of what
those overrides did *not* fix at the source, for scoping as real work once
the current run finishes.

## 2. Scope and source material

Reviewed directly, this session, via `git show origin/main:<path>`:

- `lcats/lcats/analysis/event_role_world/entity_extractor.py`
- `lcats/lcats/analysis/event_role_world/event_extractor.py`
- `lcats/lcats/analysis/event_role_world/relation_extractor.py`
- `lcats/lcats/analysis/event_role_world/discourse_extractor.py`
- `lcats/lcats/analysis/event_role_world/story_relation_extractor.py`
- `lcats/lcats/analysis/event_role_world/hypothesis_extractor.py`
- `lcats/lcats/analysis/event_role_world/processor.py`
- `lcats/lcats/analysis/llm_extractor.py`
- `lcats/lcats/analysis/scene_analysis.py`
- `lcats/lcats/analysis/story_analysis.py`
- `lcats/lcats/analysis/story_processors.py`
- `lcats/lcats/analysis/text_segmenter.py`
- `lcats/lcats/analysis/corpus/assess.py`
- `experiments/03_cross_segment_relation_pilot/run_pilot.py`

Also grounded in Anthropic's own documentation (fetched live this session):
`platform.claude.com/docs/en/agents-and-tools/tool-use/strict-tool-use` and
`platform.claude.com/docs/en/build-with-claude/structured-outputs`.

Governing proposal: `lcats/project/design/proposals/adopted/lcats-event-role-world-extractor/00_proposal.md`
- explicitly separates "scene/sequel extraction" (a Non-Goal to reimplement)
  from "the Event-Role-World extractor," and its own "Implementation
  prerequisites" section already flags that "the current scene/sequel
  prompts'" `json_object` mode is the weaker pattern the ERW stages were
  specifically designed to replace via `tool=` - i.e. this gap in
  `scene_analysis.py` was a known, accepted limitation at proposal time,
  not an oversight introduced later.

## 3. Findings

### Category A - tool schemas missing `strict: true` / `additionalProperties: false`

| File:line | Schema | Inside `event_role_world/`? |
|---|---|---|
| `entity_extractor.py:15` | `ENTITY_TOOL_SCHEMA` | yes |
| `event_extractor.py:16` | `EVENT_TOOL_SCHEMA` | yes |
| `relation_extractor.py:15` | `RELATION_TOOL_SCHEMA` | yes |
| `discourse_extractor.py:17` | `DISCOURSE_TOOL_SCHEMA` | yes |
| `story_relation_extractor.py:31` | `STORY_RELATION_TOOL_SCHEMA` | yes |
| `hypothesis_extractor.py:15` | `HYPOTHESIS_TOOL_SCHEMA` | yes (unused by this pilot - `include_hypotheses=False` - but shared production code) |
| `lcats/lcats/analysis/corpus/assess.py:31` | `ASSESSMENT_TOOL` | **no** - this is the genre-detection tool used by this pilot's own Step 3/4 scan, entirely outside the forbidden path |

Per Anthropic's Strict tool use docs: *"Without strict mode, Claude might
return incompatible types ... or omit required fields, breaking your
functions and causing runtime errors."* None of the seven schemas above set
`strict: true`, and none set the `additionalProperties: false` it
additionally requires on every object (top-level and nested inside array
items) per the JSON Schema limitations docs.

`run_pilot.py`'s `_strict_tool_schema()`/`_close_schema_objects()`
(added in PR #168, hardened further in its review round) already deep-copy
and patch the five ERW schemas that this pilot's `_build_erw_extractors()`
constructs, at runtime, gated to `--backend anthropic` only. This does
**not** reach `hypothesis_extractor.py` (never built by this pilot) or
`corpus/assess.py`'s `ASSESSMENT_TOOL` (built via a separate code path,
`assess_story()`, not through `_build_erw_extractors()` at all).

### Category B - unguarded array-item type assumptions (the exact crash class hit live in PR #168)

Every one of the six Event-Role-World extractors shares the identical
pattern - iterating a tool-result array and calling `.get(...)` on each
item with no `isinstance(item, dict)` guard:

- `entity_extractor.py:142` (`entities`), `:144` (`mentions`)
- `event_extractor.py:185` (`temporal_anchors`), `:203` (`spatial_anchors`), `:219` (`events`), `:225` (`semantic_roles`)
- `relation_extractor.py:131` (`relations`) - **this is the site that actually crashed** (`AttributeError: 'str' object has no attribute 'get'`, fixed for now only via PR #168's runtime strict-schema override, not at the source)
- `discourse_extractor.py:196` (`speech_acts`), `:213` (`explanations`), `:232` (`sf_tags`)
- `story_relation_extractor.py:205` (`relations`)
- `hypothesis_extractor.py:146` (`hypotheses`)

Eleven sites total. Strict mode (Category A) reduces the odds any of these
fire, but does not make the code defensive - a belt-and-suspenders
`isinstance` check at each site is the complete fix regardless of schema
strictness.

### Category C - extractors with no tool schema at all (fully unconstrained JSON-in-text)

- `scene_analysis.py:186` `make_segment_extractor` - Stage 1 segmentation.
  **Confirmed live**: with `--model claude-haiku-4-5-20251001`, 11 of 17
  sampled stories (65%) were excluded with `extraction_error="parsing_error"`
  in the user's own real run, and the `western` stratum had zero included
  stories. This is the actual, currently-blocking reliability problem -
  worse than either crash already fixed.
- `scene_analysis.py:465` `make_semantics_extractor` - per-segment semantics
  evaluation (`output_key="judgment"`). Same risk class as segmentation;
  not exercised by this pilot, so failure rate is unmeasured, not absent.
- `story_analysis.py:398` `make_doc_classification_extractor` - whole-text
  document classification (`output_key="classification"`). Same risk
  class, different module, also unmeasured.

`llm_extractor.py`'s `extract()` method ([`:373-401` region]) behaves
differently on the tool_schema path than the non-tool_schema path: when
`tool_schema` is set, `extracted_output` becomes the **whole** parsed dict
(e.g. `{"relations": [...]}`), with no `output_key` unwrapping - this is
load-bearing for the six ERW extractors (each of which reads a
differently-named top-level key: `relations`, `entities`, etc., not
`output_key`'s default of `"segments"`). Retrofitting `scene_analysis.py`'s
`make_segment_extractor` with a `tool_schema` would change its
`extracted_output` shape from a bare list to `{"segments": [...]}`, which
would break its **other** real caller,
`lcats/lcats/analysis/story_processors.py:76,142` (`segments =
seg_extraction.get("extracted_output") or []` expects a bare list today).
Any fix here needs to update both call sites (or design around it, e.g. a
second, schema-hardened extractor specific to one caller) - not just add
`tool_schema=` to the shared factory function in isolation.

### Category D - `processor.py` (blocked by `forbidden_actions: modify_event_role_world_extractor`)

- `processor.py:315-329` `process_segments()` (plural, the normal public
  entry point) has no `model` parameter - it builds every extractor via its
  factory (`make_entity_extractor(llm_backend)`, etc.) with each one's
  hardcoded `gpt-4o` default baked in. Any caller with a non-OpenAI backend
  silently gets an invalid model ID unless, like `run_pilot.py`, it avoids
  `process_segments()` entirely and drives `process_segment()` (singular)
  directly with self-built, model-overridden extractors.
- `processor.py:130-137` (entity), `:158-160` (event), `:178-182`
  (relation), `:197-201` (discourse), `:223-227` (hypothesis) - each pass's
  `process_segment()` stringifies the structured `api_error` dict (which
  already carries `category`/`can_retry`/`should_abort_batch` from
  `llm_extractor.py`'s `_classify_api_error`) into a plain f-string before
  appending it to `extraction_errors`, discarding that structure. This
  forced `run_pilot.py`'s `FatalPilotError`/`_check_fatal()` (PR #166) to
  re-derive fatality via substring-matching on the stringified message
  instead of reading the flag that already exists one layer up.

## 4. Next steps (not yet started)

1. Let the in-progress real run (Opus, post-Haiku-switch) finish and
   inspect its results/exclusion rate - does switching models alone resolve
   Category C's segmentation failures enough to trust this run's density
   numbers, or is a source-level fix still needed before WI-EVENT-0030 can
   close?
2. Revisit this file, discuss scope, then create the actual work item(s) -
   likely a workstream given the breadth (Categories A/B/D require their
   own work item(s) since they touch `event_role_world/` directly and need
   a `forbidden_actions`-free work item to do so; Category C is a separate,
   more novel design problem per extractor - segmentation's fix in
   particular needs to address the `story_processors.py` blast radius
   noted above, not just bolt on a schema).
3. No code changes have been made as part of this audit - it is a finding
   only.
