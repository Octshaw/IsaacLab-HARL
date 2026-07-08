# Phase 9G-7C Default-Off Resolver Runtime Integration Design Readiness Audit

Date: 2026-07-08

## Scope

Phase 9G-7C is a documentation-only design/readiness audit for integrating the standalone `AssignmentLifecycleResolver` into real RL playback and comparison-method runtime paths in a later phase.

No Python source files were modified.

No runtime integration occurred.

No playback, comparison-method evaluation, training, or short training smoke was run.

No commit was made.

## Files Inspected

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/AGENTS.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260708/PHASE9G7A_EFFECTIVE_ASSIGNMENT_RESOLVER_ACTIVE_TARGET_LATCH_DESIGN_AUDIT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260708/PHASE9G7B_SHARED_EFFECTIVE_ASSIGNMENT_RESOLVER_PROTOTYPE_REPORT.md
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
scripts/environments/analyze_phase9g6d_lifecycle_runtime_validation.py
```

## Files Created

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260708/PHASE9G7C_DEFAULT_OFF_RESOLVER_RUNTIME_INTEGRATION_DESIGN_READINESS_AUDIT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260708/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G7C_RESOLVER_RUNTIME_INTEGRATION_DESIGN_20260708.md
```

## Files Updated

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
```

## Current Runtime Boundary Findings

### RL / HAPPO Path

`AssignmentHarlWrapper.step()` currently performs:

```text
pre_step_problem = env.get_assignment_problem()
pre_step_available_actions = _build_available_actions(pre_step_problem)
assignment_proposal = decode_actions(discrete_actions)
env_actions = assignment_to_env_actions(assignment_proposal)
env.step(env_actions)
post_step_problem = env.get_assignment_problem()
_update_assignment_diagnostics(assignment=assignment_proposal, ...)
_compute_assignment_reward_decomposition(assignment=assignment_proposal, ...)
_augment_info(...)
reset assignment diagnostics for done envs
build next available_actions
```

This is the only RL point where a behavior-changing resolver can be inserted without becoming playback-only.

### Comparison-Method Path

`evaluate_assignment_methods.py` currently performs:

```text
problem = get_assignment_problem()
assignment_proposal = solver.solve(problem)
actions = viewpoint_assignment_to_actions(unwrapped, assignment_proposal)
env.step(actions)
post-step diagnostics and optional passive lifecycle logging
done/manual reset handling
```

Random, nearest, greedy, and future method adapters must pass through the same proposal/effective boundary.

### Controller Conversion

`viewpoint_assignment_to_actions()` accepts `[E, M]` assignment tensors. Invalid, covered, infeasible, or noop entries become zero target-directed actions through the controller validity mask.

This is important for active-target infeasibility: if the resolver keeps returning an infeasible active target, the controller may emit zero action for that robot.

### Budget Signal Timing

Wrapper budget-trigger diagnostics are computed after `env.step()` inside `_update_assignment_diagnostics()` / `_update_assignment_cooldown()`.

The current budget trigger uses the `assignment` tensor supplied to wrapper diagnostics. With the resolver enabled, that tensor must be the executed `effective_assignment` or be explicitly transformed before being passed into `resolver.observe_post_step()`.

Required invariant:

```text
budget failure releases the currently active effective robot-target pair,
not merely the raw proposal pair.
```

## Architecture Matrix

| Architecture | Method comparability | Future training reuse | Future SOTA compatibility | Single source of truth | Default-off identity safety | Reset handling | Diagnostic clarity | Implementation complexity | Testability | Decision |
|---|---|---|---|---|---|---|---|---|---|---|
| A: resolver only inside RL wrapper | Weak for baselines | Strong for RL | Weak | One RL source only | Good for RL | Good in wrapper | Fragmented | Medium | Medium | No |
| B: duplicated resolver integration in RL and comparison scripts | Medium | Weak; playback/eval only | Medium | Risk of divergence | Risky | Duplicated | Confusing | Medium-high | Medium | No |
| C: shared runtime adapter used by wrapper and comparison paths | Strong | Strong if wrapper uses it | Strong | One resolver adapter contract | Strong when disabled | Shared API, path-local state | Strong | Medium | Strong | Selected |
| D: env-owned resolver integration | Strong eventually | Strong eventually | Strong | Highest eventual clarity | Riskier first step | Natural env reset | Strong | High | Harder first step | Defer |

Selected architecture:

```text
Architecture C:
one shared resolver runtime adapter used by AssignmentHARLWrapper and comparison-method evaluation paths.
```

The adapter should be introduced as:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_lifecycle_resolver_runtime.py
```

Alternative acceptable name:

```text
assignment_lifecycle_runtime.py
```

The selected name should make clear this is the behavior resolver runtime adapter, not the passive proxy diagnostics adapter.

## Shared Runtime Adapter Responsibility

The future adapter should own:

```text
resolver construction
enabled/disabled configuration
pre-step proposal resolution
post-step lifecycle observation
proposal/effective diagnostics
resolver event draining
subset/full reset coordination
resolver output serialization when logging is enabled
diagnostic-only stranded/infeasible counters
```

The adapter must not own:

```text
policy inference
solver decisions
continuous controller behavior
env physics
task completion truth
reward formulas
available action masks
observations
```

## Selected RL Integration Point

The resolver behavior must live inside `AssignmentHarlWrapper.step()` through the shared adapter.

Selected order:

```text
raw policy action
  -> decode_actions()
  -> assignment_proposal [E, M]
  -> resolver adapter resolve_pre_step()
  -> effective_assignment [E, M]
  -> assignment_to_env_actions(effective_assignment)
  -> env.step()
  -> wrapper diagnostics/reward using effective_assignment for executed-action semantics
  -> resolver adapter observe_post_step()
  -> done-env resolver reset after final post-step events
```

Rationale:

```text
Playback-only integration would create behavior that training does not use.
Wrapper integration allows future training and playback to share the same semantics.
The shared adapter prevents the wrapper from owning a one-off lifecycle implementation.
```

Default-off identity requirement:

```text
when resolver is disabled, effective_assignment == assignment_proposal,
no resolver state accumulates,
no resolver files are written unless logging is explicitly enabled,
existing checkpoint playback remains identical.
```

Diagnostics requirement:

```text
both assignment_proposal and effective_assignment must be exposed when resolver logging is enabled.
```

## Selected Comparison-Method Integration Point

The comparison-method path should call the same shared runtime adapter immediately after method output and before controller conversion:

```text
solver/method output
  -> assignment_proposal [E, M]
  -> resolver adapter resolve_pre_step()
  -> effective_assignment [E, M]
  -> viewpoint_assignment_to_actions(unwrapped, effective_assignment)
  -> env.step()
  -> resolver adapter observe_post_step()
```

This must be generic over method names. Do not hardcode a random/nearest/greedy whitelist.

Each method run must get:

```text
a fresh resolver adapter instance
a fresh resolver state
a method-specific resolver output directory
no shared resolver state across methods
```

Future SOTA adapters must convert their native output into the same standardized `assignment_proposal [E, M]` boundary.

## Complete Pre/Post-Step Ordering Contract

For decision row `t`:

```text
1. Capture pre_problem_t from env.get_assignment_problem().
2. Decode or adapt method output to assignment_proposal_t [E, M].
3. Clone or retain immutable reference to pre_problem_t for resolver post-step consistency.
4. Capture active_target_before and task_owner_before from resolver snapshot.
5. Call resolver.resolve_pre_step(pre_problem_t, assignment_proposal_t).
6. Record effective_assignment_t from resolver pre-step result.
7. Convert effective_assignment_t to env actions.
8. Execute env.step(env_actions_t).
9. Capture post_problem_t, preserving pre-reset covered masks for done envs.
10. Update existing wrapper/runtime diagnostics from effective_assignment_t where those diagnostics describe executed behavior.
11. Build budget_failure_pairs from post-step diagnostics using effective_assignment_t.
12. Call resolver.observe_post_step(pre_problem_t, assignment_proposal_t, effective_assignment_t, post_problem_t, diagnostics, done_env_ids_t).
13. Drain resolver events and write resolver diagnostics.
14. Only after post-step resolver events are recorded, reset done env ids in resolver and runtime buffers.
15. Capture active_target_after and task_owner_after.
```

This ordering prevents:

```text
off-by-one budget release
completion-after-reset loss
proposal/effective mismatch
wrong episode ids
lost final transition evidence
```

## Budget Diagnostic Handoff

Current sources:

```text
assignment_cooldown.budget_last_triggered_by_budget [E, M]
assignment_cooldown.budget_trigger_count
assignment_failed_pair_memory.last_trigger_robot_ids / target_ids / reason
wrapper._last_budget_triggered_by_budget
wrapper._last_budget_attempt_steps_for_selected_pair
wrapper._last_budget_ratio_for_selected_pair
```

Selected Phase 9G-7D handoff:

```text
construct resolver budget_failure_pairs after wrapper cooldown diagnostics update;
for each env/robot with budget_last_triggered_by_budget=True,
use effective_assignment[env, robot] as target_id;
ignore raw proposal target for release semantics;
include step, env_id, robot_id, target_id, reason="budget_trigger".
```

