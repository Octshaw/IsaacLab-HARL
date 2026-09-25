# Phase B2-T0-RE1 Bounded Repeated-Update Continuity Report

Date: 2026-09-10

Classification:
`PHASE-B2-T0-RE1-BOUNDED-REPEATED-UPDATE-CONTINUITY-COMPLETE-AWAITING-GPT-REVIEW`

## A. repository authority

The read-only authority captured before AppLauncher was:

```text
branch: main
HEAD: b71d85a32f51be6ada324f870813a56bb45dd396
origin/main: b71d85a32f51be6ada324f870813a56bb45dd396
merge-base: b71d85a32f51be6ada324f870813a56bb45dd396
HEAD == origin/main == merge-base: true
working-tree porcelain lines: 431
working-tree porcelain SHA-256: fd2b5eedb063b03d05cb145cfc6f85be1166e29dbd09d39daf04ab4a99df6ab4
staged paths: 359
staged-index SHA-256: a40169043c3bfffd481a7ed1bddf3e52663d61379bedfd2610781457d11f947c
monthly-migration paths: 359
monthly-migration path-set SHA-256: 0f2b8f7b52148e39196cbeb40fd9f4edd94fb762b6daf8be6279a116b80a39ab
```

The pre-existing staged migration was preserved. No add, commit, push, reset,
checkout, or clean operation occurred.

## B. starting reviewed authority

B2-R0 through B2-R7 and B2-T0-LD entered this retry as `GPT REVIEW PASS /
CLOSED`. Training-update readiness, the real single-transaction integration,
and lifecycle decision gating were `REVIEW PASS / ESTABLISHED`. The public
route remained `DORMANT / BLOCKED`; B2-R6a/R6b, checkpoint work, long training,
evaluation, and playback were not authorized.

## C. run03 historical separation

Run03 remains `PARTIAL_UPDATE / POISONED / STOPPED / HISTORICAL`. Its process,
AppLauncher, environment, learners, optimizers, ValueNorm, buffers, ledger,
permits, and update IDs were not reused. Its tx2 actor-2 exact historical cause
remains `UNRESOLVED FROM EXISTING DURABLE ARTIFACTS`. RE1 is a new process and
does not retrospectively reclassify run03.

## D. LD qualification identity

The qualified read-only observer remained exact at SHA-256
`af607d6d24c908f7c78e1af3ed3843bd2c87921309a6eb36514e37be95aa6052`.
The 13/13 controlled LD matrix passed again, including continuation, reopened
decision, asynchronous `(0,0,1)`, terminal/current-generation, nonmutation, and
the three precise negative guards. Physical step was never used as decision
authority.

## E. current source hashes

Production/reviewed sources were exact:

| Source | SHA-256 |
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

Installed HARL was exact: HAPPO `dd44fe784216...cf96`, VCritic
`ae66390702ef...bf3`, VNet `a3760b3fdf29...7c3`, and ValueNorm
`a35471b13656...8b0`. The final RE1 harness SHA-256 was
`a77c5caa8847980973aba718f19e7e1f8533cbb0c6756856272e8d29f5bfb95f`.
Source/config identity digest was
`94304667279b47db3cbfa3f97fafac854f1d4094bf1b71d1f004b8e291cc3877`.

## F. files created/modified

Modified by RE1 before the first mutation:

- `scripts/environments/test_assignment_phase_b2_t0_bounded_repeated_update_training_smoke.py` — test-only RE1 identity, row logging, fresh-provenance, two-stage bridge serialization, and artifact binding.

Created:

- this report;
- `TASK_PROGRESS_ARCHIVE_BEFORE_B2_T0_RE1_HANDOFF_20260910.md`;
- the bounded JSON artifacts listed below.

`AgentRead/TASK_PROGRESS.md` was updated only after its byte-exact archive was
created. Production semantic source modifications by RE1: **0**. No harness or
production file was changed after learner mutation began.

## G. preflight

