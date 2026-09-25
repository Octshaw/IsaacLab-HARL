# Phase B2-T4-RE6-R1 — W2I-bound normal-horizon learned-training integration

**Final classification: `PHASE-B2-T4-RE6-R1-STOP-INHERITED-POSTPROCESS-KEYERROR-AFTER-MUTATION`.** This was the sole fresh formal attempt. It reached 160 transaction-ledger rows and 320 physical transitions, but failed during success postprocessing after irreversible learner mutation. The worker receipt says `partial_update=true`, `route_poisoned=true`; no retry or learner reuse is permitted. The raw supervisor classification is the broader `PHASE-B2-T4-RE6-R1-STOP-FORMAL-WORKER-FAILURE`. [Raw final result](b2_t4_re6_r1_artifacts/final_result.json), [worker receipt](b2_t4_re6_r1_artifacts/formal_worker_receipt.json), and [narrow adjudication](b2_t4_re6_r1_artifacts/qualification_adjudication.json) are kept distinct.

## A. Repository authority

Branch `main`; HEAD/origin/main/merge-base `b71d85a32f51be6ada324f870813a56bb45dd396`. The pre-edit full porcelain was 9,711 lines (UTF-8/LF SHA-256 `3fd690129c05acbee217e24947a2dfb4cba15425419cbfa74c4a35ec9a623d08`). The pre-existing 359 staged paths and staged-index digest `a40169043c3bfffd481a7ed1bddf3e52663d61379bedfd2610781457d11f947c` were unchanged; monthly path-set baseline was `0f2b8f7b52148e39196cbeb40fd9f4edd94fb762b6daf8be6279a116b80a39ab`. No git add/commit/push. [Authority record](b2_t4_re6_r1_artifacts/repository_authority.json).

## B. Reviewed starting authority

B2-R0–R7, B2-T0–T3, NR/SR/ZD/EP-Q/PW/W2E/W2I remain user-asserted GPT REVIEW PASS / CLOSED. That authority enabled exactly this fresh attempt, not historical repair, checkpoint continuation, public activation, or long training.

## C. Historical RE5 preservation

RE5 remains GPT REVIEW STOP CONFIRMED / HISTORICAL / POISONED / NOT QUALIFIED. Its learner was not reused. The read-only W2I replay after this attempt confirmed the 14 protected RE5 artifacts remained byte-identical.

## D. Historical RE6 preservation

Historical RE6 remains a separate PRE-RUNTIME STOP for W2E helper identity, with no learner mutation and not poisoned. Its report and final-result hashes remained unchanged in the post-run W2I check.

## E. W2I reviewed identity authority

The user-provided review closes W2I and approves the exact selector hash and 15,089 bytes. The W2I binding manifest was checked against SHA-256 `3bddfb2b34b2544167267a76beb9bb3bda77d48f49bd23fa79878296c6cdc85b`.

## F. W2E selector identity gate

| Item | Expected SHA-256 | Actual SHA-256 | Gate |
|---|---|---|---|
| W2E selector | `8a4923200c4bee914985dc436e2ebf714c39578e5025fd419d9799b4a0f8abd0` | same | PASS |
| W2I binding | `3bddfb2b34b2544167267a76beb9bb3bda77d48f49bd23fa79878296c6cdc85b` | same | PASS |
| PW helper | `e1c5dd249a845efd188fadd841202133d1aa363f162398930199837157f2e76b` | same | PASS |

The unchanged offline runner and contract artifact also matched their reviewed digests. [Identity gate](b2_t4_re6_r1_artifacts/reviewed_w2e_identity_gate.json).

## G. Production source identities

Full transaction `a45db23b863c51334b15205b3c50fa5997ab8f5e4a32f8c4a801242365b583d7`, real adapter `57419d52caa77160609f77b289979ed6785fc645eab1b17320e9cbda1e9500ac`, and environment `f96f6b6e9a530cd0b438344a11dc67670559206f3521d641d776d4bd475c6363` matched. Production semantic edits: zero. The inherited RE3 static suite checked its additional B1/P2/decision dependencies. [Static authority](b2_t4_re6_r1_artifacts/static_authority.json).

## H. PW authority

