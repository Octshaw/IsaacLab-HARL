# Lifecycle-aware Dynamic MRTA — Task Progress

Updated: 2026-09-01

## Current status

```text
B2-R0: GPT REVIEW PASS / FROZEN
B2-R1: GPT REVIEW PASS / CLOSED
B2-R2: GPT REVIEW PASS / CLOSED
B2-R3: GPT REVIEW PASS / CLOSED
B2-R4: GPT REVIEW PASS / CLOSED
B2-R5: GPT REVIEW PASS / CLOSED

B2-R5I: NOT COMPLETE
classification: PHASE-B2-R5I-STOP-POST-MUTATION-FACTOR-AUDIT-NOT-COMPLETE
route: PARTIAL_UPDATE / POISONED / PROCESS STOPPED
successful real full learner transactions: 0
S10 entries: 0

real Isaac full-learner integration: NOT ESTABLISHED
training-update readiness: NOT YET ESTABLISHED
public learned-policy route: DORMANT / BLOCKED
```

## B2-R5I outcome

The bounded real Isaac worker constructed and reset one
`Isaac-Scan-Mobile-Manipulator-Direct-v0` environment with profile
`event_gated_local_mrta`, collected one `T=2,E=2,M=3,N=12` batch in two real
environment steps, and entered the private R5 transaction once.

The deterministic actor order was `(1, 2, 0)`. Actor 1 completed five
backward/optimizer steps and actor 2 completed five. The actor-2 R3 factor
post-audit then raised `STOP — B2-R FACTOR`. Because mutation had already
occurred, the route was poisoned and the process stopped immediately. Actor 0,
critic mutation, live ValueNorm mutation, rollout-mode restore, all rollovers,
terminal-ledger reset, S10 and checkpoint I/O were not entered.

The failure exposed a mask-shape bug in the accumulated R3 source: applying
`nonzero(...).flatten()` directly to a real `[B,1]` mask mixed row indices with
the zero column coordinate. The narrow repair first flattens the mask and then
extracts true-row indices, accepts `[B]` and `[B,1]`, and rejects wider masks.
Its pure regression passed. No controlled or real learner transaction was run
after that source repair, so the repair is not evidence of a successful B2-R5I
transaction and this task does not authorize an automatic retry.

## Exact bounded execution evidence

```text
authoritative real collection workers:        1
real environment construction/reset:          1 / 1
real environment steps:                       2
real DVM / forced-continuation decisions:      6 / 6
event-return computations:                    1
private R5 coordinator entries:               1
training-mode entries / rollout restorations: 1 / 0
actor backward / optimizer.step:              10 / 10
per actor 0,1,2 backward/step:                 0/0, 5/5, 5/5
critic backward / optimizer.step:             0 / 0
live ValueNorm updates:                        0
critic rollover / ledger reset:               0 / 0
actor storage rollovers:                       0
successful real full learner transactions:    0
S10 entries:                                   0
checkpoint weight I/O:                         0
training campaign / evaluation / playback:    0 / 0 / 0
public learned-policy activation:              0
```

The collected batch included a real TIME_LIMIT terminal/autoreset event and
passed the pre-learner terminal-history, final-observation and P2 checks.
Event returns were computed once. Their in-memory digests were not durably
emitted before the later post-mutation exception, so no digest value is
claimed. This is real terminal collection evidence, not successful full
learner-transaction evidence.

## Files

Created:

- `assignment_event_training_real_isaac_adapter.py`
- `assignment_event_training_real_isaac_adapter_guards.py`
- `scripts/environments/test_assignment_phase_b2_r5i_real_isaac_single_transaction.py`
- `scripts/environments/test_assignment_phase_b2_r5i_real_shape_binding_pure.py`
- `202609/20260901/PHASE_B2_R5I_REAL_ISAAC_SINGLE_TRANSACTION_INTEGRATION_REPORT.md`
- `202609/20260901/TASK_PROGRESS_ARCHIVE_BEFORE_B2_R5I_HANDOFF_20260901.md`

Modified:

- `assignment_event_training_actor_mutation.py`
- this `TASK_PROGRESS.md`

The handoff archive is byte-exact to the pre-R5I file: SHA-256
`986c49cfa15333c53bd648b1045e0cdaa4123fac8220335aaa1761965e435b42`,
5,530 bytes. Installed HARL files were not modified.

## Verification

- New and modified Python files compile.
- R5I static/private/public guards pass: one R5 call, one event-return call,
  zero new backward/optimizer/ValueNorm executors, zero environment lifecycle
  calls in the adapter, and zero public production references.
- All three R1 pure suites, the R3 controlled mutation regression, and the R5
  controlled full-transaction regression passed before the real run.
- After the failure and repair, the dedicated `[B]`/`[B,1]` shape-binding pure
  regression, R1 update-plan/factor pure checks, compile checks and R5I static
  guards passed.
- No learner transaction was rerun after the repair.

Failure artifact: `%LOCALAPPDATA%\\Temp\\b2_r5i_real_single_20260901.json`,
SHA-256 `f774ee34ee2208d40fb31718bb4945f17a01e68f94ff489f86e9e07bb2d950fa`.

## Retained boundaries

Do not retry the real transaction without separate explicit authorization. Do
not proceed to B2-R6 or B2-R7, start training, run evaluation/playback, perform
checkpoint weight I/O, activate the public route, stage, commit or push.

## Next step

Independent GPT review of the B2-R5I failure evidence, poisoned-route handling,
and narrow row-index repair. A new B2-R5I reentry, if desired, requires a
separate explicit instruction.
