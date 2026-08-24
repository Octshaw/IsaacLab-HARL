# Phase B0 Pre-Reset Lifecycle Authority Runtime Design

## 1. Classification

```text
classification:
  PHASE-B0-DESIGN-COMPLETE-AWAITING-GPT-REVIEW

starting HEAD:
  912b3b59831fcad8dd29ac575b2a1851bf2c21d1

starting branch:
  main

starting worktree/index:
  clean / empty

Phase A:
  COMPLETE
  accepted at declared pure/static/manifest evidence level
  committed by user

B0:
  design complete
  implementation not authorized

B/C/D/E:
  not entered

contract/runtime gap:
  none requiring Phase-A contract revision

runtime event profile:
  still not implemented

runtime identity:
  still deferred

11 numeric TBDs:
  unresolved
```

This is a design-only result. No production Python, YAML, HARL, checkpoint,
resolver, environment behavior, or test was changed or executed. No Isaac,
training, playback, or evaluation process was started, and no commit was made.

The source audit found that the current runtime cannot itself be treated as a
valid B0 implementation. In particular, wrapper-side post-step reconstruction
is too late, current scan completion loses pair attribution, and the current
Contract-C resolver is a separate prototype authority. These are integration
constraints, not a required revision to the frozen Phase-A schemas: an
event-profile-only pre-reset producer and authority can satisfy the contracts.

## 2. Scope and Phase-A assumptions

This design implements rather than redefines the frozen split:

```text
ENV_EXECUTION_FACTS_PRODUCER_V1
  -> ExecutionTransitionFacts
  -> LIFECYCLE_AUTHORITY_V1
  -> LifecycleTransitionResult
  -> later event / assignment runtime
```

The following are treated as authoritative and unchanged:

- `ExecutionTransitionFacts` and `LifecycleTransitionResult` exact schemas,
  shapes, dtypes, producer/authority identities, alias isolation, generation,
  consume-once, token, and receipt semantics;
- `TaskLifecycleState`, `RobotLifecycleState`, and `TerminationReason` enum
  values and order;
- pair-attributed completion, forced release, and terminal failure;
- episode-cumulative structural failed pairs;
- `TEAM_INFEASIBLE` derivation only from all-robot permanent failed pairs;
- termination priority `ALL_TASKS_COMPLETED`, then
  `NO_FEASIBLE_TASKS_REMAIN`, then `TIME_LIMIT`, then `NONE`;
- terminal no-actor/no-proposal/no-forced-row/no-resolver behavior plus one
  finalized pre-reset centralized-critic sidecar;
- direct bypass for all four existing profiles;
- all eleven unresolved numeric method parameters.

Phase A established interfaces only. This design does not assume the existence
of a runtime producer, authority, scheduler, local set, cost estimator, Top-K,
DVM, component resolver, team reward, HARL sidecar transport, diagnostic sink,
or checkpoint-ready V3.

The current scan dwell/coverage calculation is a prototype execution signal,
not proof of a real terminal-alignment detector. B0 can define its owner-gated
adapter and validate it against the frozen contract; it must not claim real
robot/IK/collision completion evidence that the current skeleton does not
provide.

## 3. Current runtime execution/reset order

### 3.1 Exact current order

The actual current order is:

```text
HARL actor/value inference for the already-buffered observation
-> AssignmentHarlWrapper reads get_assignment_problem()
-> decode policy proposal
-> current Contract-C resolver resolve_pre_step()
   -> enabled route may immediately mutate prototype owner/pair state
-> effective assignment
-> AssignmentController maps task IDs to 9-D actions
-> DirectMARLEnv.step()
   -> _pre_physics_step()
      -> clone previous action
      -> clamp action
      -> mutate proxy base/scanner poses
   -> decimated physics/render/scene update
   -> increment episode_length_buf and common_step_counter
   -> ScanMobileManipulatorEnv._get_dones()
      -> _update_scan_progress()
         -> position/orientation/workspace/range/FOV candidate
         -> update dwell_counter
         -> form local new_candidate [E,M,N]
         -> split per-robot reward credit
         -> reduce to newly_covered [E,N]
         -> mutate viewpoints_covered in place
      -> all-covered termination
      -> time-limit truncation
   -> _get_rewards() from updated pre-reset buffers
   -> DirectMARLEnv._reset_idx(done envs)
      -> scene/reset events/noise/episode-length reset
      -> scan env overwrites physical/progress/action buffers
   -> interval events
   -> _get_observations() from reset/new-episode state for done rows
   -> return post-reset obs + pre-reset reward/done tensors
-> wrapper regains control
-> wrapper reads post_step_problem (already reset for done rows)
-> wrapper diagnostics/reward reconstruction
-> current resolver observe_post_step() and reset
-> wrapper diagnostic reset and wrapper-only episode-generation increment
-> wrapper builds augmented obs/shared obs/mask from post-reset problem
-> training facade discards wrapper infos before HARL insertion
```

Primary evidence:

- `source/isaaclab/isaaclab/envs/direct_marl_env.py:328-415` places dones and
  reward before autoreset and observations after autoreset.
- `scan_mobile_manipulator_env.py:2805-2843` mutates proxy physical state in
  `_pre_physics_step()`.
- `scan_mobile_manipulator_env.py:2930-2983` computes, reduces, and discards the
  pair-shaped scan candidate while mutating coverage.
- `scan_mobile_manipulator_env.py:3012-3020` computes all-covered and time-out.
- `scan_mobile_manipulator_env.py:3022-3047` performs in-place reset writes.
- `assignment_harl_wrapper.py:461-560` reads the post-step problem only after
  the environment has returned.

### 3.2 Information that is overwritten or ceases to be reliable

For done rows, `_reset_idx()` overwrites before the wrapper can inspect:

- `base_pos [E,M,3]`, `base_yaw [E,M]`;
- `scanner_pos [E,M,3]`, `scanner_quat [E,M,4]`;
- `viewpoints_covered [E,N]`;
- `dwell_counter [E,M,N]`;
- `last_global_coverage_gain [E]`;
- `last_own_coverage_gain [E,M]`;
- `last_duplicate_scans [E,M]`;
- `last_reach_violation [E,M]`;
- every agent's current and previous action tensors;
- base `episode_length_buf`, scene state, reset events, and noise-model state.

The exact `new_candidate [E,M,N]` is a method-local tensor and disappears even
on nonterminal steps. Only a task-level reduction and fractional reward credit
remain.

`get_assignment_problem()` also exposes live aliases for pose and coverage
tensors (`scan_mobile_manipulator_env.py:1722-1738`). The wrapper stores the
mapping at `assignment_harl_wrapper.py:466` without cloning it. Therefore its
later `covered_before` reads are not an immutable pre-step snapshot: by the time
they are used, the tensor has been mutated by scan progress or reset.

