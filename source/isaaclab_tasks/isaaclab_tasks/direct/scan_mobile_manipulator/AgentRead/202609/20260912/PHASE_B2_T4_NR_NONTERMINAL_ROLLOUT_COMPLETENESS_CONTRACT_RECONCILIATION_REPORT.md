# Phase B2-T4-NR — Nonterminal Rollout-Completeness Contract Reconciliation

Classification: `PHASE-B2-T4-NR-NONTERMINAL-ROLLOUT-COMPLETENESS-CONTRACT-QUALIFIED-AWAITING-GPT-REVIEW`

## A. Repository authority

- Branch: `main`.
- HEAD, `origin/main`, and merge-base: `b71d85a32f51be6ada324f870813a56bb45dd396`.
- Starting working-tree status: 463 porcelain lines.
- Ending working-tree status: 475 porcelain lines; the increase is the authorized B2-T4-NR production/test/report/artifact set.
- Preserved staged monthly-migration paths: 359.
- Preserved staged-index SHA-256: `a40169043c3bfffd481a7ed1bddf3e52663d61379bedfd2610781457d11f947c`.
- Preserved monthly path-set SHA-256: `0f2b8f7b52148e39196cbeb40fd9f4edd94fb762b6daf8be6279a116b80a39ab`.
- No add, commit, push, reset, checkout, or clean was run.

## B. Starting reviewed authority

`B2-R0` through `B2-R7` and `B2-T0` through `B2-T3` remain GPT REVIEW PASS / CLOSED. The established lower-level all-NONE bootstrap and zero-DVM transaction results were treated as inherited evidence, not as authority to retry B2-T4.

## C. B2-T4 stop handoff

The historical B2-T4 classification remains exactly `PHASE-B2-T4-STOP-NONTERMINAL-BOOTSTRAP-NOT-QUALIFIED`. It is STOPPED / HISTORICAL / NOT COMPLETE and was not reclassified. B2-T4 tx001 was not started.

## D. Exact old contract trace

Source inspection found the two pre-update blockers named by the handoff and one same-contract downstream residue:

1. the real adapter unconditionally required `route.collector.consumed_terminal_keys` to be nonempty;
2. R5 S0 rejected `not keys` even after structural rollout evidence was complete;
3. R5 S7 also rejected `not terminal_keys_after`, so an all-NONE rollout accepted by a repaired S0 would still stop after controlled mutation.

The third residue was exposed by the first source-faithful all-NONE integration attempt and was reconciled in the same full-transaction file. No broader production dependency was changed.

## E. Rollout-completeness definition

Production `assignment_event_learned_route.finish_rollout` establishes structural completeness from initialization, every critic `_event_slot_written`, and every actor `next_action_slot == T` (current lines 554–576). The real adapter independently checks actor cursors and critic event slots, requires the complete `[T,E,1]` reason grid, evaluates one finite final current-next critic value, computes event returns once, and binds immutable rollout/update identity. None of those facts depends on `terminal_count > 0`.

## F. Terminal-evidence completeness definition

Terminal evidence is complete iff the unique observed consumed keys exactly equal the unique expected keys derived from authoritative non-NONE reason rows. Duplicate detection occurs before set comparison. Empty/empty is valid; empty/nonempty and nonempty/empty are fail-closed.

## G. Terminal identity authority

The existing `EventTerminalCorrelationKeyV2` remains the only key identity: `(env_id, episode_generation, transition_generation)` (terminal transport lines 148–165). `EventLearnerTransitionExpectationV2` captures the sealed pre-step decision bundle; `expected_key(env_id)` retains the bundle episode generation and uses source transition generation plus one (lines 172–240). No clock or identity format was invented.

## H. Expected-terminal derivation

The adapter helper `_derive_expected_terminal_keys_v1` walks all `T` actor-storage `decision_bundle_refs`, requires every actor to share the exact canonical bundle object for each slot, validates the `[T,E,1]` reason domain, and calls the existing `expectation.expected_key(env_id)` only when the authoritative reason is not `NONE`. Thus ALL_TASKS_COMPLETED, NO_FEASIBLE_TASKS_REMAIN, and TIME_LIMIT require evidence; NONE does not.

