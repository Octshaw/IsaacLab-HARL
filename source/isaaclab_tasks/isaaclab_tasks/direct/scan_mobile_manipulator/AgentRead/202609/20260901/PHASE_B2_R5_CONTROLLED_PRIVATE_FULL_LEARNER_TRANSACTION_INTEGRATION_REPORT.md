# Phase B2-R5 Controlled Private Full Learner Transaction Integration Report

Date: 2026-09-01

Classification:

`PHASE-B2-R5-CONTROLLED-PRIVATE-FULL-LEARNER-TRANSACTION-INTEGRATION-COMPLETE-AWAITING-GPT-REVIEW`

## A. Repository authority

- Branch/upstream: `main` / `origin/main`.
- HEAD, `origin/main`, merge-base:
  `b71d85a32f51be6ada324f870813a56bb45dd396`.
- Dirty tree: accumulated reviewed, uncommitted B2-R0 through B2-R4 private
  artifacts plus this authorized B2-R5 private slice.
- Staging, commit, push: 0.

## B. R0-R4 frozen authority

B2-R0 is GPT REVIEW PASS / FROZEN. B2-R1 through R4 are GPT REVIEW PASS /
CLOSED under the supplied R5 starting authority. R5 composes their reviewed
authority, plan, unique backward, actor-mutation, factor, critic-mutation and
live-ValueNorm seams without changing them. P2/lifecycle, proposal/logprob,
DVM, terminal precedence, pre-reset terminal evidence, compute-once returns,
`returns[:-1]`, and public/default-off contracts remain frozen.

## C. Files created/modified

Created:

- `assignment_event_training_full_transaction.py`
- `assignment_event_training_full_transaction_guards.py`
- `_assignment_phase_b2_r5_full_transaction_helpers.py`
- `test_assignment_phase_b2_r5_controlled_private_full_learner_transaction.py`
- this report
- `TASK_PROGRESS_ARCHIVE_BEFORE_B2_R5_HANDOFF_20260901.md`

Modified after the archive: `AgentRead/TASK_PROGRESS.md` only.

Final R5 Python SHA-256 values:

- coordinator: `ec42cb68db274f42144489f4e8ef199311c557016c4859475057c1deed417c35`
- guards: `de016f5ae022fe7bd41d0bc7bd37021f1c74afe35e192f402a3618a332173367`
- fixtures: `a37946ca80a540cc9930d8800d28bec4f352ccd442fd90cc3955ece370eb1969`
- harness: `f5ae8cc98a0856bca9342219144bd6bbec44a0e73e102a2850e88eabfbc9d417`

The pre-R5 progress archive is byte-exact: source/archive SHA-256
`3e58607b3b2d77b638d39a4a0ac57007edaa31040aa52be19d7cbc49961e88ef`,
3,418 bytes.

## D. Private dependency graph

The static graph records 18 explicit private edges. Its execution spine is:

```text
R5 coordinator
  -> R1 evidence / plans / control
  -> R2 unique backward executor
  -> R3 actor mutation + factor sequence
  -> R4 critic + live ValueNorm sequence
  -> reviewed event critic-buffer rollover / terminal-ledger reset
  -> controlled actor-storage rebuild
```

R5 calls the R3 and R4 sequence authorities once each and introduces no second
backward, actor step, critic step, or ValueNorm update executor.

## E. Real-vs-synthetic classification

REAL: installed HAPPO actors, actor Adam optimizers, VCritic/VNet, critic Adam,
live ValueNorm, real forward/backward/clip/step, real sequential factor
evaluation, actual repo-local `EventOnPolicyCriticBufferEPV2.after_update()`,
and actual `EventTerminalLearnerCollectorV2` ledger reset.

CONTROLLED/SYNTHETIC: CPU observations/actions/logprobs/masks, four-category
terminal reason grid and timeout sidecar, already-frozen event return tensor,
controlled actor storage objects and their real in-memory rebuild, injected
faults, and disposable transaction contexts. No Isaac or real environment
rollout was executed.

## F. Resolved configuration

`T=2`, `E=3`, `M=3`, `N=4`, `B=6`; actor epochs/minibatches `2/2`; critic
epochs/minibatches `1/1`; ValueNorm enabled; fixed order false. Actor order was
generated once from seed 7 as `(0,1,2)`. Authority digest:
`259807fdbf7eccc7e587c9663366843612f974b8c20ba96db31bede66fd64e80`.

## G. S0 rollout-complete evidence

All three actor cursors were at 2, both critic event slots were written, critic
cursor was 0 after canonical wrap, terminal ledger contained three keys,
current/final observation/mask/DVM/active slots were bound, and proposal/
behavior evidence was present. Rollout evidence digest:
`690df59c5a14fb289fcbeaf00ac5a50b883727e478e131785e454480e7eb2d2f`.

## H. S1 final-value/terminal evidence

