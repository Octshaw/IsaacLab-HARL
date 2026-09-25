# Lifecycle-aware Dynamic MRTA — Task Progress

Updated: 2026-09-09

## Current status

```text
B2-R0: GPT REVIEW PASS / FROZEN
B2-R1 through B2-R5: GPT REVIEW PASS / CLOSED
B2-R5I-RC: GPT REVIEW PASS / CLOSED
B2-R5I-VF: GPT REVIEW PASS / CLOSED
B2-R5I-CG: GPT REVIEW PASS / CLOSED
B2-R5I: GPT REVIEW PASS / CLOSED
B2-R7: GPT REVIEW PASS / CLOSED

B2-T0:
  FAILED / NOT COMPLETE
  AWAITING INDEPENDENT GPT REVIEW

training-update readiness: REVIEW PASS / ESTABLISHED
real Isaac single-transaction integration: REVIEW PASS / ESTABLISHED
repeated-update continuity: NOT ESTABLISHED
successful B2-T0 transactions: 1 / 3
B2-T0 S10: 1 / 3
cross-transaction bridges: 0 / 2 PASS

mutation-bearing B2-T0 run03:
  PARTIAL_UPDATE / POISONED / STOPPED / HISTORICAL

public learned-policy route: DORMANT / BLOCKED
B2-R6a/R6b: NOT AUTHORIZED
checkpoint I/O: 0
long training / evaluation / playback: NOT AUTHORIZED
```

Classification:
`PHASE-B2-T0-STOP-TX2-FORCED-CONTINUATION-RESAMPLED-NOT-COMPLETE`

## Latest execution result

B2-T0 attempted the exact three-transaction repeated-update smoke. All six
required preflight items passed, including qualified source identity, shape,
canonical ValueNorm, CG critic classification, and static private/public
authority guards. Semantic production source modifications remained zero.

The mutation-bearing run03 used one fresh process, one AppLauncher, one real
Isaac environment, one explicit reset, one private route construction, and one
persistent actor/critic/optimizer/ValueNorm learner construction:

```text
run identity: b2-t0-repeated-smoke-26616
environment/profile: Isaac-Scan-Mobile-Manipulator-Direct-v0 / event_gated_local_mrta
device: cuda:0
T/E/M/N: 2/2/3/12
actor epochs/minibatches: 5/2
critic epochs/minibatches: 5/2
ValueNorm: enabled
fixed_order: false
```

Transaction 1 completed S0-S10:

```text
update ID: b2-t0-repeated-smoke-26616-tx1
actor order: (1,2,0)
actor backward / optimizer.step: 15 / 15
factor segments: 3
event returns / stock compute_returns: 1 / 0
VALID_NONZERO_UPDATE: 5
VALID_ZERO_EFFECTIVE_UPDATE: 5
critic backward / optimizer.step: 10 / 10
ValueNorm.update: 10
critic rollover / ledger reset / actor rollovers: 1 / 1 / 3
S7 / S8 / S9 / S10: 1 / 1 / 1 / 1
```

Its Adam counters advanced actors `0 -> 5` and critic `0 -> 10`; canonical
ValueNorm advanced from `ade87b...b0d9` to `51bf53...2a59`. All completed
losses, gradients, parameters, optimizer states, and ValueNorm fields were
finite. Two TIME_LIMIT terminal rows retained exact correlated pre-reset
critic evidence through ACK and were consumed at ordered S9.

## Transaction-2 bridge failure

After transaction-1 S10, in-process pre-collection guards passed persistent
learner state equality, route-unpoisoned, empty-ledger, clean-gradient,
rollout-mode, and slot-zero/cursor conditions. Transaction-2 then collected
two real steps. Actor call counts were `(1,1,1)` at its start, `(2,2,2)` after
its first step, and `(2,2,3)` after its second step. The additional actor-2
policy call triggered:

`STOP — B2-T0 TX2_FORCED_CONTINUATION_RESAMPLED: ((1, 1, 1), (2, 2, 3))`

The stop occurred before the transaction-2 R5 adapter, actor/critic backward,
optimizer step, ValueNorm update, plan/permit construction, or pre-mutation
artifact. No durable tx1-to-tx2 bridge receipt was completed.

Because transaction 1 had already mutated the learner, the whole run was
immediately classified `partial_update=true`, `route_poisoned=true`, stopped,
and closed. No retry was performed. Transaction 3 and transaction 4 were never
started.

The failure does not itself decide whether actor 2 legitimately reopened a
lifecycle decision on the second step or whether that behavior is a semantic
defect. That requires independent review/design audit, not a poisoned-run
retry.

