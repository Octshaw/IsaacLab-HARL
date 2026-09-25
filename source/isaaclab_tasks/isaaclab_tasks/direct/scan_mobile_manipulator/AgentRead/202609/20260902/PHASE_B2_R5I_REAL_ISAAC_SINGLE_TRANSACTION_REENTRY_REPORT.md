# Phase B2-R5I-RE Fresh-Process Real-Isaac Single-Transaction Reentry Report

Date: 2026-09-02

Classification:
`PHASE-B2-R5I-RE-STOP-LIVE-VALUENORM-NO-STATE-MUTATION-NOT-COMPLETE`

This report records the one authorized fresh-process real-Isaac reentry. The
run failed after mutation began, so the new route is poisoned and was stopped
without repair or retry. B2-R5I remains NOT COMPLETE.

## A. Repository/source authority

- Branch: `main`.
- `HEAD`, `origin/main`, and merge base: `b71d85a32f51be6ada324f870813a56bb45dd396`.
- Qualified R3 actor-mutation source SHA-256:
  `08eb3442ac52dc4f7fd69434486ee7ec77920c64e614d0a19944f4b163b078e3`.
- The pre-mutation artifact durably records the exact repository and installed
  HARL source hashes used by process 13068.
- The 359 pre-existing staged archive-migration entries were not altered.

## B. Historical poisoned-route separation

The historical B2-R5I route remains `PARTIAL_UPDATE / POISONED / PROCESS
STOPPED` and was not reused. This reentry used a new OS process, new learner
objects, and update/run identity `b2-r5i-re-fresh-13068`; both durable artifacts
record `fresh_process=true` and `historical_route_reused=false`.

This fresh route is now independently `PARTIAL_UPDATE / POISONED / PROCESS
STOPPED`. The two failure identities must not be conflated:

1. Historical attempt: R3 factor-path failure; retained only as evidence.
2. Fresh reentry: S6 live ValueNorm update executed but produced no state
   fingerprint mutation.

## C. RC qualification identity

`B2-R5I-RC` is `GPT REVIEW PASS / CLOSED`. Its qualified `[B]`/`[B,1]`
canonical mask-row behavior was the fixed R3 source identity above. RC did not
establish a real full learner transaction and did not make the historical
poisoned process reusable.

## D. Files created/modified

Modified for this authorized integration/observability slice:

- `assignment_event_training_real_isaac_adapter.py`: durable pre-mutation and
  post-failure observer integration around the existing R5 coordinator.
- `scripts/environments/test_assignment_phase_b2_r5i_real_isaac_single_transaction.py`:
  fresh reentry identity, qualified-source check, and persistent artifact
  paths.
- `AgentRead/TASK_PROGRESS.md`: concise fail-stop handoff.

Created:

- this report;
- `TASK_PROGRESS_ARCHIVE_BEFORE_B2_R5I_RE_HANDOFF_20260902.md`;
- three external durable evidence artifacts listed in section O.

No R3 actor mutation, R4 critic/ValueNorm mutation, R5 transaction semantic
source, installed HARL source, or public route source was changed in this
reentry slice.

## E. Fresh process/AppLauncher/env identity

- Fresh worker process: PID 13068.
- Run/update identity: `b2-r5i-re-fresh-13068`.
- AppLauncher lifetimes: 1.
- Real environment constructions: 1.
- Real resets: 1.
- Real physical rollout steps: 2.
- The process terminated and was not reused. No durable environment-close or
  SimulationApp-close receipt was returned, so this report does not fabricate
  one.

## F. Real config T/E/M/N

The resolved real configuration was `T=2`, `E=2`, `M=3`, `N=12` with five
actor epochs, two actor minibatches, five critic epochs, two critic
minibatches, shuffled actor order, and live ValueNorm enabled. Config digest:
`caf5884da95c6c6ac32658782e44710ee308891490999bf9e7a19ff1f89dc914`.

## G. Real-vs-controlled classification

This was one real Isaac collection and live learner-mutation attempt in a
fresh process. It was not a controlled/synthetic learner transaction. It is a
post-mutation STOP, not a PASS transaction and not evidence of full-learner
integration readiness.

## H. Real collection path

One AppLauncher lifetime constructed and reset the real environment, then made
two physical rollout steps through the private assignment-event collection and
terminal learner-transport path. The collected batch then entered the single
existing R5 coordinator; no second transaction implementation was constructed.

## I. Real actor observations/actions/logprobs

The pre-mutation artifact binds the real rollout inputs before the first actor
optimizer step:

- actor-observation digest:
  `f3e448a008f421e8a9438ae49681a716836be00bcc7b9382a328be3739c3f468`;
