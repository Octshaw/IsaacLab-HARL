# Phase A3x-1 Event Profile Schema Descriptor Implementation Report

## 1. Classification

```text
classification:
  PHASE-A3X1-DESCRIPTOR-ONLY-IMPLEMENTATION-COMPLETE-AWAITING-GPT-REVIEW

A1:
  complete
  review passed

A2:
  complete
  review passed

A3:
  complete after targeted schema-freeze extension
  awaiting A3x-1 review confirmation

A3x-0:
  design accepted

A3x-1:
  complete by pure/descriptor evidence
  stopped for GPT/user review

A4a:
  blocked pending A3x-1 review
  not restarted

A4b/A5/A6:
  not entered

Phase B0/B/C/D/E:
  not entered

commit:
  none
```

This classification is deliberately narrow. It means that the frozen public
schema identities, projections, key order, references, validation boundaries,
and pure tests exist. It does **not** mean that any event observation builder,
retry scheduler, local-set/Top-K algorithm, resolver, terminal sidecar
transport, DVM-aware trainer, sequential-factor update, model, or V3 checkpoint
path has been implemented or executed.

The final root-agent verification completed with all required compile,
regression, V2-hash, and repository checks passing; sections 18--20 record the
exact results.

## 2. Authorization and scope

The direct authorization was:

```text
classification:
  PHASE-A3X1-DESCRIPTOR-ONLY-IMPLEMENTATION-AUTHORIZED
```

The sole implementation authority was the accepted A3x-0R freeze in
`AgentRead/202608/20260803/PHASE_A3X0_EVENT_SCHEMA_FREEZE_DESIGN.md`. The authorized
slice was limited to:

- one new canonical event-profile schema aggregate;
- descriptor-only v2 extensions to the MRTA, event, and transition contracts;
- the two public lifecycle-state enums frozen by A3x-0R;
- pure immutable semantic projections and exact static tests;
- this report and the concise `TASK_PROGRESS.md` handoff.

The slice did not authorize changes to environment, state, wrapper, runtime
lifecycle authority, observation construction, resolver, runner, trainer,
buffer, reward behavior, diagnostics sinks, scenario/YAML, V2 checkpoint code,
V3 manifest/fingerprint code, entrypoints, or installed HARL. It also prohibited
training, playback, evaluation, Isaac/AppLauncher, actor/critic construction,
optimizer work, checkpoint I/O, runtime diagnostics, commit, and choosing values
for any of the 11 numeric-TBD method parameters.

The implementation evidence therefore establishes only:

```text
schema definitions exist
exact key/order/value contracts are enforceable
canonical descriptor references can be resolved and drift-checked
descriptor output is deterministic and deeply read-only
existing DTO and record schema identities remain v1
```

## 3. Starting repository state

The required preflight established:

```text
starting HEAD:
  dca976001d8c53a9cfb424b468fa58d9fca367f6

recent commits:
  dca97600 docs(assignment): approve event-gated local MRTA design for Phase A
  e3febe41 docs(assignment): validate multi-condition late-training regression
  9d31b15f - add deterministic baseline and cyclic pose-slot profiles ...

active interpreter:
  C:\isaacenvs\isaac45_harl\python.exe

starting index:
  empty

starting git diff --check:
  exit 0
```

The starting worktree was the known 34-path A1--A4a/A3x cohort. It already
contained inherited modified and untracked Phase A files, including paths that
were forbidden for new A3x-1 edits. Those paths were treated as user-owned
baseline state: no reset, clean, checkout, deletion, or overwrite was used.
Preflight found no unknown worktree path and no staged change.

Line-ending warnings emitted by `git diff --check` for inherited tracked files
did not represent whitespace errors; the command exited successfully.

## 4. Files changed

The A3x-1 change set is intentionally confined to the following authorized
paths.

New production contract:

- `assignment_event_profile_schema_contract.py` -- canonical aggregate owner
  for scale, actor/shared schema, global unresolved-parameter inventory,
  DVM/factor training semantics, model/training projections, runtime readiness,
  and the 19-section ownership inventory.

Descriptor-only production modifications:

- `assignment_mrta_contract.py` -- public descriptor v2, action contract,
  local-candidate, cost/path, component projections, and nine domain triples;
- `assignment_event_contract.py` -- public descriptor v2 and scheduled retry
  opportunity projection/triple;
- `assignment_lifecycle_transition_contract.py` -- public descriptor v2,
  public task/robot lifecycle enums, and failure/termination projection.

Pure tests:

- new `scripts/environments/test_assignment_event_profile_schema_contract.py`;
- modified `scripts/environments/test_assignment_event_gated_mrta_contract.py`;
- modified `scripts/environments/test_assignment_lifecycle_transition_contract.py`.

Documentation:

- this report;
- `AgentRead/TASK_PROGRESS.md` (final handoff update is owned by the root agent).

