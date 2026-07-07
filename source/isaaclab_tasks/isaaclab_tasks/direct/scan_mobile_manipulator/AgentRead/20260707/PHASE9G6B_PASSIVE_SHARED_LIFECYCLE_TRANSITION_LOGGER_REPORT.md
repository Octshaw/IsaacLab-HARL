# Phase 9G-6B Passive Shared Lifecycle Transition Logger Report

Date: 2026-07-07

## Scope And Boundary

Phase 9G-6B implemented a standalone passive lifecycle transition logger and fake-sequence smoke test.

This phase did not integrate the logger into the RL wrapper, baseline evaluation, playback diagnostics, env, controller, HARL, rewards, observations, available-action masks, action decoding, action semantics, scenario YAML, cooldown, redirect guardrail, or failed-pair memory behavior.

No training, playback, simulation rollout, or broad evaluation was run. No commit was made.

## Files Inspected

Read first:

- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/AGENTS.md`
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md`
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260707/PHASE9G6A_ACTIVE_TASK_LIFECYCLE_TRANSITION_INTERFACE_AUDIT.md`
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260707/PHASE9G5_FAILED_PAIR_MEMORY_DESIGN_DECISION_REVIEW.md`

Interface/source context:

- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_state.py`
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_rl_interface.py`
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_wrapper.py`
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_controller.py`
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py`
- `scripts/environments/analyze_phase9g1_lifecycle_reconstruction.py`
- `scripts/environments/test_assignment_harl_wrapper_smoke.py`
- `scripts/environments/test_assignment_failed_pair_memory_smoke.py`
- `scripts/environments/evaluate_assignment_methods.py`

## Files Created Or Updated

Created:

- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_lifecycle.py`
- `scripts/environments/test_assignment_lifecycle_transition_logger_smoke.py`
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260707/PHASE9G6B_PASSIVE_SHARED_LIFECYCLE_TRANSITION_LOGGER_REPORT.md`
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260707/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G6B_PASSIVE_SHARED_LIFECYCLE_TRANSITION_LOGGER_20260707.md`

Updated:

- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md`

No existing Python behavior file was modified.

## Public Logger API

Module:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_lifecycle.py
```

Primary class:

```python
AssignmentLifecycleTransitionLogger(
    num_envs=E,
    num_robots=M,
    num_tasks=N,
    device=device,
    strict_proposals=True,
    retain_events=True,
)
```

Public methods:

```python
reset(env_ids=None, emit_events=True)

observe_pre_step(
    problem=pre_step_problem,
    assignment_proposal=assignment_proposal,
    method_metadata=None,
)

observe_post_step(
    pre_step_problem=pre_step_problem,
    assignment_proposal=assignment_proposal,
    post_step_problem=post_step_problem,
    external_diagnostics=None,
    method_metadata=None,
)

update(
    pre_step_problem=pre_step_problem,
    assignment_proposal=assignment_proposal,
    post_step_problem=post_step_problem,
    external_diagnostics=None,
    method_metadata=None,
)

snapshot()
pop_events()
peek_events()
clone_problem_inputs(problem)
```

The API separates pre-step proposal observation, post-step completion/failure observation, state snapshot, event retrieval, and reset. `update()` is a convenience wrapper around pre/post observation.

## Method-Agnostic Proposal Boundary

The standardized current-step proposal is:

```text
assignment_proposal: torch.Tensor
shape: [num_envs, num_robots]
dtype: integer-compatible, converted internally to torch.long clone
values:
  0..N-1 = proposed target id
  -1 = decoded noop / no proposed target
```

The logger does not require the proposal to originate from HARL or a discrete RL policy. It can accept standardized proposals produced by current or future method adapters.

Future adapter boundary:

```text
method-specific output
        ->
method adapter
        ->
standardized assignment_proposal [E, M]
        ->
passive/shared lifecycle logger
```

Supported future method forms by adapter, not by direct logger coupling:

- one target per robot;
- global matching;
- score/cost matrix;
- task priority vector;
- per-robot task queue;
- partial assignment;
- auction result;
- optimization result;
- graph, Transformer, neural, centralized, or decentralized allocation output.

Optional metadata accepted:

```text
method_name
proposal_type
proposal_score
proposal_cost
proposal_confidence
external_plan_id
```

Only `method_name` is currently copied into event logs. Metadata never changes transition reconstruction.

## State Tensor Shapes And Dtypes

For `E = num_envs`, `M = num_robots`, `N = num_tasks`:

| Field | Shape | Dtype | Notes |
| --- | --- | --- | --- |
| `step` | `[E]` | `torch.long` | Passive logger row counter. |
| `robot_state_proxy` | `[E, M]` | `torch.long` | Proxy robot state only. |
| `active_target_proxy` | `[E, M]` | `torch.long` | `-1` means no active proxy target. |
| `task_owner_proxy` | `[E, N]` | `torch.long` | `-1` means no proxy owner. |
| `task_state_proxy` | `[E, N]` | `torch.long` | Completion derives from `viewpoints_covered`. |
| `pair_state_proxy` | `[E, M, N]` | `torch.long` | Pair proxy state only. |
| `attempt_start_step_proxy` | `[E, M]` | `torch.long` | `-1` means no active proxy attempt. |
| `attempt_age_proxy` | `[E, M]` | `torch.long` | Incremental proxy age. |
| `last_proposal` | `[E, M]` | `torch.long` | `-2` means no proposal seen yet. |

The snapshot also includes:

- `event_count`;
- `last_event_type`;
- `last_transition_reason`;
- proxy state name maps.

## Proxy-State Semantics

Robot proxy states:

```text
ROBOT_IDLE_PROXY
ROBOT_ACTIVE_PROXY
ROBOT_RELEASED_PROXY
ROBOT_RESET_PROXY
```

Task proxy states:

```text
TASK_OPEN_PROXY
TASK_CLAIMED_PROXY
TASK_COMPLETED
```

Pair proxy states:

```text
PAIR_NONE
PAIR_ACTIVE_PROXY
PAIR_COMPLETED
PAIR_FAILED_BUDGET_PROXY
PAIR_RELEASED_PROXY
PAIR_TIMEOUT_PROXY
```

`TASK_COMPLETED` is not labeled as proxy because it is derived directly from the env-owned `viewpoints_covered` signal. Other inferred states remain explicitly proxy states.

Proxy updates are reconstruction state only. They do not change assignments, masks, actions, controller commands, env dynamics, rewards, observations, HARL behavior, or baseline decisions.

## Event Schema

Events are emitted as `AssignmentLifecycleEvent` dataclasses and returned from `pop_events()` / `peek_events()` as dictionaries.

Core fields:

```text
event_type
env_id
step
robot_id, when applicable
target_id, when applicable
method_name, when supplied
details, flattened into the output dictionary
```

Implemented diagnostic events:

```text
attempt_started_proxy
attempt_continued_proxy
noop_idle_proxy
noop_after_active_ambiguous
target_completed_proxy
target_completed_by_teammate_proxy
active_target_became_covered_proxy
budget_failure_proxy
release_proxy
switch_request_proxy
exact_claim_conflict_proxy
reset_proxy
unavailable_target_proposal_proxy
invalid_assignment_proposal_proxy, only when strict_proposals=False
```

Strict proposal validation is enabled by default. Out-of-range proposal ids raise `ValueError` rather than being silently clamped.

## Transition Reconstruction Rules

Pre-step proposal observation:

- no previous active proxy target and target proposal available/uncovered -> `attempt_started_proxy`;
- previous active proxy target equals current target proposal -> `attempt_continued_proxy`;
- idle plus `-1` proposal -> `noop_idle_proxy`;
- active proxy target plus `-1` proposal -> `noop_after_active_ambiguous`;
- active proxy target A plus proposed target B -> `switch_request_proxy`;
- two or more robots propose the same valid uncovered target -> `exact_claim_conflict_proxy`.

Noop-after-active is intentionally not labeled as continuation. Current behavior sends no target-directed command. Future Contract C could reinterpret noop as continue, but Phase 9G-6B does not apply that semantic.

Post-step observation:

- new coverage from `viewpoints_covered` -> `target_completed_proxy`;
- if supplied `completed_by_robot_ids` identifies a different completing robot -> `target_completed_by_teammate_proxy`;
- otherwise completion by another robot is not fabricated;
- supplied budget diagnostics -> `budget_failure_proxy` followed by `release_proxy`;
- no new failure criteria are invented.

## Exact-Conflict Hypothetical Arbitration Diagnostics

When multiple robots in the same env propose the same valid uncovered target, the logger emits:

```text
exact_claim_conflict_proxy
```

Event fields include:

```text
claiming_robot_ids
claiming_costs
would_be_winner_robot_id
would_be_loser_robot_ids
arbitration_rule
fallback_reason
behavior_changed = False
```

Hypothetical arbitration rule:

```text
lowest_path_cost_robot_id_tiebreak
```

If costs are unavailable or non-finite, the fallback is deterministic robot-id ordering and the fallback reason is recorded. The logger does not mask losers, modify proposals, enforce ownership, or produce effective assignments.

## Fake-Sequence Smoke Test Matrix

Smoke test:

```text
scripts/environments/test_assignment_lifecycle_transition_logger_smoke.py
```

Covered sequences:

| Sequence | Coverage |
| --- | --- |
| A normal attempt | `attempt_started_proxy`, `attempt_continued_proxy`, `target_completed_proxy`; active target clears after completion. |
| B noop idle | repeated `noop_idle_proxy`; no active target created. |
| C noop after active | `noop_after_active_ambiguous`; no controller continuation claim. |
| D switch request | `switch_request_proxy`; previous and new target ids logged. |
| E budget failure and release | supplied budget trigger logs `budget_failure_proxy` and `release_proxy`; inputs unchanged. |
| F exact target conflict | lowest-cost winner, equal-cost robot-id tie-break, and cost-unavailable fallback tested. |
| G teammate completion | supplied completing robot id logs `target_completed_by_teammate_proxy`. |
| H reset | subset and full reset clear proxy state deterministically. |
| I method-agnostic equivalence | identical standardized proposal sequence tested for `happo`, `random`, `nearest`, `greedy`, `future_sota_placeholder`. |
| J input non-mutation | pre/post problem tensors, proposal tensor, and external diagnostics remain unchanged. |

Additional variable-shape and validation coverage:

```text
M=1, N=3
M=3, N=5
M=4, N=8
multiple envs
covered target diagnostic
invalid proposals raise clear ValueError
```

## Smoke Test Result

Command:

```powershell
conda run -p C:\isaacenvs\isaac45_harl python scripts/environments/test_assignment_lifecycle_transition_logger_smoke.py
```

Result:

```text
passed
sequence_count = 11
behavior_changed = false
assignments_modified = false
masks_modified = false
observations_modified = false
controller_or_env_invoked = false
training_or_playback_invoked = false
```

Method compatibility result:

```text
happo, random, nearest, greedy, and future_sota_placeholder produced identical transition types and tensor snapshots for the same standardized proposal sequence, excluding metadata.
```

Exact-conflict result:

```text
lowest-cost case: robot 1 won over robot 0
equal-cost tie: robot 0 won by robot-id tie-break
cost-unavailable fallback: robot 0 won with fallback_reason = cost_unavailable_or_non_finite
proposal_not_mutated = true
```

Input non-mutation result:

```text
problem_not_mutated = true
proposal_not_mutated = true
external_diagnostics_not_mutated = true
```

## Difference From Phase 9G-1 Analyzer

Phase 9G-1:

```text
offline reconstruction from completed assignment_history.csv
can use future rows and full episode history
analysis-only
CSV-column dependent
```

Phase 9G-6B:

```text
online passive transition reconstruction
uses only current pre/post assignment problem snapshots and current assignment proposal
maintains incremental proxy state
method-agnostic standardized proposal interface
future lifecycle manager interface prototype
pure fake-sequence tested
```

The 9G-6B logger does not duplicate the full 9G-1 analyzer. It turns the relevant transition concepts into a small online component that can later be attached to RL and non-RL allocation paths.

## Behavior Integration Confirmation

No integration occurred in Phase 9G-6B.

Not modified:

```text
assignment_harl_wrapper.py
assignment_rl_interface.py
assignment_controller.py
scan_mobile_manipulator_env.py
assignment_state.py
evaluate_assignment_methods.py
evaluate_assignment_rl_playback_diagnostics.py
baseline solver files
scenario YAML
HARL code
installed site-packages
```

The logger is not imported by any behavior path. It does not produce effective assignments and cannot affect masks, observations, rewards, controller commands, env dynamics, training, playback, or baseline decisions.

## Validation Commands And Results

```powershell
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_lifecycle.py
```

Result: passed.

```powershell
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/test_assignment_lifecycle_transition_logger_smoke.py
```

Result: passed.

```powershell
conda run -p C:\isaacenvs\isaac45_harl python scripts/environments/test_assignment_lifecycle_transition_logger_smoke.py
```

Result: passed.

```powershell
git diff --check
```

Result: passed with an LF-to-CRLF working-copy warning for `TASK_PROGRESS.md` only.

```powershell
git status --short --untracked-files=all
```

Result: completed. The worktree contains Phase 9G-6A documentation changes plus the new Phase 9G-6B logger, smoke test, report, archive, and `TASK_PROGRESS.md` update.

## Recommended Next Smallest Phase

Recommended Phase 9G-6C:

```text
Attach the passive logger to RL playback diagnostics and current comparison-method evaluation as diagnostics only.
No behavior change.
No action latching.
No effective assignment resolver.
No mask changes.
No observation changes.
No reward changes.
No controller/env changes.
No training.
Playback only if explicitly authorized.
```

Alternative Phase 9G-6C if integration risk is considered too high:

```text
Expand the generic assignment proposal adapter contract without attaching it to runtime scripts.
```

Do not automatically implement action latching or Contract C. The next behavior-bearing design should wait until passive logs are attached and reviewed across RL and method-comparison paths.