If the failed-pair-memory diagnostic provides a target id and resolver is enabled, it must be treated as secondary metadata only unless it matches the effective pair. The resolver must not release a raw proposal target that was rejected or converted to active-target continuation.

## Proposal Versus Effective Assignment Logging Schema

Phase 9G-7D should add a shared resolver runtime record with at least:

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

Recommended storage:

| Field group | Destination |
|---|---|
| Full resolver events | `assignment_lifecycle_resolver_events.jsonl` |
| Resolver summary counts | `assignment_lifecycle_resolver_summary.json` |
| Proposal/effective row diagnostics | resolver JSONL, optionally resolver row CSV |
| Existing assignment_history proposal columns | keep method proposal meaning |
| Controller input assignment | add explicit effective/controller fields when resolver logging is enabled |
| Passive proxy diagnostics | keep existing passive files separate |

Do not silently replace existing assignment-history assignment fields with effective assignments.

For enabled resolver runs, method output and controller input must be distinguishable:

```text
assignment_proposal_target_id
effective_assignment_target_id
proposal_effective_changed
```

## Resolver And Passive Logger Coexistence

Selected principle:

```text
resolver is behavior source of truth when enabled.
passive logger must not independently drive or contradict resolver state.
```

Coexistence matrix:

| Resolver | Passive logger | Intended behavior |
|---|---|---|
| off | off | Current original behavior |
| off | on | Phase 9G-6 passive proposal diagnostics |
| on | on | Resolver drives behavior; passive logger may observe effective assignment only as proxy diagnostics; resolver events are authoritative |
| on | off | Supported but not recommended for first enabled validation because resolver behavior needs diagnostics |

Selected detailed rules:

```text
when resolver is disabled, passive logger observes assignment_proposal as today;
when resolver is enabled and passive logger is also enabled, passive logger should observe effective_assignment, not raw proposal;
resolver events should be written to separate resolver files;
passive proxy events should not be summed with resolver behavior events;
duplicate completion/budget/release interpretations are avoided by treating resolver summaries as authoritative for behavior;
raw proposal acceptance/rejection belongs in resolver diagnostics, not passive ownership reconstruction.
```

First enabled validation recommendation:

```text
enable resolver diagnostics;
keep passive logger optional;
if passive logger is enabled, label its input stream as effective_assignment_from_resolver.
```

## Proposed Runtime Output Files

Keep resolver behavior diagnostics separate from passive proxy diagnostics:

```text
assignment_lifecycle_resolver_events.jsonl
assignment_lifecycle_resolver_summary.json
assignment_lifecycle_resolver_rows.csv   # optional, if row comparison is useful
```

Every resolver event should include:

```text
schema_version
method_name
episode_id
env_id
step
event_type
robot_id
target_id
assignment_proposal_for_robot
effective_assignment_for_robot
behavior_changed
active_target_id
owner_robot_id
release_reason
failure_reason
proposal_rejected_reason
```

Summary should include:

```text
enabled
method_name
num_envs
num_robots
num_tasks
total_steps_observed
total_events
proposal_effective_changed_count
attempt_started_count
attempt_continued_same_target_count
attempt_continued_noop_contract_c_count
switch_rejected_executing_count
exact_claim_conflict_resolved_count
claim_lost_count
owned_target_rejected_count
covered_target_rejected_count
failed_pair_reclaim_rejected_count
active_target_infeasible_deferred_count
target_completed_count
budget_failure_count
release_budget_failure_count
reset_count
stranded_failed_pair_task_count
behavior_changed
```

## Configuration And CLI Boundary

Recommended code-default config fields:

```text
assignment_lifecycle_resolver_enabled = False
assignment_lifecycle_resolver_strict_proposals = True
assignment_lifecycle_resolver_log_diagnostics = False
```

Recommended runtime CLI flags:

```text
--assignment_lifecycle_resolver_enabled
--log_assignment_lifecycle_resolver
--assignment_lifecycle_resolver_output_dir
```

Phase 9G-7D should not require scenario YAML edits. Prefer code-level defaults plus CLI/runtime overrides.

Default-off invariant:

```text
resolver disabled by default
proposal passes through unchanged
no resolver behavior state accumulates
no resolver output files unless logging is enabled
existing checkpoints remain behavior-identical
random/nearest/greedy remain behavior-identical
```

## Disabled Runtime Identity Plan

Future identity comparison should include:

```text
old path / resolver absent
resolver adapter present but disabled
```

For RL and one deterministic baseline, compare:

```text
assignment_history.csv
per_episode.csv
summary.csv
coverage ratio
coverage AUC
episode length
budget trigger count
controller input assignments
decoded assignment proposal sequence
```

