# Phase 9G-7B Shared Effective-Assignment Resolver Prototype Report

Date: 2026-07-08

## Scope

Phase 9G-7B implemented a pure shared effective-assignment resolver prototype with fake-sequence smoke tests only.

The resolver is disabled by default and is not integrated into any runtime path.

No playback, comparison-method evaluation, training, or short training smoke was run.

## Files Inspected

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/AGENTS.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260708/PHASE9G7A_EFFECTIVE_ASSIGNMENT_RESOLVER_ACTIVE_TARGET_LATCH_DESIGN_AUDIT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_lifecycle.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_lifecycle_diagnostics.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_state.py
scripts/environments/test_assignment_lifecycle_transition_logger_smoke.py
scripts/environments/test_assignment_lifecycle_runtime_integration_smoke.py
```

## Files Created

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_lifecycle_resolver.py
scripts/environments/test_assignment_lifecycle_resolver_smoke.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260708/PHASE9G7B_SHARED_EFFECTIVE_ASSIGNMENT_RESOLVER_PROTOTYPE_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260708/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G7B_SHARED_EFFECTIVE_ASSIGNMENT_RESOLVER_PROTOTYPE_20260708.md
```

## Files Updated

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
```

No runtime integration files were modified.

## Implementation Boundary

The new resolver module is standalone. It was not attached to:

```text
assignment_harl_wrapper.py
assignment_controller.py
scan_mobile_manipulator_env.py
evaluate_assignment_rl_playback_diagnostics.py
evaluate_assignment_methods.py
```

Therefore no wrapper, controller, environment, observation, mask, reward, HARL, baseline, solver, scenario YAML, cooldown, redirect guardrail, or failed-pair memory behavior changed.

## Resolver Public API

Class:

```python
AssignmentLifecycleResolver(
    num_envs: int,
    num_robots: int,
    num_tasks: int,
    device: str | torch.device = "cpu",
    enabled: bool = False,
    strict_proposals: bool = True,
)
```

Primary methods:

```python
resolve_pre_step(problem, assignment_proposal, method_metadata=None)
observe_post_step(
    pre_step_problem,
    assignment_proposal,
    effective_assignment,
    post_step_problem,
    external_diagnostics=None,
    done_env_ids=None,
    method_metadata=None,
)
snapshot()
pop_events()
peek_events()
reset(env_ids=None)
```

The resolver accepts standardized decoded proposals:

```text
assignment_proposal [E, M]
0..N-1 = target id
-1 = noop / no new target proposal
```

It does not know about raw HARL noop id `N`.

## State Tensors And Enums

Implemented persistent state:

| Field | Shape | Dtype | Sentinel / values |
|---|---:|---|---|
| `step` | `[E]` | `torch.long` | starts at `0` |
| `active_target_id` | `[E, M]` | `torch.long` | `-1 = none` |
| `robot_execution_state` | `[E, M]` | `torch.long` | `0 = IDLE`, `1 = EXECUTING` |
| `task_owner_robot_id` | `[E, N]` | `torch.long` | `-1 = unowned` |
| `attempt_start_step` | `[E, M]` | `torch.long` | `-1 = none` |
| `attempt_age` | `[E, M]` | `torch.long` | `0` while idle |
| `pair_state` | `[E, M, N]` | `torch.long` | `0 NONE`, `1 ACTIVE`, `2 COMPLETED`, `3 FAILED_BUDGET`, `4 RELEASED_BUDGET` |
| `last_release_reason` | `[E, M]` | `torch.long` | `-1 = none`, `1 = budget_failure` |
| `last_failure_reason` | `[E, M]` | `torch.long` | `-1 = none`, `1 = budget_failure` |

No persistent `RELEASED` robot state was added. Release is a transition/event; released robots return to `IDLE`.

## Disabled-Mode Identity Contract

When `enabled=False`, `resolve_pre_step()`:

```text
clones assignment_proposal to effective_assignment
does not interpret noop
does not validate proposal range semantics
does not arbitrate conflicts
does not reject switches
does not update active targets, owners, pair state, or attempt age
emits no events
returns behavior_changed = False
```

When disabled, `observe_post_step()` does not update lifecycle state and emits no events.

The smoke test verified that the full resolver snapshot is unchanged after disabled pre/post calls, including with proposal values outside enabled strict range.

## Enabled Contract C Rules

Implemented enabled pre-step rules:

| Current state | Proposal | Effective assignment | Result |
|---|---|---|---|
| idle | noop | noop | remain idle; `noop_idle` |
| idle | valid open target | target | claim target; owner created; `attempt_started` |
| executing | same target | active target | continue; `attempt_continued_same_target` |
| executing | noop | active target | continue under Contract C; `behavior_changed=True`; `attempt_continued_noop_contract_c` |
| executing | different target | active target | switch rejected; ownership unchanged; `behavior_changed=True`; `switch_rejected_executing` |

Noop is not release. Switching is rejected in the first prototype.

## Ownership Rules

Implemented invariants:

```text
at most one active target per robot
at most one owner per task
existing owner has priority over new claims
completion clears ownership
budget failure/release clears ownership for the failed active pair
one robot failure does not globally fail a target
same robot failed-pair reclaim is rejected until target completion or reset
teammates may claim released targets when open and feasible
```

## Arbitration Rules

Simultaneous new idle claims on the same unowned open target are resolved by:

```text
lowest finite path cost wins
lower robot id breaks exact cost ties
lower robot id fallback is used when costs are unavailable or non-finite
```

Losing robots remain idle and receive effective noop. The proposal tensor is never mutated.

Existing active ownership has priority over new claims and is not stolen by a lower-cost teammate proposal.

## Completion Behavior

Completion is detected only from newly covered `viewpoints_covered` in post-step snapshots.

For a completed target:

```text
target_completed event emitted
active owner/robot cleared when known from resolver ownership
robot becomes IDLE
task owner clears
attempt metadata clears
pair states for that target become COMPLETED, clearing failed/released pair states for the completed target
```

The resolver does not fabricate a completing robot if no owner/active association exists.

## Budget Failure / Release Behavior

Budget failure/release uses only supplied external diagnostics:

```text
external_diagnostics["budget_failure_pairs"]
external_diagnostics["budget_failure_mask"]
```

For a validated robot-target failure:

```text
budget_failure event emitted
release_budget_failure event emitted
active target clears when it matches
task owner clears when it matches
robot becomes IDLE
attempt metadata clears
pair state becomes RELEASED_BUDGET
last failure/release reasons record budget failure
```

The target remains open if not covered.

## Failed-Pair Persistence Behavior

The first prototype uses episode-persistent same-robot failed-pair rejection:

```text
budget-failed robot-target pair remains rejected until target completion or env reset
```

This is intentionally not a final retry policy. The smoke test includes the stranded-task limitation:

```text
robot 0 budget-fails target
target remains uncovered
teammates are infeasible
robot 0 retries
robot 0 is rejected and target remains unowned/open
```

This risk must be handled before runtime behavior integration, for example with explicit retry policy, timeout escalation, or observation-aware training design.

## Active Infeasibility Deferred Behavior

If an executing active target becomes infeasible in a later pre-step problem:

```text
effective assignment remains the active target
owner remains
active target remains latched
active_target_infeasible_deferred event emitted
```

The resolver does not release infeasible active targets in Phase 9G-7B. This is a deferred runtime-risk decision for a later phase.

## Event Schema

Events are dictionaries returned by `pop_events()` / `peek_events()`.

Implemented event types:

```text
attempt_started
attempt_continued_same_target
attempt_continued_noop_contract_c
noop_idle
switch_rejected_executing
exact_claim_conflict_resolved
claim_lost
owned_target_rejected
covered_target_rejected
failed_pair_reclaim_rejected
active_target_infeasible_deferred
target_completed
budget_failure
release_budget_failure
reset
```

Additional enabled rejection event:

```text
unavailable_target_rejected
```

Events include applicable fields such as:

```text
event_type
env_id
step
robot_id
target_id
previous_target_id
proposed_target_id
effective_target_id
owner_robot_id
claiming_robot_ids
claiming_costs
winner_robot_id
loser_robot_ids
reason
behavior_changed
method_name
```

Events are retained only until drained by `pop_events()`.

## Fake-Sequence Test Matrix

Smoke script:

```text
scripts/environments/test_assignment_lifecycle_resolver_smoke.py
```

Covered requirements:

| Requirement | Result |
|---|---|
| disabled absolute identity | passed |
| idle target claim | passed |
| idle noop | passed |
| same-target continuation | passed |
| noop-as-continue | passed |
| switch rejected | passed |
| completion release | passed |
| budget failure release | passed |
| failed-pair immediate reclaim rejected | passed |
| teammate claim after failed owner release | passed |
| failed-pair cleared on completion | passed |
| failed-pair cleared on reset | passed |
| exact conflict arbitration | passed |
| active owner priority | passed |
| covered target rejected | passed |
| active target infeasible deferred | passed |
| invalid proposal errors in enabled strict mode | passed |
| subset reset | passed |
| variable E/M/N | passed |
| method-agnostic metadata | passed |
| input non-mutation | passed |
| episode-persistent failed-pair limitation | passed and documented |

Variable shape coverage:

```text
E=1, M=1, N=3
E=2, M=3, N=5
E=2, M=4, N=8
```

Method labels tested:

```text
happo
random
nearest
greedy
future_sota_placeholder
```

## Input Non-Mutation Result

The smoke test verified the resolver does not mutate:

```text
AssignmentProblem-like problem tensors
assignment proposal
cost matrix
available/feasible masks
coverage tensor
external diagnostics
done env ids
method metadata
```

## Difference From Phase 9G-6 Passive Logger

Phase 9G-6 passive logger:

```text
observes proposals
reconstructs proxy state
never changes execution
does not produce effective assignments
```

Phase 9G-7B resolver:

```text
interprets proposals when enabled
owns behavior-driving prototype state
produces effective assignments
is still not integrated into runtime
```

The resolver does not import or reuse `AssignmentLifecycleTransitionLogger` as its state machine, avoiding two competing lifecycle state owners.

## Known Limitations

```text
No runtime integration.
No wrapper/controller/env behavior change.
No lifecycle-aware available_actions.
No lifecycle-aware observations.
No training-ready Markov state.
No explicit release action.
No switching while executing.
No TTL or retry policy for failed pairs.
Episode-persistent failed-pair rejection can strand tasks.
Active target infeasibility release is deferred.
No playback/evaluation identity evidence yet.
```

## Validation Commands And Results

```powershell
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_lifecycle_resolver.py
```

Result: passed.

```powershell
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/test_assignment_lifecycle_resolver_smoke.py
```

Result: passed.

```powershell
conda run -p C:\isaacenvs\isaac45_harl python scripts/environments/test_assignment_lifecycle_resolver_smoke.py --json
```

Result: passed, 20 grouped smoke cases covering the required fake-sequence matrix.

Final repository checks are recorded in `TASK_PROGRESS.md`.

```powershell
git diff --check
```

Result: passed with the existing LF-to-CRLF warning for `TASK_PROGRESS.md` only.

```powershell
git status --short --untracked-files=all
```

Result: completed. The worktree contains the expected modified `TASK_PROGRESS.md`, untracked 9G-7A documentation carry-over, and new 9G-7B resolver/test/report/archive files.

## Boundary Confirmation

No runtime integration occurred.

No playback or comparison-method evaluation ran.

No training or short training smoke ran.

No assignment wrapper, controller, environment, observation, mask, reward, HARL, solver, scenario YAML, cooldown, redirect guardrail, or failed-pair memory behavior changed.

No commit was made.

## Recommended Next Phase

Recommended next phase:

```text
Phase 9G-7C:
default-off resolver runtime integration design/readiness audit
```

Do not integrate the resolver automatically.

The next audit should decide:

```text
how wrapper and comparison paths share one resolver adapter
where post-step budget diagnostics enter
how resolver and passive logger coexist
how enabled/disabled identity will be validated
how active-target infeasibility is handled
how stranded failed-pair tasks are detected
whether observation changes remain deferred
```

Training remains prohibited until lifecycle behavior-driving state is represented in observations.