No `TASK_PROGRESS` archive was created. The handoff remained within the
repository's approximate 200--300 line guideline, and this phase required a
targeted in-place update rather than a substantial historical rewrite.

No other production, configuration, checkpoint, entrypoint, external package,
or installed HARL file belongs to the A3x-1 delta.

## 5. Canonical module identity and import DAG

The new source has exactly one valid module identity:

```text
isaaclab_tasks.direct.scan_mobile_manipulator.assignment_event_profile_schema_contract
```

Its contract version is:

```text
assignment_event_profile_schema_contract_v1
```

The canonical `__name__` guard is required before dependency imports, Torch, or
identity-bearing enum/dataclass/exception definitions. Wrong or bare source
keys fail closed; the implementation has no bare-import fallback and creates no
`sys.modules` alias.

The dependency direction is one-way:

```text
assignment_profile_contract
assignment_lifecycle_transition_contract
assignment_event_contract
assignment_mrta_contract
assignment_team_reward_contract
assignment_event_gated_diagnostics_contract
    -> assignment_event_profile_schema_contract
    -> future assignment_checkpoint_contract_v3
    -> future semantic dispatcher
```

The aggregate resolves dependencies only under the fixed package prefix
`isaaclab_tasks.direct.scan_mobile_manipulator`. Domain contracts do not import
the aggregate in reverse. Ownership records serialize frozen module basenames,
while the resolver maps only those basenames to the canonical package; arbitrary
caller-provided module paths and bare lookups are rejected.

The aggregate is a pure contract module. It does not import Isaac, AppLauncher,
HARL runtime objects, checkpoint modules, runner/trainer/buffer modules, or the
environment/wrapper.

## 6. Event-profile root and scale contract

The aggregate root is exactly 11 ordered keys:

```text
contract_version
scale_contract
actor_schema
shared_schema
unresolved_parameter_inventory
decision_valid_training_contract
sequential_factor_contract
model_structure
training_contract
runtime_readiness_contract
v3_section_ownership
```

Its exact root version is
`assignment_event_profile_schema_contract_v1`; it has no free-form metadata,
notes, extensions, or arbitrary mapping slot. Nested public key counts are:

| Nested mapping | Exact keys |
|---|---:|
| `scale_contract` | 11 |
| `actor_schema` | 18 |
| `shared_schema` | 19 |
| `unresolved_parameter_inventory` | 6 |
| `decision_valid_training_contract` | 14 |
| `sequential_factor_contract` | 11 |
| `model_structure` | 28 |
| `training_contract` | 9 |
| `runtime_readiness_contract` | 6 |
| `v3_section_ownership` | 5 |

The scale contract is exactly:

```text
contract_version
M
N
ordered_agent_names
ordered_task_ids
scene_env_spacing
sim_dt_seconds
control_decimation
physical_control_step_seconds
episode_time_limit_seconds
episode_horizon_steps
```

with version `event_gated_scale_contract_v1`. It enforces positive exact
dimensions, unique nonempty ordered agent names, `ordered_task_ids ==
tuple(range(N))`, finite positive spatial/time scales, exact integer
decimation/horizon, and:

```text
physical_control_step_seconds = sim_dt_seconds * control_decimation
episode_horizon_steps = ceil(
  episode_time_limit_seconds / physical_control_step_seconds
)
```

Python `bool` is not accepted as an integer. Agent/task identity, horizon, and
derived-value mismatches fail closed. Action dimension and noop encoding are
not duplicated here; they remain owned by MRTA v2.

The frozen dimensions are evaluated from the same `M/N` scale authority:

```text
actor_obs_dim(M,N)  = 6*M*N + 30*M + 14*N + 2
shared_obs_dim(M,N) = 6*M*N + 31*M + 15*N + 8

M=3, N=50:
  actor dimension  = 1692
  shared dimension = 1751
  action dimension = 51
```

These are serialized interface identities, not evidence that a runtime
observation tensor has been built.

## 7. Actor schema descriptor

`actor_schema` has exactly 18 ordered top-level keys, 15 block records, and 12
ordered fields per record. Its identity is:

```text
schema_version:
  event_gated_global_actor_observation_v1
scope:
  global_fixed_width_per_actor_complete_team_state_v1
output_dtype:
  torch.float32
dimension_formula:
  6*M*N + 30*M + 14*N + 2
reference_dimension:
  M=3, N=50, dimension=1692
temporal_boundary:
  fact_updated_a0_pre_policy_no_same_tick_resolver_outcome_v1
```

The exact block order is:

1. `actor_robot_identity_one_hot`;
2. `global_robot_physical_table`;
3. `global_robot_lifecycle_table`;
4. `global_task_pose_table`;
5. `global_task_lifecycle_one_hot`;
6. `event_updated_task_ownership_one_hot`;
7. `event_updated_baseline_assignment_one_hot`;
8. `episode_permanent_failed_pair_mask`;
9. `assignment_tick_nominal_path_valid_mask`;
10. `assignment_tick_normalized_nominal_remaining_cost`;
11. `target_action_mask`;
12. `noop_action_mask`;
13. `assignment_trigger_context`;
14. `per_robot_workload`;
15. `episode_context`.

