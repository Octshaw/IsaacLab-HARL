# Phase B2-R5I Real-Isaac Single-Transaction Integration Report

Date: 2026-09-01 (Asia/Shanghai)

## Classification

```text
PHASE-B2-R5I-STOP-POST-MUTATION-FACTOR-AUDIT-NOT-COMPLETE

B2-R5I:
  NOT COMPLETE

route:
  PARTIAL_UPDATE / POISONED / PROCESS STOPPED

successful real full learner transactions:
  0

S10 entries:
  0
```

The real runtime collection reached the reviewed R5 actor sequence, but the
second actor segment failed the R3 factor post-audit after real actor optimizer
mutation. The worker stopped. It did not run critic or ValueNorm mutation,
restore rollout mode, roll buffers, reset the terminal ledger, enter S10, save
weights, retry, or start another learner transaction. Therefore the requested
completion classification is not claimed.

## A. Repository authority

```text
branch:      main
HEAD:        b71d85a32f51be6ada324f870813a56bb45dd396
origin/main: b71d85a32f51be6ada324f870813a56bb45dd396
merge-base:  b71d85a32f51be6ada324f870813a56bb45dd396
relationship: HEAD == origin/main == merge-base
```

The starting dirty tree contained the reviewed uncommitted B2-R0 through R5
private artifacts and the separately performed AgentRead monthly archive
migration. Those existing items were preserved. This task staged none of its
B2-R5I paths and made no commit; pre-existing archive-migration index entries
were left untouched.

## B. Frozen R0-R5 authority

- B2-R0: GPT REVIEW PASS / FROZEN.
- B2-R1 through B2-R5: GPT REVIEW PASS / CLOSED under the supplied authority.
- B2-V2 runtime, policy-interface, and terminal learner-transport evidence was
  reused without changing lifecycle/P2, resolver, DVM, observation, reward,
  terminal precedence, event GAE, or controller semantics.
- The only mutation authorities remained the reviewed R2 backward, R3 actor
  step, R4 critic step/live ValueNorm, and R5 full-transaction coordinator.

## C. Files created or modified

Created:

- `assignment_event_training_real_isaac_adapter.py`
- `assignment_event_training_real_isaac_adapter_guards.py`
- `scripts/environments/test_assignment_phase_b2_r5i_real_isaac_single_transaction.py`
- `scripts/environments/test_assignment_phase_b2_r5i_real_shape_binding_pure.py`
- this report
- `TASK_PROGRESS_ARCHIVE_BEFORE_B2_R5I_HANDOFF_20260901.md`

Modified within the accumulated uncommitted R3 source:

- `assignment_event_training_actor_mutation.py`
  - device-bound CUDA index and active-mask construction;
  - canonical `[B]`/`[B,1]` true-row extraction after the real failure exposed
    coordinate flattening.
- `AgentRead/TASK_PROGRESS.md` after its byte-exact archive.

No installed HARL file was modified. The installed hashes remained:

```text
happo.py:    dd44fe7842160aa215b2d220726f6dd5e70b251c1a2e9c50cfeb6bd00535cf96
v_critic.py: ae66390702efb55099d151c11f28ae533f25ef6d62697949445abd2979708bf3
valuenorm.py:a35471b136567bde0b7fc7be34a7873efa617bdabf9a9074517ff0e3ef3fb8b0
```

## D. Exact real Isaac profile and config

```text
environment: Isaac-Scan-Mobile-Manipulator-Direct-v0
environment type: ScanMobileManipulatorEnv
profile: event_gated_local_mrta
device: cuda:0
resolved_T: 2
resolved_E: 2
resolved_M: 3
resolved_N: 12
B: 4
episode horizon: 3 physical control steps
actor epochs/minibatches: 5 / 2
critic epochs/minibatches: 5 / 2
ValueNorm: enabled
fixed_order: false
order seed: 1
actor order: (1,2,0)
```

