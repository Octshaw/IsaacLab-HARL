# Phase 9G-7D Default-Off Resolver Runtime Adapter Integration Report

Date: 2026-07-08

## Scope

Phase 9G-7D implemented the shared `AssignmentLifecycleResolver` runtime adapter, default-off wiring into the RL wrapper path, default-off wiring into the comparison-method path, and pure Python/Torch integration smoke tests.

No Isaac Sim runtime was launched.

No playback, comparison-method evaluation episode, training, or short training smoke was run.

No commit was made.

## Files Inspected

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/AGENTS.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260708/PHASE9G7A_EFFECTIVE_ASSIGNMENT_RESOLVER_ACTIVE_TARGET_LATCH_DESIGN_AUDIT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260708/PHASE9G7B_SHARED_EFFECTIVE_ASSIGNMENT_RESOLVER_PROTOTYPE_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260708/PHASE9G7C_DEFAULT_OFF_RESOLVER_RUNTIME_INTEGRATION_DESIGN_READINESS_AUDIT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_lifecycle_resolver.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_lifecycle.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_lifecycle_diagnostics.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_wrapper.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_rl_interface.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_controller.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_state.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py
scripts/environments/evaluate_assignment_rl_playback_diagnostics.py
scripts/environments/evaluate_assignment_methods.py
scripts/environments/test_assignment_lifecycle_resolver_smoke.py
scripts/environments/test_assignment_lifecycle_transition_logger_smoke.py
scripts/environments/test_assignment_lifecycle_runtime_integration_smoke.py
```

## Files Created

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_lifecycle_resolver_runtime.py
scripts/environments/test_assignment_lifecycle_resolver_runtime_smoke.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260708/PHASE9G7D_DEFAULT_OFF_RESOLVER_RUNTIME_ADAPTER_INTEGRATION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260708/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G7D_DEFAULT_OFF_RESOLVER_RUNTIME_ADAPTER_INTEGRATION_20260708.md
```

## Files Updated

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_wrapper.py
scripts/environments/evaluate_assignment_methods.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
```

`scripts/environments/evaluate_assignment_rl_playback_diagnostics.py` was inspected but not modified. The RL path uses the wrapper-owned adapter, so a second playback-script resolver owner was not needed in Phase 9G-7D.

## Runtime Adapter Public API

New module:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_lifecycle_resolver_runtime.py
```

Primary class:

```python
AssignmentLifecycleResolverRuntimeAdapter(
    enabled: bool = False,
    num_envs: int,
    num_robots: int,
    num_tasks: int,
    device: str | torch.device = "cpu",
    method_name: str = "unknown",
    output_dir: Path | str | None = None,
    log_diagnostics: bool = False,
    strict_proposals: bool = True,
)
```

Public methods:

```text
resolve_pre_step(problem, assignment_proposal, episode_ids=None, method_metadata=None)
observe_post_step(pre_step_problem, assignment_proposal, effective_assignment, post_step_problem, external_diagnostics=None, done_env_ids=None, episode_ids=None, method_metadata=None)
reset_envs(env_ids=None, episode_ids=None, method_metadata=None)
snapshot()
pop_events()
peek_events()
finalize()
passive_lifecycle_input(assignment_proposal, effective_assignment)
budget_failure_diagnostics(effective_assignment, info=None, budget_trigger_mask=None)
```

The adapter owns exactly one `AssignmentLifecycleResolver`. It does not duplicate resolver behavior logic and does not own policy inference, solver decisions, controller logic, env physics, rewards, masks, or observations.

## Configuration And CLI Fields

Wrapper code-default fields:

```text
assignment_lifecycle_resolver_enabled = False
assignment_lifecycle_resolver_strict_proposals = True
assignment_lifecycle_resolver_log_diagnostics = False
assignment_lifecycle_resolver_output_dir = None
```

Comparison-method CLI fields:

```text
--assignment_lifecycle_resolver_enabled
--log_assignment_lifecycle_resolver
--assignment_lifecycle_resolver_output_dir
```