- proposal-action digest:
  `4136c7cfe4461db0db73ec7bad0508e24a0d63c1ab5f000fe3168dedf73863c4`;
- rollout behavior-logprob digest:
  `c95db5620e515dbdcae42e30be921bb8f6ccaf7961dc09702700ea7d84cfcbe5`.

## J. DVM/active/availability masks and shapes

For actors 0, 1, and 2, DVM and active masks each had shape `[4,1]`.
Availability digest was
`c078c316b443933cdf8ec2eddc338e63a02eb84e7df7be9d08ebe50e44765093`;
DVM digest was
`457fb86bae1127d870419e5824b66d98cfae9b98cc6386f6e4fe4d6d65e99cae`;
active-mask digest was
`a78d27153a730922deaa63ddc5968729a02a3e22aa15ea0e2fbac59adbc80eef`.

## K. Canonical row extraction witness

Each actor produced DVM rows `(0,1)`, active-and-DVM rows `(0,1)`, and off-DVM
rows `(2,3)`. Each per-actor row audit recorded zero duplicate DVM rows, zero
out-of-range DVM rows, zero duplicate off-DVM rows, and zero out-of-range
off-DVM rows. This is the real-batch witness of the qualified R3 `[B,1]` path.

## L. Proposal/effective/P2 separation

`proposal_effective_authority_separate=true`. Proposal evidence and effective
assignment/P2 evidence remained separate; effective-assignment digest was
`cc79daa97bff210281c2c067b770985ad82a292792cc60d7e0fa26cc360062d3`.

## M. Real terminal/autoreset evidence

The two real physical rollout steps produced two TIME_LIMIT/autoreset terminal
events. Lifecycle rollout-evidence digest was
`0d4bec7264b10940ff8526c6de3ecb352d367859479c1964658f160ee4a55ac4`;
terminal-reason-grid digest was
`137fd13cd7f836c5566810b9755e22027a4077a311e693286b0822e22dfa8d0a`.
No synthetic final slot was used.

## N. Timeout-sidecar identity

Timeout-sidecar digest was
`6ddd3b7436d04ae8c7603ac0fe4b92245cea991cd8962a56aed332aa1401df03`;
timeout-critic evidence digest was
`68465b82e85069abd9f41e80099fa3166d5dba6b38a7f9906086ede985722edf`.
The terminal ledger contained exact keys `(0,0,1)` and `(1,0,1)`, count 2.

## O. Pre-mutation durable evidence artifact

Before the first actor optimizer step, the adapter durably wrote S0-S4 plus
the S5 entry boundary, source/config/input/plan digests, initial component
fingerprints, and zero pre-emit actor, critic, and ValueNorm mutation counts.

- Pre-mutation:
  `C:\Users\33506\AppData\Local\Temp\b2_r5i_re_pre_mutation_20260902_01.json`,
  9,117 bytes, SHA-256
  `8c511a47947d4e5c7eec9f04e121fb1d465165878483d0558f3e737851bb6948`.
- Post-failure:
  `C:\Users\33506\AppData\Local\Temp\b2_r5i_re_post_failure_20260902_01.json`,
  1,594 bytes, SHA-256
  `ab8ce8e4949e5084a6cfb33c79e4e9292c208659a72e6ec87b55397cfdec9e1d`.
- Supervisor result:
  `C:\Users\33506\AppData\Local\Temp\b2_r5i_re_result_20260902_01.json`,
  16,550 bytes, SHA-256
  `87d49d645408901fcf7e6c68ef93489af0f42cf605c2507aef4d09ef4756fe56`.

## P. Event returns compute-once and digest

Event returns were computed exactly once. Digest:
`98840b7991923e26a5b027892008e55c7f3f104cfb32824994a4f8686db3c95e`.

## Q. `returns[:-1]` identity

The frozen learner training slice had the same digest as the event-return
evidence:
`98840b7991923e26a5b027892008e55c7f3f104cfb32824994a4f8686db3c95e`.

## R. Immutable plan and count derivation

- Actor order: `(1,2,0)`.
- Actor plan digest:
  `ec15fcf526d447e4abb447d13025b98c9364df3e80fa9c440945b9a93b2df8e0`.
- Critic plan digest:
  `55d4579bd1118f47f747702962fc72d67183046aa09ecf31f4f198801c92ef25`.
- Expected actor backward/step: 5/5 for each actor.
- Expected critic backward/step: 10/10.
- Expected live ValueNorm updates: 10.

## S. S0-S4

The durable pre-mutation history is exactly `S0_ROLLOUT_COMPLETE`,
`S1_FINAL_VALUE_EVALUATED`, `S2_EVENT_RETURNS_FROZEN`,
`S3_UPDATE_PLAN_FROZEN`, `S4_TRAINING_MODE_ENTERED`. Training mode was entered
once. All mutation counters were zero when this artifact was emitted.

