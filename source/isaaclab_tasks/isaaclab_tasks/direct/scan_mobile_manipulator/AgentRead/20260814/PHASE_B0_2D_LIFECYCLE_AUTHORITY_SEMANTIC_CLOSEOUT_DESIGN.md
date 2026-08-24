# Phase B0-2D Lifecycle Authority Semantic Closeout Design

## 1. Classification and decision

```text
classification:
  PHASE-B0-2D-LIFECYCLE-AUTHORITY-SEMANTIC-CLOSEOUT-DESIGN-COMPLETE-AWAITING-GPT-REVIEW

starting HEAD:
  912b3b59831fcad8dd29ac575b2a1851bf2c21d1

starting branch:
  main

Phase A:
  complete at the accepted pure/static/manifest evidence level

Phase B0 design:
  PHASE-B0-DESIGN-CONDITIONAL-PASS remains historical and unchanged

B0-1A:
  review passed

B0-1B:
  review passed

B0-2D:
  design complete

simultaneous-cause matrix:
  frozen

robot lifecycle transition table:
  frozen

task lifecycle B0 authority scope:
  frozen

termination ordering:
  frozen

authority/state-store/resolver capability split:
  frozen

receipt retry/runtime fail-stop distinction:
  frozen

event ordering:
  frozen

Phase-A contract revision:
  none

B0 contract/runtime gap:
  none requiring a frozen schema change

B0-2 implementation:
  not authorized

B0-3+:
  not authorized

Phase B/C/D/E:
  not entered

code changes:
  none

training/playback/evaluation:
  not run

commit:
  none
```

This document is the authoritative B0-2D addendum to
`PHASE_B0_PRE_RESET_LIFECYCLE_AUTHORITY_RUNTIME_DESIGN.md`. It closes the
semantic conditions left for review there; it does not overwrite that report
or promote its conditional classification. If this addendum and the older
report differ on a B0-2 transition semantic, this targeted addendum controls.

The closeout found that the frozen `ExecutionTransitionFacts` and
`LifecycleTransitionResult` fields are sufficient for the B0-2 authority
scope. The absent `CLAIMED -> NAVIGATING -> ALIGNING` progress edges remain a
deliberately deferred capability, not a blocker for completion, release,
permanent failure, health, TEAM_INFEASIBLE, or termination processing.

No Python, test, environment, wrapper, resolver, controller, HARL, YAML,
checkpoint, or frozen contract file is changed by B0-2D. No implementation
test or Isaac/AppLauncher process is run.

## 2. Frozen identities and normative language

The following Phase-A identities remain the only public encodings:

```text
TaskLifecycleState:
  AVAILABLE = 0
  CLAIMED = 1
  NAVIGATING = 2
  ALIGNING = 3
  COMPLETED = 4
  TEAM_INFEASIBLE = 5

RobotLifecycleState:
  EXECUTING = 0
  NEEDS_ASSIGNMENT = 1
  WAITING_FOR_TASK = 2
  UNAVAILABLE = 3

TerminationReason:
  NONE = 0
  ALL_TASKS_COMPLETED = 1
  NO_FEASIBLE_TASKS_REMAIN = 2
  TIME_LIMIT = 3
```

In this document:

- `C[e,i,j]` is `completion_signals`;
- `F[e,i,j]` is `terminal_pair_failure_signals`;
- `R[e,i,j]` is `forced_release_signals`;
- `U[e,i]` is `robot_unavailable_signals`;
- `Rc[e,i]` is `robot_recovered_signals`;
- `owner0[e,j]`, `task0[e,j]`, and `robot0[e,i]` are the immutable
  pre-transition ownership/task/robot state;
- `failed0[e,i,j]` is the state-store cumulative failed-pair snapshot;
- `a0[e,j]` is the event-updated ownership in the finalized lifecycle result,
  before any later Phase-B assignment commit;
- an active task state is exactly `CLAIMED`, `NAVIGATING`, or `ALIGNING`;
- a terminal task state is exactly `COMPLETED` or `TEAM_INFEASIBLE`.

`M` and `N` retain their resolved robot/task dimensions. All equations are
per environment even where `e` is omitted. `any_i` and `all_i` reduce only the
global robot-ID axis. “Edge” means false/other-state before the physical
transition and true/target-state after that same transition.

The words MUST, MUST NOT, and INVALID below are implementation-testable
requirements. INVALID always means typed fail-closed during full-batch
prevalidation, before ledger consume, result finalization, state mutation, or
generation commit.

## 3. Preconditions and full-state invariants

The authority validates the complete selected batch against one immutable
state-store snapshot and version before deriving any candidate. The frozen
facts factory does not enforce every item in this section, so B0-2 must.

For every selected environment:

1. Every task, robot, termination, authority, profile, producer, generation,
   token, shape, dtype, device, and row identity is in its exact frozen domain.
