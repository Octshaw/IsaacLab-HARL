# Lifecycle-aware Dynamic MRTA — Task Progress

Updated: 2026-09-09

## Current status

```text
B2-R0: GPT REVIEW PASS / FROZEN
B2-R1 through B2-R5: GPT REVIEW PASS / CLOSED
B2-R5I-RC: GPT REVIEW PASS / CLOSED
B2-R5I-VF: GPT REVIEW PASS / CLOSED
B2-R5I-CG: GPT REVIEW PASS / CLOSED

B2-R5I attempts 1/2/3:
  PARTIAL_UPDATE / POISONED / STOPPED / HISTORICAL

B2-R5I attempt 4:
  COMPLETE / AWAITING GPT REVIEW

successful real full learner transactions: 1
real S10 entries: 1
real Isaac full-learner integration: COMPLETE / AWAITING GPT REVIEW
B2-R5I: COMPLETE / AWAITING GPT REVIEW
training-update readiness: NOT YET ESTABLISHED
B2-R6a/R6b and B2-R7: NOT AUTHORIZED
public learned-policy route: DORMANT / BLOCKED
training / evaluation / playback: NOT AUTHORIZED
```

Classification:
`PHASE-B2-R5I-REAL-ISAAC-SINGLE-TRANSACTION-ATTEMPT4-COMPLETE-AWAITING-GPT-REVIEW`

## Latest completed work

B2-R5I-RE3 attempt 4 executed one fresh-process, headless `cuda:0`, real-Isaac
learner transaction. It used PID 26684, update ID
`b2-r5i-re3-fresh-26684`, one AppLauncher, one environment, one reset, two
physical rollout steps, one learner transaction, and zero retries.

Fresh runtime resolved:

```text
environment: Isaac-Scan-Mobile-Manipulator-Direct-v0
profile: event_gated_local_mrta
T/E/M/N: 2/2/3/12
actor epochs/minibatches: 5/2
critic epochs/minibatches: 5/2
ValueNorm: enabled
fixed_order: false
actor order: (1,2,0)
```

The real route produced two natural terminal/autoreset events. Pre-reset
historical critic state and post-reset current state were distinct, timeout
critic input matched exactly, runtime ACK completed, and learner ledger keys
remained available until the ordered S9 reset.

Event returns executed once; stock HARL `compute_returns` executed zero times.
The `[T,E,1]` event-return result exactly equalled the non-alias
`returns[:-1]` training slice, with the final structural slot excluded.

## Real S5/S6 result

All three actor segments completed in order `(1,2,0)`. Each actor executed
five backward and five optimizer steps, for totals `15/15`; each factor receipt
passed and off-DVM entries remained exact one.

All ten planned critic minibatches completed:

```text
VALID_NONZERO_UPDATE: 5
VALID_ZERO_EFFECTIVE_UPDATE: 5
critic backward: 10
critic optimizer.step: 10
ValueNorm.update: 10
canonical CUDA ValueNorm mutations: 10
complete critic receipts: 10/10
```

The natural classifications alternated by minibatch. Each epoch's rows `(0,1)`
were valid nonzero; rows `(2,3)` were connected, finite, exact-zero derivative
cases with source-faithful `CLIPPED_VALUE_PLATEAU` proof. Every valid-zero
minibatch still executed one Adam step. Retained Adam moments changed optimizer
state and critic parameters in all five zero-effective receipts.

Attempt-4 durable observability records pre-backward loss/graph decomposition
and post-backward per-parameter gradient evidence, Adam state before/after,
ValueNorm state, source/target digests, physical rows, cumulative counts, and
complete receipts after every minibatch.

## S7-S10 and next-rollout check

- S7 exact count, ownership, evidence, quiescence, and no-poison audit: PASS.
- S8 training-to-rollout mode restoration exactly once: PASS.
- S9 order `critic after_update -> ledger reset -> actor 0/1/2 rollover`: PASS.
- S10: exactly one; gradients and permits zero, receipts complete, ledger
  empty, cursors reset, compute-once state reset, route unpoisoned: PASS.
- One post-S10 read-only next-rollout consistency check: PASS.
- No second transaction was started.

## Files changed for attempt 4

Modified:

- `assignment_event_training_real_isaac_adapter.py`
- `scripts/environments/test_assignment_phase_b2_r5i_real_isaac_single_transaction.py`
- `AgentRead/TASK_PROGRESS.md`

Created:

- `202609/20260909/PHASE_B2_R5I_REAL_ISAAC_SINGLE_TRANSACTION_ATTEMPT4_REPORT.md`
- `202609/20260909/TASK_PROGRESS_ARCHIVE_BEFORE_B2_R5I_RE3_ATTEMPT4_HANDOFF_20260909.md`

The adapter and harness changes are logging/serialization/attempt-identity
changes only. No CG classifier, loss math, critic architecture, Adam,
ValueNorm, actor/factor, lifecycle/P2, event-return, terminal, or R5 ordering
semantics changed. No installed HARL source changed.

The TASK_PROGRESS archive is byte-exact to the pre-rewrite file:

```text
bytes: 6953
sha256: d9d85e49e6db1498748c913ffda23ca01aa835106ecbb863b7d8d4b6c2f69737
```

## Latest verification

- Approved interpreter identity: PASS.
- Relevant `py_compile`: PASS.
- `[B]`/`[B,1]` pure shape regression: PASS.
- ValueNorm canonical runtime fingerprint CPU/CUDA focused regression: PASS.
- CG zero-gradient classifier CPU/CUDA focused regression and negatives: PASS.
- R5I pre-run static-only/private/public guard: PASS.
- One formal real-Isaac attempt 4: PASS to S10.
- R5I post-run static-only/private/public guard: PASS.
- Static cardinality: backward/actor-step/critic-step/ValueNorm `1/1/1/1`, R5
  actor/critic coordinator calls `1/1`, reviewed private edges 18, public refs 0.

Repository authority remained `main` at
`b71d85a32f51be6ada324f870813a56bb45dd396`, equal to `origin/main` and
merge-base. The 359 pre-existing staged monthly-archive paths remain exact;
staged-index SHA-256 remains
`a40169043c3bfffd481a7ed1bddf3e52663d61379bedfd2610781457d11f947c`.

## Durable artifacts

```text
pre_mutation:
  bytes 202320
  sha256 bd150f83f8abe3d69ca9ba4b615460e02891d61646f955e43eeeff54d57c6a42
actor_factor_progress:
  bytes 6295
  sha256 9fb02b23fcd88046b47583b33a5766f3a82d0f56472b570cb956e35416dedfa5
critic_classification_progress:
  bytes 782411
  sha256 5e8919831490bf471da7f384034c9d6c309d924499e3f04c3266cb8151288f40
final_success:
  bytes 402791
  sha256 f3d33d549d2037e791c91772542bf7b6fdcbe62ba2277c4e323a9e0fa3d4eb3a
```

Artifacts remain in
`C:\Users\33506\AppData\Local\Temp\b2_r5i_re3_attempt4_20260909_*.json`.

## Retained nonclaims / do not do

- Attempt 4 is awaiting independent GPT review; do not self-classify it or
  B2-R5I as GPT REVIEW PASS.
- Attempts 1/2/3 remain poisoned historical routes and may never be reused.
- This one bounded transaction is not a training campaign, performance result,
  convergence result, or public learned-policy readiness claim.
- Training-update readiness remains `NOT YET ESTABLISHED`.
- Do not begin B2-R6a/R6b or B2-R7, training, checkpoint save/load,
  evaluation/playback, or public-route activation without explicit authority.
- No stage, commit, or push occurred.

## Next step

Independent GPT review of B2-R5I-RE3 attempt 4. Stop and wait for review.

## Detailed reports / archives

- `202609/20260909/PHASE_B2_R5I_REAL_ISAAC_SINGLE_TRANSACTION_ATTEMPT4_REPORT.md`
- `202609/20260909/TASK_PROGRESS_ARCHIVE_BEFORE_B2_R5I_RE3_ATTEMPT4_HANDOFF_20260909.md`
- `202609/20260908/PHASE_B2_R5I_CG_CRITIC_ZERO_EFFECTIVE_GRADIENT_CLASSIFICATION_REPORT.md`
- `202609/20260908/PHASE_B2_R5I_REAL_ISAAC_SINGLE_TRANSACTION_ATTEMPT3_REPORT.md`
- `202609/20260902/PHASE_B2_R5I_VF_VALUENORM_RUNTIME_FINGERPRINT_COMPATIBILITY_QUALIFICATION_REPORT.md`
- `202609/20260902/PHASE_B2_R5I_RC_POST_REPAIR_CONTROLLED_REGRESSION_QUALIFICATION_REPORT.md`