All resolver behavior remains disabled by default. No scenario YAML changes were added.

## Wrapper Integration Point

`AssignmentHARLWrapper.step()` now follows this order:

```text
pre_step_problem
pre_step_available_actions
assignment_proposal = decode_actions(discrete_actions)
resolver_runtime.resolve_pre_step(pre_step_problem, assignment_proposal)
effective_assignment = pre_result.effective_assignment
assignment_to_env_actions(effective_assignment)
env.step(env_actions)
post_step_problem
executed-behavior diagnostics/reward using effective_assignment
budget diagnostics built from effective_assignment
resolver_runtime.observe_post_step(...)
resolver event drain
done-env assignment diagnostics reset
```

When the resolver is disabled, `effective_assignment` is a clone of `assignment_proposal`, so the controller input and wrapper diagnostics remain behavior-identical.

The wrapper exposes read-only resolver step data through:

```text
get_last_assignment_lifecycle_resolution()
```

The payload contains cloned proposal/effective tensors, pre/post result flags, resolver snapshot, and drained resolver events. Existing default output schemas are not changed merely because the adapter exists.

## Comparison Integration Point

`evaluate_assignment_methods.py` now constructs one `AssignmentLifecycleResolverRuntimeAdapter` per evaluated method. Each method receives a fresh resolver state and method-specific output directory.

Selected order:

```text
assignment_proposal = solver.solve(problem)
resolver_adapter.resolve_pre_step(problem, assignment_proposal)
effective_assignment = pre_result.effective_assignment
viewpoint_assignment_to_actions(unwrapped, effective_assignment)
env.step(actions)
resolver_adapter.observe_post_step(...)
resolver_adapter.finalize()
```

The method name is metadata only. No random/nearest/greedy whitelist was introduced; future method names follow the same standardized `assignment_proposal [E, M]` boundary.

Existing assignment-history rows preserve proposal semantics. Executed-controller paths use `effective_assignment`.

## Default-Off Guarantees

When `enabled=False`:

```text
effective_assignment == assignment_proposal.clone()
assignment_proposal is not mutated
underlying resolver state remains default
no active target or owner state accumulates
no resolver behavior events are emitted
behavior_changed = False
no output directory or files are created when log_diagnostics=False
```

The adapter object may exist, but disabled pre/post/reset calls do not change assignment behavior or accumulate lifecycle state.

## Proposal / Effective Separation

The implementation keeps separate:

```text
assignment_proposal:
  decoded policy/solver request

effective_assignment:
  resolver output consumed by controller conversion
```

Resolver row diagnostics include both values and a `proposal_effective_changed` flag. The wrapper also stores:

```text
last_assignment_proposal
last_effective_assignment
last_assignment
```

`last_assignment` remains the executed assignment used by current wrapper diagnostics.

## Budget Effective-Pair Handoff

Budget release handoff is centralized through:

```text
build_resolver_budget_failure_diagnostics(effective_assignment, info=None, budget_trigger_mask=None)
```

For each budget-triggered `(env_id, robot_id)`, the resolver receives:

```text
target_id = effective_assignment[env_id, robot_id]
```

Only valid target ids are included. Raw rejected proposal targets and noop `-1` are not released.

The runtime smoke covers both mandatory cases:

```text
active target A, proposal B rejected, budget releases A
active target A, proposal noop interpreted as continue, budget releases A
```

## Passive Logger Stream Selection

Shared helper:

```text
select_assignment_lifecycle_passive_input(resolver_enabled, assignment_proposal, effective_assignment)
```

Selected rule:

```text
resolver disabled -> passive logger observes assignment_proposal with proposal_type="standardized_assignment"
resolver enabled -> passive logger observes effective_assignment with proposal_type="effective_assignment_from_resolver"
```

Resolver events remain authoritative for behavior. Passive proxy diagnostics remain separate and do not drive resolver state.

## Pre/Post/Reset Ordering

The adapter enforces paired pre/post rows. If enabled, `observe_post_step()` verifies that:

```text
assignment_proposal matches the pending pre-step proposal
effective_assignment matches the pending resolver output
pre-step problem tensor shapes match the pending pre-step snapshot
```

Post-step completion/budget/release events are observed before done-env reset events. Subset reset clears only selected env ids and preserves continuing env state.

## Resolver Output Schemas

Resolver diagnostics are written only when `log_diagnostics=True`.

Output files:

```text
assignment_lifecycle_resolver_events.jsonl
assignment_lifecycle_resolver_summary.json
assignment_lifecycle_resolver_rows.csv
```

Schema version:

```text
phase9g7d_assignment_lifecycle_resolver_runtime_v1
```

Required row fields implemented:

```text
schema_version
method_name
episode_id
env_id
step
assignment_proposal
effective_assignment
proposal_effective_changed
proposal_accepted
proposal_rejected_reason
continued_from_active_target
new_claim_started
switch_requested
switch_rejected
claim_conflict
claim_winner
claim_loser
active_target_before
active_target_after
task_owner_before
task_owner_after
resolver_events
behavior_changed
```

Summary fields include:

```text
schema_version
enabled
method_name
num_envs
num_robots
num_tasks
total_steps_observed
total_events
proposal_effective_changed_count
event-type counts
active_target_infeasible_step_count
active_target_infeasible_streak
active_target_infeasible_max_streak
active_target_infeasible_robot_target_pairs
stranded_failed_pair_started_count
stranded_failed_pair_recovered_count
stranded_failed_pair_current_count
stranded_failed_pair_max_streak
behavior_changed
```

`finalize()` is idempotent. Resolver events are drainable through `pop_events()` and are not retained in duplicate unbounded buffers by the adapter.

## Active-Infeasibility Monitoring

The adapter adds diagnostics-only counters for executing active targets that are currently unavailable or infeasible:

```text
active_target_infeasible_step_count
active_target_infeasible_streak
active_target_infeasible_max_streak
active_target_infeasible_robot_target_pairs
active_target_infeasible_deferred events from the resolver
```

No automatic release is added. Ownership, active target state, and effective assignment are not changed by this monitor.

`active_target_infeasible_without_motion_count` was not implemented because the pure adapter has no motion diagnostics. It remains deferred until a runtime caller supplies explicit motion state.

## Stranded Detector Behavior

The adapter adds diagnostics-only stranded failed-pair detection. Candidate condition:

```text
task uncovered
task unowned
failed/released pair exists for the task
all robots are unavailable/infeasible or blocked by same-robot failed-pair state
```

Events:

```text
stranded_failed_pair_started
stranded_failed_pair_recovered
```

The detector tracks streaks and affected target ids. It does not clear failed pairs, add TTL expiry, permit retry, alter ownership, or change effective assignment.

## Method Instance Isolation

Comparison-method integration uses a fresh adapter per method:

```text
random / nearest / greedy / future methods each get independent resolver state
method-specific output subdirectory
fresh counters and summary
```

The smoke test verifies independent adapters and output files for multiple method labels, including `future_sota_placeholder`.

## Fake Integration Test Matrix

Smoke script:

```text
scripts/environments/test_assignment_lifecycle_resolver_runtime_smoke.py
```

Coverage:

| Case | Result |
|---|---|
| disabled adapter absolute identity | passed |
| disabled wrapper integration identity | passed |
| disabled comparison integration identity | passed |
| enabled noop-as-continue controller input | passed |
| enabled switch rejection controller input | passed |
| budget release uses effective target | passed |
| proposal/effective logging | passed |
| passive logger stream selection | passed |
| post-step event before reset | passed |
| subset reset | passed |
| fresh adapter per method | passed |
| output file parsing | passed |
| no output collision | passed |
| event draining/finalize | passed |
| active infeasibility monitoring | passed |
| stranded detector start/continue/recovery | passed |
| variable E/M/N | passed |
| input non-mutation | passed |
| strict proposal behavior | passed |
| default output compatibility | passed |