Observed reset interface shapes matched prior B2-V2:

```text
actor observation: [2,3,421]
critic/share observation: [2,3,418]
available actions: [2,3,13]
```

## E. AppLauncher and environment identity

Both workers used the approved interpreter and one headless `cuda:0`
AppLauncher lifetime each. The first stopped at adapter import before
environment construction. The second constructed the real environment, reset
once, collected two physical transitions, closed the environment, and closed
SimulationApp. There was no GUI, video, evaluation, playback, or campaign.

## F. Real versus controlled evidence classification

REAL ISAAC / RUNTIME in the post-mutation worker:

- environment observation and post-autoreset current state;
- wrapper actor/critic observations and available-action masks;
- DVM and active masks;
- original policy proposals and original rollout behavior logprobs;
- P2/final-assignment/controller path;
- two real physical transitions;
- real TIME_LIMIT terminal/autoreset historical payload;
- exact pre-reset timeout critic input and post-reset current separation;
- real event critic buffer and compute-once return construction.

REAL LEARNER:

- installed HAPPO actors and actor Adam optimizers;
- real CUDA forward/backward/clip/optimizer step;
- factor-pre/post evaluation;
- reviewed R2/R3 and R5 coordinator entry.

CONTROLLED ONLY:

- pre-runtime static checks;
- CPU R1/R3/R5 regression harnesses run before the real attempt;
- the final `[B,1]` row-index regression run after process stop.

No synthetic runtime field replaced the authoritative real transaction.

## G. Real wrapper/runtime collection path

The path was:

```text
AppLauncher / real Isaac env
-> _compose_event_assignment_harl_wrapper
-> environment-owned lifecycle/P2 domain
-> dormant private event route collect_step x2
-> real actor storages + terminal learner collector + event critic buffer
-> private R5I evidence adapter
-> existing R5 full learner coordinator
```

The adapter constructs or steps no environment and contains no independent
backward, optimizer-step, or live-ValueNorm executor.

## H. Actor observation/action/logprob identity

At the first transition each of the three real actor recorder calls was checked
against the exact proposal envelope action and logprob for the same actor. The
stored learner inputs came directly from the completed real actor storages:
historical obs, historical availability, original proposal, original rollout
logprob, DVM, and active mask. No behavior logprob was recomputed.

## I. DVM, active, availability, and continuation

- Per actor DVM rows: `2,2,2` over `B=4`.
- Per actor active-and-DVM rows: `2,2,2`.
- Per actor forced/off-DVM rows: `2,2,2`.
- First transition: six genuine DVM policy rows.
- Second transition: six genuine forced continuation rows.
- Actor calls after the second transition remained `1,1,1`; no actor was
  resampled and no new policy proposal was created for continuation.

## J. Proposal versus effective assignment

The first and second controller assignments were checked exactly against the
final P2 publication. Actor storage retained the proposal/action/logprob pair;
effective assignment remained environment-owned P2/controller evidence and was
not substituted into the PPO behavior pair. The second transition additionally
made the distinction numeric and semantic: proposal-present was false while
the existing effective assignments continued.

## K. Lifecycle/P2 evidence

The real wrapper remained the reviewed P2 authority. The public wrapper step
fence rejected the dummy public action before environment mutation. The two
private steps retained `proposal -> lifecycle/P2 -> final P2 -> controller`.

## L. Terminal/autoreset classification

```text
REAL-ISAAC-FULL-TRANSACTION-WITH-TERMINAL-AUTORESET-EVIDENCE
```

This describes the collected real batch only, not a successful full learner
transaction. Both environments terminated by TIME_LIMIT on transition two.
Pre-reset historical critic observations differed from post-reset current
observations, episode generations advanced, safe historical copy preceded ACK,
and runtime terminal slots were empty after ACK while the learner ledger
remained populated until the later failure.

## M. Timeout/terminal evidence

