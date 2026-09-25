# Phase B2-T0 Bounded Repeated-Update Training Smoke Report

Date: 2026-09-09

Final adjudicated classification:

`PHASE-B2-T0-STOP-TX2-FORCED-CONTINUATION-RESAMPLED-NOT-COMPLETE`

This is a failure handoff. B2-T0 did not establish three-transaction repeated-update continuity. The mutation-bearing run completed transaction 1 through S10, then stopped during transaction-2 collection when the bounded harness observed an additional actor-2 policy call on the second collection step. Because transaction 1 had already mutated the persistent learner, the process was classified `partial_update=true`, poisoned, closed, and never retried.

## A. Repository authority

The authority recorded immediately before execution and rechecked after the stop was:

| Field | Value |
|---|---|
| branch | `main` |
| HEAD | `b71d85a32f51be6ada324f870813a56bb45dd396` |
| origin/main | `b71d85a32f51be6ada324f870813a56bb45dd396` |
| merge-base | `b71d85a32f51be6ada324f870813a56bb45dd396` |
| HEAD/origin/merge-base equal | yes |
| staged paths | 359 |
| staged-index SHA-256 | `a40169043c3bfffd481a7ed1bddf3e52663d61379bedfd2610781457d11f947c` |
| staged monthly-migration entries | 359 |
| staged monthly path-set SHA-256 | `0f2b8f7b52148e39196cbeb40fd9f4edd94fb762b6daf8be6279a116b80a39ab` |

The pre-existing staged migration index was preserved. No `git add`, `git commit`, or `git push` was run.

## B. Starting R7 authority

The supplied starting authority superseded the older awaiting-review wording in the R7 handoff:

- B2-R0: `GPT REVIEW PASS / FROZEN`;
- B2-R1 through B2-R5: `GPT REVIEW PASS / CLOSED`;
- B2-R5I-RC, VF, CG, and B2-R5I: `GPT REVIEW PASS / CLOSED`;
- B2-R7: `GPT REVIEW PASS / CLOSED`;
- training-update readiness: `REVIEW PASS / ESTABLISHED`;
- real Isaac full-learner integration and real next-rollout readiness: `REVIEW PASS / ESTABLISHED`;
- public learned-policy route: `DORMANT / BLOCKED`;
- B2-R6a/R6b and long training: `NOT AUTHORIZED`.

Historical B2-R5I attempts 1/2/3 remain poisoned/stopped/historical and were not reused. Attempt 4 remains the reviewed single-transaction witness.

## C. Qualified source hashes

All required semantic sources matched the R7-qualified identities before every AppLauncher start.

| Repository source | SHA-256 |
|---|---|
| `assignment_event_training_evidence.py` | `1d9ae8c460fec99fea40fe0b0d954987d68857f19f47e71e2d7f57e6c8152ed9` |
| `assignment_event_training_plans.py` | `4223b391de5e9302f6c7e895e4ee4da10b6dd8c8860a418036bad5f1441787ad` |
| `assignment_event_training_control.py` | `c3291a2abe94fba3170ecf5e79e6e8aeaa302dbb9c58cda488038323e9c6eb1a` |
| `assignment_event_training_static_guards.py` | `05fed8102340d0738a3af9bab178c1234e6ce8f349929147da1fefe0cd1975db` |
| `assignment_event_training_gradient_probe.py` | `5501947f64ebe33c003b0e08b2fbacd6ccd826c3e5e78d115401ed11061dd985` |
| `assignment_event_training_actor_mutation.py` | `08eb3442ac52dc4f7fd69434486ee7ec77920c64e614d0a19944f4b163b078e3` |
| `assignment_event_training_critic_mutation.py` | `9719bcd059cfe9a670cc9715117ef00e965f708c82134a59c3a1f77296173dde` |
| `assignment_event_training_full_transaction.py` | `ec42cb68db274f42144489f4e8ef199311c557016c4859475057c1deed417c35` |
| `assignment_event_training_real_isaac_adapter.py` | `bff37075343795703b3ad4c7f7d27727278fd23e095e81d2de6b62a94821560e` |
| `assignment_value_normalizer_checkpoint.py` | `baa339431fa2b2c1933c468091f47b818f3fea7e2ce1394ffdd18c94265d11c1` |

