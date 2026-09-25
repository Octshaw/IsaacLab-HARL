# Phase B2-R5I Real-Isaac Single-Transaction Attempt 3 Report

Date: 2026-09-08 (Asia/Shanghai)

Classification:
`PHASE-B2-R5I-RE2-STOP-S6-CRITIC-SEQUENCE-NOT-COMPLETE`

Attempt 3 completed the full real S5 actor sequence and entered S6. Critic
epoch 0/minibatch 0 completed one canonical live ValueNorm update, one
nonzero finite backward, and one optimizer step. Epoch 0/minibatch 1 then
completed its second canonical live ValueNorm update, but its critic backward
failed the owned-gradient nonzero audit. This is a post-mutation failure:
`partial_update=true`, `route_poisoned=true`, and `S10=0`. The process was
stopped and no repair or rerun was performed under this authorization.

## A. Repository authority

```text
branch:      main
HEAD:        b71d85a32f51be6ada324f870813a56bb45dd396
origin/main: b71d85a32f51be6ada324f870813a56bb45dd396
merge-base:  b71d85a32f51be6ada324f870813a56bb45dd396
relationship: HEAD == origin/main == merge-base
```

The 359 pre-existing monthly-archive migration entries were preserved. Their
staged-index digest was unchanged before and after the run:
`a40169043c3bfffd481a7ed1bddf3e52663d61379bedfd2610781457d11f947c`.
This task did not run `git add`, `git commit`, or `git push`.

## B. Attempt-1/attempt-2 historical separation

- Attempt 1 remains historical `PARTIAL_UPDATE / POISONED / STOPPED`; it
  failed the pre-repair R3 `[B,1]` factor audit after actor mutation.
- Attempt 2 remains historical `PARTIAL_UPDATE / POISONED / STOPPED`; it
  completed S5 and stopped at the old registration-only ValueNorm fingerprint
  false negative.
- Attempt 3 used fresh PID 24480 and update/run identity
  `b2-r5i-re2-fresh-24480`. Durable evidence records `fresh_process=true` and
  `historical_route_reused=false`. Neither historical route was reused or
  rehabilitated.

Attempt 3 is a third independently poisoned route. Its critic-gradient failure
must not be conflated with either earlier failure.

## C. RC and VF qualification identities

- `B2-R5I-RC`: GPT REVIEW PASS / CLOSED. The controlled canonical `[B]` and
  `[B,1]` row repair remained qualified and crossed real S5 in attempt 3.
- `B2-R5I-VF`: GPT REVIEW PASS / CLOSED. Canonical live state is the ordered
  tuple `running_mean`, `running_mean_sq`, `debiasing_term`, qualified on CPU
  registered, CPU runtime-style Tensor, and CUDA runtime-style Tensor
  representations.
- Qualified R5I baseline digest:
  `336dfdad1c6246b5e7b1b9ff6258cd9c7b87c19982007b442abca680f7cd339d`.
- Attempt-3 audited logging-only adapter digest:
  `e19c39a756b73d884b221d4755f8d99474738c8475e1702e93ba0cb50ef923f9`.

RC and VF qualification did not pre-approve a successful real transaction and
does not make any poisoned route reusable.

## D. Qualified source hashes

Repository sources used by the fresh worker:

```text
assignment_event_training_evidence.py
  1d9ae8c460fec99fea40fe0b0d954987d68857f19f47e71e2d7f57e6c8152ed9
assignment_event_training_gradient_probe.py
  19c24185436962099c7f0e4b149161ce42349c017dcef4b1338e3c6a370f3a17
assignment_event_training_actor_mutation.py
  08eb3442ac52dc4f7fd69434486ee7ec77920c64e614d0a19944f4b163b078e3
assignment_event_training_critic_mutation.py
  a9f1e885b35fb749ffd97397d2c991698262dc9d141e30b45d7a45fb3c0bfcaa
assignment_event_training_full_transaction.py
  ec42cb68db274f42144489f4e8ef199311c557016c4859475057c1deed417c35
assignment_value_normalizer_checkpoint.py
  baa339431fa2b2c1933c468091f47b818f3fea7e2ce1394ffdd18c94265d11c1
```