The environment contains no authoritative `current_assignment` or
`effective_assignment` tensor. Those identities exist in the wrapper/current
resolver, while controller conversion to continuous actions is non-invertible:
noop, invalid, covered, and infeasible assignments can all become zero actions.
An environment hook cannot reconstruct ownership from those actions.

### 3.3 Current wrapper/HARL storage boundary

The returned reward and done tensors are calculated before reset, but returned
observations/shared observations for done rows are new-episode state. The
wrapper ORs terminated and truncated into one done tensor and the training
facade returns empty per-agent `infos`. Current HARL therefore has neither the
final termination reason nor a pre-reset centralized state; the ordinary
`t+1` shared observation is the reset state.

## 4. Current lifecycle-relevant state inventory

| Concept | Current storage/producer | Current limitation |
|---|---|---|
| Task completion | env `viewpoints_covered [E,N]` | global proxy only; pair edge discarded; reset in place |
| Task state | ephemeral `task_status` in `get_assignment_problem()` | only unassigned/completed proxy; not persistent |
| Robot state | ephemeral all-`ROBOT_IDLE` tensor | placeholder; no availability lifecycle |
| Current task | resolver `active_target_id [E,M]` | Contract-C prototype only |
| Task owner | resolver `task_owner_robot_id [E,N]` | Contract-C prototype; immediate mutation |
| Failed pair | resolver `pair_state [E,M,N]` plus wrapper TTL memory | budget/release heuristic, not structural cumulative failed pair |
| Completion count | wrapper `_per_robot_completed_count` | diagnostic/fractional reconstruction; reset after autoreset |
| Workload | wrapper counters | not authoritative and not pair-exact |
| Termination | all-covered/time-out booleans | no frozen reason tensor |
| Episode generation | wrapper `_lifecycle_episode_generation` | wrapper-only and advanced after autoreset |
| Transition generation | none | not implemented |
| Consume token/receipt | none | not implemented |
| Assignment-tick generation | none | not implemented |
| Terminal critic sidecar | none | post-reset shared observation only |

`assignment_state.py` defines legacy constants and a counting helper but owns no
state tensor. `assignment_initial_condition.py` owns immutable playback/reset
pose identity, not transition or lifecycle state. The current lifecycle
observation module is a Contract-C decision-snapshot builder and cannot be
renamed or reused as the B0 authority.

## 5. Identified integration hazards

1. **Autoreset precedes wrapper inspection.** Any wrapper-after-step facts
   producer is necessarily post-reset for terminal rows.
2. **The wrapper's apparent pre-step mapping aliases live environment state.**
   It is not a safe snapshot even before considering autoreset.
3. **Current completion is reduced too early.** Multiple robots may satisfy one
   task, credit is split, robot-task attribution is discarded, and global
   coverage is mutated before authority.
4. **Assignment identity is outside the environment.** Continuous control
   actions cannot be inverted to recover owner/current task.
5. **The current resolver is a second, incompatible prototype authority.** It
   immediately mutates owner/pair state, uses budget failure, resets its step
   counter, and has no frozen generation/token/receipt contract.
6. **Structural failure, forced release, and robot health edges have no current
   physical producer.** They need typed execution reporter ports; wrapper
   budget heuristics must not stand in for them.
7. **Current termination distinction is lost downstream.** Done is OR-reduced
   and infos are discarded.
8. **No terminal physical/lifecycle state survives reset.** A sidecar must be
   materialized before `_reset_idx()` and own its storage.
9. **The event profile is intentionally unreachable.** It remains
   `INTERFACE_ONLY`, is rejected before `gymnasium.make`, and its aggregate
   descriptor freezes runtime execution as unauthorized. B0 foundation code
   must remain dormant and must not globally flip readiness.
10. **The result factory validates schema-level invariants but not the complete
    lifecycle algorithm.** B0 authority and tests must separately enforce the
    failed-pair, TEAM_INFEASIBLE, release, state-transition, event, and
    termination equations.

## 6. Candidate authority placements

| Option | Pre-reset correctness | Ownership clarity | Isaac reset compatibility | Coupling/testability | Isolation and future integration | Assessment |
|---|---|---|---|---|---|---|
| A. Inline producer and authority directly in `ScanMobileManipulatorEnv` | correct if called in `_get_dones()` | producer/authority roles can become entangled | compatible | high env coupling; most tests would need env-shaped fixtures | event branch possible, but shared-file edits raise regression risk | viable but not preferred |
| B. Wrapper after `_env.step()` | incorrect for terminal rows | duplicates reconstruction in wrapper | incompatible with current autoreset | easy to code but semantically untestable at terminal | risks reusing old resolver and post-reset state | rejected |
| C. Dedicated transition adapter called only by wrapper | still too late unless env calls it | clearer component | incompatible if wrapper-only | pure-testable | future integration possible | rejected as wrapper-only |
| D. Dedicated event-profile coordinator owned/invoked by the environment at `_get_dones()`, with capability-limited ports for future wrapper/controller readers | correct | unique producer, authority, store, and mailbox are explicit | compatible; artifacts outlive reset | pure core plus narrow env hook | best default-off isolation and B/C handoff | **recommended** |

A full override of `DirectMARLEnv.step()` is not recommended. It would duplicate
upstream Isaac ordering and make future base-class drift a hidden correctness
risk. `_reset_idx()` alone is also insufficient because it runs only on reset
transitions and pair completion has already disappeared.

## 7. Recommended B0 architecture

### 7.1 Component placement

Add one repo-local, event-profile-only `AssignmentLifecycleRuntimeCoordinator`
composed of four capability-separated parts:

```text
ExecutionSignalInbox
  reporters: scan/controller/health adapters
  writer authority: raw reporters only
        |
        v
EnvironmentExecutionFactsProducer
  identity: ENV_EXECUTION_FACTS_PRODUCER_V1
  only public facts-construction capability
        |
        v
LifecycleAuthorityRuntime + LifecycleStateStore + TransitionConsumeLedger
  identity: LIFECYCLE_AUTHORITY_V1
  only lifecycle/result/state writer
        |
        +--> immutable LifecycleTransitionResult
        +--> terminal critic sidecar when terminal
        +--> TransitionAuthorityDiagnostic envelopes in memory
        v
PreResetTransitionMailbox
  read/acknowledge only for later event facade/runner
```

The coordinator is constructed only from the exact
`ResolvedEventGatedAssignmentProfile` subtype. Existing profile subtypes are
rejected by its constructor. Conversely, the existing wrapper/resolver routes
never construct or call it.

For future integration, the same coordinator object is injected into the
event-specific environment/facade path. Ports prevent the wrapper from calling
the producer or ledger directly:

- environment receives the producer/finalize/reset port;
- future Phase-B resolver receives a staged-commit request port, not writable
  tensor access;
- future wrapper/HARL adapter receives only immutable handoff read/ack ports;
- diagnostics receives clone/summary access only.

