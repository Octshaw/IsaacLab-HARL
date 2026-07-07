# Phase 9G-6A Active-Task / Release Lifecycle Transition Interface Audit

Date: 2026-07-07

## Scope And Boundary

Phase 9G-6A is a documentation-only active-task / release lifecycle transition and interface contract audit. It does not implement lifecycle behavior. It does not change wrapper behavior, environment behavior, observations, rewards, available action shape or contents, action ids, action semantics, controller behavior, HARL code, baselines, scenario YAML, cooldown, redirect guardrail, or failed-pair memory tuning.

The purpose is to move beyond the Phase 9G-0 state vocabulary and define the interface contracts that a future lifecycle prototype would need: decision cadence, action/noop semantics, source of truth, ownership arbitration, transition events, observation migration, baseline integration, and the minimum safe next phase.

## Files Inspected

Documentation and evidence:

- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/AGENTS.md`
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md`
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260705/PHASE9G0_ACTIVE_TASK_LIFECYCLE_DESIGN_AUDIT.md`
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260706/PHASE9G1_LIFECYCLE_RECONSTRUCTION_ANALYZER_REPORT.md`
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260706/PHASE9G2_FAILED_PAIR_RELEASE_MEMORY_IMPLEMENTATION_REPORT.md`
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260706/PHASE9G3_FAILED_PAIR_MEMORY_PLAYBACK_VALIDATION_REPORT.md`
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260706/PHASE9G4A_TTL_BOUNDARY_SEMANTICS_REVIEW.md`
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260706/PHASE9G4B_FAILED_PAIR_MEMORY_D6_PLAYBACK_VALIDATION_REPORT.md`
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260707/PHASE9G5_FAILED_PAIR_MEMORY_DESIGN_DECISION_REVIEW.md`

Source and interface files:

- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_wrapper.py`
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_rl_interface.py`
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_state.py`
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_controller.py`
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py`
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scenario_config.py`

Execution, playback, baseline, and smoke-test paths:

- `scripts/environments/evaluate_assignment_rl_playback_diagnostics.py`
- `scripts/environments/evaluate_assignment_methods.py`
- `scripts/environments/test_assignment_harl_wrapper_smoke.py`
- `scripts/environments/test_assignment_cooldown_mask_smoke.py`
- `scripts/environments/test_assignment_failed_pair_memory_smoke.py`

## Evidence Preserved From Phase 9G

| Phase | Mechanism activation | Action suppression | Return delay | Total same-owner returns | Coverage improvement |
| --- | --- | --- | --- | --- | --- |
| 9G-1 lifecycle reconstruction | Offline proxy found 12 budget-failed/released segments. | None. Analyzer only. | Same owner returned after release. | 12 same-owner returns. | `coverage_gain_within_20_count = 0`. |
| 9G-2 implementation | Disabled-by-default pair memory added. | Only possible when enabled. | Temporary TTL memory only. | Not validated in 9G-2. | No behavior claim. |
| 9G-3 D=5 playback | Memory triggered 6 times. | Suppressed 0 actions. | Memory expired before T+6 returns. | 6 same-owner returns. | `coverage_gain_within_20_count = 0`. |
| 9G-4A TTL review | Fake-env review defined TTL contract. | D covers T+1 through T+D. | D=5 misses T+6; D=6 covers T+6. | Not playback. | Not playback. |
| 9G-4B D=6 playback | Memory triggered 6 times. | Suppressed 6 original T+6 reacquisitions. | Returns shifted to T+7 after expiry. | 6 same-owner returns. | `coverage_gain_after_release_count = 0`, `coverage_gain_within_20_count = 0`; noop and fail-open remained 0. |

The evidence distinguishes activation, suppression, delay, return-count reduction, and coverage gain. Phase 9G-4B proved that TTL-only memory can suppress and delay a repeated assignment. It did not reduce total same-owner returns and did not improve coverage.

## Current Decision Cadence

### Current RL Wrapper Path

The current RL assignment contract is target-every-step:

1. The policy produces one discrete assignment action for every robot on every wrapper step.
2. `AssignmentHARLWrapper.step()` reads a pre-step assignment problem from the env.
3. The wrapper builds `available_actions` from the env `available_mask` plus wrapper overlays.
4. The wrapper decodes each discrete id with `decode_discrete_assignment()`.
5. Target ids `0..N-1` become viewpoint ids. The noop id `N` becomes `-1`.
6. `assignment_to_env_actions()` passes the decoded assignment to `viewpoint_assignment_to_actions()`.
7. `viewpoint_assignment_to_actions()` computes the continuous base/scanner action for the current step only.
8. `env.step()` applies the continuous action through the env task-space action buffers.
9. The env updates scan progress and `viewpoints_covered`.
10. The wrapper updates diagnostics, stores `last_assignment`, stores `_previous_assignment`, and builds next-step observations and `available_actions`.

### Current Controller And Env Contract

The env/controller does not retain a task target as an active assignment. Motion toward a viewpoint depends on the current step assignment being selected again on successive steps.

If a robot selects noop after selecting a target in the previous step:

- the noop decodes to `-1`;
- `viewpoint_assignment_to_actions()` treats that robot as invalid/noop for target motion;
- the robot receives zero high-level task-space command for that step;
- `_previous_assignment` may still record the prior target for observations, diagnostics, cooldown, redirect guardrail, and failed-pair memory logic;
- `_previous_assignment` does not continue execution or command the robot.

### Current Baseline Path

The baseline evaluation path also uses target-every-step semantics:

1. `evaluate_assignment_methods.py` asks a solver for a fresh assignment each env step.
2. Solvers operate on the current `AssignmentProblem` snapshot.
3. Solvers choose targets from `available_mask` or noop if no target is available.
4. `viewpoint_assignment_to_actions()` converts the fresh assignment to continuous action.
5. There is no shared persistent active-target state.

Random, nearest, and greedy solvers avoid exact duplicate target selection inside the current decision row, but they do not own, latch, or release targets across steps.

### Where `active_target_id` Would Enter

A future `active_target_id` cannot be only a diagnostic field if it is meant to change execution. It must enter between policy/baseline action selection and controller conversion:

```text
policy_or_solver_action + lifecycle_state -> effective_assignment -> viewpoint_assignment_to_actions()
```

That resolver would decide whether a robot's current policy action starts a new attempt, continues an active target, switches target, remains idle, or releases. It would also need to feed:

- `available_actions` construction;
- actor and critic observations before training;
- RL playback diagnostics;
- baseline evaluation;
- reset handling;
- same-step claim arbitration.

## Assignment Action Contract Options

| Contract | Meaning | Semantic clarity | Controller compatibility | Policy observability | Checkpoint compatibility | Baseline compatibility | Complexity | MDP-change risk | Variable M/N support |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A: target every step | Every robot chooses its pursued target every step; repeated target means continue. | Current but weak for lifecycle. | Fully compatible. | Existing observations are enough for current behavior, not true lifecycle. | Best. | Current baseline behavior. | Low. | Low if unchanged, but insufficient. | Good. |
| B: assign only when idle/released | A target action starts an attempt; target is latched while executing. | Strong. | Needs effective assignment latch before controller. | Requires active state in observations for training. | Playback can be disabled by default; trained checkpoints not semantically compatible when enabled. | Needs shared lifecycle layer. | Medium-high. | High when enabled. | Good if lifecycle tensors are `[env, robot]`, `[env, task]`, `[env, robot, task]`. |
| C: explicit continue semantics without new action ids | Target action starts/switches; noop means continue active target when executing, remain idle when idle. | Strong if observations expose robot state. | Compatible through effective assignment resolver. | Requires robot executing/idle and active target observations. | Shape-compatible but semantic change when enabled. | Needs shared resolver for RL and baselines. | Medium. | High when enabled. | Good with existing `[M, N+1]` action shape. |
| D: separate continue/release action ids | Adds explicit continue/release actions. | Clearest. | Needs resolver and new action mapping. | Clear if observed. | Breaks action shape/id contract. | Requires solver rewrite and new baseline actions. | High. | Very high. | More complex because action dimension changes with N plus extra ids. |

Recommended next prototype contract: Contract C, but only after a passive transition logger confirms the transition stream. Contract C preserves the `[M, N+1]` tensor shape and avoids new action ids, while making execution continuous through a lifecycle resolver. It is still a real action-semantics change when enabled, so it must remain disabled during fixed-checkpoint playback and must not be used for training without observation migration.

Contract B is the conceptual foundation behind Contract C. Contract C is the practical shape-preserving version: it defines what noop means while executing. Contract D should be deferred unless noop overload proves unworkable.

## Noop Semantics

Today, noop means no target assignment for this step. It is always available, decodes to `-1`, and produces zero target-directed controller action. It does not mean continue, release, retain ownership, or complete an active target.

Under a lifecycle design, noop should not mean explicit release. Release should initially be driven by lifecycle events such as completion, budget failure, timeout, infeasibility, or an explicit future release action if one is later added.

Recommended lifecycle noop semantics for a shape-preserving prototype:

| Robot state | Noop meaning | Required observation support | Risk |
| --- | --- | --- | --- |
| Idle | Remain idle / no new assignment. | `robot_is_idle`, no active target. | Low. |
| Executing | Continue current active target. | `robot_is_executing`, active target id/embedding, active attempt age. | Medium if hidden; acceptable only for disabled playback prototype or training after observation migration. |
| Released/failed | Do not reacquire a failed same-robot pair on this row; select a new target or remain idle. | released/failed pair context, active/release reason if used for policy learning. | Hidden-state risk if behavior affects masks but observations do not expose it. |
| Completed | Robot should transition to idle before the next decision. | completion/idle state. | Low if completion is env-derived. |

Overloading noop is not safe for training unless the policy can distinguish idle from executing and can identify the active target. Hidden state would make the same action id mean different things without policy-visible context. It is acceptable for diagnostic playback only when the purpose is to inspect fixed behavior, not to draw training conclusions.

## Source Of Truth

Recommended placement is a shared lifecycle manager interface that can be used by both RL and baseline paths, with env promotion later for persistent semantic truth. The next phase should begin as a passive logger, not behavior.

| Field | Recommended source of truth | Writer | Reader | Reset timing | Affects `available_actions`? | Must appear in observations before training? |
| --- | --- | --- | --- | --- | --- | --- |
| `viewpoints_covered` | Env-owned persistent state. | Env scan progress update. | Env, wrapper, baselines, lifecycle manager. | Env reset. | Yes, already through env `available_mask`. | Already represented through task features. |
| Task completion | Derived from `viewpoints_covered`; eventually env-owned task lifecycle. | Env. | Wrapper, lifecycle manager, baselines. | Env reset. | Yes. | Yes, already covered flag. |
| Robot physical position | Env-owned persistent state. | Env dynamics/task-space integration. | Controller, env observations, assignment problem. | Env reset. | Indirectly through feasibility/cost. | Already in base/scanner observations and assignment features. |
| Current commanded target | Derived per step today; controller/effective assignment snapshot. | Wrapper or baseline action resolver. | Controller. | Each decision row. | No direct mask effect today. | Not today; future active target should be exposed. |
| `active_target_id` | Future lifecycle-owned persistent state; passive logger first. | Lifecycle manager after action arbitration. | Resolver, diagnostics, observations. | Robot/episode reset, completion, release, failure, switch. | Yes when behavior enabled. | Yes. |
| `task_owner_robot_id` | Future lifecycle-owned task state; env promotion later. | Lifecycle manager/arbitration. | Resolver, baselines, diagnostics. | Task completion, release, reset. | Yes, claim mask for other robots if enabled. | Yes, at least relational/shared observation. |
| Robot lifecycle state | Future lifecycle-owned persistent state. | Lifecycle manager. | Resolver, observations, diagnostics. | Robot/episode reset. | Yes. | Yes. |
| Task lifecycle state | Future lifecycle-owned persistent state; completion remains env-derived. | Env for completion; lifecycle manager for claim/release proxy. | Resolver, baselines, observations. | Task completion/reset/release. | Yes. | Yes. |
| Pair attempt state | Future lifecycle-owned pair state; wrapper-local prototypes only if disabled. | Lifecycle manager. | Resolver, diagnostics, failed-pair memory bridge. | Pair release, expiry, coverage, reset. | Yes for same-robot failed/released suppression. | Yes if behavior is trained. |
| Attempt start step | Lifecycle-owned persistent metadata. | Lifecycle manager on claim/start. | Timeout/failure logic, diagnostics, observations. | Attempt end/reset. | Indirectly. | Yes as attempt age or normalized age if trained. |
| Attempt age | Derived from current step minus attempt start. | Lifecycle manager/diagnostics. | Timeout/failure logic, observations. | Attempt end/reset. | Indirectly. | Yes if timeout/failure affects policy. |
| Progress/no-progress | Derived snapshot plus optional lifecycle accumulator. | Env/lifecycle manager from distance/coverage signals. | Failure/diagnostics. | Attempt end/reset. | Only if used as failure guard. | Yes if it affects behavior. |
| Failure reason | Lifecycle-owned event metadata. | Lifecycle manager from approved signals. | Diagnostics, observations if trained. | Pair release/reset or TTL expiry. | Possibly. | Yes if failure memory affects masks. |
| Release reason | Lifecycle-owned event metadata. | Lifecycle manager. | Diagnostics, observations. | Release/reset. | Possibly. | Yes if release state changes action availability. |
| Timeout state | Lifecycle-owned state derived from attempt age or budget trigger. | Lifecycle manager. | Resolver, diagnostics. | Release/reset. | Yes if timeout releases/suppresses pair. | Yes if behavior is trained. |

Controller-owned state should remain limited to immediate continuous command generation. The controller should not become the owner of assignment lifecycle.

## Exact Transition Contract

This table defines the target contract for a future lifecycle prototype. It is not implemented in Phase 9G-6A.

| Current robot state | Current task state | Current pair state | Event/signal | Guard condition | Next robot state | Next task state | Next pair state | Ownership update | Active target update | Available-actions effect | Observation effect | Diagnostic event |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| idle | open | none | robot selects open target | target feasible and not covered; arbitration winner | assigned/executing | claimed | active | owner becomes robot id | set to target id | target may be hidden from other robots for exact ownership if behavior enabled | expose executing, active target, owner relation | `attempt_started` |
| assigned | claimed | active | first post-claim controller row | active target valid | executing | claimed | active | unchanged | unchanged | executing robot uses continue/current-target rule | expose attempt age 0/1 | `execution_started` |
| executing | claimed | active | normal progress row | target not covered, no failure/timeout | executing | claimed | active | unchanged | unchanged | depends on selected contract; current target/noop continue available | expose increased attempt age/progress | `attempt_continued` |
| executing | claimed/open | active | target becomes covered by same robot | `viewpoints_covered[target]` becomes true | idle | completed | completed | clear owner | clear active target | completed target unavailable to all | expose idle and covered task | `attempt_completed` |
| executing | claimed/open | active | target covered by teammate | `viewpoints_covered[target]` true and owner is different | idle | completed | released_or_completed | clear owner | clear active target | completed target unavailable to all | expose idle and covered task | `target_completed_by_teammate` |
| executing | claimed | active | budget failure | approved budget trigger for pair | released/idle | open or released | failed_budget/released | clear same owner; target not globally failed | clear active target | same robot may be temporarily blocked from pair; teammates may still select target | expose failure/release if behavior trained | `attempt_failed_budget` |
| executing | claimed | active | no-progress failure | future approved no-progress signal | unresolved | unresolved | unresolved | unresolved | unresolved | unresolved until signal is designed | must expose if used | `attempt_failed_no_progress_candidate` |
| executing | claimed | active | timeout | attempt age exceeds configured timeout | released/idle | open or released | timeout/released | clear owner | clear active target | same-robot retry rule depends on lifecycle config | expose timeout/release if trained | `attempt_timeout` |
| executing | claimed | active | explicit release | future explicit release action or system release | unresolved | open/released | released | clear owner | clear active target | target open to eligible robots | expose release if action-driven | `attempt_released_explicit` |
| executing | claimed | active | robot switches target | target action differs from active target | unresolved; recommended defer switching semantics | unresolved | old pair released/switch, new pair active | old owner clear, new owner set after arbitration | set new target only if switch allowed | would be a major action semantic change | must expose switch eligibility | `attempt_switch_requested` |
| idle | open/completed | none | robot selects noop | none | idle | unchanged | none | none | none | noop remains available | expose idle | `noop_idle` |
| executing | claimed | active | robot selects noop | Contract C: noop means continue | executing | claimed | active | unchanged | unchanged | noop is interpreted as continue, not release | must expose executing and active target | `noop_continue` |
| any | any | any | robot reset | env reset for robot/env | idle | task state from env coverage reset/snapshot | none | clear owner involving robot | clear active target | rebuild from env problem | reset lifecycle observations | `robot_reset` |
| any | any | any | episode reset | env reset | idle | open except preconfigured covered if any | none | clear all owners | clear all active targets | rebuild from env problem | reset all lifecycle observations | `episode_reset` |
| executing/idle | open/claimed | active/none | task becomes unavailable/infeasible | feasible mask false or target invalid while not covered | unresolved; likely release or block | open/blocked proxy | blocked/released | clear or retain depending on cause | clear if release | mask infeasible target through env available mask | expose infeasible/block if behavior trained | `task_infeasible_or_unavailable` |

Unresolved rows should not be silently implemented. In particular, no-progress failure, explicit release, target switching, and infeasibility release need a narrow follow-up design before behavior changes.

## Ownership And Same-Step Arbitration

When two or more robots select the same open target in the same decision row, a future lifecycle owner must be chosen before claims become persistent.

| Rule | Determinism | Fairness | Load balancing | Path-cost consistency | Baseline comparability | Vectorized difficulty | Policy learning implications |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Fixed robot-id priority | High. | Low; low-id robots win ties. | Weak. | Ignores path quality. | Easy but can bias baselines. | Low. | Policy may learn id ordering artifacts. |
| Lowest path-cost winner | High with tie-breaker. | Medium. | Medium. | Strong. | Strong because baselines already use costs. | Medium. | Encourages cost-aware assignment. |
| Highest feasibility/confidence winner | High if score defined. | Medium. | Medium. | Depends on score. | Harder if baselines do not share score. | Medium. | Risk of opaque scoring artifacts. |
| Centralized deterministic resolver | High. | Depends on objective. | Strong if objective includes load. | Strong if objective includes cost. | Strong if shared by RL/baselines. | Medium-high. | Clean but may hide assignment reasoning from policy if not observed. |
| Temporary duplicate claims then resolve next step | Lower. | Ambiguous. | Weak. | Delays conflict handling. | Poor. | Medium. | Creates unstable one-step ownership semantics. |
| Reject all conflicting claims | High. | Harsh but fair. | Weak. | Wastes decisions. | Poor if baselines conflict. | Low. | May create avoidable idle/noop pressure. |

Recommended minimal deterministic arbitration for a future prototype: lowest path-cost winner with robot-id tie-breaker, implemented inside a centralized lifecycle resolver shared by RL and baselines. This is deterministic, uses existing assignment cost structure, and avoids pure robot-id bias except for exact cost ties.

This only addresses same exact target conflict. It does not solve nearby target conflict, path overlap, or near-miss behavior. Nearby target spacing and path interaction remain separate coordination or controller/trajectory concerns.

## Completion, Failure, Timeout, And Release Signals

| Existing signal | Reliable for completion? | Reliable for failure? | Reliable for timeout? | Reliable for release? | Recommended use |
| --- | --- | --- | --- | --- | --- |
| `viewpoints_covered` | Yes. | No. | No. | Completion release only. | Completion source of truth. |
| New coverage gain | Indirect. | No by itself. | No. | Diagnostics. | Progress diagnostic; not completion unless target covered. |
| Reach violation | No. | Candidate only if clearly defined per attempt. | No. | Candidate. | Diagnostics or future failure guard after validation. |
| Same-target streak | No. | No. Normal motion requires repeated target selection today. | No. | No. | Diagnostics only. |
| Budget trigger | No. | Yes for initial budget-failure/timeout proxy if semantics are explicit. | Candidate. | Yes, can release same robot-target attempt. | Initial failure/release source. |
| Failed-attempt count | No. | Accumulator, not event source. | No. | May affect retry eligibility. | Diagnostics or retry policy. |
| Distance/progress signals | No. | Candidate with careful thresholds. | Candidate. | Candidate. | Future design, not Phase 9G-6A behavior. |
| Steps since global gain | No. | Too global for pair failure. | Candidate for episode-level stagnation. | No. | Diagnostics only for pair lifecycle. |
| Episode termination/reset | Ends episode. | No. | Yes at episode scope. | Clears all lifecycle. | Reset/clear source. |

Completion must remain tied to `viewpoints_covered` or an equally explicit env completion signal. Same-target repetition alone must not be treated as failure. A budget trigger can support an initial failure/timeout transition, but it must be named as a budget timeout/failure and remain pair-scoped. One robot failing a target must not mark that target globally failed.

## Observation Migration Plan

### Stage 1: Diagnostic / Playback Prototype

Lifecycle state may remain hidden only if it is passive diagnostics or disabled-by-default playback analysis. No training conclusions should be drawn from hidden lifecycle state.

### Stage 2: Disabled-By-Default Behavior Prototype

A behavior prototype may preserve old observation shape for fixed-checkpoint playback, but results must be interpreted as guardrail diagnostics. This can test whether a lifecycle resolver has mechanical effects, not whether a policy can learn it.

### Stage 3: Training-Ready Lifecycle

Training-ready lifecycle requires observation migration. Candidate fields:

| Field | Actor observation | Shared/critic observation | Reason |
| --- | --- | --- | --- |
| `robot_is_idle` | Yes. | Yes. | Needed to interpret noop and target actions. |
| `robot_is_executing` | Yes. | Yes. | Needed to distinguish continue from no assignment. |
| `active_target_one_hot` or embedding | Yes. | Yes. | Needed for continue/current target semantics. |
| `active_attempt_age` | Yes. | Yes. | Needed for timeout/failure risk. |
| `task_claimed` flag | Yes, per task. | Yes. | Needed to avoid choosing owned tasks. |
| `task_owner` relation | Possibly local relation; yes if exact ownership affects mask. | Yes. | Important for centralized value and teammate awareness. |
| `pair_failed/released` flag | Yes if it affects availability. | Yes. | Hidden failed-pair state would otherwise create non-Markov behavior. |
| `release/failure reason` encoding | Optional actor, useful shared. | Yes if behavior/reward depends on reason. | Supports explainability and credit assignment. |

Observation changes are deferred. They are required before training a persistent lifecycle policy.

## Available-Actions Contract

The action tensor shape can remain `[M, N+1]`, but the contents and semantics may become stateful.

| Lifecycle state | Possible available-actions rule | Shape preserved? | Semantic change? | Notes |
| --- | --- | --- | --- | --- |
| Idle | Open feasible targets plus noop. | Yes. | Minimal. | Closest to current behavior. |
| Executing | Only current active target plus noop. | Yes. | Yes. Target id means continue/switch constraints. | Keeps current target explicit but may force repeated selection. |
| Executing | Only noop, interpreted as continue. | Yes. | Yes. Noop becomes state-dependent. | Requires observation fields; can reduce action burden. |
| Executing | All targets available; selecting another target explicitly switches/releases old target. | Yes. | High. | Switching semantics must be designed before use. |
| Failed/released | Open targets excluding failed same-robot pair; teammate may still select released target. | Yes. | Yes. Pair-scoped stateful mask. | Must be visible before training. |
| Completed | Robot transitions to idle before next decision. | Yes. | Low. | Completion source remains `viewpoints_covered`. |

Recommended prototype rule for a future disabled behavior phase: idle robots see open feasible targets plus noop; executing robots continue active targets through the resolver, with Contract C noop-as-continue tested only after passive transition logging. Exact mask contents should not change in Phase 9G-6B if it is passive.

## Baseline Solver Contract

Baselines should not receive a different assignment MDP than RL. A lifecycle implemented only inside the RL wrapper would make baseline comparisons semantically inconsistent.

Recommended baseline contract:

- solvers may still be invoked every env step;
- the shared lifecycle resolver decides which robots are eligible for a new assignment;
- executing robots retain active assignments through the resolver;
- idle/released robots receive solver-selected targets;
- same-step conflicts are resolved by the shared arbitration rule;
- lifecycle state is exposed to baselines through a lifecycle-augmented problem or through the shared resolver interface;
- random, nearest, greedy, and RL all share the same ownership/release rules.

Calling solvers only for idle/released robots is conceptually clean but requires more invasive changes to solver interfaces. A shared resolver around existing solver outputs is the smaller integration path.

## Architectural Options

| Option | Semantic correctness | Effort | Behavior-change risk | Hidden-state risk | Checkpoint compatibility | Baseline comparability | Controller coupling | Testability | Variable M/N scalability |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A: wrapper-local ownership/action-latching prototype | Medium; RL-only unless duplicated. | Medium. | Medium-high when enabled. | High without observation changes. | Disabled playback compatible; enabled semantics differ. | Weak unless baselines get equivalent logic. | Low-medium through effective assignment. | Good fake-env tests. | Good if tensorized. |
| B: env-owned persistent lifecycle | High. | High. | High. | Lower if observations updated. | Requires new training for enabled behavior. | Strong if baselines use env state. | Medium; env/controller boundary must stay clean. | Requires env-level tests. | Good if designed with dynamic sizes. |
| C: shared lifecycle manager used by RL wrapper and baseline evaluation | High if later promoted or env-synchronized. | Medium. | Can start passive; behavior later. | Medium until observations migrate. | Good while passive/disabled. | Strong. | Low if it outputs effective assignment before controller. | Strong with pure unit tests. | Good. |
| D: hybrid passive logger, disabled wrapper prototype, then shared/env promotion | Highest staged safety. | Medium over phases. | Low first, then controlled. | Managed by observation migration gate. | Strong in passive/disabled phases. | Strong if shared manager is used early. | Low initially. | Strong. | Good. |

Recommended architecture: Option D, beginning with a shared passive lifecycle transition logger in Phase 9G-6B. This avoids a large env-level implementation while preventing an RL-wrapper-only lifecycle from becoming a divergent source of truth.

## Relationship To Current Failed-Pair Memory

The current failed-pair memory should remain disabled-by-default diagnostic/experimental guardrail code. It should not become a second source of pair failure state.

If a lifecycle is later implemented, the failed-pair memory concept can be folded into one of two roles:

1. a lifecycle-owned `pair_failed` / `released_temporarily_unavailable_to_same_robot` substate; or
2. a diagnostic-only comparison mechanism for measuring what pair-scoped suppression would have done.

It should not independently decide that a target is globally failed, and it should not mark targets covered. Completion remains tied to `viewpoints_covered`.

## Recommended Next Smallest Phase

Recommended next phase: Phase 9G-6B passive/shared lifecycle transition logger.

Purpose:

- reconstruct lifecycle transitions online from the same inputs used by wrapper and baseline paths;
- log ownership, active target, release, failure, and ambiguity events;
- do not change actions, masks, observations, rewards, controller commands, env dynamics, baselines, or HARL behavior;
- use this trace to validate transition contracts before any action-latching prototype.

Likely files to change in Phase 9G-6B:

- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_lifecycle.py` or `assignment_lifecycle_manager.py` as a new passive/shared manager.
- `scripts/environments/test_assignment_lifecycle_transition_logger_smoke.py` for fake problem/action sequences.
- Optionally `scripts/environments/evaluate_assignment_rl_playback_diagnostics.py` and `scripts/environments/evaluate_assignment_methods.py` only to attach passive diagnostics, not to change behavior.
- Phase 9G-6B report under `AgentRead/YYYYMMDD/`.
- `AgentRead/TASK_PROGRESS.md`.