Reviewed immutable PW helper matched its SHA. No old mutable progress path was found. Per-transaction and post-failure read-only campaign reconciliation found 41 critic and 4 actor/factor records per transaction, with zero missing, duplicate, order, digest, or temp-residue faults. This diagnostic cannot rescue failed Layer A. [PW campaign reconciliation](b2_t4_re6_r1_artifacts/pw_campaign_reconciliation.json).

## I. EP-Q authority

The reviewed EP-Q v2 helper was inherited unchanged. Layer B used subprocess wait, timeout, return code, original PID absence, and matching-worker emptiness; shutdown text was diagnostic only.

## J. RE6-R1 harness identity

The new test-side [harness](../../../../../../../../scripts/environments/test_assignment_phase_b2_t4_re6_r1_normal_horizon_learned_training_integration.py) SHA-256 was `858656975abef50adf6a143fe7f6bc68731756d2ad6378430acc6b9e3f3d049c` at freeze and launch. It source-derived frozen RE5 SHA-256 `4ae8e721e4dfbb42f53dd49bf91c002b502f7f2cf29757e2cf756bbe067ca2d8` into a distinct `20260920/b2_t4_re6_r1_artifacts` namespace. The inherited RE5 postprocessor contained a latent dictionary-key bug that the preflight did not exercise.

## K. RE5→RE6-R1 gate equivalence

| Gate | Historical RE5 | RE6-R1 | Source comparison |
|---|---|---|---|
| W1 | P2 cross-update ownership | same | unchanged |
| W2 | textual `task_claimed` | reviewed W2E-v2 `reconcile` | intentional replacement |
| W3/W4/W5/W6/W7 | RE3/RE1 witness gates | same | unchanged |
| NR/SR/ZD/PW | reviewed test-side contracts | same | unchanged |
| EP-Q Layer B | reviewed process predicates | same | unchanged |
| Layer A, poison, postprocessor | RE5-derived | same | **latent `_base_atomic_json` lookup failed** |

The pre-run [equivalence audit](b2_t4_re6_r1_artifacts/re5_re6_r1_gate_equivalence.json) passed its implemented checks. The formal failure shows that this was not sufficient end-to-end readiness; [the gap record](b2_t4_re6_r1_artifacts/preflight_contract_gap.json) explicitly retracts any full-qualification inference.

## L. Legacy W2 nonauthority

Fresh old W2 was `null`, with `authoritative_for_RE6_R1=false`. Its absence did not throw the inherited required-witness gate. [Legacy diagnostic](b2_t4_re6_r1_artifacts/legacy_w2_diagnostic.json).

## M. W2E-v2 sole authority

The reviewed selector's `reconcile` supplied the W2 result; no selector logic was duplicated. Fresh result: 29 candidates, 12 valid, deterministic first valid chain PASS. [Authority binding](b2_t4_re6_r1_artifacts/w2_authority_binding.json).

## N. W2E input-evidence sufficiency

The reviewed runner's `normalize` mapped transaction-indexed lifecycle steps and decisions, transaction ledger, and bridge ledger into the selector input. The copied historical ledger replay and fresh post-tx160 reconciliation both populated every required evidence class. [Normalization mapping](b2_t4_re6_r1_artifacts/re6_r1_w2e_normalization_mapping.json).

## O. NTFS/same-volume

The preflight recorded NTFS, temp/final same volume, and PW same-directory temp contract as PASS. [Filesystem precondition](b2_t4_re6_r1_artifacts/filesystem_precondition.json).

## P. Pre-runtime qualification

The implemented [39-gate matrix](b2_t4_re6_r1_artifacts/re6_r1_pre_runtime_39_gate_matrix.json) and [preflight summary](b2_t4_re6_r1_artifacts/preflight_summary.json) passed without AppLauncher. **Retrospective limit:** the Layer-A synthetic predicate omitted the task-required direct W2E/W2I digest fields, and the postprocessing success path was not replayed through the missing-key lookup. Thus raw preflight PASS does not establish task-level qualification.

## Q. Final runner readiness