Installed HARL sources were not modified:

```text
happo.py:    dd44fe7842160aa215b2d220726f6dd5e70b251c1a2e9c50cfeb6bd00535cf96
v_critic.py: ae66390702efb55099d151c11f28ae533f25ef6d62697949445abd2979708bf3
valuenorm.py:a35471b136567bde0b7fc7be34a7873efa617bdabf9a9074517ff0e3ef3fb8b0
```

## E. Files created/modified

Modified before learner mutation for bounded logging/harness observability:

- `assignment_event_training_real_isaac_adapter.py`: durable S5 factor and S6
  canonical ValueNorm/critic progress observers plus fail-stop receipts; no R3,
  R4, or R5 semantics changed.
- `scripts/environments/test_assignment_phase_b2_r5i_real_isaac_single_transaction.py`:
  attempt-3 fresh-worker identity, artifact routing, source/static checks, and
  failure persistence.

Created:

- `scripts/environments/test_assignment_phase_b2_r5i_re2_observability_pure.py`;
- this report;
- `TASK_PROGRESS_ARCHIVE_BEFORE_B2_R5I_RE2_ATTEMPT3_HANDOFF_20260908.md`.

`AgentRead/TASK_PROGRESS.md` is rewritten after that byte-exact archive. No
qualified semantic production/evidence source and no installed package file
was changed in this attempt-3 slice.

## F. Fresh process/AppLauncher/env identity

```text
formal supervisor attempts: 1
fresh worker processes:      1
worker PID:                  24480
run/update identity:         b2-r5i-re2-fresh-24480
AppLauncher lifetimes:       1
environment constructions:  1
environment:                 Isaac-Scan-Mobile-Manipulator-Direct-v0
environment type:            ScanMobileManipulatorEnv
profile:                     event_gated_local_mrta
device:                      cuda:0
resets:                      1
```

The supervisor recorded worker JSON status `failed` and a valid failure
result. Its OS exit code was 0 because the worker serialized the handled
contract failure; this does not convert the transaction to PASS. No durable
environment-close or SimulationApp-close receipt was returned, so none is
claimed. PID 24480 was not reused.

## G. Exact real config

```text
resolved T/E/M/N:             2 / 2 / 3 / 12
actor epochs/minibatches:     5 / 2
critic epochs/minibatches:    5 / 2
actor/critic partition:       reviewed_exact_coverage
fixed actor order:            false
ValueNorm enabled:            true
clip_param:                   0.2
entropy_coef:                 0.01
max_grad_norm:                10.0
use_clipped_value_loss:       true
use_huber_loss:               true
use_max_grad_norm:            true
use_policy_active_masks:      true
value_loss_coef:              1.0
config digest: caf5884da95c6c6ac32658782e44710ee308891490999bf9e7a19ff1f89dc914
```

## H. Real-vs-controlled classification

The formal transaction used real Isaac environment/reset/step outputs and
live CUDA learner objects. It was not a synthetic or controlled R3/R4/R5
transaction. The CPU/CUDA preflight probes and the pure observability test are
separate non-Isaac qualification evidence and are not counted as real learner
transactions.

## I. Real runtime collection path

One reset and two real rollout steps produced the `T=2, E=2, M=3` historical
batch. Two terminal/autoreset records were transported. The batch entered the
single reviewed R5 coordinator. There was no second full-transaction
implementation and no second learner batch.

Bound runtime digests were:

```text
actor observation:  f3e448a008f421e8a9438ae49681a716836be00bcc7b9382a328be3739c3f468
critic observation: 86d29fdd0c98f7f9b5db01f1c8cd46c7ba45753303e508ee789cd554d801f4e1
availability:       c078c316b443933cdf8ec2eddc338e63a02eb84e7df7be9d08ebe50e44765093
lifecycle evidence: 341efda8f45c37ef8369b2f890f81fecbc491e70bb4477b552b8dc573e1809b2
```

