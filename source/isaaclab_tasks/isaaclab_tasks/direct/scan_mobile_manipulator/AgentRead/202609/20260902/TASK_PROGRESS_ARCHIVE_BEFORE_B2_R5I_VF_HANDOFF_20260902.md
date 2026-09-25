# Lifecycle-aware Dynamic MRTA — Task Progress

Updated: 2026-09-02

## Current status

```text
B2-R0: GPT REVIEW PASS / FROZEN
B2-R1 through B2-R5: GPT REVIEW PASS / CLOSED
B2-R5I-RC: GPT REVIEW PASS / CLOSED
R3 [B]/[B,1] repair: CONTROLLED QUALIFIED

B2-R5I: NOT COMPLETE
successful real full learner transactions: 0
real B2-R5I S10 entries: 0

historical attempt 1: PARTIAL_UPDATE / POISONED / PROCESS STOPPED
fresh reentry attempt 2: PARTIAL_UPDATE / POISONED / PROCESS STOPPED
real Isaac full-learner integration: NOT ESTABLISHED
training-update readiness: NOT YET ESTABLISHED
B2-R6a/R6b and B2-R7: NOT AUTHORIZED
public learned-policy route: DORMANT / BLOCKED
```

Classification:
`PHASE-B2-R5I-RE-STOP-LIVE-VALUENORM-NO-STATE-MUTATION-NOT-COMPLETE`

## Latest authorized reentry

One fresh process (PID 13068, identity `b2-r5i-re-fresh-13068`) performed one
real Isaac collection and entered the existing R5 learner coordinator. It did
not reuse the historical poisoned route.

Durable pre-mutation evidence captured S0-S4 plus the S5 entry boundary before
any actor step. Real config was `T=2, E=2, M=3, N=12`; actor order was
`(1,2,0)`. Two physical rollout steps produced two TIME_LIMIT/autoreset events.
Event returns were computed once.

S5 completed: each actor executed 5 backward calls and 5 optimizer steps
(15/15 total). In S6, the first live ValueNorm update was invoked, but its
state fingerprint did not change. R4 raised `STOP — B2-R MUTATION_ATTRIBUTION`.
The fresh route is therefore poisoned. No retry or second real worker ran.

## Exact counts and boundary

```text
AppLauncher / env construction / reset: 1 / 1 / 1
real physical rollout steps / terminal events: 2 / 2
event-return computations: 1
actor backward / optimizer.step: 15 / 15; per actor (5,5,5)
critic backward / optimizer.step: 0 / 0
live ValueNorm.update: 1
S7 / S8 / S9 / S10 entries: 0 / 0 / 0 / 0
critic rollover / ledger reset / actor rollovers: 0 / 0 / 0
successful real full learner transactions: 0
retry / checkpoint weight I/O / training-eval-playback / public route: 0
```

The qualified R3 source SHA-256 was
`08eb3442ac52dc4f7fd69434486ee7ec77920c64e614d0a19944f4b163b078e3`.
Post-STOP `py_compile`, R5I static-only, pure mask-shape, executor cardinality,
private-dependency, and public-reference guards passed. No real rerun occurred.

## Durable evidence and report

- Pre-mutation artifact: `b2_r5i_re_pre_mutation_20260902_01.json`, 9,117
  bytes, SHA-256 `8c511a47947d4e5c7eec9f04e121fb1d465165878483d0558f3e737851bb6948`.
- Post-failure artifact: `b2_r5i_re_post_failure_20260902_01.json`, 1,594
  bytes, SHA-256 `ab8ce8e4949e5084a6cfb33c79e4e9292c208659a72e6ec87b55397cfdec9e1d`.
- Supervisor result: `b2_r5i_re_result_20260902_01.json`, 16,550 bytes,
  SHA-256 `87d49d645408901fcf7e6c68ef93489af0f42cf605c2507aef4d09ef4756fe56`.
- Full report:
  `202609/20260902/PHASE_B2_R5I_REAL_ISAAC_SINGLE_TRANSACTION_REENTRY_REPORT.md`.

The pre-reentry handoff archive is byte-exact: 4,594 bytes, SHA-256
`c61adbd6784d1fe0581df892057d61f19e7e66826df4ab81732356a955c68828`.

## Do not do

Both real attempt processes are permanently non-reusable. Do not repair and
rerun real learner mutation without new authorization. Do not begin B2-R6 or
B2-R7, train, evaluate/play back, perform checkpoint weight I/O, activate the
public route, stage, commit, or push.

## Next step

Independent GPT review of this fresh-process B2-R5I reentry failure record.