The second collection used one current critic call followed by exactly one
timeout critic call. Exact input comparison between the environment-owned
pre-reset sidecar batch and the observed timeout critic input passed before
learner entry. The reason grid was `NONE` at slot zero and `TIME_LIMIT` at slot
one. Higher-priority terminal categories were not present in this batch.

The in-memory terminal digests were not durably emitted before the later
post-mutation exception; this report does not fabricate them from another run.

## N. Event returns compute-once evidence

The real adapter verified `_event_returns_computed == false`, called the
reviewed `EventOnPolicyCriticBufferEPV2.compute_event_returns()` exactly once,
and passed result shape/finiteness/equality/no-alias guards before any actor
mutation. Reaching S5 proves S2/S3 accepted the return binding. Stock HARL
`compute_returns()` calls were zero.

The result digest was in-memory only and was not durably emitted before the
post-mutation exception. This is a retained failure-observability gap, not a
license to reconstruct a synthetic value.

## O. `returns[:-1]` identity

The learner target was the same transaction's real
`critic_buffer.returns[:-1]`, shape `[2,2,1]`; it was finite, exactly equal to
the event result, non-aliasing, and excluded the `[2,1]` structural final slot.
Critic mutation never began.

## P. Immutable plan and count derivation

The real plan derived, rather than copied, these counts:

```text
actor per actor:
  5 epochs x one nonempty active-and-DVM minibatch = 5 backward / 5 step

critic:
  5 epochs x 2 exact-coverage minibatches = 10 backward / 10 step

ValueNorm enabled:
  expected 10 updates
```

The generated order was `(1,2,0)`. Only the first two order positions executed
before failure.

## Q. S0-S4 evidence

- S0 real rollout/buffer/storage/terminal-ledger completeness: passed.
- S1 real final value and historical terminal binding: passed.
- S2 real event return freeze and identity: passed.
- S3 immutable real-batch plan: passed.
- S4 one training-mode entry: passed.

## R. Real actor sequence

Actor 1 completed five real backward/Adam steps. Actor 2 then completed five
real backward/Adam steps. Actor 0 did not begin. Exact executed count:

```text
per actor backward:       actor0=0, actor1=5, actor2=5
per actor optimizer.step: actor0=0, actor1=5, actor2=5
total:                    10 / 10
```

## S. Sequential factor evidence and failure

The failure occurred during actor2's factor segment post-audit after its fifth
step. Root cause was exact and source-local:

```text
real mask shape: [B,1]
old extraction: mask.nonzero(as_tuple=False).flatten()
effect: row coordinates and the column coordinate 0 were mixed
```

With order `(1,2,0)`, actor1 had already created a non-one factor at DVM row 0.
Actor2's off-DVM witness construction incorrectly included row 0 through the
flattened column coordinate and then observed the legitimate actor2 factor
change there. R3 correctly failed closed with `STOP — B2-R FACTOR`, but the
witness row set was wrong.

The post-stop source repair now extracts canonical rows through
`mask.reshape(-1).nonzero(...)`. A pure regression proves identical indices for
`[B]` and `[B,1]`, exact off-DVM rows `(2,3)`, exclusion of row 0, and
fail-closed rejection of `[B,2]`. No real rerun was performed.

## T. Critic and ValueNorm sequence

Not entered:

```text
critic backward:       0
critic optimizer.step: 0
live ValueNorm.update: 0
```

## U. S7 post-update audit

Not reached. The actor factor failure occurred in S5. No full post-update audit
passed.

## V. S8 rollout mode

Not reached. Rollout-mode restoration count: `0`.

## W. S9 critic rollover

Not reached. Critic rollover count: `0`.

## X. Terminal-ledger reset

Not executed. The real terminal learner ledger was intentionally not cleared
after the partial update. Reset count: `0`.

## Y. Actor storage rollover

Not executed. Actor storage rollover count: `0`; real current slots were not
substituted or reused after failure.

