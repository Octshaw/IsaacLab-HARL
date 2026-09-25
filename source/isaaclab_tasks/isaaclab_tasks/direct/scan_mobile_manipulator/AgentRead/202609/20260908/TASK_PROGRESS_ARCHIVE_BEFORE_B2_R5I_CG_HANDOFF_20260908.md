# Lifecycle-aware Dynamic MRTA — Task Progress

Updated: 2026-09-08

## Current status

```text
B2-R0: GPT REVIEW PASS / FROZEN
B2-R1 through B2-R5: GPT REVIEW PASS / CLOSED
B2-R5I-RC: GPT REVIEW PASS / CLOSED
B2-R5I-VF: GPT REVIEW PASS / CLOSED

B2-R5I attempt 1: PARTIAL_UPDATE / POISONED / STOPPED / HISTORICAL
B2-R5I attempt 2: PARTIAL_UPDATE / POISONED / STOPPED / HISTORICAL
B2-R5I attempt 3: PARTIAL_UPDATE / POISONED / STOPPED / AWAITING GPT REVIEW

B2-R5I: NOT COMPLETE
successful real full learner transactions: 0
real S10 entries: 0
further real Isaac reentry: NOT AUTHORIZED
real Isaac full-learner integration: NOT ESTABLISHED
training-update readiness: NOT YET ESTABLISHED
B2-R6a/R6b and B2-R7: NOT AUTHORIZED
public learned-policy route: DORMANT / BLOCKED
training / evaluation / playback: NOT AUTHORIZED
```

Classification:
`PHASE-B2-R5I-RE2-STOP-S6-CRITIC-SEQUENCE-NOT-COMPLETE`

## Latest completed work

The one authorized attempt-3 fresh process ran with PID 24480 and identity
`b2-r5i-re2-fresh-24480`. It did not reuse attempts 1 or 2. One AppLauncher,
one real environment construction/reset, two real rollout steps, and two
terminal/autoreset records produced the bounded `T=2, E=2, M=3, N=12` batch.

S0-S4 completed. S5 completed actor order `(1,2,0)`: every actor performed
five backward operations and five optimizer steps, all three factor
post-audits passed, and durable receipts were flushed after each segment.

S6 epoch 0/minibatch 0 completed canonical live ValueNorm update, finite
nonzero critic backward, and critic optimizer step. Minibatch 1 completed a
second finite canonical ValueNorm update, then failed the nonzero owned-gradient
audit with `STOP — B2-R MUTATION_ATTRIBUTION`. Exact completed counts are:

```text
actor backward / optimizer.step: (5,5,5) / (5,5,5)
critic backward / optimizer.step: 1 / 1
live ValueNorm.update:             2
canonical ValueNorm mutations:    2
S7/S8/S9/S10:                     not reached
critic / ledger / actor rollover: 0 / 0 / 0
successful real transactions:     0
```

The second critic backward was attempted but failed inside its post-backward
audit before a completion counter/receipt. Attempt 3 is therefore
`partial_update=true`, `route_poisoned=true`, and permanently nonreusable under
the current authorization. No repair or rerun was performed.

## Active architecture / evidence path

- Real collection and terminal learner transport feed the existing reviewed
  R5 coordinator; no second transaction implementation exists.
- Original proposal action and rollout behavior logprob remain separate from
  effective assignment/P2 evidence.
- Event returns compute exactly once; the frozen `returns[:-1]` digest equals
  the event-return digest and excludes the final structural slot.
- Canonical live ValueNorm observation reads `running_mean`,
  `running_mean_sq`, and `debiasing_term` directly on `cuda:0`; native empty
  `state_dict()` is diagnostic only.
- Attempt-3 adapter additions are bounded logging/observer/fail-stop hooks and
  contain no new backward, optimizer-step, or live-ValueNorm executor.

## Files changed for attempt 3

Modified before real mutation:

- `assignment_event_training_real_isaac_adapter.py`
- `scripts/environments/test_assignment_phase_b2_r5i_real_isaac_single_transaction.py`

Created:

- `scripts/environments/test_assignment_phase_b2_r5i_re2_observability_pure.py`
- `202609/20260908/PHASE_B2_R5I_REAL_ISAAC_SINGLE_TRANSACTION_ATTEMPT3_REPORT.md`
- `202609/20260908/TASK_PROGRESS_ARCHIVE_BEFORE_B2_R5I_RE2_ATTEMPT3_HANDOFF_20260908.md`

This file was rewritten after its byte-exact archive. No qualified R3/R4/R5
semantic source or installed HARL file was changed for attempt 3.

## Latest verification

- Exact interpreter: `C:\isaacenvs\isaac45_harl\python.exe` — PASS.
- Relevant `py_compile` checks — PASS.
- Pure `[B]`/`[B,1]` shape binding — PASS, two encodings, no mutation.
- Focused VF runtime-fingerprint qualification — PASS, 53 assertions.
- Attempt-3 pure durable-observer checks — PASS, 73 assertions.
- R5I static-only checks before and after the real run — PASS.
- One formal real Isaac worker — expected fail-stop at S6; no retry.
- Static cardinality remains backward/actor-step/critic-step/ValueNorm
  `1/1/1/1`, R5 coordinator `1`, reviewed private edges `18`, public refs `0`.
- Pre-existing staged paths remain 359; staged-index SHA-256 remains
  `a40169043c3bfffd481a7ed1bddf3e52663d61379bedfd2610781457d11f947c`.

## Known issue / blocker

At critic epoch 0/minibatch 1, rows `(2,3)`, the canonical ValueNorm update
changed all three finite live fields, but the subsequent nondegenerate critic
backward produced no nonzero owned gradient. The reviewed gradient guard
correctly stopped the transaction. Diagnosing or changing critic/gradient
semantics and running attempt 4 requires new explicit authorization.

The worker serialized a valid failed result but exited with OS code 0; no
durable environment/SimulationApp close receipt was returned. This diagnostic
does not alter the failed classification. No process or reusable route remains.

## Do not do

Do not reuse any of the three poisoned routes. Do not patch learner semantics
and rerun Isaac under the attempt-3 authorization. Do not begin B2-R6a/R6b or
B2-R7, start training, evaluate/play back, save/load checkpoints, write
best-model outputs, activate the public route, stage, commit, or push.

## Next step

Independent GPT review of the attempt-3 S6 critic-gradient failure and its
durable evidence. Wait for explicit follow-up authorization before design,
semantic changes, or any further real Isaac reentry.

## Detailed reports / archives

- `202609/20260908/PHASE_B2_R5I_REAL_ISAAC_SINGLE_TRANSACTION_ATTEMPT3_REPORT.md`
- `202609/20260908/TASK_PROGRESS_ARCHIVE_BEFORE_B2_R5I_RE2_ATTEMPT3_HANDOFF_20260908.md`
- `202609/20260902/PHASE_B2_R5I_VF_VALUENORM_RUNTIME_FINGERPRINT_COMPATIBILITY_QUALIFICATION_REPORT.md`
- `202609/20260902/PHASE_B2_R5I_RC_POST_REPAIR_CONTROLLED_REGRESSION_QUALIFICATION_REPORT.md`
- `202609/20260902/PHASE_B2_R5I_REAL_ISAAC_SINGLE_TRANSACTION_REENTRY_REPORT.md`
- `202609/20260901/PHASE_B2_R5I_REAL_ISAAC_SINGLE_TRANSACTION_INTEGRATION_REPORT.md`

Archive byte identity before this rewrite:

```text
bytes:  3960
sha256: f55162eac50106625ac1812ff2c185a1343efd1865b3244dbaa5331c3df2768d
```
