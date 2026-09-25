# Phase A5 Diagnostics and Reward Semantic Configuration Report

## 1. Classification

```text
PHASE-A5-DIAGNOSTICS-REWARD-SEMANTIC-CLOSEOUT-COMPLETE-AWAITING-GPT-REVIEW
```

Phase A5 completed the authorized pure/schema/semantic closeout for the
already-frozen A3 diagnostics and team-reward contracts. The production
contracts, A3x event-profile authority, and A4 V3 interface descriptor did not
change. This report records test evidence only; it does not authorize or claim
runtime production, training, checkpoint-weight use, playback, or evaluation.

## 2. Authorization and scope

The authorized scope was limited to:

- reading the current repository and authoritative AgentRead documents;
- extending the two existing pure test suites
  `test_assignment_team_reward_contract.py` and
  `test_assignment_event_gated_diagnostics_contract.py`;
- proving that the frozen A3 reward/diagnostics meanings remain exact and are
  still bound into the unchanged A4 V3 interface fingerprint;
- creating this report and preparing a root-level `TASK_PROGRESS.md` update.

The phase explicitly excluded production behavior changes, diagnostic
producer/sink wiring, environment/wrapper/runner/trainer edits, numeric
parameter selection, Isaac/AppLauncher execution, training, playback, formal
evaluation, model construction, real checkpoint tensor I/O, and commits.

## 3. Starting repository state

```text
HEAD:
  dca976001d8c53a9cfb424b468fa58d9fca367f6

starting index:
  empty

starting worktree:
  inherited known A1-A4b implementation/documentation cohort
  no unknown A5 production edit

A1-A3x:
  complete; review passed

A4a:
  complete; review passed

A4b:
  complete; review passed

A5 starting test baselines:
  reward       6/6
  diagnostics  8/8
```

The report path did not exist at Phase A5 start. No commit was made.

Root finalization confirmed:

```text
ending HEAD:
  dca976001d8c53a9cfb424b468fa58d9fca367f6
ending worktree:
  49 paths = inherited 48-path A1-A4b cohort + this authorized A5 report
  13 tracked modified + 36 untracked
ending index:
  empty
ending git diff --check:
  exit 0; inherited LF/CRLF conversion notices only
unknown/non-authorized A5 paths:
  none
```

## 4. Files changed

Authorized A5 changes are confined to:

```text
scripts/environments/test_assignment_team_reward_contract.py
scripts/environments/test_assignment_event_gated_diagnostics_contract.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/
  AgentRead/202608/20260808/
  PHASE_A5_DIAGNOSTICS_AND_REWARD_SEMANTIC_CONFIGURATION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/
  AgentRead/TASK_PROGRESS.md
  (root finalization only)
```

No production contract, environment, wrapper, resolver, reward path, runner,
trainer, buffer, checkpoint implementation, playback script, scenario, or
installed HARL file was modified by A5.

Final pure-test source fingerprints are:

```text
test_assignment_team_reward_contract.py:
  038600c047c6e1cc21b05bec8b00362f744db50b1e28d8d8cfd3b8a4bea040ba

test_assignment_event_gated_diagnostics_contract.py:
  22ca7d788cc703a6e7bcee20e7011af982ee7a17c94160d3653d4c08537ddbf2
```

```text
final report line count:
  731
final TASK_PROGRESS line count:
  354
TASK_PROGRESS archive:
  not created
reason:
  targeted in-place handoff update; no historical rewrite or condensation
```

## 5. Production source immutability evidence

The four protected source files were hashed before and after the A5 test
changes. Every digest is byte-for-byte identical:

| Protected source | Before SHA-256 | After SHA-256 |
|---|---|---|
| `assignment_team_reward_contract.py` | `21c27d60ade6008fdeaa77e726bfdb7930fa1acf84a02c9a9457bab6335ca97c` | `21c27d60ade6008fdeaa77e726bfdb7930fa1acf84a02c9a9457bab6335ca97c` |
| `assignment_event_gated_diagnostics_contract.py` | `d013044170914df3b62bbb09dfbce34f29497ab644b7fb47225cbc4496e19a0a` | `d013044170914df3b62bbb09dfbce34f29497ab644b7fb47225cbc4496e19a0a` |
| `assignment_checkpoint_contract_v3.py` | `7995432b63c5e0befd8eae1d6f793889f681b07f61c53fadeba103932c787d16` | `7995432b63c5e0befd8eae1d6f793889f681b07f61c53fadeba103932c787d16` |
| `assignment_event_profile_schema_contract.py` | `04eb153f296196e8a098f071fdea3721e27893564b4fa2df81ff91fc088859ef` | `04eb153f296196e8a098f071fdea3721e27893564b4fa2df81ff91fc088859ef` |