## Z. S10 quiescence

Not reached. S10 entries: `0`. Checkpoint boundary eligibility was not
established.

## AA. Next-rollout-ready evidence

Failed by policy. The route was partial/poisoned and the process was stopped.
No next observation consistency read, collection, optimizer cycle, or learner
transaction was started.

## AB. Private dependency/static/public guards

Passing final static result:

```text
R5 coordinator calls in adapter:        1
event-return producer calls in adapter: 1
new backward executors:                 0
new optimizer-step executors:           0
new live ValueNorm executors:           0
environment reset/step/make in adapter: 0
public production files scanned:        57
public R5I references:                  0
private exports:                        0
```

The public route remained dormant/blocked. No runner, profile default, legacy
behavior, checkpoint contract, or installed HARL source changed.

## AC. Exact execution counts

Successful transaction count is separated from the task-wide attempts.

```text
successful real full learner transactions: 0
S10 entries:                               0

real Isaac environment resets:             1
real rollout steps collected:               2
event-return compute:                       1

actor backward / optimizer.step:          10 / 10
per actor backward/step:                    0/0, 5/5, 5/5
critic backward / optimizer.step:           0 / 0
live ValueNorm.update:                      0

training-mode entries:                     1
rollout-mode restorations:                 0
critic rollover:                            0
terminal-ledger reset:                      0
actor storage rollovers:                    0

checkpoint weight I/O:                     0
training campaigns:                         0
evaluation/playback:                        0
public route activations:                   0
```

Task-wide worker/setup accounting:

```text
PTY command creation failures before process: 1
AppLauncher workers/lifetimes:                2 / 2
pre-environment import failures:              1
post-mutation poisoned real runs:              1
real environment constructions/resets/steps:  1 / 1 / 2
fresh real learner transactions begun:         1
retries after post-mutation failure:            0
```

The actor `10/10` count is an exact deterministic source/evidence derivation:
order `(1,2,0)`, five planned steps per actor, failure in actor2's post-factor
audit after its segment. No critic call can occur before that source boundary.

## AD. Diagnostic/setup attempts

1. A requested PTY process was rejected by Windows before any subprocess
   existed; it is not an AppLauncher or authoritative attempt.
2. The first worker stopped at an incorrect adapter import before environment
   construction, reset, collection, return computation, or mutation. The
   import was corrected and static checks passed.
3. The second worker performed the sole real collection/learner entry and then
   failed after mutation. Per the hard boundary, no further real run occurred.

External failure artifact:

```text
path: C:\Users\33506\AppData\Local\Temp\b2_r5i_real_single_20260901.json
bytes: 15934
SHA-256: f774ee34ee2208d40fb31718bb4945f17a01e68f94ff489f86e9e07bb2d950fa
```

## AE. Verification and retained nonclaims

Passing checks:

- `py_compile` for the modified/new R3/R5I Python files;
- all three R1 pure suites before real execution;
- R3 controlled actor mutation regression before real execution;
- R5 controlled full-transaction regression before real execution;
- R5I static/private guard before both workers and after the source repair;
- R5I `[B]`/`[B,1]` row-index pure regression after process stop;
- R1 plan/factor pure regression after process stop.

No post-failure controlled or real learner transaction was run after the source
repair.

This phase does not establish a successful real full learner transaction,
S10, next-rollout readiness, training-update readiness, convergence, policy
quality, long-run stability, checkpoint recovery, exact resume, evaluation, or
public learned-policy readiness.

## AF. Recommendation boundary for GPT review

Independent GPT review should evaluate:

1. the partial-update/poison classification and exact count derivation;
2. the narrow canonical-row repair and its pure regression;
3. whether a separately authorized new B2-R5I reentry is warranted.

This task does not authorize that reentry. Do not proceed to B2-R7 or B2-R6,
do not start training, do not save/load weights, and do not activate the public
route.
