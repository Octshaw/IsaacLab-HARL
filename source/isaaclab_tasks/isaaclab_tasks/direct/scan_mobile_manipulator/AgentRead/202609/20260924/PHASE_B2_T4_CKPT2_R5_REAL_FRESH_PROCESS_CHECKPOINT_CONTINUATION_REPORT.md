# Phase B2-T4-CKPT2-R5 Real Fresh-Process Checkpoint Continuation Report

Classification:

`PHASE-B2-T4-CKPT2-R5-STOP-PROCESS-A-UPDATE`

Run identity: `b2-t4-ckpt2-r5-20260924-real01-9a6c4f17`

This was the single authorized R5 attempt. It stopped in Process A tx001 at the S5 pre-mutation observation boundary. No actor backward, actor optimizer step, critic mutation, or ValueNorm mutation occurred; the route was not poisoned; Process B was not launched; no checkpoint generation was published. Retry is not authorized.

## A. Historical preservation

CKPT2/R1/R2/R3/R4 harnesses, reports, and evidence roots were read-only verified before Process A. All five preservation receipts are `PASS`. R4 remains historical as `GPT REVIEW STOP CONFIRMED / TEST-SIDE FIXED PREDICATE / NOT LEARNER DEFECT / NOT POISONED / NO RETRY`.

CKPT1 production hashes remained:

- `assignment_optimization_checkpoint.py`: `b0fec513bad87af961450345f1ee5849cca04c4da5429a483af5f31f8a6e76b9`
- `assignment_harl_training.py`: `31295d60a01d11657b924e6d8332f160b278eeeb236109b59409bfbf55f7e787`

Installed HARL preservation also passed. No historical artifact was modified.

## B. R4 fixed actor-count predicate review

The pure qualification reproduced the R4 error using the real production plan constructor. A valid frozen plan produced `(5,5,10)` and the historical fixed predicate `(5,5,5)` rejected it. The fixed uniform predicate was removed from the R5 ledger contract. This finding remains valid despite the later R5 runtime STOP.

## C. Authoritative actor plan count contract

The expected-count authority is:

`assignment_event_training_plans.py:B2RActorUpdatePlanV1.expected_backward_count_by_actor`

and:

`assignment_event_training_plans.py:B2RActorUpdatePlanV1.expected_optimizer_step_count_by_actor`

`build_actor_update_plan_v1` derives these values by counting each actor's nonempty frozen minibatches. `_PreMutationObservedActorInputsV1` in `assignment_event_training_real_isaac_adapter.py` exposes them after S3 plan freeze and before the first actor mutation. Observed counts come from `B2R5IRealTransactionEvidenceV1.exact_execution_counts` and are valid only after a returned transaction.

Config alone is not the authority. Zero-DVM/forced-only actors have expected backward/step counts of zero and must not mutate.

## D. Historical dynamic plan consistency

Read-only B2-T0-RE1 evidence passed the same plan-derived contract:

| Tx | Actor order | Frozen plan expected | Actor progress observed | Adam delta | Result |
|---|---|---|---|---|---|
| tx001 | `(1,2,0)` | `(5,5,5)` | `(5,5,5)` | `(5,5,5)` | PASS |
| tx002 | `(0,2,1)` | `(5,5,10)` | `(5,5,10)` | `(5,5,10)` | PASS |
| tx003 | `(1,0,2)` | `(10,5,5)` | `(10,5,5)` | `(10,5,5)` | PASS |

The historical actor Adam progression was `(0,0,0) -> (5,5,5) -> (10,10,15) -> (20,15,20)`. Each delta equals the corresponding frozen plan; no tuple lookup is part of the contract.

## E. Pre-runtime qualification

- CKPT1 focused suite: 6/6 PASS.
- CKPT1 negative matrix: 25/25 expected rejection.
- Actor-plan positive matrix: 5/5 PASS, including dynamic nonuniform, one-zero-actor, and all-zero-actor cases.
- Actor-count negative matrix: 12/12 expected STOP; unexpected PASS count zero.
- Historical dynamic-plan and Adam consistency: PASS.
- ONE_TO_ONE_BOUND, CASE C, returned `update_id`, and event-return authority: preserved.
- Pure/runtime OS-process isolation, LR-before-fingerprint ordering, and A-to-B gate: preserved.
- R5 harness frozen before A at SHA-256 `e6546bdae034a7abb18d1ad70e16a4e2f5eab897251ba4561acf2e5d604fd039`.

## F. Process-A environment / learner

Process A PID `23952` used `C:\isaacenvs\isaac45_harl\python.exe` and real CUDA device `cuda:0`. Real package identity, Gym registration, environment creation, fresh learner creation, and CUDA warm-up passed. The environment and SimulationApp closed cleanly. PID `23952` is inactive.