| Installed HARL source | SHA-256 |
|---|---|
| `algorithms/actors/happo.py` | `dd44fe7842160aa215b2d220726f6dd5e70b251c1a2e9c50cfeb6bd00535cf96` |
| `algorithms/critics/v_critic.py` | `ae66390702efb55099d151c11f28ae533f25ef6d62697949445abd2979708bf3` |
| `models/value_function_models/v_net.py` | `a3760b3fdf290c73bb13a752c0b0d39f69fd6fa207560272954b44a027f427c3` |
| `common/valuenorm.py` | `a35471b136567bde0b7fc7be34a7873efa617bdabf9a9074517ff0e3ef3fb8b0` |

## D. Files created/modified

Created:

- `scripts/environments/test_assignment_phase_b2_t0_bounded_repeated_update_training_smoke.py` — bounded test/orchestration and durable-evidence harness, final SHA-256 `b01d5af1ea31e04d1c96284403d8437dd1e912639c363081c8917f0c7fe56575`;
- this report;
- `TASK_PROGRESS_ARCHIVE_BEFORE_B2_T0_FAILURE_HANDOFF_20260909.md`;
- bounded JSON artifacts under `%TEMP%` listed below.

Modified:

- `AgentRead/TASK_PROGRESS.md` for this failure handoff.

Semantic production source modifications: **0**. The harness was corrected twice before any learner mutation: first to keep pure-test package placeholders out of the worker, then to recognize the installed HARL critic cursor's cyclic `step == 0` after exactly `T` inserts. No file was changed after the mutation-bearing run03 failure.

## E. Fresh process/env/learner identity

The mutation-bearing run03 used:

| Field | Value |
|---|---|
| run identity | `b2-t0-repeated-smoke-26616` |
| PID | `26616` |
| fresh process | true |
| historical route reused | false |
| AppLauncher lifetimes in run03 | 1 |
| environment constructions in run03 | 1 |
| explicit environment resets in run03 | 1 |
| learner constructions in run03 | 1 |
| private route constructions in run03 | 1 |

Actor, actor optimizer, critic, critic optimizer, and ValueNorm objects were each constructed once in run03 and remained live through transaction 1 and the transaction-2 collection attempt. The required three-success continuity was not reached, so B2-T0 persistent-learner identity is **not accepted as a completed gate**.

Two earlier fresh processes were permitted startup/pre-mutation restarts:

| Run | PID | Environment | Rollout steps | Learner mutation | Result |
|---|---:|---:|---:|---|---|
| run01 | 19288 | 0 | 0 | false | package placeholder shadowed Gym entry point; fixed before retry |
| run02 | 17772 | 1 | 2 | false | harness expected non-cyclic critic cursor; fixed before retry |
| run03 | 26616 | 1 | 4 | true in tx1 | tx2 collection failure; poisoned; no retry |

The run01 and run02 objects/processes were closed and never combined with run03.

## F. Exact config

Runtime-resolved configuration was:

```text
environment: Isaac-Scan-Mobile-Manipulator-Direct-v0
profile: event_gated_local_mrta
device: cuda:0
T/E/M/N: 2/2/3/12
actor epochs/minibatches: 5/2
critic epochs/minibatches: 5/2
ValueNorm: enabled
fixed_order: false
```

The workload was not enlarged.

## G. Bounded smoke definition

The harness bounded execution to three intended transactions in one worker and one AppLauncher, with one persistent learner construction, transaction-local update IDs/plans/permits/receipts, no transaction 4, and a final read-only quiescence check only if all three succeeded. No convergence, reward, coverage, checkpoint, evaluation, or public-route criterion was present.

The required preflight passed:

1. approved interpreter identity;
2. 14 relevant files through `py_compile`;
3. `[B]`/`[B,1]` shape regression;
4. focused canonical ValueNorm regression, 53 assertions;
5. focused CG classifier regression, including CUDA and valid-zero witnesses;
6. R5I/R7 static authority guard.

Static executor cardinality was backward/actor-step/critic-step/live-ValueNorm `1/1/1/1`, R5 actor/critic sequence calls `1/1`, scheduler steps `0`, and nine public guard faults. The preflight static artifact was 387,222 bytes with SHA-256 `a466f4faa90e795ea57c91bb03e217d248a1a1ac588ba7b865b449842ad83c26`.

## H. Transaction-1 rollout

