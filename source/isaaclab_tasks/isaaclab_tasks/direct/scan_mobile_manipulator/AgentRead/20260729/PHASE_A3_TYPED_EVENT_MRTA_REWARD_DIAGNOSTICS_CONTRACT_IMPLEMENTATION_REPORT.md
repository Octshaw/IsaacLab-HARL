# Phase A3 Typed Event / MRTA / Reward / Diagnostics Contract Report

## 1. Classification

```text
classification:
  PHASE-A3-IMPLEMENTATION-COMPLETE-AWAITING-GPT-REVIEW

A1:
  complete
  review passed

A2:
  complete
  review passed

A3:
  complete by pure/schema evidence

A4–A6:
  not entered

Phase B0/B/C/D/E:
  not entered

commit:
  none
```

This classification is limited to pure interfaces, exact-schema validation,
deterministic serialization, and pure/static regressions. Runtime evidence is
explicitly absent.

## 2. Authorization and scope

The direct authorization was the 2026-07-29 instruction classified
`PHASE-A3-IMPLEMENTATION-AUTHORIZED`. Work was limited to:

- three mutually exclusive typed record systems;
- nominal-cost/path, local-set, Top-K, DVM, proposal, and component DTOs;
- the frozen team-reward semantic configuration and a synthetic oracle;
- typed diagnostic payloads/envelopes without a logger or sink;
- the minimum A2 change needed to accept canonical typed lifecycle events;
- pure/schema tests and documentation.

No environment, state, wrapper, resolver runtime, runner, trainer, buffer,
runtime reward, checkpoint, entrypoint, scenario, YAML/JSON, or installed HARL
behavior was changed by A3.

## 3. Starting repository state

```text
starting HEAD:
  dca976001d8c53a9cfb424b468fa58d9fca367f6

recent commits:
  dca97600 docs(assignment): approve event-gated local MRTA design for Phase A
  e3febe41 docs(assignment): validate multi-condition late-training regression
  9d31b15f add deterministic baseline and cyclic pose-slot profiles ...

active interpreter:
  C:\isaacenvs\isaac45_harl\python.exe

starting index:
  empty
```

The starting worktree was the exact documented 25-path Phase A/A1/A2 cohort.
Those inherited changes include files forbidden for new A3 edits, but their
presence was known before A3 and they were not modified by this slice. The
ending 33-path cohort is the same 25 paths plus the eight new A3 production,
test, and report files. No unknown path appeared.

## 4. Files changed

A3 production additions:

- `assignment_event_contract.py`;
- `assignment_mrta_contract.py`;
- `assignment_team_reward_contract.py`;
- `assignment_event_gated_diagnostics_contract.py`.

Authorized A2 integration:

- `assignment_lifecycle_transition_contract.py` — only the canonical typed
  lifecycle-event boundary;
- `scripts/environments/test_assignment_lifecycle_transition_contract.py` —
  typed-event integration regressions while retaining the A2 suite.

A3 pure tests:

- `scripts/environments/test_assignment_event_gated_mrta_contract.py`;
- `scripts/environments/test_assignment_team_reward_contract.py`;
- `scripts/environments/test_assignment_event_gated_diagnostics_contract.py`.

Documentation:

- this implementation report;
- `AgentRead/TASK_PROGRESS.md`.

No `TASK_PROGRESS` archive was created. The previous handoff was 288 lines,
within the repository's approximate 200–300 line guideline, and the direct A3
instruction requested an in-place update rather than a mechanical archive.

## 5. Canonical module identities

The four production module keys are exactly:

```text
isaaclab_tasks.direct.scan_mobile_manipulator.assignment_event_contract
isaaclab_tasks.direct.scan_mobile_manipulator.assignment_mrta_contract
isaaclab_tasks.direct.scan_mobile_manipulator.assignment_team_reward_contract
isaaclab_tasks.direct.scan_mobile_manipulator.assignment_event_gated_diagnostics_contract
```

Each module checks its canonical `__name__` before Torch import or any
identity-bearing enum, dataclass, or custom exception. Package-internal
dependencies are canonical relative imports. There is no bare fallback,
`sys.modules` alias, duplicate authority enum, or mapping/JSON reconstruction
of canonical event records.

The event module imports the sole A2 `LifecycleAuthorityId`. The A2 transition
module has no top-level event import and performs a late canonical import only
inside lifecycle-event validation, avoiding a transition/event cycle.

