# TASK_PROGRESS

Compact handoff for the assignment-based scan-mobile-manipulator work.

## Current Status

Phase 9G-1 is complete.

This phase added a standalone diagnostic-only lifecycle proxy reconstruction analyzer for existing `assignment_history.csv` rows. It is offline CSV analysis only and does not implement lifecycle behavior.

No env or wrapper behavior changed. No training was run. No playback was run. No reward formulas, reward scales, actor/shared observations, `available_actions` shape, assignment action semantics, env dynamics, controller behavior, HARL, baseline solvers, scenario YAML, installed `site-packages`, cooldown behavior, redirect guardrail behavior, or default scenario behavior were changed.

No commit was made.

## Latest Completed Phase

Phase 9G-1: lifecycle proxy reconstruction analyzer.

Report:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260706/PHASE9G1_LIFECYCLE_RECONSTRUCTION_ANALYZER_REPORT.md
```

## Analyzer

Created:

```text
scripts/environments/analyze_phase9g1_lifecycle_reconstruction.py
```

The analyzer:

```text
accepts one or more existing assignment_history.csv files
builds a per-file column inventory before reconstruction
reports required/optional columns present and missing
emits row-level lifecycle proxy CSV
emits file-level summary CSV
emits aggregate summary JSON
emits column inventory JSON
prints concise console summaries
```

Proxy states:

```text
idle_or_noop_proxy
assigned_proxy
executing_proxy
completed_proxy
failed_budget_proxy
released_after_failure_proxy
returned_after_release_proxy
teammate_reacquired_proxy
unknown_or_insufficient_columns
```

Required columns:

```text
episode
env_id
step
robot_id
is_noop
selected_viewpoint_id or assigned_viewpoint_id
```

## Validation Result

Interpreter:

```text
conda run -p C:\isaacenvs\isaac45_harl python -c "import sys; print(sys.executable)"
result: C:\isaacenvs\isaac45_harl\python.exe
```

Syntax:

```text
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/analyze_phase9g1_lifecycle_reconstruction.py
result: passed
```

Self-test:

```text
conda run -p C:\isaacenvs\isaac45_harl python scripts/environments/analyze_phase9g1_lifecycle_reconstruction.py --self-test --output_dir results/assignment_diagnostics/phase9g1_lifecycle_reconstruction_self_test
result: passed
```

Self-test covered:

```text
successful completion
budget-trigger failure
cooldown/release proxy
same robot returning to the failed pair
teammate reacquiring the released target
noop row
covered-before row
overlapping trigger windows
missing optional columns
```

Existing local Phase 9F history analysis:

```text
conda run -p C:\isaacenvs\isaac45_harl python scripts/environments/analyze_phase9g1_lifecycle_reconstruction.py --history results/assignment_diagnostics/phase9f2c_trigger_window_row_level_validation/assignment_history.csv results/assignment_diagnostics/phase9f5_redirect_guardrail_validation/assignment_history.csv --output_dir results/assignment_diagnostics/phase9g1_lifecycle_reconstruction_phase9f_existing
result: passed
```

Existing-history aggregate:

```text
files = 2
rows = 1794
unsupported = 0
budget_failed_segments = 12
released_segments = 12
same_owner_returns = 12
teammate_reacquires = 4
median_same_owner_return_delay_steps = 5
coverage_gain_after_release_count = 0
coverage_gain_within_20_count = 0
phase9g2_signal = supports_phase9g2_failed_pair_release_memory
```

Final whitespace validation:

```text
git diff --check
result: passed
notes: Git reported an LF-to-CRLF working-copy warning for TASK_PROGRESS.md only.
```

## Key Files

Created:

```text
scripts/environments/analyze_phase9g1_lifecycle_reconstruction.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260706/PHASE9G1_LIFECYCLE_RECONSTRUCTION_ANALYZER_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260706/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G1_LIFECYCLE_RECONSTRUCTION_ANALYZER_20260706.md
```

Updated:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
```

Generated analyzer outputs:

```text
results/assignment_diagnostics/phase9g1_lifecycle_reconstruction_self_test/
results/assignment_diagnostics/phase9g1_lifecycle_reconstruction_phase9f_existing/
```

These are offline analyzer outputs only. They are not playback/training outputs.

## Phase 9G-2 Recommendation

Phase 9G-1 evidence supports starting Phase 9G-2 as a small, disabled-by-default wrapper-local failed-pair/release-memory experiment.

Boundary for Phase 9G-2:

```text
disabled by default
wrapper-local first
preserve observation shape
preserve available_actions shape
preserve reward formulas and scales
preserve assignment action semantics
preserve env dynamics and controller behavior
do not modify HARL or baseline solvers
do not modify scenario YAML unless explicitly requested
do not tune cooldown
do not tune Phase 9F redirect guardrail
fake-env smoke before playback
no training
```

Rationale:

```text
Existing Phase 9F histories show 12/12 budget-failed proxy segments released and later reacquired by the same owner.
Coverage gain within 20 steps after release is 0/12.
Phase 9F redirect guardrail did not reduce this repeated-return pattern.
```

## Known Issues / Risks

```text
Lifecycle states are proxy labels, not env-owned lifecycle state.
The analyzer is evidence-gathering only and cannot prove performance improvement.
Wrapper-local failed-pair memory would be hidden state if later used for training without observation exposure.
Future masking can create overmask/noop pressure and needs fail-open/noop diagnostics.
Env-level task_status / robot_status lifecycle should remain deferred until wrapper-local evidence is insufficient.
```

## Do Not Do

Do not commit unless explicitly asked.

Do not train.

Do not run playback unless explicitly authorized.

Do not implement env-level lifecycle in Phase 9G-2.

Do not change reward formulas or reward scales, actor/shared observations, `available_actions` shape, assignment action semantics, env dynamics, controller behavior, HARL, baseline solvers, scenario YAML, installed `site-packages`, cooldown behavior, redirect guardrail behavior, or default scenario behavior.

## Next Step

Recommended next phase:

```text
Phase 9G-2: design and implement a disabled-by-default wrapper-local failed-pair/release-memory guardrail, with fake-env smoke coverage only.
```

Start by reading:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260706/PHASE9G1_LIFECYCLE_RECONSTRUCTION_ANALYZER_REPORT.md
scripts/environments/analyze_phase9g1_lifecycle_reconstruction.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_wrapper.py
scripts/environments/test_assignment_cooldown_mask_smoke.py
```

## Detailed Reports / Archives

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260706/PHASE9G1_LIFECYCLE_RECONSTRUCTION_ANALYZER_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260706/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G1_LIFECYCLE_RECONSTRUCTION_ANALYZER_20260706.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260705/PHASE9G0_ACTIVE_TASK_LIFECYCLE_DESIGN_AUDIT.md
```
