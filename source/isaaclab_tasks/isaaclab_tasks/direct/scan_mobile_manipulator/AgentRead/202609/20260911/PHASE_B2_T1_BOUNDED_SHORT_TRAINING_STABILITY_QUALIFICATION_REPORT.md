# Phase B2-T1 Bounded Short Training Stability Qualification Report

Date: 2026-09-11

Classification:
`PHASE-B2-T1-BOUNDED-SHORT-TRAINING-STABILITY-QUALIFIED-AWAITING-GPT-REVIEW`

## A. repository authority

The read-only authority captured before AppLauncher, after the authorized new
T1 harness existed, was:

```text
branch: main
HEAD: b71d85a32f51be6ada324f870813a56bb45dd396
origin/main: b71d85a32f51be6ada324f870813a56bb45dd396
merge-base: b71d85a32f51be6ada324f870813a56bb45dd396
HEAD == origin/main == merge-base: true
working-tree porcelain lines: 434
working-tree porcelain SHA-256: d202bdc45c4597865f1f742126d0bc96b32ddfbea40a6e76a9f979f21fb8660f
staged paths: 359
staged-index SHA-256: a40169043c3bfffd481a7ed1bddf3e52663d61379bedfd2610781457d11f947c
monthly-migration paths: 359
monthly-migration path-set SHA-256: 0f2b8f7b52148e39196cbeb40fd9f4edd94fb762b6daf8be6279a116b80a39ab
```

No add, commit, push, reset, checkout, or clean operation occurred. The
pre-existing staged migration was preserved exactly.

## B. starting reviewed authority

The user-supplied authority is accepted exactly: B2-R0 through B2-R7,
B2-T0-LD, B2-T0-RE1, and B2-T0 are `GPT REVIEW PASS / CLOSED`.
Training-update readiness, the real single transaction, lifecycle decision
gating, repeated-update continuity, and persistent learner continuity are
`REVIEW PASS / ESTABLISHED`. B2-T0-RE1 contributed 3/3 transactions, 3/3
S10, and 2/2 bridges. Checkpoint continuation remains not established;
B2-R6a/R6b and long training were not authorized; the public route remains
`DORMANT / BLOCKED`.

## C. historical poisoned-route separation

B2-R5I attempts 1/2/3 and B2-T0 run03 remain poisoned, stopped, historical,
and permanently non-reusable. No process, AppLauncher, environment, learner,
optimizer, ValueNorm, buffer, ledger, permit, update ID, or receipt from those
routes was reused. Run03 tx2 actor-2's exact historical cause remains
`UNRESOLVED FROM EXISTING DURABLE ARTIFACTS`.

## D. source identities

All ten qualified production identities matched B2-T0-RE1 exactly:

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

LD helper remained `af607d6d...aa6052`; RE1 harness remained
`a77c5caa...fb95f`; the new T1 harness used by the formal run was
`8c08bffd...ab0932`. Installed HAPPO/VCritic/VNet/ValueNorm were respectively
`dd44fe78...5cf96`, `ae663907...08bf3`, `a3760b3f...427c3`, and
`a35471b1...f8b0`. The run's source/config digest was
`70bbd337bb3a4ba50477eb42fb97ac5bc99d47db9d3367c621f575defe284110`.
Pre- and post-run static source identity both passed.

## E. files created/modified

Created before formal mutation:

- `scripts/environments/test_assignment_phase_b2_t1_bounded_short_training_stability.py`;
- bounded `%TEMP%` evidence with prefix `b2_t1_short_training_20260911_formal01_`.

Created after the run:

- this report;
- `TASK_PROGRESS_ARCHIVE_BEFORE_B2_T1_HANDOFF_20260911.md`.

Modified after its byte-exact archive: `AgentRead/TASK_PROGRESS.md`.
Production semantic source modifications: **0**. Installed HARL modifications:
**0**. No source was changed after formal learner mutation began.

## F. preflight

PASS: approved interpreter `C:\isaacenvs\isaac45_harl\python.exe`; 13-file
`py_compile`; `[B]`/`[B,1]` geometry; ValueNorm 53 assertions; CG focused
classification; LD 13/13; static/private/public authority. One initial static
harness invocation found a test-side identity aggregation `KeyError` before
AppLauncher; the new harness alone was corrected, recompiled, and the complete
preflight then passed. One misspelled LD command path opened no script and was
rerun correctly. Neither event launched Isaac or mutated a learner.

