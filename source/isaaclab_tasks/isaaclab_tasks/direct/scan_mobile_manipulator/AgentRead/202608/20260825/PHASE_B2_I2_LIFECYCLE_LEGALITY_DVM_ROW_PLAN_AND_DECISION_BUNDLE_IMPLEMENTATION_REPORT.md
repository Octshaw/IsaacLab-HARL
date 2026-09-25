# Phase B2-I2 Lifecycle Legality, DVM, Row Plan, and Decision Bundle — Implementation Report

Date: 2026-08-25

Classification: `PHASE-B2-I2-LIFECYCLE-LEGALITY-DVM-ROW-PLAN-AND-DECISION-BUNDLE-COMPLETE-AWAITING-GPT-REVIEW`

## 1. Status and boundary

```text
B2-D:                              REVIEW PASS / FROZEN
B2-I0:                             REVIEW PASS / CLOSED
B2-I1:                             REVIEW PASS / CLOSED
B2-I2:                             IMPLEMENTED / AWAITING GPT REVIEW
Phase B overall:                   NOT COMPLETE
runtime readiness:                BLOCKED
policy readiness:                 BLOCKED
learner readiness:                BLOCKED
public learned-policy event step: BLOCKED
training:                          NOT AUTHORIZED
commit:                            NONE
```

Only B2-I2 was implemented. B2-I3a and every later slice remain not authorized and were not started.

## 2. Starting checkpoint

```text
branch: main
HEAD: 14993dee344bade0230d2eb97b5f22171331f44a
subject: feat(mrta): complete lifecycle runtime backbone and wrapper integration
B2-I1 review authority: REVIEW PASS / CLOSED, supplied by the user
```

The existing uncommitted B2-D, B2-I0, and B2-I1 deliverables were preserved. No commit was created.

## 3. Changed files

Implementation:

- `assignment_event_policy_decision.py` — new task-local pure Torch B2-I2 legality and routing module.

Verification:

- `scripts/environments/test_assignment_phase_b2_i2_lifecycle_legality_dvm_row_plan_decision_bundle_pure.py` — new 17-oracle fixture.

Documentation:

- this report;
- `AgentRead/TASK_PROGRESS.md`.

No I1 evidence source, I4-2 adapter, wrapper, facade, P2/lifecycle writer, M1/B1 transaction, Ak/controller, environment, DirectMARLEnv, runner, buffer, GAE, configuration, checkpoint, or installed HARL file was modified.

## 4. Exact input and no-recapture proof

The only producer input is:

```text
one exact canonical EventPolicyEvidenceSnapshot object
-> pure legality and routing projection
-> one sealed EventPolicyDecisionBundle
```

I2 does not import the current-publication producer, claim-window runtime, environment, or I4-2 adapter. It accepts no P2 publication, OPEN view, assignment problem, feasibility tensor, or cost tensor argument. It consumes only lifecycle and physical fields already detached inside the exact I1 snapshot.

The dynamic oracle mutates original problem feasibility/cost tensors, P2 lifecycle backing, and the supplied OPEN view after I1 capture. I2 output continues to follow the sealed snapshot and the instrumented assignment problem records no additional reads. A static oracle proves there is no `source_publication` or `source_window_identity` access path in I2.

## 5. EventPolicyDecisionBundle exact schema

The factory-only frozen bundle contains:

```text
schema/profile/projector identity
exact EventPolicyEvidenceSnapshot reference
exact EventPolicyEvidenceIdentityV2 reference
EventPolicyI42ProposalSourceBindingV2
available_actions_bool [E,M,N+1] bool
runner_available_actions [E,M,N+1] float32
decision_valid_mask [E,M,1] bool
row_kind [E,M] int64
forced_action_id [E,M,1] int64
policy_proposal_present_mask [E,M,1] bool
policy_row_mask [E,M,1] bool
forced_continuation_mask [E,M,1] bool
forced_noop_mask [E,M,1] bool
forced_row_mask [E,M,1] bool
terminal_no_row_mask [E,M,1] bool
storage_row_mask [E,M,1] bool
immutable provenance/routing metadata
```

All public tensor properties return detached contiguous clones. The exact I1 snapshot and identity are retained as immutable reference bindings. The bundle cannot be partially created or later filled with actions/logprobs.

## 6. Lifecycle legality conjunction

For robot `r` and task `j`, new-claim legality is exactly:

```text
robot_state[r] == NEEDS_ASSIGNMENT
AND task_state[j] == AVAILABLE
AND ownership[j] == -1
AND cumulative_failed_pairs[r,j] == false
AND explicit_physical_feasibility[r,j] == true
```

