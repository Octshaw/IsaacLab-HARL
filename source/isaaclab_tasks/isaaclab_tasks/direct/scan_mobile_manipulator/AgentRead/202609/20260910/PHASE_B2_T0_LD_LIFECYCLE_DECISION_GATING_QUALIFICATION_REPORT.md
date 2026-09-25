# Phase B2-T0-LD Lifecycle Decision-Gating Qualification Report

Date: 2026-09-10

Classification:
`PHASE-B2-T0-LD-LIFECYCLE-DECISION-GATING-QUALIFIED-AWAITING-GPT-REVIEW`

## A. repository authority

Read-only authority at qualification closeout:

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
monthly-migration path-set SHA-256: 0f2b8f7b52148e39196cbeb40fd9f4edd94fb762b6daf8be6279a116b80a39ab
```

The pre-existing staged monthly migration remained byte-for-byte/index-exact.
No add, commit, push, reset, checkout, or clean operation occurred.

## B. starting B2-T0 failure state

B2-R0 through B2-R7 remain `GPT REVIEW PASS / CLOSED`; training-update
readiness and the single real transaction remain established. B2-T0 run03
completed tx1 through S10, then stopped during tx2 collection after cumulative
actor counters changed `(1,1,1) -> (2,2,2) -> (2,2,3)`. Run03 remains
`PARTIAL_UPDATE / POISONED / STOPPED / HISTORICAL`; B2-T0 remains not complete,
and repeated-update continuity remains not established.

## C. run03 read-only artifact inventory

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `run03_final_result.json` | 1,405 | `d1b1cc44b82b352d96d38a37ca1caef1092d479ec960a732a18ecba9b2bcc25f` |
| `run03_process_config_authority.json` | 198,320 | `28602630b1ceeaea5cda45dfa85a517adbabd8e44a63e2fc4ee94545ef342c33` |
| `run03_supervisor.json` | 414,525 | `6c1e564b0c4d860fbd9fdf600528ba4590abe0db33c6cf609ea318ab3786bcbf` |
| `run03_tx1_actor_factor_progress.json` | 6,039 | `8d2a03edf3f9fba0006eef8d286593c2fc4fe1ff0d432f065f6b365b1f3e4a69` |
| `run03_tx1_critic_progress.json` | 780,711 | `404a31bfc066b11a58497d0daddaab934d0922558eea839f82f2e5c96750b83a` |
| `run03_tx1_pre_mutation.json` | 23,191 | `1be27cb22994b0895b215a28a245498caba1e84277d8233c4d84de1277067fe6` |
| `run03_tx1_s10.json` | 423,096 | `4f4bdb7bf997966f66529c5cb69db988132ce81a1b5c092b07b352b1e5564026` |

All were inspected read-only. There is no tx2 boundary, rollout, pre-mutation,
bridge, lifecycle-row, DVM, ownership, terminal, or generation artifact.

## D. current production lifecycle authority

`assignment_lifecycle_transition_contract.py:77-100` identifies the sole
`LIFECYCLE_AUTHORITY_V1` and the canonical task/robot enums.
`assignment_lifecycle_transaction_runtime.py:1662-1737` consumes execution
facts, completes/releases ownership, updates failed pairs, and independently
derives each `[E,M]` robot row as `NEEDS_ASSIGNMENT`, `EXECUTING`,
`WAITING_FOR_TASK`, or `UNAVAILABLE`. The resulting P2 lifecycle snapshot is
the only current lifecycle truth; B2-T0-LD adds no state machine or ownership.

## E. policy invocation source path

The exact path is:

```text
current P2 publication
  -> I1 immutable current evidence snapshot
  -> I2 row classification / DVM
  -> I3a per-actor DVM env subset
  -> actor.get_actions once when subset nonempty
  -> immutable proposal envelope
  -> existing I4-2 adapter/resolver/effective assignment
  -> existing P2/controller step
