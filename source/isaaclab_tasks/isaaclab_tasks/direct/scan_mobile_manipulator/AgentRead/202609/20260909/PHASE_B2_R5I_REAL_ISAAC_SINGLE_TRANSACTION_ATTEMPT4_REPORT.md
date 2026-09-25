# Phase B2-R5I-RE3 Fresh-Process Real-Isaac Single-Transaction Reentry — Attempt 4

Date: 2026-09-09

Classification:
`PHASE-B2-R5I-REAL-ISAAC-SINGLE-TRANSACTION-ATTEMPT4-COMPLETE-AWAITING-GPT-REVIEW`

## A. Repository authority

- Branch: `main`.
- HEAD, `origin/main`, and merge-base: `b71d85a32f51be6ada324f870813a56bb45dd396` (exactly equal).
- Pre-run working-tree porcelain: 420 lines; SHA-256 `433b4e97e69d4b200d0adb7577c36ede8b148f6a2d139f14107808320d3725bd`.
- Existing staged monthly-archive entries: 359.
- Staged-index SHA-256 before and after: `a40169043c3bfffd481a7ed1bddf3e52663d61379bedfd2610781457d11f947c`.
- No `git add`, commit, or push was performed.

## B. Attempts 1/2/3 historical separation

Attempts 1, 2, and 3 remain `PARTIAL_UPDATE / POISONED / STOPPED / HISTORICAL`.
Attempt 4 used PID 26684 and update ID `b2-r5i-re3-fresh-26684`; no process,
AppLauncher, environment, component, optimizer, ValueNorm, buffer, ledger,
permit, or update ID from a prior attempt was reused. Attempt 3 is not
retrospectively reclassified.

## C. CG qualification identity

The user supplied B2-R5I-CG as `GPT REVIEW PASS / CLOSED`. Its qualified
classifier permits only `VALID_NONZERO_UPDATE` and rigorously proved
`VALID_ZERO_EFFECTIVE_UPDATE`; disconnected/unused, nonfinite, ownership, and
foreign-gradient cases remain STOP. CG report SHA-256:
`6b50c7d42b585235b2941f55296b13ef3703523f17a142ea4db275bd74a4b9d3`.

## D. Qualified source hashes

Repo semantic sources were verified before AppLauncher:

| Source | SHA-256 |
|---|---|
| `assignment_event_training_evidence.py` | `1d9ae8c460fec99fea40fe0b0d954987d68857f19f47e71e2d7f57e6c8152ed9` |
| `assignment_event_training_gradient_probe.py` | `5501947f64ebe33c003b0e08b2fbacd6ccd826c3e5e78d115401ed11061dd985` |
| `assignment_event_training_actor_mutation.py` | `08eb3442ac52dc4f7fd69434486ee7ec77920c64e614d0a19944f4b163b078e3` |
| `assignment_event_training_critic_mutation.py` | `9719bcd059cfe9a670cc9715117ef00e965f708c82134a59c3a1f77296173dde` |
| `assignment_event_training_full_transaction.py` | `ec42cb68db274f42144489f4e8ef199311c557016c4859475057c1deed417c35` |
| `assignment_value_normalizer_checkpoint.py` | `baa339431fa2b2c1933c468091f47b818f3fea7e2ce1394ffdd18c94265d11c1` |

Attempt-4 logging-only adapter SHA-256:
`bff37075343795703b3ad4c7f7d27727278fd23e095e81d2de6b62a94821560e`.

Installed HARL sources were unchanged and exact:

| Source | SHA-256 |
|---|---|
| `algorithms/actors/happo.py` | `dd44fe7842160aa215b2d220726f6dd5e70b251c1a2e9c50cfeb6bd00535cf96` |
| `algorithms/critics/v_critic.py` | `ae66390702efb55099d151c11f28ae533f25ef6d62697949445abd2979708bf3` |
| `models/value_function_models/v_net.py` | `a3760b3fdf290c73bb13a752c0b0d39f69fd6fa207560272954b44a027f427c3` |
| `common/valuenorm.py` | `a35471b136567bde0b7fc7be34a7873efa617bdabf9a9074517ff0e3ef3fb8b0` |

## E. Files created/modified

Modified for pre-mutation observability/harness identity only:

- `assignment_event_training_real_isaac_adapter.py`
- `scripts/environments/test_assignment_phase_b2_r5i_real_isaac_single_transaction.py`
- `AgentRead/TASK_PROGRESS.md`

