# Lifecycle-aware Dynamic MRTA — Task Progress

Updated: 2026-09-10

## Current status

```text
B2-R0: GPT REVIEW PASS / FROZEN
B2-R1 through B2-R5: GPT REVIEW PASS / CLOSED
B2-R5I-RC / VF / CG: GPT REVIEW PASS / CLOSED
B2-R5I: GPT REVIEW PASS / CLOSED
B2-R7: GPT REVIEW PASS / CLOSED

B2-T0:
  NOT COMPLETE

B2-T0 run03:
  PARTIAL_UPDATE / POISONED / STOPPED / HISTORICAL

B2-T0-LD:
  LIFECYCLE DECISION-GATING QUALIFICATION COMPLETE
  AWAITING GPT REVIEW

lifecycle decision gating:
  QUALIFIED / AWAITING GPT REVIEW

run03 tx2 actor-2 exact historical cause:
  UNRESOLVED FROM EXISTING DURABLE ARTIFACTS

training-update readiness: REVIEW PASS / ESTABLISHED
real Isaac single-transaction integration: REVIEW PASS / ESTABLISHED
repeated-update continuity: NOT ESTABLISHED
successful B2-T0 transactions: 1 / 3
B2-T0 S10: 1 / 3
cross-transaction bridges: 0 / 2 PASS

next real B2-T0 retry: NOT AUTHORIZED
public learned-policy route: DORMANT / BLOCKED
B2-R6a/R6b: NOT AUTHORIZED
checkpoint I/O: 0
long training / evaluation / playback: NOT AUTHORIZED
```

Classification:
`PHASE-B2-T0-LD-LIFECYCLE-DECISION-GATING-QUALIFIED-AWAITING-GPT-REVIEW`

## B2-T0-LD result

The current production decision path is internally consistent. The exact
current P2 lifecycle publication is captured into immutable I1 evidence; I2
classifies every environment/robot row; DVM is true exactly for a
`POLICY_DECISION_ROW`; and I3a calls each actor once on only its nonempty DVM
environment subset. Physical rollout-step position is not an input to this
eligibility path.

The correct invariant is:

```text
decision_required == true  -> exactly one new proposal row
decision_required == false -> zero new proposal rows
```

`EXECUTING` with one active owned task remains forced continuation with no
policy sample, proposal, or behavior logprob evidence. `WAITING_FOR_TASK`,
`UNAVAILABLE`, and `NEEDS_ASSIGNMENT` with no legal target remain forced noop.
A new proposal is permitted only when current authoritative lifecycle state is
`NEEDS_ASSIGNMENT` and at least one task is available, unowned, not a failed
pair, and physically feasible.

The multi-robot gate is asynchronous. One controlled environment passed:

```text
robot 0: continuation -> 0 calls
robot 1: continuation -> 0 calls
robot 2: reopened decision -> 1 call
```

## B2-T0 harness root cause and correction

Root cause: `OUTCOME A — HARNESS OVERCONSTRAINT`.

The old B2-T0 harness treated the second physical collection step as forced
continuation for every robot and rejected any later cumulative actor-counter
increase. That generalized one single-transaction fixture pattern into a false
repeated-rollout invariant.

The B2-T0 harness now uses a read-only test-side observer bound to the exact
pre-call decision bundle and I3a actor-call record. For every environment,
robot, and collection boundary it records lifecycle/ownership, generation,
row kind, DVM-derived `decision_required`, call participation, proposal and
logprob presence, continuation, autoreset context, and immutable decision
identity. Cumulative actor deltas are supplemental only and must agree with the
invocation-site record.

No production lifecycle, P2, resolver, effective-assignment, action-mask,
terminal, learner, return, or transaction semantics changed.

## Controlled qualification

The dedicated no-Isaac matrix passed 13/13 cases:

- A: genuine executing continuation, `(0)`;
- B: completion/release with remaining work reopens, `(1)`;
- C: failed/released pair with another legal target reopens, `(1)`;
- D: initial unassigned eligible robot, `(1)`;
- E: canonical postepisode-reset current generation publication, `(1)`;
- F: unavailable forced-noop robot, `(0)`;
- G: asynchronous three-robot state, `(0,0,1)`;
- H: all three continuation, `(0,0,0)`;
- I: all three decision-required, `(1,1,1)`;
- J: duplicate call, precise STOP;
- K: missing required call, precise STOP;
- L: policy call during continuation, precise STOP;
- M: physical index 1 versus 99 gives the same eligibility and zero observer
  mutation.

Precise negative classifications are:

```text
STOP — B2-T0 DUPLICATE_POLICY_CALL
STOP — B2-T0 MISSING_REQUIRED_POLICY_CALL
STOP — B2-T0 POLICY_CALL_DURING_CONTINUATION
```

The existing source-faithful multi-step suite also passed 5/5, including the
real controlled lifecycle sequence `POLICY -> CONTINUATION -> POLICY` after
completion/release. Input lifecycle/DVM/action/logprob digests were unchanged
by observation.