Each record serializes exact order, name, category, treatment, primitive shape,
source/serialized dtype, flatten rule, column order, semantic source,
visibility, and normalization rule. Global robot/task IDs are never locally
renumbered or repacked. The generation association key is:

```text
(env_id,
 episode_generation,
 transition_generation,
 assignment_tick_generation)
```

Tick-conditioned lifecycle/local-set/cost/DVM sources must have exact matching
generations before construction; mismatch is fail-closed. Ordinary no-tick and
terminal rows instead require the tick DTOs to be absent.

The eight-key normalization contract fixes environment-spacing/time/horizon
denominators, `wxyz` quaternion normalization/sign, zero fill accompanied by
false validity for invalid/no-tick cost observations, and a separate model
feature-normalization identity. The 15 ordered exclusions prevent local slot
repacking, Contract-C budget/private identities, record IDs, raw events,
proposal/log-prob/outcome leakage, same-tick resolver/effective assignments, and
future facts from becoming policy features.

No actor observation is constructed in A3x-1.

## 8. Shared schema and terminal sidecar descriptor

`shared_schema` has exactly 19 ordered top-level keys, 19 block records, and 10
ordered fields per record. Its identity is:

```text
schema_version:
  event_gated_global_centralized_observation_v1
construction_mode:
  global_fixed_width_centralized_v1
semantic_state_shape:
  ("E", "S")
runner_transport_shape:
  ("E", "M", "S")
critic_input_shape:
  ("B", "S")
runner_transport_mode:
  repeat_identical_semantic_shared_state_across_agent_axis_v1
dimension_formula:
  6*M*N + 31*M + 15*N + 8
reference_dimension:
  M=3, N=50, semantic_dimension=1751, runner_agent_count=3
```

The shared state stores actor blocks 2--15 once, without actor identity, then
adds five critic-only blocks:

```text
local_robot_mask
local_task_mask
owner_added_robot_mask
local_set_flags
termination_reason_one_hot
```

It is explicitly not a concatenation of all actor observations. Repetition
across the runner agent axis is transport metadata and does not change semantic
dimension `S`.

The terminal sidecar contract has exactly 15 keys. It binds finalized pre-reset
physical/lifecycle/a0/failed/workload/progress state and the finalized
`LifecycleTransitionResult.termination_reason`, while requiring:

```text
assignment_tick_present: false
path/cost: zero value and false validity
local-set blocks: all false
semantic action masks: all false
decision_valid: false
storage_row_present: false
policy_proposal_present: false
forced_nondecision_present: false
pre_reset_sidecar_required: true
reset_state_alias_forbidden: true
critic buffer ordering: terminal sidecar before new-episode initial row
```

This is an interface requirement only. A3x-1 does not implement sidecar
construction, autoreset transport, or critic-buffer insertion.

The shared descriptor carries 17 ordered exclusions: the actor's 15 exclusions
plus actor identity one-hot and duplicated actor-observation concatenation.

## 9. Ordinary no-tick and terminal row separation

The descriptor freezes two different row classes; they must not be collapsed:

| Property | Ordinary nonterminal no-tick | Terminal |
|---|---|---|
| Row class | `nonterminal_forced_nondecision` | `terminal_no_row` |
| Assignment tick | false | false |
| Semantic legal count | 1 | 0 |
| Action mask | current-task-only for executing; noop-only otherwise | target/noop/all available false |
| DVM | false | false |
| Forced action ID | unique legal task/noop ID | `-1` |
| Actor sampling | not called | not called |
| Storage row | present | absent |
| Policy proposal | absent | absent |
| Forced nondecision | present | absent |
| Resolver/component row | absent | absent |
| Critic treatment | ordinary valid physical-step sample | pre-reset boundary sidecar, not an extra transition/loss sample |

The ordinary row uses `proposal_snapshot_v1` only as deterministic historical
available-action/action storage. It does not fabricate an A3 DVM snapshot. The
terminal row creates no proposal, forced placeholder, local set, cost DTO,
resolver input, or action/log-prob storage. A fixed-shape `NO_ROW` carrier, if a
future transport needs one, remains semantic absence rather than a row.

This separation preserves fixed-physical-step critic semantics without turning
forced continuation/noop samples into actor decisions.

## 10. MRTA descriptor v2

The MRTA public descriptor version is bumped only at descriptor level:

```text
assignment_mrta_contract_v2
```

It adds four deeply read-only projections:

| Projection | Exact top-level keys | Version |
|---|---:|---|
| `action_contract` | 10 | `event_gated_action_contract_v1` |
| `local_candidate_semantics` | 24 | `event_gated_local_candidate_semantics_v1` |
| `cost_path_semantics` | 22 | `event_gated_cost_path_semantics_v1` |
| `component_semantics` | 28 | `event_gated_component_semantics_v1` |

The action contract uniquely owns `num_agents=M`, `action_dimension=N+1`,
global task IDs `0..N-1`, raw noop ID `N`, decoded noop `-1`, target-then-noop
action ordering, DVM/proposal schema references, and seven exact cross-section
invariants.

The local projection freezes event/needs-assignment seeds, global-ID Top-K,
current-task retention, exactly one owner-expansion round, no second-layer
recursion, outside-set preemption exclusion, transitive overlap merge,
post-merge recomputation, fail-closed overflow, and three unresolved triples.
It does not implement set construction or sorting.

The cost projection freezes `[E,M,N]` float32 navigation/alignment/nominal
expected-time matrices, exact nominal sum, per-tick recomputation, current-owner
remaining-time semantics, pair-specific alignment with a per-robot constant
fallback interface, explicit path-valid authority, and canonical NaN for invalid
pairs. It does not estimate paths or costs.

The component projection freezes proposal-only input, contention order,
complete connected components, all-accept/all-reject behavior, covered-owner
CONTINUE override, count gates, strict pair/component improvement equations,
transfer penalty placement, rejection order/attribution, atomic staging, and
forbidden search/subset/runner-up/unproposed-task behavior. It does not run a
resolver or commit ownership.

The nine MRTA-owned unresolved triples are the three local caps/Top-K values,
`alignment_time_constant`, and five pair/component/transfer thresholds. Existing
MRTA DTO versions and field order remain exactly:

```text
unresolved_parameter_spec_v1
nominal_pair_cost_result_v1
local_set_request_v1
local_set_result_v1
top_k_candidate_result_v1
decision_valid_mask_snapshot_v1
proposal_snapshot_v1
transfer_component_request_v1
transfer_component_result_v1
component_rejection_record_v1
```

The modified pure MRTA/event suite has already provided `13/13` passing
evidence; the final matrix is recorded in section 18.

## 11. Event descriptor v2

The event public descriptor version is:

```text
assignment_event_contract_v2
```

It adds `scheduled_assignment_opportunity_semantics`, an exact 12-key mapping
with version
`event_gated_scheduled_assignment_opportunity_semantics_v1`. The mapping owns
the `assignment_retry_cadence` triple and freezes:

- finalized physical `transition_generation` as the counter source;
- persistent-unassigned eligibility;
- anchor initialization and refresh;
- due equation against cadence;
- episode-local emitted retry generation;
- early lifecycle trigger behavior;
- assigned/unavailable/terminal/reset anchor invalidation;
- output as existing `AssignmentOpportunityRecord(ASSIGNMENT_RETRY_DUE)`.

It is a scheduler contract, not a scheduler implementation. No timer, anchor
state, retry record, assignment tick, or runtime side effect is created here.

The three existing record systems and their mappings remain unchanged:

```text
lifecycle_event_record_v1
assignment_opportunity_record_v1
resolver_diagnostic_record_v1
```

The descriptor still keeps lifecycle events, scheduled opportunities, and
post-resolver diagnostics disjoint; resolver diagnostics are not triggers.

## 12. Transition descriptor v2 and state enums

The transition public descriptor version is:

```text
assignment_lifecycle_transition_contract_v2
```

It is the unique public owner of these exact integer enum orders:

```text
TaskLifecycleState:
  AVAILABLE=0
  CLAIMED=1
  NAVIGATING=2
  ALIGNING=3
  COMPLETED=4
  TEAM_INFEASIBLE=5

RobotLifecycleState:
  EXECUTING=0
  NEEDS_ASSIGNMENT=1
  WAITING_FOR_TASK=2
  UNAVAILABLE=3

TerminationReason (unchanged):
  NONE=0
  ALL_TASKS_COMPLETED=1
  NO_FEASIBLE_TASKS_REMAIN=2
  TIME_LIMIT=3
```

`ROBOT_RECOVERED` remains a transient lifecycle event, not a robot state.

The exact 22-key `failure_termination_semantics` mapping freezes failed-pair
accumulation/reset, TEAM_INFEASIBLE derivation from episode-cumulative terminal
pair failures, path-invalid non-equivalence, terminal ownership release,
fact-update/a0/termination order, termination priority, `bad_transition`
transport boundary, unmappable-terminal fail-closed behavior, terminal no-row
semantics, and episode/transition/assignment-tick generation rules.

The descriptor-only extension leaves all A2 DTO/record identities and field
orders unchanged:

```text
execution_transition_facts_v1
lifecycle_transition_result_v1
transition_consume_receipt_v1
execution_facts_producer_contract_v1
unique_lifecycle_authority_v1
pair_attributed_execution_signals_v1
```