2. `AVAILABLE`, `COMPLETED`, and `TEAM_INFEASIBLE` tasks have owner `-1`.
3. Every `CLAIMED`, `NAVIGATING`, or `ALIGNING` task has exactly one owner in
   `0..M-1`.
4. One robot owns at most one active task. Ownership and the derived
   robot-to-current-task inverse are mutual inverses.
5. `EXECUTING` means exactly one owned active task.
   `NEEDS_ASSIGNMENT`, `WAITING_FOR_TASK`, and `UNAVAILABLE` mean no owned
   task.
6. `COMPLETED` and `TEAM_INFEASIBLE` are episode-absorbing. They accept no
   `C`, `F`, or `R`; an unavailable edge cannot release them.
7. `C`, `F`, and `R` each match the exact pre-transition owner and an active
   task. More than one completion robot for one task is invalid.
8. `C & F` on one pair is invalid. No precedence winner is selected.
9. `U` requires `robot0 != UNAVAILABLE`. `Rc` requires
   `robot0 == UNAVAILABLE` and no ownership. Repeated unavailable/recovery
   level reports are not edges and are invalid.
10. `U & Rc` for one robot is invalid.
11. The pre-transition TEAM equation already holds: a non-completed task with
    all cumulative robot pairs failed is `TEAM_INFEASIBLE`; a
    `TEAM_INFEASIBLE` task has all such pairs failed. This prevents latent
    terminal drift from being “repaired” during an unrelated transition.
12. Completion counts are non-negative episode-local integers and agree with
    the state store. A result never reconstructs them from wrapper reward or
    coverage deltas.

Any stale store version, stale/foreign generation context, state/facts owner
disagreement, or invalid row rejects the whole candidate batch. Validation is
not row-by-row mutation.

## 4. D1 — Capability and authority boundary

### 4.1 Exact boundary

```text
physical environment
  -> supplies raw physical/reporter inputs
  -> invokes one CoordinatorPreResetPort before autoreset

coordinator
  -> owns the exclusive transaction/publication lock
  -> invokes the producer, authority transaction, state store, and clock
  -> orders capabilities but is not a second semantic authority

EnvironmentExecutionFactsProducer
  -> constructs one frozen ExecutionTransitionFacts batch only

LifecycleAuthorityRuntime / LIFECYCLE_AUTHORITY_V1
  -> is the sole lifecycle derivation authority
  -> derives candidate completion, release, permanent failure, health,
     task/robot/ownership/counter state, TEAM_INFEASIBLE, final reason,
     lifecycle events, and LifecycleTransitionResult inputs

LifecycleStateStore
  -> is the sole writable lifecycle-state boundary
  -> exposes immutable versioned snapshots and capability-limited atomic swaps
```

The environment receives only the coordinator invocation surface and the
published finalized handoff. It does not receive or retain:

- the producer object or producer stamp capability;
- `TransitionConsumeLedger` or a consume capability;
- the lifecycle authority stamp;
- the result factory/finalization capability;
- an issued receipt;
- writable lifecycle tensors or a state-store mutation capability;
- a lifecycle event factory;
- a clock commit capability.

The environment therefore cannot finalize `LifecycleTransitionResult`, issue
or consume a receipt, derive a lifecycle event, or directly update state. The
older phrase “environment receives producer/finalize/reset port” is replaced
by “environment supplies raw inputs and invokes one coordinator pre-reset
port.” Episode rebuild is likewise coordinator-mediated and does not expose
these capabilities to the environment.

The facts producer has no lifecycle semantics. It validates caller-supplied
raw tensors, allocates the independent consume-once token, and calls the
frozen facts factory. It does not derive final reason, release, failed-pair
state, TEAM_INFEASIBLE, events, state updates, receipts, or results.

The state store is a writer, not a semantic authority. It accepts only a
fully validated, exact-version candidate from the sole authority transaction
or the separately typed later assignment-commit capability. It does not infer
events or repair an invalid candidate.

## 5. D2 — Lifecycle derivation versus later assignment commit

### 5.1 Projection owned by the lifecycle authority

`LIFECYCLE_AUTHORITY_V1` exclusively owns the derivation of:

```text
completion
forced/health/failure-driven release
new and cumulative structural terminal pair failure
robot unavailable/recovered state effect
TEAM_INFEASIBLE
final TerminationReason
lifecycle event set and ordering
event-updated ownership a0
episode completion-count/workload delta
LifecycleTransitionResult
```

No resolver or assignment policy may recompute, override, or append to this
projection.

### 5.2 Projection owned by future Phase B

Future Phase B may request only a post-`a0` claim, assignment, or transfer.
The request is a typed staged value bound to:

- exact environment, episode, and transition generations;
- the exact finalized lifecycle `a0` identity;
- the exact current state-store version;
- one closed selected environment/component batch.

The state store, not the resolver, validates that the row is nonterminal, the
expected `a0` and version still match, robots/tasks/pairs are legal, one robot
gets at most one task, one task gets at most one owner, and ownership/current
task remain mutual inverses. It then changes only the assignment-owned live
projection in one atomic assignment commit:

```text
ownership after a0
AVAILABLE -> CLAIMED task state as applicable
robot assignment state
derived inverse current task
```

A reviewed transfer may atomically change those assignment-owned fields. It
does not retroactively set `released_tasks`, and its separately typed resolver
diagnostic is not a lifecycle transition event.

The staged assignment capability MUST NOT:

- rewrite the immutable finalized `LifecycleTransitionResult` or historical
  `a0`;
- derive or mutate completion counts, released-task result bits, failed pairs,
  `TEAM_INFEASIBLE`, termination, or lifecycle events;
- mutate store tensors directly;
- commit against a terminal `a0`;
- bypass full-batch/component closure or the store version check.

This is one lifecycle derivation authority, one storage writer boundary, and a
later narrow assignment-commit capability. It is not two lifecycle
authorities.

## 6. D3 — Exact simultaneous-cause semantics

### 6.1 Vector equations

After the conflict/owner/prestate checks, the authority derives from immutable
inputs:

```text
completed[j] = any_i C[i,j]

new_failed[i,j] = F[i,j] & ~failed0[i,j]

updated_failed[i,j] = failed0[i,j] | new_failed[i,j]

unavailable_release[i,j] =
  U[i]
  & (owner0[j] == i)
  & (task0[j] in {CLAIMED, NAVIGATING, ALIGNING})

release_request[i,j] = R[i,j] | F[i,j] | unavailable_release[i,j]

released[j] = any_i release_request[i,j] & ~completed[j]
```

The union in `release_request` is Boolean. Two or three raw causes never
produce two result bits or two `TASK_RELEASED` events. Completion masks release
for that task after `C & F` has already been rejected: `C+R`, `C+U`, and
`C+R+U` complete the task and do not release it.

Candidate task update before TEAM derivation is exact:

```text
if completed[j]:
  task_candidate[j] = COMPLETED
  owner_candidate[j] = -1
elif released[j]:
  task_candidate[j] = AVAILABLE
  owner_candidate[j] = -1
else:
  task_candidate[j] = task0[j]
  owner_candidate[j] = owner0[j]
```

Terminal prior states are preserved by the precondition that they receive no
raw pair signal. Failure is cumulative and monotonic; completion and recovery
do not clear it.

Completion attribution and workload are exact:

```text
completion_delta[i] = sum_j C[i,j]
completion_count1[i] = completion_count0[i] + completion_delta[i]
per_robot_workload1[i] = completion_count1[i] / N
```

`C+U` and `C+R+U` still credit the completing owner. `R`, `F`, `U`, and `Rc`
never increment completion count. No fractional multi-robot credit, global
coverage reconstruction, or reward-derived attribution is permitted.

### 6.2 Complete owned-pair matrix

The next table covers all `C/F/R/U` bit patterns for one valid active owned
pair `(i,j)` with `Rc=0`. “P” means apply the exact final robot projection in
Section 7 after all tasks and failures are updated. Events shown are the
logical set; Section 10 supplies the exact serialization order.

| C | F | R | U | Valid | Task/owner/result | Failed-pair effect | Robot | Logical events |
|---:|---:|---:|---:|---|---|---|---|---|
| 0 | 0 | 0 | 0 | yes | preserve active state and owner; no completed/released bit | unchanged | `EXECUTING` | none |
| 0 | 0 | 0 | 1 | yes | `AVAILABLE`, owner `-1`, released once | unchanged | `UNAVAILABLE` | release, unavailable |
| 0 | 0 | 1 | 0 | yes | `AVAILABLE`, owner `-1`, released once | unchanged | P | release, needs if state edge |
| 0 | 0 | 1 | 1 | yes | same single release as either cause | unchanged | `UNAVAILABLE` | one release, unavailable |
| 0 | 1 | 0 | 0 | yes | `AVAILABLE`, owner `-1`, released once; then TEAM rule | `new=F&~failed0`; cumulative OR | P | one release, pair failure only if new, TEAM if edge, needs if state edge |
| 0 | 1 | 0 | 1 | yes | one release; then TEAM rule | same | `UNAVAILABLE` | one release, pair failure if new, TEAM if edge, unavailable |
| 0 | 1 | 1 | 0 | yes | explicit and failure release deduplicate; then TEAM rule | same | P | one release, pair failure if new, TEAM if edge, needs if state edge |
| 0 | 1 | 1 | 1 | yes | all three release causes deduplicate; then TEAM rule | same | `UNAVAILABLE` | one release, pair failure if new, TEAM if edge, unavailable |
| 1 | 0 | 0 | 0 | yes | `COMPLETED`, owner `-1`, completed true, released false | unchanged | P | completed, needs if state edge |
| 1 | 0 | 0 | 1 | yes | `COMPLETED`, owner `-1`, completed true, released false | unchanged | `UNAVAILABLE` | completed, unavailable |
| 1 | 0 | 1 | 0 | yes | completion wins over redundant release; released false | unchanged | P | completed, needs if state edge |
| 1 | 0 | 1 | 1 | yes | completion wins for task; released false | unchanged | `UNAVAILABLE` | completed, unavailable |
| 1 | 1 | 0 | 0 | **no** | invalid `C & F` | none | none | none |
| 1 | 1 | 0 | 1 | **no** | invalid `C & F` | none | none | none |
| 1 | 1 | 1 | 0 | **no** | invalid `C & F`; `R` does not select a winner | none | none | none |
| 1 | 1 | 1 | 1 | **no** | invalid `C & F`; `R/U` do not select a winner | none | none | none |