This closes the A5 production-immutability gate. No contract version, field,
descriptor mapping, runtime route, or fingerprint authority was changed.

## 6. Diagnostic enum and envelope identity

The diagnostics tests independently pin enum member names, serialized values,
and declaration order rather than deriving expected values from the production
descriptor.

```text
DiagnosticAvailability:
  PRODUCED             -> produced
  DEFINED_NOT_PRODUCED -> defined_not_produced
  NOT_APPLICABLE       -> not_applicable

DiagnosticKind:
  PROFILE_ROUTE        -> profile_route
  TRANSITION_AUTHORITY -> transition_authority
  ASSIGNMENT_TICK      -> assignment_tick
  PROPOSAL_RESOLUTION  -> proposal_resolution
  ACTOR_UPDATE         -> actor_update
  TEAM_REWARD          -> team_reward
  CHECKPOINT_SEMANTIC  -> checkpoint_semantic
  DEFAULT_OFF_IDENTITY -> default_off_identity

TransitionConsumeStatus:
  FIRST_CONSUME
  DUPLICATE
  STALE
  FUTURE
  MISMATCH

DefaultOffCohort:
  D0_ABSENT
  D1_PRE_RESOLVED_VALID
  SCENARIO_CORRECTION
```

`DiagnosticEnvelope` remains schema
`event_gated_diagnostic_envelope_v1` with the exact dataclass and serialized
field order:

```text
schema_version
kind
resolved_profile
env_id
episode_generation
transition_generation
assignment_tick_generation
availability
payload
```

The test validates the actual asymmetric API precisely:

- `from_mapping()` accepts an exact-key **typed mapping** containing canonical
  enum and payload objects;
- that typed mapping reconstructs the envelope and produces the exact immutable
  primitive mapping through `to_mapping()`;
- missing/unknown keys, a wrong schema, a wrong enum identity, a wrong value
  type, and a wrong kind/payload binding fail closed;
- A5 does **not** claim that the primitive output of `to_mapping()` is accepted
  as an input to `from_mapping()`.

## 7. Eight typed payload union

`DiagnosticPayload` remains the exact union of eight canonical dataclasses. It
does not contain `Any`, `dict`, a universal details bag, or an arbitrary
metadata bag. The tests compare both `dataclasses.fields()` order and serialized
mapping order against independent literals and inspect the AST union itself.