All required pre-AppLauncher checks passed:

1. approved interpreter: `C:\isaacenvs\isaac45_harl\python.exe`;
2. 13 relevant files through `py_compile`;
3. `[B]`/`[B,1]` row geometry PASS;
4. canonical ValueNorm PASS, 53 assertions;
5. CG classifier PASS, including CUDA and valid-zero witnesses;
6. B2-T0-LD matrix 13/13 PASS;
7. static/private/public authority PASS.

One earlier three-file `py_compile` was an implementation-time syntax check,
not a diagnostic worker. The static artifact is
`%TEMP%\b2_t0_re1_static_20260910.json`, 389,368 bytes, SHA-256
`dd1682df1994b8298668dc63bbeb5d202a09061bf72da1a88016031bc7f740ec`.

## H. fresh process/environment/learner identity

```text
run ID: b2-t0-re1-repeated-smoke-16980
PID: 16980
fresh process: true
historical route reused: false
formal mutation-bearing workers: 1
AppLauncher lifetimes: 1
environment constructions/resets: 1/1
private route constructions: 1
learner constructions: 1
persistent learner object identities stable: true
transaction-local coordinator instances: 3
retry count: 0
worker exit code: 0
```

## I. exact runtime config

Environment `Isaac-Scan-Mobile-Manipulator-Direct-v0`, profile
`event_gated_local_mrta`, device `cuda:0`; runtime-resolved `T/E/M/N =
2/2/3/12`; actor epochs/minibatches `5/2`; critic epochs/minibatches `5/2`;
ValueNorm enabled; `fixed_order=false`. Initial actor/critic/availability
shapes were `[2,3,421]`, `[2,3,418]`, and `[2,3,13]`.

## J. transaction architecture

The one persistent learner executed exactly:

```text
tx1 fresh rollout -> S0-S10
  -> bridge1 pre -> tx2 fresh rollout -> LD gate -> bridge1 post -> tx2 S0-S10
  -> bridge2 pre -> tx3 fresh rollout -> LD gate -> bridge2 post -> tx3 S0-S10
  -> final read-only quiescence -> STOP
```

Update IDs were distinct: `<run>-tx1`, `<run>-tx2`, and `<run>-tx3`. No tx4
was started.

## K. tx1 rollout lifecycle decision evidence

Collection 1 had six `NEEDS_ASSIGNMENT/POLICY_DECISION_ROW` rows and calls
`(1,1,1,1,1,1)`. Collection 2 had six
`EXECUTING/FORCED_CONTINUATION_ROW` rows and calls `(0,0,0,0,0,0)`.
Rollout/provenance digests were `56f787061fba...1fef` and
`0180a7eee041...8828`; terminal keys were `(0,0,1)` and `(1,0,1)`.

## L. tx1 S0-S10

Actor order `(1,2,0)`; actor backward/step `(5,5,5)/(5,5,5)`; critic
backward/step `10/10`; ValueNorm updates `10`; critic classes `5 nonzero + 5
valid-zero`; factor segments `3`; S7/S8/S9/S10 all PASS.

## M. bridge-1 pre-collection receipt

Receipt SHA-256 `0892f2d5f148c0ea2d5cd183be256e4e03deec90aa47d35a5ddc33388ed28728`
was durable after global physical step 2 and before step 3. Tx1 post equaled
tx2 pre; object IDs, parameters, optimizers, ValueNorm and Adam state persisted;
route was unpoisoned; models were in rollout mode; gradients/permits/ledger
were clear; cursors/critic/event-return state were reset; next collection was
authorized.

## N. tx2 rollout lifecycle decision evidence

Collection 3, the post-autoreset current generation, had six policy rows and
calls `(1,1,1,1,1,1)`. Collection 4 was asynchronous: env0 robot2 reopened a
decision while the other five rows continued, giving calls
`(0,0,1,0,0,0)`. This is the qualified lifecycle-derived behavior that the old
run03 harness incorrectly rejected by physical-step position.