## J. Proposal/action/logprob identity

```text
proposal action:      4136c7cfe4461db0db73ec7bad0508e24a0d63c1ab5f000fe3168dedf73863c4
rollout behavior logprob:
  c95db5620e515dbdcae42e30be921bb8f6ccaf7961dc09702700ea7d84cfcbe5
```

The original real proposal action and stored rollout behavior logprob were
used. The behavior logprob was not recomputed or replaced by effective
assignment evidence.

## K. DVM/active/availability shapes and rows

For actors 0, 1, and 2, both DVM and active-mask shapes were `[4,1]`.

```text
actor 0: DVM rows (0,1); active-and-DVM rows (0,1); off-DVM rows (2,3)
actor 1: DVM rows (0,1); active-and-DVM rows (0,1); off-DVM rows (2,3)
actor 2: DVM rows (0,1); active-and-DVM rows (0,1); off-DVM rows (2,3)
```

Every canonical-row audit recorded zero duplicate, out-of-range, omission, and
unexpected-row faults. Availability digest is listed in section I; DVM digest
is `457fb86bae1127d870419e5824b66d98cfae9b98cc6386f6e4fe4d6d65e99cae`
and active-mask digest is
`a78d27153a730922deaa63ddc5968729a02a3e22aa15ea0e2fbac59adbc80eef`.

## L. P2/effective-assignment separation

Proposal/effective authority separation was true. Effective-assignment digest
was `cc79daa97bff210281c2c067b770985ad82a292792cc60d7e0fa26cc360062d3`.
No lifecycle/P2, resolver, proposal, or behavior-logprob semantic was changed.

## M. Terminal/autoreset evidence

Two terminal/autoreset records were bound under keys `(0,0,1)` and `(1,0,1)`.
The authoritative pre-reset critic digest was
`c120c16dd20e4c7138e841ba72f2b0f863bef25c09f313864c50650bf8c0d23a`;
the post-reset current-state critic digest was distinct:
`df1bc7ba60579082acd37b2dc69ecdd54cbc5f99c8d9547beaf54db1fdf39a23`.
Terminal-reason-grid digest was
`137fd13cd7f836c5566810b9755e22027a4077a311e693286b0822e22dfa8d0a`.

## N. Timeout sidecar

Timeout sidecar digest was
`6ddd3b7436d04ae8c7603ac0fe4b92245cea991cd8962a56aed332aa1401df03`;
timeout-critic evidence digest was
`68465b82e85069abd9f41e80099fa3166d5dba6b38a7f9906086ede985722edf`.
Exact timeout-critic identity and runtime ACK were true. The learner ledger was
still retained after ACK, with two keys, before learner mutation.

## O. Pre-mutation durable artifact

Before the first actor optimizer step, every mutation counter was zero and the
state history was S0 through S4 with one training-mode entry. Durable artifact:

```text
%TEMP%/b2_r5i_re2_attempt3_pre_mutation_20260907_01.json
bytes:  201525
sha256: 0e90e607755c2de5e5188637623a0fdbf9f65d36e87ca668ce4f6efc9ef695ef
```

It binds repository/source authority, real runtime digests, terminal evidence,
returns, plans, expected counts, masks, initial component fingerprints, and
the initial canonical CUDA ValueNorm state without dumping model state.

## P. Event-return digest

Event returns were computed exactly once by the event-aware route. The stock
`compute_returns` call count was zero. Digest:
`98840b7991923e26a5b027892008e55c7f3f104cfb32824994a4f8686db3c95e`.

## Q. `returns[:-1]` identity

The frozen training slice `returns[:-1]` had the same digest as the event
return result and exact equality was true. The two objects did not alias. The
excluded structural final slot digest was
`af5570f5a1810b7af78caf4bc70a660f0df51e42baf91d4de5b2328de0e83dfc`.

## R. Immutable plan/count derivation