| Kind | Canonical payload | Frozen fields | Count |
|---|---|---|---:|
| `PROFILE_ROUTE` | `ProfileRouteDiagnostic` | `profile_contract_version, resolved_variant, runtime_route, checkpoint_family, runtime_readiness, resolution_origin, event_target_semantics_contract_version` | 7 |
| `TRANSITION_AUTHORITY` | `TransitionAuthorityDiagnostic` | `facts_schema_version, result_schema_version, facts_producer_id, lifecycle_authority_id, consume_token, receipt_id, consume_status, generation_match, facts_producer_match, lifecycle_authority_match, pair_attribution_contract_version, pair_attribution_validated, observable_immutability_contract_version` | 13 |
| `ASSIGNMENT_TICK` | `AssignmentTickDiagnostic` | `assignment_tick_count, lifecycle_event_ids, lifecycle_causal_sources, assignment_opportunity_ids, assignment_opportunity_types, trigger_eligible_count, resolver_diagnostic_count, suppressed_resolver_diagnostic_trigger_count, local_robot_count, local_task_count, per_robot_decision_count, decision_valid_count, policy_proposal_count_by_kind, forced_storage_row_count, accepted_component_count, rejected_component_count, ownership_transfer_count, needs_assignment_duration, idle_with_available_task_count, failed_pair_count, team_infeasible_task_count, termination_reason` | 22 |
| `PROPOSAL_RESOLUTION` | `ProposalResolutionDiagnostic` | `robot_id, storage_row_present, policy_proposal_present, forced_nondecision, decision_valid, stored_row_kind, proposal_kind, stored_action_id, proposed_task_id, effective_assignment, proposal_accepted, proposal_effective_mismatch, component_id, component_size, rejection_reason, policy_caused, penalty_eligible, ownership_transfer_count, local_cost_before, local_cost_after` | 20 |
| `ACTOR_UPDATE` | `ActorUpdateDiagnostic` | `actor_id, decision_valid_sample_count, skipped_actor_update_count, skipped_minibatch_count, singleton_advantage_fallback_count, nondecision_factor_identity_violation_count, reduction_denominator` | 7 |
| `TEAM_REWARD` | `TeamRewardDiagnostic` | `wrapper_final_reward_mean, policy_rejected_component_count, rejection_penalty_scale, team_reward, broadcast_agent_count, broadcast_equal` | 6 |
| `CHECKPOINT_SEMANTIC` | `CheckpointSemanticDiagnostic` | `manifest_format_version, manifest_kind, profile_name, checkpoint_family, fingerprint_sha256, purpose, compatibility_classification, runtime_readiness` | 8 |
| `DEFAULT_OFF_IDENTITY` | `DefaultOffIdentityDiagnostic` | `cohort, surface, evidence_label, expected_digest, actual_digest, matched, deferred_reason` | 7 |

The frozen count sequence is therefore exactly:

```text
7 / 13 / 22 / 20 / 7 / 6 / 8 / 7
```

Each class has an explicit positive constructor reconstruction plus missing
field, unknown field, and wrong-type negatives. All five diagnostic float
fields reject `NaN`, positive infinity, and negative infinity (15 negative
cases). Both fixed-`M` tuples in `AssignmentTickDiagnostic` reject length
mismatch.

## 8. Phase availability semantics

The authoritative Phase-A availability boundary is independently pinned in the
test:

```text
static semantic evidence may be constructed in Phase A:
  PROFILE_ROUTE
  CHECKPOINT_SEMANTIC
  DEFAULT_OFF_IDENTITY

runtime producers do not exist in Phase A:
  TRANSITION_AUTHORITY
  ASSIGNMENT_TICK
  PROPOSAL_RESOLUTION
  ACTOR_UPDATE
  TEAM_REWARD
```

The production descriptor intentionally provides generic availability/payload
rules, not a per-kind phase table. Therefore this is an authoritative test-level
phase fixture combined with no-producer/no-sink evidence; the report does not
claim that the production descriptor itself enforces the phase table. No
contradiction between the frozen authority and production contract was found.

The three static `PRODUCED` objects are pure semantic test objects. They are not
runtime measurements and do not imply a logger or sink.

## 9. DEFINED_NOT_PRODUCED / NOT_APPLICABLE behavior

For each of the five later-runtime-producer kinds, A5 constructs a valid
zero/fake-empty typed payload and proves both of these envelopes reject it:

```text
DEFINED_NOT_PRODUCED + non-None typed payload -> reject
NOT_APPLICABLE       + non-None typed payload -> reject
```

The only valid form for either unavailable state is `payload=None`. Ten
explicit negative cases prevent zero counts, empty tuples, false flags, zero
floats, or fabricated IDs from masquerading as a produced measurement.

For each of the three static-evidence kinds, A5 also proves:

```text
PRODUCED + exact typed payload -> accept
PRODUCED + None                -> reject
PRODUCED + wrong payload type  -> reject
```

## 10. Proposal-resolution diagnostic relations

The frozen four-row relations remain exact:

- `policy_proposal_present == decision_valid`;
- forced nondecision means a storage row exists while decision-valid is false;
- no-row means no policy proposal and no forced storage row;
- a forced nondecision cannot claim policy-proposal presence;
- a non-policy row cannot claim proposal acceptance, proposal/effective
  mismatch, policy-caused rejection, or penalty eligibility;
- a rejected real proposal remains a policy proposal and remains
  decision-valid;