## O. bridge-1 post-collection receipt

Receipt SHA-256 `3471c2b947bca4d0c67c798dd229c28d6df84275d61d0a039d37bca9c5f86bd6`
was durable after tx2 collection validation and before tx2 mutation. It binds
the pre receipt, tx2 rollout-decision receipt `c394f46b4d5...b3500`, new actor,
critic, proposal, logprob, DVM, active-mask, lifecycle, terminal, and call
evidence. Tx2 collection mutated no learner state.

## P. tx2 S0-S10

Actor order `(0,2,1)`; actor backward/step `(5,5,10)/(5,5,10)`; critic
backward/step `10/10`; ValueNorm updates `10`; critic classes `6 nonzero + 4
valid-zero`; factor segments `3`; S7/S8/S9/S10 all PASS.

## Q. bridge-2 pre-collection receipt

Receipt SHA-256 `65bd37d713c5697d45cd456092cbffec2e61fbc49c62350939e1a75a05824a3b`
was durable after global physical step 4 and before step 5. All required
tx2-post to tx3-pre persistent and quiescent fields passed.

## R. tx3 rollout lifecycle decision evidence

Collection 5, the next post-autoreset current generation, had six policy rows
and calls `(1,1,1,1,1,1)`. Collection 6 was asynchronous: env1 robot0 reopened
a decision while five rows continued, giving `(0,0,0,1,0,0)`. All call,
proposal, logprob, DVM, availability, ownership, and generation bindings passed.

## S. bridge-2 post-collection receipt

Receipt SHA-256 `146977dd20708f30c8c179dbe81c272aaca525cb64a880658558fdefbe9a2078`
was durable after tx3 collection and before tx3 mutation. It binds pre receipt,
tx3 rollout-decision receipt `f72ecb92bd4c...dc89f`, all fresh rollout and
lifecycle evidence, and exact zero collection-time learner mutation.

## T. tx3 S0-S10

Actor order `(1,0,2)`; actor backward/step `(10,5,5)/(10,5,5)`; critic
backward/step `10/10`; ValueNorm updates `10`; critic classes `6 nonzero + 4
valid-zero`; factor segments `3`; S7/S8/S9/S10 all PASS.

## U. lifecycle call-cardinality evidence

Six boundary receipts contained 36 rows: 20 policy-required and 16
continuation, with zero forced-noop rows. Every required row had exactly one
I3a participation/proposal/logprob; every continuation had zero. Missing,
duplicate, and continuation-resample faults were `0/0/0`. Cumulative actor
counters agreed and remained supplemental.

## V. asynchronous robot decision evidence

Tx2 collection 4 proved `(0,0,1,0,0,0)` and tx3 collection 6 proved
`(0,0,0,1,0,0)`. In each, the sole `1` was a current
`NEEDS_ASSIGNMENT/POLICY_DECISION_ROW`; all `0` rows were current
`EXECUTING/FORCED_CONTINUATION_ROW`. This is real repeated-run asynchronous
evidence, not a synchronized or physical-step heuristic.

## W. actor sequences

Orders were `(1,2,0)`, `(0,2,1)`, `(1,0,2)`. Plan-derived actor
backward/optimizer totals were `15/15`, `20/20`, `20/20`, aggregate `55/55`.
Only the current actor mutated in each segment; foreign actors, critic, critic
optimizer, and ValueNorm remained frozen.

## X. factor sequences

Each transaction initialized the same fresh full-factor identity
`f6bb1294da2f...08e4`, then completed exactly three transaction-local segments.
Final factor digests were `fb3e86b471d8...36ac`, `935ed28a8ef8...8155`, and
`be840a8d6572...d936`. Off-DVM exact-one and prior-actor accumulation audits
passed; no final factor crossed a transaction boundary.

## Y. critic classifications