Exactly one final frozen-harness readiness replay passed SR/bookkeeping, ZD, PW, production-shaped W2E, legacy-W2 nonblocking, synthetic Layer A, and EP-Q checks. It likewise did not cover the later inherited postprocessor lookup. [Readiness result](b2_t4_re6_r1_artifacts/runner_readiness_replay.json).

## R. CUDA/CUBLAS

One worker-local `cuda:0` matrix-multiply probe passed before AppLauncher, with zero retries. [Probe](b2_t4_re6_r1_artifacts/cuda_cublas_readiness.json).

## S. Canonical import ordering

Preflight import-order regression passed. Worker started AppLauncher before importing `isaaclab_tasks`, then resolved the canonical environment entry-point class. The receipt records `entry_point_resolution_pass=true`.

## T. Fresh formal process

One supervisor launched one worker, zero retries. The worker exited; original PID 7476 was absent and matching worker set empty. The worker process exit code was zero, but its durable receipt status was failure; exit code and Layer B cannot override failed Layer A.

## U. Runtime configuration

Environment `Isaac-Scan-Mobile-Manipulator-Direct-v0`, profile `event_gated_local_mrta`, CUDA:0, T=2, E=2, M=3, N=12, actor/critic epochs 5 and minibatches 2, ValueNorm enabled, fixed order false. [Config authority](b2_t4_re6_r1_artifacts/process_config_authority.json).

## V. Horizon separation

Normal horizon remained 30.0 s, max 300 steps, control step 0.1 s. No short-horizon override was used. Two canonical TIME_LIMIT/autoresets occurred at tx150; no learner-boundary reset was claimed.

## W. Transaction definition

Only post-rollout, NR/ZD, production S0–S10, SR/bookkeeping, durable-readback ledger rows counted. 160 such rows exist, but full campaign qualification failed after their publication.

## X. Transaction inventory

Exactly tx001–tx160 were recorded, 320 physical transitions, 159 bridges, no tx161. Detailed sentinel files and complete append-only ledgers remain in the attempt directory.

## Y. Transaction table

The full 160-row [diagnostic transaction table](b2_t4_re6_r1_artifacts/transaction_table.md) joins S10, ledger, generation, policy/continuation/noop, zero-DVM, terminal, completion, PW and bridge evidence. It is not a success certificate.

## Z. Episode/update timeline

160 timeline rows record the normal-horizon progression. Generation changes only at canonical terminal/autoreset; tx150 is the first terminal witness and tx151 the fresh post-autoreset training witness. [Timeline ledger](b2_t4_re6_r1_artifacts/episode_update_timeline.jsonl).

## AA. Decision gating

Source-derived execution counted zero missing, duplicate, or continuation-resample policy-call faults. Per-transaction policy/continuation/noop counts are in the table.

## AB. NR

NR preflight suite and terminal matrix passed. Fresh terminal reconciliation ledger has 160 rows; tx001 demonstrates empty expected/observed terminal keys for NONE. [NR ledger](b2_t4_re6_r1_artifacts/terminal_reconciliation.jsonl).

## AC. SR

SR positive/negative and retained replay checks passed preflight. Fresh S10/bookkeeping ledger rows reached 160; this does not override postprocess failure.

## AD. ZD

ZD positive/negative and retained RE2 replay passed preflight. Fresh evidence includes 452 zero-DVM actor/transaction pairs. [ZD ledger](b2_t4_re6_r1_artifacts/zero_dvm_actor_ledger.jsonl).

## AE. Zero-DVM

139 transactions had all actors at zero DVM. W3 tx002 records zero backward/step, unchanged optimizer/parameters/Adam, and identity factor while the transaction's critic continued.

## AF. Actor plan

Transaction evidence summed 165 actor backward and 165 actor optimizer steps. These are observed learner counts, not a final Layer-A pass after the postprocess error.

## AG. Actor evidence

The 160-row actor reconciliation ledger recorded zero faults in the RE3 final evidence. [Actor evidence](b2_t4_re6_r1_artifacts/actor_evidence_reconciliation.jsonl).

## AH. Factor

Source-derived per-transaction factor audits ran; the success receipt was never built, so the task-level cumulative factor gate is not asserted as qualified.

## AI. Critic