Variable shape coverage:

```text
E=1, M=1, N=3
E=2, M=3, N=5
E=2, M=4, N=8
```

Method labels covered:

```text
happo
random
nearest
greedy
future_sota_placeholder
```

## Input Non-Mutation Result

The runtime smoke verifies the adapter does not mutate:

```text
pre/post problem tensors
assignment proposal
effective assignment supplied to post-step
external diagnostics
done env ids
episode ids
method metadata
passive input selection values
```

## Existing Test Regression Results

The following existing smokes still pass:

```text
scripts/environments/test_assignment_lifecycle_resolver_smoke.py --json
scripts/environments/test_assignment_lifecycle_transition_logger_smoke.py
scripts/environments/test_assignment_lifecycle_runtime_integration_smoke.py
```

This confirms the new runtime adapter did not break the standalone resolver, passive transition logger, or Phase 9G-6 passive diagnostics integration smokes.

## Known Limitations

```text
No Isaac Sim runtime validation in Phase 9G-7D.
No playback or comparison-method evaluation episodes.
No training or short training smoke.
Resolver remains default-off.
Enabled resolver behavior is only fake-smoke validated.
RL playback diagnostics script was not modified; it will access resolver data through the wrapper-owned read-only accessor in a later bounded runtime phase.
No lifecycle-aware observations.
No lifecycle-aware available_actions.
No automatic infeasible-active-target release.
No TTL or retry policy for resolver failed pairs.
Episode-persistent failed-pair rejection can still strand tasks; the new detector only reports it.
```

## Validation Commands And Results

Syntax checks:

```powershell
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_lifecycle_resolver.py
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_lifecycle_resolver_runtime.py
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_wrapper.py
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/evaluate_assignment_methods.py
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/test_assignment_lifecycle_resolver_runtime_smoke.py
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/test_assignment_lifecycle_resolver_smoke.py
```

Result: passed.

Pure smoke tests:

```powershell
conda run -p C:\isaacenvs\isaac45_harl python scripts/environments/test_assignment_lifecycle_resolver_smoke.py --json
conda run -p C:\isaacenvs\isaac45_harl python scripts/environments/test_assignment_lifecycle_resolver_runtime_smoke.py --json
conda run -p C:\isaacenvs\isaac45_harl python scripts/environments/test_assignment_lifecycle_transition_logger_smoke.py
conda run -p C:\isaacenvs\isaac45_harl python scripts/environments/test_assignment_lifecycle_runtime_integration_smoke.py
```

Result: passed.

Repository checks:

```powershell
git diff --check
```

Result: passed; Git emitted LF-to-CRLF working-copy warnings for modified text files only.

```powershell
git status --short --untracked-files=all
```

Result: completed; current status is recorded in `TASK_PROGRESS.md` and final response.

## Boundary Confirmation

No action-space shape, raw HARL action decoding, available actions, available masks, actor observations, shared/critic observations, reward formulas, controller algorithms, env dynamics, task completion semantics, solver decisions, scenario YAML, cooldown tuning, redirect guardrail tuning, or legacy failed-pair memory tuning changed.

Default-off wiring changes were added, but no default assignment behavior changed.

No Isaac Sim command, playback, comparison-method evaluation episode, training, or short training smoke was run.

No commit was made.

## Conclusion

Phase 9G-7D PASS.

The shared runtime adapter exists, the RL wrapper and comparison-method paths share the same default-off adapter contract, proposal/effective assignment separation is preserved, budget handoff uses effective assignments, passive logger coexistence is explicit, reset ordering is covered by fake tests, and diagnostics-only infeasibility/stranding monitors do not change resolver behavior.

## Recommended Next Phase

Recommended next phase:

```text
Phase 9G-7E:
bounded disabled runtime identity and enabled resolver semantic validation
```

Phase 9G-7E may run short bounded RL playback and short bounded nearest/random/greedy evaluations. It must not run training.

Long training remains user-run only after lifecycle observation integration.