## I. Observed-terminal reconciliation

`EventTerminalLearnerCollectorV2.consume_before_optimizer_update` gets keys from canonical terminal correlation, rejects already-consumed keys, and reserves the keys before critic evaluation/insertion (critic-buffer lines 327–493). The new shared R5 reconciler validates immutable tuple shape and nonnegative exact integers, detects expected and observed duplicates, classifies missing, unexpected, generation-only, and general identity mismatch separately, and returns a digest-bound exact-match receipt.

## J. Adapter old/new invariant

BEFORE:

> rollout accepted only if terminal learner key ledger was nonempty.

AFTER:

> rollout completeness is established independently; terminal historical evidence is required exactly for rows whose canonical termination reasons require it; an empty terminal-evidence set is valid only when the expected set is empty.

The adapter now derives expected keys from canonical slot identities/reasons, calls the shared reconciler, and binds both expected keys and the reconciliation receipt digest into rollout and pre-mutation evidence.

## K. R5 S0 old/new invariant

S0 no longer treats key presence as rollout completeness. It calls the same shared reconciler against live collector keys, validates the receipt digest and all independent structural/final-value/event-return evidence, and rejects any mismatch. S7 still requires the terminal ledger to remain byte-semantically unchanged during mutation, but no longer requires it to be nonempty.

## L. Production files changed

1. `assignment_event_training_real_isaac_adapter.py` — canonical expected-key derivation, shared reconciliation call, and receipt binding.
2. `assignment_event_training_full_transaction.py` — shared reconciliation receipt/helper, rollout receipt fields, S0 shared validation, and S7 removal of the residual nonempty assumption.

Test support changed in `_assignment_phase_b2_r5_full_transaction_helpers.py`; the dedicated qualification is `test_assignment_phase_b2_t4_nr_nonterminal_rollout_completeness_contract.py`.

## M. Production diff rationale

Adapter old invariant: nonempty observed ledger. New invariant: exact expected/observed match derived from canonical row identity. This permits ordinary nonterminal horizons while rejecting stale or absent terminal history.

Coordinator old invariant: S0 and S7 independently required nonempty keys. New invariant: S0 owns exact shared reconciliation; S7 only proves that the already-reconciled ledger did not mutate during the learner update. Terminal fail-closed behavior is stronger and more diagnostic, not optional.

No environment, lifecycle, reason priority, reward, controller, actor collection, PPO/HAPPO, critic, CG, ValueNorm, checkpoint, or public-route semantics changed.

Current source SHA-256 values:

- full transaction: `a6b8f4d283d5eaf14a4a7d686e1f3b6424837552d673909ea5808b2bf7d057de`;
- adapter: `b85034d7436de4a79c37de0f2e40a09200dfbca225994c0cae2c8f6bcd491014`.

## N. All-NONE positive witness

Matrix A passed with 0 expected and 0 observed keys. The integrated `T=2,E=2` route produced four NONE rows, no timeout sidecar rows, one finite final current-next bootstrap evaluation, one event-return computation, and reached S10.

## O. All-NONE stale/extra negative witness

Matrix B supplied one stale key against an empty expected set and stopped precisely with `STOP — B2-R TERMINAL_EVIDENCE_UNEXPECTED`. No false accept occurred.

## P. TIME_LIMIT positive/negative witnesses

An exact TIME_LIMIT key passed. The corresponding missing-key case stopped with `TERMINAL_EVIDENCE_MISSING`. I5b regression retained historical pre-reset timeout bootstrap and trace-stop behavior.

## Q. Terminal generation mismatch witness

Wrong generation for the same environment and stale previous-generation evidence each stopped with `STOP — B2-R TERMINAL_GENERATION_MISMATCH`. A wrong environment identity stopped with `TERMINAL_EVIDENCE_IDENTITY_MISMATCH`.

## R. ALL_TASKS_COMPLETED witness

The exact required key passed. I5b regression retained zero bootstrap and trace stop. The integrated mixed route contained one real ALL_TASKS_COMPLETED row.

## S. NO_FEASIBLE_TASKS_REMAIN witness