Consume-once ledger, producer/authority stamps, tensor alias isolation, result
factory, facts/result/receipt fields, and lifecycle finalization behavior are
unchanged. The modified transition suite has already provided `12/12` passing
evidence.

## 13. Ordered unresolved parameter inventory

The aggregate owns a six-key inventory mapping with version
`event_gated_unresolved_parameter_inventory_v1`, a seven-key reference-record
shape, and exactly 11 ordered names -- no twelfth parameter:

1. `top_k_tasks_per_robot`;
2. `local_robot_cap`;
3. `local_task_cap`;
4. `pair_abs_threshold`;
5. `pair_rel_threshold`;
6. `component_abs_threshold`;
7. `component_rel_threshold`;
8. `transfer_penalty`;
9. `rejection_penalty_scale`;
10. `alignment_time_constant`;
11. `assignment_retry_cadence`.

Each reference record is exactly:

```text
name
triple_owner_module
triple_owner_contract_version
triple_descriptor_key_path
expected_concrete_type
unit
legal_domain
```

The typed owner vocabulary is closed:

```text
PHASE_B_RUNTIME                              = phase_b
PHASE_D_REWARD                              = phase_d
PHASE_E_EVALUATION                          = phase_e
PHASE_B_RUNTIME_AND_PHASE_E_EVALUATION      = phase_b_e
PHASE_D_REWARD_AND_PHASE_E_EVALUATION       = phase_d_e
```

The aggregate owns order and concrete-value metadata only; each domain
descriptor uniquely owns `(name, owner_phase, semantic_purpose)`. Type semantics
exclude bool from `exact_int`, require exact finite float for `finite_float`,
and require an exact length-`M` tuple of finite nonnegative floats for
`tuple_finite_float_len_M`. No numeric value or default was selected.

## 14. Domain descriptor drift checks

The 11 canonical references are:

| # | Name | Owner/version | Descriptor path |
|---:|---|---|---|
| 1 | `top_k_tasks_per_robot` | MRTA v2 | `local_candidate_semantics.unresolved_parameters[0]` |
| 2 | `local_robot_cap` | MRTA v2 | `local_candidate_semantics.unresolved_parameters[1]` |
| 3 | `local_task_cap` | MRTA v2 | `local_candidate_semantics.unresolved_parameters[2]` |
| 4 | `pair_abs_threshold` | MRTA v2 | `component_semantics.unresolved_parameters[0]` |
| 5 | `pair_rel_threshold` | MRTA v2 | `component_semantics.unresolved_parameters[1]` |
| 6 | `component_abs_threshold` | MRTA v2 | `component_semantics.unresolved_parameters[2]` |
| 7 | `component_rel_threshold` | MRTA v2 | `component_semantics.unresolved_parameters[3]` |
| 8 | `transfer_penalty` | MRTA v2 | `component_semantics.unresolved_parameters[4]` |
| 9 | `rejection_penalty_scale` | team reward v1 | `unresolved_parameter` |
| 10 | `alignment_time_constant` | MRTA v2 | `cost_path_semantics.unresolved_parameters[0]` |
| 11 | `assignment_retry_cadence` | event v2 | `scheduled_assignment_opportunity_semantics.unresolved_parameter` |

Here `MRTA v2`, `event v2`, and `team reward v1` resolve only to their full
canonical module keys and exact contract versions. The aggregate extracts the
first three authoritative fields from each mapping and checks exact equality
with the global inventory. The existing five-key reward record remains v1; its
two reward-specific fields are not re-owned or modified.

Wrong module key, bare lookup, contract-version drift, missing/wrong key path,
index/order drift, triple drift, unknown owner value, or metadata drift fails
closed. Domain contracts do not import the aggregate, so drift checking does not
create a dependency cycle.

`validate_event_profile_domain_references()` is a narrow pure revalidation
surface for those exact frozen references. It adds no descriptor field and is
not part of future fingerprint identity; it exists so drift can be rejected
without runtime construction or arbitrary module lookup.

## 15. Model and training projections

`model_structure` is an exact 28-key immutable identity projection with version
`event_gated_model_structure_projection_v1` and status:

```text
interface_identity_only_not_runtime_verified
```

Key frozen values include:

```text
actor: HAPPO/StochasticPolicy
critic: VCritic/VNet
distribution: Categorical
actor schema/dimension: actor_schema version/formula
critic schema/dimension: shared_schema version/formula
action dimension: action_contract.action_dimension
actor_hidden_sizes: (256, 256)
critic_hidden_sizes: (256, 256)
activation: relu
feature_normalization: true
share_param: false
state type: EP
recurrent flags: false/false
recurrent_n: 1
initialization: orthogonal_
action_gain: 0.01
serialization: state_dict
save_entire_model: false
state_dict inventory: deferred checkpoint-ready manifest
```

