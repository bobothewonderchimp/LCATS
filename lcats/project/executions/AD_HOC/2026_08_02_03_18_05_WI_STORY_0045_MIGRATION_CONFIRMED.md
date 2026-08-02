---
execution_id: 2026_08_02_03_18_05_WI_STORY_0045_MIGRATION_CONFIRMED
prompt_id: PROMPT(AD_HOC:WI_STORY_0045_MIGRATION_CONFIRMED)[2026-08-01T23:52:33+00:00]
work_item: AD_HOC
status: landed
rerun_of: 2026_08_01_20_26_07_WI_STORY_0045
pr: 
commit: a1bd77a651aaada3dd0751b649ebeb328c33d0a7
created_at: 2026-08-02T03:18:05+00:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-STORY-0045.md
session_transcript: claude-app:ca0e8b20-2e3a-44f3-90b6-c506f3b98336
---

# Summary

Records the explicit, dated migration-confirmation checklist item
required by `WI-STORY-0045`'s own Required Changes item 1 and its
frontmatter `acceptance:` list's first bullet, before any code in that
work item is touched. The primary `WI-STORY-0045` execution record
(`2026_08_01_20_26_07_WI_STORY_0045`) is already merged and immutable —
per the established convention, this confirmation is recorded in a new,
separate record (`rerun_of` linking back to it) rather than editing that
body.

# Result

**Migration confirmed: 2026-08-01.** The user ran a real, production
`lcats gather` followed by `lcats promote` (not a dry run, not a
representative/test fixture — the actual `corpora/` snapshot). The
resulting commit, `a1bd77a651aaada3dd0751b649ebeb328c33d0a7` ("Promote
bucketed data to corpora."), renamed all 1,868 previously-flat story
files across 12 collections
(`anderson`, `chesterton`, `grimm`, `hemingway`, `london`, `lovecraft`,
`mass_quantities`, `ohenry-four_million`, `ohenry-whirligigs`, `sherlock`,
`wilde_happy_prince`, `wodehouse`) from `<collection>/<story>.json` to
`<collection>/<story>/story.json` — a pure rename (0 insertions, 0
deletions across all 1,868 files per `git diff --stat`), confirming no
content was altered, only the layout.

Verified directly against this exact commit (`git ls-tree -r --full-tree
a1bd77a6 --name-only`), not assumed from the commit message:

- Total `*.json` files under `corpora/`: **1,868**
- Files matching the canonical bucket leaf `.../story.json`: **1,868**
- Remaining flat (non-`story.json`) files: **0**

This matches the acceptance criterion's exact literal check ("`git
ls-files corpora/` shows only `story.json` leaves") and the WI's own
Problem/Context baseline (1,868 flat files, 0 nested, as of the governing
proposal) — the count is unchanged, only every file's layout moved from
flat to bucket, confirming a complete 1:1 migration with no stories lost
or added in the process.

# Validation

- `git ls-tree -r --full-tree a1bd77a6 --name-only | grep '^corpora/' |
  grep '\.json$' | wc -l` → 1868
- `git ls-tree -r --full-tree a1bd77a6 --name-only | grep
  '^corpora/.*/story\.json$' | wc -l` → 1868
- `git ls-tree -r --full-tree a1bd77a6 --name-only | grep '^corpora/' |
  grep '\.json$' | grep -v '/story\.json$' | wc -l` → 0
- `git diff --stat 8a455185 a1bd77a6` → 1868 files changed, 0
  insertions(+), 0 deletions(-) (pure renames)

# Follow-up

- `WI-STORY-0045`'s hard gate (Required Changes item 1 / acceptance
  criterion 1) is now satisfied. The work item itself remains in
  `project/work_items/proposed/` — this record only confirms the
  precondition; implementing the actual code retraction (Required
  Changes items 2-5) is separate, future work, not performed here.