Preferred criterion:

```text
exact SHA equality for deterministic artifacts
```

Additional resolver-specific disabled checks:

```text
proposal == effective_assignment for every row
resolver snapshot remains default/empty
resolver event count = 0
behavior_changed = false
no resolver output files unless logging explicitly enabled
```

## Enabled Runtime Invariant Plan

Enabled behavior is expected to differ from old target-every-step trajectories. Do not require identity.

Required invariants:

```text
controller receives effective_assignment
proposal tensor remains unchanged
every proposal/effective difference has an explaining resolver event
one robot has at most one active target
one task has at most one owner
noop while executing continues active target
switch requests do not change effective target
completion clears owner and active target
budget failure releases owner and active target
done reset clears selected env state after final events
raw proposal and effective assignment are both logged
```

The first enabled runtime should make no performance claim. It should validate semantics and diagnostic consistency only.

## Active-Target Infeasibility Runtime Policy

Inspection finding:

```text
viewpoint_assignment_to_actions() returns zero target-directed action for infeasible effective assignments.
```

Risk:

```text
the resolver can keep an active target latched even after that target becomes infeasible;
the controller may output zero action;
the current budget trigger may not fire if availability/feasibility gates exclude that selected pair;
the robot can become stuck without release.
```

Selected first-runtime policy:

```text
Option B:
runtime adapter detects repeated infeasible active target but only logs it.
Do not release immediately in Phase 9G-7D.
```

Required counters:

```text
active_target_infeasible_step_count
active_target_infeasible_streak
active_target_infeasible_without_motion_count
active_target_infeasible_robot_target_pairs
```

Do not silently alter resolver semantics in Phase 9G-7D.

## Stranded Failed-Pair Diagnostics Policy

The 9G-7B resolver uses episode-persistent same-robot failed-pair rejection. This can strand a task.

Selected first-runtime policy:

```text
detect and log only;
do not automatically clear failed pairs;
do not add TTL expiry;
do not add a retry policy in 9G-7D.
```

Candidate stranded condition:

```text
task uncovered
task unowned
at least one robot-target failed/released pair exists for the task
all non-failed robot-target pairs are infeasible/unavailable
all feasible robots are blocked by resolver failed-pair state
```

Recommended logging:

```text
evaluate every pre-step after resolver state is available;
emit one event when the stranded condition starts;
track streak/duration in summary counters;
emit a recovery event if the target becomes claimable again or covered.
```

False-positive mitigation:

```text
include available/feasible masks and blocked robot ids in the event;
track streak length rather than treating one row as proof of permanent stranding;
do not trigger behavior changes from the detector.
```

## Existing Guardrail Interaction

Current guardrails:

```text
cooldown masking
Phase 9F redirect guardrail
Phase 9G failed-pair memory
```

Selected interaction for first resolver-enabled runtime validation:

```text
available_actions masks still operate before policy proposal;
resolver interprets decoded proposals after mask-limited policy/solver output;
cooldown budget diagnostics may remain the source of budget failure/release;
legacy failed-pair memory should remain disabled when resolver behavior is enabled;
redirect guardrail should remain disabled unless a specific interaction test is authorized;
resolver owns final failed-pair behavior when enabled.
```

Rationale:

```text
do not enable two competing behavior mechanisms for the same failed-pair semantics;
do not tune cooldown, redirect, or failed-pair memory while validating resolver semantics;
preserve existing masks unless a later phase explicitly authorizes lifecycle-aware available_actions.
```

## Observation And Training Gate

No training with resolver enabled.

The current policy cannot observe:

```text
active target
idle/executing state
task ownership
failed/released pair state
attempt age
release/failure reason
```

Phase 9G-7D may support:

```text
default-off integration smoke
disabled runtime identity design hooks
enabled bounded runtime diagnostics in a later phase
```

It must not support:

```text
enabled resolver training
performance claims
long training
short training smoke
```

Training gate:

```text
no lifecycle training until all behavior-driving lifecycle state is represented in actor/critic observations as needed.
```

## Proposed Runtime Adapter API

Recommended class:

```python
AssignmentLifecycleResolverRuntimeAdapter(
    enabled=False,
    num_envs=E,
    num_robots=M,
    num_tasks=N,
    device=device,
    method_name="happo",
    output_dir=None,
    log_diagnostics=False,
    strict_proposals=True,
)
```

Recommended pre-step API:

```python
pre = adapter.resolve_pre_step(
    problem=pre_problem,
    assignment_proposal=proposal,
    episode_ids=episode_ids,
    method_metadata=metadata,
)

effective_assignment = pre.effective_assignment
```