The `(256,256)` critic identity follows the actual assignment runner projection:
both actor and critic read `algo_args["model"]["hidden_sizes"]` at
`assignment_harl_training.py:525-526`. The unconsumed YAML
`hidden_sizes_critic: [512,256]` is intentionally absent. The runner and YAML
were read only and not modified.

`training_contract` has exactly nine top-level keys. Its config-binding records
have exactly six ordered fields and preserve current HAPPO/config identity for
fixed physical-step rollout, standard GAE, all-valid-step critic returns and
ValueNorm, Adam/PPO settings, feed-forward non-shared actors, policy sequence,
serialization, and deferred runtime evidence. Config values are
`CONFIG_BOUND_CURRENT_IDENTITY`, not method parameters selected by A3x-1.

The sibling DVM actor-training contract has 14 keys. It freezes
`[T+1,E,1]` per-actor mask shape, the `[:-1]` training slice, independent
active/DVM conjunction, valid-count normalization, rollout-level actor-valid
advantage population, zero/singleton/multi-sample rules, empty-minibatch skip,
rejected-proposal inclusion, and no critic DVM use.

Its exact reduction and boundary literals include:

```text
training_slice:
  decision_valid_mask[:-1]_over_storage_row_present_nonterminal_rows_only_terminal_no_row_excluded
actor_valid_equation:
  actor_valid=active_mask AND decision_valid_mask
policy_loss_reduction:
  masked_mean=sum(actor_valid*policy_loss)/sum(actor_valid)
entropy_reduction:
  masked_mean=sum(actor_valid*entropy)/sum(actor_valid)
zero_valid_actor_rule:
  skip_actor_forward_backward_optimizer_factor_and_logger_update
critic_dvm_usage:
  not_used
```

The sequential-factor contract has 11 keys and freezes shared `[T,E,1]` factor
identity. Nondecision rows use the semantic equivalent of:

```python
effective_ratio = torch.where(
    decision_valid_mask,
    raw_ratio,
    torch.ones_like(raw_ratio),
)
```

An actor with zero valid rows does not evaluate ratios and leaves factor
unchanged. Terminal has no action/factor row; ordinary forced no-tick rows have
DVM false and ratio identity one. This is a serialized semantic literal only:
no buffer, trainer, factor, optimizer, forward, or backward operation was
implemented or run.

```text
factor_shape:
  (T,E,1)
agent_update_order_source:
  algo.fixed_order_current_false_uses_runner_random_permutation_rule
effective_ratio_equation:
  effective_ratio=torch.where(decision_valid_mask,raw_ratio,torch.ones_like(raw_ratio))
zero_valid_actor_rule:
  zero_valid_actor_skips_ratio_evaluation_and_leaves_factor_unchanged
agent_axis_rule:
  shared_factor_has_no_agent_axis;terminal_no_row_has_no_factor_or_action_row
```

## 16. V3 section ownership inventory

`v3_section_ownership` has exactly five top-level keys, 19 records, and six
ordered fields per record:

```text
order
section_name
owner_module
owner_contract_version
descriptor_key_path
projection_mode
```

Its version is `event_gated_v3_section_ownership_v1`; allowed projection modes
are only `inline_owned_mapping` and `canonical_reference`. Record order and
authority are:

| # | Section | Owner | Key path | Mode |
|---:|---|---|---|---|
| 1 | `identity` | profile v1 | `resolved_event_profile_mapping` | reference |
| 2 | `scale` | event-profile v1 | `scale_contract` | inline |
| 3 | `actor_schema` | event-profile v1 | `actor_schema` | inline |
| 4 | `shared_schema` | event-profile v1 | `shared_schema` | inline |
| 5 | `action_contract` | MRTA v2 | `action_contract` | reference |
| 6 | `transition_contract` | transition v2 | `$` | reference |
| 7 | `event_tick_contract` | event v2 | `$` | reference |
| 8 | `local_candidate_contract` | MRTA v2 | `local_candidate_semantics` | reference |
| 9 | `cost_path_contract` | MRTA v2 | `cost_path_semantics` | reference |
| 10 | `decision_valid_training_contract` | event-profile v1 | same root key | inline |
| 11 | `sequential_factor_contract` | event-profile v1 | same root key | inline |
| 12 | `component_contract` | MRTA v2 | `component_semantics` | reference |
| 13 | `reward_contract` | team reward v1 | `$` | reference |
| 14 | `failure_termination_contract` | transition v2 | `failure_termination_semantics` | reference |
| 15 | `diagnostics_contract` | diagnostics v1 | `$` | reference |
| 16 | `policy_sequence_contract` | profile v1 | `resolved_event_profile_mapping.event_gated_target_semantics` | reference |
| 17 | `model_structure` | event-profile v1 | `model_structure` | inline |
| 18 | `training_contract` | event-profile v1 | `training_contract` | inline |
| 19 | `runtime_readiness_contract` | event-profile v1 | `runtime_readiness_contract` | inline |