The reviewed v2 path/local/retry seams remain explicitly omitted with no synthetic defaults. I2 validates that I1 provenance still declares those seams omitted; an active or malformed seam without a corresponding frozen I1 tensor fails closed.

## 7. Task-state legality

| Task state | New claim candidate | Owner continuation |
|---|---:|---:|
| `AVAILABLE` | only if full conjunction passes | not applicable |
| `CLAIMED` | no | active owner only |
| `NAVIGATING` | no | active owner only |
| `ALIGNING` | no | active owner only |
| `COMPLETED` | no | no |
| `TEAM_INFEASIBLE` | no | no |

An available-but-owned task is not exposed for a new claim. Claimed/navigating/aligning tasks are never exposed to another robot actor.

## 8. Four row semantics

| Row kind | Current production condition | Semantic mask | DVM | Forced ID |
|---|---|---|---:|---:|
| `POLICY_DECISION_ROW` | `NEEDS_ASSIGNMENT` with legal target | legal targets plus noop | true | `-1` invalid sentinel |
| `FORCED_CONTINUATION_ROW` | `EXECUTING` with exactly one active owned task | owned task only, noop false | false | owned task ID |
| `FORCED_NOOP_ROW` | no-target `NEEDS_ASSIGNMENT`, `WAITING_FOR_TASK`, `UNAVAILABLE` | noop only | false | raw noop ID `N` |
| `TERMINAL_NO_ROW` | historical descriptor only | all false | false | `-1`, no routed action |

The current I2 bundle accepts only the I1 current nonterminal snapshot and produces only the first three kinds. `TERMINAL_NO_ROW` is implemented only by `EventPolicyTerminalNoRowDescriptorV2`; it has no I1 snapshot input, actor/storage row, terminal sidecar, or historical producer.

## 9. EXECUTING continuation

An `EXECUTING` row must have exactly one owned task and inverse `current_owned_task_id` must agree with ownership. The task must be `CLAIMED`, `NAVIGATING`, or `ALIGNING`. Missing ownership, multiple ownership, inverse mismatch, or non-active owned task fails closed.

Continuation ignores transient feasibility and ranking cost. It always routes the authoritative owned task only. It is not actor resampling, reassignment, B1 request, resolver result, or ownership repair.

## 10. DVM and available actions

```text
decision_valid_mask == policy_row_mask
decision_valid_mask is true iff row_kind == POLICY_DECISION_ROW
```

DVM is not HARL `active_masks`; no learner or PPO/HAPPO semantics are implemented. Internal available actions are bool and only the stored HARL-facing boundary copy is float32. Every current row has at least one routed action. Noop is false for continuation, true for policy rows, and the sole action for forced-noop rows.

## 11. Forced action and proposal ledger

```text
policy row:       -1 invalid sentinel; no forced action
continuation row: authoritative current task ID
forced-noop row:  N, for future N -> -1 decode
terminal concept: -1, no routed action
```

`policy_proposal_present_mask` equals DVM and means only that future actor inference is expected on the row. There is no sampled proposal, proposal logprob, fake forced proposal/logprob, resolver winner, transaction candidate, or effective assignment in I2.

## 12. Same-task conflict and cost separation

I2 performs no cross-robot exclusivity. Two policy rows may both expose the same available task, preserving both future original proposals for existing I4-2 arbitration.

Geometric ranking cost is not read by the legality projector. A paired oracle changes every finite cost while keeping lifecycle/ownership/failed/feasibility evidence identical; masks and row kinds remain equal. Finite cost cannot create legality.

## 13. Exact I4-2 boundary

`EventPolicyI42ProposalSourceBindingV2` retains the exact I1 snapshot and identity objects, P2 publication identity reference, episode/transition tuples, OPEN opaque identity, and descriptors for the existing I4-2 adapter/snapshot types.

It is explicitly pre-inference and pre-arbitration. No `EventProposalDecisionSnapshot` is constructed, no adapter is imported or called, and no proposal, resolver, M1/B1, or ownership commit occurs. A numerically equal replacement I1 snapshot fails exact-object validation.

## 14. Immutability and evidence preservation

The fixture mutates returned available-actions, DVM, and forced-ID tensors and proves the bundle remains unchanged. It also proves I2 sealing leaves I1 actor, semantic critic, and runner critic tensors bitwise unchanged.

Identity metadata remains validation-only and absent from numerical I2 outputs. The bundle is bounded and has no in-place completion path for future actions or logprobs.

## 15. Verification matrix

