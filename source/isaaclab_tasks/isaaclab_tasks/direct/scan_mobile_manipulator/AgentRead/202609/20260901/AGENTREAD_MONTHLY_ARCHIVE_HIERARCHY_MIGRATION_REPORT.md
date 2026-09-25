# AgentRead Monthly Archive Hierarchy Migration Report

Date: 2026-09-01

Classification:
`AGENTREAD-MONTHLY-ARCHIVE-HIERARCHY-MIGRATION-COMPLETE-AWAITING-GPT-REVIEW`

## 1. Migration purpose

Reduce top-level `AgentRead` directory growth while preserving each immutable
daily archive boundary and every historical report filename.

## 2. Old hierarchy

The pre-migration archive hierarchy placed each `YYYYMMDD` directory directly
under `AgentRead`.

## 3. New hierarchy

The permanent hierarchy is `AgentRead/YYYYMM/YYYYMMDD/`. The `YYYYMM` directory
is grouping only; Markdown files remain inside their original `YYYYMMDD`
directory and are not flattened.

## 4. Date directories migrated

42 date directories were migrated:

- `202606`: `20260604`, `20260605`, `20260606`, `20260610`, `20260615`,
  `20260622`, `20260623`, `20260624`, `20260625`, `20260628`, `20260629`,
  `20260630`
- `202607`: `20260701`, `20260702`, `20260705`, `20260706`, `20260707`,
  `20260708`, `20260709`, `20260710`, `20260720`, `20260721`, `20260722`,
  `20260724`, `20260727`, `20260729`
- `202608`: `20260803`, `20260807`, `20260808`, `20260809`, `20260814`,
  `20260821`, `20260822`, `20260823`, `20260824`, `20260825`, `20260826`,
  `20260827`, `20260828`, `20260829`, `20260831`
- `202609`: `20260901`

All four month directories were newly created. The first 41 daily directories
were moved with `git mv`; the pre-existing untracked `20260901` directory was
moved with a filesystem rename.

## 5. Path references updated

- 1,962 concrete old-hierarchy path occurrences were repaired.
- 11 generic archive-rule occurrences were upgraded.
- 274 documentation files received path-only repairs.
- Two current/historical handoff files using bare date-directory paths were
  updated to include the month directory.
- No standalone date values or dates embedded in filenames were mechanically
  rewritten.

## 6. AGENTS.md rule changes

`AGENTS.md` now requires deriving both the local `YYYYMMDD` date and its
`YYYYMM` month, creating the month directory when absent, and writing all long
plans, reports, design notes, investigations, phase summaries, and handoff
archives under `AgentRead/YYYYMM/YYYYMMDD/`. It explicitly prohibits falling
back to the former one-level daily layout.

## 7. Relative-link audit

All 23 relative Markdown links in migrated reports were resolved against their
new locations. Ten links from two `20260727` design documents to top-level
`AGENTS.md` or `TASK_PROGRESS.md` required one additional parent traversal.
Thirteen same-month links from `20260727` to `20260724` remained correct without
text changes. The post-repair result is 23/23 existing targets.

## 8. Verification

- Pre-move inventory: 373 files, 5,677,310 bytes.
- Immediate post-move SHA-256 and length comparison: 373/373 preserved; zero
  missing, zero extra, zero content changes.
- Top-level eight-digit date directories after migration: zero.
- Month directories contain daily directories rather than flattened Markdown
  files.
- Concrete old-hierarchy path residue after repair: zero active references.
- Generic old-rule residue after repair: zero current-rule references.
- Final archive inventory: 374 files under daily directories, consisting of
  the 373 migrated files plus this report; with the two top-level handoff files,
  `AgentRead` contains 376 files in total.
- Current `TASK_PROGRESS.md` detailed-report targets: 3/3 exist.
- Git move review: 359 tracked files are exact `R100` moves; the remaining 14
  pre-existing daily files were untracked and remained untracked after their
  directory move.
- Tracked working-tree changes introduced by this migration are confined to
  `AgentRead`; `git diff --check` passed.
- Training, simulation, playback, Isaac Lab, GPU evaluation, Python tests, and
  compilation checks were not run because they are outside this task's
  documentation-only verification boundary.

## 9. Known exceptions

The repository contains 14 pre-existing historical or illustrative Markdown
target strings whose referenced files do not exist. They include wrong-date
historical expectations, a doubled `.md` suffix, and filenames containing
literal `...` placeholders. They were not introduced by this migration and
were intentionally not corrected because this task does not authorize general
historical-content cleanup. Current `TASK_PROGRESS.md` detailed-report targets
and the migration report target exist.

The starting worktree also contained unrelated, unstaged B2-R1 through B2-R5
source, test, and documentation changes. They were preserved and were not
reverted, staged, or committed.

The 359 tracked archive moves are present in the index as the normal result of
the requested `git mv` operation. Subsequent reference-only working-tree edits
and all pre-existing unrelated changes remain unstaged. No commit was created.

## 10. Scope statement

This was documentation/archive-only work. No runtime, RL, HARL, environment,
controller, wrapper, solver, reward, observation/action, training, scenario, or
installed `site-packages` behavior changed. No training or simulation was run.
No commit was created.