Created:

- this report;
- `TASK_PROGRESS_ARCHIVE_BEFORE_B2_R5I_RE3_ATTEMPT4_HANDOFF_20260909.md`.

No CG classifier, loss math, optimizer semantics, ValueNorm math, actor/factor,
lifecycle, returns, terminal, or R5 ordering source was modified for attempt 4.

## F. Fresh process/AppLauncher/env

- Formal supervisor attempts: 1; formal workers: 1; retries: 0.
- Fresh worker PID: 26684; `fresh_process=true`; `historical_route_reused=false`.
- AppLauncher lifetimes: 1; environment constructions: 1; resets: 1.
- Headless `cuda:0`; environment `Isaac-Scan-Mobile-Manipulator-Direct-v0`.

## G. Exact config

Fresh runtime resolved `T=2`, `E=2`, `M=3`, `N=12`; actor epochs/minibatches
`5/2`; critic epochs/minibatches `5/2`; ValueNorm enabled; `fixed_order=false`.
Resolved actor order was `(1,2,0)`. Config digest:
`caf5884da95c6c6ac32658782e44710ee308891490999bf9e7a19ff1f89dc914`.

## H. Runtime evidence

Exactly two physical rollout steps filled the real batch. Initial shapes were
actor obs `[2,3,421]`, critic obs `[2,3,418]`, and available actions
`[2,3,13]`. The three actors were called once per decision collection.

## I. Proposal/logprob identity

- Proposal digest: `4136c7cfe4461db0db73ec7bad0508e24a0d63c1ab5f000fe3168dedf73863c4`.
- Behavior-logprob digest: `c95db5620e515dbdcae42e30be921bb8f6ccaf7961dc09702700ea7d84cfcbe5`.
- Availability digest: `c078c316b443933cdf8ec2eddc338e63a02eb84e7df7be9d08ebe50e44765093`.
- Behavior logprob was not recomputed.

## J. Masks/DVM/active

DVM digest: `457fb86bae1127d870419e5824b66d98cfae9b98cc6386f6e4fe4d6d65e99cae`;
active-mask digest: `a78d27153a730922deaa63ddc5968729a02a3e22aa15ea0e2fbac59adbc80eef`.
Every actor had two DVM and active-and-DVM rows; each had two forced/off-DVM
rows. No shape, duplicate, range, or false-row injection fault occurred.

## K. P2/effective separation

Effective-assignment evidence digest:
`cc79daa97bff210281c2c067b770985ad82a292792cc60d7e0fa26cc360062d3`.
Proposal and effective authority remained explicitly separate.

## L. Terminal/autoreset

Two natural terminal/autoreset events occurred, classified
`REAL-ISAAC-FULL-TRANSACTION-WITH-TERMINAL-AUTORESET-EVIDENCE`. Historical
keys were `(0,0,1)` and `(1,0,1)`. Pre-reset critic digest
`c120c16dd20e4c7138e841ba72f2b0f863bef25c09f313864c50650bf8c0d23a`
and post-reset current digest
`df1bc7ba60579082acd37b2dc69ecdd54cbc5f99c8d9547beaf54db1fdf39a23`
were distinct. Runtime ACK completed while learner keys were retained until S9.

## M. Timeout sidecar

Timeout critic input matched exactly. Timeout evidence digest:
`68465b82e85069abd9f41e80099fa3166d5dba6b38a7f9906086ede985722edf`;
terminal correlation digest:
`ebc73e05efccfabe68340281ddfb3ff71c788712dda90f06887d195f41053c1e`.

## N. Pre-mutation artifact

Before the first actor optimizer step, S0-S4/S5-entry evidence was atomically
flushed with all mutation counters zero. Artifact:
`C:\Users\33506\AppData\Local\Temp\b2_r5i_re3_attempt4_20260909_pre_mutation.json`,
202320 bytes, SHA-256
`bd150f83f8abe3d69ca9ba4b615460e02891d61646f955e43eeeff54d57c6a42`.

## O. Event returns

Reviewed event-return computation executed exactly once; stock HARL
`compute_returns` executed zero times. Result was finite `[T,E,1]` and digest
`98840b7991923e26a5b027892008e55c7f3f104cfb32824994a4f8686db3c95e`.

## P. returns[:-1]