The controlled evidence explicitly records final-value evaluation, historical
pre-reset terminal ownership, separate runtime ACK and learner consumption,
the four reason identities, exact-one selection and frozen precedence. The
reason-grid digest is
`d8d7e7fc664a14d393f336d38a1bb476268389d8bd6a1a9da4405e630e1294c4`;
timeout-sidecar digest is
`95dc535845dc16ed92627e1bab9ad88113a3efe9e8b93c7cd67a50b97fee16ec`.

## I. S2 frozen return evidence

The detached event result was exact-value-equal and non-aliasing with
`critic_buffer.returns[:-1]`. Target digest:
`48e4067ea7c9b2e6c86867219c26e2222257eea9f04411e276fbf860e19c1e4e`.
The structural `654.0` final slot digest
`22750e08ead7f283de7bd347c574fc4f4a38a3282fbb5f39879d57e5bc9ab474`
was excluded. Compute count was exactly one; stock `compute_returns()` was 0.

## J. S3 immutable update plan

The complete plan freezes update/config, actor order and counts, actor plan
digest `098a1510...d6db`, critic plan digest `0c03f3b8...bcc3`, lifecycle and
return digests, initial factor and component state, and exact S0-S10 history.
Full plan digest:
`e3ab0e7bd2842aa603fb4315bd57306affca2d5d6a56957a397f2b077aeea4fe`.

## K. S4 training-mode entry

All actors and critic began explicitly in rollout/eval mode. After S3, one
mode receipt changed all four modules to training mode with gradients absent.
No mutation occurred before this transition.

## L. S5 actor sequence

The reviewed R3 seam ran one actor order `(0,1,2)`. Actor0 and actor1 each
executed 4 backward/steps; forced-only actor2 executed 0/0 and remained exact
unchanged. Critic, critic optimizer and live ValueNorm remained unchanged
through S5; gradients were cleaned between minibatches/actors.

## M. Actor factor chain

The full `[2,3,1]` factor started at digest
`f46913286d895f62d646314f400fc3d7a543cf34eb4ae56df87f43dc4582a36b`
and ended at
`9b492e810a369041bbd4a8a568a5e52e163a24c637a7ffb378ea1aed4937e34d`.
Actor1 received actor0's completed factor; actor2 performed an exact skip.
Off-DVM ratios stayed exact one and prior accumulation was preserved.

## N. S6 critic/ValueNorm sequence

Only after S5 completed did the reviewed R4 seam execute one raw-target live
ValueNorm update, same-batch normalization, real critic forward/loss/backward,
critic-only clipping and one Adam step. All actors remained exact unchanged
during S6 and gradients were cleaned.

## O. Critic exact-row coverage

The immutable single critic minibatch was `(0,1,2,3,4,5)`, covering all six
physical rows exactly once. No DVM filtering and no final-slot sampling
occurred. Observed backward/step counts were `1/1`.

## P. ValueNorm receipts

One R4 receipt bound the raw target digest, epoch/minibatch, all six rows,
single-use permit, pre/post live-state fingerprints, running mean, running
mean-square, debiasing term, finite mutation and update order. The same raw
tensor object/content was normalized from the resulting state. Observed live
update count was 1 for the successful transaction.

## Q. S7 full post-update audit

Expected/observed actor, critic and ValueNorm counts matched. Actor0/actor1,
their optimizers, critic, critic optimizer and ValueNorm changed; actor2 did
not. Frozen inputs, terminal keys, target, plan and lifecycle evidence remained
unchanged. Parameters, optimizer states and ValueNorm were finite; gradients
were absent and all receipts were complete.

## R. S8 rollout-mode restoration

S8 occurred only after S7 PASS. One receipt restored every actor and critic to
rollout/eval mode, with no pending gradients. No mutation operation ran after
restoration.

## S. S9 rollover order

The exact observed operation order was:

```text
critic_buffer.after_update
terminal_ledger.reset
actor_storage[0].rollover
actor_storage[1].rollover
actor_storage[2].rollover
```

Critic final share-observation state became slot zero before any ledger reset.

## T. Terminal-ledger reset evidence

Terminal keys `(0,0,10)`, `(1,0,11)`, `(2,1,12)` remained present through
actor mutation, critic mutation and S7. The actual collector reset ran once,
only after critic rollover, and left zero keys. Runtime ACK never served as
learner consumption.

## U. Actor storage rollover

Each controlled storage performed a real in-memory rebuild after ledger reset.
Every cursor became 0; action/logprob transition slots were cleared; slot-zero
observation, availability, DVM and active-mask digests exactly matched their
frozen final current slots. Historical terminal observations, old proposals,
effective assignments and behavior receipts were not used as slot zero.

## V. S10 quiescence evidence

One immutable quiescence receipt proved zero gradients, permits, incomplete
receipts and terminal keys; unpoisoned state; rollout modes; reset cursors and
compute-once flag; and new rollout guards. Quiescence digest:
`7a38f1be0d56c44379566835774b4b503181f805561902e28c3aec288e4229fb`.
`checkpoint_boundary_eligible_by_state_machine=true`; checkpoint I/O remained 0.

## W. Complete transaction count ledger

Successful transaction only:

- actor backward/step by actor: `(4/4, 4/4, 0/0)`;
- critic backward/step/ValueNorm: `1/1/1`;
- training-mode entry / rollout restoration: `1/1`;
- critic rollover / ledger reset / actor rollovers: `1/1/3`;
- S10 entries: 1.

## X. Successful full transaction mutation summary

One authoritative successful transaction reached S10 in the passing harness.
Actors 0 and 1 and their Adam states mutated; actor2 stayed unchanged; critic,
critic Adam and live ValueNorm mutated. Full evidence digest:
`e7308815d33648d2116ec9b7ae3f9a7ef2fd337cc1c93f0fe19fbf7a80c0c9d3`.

## Y. Pre-mutation failure

One controlled S0 rejection produced actor/critic/ValueNorm `0/0/0`,
`partial_update=false`, no poison under the pre-mutation failure policy, no
mode entry, rollover, ledger reset or S10.

## Z. Actor post-step poison

One actor backward/step executed, then factor completion failed at S5. The
route became partial/poisoned; remaining actor steps, critic sequence,
restoration, rollover, ledger reset and S10 were all 0.

## AA. Post-ValueNorm poison

The actor sequence completed (`8` steps), one live ValueNorm update executed,
and S6 failed before critic backward/step. The route was partial/poisoned and
all later mutation/rollover/S10 actions were denied.

## AB. Post-critic-step poison

Actor sequence `8`, ValueNorm `1`, critic backward/step `1/1` executed before
the S6 fault. No later critic minibatch, restoration, rollover, ledger reset or
S10 occurred.

## AC. Post-update-audit poison

Actor `8`, critic `1`, and ValueNorm `1` completed, then a deliberate S7 audit
corruption failed. The transaction was partial/poisoned; S8, S9 and S10 were
not reached. This proves optimizer completion alone cannot authorize rollover.

## AD. Rollover-order faults

Pure fail-closed checks rejected ledger reset before critic rollover, actor
rollover before ledger reset, S9 before S8, S10 before complete rollover,
pending permit/terminal state at quiescence, and S10 continuation while
poisoned. None invoked a rollover mutation.

## AE. Fault-injection matrix

The authoritative harness passed 33 pure integrated fault assertions:
authority/plan 7, ordering 8, segment-mutation isolation 4, permit 5, factor 2,
terminal 3, poison continuation 4. It also passed 9 static/public faults, one
pre-mutation failed transaction and four distinct post-mutation poisoned
transactions.

## AF. Static/private/public guards

Passing cardinalities across R2-R5 executors:

- reviewed backward executor: 1 (R2);
- reviewed actor optimizer-step executor: 1 (R3);
- reviewed critic optimizer-step executor: 1 (R4);
- reviewed live ValueNorm executor: 1 (R4);
- R5 calls to R3 actor sequence / R4 critic sequence: `1/1`;
- scheduler steps and violations: 0.

All 18 private dependency edges matched the allowlist. Fifty-seven production
files contained no R5 reference. Three R1 pure suites, R2 source/production
guard, R3 static/public guard and R4 static guard all passed without replaying
their standalone mutation harnesses.

## AG. Exact execution counts

Authoritative final PASS harness, including required disposable failures:

```text
successful full transactions:              1
S10 entries:                                1
actor backward / optimizer.step:           33 / 33
per actor backward/step:                    17/17, 16/16, 0/0
critic backward / optimizer.step:            3 / 3
live ValueNorm.update:                       4
critic rollover:                             1
terminal-ledger reset:                       1
actor storage rollover:                      3
training-mode entries:                       5
rollout-mode restorations:                   1
pre-mutation failed transactions:            1
actor-post-step poisoned transactions:       1
post-ValueNorm poisoned transactions:        1
post-critic-step poisoned transactions:      1
post-update-audit poisoned transactions:     1
scheduler.step:                              0
Isaac/runtime rollouts:                      0
training campaigns:                          0
evaluation/playback:                         0
checkpoint weight I/O:                       0
public route activations:                    0
```

Two diagnostic harness runs each reached one disposable successful S10 before
a test-only fault assertion bug stopped the process. Task-wide totals are
therefore: successful full transactions/S10 `3/3`; actor backward/step `49/49`
with per-actor `25/25, 24/24, 0/0`; critic backward/step `5/5`; ValueNorm `6`;
training-mode/restoration `7/3`; critic rollover/ledger reset/actor rollovers
`3/3/9`; pre-mutation failures `3`. The four integrated poisoned cases ran only
in the final PASS. All objects were disposable in-memory CPU fixtures and no
state was saved.

## AH. Retained nonclaims

Controlled private full-learner integration is COMPLETE / AWAITING GPT REVIEW.
Real Isaac full-learner integration is NOT AUTHORIZED / NOT ESTABLISHED.
Training-update readiness remains NOT YET ESTABLISHED. This phase does not
establish real-runtime transaction identity, training, convergence, policy
quality, checkpoint continuation/resume, arbitrary M/N, public-route readiness,
R6 or R7. Public learned-policy route remains DORMANT / BLOCKED. No Isaac,
training campaign, evaluation/playback, checkpoint I/O, staging or commit was
performed. Stop after R5 for independent GPT review.