## 6. Three disjoint record systems

The frozen enum counts and order are:

```text
LifecycleEventType:
  7
  TASK_COMPLETED
  TASK_RELEASED
  TERMINAL_PAIR_FAILURE_RECORDED
  TASK_BECAME_TEAM_INFEASIBLE
  ROBOT_BECAME_UNAVAILABLE
  ROBOT_RECOVERED
  ROBOT_NEEDS_ASSIGNMENT

AssignmentOpportunityType:
  1
  ASSIGNMENT_RETRY_DUE

ResolverDiagnosticType:
  3
  COMPONENT_ACCEPTED
  COMPONENT_REJECTED
  OWNERSHIP_TRANSFER_COMMITTED
```

`LifecycleEventRecord` binds its tuple ID to env/episode/transition/ordinal,
requires the canonical lifecycle authority and facts-consume token, enforces
`trigger_eligible=True`, and strictly matches each event type to one of
`TaskLifecycleEventPayload`, `RobotLifecycleEventPayload`, or
`PairFailureEventPayload`.

`AssignmentOpportunityRecord` independently binds its five-part ID,
`RETRY_SCHEDULER_V1`, assignment-tick and retry generations, and
`trigger_eligible=True`. It carries no lifecycle-authority stamp.

`ResolverDiagnosticRecord` binds its diagnostic ID and canonical producer,
accepts only its three typed payloads, and requires
`trigger_eligible=False`.

Strict placement validators establish:

- lifecycle results contain lifecycle events only;
- retry output contains opportunities only;
- local trigger input contains lifecycle events and opportunities only;
- resolver diagnostics remain in the diagnostic stream and never become a
  local trigger.

All records are frozen/slots objects with deterministic primitive immutable
serialization. There is no mutable details dictionary or universal payload.

## 7. Lifecycle result event integration

`LifecycleTransitionResult.lifecycle_events` now accepts an empty tuple or an
exact canonical tuple of `LifecycleEventRecord`. Finalization validates:

- authority identity equals the result authority;
- env ID exists in the result batch;
- episode and transition generations equal the corresponding result row;
- facts-consume token equals that row's consumed token;
- event ID and ordinal are internally bound;
- per-env ordinals are unique and input order is canonical
  `(env_id, ordinal)`.

Opportunity and resolver-diagnostic records fail the exact type boundary.
No A2 facts field, producer/authority identity, ledger/token/receipt behavior,
generation matrix, pair attribution, tensor immutability, or public A2
facts/result field order was changed. The A2 suite remains `11/11`.

## 8. Nominal cost and path contract

`NominalPairCostResult` validates caller-provided `[E,M,N]` `float32` tensors:

```text
nominal_cost = navigation_cost + alignment_cost
```

For `path_valid=True`, all three costs are finite and non-negative. For
`path_valid=False`, all three are canonical `NaN`; a large finite sentinel is
rejected. Cost unit, estimator version, device, exact shapes/dtypes, and all
four generation tensors are bound. The DTO does not estimate a path or choose
a cost algorithm.

All eight tensor DTOs use frozen/slots metadata, cloned/detached/contiguous
private snapshots, clone-returning accessors, exact device/shape/dtype checks,
supported-path mutation detection, and deterministic read-only mappings.

`UnresolvedParameterSpec(name, owner_phase, semantic_purpose)` contains no
numeric recommendation or selected default.

## 9. Local set and Top-K contracts

`LocalSetRequest` validates, but does not construct, a local set. In addition
to exact tensor/generation/ownership rules, it enforces:

- `needs_assignment_mask` is a subset of `seed_robot_mask`;
- lifecycle-event and opportunity robots are in `[0,M)` and are seeds;
- trigger records match their per-env generation row;
- resolver diagnostics cannot enter trigger collections;
- owner expansion rounds are exactly one;
- Top-K and cap values remain unresolved typed specs.

`LocalSetResult` validates rounds-used `0/1`, owner-added subset relations, and
overflow fail-closed disposition. It does not run owner expansion, overlap
merge, or cap truncation.

`TopKCandidateResult` preserves global task IDs, validates unique valid IDs per
robot, uses `-1`/`NaN` for invalid slots, and requires every nonnegative
current task to be retained as a valid candidate even when it would not be in
the caller's ordinary Top-K. It does not select or sort candidates.