With `F=0`, release or unavailability alone cannot create a TEAM edge: the
failed-pair tensor is unchanged, and the valid prestate already excludes an
active non-completed task whose pairs are all failed. Accordingly those rows
emit no `TASK_BECAME_TEAM_INFEASIBLE` event.

For an owned pair, every one of the 16 patterns with `Rc=1` is invalid. The
robot cannot be both the owner/`EXECUTING` and prior `UNAVAILABLE`, and `U&Rc`
is independently forbidden. Together with the table, this classifies all 32
five-bit combinations for an owned pair.

### 6.3 Recovery-only and unowned cases

The only valid recovery pattern is robot-scoped:

```text
prior robot state = UNAVAILABLE
prior ownership count = 0
C = F = R = U = 0 for that robot
Rc = 1
```

It clears the unavailable health condition and applies projection P. The final
state is `NEEDS_ASSIGNMENT` when at least one structurally eligible unowned
AVAILABLE task exists for that robot, otherwise `WAITING_FOR_TASK`. It emits
`ROBOT_RECOVERED` and additionally `ROBOT_NEEDS_ASSIGNMENT` only if the final
state is `NEEDS_ASSIGNMENT` and that is a real state edge.

For an unowned robot-task pair, `C`, `F`, and `R` are invalid because each is
owner-gated. `U` remains legal at robot scope and releases the robot's actual
owned active task, if any. An unavailable robot with no task emits only the
robot event. A no-signal unowned pair has no pair effect.

### 6.4 Multiple pairs and environments

All pair effects are derived in parallel from `owner0`, never from a partially
updated owner. Current invariants allow a robot to own at most one active task,
but the unavailable release is still defined as the union over every owned
nonterminal task so the safety rule cannot silently become first-match logic.

Different environments are independent semantically but are one atomic input
batch. One invalid row rejects all rows. Global robot/task IDs, not incidental
tensor iteration or dictionary insertion order, determine event identity.

## 7. D4 — Exact RobotLifecycleState transition table

### 7.1 Final robot projection P

The authority first derives task state, failed pairs, and `a0`. It then applies
one projection to every robot. This is not an ad hoc winner among raw causes.

Define:

```text
unavailable_after[i] =
  U[i]
  OR (robot0[i] == UNAVAILABLE AND NOT Rc[i])

owns_active_after[i] =
  exactly one j satisfies
    a0[j] == i
    AND task1[j] in {CLAIMED, NAVIGATING, ALIGNING}

eligible_unowned_work_after[i] =
  exists j such that
    task1[j] == AVAILABLE
    AND a0[j] == -1
    AND updated_failed[i,j] == false
```

The exact final state is:

```text
if unavailable_after[i]:
  robot1[i] = UNAVAILABLE
elif owns_active_after[i]:
  robot1[i] = EXECUTING
elif eligible_unowned_work_after[i]:
  robot1[i] = NEEDS_ASSIGNMENT
else:
  robot1[i] = WAITING_FOR_TASK
```

The state/ownership invariants are validated again after this projection.
Transient path validity, Top-K/local-set membership, cost, cooldown, budget,
or retry timing does not change this projection. Those may affect a future
assignment opportunity but cannot disguise structurally available work.

`ROBOT_NEEDS_ASSIGNMENT` is emitted exactly when
`robot0 != NEEDS_ASSIGNMENT` and `robot1 == NEEDS_ASSIGNMENT`. Merely
preserving `NEEDS_ASSIGNMENT` emits no duplicate event. A change from
`NEEDS_ASSIGNMENT` to `WAITING_FOR_TASK` has no invented event because the
frozen vocabulary contains no waiting event.

### 7.2 Cause table by prior state

| Prior robot state | No robot/owned-pair edge | Owned completion | Owned release | Owned failure | Unavailable edge | Recovery edge |
|---|---|---|---|---|---|---|
| `EXECUTING` | remains `EXECUTING` because ownership remains | clear completed ownership, then P | clear ownership, then P | record failure, clear ownership, then P | `UNAVAILABLE`; release any owned nonterminal task except a simultaneously completed task | invalid |
| `NEEDS_ASSIGNMENT` | P; remains needs only while eligible work exists | invalid: no owned task | invalid | invalid | `UNAVAILABLE` | invalid |
| `WAITING_FOR_TASK` | P; may enter needs only when eligible work now exists | invalid: no owned task | invalid | invalid | `UNAVAILABLE` | invalid |
| `UNAVAILABLE` | remains `UNAVAILABLE` | invalid | invalid | invalid | invalid repeated edge | clear unavailable condition, then P |