```

`assignment_event_policy_evidence.py:818-927` binds I1 to the exact current P2
publication and OPEN window. `assignment_event_policy_decision.py:556-656`
classifies rows. `assignment_event_actor_collection.py:621-674` performs the
only actor invocation: one batch call per actor when its DVM environment subset
is nonempty, otherwise no call. `assignment_event_learned_route.py:466-548`
preserves this bundle through proposal, resolver/facade, P2 step, next-current
capture, and actor/critic slot insertion. Physical step index is absent from
the eligibility calculation.

## F. continuation decision semantics

An authoritative `EXECUTING` robot must own exactly one active task in
`CLAIMED`, `NAVIGATING`, or `ALIGNING`; contradictions fail closed. I2 emits
`FORCED_CONTINUATION_ROW`, DVM false, the current owned task as the sole forced
action, no new proposal, and no behavior logprob evidence. The resolver retains
the active target and records continuation. A policy call on this row is a
true lifecycle violation.

## G. reopened-decision semantics

The lifecycle authority releases completed, explicitly released, failed, or
unavailable-owned tasks as source facts require. After updated task/ownership
state, a robot with eligible remaining work becomes `NEEDS_ASSIGNMENT`.
I2 permits a new decision only when that state also has at least one task that
is `AVAILABLE`, unowned, not a failed pair, and explicitly physically feasible.
Thus completion/release may reopen a decision, but neither physical-step
advance nor absence of ownership alone is sufficient.

## H. asynchronous multi-robot lifecycle semantics

All authoritative tensors and I2 row classification are per `[E,M]` row.
I3a builds a separate environment subset for each robot. No synchronization
rule requires all robots in one environment to share a decision boundary.
The controlled primary witness passed `(continuation, continuation, reopened)`
with per-row calls `(0,0,1)` at one environment and one physical boundary.

## I. terminal/autoreset decision semantics

I1 rejects historical terminal rows (`assignment_event_policy_evidence.py:
912-925`). Terminal evidence remains attached to the previous transition;
the learned route then obtains the post-autoreset current P2 publication and
its episode/transition identity for the next bundle. A decision in that new,
current, nonterminal generation is not a continuation resample. The new
observer marks an episode-generation change as
`POST_AUTORESET_CURRENT_GENERATION` without changing terminal/I5b behavior.

## J. DVM/active/available-action relationship

- DVM is pre-inference eligibility in I2: true iff `POLICY_DECISION_ROW`.
- `policy_proposal_present_mask` in I2 is an eligibility plan; I3a fills an
  actual original-proposal ledger on exactly those rows and binds it back.
- Active mask is separate learner evidence. Actor collection uses DVM, while
  actor loss uses `active AND DVM`; active does not create a decision.
- `available_actions` expresses legal/forced action choice. On policy rows it
  constrains sampling after invocation; on continuation/noop rows it carries
  one forced action without invoking policy.

The observer reuses DVM/row kind; it does not overload either with new meaning.

## K. run03 actor-2 reconstructable evidence

Durable evidence establishes only: tx1 completed S10; tx2 began; after its
first collection step all cumulative counters were `(2,2,2)`; after the second
they were `(2,2,3)`; the stop occurred before tx2 adapter/mutation artifacts;
and tx1 had already mutated the learner. Current qualified source shows how a
call would be gated, but current code behavior is not substituted for missing
historical pre-call state.

## L. run03 actor-2 unrecoverable evidence

The artifacts do not preserve actor-2's tx2-step-2 robot state, owned task,
task lifecycle, completion/release/failure event, availability, terminal/reset
context, episode generation, DVM, valid environment subset, or proposal row.

```text
RUN03 TX2 ACTOR-2 EXACT LIFECYCLE DECISION CAUSE:
  UNRESOLVED FROM EXISTING DURABLE ARTIFACTS
