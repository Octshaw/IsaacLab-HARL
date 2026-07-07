# TASK_PROGRESS

Compact handoff for the assignment-based scan-mobile-manipulator work.

## Current Status

Phase 9G-4A TTL-boundary semantics review is complete.

Phase 9G-4A used fake-env/unit-style validation only. No training was run. No playback was run. No failed-pair memory behavior was changed.

Current TTL semantics:

```text
When failed-pair memory is triggered at logical step T with duration_steps = D,
the pair is active/suppressible for subsequent decision/build_available_actions rows T+1 through T+D.
The pair is inactive at T+D+1.
```

Therefore:

```text
D=5 covers T+4 and T+5, but misses T+6.
D=6, D=7, and D=10 cover T+6 under current semantics.
```

This explains the Phase 9G-3 result: the observed repeated-return rows were at trigger-to-return delta T+6, so `duration_steps=5` expired before reacquisition.

No reward formulas or reward scales, actor/shared observations, `available_actions` shape, assignment action semantics, env dynamics, controller behavior, HARL code, baseline solvers, scenario YAML, installed `site-packages`, cooldown tuning, or Phase 9F redirect guardrail tuning were changed.

No commit was made.

## Latest Completed Phase

Phase 9G-4A: TTL-boundary semantics review and fake-env validation.

Report:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260706/PHASE9G4A_TTL_BOUNDARY_SEMANTICS_REVIEW.md
```

Archive:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260706/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G4A_TTL_BOUNDARY_SEMANTICS_REVIEW_20260706.md
```

## Files Changed Or Created In Phase 9G-4A

Created:

```text
scripts/environments/test_assignment_failed_pair_memory_ttl_boundary_smoke.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260706/PHASE9G4A_TTL_BOUNDARY_SEMANTICS_REVIEW.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260706/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G4A_TTL_BOUNDARY_SEMANTICS_REVIEW_20260706.md
results/assignment_diagnostics/phase9g4a_ttl_boundary_smoke/ttl_boundary_trace.json
```

Updated:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
```

Not changed in Phase 9G-4A:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_wrapper.py
```

Note: the worktree still contains earlier uncommitted Phase 9G-1/9G-2/9G-3 files and modifications.

## Latest Verification

Passed:

```text
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/test_assignment_failed_pair_memory_smoke.py
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/test_assignment_failed_pair_memory_ttl_boundary_smoke.py
conda run -p C:\isaacenvs\isaac45_harl python scripts/environments/test_assignment_failed_pair_memory_smoke.py
conda run -p C:\isaacenvs\isaac45_harl python scripts/environments/test_assignment_failed_pair_memory_ttl_boundary_smoke.py --result_file results/assignment_diagnostics/phase9g4a_ttl_boundary_smoke/ttl_boundary_trace.json
git diff --check
```

`git diff --check` passed with LF-to-CRLF working-copy warnings only.

## Known Issues / Blockers

Phase 9G-3 enabled failed-pair memory with `duration_steps=5` failed because it triggered but suppressed zero actions at the repeated-return rows.

Phase 9G-4A shows this is a TTL boundary issue, not a trigger-source failure:

```text
failed-pair memory trigger source works
D=5 active offsets = 1..5
observed G3 return offset = 6
```

Longer duration has not been playback-validated. Do not infer coverage gains from fake-env TTL coverage alone.

## Do Not Do

Do not commit unless explicitly asked.

Do not train.

Do not run playback unless explicitly authorized.

Do not change reward formulas or reward scales, actor/shared observations, `available_actions` shape, assignment action semantics, env dynamics, controller behavior, HARL, baseline solvers, scenario YAML, installed `site-packages`, cooldown tuning, or redirect guardrail tuning.

Do not change TTL decrement semantics without a separate implementation phase and fake-env update.

## Next Step

Recommended Phase 9G-4B:

```text
Option A: keep current TTL semantics and, only if explicitly authorized, run playback-only validation with a longer disabled-by-default duration such as D=6 or D=10.
```

Reason:

```text
Current semantics are coherent: D future decision/build calls.
D=6 is the smallest duration that covers the observed T+6 return rows.
D=10 is a conservative broader window but carries more overmask/noop/reacquisition risk.
```

Option B remains possible but broader:

```text
adjust TTL decrement timing, update fake-env expectations, then rerun default-disabled identity and enabled playback-only validation
```

## Detailed Reports / Archives

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260706/PHASE9G4A_TTL_BOUNDARY_SEMANTICS_REVIEW.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260706/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G4A_TTL_BOUNDARY_SEMANTICS_REVIEW_20260706.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260706/PHASE9G3_FAILED_PAIR_MEMORY_PLAYBACK_VALIDATION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260706/PHASE9G2_FAILED_PAIR_RELEASE_MEMORY_IMPLEMENTATION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260706/PHASE9G1_LIFECYCLE_RECONSTRUCTION_ANALYZER_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260705/PHASE9G0_ACTIVE_TASK_LIFECYCLE_DESIGN_AUDIT.md
```