## G. Process-A TX001-TX003 actor plans

tx001 reached S3 plan freeze and S5 actor-sequence entry. The observer payload already contained frozen expected backward and step counts `((0,5),(1,5),(2,5))` with all mutation counters at zero.

The direct observer payload correctly carried `resolved_config` as a frozen `B2RResolvedConfigV1` dataclass. The R5 harness callback incorrectly accepted that value only when it was a `Mapping`; it therefore fell back to `epoch_count=0` and raised `PRE-MUTATION-PLAN-POLICY`. This is a test-side receipt-binding defect, not evidence of a learner defect or actor-count mismatch.

| Tx | Actor order | Frozen expected actor steps | Observed actor steps | Adam delta | Exact match | Result |
|---|---|---|---|---|---:|---|
| A tx001 | available in observer but canonical receipt not committed | `(5,5,5)` | no returned transaction; mutation counters `(0,0,0)` | `(0,0,0)` | N/A | STOP before mutation |
| A tx002 | NOT STARTED | N/A | N/A | N/A | N/A | NOT STARTED |
| A tx003 | NOT STARTED | N/A | N/A | N/A | N/A | NOT STARTED |
| B tx004 | NOT STARTED | N/A | N/A | N/A | N/A | NOT STARTED |
| B tx005 | NOT STARTED | N/A | N/A | N/A | N/A | NOT STARTED |
| B tx006 | NOT STARTED | N/A | N/A | N/A | N/A | NOT STARTED |

No transaction ledger row was appended because tx001 did not return.

## H. Checkpoint save

Not reached. Save count `0`, generation publication count `0`, and load count `0`. No `latest.json` or checkpoint generation exists under the R5 checkpoint root.

## I. Process-A semantic success / A-to-B gate

No Process-A success receipt was written. Parent adjudication correctly denied B because completed transaction count, quiescence receipt, checkpoint save, generation, manifest, latest pointer, and checkpoint validation were absent. This is `PHASE-B2-T4-CKPT2-R5-STOP-PROCESS-A-SEMANTIC-GATE` at the parent surface; the narrower causal classification is `PHASE-B2-T4-CKPT2-R5-STOP-PROCESS-A-UPDATE`.

## J. Process-B strict load

Not reached; Process B was not launched.

## K. CUDA device restoration

Not established because no checkpoint load occurred.

## L. Cross-process state equality

Not established because Process B was not launched.

## M. Process-B TX004-TX006 actor plans

Not started. tx007 was also not started.

## N. Optimizer continuity

Not established. The R5 failure occurred before any optimizer mutation and before checkpoint save/load.

## O. ValueNorm continuity

Not established. ValueNorm update count before failure was zero.

## P. Progression / LR continuity

Not established across a checkpoint. The pre-existing LR-before-fingerprint contract passed pure qualification, but no completed R5 update advanced checkpoint progression.

## Q. Process quiescence

- Parent PID `29060`: inactive.
- Pure qualification child: exited before A.
- Process A PID `23952`: inactive.
- Process B: never launched.
- Matching R5 Python worker count: zero.
- Environment close: PASS.
- SimulationApp close invoked: true.
- Route poisoned: false.
- Partial update: false.
- Retry count: zero.

## R. Final checkpoint-continuation verdict

R5 is `STOP-PROCESS-A-UPDATE` and the single attempt is consumed. The dynamic actor-plan authority is established in pure and historical evidence, but real 3+3 checkpoint continuation is not established. The runtime failure was caused by the new R5 test harness's pre-mutation metadata lookup before learner mutation; it does not invalidate the production frozen-plan semantics and does not establish a learner defect.

| State | A pre-save | B post-load | Equal | B after tx004 | Continuity |
|---|---|---|---:|---|---:|
| actor weights | not reached | not launched | N/A | not started | NOT ESTABLISHED |
| actor Adam steps/moments | not reached | not launched | N/A | not started | NOT ESTABLISHED |
| critic weights | not reached | not launched | N/A | not started | NOT ESTABLISHED |
| critic Adam steps/moments | not reached | not launched | N/A | not started | NOT ESTABLISHED |
| ValueNorm | not reached | not launched | N/A | not started | NOT ESTABLISHED |
| progression | not reached | not launched | N/A | not started | NOT ESTABLISHED |
| LR schedule position | not reached | not launched | N/A | not started | NOT ESTABLISHED |
| semantic config | not reached | not launched | N/A | not started | NOT ESTABLISHED |

No R15, evaluation, playback, paper-scale training, public learned-policy activation, git add, commit, or push occurred. No second R5 attempt is authorized or launched. The next gate is independent GPT review of this R5 STOP evidence.
