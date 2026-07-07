# Phase 9G-6C Passive Lifecycle Runtime Integration Report

Date: 2026-07-07

## Scope

Phase 9G-6C integrated the Phase 9G-6B passive shared lifecycle transition logger into the two runtime diagnostics entry points behind default-off diagnostics flags:

- RL playback diagnostics path.
- Generic comparison-method evaluation path.

This phase is diagnostics-only and integration-smoke-only. It does not change assignment behavior, method proposals, action decoding, masks, observations, rewards, controller commands, environment dynamics, HARL behavior, baseline solver behavior, scenario YAML, cooldown behavior, redirect guardrail behavior, or failed-pair memory behavior.

No playback, comparison-method evaluation episode, simulation rollout, or training was run.

## Files Inspected

Project guidance and reports:

- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/AGENTS.md`
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md`
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260707/PHASE9G6A_ACTIVE_TASK_LIFECYCLE_TRANSITION_INTERFACE_AUDIT.md`
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260707/PHASE9G6B_PASSIVE_SHARED_LIFECYCLE_TRANSITION_LOGGER_REPORT.md`

Lifecycle and assignment code:

- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_lifecycle.py`
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_state.py`
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_rl_interface.py`
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_wrapper.py`

Runtime and smoke paths:

- `scripts/environments/evaluate_assignment_rl_playback_diagnostics.py`
- `scripts/environments/evaluate_assignment_methods.py`
- `scripts/environments/test_assignment_lifecycle_transition_logger_smoke.py`
- `scripts/environments/test_assignment_failed_pair_memory_smoke.py`
- `scripts/environments/evaluate_assignment_methods.py`

## Files Created

- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_lifecycle_diagnostics.py`
- `scripts/environments/test_assignment_lifecycle_runtime_integration_smoke.py`
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260707/PHASE9G6C_PASSIVE_LIFECYCLE_RUNTIME_INTEGRATION_REPORT.md`
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260707/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G6C_PASSIVE_LIFECYCLE_RUNTIME_INTEGRATION_20260707.md`

## Files Updated

- `scripts/environments/evaluate_assignment_rl_playback_diagnostics.py`
- `scripts/environments/evaluate_assignment_methods.py`
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md`

No behavior modules such as `assignment_harl_wrapper.py`, `assignment_controller.py`, `scan_mobile_manipulator_env.py`, `assignment_state.py`, scenario YAML, HARL code, or solver behavior files were modified in this phase.

## Shared Adapter API

New module:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_lifecycle_diagnostics.py
```

Primary class:

```python
AssignmentLifecycleDiagnosticsAdapter(
    enabled: bool,
    num_envs: int,
    num_robots: int,
    num_tasks: int,
    device: str | torch.device = "cpu",
    method_name: str = "unknown",
    output_dir: Path | str | None = None,
    proposal_type: str | None = None,
)
```

Public methods:

```python
observe_pre_step(problem, assignment_proposal, episode_ids=None, method_metadata=None)
observe_post_step(
    pre_step_problem,
    assignment_proposal,
    post_step_problem,
    external_diagnostics=None,
    completed_by_robot_ids=None,
    done_env_ids=None,
    episode_ids=None,
    method_metadata=None,
)
reset_envs(env_ids=None, episode_ids=None)
snapshot()
finalize()
```

Shared helper functions:

```python
normalize_assignment_lifecycle_proposal(...)
make_assignment_lifecycle_post_problem(...)
build_assignment_lifecycle_external_diagnostics(...)
```

The adapter owns `AssignmentLifecycleTransitionLogger`, drains lifecycle events into output files, accumulates bounded summary counters, and resets selected env ids after post-step events have been recorded.

The adapter does not return or produce effective assignments. It returns diagnostics only.

## Default-Off Behavior

Both runtime scripts now expose default-off diagnostics flags:

```text
--log_assignment_lifecycle
--assignment_lifecycle_output_dir
```

Default behavior:

- `--log_assignment_lifecycle` is false.
- No lifecycle logger state is constructed in the adapter.
- No lifecycle output directory or files are created.
- Existing assignment history and diagnostic output schemas remain unchanged.
- Assignments, actions, masks, observations, rewards, controller commands, env dynamics, HARL behavior, and solver decisions are unchanged.

When enabled, the passive logger records diagnostics only:

- `assignment_lifecycle_events.jsonl`
- `assignment_lifecycle_summary.json`

Every event and summary includes `behavior_changed = false`.

## Method-Agnostic Proposal Boundary

The adapter consumes only standardized decoded proposals:

```text
assignment_proposal [num_envs, num_robots]
0..N-1 = target id
-1 = decoded noop / no proposed target
```

The adapter does not know about HARL action ids. Raw discrete noop id `N` is rejected by proposal validation; callers must pass decoded `-1`.

Future method boundary:

```text
method-specific output
  -> method adapter / decoder
  -> standardized assignment_proposal [E, M]
  -> shared lifecycle diagnostics adapter
  -> AssignmentLifecycleTransitionLogger
  -> lifecycle events + summary