`F+R` and `F+U` retain the same table outcome while deduplicating release.
`C+R` retains completion. `C+U` retains task completion but final robot
`UNAVAILABLE`. Every `C+F` and every `U+Rc` combination fails before consume.

### 7.3 Terminal rows

Termination is derived after projection P; it does not synthesize a second
robot-state normalization:

- `ALL_TASKS_COMPLETED`: no AVAILABLE or active task remains, so every healthy
  unowned robot is `WAITING_FOR_TASK`; unavailable robots remain
  `UNAVAILABLE`. A completing healthy robot is therefore waiting, not needs.
- `NO_FEASIBLE_TASKS_REMAIN`: every task is completed or team-infeasible, so
  every healthy unowned robot is `WAITING_FOR_TASK`; unavailable robots remain
  `UNAVAILABLE`.
- `TIME_LIMIT`: time itself releases no task and rewrites no ownership. A robot
  still owning active work remains `EXECUTING`; an unavailable robot remains
  `UNAVAILABLE`; an unowned healthy robot is needs or waiting by P.
- `NONE`: the same P equation applies.

A terminal row never schedules actor/proposal/resolver work, regardless of the
stored robot state or a same-transition needs event. Thus a TIME_LIMIT row may
faithfully record an actual transition into `NEEDS_ASSIGNMENT` while the
frozen terminal no-row rule still suppresses every assignment action. No
terminal-only lifecycle event is invented.

## 8. D5 — TaskLifecycleState authority scope

### 8.1 B0-2 authoritative transitions

| Prior task state | No valid owned event | Completion C | Release from R/F/owner-U | TEAM derivation |
|---|---|---|---|---|
| `AVAILABLE` | preserve, owner `-1` | invalid: no owner | invalid: no owner | prestate equation already prevents latent all-failed AVAILABLE |
| `CLAIMED` | preserve exact state and owner | `COMPLETED`, owner `-1` | intermediate `AVAILABLE`, owner `-1` | after release, becomes `TEAM_INFEASIBLE` iff all updated pairs failed |
| `NAVIGATING` | preserve exact state and owner | `COMPLETED`, owner `-1` | intermediate `AVAILABLE`, owner `-1` | same |
| `ALIGNING` | preserve exact state and owner | `COMPLETED`, owner `-1` | intermediate `AVAILABLE`, owner `-1` | same |
| `COMPLETED` | preserve, owner `-1` | invalid | invalid | completion is absorbing and excludes TEAM |
| `TEAM_INFEASIBLE` | preserve, owner `-1` | invalid | invalid | absorbing because failed pairs are monotonic |

Completion is a canonical owner-attributed terminal success edge. B0-2 accepts
it from any existing active state; it does not require the store to claim that
an unreported `ALIGNING` transition occurred. This permits the frozen facts to
authoritatively close work without inventing missing progress signals.

### 8.2 Explicitly deferred progress transitions

B0-2 does not create or claim:

```text
AVAILABLE -> CLAIMED       except via a later typed assignment commit
CLAIMED -> NAVIGATING
NAVIGATING -> ALIGNING
```

`ExecutionTransitionFacts` has no navigation-started, arrived, or
alignment-started edge, so the last two transitions cannot be inferred from
continuous controller actions, distance, wrapper state, or elapsed time. This
does not require a Phase-A schema change for B0-2: existing active phases are
preserved, and the canonical completion edge closes any active phase.

A future progression feature requires a separately reviewed typed reporter or
capability, exact generation/store-version binding, and the same sole state
writer. Until then it is **NOT IMPLEMENTED / NOT CLAIMED**. B0-2 tests must not
advertise phase-progression runtime evidence.

## 9. TEAM_INFEASIBLE closeout

After completion/release and cumulative failed-pair update, task `j` has exact
final terminal derivation:

```text
team_condition[j] =
  task_candidate[j] != COMPLETED
  AND all_i updated_failed[i,j]

if task_candidate[j] == COMPLETED:
  task1[j] = COMPLETED
elif team_condition[j]:
  task1[j] = TEAM_INFEASIBLE
  a0[j] = -1
else:
  task1[j] = task_candidate[j]
```

`new_team_infeasible_tasks[j]` is true exactly when `team_condition[j]` is
true and `task0[j] != TEAM_INFEASIBLE`. Completion therefore wins over TEAM in
every legal completion combination. The same-pair completion/failure conflict
was already rejected, so this is not a precedence rule for invalid input.

Only episode-cumulative permanent structural failure contributes to
`updated_failed`. None of the following can set a failed pair or create
TEAM_INFEASIBLE:

```text
transient path invalidity
local set or Top-K emptiness
finite/infinite nominal cost caused by a transient path result
cooldown
budget exhaustion
temporary stall
retry cadence
resolver rejection
```

No threshold or one of the eleven method numeric TBDs is selected by this
equation.

## 10. Lifecycle events and exact canonical order

### 10.1 Logical event equations

The authority first constructs a deduplicated logical set:

| Event type | Exact emission condition | IDs/payload state | Causal source |
|---|---|---|---|
| `TASK_COMPLETED` | `completed[j]` | task `j`; cause robot is the unique completing owner; active state -> `COMPLETED` | `EXECUTION_FACTS` |
| `TASK_RELEASED` | `released[j]` | task `j`; cause robot is prior owner; active state -> intermediate `AVAILABLE` | `EXECUTION_FACTS` |
| `TERMINAL_PAIR_FAILURE_RECORDED` | `new_failed[i,j]` | pair `(i,j)`; `newly_recorded=true` | `EXECUTION_FACTS` |
| `TASK_BECAME_TEAM_INFEASIBLE` | `new_team_infeasible_tasks[j]` | task `j`; `AVAILABLE` -> `TEAM_INFEASIBLE`; cause robot `-1` | `LIFECYCLE_DERIVATION` |
| `ROBOT_BECAME_UNAVAILABLE` | `U[i]` | robot `i`; prior state -> `UNAVAILABLE` | `EXECUTION_FACTS` |
| `ROBOT_RECOVERED` | `Rc[i]` | robot `i`; `UNAVAILABLE` -> final P state | `EXECUTION_FACTS` |
| `ROBOT_NEEDS_ASSIGNMENT` | prior state is not needs and final P state is needs | robot `i`; prior state -> `NEEDS_ASSIGNMENT` | `LIFECYCLE_DERIVATION` |

Every event has the frozen `trigger_eligible=true`, exact authority identity,
facts token, environment ID, and episode/transition generations. Terminal
suppression is a scheduler rule after the result; it does not falsify a real
state edge in the event record.

The TEAM event uses cause robot `-1`, even when one new pair happened to close
the all-robot equation. TEAM is a cumulative lifecycle derivation and no
arbitrary last-writer attribution is permitted.

If release immediately leads to TEAM, the release payload records the real
intermediate active-to-AVAILABLE edge and the TEAM payload records
AVAILABLE-to-TEAM_INFEASIBLE. This does not mean two state-store mutations;
both are records derived from one candidate, committed once.

### 10.2 Total serialization order

The Phase-A enum declaration is the primary same-transition type order and is
not replaced:

```text
0 TASK_COMPLETED
1 TASK_RELEASED
2 TERMINAL_PAIR_FAILURE_RECORDED
3 TASK_BECAME_TEAM_INFEASIBLE
4 ROBOT_BECAME_UNAVAILABLE
5 ROBOT_RECOVERED
6 ROBOT_NEEDS_ASSIGNMENT
```

The full deterministic sort is:

1. `env_id` ascending;
2. enum declaration rank above ascending;
3. for task events, `task_id` ascending then `cause_robot_id` ascending;
4. for pair-failure events, `robot_id` ascending then `task_id` ascending;
5. for robot events, `robot_id` ascending.

After sorting, each environment receives contiguous ordinal `0..K-1`, and:

```text
event_id = (env_id, episode_generation, transition_generation, ordinal)
```

Serialization order is deliberately distinct from internal derivation order.
For example, an `F` transition updates the failed pair before checking TEAM,
but the frozen type order serializes `TASK_RELEASED` before
`TERMINAL_PAIR_FAILURE_RECORDED`. No Python mapping order, raw tensor scan
order, robot loop, task loop, or concurrent reporter arrival order is visible.

Representative exact sequences, after omitting non-emitted optional edges,
are:

```text
C + U:
  TASK_COMPLETED
  ROBOT_BECAME_UNAVAILABLE

F + R, final robot enters needs:
  TASK_RELEASED
  TERMINAL_PAIR_FAILURE_RECORDED   # only if the pair is new
  TASK_BECAME_TEAM_INFEASIBLE      # only if the task edge occurs
  ROBOT_NEEDS_ASSIGNMENT

F + U:
  TASK_RELEASED
  TERMINAL_PAIR_FAILURE_RECORDED   # only if new
  TASK_BECAME_TEAM_INFEASIBLE      # only if edge
  ROBOT_BECAME_UNAVAILABLE

R + U:
  TASK_RELEASED
  ROBOT_BECAME_UNAVAILABLE

recovery to needs:
  ROBOT_RECOVERED
  ROBOT_NEEDS_ASSIGNMENT
```

Repeated structural input against an already cumulative failed pair yields
`new_failed=false` and no pair-failure event. Its owner-gated release semantic
is still the same Boolean union; normal future assignment validation must not
assign a known failed pair in the first place.

## 11. D6 — Final reason, ordering, and Gym projection

