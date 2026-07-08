# Phase 9G-7A Effective-Assignment Resolver / Active-Target Latch Design Audit

Date: 2026-07-08

## Scope And Boundary

Phase 9G-7A is a documentation-only design audit for a future shared effective-assignment resolver, active-target latch, and Contract C execution semantics.

This phase does not implement behavior. It does not modify Python source files, create a resolver implementation, latch active targets, change noop semantics, create effective assignments, enforce ownership, apply conflict arbitration, change masks, observations, rewards, controller commands, env actions, env dynamics, HARL, solver behavior, scenario YAML, cooldown, redirect guardrail, or failed-pair memory.

No training, short training smoke, playback, comparison-method evaluation, or commit was run.

## Post-Commit Repository State

Commands run at the start of Phase 9G-7A:

```powershell
git status --short
git log -1 --oneline
```

Results:

```text
git status --short: clean
git log -1 --oneline: 91c731af feat(assignment): add passive shared lifecycle diagnostics
```

The user manually committed the complete Phase 9G-6 block. Phase 9G-6 is closed. Phase 9G-7A begins from the committed passive lifecycle diagnostics baseline.

Historical Phase 9G-6 reports still state "no commit was made" because that was true when each report was produced. Those historical statements were not changed.

## Files Inspected

Read-first documents:

- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/AGENTS.md`
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md`
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260707/PHASE9G6A_ACTIVE_TASK_LIFECYCLE_TRANSITION_INTERFACE_AUDIT.md`
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260707/PHASE9G6B_PASSIVE_SHARED_LIFECYCLE_TRANSITION_LOGGER_REPORT.md`
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260707/PHASE9G6C_PASSIVE_LIFECYCLE_RUNTIME_INTEGRATION_REPORT.md`
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260707/PHASE9G6D_PASSIVE_LIFECYCLE_BOUNDED_RUNTIME_VALIDATION_REPORT.md`
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260707/PHASE9G6E_COMMIT_READINESS_REVIEW.md`

Source and runtime boundaries:

- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_lifecycle.py`
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_lifecycle_diagnostics.py`
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_wrapper.py`
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_rl_interface.py`
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_state.py`
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_controller.py`
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py`
- `scripts/environments/evaluate_assignment_rl_playback_diagnostics.py`
- `scripts/environments/evaluate_assignment_methods.py`

Reusable test/analyzer contracts:

- `scripts/environments/test_assignment_lifecycle_transition_logger_smoke.py`
- `scripts/environments/test_assignment_lifecycle_runtime_integration_smoke.py`
- `scripts/environments/analyze_phase9g6d_lifecycle_runtime_validation.py`

## Current Baseline

Current execution is still proposal-direct-to-controller:

```text
method-specific output
  -> decoder / solver
  -> assignment_proposal [E, M]
  -> viewpoint_assignment_to_actions()
  -> controller / environment
```

RL path:

- The policy emits discrete ids.
- `decode_discrete_assignment()` maps target ids `0..N-1` to targets and raw noop id `N` to `-1`.
- `AssignmentHARLWrapper.step()` immediately converts the decoded assignment to env actions through `assignment_to_env_actions()`.

Comparison-method path:

- The solver emits assignment tensor `[E, M]`.
- `evaluate_assignment_methods.py` immediately passes that assignment to `viewpoint_assignment_to_actions()`.

Controller boundary:

- `viewpoint_assignment_to_actions()` accepts only a target/noop assignment tensor.
- It does not own lifecycle state.
- Invalid, infeasible, covered, or noop entries become zero target-directed actions.

Environment boundary:

- `scan_mobile_manipulator_env.py` owns physical state and `viewpoints_covered`.
- `get_assignment_problem()` currently returns `task_status` as unassigned/completed and `robot_status` as idle snapshots.
- It does not own active targets or assignment lifecycle.

Phase 9G-6 passive diagnostics:

- Observe standardized proposals.
- Reconstruct proxy transition state.
- Write diagnostics only.
- Do not produce effective assignments.

## Required Final Decisions