```

## M. old B2-T0 harness assumption

The old harness required every actor counter to increase once on physical step
1, then required all counters to remain unchanged and all proposal masks to be
false on physical step 2. It used global cumulative counters plus rollout
position as lifecycle authority. That assertion was valid for one prior fixed
fixture pattern, not for repeated asynchronous lifecycle evolution.

## N. root-cause classification

`OUTCOME A — HARNESS OVERCONSTRAINT`.

Production gating is internally consistent and already supports a legitimate
later decision after reviewed lifecycle reopening. No controlled source path
called policy for a proven continuation. The B2-T0 failure was caused by the
harness's unsupported second-step invariant; this does not retrospectively
decide run03 actor-2's exact cause.

## O. lifecycle-derived observer design

The harness now reads the exact pre-call bundle retained by the proposal
envelope. For every environment/robot it records collection/physical indices,
episode and transition generations, robot state, owned task, I2 row reason,
DVM-derived `decision_required`, I3a actor-subset participation count, actual
proposal/logprob presence, continuation, reset context, and read-only ownership
before/after. Decision identity is
`(episode_generation, transition_generation, collection_index, env, robot)`.

Primary cardinality comes from the invocation-site I3a call record and valid
environment subset. ActorRecorder cumulative deltas are supplemental and must
agree with the I3a batch record. The check is exact: required means one row
participation; nonrequired means zero; missing and duplicate calls STOP.

## P. genuine continuation witness

Case A: an `EXECUTING` robot owning an active `NAVIGATING` task produced DVM
false, forced continuation, zero actor calls, no proposal, and no behavior
logprob evidence. PASS. Case H independently passed three simultaneous
continuations with `(0,0,0)`.

## Q. reopened-decision witness

Cases B-D passed source-derived reopening for post-completion/release with
remaining work, failed-pair release with another legal target, and initial
unassigned eligibility. Each produced DVM true and exactly one proposal call.
The existing controlled multi-step lifecycle suite additionally passed the
actual row sequence `POLICY -> CONTINUATION -> POLICY` after completion/release.

## R. asynchronous 3-robot witness

Case G, same env and boundary:

```text
robot 0: EXECUTING continuation -> 0
robot 1: EXECUTING continuation -> 0
robot 2: NEEDS_ASSIGNMENT with legal target -> 1
observer result: PASS
```

## S. missing-call negative witness

Case K changed one policy-required row's call/proposal/logprob evidence to
zero. It failed closed with `STOP — B2-T0 MISSING_REQUIRED_POLICY_CALL`.

## T. duplicate-call negative witness

Case J supplied two calls for one decision identity. It failed closed with
`STOP — B2-T0 DUPLICATE_POLICY_CALL`.

## U. invalid continuation-resample witness

Case L supplied one call/proposal/logprob for an authoritative continuation.
It failed closed with `STOP — B2-T0 POLICY_CALL_DURING_CONTINUATION`.

## V. unavailable/nondecision witness

Case F projected `UNAVAILABLE` to `FORCED_NOOP_ROW`, DVM false, noop-only
availability, zero actor calls, and zero proposal evidence. PASS. The source
also treats waiting and `NEEDS_ASSIGNMENT` with no legal target as forced noop.

## W. terminal/autoreset witness

Case E used a canonical episode-reset current publication, not historical
terminal evidence. The current generation was decision-eligible and received
exactly one call. The observer retained the generation and
`POST_AUTORESET_CURRENT_GENERATION` context. PASS. No I5b or terminal source was
modified.

## X. observer nonmutation proof

The observer accepts frozen scalar/tuple DTOs and returns a new frozen receipt.
For every positive controlled case, SHA-256 over source task/robot/ownership,
DVM, action, and logprob tensors was identical before and after observation.
Case M showed the same decision/call result at physical indices 1 and 99.
Observer mutation count: 0. No P2, actor, critic, optimizer, ValueNorm, buffer,
terminal-ledger, resolver, or effective-assignment mutation API is reachable.

## Y. files created/modified

Created:

- `scripts/environments/_assignment_phase_b2_t0_ld_decision_gate.py`;
- `scripts/environments/test_assignment_phase_b2_t0_ld_lifecycle_decision_gating_pure.py`;
- this report;
- `TASK_PROGRESS_ARCHIVE_BEFORE_B2_T0_LD_HANDOFF_20260910.md`.

Modified:

- `scripts/environments/test_assignment_phase_b2_t0_bounded_repeated_update_training_smoke.py`;
- `AgentRead/TASK_PROGRESS.md`.

The B2-T0 harness is one modified file. Its old step-position assertions were
removed and lifecycle gate receipts were added to future transaction/S10
artifacts. No B2-T0 runtime was executed.

## Z. production semantic modification count

Production semantic source modifications: **0**. Lifecycle, P2, action masks,
resolver, effective assignment, PPO evidence, returns, terminal, and R5
transaction sources are unchanged.

## AA. static/private/public guards

Static-only B2-T0/R7 authority passed:

```text
backward executor: 1
actor optimizer.step executor: 1
critic optimizer.step executor: 1
live ValueNorm.update executor: 1
R5 actor sequence calls: 1
R5 critic sequence calls: 1
scheduler steps: 0
reviewed private dependency edges: 18
public activation references: 0 (nine forbidden-public fixtures still fault)
qualified production and installed HARL hashes: exact
```

Artifact: `%TEMP%/b2_t0_ld_static_20260910.json`, 388,260 bytes, SHA-256
`16db3845697ef125b968a9b3f252428f90a2b6c17cff0f69d8f584900cbc5bda`.

## AB. exact controlled-test counts

```text
py_compile files: 3 PASS
B2-T0-LD controlled cases: 13 / 13 PASS
existing source-faithful multistep cases: 5 / 5 PASS
static-only authority checks: 1 PASS

