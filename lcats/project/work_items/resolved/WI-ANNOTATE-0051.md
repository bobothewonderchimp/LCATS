---
resolution: "Implemented and merged via PR #241 (commit 99457ce3): built lcats annotate, running lcats assess (genre) and scene_analysis (segmentation) over story buckets, writing genre.json/scenes.json + README.md sidecars into data/ bucket directories, with checkpoint-safe writes (lcats.utils.checkpoint, dedicated .annotate_checkpoints/ dir, never data/corpora/cache). Two review rounds (12 findings total, 6 codex + 6 copilot) hardened it further: alignment/validation error rejection, atomic sidecar/README writes, stale-sidecar removal on failed recompute, module-import convention, full fingerprint completeness (author/url, user prompt template, max_tokens), clean error-message extraction, and an empty-collection guard. Pre-push self-review (cold subagent) caught 2 more issues before the PR's first bot round. See execution record project/executions/WI-ANNOTATE-0051/2026_08_07_07_01_05_WI_ANNOTATE_0051.md."
blocked_reason: null
blocked: false
id: WI-ANNOTATE-0051
title: Build lcats annotate command with checkpoint-safe sidecar writes
type: deliverable
status: resolved
owner: unassigned
contributors: []
assigned_agents: []
related_focus:
  - FOCUS-WORLDCON-2026
related_roadmap:
  - ROADMAP-CORE
related_workstreams:
  - WS-WORLDCON-FAST-PATH-ANNOTATION
related_design:
  - project/design/proposals/adopted/worldcon-fast-path-annotation/00_proposal.md
  - project/design/proposals/adopted/lcats-pipeline-checkpointing/00_proposal.md
depends_on:
  - WI-ANNOTATE-0050
blocked_by: []
expected_actions:
  - create_file
  - edit_file
  - run_tests
  - create_pr
  - add_cli_command
forbidden_actions:
  - force_push
  - delete_branch
  - implement_specials_audit_sidecar
acceptance:
  - lcats annotate exists as a registered subcommand in lcats/src/lcats/cli.py, following the assess/promote parent-parser + _handle_<name> pattern
  - It iterates collection directories, then calls discovery.iter_collection_story_files once per collection - never directly against a multi-collection root
  - It writes genre.json and scenes.json sidecars plus a per-bucket README.md summarizing them
  - Each sidecar write goes through lcats.utils.checkpoint's read_checkpoint/write_checkpoint, keyed per story-bucket and per stage, with the model/prompt configuration in the fingerprint
  - lrh validate reports 0 errors
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
artifacts_expected:
  - lcats/src/lcats/analysis/corpus/annotate.py
  - lcats/src/lcats/analysis/corpus/annotate_cli.py
  - lcats/src/lcats/cli.py
---

## Summary

Build `lcats annotate`, a new CLI command that runs `lcats assess`
(genre) and `scene_analysis` (scene/sequel segmentation) over story
buckets, writing `genre.json`/`scenes.json` sidecars plus a per-bucket
`README.md`, with each sidecar write made crash-safe via the existing
checkpoint pattern.

## Problem / Context