The exact required key passed. I5b regression retained zero bootstrap and trace stop.

## T. Mixed NONE/TIME_LIMIT witness

The pure mixed case passed with evidence only for TIME_LIMIT. The integrated mixed route contained six NONE rows and one TIME_LIMIT row; exactly one timeout sidecar row was consumed.

## U. Mixed NONE/completion witness

The pure mixed case passed with evidence only for completion. The integrated route contained six NONE rows and one ALL_TASKS_COMPLETED row; NONE rows fabricated no terminal key.

## V. Duplicate evidence witness

An observed repeated key was detected before set conversion and stopped with `STOP — B2-R TERMINAL_EVIDENCE_DUPLICATE`.

## W. Missing current-next bootstrap witness

An otherwise structurally complete all-NONE R5 receipt with 0/0 terminal keys but `final_value_evaluated=False` stopped at S0 with `STOP — B2-R ROLLOUT_INCOMPLETE`. Terminal absence therefore does not remove the independent final-bootstrap requirement.

## X. Zero-DVM regression

The controlled all-zero-DVM full transaction passed: actor backward `[0,0,0]`, actor optimizer.step `[0,0,0]`, actor parameters and optimizer states unchanged, identity factor unchanged, critic backward/step `1/1`, ValueNorm update `1`, and S7–S10 `1/1/1/1`.

## Y. Event-return regression

The full I5b suite passed 14/14. It covers all NONE current-next bootstrap, TIME_LIMIT historical sidecar, completion/no-feasible zero bootstrap, mixed rows, compute-once/no-alias, ValueNorm on/off, and the stock consistency oracle. Production stock `compute_returns` calls remained 0.

## Z. Integrated all-NONE R5 witness

The private source-faithful CPU route traversed adapter validation → S0 → final-value binding → event-return construction → full R5 transaction. Result: 0/0 terminal keys, actor backward/step `[4,4]/[4,4]`, critic backward/step `1/1`, ValueNorm update `1`, and S10 `1`. Evidence digest: `849ba0f49c0455d24a06d5714776d53e2ac7127052449bddbd1f9208a8633d8f`.

## AA. Integrated mixed R5 witness

The `T=2,E=4` private route produced NONE 6, ALL_TASKS_COMPLETED 1, and TIME_LIMIT 1. Expected/observed terminal keys were 2/2 exact; actor backward/step were `[4,4,0]/[4,4,0]`; critic backward/step `1/1`; ValueNorm update `1`; S10 `1`. Evidence digest: `1269abdf720f83bb52e9078958e2825a4dcaa8cc97503b9df2e5c15866ff68a8`.

## AB. Integrated terminal-missing fail-closed witness

A fresh mixed route first produced canonical exact keys. Test-only corruption removed `(1,0,3)` from the live collector. The adapter stopped with `TERMINAL_EVIDENCE_MISSING` before S0 and before any learner mutation; the route was not poisoned because no irreversible operation began.

## AC. Backward-compatibility regression

The terminal-rich controlled R5 suite passed after the change, retaining exact keys `[(0,0,10),(1,0,11),(2,1,12)]`, missing/wrong terminal failures, one successful S0–S10 transaction, and its poison/fault matrix. This is the previous terminal contract plus valid nonterminal support.

## AD. Static/private/public guards

Passing guards/results:

- R1 authority/ownership/fingerprint;
- R1 permits/ordering/static public guards;
- R1 update plans/factor;
- R5 static private/public and full transaction;
- R5I real-shape binding;
- final `py_compile` of all changed production/test files.

The R5 static audit retained one backward executor, one actor-step executor, one critic-step executor, one live-ValueNorm executor, scheduler steps 0, private exports 0, and public activation 0. A legacy standalone R5I-RE2 observability test still refers to removed historical `_scoped_attempt3_progress_observers_v1` while production exposes `_scoped_attempt4_progress_observers_v1`; it failed before exercising this contract and was not edited or used as the required authority guard.

## AE. Exact execution counts