Interpreter:

```text
C:\isaacenvs\isaac45_harl\python.exe
Python 3.10.20
```

| Suite | normal | `-I -B` |
|---|---:|---:|
| B2-I2 legality/DVM/decision bundle | `17/17 PASS` | `17/17 PASS` |
| B2-I1 evidence/current projectors | `14/14 PASS` | `14/14 PASS` |
| B2-I0 no-tick reconciliation | `13/13 PASS` | `13/13 PASS` |
| historical v1 schema | `9/9 PASS` | `9/9 PASS` |
| Phase-A default-off identity | `16/16 PASS` | `16/16 PASS` |
| profile contract | `16/16 PASS` | `16/16 PASS` |

`py_compile` for the new module and fixture: `2/2 PASS`.

The first B2-I2 authoring run reported `16/17`: the no-recapture oracle itself used the instrumented mapping accessor while mutating sources and incremented its own counter. The fixture was corrected to use the base dictionary accessor; production logic was unchanged. Both final modes then passed `17/17`.

## 16. Protected hashes

The fixture checks 12 frozen source anchors, including I1, I0/v1 schema, profile/default-off, wrapper/training, facade/I4-2 adapter, lifecycle/P2, and environment integration.

```text
assignment_event_policy_evidence.py
  7563835ca94eb08baab463a349aa8d27a056da12477e3ded8827b512dd86f83a
assignment_event_profile_schema_contract_v2.py
  9fb64e62f1fff8b2ad9eafd8137f8d71b8912464e4c859e2b8b395421c37f955
assignment_event_proposal_adapter.py
  874b4c7b71e6c42f9e6dabeefa25a708d25d8518e3366fe91b86b9b1a739bedd
assignment_harl_wrapper.py
  f238536c8a4bed53da984e4f2d81150f7b634915e49b601d86eb407fae9fa2ae
scan_mobile_manipulator_env.py
  c19b5de8f73d22fbc8b4c1f6b38dbfc4804d28b6e37b002cdfc4e20d5ecc9c99
```

New artifact hashes:

```text
assignment_event_policy_decision.py
  d465de33edb11769dfd3fc34e535416ba9bb212f4fbdd770a11dde1830862697
test_assignment_phase_b2_i2_lifecycle_legality_dvm_row_plan_decision_bundle_pure.py
  faad542d572798d9ac54a7d6f7229dbabea9c1752c5db4eb3f5699247a9cfea6
```

Final `git diff --check`, untracked whitespace inspection, exact bytecode cleanup, and hash confirmation are included in final hygiene.

## 17. Runtime/readiness non-claims

No Isaac, AppLauncher, HARL rollout, actor inference, optimizer, training, playback, evaluation, or checkpoint operation was run. Installed HARL was not modified. I2 is not wired into public wrapper reset/step and changes no readiness gate or legacy/default route.

## 18. Remaining blockers

- B2-I3a DVM-aware actor collection/storage and separate proposal envelope;
- B2-I3b policy/HAPPO full-index math;
- B2-I4 authoritative pre-reset terminal critic sidecar;
- B2-I5a historical learner/value/buffer transport;
- B2-I5b TIME_LIMIT GAE/ValueNorm semantics;
- B2-I6 dormant public learned-policy route;
- later pure and real-interface verification/readiness gates.

External path/local/retry producers and all eleven numeric TBDs remain deferred. Transformer/GNN/Set Transformer, variable cardinality, arbitrary-cardinality checkpoints, training, playback, and evaluation remain out of scope.

```text
next proposed slice: B2-I3a — DVM-aware actor collection/storage and proposal envelope
status: NOT AUTHORIZED
```

## 19. Final classification

```text
classification:
  PHASE-B2-I2-LIFECYCLE-LEGALITY-DVM-ROW-PLAN-AND-DECISION-BUNDLE-COMPLETE-AWAITING-GPT-REVIEW
B2-D:
  REVIEW PASS / FROZEN
B2-I0:
  REVIEW PASS / CLOSED
B2-I1:
  REVIEW PASS / CLOSED
B2-I2:
  IMPLEMENTED / AWAITING GPT REVIEW
tests:
  PASS
Isaac:
  NOT RUN
HARL runtime:
  NOT RUN
training/playback/evaluation:
  NOT RUN
runtime readiness:
  BLOCKED
policy readiness:
  BLOCKED
learner readiness:
  BLOCKED
training:
  NOT AUTHORIZED
commit:
  NONE
```

Stop here pending GPT independent review and explicit user authorization. Do not begin B2-I3a.