production semantic source modifications: 0
B2-T0 harness modifications: 1 file
controlled lifecycle-decision witnesses: 13 cases
genuine-continuation PASS witnesses: 3 cases / 6 continuation rows
dedicated reopened-decision PASS witnesses: 6 cases / 8 decision rows
asynchronous robot witnesses: 1 case / 3 rows
missing-call STOP witnesses: 1
duplicate-call STOP witnesses: 1
continuation-resample STOP witnesses: 1
terminal/autoreset witnesses: 1
unavailable/nondecision witnesses: 1
observer mutations: 0

Isaac/AppLauncher/SimulationApp: 0/0/0
real rollout: 0
learner backward: 0
optimizer.step: 0
ValueNorm.update: 0
checkpoint I/O: 0
public activation: 0
B2-T0 retries: 0
```

## AC. retained poisoned-route/nonclaims

Run03 and B2-R5I attempts 1/2/3 remain poisoned historical routes and were not
reused or reclassified. Tx1 remains the only successful B2-T0 transaction and
S10. This qualification establishes gating semantics only; it does not
establish run03's missing cause, repeated-update continuity, checkpoint/exact
resume, training quality, convergence, evaluation, playback, or public route
readiness. R7 remains valid.

## AD. B2-T0 retry boundary

B2-T0 remains `NOT COMPLETE`; repeated-update continuity remains
`NOT ESTABLISHED`. A new real B2-T0 retry requires separate authorization after
independent review. Long training, B2-R6a/R6b, checkpoint I/O, evaluation,
playback, and public activation remain unauthorized.

## AE. final classification

`PHASE-B2-T0-LD-LIFECYCLE-DECISION-GATING-QUALIFIED-AWAITING-GPT-REVIEW`

Recommended state:

```text
B2-R0 through B2-R7: GPT REVIEW PASS / CLOSED
B2-T0 run03: PARTIAL_UPDATE / POISONED / STOPPED / HISTORICAL
B2-T0: NOT COMPLETE
B2-T0-LD: LIFECYCLE DECISION-GATING QUALIFICATION COMPLETE / AWAITING GPT REVIEW
lifecycle decision gating: QUALIFIED / AWAITING GPT REVIEW
run03 tx2 actor-2 exact historical cause: UNRESOLVED FROM EXISTING DURABLE ARTIFACTS
training-update readiness: REVIEW PASS / ESTABLISHED
repeated-update continuity: NOT ESTABLISHED
next B2-T0 retry: NOT AUTHORIZED
public learned-policy route: DORMANT / BLOCKED
```

## AF. GPT-review handoff

Please independently review the Outcome-A source trace, DVM-as-existing
pre-inference eligibility, I3a subset cardinality, asynchronous witness,
negative STOP witnesses, terminal generation boundary, nonmutation proof, and
harness-only diff. Do not retry B2-T0, start long training/B2-R6, perform
checkpoint I/O, activate the public route, stage, commit, or push. Stop and wait
for review.