Transaction 1 collected two real Isaac steps. Its update ID was `b2-t0-repeated-smoke-26616-tx1`; terminal keys were `(0,0,1)` and `(1,0,1)`. The reason grid contained two `NONE` slots and two `TIME_LIMIT` slots. The timeout critic input matched the correlated pre-reset evidence exactly, and runtime ACK occurred before learner ledger consumption.

Selected transaction-scoped digests:

| Evidence | Digest |
|---|---|
| rollout | `9a013cad55006aa12a934e363736f56e0df716206e214f17c41c916a3461cd40` |
| actor observations | `f3e448a008f421e8a9438ae49681a716836be00bcc7b9382a328be3739c3f468` |
| available actions | `c078c316b443933cdf8ec2eddc338e63a02eb84e7df7be9d08ebe50e44765093` |
| proposals | `4136c7cfe4461db0db73ec7bad0508e24a0d63c1ab5f000fe3168dedf73863c4` |
| behavior logprobs | `30dfaeeff47bbf55bb9663b09654dd2fe9880906cfae267d1b9cf7cf72d2e983` |
| DVM | `457fb86bae1127d870419e5824b66d98cfae9b98cc6386f6e4fe4d6d65e99cae` |
| active masks | `9aec432bf5c3b6306234b6106a7263cb2064ac8269acb003e9a2a71fbf62dc57` |
| critic masks | `f7073700a0d31bd6ab880f47fd3f67365d773258f4516dc07693bddbf0a4d59d` |
| transition identity | `40b08db4106fbe7c5a26c8b4d672cb45d9e64720f71acb3ecfebdc1d42d59fcb` |

## I. Transaction-1 learner/S0-S10

Transaction 1 independently passed S0 through S10. Its actor order was `(1,2,0)`; actor plan digest was `da6a6f3077d148e30c7daa72816910be596f1c903a3bfb3dbd05c945a3e54e76`; critic plan digest was `649e44f2c3f0f5d4189578980dea16b02674cd5cebe91fce868956cd93453ecd`.

```text
actor backward / optimizer.step: 15 / 15
critic backward / optimizer.step: 10 / 10
ValueNorm.update: 10
VALID_NONZERO_UPDATE: 5
VALID_ZERO_EFFECTIVE_UPDATE: 5
factor segments: 3
critic rollover / ledger reset / actor rollovers: 1 / 1 / 3
S7 / S8 / S9 / S10: 1 / 1 / 1 / 1
```

The learner state digest was unchanged by collection (`56302c...f5f3` before and after collection) and became `3f8b80...8af8` after the update. Transaction evidence digest was `3eaf4df865167a0910251017111fd72ba733cd10135ae9aee97d15a42699d8a3`.

## J. Bridge tx1->tx2

The bridge did **not** produce the required durable PASS receipt. Before transaction-2 collection, in-process guards necessarily passed tx1-post equals tx2-pre persistent-state comparison, route unpoisoned, S10 ledger empty, clean gradients, zero cursors, and rollout mode; otherwise execution would have stopped before collection. These are control-flow observations, not a durable bridge artifact and therefore not sufficient for acceptance.

During transaction-2 collection, actor recorder counts moved from `(1,1,1)` at the start to `(2,2,3)` after the second step; the first step had already established `(2,2,2)`, so actor 2 received one additional policy call on the second step. The harness stopped at:

`STOP — B2-T0 TX2_FORCED_CONTINUATION_RESAMPLED: ((1, 1, 1), (2, 2, 3))`

No tx1-to-tx2 bridge JSON was emitted. Bridge 1 is **FAILED / NOT ESTABLISHED**, not PASS.

## K. Transaction-2 rollout

Four real rollout steps were counted across run03, so two transaction-2 collection steps executed. The observed additional actor-2 call was not silently accepted. No transaction-2 rollout digest or pre-mutation artifact was emitted because the harness stopped before that serialization point.

This report does not adjudicate whether the additional actor-2 decision was a legitimate reopened lifecycle decision or a semantic defect. Resolving that question would require a new, separately authorized design/static audit. It cannot be diagnosed by retrying the poisoned run.

## L. Transaction-2 learner/S0-S10

Transaction 2 never entered the R5 mutation adapter and performed no transaction-2 backward, optimizer step, or ValueNorm update. It has no completed S0-S10 transaction receipt. Because transaction 1 had already mutated the learner, the whole process is nevertheless `partial_update=true` under the phase-wide poison rule.