Per transaction valid classes were `5+5`, `6+4`, and `6+4`; aggregate
`VALID_NONZERO_UPDATE=17`, `VALID_ZERO_EFFECTIVE_UPDATE=13`. All 30 planned
minibatches had connected finite graphs and exactly one valid class. Critic
backward/step was `10/10` per transaction and `30/30` aggregate.

## Z. ValueNorm per transaction

Each transaction performed exactly 10 canonical live updates. Digests advanced:
`ade87b...b0d9 -> 51bf53...2a59 -> 4219e7...26aa -> a4e3b2...a20a`.
ValueNorm was unchanged during every rollout collection.

## AA. actor parameter continuity

Tx1 post exactly equaled tx2 pre, and tx2 post exactly equaled tx3 pre. The
three actor module object IDs remained stable. PASS/PASS.

## AB. actor optimizer continuity

Actor optimizer digests and object IDs were continuous across both bridges.
No reset or replacement occurred. PASS/PASS.

## AC. critic parameter continuity

Critic parameter digest and critic module object ID were continuous across
both bridges. PASS/PASS.

## AD. critic optimizer continuity

Critic optimizer digest and optimizer object ID were continuous across both
bridges. PASS/PASS.

## AE. ValueNorm continuity

Each previous final ValueNorm digest equaled both the next pre-collection and
next post-collection digest. The live ValueNorm object ID was stable. PASS/PASS.

## AF. Adam counter continuity

Actor counters advanced by actual plans: `(0,0,0)->(5,5,5)`, then
`(5,5,5)->(10,10,15)`, then `(10,10,15)->(20,15,20)`. Critic counters advanced
`0->10->20->30`. Every next pre-state equaled the previous post-state; there
was no reset, decrement, or unexplained discontinuity.

## AG. buffer/cursor continuity

Each S9 executed critic `after_update`, ledger reset, then actor rollover
`0,1,2`. Totals were 3 critic rollovers and 9 actor rollovers. Every S10 had
critic cyclic cursor zero, event-slot ledger empty, and actor cursors zero;
each next collection then filled exactly T slots.

## AH. terminal-ledger continuity

Natural terminal keys were `(0,0,1)/(1,0,1)`, `(0,1,3)/(1,1,3)`, and
`(0,2,5)/(1,2,5)`: six unique events. Runtime ACK did not consume learner
evidence. Each ledger survived through S9, reset once, and was empty at S10 and
the next pre-collection receipt.

## AI. event-return compute-once continuity

Reviewed event returns executed exactly once per transaction, total 3. Stock
HARL `compute_returns` was 0. Every finite `[T,E,1]` result was the exact
non-alias `returns[:-1]` target, excluded the structural final slot, and its
compute-once state reset at S10.

## AJ. permit/gradient continuity

Every S7/S10 and both pre receipts had clean gradients and zero pending
backward, optimizer, and ValueNorm permits. Collections did not introduce
learner gradients or stale permits. PASS/PASS.

## AK. S7/S8/S9/S10 counts

```text
S7 PASS: 3
S8 PASS: 3
S9 PASS: 3
S10 PASS: 3
critic rollovers: 3
ledger-reset invocations: 3
actor rollovers: 9
```

## AL. durable bridge acceptance table

| Evidence | Tx1 -> Tx2 | Tx2 -> Tx3 |
|---|---|---|
| pre-collection receipt durable | PASS | PASS |
| same actor objects | PASS | PASS |
| actor params continuity | PASS | PASS |
| actor Adam continuity | PASS | PASS |
| same critic object | PASS | PASS |
| critic params continuity | PASS | PASS |
| critic Adam continuity | PASS | PASS |
| same ValueNorm object | PASS | PASS |
| ValueNorm continuity | PASS | PASS |
| ledger empty at S10 | PASS | PASS |
| permits zero | PASS | PASS |
| gradients clear | PASS | PASS |
| cursors reset | PASS | PASS |
| new rollout collected | PASS | PASS |
| lifecycle decision gate | PASS | PASS |
| collection learner mutation | 0 | 0 |
| post-collection receipt durable | PASS | PASS |
| new update_id | PASS | PASS |
| next S0 entered | PASS | PASS |

