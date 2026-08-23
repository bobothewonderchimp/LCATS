---
execution_id: 2026_08_23_05_29_30_WI_LINGUISTICS_0004_REVIEW
prompt_id: PROMPT(AD_HOC:WI_LINGUISTICS_0004_REVIEW)[2026-08-23T05:26:09+00:00]
work_item: AD_HOC
status: landed
rerun_of: 2026_08_23_05_21_57_WI_LINGUISTICS_0004
pr: https://github.com/xenotaur/LCATS/pull/370
commit: 2dd81ee84afc41befab23dd46fc6adf3314a7fb5
created_at: 2026-08-23T05:29:30+00:00
agent: codex_app
instruction_source: https://github.com/xenotaur/LCATS/pull/370
session_transcript: codex-app:01a02150-2142-7d23-879f-0fdf4457ed76
---

# Summary

Address two reviewer findings on PR #370 before landing the work-item PR.

# Result

- Fixed the snapshot-resume requirement in `WI-LINGUISTICS-0004`: the
  experiment must write `snapshot_manifest.json` with source/copy inventory and
  hashes before analysis begins, and `--resume` must preserve and validate that
  saved provenance instead of deriving provenance from the resumed checkout.
- Fixed validation-command wording in `WI-LINGUISTICS-0004`: experiment
  commands are run from the repository root, while package scripts are run from
  `lcats/` using the project Python environment.

# Validation

- `scripts/version tools` from `lcats/`: completed; reported LCATS
  `0.1.1.dev744+ge213e0bbd.d20260823`, Python `3.11.8`, Ruff `0.16.2`, and
  Black `26.5.1` via the ambient `black` executable. The command also emitted
  an existing `lcats.utils` deprecation warning.
- Initial `scripts/format --check --diff` from `lcats/`: failed because the
  ambient `black` executable was `26.5.1` while the project requires
  `25.11.0`.
- `scripts/develop` from `lcats/`: completed and installed project dev
  dependencies, including Black `25.11.0` and Ruff `0.15.0`.
- `PATH=/Users/centaur/anaconda3/bin:$PATH scripts/format --check --diff` from
  `lcats/`: passed; 216 files would be left unchanged.
- `PATH=/Users/centaur/anaconda3/bin:$PATH scripts/lint` from `lcats/`: passed.
- `PATH=/Users/centaur/anaconda3/bin:$PATH scripts/test` from `lcats/`: passed;
  2017 tests OK.
- `lrh validate` from `lcats/`: 0 errors, 214 warnings.

# Follow-up

- Continue the `/lrh-land` chain for PR #370: confirm fixes, merge gate, and
  closeout.