| Decision | Selected Phase 9G-7A contract |
| --- | --- |
| Resolver architecture | Shared standalone resolver used by RL, current baselines, and future method adapters. |
| Active-target state owner | Shared resolver owns behavior-driving active-target state in the first prototype; env remains completion/physical truth. |
| Contract C noop semantics | Noop while idle means remain idle; noop while executing means continue current active target. Noop is not release. |
| Same-target repeat | Repeating the active target explicitly counts as continue. |
| Switching rule | Switching while executing is rejected in the first prototype; effective assignment continues the active target. Switching can become configuration-gated later. |
| Ownership rule | At most one active target per robot and at most one owner per task. One robot failure never globally fails a task. |
| Same-step arbitration | Active owners have priority. Lowest path cost with robot-id tie-break arbitrates simultaneous new claims on an unowned open task. |
| First completion/failure/release signals | Completion from `viewpoints_covered`, budget-trigger failure/release from existing diagnostics, and reset. |
| Default-off boundary | `assignment_lifecycle_resolver_enabled = False` or equivalent explicit gate; disabled means proposal passes through unchanged. |
| Observation/training gate | No lifecycle training until all behavior-driving lifecycle state is visible to actor/critic as needed. |
| Phase 9G-7B scope | Pure shared resolver prototype, disabled by default, fake-sequence smoke tests only, no runtime integration. |

## Resolver Responsibility

The future resolver should conceptually receive:

```text
pre_step_assignment_problem
assignment_proposal [E, M]
persistent resolver lifecycle state
optional method metadata
optional already-existing external diagnostics
```

It should conceptually produce:

```text
effective_assignment [E, M]
updated lifecycle state
transition events
resolver diagnostics
```

It should also produce:

- `proposal_accepted [E, M]`;
- `proposal_rejected_reason [E, M]` as stable integer enum plus names;
- `continued_from_active_target [E, M]`;
- `new_claim_started [E, M]`;
- `claim_winner [E, M]` or per-target winner diagnostics;
- `claim_loser [E, M]`;
- `release_reason [E, M]`;
- `switch_reason [E, M]`;
- `behavior_changed` summary flag.

The resolver must not own continuous control. The controller consumes only `effective_assignment`.

The resolver should not write env state directly. It reads env-owned completion and feasibility snapshots, updates resolver-owned lifecycle tensors, and emits effective assignments for the existing controller bridge.

## Proposal Versus Effective Assignment

Definitions:

```text
assignment_proposal:
  what the allocation method requests this step

effective_assignment:
  what target each robot actually executes this step
```

The proposal is method output. The effective assignment is resolver output. When the resolver is disabled, these are identical.

| Situation | Proposal | Current active target | Effective assignment | State transition | Ownership transition | Diagnostic event | Proposal accepted? |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Idle robot proposes target | target `j` | none | `j` if feasible, uncovered, open, and arbitration winner | idle -> executing | task `j` owner becomes robot | `attempt_started` | yes if winner |
| Idle robot proposes noop | `-1` | none | `-1` | remains idle | none | `noop_idle` | yes |
| Executing robot proposes same target | active target `j` | `j` | `j` | continue executing | unchanged | `attempt_continued_same_target` | yes as continue |
| Executing robot proposes noop | `-1` | `j` | `j` | continue executing | unchanged | `attempt_continued_noop_contract_c` | yes as continue |
| Executing robot proposes different target | target `k`, `k != j` | `j` | `j` in first prototype | continue active target; switch request rejected | unchanged | `switch_rejected_executing` | no |
| Executing target becomes covered | any proposal on row; coverage observed post-step | `j` | pre-step effective assignment follows normal rule; post-step clears state | executing -> idle after post-step | owner cleared; task completed | `target_completed` or `active_target_became_covered` | n/a post-step |
| Executing robot hits budget failure | any proposal on row; budget observed post-step | `j` | pre-step effective assignment follows normal rule; post-step clears state | executing -> released/idle after post-step | owner cleared; pair marked failed/released | `budget_failure`, `release_budget_failure` | n/a post-step |
| Executing target becomes infeasible | any proposal | `j` | `j` in first prototype unless completed/failed/reset | no behavior release in first prototype | unchanged | `active_target_infeasible_deferred` diagnostic only | n/a |
| Two idle robots propose same target | target `j` from multiple robots | none for all claimers | winner gets `j`; losers get `-1` | winner starts, losers remain idle | owner becomes winner | `exact_claim_conflict_resolved` | winner yes, losers no |
| Proposal target already owned by teammate | target `j` | none or other active target | idle proposer gets `-1`; executing proposer continues own active target | idle remains idle or executing continues | unchanged | `owned_target_rejected` | no |
| Proposal target already covered | target `j` | none or active target | idle proposer gets `-1`; executing proposer continues own active target | no new claim | unchanged | `covered_target_rejected` | no |
| Invalid proposal | id `< -1` or `>= N` after decoding | any | disabled mode should never call resolver; enabled strict mode rejects row in fake tests | no state update after validation failure | none | `invalid_assignment_proposal` or exception in strict mode | no |
| Done/reset env | any | any | no controller row after reset; state cleared | reset to idle | all owners cleared | `reset` | n/a |

