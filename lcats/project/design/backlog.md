# LCATS Backlog

Untracked or under-tracked follow-up items: things worth doing that don't
currently have a work item, workstream, or proposal of their own. This is a
plain notes file, not an LRH planning-node type — it isn't schema-validated
by `lrh validate` and doesn't carry frontmatter. When an item here is ready
to be scoped, promote it via `/lrh-work-item` (or `/lrh-workstream` /
`/lrh-proposal` if it's bigger than one work item) and remove it from this
list rather than letting it live in both places.

Add an entry here whenever a workstream closes with unresolved Non-Goals,
or when review/investigation surfaces a real gap that isn't worth blocking
the current PR on. Each entry should say what's known now and what the
first concrete next step would be — not a full design.

---

## From WS-STORY-BUCKET-LAYOUT's Non-Goals (closed 2026-08-02)

These three were explicitly deferred in `WS-STORY-BUCKET-LAYOUT`'s Non-Goals
section. Now that the workstream is closed and archived
(`project/workstreams/resolved/WS-STORY-BUCKET-LAYOUT.md`), they have no
active tracker at all.

### Hardcoded flat-layout paths in two notebooks

`lcats/notebooks/12_extract_scenes.ipynb` and `13_clean_corpus.ipynb` were
called out as still assuming the retracted flat `<collection>/<story>.json`
layout. Per `AGENTS.md`, notebooks aren't edited as a matter of course, so
this was deliberately left for a dedicated follow-up. **Next step:** confirm
which cells actually construct flat-style paths (a fresh read against
current notebook content, not this note), then scope a small WI to update
them to the bucket layout.

### Non-recursive glob bugs in two experiment scripts

`experiments/02_llm_backend_comparison/run_comparison.py` and
`experiments/02_llm_backend_comparison/smoke_test.py` were flagged as having
non-recursive glob bugs; `experiments/03_cross_segment_relation_pilot/check_segmentation_reliability.py`
has a related stem-collision output-naming bug. Described as more pressing
than the notebooks item (silent failure mode) but still deferred so all
three get fixed once against the final (now-retracted) layout. **Next
step:** re-verify each bug is still present, then scope one small WI
covering all three (same root cause family).

### Whether notebooks/ and experiments/ should be librarized

Open architecture question: should `notebooks/` and `experiments/`
implementation code move into the installable `lcats` package with unit
test coverage, rather than living as standalone scripts? No decision was
made; explicitly out of scope for `WS-STORY-BUCKET-LAYOUT`. **Next step:**
this is a proposal-shaped question (affects testing strategy and packaging
conventions), not a work item — raise via `/lrh-proposal` if/when someone
wants to press on it.

---

## Other known gaps worth following up on

### `lcats survey` and `lcats promote` disagree on which mojibake findings to flag

`lcats survey --mode specials` applies the legacy `unicode.DEFAULT_EXCLUDED_CHARS`
list (via `cli.py`'s `run_survey`), which silently lets through some
mojibake characters (e.g. bare `Â`/`Ã`/`â`) that `lcats promote`'s
independent `survey_collection()` (in `promote.py`, using an empty
exclusion set) correctly flags. Confirmed by direct testing, not inference
— `lcats promote --dry-run` is the real release gate and isn't affected,
but a human running `lcats survey` for diagnostics can see zero findings on
a file that genuinely has unrepaired mojibake. Has a nominal home —
`WS-SPECIALS-CLEANUP` (still `status: proposed`, `stage: assessed`) was
meant to revisit this architecture, but no specific WI covers it yet.
**Next step:** likely resolution is making `lcats survey`'s CLI stop
applying `unicode.DEFAULT_EXCLUDED_CHARS` by default (or sharing one
exclusion path between both commands) — scope as a WI under
`WS-SPECIALS-CLEANUP` when that workstream is next picked up.

### `VALID_GENRES` still has 4 genres, not the reconciled 8

`lcats/src/lcats/analysis/corpus/assess.py`'s `VALID_GENRES` is
`("science fiction", "horror", "western", "romance")` (confirmed current as
of 2026-08-02) — the Worldcon 2026 paper's actual target is 8: science
fiction, horror, humor, western, romance, mystery, fantasy, adventure. This
gap already has a work item, `WI-ASSESS-0031` (`status: proposed`, not yet
implemented) — not a backlog item on its own, listed here only as a
pointer. Two related gaps from the same reconciliation genuinely have no
work item yet:

- **Current-classifier full-corpus survey** under the 8-genre scheme —
  needed before sizing any stratified annotation pilot; do not reuse the
  2025-10 `experiments/01_classify_corpora` counts, they're a different,
  older classifier's output.
- **Re-scoping `WI-EVENT-0030`'s stratified pilot** for 8 genres instead of
  4 — depends on both `WI-ASSESS-0031` and the corpus survey above.

Both carry real API cost and should get cost estimates before being scoped
as work items, per `project/design/event-role-world-genre-target-reconciliation.md`'s
own recommendation.

### ERW pipeline audit's Category E (cost/checkpointing/local-model options) never promoted to a proposal

`project/audits/2026-07-27-erw-pipeline-structured-output-reliability-audit.md`'s
Category E — cost/logging/checkpointing/local-model options, plus a
corpus-wide reconsideration of workflow-orchestration options — was
deliberately left unscoped when the audit's other categories became
`WI-EVENT-0032`/`WI-EVENT-0033`. It still lives only as prose inside the
audit doc. A follow-on vetting pass (of `run_pilot.py`, 2026-07-29) found
this is now a real blocker: a minimal real Event-Role-World pilot run costs
~98-479 LLM calls with no resume/checkpoint capability and no test coverage
on the cost-dominant functions — not safe to run again without it. **Next
step:** promote Category E to a real `/lrh-proposal`, incorporating the
vetting pass's 3 additional gaps (a bounded small-scale trial, call-count
estimation, rate-limit/retry classification) alongside the audit's original
scope.

~~### Pre-existing masking bug in `discovery.py`'s recursive selector~~ — **fixed, [PR #208](https://github.com/xenotaur/LCATS/pull/208), merged 2026-08-02**

Resolved: `_walk_canonical_story_files` no longer mistakes a stray flat
`story.json` at a collection root for a leaf story bucket. Fixed via a new
`_is_leaf_story_bucket` helper that breaks the ambiguity with a domain
rule — a directory is only a real leaf bucket if none of its own
subdirectories are themselves buckets (genuine story buckets never nest
inside each other). No work item was created for this fix; it landed as
an ad hoc PR with its own backfilled execution records. Left here as a
record of resolution rather than deleted outright, since the PR itself
carries no pointer back to this backlog entry.