The training slice had the same digest as the event-return result and was a
non-alias. Final structural-slot digest
`af5570f5a1810b7af78caf4bc70a660f0df51e42baf91d4de5b2328de0e83dfc`
was distinct and excluded.

## Q. Plan/count derivation

Actor-plan digest:
`25f5748ce45916b6060f7c6f09281c99def17f6b72014ce1ef7b45ac747eed11`;
critic-plan digest:
`2dc74c7b4f6b378db84a04484060201d80522d97e4f3bedd8f9c4c3a93f9a3db`.
Expected actor backward/step counts were 5 each for actors 0/1/2. The critic
plan contained 10 minibatches, hence 10 backward, 10 step, and 10 ValueNorm
updates.

## R. S0-S4

Fresh authority, collection, masks, terminal transport, event returns,
immutable inputs, and plans completed without mutation. The durable S5 entry
receipt confirms actor/critic/ValueNorm mutation counters `0/0/0/0/0`.

## S. Actor sequence

Actor execution order `(1,2,0)` completed. Each actor performed five backward
and five optimizer steps, for totals `15/15`; the sequence completion receipt
was true.

## T. Factor receipts

Three segment receipts plus one sequence-complete receipt were atomically
flushed. Every segment passed factor post-audit, preserved prior accumulation,
and kept off-DVM entries exact one. Factor progression ended at digest
`fb3e86b471d87c9965fb3281fba4f0bab16ed768d7eb8ccea57e46db6e2236ac`.
Artifact: 6295 bytes, SHA-256
`9fb02b23fcd88046b47583b33a5766f3a82d0f56472b570cb956e35416dedfa5`.

## U. S6 critic overview

All ten planned physical minibatches completed. Each epoch processed rows
`(0,1)` then `(2,3)`. The natural classifications alternated nonzero and
zero-effective, producing exact totals 5 and 5.

## V. Per-minibatch loss decomposition

Every minibatch emitted a pre-backward source-faithful decomposition and a
post-step complete receipt. Nonzero losses by epoch were approximately
`0.732263, 2.713821, 1.581509, 0.574333, 0.613995`; proved plateau losses were
approximately `1.157928` in each epoch. Bounded per-row evidence includes raw
and normalized returns, old/current/clipped predictions, both branch errors
and losses, selected branch, local derivative, and zero reason.

## W. Graph diagnostics

Ten pre-backward graph receipts were durable. All graphs were connected and
finite. Rows `(0,1)` had finite nonzero `dLoss/dValues`; rows `(2,3)` had a
finite exact-zero derivative with `CLIPPED_VALUE_PLATEAU` proof.

## X. Gradient classification receipts

Ten post-backward receipts contain every critic-owned parameter's name,
`requires_grad`, presence, shape, dtype/device, finiteness, exact-zero/nonzero
status, norm, and digest. No required gradient was `None`, no nonfinite or
foreign gradient appeared, and all ten receipts have `receipt_complete=true`.

## Y. Valid-nonzero receipts

`VALID_NONZERO_UPDATE=5`, one at minibatch 0 of each epoch. All had finite
nonzero derivative and owned gradients, parameter mutation, optimizer-state
mutation, cleanup, and exactly one Adam step.

## Z. Valid-zero-effective receipts

`VALID_ZERO_EFFECTIVE_UPDATE=5`, one at minibatch 1 of each epoch. Every case
had connected finite graph, exact-zero derivative, complete present finite
exact-zero owned gradients, no foreign gradient, and source-faithful strict
clipped-plateau proof. No zero case was fabricated.

## AA. Adam state evidence

Every receipt contains per-parameter Adam state before/after. Step vectors
advanced exactly `0->1`, `1->2`, ..., `9->10`. All five zero-effective steps
were executed; retained moments caused both optimizer and critic parameter
fingerprints to mutate in every zero-effective receipt.

## AB. ValueNorm receipts

Ten canonical CUDA ValueNorm mutations were observed, one before each
backward. Each receipt binds the same raw batch to update and both normalize
calls, records canonical pre/post live state, and reports finite state.

## AC. Critic counts

Planned/completed minibatches `10/10`; valid classes `5+5=10`; backward
`10`; optimizer steps `10`; ValueNorm updates `10`. No count drift occurred.
Critic progress artifact: 782411 bytes, SHA-256
`5e8919831490bf471da7f384034c9d6c309d924499e3f04c3266cb8151288f40`.

