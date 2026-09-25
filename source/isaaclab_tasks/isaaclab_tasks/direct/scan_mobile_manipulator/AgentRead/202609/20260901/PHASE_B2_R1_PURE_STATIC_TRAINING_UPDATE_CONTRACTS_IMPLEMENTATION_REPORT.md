# Phase B2-R1 Pure/Static Training-Update Contracts Implementation Report

Date: 2026-09-01

Classification:

```text
PHASE-B2-R1-PURE-STATIC-TRAINING-UPDATE-CONTRACTS-IMPLEMENTATION-COMPLETE-AWAITING-GPT-REVIEW
```

## A. Repository authority

Starting and closing committed authority are identical:

```text
branch:      main
HEAD:        b71d85a32f51be6ada324f870813a56bb45dd396
upstream:    origin/main
merge-base:  b71d85a32f51be6ada324f870813a56bb45dd396
relationship: HEAD == origin/main == merge-base
```

B2-V2 is `GPT REVIEW PASS / CLOSED`. B2-R0 is `GPT REVIEW PASS / FROZEN` by
the explicit starting instruction for this slice. The starting dirty tree
contained the prior B2-R0 AgentRead handoff edits and archives. B2-R1 preserved
those items, added only isolated contract/test/documentation files, and did not
modify an existing production runtime implementation.

Relevant frozen installed-HARL SHA-256 identities were read only:

```text
harl/algorithms/actors/happo.py
  dd44fe7842160aa215b2d220726f6dd5e70b251c1a2e9c50cfeb6bd00535cf96
harl/algorithms/critics/v_critic.py
  ae66390702efb55099d151c11f28ae533f25ef6d62697949445abd2979708bf3
harl/runners/on_policy_ha_runner.py
  14f68bac719be40af8117284741c06e7434a18458d07cb30d5400bc32d02579a
harl/common/buffers/on_policy_critic_buffer_ep.py
  0a288f3888908b98157a0848744d7eebec655159d5e89d9c85436a2e30b9a46f
harl/common/valuenorm.py
  a35471b136567bde0b7fc7be34a7873efa617bdabf9a9074517ff0e3ef3fb8b0
```

Installed HARL was not modified.

## B. Files created or modified

Created production-isolated contract modules:

- `assignment_event_training_evidence.py`
- `assignment_event_training_plans.py`
- `assignment_event_training_control.py`
- `assignment_event_training_static_guards.py`

All four are private by construction (`__all__ == ()`), use canonical module
identity guards, and are not imported by the current production route.

Created pure test support/tests:

- `scripts/environments/_assignment_phase_b2_r1_contract_helpers.py`
- `scripts/environments/test_assignment_phase_b2_r1_authority_ownership_fingerprint_pure.py`
- `scripts/environments/test_assignment_phase_b2_r1_update_plans_factor_pure.py`
- `scripts/environments/test_assignment_phase_b2_r1_permits_ordering_static_guards_pure.py`

Created documentation:

- this report;
- `AgentRead/202609/20260901/TASK_PROGRESS_ARCHIVE_BEFORE_B2_R1_HANDOFF_20260901.md`;
- updated `AgentRead/TASK_PROGRESS.md` after the byte-exact archive.

No existing runtime, lifecycle, reward, resolver, scheduler, viewpoint,
controller, observation, DVM, profile, wrapper, public runner, or installed-HARL
source was modified.

## C. Implementation inventory

The B2-R1 implementation is deliberately split into four small modules rather
than a real coordinator:

1. authority/evidence: deterministic serialization, source/config authority,
   termination selection evidence, frozen training inputs, component
   fingerprints, and ownership/disjointness;
2. plans: actor plans, exact partitions, full-index factor transitions, critic
   plans, and configuration-derived call counts;
3. control: immutable permits, a test-only single-use ledger, mutation
   expectations, synthetic-only receipts, bounded failure evidence, and the
   S0-S10 validator;
4. guards: repository-local AST guards for forbidden stock update paths,
   forbidden mutation calls, and public-route references.

There is no callable training-update coordinator and no connection from a
permit to autograd, an optimizer, ValueNorm mutation, a runner, or rollover.

## D. Frozen B2-R0 contracts preserved

- P2 remains sole ownership truth; no lifecycle source changed.
- Proposal/effective assignment and actor behavior evidence remain distinct.
- DVM remains independent of active masks and available actions.
- Actor evaluation rows are DVM; actor loss rows are active-and-DVM.
- Forced/no-policy rows cannot enter actor loss and their `0.0` sentinel is not
  treated as behavior logprob.