```text
actor order:          (1,2,0)
actor plan digest:    edda0edf18efcc45fd1dc327e0fc008d1bb58382d3e6062a3741d7cf185f4c51
critic plan digest:   315ae1f4477b9fb45d9e09becfba8df878f00de33aee9146eb69cf5a76807bf8
expected actor backward/step per actor: (5,5,5) / (5,5,5)
expected critic backward/step:          10 / 10
expected live ValueNorm updates:         10
```

Counts were derived from the resolved shuffled plan; they were not hard-coded
as success criteria. Rollout evidence, terminal evidence, returns, and plans
remained frozen through the reached boundary.

## S. S0-S4

S0 real rollout complete, S1 terminal/final-value evidence bound, S2 event
returns frozen once, S3 immutable plans frozen, and S4 explicit training mode
all completed before the first optimizer mutation. State history then entered
S5 and S6 in order.

## T. Complete actor sequence

S5 completed for actor order `(1,2,0)`. Each actor completed five backward
operations and five optimizer steps. Totals were 15/15. Each segment passed
the factor post-audit, preserved prior accumulation, used real historical
inputs, and cleaned gradients before the next segment.

## U. Per-actor durable factor receipts

The progress artifact was flushed after every actor segment:

| Actor/order | Factor before | Pre logprob | Post logprob | Full ratio / factor after | DVM/off-DVM | Bwd/step | Audit |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1/0 | `f6bb1294…08e4` | `983034b6…5f9` | `b1d47e45…3599` | `e2358e69…541b` / `e2358e69…541b` | `(0,1)` / `(2,3)` | 5/5 | PASS |
| 2/1 | `e2358e69…541b` | `ef86fad1…5f9` | `1ec903fe…1c5` | `0d87b88f…542` / `605bc052…57ce` | `(0,1)` / `(2,3)` | 5/5 | PASS |
| 0/2 | `605bc052…57ce` | `21566507…f87` | `6115ed12…2eb` | `b04c0b74…93f` / `fb3e86b4…36ac` | `(0,1)` / `(2,3)` | 5/5 | PASS |

All three off-DVM exact-one audits were true. Full values are retained in:

```text
%TEMP%/b2_r5i_re2_attempt3_factor_progress_20260907_01.json
bytes:  6295
sha256: 03b9cf1dbd95e2873fbacd010fa53d21b1c2aa2017406149765686ae568d5937
events: 4 (three segment receipts plus S5-complete receipt)
```

## V. Final factor

`complete_actor_sequence=true`, three actor segments and three post-audit
passes were durably recorded. Initial factor digest was
`f6bb1294da2f78cd935b01c7656280df5eaa0439e9d97bc03775825a41a508e4`;
final factor digest was
`fb3e86b471d87c9965fb3281fba4f0bab16ed768d7eb8ccea57e46db6e2236ac`.

## W. S6 critic sequence

S6 did not complete. Epoch 0/minibatch 0, physical rows `(0,1)`, completed its
ValueNorm update, critic backward, and critic optimizer step. Epoch
0/minibatch 1, rows `(2,3)`, completed its canonical ValueNorm update and then
attempted critic backward. The backward audit observed no nonzero owned
gradient and raised:

```text
B2RContractError: nondegenerate probe produced no nonzero owned gradient;
stop_code='STOP — B2-R MUTATION_ATTRIBUTION';
stage='post_backward_gradient_audit';
expected='at least one nonzero owned gradient'; observed=False
```

The authoritative completed critic backward count is 1 because the second
call failed inside its post-backward audit before a completion receipt/counter.
It is separately reported as an attempted second backward, not as a completed
one. No minibatch-1 optimizer step or later critic minibatch ran.

## X. Per-minibatch canonical ValueNorm pre/post evidence

Initial canonical CUDA fingerprint was
`ade87b50d42654800d34babd0b0942a9901b1e91a7e6c12728a3d64b3bc6b0d9`.
All three live attributes were ordinary `Tensor` objects on `cuda:0`; native
`state_dict()` key count was zero and was diagnostic only.

Minibatch `(epoch=0, mb=0, rows=(0,1))`:

- raw target digest:
  `344626ed4ac2932a76f3ca3baca462e7f5244465ad114b0fb5066a0487ea2b2b`;