```

This boundary supports current RL, random, nearest, greedy, and future centralized, decentralized, auction, optimization, graph, Transformer, queue, matching, score-matrix, or market-based allocation methods, provided each method has an adapter that emits the standardized proposal tensor.

Method metadata is accepted as optional diagnostics metadata and does not change transition reconstruction.

## RL Integration Point

File:

```text
scripts/environments/evaluate_assignment_rl_playback_diagnostics.py
```

Integration point:

1. Decode the existing policy action into `assignment` as before.
2. Call `lifecycle_adapter.observe_pre_step(problem=pre_problem, assignment_proposal=assignment, ...)` before `wrapper.step(action)`.
3. Execute the existing `wrapper.step(action)` unchanged.
4. Build a post-step problem snapshot with the post-step coverage mask captured before reset-sensitive state can obscure completion evidence.
5. Forward existing wrapper diagnostics through `build_assignment_lifecycle_external_diagnostics(...)` when present.
6. Call `observe_post_step(...)` with post-step problem and done env ids.
7. Finalize lifecycle output only when diagnostics flag is enabled.

No checkpoint loading, policy action, action decoding, env action conversion, playback stopping behavior, assignment history fields, reward diagnostics, or coverage diagnostics were changed.

## Comparison-Method Integration Point

File:

```text
scripts/environments/evaluate_assignment_methods.py
```

Integration point:

1. Use each method's existing assignment tensor as the standardized proposal.
2. Call the shared adapter before the existing env step.
3. Step the environment with the same assignment as before.
4. Use the post-step problem and captured covered mask for lifecycle post-step observation.
5. Reset only the done env ids after final post-step lifecycle events are recorded.
6. Write the same event and summary schema as the RL path.

The method name is passed as metadata and may be `random`, `nearest`, `greedy`, or any future method name. No hardcoded lifecycle method whitelist was added.

Solver output, solver cadence, solver assignments, env actions, and existing evaluation metrics are unchanged.

## Step Alignment Contract

The adapter enforces a pre/post pairing for each decision row:

```text
pre_problem_t
assignment_proposal_t
env.step(action derived from assignment_proposal_t)
post_problem_t
external_diagnostics_t
done_env_ids_t
reset selected env ids only after post-step events
```

The integration smoke test checks that completion events are recorded before reset events for a done env.

The adapter stores cloned pre-step core tensors internally so later env-side mutation or reset does not corrupt the pending pre-step snapshot used for lifecycle reconstruction. The adapter validates the post-step call order and proposal shape against the pending pre-step call.

## Done / Reset Ordering

Reset behavior is handled by the adapter:

- `done_env_ids` are passed to `observe_post_step`.
- The logger records post-step transition events first.
- The adapter then calls logger reset for only the done env ids.
- Reset events identify the affected env ids.
- Continuing envs retain their passive proxy state.

This preserves the ordering needed to record final completion, failure, conflict, or release proxy events before clearing proxy state.

## Event Output Schema

Event file:

```text
assignment_lifecycle_events.jsonl
```

Schema version:

```text
phase9g6c_assignment_lifecycle_diagnostics_v1
```

Each event row contains:

```text
schema_version
method_name
proposal_type
episode_id
env_id
step
event_type
robot_id
target_id
previous_target_id
new_target_id
attempt_age_proxy
failure_reason
release_reason
claiming_robot_ids
claiming_costs
would_be_winner_robot_id
would_be_loser_robot_ids
arbitration_rule
fallback_reason
behavior_changed
```

Missing scalar fields are serialized as `null`. Missing list fields are serialized as empty lists. `behavior_changed` is always false.

## Summary Output Schema

Summary file:

```text
assignment_lifecycle_summary.json
```

Required summary fields implemented:

```text
schema_version
enabled
method_name
num_envs
num_robots
num_tasks
total_steps_observed
total_events
attempt_started_proxy_count
attempt_continued_proxy_count
noop_idle_proxy_count
noop_after_active_ambiguous_count
switch_request_proxy_count
target_completed_proxy_count
target_completed_by_teammate_proxy_count
active_target_became_covered_proxy_count
budget_failure_proxy_count
release_proxy_count
exact_claim_conflict_proxy_count
unavailable_target_proposal_proxy_count
invalid_assignment_proposal_proxy_count
hypothetical_conflict_loser_count
reset_proxy_count
attempt_age_proxy_min
attempt_age_proxy_mean
attempt_age_proxy_max
behavior_changed
```

The summary also records output paths when files are written.

## Integration Smoke Matrix

New smoke test:

```text
scripts/environments/test_assignment_lifecycle_runtime_integration_smoke.py
```

This is a pure Python/Torch fake integration test. It does not launch Isaac Sim, run playback, run comparison evaluation episodes, or train.

Coverage:

| Case | Result |
|---|---|
| Disabled identity: no logger, no files, proposal unchanged | PASS |
| Correct pre/post ordering and completion-before-reset | PASS |
| Subset done/reset for E=3 with envs 0 and 2 reset only | PASS |
| RL proposal normalization: decoded noop `-1` accepted, raw noop id `N` rejected | PASS |
| Comparison/future method proposal metadata equivalence | PASS |
| Unified output schema across RL, baseline, and future method labels | PASS |
| Event draining and idempotent finalize | PASS |
| Input non-mutation | PASS |
| Exact conflict remains passive with hypothetical winner/losers only | PASS |
| Output file parsing for JSONL and JSON summary | PASS |
| Arbitrary method name `new_sota_method_v1` accepted | PASS |
| Variable M/N integration | PASS |

## Variable M/N Results

The runtime integration smoke covered:

```text
E=1, M=1, N=3
E=2, M=3, N=5
E=2, M=4, N=8
```

For all cases:

- State tensor shapes matched the configured env/robot/task counts.
- Standardized proposals were accepted.
- Lifecycle events were written using the same schema.
- No fixed `M=3` or `N=50` assumption was introduced.

## Method-Agnostic Schema Equivalence

The smoke ran identical proposal/problem sequences using method labels:

```text
happo
random
nearest
greedy
future_sota_placeholder
new_sota_method_v1
```

Result:

- Lifecycle transition types and counts were identical for identical standardized proposals.
- Event and summary schemas were identical.
- Method name differed only as metadata.
- No hardcoded method whitelist rejected future method names.

## Input Non-Mutation Results

The integration smoke verifies that the adapter does not mutate:

- Pre-step `AssignmentProblem` tensors.
- Post-step `AssignmentProblem` tensors.
- Assignment proposal tensors.
- Available masks.
- Cost matrices.
- Coverage tensors.
- External diagnostics dictionaries.
- Done env id tensors.
- Method metadata dictionaries.

## Exact Conflict Passive Diagnostics

Exact same-target conflict diagnostics remain passive.

When two or more robots propose the same valid uncovered target:

- The logger emits `exact_claim_conflict_proxy`.
- The event includes claiming robot ids, costs when available, hypothetical winner, hypothetical losers, arbitration rule, and fallback reason if applicable.
- Hypothetical arbitration uses lowest path cost, with robot-id tie-breaker for equal or unavailable costs.
- The standardized proposal tensor remains unchanged.
- No masks are changed.
- No effective assignment is returned.
- `behavior_changed` remains false.

## Behavior-Preservation Results

Confirmed by smoke tests and code inspection:

- Assignment proposal before adapter equals assignment proposal after adapter.
- Available mask before adapter equals available mask after adapter.
- Adapter does not invoke controller or env functions in smoke tests.
- Adapter does not produce effective assignments.
- Adapter does not enforce ownership.
- Adapter does not latch active targets.
- Adapter does not apply hypothetical arbitration.
- Adapter does not modify actions, masks, observations, rewards, controller commands, env dynamics, HARL behavior, or solver behavior.
- `behavior_changed` is false in every event and summary.

## Difference From Phase 9G-1

Phase 9G-1:

- Offline reconstruction from completed `assignment_history.csv` files.
- Can use full histories and future rows.
- Analysis-only and file-oriented.

Phase 9G-6C:

- Online passive integration over current runtime pre/post step snapshots.
- Uses only the current standardized proposal and current pre/post problem pair.
- Maintains incremental proxy state through `AssignmentLifecycleTransitionLogger`.
- Provides a shared method-agnostic adapter for RL, current baselines, and future comparison methods.
- Still diagnostics-only and behavior-neutral.

## Validation Commands And Results

Commands run:

```powershell
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_lifecycle.py
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_lifecycle_diagnostics.py
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/test_assignment_lifecycle_transition_logger_smoke.py
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/test_assignment_lifecycle_runtime_integration_smoke.py
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/evaluate_assignment_rl_playback_diagnostics.py
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/evaluate_assignment_methods.py
conda run -p C:\isaacenvs\isaac45_harl python scripts/environments/test_assignment_lifecycle_transition_logger_smoke.py
conda run -p C:\isaacenvs\isaac45_harl python scripts/environments/test_assignment_lifecycle_runtime_integration_smoke.py
git diff --check
git status --short --untracked-files=all
```

Results:

```text
py_compile assignment_lifecycle.py: PASS
py_compile assignment_lifecycle_diagnostics.py: PASS
py_compile test_assignment_lifecycle_transition_logger_smoke.py: PASS
py_compile test_assignment_lifecycle_runtime_integration_smoke.py: PASS
py_compile evaluate_assignment_rl_playback_diagnostics.py: PASS
py_compile evaluate_assignment_methods.py: PASS
test_assignment_lifecycle_transition_logger_smoke.py: PASS
test_assignment_lifecycle_runtime_integration_smoke.py: PASS
git diff --check: PASS
git status --short --untracked-files=all: completed
```

## Explicit Non-Changes

Phase 9G-6C did not change:

- Assignment proposals chosen by any method.
- Decoded assignments.
- Env actions.
- Available actions.
- Available masks.
- Actor observations.
- Shared/critic observations.
- Reward formulas or reward scales.
- Controller commands.
- Environment dynamics.
- Task completion behavior.
- HARL code or behavior.
- Random, nearest, greedy, or other solver decisions.
- Scenario YAML.
- Cooldown behavior.
- Redirect guardrail behavior.
- Failed-pair memory behavior.

No formal playback was run. No comparison-method evaluation episode was run. No simulation rollout was run. No training was run.

## Recommendation

Recommended next phase:

```text
Phase 9G-6D: bounded runtime validation of passive lifecycle diagnostics.
```

Suggested boundary:

- Run one RL playback diagnostic run with `--log_assignment_lifecycle`.
- Run one or more current comparison-method diagnostic runs with `--log_assignment_lifecycle`.
- Verify lifecycle event and summary files are populated.
- Compare schema consistency across RL, current baselines, and a placeholder/future method label if available.
- Confirm diagnostics remain behavior-neutral.
- Do not train.
- Do not implement action latching, ownership enforcement, mask changes, observation changes, or Contract C behavior.

After Phase 9G-6D passes, perform a Phase 9G-6 commit-readiness review covering 9G-6A through 9G-6D before the user manually commits the complete block.