## 10. DVM and proposal four-mask contract

`DecisionValidMaskSnapshot` validates the complete provenance conjunction:

```text
target_action_mask
== global_task_valid_mask
& failed_pair_legal_mask
& nominal_path_valid_mask
& local_topk_or_continue_mask
& ownership_preemption_legal_mask
& robot_available_mask

available_actions = concat(target_action_mask, noop_action_mask)

decision_valid_mask
== decision_opportunity_present
& robot_available
& semantic_legal_action_count >= 2
```

The constructor additionally requires transient, non-persisted caller context
for `current_task_id [E,M]`, `executing_mask [E,M]`, and
`idle_or_needs_assignment_mask [E,M]`. It verifies disjoint/complete
opportunity context, executing-current `CONTINUE` retention, executing noop
prohibition, and idle/needs noop availability without importing runtime state
enums.

The three row classes are:

| row | semantic actions | DVM | stored proposal meaning |
| --- | ---: | ---: | --- |
| decision-valid | at least 2 | true | real policy proposal |
| nonterminal forced | at least 1 | false | forced storage placeholder |
| no opportunity / no row | 0 | false | no policy or storage evidence |

`ProposalSnapshot` freezes the four-mask relations:

```text
policy_proposal_present_mask == decision_valid_mask
storage_row_present_mask == nonterminal_mask
forced_nondecision_mask
  == storage_row_present_mask & nonterminal_mask & ~decision_valid_mask
storage_row_present_mask
  == policy_proposal_present_mask | forced_nondecision_mask
policy_proposal_present_mask & forced_nondecision_mask == false
```

Policy rows retain sampled action/log-probability and `ProposalKind`.
`NOOP_IDLE` can be a real policy proposal. Forced rows are never proposals,
and rejected proposals remain policy rows. `ProposalSnapshot` deliberately has
no `effective_assignment` field.

## 11. Component contracts

`TransferComponentRequest` is a single-env caller-provided component snapshot.
It validates exact proposal meaning:

| baseline | proposed | kind |
| --- | --- | --- |
| `-1` | task | `CLAIM` |
| current task | same task | `CONTINUE` |
| current task | different task | `SWITCH` |
| `-1` | `-1` | `NOOP_IDLE` |

It rejects forced/non-policy proposals, illegal or invalid-cost pairs,
inconsistent assignment/ownership, missing baseline owner/task membership,
and dangling declared members. These are local relational assertions; the
module does not build a graph, find connected components, search proposal
subsets, arbitrate contention, calculate an objective, or commit state.

`TransferComponentResult` validates caller-staged whole-component output:

| result case | required relation |
| --- | --- |
| rejected component | baseline assignment/ownership/count/cost retained; zero transfers |
| accepted proposal | effective assignment equals the policy-proposed task |
| accepted component, false proposal | only a current-owner `CONTINUE` may be overridden |
| overridden `CONTINUE` | robot becomes unassigned (`-1`) and its task is taken by another accepted proposal |
| non-policy member | effective assignment remains baseline |
| outside-component robot/task | assignment/ownership remains baseline |
| accepted count | `assigned_count_after >= assigned_count_before` |
| owner transfer | counts only owned-task owner-to-different-owner changes |
| claim of unowned task | zero active-preemption transfers |

The legal `CONTINUE`-override regression uses three robots:

```text
baseline:
  [t0, t1, -1]

proposals:
  [SWITCH→t1, CONTINUE→t1, CLAIM→t0]

effective:
  [t1, -1, t0]

proposal_accepted:
  [true, false, true]
```

The former two-robot shape that reassigned an unproposed task to the displaced
owner is now rejected, as are partial false `CLAIM`, `SWITCH`, `NOOP_IDLE`,
uncovered `CONTINUE`, accepted count decrease, non-policy rewrites, and
outside-component rewrites.

`ComponentRejectionRecord` uses canonical rejection ordering and enforces one
penalty unit iff penalty-eligible. Overflow, post-snapshot system invalidation,
and terminal-transition rejection are non-policy-caused and not
penalty-eligible. A3 does not apply a reward penalty.

## 12. Team reward semantic contract

`TeamRewardContractSpec` freezes:

```text
wrapper_reward_source:
  AssignmentHarlWrapper.final_reward
base_reducer:
  mean_over_robot_axis
penalty_order:
  after_mean_before_broadcast
penalty_unit:
  once_per_penalty_eligible_rejected_component
broadcast_mode:
  identical_all_agents
critic_reward_source:
  broadcast_team_reward
valuenorm_source:
  all_physical_step_critic_returns
raw_per_agent_usage:
  diagnostics_only
```

The current ordered env reward-scale identity has six entries: global
coverage, own coverage, duplicate scan, reach violation, action rate, and time
penalty. The wrapper shaping identity has six entries: repeated-assignment
scale/grace, no-progress scale/grace/cap, and selected-path cost scale.

`rejection_penalty_scale` remains
`UnresolvedParameterSpec("rejection_penalty_scale", "phase_d_e",
"once_per_penalty_eligible_rejected_component")`.

For synthetic `float32` data, the pure oracle confirmed:

```text
base team reward:
  [[3.0], [4.0]]

penalty-eligible rejected component counts:
  [2, 1]

synthetic penalty scale:
  0.5

team reward:
  [[2.0], [3.5]]

learner reward:
  identical broadcast across every agent
```

The synthetic scale verifies ordering only; it is not a selected runtime
parameter. No wrapper reward or critic/ValueNorm route was changed.

## 13. Structured diagnostics contract

The exact enum cardinalities are:

```text
DiagnosticAvailability:
  3
DiagnosticKind:
  8
TransitionConsumeStatus:
  5
DefaultOffCohort:
  3
```

The eight typed payload field counts, independently pinned to the authoritative
literal order rather than inferred from the production descriptor, are:

```text
profile_route:          7
transition_authority:  13
assignment_tick:       22
proposal_resolution:   20
actor_update:           7
team_reward:            6
checkpoint_semantic:    8
default_off_identity:   7
```

`DiagnosticEnvelope` strictly binds kind to its canonical payload.
`DEFINED_NOT_PRODUCED` and `NOT_APPLICABLE` require `payload=None`; zero-filled
fake measurements are rejected. Proposal-resolution optional values obey the
four row classes, and non-policy rows cannot claim policy/reward attribution.
All floats are finite, fixed per-robot tuples require explicit expected `M`,
unknown fields fail, and serialization contains immutable Python primitives
only.

This module defines no logger, file sink, checkpoint producer, or runtime
measurement path.

## 14. Public schema descriptors

All four modules export deterministic deeply read-only descriptors with:

- contract/schema versions and exact field/enum order;
- public shapes, dtypes, generation identities, and placement rules;
- DVM construction context and mask equations;
- proposal/effective separation and component validation boundary;
- unresolved parameter identities and reward operation order;
- diagnostic kind/payload mapping and availability rules.

Tests recursively attempted mutation and verified deterministic equality.
Descriptors expose no tensor storage/version/detector/capability details,
logger path, checkpoint fingerprint, numeric TBD value, future evidence ID, or
runtime implementation.

## 15. Tests and command results

Final commands used the required interpreter and all exited `0`:

```text
python -c "import sys; print(sys.executable)"
  C:\isaacenvs\isaac45_harl\python.exe

python -m py_compile <five production contracts> <four pure tests>
  exit 0

test_assignment_event_gated_mrta_contract.py --json
  12/12

test_assignment_team_reward_contract.py --json
  6/6

test_assignment_event_gated_diagnostics_contract.py --json
  8/8

test_assignment_lifecycle_transition_contract.py --json
  11/11

test_assignment_profile_contract.py --json
  A1a 11/11
  A1b 5/5
  combined 16/16

test_assignment_profile_production_wiring.py --json
  10/10

test_assignment_initial_condition_contract.py --json
  9/9
```

Totals:

```text
A3 test groups:
  26/26

required A1/A2/initial-condition regression groups:
  46/46

combined pure/static groups:
  72/72
```

Development-time failures were resolved before the final run:

- A2 temporarily reported `10/11` while its typed-event test expectation and
  clean canonical harness were corrected;
- early reward/diagnostic fixtures reported `0/6`, `5/8`, and later `5/6`
  because a synthetic owner fixture and overly broad private-term checks were
  wrong;
- MRTA temporarily reported `11/12` because a negative fixture hit the earlier
  membership guard rather than its intended guard;