### 7.2 Proposed physical-step order

```text
event wrapper/controller arms exact execution context for generation g
-> _pre_physics_step / physics
-> scan/controller/health reporters form raw execution edges
-> event-specific _get_dones()
   -> compute completion candidate without global completion mutation
   -> freeze pre-event lifecycle/ownership snapshot
   -> ENV_EXECUTION_FACTS_PRODUCER_V1 builds one facts batch
   -> pure authority derives candidate next state with no mutation
   -> TransitionConsumeLedger atomically consumes facts once
   -> LIFECYCLE_AUTHORITY_V1 finalizes one result batch
   -> atomically commit lifecycle state/counters
   -> finalize termination projection
   -> if terminal, build and retain pre-reset critic sidecar
   -> publish immutable transition handoff
   -> commit environment coverage/reward bookkeeping from authoritative result
   -> return terminated/truncated projection
-> _get_rewards() from committed same-transition state
-> DirectMARLEnv autoreset
   -> mailbox and sidecar survive
   -> episode-local lifecycle state rebuilt and episode generation advances
-> base computes new-episode observations
-> future event facade reads and acknowledges exactly generation g handoff
```

There is one physical transition and one facts/result pair. The authority call,
event collection, terminal sidecar, and future assignment tick are synchronous
logic within or between physical steps; none is an extra environment step.

### 7.3 Ownership/dataflow diagram

```text
physical execution reporters
        |
        v
environment facts producer -- no lifecycle mutation
        |
        v
ExecutionTransitionFacts -- immutable, one batch, one token per row
        |
        v
single lifecycle authority/state store
        |
        +--> LifecycleTransitionResult / a0
        +--> lifecycle events
        +--> terminal sidecar
        |
        v
later B scheduler/local set/component resolver
        |
        v
staged commit request back through the single state-store boundary
```

## 8. `ExecutionTransitionFacts` producer

### 8.1 Exact producer point

The unique producer runs once per full vectorized physical transition inside
the event-specific `_get_dones()` path, after physical execution and raw scan
detection, but before any authoritative task completion is committed and before
control returns to `DirectMARLEnv.step()` where `_reset_idx()` may run.

The current `_update_scan_progress()` must be separated for the event route:

```text
detect physical scan/alignment inputs
-> build canonical owner-gated completion edge
-> capture/consume/finalize lifecycle transition
-> commit coverage and reward bookkeeping from finalized result
```

The existing four profiles continue to call the current detection/reduction/
mutation path unchanged.

### 8.2 Exact field-source table

`E` is the full vectorized batch, `M` fixed robots, and `N` fixed tasks. All
tensors are on the declared environment device and are passed to the frozen
factory, which performs `detach().clone().contiguous()` and exact dtype/shape
validation.

| Frozen field | Runtime source | Capture timing | Shape/dtype | Single owner | Temporal class |
|---|---|---|---|---|---|
| `schema_version` | frozen constant `execution_transition_facts_v1` | construction | scalar `str` | producer | static |
| `producer_contract_version` | frozen producer stamp | construction | scalar `str` | producer | static |
| `producer_id` | exact `ENV_EXECUTION_FACTS_PRODUCER_V1` stamp | construction | string enum | producer | static |
| `env_id` | stable vector env row IDs, canonical ascending order | construction | `[E] int64` | producer clock/context | transition identity |
| `episode_generation` | coordinator generation clock, current old-episode value | before any reset | `[E] int64` | generation clock | pre-reset/current episode |
| `transition_generation` | next process-lifetime generation reserved for each row | facts construction; committed on finalization | `[E] int64` | generation clock | this physical transition |
| `physical_terminated` | environment raw physical-terminal proposal; current skeleton source is all physically completed scan tasks | after raw execution detection | `[E] bool` | producer | post-physical/pre-lifecycle |
| `physical_truncated` | environment raw truncation classifier | after counter increment | `[E] bool` | producer | post-physical/pre-lifecycle |
| `time_limit_reached` | exact horizon comparison currently made in `_get_dones()` | after counter increment | `[E] bool` | producer | post-physical/pre-lifecycle |
| `bad_transition` | explicit environment truncation/bootstrap classifier; for the current only-truncation-is-time-limit skeleton, equal to the time-limit edge, with transport deferred to D | same time as truncation | `[E] bool` | producer | raw runtime fact |
| `completion_signals` | one canonical current-owner/current-task alignment-success edge from the execution completion adapter | after low-level predicates/dwell edge, before global coverage commit | `[E,M,N] bool` | producer | post-physical/pre-lifecycle |
| `terminal_pair_failure_signals` | typed structural terminal failure reporter inbox only; never budget/stall/path-invalid inference | before facts freeze | `[E,M,N] bool` | producer drains reporters | post-physical/pre-lifecycle |
| `forced_release_signals` | typed execution/system forced-release reporter inbox | before facts freeze | `[E,M,N] bool` | producer drains reporters | post-physical/pre-lifecycle |
| `robot_unavailable_signals` | typed robot-health falling-edge reporter | before facts freeze | `[E,M] bool` | producer drains reporter | post-physical/pre-lifecycle |
| `robot_recovered_signals` | typed robot-health recovery-edge reporter | before facts freeze | `[E,M] bool` | producer drains reporter | post-physical/pre-lifecycle |
| `coverage_before_reset` | prospective final physical coverage for this transition, computed without aliasing resettable storage and committed only after result finalization | after canonical completion edge, before reset | `[E,N] bool` | producer | post-physical/pre-reset |
| `task_state_before_transition` | immutable authority-state snapshot supplied to the producer port | before applying this transition's event mutations | `[E,N] int64` | state store writes; producer reads | pre-event baseline |
| `robot_state_before_transition` | immutable authority-state snapshot | before applying availability/release/completion effects | `[E,M] int64` | state store writes; producer reads | pre-event baseline |
| `ownership_before_transition` | immutable canonical task-owner snapshot | before applying this transition's events | `[E,N] int64` | state store writes; producer reads | pre-event baseline |
| `consume_once_token` | separate non-RNG producer counter, allocated per row and never reset | facts construction | `[E] int64` | producer | this facts instance |

The raw object contains no final termination reason, TEAM_INFEASIBLE, updated
state, release result, failed-pair result, lifecycle event, or receipt.

### 8.3 Reporter versus producer distinction

Multiple low-level components may report typed raw edges into the inbox, but
only the environment producer can construct `ExecutionTransitionFacts`.
Reporter tensors are not facts objects, cannot allocate generation/token, and
cannot finalize lifecycle state. Missing capabilities in the current scan
skeleton use an explicit no-event reporter (all false) only because that
skeleton cannot produce those events; this is not evidence that structural
failure or robot recovery has been runtime-validated.

## 9. Lifecycle authority runtime

The authority consumes exactly one facts batch and produces exactly one result
batch per physical step. It does not reuse `AssignmentLifecycleResolver` or
`AssignmentLifecycleResolverRuntimeAdapter`.