Observed 1,600 critic backward and 1,600 optimizer steps: 1,576 `VALID_NONZERO_UPDATE`, 24 `VALID_ZERO_EFFECTIVE_UPDATE`. The postprocess failure still blocks qualification.

## AJ. ValueNorm

Observed 1,600 ValueNorm updates through critic training. Continuity is not elevated to a successful Layer-A receipt.

## AK. Event returns

Observed 160 reviewed event-return computations and zero stock HARL `compute_returns` calls.

## AL. Collection learner immutability

The 159 bridges recorded collection/learner continuity; RE3's final in-worker quiescence check passed before the later postprocess exception. The route was subsequently classified poisoned, so that earlier check is not final route health.

## AM. Actor Adam

W3 zero-DVM actor's Adam state was unchanged. No full-campaign actor-Adam qualification claim is made after failed Layer A.

## AN. Critic Adam

Critic step counts are 1,600. A full-campaign Adam continuity receipt was not produced, so this remains observed diagnostic evidence only.

## AO. Bridges

159/159 append-only bridge rows exist and passed their per-row predicates. [Bridge ledger](b2_t4_re6_r1_artifacts/bridge_ledger.jsonl).

## AP. PW per-tx

160 per-transaction PW reconciliation rows each recorded 41 critic and 4 actor/factor immutable records with zero listed integrity faults. [PW per-tx ledger](b2_t4_re6_r1_artifacts/pw_transaction_reconciliation.jsonl).

## AQ. PW campaign

Post-failure read-only reconciliation found critic 6,560/6,560 and actor/factor 640/640, with zero missing/duplicate/order/digest/temp faults. It was run only after process quiescence and does not turn the failed worker receipt into success.

## AR. W1

Provisional W1 passed at tx001→tx002, env0/robot1/task4, same P2 ownership with forced continuation and zero fresh policy call. [W1 file](b2_t4_re6_r1_artifacts/W1_cross_update_ownership.json).

## AS. W2E candidate inventory

Reviewed selector returned 29 candidates, 12 valid, with rejection reasons preserved for invalid candidates. [Complete inventory](b2_t4_re6_r1_artifacts/w2e_candidate_inventory.json).

## AT. W2E selected witness

Deterministic first valid witness: env1/robot1/task10, episode generation 0, claim tx12/step23, bridges 12–14, completion tx15/step30, reopen tx16/step31. [Selected witness](b2_t4_re6_r1_artifacts/w2e_selected_witness.json).

## AU. W2 claim

Selector Layer A passed from B1/P2 ownership/task-state transition and admitted effective assignment, not textual `task_claimed`.

## AV. W2 continuity

Layer B passed same env/robot/task/generation ownership across qualified pre-completion bridges 12–14 with continuation; no release, reassignment, transfer, or failed-pair break was accepted.

## AW. W2 completion

Layer C passed at tx15/step30 from a `task_completed` event and completion-count increment.

## AX. W2 clear

Layer D passed with task owner/current-task clear after completion.

## AY. W2 reopen

Layer E passed at tx16/step31 with the same robot decision reopened and exactly one policy call.

## AZ. Legacy W2 diagnostic

Legacy old W2 remained `null` and explicitly non-authoritative. Its absence did not cause the formal failure.

## BA. W3

Provisional real zero-DVM actor witness passed at tx002; see section AE.

## BB. W4

Provisional nonterminal bootstrap witness passed at tx001: NONE terminal keys empty/empty, current next-state critic bootstrap, event returns and S10.

## BC. W5

Provisional normal-horizon terminal/autoreset witness passed at tx150, with two canonical TIME_LIMIT terminal keys. No forced TIME_LIMIT shortcut was used.

## BD. W6

Provisional fresh post-autoreset learned transaction passed at tx151, new generation after tx150.

## BE. W7

Provisional runtime/P2 pre-S0/post-S10 immutability was equal 160/160. [W7 file](b2_t4_re6_r1_artifacts/W7_runtime_p2_immutability.json).

## BF. Task progress

22 `TASK_COMPLETED` events and positive completion delta were observed before episode reset. This is capability evidence, not performance qualification.

## BG. Coverage/completions

Maximum coverage was 11; the last post-reset state had coverage 0/0. The task-progress gate used positive historical maximum and completion events, not a final-episode score.