Tests resolve every canonical owner and dereference every path. Record order is
exactly `1..19`, section names are unique, and each semantic field has one
authority. The runtime-readiness mapping includes the complete six-key
unresolved inventory, not only a version pointer, so future canonical bytes
cannot silently omit content drift.

`validate_event_profile_v3_section_ownership_record()` is a narrow pure
validator/test seam. It accepts only one of the exact 19 records, fixed
canonical basenames, the two allowed projection modes, matching owner versions,
and resolvable frozen paths. It is not a descriptor section or fingerprint
field.

This inventory is not a V3 manifest. A3x-1 creates no V3 dataclass, canonical
bytes, fingerprint, save/load path, or checkpoint golden.

## 17. Descriptor immutability and privacy

All new and extended descriptors are recursively converted to read-only
mappings and tuples. No nested list or mutable dictionary is exposed. Repeated
getter calls are semantically deterministic; caller mutation attempts fail and
cannot modify source authority or a subsequent result.

The public representation uses only stable primitives: strings, exact
integers/floats/bools, tuples, and read-only mappings. It excludes tensors,
tensor versions/pointers, record storage handles, mutation-detector identity,
private digests, capability objects, factory seals, ledger layout, module
aliases, absolute/drive/user/host/process/time identity, checkpoint fingerprints,
RNG state, and runtime objects. Frozen public exclusion *literals* describe
what is forbidden but do not serialize the forbidden private object or handle.

The allowed public `state_dict_key_contract_version` is semantic identity only;
no actual model state-dict key inventory is present. Import/build/get operations
perform no file I/O, logging, stdout/stderr output, cwd/env/sys.path mutation,
RNG consumption, or registry mutation.

## 18. Tests and command results

All Python commands use:

```text
D:\miniconda3\Scripts\conda.exe run
  -p C:\isaacenvs\isaac45_harl
  python ...
```

The active interpreter was verified as
`C:\isaacenvs\isaac45_harl\python.exe`.

### Syntax verification

The seven changed production/test Python files are checked together with
`python -m py_compile`.

```text
py_compile:
  exit 0
  seven changed production/test Python files compiled
```

### Pure regression matrix

| Category | Suite | Result |
|---|---|---:|
| New A3x-1 | `test_assignment_event_profile_schema_contract.py` | **9/9 pass** |
| Modified A3 | `test_assignment_event_gated_mrta_contract.py` | **13/13 pass** |
| Modified A2/A3 | `test_assignment_lifecycle_transition_contract.py` | **12/12 pass** |
| Unchanged A3 | `test_assignment_team_reward_contract.py` | **6/6 pass** |
| Unchanged A3 | `test_assignment_event_gated_diagnostics_contract.py` | **8/8 pass** |
| Unchanged A1 | `test_assignment_profile_contract.py` | **16/16 pass** |
| Unchanged A1 production wiring | `test_assignment_profile_production_wiring.py` | **10/10 pass** |
| Unchanged A1/A2 boundary | `test_assignment_initial_condition_contract.py` | **9/9 pass** |
| V2 checkpoint core | `test_assignment_checkpoint_contract_core.py` | **28/28 pass** |

Required reporting totals:

```text
new A3x-1 tests:
  9/9 pass

modified A3/A2 tests:
  25/25 pass

unchanged A1/A2/A3 regressions excluding checkpoint core:
  49/49 pass

V2 checkpoint core:
  28/28 pass

combined total:
  111/111 pass
```

The aggregate suite covers canonical identity, wrong-key early failure, root and
scale validation, multiple dimension cases, exact actor/shared records,
ordinary/terminal semantics, all 11 parameter references and drift rejection,
model/training/DVM/factor identities, 19 ownership paths, deep immutability,
privacy, RNG/import/file/logging side effects, and prohibited-runtime imports.

No training, simulation, playback, evaluation, model, optimizer, or checkpoint
operation is part of this matrix.

## 19. V2 checkpoint preservation

The V2 checkpoint implementation and goldens are outside the A3x-1 edit set.
The frozen values are:

```text
assignment_checkpoint_contract.py SHA-256:
  8f220bb62bcacf108876bf02d97141f77af8761cced7669e9f73406d00b90bc0

legacy v2 canonical SHA-256:
  1b525f3d577f0064dc86e1f2231c7569bf0e46fa9735960937d475323d5cf60f

Contract-C v2 canonical SHA-256:
  88c8000cae494af36c441288659cf84fa428324784d1ea807a0d8e48654ae398
```

The source hash was verified at preflight and again at finalization. The two
canonical hashes were reconfirmed from the unchanged pure-core fixtures without
updating any golden:

```text
V2 core/hash final status:
  28/28 pass
  source and both canonical SHA-256 values exact match
```

No V2 parser, manifest, classification, canonicalization, source, bytes, hash,
or golden was modified. No checkpoint save/load or user/model file was opened.