- Sequential factor remains full resolved `[T,E,1]`, with exact-one off-DVM
  ratio and retained prior-actor accumulation.
- Critic plans require every physical `k` in `[0,T*E)` exactly once per epoch
  and bind a raw-target identity for `returns[:-1]`.
- Event returns are not recomputed; stock `compute_returns()` remains forbidden.
- Termination precedence is
  `ALL_TASKS_COMPLETED > NO_FEASIBLE_TASKS_REMAIN > TIME_LIMIT > NONE`.
- The private learned-policy route remains dormant/default-off and public use
  remains blocked.

## E. DTO/schema inventory

Implemented immutable/frozen DTOs include:

- `B2RSourceDigestV1`, `B2RResolvedConfigV1`, `B2RUpdateAuthorityV1`;
- `B2RTerminationSelectionEvidenceV1`, `B2RFrozenTrainingInputsV1`;
- tensor, gradient, optimizer-group, optimizer-state, component-fingerprint,
  and ownership evidence DTOs;
- actor minibatch/update plans, factor transition evidence, critic update plan;
- mutation permit/consumption/expectation, synthetic step receipt;
- failure and ordering evidence.

Canonical indices are explicit as `k = t * resolved_E + env_id`. Counts and
partitions are derived from the frozen resolved config; no R0 example dimension
is an architecture constant. The schemas support a later backward-only slice
with backward count greater than zero and optimizer-step count equal to zero.

## F. Canonical digest and fingerprint results

Pure tests established:

- same content and copied equivalent content produce the same digest;
- scalar, dtype, shape, tensor value, resolved dimension, and meaningful tuple
  order changes are detected;
- tensor fingerprints bind shape, dtype, device classification, finite state,
  exact bounded byte digest, and `requires_grad` where relevant;
- component fingerprints bind ordered named parameters, buffers, train/eval
  mode, absent/present gradient evidence, optimizer groups/hyperparameters,
  optimizer-state schema, and complete ValueNorm `state_dict()` tensors;
- repeated read-only fingerprints of the same module/optimizer/ValueNorm
  fixture are identical; equivalent copied modules are identical; train/eval
  mode differs;
- no object address and no unbounded raw weight/tensor dump enters evidence.

## G. Ownership and disjointness

The intended synthetic topology of three distinct actors plus one distinct
critic passed exact ownership. Actor optimizer parameter sets were mutually
disjoint, the critic was disjoint from all actors, and every required parameter
was owned exactly once.

Six precise `STOP — B2-R OWNERSHIP` fixtures rejected actor-owning-critic
parameters, actor overlap, critic/actor overlap, missing ownership, unexpected
extra ownership, and requested shared-parameter mode. Pre/post fingerprints
proved these inspections did not mutate the live fixture.

## H. Actor update-plan tests

Actor plans passed deterministic digest, exact actor permutation, two epochs,
three minibatches, multiple `t`/environment indices, mixed DVM, DVM-but-inactive
rows, and all-forced actor coverage. The all-forced actor derived zero backward
and zero step calls. Eight fail-closed fixtures covered duplicate/missing/bad
actors, bad DVM index, wrong config, loss outside DVM authority, duplicate loss
row, and incorrect expected counts.

## I. Full-index factor tests

Two full `[3,4,1]` transitions established finite positive recurrence, exact-one
off-DVM ratios, canonical scatter, exact skip behavior, and preservation of a
prior actor's accumulated factor through a later skipped/forced actor.

Nine `STOP — B2-R FACTOR` fixtures covered duplicate/noncanonical scatter,
nonfinite logprob, nonfinite ratio, underflow to zero, nonpositive factor,
off-DVM non-one evidence, nonpositive-ratio evidence, recurrence mismatch, and
skipped-actor mutation evidence. No compact-DVM factor exists.

## J. Critic exact-row coverage and counts

For the synthetic resolved config `T=3`, `E=4`, `B=12`, two critic epochs and
five reviewed exact-coverage minibatches per epoch covered every row exactly
once. The derived counts were 10 backward, 10 optimizer-step, and 10 ValueNorm
calls when enabled. Disabled step policy derived `10/0/0`; disabled ValueNorm
derived zero ValueNorm calls.

Ten fixtures rejected a dropped row, duplicate row, out-of-range row, empty
partition, bad epoch count, bad minibatch count, floor-remainder omission,
wrong config binding, incorrect step count, and incorrect ValueNorm count.

These are calculated expectations only; none was executed.

## K. Permit, ordering, receipt, and failure evidence