## Contract C Exact Semantics

Selected Contract C:

```text
target action starts an assignment when idle
target action repeats/continues the active target when already executing same target
noop while idle means remain idle
noop while executing means continue current active target
```

Exact answers:

- Repeating the same target explicitly counts as continue.
- Noop while executing always counts as continue while the active target is still valid and not released.
- A different target action while executing is a switch request.
- Switching is rejected in the first prototype and should be configuration-gated only in a later phase.
- Noop never means release in the first prototype.
- Release is event-driven, not action-driven.

Events that release an active target in the first prototype:

- target completion from post-step `viewpoints_covered`;
- budget-trigger failure/release from existing diagnostics;
- env reset or subset reset.

Deferred release events:

- no-progress failure;
- reach violation failure;
- infeasibility release;
- explicit release action;
- timeout independent of budget.

`active_target_id` clears after post-step completion, post-step budget failure/release, or reset. A robot becomes eligible for a new target proposal on the next decision row after active target is cleared.

## Active-Target Latch Ownership

Architecture options:

| Option | RL/baseline comparability | Future SOTA compatibility | Checkpoint compatibility | Controller coupling | Reset handling | Vectorized support | Testability | Hidden-state risk | Source-of-truth risk | Effort |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A: wrapper-local resolver | Weak; baselines need duplicate logic | Weak | Good when disabled | Medium | Wrapper-only | Good if tensorized | Good for RL only | High if behavior trained | High duplication | Medium |
| B: new shared resolver module | Strong | Strong | Good when disabled | Low; outputs assignment only | Shared reset API | Good | Strong pure tests | Medium until observations migrate | Low for prototype | Medium |
| C: env-owned lifecycle state | Strong | Strong | Enabled behavior needs new training | Medium | Natural env reset | Good | More expensive | Lower after observations | Strong but invasive | High |
| D: shared resolver first, later env promotion | Strong | Strong | Good while disabled | Low first, controlled later | Shared now, env later | Good | Strong staged tests | Managed by training gate | Low if promotion is explicit | Medium over phases |

Selected architecture: Option D.

Phase 9G-7B should implement a shared standalone resolver first, not a wrapper-local resolver and not immediate env-owned lifecycle. The shared resolver becomes the active-target state owner for the disabled prototype. Env-owned completion and physical state remain authoritative. Later env promotion may happen only after the shared contract is validated.

## Proposed Persistent State

Minimum first-prototype state:

| Field | Shape | Dtype | Sentinel | Writer | Reader | Reset condition | First prototype? | Category |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `active_target_id` | `[E, M]` | `torch.long` | `-1` no active target | resolver | resolver, diagnostics, future obs | completion, budget release, reset | required | behavior-driving |
| `robot_execution_state` | `[E, M]` | `torch.long` enum | `0 idle` | resolver | resolver, diagnostics, future obs | reset; completion/release -> idle | required | behavior-driving |
| `task_owner_robot_id` | `[E, N]` | `torch.long` | `-1` no owner | resolver | resolver, diagnostics, future obs | completion, release, reset | required | behavior-driving |
| `attempt_start_step` | `[E, M]` | `torch.long` | `-1` none | resolver | resolver, diagnostics | completion, release, reset | required | behavior-driving / diagnostic |
| `attempt_age` | `[E, M]` | `torch.long` | `0` when idle | resolver or derived from step | diagnostics, future obs | completion, release, reset | required | derived behavior metadata |
| `pair_state` | `[E, M, N]` | `torch.long` enum | `0 none` | resolver | resolver, diagnostics, future obs | reset; covered target may clear | required if failed-pair retry rejection is included | behavior-driving |
| `last_release_reason` | `[E, M]` | `torch.long` enum | `-1 none` | resolver | diagnostics, future obs | reset or next attempt | required as diagnostics | diagnostic-only first |
| `last_failure_reason` | `[E, M]` | `torch.long` enum | `-1 none` | resolver | diagnostics, future obs | reset or next attempt | required as diagnostics | diagnostic-only first |
| `step` | `[E]` | `torch.long` | `0` | resolver | resolver | reset | required | derived/timing |

Do not automatically copy every Phase 9G-6 proxy tensor into behavior state. Phase 9G-7B should keep only the state needed to produce `effective_assignment` and explain it.

Recommended first-prototype enums:

```text
robot_execution_state:
  0 idle
  1 executing
  2 released

pair_state:
  0 none
  1 active
  2 completed
  3 failed_budget
  4 released_budget
```

Same-robot retry after budget failure:

- Mark the robot-target pair as `failed_budget` / `released_budget`.
- Reject same-robot immediate reclaim while that pair state remains failed/released.
- Keep the task open to teammates unless covered.
- Clear the failed/released pair state on target coverage or reset.

This is the smallest lifecycle-owned alternative to TTL-only masking. It should remain disabled by default and fake-sequence tested first.

## Completion, Failure, Release, And Timeout

First accepted transition signals:

| Signal | Observed when | Pre/post controller execution | Active target clears? | Owner clears? | Same robot retry? | Teammate claim? |
| --- | --- | --- | --- | --- | --- | --- |
| Completion | post-step `viewpoints_covered` changes false -> true | after controller execution | yes | yes; task becomes completed | no because task is covered | no because task is covered |
| Budget failure/release | post-step existing budget-trigger diagnostics identify robot-target pair | after controller execution | yes | yes; task remains open if not covered | no while pair state is failed/released | yes if task open and feasible |
| Reset | full or subset env reset | after final post-step diagnostics or before first row | yes | yes | state cleared | state cleared |

Deferred:

- no-progress failure;
- reach violation failure;
- target infeasibility release;
- explicit release action;
- timeout independent of budget.

Infeasibility:

The first prototype may reject a new idle claim if `available_mask`/`feasible_mask` says the target is unavailable. It should not release an already executing active target only because the next pre-step snapshot reports infeasibility; that needs a separate design because controller motion can require multiple steps and transient feasibility changes could cause churn.

## Same-Step Conflict Arbitration

Selected applied rule:

```text
active ownership has priority over new claims
lowest path cost wins simultaneous new claims on an unowned open task
robot id breaks exact cost ties
robot id fallback is used when costs are unavailable or non-finite
```

Answers:

- Arbitration happens before active-target latching for new claims.
- Existing active owners are protected from new claims.
- A newly proposed lower-cost robot cannot steal an already owned target in the first prototype.
- Arbitration applies only to multiple idle/released robots proposing the same unowned, uncovered, feasible target.
- Losing idle robots get effective assignment `-1` and remain idle.
- Losing executing robots should not exist in the new-claim set; executing robots continue previous active targets.
- Non-finite costs use deterministic robot-id ordering and record `fallback_reason = cost_unavailable_or_non_finite`.
- Exact cost ties use lower robot id.

This only resolves exact same-target ownership. It does not solve nearby target conflict, path crossing, overlap, or near-miss behavior.

## Ownership Rules

Selected invariants:

- At most one active target per robot.
- At most one owner per task.
- Ownership is created only when an idle/released robot's target proposal is accepted and wins arbitration.
- Ownership is cleared on completion, budget release, reset, or later explicitly designed release.
- Completed tasks retain no active owner.
- Teammates may propose an owned task, but the resolver rejects that proposal for execution.
- If the teammate is idle, its effective assignment is `-1`.
- If the teammate is executing another active target, it continues that active target.
- One robot's failure never globally blocks a task.
- Pair failure is robot-target scoped.