- pre/post fingerprints: `ade87b50…b0d9` -> `aed49955…42ec`;
- changed finite fields: all three;
- post values/digests:
  `running_mean=1.6533523421458085e-06` / `0607ae34…959b`,
  `running_mean_sq=2.8189148792989727e-07` / `10ab52f2…119`,
  `debiasing_term=9.999999747378752e-06` / `e6540c5b…68c`.

Minibatch `(epoch=0, mb=1, rows=(2,3))`:

- raw target digest:
  `6ff35e22c08a3abf979be0ca526a6936767ee52710043b9c21521f2ee9637eca`;
- pre/post fingerprints: `aed49955…42ec` -> `3585ecfd…1828`;
- changed finite fields: all three;
- post values/digests:
  `running_mean=3.4216056974401e-06` / `44a76893…1ecf`,
  `running_mean_sq=6.032549322299019e-07` / `33c1aebe…5bd8`,
  `debiasing_term=1.9999899450340308e-05` / `3212ddf5…8fde`.

Thus canonical ValueNorm observability worked correctly in attempt 3. The
failure was the subsequent critic-gradient audit, not another ValueNorm
fingerprint false negative. The second live update itself makes the route
post-mutation and poisoned even though its critic minibatch did not complete.

## Y. Critic mutation receipts

The sole complete critic minibatch receipt recorded:

```text
epoch/minibatch: 0 / 0
rows:            (0,1)
critic loss:     0.7322631478309631
gradient finite/nonzero: true / true
gradient norm:   36.85271347028996
clip result:     36.85271072387695
critic parameter: a189358f…e7d -> 2d4c7d49…9200
critic optimizer: 910cbcee…3a7 -> d69ed0ff…f2e9
receipt complete: true
```

The second minibatch has durable pre- and post-ValueNorm events but no critic
completion receipt. Progress artifact:

```text
%TEMP%/b2_r5i_re2_attempt3_critic_progress_20260907_01.json
bytes:  21610
sha256: 4d991a517df679602cf740c5c86f51116887ff34db8f88d3df011dd8c39615bc
events: 5
```

## Z. S7 audit

Not reached. Expected critic/ValueNorm counts were incomplete and the route
was already poisoned. No S7 PASS is claimed.

## AA. S8 mode restoration

Not reached. Rollout-mode restoration count is 0. No same-process restoration
was attempted after the post-mutation failure.

## AB. S9 rollover

Not reached. Critic rollover count is 0 and rollover was explicitly
disallowed by the failure receipt.

## AC. Terminal ledger reset

Not reached. Terminal-ledger reset count is 0. The ledger was not cleared or
used to create a false clean boundary.

## AD. Actor storage rollover

Not reached. Actor storage rollover count is 0; no current runtime state was
written into new slot zero.

## AE. S10

S10 entries: 0. No quiescence receipt, checkpoint-boundary eligibility, or
successful real full learner transaction is claimed.

## AF. Next-rollout-ready check

Not reached. The poisoned route is not next-rollout-ready and cannot collect a
second learner batch.

## AG. Static/private/public guards

Pre- and post-run static checks passed under the exact interpreter
`C:\isaacenvs\isaac45_harl\python.exe`.

```text
reviewed backward executors:             1
reviewed actor optimizer-step executors: 1
reviewed critic optimizer-step executors:1
reviewed live ValueNorm executors:       1
R5 actor-sequence calls:                 1
R5 critic-sequence calls:                1
R5 coordinator calls:                    1
private dependency edges:                18 (reviewed allowlist)
new adapter backward/step/VN calls:      0 / 0 / 0
public references:                       0
public activation:                       0
```

Static artifacts before and after the real run:

```text
%TEMP%/b2_r5i_re2_attempt3_static_pre_20260907_01.json
bytes:  191462
sha256: b05f3aa3cd4a594dab4b9a880b796e9f44da6ff172e9194623d0f0c5346b0583

%TEMP%/b2_r5i_re2_attempt3_static_post_20260908_01.json
bytes:  191462
sha256: b05f3aa3cd4a594dab4b9a880b796e9f44da6ff172e9194623d0f0c5346b0583
```