`PROP-WORLDCON-FAST-PATH-ANNOTATION` (adopted) and
`WS-WORLDCON-FAST-PATH-ANNOTATION` (this item's governing workstream)
exist because the ERW event/relation extractor is too slow/costly/
unreliable to produce a Worldcon 2026 paper dataset in time. `lcats
assess` and `scene_analysis` are the two extractors mature enough to
trust at scale (once WI-ANNOTATE-0050's truncation fixes land), but
neither has a first-class way to persist its output as a reusable
sidecar in the corpus's bucket layout.

Two design constraints from PR review rounds on the proposal/workstream
apply directly to this item's implementation, not just its design:

1. **Per-collection iteration only.** `discovery.iter_collection_story_files`
   (`lcats/src/lcats/analysis/corpus/discovery.py:54`) only checks the
   immediate children of the path it's given for a `story.json` — called
   directly against a multi-collection root (`data/`/`corpora/`), it
   silently yields nothing, since a root's immediate children are
   collections, not story buckets (PR #226 review finding). `lcats
   annotate` must enumerate collection directories first (mirroring
   `promote.py`'s `promote_collections`, `lcats/src/lcats/analysis/corpus/promote.py`)
   and call the selector once per collection.
2. **Checkpoint-safe writes.** `lcats.utils.checkpoint`
   (`lcats/src/lcats/utils/checkpoint.py`) — from the already-adopted,
   already-implemented `PROP-LCATS-PIPELINE-CHECKPOINTING` — provides
   `read_checkpoint`/`write_checkpoint` with atomic publication and a
   fingerprint-based staleness check. Without it, an interruption
   between writing `genre.json` and `scenes.json` for a story could
   either repeat a paid LLM call on resume, or pair a valid `genre.json`
   with a `scenes.json` produced under a different model/prompt
   configuration, corrupting the dataset (PR #230 review finding).

### Duplication search
- In-repo: No existing `lcats annotate` implementation.
- Sibling repos: None identified.
- External libraries: None identified.
- Recommendation: Proceed.

### Demand search
- Work items: None found requesting this directly beyond this item's own
  workstream.
- Proposals: `PROP-WORLDCON-FAST-PATH-ANNOTATION` requests this command
  directly.
- Backlog: No matching entry.
- Recommendation: Proceed.

## Scope

- Implement `lcats annotate` as a new subcommand, registered in
  `lcats/src/lcats/cli.py` following the `assess`/`promote` pattern (a
  `build_parser()` in a new `annotate_cli.py`, a `_handle_annotate`
  dispatcher, `command_parsers["annotate"]`).
- Write `genre.json`, `scenes.json`, and a per-bucket `README.md` into
  each story's bucket directory under `data/`.
- Wire per-sidecar writes through `lcats.utils.checkpoint`.
- Does not implement the specials/mojibake audit sidecar (deferred, per
  the proposal's Decision 1).

## Required Changes

1. Create `lcats/src/lcats/analysis/corpus/annotate.py` (or similarly-named
   module) implementing the core annotation logic: given a collection
   directory, enumerate story buckets via
   `discovery.iter_collection_story_files`, run `lcats assess`'s
   `assess_story` and `scene_analysis.make_segment_extractor`'s
   extractor per story, and write `genre.json`/`scenes.json`.
2. For each sidecar write, call `checkpoint.resolve_roots(...)` to get a
   `CheckpointRoots`, then `checkpoint.read_checkpoint`/`write_checkpoint`
   keyed by story-bucket identity and sidecar stage name (e.g. `"genre"`,
   `"scenes"`), with a fingerprint including model name and
   prompt/schema version — following
   `PROP-LCATS-PIPELINE-CHECKPOINTING`'s Decision 2 requirement
   (success/failure predicate + configuration identity).
3. Write the per-bucket `README.md` after a bucket's sidecars are
   written, summarizing `story.json` plus whatever sidecars exist.
4. Add a top-level enumeration function that iterates every collection
   directory under a given root (mirroring
   `promote.promote_collections`'s pattern) and calls the per-collection
   annotation logic once per collection.
5. Create `lcats/src/lcats/analysis/corpus/annotate_cli.py` with `build_parser()`
   following `assess_cli.py`/`promote_cli.py`'s shape.
6. Register the `annotate` subcommand in `lcats/src/lcats/cli.py`, following
   the exact `assess`/`promote` registration pattern (parent parser +
   `subparsers.add_parser` + `set_defaults(handler=_handle_annotate)` +
   `command_parsers["annotate"] = annotate_parser`).
7. Add unit tests for the core annotation logic, the checkpoint
   integration (interrupted-then-resumed scenario), and the CLI
   registration.

## Non-Goals

- Does not implement the specials/mojibake audit sidecar.
- Does not extend `lcats promote`'s sidecar validation — that is
  WI-ANNOTATE-0052.
- Does not fix `lcats stats`'s selector — that is WI-ANNOTATE-0053.
- Does not run the actual per-genre annotation pass — that is
  WI-ANNOTATE-0054.
- Does not depend on genre count — `WI-ASSESS-0031`'s 4→8 genre
  extension landed via PR #224 before this item was drafted; `lcats
  annotate` works against whatever `assess.VALID_GENRES` currently
  contains, with no genre-count-specific logic of its own.

## Acceptance Criteria

- `lcats annotate <collection-dir>` runs end to end against at least one
  real collection, writing `genre.json`/`scenes.json`/`README.md` per
  story bucket.
- Running it directly against a multi-collection root does not silently
  produce zero output — it processes every collection.
- Interrupting a run mid-story (simulated) and resuming does not repeat
  a completed stage's paid call, and does not pair sidecars from
  mismatched configurations.
- `lrh validate` reports 0 errors.

## Validation

- `scripts/version tools`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh validate`
- `lcats annotate --help`

## Risk Notes

- Checkpoint fingerprinting must hash the actual model/prompt/schema
  identity, not just a label — see
  `feedback_checkpoint_fingerprint_must_hash_actual_input` precedent
  from this project's own checkpoint work.
- README.md generation must never be mistaken for a JSON sidecar by any
  discovery/promote/stats selector — confirm it isn't matched by
  `find_json_files` or `iter_collection_story_files`.

## Dependencies / Order

Depends on WI-ANNOTATE-0050 (truncation fixes must land first, or this
command will reproduce both failures immediately). WI-ANNOTATE-0052 and
WI-ANNOTATE-0054 depend on this item.

## Related Workstream and Designs

- Workstream: `project/workstreams/proposed/WS-WORLDCON-FAST-PATH-ANNOTATION.md`
- Design: `project/design/proposals/adopted/worldcon-fast-path-annotation/00_proposal.md`
  (Design Decisions 2, 3, 6)
- Design: `project/design/proposals/adopted/lcats-pipeline-checkpointing/00_proposal.md`
