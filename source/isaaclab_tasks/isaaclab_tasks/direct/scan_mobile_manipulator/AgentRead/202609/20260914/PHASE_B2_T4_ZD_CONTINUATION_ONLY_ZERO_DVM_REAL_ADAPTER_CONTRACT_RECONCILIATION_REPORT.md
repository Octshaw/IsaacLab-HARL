# Phase B2-T4-ZD Continuation-only / Zero-DVM Real-adapter Contract Reconciliation Report

Date: 2026-09-14

Classification: `PHASE-B2-T4-ZD-CONTINUATION-ONLY-ZERO-DVM-REAL-ADAPTER-CONTRACT-QUALIFIED-AWAITING-GPT-REVIEW`

## A. Repository authority

The qualification used branch `main` at `b71d85a32f51be6ada324f870813a56bb45dd396`; `HEAD`, `origin/main`, and their merge-base were equal. The existing 359 staged monthly-archive migration paths were untouched. The staged-index SHA-256 remained `a40169043c3bfffd481a7ed1bddf3e52663d61379bedfd2610781457d11f947c`, and the monthly path-set SHA-256 remained `0f2b8f7b52148e39196cbeb40fd9f4edd94fb762b6daf8be6279a116b80a39ab`. No `git add`, commit, push, reset, checkout, or clean operation occurred.

## B. Starting reviewed authority

B2-R0 through B2-R7 and B2-T0 through B2-T3 remain GPT-review closed. Original B2-T4 remains historical and incomplete; B2-T4-NR and B2-T4-SR remain closed; B2-T4-RE1 and B2-T4-RE2 remain historical, poisoned, and incomplete. B2-T4-ZD alone was authorized for design, implementation, and CPU qualification. B2-T4-RE3 and B2-R6 were not authorized.

## C. Historical RE2 preservation

RE2 was not reclassified or modified. The retained tx002 rollout evidence, final result, and failure adjudication remained byte-identical:

| Artifact | SHA-256 |
|---|---|
| tx002 rollout decision evidence | `93b4624167ce8b8dd052e4d3ab4c3cf105b34cd1a140ee840313edc2f8935fda` |
| RE2 final result | `0f50df029eec40f5e4dcc69f3420078232b2882cf9a7061ece7efc0890529185` |
| RE2 failure adjudication | `2659989026f652458867fa61931a871da94e499792d3573fbfe7dc535da39160` |

RE2 retains tx001 S10 and ledger qualification, tx002 physical completion, `partial_update=true`, `route_poisoned=true`, and retry count zero.

## D. Exact RE2 tx002 failure trace

The retained tx002 contains `T=2`, `E=2`, `M=3`, 12 physical actor rows, 12 continuation rows, zero policy calls, zero DVM rows, zero forced-noop rows, and no collection-time learner mutation. The former adapter then rejected it before S0 with `real batch has no active-and-DVM actor training opportunity`. No downstream R5 zero-DVM limitation caused that STOP.

## E. Active-mask semantics

The active mask remains the canonical actor-loss participation mask stored for each physical row. ZD does not redefine it. The actor loss population continues to use the intersection `active AND DVM`.

## F. DVM semantics

DVM remains reviewed pre-inference policy-decision eligibility evidence. A continuation row has DVM false, causes no policy call, and creates no fresh proposal/logprob evidence. A policy-decision row has DVM true and exactly one bound policy sample. No DVM, lifecycle-gate, or continuation semantics changed.

## G. Expected actor-training population

For every actor and flattened `(slot, env)` position, the adapter reads the sealed decision-bundle DVM and canonical storage active mask. Each true `active AND DVM` intersection creates one expected identity:

`(update_id, actor_id, slot, env_id, episode_generation, transition_generation)`.

Counts are derived from these identities; they are not used as a substitute for identity equality.

## H. Observed actor evidence population

Observed rows come from the actually bound actor inputs after exact position-preserving equality with completed canonical storage. DVM rows additionally require finite actor observation, present/legal action proposal, finite behavior old logprob, policy-row kind, and no forced-action identity. Off-DVM rows require no proposal, the canonical forced action, and the reviewed forced-row logprob sentinel.

## I. Actor row identity authority

Update, actor, rollout slot, environment, episode generation, and transition generation jointly identify a row. Transition generation `-1` remains legal because it is the reviewed initial-generation sentinel. Wrong update, wrong actor, wrong slot/env/generation, missing, unexpected, and duplicate rows all fail closed. Duplicate detection occurs before set comparison.

## J. Old adapter invariant

BEFORE: real adapter admitted a batch only if at least one active-and-DVM actor training opportunity existed.

## K. New adapter invariant

AFTER: real rollout completeness is independent of actor-training population size; actor evidence is required exactly for canonical active-and-DVM rows; an empty actor-training population is valid only when the expected population is exactly empty.

Formally, expected and observed row identities must match exactly per actor and batch-wide. Empty/empty is valid. Expected-nonempty/observed-missing and expected-empty/observed-nonempty remain STOP conditions.