## 20. Side-effect and boundary audit

| Boundary | A3x-1 result |
|---|---|
| Environment/wrapper/state/runtime lifecycle | unchanged |
| Observation/action-mask runtime construction | not implemented or run |
| Local set/Top-K/cost/resolver | not implemented or run |
| Reward/diagnostics runtime | unchanged; not run |
| Runner/trainer/buffer/GAE/ValueNorm/factor | unchanged; not run |
| Scenario/YAML | read only; unchanged by this slice |
| Actor/critic/optimizer/forward/backward | not constructed or run |
| Isaac/AppLauncher | not launched |
| Training/playback/evaluation | not run |
| Checkpoint I/O | not run |
| V3 manifest/fingerprint/canonical bytes | not created |
| Installed HARL/site-packages | unchanged |
| Commit | none |
| A4a | not restarted |

The tests are pure/static source/module checks. They do not prove runtime
transport or behavior. The aggregate contract's `runtime_readiness_contract`
therefore remains:

```text
projection_version: event_gated_runtime_readiness_projection_v1
profile readiness: interface_only
unresolved status: all_11_unresolved
runtime_execution_authorized: false
checkpoint_weight_use_authorized: false
```

Final repository audit:

```text
ending HEAD:
  dca976001d8c53a9cfb424b468fa58d9fca367f6

git diff --check:
  exit 0

index:
  empty

unknown or unauthorized A3x-1 paths:
  none
```

## 21. Deferred runtime and A4a work

The following are explicit future work and are not implied by this report:

- resolve and validate all 11 numeric-TBD method parameters in their owner
  phases;
- implement the event update -> termination -> trigger merge -> local set ->
  cost -> Top-K -> mask/DVM -> policy -> resolver -> atomic commit runtime;
- construct 1692D actor and 1751D centralized shared observations;
- implement scheduled retry anchors and retry emission;
- implement terminal pre-reset shared-state sidecar transport without an actor
  row;
- implement proposal/effective separation in runtime storage and logging;
- implement DVM-aware actor loss/entropy/advantage normalization and safe
  zero-valid actor skip;
- implement per-agent `torch.where` ratio identity in HAPPO sequential factor;
- implement TEAM_INFEASIBLE runtime derivation/termination and Phase D reward;
- restart A4a only after GPT/user review passes A3x-1;
- under a future authorization, build the first V3 interface manifest and
  fingerprint from these unique owners;
- construct a model/state-dict inventory only for a separately authorized
  checkpoint-ready contract.

A4a remains blocked. A4b/A5/A6 and Phase B0/B/C/D/E have not been entered.

## 22. Risks and blockers

The descriptor implementation found no architectural blocker inside the
authorized pure slice. The material future risks are:

1. **Terminal autoreset boundary.** The current runtime must eventually preserve
   finalized pre-reset critic state without inventing an actor/storage row.
2. **DVM/factor integration.** Masking only final actor loss would still allow a
   nondecision ratio to contaminate later HAPPO factors; runner, buffer, and
   trainer changes remain necessary.
3. **Numeric readiness.** All 11 method values are intentionally unresolved, so
   runtime and weight use remain fail-closed.
4. **Projection versus execution.** Static model/config identities can drift
   from a future constructed route; runtime evidence and state-dict inventory
   are still required.
5. **Canonical ownership.** Future V3 code must consume these 19 owner records,
   not duplicate values from prose or accept bare module/path lookup.
6. **Generation coherence.** Future builders must enforce a single finalized
   generation across lifecycle, local set, cost, masks, DVM, and proposal.
7. **Default behavior.** The current Phase 9G/V2 runtime has not been changed or
   behaviorally compared in this descriptor-only slice.

All final compile/regression/hash/git checks passed. No blocker, schema
relaxation, or scope expansion was required.

## 23. Final classification

The final verified implementation classification is:

```text
classification:
  PHASE-A3X1-DESCRIPTOR-ONLY-IMPLEMENTATION-COMPLETE-AWAITING-GPT-REVIEW

event-profile schema descriptor:
  implemented

MRTA descriptor:
  assignment_mrta_contract_v2

event descriptor:
  assignment_event_contract_v2

transition descriptor:
  assignment_lifecycle_transition_contract_v2

DTO/record schemas:
  unchanged

runtime assignment behavior:
  not implemented

V3 manifest/fingerprint:
  none

checkpoint I/O:
  none

Isaac/AppLauncher:
  not run

training/playback/evaluation:
  not run

installed HARL:
  unchanged

commit:
  none
```

The recommended next action is a narrow GPT/user review of this A3x-1
descriptor evidence. Do not restart A4a or enter runtime implementation until
that review explicitly passes.

```text
A3x-1:
  stopped for GPT/user review

A4a:
  not restarted

A4b/A5/A6:
  not entered

Phase B0/B/C/D/E:
  not entered
```