Recommended no-partial-mutation algorithm:

1. Validate coordinator/profile/context identity and facts integrity.
2. Clone the prior state-store tensors and counters into a candidate state.
3. Validate the complete signal conflict/owner/cardinality matrix.
4. Derive completion, release, new failed pairs, availability, ownership, task
   state, robot state, workload, TEAM_INFEASIBLE, events, and termination in
   candidate storage only.
5. Assert all B0 semantic equations not enforced by the result factory.
6. Ask `TransitionConsumeLedger` to atomically consume the full batch using
   exact per-row generation expectations.
7. Receive the immutable receipt; finalize the result through
   `LifecycleTransitionResultFactory` with the canonical authority stamp.
8. Only after successful result finalization, atomically swap candidate state
   into the state store, commit transition generations, construct diagnostics
   and any terminal sidecar, and publish the immutable handoff.

If finalization fails after a ledger receipt is issued, the process fails
closed; it must not retry that physical transition or partially mutate state.

The event-updated `updated_ownership` in the result is baseline `a0`. A future
Phase-B component resolver returns a staged commit request; the state store
applies the accepted request through one narrow atomic method. The resolver
does not receive writable ownership storage and cannot amend the already
finalized transition result.

## 10. Completion attribution

### 10.1 Canonical completion predicate

The current all-pairs `new_candidate` cannot be copied into facts. For the event
route, one execution completion adapter evaluates only the robot's canonical
current task and emits an edge when all required terminal-alignment conditions
and dwell-edge semantics hold:

```text
completion_signals[e,i,j] =
    canonical_alignment_success_edge[e,i,j]
    AND ownership_before_transition[e,j] == i
    AND current_task_from_ownership[e,i] == j
    AND task j is not already terminal
```

The current position/orientation/workspace/range/FOV/dwell predicates may feed
this adapter in a controlled skeleton test, but are explicitly labeled a
prototype completion source. A real IK/collision/alignment completion source
remains implementation evidence to be established later.

### 10.2 Exact attribution retained

For every completion, the authority retains:

- completion occurred: `completion_signals[e,i,j] == true`;
- completing robot: pair index `i`;
- completed task: pair index `j`;
- previous owner: `ownership_before_transition[e,j]`, which must equal `i`;
- task-level result: `completed_tasks[e,j]`;
- durable attribution: `TASK_COMPLETED` lifecycle event with
  `cause_robot_id=i` and authoritative completion/workload increment for `i`.

Only after this attribution and result finalization may the event route project
the task into `viewpoints_covered`/`COMPLETED`. A task never becomes merely
globally complete first.

### 10.3 Multiple apparent completion signals

Individual geometric/sensor/controller predicates are ingredients of one
canonical composite detector, not independent completion producers. Passive
non-owner scan candidates remain execution diagnostics and do not become
completion facts. If more than one owner-qualified robot-task edge survives
for the same task, an edge does not match the owner/current-task snapshot, or
two canonical detectors disagree, facts construction fails before coverage or
lifecycle mutation. No lowest-ID winner, reward-credit split, or wrapper
reconstruction is permitted.

Recommended simultaneous-cause rule for review:

- same-pair completion plus terminal failure: frozen contract error;
- completion plus forced release/unavailability for the completed task:
  completion is the terminal task outcome; robot availability still changes,
  but no redundant task-release event is emitted;
- terminal failure plus explicit forced release for the same pair: one release
  result/event, plus the distinct new-failed-pair event;
- all other ambiguous cause combinations: fail closed before consume.

## 11. Release, failure, and availability handling

### 11.1 Forced release

A true `forced_release_signals[e,i,j]` must match owner `i`. For a nonterminal
task, the authority:

- sets owner to `-1`;
- sets `released_tasks[e,j]`;
- returns task to `AVAILABLE` unless another same-transition terminal rule
  applies;
- sets the robot to `NEEDS_ASSIGNMENT` unless it is `UNAVAILABLE` or the
  terminal branch leaves no real assignment choice;
- emits one `TASK_RELEASED` and, when applicable, one
  `ROBOT_NEEDS_ASSIGNMENT` lifecycle event.

It does not mark a failed pair.

### 11.2 Structural terminal pair failure

Only a typed structural terminal signal can set a permanent failed pair:

```text
new_failed_pairs =
  terminal_pair_failure_signals & ~prior_failed_pairs

updated_failed_pairs =
  prior_failed_pairs | new_failed_pairs
```

The authority releases the owned task, emits
`TERMINAL_PAIR_FAILURE_RECORDED`, emits the corresponding task release and
robot-needs-assignment transitions as applicable, and then derives
TEAM_INFEASIBLE. Current budget exhaustion, cooldown, temporary stall,
temporary obstacle/path invalidity, or Contract-C `PAIR_FAILED_BUDGET` /
`PAIR_RELEASED_BUDGET` cannot enter this path.

### 11.3 Robot unavailable/recovered

An unavailable edge:

- changes the robot to `UNAVAILABLE`;
- releases every nonterminal task it owns through the same authority
  transaction;
- prevents a decision-valid assignment later;
- emits `ROBOT_BECAME_UNAVAILABLE` plus task-release events.

A recovery edge is valid only against the prior unavailable state. Because B0
unavailability releases ownership, the recovered robot normally becomes
`NEEDS_ASSIGNMENT`; a later phase may validate the frozen legal-EXECUTING
recovery case only if ownership was intentionally retained by an explicitly
approved rule. `ROBOT_RECOVERED` remains a transient event, not a stored state.

Robot unavailable and recovered cannot coexist in one transition. Health
reporters propose edges; only the lifecycle authority changes robot state.

## 12. Cumulative failed-pair handling

`updated_failed_pairs [E,M,N]` is owned by the lifecycle state store, not the
resolver, wrapper, observation builder, or logger. It is cloned as
`prior_failed_pairs` for candidate derivation and exposed in each finalized
result. It:

- is monotonic within an episode;
- ignores duplicate structural reports (`new_failed_pairs` remains false for a
  previously failed pair);
- clears only during episode-state rebuild in `_reset_idx()`;
- is never cleared by task completion, release, recovery, retry, or resolver
  commit;
- is the only failed-pair input to TEAM_INFEASIBLE and later masks.

## 13. TEAM_INFEASIBLE boundary

B0 can and must derive exactly:

```text
task j becomes TEAM_INFEASIBLE iff
  task j is not COMPLETED
  AND all robots i have updated_failed_pairs[e,i,j] == true
```

`new_team_infeasible_tasks` is the edge from not-team-infeasible to this state.
The authority clears ownership before finalizing `a0` and emits
`TASK_BECAME_TEAM_INFEASIBLE`.

B0 cannot infer TEAM_INFEASIBLE from:

- all current nominal paths being invalid;
- an empty later local set or Top-K;
- current budget/cooldown state;
- temporary obstruction or controller stall;
- the absence of a Phase-B candidate/cost implementation.

Phase B owns transient path-valid/cost/candidate evidence. Phase D owns final
learner/metric transport. Neither may redefine the B0 permanent failed-pair
equation.

## 14. Termination semantics

### 14.1 Proposal versus final authority

The environment producer records raw `physical_terminated`,
`physical_truncated`, `time_limit_reached`, and `bad_transition`. It does not
write a lifecycle reason. After all state mutations, the lifecycle authority
freezes exactly one reason per env in this priority:

```text
if all updated tasks are COMPLETED:
    ALL_TASKS_COMPLETED
elif all updated tasks are in {COMPLETED, TEAM_INFEASIBLE}:
    NO_FEASIBLE_TASKS_REMAIN
elif time_limit_reached:
    TIME_LIMIT
else:
    NONE
```

Then the event environment projects the finalized reason to Isaac/Gym done
channels:

```text
ALL_TASKS_COMPLETED or NO_FEASIBLE_TASKS_REMAIN:
  terminated = true
  truncated = false

TIME_LIMIT:
  terminated = false
  truncated = true

NONE:
  terminated = false
  truncated = false
```

If physical termination/truncation is true but the updated state maps to
`NONE`, or if an unsupported non-time-limit truncation appears, the transition
fails closed. No `OTHER` reason may be invented. If completion and time limit
occur together, the frozen priority preserves the raw time-limit fact but
finalizes the completion reason and terminal projection.

### 14.2 Phase boundary

B0 freezes and exposes the reason before reset. Phase D later carries that
reason and `bad_transition` through the environment facade to HARL proper-time-
limit/bad-mask logic. B0 does not change GAE, masks, returns, or training.

## 15. Terminal pre-reset critic sidecar

### 15.1 Capture point and content

For every row whose finalized reason is not `NONE`, the coordinator builds the
sidecar immediately after result/state finalization and before `_get_dones()`
returns. It uses cloned pre-reset physical tensors plus the finalized lifecycle
state; `_reset_idx()` never owns or clears it.

The B0 sidecar batch is recommended to carry:

```text
schema/contract identity
terminal_env_ids [K] int64
episode_generation [K] int64
transition_generation [K] int64
facts_consume_token [K] int64
authority_receipt_id [K] int64
termination_reason [K] int64
centralized_shared_state [K,S] float32
```

`centralized_shared_state` follows the frozen terminal shared-state contract:

- final pre-reset global robot physical table (base/scanner pose and fixed
  capability columns);
- final task poses;
- finalized task/robot lifecycle one-hots;
- final `a0` ownership/current-task projection;
- cumulative failed-pair mask;
- authoritative per-robot completion workload;
- final episode progress and termination reason;
- path/cost blocks zero with false validity;
- local-set blocks false;
- target/noop masks false;
- assignment tick absent and DVM false.

It contains no actor identity row, action, proposal, log probability, resolver
result, component, reward sample, or reset-state alias.

### 15.2 Lifetime and later HARL transport

The pre-reset mailbox owns sidecar storage until the event facade/runner
acknowledges the exact transition generation. Overwrite before acknowledgement,
double read, generation mismatch, or reset-time deletion is a typed failure.

Later B/C integration attaches the sidecar to the already-existing physical
transition row as an alternate terminal/bootstrap shared state:

```text
one reward/done/action transition row at t
+ optional terminal_pre_reset_share_obs sidecar for that same row
!= append a t+1 physical transition
```

The runner may evaluate/store the sidecar for correct terminal/time-limit
handling, but it must not append an actor row, proposal row, forced row, reward
row, critic-loss sample, or extra discount step. The ordinary returned post-
reset observation remains the initial observation of the next episode. Exact
buffer/GAE transport is deferred to C/D.

## 16. Episode, transition, token, receipt, and tick generations

There is no separate public `facts_generation`; facts carry episode and
transition generations.

| Counter/identity | Initial convention | Increment | Reset behavior | Owner |
|---|---|---|---|---|
| `episode_generation` | internal `-1`; first reset exposes episode `0` | once at each explicit/autoreset episode rebuild, after old terminal handoff is safe | never decremented; episode-local state rebuilt | coordinator generation clock |
| `transition_generation` | internal `-1`; first finalized physical transition is `0` | once per env row per finalized physical transition | never reset across episodes | coordinator generation clock |
| `consume_once_token` | internal `-1`; producer allocates next nonnegative token | once per facts row construction; non-RNG | never reset | facts producer |
| `authority_receipt_id` | ledger-defined per-env first successful receipt is `1` | once per successful atomic consume, following frozen collision-avoidance rule | never reset | consume ledger |
| `assignment_tick_generation` | internal `-1` means no tick yet/not applicable | later B increments once per canonical merged tick; overlapping triggers share it | process-lifetime monotonic; B0 never increments it | central generation clock through later scheduler port |

Detailed transition sequence:

```text
producer reserves transition generation g and token q
-> facts carries episode p, transition g, token q
-> authority supplies expected (env,p,g) to ledger
-> ledger atomically issues receipt r bound to (p,g,q)
-> result factory copies p,g,q and r
-> state and transition clock commit only with finalized result
-> reset, if any, advances episode p -> p+1 after sidecar publication
```

Stale, duplicate, future, wrong-env, wrong-episode, wrong-token, wrong-producer,
or wrong-authority input fails before state mutation. A result cannot be
created without the issued receipt.

## 17. Reset/autoreset ordering

### 17.1 Automatic reset

Current Isaac direct autoreset is not optional: done rows are reset inside
`DirectMARLEnv.step()` before the wrapper regains control. The viable handshake
is therefore:

```text
facts/result/termination finalized in _get_dones()
-> terminal sidecar + handoff own cloned storage
-> _get_rewards()
-> subclass _reset_idx(done envs) enters
   -> assert terminal handoff exists for each autoreset row
   -> close old episode and rebuild lifecycle episode state
   -> advance episode generation exactly once
   -> call base/scan physical reset
   -> do not clear old transition handoff/sidecar
-> post-reset observations
```

The exact lifecycle reset rebuild is:

- task states to `AVAILABLE` for nonterminal scenario tasks;
- robot states to the initial availability-derived state, normally
  `NEEDS_ASSIGNMENT` in the current static-health skeleton;
- ownership to `-1`;
- cumulative failed pairs false;
- completion/workload/needs-assignment duration counters zero;
- termination reason `NONE`;
- episode-local event/retry state cleared;
- episode generation advanced;
- transition generation, producer token, receipt, and assignment-tick
  generation not reset.

Tasks must not be marked TEAM_INFEASIBLE merely from static/path feasibility at
reset.

### 17.2 Explicit reset