The qualified hashes in section D and the audited attempt-3 adapter hash were
exact after the failed run. The 359-entry staged index digest remained exact.

## AH. Exact authoritative counts

```text
attempt:                                  3
formal supervisor attempts:               1
fresh worker processes:                   1
retry count:                              0
AppLauncher lifetimes:                    1
environment constructions:               1
resets:                                   1
real rollout steps:                       2
terminal/autoreset events:                2
event-return computations:                1
stock compute_returns calls:              0
training-mode entries:                    1
actor order:                              (1,2,0)
per-actor backward:                       (5,5,5)
per-actor optimizer.step:                 (5,5,5)
factor post-audit PASS:                   3
critic epochs/minibatches planned:        5 / 2
critic backward completed:                1
critic backward additionally attempted:  1 (failed audit)
critic optimizer.step completed:          1
live ValueNorm.update completed:          2
canonical ValueNorm mutation receipts:    2
critic rollover:                          0
terminal-ledger reset:                    0
actor rollovers:                          0
rollout-mode restorations:                0
successful real full transactions:        0
S10:                                      0
checkpoint weight I/O:                    0
training campaigns:                       0
evaluation/playback:                      0
public activations:                       0
```

Per actor, DVM rows were `(0,1)`, active-and-DVM rows were `(0,1)`, and
off-DVM rows were `(2,3)`.

## AI. Setup/diagnostic attempts

There were no pre-mutation formal setup retries: one supervisor, one fresh
worker, and retry count zero. Before mutation:

- the exact conda interpreter and relevant `py_compile` checks passed;
- the pure shape-binding regression passed both supported encodings with
  canonical rows `(0,1)` and `(2,3)`, no range/duplicate faults, and zero
  mutation;
- the focused VF runtime fingerprint qualification passed 53 assertions,
  using standalone CPU/CUDA ValueNorm probes only;
- the new pure durable-observer test passed 73 assertions with no Isaac,
  learner mutation, or full transaction;
- R5I static-only preflight passed.

The single formal real run then produced valid pre-mutation, S5, S6, and
post-failure evidence. Post-run static-only verification also passed. The
handled worker returned OS exit code 0 while its valid JSON status and
classification were `failed`; this shutdown/exit-code diagnostic is retained
and is not treated as success. `durable_observer_error` was null.

Additional bounded artifacts:

```text
post-failure receipt:
  %TEMP%/b2_r5i_re2_attempt3_post_failure_20260907_01.json
  2033 bytes
  b76fa048f871d907eea4c20478455c56bb0b8ec8589e3b777fc9062755cba482

final failure receipt (byte-identical):
  %TEMP%/b2_r5i_re2_attempt3_final_receipt_20260907_01.json
  2033 bytes
  b76fa048f871d907eea4c20478455c56bb0b8ec8589e3b777fc9062755cba482

supervisor result:
  %TEMP%/b2_r5i_re2_attempt3_result_20260907_01.json
  217678 bytes
  81370b417e535353352c0f09f748e48af6050a72fba3f1f005843ad2a9e16815
```

## AJ. Retained nonclaims

This report does not establish B2-R5I completion, training-update readiness,
performance, convergence, checkpoint eligibility, a reusable learner route,
another rollout boundary, public-route readiness, B2-R6a/R6b, or B2-R7. No
training loop, long training, evaluation, playback, checkpoint save/load,
best-model write, performance comparison, staging, commit, or public-route
activation occurred.

## AK. GPT handoff

Independent GPT review should examine the attempt-3 S6 failure at critic epoch
0/minibatch 1: canonical ValueNorm mutation succeeded and remained finite, but
the subsequent nondegenerate critic probe produced zero owned gradient. Under
the authorized retry policy, do not patch learner semantics and do not run a
fourth real transaction from this handoff. Attempts 1, 2, and 3 remain
separate poisoned historical routes. B2-R5I remains NOT COMPLETE; wait for a
new explicit review/design authorization.