## Switching Semantics

Options:

| Option | Policy clarity | Baseline behavior | Future SOTA queues | Controller discontinuity | Path inefficiency | Hidden-state risk | Complexity |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A: reject switches while executing | High | Stable; methods may keep proposing but resolver continues active target | Queues need later adapter semantics | Low | Possible delay if better target appears | Medium until observed | Low |
| B: allow switch and implicitly release old target | Medium | Large behavior change | Natural for queue methods | High | Can thrash paths | High | Medium |
| C: allow switch only after failure/release | High | Stable | Compatible; queues wait for release | Low | May miss opportunistic changes | Medium | Low-medium |
| D: configuration-gated switch behavior | Flexible | Needs careful test matrix | Flexible | Depends on mode | Depends on mode | Medium-high | Medium |

Selected first prototype behavior: reject target switches while executing. The effective assignment remains the current active target. Emit `switch_rejected_executing` with previous and proposed target ids.

This is equivalent to Option C for the first prototype: switching is available only after the robot is no longer executing because of completion, budget release, or reset. A future config-gated switch mode may be added after resolver identity and observation implications are validated.

## Idle And Executing Method Invocation

Options:

| Model | Description | HAPPO | Random/nearest/greedy | Future centralized matching | Future queues/auction/optimization | Implementation impact |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Every method proposes for every robot every step; resolver interprets executing proposals | Best compatibility | Best compatibility | Matching output can still be adapted to `[E, M]` | Queues can emit current head or noop | Smallest |
| 2 | Methods are called only for idle/released robots | Requires RL wrapper/action cadence changes | Requires solver API changes | Requires partial matching interface | Natural for queues but new adapter work | Larger |
| 3 | Method adapter emits proposal validity mask | Requires new adapter contract | Requires new adapter contract | Useful later | Useful later | Medium |

Selected first prototype: Model 1.

Every method still proposes for every robot every step. The resolver interprets proposals for executing robots as continue, switch request, or ignored/rejected. This minimizes changes to HAPPO, random, nearest, greedy, and future method adapters.

## Available-Actions Implications

Phase 9G-7B should not change `available_actions` unless separately authorized.

Candidate future action availability:

| Robot state | Candidate mask rule | Contract C interaction | Recommendation |
| --- | --- | --- | --- |
| idle | open feasible targets + noop | target starts, noop idle | future behavior phase after resolver fake tests |
| executing | all target actions + noop | resolver interprets noop/same target as continue, different target as rejected switch | safest for disabled/fixed-checkpoint playback because shape/content can remain unchanged |
| executing | current target + noop | makes switch impossible at mask level | possible later, but changes action contents |
| executing | only noop | Contract C pure continue action | clearer but larger hidden semantic shift |
| released/failed | open feasible targets excluding failed same-robot pair + noop | target starts if allowed; failed pair rejected | should wait for observation migration or disabled playback diagnostics |
| completed transition | robot becomes idle before next decision | normal idle mask | safe after completion source is env-owned |

For Phase 9G-7B, the resolver should be fake-sequence tested without changing action masks. Runtime mask changes are a separate authorization gate.

## Observation And Markov Requirements

The first disabled behavior prototype may be tested with fixed checkpoints or fake sequences, but it is not training-ready.

Training-ready lifecycle requires these fields:

| Field | Actor observation | Shared/critic observation | Reason |
| --- | --- | --- | --- |
| `robot_is_idle` | yes | yes | Interpret noop and target actions. |
| `robot_is_executing` | yes | yes | Distinguish continue from idle noop. |
| `active_target_id` or embedding | yes | yes | Know what noop continues. |
| `task_claimed` | yes | yes | Avoid owned tasks. |
| `task_owner` relation | useful local relation | yes | Explain teammate ownership. |
| `attempt_age` | yes | yes | Interpret timeout/failure risk. |
| `pair_failed/released` state | yes if it affects eligibility | yes | Avoid hidden same-robot retry rejection. |
| `failure/release reason` | optional actor if used in policy | yes if behavior/reward depends on reason | Explain why target is unavailable/released. |