- `NOOP_IDLE` may be a real policy proposal;
- accepted proposals cannot carry a rejection reason or mismatch;
- overflow, post-snapshot invalidation, and terminal-transition rejection
  cannot be policy-caused or penalty-eligible.

These are DTO/schema tests only. A5 did not execute the resolver or assert that
runtime proposal/effective records are currently produced.

## 11. Team reward canonical spec

The exact semantic sequence remains:

```text
AssignmentHarlWrapper.final_reward
→ mean_over_robot_axis
→ once-per-penalty-eligible-component penalty
→ identical_all_agents broadcast
```

The frozen `TeamRewardContractSpec` order and identities remain:

```text
schema_version:
  event_gated_team_reward_contract_v1
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

The current ordered six-entry base-environment reward-scale identity and
six-entry wrapper-shaping identity remain fingerprinted. Raw per-agent reward
is diagnostics-only under the target contract; this phase does not connect the
target team reward to the learner.

## 12. Mean → component penalty → broadcast oracle

The pure synthetic oracle confirms the operation order with:

```text
wrapper-final per-agent reward mean:
  [[3.0], [4.0]]

penalty-eligible component counts:
  [2, 1]

test-only rejection penalty scale:
  0.5

team reward after component-once penalty:
  [[2.0], [3.5]]
```

The formula is:

```text
base_team_reward[e]
  = mean_i(wrapper_final_reward[e,i])

team_reward[e]
  = base_team_reward[e]
    - rejection_penalty_scale
    * policy_rejected_component_count[e]

learner_reward[e,i]
  = team_reward[e]
```

`0.5` is test data only. It is not a selected configuration value, default,
checkpoint parameter, or authorization to run the target reward path.

## 13. Broadcast equality

The oracle proves that every agent in an environment receives an identical
copy of the final team reward and that the result shapes remain:

```text
base_team_reward: [E,1]
team_reward:      [E,1]
learner_reward:   [E,M,1]
```

For the frozen fixture, `M=3` and the final values are broadcast exactly to all
three agents. The reward suite also checks exact `float32`, finite values, device consistency,
no autograd requirement, alias isolation, protected-result mutation detection,
and non-equivalence of incorrect operation orders. This remains a pure oracle;
no critic buffer, ValueNorm instance, or runtime reward tensor was modified.

## 14. Rejection penalty eligibility/unit

The canonical unit is one per unique penalty-eligible rejected component, not
one per member robot and not one per per-robot diagnostic row. Tests exercise
eligible and ineligible `ComponentRejectionRecord` outcomes and preserve:

```text
penalty unit:
  1 iff the canonical component rejection is policy-caused and penalty-eligible
  0 otherwise
```

Overflow fail-closed, post-snapshot system invalidation, and terminal transition
remain non-policy reasons with zero penalty units. A5 did not activate a
rejection penalty in reward or training.

The exact pure evidence is:

```text
eligible canonical component records:
  [1, 1]

non-policy overflow / post-snapshot / terminal records:
  [0, 0, 0]
```

## 15. Unresolved rejection_penalty_scale

The parameter remains the exact unresolved triple:

```text
name:
  rejection_penalty_scale
owner_phase:
  phase_d_e
semantic_purpose:
  once_per_penalty_eligible_rejected_component
```

No numeric default or resolved value was added. In the 11-entry V3 unresolved
inventory it remains entry 9 with the exact reference:

```text
owner module:
  assignment_team_reward_contract
owner contract:
  assignment_team_reward_contract_v1
descriptor key path:
  unresolved_parameter
name:
  rejection_penalty_scale
expected concrete type:
  finite_float
unit:
  team_reward_units_per_rejected_component
legal domain:
  value >= 0
```

## 16. V3 reward/diagnostics mapping preservation

The typed V3 `reward_contract` projection remains exact-equal to
`get_assignment_team_reward_contract_descriptor()`. The typed V3
`diagnostics_contract` field projection remains exact-equal to
`get_assignment_event_gated_diagnostics_descriptor()` with the frozen ten
fields:

```text
contract_version
schema_version
diagnostic_availability_order
diagnostic_kind_order
transition_consume_status_order
default_off_cohort_order
envelope_field_order
payload_type_by_kind
availability_rules
serialization
```

The diagnostics comparison uses typed section attributes so tuple-valued
semantic sequences are compared without confusing V3 JSON list normalization
with an authority change. Canonical bytes/hash are checked separately.

No A5-only field was added. In particular, neither section contains a logger
path, sink configuration, file format, runtime evidence ID, TensorBoard key, or
numeric penalty selection. Section ownership remains canonical-reference
ownership by reward v1 and diagnostics v1.

## 17. V3 checkpoint-ready unresolved gate

The A4a checkpoint-ready builder remains typed fail-closed. Runtime readiness
still reports:

```text
unresolved_parameter_resolution_status:
  all_11_unresolved