Static cardinality was backward/actor-step/critic-step/live-ValueNorm
`1/1/1/1`, R5 coordinator `1`, scheduler `0`, reviewed private edges `18`,
and public references `0` (nine negative fixtures). Preflight and post-run
static artifacts are byte-identical at SHA-256 `a7dfb0e6...33f361`.

## G. formal fresh process

```text
run ID: b2-t1-short-training-25028
PID: 25028
formal mutation-bearing workers: 1
pre-mutation diagnostic workers: 0
AppLauncher lifetimes: 1
environment constructions/resets: 1/1
learner constructions: 1
transaction-local coordinator instances: 30
formal retries: 0
worker exit code: 0
```

## H. exact runtime config

Real environment `Isaac-Scan-Mobile-Manipulator-Direct-v0`, private profile
`event_gated_local_mrta`, device `cuda:0`; runtime-resolved `T/E/M/N =
2/2/3/12`; actor epochs/minibatches `5/2`; critic epochs/minibatches `5/2`;
ValueNorm enabled; `fixed_order=false`. Initial actor/critic/availability
shapes were `[2,3,421]`, `[2,3,418]`, and `[2,3,13]`.

## I. 30-update bounded-run definition

One persistent learner executed exactly 30 cycles of fresh two-step rollout,
LD validation, S0-S10 transaction, rollover, and next-rollout bridge. Tx30 S10
was followed by one final read-only quiescence audit and stop. Tx31 was not
started.

## J. update-ID inventory

Exactly 30 unique accepted IDs formed the closed interval
`b2-t1-short-training-25028-tx01` through
`b2-t1-short-training-25028-tx30`. No ID, plan, factor, permit, receipt, or
event-return token crossed transaction identity.

## K. lifecycle decision-gating summary

Sixty boundary receipts covered 360 `[E,M]` rows: 203 policy-required, 157
continuation, and zero forced-noop rows. Missing-call, duplicate-call, and
continuation-resample faults were all zero. Every receipt independently passed
the unchanged B2-T0-LD observer; physical step was never call authority.

## L. asynchronous lifecycle observations

Eighteen collection boundaries mixed policy and continuation rows. Examples
include calls `(0,0,1,0,0,0)` at tx02/collection04 and
`(0,0,0,1,0,0)` at tx03/collection06. Transaction totals varied naturally:
policy rows 6-8 and continuation rows 4-6. No synchronous-phase assumption was
used.

## M. actor-order sequence

The 30 frozen orders were:

```text
120 021 102 102 210 201 012 012 102 201
021 021 102 012 021 102 021 120 102 210
021 210 012 201 210 210 012 201 201 021
```

Permutation frequencies were `012:5`, `021:7`, `102:6`, `120:2`, `201:5`,
and `210:5`. Repeated orders were accepted as required.

## N. actor update counts

Plan-derived actor backward/step totals were actor0/actor1/actor2 =
`170/150/235`, aggregate `555/555`. Transaction-local actor counts varied
between five and ten per actor according to actual active-and-DVM rows. All
ownership/freeze and exact-plan checks passed.

## O. factor audit summary

Each transaction began with a fresh `[T,E,1]` all-one factor. Three actor
segments per transaction produced 90/90 factor audits. DVM ratios, off-DVM
exact-one behavior, prior-actor accumulation, and transaction-local finality
all passed; no factor crossed a bridge.

## P. critic classification summary

All 300 critic minibatches received exactly one reviewed class:
`VALID_NONZERO_UPDATE=279` and `VALID_ZERO_EFFECTIVE_UPDATE=21`. Every valid
zero retained connected finite graph, exact-zero derivative/owned gradients,
source-faithful zero proof, no foreign gradient, and one planned Adam step.
No class-ratio threshold was applied.

## Q. critic/ValueNorm counts

Per transaction, planned/completed/backward/step critic minibatches were
`10/10/10/10`; ValueNorm.update was 10. Aggregate critic
minibatch/backward/step and ValueNorm.update were `300/300/300/300`.

## R. actor optimizer continuity

Actor module and optimizer object IDs remained stable across every bridge.
Every next pre-state exactly equaled the preceding post-state. Final Adam step
counters were `(170,150,235)`, exactly matching the executed plans.

## S. critic optimizer continuity

The critic module and optimizer IDs were stable throughout. Critic Adam
advanced exactly `0 -> 300`, ten steps per transaction, without reset,
decrement, or unexplained jump.

## T. Adam counter trajectories