Gate:

```text
No lifecycle training until the policy can observe all behavior-driving lifecycle state.
```

Short training smoke may be allowed only in a later observation-integration phase. Long training remains user-run only.

## Default-Off Identity

Recommended config boundary:

```text
assignment_lifecycle_resolver_enabled = False
```

Optional future fields:

```text
assignment_lifecycle_resolver_log_diagnostics = True
assignment_lifecycle_resolver_reject_switch_while_executing = True
assignment_lifecycle_resolver_reject_failed_pair_reclaim = True
assignment_lifecycle_resolver_arbitration = "lowest_cost_robot_id_tiebreak"
```

When disabled:

- `effective_assignment == assignment_proposal`;
- current target-every-step behavior is preserved;
- current noop semantics are preserved;
- no persistent active target affects control;
- no ownership affects control;
- old checkpoints remain behavior-identical;
- random, nearest, greedy, and future adapters remain behavior-identical;
- no lifecycle resolver state should alter masks, observations, rewards, controller commands, or env dynamics.

When enabled:

- proposals are interpreted through the resolver;
- active-target latch may change effective assignment;
- Contract C semantics become active;
- the MDP changes even if action shape remains `[M, N+1]`.

## Reset And Vectorized Environments

Requirements:

- Support `E` parallel envs.
- Support variable `M` robots and `N` tasks.
- No hardcoded `M=3` or `N=50`.

Reset behavior:

| Reset/event | Required behavior |
| --- | --- |
| Full episode reset | Clear active targets, robot states, owners, pair states, attempt metadata, last reasons, and step counters for all envs. |
| Subset env reset | Clear only selected env ids; preserve continuing env state. |
| Robot-specific reset | Defer unless env exposes robot-specific reset; if later supported, clear that robot and any task owned by it. |
| Task completion | Clear owner for completed task, clear active target for robots executing it, mark task completed. |
| Termination/truncation | Record final post-step events before clearing selected env state. |

## Proposed Resolver API

Recommended module for Phase 9G-7B:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_lifecycle_resolver.py
```

Conceptual API:

```python
resolver = AssignmentLifecycleResolver(
    num_envs=E,
    num_robots=M,
    num_tasks=N,
    device=device,
    enabled=False,
)

pre_result = resolver.resolve_pre_step(
    problem=problem,
    assignment_proposal=proposal,
    method_metadata=metadata,
)

effective_assignment = pre_result.effective_assignment

