# Lifecycle-aware Dynamic MRTA — Task Progress

Updated: 2026-09-12

## Current status

```text
B2-R0 through B2-R7: GPT REVIEW PASS / CLOSED
B2-T0 through B2-T3: GPT REVIEW PASS / CLOSED

B2-T4:
  STOPPED / HISTORICAL / NOT COMPLETE
  PHASE-B2-T4-STOP-NONTERMINAL-BOOTSTRAP-NOT-QUALIFIED

B2-T4-NR:
  NONTERMINAL ROLLOUT-COMPLETENESS CONTRACT RECONCILIATION COMPLETE
  AWAITING INDEPENDENT GPT REVIEW

zero-DVM actor behavior: PURE FULL-TRANSACTION QUALIFIED
all-zero-decision transaction: PURE FULL-TRANSACTION QUALIFIED
lower-level all-NONE event-return bootstrap: PURE QUALIFIED
rollout completeness: DECOUPLED FROM TERMINAL PRESENCE / AWAITING GPT REVIEW
terminal historical evidence: EXACT CONDITIONAL MATCHING / AWAITING GPT REVIEW
all-NONE integrated private route: PASS / AWAITING GPT REVIEW
mixed terminal/nonterminal private route: PASS / AWAITING GPT REVIEW
terminal fail-closed regression: PASS / AWAITING GPT REVIEW

normal-horizon learned updates: 0 / 160
bridges: 0 / 159
CUDA/CUBLAS readiness probes: 0 (not reached)
formal workers / AppLauncher / environments / learners: 0 / 0 / 0 / 0
physical environment steps / learner mutations: 0 / 0
production semantic modifications: 2 files, validation contract only

checkpoint continuation: NOT ESTABLISHED
long / paper-scale training: NOT AUTHORIZED
B2-R6: NOT AUTHORIZED
public learned-policy route: DORMANT / BLOCKED
B2-T4 retry: NOT AUTHORIZED
```

Classification:
`PHASE-B2-T4-NR-NONTERMINAL-ROLLOUT-COMPLETENESS-CONTRACT-QUALIFIED-AWAITING-GPT-REVIEW`

## Latest phase result

Phase B2-T4-NR implemented the narrowly authorized validation-contract repair.
Rollout completeness remains established by all T actor/critic slots, immutable
rollout identity, one finite final current-next critic value, and one event-return
construction. Separately, expected terminal keys are derived from the exact
sealed pre-step decision identities only for non-NONE reason rows and reconciled
exactly with the consumed learner ledger. Empty/empty is valid; missing, extra,
duplicate, wrong-generation, and wrong-identity evidence remain fail-closed.

A source-faithful private CPU `T=2,E=2` all-NONE rollout produced zero expected
and observed terminal keys, used current-next bootstrap, and reached R5 S10. A
`T=2,E=4` mixed rollout produced six NONE, one TIME_LIMIT, and one
ALL_TASKS_COMPLETED row, matched two expected/observed terminal keys, and reached
S10. Removing one real terminal key stopped before S0 and before mutation with
`STOP — B2-R TERMINAL_EVIDENCE_MISSING`.

The original B2-T4 preflight STOP remains historical and unchanged. No
AppLauncher/real Isaac environment, formal normal-horizon update, tx001,
checkpoint I/O, public activation, playback, or long training was started.

## Zero-DVM result

A separate controlled CPU full R5 transaction qualified the zero-decision
learner path. With all three actor DVM and active populations empty, expected
and observed actor backward/optimizer-step counts were `[0,0,0]`; all actor
parameters and optimizer states remained unchanged; factor stayed identity.
Critic backward/step and ValueNorm update each executed once, and
S7/S8/S9/S10 reached `1/1/1/1`. Thus the B2-T4 blocker is not zero-DVM actor
semantics.

## Preflight evidence

The approved interpreter and final `py_compile` passed. The dedicated B2-T4-NR
matrix passed 14/14 contractual cases, and all three source-faithful integrated
witnesses passed. I5b passed 14/14; the terminal-rich R5 suite passed; zero-DVM
passed; R1 authority/ownership, permits/ordering/static public, update-plan/factor,
and R5I real-shape guards passed. Public activation remained 0.

The source identities most directly responsible for the STOP are:

```text
assignment_event_training_full_transaction.py:
  a6b8f4d283d5eaf14a4a7d686e1f3b6424837552d673909ea5808b2bf7d057de
assignment_event_training_real_isaac_adapter.py:
  b85034d7436de4a79c37de0f2e40a09200dfbca225994c0cae2c8f6bcd491014
```

## Exact B2-T4-NR execution counts