The planned in-memory update ID would have been `b2-t0-repeated-smoke-26616-tx2`, but no immutable transaction-2 pre-mutation artifact was emitted, so it is not counted as a completed/accepted update identity.

## M. Bridge tx2->tx3

Not reached. Bridge 2 is **NOT ESTABLISHED**.

## N. Transaction-3 rollout

Not started. No transaction-3 environment step or rollout artifact exists.

## O. Transaction-3 learner/S0-S10

Not started. Transaction 3 performed zero learner operations.

## P. Actor-order evidence per transaction

| Transaction | Actor order | Status |
|---|---|---|
| 1 | `(1,2,0)` | independently frozen once; complete |
| 2 | none | stopped before plan/order freeze |
| 3 | none | not started |

## Q. Factor evidence per transaction

Transaction 1 began with factor digest `f6bb1294da2f78cd935b01c7656280df5eaa0439e9d97bc03775825a41a508e4`, completed three ordered factor segments, and ended with `fb3e86b471d87c9965fb3281fba4f0bab16ed768d7eb8ccea57e46db6e2236ac`. Four durable factor-progress events were written. Transactions 2 and 3 never initialized an update factor.

## R. Critic-class evidence per transaction

Transaction 1 classified all ten critic minibatches exactly: five `VALID_NONZERO_UPDATE` and five `VALID_ZERO_EFFECTIVE_UPDATE`. Backward, optimizer step, and ValueNorm update were each ten. Forty-one durable critic-progress events captured the sequence. Transactions 2 and 3 had no critic minibatches.

The qualified CG classifier was unchanged. No shortcut was added for valid-zero updates.

## S. ValueNorm continuity

Transaction 1 canonical ValueNorm digest advanced from `ade87b50d42654800d34babd0b0942a9901b1e91a7e6c12728a3d64b3bc6b0d9` to `51bf53a98eb07d95243b6b322181ff3f5cbec5c031d335ac6ae750d8d14c2a59` across ten finite updates. The in-process tx1-post/tx2-pre guard passed before collection, but no durable bridge receipt was reached. Therefore cross-transaction ValueNorm continuity is **observed by control flow but not accepted/established**.

## T. Actor optimizer continuity

All actor Adam counters advanced from 0 to 5 in transaction 1. The in-process tx1-post/tx2-pre equality guard passed, and collection had not yet invoked a learner update when the stop occurred. No durable bridge receipt exists; B2-T0 actor optimizer continuity remains **not established**.

## U. Critic optimizer continuity

All critic Adam parameter counters advanced from 0 to 10 in transaction 1. The same evidence boundary applies: an in-process boundary guard passed, but no durable bridge artifact exists and no transaction-2 update occurred. Critic optimizer continuity across completed updates remains **not established**.

## V. Parameter continuity

Transaction-1 collection did not mutate actor or critic parameters, and its update did. Stable object IDs and exact state fingerprints were checked in-process before transaction-2 collection. No accepted tx1-post to tx2-pre/tx2-post evidence pair was completed. Parameter continuity for the required three transactions remains **not established**.

## W. Buffer/cursor continuity

Transaction 1 passed ordered critic `after_update`, ledger reset, and three actor rollovers; its S10 receipt records critic cyclic cursor zero, empty event-slot ledger, actor cursors zero, and current slot-zero state. Transaction-2 collection then advanced from that slot-zero boundary for two steps. The failure occurred before a transaction-2 rollover or durable bridge receipt. Required three-cycle buffer/cursor continuity is **not established**.

## X. Terminal-ledger continuity

Transaction 1 retained two terminal keys through runtime ACK and consumed/reset them once at S9; its S10 ledger was empty. Transaction-2 start guards confirmed an empty learner ledger. The failure occurred before transaction-2 terminal-history serialization, so freshness/reset behavior for transaction 2 and 3 is **not established**.

## Y. Permit/gradient continuity

Transaction 1 consumed all permits and reached S10 with gradients clear. Transaction-2 stopped before plans or permits were created and before any new backward. No stale permit or gradient was observed before the stop, but the required two durable bridge proofs were not completed. Overall continuity is **not established**.

## Z. Event-return compute-once reset

Transaction 1 computed reviewed event returns exactly once; stock HARL `compute_returns` remained zero. Its S10 rollover reset the compute-once state. Transaction 2 stopped before return computation. Total reviewed event-return computations: 1, not the required 3.