post_result = resolver.observe_post_step(
    pre_step_problem=problem,
    assignment_proposal=proposal,
    effective_assignment=effective_assignment,
    post_step_problem=post_problem,
    external_diagnostics=diagnostics,
    done_env_ids=done_env_ids,
)
```

Result schema:

```text
effective_assignment [E, M]
proposal_accepted [E, M]
proposal_rejected_reason [E, M]
continued_from_active_target [E, M]
new_claim_started [E, M]
claim_conflict [E, M]
claim_winner [E, M]
claim_loser [E, M]
released [E, M]
release_reason [E, M]
switch_requested [E, M]
switch_rejected [E, M]
resolver_events list[dict]
behavior_changed bool
```

When disabled:

```text
effective_assignment = assignment_proposal.clone()
behavior_changed = false
all transition/change flags false
```

When enabled, `behavior_changed` may be true if any effective assignment differs from proposal or if ownership/continuation semantics changed execution.

## Relationship To Passive Logger

The future resolver should not reuse `AssignmentLifecycleTransitionLogger` as its behavior state machine. That logger is proxy-only and diagnostics-only.

Selected relationship:

- Resolver owns behavior-driving state.
- Passive logger remains diagnostics/validation support.
- Shared event names/schema should be reused where possible.
- Resolver events should drop `_proxy` suffix when they represent actual resolver behavior.
- Proxy-only events remain proxy-only in Phase 9G-6 diagnostics.

Mapping:

| Phase 9G-6 proxy event | Future resolver event |
| --- | --- |
| `attempt_started_proxy` | `attempt_started` |
| `attempt_continued_proxy` | `attempt_continued` |
| `noop_idle_proxy` | `noop_idle` |
| `noop_after_active_ambiguous` | replaced by `attempt_continued_noop_contract_c` |
| `switch_request_proxy` | `switch_rejected_executing` first; later `switch_accepted` if enabled |
| `exact_claim_conflict_proxy` | `exact_claim_conflict_resolved` when applied |
| `target_completed_proxy` | `target_completed` |
| `budget_failure_proxy` | `budget_failure` |
| `release_proxy` | `release_budget_failure` |
| `reset_proxy` | `reset` |

Avoid two competing lifecycle state machines. The passive logger may observe resolver outputs later, but it must not independently drive behavior.

## Architectural Decision Matrix

| Architecture | Semantic correctness | Method comparability | Future SOTA compatibility | Default-off safety | Checkpoint compatibility | Controller coupling | Testability | Vectorized scalability | Source-of-truth clarity | Complexity |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A: RL-wrapper-local resolver | Medium | Weak | Weak | Good | Good when disabled | Medium | Medium | Good if tensorized | Weak; RL-only state | Medium |
| B: shared standalone resolver used by all methods | High for prototype | Strong | Strong | Good | Good when disabled | Low | Strong | Strong | Good within resolver boundary | Medium |
| C: env-owned lifecycle | Highest eventual | Strong | Strong | Riskier first step | Requires new training when enabled | Medium | Harder | Strong | Strong | High |
| D: shared disabled resolver prototype followed by later env promotion | Highest staged safety | Strong | Strong | Best | Good while disabled | Low first | Strong | Strong | Strong with explicit promotion gate | Medium staged |

Selected architecture: D.

Phase 9G-7B should implement B as the first concrete step, within the D migration path.

## Phase 9G-7B Minimal Prototype Boundary

Recommended next phase:

```text
Phase 9G-7B:
pure shared effective-assignment resolver prototype
disabled by default
fake-sequence smoke tests only
no runtime integration
```

Likely files:

- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_lifecycle_resolver.py`
- `scripts/environments/test_assignment_lifecycle_resolver_smoke.py`
- Phase 9G-7B implementation report under `AgentRead/YYYYMMDD/`
- `AgentRead/TASK_PROGRESS.md`

Do not modify in 9G-7B unless explicitly authorized:

- `assignment_harl_wrapper.py`
- `evaluate_assignment_rl_playback_diagnostics.py`
- `evaluate_assignment_methods.py`
- `assignment_controller.py`
- `scan_mobile_manipulator_env.py`
- scenario YAML
- observations/rewards/masks

Required fake-sequence coverage:

- default-off identity;
- idle target claim;
- idle noop;
- executing same-target continuation;
- noop-as-continue;
- switch while executing rejected;
- completion release;
- budget failure release;
- same-robot failed-pair retry rejection;
- teammate claim after another robot budget-fails the target;
- subset/full reset;
- simultaneous exact-target arbitration;
- owned-target proposal rejection;
- covered-target proposal rejection;
- invalid proposal handling;
- variable `E`, `M`, `N`;
- input non-mutation.

No runtime integration, playback, comparison-method evaluation, short training smoke, or training should run in 9G-7B.

## Final Recommendation

Proceed to Phase 9G-7B with a pure shared resolver prototype and fake-sequence smoke tests only.

The first behavior-capable resolver should remain disabled by default and should not be integrated into RL playback or comparison-method runtime paths until its fake-sequence contract is validated.

Selected implementation contract:

- shared resolver module;
- behavior-driving active target and ownership state owned by resolver;
- disabled means exact proposal pass-through;
- enabled Contract C means noop while executing continues active target;
- switch while executing rejected;
- existing active ownership protected;
- lowest path cost plus robot-id tie-break for simultaneous new claims;
- completion, budget failure/release, and reset only;
- same-robot failed-pair retry rejected while target remains uncovered and pair state remains failed/released;
- teammate may claim released target if open, feasible, and arbitration winner;
- no training until observations expose all behavior-driving lifecycle state.

## Validation

Allowed documentation-only validation:

```powershell
git status --short --untracked-files=all
git diff --check
```

Results are recorded in `TASK_PROGRESS.md` and the final response.