Phase B2-T4-NR Python invocations: 16 total — 14 passed, 2 diagnostic/development failures. The failures were (a) the first integrated all-NONE run exposing the residual S7 nonempty guard, and (b) the unrelated stale attempt3 observer test named above.

Successful dedicated NR suite:

- source-faithful integrated runs: 3 (all-NONE positive, mixed positive, terminal-missing negative);
- all-NONE positive cases: 2 (pure matrix plus integrated);
- mixed positive cases: 3 (two pure matrix plus integrated);
- negative fail-closed cases: 10 (eight reconciliation matrix, missing final bootstrap, integrated missing terminal);
- unexpected negative passes: 0; missing-terminal false accepts: 0.

All phase attempts, including regressions and the diagnostic S7 discovery:

- source-faithful synthetic route constructions/resets/steps: `4/4/8`;
- controlled actor backward/optimizer.step: `90/90` total;
- controlled critic backward/optimizer.step: `10/10` total;
- controlled ValueNorm.update: `12` total;
- real Isaac environments, AppLauncher lifetimes, formal B2-T4 learners: `0/0/0`;
- formal B2-T4 updates: 0; tx001: NOT STARTED;
- checkpoint I/O, public activation, evaluation/playback: `0/0/0`.

The controlled mutation totals include two terminal-rich R5 regression invocations (33/33 actor, 3/3 critic, 4 ValueNorm each), the first S7 diagnostic all-NONE run (8/8, 1/1, 1), the successful all-NONE plus mixed witnesses (16/16, 2/2, 2), and the zero-DVM regression (0/0, 1/1, 1). They are not formal normal-horizon B2-T4 training updates.

## AF. Retained nonclaims

This phase does not establish a B2-T4 retry, 160-update stability, training quality, convergence, checkpoint continuation, B2-R6, public learned-policy readiness, or paper-scale training. It used no AppLauncher, real Isaac environment, checkpoint weights, playback, or public activation.

## AG. Final classification

`PHASE-B2-T4-NR-NONTERMINAL-ROLLOUT-COMPLETENESS-CONTRACT-QUALIFIED-AWAITING-GPT-REVIEW`

### Primary contract table

| Reason/evidence pattern | Expected terminal keys | Observed terminal keys | Expected result | Actual result |
|---|---:|---:|---|---|
| all NONE | 0 | 0 | PASS | PASS |
| all NONE + stale key | 0 | 1 | STOP | `TERMINAL_EVIDENCE_UNEXPECTED` |
| TIME_LIMIT exact | 1 | 1 exact | PASS | PASS |
| TIME_LIMIT missing | 1 | 0 | STOP | `TERMINAL_EVIDENCE_MISSING` |
| TIME_LIMIT wrong generation | 1 | 1 wrong | STOP | `TERMINAL_GENERATION_MISMATCH` |
| ALL_TASKS_COMPLETED exact | 1 | 1 exact | PASS | PASS |
| NO_FEASIBLE_TASKS_REMAIN exact | 1 | 1 exact | PASS | PASS |
| NONE + TIME_LIMIT mixed | terminal rows only | exact | PASS | PASS |
| NONE + completion mixed | terminal rows only | exact | PASS | PASS |
| mixed + missing terminal | N | N-1 | STOP | `TERMINAL_EVIDENCE_MISSING` |
| duplicate terminal evidence | N | duplicate | STOP | `TERMINAL_EVIDENCE_DUPLICATE` |
| all NONE + final bootstrap missing | 0 | 0 | STOP | `ROLLOUT_INCOMPLETE` |
| terminal stale previous generation | 1 | 1 stale | STOP | `TERMINAL_GENERATION_MISMATCH` |
| extra evidence for NONE env | N | N+1 | STOP | `TERMINAL_EVIDENCE_UNEXPECTED` |

## AH. GPT-review handoff

B2-T4-NR is COMPLETE / AWAITING GPT REVIEW. Rollout completeness is decoupled from terminal presence; exact conditional terminal-evidence matching is enforced; all-NONE and mixed integrated routes pass; terminal missing/extra/duplicate/generation failures remain closed. B2-T4 remains historically stopped. A fresh B2-T4 retry is NOT AUTHORIZED. Stop here and await independent review.