Rolling actor/critic maxima were: tx01 `(5,5,5)/10`; tx05
`(30,25,40)/50`; tx10 `(55,50,75)/100`; tx15 `(90,75,120)/150`; tx20
`(115,100,155)/200`; tx25 `(140,125,190)/250`; tx30
`(170,150,235)/300`. All 29 exact bridge equalities passed.

## U. ValueNorm trajectory

Canonical digests at tx01/05/10/15/20/25/30 were respectively
`51bf53a9...2a59`, `896b7973...e191`, `860157db...3b86`,
`f5aa7ec2...7dce`, `0a862a28...18e7`, `36992903...286b`, and
`313ff30a...4341`. The live object ID stayed fixed. Previous post equaled next
pre-collection and next post-collection on all bridges; all fields stayed
finite.

## V. collection-time immutability

All 30 pre/post collection snapshots matched exactly for actor parameters and
optimizers, critic parameters and optimizer, and canonical ValueNorm. Learner
mutation during collection was zero.

## W. 29-bridge continuity summary

All 29 bridges passed actor/critic/optimizer/ValueNorm fingerprints and object
identity, Adam continuity, unpoisoned route, rollout mode, clean gradients,
zero permits, empty ledger at the prior S10, reset cursors/compute-once state,
fresh next provenance, collection immutability, changed update ID, and next S0.

## X. terminal/autoreset summary

Natural timeout/autoreset produced 60 historical terminal events with 60
unique `(env, episode_generation, transition_generation)` keys. The complete
critic reason grids contained 60 `NONE` transition rows and 60 `TIME_LIMIT`
rows. Pre-reset timeout critic correlation passed every transaction; current
post-autoreset state remained separate.

## Y. terminal-ledger continuity

Runtime ACK never consumed learner evidence. Each transaction's terminal keys
persisted until S9, where the ledger reset exactly once after critic rollover;
every S10 and next pre-collection had an empty ledger. Ledger-reset invocations:
30.

## Z. event-return compute-once summary

Reviewed event returns executed exactly 30 times; stock HARL
`compute_returns` executed zero times. Each target was finite `[2,2,1]`, exact
to the non-alias `returns[:-1]` result, excluded the final structural slot,
and reset its compute-once state at S10.

## AA. S7/S8/S9/S10 summary

S7/S8/S9/S10 were `30/30/30/30 PASS`. Critic rollovers, ledger resets, and
actor rollovers were `30/30/90`.

## AB. numerical health

All actor/critic parameters and optimizer states, ValueNorm state, returns,
losses, gradients, ratios, and factors remained finite. Observed aggregate
ranges: actor loss `[-1.4877584, 1.1328919]`, actor gradient norm
`[0.0026655, 20.9520688]`, critic loss `[0.000004706, 2.7138209]`, and critic
gradient norm `[0, 61.3387802]`. Zero critic gradients occurred only under the
qualified valid-zero class.

## AC. training-signal diagnostics

Diagnostic-only time series were retained for team reward, actor/critic loss,
and actor/critic gradient norm. Per-agent reward, coverage, completed/new
viewpoints, duplicate scans, reach violations, task completions,
releases/reassignments, and policy entropy were not emitted and are reported
`NOT AVAILABLE`. No production logic was added to obtain them.

## AD. reward diagnostics

Per-transaction team reward sum ranged from `-0.0715446` to `-0.0573333`,
mean `-0.0658948`. This is diagnostic only: no convergence inference, reward
improvement claim, or performance threshold was applied.

## AE. coverage/task-progress diagnostics

Coverage and task-progress metrics were `NOT AVAILABLE`. No coverage,
completion, reassignment, duplicate-scan, or reach-violation claim is made.

## AF. entropy/loss/gradient diagnostics

Policy entropy was `NOT AVAILABLE`. Across 555 actor steps, actor loss mean was
`-0.2306032` and gradient norm mean `3.6522957`. Across 300 critic steps,
critic loss mean was `0.0575253` and gradient norm mean `1.9253270`.
Diagnostic only; no trend or policy-quality inference is made.

## AG. rolling health checkpoints

Exactly seven append-only health entries exist after tx01/05/10/15/20/25/30.
Each binds actor/critic/VN fingerprints, Adam summaries, cumulative lifecycle,
terminal, critic-class and reward totals, finiteness, poison state, and the last
S10. These are evidence summaries, not model checkpoints.

## AH. sentinel transaction evidence