A valid synthetic single-use permit consumption passed. Thirteen permit faults
rejected double use, expiry, wrong owner/actor/stage/operation/minibatch/index,
stale update/config authority, out-of-order issuance, disallowed ValueNorm use,
and consumption after poison.

The S0-S10 sequence passed all ten legal transitions. Eight ordering faults
rejected a skipped/reversed state, actor before plan freeze, critic before actor
completion, rollover before post-update audit, checkpoint before S10,
quiescence with a pending permit, and continuation from a poisoned actor stage.

Synthetic-only receipts passed and a non-synthetic receipt was rejected.
Mutation expectation DTOs represent future backward-only/no-step slices.
Failure DTOs represent both a no-mutation R1 fault (`partial_update=false`) and
a future irreversible partial update with poison/quarantine and every
continuation permission false; inconsistent evidence was rejected.

## L. Source/AST and public-route guards

Passing guards scanned:

- five event/private source files: the four R1 modules plus the existing
  `assignment_event_learned_route.py`;
- all four B2-R1 helper/test files for executable mutation calls;
- 57 production Python files in `scan_mobile_manipulator` for any reference to
  the four private R1 modules.

No executable call to backward, optimizer step, ValueNorm update, stock HARL
trainer/update, or stock `compute_returns()` was found. Six stock-path, four
mutation-call, and one public-import synthetic AST faults produced the exact
frozen STOP category (`STOCK_FULL_ROW_ACTOR_PATH`, `CRITIC_TRAINING_SLICE`,
`STOCK_RETURNS_BYPASS`, `UNAUTHORIZED_BACKWARD`,
`UNAUTHORIZED_OPTIMIZER_STEP`, `VALUENORM`, or `PUBLIC_ROUTE_OPEN`). Installed
HARL definitions were not scanned as violations.

The production scan found zero references to the private R1 modules, and all
four modules export nothing. Therefore adding these files cannot instantiate or
select an R1 coordinator from the current public route. Default and legacy
profiles are unaffected because no existing route/config/profile file changed.

## M. Commands and results

All commands used the approved environment and exited zero:

```text
conda run -p C:\isaacenvs\isaac45_harl python \
  scripts/environments/test_assignment_phase_b2_r1_authority_ownership_fingerprint_pure.py
PASS

conda run -p C:\isaacenvs\isaac45_harl python \
  scripts/environments/test_assignment_phase_b2_r1_update_plans_factor_pure.py
PASS

conda run -p C:\isaacenvs\isaac45_harl python \
  scripts/environments/test_assignment_phase_b2_r1_permits_ordering_static_guards_pure.py
PASS
```

The matrix contains 75 explicit expected-STOP checks plus additional positive
digest/config drift detection. All precise STOP expectations matched. Initial
compile-only syntax validation also passed.

## N. Zero-execution proof

```text
backward count executed:                  0
torch.autograd.backward count executed:   0
optimizer step count executed:            0
optimizer-state mutations executed:       0
actor/critic parameter mutations:          0
live ValueNorm training updates:           0
Isaac/AppLauncher/SimulationApp actions:   0
environment rollouts:                      0
HARL trainer/update actions:               0
training/playback/evaluation actions:       0
checkpoint weight load/save actions:       0
public learned-policy activations:          0
```

This follows both from the executed pure paths and from the passing AST guard
over the contract implementation and tests. Optimizers were constructed only
for read-only topology/fingerprint inspection.

## O. Archive evidence

Before rewriting `TASK_PROGRESS.md`, its bytes were copied without text
conversion:

```text
source bytes:  8680
archive bytes: 8680
byte equality: true
SHA-256: c5f041a75d2e4cffb03b88a105bb05cbba0f39af7face1ccd2db1477b71f7fb3
Git blob: 8a03ac32ebfedcd4b5b96628e735ab02f54b6490
```

## P. Retained nonclaims and handoff

B2-R1 does not establish autograd correctness, finite real gradients, real
actor/critic/optimizer/ValueNorm mutation, a complete learner update,
training-update readiness, convergence, policy quality, public-route readiness,
checkpoint continuation, or exact resume.

```text
B2-R0: GPT REVIEW PASS / FROZEN
B2-R1: IMPLEMENTATION COMPLETE / PURE-STATIC VERIFICATION COMPLETE /
       AWAITING GPT REVIEW
B2-R2: NOT AUTHORIZED
training-update readiness: NOT YET ESTABLISHED
public learned-policy route: DORMANT / BLOCKED
training: NOT AUTHORIZED
commit: NONE
next: independent GPT review of B2-R1
```