An explicit reset with no preceding physical transition increments episode
generation and rebuilds episode-local state but creates no fake facts, result,
reward row, or terminal sidecar. An explicit reset while a physical transition
is armed or a handoff is unacknowledged fails closed unless the caller uses an
explicit reviewed cancellation/close protocol. Initial reset follows the same
rule and establishes episode generation zero.

### 17.3 Snapshot lifetime

Facts and results already clone their input tensors through frozen factories.
The sidecar and handoff must additionally clone every resettable physical
source before `_reset_idx()`. Static task/capability tensors may be referenced
only while constructing the final sidecar tensor; the stored sidecar itself is
no-alias. The mailbox, not the environment reset buffers or wrapper, owns the
artifact lifetime.

## 18. State ownership table

| State | Single owner | Readers | Writer(s) | Reset behavior | Update timing |
|---|---|---|---|---|---|
| Task lifecycle state `[E,N]` | `LifecycleStateStore` | facts producer snapshot, sidecar, later B observation/resolver | lifecycle authority; future resolver submits commit request but store performs write | `AVAILABLE` baseline; no path-derived infeasible | after facts consume; future claim commit through same store |
| Robot lifecycle state `[E,M]` | `LifecycleStateStore` | producer snapshot, sidecar, later scheduler/observation | lifecycle authority only | initial health-derived state | completion/release/availability transaction |
| Task owner `[E,N]` | `LifecycleStateStore` | producer, sidecar, later resolver/controller | lifecycle authority state-store API only | all `-1` | event release/completion or future atomic resolver commit |
| Robot current task `[E,M]` | derived inverse view of task owner, not independent storage | controller, observation, completion adapter | no independent writer; state-store projector | all `-1` | recomputed after each atomic ownership change |
| Cumulative failed pair `[E,M,N]` | `LifecycleStateStore` | authority, sidecar, later mask/cost/resolver | lifecycle authority only | all false | structural failure before TEAM_INFEASIBLE |
| Completion count `[E,M]` | `LifecycleStateStore` | workload projector, sidecar, diagnostics | lifecycle authority from pair completion only | zero | same completion transaction |
| Workload counters | `LifecycleStateStore` | sidecar, later observation/diagnostics | lifecycle authority only | zero | from finalized attributed lifecycle results |
| Termination reason `[E]` | `LifecycleStateStore` current finalized row | env done projection, sidecar, later D | lifecycle authority only | `NONE` | last step after updated task state |
| Episode generation `[E]` | central generation clock | producer/result/events/mailbox | reset handshake only | increment, never zeroed by later resets | once per episode rebuild |
| Transition generation `[E]` | central generation clock | producer/ledger/result/events/mailbox | coordinator finalize path only | never reset | once per finalized physical transition |
| Assignment-tick generation `[E]` | central generation clock | later B/C artifacts/diagnostics | later scheduler through clock port | never reset | no B0 increment; once per future merged tick |

Diagnostic counters are read-only consumers of finalized artifacts and cannot
feed lifecycle state. Logger/file sinks are not state owners.

## 19. Existing-profile/default-off isolation

The four existing profiles remain exactly on their current routes:

```text
legacy
lifecycle_contract_c
lifecycle_ablation
diagnostics_hidden_state
```

They continue to use their existing wrapper, observations, masks, current
resolver settings, rewards, HARL sequence, checkpoint V2 identity, logging, and
side effects. They do not construct the B0 coordinator, arm a transition, call
the B0 `_get_dones()` path, publish a sidecar, or produce B0 diagnostics.

The new B0 coordinator rejects `ResolvedExistingAssignmentProfile` by exact
type. The event route does not reuse current Contract-C resolver state,
`assignment_lifecycle_observation.py`, wrapper cooldown/budget failure, or
`assignment_state.py` constants.

### 19.1 Readiness remains fail-closed

During all B0 implementation slices:

- event profile remains `EVENT_GATED_PHASE_A_INTERFACE_ONLY`;
- runtime readiness remains `INTERFACE_ONLY`;
- normal training/playback support remains blocked;
- `require_assignment_profile_runtime_ready()` continues to reject the event
  subtype before `gymnasium.make`;
- event schema continues to say all eleven parameters unresolved and runtime
  execution unauthorized;
- V3 remains interface-only and weight use remains blocked.

Thus B0 code is dormant/default-off in production entrypoints and can be
validated first through pure components, fake hooks, and only a separately
authorized event-environment B0 harness.

### 19.2 Future atomic readiness switch

The full event route may open only in one reviewed atomic package after all
required B0/B/C/D runtime gates and numeric owners are ready. That package must
change and cross-check together:

- event runtime-route identity and profile readiness/support;
- `require_assignment_profile_runtime_ready()` event branch;
- event-specific environment/facade/wrapper dispatch;
- same-object coordinator/profile propagation;
- aggregate runtime-readiness projection and new V3 checkpoint-ready identity;
- training/playback/checkpoint guards appropriate to the then-authorized scope.

Changing only a registry literal, weakening the current helper, routing the
event subtype through old booleans, or using the B0 foundation as proof that
B/C/D are ready is prohibited.

## 20. Diagnostic producer boundary

B0 first makes `TRANSITION_AUTHORITY` genuinely producible. Immediately after
successful result finalization, the coordinator may construct one in-memory
`DiagnosticEnvelope` per env with:

- exact facts/result versions;
- exact producer and authority IDs;
- consume token and real receipt ID;
- `FIRST_CONSUME` status;
- generation/producer/authority match true from the validated artifacts;
- pair-attribution contract and validation status;
- observable immutability contract version;
- `assignment_tick_generation=-1` because B0 has no tick.

No sink, info key, TensorBoard key, file, directory, JSONL, CSV, or logger is
created.

The diagnostic schema requires a receipt ID even for failure status values,
while duplicate/stale/future failures issue no receipt. B0 therefore produces
the payload only for successful `FIRST_CONSUME`; typed exceptions remain the
failure evidence. It does not invent receipt ID zero or another sentinel.

`ASSIGNMENT_TICK` is a monolithic later-phase payload and cannot be partially
filled merely because B0 knows failed-pair counts or termination. It remains
`DEFINED_NOT_PRODUCED`, as do proposal, actor-update, team-reward, and later
runtime diagnostics. Profile/checkpoint/default-off diagnostics keep their
existing Phase-A availability; B0 does not reinterpret them.

## 21. Proposed implementation files

No file in this section is modified by this design pass.

Recommended additions:

- `assignment_lifecycle_authority_runtime.py` — coordinator, producer port,
  state store, generation clock, authority derivation, mailbox;
- `assignment_terminal_critic_sidecar.py` — terminal-only shared-state builder
  and immutable sidecar batch;
- `scripts/environments/test_assignment_phase_b0_lifecycle_authority_pure.py`;
- `scripts/environments/test_assignment_phase_b0_pre_reset_hook_pure.py`;
- later, only under explicit Isaac authorization,
  `scripts/environments/test_assignment_phase_b0_isaac_smoke.py`.