runtime_execution_authorized:
  false
checkpoint_weight_use_authorized:
  false
```

`rejection_penalty_scale` remains in the rejection reason/inventory. Supplying
the synthetic test value `0.5` does not resolve the parameter, does not create a
checkpoint-ready manifest, and does not authorize weights. V3 remains an
interface semantic descriptor only.

## 18. Old-route no-sink/no-info/no-file/no-RNG evidence

Clean-child tests resolve the `legacy` and `lifecycle_contract_c` profiles
through the pure canonical profile API and confirm both retain their existing
ready routes. The event-gated profile remains `interface_only` and its runtime
readiness guard raises the expected typed denial.

The same isolated child snapshots and rechecks:

- the temporary working-directory file/directory inventory;
- Python RNG state;
- Torch RNG state;
- environment variables, cwd, and `sys.path`;
- root handlers and root logger level;
- full named-logger names, levels, propagation, disabled state, and handler
  identities;
- A1 registry/profile identity and A2 lifecycle authority/facts identity;
- source hashes and stdout/stderr.

It then constructs the pure reward oracle and reward/diagnostics descriptors.
All snapshots remain unchanged. Static AST inspection finds no new event
diagnostic writes to `info`, `infos`, `extras`, or episode-info structures and
no logger/file/JSONL/CSV/TensorBoard/runtime sink wiring in the two A3 contracts.

This claim is deliberately scoped to the Phase-A event-gated reward and
diagnostics contracts. It does not claim that unrelated historical lifecycle
diagnostic code is globally absent.

## 19. Test and regression results

All Python commands used the mandated interpreter:

```text
D:\miniconda3\Scripts\conda.exe run
  -p C:\isaacenvs\isaac45_harl
  python ...
```

The required matrix is:

| Suite | Result |
|---|---:|
| team reward, previous 6 plus A5 6 | 12/12 |
| event-gated diagnostics, previous 8 plus A5 4 | 12/12 |
| A4a V3/semantic dispatcher | 12/12 |
| A4b checkpoint entry guard integration | 10/10 |
| A3x event-profile schema | 9/9 |
| A3 event-gated MRTA | 13/13 |
| A2 lifecycle transition contract | 12/12 |
| A1 profile contract | 16/16 |
| production profile wiring | 10/10 |
| initial-condition contract | 9/9 |
| V2 checkpoint core | 28/28 |

```text
required total:
  143/143
```

The optional pure training-run audit also passed:

```text
optional assignment training-run audit:
  4/4

required plus optional:
  147/147
```

The modified test files compile successfully with `python -m py_compile`.
No Isaac/runtime test was included in these counts.

## 20. V2/V3 golden preservation

V2 remains byte/hash exact:

```text
V2 contract source SHA-256:
  8f220bb62bcacf108876bf02d97141f77af8761cced7669e9f73406d00b90bc0

legacy canonical bytes:
  5509
legacy canonical SHA-256:
  1b525f3d577f0064dc86e1f2231c7569bf0e46fa9735960937d475323d5cf60f

Contract-C canonical bytes:
  7234
Contract-C canonical SHA-256:
  88c8000cae494af36c441288659cf84fa428324784d1ea807a0d8e48654ae398
```

The frozen V3 interface descriptor remains:

```text
V3 canonical bytes:
  67794

V3 interface SHA-256:
  03c33620e8324c034de5f9014dfd0cb76bef2fc06c99b15895f94b9981cb2b6a