States to add as passive proxy/logged states:

- robot: `idle_proxy`, `executing_proxy`, `released_proxy`, `reset_proxy`;
- task: `open_proxy`, `claimed_proxy`, `completed`;
- pair: `none`, `active_proxy`, `completed`, `failed_budget_proxy`, `released_proxy`, `timeout_proxy`;
- metadata: `active_target_id`, `owner_robot_id`, `attempt_start_step`, `attempt_age`, `failure_reason`, `release_reason`.

Transitions to log first:

- idle robot selects open target;
- executing robot repeats/continues target;
- robot selects noop while idle;
- robot selects noop while previously active, marked as ambiguous under current behavior;
- target becomes covered;
- target covered by teammate;
- budget failure proxy;
- release proxy;
- switch-target request;
- reset.

Disabled/default boundary:

- no behavior effect;
- no available-actions changes;
- no observation changes;
- no action semantics changes;
- no reward changes;
- no controller/env changes;
- no training.

Required smoke tests:

- deterministic fake sequence for start, continue, noop idle, noop while active, completion, teammate completion, budget failure, release, switch request, reset;
- same-step exact target conflict logging with lowest path-cost plus robot-id tie-breaker as proposed contract, without applying behavior;
- variable M/N shape coverage;
- confirmation that source available masks and assignments are not mutated;
- confirmation that logger output is diagnostic-only.