## BH. tx130 sentinel

tx130 S10 and full ledger row exist. Its inherited PW comparison recorded PASS and 41 critic progress records; no PermissionError was recorded. No numerical equivalence with historical RE4/RE5 is claimed.

## BI. Numerical health

All 160 transaction ledger `finite` flags were true. The task-required full numerical-health success receipt was not produced, so this remains bounded observed evidence.

## BJ. Rolling health

160 rolling-health ledger rows exist. The final route status is poisoned due to the postprocess failure, regardless of earlier rolling observations. [Rolling ledger](b2_t4_re6_r1_artifacts/rolling_health.jsonl).

## BK. Layer-A receipt

FAIL. The durable failure receipt records `KeyError('_base_atomic_json')` at source-derived RE5 `run_formal_worker` after RE3's postprocessor returned and before RE5 could publish its phase-specific final payload or PW success receipt. It also lacks direct W2E/W2I digest fields required of a successful task-level receipt. Raw Layer-A checks show status failure, incomplete receipt counters, and no successful route claim.

## BL. Env close

The worker's failure receipt was durably written/read back before `env.close`; `env_close_pass=true`, `app_close_invoked=true`. This does not mean every internal Kit callback returned.

## BM. EP-Q Layer B

PASS: wait complete, no timeout, exit code zero, original PID absent, no matching worker. Layer B cannot override failed Layer A. [Process quiescence](b2_t4_re6_r1_artifacts/process_quiescence.json).

## BN. Shutdown diagnostics

Shutdown marker was not observed and was not authoritative. No success inference rests on shutdown text.

## BO. Supervisor adjudication

Raw supervisor status failed, raw classification `PHASE-B2-T4-RE6-R1-STOP-FORMAL-WORKER-FAILURE`, Layer A FAIL, Layer B PASS. The narrower source-backed post-formal classification identifies the inherited missing-key error. Supervisor and worker count remained 1/1/0 retries. [Supervisor result](b2_t4_re6_r1_artifacts/formal_supervisor_result.json).

## BP. Exact counts

The final inherited preflight summary recorded 14 child Python invocations, but the overall pre-runtime Python invocation count is **not established**: exploratory pure checks and earlier preflight repeats were not captured in one authoritative counter. This is another reason not to assert the requested full PASS. Final readiness 1; supervisor/worker/retries 1/1/0; CUDA 1; AppLauncher 1; environment/reset/persistent learner 1/1/1 from runtime counters/final evidence; physical 320; S10 and transaction ledger 160/160; bridges 159; PW critic 6,560, actor/factor 640; W2E candidates/valid 29/12; actor backward/step 165/165; critic backward/step 1,600/1,600; critic classes 1,576 nonzero + 24 zero-effective; ValueNorm 1,600; event returns 160, stock returns 0; terminal/autoreset 2; W7 160/160; checkpoint/public/evaluation 0/0/0; tx161 not started. Receipt-level environment/learner counts stayed zero because the success payload was never built; do not confuse those defaults with absence of runtime execution.

## BQ. Retained nonclaims

No RE6-R1 qualification PASS, no GPT REVIEW PASS, no reusable learner, no checkpoint continuation, no B2-R6, no long/paper-scale training, no public learned-policy activation, and no evaluation/playback. W1–W7 files were published before the later failure and are retained only as provisional facts. [Publication-status record](b2_t4_re6_r1_artifacts/witness_publication_status.json).

## BR. Final classification

`PHASE-B2-T4-RE6-R1-STOP-INHERITED-POSTPROCESS-KEYERROR-AFTER-MUTATION`; `partial_update=true`; `route_poisoned=true`. No retry. This is a STOP despite strong bounded runtime and W2E/PW evidence.

## BS. GPT-review handoff

Review the frozen raw receipt, source-derived RE5 line using `engine['_base_atomic_json']`, derived engine key inventory, preflight gap, provisional W1–W7 files, W2E inventory, PW post-failure diagnostic, and EP-Q Layer B. Any future attempt requires a new explicitly authorized fresh namespace and pre-runtime proof of the full postprocess and receipt path; this report does not authorize it.