## AA. S7/S8/S9/S10 counts

| Stage/cycle | Observed | Required for PASS |
|---|---:|---:|
| S0 completed learner entries | 1 | 3 |
| S7 PASS | 1 | 3 |
| S8 PASS | 1 | 3 |
| S9 PASS | 1 | 3 |
| S10 PASS | 1 | 3 |
| critic rollovers | 1 | 3 |
| ledger-reset invocations | 1 | 3 |
| actor rollovers | 3 | 9 |
| S10-to-next-S0 bridge receipts | 0 | 2 |

## AB. Numerical health

All completed transaction-1 actor/critic parameters, optimizer states, ValueNorm fields, losses, gradients, ratios, factors, and event returns passed finite checks. Actor losses ranged from `-0.7624865770` to `-0.0256489199`; actor gradient norms from `0.0061561252` to `11.1880459024`; critic losses from `0.5743330717` to `2.7138209343`; critic gradient norms from exact zero to `61.3387802355`. No NaN/Inf caused the stop.

No numerical-health claim is made for a transaction-2 update because none occurred.

## AC. Diagnostic-only reward/coverage observations

Transaction-1 team reward sum was `-0.07066666893661022`, diagnostic only. No reward trend, threshold, policy-quality, coverage, or convergence criterion was applied. Coverage was not emitted into the bounded artifact and is not inferred.

## AD. Cross-transaction continuity table

| Evidence | Tx1 post -> Tx2 pre | Tx2 post -> Tx3 pre |
|---|---|---|
| actor params | in-process pre-collection guard passed; no durable bridge; **not established** | not reached |
| actor Adam | in-process pre-collection guard passed; no durable bridge; **not established** | not reached |
| critic params | in-process pre-collection guard passed; no durable bridge; **not established** | not reached |
| critic Adam | in-process pre-collection guard passed; no durable bridge; **not established** | not reached |
| ValueNorm | in-process pre-collection guard passed; no durable bridge; **not established** | not reached |
| ledger at S10 | empty after tx1; tx2-start guard passed | not reached |
| permits at S10 | zero after tx1 | not reached |
| gradients at S10 | clear after tx1 | not reached |
| actor cursors | reset after tx1; tx2 collection advanced | not reached |
| critic buffer | rolled after tx1; tx2 collection advanced | not reached |
| next rollout | two steps collected; failed on extra actor-2 call before durable receipt | not reached |
| update_id | planned change only; tx2 artifact absent | not reached |

This table intentionally does not convert control-flow implications into the two explicit PASS receipts required by B2-T0.

## AE. Static/private/public guards

All six bounded preflight items passed. Qualified semantic hashes remained exact. The private dormant route was used; a public wrapper call was rejected before environment mutation and the descriptor remained `private_test_only_dormant` / `blocked_pending_B2_V1_V2_R`. Public activation count was zero.

## AF. Exact execution counts

For mutation-bearing run03:

```text
fresh process workers: 1
AppLauncher lifetimes: 1
environment constructions: 1
explicit environment resets: 1
distinct learner constructions: 1
successful full transactions: 1
distinct completed update IDs: 1
S0 / S7 / S8 / S9 / S10: 1 / 1 / 1 / 1 / 1
S10->next-S0 bridge receipts: 0
real rollout steps: 4
terminal/autoreset events serialized before stop: 2
event-return computations: 1
stock compute_returns: 0
actor backward / optimizer.step: 15 / 15
critic backward / optimizer.step: 10 / 10
VALID_NONZERO_UPDATE: 5
VALID_ZERO_EFFECTIVE_UPDATE: 5
ValueNorm.update: 10
critic rollovers: 1
ledger-reset invocations: 1
actor rollovers: 3
transaction 3 started: 0
transaction 4 started: 0
checkpoint weight I/O: 0
public activation: 0
evaluation/playback: 0
long-training transactions: 0
```

Across the entire authorized task there were three fresh worker/AppLauncher starts: two pre-mutation startup/harness failures permitted by section 29, then one mutation-bearing run. They are not combined to claim transaction success; only run03's one successful transaction is counted.