Recommended later B0 modifications:

- `scan_mobile_manipulator_env.py` — event-only detection/finalize/reset hook;
- a narrow event handoff/facade module, preferably new rather than expanding
  the existing-profile wrapper path;
- `assignment_harl_wrapper.py` only if a reviewed event-specific branch can be
  added without weakening the existing pre-`gymnasium.make` barrier;
- `TASK_PROGRESS.md` and the B0 implementation report in the authorized slice.

Frozen contracts should be consumed unchanged:

- `assignment_profile_contract.py`;
- `assignment_lifecycle_transition_contract.py`;
- `assignment_event_contract.py`;
- `assignment_mrta_contract.py`;
- `assignment_event_profile_schema_contract.py`;
- `assignment_event_gated_diagnostics_contract.py`.

Any need to change their field order, enum, equation, version, or readiness
projection during a B0 foundation slice is a stop for GPT/user review.

## 22. Proposed pure tests

At minimum, pure/fake-runtime tests must cover:

1. exact facts fields, shape/dtype/device, producer identity, no derived fields;
2. one full-batch facts/result pair per physical transition;
3. correct first consume, receipt, and exact generation/token binding;
4. duplicate/stale/future/wrong-env/wrong-episode/wrong-token/wrong-authority
   fail before state mutation;
5. batch atomicity when one row is invalid;
6. completion cardinality, owner attribution, previous-owner event attribution,
   and completion/failure conflict;
7. no task-level coverage commit before pair attribution/result finalization;
8. forced release without failed-pair mutation;
9. structural failure delta/cumulative equations and duplicate signal behavior;
10. robot unavailable release and recovery transition;
11. TEAM_INFEASIBLE only after cumulative failed-pair update;
12. nominal path invalidity never creates TEAM_INFEASIBLE;
13. all four termination reasons and exact priority, including completion plus
    time limit;
14. unmappable physical terminal/truncation fail closed;
15. canonical lifecycle event IDs, ordinal ordering, payload IDs, source,
    authority, token, and trigger eligibility;
16. completed/TEAM_INFEASIBLE ownership `-1` and canonical inverse current task;
17. episode reset clears only episode-local state; process-lifetime counters do
    not reset;
18. initial/explicit reset creates no fake transition;
19. terminal sidecar exact blocks, all-zero deferred blocks/masks, no aliases,
    mailbox survival across fake reset, read-once acknowledgement;
20. `TRANSITION_AUTHORITY` success diagnostic and no fabricated failure
    receipt;
21. coordinator rejects each existing resolved-profile subtype;
22. all existing-profile routes produce no B0 state, event, info, file, or RNG
    side effect;
23. source/static ordering proves producer call before any `_reset_idx()` and
    wrapper/HARL does not reconstruct facts.

Pure tests may use synthetic tensors and fake reset buffers. They must not
start AppLauncher, gym/Isaac, HARL actors, checkpoint I/O, training, playback,
or evaluation.

## 23. Proposed Isaac/runtime tests for later authorization

These are designs only and require a separate explicit runtime authorization.
They must use the required conda environment and remain bounded:

- one/few-step event-environment B0 harness proving `_get_dones()` publishes a
  handoff before autoreset;
- terminal completion row proving pair robot/task/previous owner and final
  physical pose survive while returned observation is post-reset;
- time-limit row proving raw truncation, finalized `TIME_LIMIT`, and sidecar;
- selected-env vector autoreset proving non-done rows keep their episode state;
- manual reset proving generation increment with no fake transition;
- structural failure/release/unavailable/recovery using controlled injected
  reporters, not invented physical detectors;
- mailbox acknowledgement and next-step stale-handoff protection;
- exact existing-profile default-off regression.

Because the formal event HARL factory currently blocks before
`gymnasium.make`, an environment-level B0 harness must itself be explicitly
reviewed; it cannot masquerade as end-to-end event HARL readiness. If no such
harness is approved, Isaac evidence remains deferred until the future atomic
readiness package. No training, playback, evaluation, optimizer, or long
simulation is part of a B0 smoke.

## 24. Rollback and fail-closed strategy

- Existing profiles have no coordinator and retain direct old implementations.
- Event coordinator construction requires the exact event subtype.
- B0 foundation remains unreachable from normal production entrypoints until
  a later atomic switch.
- State mutation uses candidate copies and one post-result atomic swap.
- Mailbox overwrite, missing arm context, missing terminal sidecar, reset before
  finalization, or generation mismatch is fatal.
- Any unowned/ambiguous canonical completion fails before coverage mutation.
- Unsupported physical terminal/truncation fails with terminal policy disabled
  (`DVM=0`, no proposal/commit) and no invented reason.
- No fallback to wrapper reconstruction, current resolver pair state, last
  effective assignment, logger output, or reset-state inference exists.
- Rollback of a B0 implementation consists of removing the dormant event-only
  coordinator/hook; existing profile behavior does not depend on it.

Stop classification if implementation reveals an exact frozen incompatibility:

```text
STOP — B0 CONTRACT/RUNTIME GAP
```

The stop report must name the exact contract field/equation and the actual
runtime fact that cannot satisfy it. It must not patch the frozen contract.

## 25. Explicitly deferred B/C/D/E work

B0 does not implement or select behavior for:

- scheduled assignment retry or its cadence;
- local robot/task set, owner expansion, overlap merge, or caps;
- Top-K or expected-time cost/path estimator;
- event action masks or DVM;
- actor sampling, log probabilities, rollout buffer, or valid-only actor loss;
- zero/singleton actor update behavior or sequential factor;
- transfer graph/component objective/resolver or ownership optimization;
- team reward or rejection penalty;
- HARL terminal-sidecar buffer/GAE/ValueNorm adaptation;
- proper-time-limit bad-mask transport beyond freezing raw B0 facts;
- checkpoint-ready V3, state-dict inventory, or weight use;
- training, playback, evaluation, ablation, or performance claims.

The future Phase-B resolver may request an atomic ownership commit through the
B0 state-store boundary; that narrow port is the only B0 interface designed for
it.

## 26. Numeric-TBD ownership

No numeric value is owned or selected by B0.

| Parameter | Frozen later owner |
|---|---|
| `top_k_tasks_per_robot` | Phase B runtime + Phase E evaluation |
| `local_robot_cap` | Phase B runtime |
| `local_task_cap` | Phase B runtime |
| `pair_abs_threshold` | Phase B runtime + Phase E evaluation |
| `pair_rel_threshold` | Phase B runtime + Phase E evaluation |
| `component_abs_threshold` | Phase B runtime + Phase E evaluation |
| `component_rel_threshold` | Phase B runtime + Phase E evaluation |
| `transfer_penalty` | Phase B runtime + Phase E evaluation |
| `rejection_penalty_scale` | Phase D reward + Phase E evaluation |
| `alignment_time_constant` | Phase B runtime + Phase E evaluation |
| `assignment_retry_cadence` | Phase B runtime |