## B2-T0 exact counts

For mutation-bearing run03:

```text
fresh worker / AppLauncher / environment / learner constructions: 1 / 1 / 1 / 1
explicit reset / real rollout steps: 1 / 4
successful full transactions: 1
distinct completed update IDs: 1
S0 / S7 / S8 / S9 / S10: 1 / 1 / 1 / 1 / 1
bridge receipts: 0
event-return computations / stock compute_returns: 1 / 0
actor backward / optimizer.step: 15 / 15
critic backward / optimizer.step: 10 / 10
VALID_NONZERO_UPDATE / VALID_ZERO_EFFECTIVE_UPDATE: 5 / 5
ValueNorm.update: 10
critic rollover / ledger reset / actor rollovers: 1 / 1 / 3
transaction 3 / transaction 4 started: 0 / 0
checkpoint weight I/O / public activation / evaluation-playback: 0 / 0 / 0
long-training transactions: 0
```

Two earlier fresh workers were permitted pre-mutation restarts and are not
combined with run03:

- run01: package-placeholder startup conflict; environment 0, learner mutation
  false;
- run02: incorrect harness assumption about HARL's cyclic critic cursor;
  rollout steps 2, learner mutation false;
- run03: one successful transaction, then transaction-2 collection failure;
  prior mutation true, poisoned, no retry.

## Preserved B2-R5I/R7 history

Historical B2-R5I attempts remain retained:

- attempt 1: post-actor-mutation `[B,1]` factor-audit failure;
  `PARTIAL_UPDATE / POISONED / STOPPED / HISTORICAL`;
- attempt 2: CUDA live ValueNorm fingerprint observability failure;
  `PARTIAL_UPDATE / POISONED / STOPPED / HISTORICAL`;
- attempt 3: old critic nonzero-only guard rejection after ValueNorm mutation;
  `PARTIAL_UPDATE / POISONED / STOPPED / HISTORICAL`;
- attempt 4: complete real transaction/S10/next-rollout witness;
  `GPT REVIEW PASS / CLOSED` under the supplied starting authority.

B2-R7 remains `GPT REVIEW PASS / CLOSED`, and training-update readiness remains
`REVIEW PASS / ESTABLISHED`. B2-T0's failure means only that repeated-update
continuity is not established; it does not erase the reviewed single-update
authority.

## Repository and archive discipline

Repository authority remained `main` at
`b71d85a32f51be6ada324f870813a56bb45dd396`, equal to `origin/main` and the
merge-base. The 359 staged monthly-migration entries and staged-index SHA-256
`a40169043c3bfffd481a7ed1bddf3e52663d61379bedfd2610781457d11f947c`
were preserved.

The pre-B2-T0-rewrite archive is byte-exact:

```text
path: 202609/20260909/TASK_PROGRESS_ARCHIVE_BEFORE_B2_T0_FAILURE_HANDOFF_20260909.md
bytes: 7764
sha256: 61f28e363727441541ae9da5806c87178397f741fffff53406e213852a5ed5eb
```

No stage, commit, or push occurred.

## Retained boundaries and next step

- Repeated-update continuity: `NOT ESTABLISHED`.
- Public learned-policy route: `DORMANT / BLOCKED`.
- Checkpoint readiness/exact resume: `NOT ESTABLISHED`; weight I/O was zero.
- B2-R6a/R6b, long training, evaluation, and playback remain not authorized.
- The poisoned run03 must never be reused or combined with another run.

Next: independent GPT review of the B2-T0 failure and the transaction-2
actor-2 lifecycle decision. Do not retry B2-T0, start another transaction,
begin B2-R6/long training, perform checkpoint I/O, activate the public route,
stage, commit, or push without new explicit authorization.

## Detailed report and archive

- `202609/20260909/PHASE_B2_T0_BOUNDED_REPEATED_UPDATE_TRAINING_SMOKE_REPORT.md`
- `202609/20260909/TASK_PROGRESS_ARCHIVE_BEFORE_B2_T0_FAILURE_HANDOFF_20260909.md`
- `202609/20260909/PHASE_B2_R7_TRAINING_UPDATE_READINESS_FINAL_CLOSURE_REPORT.md`
- `202609/20260909/PHASE_B2_R5I_REAL_ISAAC_SINGLE_TRANSACTION_ATTEMPT4_REPORT.md`
- `202609/20260908/PHASE_B2_R5I_CG_CRITIC_ZERO_EFFECTIVE_GRADIENT_CLASSIFICATION_REPORT.md`