Durable run03 artifacts:

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `run03_final_result.json` | 1,405 | `d1b1cc44b82b352d96d38a37ca1caef1092d479ec960a732a18ecba9b2bcc25f` |
| `run03_process_config_authority.json` | 198,320 | `28602630b1ceeaea5cda45dfa85a517adbabd8e44a63e2fc4ee94545ef342c33` |
| `run03_supervisor.json` | 414,525 | `6c1e564b0c4d860fbd9fdf600528ba4590abe0db33c6cf609ea318ab3786bcbf` |
| `run03_tx1_actor_factor_progress.json` | 6,039 | `8d2a03edf3f9fba0006eef8d286593c2fc4fe1ff0d432f065f6b365b1f3e4a69` |
| `run03_tx1_critic_progress.json` | 780,711 | `404a31bfc066b11a58497d0daddaab934d0922558eea839f82f2e5c96750b83a` |
| `run03_tx1_pre_mutation.json` | 23,191 | `1be27cb22994b0895b215a28a245498caba1e84277d8233c4d84de1277067fe6` |
| `run03_tx1_s10.json` | 423,096 | `4f4bdb7bf997966f66529c5cb69db988132ce81a1b5c092b07b352b1e5564026` |

Raw supervisor hashes for the two permitted pre-mutation failures were run01 `adf09e671174807fd2ad20bb7024f08e09a4eee496928a1b58cf53f95c7b2d54` and run02 `6f7efca1438832a0ab4de4e17000120000d6c7e5a00a35f264f31bba57d5eda0`.

## AG. Checkpoint/public/training nonclaims

- Checkpoint weight I/O: 0; checkpoint readiness and exact resume remain `NOT ESTABLISHED`.
- Public learned-policy route remains `DORMANT / BLOCKED`.
- Evaluation/playback: 0.
- Long training: not authorized and not performed.
- B2-R6a/R6b: not authorized and not started.
- B2-T0 does not establish repeated-update continuity, long-run stability, performance, convergence, reward improvement, multi-seed robustness, or public readiness.
- The one completed tx1 does not satisfy or approximate the exact 3/3 gate.

## AH. Failure policy evidence

The run03 supervisor artifact emitted the generic machine classification `PHASE-B2-T0-STOP-TX2-BOUNDED-SMOKE-FAILURE-NOT-COMPLETE` and the precise error `TX2_FORCED_CONTINUATION_RESAMPLED`. This report narrows the required human-readable classification without modifying or overwriting the raw artifact.

```text
successful transactions before failure: 1
failing transaction: 2
mutation had begun: true (transaction 1)
transaction-2 learner mutation: false
partial_update: true
route_poisoned: true
last completed S-state: S10_QUIESCENT (transaction 1)
bridge failed: true
retry performed after mutation: false
```

The process was stopped and closed. No learner reconstruction, checkpoint restore, optimizer reset, continuation to transaction 3, or fresh-process retry occurred after mutation.

## AI. Final classification

`PHASE-B2-T0-STOP-TX2-FORCED-CONTINUATION-RESAMPLED-NOT-COMPLETE`

Recommended state:

```text
B2-R0 through B2-R7: GPT REVIEW PASS / CLOSED
B2-T0: FAILED / NOT COMPLETE / AWAITING GPT REVIEW
training-update readiness: REVIEW PASS / ESTABLISHED
repeated-update continuity: NOT ESTABLISHED
successful B2-T0 transactions: 1 / 3
B2-T0 S10: 1 / 3
cross-transaction bridges: 0 / 2 PASS
mutation-bearing run03: PARTIAL_UPDATE / POISONED / STOPPED / HISTORICAL
public route: DORMANT / BLOCKED
checkpoint readiness: NOT ESTABLISHED
long training: NOT AUTHORIZED
```

## AJ. GPT handoff

Independent GPT review should inspect the transaction-2 lifecycle row classification that caused actor 2 to sample on the second collection step. The review must decide whether the single-transaction fixture assumption (“second step is forced continuation for every actor”) was incorrectly generalized to a repeated rollout, or whether actor 2's reopened decision is a semantic violation.

No execution is authorized by this handoff. Do not retry B2-T0, start transaction 3 or 4, begin long training/B2-R6, load or save checkpoints, activate the public route, stage, commit, or push without new explicit authorization.

The byte-exact pre-rewrite progress archive is:

```text
path: 202609/20260909/TASK_PROGRESS_ARCHIVE_BEFORE_B2_T0_FAILURE_HANDOFF_20260909.md
bytes: 7764
sha256: 61f28e363727441541ae9da5806c87178397f741fffff53406e213852a5ed5eb
```