Recommended post-step API:

```python
post = adapter.observe_post_step(
    pre_step_problem=pre_problem,
    assignment_proposal=proposal,
    effective_assignment=effective_assignment,
    post_step_problem=post_problem,
    external_diagnostics=diagnostics,
    done_env_ids=done_env_ids,
    episode_ids=episode_ids,
)
```

Other methods:

```text
snapshot()
pop_events()
finalize()
reset_envs(env_ids=None)
```

Disabled behavior:

```text
return proposal clone as effective assignment;
do not construct output files unless log flag is explicitly enabled;
do not accumulate behavior state.
```

The adapter must not duplicate resolver behavior logic. It should call `AssignmentLifecycleResolver` and only handle wiring, output, and runtime diagnostics.

## Wrapper Versus Script Ownership

Selected wiring plan:

```text
shared adapter module
AssignmentHARLWrapper owns one adapter instance for RL wrapper streams
comparison script owns one adapter instance per method
same underlying resolver implementation and adapter API
exactly one resolver state owner per runtime environment stream
```

Why wrapper-owned for RL:

```text
future training reuse requires resolver semantics inside the wrapper path;
playback scripts alone are insufficient and would create semantic drift.
```

Why script-owned for comparison:

```text
comparison methods bypass the HARL wrapper and call the controller directly;
each method must have a fresh resolver state and output directory.
```

## Comparison Method Instance Lifetime

If `evaluate_assignment_methods.py` evaluates multiple methods:

```text
random
nearest
greedy
future methods
```

each method must receive:

```text
fresh resolver instance
fresh output directory
fresh episode/reset state
fresh summary counters
```

No resolver state may be shared across methods.

No lifecycle output collision is allowed.

## Phase 9G-7D Boundary

Recommended next phase:

```text
Phase 9G-7D:
default-off shared resolver runtime adapter and integration smoke
```

Likely implementation scope:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_lifecycle_resolver_runtime.py
scripts/environments/test_assignment_lifecycle_resolver_runtime_smoke.py
minimal default-off wiring hooks in AssignmentHARLWrapper
minimal default-off wiring hooks in evaluate_assignment_methods.py
documentation/report update
TASK_PROGRESS update
```

Phase 9G-7D should not run playback/evaluation/training.

Recommended 9G-7D smoke coverage:

```text
default-off wrapper adapter identity with fake tensors
default-off comparison adapter identity with fake method labels
proposal/effective row schema
done-env reset ordering
budget diagnostic handoff uses effective_assignment
passive logger coexistence mode selection
no output files unless logging enabled
variable E/M/N
input non-mutation
```

Recommended sequence after 9G-7D:

```text
Phase 9G-7E:
bounded disabled identity and enabled runtime diagnostics

Phase 9G-7F:
commit-readiness review
```

## Final Decisions

| Topic | Phase 9G-7C decision |
|---|---|
| Shared runtime architecture | One shared resolver runtime adapter used by wrapper and comparison paths |
| RL integration point | Inside `AssignmentHarlWrapper.step()` via shared adapter, before controller conversion |
| Comparison integration point | In `evaluate_assignment_methods.py`, after solver output and before `viewpoint_assignment_to_actions()` |
| Pre/post ordering | Pre problem + proposal -> resolver -> effective -> controller -> env step -> post problem/diagnostics -> resolver post -> reset |
| Budget handoff | Build budget failure pairs from effective assignment, not raw proposal |
| Proposal/effective logging | Separate proposal and effective fields; do not silently replace existing assignment columns |
| Passive logger coexistence | Resolver is behavior source of truth; passive logger remains proxy-only and should observe effective assignment if resolver enabled |
| Config/CLI boundary | Code defaults plus CLI flags; resolver disabled by default; no scenario YAML requirement |
| Disabled identity plan | Compare old path vs adapter-present-disabled with exact deterministic artifact equality |
| Enabled invariant plan | Validate ownership, continuation, reset, completion, budget release, and proposal/effective explanations; no identity expected |
| Infeasibility policy | Log-only monitoring; no automatic release in first runtime integration |
| Stranded-task policy | Diagnostics-only detector; no automatic failed-pair clear or TTL |
| Guardrails | Keep legacy failed-pair memory disabled for resolver-enabled tests; do not tune cooldown/redirect |
| Observation/training gate | No resolver-enabled training until lifecycle state is observable |
| Phase 9G-7D scope | Default-off runtime adapter + integration smoke only |

## Validation

Allowed documentation-only validation:

```powershell
git status --short --untracked-files=all
git diff --check
```

Results are recorded in `TASK_PROGRESS.md`.