Full pre-mutation, rollout-decision, actor-factor, critic-progress, and S10
receipts were retained for tx01, tx10, tx20, and tx30. No model weights were
dumped. Non-sentinel full details were compacted only after formal success; the
append-only ledgers and final aggregate retain the bounded audit trail.

## AI. append-only transaction ledger

The transaction, bridge, lifecycle, metric, and rolling JSONL ledgers contain
exactly `30/29/30/30/7` complete entries. Post-success artifact compaction
removed 188 redundant non-sentinel/individual-bridge files, leaving 30 bounded
files and zero individual bridge files. The artifact manifest SHA-256 is
`2df7ea7d...58a7e`; final result SHA-256 is `ee81d38f...2863d`.

## AJ. static/private/public guards

Pre- and post-run guards both passed: unique executors `1/1/1/1`, R5
coordinator `1`, R5 actor/critic sequence call sites `1/1`, scheduler `0`,
private edges `18`, public references `0`. No production or installed source
drifted during the run.

## AK. exact action counts

```text
formal mutation-bearing workers: 1
pre-mutation diagnostic workers: 0
AppLauncher / environment construction / reset: 1 / 1 / 1
learner constructions: 1
successful updates / unique IDs / rollout batches: 30 / 30 / 30
physical environment steps: 60
bridges: 29
lifecycle boundary / row receipts: 60 / 360
policy-required / continuation / noop: 203 / 157 / 0
actor policy-call faults: 0
event-return / stock compute_returns: 30 / 0
actor backward / optimizer.step / factor audits: 555 / 555 / 90
critic minibatches / backward / optimizer.step: 300 / 300 / 300
VALID_NONZERO / VALID_ZERO_EFFECTIVE: 279 / 21
ValueNorm.update: 300
S7 / S8 / S9 / S10: 30 / 30 / 30 / 30
critic rollovers / ledger resets / actor rollovers: 30 / 30 / 90
final read-only quiescence: 1
tx31 started: 0
checkpoint weight I/O / public activation / evaluation-playback: 0 / 0 / 0
production semantic modifications: 0
```

## AL. checkpoint/public/evaluation nonclaims

Checkpoint weight I/O, public activation, evaluation, playback, and video were
all zero. B2-T1 does not establish checkpoint continuation, exact resume,
public-route readiness, or policy performance.

## AM. remaining limitations

This is one bounded 30-update, one-seed, fixed runtime-resolution stability
qualification. It does not establish convergence, reward/coverage improvement,
policy quality, multi-seed robustness, long-run stability, arbitrary or
variable cardinality, zero-shot generalization, checkpoint continuation, exact
resume, evaluation readiness, or public-route readiness. Metrics reported
`NOT AVAILABLE` remain unavailable rather than inferred.

## AN. final quiescence

Exactly one final read-only audit after tx30 found: route unpoisoned; all model,
optimizer, and ValueNorm state finite; rollout modes active; gradients clear;
permits zero; terminal ledger empty; actor/critic cursors reset; event-return
compute-once reset; current runtime state valid. PASS. No tx31 followed.

## AO. final classification

`PHASE-B2-T1-BOUNDED-SHORT-TRAINING-STABILITY-QUALIFIED-AWAITING-GPT-REVIEW`

Recommended state:

```text
B2-R0 through B2-R7: GPT REVIEW PASS / CLOSED
B2-T0-LD: GPT REVIEW PASS / CLOSED
B2-T0: GPT REVIEW PASS / CLOSED
B2-T1: 30-UPDATE SHORT TRAINING STABILITY COMPLETE / AWAITING GPT REVIEW
successful B2-T1 updates: 30 / 30
S10: 30 / 30
cross-transaction bridges: 29 / 29 PASS
training-update readiness: REVIEW PASS / ESTABLISHED
repeated-update continuity: REVIEW PASS / ESTABLISHED
bounded short-training stability: COMPLETE / AWAITING GPT REVIEW
long training: NOT AUTHORIZED
checkpoint continuation: NOT ESTABLISHED
public route: DORMANT / BLOCKED
```

This report does not self-issue `GPT REVIEW PASS`.

## AP. GPT-review handoff

Please independently review qualified source/config identity, the dynamic
test-side T1 bound, all 30 transaction-ledger entries, 29 bridge entries,
lifecycle cardinality, Adam and ValueNorm trajectories, four sentinel receipts,
rolling health, numerical diagnostics, final quiescence, and the retained
historical/nonclaim boundaries. Do not start tx31, long training, B2-R6,
checkpoint work, evaluation/playback, public activation, staging, commit, or
push without new explicit authorization.