Playback should not be required for the first 9G-6B implementation if it is fake-sequence and diagnostics-only. Playback can be considered later only after the passive logger is reviewed and explicitly authorized. Observation changes are deferred. Training remains prohibited.

## Final Recommendation

Proceed with Phase 9G-6B as a passive/shared lifecycle transition logger interface. Do not jump directly to env-owned lifecycle behavior or wrapper-local action latching. The project needs a verified transition stream and source-of-truth interface before changing the MDP.

Selected contract direction:

- future behavior prototype should use Contract C, explicit continue semantics without new action ids, only after passive logger review;
- noop should mean idle/no assignment when idle and continue active target when executing, but only when the policy can observe the state distinction;
- release should not be overloaded onto noop in the first lifecycle design.

Selected source-of-truth direction:

- completion and physical state remain env-owned;
- lifecycle should be represented by a shared lifecycle manager first, with env promotion later if behavior becomes core environment semantics;
- controller remains a consumer of effective assignment, not owner of lifecycle.

Selected arbitration direction:

- use a centralized deterministic lowest-path-cost winner with robot-id tie-breaker for exact same-target claim conflicts;
- do not claim this solves nearby target conflicts, path overlap, or near-misses.

No training was run. No playback was run. No Python source files were modified in Phase 9G-6A.

## Validation

Allowed validation for this documentation-only phase:

```powershell
git status --short --untracked-files=all
git diff --check
```

Results are recorded in the final handoff response after the report and `TASK_PROGRESS.md` update.