Both complete S10-to-next-S0 bridges passed. Aggregate bridge artifact SHA-256:
`d1349ac824b6b6603f8c2b3ee5b7a4198650894fb3695ad304c016622d1e6d12`.

## AM. numerical health

All actor/critic parameters, optimizer states, ValueNorm state, losses,
gradients, ratios, factors, and event returns were finite. Actor loss ranges by
transaction were `[-0.76249,-0.02565]`, `[-0.95763,0.77549]`, and
`[-1.40321,0.52005]`; critic loss ranges were `[0.57433,2.71382]`,
`[0.00354,0.14050]`, and `[0.00659,0.10572]`. Zero critic gradient norms only
occurred in valid-zero classifications. No NaN/Inf occurred.

## AN. diagnostic reward/coverage observations

Diagnostic team reward sums were `-0.0706666689`, `-0.0695555583`, and
`-0.0706666671`. Coverage was not emitted and is not inferred. No reward,
coverage, monotonic-loss, convergence, or policy-quality acceptance criterion
was used.

## AO. static/private/public guards

Backward/actor-step/critic-step/live-ValueNorm executors were `1/1/1/1`; R5
actor/critic sequence call sites were `1/1`; scheduler steps `0`; reviewed
private edges `18`; public activation references `0` with nine negative public
fixtures. The private dormant route alone was used.

## AP. exact execution counts

```text
formal mutation-bearing workers: 1
pre-mutation diagnostic workers: 0
AppLauncher lifetimes: 1
environment constructions/resets: 1/1
learner constructions in formal run: 1
successful full transactions: 3
distinct accepted update IDs: 3
real rollout batches / physical steps: 3 / 6
lifecycle boundary / row receipts: 6 / 36
policy-required / continuation / forced-noop rows: 20 / 16 / 0
missing / duplicate / continuation-resample faults: 0 / 0 / 0
event-return computations / stock compute_returns: 3 / 0
actor backward / optimizer.step / factor audits: 55 / 55 / 9
critic minibatches / backward / optimizer.step: 30 / 30 / 30
VALID_NONZERO / VALID_ZERO_EFFECTIVE: 17 / 13
ValueNorm.update: 30
S7 / S8 / S9 / S10: 3 / 3 / 3 / 3
bridge pre / bridge post / complete bridges: 2 / 2 / 2
critic rollovers / ledger resets / actor rollovers: 3 / 3 / 9
checkpoint weight I/O / public activation / evaluation-playback: 0 / 0 / 0
tx4 started: 0
```

