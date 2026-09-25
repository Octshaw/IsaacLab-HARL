# Lifecycle-aware Dynamic MRTA — Task Progress

Updated: 2026-09-14

## Current status

```text
B2-R0 through B2-R7: GPT REVIEW PASS / CLOSED
B2-T0 through B2-T3: GPT REVIEW PASS / CLOSED

B2-T4 original attempt:
  STOPPED / HISTORICAL / NOT COMPLETE
  PHASE-B2-T4-STOP-NONTERMINAL-BOOTSTRAP-NOT-QUALIFIED

B2-T4-NR: GPT REVIEW PASS / CLOSED

B2-T4-RE1:
  STOPPED / HISTORICAL / POISONED / NOT COMPLETE
  PHASE-B2-T4-RE1-STOP-TX001-EVIDENCE-LEDGER-SERIALIZATION-NOT-COMPLETE

B2-T4-SR: GPT REVIEW PASS / CLOSED

B2-T4-RE2:
  STOPPED / HISTORICAL / POISONED / NOT COMPLETE
  PHASE-B2-T4-RE2-STOP-TX2-BOUNDED-SMOKE-FAILURE-NOT-COMPLETE

B2-T4-ZD:
  COMPLETE / AWAITING GPT REVIEW
  PHASE-B2-T4-ZD-CONTINUATION-ONLY-ZERO-DVM-REAL-ADAPTER-CONTRACT-QUALIFIED-AWAITING-GPT-REVIEW

continuation-only real adapter: QUALIFIED / AWAITING GPT REVIEW
all-zero-DVM actor transaction: PASS / AWAITING GPT REVIEW
actor fail-closed: PRESERVED / AWAITING GPT REVIEW
terminal/NR semantics: UNCHANGED / PASS

B2-T4-RE3: NOT AUTHORIZED
checkpoint continuation: NOT ESTABLISHED
long / paper-scale training: NOT AUTHORIZED
B2-R6 continuation work: NOT AUTHORIZED
public learned-policy route: DORMANT / BLOCKED
```

## Latest phase result

B2-T4-ZD reconciled the narrow real-adapter admission mismatch exposed by RE2 tx002. The old adapter required at least one active-and-DVM actor row even though the reviewed R5 transaction already supports a valid all-zero-DVM actor sequence.

The new contract requires exact expected/observed actor-evidence row identity equality per actor and batch-wide. Identity is `(update_id, actor_id, slot, env_id, episode_generation, transition_generation)`. Empty/empty is valid; missing, unexpected, duplicate, wrong-update, and wrong-row evidence remain fail-closed. DVM, active mask, lifecycle, actor PPO, factor, critic, ValueNorm, GAE/event-return, terminal, checkpoint, and public-route semantics were not changed.

Three source-faithful CPU positives passed:

- actor-rich: expected/observed `[2,2,2]`, actor backward/step `[2,2,2]` / `[2,2,2]`, critic `1/1`, ValueNorm `1`, S10;
- partial zero-DVM: expected/observed `[2,0,2]`, actor backward/step `[2,0,2]` / `[2,0,2]`, actor1 parameter/optimizer/Adam unchanged and factor identity, critic `1/1`, ValueNorm `1`, S10;
- all-zero-DVM continuation: expected/observed `[0,0,0]`, actor backward/step `[0,0,0]` / `[0,0,0]`, all actor Adam counters unchanged, full factor identity, critic `1/1`, critic Adam +1, ValueNorm `1`, event returns `1`, stock `compute_returns=0`, S7–S10.

Ten negative cases all stopped before prohibited mutation where applicable: missing behavior logprob, missing action/proposal, missing observation, missing row, unexpected row, equal-count wrong identity, continuation carrying fresh policy evidence, duplicate row, wrong update, and wrong actor/slot identity. Unexpected negative passes were zero.

## Historical RE2 remains retained

RE2 is not reclassified. tx001 remains one production-S10 and ledger-qualified update. tx002 remains a valid physical continuation-only rollout with 12 continuation rows, zero policy calls, zero DVM rows, zero forced-noop rows, and zero collection-time learner mutation. Because tx001 had already mutated the persistent learner, RE2 retains `partial_update=true`, `route_poisoned=true`, and retry count zero.

ZD verified the immutable tx002 evidence hashes and replayed its population/lifecycle shape through the source-faithful private adapter to S0–S10 without rerunning Isaac. This new replay repairs a prerequisite only; it does not retroactively complete RE2.