## AD. S7

S7 post-audit passed: actor/factor counts exact, all critic rows/epochs and
valid classes exact, ValueNorm finite, mutation ownership valid, rollout and
plan evidence unchanged, gradients clean, permits empty, receipts complete,
and route unpoisoned.

## AE. S8

All actors and critic transitioned from training mode back to rollout/eval
mode exactly once. Gradients were clean and no later learner mutation occurred.

## AF. S9

Rollover order was exact: critic buffer `after_update`, terminal-ledger reset,
then actor storage rollovers 0, 1, 2. Critic rollover count was one and actor
rollover count was three; all final current slots were reused from the real
post-autoreset state.

## AG. Ledger reset

Before reset, the ledger held the two historical terminal keys. After the one
S9 reset it was empty; no terminal evidence was substituted.

## AH. Actor rollover

All three actor cursors reset and slot zero matched the current decision
bundle. The actor rollover receipts bind distinct pre/post storage digests.

## AI. S10

Exactly one S10 was entered. Route poison was false; gradients and permits were
zero; receipts complete; ledger empty; actor/critic cursors reset; models in
rollout mode; compute-once state reset. Transaction evidence digest:
`72aacdf64dfff8217f47715e7ba54061ec91c21b05ba5a3d6f710cd53f859c03`.
Final receipt: 402791 bytes, SHA-256
`f3d33d549d2037e791c91772542bf7b6fdcbe62ba2277c4e323a9e0fa3d4eb3a`.

## AJ. Next-rollout-ready

The single post-S10 read-only consistency check passed: current runtime state
exists, slot zero matches, ledger and cursors are reset, route is unpoisoned,
and models are in rollout mode. `next_rollout_ready=true`. No second learner
transaction was started.

## AK. Static/public guards

Pre- and post-run guards passed identically: unique backward, actor-step,
critic-step, and ValueNorm executors `1/1/1/1`; R5 actor/critic calls `1/1`;
reviewed private edges 18; public references 0. The public learned-policy route
remained `DORMANT / BLOCKED`.

## AL. Exact execution counts

```text
attempt: 4
fresh workers: 1
AppLauncher lifetimes: 1
environment construction/reset: 1/1
rollout steps: 2
terminal/autoreset events: 2
event returns: 1
actor backward/step: (5,5,5) / (5,5,5)
factor audits: 3
critic minibatches planned/completed: 10/10
VALID_NONZERO_UPDATE: 5
VALID_ZERO_EFFECTIVE_UPDATE: 5
critic backward/optimizer.step: 10/10
ValueNorm.update/canonical mutations: 10/10
critic rollover: 1
terminal ledger reset: 1
actor rollovers: 3
S10: 1
successful real full learner transactions: 1
checkpoint weight I/O: 0
training/evaluation/playback: 0/0/0
public activation: 0
```

## AM. Diagnostic/setup attempts

There was one formal attempt, one fresh worker, and zero retries. Preflight
passed interpreter identity, relevant `py_compile`, [B]/[B,1] pure shape,
ValueNorm CPU/CUDA fingerprint, CG CPU/CUDA classifier, R5I static-only, and
executor cardinality. The full controlled R4/R5 matrices were not rerun.
Supervisor artifact: 660346 bytes, SHA-256
`e14efe932d70b470ea0096f9ae3467849baa9bddb1a9f161292fdbbab4f8ebdc`.

## AN. Retained nonclaims

- This is one bounded private real-Isaac integration transaction, not a
  training campaign, performance result, convergence claim, or public-route
  readiness claim.
- Training-update readiness remains `NOT YET ESTABLISHED` pending independent
  review and later explicitly authorized gates.
- Checkpoint save/load, evaluation, playback, B2-R6a/R6b, and B2-R7 did not run.
- Attempts 1/2/3 remain poisoned historical evidence.
- No installed HARL file was modified; no stage, commit, or push occurred.

## AO. GPT handoff

Attempt 4 is `COMPLETE / AWAITING GPT REVIEW`. B2-R5I real-Isaac full-learner
integration has one successful transaction and one real S10, both awaiting
independent GPT review. Do not self-classify GPT REVIEW PASS. Do not begin
B2-R6/B2-R7, training, checkpoint work, evaluation/playback, or public-route
activation without new explicit authorization.