### 11.1 Exact reason equation

The authority derives reason from final task state, then the raw time-limit
fact, in this exact priority:

```text
if all_j task1[j] == COMPLETED:
  reason = ALL_TASKS_COMPLETED
elif all_j task1[j] in {COMPLETED, TEAM_INFEASIBLE}:
  reason = NO_FEASIBLE_TASKS_REMAIN
elif time_limit_reached:
  reason = TIME_LIMIT
else:
  reason = NONE
```

Thus a completion or TEAM transition on the horizon wins over TIME_LIMIT.
`TerminationReason` is a field of the frozen `LifecycleTransitionResult`; it
is not a post-result Gym decoration.

Physical flags define a fail-closed mapping boundary:

- the authority may derive `ALL_TASKS_COMPLETED` or
  `NO_FEASIBLE_TASKS_REMAIN` even if `physical_terminated` is false;
- if `physical_terminated` is true, final task state must map to one of those
  two reasons;
- `physical_truncated` without `time_limit_reached` is unsupported and fails
  closed;
- `time_limit_reached` requires `physical_truncated`, as the frozen facts
  contract already enforces;
- `bad_transition` is only a bootstrap/transport fact and never a fifth
  reason; if it is the sole non-time-limit truncation cause, the transition is
  unmappable and fails closed;
- any physical terminated/truncated boundary that cannot satisfy these rules
  finalizes no result and mutates no lifecycle state.

Only after successful result finalization and state/generation commit is the
final reason projected to Gym outputs:

| Final reason | `terminated` | `truncated` |
|---|---:|---:|
| `NONE` | false | false |
| `ALL_TASKS_COMPLETED` | true | false |
| `NO_FEASIBLE_TASKS_REMAIN` | true | false |
| `TIME_LIMIT` | false | true |

The projection follows the finalized reason even when raw time limit and a
higher-priority task-terminal condition occur together.

### 11.2 Exact authority transaction order

One selected full batch follows exactly these stages:

1. Validate exact event profile, producer/authority identities, facts
   integrity, generation context, dimensions, and the complete versioned
   prestate/invariants. Capture one immutable store snapshot and version.
2. Clone candidate storage and derive completion, deduplicated release,
   new/updated permanent failed pairs, health, ownership, task state, base
   robot state, completion counters, and the logical event candidate without
   mutating live state.
3. Derive `TEAM_INFEASIBLE` and its edge only from `updated_failed`.
4. Apply final robot projection P, derive the priority-ordered final reason,
   and finish the ordered event/result candidate.
5. Perform receipt-independent, full-batch prevalidation of every B0 equation,
   enum/state/ownership inverse, counter, TEAM, reason, event, and frozen
   result-input invariant. This stage does **not** call the frozen result
   factory, because the factory requires an issued receipt.
6. Call `TransitionConsumeLedger.consume` exactly once for the entire facts
   batch and receive one exact issued receipt.
7. Call the frozen result factory/finalizer exactly once with that same
   receipt. It revalidates frozen result invariants and claims the receipt only
   after successful result construction.
8. Inside the coordinator's exclusive, non-observable success tail, first
   perform the already prevalidated no-fail single `LifecycleStateStore`
   pointer/state swap against the captured version. Then call the B0-1B clock
   commit as the final internal success marker. Completion of that clock
   commit constitutes authoritative success; only after both operations
   succeed may the result/state be published.
9. Project the finalized result reason to `terminated/truncated`, publish the
   immutable pre-reset handoff, and only then permit the environment autoreset
   path.

Stage 5 mirrors and strengthens the frozen factory checks; it does not create
a second result object or claim factory authority. Store version and
generation context are rechecked/prepared under the coordinator transaction
lock before Stage 6 so ordinary stale-state failures occur before consume.

The logical atomicity boundary is publication under one exclusive coordinator
transaction. State candidate application is one validated pointer/state swap,
not a sequence of externally visible tensor writes. No observer can see a
finalized result with old state, new state without its result, or an advanced
generation before authoritative success.

An invalid row in Stages 1–5 rejects the entire batch with:

```text
no ledger consume
no result
no state mutation
no generation commit
no Gym publication
```

The facts producer may already have allocated and burned a consume-once token.
That token is independent of generation. The B0-1B transition candidate
remains outstanding and committed transition generation remains unchanged
until Stage 8 authoritative success; no cancel, rollback, or token reuse is
introduced.

Because ledger/factory/store/clock are distinct guarded authorities, an
unexpected exception after receipt issuance is not recoverable as an ordinary
transaction retry. The coordinator publishes nothing, marks the runtime
poisoned, and requires teardown. It never rolls back, silently resumes, resets
the candidate, or calls ledger consume again. This fatal tail rule is an
implementation obligation; it does not pretend that multiple mutable objects
have a rollback transaction they do not possess.

## 12. Receipt capability versus B0 runtime policy

The frozen contract remains exact:

```text
ledger consume succeeds
-> receipt is issued and unfinalized

result finalization validation fails
-> receipt remains issued and unfinalized
-> corrected finalization with that same receipt remains contract-legal

result finalization succeeds
-> receipt is claimed/finalized
-> successful reuse is rejected
```

B0 does not remove or redefine that capability. In particular, a failed
factory call does not authorize a second ledger consume for the same facts.

The normal B0 coordinator policy is stricter operationally: complete Stage-5
prevalidation is intended to make an internal Stage-7 invariant failure
impossible. If it nevertheless occurs, the coordinator treats it as a fatal
implementation invariant violation. It performs no automatic correction or
retry, does not consume again, does not publish, and does not commit the state
store or generation clock. The still-valid contract-level same-receipt retry
capability remains available to frozen contract tests and future explicitly
reviewed recovery designs; it is simply not exercised by normal B0 runtime.

## 13. Direct B0-2 implementation/test oracle

No implementation is authorized by this document. A later authorized B0-2
slice must translate, without reinterpretation, at least these groups:

1. exact prestate enum/ownership/current-task/TEAM/version validation;
2. all 32 owned-pair `C/F/R/U/Rc` combinations, including every invalid row;
3. multi-cause release deduplication and completion masking of release;
4. owner-attributed completion count for `C`, `C+R`, `C+U`, and `C+R+U`;
5. new versus cumulative failure and TEAM edge derivation;
6. recovery-only legality and all four prior robot-state rows;
7. healthy terminal waiting, unavailable terminal preservation, and TIME_LIMIT
   no-synthetic-release behavior;
8. task preservation and completion/release from all three active phases;
9. deterministic logical-event deduplication, payloads, causal source, total
   ordering, contiguous ordinals, and repeated-run identity;
10. reason priority and every supported/unsupported physical flag mapping;
11. one-invalid-row full-batch rejection before ledger consume/state/clock;
12. exact one-consume/one-finalize success and frozen same-receipt retry
    capability versus coordinator fail-stop policy;
13. token-gap with the same outstanding generation candidate and success-only
    generation commit;
14. capability isolation proving the environment/resolver cannot access
    producer, ledger, receipt, factory, writable state, or clock commit;
15. absence of direct entrypoint wiring until the separately authorized
    integration/runtime-ready gate.

Pure evidence for these groups will still not establish real IK/collision/
terminal-alignment detector identity, environment pre-reset integration,
terminal-sidecar transport, or Isaac runtime evidence. Those claims require
their own authorized phases.

## 14. Unresolved numeric and later-phase boundary

All eleven method numeric TBDs remain unresolved and in their frozen order:

```text
top_k_tasks_per_robot
local_robot_cap
local_task_cap
pair_abs_threshold
pair_rel_threshold
component_abs_threshold
component_rel_threshold
transfer_penalty
rejection_penalty_scale
alignment_time_constant
assignment_retry_cadence
```

B0-2D selects no default, threshold, penalty, constant, or cadence. These
numbers cannot alter the permanent-failure/TEAM equation or the transition
matrix in this document.

Still outside B0-2D and unauthorized are the B0-2 implementation itself, the
environment pre-reset hook, real execution reporters, state store/authority/
ledger/result runtime, terminal sidecar, event scheduler/observation path,
Phase-B resolver and assignment commit, DVM/trainer behavior, reward runtime,
diagnostic sink, checkpoint-ready V3, and every B0-3+/B/C/D/E activity.

## 15. Evidence basis and final handoff

This closeout rechecked, without editing, the canonical authorities:

- `assignment_lifecycle_transition_contract.py`: exact enum identities, facts
  ownership/conflict rules, consume ledger, result/factory/receipt binding,
  TEAM and reason descriptor;
- `assignment_event_contract.py`: exact event enum declaration order, payload
  bindings, authority/token/generation identity, trigger eligibility, and
  canonical event IDs;
- `assignment_profile_contract.py`: event-profile interface-only/default-off
  boundary;
- `PHASE_B0_PRE_RESET_LIFECYCLE_AUTHORITY_RUNTIME_DESIGN.md`: physical/reset
  ordering, owner-gated facts source, cumulative failure, atomicity, and
  deferred integration constraints;
- the B0-1A and B0-1B implementation reports: pure producer responsibility,
  consume token behavior, retained environment-domain clock, outstanding
  candidate, and success-only generation commit.

The frozen result factory intentionally does not prove every B0 equation in
this addendum. B0-2 must prevalidate the stronger matrix, state inverse, robot
projection, event/result equivalence, TEAM equation, and reason equation
before consume. This is an implementation obligation, not a contract gap.

Final decision:

```text
STOP condition:
  not triggered

frozen schema change:
  not required

progression facts:
  deferred and not claimed

next action:
  GPT/user review of this design-only closeout

implementation authorization inferred:
  none
```

Work stops at this design handoff. B0-2 implementation must not begin without
new explicit authorization.