```

Both V3 values are **unchanged**. A5 did not create a new fingerprint, update a
golden, or change canonicalization.

## 21. Side-effect audit

Static AST/call inspection of the pure reward and diagnostics contracts found
no:

```text
AppLauncher / omni / isaacsim / HARL runtime import
gym.make
torch.save / torch.load
open or Path.write_text/write_bytes
json.dump / csv.writer
SummaryWriter / wandb / logger handler creation
optimizer / backward / load_state_dict
resolver commit / environment step
runtime info/extras assignment
```

The A5 work performed no environment/wrapper/resolver execution, actor/critic
construction, forward/backward pass, optimizer operation, rollout mutation,
training, playback, diagnosis, formal evaluation, real model/checkpoint tensor
I/O, Isaac launch, or AppLauncher launch. The reward oracle uses only small,
synthetic CPU tensors under a pure test boundary. Installed HARL was unchanged,
and no commit was created.

## 22. Deferred runtime evidence

The following remain explicitly deferred:

- production of lifecycle, assignment-tick, proposal-resolution, actor-update,
  and team-reward diagnostics;
- diagnostic aggregation, logger/sink, info/extras/TensorBoard/file wiring;
- the event-gated scheduler, local set, cost/Top-K, DVM, proposal sampling,
  resolver component, and atomic-transfer runtime;
- runtime team-reward reduction and component rejection penalty;
- critic-buffer reward transport and ValueNorm behavior;
- selection and validation of `rejection_penalty_scale` in Phase D/E;
- runtime termination and failure metrics;
- checkpoint-ready V3, runtime evidence, state-dict inventory, and V3 weight
  save/load;
- Isaac smoke, training, playback, evaluation, and ablation evidence.

Consequently A5 does not claim that `TeamRewardDiagnostic` is runtime-produced,
that team reward reaches the critic, that ValueNorm is updated, or that the
event profile is runtime-ready.

## 23. Risks/blockers

No production-contract blocker or frozen-authority gap was found.

One non-blocking **LOW** test-hardening risk remains: future pure-oracle tests
could broaden independently computed shape/value matrices across additional
`E`, `M`, component-count, and synthetic-scale cases. This is optional
future test-oracle hardening, not evidence of a production reward defect, not a
schema gap, and not an A5 completion blocker.

A second LOW evidence boundary is intentional: no-sink/no-info evidence is
source/static plus exercised pure clean-child evidence. It proves the current
Phase-A sources and covered old-profile resolution paths, but does not claim
absence of hypothetical future reflective/dynamically aliased runtime wiring
or an A6 runtime producer. Runtime producer/sink evidence remains deferred.

Independent review found no HIGH or MEDIUM issue in the A5 reward/diagnostics
test-only closeout.

All substantive runtime risks remain deferred to their authorized phases:
producer timing, component identity/deduplication, reward transport,
critic/ValueNorm integration, logging throughput, and runtime default-off
identity require later implementation and execution evidence.

## 24. Final classification

```text
classification:
  PHASE-A5-DIAGNOSTICS-REWARD-SEMANTIC-CLOSEOUT-COMPLETE-AWAITING-GPT-REVIEW

diagnostics schema:
  unchanged
  exact enum/envelope/8-payload/availability closeout passed

diagnostics runtime producer/sink:
  not implemented

team reward schema:
  unchanged
  canonical mean -> component-once penalty -> broadcast closeout passed

team reward runtime:
  not implemented

rejection_penalty_scale:
  unresolved
  owner_phase=phase_d_e

V3 interface fingerprint:
  unchanged
  03c33620e8324c034de5f9014dfd0cb76bef2fc06c99b15895f94b9981cb2b6a

V3 checkpoint-ready:
  unavailable

runtime event profile:
  unavailable

required pure regressions:
  143/143

optional audit included:
  147/147

Isaac/AppLauncher:
  not run

training/playback/evaluation:
  not run

real checkpoint tensor I/O:
  none

installed HARL:
  unchanged

commit:
  none

next gate:
  stop for GPT/user review
  A6 and Phase B0/B/C/D/E remain not entered and unauthorized
```

Final repository audit therefore closes with unchanged HEAD, an empty index,
the known 49-path worktree, `git diff --check` exit 0, protected production
hashes unchanged, and no commit. `TASK_PROGRESS.md` contains 354 lines and was
updated in place; no archive was created because A5 required no historical
rewrite or condensation.