## T. Complete S5 actor sequence

S5 completed for actor order `(1,2,0)`. Each actor executed five backward calls
and five optimizer steps: per-actor `(5,5,5)`, total 15/15. Reaching S6 shows
that all three actor segments and their R3 post-audits returned successfully.

## U. Factor pre/post and recurrence

Initial factor digest was
`f6bb1294da2f78cd935b01c7656280df5eaa0439e9d97bc03775825a41a508e4`.
The actor sequence completed, but R5 had not returned its receipt when R4
raised. Consequently exact per-segment factor post-digests were not durably
exported; none are inferred or fabricated here.

## V. Complete S6 critic/ValueNorm

S6 did not complete. The first live ValueNorm update was physically invoked
and the authoritative count became 1, but its post-update state fingerprint
equaled its pre-update fingerprint. R4 raised:

`STOP — B2-R MUTATION_ATTRIBUTION: nondegenerate live ValueNorm update produced no state mutation`

at `r4_valuenorm_update`. Critic backward and optimizer-step counts remained
0/0. Because mutation had already begun in S5, `partial_update=true` and
`route_poisoned=true`.

## W. S7 audit

S7 was not reached. No complete transaction-level mutation audit exists.

## X. S8 mode restoration

S8 was not reached. Rollout-mode restoration count: 0.

## Y. S9 critic rollover

S9 was not reached. Critic rollover count: 0.

## Z. Terminal-ledger reset

Terminal-ledger reset count: 0. The failure evidence explicitly records
`ledger_reset_allowed=false`.

## AA. Actor storage rollover from real current state

Actor storage rollover count: 0 for every actor. No actor storage was advanced
from the poisoned partial update.

## AB. S10 quiescence

S10 entries: 0. The state history stopped at S6 and the failure receipt records
`s10_reached=false`.

## AC. Next-rollout-ready read-only check

No next-rollout-ready receipt was issued; `next_rollout_allowed=false`. The
fresh route is not reusable.

## AD. Static/private/public guards

After the STOP, no real rerun occurred. Read-only/static verification passed:

- relevant adapter and harness `py_compile`;
- R5I `--static-only`, including the exact qualified R3 hash;
- one reviewed backward executor, one actor-step executor, one critic-step
  executor, one live ValueNorm executor, one R5 coordinator, 18 private
  dependency edges, and zero references across 57 public production files;
- pure mask shapes `[B]` and `[B,1]` passed; `[B,2]` failed closed.

## AE. Exact authoritative execution counts

```text
fresh real AppLauncher lifetimes: 1
real environment constructions: 1
real resets: 1
real physical rollout steps: 2
real terminal/autoreset events: 2
event-return computations: 1
successful fresh real full transactions: 0
S10 entries: 0
actor order: (1,2,0)
per-actor DVM rows: (0,1), (0,1), (0,1)
per-actor active-and-DVM rows: (0,1), (0,1), (0,1)
per-actor off-DVM rows: (2,3), (2,3), (2,3)
per-actor backward: (5,5,5)
per-actor optimizer.step: (5,5,5)
actor backward / optimizer.step total: 15 / 15
critic backward / optimizer.step: 0 / 0
live ValueNorm.update: 1
critic rollover / ledger reset / actor rollovers: 0 / 0 / 0
checkpoint weight I/O: 0
training/evaluation/playback: 0
public-route activations: 0
retry count: 0
```

## AF. Diagnostic/setup attempts

Before Isaac launch, one static-only preflight caught an observability false
positive: a diagnostic `payload.update(...)` expression was counted as a
ValueNorm update. Only that logging expression was rewritten; no learner
semantic source changed and no Isaac process or mutation had begun. The full
preflight then passed.

There was exactly one formal supervisor attempt and one fresh formal worker.
After the post-mutation S6 failure, no repair-and-rerun, retry, second worker,
or second transaction was executed.

## AG. Retained nonclaims

- B2-R5I is NOT COMPLETE and is not self-classified GPT REVIEW PASS.
- Real Isaac full-learner integration is NOT ESTABLISHED.
- Training-update readiness is NOT YET ESTABLISHED.
- B2-R6a/R6b and B2-R7 are NOT AUTHORIZED.
- The public learned-policy route remains DORMANT / BLOCKED.
- Training, long training, evaluation, playback, checkpoint weight I/O,
  staging, commit, and push were not performed.

## AH. GPT-review handoff

Independent GPT review should evaluate this failure record, especially the R4
ValueNorm mutation-attribution STOP. The historical route and this fresh route
must both remain permanently non-reusable. No further real reentry, repair,
B2-R6, B2-R7, training, checkpoint action, or public activation is authorized.