## Qualification and regression evidence

```text
final clean pure/static invocations: 9
ZD source-faithful adapter attempts / successful transactions: 8 / 4
NR source-faithful integrated runs: 3
RE2 tx002 retained-evidence replay: 1 PASS
primary positives: actor-rich 1, partial-zero 1, all-zero 1
negative fail-closed cases / unexpected passes: 10 / 0
primary positive actor backward / step: 10 / 10
primary positive critic backward / step / ValueNorm.update: 3 / 3 / 3
NR: 5 / 5 PASS, terminal matrix 14 / 14
SR ZD-baseline replay: 7 / 7 positive, 12 / 12 negative, ledger/bookkeeping PASS
I5b: 14 / 14 PASS
LD: 13 / 13 PASS
R5 controlled full transaction and prior zero-DVM segment: PASS
R5I shape and R1 authority/permit/order/plan/factor/static guards: PASS
AppLauncher / real Isaac / formal normal-horizon updates: 0 / 0 / 0
checkpoint I/O / public activation / B2-T4-RE3: 0 / 0 / 0
git add / commit / push: 0 / 0 / 0
```

The SR serializer source remained unchanged. Its historical fixed-production-hash runner correctly rejected the authorized ZD training-source hashes; a full replay bound to those new hashes then passed all serializer, retained RE1, ledger, bookkeeping, nonmutation, and static checks. Historical SR authority was not rewritten.

## Production scope

Exactly two production semantic files changed:

```text
assignment_event_training_full_transaction.py
  a45db23b863c51334b15205b3c50fa5997ab8f5e4a32f8c4a801242365b583d7
assignment_event_training_real_isaac_adapter.py
  57419d52caa77160609f77b289979ed6785fc645eab1b17320e9cbda1e9500ac
```

The first owns the canonical actor-evidence reconciler and S0 digest check. The second derives and binds canonical expected/observed rows and removes only the obsolete nonempty-population guard. Test/helper changes only support qualification and the new required evidence fields.

## Repository preservation

Repository authority remains branch `main` at `b71d85a32f51be6ada324f870813a56bb45dd396`, equal to `origin/main` and the merge-base. The pre-existing 359 staged monthly-migration paths remain untouched, with staged-index SHA-256 `a40169043c3bfffd481a7ed1bddf3e52663d61379bedfd2610781457d11f947c` and monthly path-set SHA-256 `0f2b8f7b52148e39196cbeb40fd9f4edd94fb762b6daf8be6279a116b80a39ab`.

The byte-exact pre-rewrite archive is `202609/20260914/TASK_PROGRESS_ARCHIVE_BEFORE_B2_T4_ZD_HANDOFF_20260914.md`: 8,763 bytes, SHA-256 `aa8cd5e9ba99a690c078df41aa6fce414d765109e5aa049d4ad27b6e36e5eca5`.

No `git add`, commit, push, reset, checkout, or clean operation occurred.

## Primary evidence

- `202609/20260914/PHASE_B2_T4_ZD_CONTINUATION_ONLY_ZERO_DVM_REAL_ADAPTER_CONTRACT_RECONCILIATION_REPORT.md`
- `202609/20260914/b2_t4_zd_artifacts/actor_evidence_contract_audit.json`
- `202609/20260914/b2_t4_zd_artifacts/actor_population_matrix.json`
- `202609/20260914/b2_t4_zd_artifacts/actor_negative_cases.json`
- `202609/20260914/b2_t4_zd_artifacts/re2_tx002_zero_dvm_replay.json`
- `202609/20260914/b2_t4_zd_artifacts/partial_zero_dvm_full_transaction.json`
- `202609/20260914/b2_t4_zd_artifacts/all_zero_dvm_full_transaction.json`
- `202609/20260914/b2_t4_zd_artifacts/actor_rich_regression.json`
- `202609/20260914/b2_t4_zd_artifacts/production_source_identity.json`
- `202609/20260914/b2_t4_zd_artifacts/backward_compatibility.json`
- `202609/20260914/b2_t4_zd_artifacts/final_result.json`
- `202609/20260914/TASK_PROGRESS_ARCHIVE_BEFORE_B2_T4_ZD_HANDOFF_20260914.md`

## Next gate

Await independent GPT review of B2-T4-ZD. Do not start B2-T4-RE3, AppLauncher, a real Isaac run, B2-R6, checkpoint I/O, public activation, evaluation/playback, or long/paper-scale training.