## Historical run03 boundary

Run03 was not reused. Its seven artifacts were inspected read-only. They prove
tx1 S10 and the tx2 cumulative actor-count sequence, but contain no tx2
boundary-level robot state, ownership, lifecycle event, DVM, generation, or
proposal receipt. Therefore:

```text
RUN03 TX2 ACTOR-2 EXACT LIFECYCLE DECISION CAUSE:
  UNRESOLVED FROM EXISTING DURABLE ARTIFACTS
```

Current source behavior is not used to manufacture the missing historical
cause. Run03 remains permanently poisoned/historical.

## Preserved B2-R5I and B2-T0 history

- B2-R5I attempt 1: post-actor-mutation `[B,1]` factor-audit failure;
  `PARTIAL_UPDATE / POISONED / STOPPED / HISTORICAL`.
- B2-R5I attempt 2: CUDA live ValueNorm fingerprint observability failure;
  `PARTIAL_UPDATE / POISONED / STOPPED / HISTORICAL`.
- B2-R5I attempt 3: old critic nonzero-only guard rejection after ValueNorm
  mutation; `PARTIAL_UPDATE / POISONED / STOPPED / HISTORICAL`.
- B2-R5I attempt 4: complete real transaction/S10/next-rollout witness;
  `GPT REVIEW PASS / CLOSED`.
- B2-T0 run03 tx1: one complete S0-S10 transaction, actor backward/step 15/15,
  critic backward/step 10/10, ValueNorm updates 10, valid critic classes 5/5.
- B2-T0 run03 tx2: stopped during collection before adapter, backward,
  optimizer, ValueNorm, plan, permit, or bridge artifact.

The current B2-T0-LD qualification does not convert tx1 into 3/3 success and
does not establish either required cross-transaction bridge.

## Static and execution boundaries

```text
py_compile: 3 files PASS
B2-T0-LD controlled matrix: 13 / 13 PASS
existing multi-step lifecycle suite: 5 / 5 PASS
B2-T0/R7 static-only authority: PASS

backward / actor step / critic step / ValueNorm executors: 1 / 1 / 1 / 1
R5 actor / critic sequence calls: 1 / 1
scheduler steps: 0
reviewed private dependency edges: 18
public references: 0

production semantic source modifications: 0
B2-T0 harness modifications: 1 file
observer mutations: 0
Isaac / AppLauncher / SimulationApp: 0 / 0 / 0
real rollout: 0
learner backward / optimizer.step / ValueNorm.update: 0 / 0 / 0
checkpoint I/O / public activation / B2-T0 retry: 0 / 0 / 0
```

Repository authority remains `main` at
`b71d85a32f51be6ada324f870813a56bb45dd396`, equal to `origin/main` and the
merge-base. The 359 staged monthly-migration paths and staged-index SHA-256
`a40169043c3bfffd481a7ed1bddf3e52663d61379bedfd2610781457d11f947c`
were preserved.

The pre-rewrite progress archive is byte-exact:

```text
path: 202609/20260910/TASK_PROGRESS_ARCHIVE_BEFORE_B2_T0_LD_HANDOFF_20260910.md
bytes: 7479
sha256: 9badcf63862ae3bbd82cc1c1b6152a7919e71d49ec8ba6a5cd2cbc8b7d93ae44
```

No stage, commit, or push occurred.

## Retained boundaries and next step

- B2-T0 is `NOT COMPLETE`.
- Repeated-update continuity is `NOT ESTABLISHED`.
- Next real B2-T0 retry is `NOT AUTHORIZED`.
- Public learned-policy route remains `DORMANT / BLOCKED`.
- B2-R6a/R6b, checkpoint work, long training, evaluation, and playback remain
  unauthorized.

Next: independent GPT review of B2-T0-LD. Do not retry B2-T0, start long
training, begin B2-R6, perform checkpoint I/O, activate the public route,
stage, commit, or push without new explicit authorization.

## Detailed report and archive

- `202609/20260910/PHASE_B2_T0_LD_LIFECYCLE_DECISION_GATING_QUALIFICATION_REPORT.md`
- `202609/20260910/TASK_PROGRESS_ARCHIVE_BEFORE_B2_T0_LD_HANDOFF_20260910.md`
- `202609/20260909/PHASE_B2_T0_BOUNDED_REPEATED_UPDATE_TRAINING_SMOKE_REPORT.md`
- `202609/20260909/PHASE_B2_R7_TRAINING_UPDATE_READINESS_FINAL_CLOSURE_REPORT.md`
- `202609/20260909/PHASE_B2_R5I_REAL_ISAAC_SINGLE_TRANSACTION_ATTEMPT4_REPORT.md`
- `202609/20260908/PHASE_B2_R5I_CG_CRITIC_ZERO_EFFECTIVE_GRADIENT_CLASSIFICATION_REPORT.md`