Durable artifact inventory:

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `process_config_authority` | 206,284 | `23af853744f3ff6bbe07b0ace302631cdcc4734e2ca690acd21cc2e288a8fdf9` |
| `tx1_rollout_decision_evidence` | 30,001 | `e568b487590c08f0f13bf9991e922e84b2eace212aed4eb811def7afa38020e9` |
| `tx1_pre_mutation` | 25,179 | `c8149dd60469936ec2b239b50bc904487f55835248da823e544d017fa55266e3` |
| `tx1_actor_factor_progress` | 6,615 | `f70f5604b5741728ce8e81907535b51b6b98a8e7397af4e51e3b137d1a378e05` |
| `tx1_critic_progress` | 785,819 | `c1b4ace39ddfa37e0c7a6c944a40ade927b122cb14c7730b0cde1521c5b850bd` |
| `tx1_s10` | 441,836 | `40cab5224940ee21641b81db7934ca009ac0f4d9a679d8789c903865ac24fbd8` |
| `bridge1_pre_collection` | 13,334 | `0892f2d5f148c0ea2d5cd183be256e4e03deec90aa47d35a5ddc33388ed28728` |
| `bridge1_post_collection` | 29,854 | `3471c2b947bca4d0c67c798dd229c28d6df84275d61d0a039d37bca9c5f86bd6` |
| `tx2_rollout_decision_evidence` | 30,152 | `c394f46b4d5c076bcadef4da8b306564950773a4d53c6ffb81d3a9ac651b3500` |
| `tx2_pre_mutation` | 27,058 | `217d21f95a40f1a9df58d3d22028ecba4d834370f02acaeff9570ba51acb9248` |
| `tx2_actor_factor_progress` | 6,617 | `2f9bb0730da4cd74efe96d0eb5f41d05d33f0e2b0966b8066f1168524ad42354` |
| `tx2_critic_progress` | 790,965 | `cdcb3600dd19f2d73129cf9ce366f17eb39341315c4bad0b4d126a96932c2330` |
| `tx2_s10` | 464,361 | `da3c45cd78843833af8b0b1509affddb2d263090deeb79cb6cd492cb2a4a00d4` |
| `bridge2_pre_collection` | 13,406 | `65bd37d713c5697d45cd456092cbffec2e61fbc49c62350939e1a75a05824a3b` |
| `bridge2_post_collection` | 29,923 | `146977dd20708f30c8c179dbe81c272aaca525cb64a880658558fdefbe9a2078` |
| `tx3_rollout_decision_evidence` | 30,221 | `f72ecb92bd4c15ed1958ea9189dc77e320f97c07f5d5b11906f202b7c29dc89f` |
| `tx3_pre_mutation` | 27,132 | `69e100166afe77dd45780ba5650f18512629ca50f97ddae5cbebe6e97bf7f26b` |
| `tx3_actor_factor_progress` | 6,617 | `1cf98d454e0a6c2a8fef5cc0e2bb96f426668061771cafef17ffb2b6382e88dc` |
| `tx3_critic_progress` | 791,369 | `1e747af2ded9a0549039e7c8f91b11750eb760cf955acc84e7f978cc362575b9` |
| `tx3_s10` | 464,948 | `4579d2343c6910d10dde01b4508a5a9ef2d42f57e6c5dfc48c4b31a10498d1b1` |
| `final_result` | 1,773,121 | `462509e74bd948424766aa5c4f263a32b166b471b0753075d09fa824d8af2186` |
| `supervisor` | 2,338,710 | `dccc203767b0fead39abd1bdc160bf7f9d531d8a346fb5c715731fa5a814f812` |

Artifacts are under `%TEMP%` with prefix
`b2_t0_re1_20260910_formal01_`. They bind run/update/source/config identities
and contain no model-weight dump.

## AQ. failure/poison evidence if applicable

No formal-run failure occurred. `partial_update=false`, route remained
unpoisoned, all three transactions completed, retry count was zero, and no
post-mutation retry/reconstruction/reset path was used.

## AR. retained nonclaims

This is a bounded three-transaction private-route continuity/integration gate,
not long training, convergence, performance, reward improvement, multi-seed,
arbitrary-cardinality, checkpoint continuation/exact-resume, evaluation,
playback, or public-route readiness evidence. B2-R6 and checkpoint work remain
not authorized; public route remains `DORMANT / BLOCKED`.

## AS. final classification

`PHASE-B2-T0-RE1-BOUNDED-REPEATED-UPDATE-CONTINUITY-COMPLETE-AWAITING-GPT-REVIEW`

The bounded result is 3/3 successful transactions, 3/3 S10, and 2/2 durable
bridges. This report does not self-issue `GPT REVIEW PASS`.

## AT. GPT-review handoff

Please independently review the source/config identity, lifecycle row receipts,
the two asynchronous reopened decisions, pre/post bridge timing and digests,
collection-time learner immutability, persistent actor/critic/optimizer/
ValueNorm continuity, plan-derived count changes, S7-S10 receipts, and final
read-only quiescence. Do not start B2-R6, checkpoint work, long training,
evaluation/playback, public activation, staging, commit, or push without new
explicit authorization.