## L. Canonical actor-evidence reconciliation

One shared `reconcile_actor_evidence_v1` authority produces the canonical receipt and digest. The adapter derives and binds the two identity populations; S0 independently recomputes the same receipt and requires the bound digest. Diagnostics distinguish missing, unexpected, duplicate, identity mismatch, and update-ID mismatch.

## M. Zero-DVM actor semantics

A zero-DVM actor has zero expected and observed training rows, zero backward calls, zero optimizer steps, unchanged parameters and optimizer state, and an identity factor segment. It is neither missing evidence nor grounds for skipping the critic transaction.

## N. All-zero-DVM transaction semantics

All actors may legally be zero-DVM when all other rollout evidence is complete. The actor sequence produces three skipped identity segments, while event returns, critic sequence, ValueNorm, post-update audit, rollout-mode restoration, rollover, and S10 continue normally.

## O. Critic independence from DVM

The critic plan remains based on every physical rollout row. ZD added no total-DVM shortcut. In the primary all-zero witness, critic backward/step were exactly `1/1`, its twelve Adam parameter-state counters each advanced from 1 to 2, and ValueNorm updated once.

## P. Factor identity semantics

No factor mathematics changed. A zero-DVM actor performs no pre/post ratio fabrication and contributes identity. In the all-zero transaction, initial and final factor digests were equal. In the partial-zero witness, actor1 contributed identity while actor2 retained the cumulative factor from actor0.

## Q. Normal actor-rich positive witness

All three actors had two expected and observed active-and-DVM rows. Actor backward/step counts were `[2,2,2]` / `[2,2,2]`; every actor mutated normally, factor audits passed, critic backward/step were `1/1`, ValueNorm updated once, and S10 was reached.

## R. Partial zero-DVM positive witness

Expected and observed populations were `[(0,2),(1,0),(2,2)]`. Actor counts were `[2,0,2]` / `[2,0,2]`. Actor1's parameter/optimizer fingerprints and Adam-state vector remained unchanged, and its factor segment was identity. Actors 0 and 2 trained; critic backward/step were `1/1`, ValueNorm updated once, and S10 was reached.

## S. All-zero-DVM positive witness

The source-faithful continuation transaction admitted expected/observed populations `[(0,0),(1,0),(2,0)]`, reached S0–S10, and retained the critic path.

| Actor | Expected DVM rows | Observed actor rows | Backward | Optimizer step | Adam delta | Factor contribution |
|---:|---:|---:|---:|---:|---:|---|
| 0 | 0 | 0 | 0 | 0 | 0 | identity |
| 1 | 0 | 0 | 0 | 0 | 0 | identity |
| 2 | 0 | 0 | 0 | 0 | 0 | identity |

Critic backward was 1; critic optimizer step was 1; ValueNorm update was 1; S7/S8/S9/S10 all passed.

## T. RE2 tx002 retained-evidence replay

The replay first verified the immutable RE2 tx002 hashes and its exact 12-continuation/zero-policy/zero-DVM facts, including continuing ownership and no collection mutation. The same population shape was then recreated through the source-faithful private route without Isaac and accepted by the repaired adapter. Transaction evidence digest was `9dc1d13194426c86a4db443115f64069c978f340d2b1b5c1f95048b246507996`; actor reconciliation digest was `53c89a4e4527a1662656d373521602b9ad7fa3e398b7efdc43c614fe41e19704`.

## U. Missing actor evidence negative witness

Three source-faithful adapter cases independently removed/corrupted a required behavior old logprob, action/proposal, and actor observation. All stopped with `ACTOR_EVIDENCE_MISSING` before mutation. A direct expected-greater-than-observed identity case also stopped as missing.

## V. Unexpected actor evidence negative witness

A direct observed-greater-than-expected case stopped with `ACTOR_EVIDENCE_UNEXPECTED`. Expected-zero did not make evidence optional.

## W. Duplicate evidence negative witness

A duplicated observed identity stopped with `ACTOR_EVIDENCE_DUPLICATE`; conversion to a set did not hide it.

## X. Row-identity mismatch witness

Equal-count/wrong-row and wrong-actor cases stopped with `ACTOR_EVIDENCE_IDENTITY_MISMATCH`; a stale update stopped with `ACTOR_EVIDENCE_UPDATE_ID_MISMATCH`.

## Y. Continuation-policy-evidence contradiction witness

A continuation/DVM-false row carrying a fresh non-sentinel policy logprob stopped with `ACTOR_EVIDENCE_UNEXPECTED` before tx002 mutation.

## Z. Actor Adam audit

In the primary replay, all twelve Adam state counters for each actor were 2 before and after the all-zero transaction. Actor parameter and optimizer digests were also unchanged. In the partial-zero fixture actor1 had no initialized Adam state before or after, while actors 0 and 2 advanced according to plan.

## AA. Critic/ValueNorm audit

