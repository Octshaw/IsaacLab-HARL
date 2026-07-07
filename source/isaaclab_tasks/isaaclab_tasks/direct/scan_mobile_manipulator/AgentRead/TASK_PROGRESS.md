# TASK_PROGRESS

Compact handoff for the assignment-based scan-mobile-manipulator work.

## Current Status

Phase 9G-5 design decision review is complete.

Phase 9G-5 was documentation-only. No code behavior changed. No Python source files were modified in this phase. No training was run. No playback was run. No broad evaluation or simulation rollout was run. No commit was made.

No wrapper behavior, env behavior, TTL duration default, TTL decrement timing, reward formula/scale, actor/shared observation, `available_actions` shape, assignment action id semantics, controller behavior, HARL code, baseline solver, scenario YAML, installed package, cooldown tuning, Phase 9F redirect guardrail tuning, new failure criteria, or env-level lifecycle behavior was changed.

## Latest Decision

Phase 9G-5 decision:

```text
Stop extending TTL-only failed-pair memory as the main solution path.
Retain the current failed-pair memory code disabled-by-default as diagnostic/experimental guardrail code.
Do not run D=10 automatically.
Treat D=10 as optional only if the user explicitly wants one bounded playback-only stress test.
Proceed toward explicit active-task/release lifecycle design through a narrow documentation-only boundary audit.
```

Reason:

```text
D=6 proved TTL memory can suppress and delay the previously missed T+6 return rows.
D=6 did not reduce total same-owner returns.
D=6 did not produce coverage gain after release or within 20 steps.
The same failed pairs were selected at T+7 immediately after memory expiry.
TTL-only masking changes temporary action availability, not task ownership, execution state, release semantics, or policy-visible failure state.
```

## Latest Completed Phase

Phase 9G-5: failed-pair memory design decision review.

Report:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260707/PHASE9G5_FAILED_PAIR_MEMORY_DESIGN_DECISION_REVIEW.md
```

Archive:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260707/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G5_FAILED_PAIR_MEMORY_DESIGN_DECISION_REVIEW_20260707.md
```

## Files Created Or Updated In Phase 9G-5

Created:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260707/PHASE9G5_FAILED_PAIR_MEMORY_DESIGN_DECISION_REVIEW.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260707/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G5_FAILED_PAIR_MEMORY_DESIGN_DECISION_REVIEW_20260707.md
```

Updated:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
```

Not modified in Phase 9G-5:

```text
Python source files
assignment_harl_wrapper.py
scenario_config.py
scan_mobile_manipulator_env.py
assignment_state.py
analyzer scripts
repository scenario YAML files
```

Note: the worktree still contains earlier uncommitted Phase 9G-1/9G-2/9G-3/9G-4A/9G-4B files and modifications.

## Active Architecture / Implementation Path

Current failed-pair memory status:

```text
disabled by default
wrapper-local
pair-scoped as (env, robot, target)
useful as diagnostic/experimental guardrail code
not a full active-task lifecycle
not recommended as the main solution path
```

Recommended path:

```text
Phase 9G-6A: explicit active-task/release lifecycle boundary audit.
```

Keep the next phase documentation-only and focused on:

```text
ownership
robot idle/executing transitions
pair failure
release
reassignment
observation visibility
action semantics
checkpoint compatibility
baseline comparability
```

## Latest Verification

Allowed validation for Phase 9G-5 completed:

```text
git status --short --untracked-files=all
result: completed; worktree still contains earlier uncommitted Phase 9G files plus the new Phase 9G-5 report/archive.

git diff --check
result: passed with LF-to-CRLF working-copy warnings only.
```

No Python validation is required because Phase 9G-5 modified documentation only and did not modify Python source files.

## Known Issues / Blockers

Temporary TTL-only failed-pair memory can delay same-owner reacquisition but has not reduced total same-owner returns or improved coverage.

D=10 is not necessary for the main design decision. It may be run only as an explicitly authorized bounded diagnostic to test whether longer TTL merely shifts the return again.

A true lifecycle likely changes action semantics even if `available_actions` shape stays `[M, N+1]`: assignment would mean "assign a target when idle or released" rather than "choose a target every step."

## Do Not Do

Do not commit unless explicitly asked.

Do not train.

Do not run playback or D=10 unless explicitly authorized.

Do not continue TTL tuning as the main solution path.

Do not change reward formulas or reward scales, actor/shared observations, `available_actions` shape, assignment action semantics, env dynamics, controller behavior, HARL, baseline solvers, scenario YAML, installed `site-packages`, cooldown tuning, or redirect guardrail tuning.

Do not implement env-level lifecycle without a separate design and implementation phase.

## Next Step

Recommended Phase 9G-6A:

```text
Explicit active-task/release lifecycle boundary audit.
Documentation/design only.
No implementation.
No training.
No playback.
```

Optional alternative, only if explicitly authorized:

```text
Phase 9G-6B: one bounded D=10 playback-only diagnostic.
```

Do not treat D=10 as a tuning loop or as the default next phase.

## Detailed Reports / Archives

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260707/PHASE9G5_FAILED_PAIR_MEMORY_DESIGN_DECISION_REVIEW.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260707/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G5_FAILED_PAIR_MEMORY_DESIGN_DECISION_REVIEW_20260707.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260706/PHASE9G4B_FAILED_PAIR_MEMORY_D6_PLAYBACK_VALIDATION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260706/PHASE9G4A_TTL_BOUNDARY_SEMANTICS_REVIEW.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260706/PHASE9G3_FAILED_PAIR_MEMORY_PLAYBACK_VALIDATION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260706/PHASE9G2_FAILED_PAIR_RELEASE_MEMORY_IMPLEMENTATION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260706/PHASE9G1_LIFECYCLE_RECONSTRUCTION_ANALYZER_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260705/PHASE9G0_ACTIVE_TASK_LIFECYCLE_DESIGN_AUDIT.md
```
