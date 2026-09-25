# Lifecycle-aware Dynamic MRTA — Task Progress

Updated: 2026-09-12

## Current status

```text
B2-R0 through B2-R7: GPT REVIEW PASS / CLOSED
B2-T0 through B2-T3: GPT REVIEW PASS / CLOSED

B2-T4:
  STOPPED AT MANDATORY PREFLIGHT
  PHASE-B2-T4-STOP-NONTERMINAL-BOOTSTRAP-NOT-QUALIFIED
  AWAITING INDEPENDENT GPT REVIEW / NEW DESIGN AUTHORIZATION

zero-DVM actor behavior: PURE FULL-TRANSACTION QUALIFIED
all-zero-decision transaction: PURE FULL-TRANSACTION QUALIFIED
lower-level all-NONE event-return bootstrap: PURE QUALIFIED
current real-Isaac adapter + R5 nonterminal integration: NOT QUALIFIED

normal-horizon learned updates: 0 / 160
bridges: 0 / 159
CUDA/CUBLAS readiness probes: 0 (not reached)
formal workers / AppLauncher / environments / learners: 0 / 0 / 0 / 0
physical environment steps / learner mutations: 0 / 0
production semantic modifications: 0

checkpoint continuation: NOT ESTABLISHED
long / paper-scale training: NOT AUTHORIZED
B2-R6: NOT AUTHORIZED
public learned-policy route: DORMANT / BLOCKED
```

Classification:
`PHASE-B2-T4-STOP-NONTERMINAL-BOOTSTRAP-NOT-QUALIFIED`

## Latest phase result

Phase B2-T4 was authorized only for a 160-transaction, `T=2`, normal-horizon
learned-training integration qualification. Its mandatory pre-AppLauncher
preflight exposed a contract gap and stopped before the intended formal worker.

The low-level event-return buffer correctly handled a controlled `T/E=2/3`
rollout with all six termination reasons `NONE`: it used the supplied current
next-state critic values as the final bootstrap, produced finite `[2,3,1]`
nonaliased returns, invoked event returns once, and used neither the timeout
sidecar nor stock HARL `compute_returns`.

The current reviewed real-Isaac adapter nevertheless requires a nonempty
`route.collector.consumed_terminal_keys` ledger before it evaluates the final
critic value. The R5 S0 rollout validator independently requires `not keys` to
be false. An ordinary normal-horizon T=2 continuation rollout legitimately has
no terminal row and no terminal key. It is therefore rejected before S0 with:

```text
STOP — B2-R5I REAL_EVIDENCE_BINDING: real terminal learner ledger is empty
```

Allowing that valid nonterminal state requires a production contract/semantic
reconciliation, which B2-T4 explicitly forbade. The phase therefore used the
specified stop classification and did not perform the CUDA/CUBLAS readiness
probe, construct AppLauncher/environment/learner, start tx001, or mutate learner
state.

## Zero-DVM result

A separate controlled CPU full R5 transaction qualified the zero-decision
learner path. With all three actor DVM and active populations empty, expected
and observed actor backward/optimizer-step counts were `[0,0,0]`; all actor
parameters and optimizer states remained unchanged; factor stayed identity.
Critic backward/step and ValueNorm update each executed once, and
S7/S8/S9/S10 reached `1/1/1/1`. Thus the B2-T4 blocker is not zero-DVM actor
semantics.

## Preflight evidence

The approved interpreter and relevant `py_compile` passed. Reviewed production
and installed HARL identities remained exact. Row geometry passed; ValueNorm
passed 53 assertions; CPU CG classification passed; LD passed 13/13; T2/T3
observer pure nonmutation passed; I3B passed 16/16; I5B passed 14/14; and
static/private/public guards passed with public activation references 0.

The source identities most directly responsible for the STOP are:

```text
assignment_event_training_real_isaac_adapter.py:
  bff37075343795703b3ad4c7f7d27727278fd23e095e81d2de6b62a94821560e
assignment_event_training_full_transaction.py:
  ec42cb68db274f42144489f4e8ef199311c557016c4859475057c1deed417c35
```

## Exact B2-T4 execution counts

```text
CUDA/CUBLAS readiness probes: 0
formal mutation-bearing workers: 0
pre-mutation harness workers: 0
pure/static Python invocations: 18 (15 passed, 3 diagnostic failures)
AppLauncher / environment / reset / learner: 0 / 0 / 0 / 0
successful learner updates / unique update IDs / rollout batches: 0 / 0 / 0
physical environment steps / bridges: 0 / 0
actor backward / optimizer.step: 0 / 0 formal
critic backward / optimizer.step / ValueNorm.update: 0 / 0 / 0 formal
event returns / stock compute_returns: 0 / 0 formal
S7 / S8 / S9 / S10: 0 / 0 / 0 / 0 formal
checkpoint weight I/O / public activation / evaluation-playback: 0 / 0 / 0
tx001 / tx161 started: 0 / 0
production semantic modifications: 0
post-mutation retries: 0
```

The three failed pure/static invocations were test-side diagnostic issues only:
two fixture-authoring corrections in the new T4 preflight and one inline CG
import-path correction. They occurred without AppLauncher, environment, formal
learner, or production changes and are not retried formal workers.

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
`202609/20260912/TASK_PROGRESS_ARCHIVE_BEFORE_B2_T4_STOP_HANDOFF_20260912.md`:
10,146 bytes, SHA-256
`e193df04df67d4cf71b6c65225e7ef9d184fd5250d285e03c93ac19934a7add7`.

No `git add`, commit, push, reset, checkout, or clean operation occurred.

## Evidence artifacts

- `202609/20260912/PHASE_B2_T4_NORMAL_HORIZON_LEARNED_TRAINING_INTEGRATION_QUALIFICATION_REPORT.md`
- `202609/20260912/b2_t4_artifacts/zero_dvm_pure_qualification.json`
- `202609/20260912/b2_t4_artifacts/nonterminal_bootstrap_pure_qualification.json`
- `202609/20260912/b2_t4_artifacts/integration_gap.json`
- `202609/20260912/b2_t4_artifacts/source_identities.json`
- `202609/20260912/b2_t4_artifacts/final_result.json`
- `202609/20260912/TASK_PROGRESS_ARCHIVE_BEFORE_B2_T4_STOP_HANDOFF_20260912.md`

## Next gate

Await independent GPT review. A new explicit design/reconciliation authority is
required before changing the R5 nonterminal rollout-completeness contract. Do
not start tx001/tx161, B2-R6, checkpoint I/O, public activation,
evaluation/playback, or long/paper-scale training under the B2-T4 authority.