```text
CUDA/CUBLAS readiness probes: 0
formal mutation-bearing workers: 0
pre-mutation harness workers: 0
Python invocations: 16 (14 passed, 2 diagnostic/development failures)
AppLauncher / environment / reset / learner: 0 / 0 / 0 / 0
successful learner updates / unique update IDs / rollout batches: 0 / 0 / 0
physical environment steps / bridges: 0 / 0
actor backward / optimizer.step: 0 / 0 formal
critic backward / optimizer.step / ValueNorm.update: 0 / 0 / 0 formal
event returns / stock compute_returns: 0 / 0 formal
S7 / S8 / S9 / S10: 0 / 0 / 0 / 0 formal
checkpoint weight I/O / public activation / evaluation-playback: 0 / 0 / 0
tx001 / tx161 started: 0 / 0
production semantic modifications: 2 validation-contract files
post-mutation retries: 0

successful dedicated source-faithful integrated runs: 3
dedicated all-NONE positive / mixed positive / fail-closed negative: 2 / 3 / 10
unexpected negative passes / missing-terminal false accepts: 0 / 0
synthetic CPU route constructions / resets / steps across attempts: 4 / 4 / 8
controlled actor backward / optimizer.step across all phase tests: 90 / 90
controlled critic backward / optimizer.step across all phase tests: 10 / 10
controlled ValueNorm.update across all phase tests: 12
```

The first failed B2-T4-NR invocation was the diagnostic all-NONE integration
that exposed the downstream S7 copy of the nonempty-ledger assumption; it was
reconciled within the authorized full-transaction validation file. The other
failure was an unrelated legacy R5I-RE2 test referring to removed historical
`_scoped_attempt3_progress_observers_v1`; it failed before this contract was
exercised and was not changed. Neither was a formal B2-T4 worker.

## Retained earlier authority and history

The B2-T3 handoff is now user-reviewed and closed. T3 separated rollout `T=2`
from the production 30-second/configured max-300 horizon and produced a
controlled task-completion witness. T3-C's five fresh-process
`CUBLAS_STATUS_NOT_INITIALIZED` failures remain historical and do not become a
B2-T4 failure because B2-T4 stopped before its one permitted readiness probe.

B2-T2's 300-update short-horizon learner/observer evidence, B2-T1, B2-T0,
B2-T0-RE1, B2-T0-LD, B2-R5I historical poisoned attempts 1/2/3, and B2-T0
run03 remain preserved. Run03 tx2 actor-2's exact historical cause remains
`UNRESOLVED FROM EXISTING DURABLE ARTIFACTS`.

No earlier bounded evidence is reclassified as normal-horizon learned-training
integration, training quality, convergence, checkpoint continuation, or public
readiness.

## Repository preservation

Repository authority remains `main` at
`b71d85a32f51be6ada324f870813a56bb45dd396`, equal to `origin/main` and the
merge-base. The 359 staged monthly-migration paths remain untouched with
staged-index SHA-256
`a40169043c3bfffd481a7ed1bddf3e52663d61379bedfd2610781457d11f947c` and
path-set SHA-256
`0f2b8f7b52148e39196cbeb40fd9f4edd94fb762b6daf8be6279a116b80a39ab`.

The byte-exact pre-rewrite archive is
`202609/20260912/TASK_PROGRESS_ARCHIVE_BEFORE_B2_T4_NR_HANDOFF_20260912.md`:
7,129 bytes, SHA-256
`ce423c43084a1234902049ccb5b12d5ab7fd97461d62a86dcdd0615cc74056d5`.

No `git add`, commit, push, reset, checkout, or clean operation occurred.

## Evidence artifacts

- `202609/20260912/PHASE_B2_T4_NORMAL_HORIZON_LEARNED_TRAINING_INTEGRATION_QUALIFICATION_REPORT.md`
- `202609/20260912/PHASE_B2_T4_NR_NONTERMINAL_ROLLOUT_COMPLETENESS_CONTRACT_RECONCILIATION_REPORT.md`
- `202609/20260912/b2_t4_nr_artifacts/source_contract_audit.json`
- `202609/20260912/b2_t4_nr_artifacts/terminal_expectation_matrix.json`
- `202609/20260912/b2_t4_nr_artifacts/all_none_positive.json`
- `202609/20260912/b2_t4_nr_artifacts/terminal_negative_cases.json`
- `202609/20260912/b2_t4_nr_artifacts/mixed_rollout_cases.json`
- `202609/20260912/b2_t4_nr_artifacts/integrated_all_none_r5.json`
- `202609/20260912/b2_t4_nr_artifacts/integrated_mixed_r5.json`
- `202609/20260912/b2_t4_nr_artifacts/backward_compatibility.json`
- `202609/20260912/b2_t4_nr_artifacts/final_result.json`
- `202609/20260912/TASK_PROGRESS_ARCHIVE_BEFORE_B2_T4_NR_HANDOFF_20260912.md`

## Next gate

Await independent GPT review of B2-T4-NR. A fresh explicit authorization is
required before retrying B2-T4. Do not start tx001/tx161, B2-R6, checkpoint I/O,
public activation, evaluation/playback, or long/paper-scale training.