Generation starting conventions, enum values, and zero-filled terminal deferred
blocks are schema mechanics, not method numeric defaults.

## 27. Risks and open questions

### 27.1 Risks controlled by this design

- **Prototype completion promotion.** The current scan predicate is adequate
  only for a controlled skeleton adapter. A real target-alignment detector must
  be separately evidenced; budget/path heuristics cannot replace it.
- **Ordinary execution-phase progression.** The B0 authority owns task/robot
  lifecycle tensors. Future claim commits and execution-phase reporters must
  enter through authority validation; the environment may report progress but
  may not write lifecycle state directly. If exact `CLAIMED -> NAVIGATING ->
  ALIGNING` progression needs a raw field absent from the frozen facts schema,
  implementation must stop rather than add an unreviewed field.
- **Simultaneous cause precedence.** The completion/release/availability rule in
  section 10.3 is the recommended deterministic interpretation and requires
  GPT/user confirmation before implementation.
- **Receipt-less failure diagnostics.** B0 emits only successful first-consume
  payloads; no sentinel is invented.
- **Event route remains unreachable.** B0 can close pure/fake-hook foundation
  evidence without claiming full Isaac/HARL event readiness.
- **Mailbox backpressure.** A missed acknowledgement must fail, not silently
  overwrite terminal state.
- **Vector batch atomicity.** One bad row rejects the full facts consume as the
  frozen ledger requires.

### 27.2 Not a current Phase-A contract gap

Autoreset does not make the contract impossible because `_get_dones()` is a
real pre-reset hook executed once on every physical step. Pair attribution can
be retained by separating event completion detection from global coverage
mutation and binding it to authoritative ownership. Dedicated typed reporter
ports can represent currently absent failure/release/health edges without
changing frozen fields. Therefore the current classification is design
complete, not `STOP — B0 CONTRACT/RUNTIME GAP`.

## 28. Recommended B0 implementation slices

Each slice requires separate explicit authorization and stops for review.

### B0-1 — Pure producer, clocks, and handoff foundation

**Scope:** new coordinator skeleton; producer port; generation/token clock;
immutable mailbox; frozen facts construction only.

**Allowed files:**

- new `assignment_lifecycle_authority_runtime.py`;
- new pure B0 test;
- B0 report/TASK_PROGRESS update.

**Done gate:** exact facts batch, tokens/generations, no aliases, no derived
fields, read/ack mailbox, event-profile-type gate.

**Tests:** `py_compile`; standalone pure `--json` cases; no env import requiring
Isaac.

**Stop conditions:** frozen contract edit needed; existing profile constructs
coordinator; any file/sink/RNG side effect.

### B0-2 — Lifecycle state mutation and consume-once authority

**Scope:** state store; completion/release/failure/availability; cumulative
failed pairs; TEAM_INFEASIBLE; events; receipt/result finalization; no env hook.

**Allowed files:**

- `assignment_lifecycle_authority_runtime.py`;
- B0 pure authority test;
- handoff docs.

**Done gate:** all equations and conflict cases, full-batch atomicity, exactly
one result, no current resolver reuse.

**Tests:** pure synthetic transition sequences across multiple envs/episodes.

**Stop conditions:** result factory is treated as sufficient without B0 semantic
checks; budget failure enters permanent pairs; duplicate writer appears.

### B0-3 — Event-only pre-reset execution integration

**Scope:** separate scan detection from event commit; owner-gated completion;
typed reporter inbox; call coordinator inside `_get_dones()`; preserve current
paths exactly.

**Allowed files:**

- `scan_mobile_manipulator_env.py`;
- B0 runtime module;
- new pure/fake pre-reset hook test;
- narrowly necessary event-env registration/helper only if separately listed
  in the authorization.

**Done gate:** source/fake order proves facts/result before reset; global
coverage changes only after attribution; existing profiles take old path.

**Tests:** pure detector fixtures, fake reset overwrite, default-off identity;
no Isaac unless separately authorized.

**Stop conditions:** exact owned completion cannot be obtained; wrapper state
must be reconstructed after step; existing scan behavior drifts.

### B0-4 — Termination, sidecar, and reset handshake

**Scope:** reason priority, done projection, terminal shared-state builder,
mailbox lifetime, explicit/autoreset episode rebuild.

**Allowed files:**

- new `assignment_terminal_critic_sidecar.py`;
- B0 runtime module;
- event-only scan hook;
- B0 pure sidecar/reset tests.

**Done gate:** all terminal rows have exactly one no-alias sidecar before reset;
no actor/storage/proposal row; generation resets exact.

**Tests:** four reasons, simultaneous time-limit/completion, selected-env reset,
manual reset, stale handoff.

**Stop conditions:** sidecar requires post-reset state; it adds a transition or
loss sample; unsupported termination is silently mapped.

### B0-5 — Transition diagnostics and isolation closeout

**Scope:** in-memory successful transition-authority payload; all later kinds
unproduced; profile/type guards; existing-profile regression inventory.

**Allowed files:**

- B0 runtime module;
- diagnostic pure tests only (frozen schema unchanged);
- dedicated B0 handoff/facade module if explicitly approved;
- closeout docs.

**Done gate:** real token/receipt payload only; no sink/info/file; four existing
profiles have no B0 artifacts; event global readiness still blocked.

**Tests:** pure diagnostics/availability/default-off/clean-child tests.

**Stop conditions:** fabricated failure receipt, partial AssignmentTick payload,
or readiness barrier weakened.

### B0-6 — Separately authorized bounded runtime evidence and closeout

**Scope:** minimal event-environment B0 harness, one/few physical transitions,
autoreset capture, final report. No HARL actor or training.

**Allowed files:** exact harness/script and docs named by the future
authorization; no installed HARL or checkpoint changes.

**Done gate:** pre-reset facts/result/sidecar proven under Isaac reset ordering;
claims remain limited to B0 lifecycle semantics.

**Tests:** targeted Isaac smoke only after explicit permission; existing-profile
regression; no training/playback/evaluation.

**Stop conditions:** normal route requires premature global readiness, GUI/long
run, event scheduler/resolver/DVM, or any performance claim.

## 29. Review gate

GPT/user review should decide only whether this B0 placement and the explicitly
identified simultaneous-cause/prototype-completion boundaries are acceptable.
It should not infer implementation authorization from this report.

```text
review request:
  approve or revise the environment-invoked dedicated coordinator placement
  approve or revise the completion/release simultaneous-cause rule
  confirm dormant foundation + later atomic readiness strategy

B0 implementation:
  not started
  not authorized

B/C/D/E:
  not entered

training/playback/evaluation:
  prohibited and not run

commit:
  none
```

B0 stops here for GPT/user review.