Each of the three positive witnesses performed exactly one critic backward, one critic optimizer step, and one ValueNorm update. The primary replay's critic optimizer counters advanced exactly one step per parameter state, and its ValueNorm digest changed.

## AB. Event-return audit

The all-zero transaction computed event returns exactly once. Stock `compute_returns` calls remained zero. The all-NONE final bootstrap was present and finite.

## AC. Lifecycle/ownership nonmutation

The retained RE2 evidence remains the lifecycle authority: all 12 rows were continuation rows for robots still EXECUTING owned tasks, with no policy call and no new claim. The replay did not alter that evidence. Existing adapter runtime/P2 immutability audits passed, and reconciliation only reads sealed bundles and completed storages.

## AD. NR regression

NR passed 5/5, including its 14-case terminal reconciliation matrix, all-NONE bootstrap, mixed terminal/nonterminal transaction, and missing-evidence fail-closed case. Terminal derivation and NONE empty/empty semantics were unchanged.

## AE. SR regression

The SR serializer source remained SHA-256 `dcf780a37387e24b4cc3c1f5ee39d006029b04875bc6422c96896cddd8cb5358`, unchanged from the reviewed source. The historical SR runner correctly STOPped when asked to require the pre-ZD training-source hashes. The same full SR suite was then replayed against the authorized ZD production hashes: 7/7 positives, 12/12 negatives, retained RE1 tx001 replay, ledger roundtrip, post-S10 bookkeeping, nonmutation, and static guards all passed. Historical SR authority was not rewritten.

## AF. Backward compatibility

The controlled terminal-rich R5 transaction passed, including the pre-existing zero-DVM actor segment. I5b passed 14/14; lifecycle-decision gating passed 13/13; R5I shape binding passed; and R1 authority/ownership, permit/order/static-public, update-plan, and factor suites passed. No missing-evidence negative began passing.

## AG. Production files changed

Exactly two production semantic files changed:

1. `assignment_event_training_full_transaction.py`, SHA-256 `a45db23b863c51334b15205b3c50fa5997ab8f5e4a32f8c4a801242365b583d7`.
2. `assignment_event_training_real_isaac_adapter.py`, SHA-256 `57419d52caa77160609f77b289979ed6785fc645eab1b17320e9cbda1e9500ac`.

The R5 CPU helper was extended only to construct the new required receipt fields, and one dedicated ZD test was added. No environment, P2, lifecycle runtime, controller, reward, decision gate, actor/critic math, factor math, ValueNorm, GAE, terminal, checkpoint, or public-route source changed.

## AH. Production diff rationale

The shared R5 file now owns the one canonical exact-row reconciler and S0 digest check. The adapter now derives expected/observed identities, validates mandatory versus forbidden row evidence, binds the canonical receipt, and removes only the obsolete global nonempty guard. The small shared change avoids parallel adapter and S0 authorities.

## AI. Static/private/public guards

Actor and critic optimizer executor ownership, ValueNorm mutation authority, and private-route boundaries remained unchanged. Scheduler changes, checkpoint I/O, and public activations were zero. Static-public guard suites passed. No public learned route was activated.

## AJ. Exact execution counts

For the final clean evidence pass:

```text
pure/static invocations: 9
ZD source-faithful adapter attempts: 8
ZD successful source-faithful full transactions: 4
NR source-faithful integrated runs: 3
RE2 tx002 replay: 1
normal actor-rich / partial-zero / all-zero positives: 1 / 1 / 1
negative fail-closed cases / unexpected passes: 10 / 0
primary positive actor backward / optimizer.step: 10 / 10
primary positive critic backward / optimizer.step: 3 / 3
primary positive ValueNorm.update: 3
AppLauncher / real Isaac / formal normal-horizon updates: 0 / 0 / 0
checkpoint I/O / public activation / B2-T4-RE3: 0 / 0 / 0
production semantic files changed: 2
git add / commit / push: 0 / 0 / 0
```

The fourth successful ZD transaction is the actor-rich setup needed to create the continuation contradiction negative witness. It is not counted again among the three primary positives.

## AK. Retained nonclaims

ZD is a bounded CPU contract qualification. It does not establish a fresh normal-horizon learned-training integration, W1–W7 qualification, checkpoint continuation, long-training readiness, convergence, or public learned-policy readiness. It does not authorize RE3, B2-R6, AppLauncher, evaluation/playback, checkpoint I/O, or long/paper-scale training.

## AL. Final classification

`PHASE-B2-T4-ZD-CONTINUATION-ONLY-ZERO-DVM-REAL-ADAPTER-CONTRACT-QUALIFIED-AWAITING-GPT-REVIEW`

This is not a self-issued GPT-review pass.

## AM. GPT-review handoff

Review the before/after contract, the canonical identity reconciliation and S0 digest binding, the 10 fail-closed negatives, the retained RE2 tx002 replay, and the strict two-file production boundary. If independently accepted, the next decision remains with the user. Do not start B2-T4-RE3 or any real Isaac/training/checkpoint/public-route activity from this report.