- an independent semantic review reproduced accepted count decrease, partial
  `SWITCH`, and automatic unproposed-task reassignment even after an earlier
  `12/12`; the validator and exact counterexamples were then added.

No failure remains in the final allowed suites.

A final independent, read-only component audit then replayed the half
`SWITCH`/`CLAIM`/`NOOP_IDLE`, count-decrease, and non-policy rewrite matrices,
confirmed the three-robot covered-`CONTINUE` case, and returned `PASS` for the
A3 pure/schema boundary. One multiline `conda run ... python -c` audit helper
invocation exited nonzero because Conda rejected a newline-containing command
argument; the identical pure matrix was rerun successfully with
`C:\isaacenvs\isaac45_harl\python.exe`. This was a command-transport failure,
not a contract/test failure, and it created no file change.

## 16. Side-effect audit

Clean-child checks observed unchanged Python/Torch RNG, cwd, environment,
`sys.path`, loggers/handlers, source hashes, and temporary file sets. NumPy
absence was preserved where applicable, and stdout/stderr remained empty.
A1 profile registry/class identity and A2 authority/facts identity/content
remained unchanged.

Static import/call inspection found no Isaac/AppLauncher, Isaac Sim, Omni,
HARL, actor distribution, optimizer/backward, graph/search/Top-K algorithm,
runtime resolver, checkpoint load/save, or file-write call in the four A3
production modules. No trailing whitespace was found in the A3 production and
test cohort.

The following were not run:

- Isaac or AppLauncher;
- environment/wrapper/resolver runtime smoke;
- actor forward/backward or training;
- playback, diagnosis, or formal evaluation;
- production checkpoint metadata or tensor I/O.

The initial-condition regression uses only its existing pure temporary
manifest fixtures; it did not read or write a user/model checkpoint.

## 17. Deferred runtime work

Explicitly deferred:

- production of real lifecycle events and retry opportunities;
- pre-reset facts capture and lifecycle-authority runtime placement;
- event scheduler and assignment-tick generation;
- real cost estimation, local-set construction, owner expansion, overlap
  merge, and Top-K selection;
- runtime DVM construction, actor-subset sampling, rollout storage, loss
  masking, advantage normalization, and HAPPO factor identity;
- component graph construction, arbitration, objective, and atomic ownership
  commit;
- team-reward reduction and rejection penalty in the runner;
- diagnostics aggregation/logger/sink;
- checkpoint v3, manifest/fingerprint integration, and checkpoint I/O;
- Isaac smoke, training, playback, and formal evaluation.

## 18. A4 schema-freeze readiness

The four descriptors, module keys, enum orders, DTO mapping field orders, and
constructor-only DVM legality context are ready to be consumed by a later
explicitly authorized A4 slice. This does not authorize A4.

`LocalSetResult` is not factory-bound to a specific `LocalSetRequest` in A3.
A4/runtime must compare generation and request/result association externally;
no current DTO field addition is required. Likewise, connected-component
membership and minimality remain runtime algorithm obligations, not A3
schema evidence.

## 19. Risks and blockers

No known blocker remains inside the authorized A3 pure/schema boundary.
Residual risks are:

1. all evidence is CPU pure/static; a `meta` tensor covers device mismatch but
   CUDA execution was not performed;
2. transient DVM current/execution context is validated only at construction
   and intentionally not serialized;
3. `LocalSetResult`/request association must be enforced by later wiring;
4. component connectedness, contention arbitration, objective improvement,
   and atomic commit remain unimplemented;
5. assigned-count validation assumes the event-updated baseline does not retain
   ownership for completed or team-infeasible tasks; lifecycle runtime must
   establish that prerequisite;
6. Top-K/cap/threshold/reward numeric parameters remain intentionally
   unresolved;
7. runtime default-off identity and checkpoint incompatibility still require
   later phase evidence.

These are deferred implementation obligations, not evidence that A3 runtime
behavior exists.

## 20. Final classification

```text
classification:
  PHASE-A3-IMPLEMENTATION-COMPLETE-AWAITING-GPT-REVIEW

pure/schema evidence:
  complete

runtime evidence:
  none

ending HEAD:
  dca976001d8c53a9cfb424b468fa58d9fca367f6

index:
  empty

installed HARL:
  unchanged

commit:
  none

A3:
  stopped for GPT/user review

A4–A6:
  not entered

Phase B0/B/C/D/E:
  not entered
```
