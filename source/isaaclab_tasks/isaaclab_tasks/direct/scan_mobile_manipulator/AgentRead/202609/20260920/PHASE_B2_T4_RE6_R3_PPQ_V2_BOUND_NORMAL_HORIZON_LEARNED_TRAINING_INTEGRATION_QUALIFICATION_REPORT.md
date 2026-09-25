# Phase B2-T4-RE6-R3 — PPQ-V2-bound normal-horizon learned-training integration

Date: 2026-09-20. Final independent classification: `PHASE-B2-T4-RE6-R3-STOP-INCOMPLETE-LAYER-A-WORKER-RECEIPT-AFTER-MUTATION`. The single formal run produced positive raw runtime, PPQ-V2 and EP-Q evidence, and its supervisor reported PASS. However, a post-supervisor audit found that inherited mandatory Layer-A worker-receipt fields were left at template defaults and their RE5 checks were omitted from the R3 supervisor. The supervisor PASS is therefore **not a qualified phase PASS**. With irreversible learner mutation already performed, this attempt is retained as STOP / poisoned / never reuse; no retry was launched. See the [independent audit](b2_t4_re6_r3_artifacts/post_supervisor_gate_equivalence_audit.json) and [failure receipt](b2_t4_re6_r3_artifacts/failure_receipt.json).

## A. Repository authority

Branch `main`, HEAD `b71d85a32f51be6ada324f870813a56bb45dd396`. The pre-existing staged monthly archive migration was preserved; no git add, commit, push, reset, checkout, or clean was performed. See [repository authority](b2_t4_re6_r3_artifacts/repository_authority.json).

## B. Reviewed authority

The user-provided starting authority closes B2-R0–R7, B2-T0–T3, and B2-T4-NR/SR/ZD/EP-Q/PW/W2E/W2I/PPQ-v1/PPQ-V2 as GPT REVIEW PASS. This does not itself qualify a fresh training attempt.

## C. Historical STOP preservation

RE5 and RE6-R1 remain historical poisoned STOPs. RE6-R2 remains a historical pre-runtime STOP with zero formal attempts and no poison. Their files and learners were not reused or modified.

## D. PPQ-V2 authority

PPQ-V2 is GPT REVIEW PASS / CLOSED for the fresh-run success-receipt contract `b2_t4_ppq_fresh_run_success_receipt_v2`. The reviewed helper, qualification runner, and schema hashes are bound in [reviewed identity gate](b2_t4_re6_r3_artifacts/reviewed_identity_gate.json).

## E. Source identities

Reviewed W2E, W2I, PW, PPQ-V2 and three frozen production hashes matched. The production full-transaction, adapter, and environment hashes were `a45db23b…b583d7`, `57419d52…9500ac`, and `f96f6b6e…5c6363` respectively. See [static authority](b2_t4_re6_r3_artifacts/static_authority.json).

## F. RE6-R3 harness

The new [R3 harness](../../../../../../../../scripts/environments/test_assignment_phase_b2_t4_re6_r3_normal_horizon_learned_training_integration.py) uses the source-derived RE5 transaction route in an R3-only artifact namespace. Its new success path is R3 normalization followed by the reviewed PPQ-V2 helper, not inherited RE5/R1 postprocessing. That removes the old hidden writer lookup, but its custom supervisor failed to preserve all inherited Layer-A worker-receipt checks. See [source derivation](b2_t4_re6_r3_artifacts/success_path_dependency_audit.json) and the [post-run audit](b2_t4_re6_r3_artifacts/post_supervisor_gate_equivalence_audit.json).

## G. Normalizer architecture

The pure [R3 normalization adapter](../../../../../../../../scripts/environments/_assignment_phase_b2_t4_re6_r3_ppq_v2_normalization.py) reconstructs campaign, W2E, lifecycle, terminal, PW, learner, and health fields from retained rows and a reviewed-PW verification callback. It has no Isaac/HARL import or historical value constants.

## H. Normalization source map

Each PPQ-V2 field is mapped to a concrete retained ledger or reviewed verifier in [the source map](b2_t4_re6_r3_artifacts/runtime_normalization_source_map.json); convenience summary claims are cross-checked, not accepted as authority.

## I. Historical normalization replay

On immutable RE6-R1 ledgers, the exact adapter reconstructed 160 transactions, 320 physical transitions, 159 bridges, W2E 29 candidates/12 valid, task completion 22, maximum coverage 11, terminal/autoreset 2, and PW 6,560/640. The deterministic W2 selection was env 1 / robot 1 / task 10, claim tx12/step23, completion tx15/step30, reopen tx16/step31. This is a normalization replay only; RE6-R1 remains poisoned. See [replay](b2_t4_re6_r3_artifacts/runtime_normalizer_historical_replay.json).

## J. Synthetic fresh normalization replay

A production-shaped R3 fixture yielded different values: W2E 1/1, env 1 / robot 0 / task 0, completion count 1, coverage 2, terminal count 1. The same adapter passed into the reviewed PPQ-V2 helper. See [replay](b2_t4_re6_r3_artifacts/runtime_normalizer_synthetic_replay.json).

## K. Normalization negative matrix

All 14 specified corruption cases stopped; unexpected PASS = 0. See [matrix](b2_t4_re6_r3_artifacts/runtime_normalizer_negative_matrix.json).

## L. Frozen normalizer identity

The adapter was frozen after tests at SHA-256 `316b58f76934de073c32bf81f510c321917decb6645d1244436031ed360e92e3`. See [identity](b2_t4_re6_r3_artifacts/runtime_normalizer_identity.json).

## M. Gate equivalence

RE6-R2 had zero formal attempts. The pre-runtime [equivalence artifact](b2_t4_re6_r3_artifacts/re6_r2_re6_r3_gate_equivalence.json) claimed unchanged transaction/NR/SR/ZD/PW/learner/process gates except reviewed PPQ-V2 and the R3 normalizer. This claim was too broad: the custom supervisor omitted inherited worker-receipt Layer-A predicates. The later [independent audit](b2_t4_re6_r3_artifacts/post_supervisor_gate_equivalence_audit.json) supersedes that pre-runtime PASS for final qualification.

## N. Hidden-dependency audit

The new success route has zero missing required engine keys and no required `_base_atomic_json` lookup; that specific historical KeyError did not recur. The [dependency audit](b2_t4_re6_r3_artifacts/success_path_dependency_audit.json) did **not** establish complete Layer-A predicate equivalence, as shown by the independent post-run audit.

## O. Full success-path preflight

The R3 synthetic normalization and PPQ-V2 chain used 7,200 immutable PW records through the reviewed PW interface, schema validation, durable candidate write, readback/digest/schema revalidation, then seven canonical witness publications. It passed without AppLauncher. However, it did not exercise the complete formal worker-receipt projection and inherited supervisor predicates, so its `pass=true` was insufficient as the task's **full** success-path preflight. See [preflight](b2_t4_re6_r3_artifacts/full_success_path_preflight.json) and [audit](b2_t4_re6_r3_artifacts/post_supervisor_gate_equivalence_audit.json).

## P. Final runner readiness

Exactly one final pure/static replay returned PASS for inherited SR/ZD, reviewed W2E/PW/PPQ-V2 and EP-Q Layer B; AppLauncher and formal-worker counts were zero at that gate. The replay did not detect the omitted inherited Layer-A receipt predicates, so its reported PASS is retained as historical pre-runtime evidence but not accepted as complete final readiness. See [readiness](b2_t4_re6_r3_artifacts/runner_readiness_replay.json).

## Q. Filesystem/PW precondition

The artifact volume is NTFS; PW temp and final paths are same-volume/same-directory, and the reviewed helper hash matched. See [filesystem evidence](b2_t4_re6_r3_artifacts/filesystem_precondition.json).

## R. CUDA/CUBLAS

Exactly one CUDA/CUBLAS probe passed inside the formal worker, with no retry. See [probe](b2_t4_re6_r3_artifacts/cuda_cublas_readiness.json).

## S. Fresh formal process

One supervisor launched one fresh worker, PID 31212, run ID `b2-t4-re6-r3-20260920-formal01-b4718cb4f54b4f589a418dad7f4c4411`, with zero retries. Worker exit code was 0; the original PID was absent after wait and matching formal-worker set was empty. See [supervisor](b2_t4_re6_r3_artifacts/formal_supervisor_result.json) and [worker receipt](b2_t4_re6_r3_artifacts/formal_worker_receipt.json).

## T. Runtime config

`T=2`, `E=2`, `M=3`, `N=12`; actor/critic epochs 5 and minibatches 2; ValueNorm enabled; normal horizon 30 seconds, maximum episode length 300, control step 0.1 seconds, CUDA:0. See [config](b2_t4_re6_r3_artifacts/process_config_authority.json).

## U. Transaction definition

Each qualified transaction includes two real physical steps, the inherited S7–S10 full learned-update gate, one event-return calculation, and zero stock `compute_returns`. The fresh campaign ended at tx160; tx161 did not start.

## V. Transaction inventory

160 qualified rows and 320 physical transitions were retained. See [transaction ledger](b2_t4_re6_r3_artifacts/transaction_ledger.jsonl), [lifecycle progress](b2_t4_re6_r3_artifacts/lifecycle_task_progress.jsonl), and [raw engine final](b2_t4_re6_r3_artifacts/b2_t4_re6_r3_normal_horizon_20260920_formal01_final_result.json).

## W. Transaction table

The append-only [transaction table](b2_t4_re6_r3_artifacts/transaction_ledger.jsonl) has indices 1–160, all S7/S8/S9/S10 true and finite. The [normalization crosscheck](b2_t4_re6_r3_artifacts/runtime_normalization_crosscheck.json) re-counts these values rather than accepting an asserted summary.

## X. Episode/update timeline

The [episode/update timeline](b2_t4_re6_r3_artifacts/episode_update_timeline.jsonl) and P2 generation-bearing [progress ledger](b2_t4_re6_r3_artifacts/lifecycle_task_progress.jsonl) retain the 160 updates, 320 steps, tx150 terminal transition, and post-reset tx151 continuation.

## Y. Decision gating

Raw counts show missing policy calls 0, duplicate policy calls 0, policy-required rows 39, and forced no-op nondecision rows 587. One call per required decision was retained; continuation rows had zero resample faults.

## Z. NR

The inherited reviewed NR gate passed in preflight and all 160 formal transactions reached qualified S10. No NR-specific failure was observed. See [preflight summary](b2_t4_re6_r3_artifacts/re6_r3_preflight_summary.json) and [transaction ledger](b2_t4_re6_r3_artifacts/transaction_ledger.jsonl).

## AA. SR

The inherited serializer and post-S10 bookkeeping replays passed; formal append-only ledgers have 160 transactions and 159 bridges. See [SR preflight](b2_t4_re6_r3_artifacts/preflight/sr/final_result.json).

## AB. ZD

The continuation-only zero-DVM route passed its replay and formal continuation resample faults were 0. See [ZD preflight](b2_t4_re6_r3_artifacts/preflight/zd/re2_tx002_zero_dvm_replay.json) and [zero-DVM ledger](b2_t4_re6_r3_artifacts/zero_dvm_actor_ledger.jsonl).

## AC. Zero-DVM

The [zero-DVM actor ledger](b2_t4_re6_r3_artifacts/zero_dvm_actor_ledger.jsonl) is retained; the valid zero-effective critic-update class contributed 24 of 1,600 critic steps, with no invalid classification accepted.

## AD. Actor plan

Observed actor backward/optimizer steps were 165/165, exactly equal to transaction-derived plans. The [normalization result](b2_t4_re6_r3_artifacts/runtime_normalization_result.json) and raw per-transaction `real_audit` reconcile these counts.

## AE. Actor evidence

160 [actor reconciliation rows](b2_t4_re6_r3_artifacts/actor_evidence_reconciliation.jsonl) had exact match and zero faults; W3/W7 and learner checks remained mandatory.

## AF. Factor

All 160 raw transactions report successful factor audit, with 480 factor segments. Actor/factor PW records are 640/640. These are bounded factor-route facts, not long-training quality.

## AG. Critic

Critic backward/optimizer steps were 1,600/1,600 and matched per-transaction plans. The classification split was 1,576 valid nonzero and 24 valid zero-effective updates; invalid updates were not accepted by the normalized receipt.

## AH. ValueNorm

ValueNorm updated 1,600 times, equal to the planned critic updates. Its object identity stayed stable and final state was finite; the reviewed PPQ-V2 receipt requires those checks.

## AI. Event returns

Event-return calculations were exactly 160; stock `compute_returns` was 0. See [transaction ledger](b2_t4_re6_r3_artifacts/transaction_ledger.jsonl).

## AJ. Adam continuity

Raw persistent learner identity reports stable actor and critic optimizer objects and finite final optimizer states. This is continuity for the one normal-horizon learner, not a checkpoint-resume claim.

## AK. Bridges

159 [bridge rows](b2_t4_re6_r3_artifacts/bridge_ledger.jsonl) bind adjacent update IDs and passed the normalizer continuity check.

## AL. PW per-transaction

160 [PW reconciliation rows](b2_t4_re6_r3_artifacts/pw_transaction_reconciliation.jsonl) correspond one-to-one with 160 transaction rows; each required 41 critic and 4 actor/factor immutable records.

## AM. PW campaign

The reviewed verifier read 6,560 critic and 640 actor/factor files. Missing, duplicate, order, digest, temp-residue, and old mutable progress path counts were all 0. See [campaign reconciliation](b2_t4_re6_r3_artifacts/pw_campaign_reconciliation.json).

## AN. W1

[Cross-update ownership](b2_t4_re6_r3_artifacts/W1_cross_update_ownership.json) PASS, published only after validated receipt.

## AO. W2E inventory

The exact reviewed selector produced 29 candidates and 12 valid entries from the fresh lifecycle/bridge ledgers. See [inventory](b2_t4_re6_r3_artifacts/w2e_candidate_inventory.json).

## AP. W2E witness

The deterministic selected [W2E witness](b2_t4_re6_r3_artifacts/W2_multi_update_completion_v2.json) is env 1, robot 1, task 10, generation 0; claim tx12/step23, completion tx15/step30, reopen tx16/step31. All five selector layers passed.

## AQ. W2 claim

Selected Layer A claim authority is true; the pre/post-claim P2 digests are present in the selected witness. No textual-claim fallback is authoritative.

## AR. W2 continuity

Selected Layer B ownership continuity is true across bridges 12–14, derived from retained updates rather than a summary constant.

## AS. W2 completion

Selected Layer C completion authority is true at tx15/step30; lifecycle event and P2 completion-count deltas reconcile campaign-wide at 22/22.

## AT. W2 clear

Selected Layer D ownership-clear assertion is true after completion.

## AU. W2 reopen

Selected Layer E decision-reopen assertion is true at tx16/step31. The ordered claim→completion→reopen satisfies the reviewed PPQ-V2 contract.

## AV. W3

[Real zero-DVM actor witness](b2_t4_re6_r3_artifacts/W3_real_zero_dvm_actor.json) PASS.

## AW. W4

[Real nonterminal bootstrap witness](b2_t4_re6_r3_artifacts/W4_real_nonterminal_bootstrap.json) PASS.

## AX. W5

[Normal-horizon terminal/autoreset witness](b2_t4_re6_r3_artifacts/W5_normal_horizon_terminal_autoreset.json) PASS.

## AY. W6

[Post-autoreset training witness](b2_t4_re6_r3_artifacts/W6_post_autoreset_training.json) PASS.

## AZ. W7

[Runtime P2 immutability witness](b2_t4_re6_r3_artifacts/W7_runtime_p2_immutability.json) PASS, 160/160 qualified rows.

## BA. Task progress

Fresh lifecycle events show 22 `task_completed`, P2 completion-count deltas 22, and maximum coverage 11. See [progress ledger](b2_t4_re6_r3_artifacts/lifecycle_task_progress.jsonl) and [normalized result](b2_t4_re6_r3_artifacts/runtime_normalization_result.json).

## BB. Terminal/autoreset

The [terminal ledger](b2_t4_re6_r3_artifacts/terminal_reconciliation.jsonl) records two `TIME_LIMIT` events at tx150 with no reason-priority fault; generation changes and qualified tx151 establish post-autoreset learned training. This is a bounded normal-horizon event, not full episode-population characterization.

## BC. tx130 sentinel

The [tx130 comparison](b2_t4_re6_r3_artifacts/re4_re5_tx130_persistence_comparison.json) passed with fresh S10=1, 41 critic PW events and zero PW faults. Its inherited diagnostic label says “RE5,” but the recorded run ID is this R3 fresh process; the historical poisoned learner was not reused.

## BD. Numerical health

All 160 transaction rows are finite; final actor/critic parameters, optimizer states, ValueNorm state, and gradient-clean flags are true. See raw engine final and [training metrics](b2_t4_re6_r3_artifacts/training_metrics.jsonl).

## BE. Actual runtime normalization

The frozen adapter processed this fresh R3 run's own retained rows, not the historical fixture, and wrote [the normalized result](b2_t4_re6_r3_artifacts/runtime_normalization_result.json). Its raw-to-normalized field comparison is:

| PPQ-V2 field | Raw source | Raw | Normalized | Check |
|---|---|---:|---:|---|
| transaction count | transaction ledger | 160 | 160 | PASS |
| physical transitions | progress steps | 320 | 320 | PASS |
| S10 | transaction ledger | 160 | 160 | PASS |
| bridges | bridge ledger | 159 | 159 | PASS |
| W2 candidates | exact W2E selector | 29 | 29 | PASS |
| W2 valid | exact W2E selector | 12 | 12 | PASS |
| selected W2 | exact W2E selector | e1/r1/t10, 12→15→16 | same | PASS |
| TASK_COMPLETED | lifecycle events | 22 | 22 | PASS |
| completion delta | same-generation P2 counts | 22 | 22 | PASS |
| maximum coverage | P2 progress | 11 | 11 | PASS |
| terminal/autoreset | terminal reconciliation | 2 | 2 | PASS |
| post-reset learned | generation + tx151 | true | true | PASS |
| PW critic | reviewed PW verifier | 6,560 | 6,560 | PASS |
| PW actor/factor | reviewed PW verifier | 640 | 640 | PASS |

The table establishes data normalization, not the omitted worker-receipt Layer-A gate.

## BF. Normalization/raw crosscheck

[Crosscheck](b2_t4_re6_r3_artifacts/runtime_normalization_crosscheck.json) PASS for the fields above; the extra worker-receipt projection discrepancy was discovered only in the subsequent independent audit. No normalized source value was manually overridden to match the historical 29/12 or 22/11/2.

## BG. PPQ-V2 Layer-A receipt

The reviewed PPQ-V2 [candidate receipt](b2_t4_re6_r3_artifacts/candidate_success_receipt.json) passed its own schema and source binding. However, the task also required unchanged inherited Layer-A worker-receipt checks. The [worker receipt](b2_t4_re6_r3_artifacts/formal_worker_receipt.json) asserted environment/reset/learner counts 0/0/0, event returns 0, task completions 0, empty learner and contract maps, and `final_in_worker_quiescence_pass=false`, while raw evidence showed 1/1/1, 160 and 22. The custom R3 supervisor did not check those inherited fields. Therefore overall Layer A is **not qualified**, despite `layer_a.pass=true` in the original supervisor artifact.

## BH. Schema validation

PPQ-V2 candidate schema validation and revalidation passed. That schema does not validate the inherited worker-receipt projections cited in BG; schema PASS cannot rescue overall Layer-A incompleteness.

## BI. Durable receipt

One PPQ-V2 candidate success receipt was durably written before canonical witness publication. The artifact is preserved unchanged; it is valid only within its PPQ-V2 contract, not as proof of the omitted inherited gate.

## BJ. Readback/digest

Readback, digest and revalidation passed. The [validation record](b2_t4_re6_r3_artifacts/success_receipt_readback_validation.json) and original supervisor show candidate SHA-256 `9ba0486bd0a5c85166a2656cea476f06675e92bf354823076fb41a4e1a1f27fa`.

## BK. Canonical publication ordering

The seven canonical witnesses were published after PPQ-V2 receipt validation, as shown by [publication order](b2_t4_re6_r3_artifacts/success_publication_order.json). They remain retained evidence, but their existence is not an overall phase PASS after the gate-equivalence finding.

## BL. Environment close

The worker receipt recorded `env_close_pass=true` and `app_close_invoked=true` before process exit. This is bounded worker evidence; it does not claim that every internal Kit shutdown callback completed.

## BM. EP-Q Layer B

The [process-quiescence predicates](b2_t4_re6_r3_artifacts/process_quiescence.json) passed: wait completed, no timeout, return code 0, original PID absent, matching worker set empty. EP-Q Layer B cannot rescue incomplete Layer A.

## BN. Process quiescence

Only the external process-level quiescence claim is established. Shutdown text was diagnostic and non-authoritative; `SimulationApp.close` normal return and every internal callback are nonclaims.

## BO. Supervisor adjudication

The original [formal supervisor result](b2_t4_re6_r3_artifacts/formal_supervisor_result.json) and [original final result](b2_t4_re6_r3_artifacts/final_result.json) are preserved byte-for-byte with their reported PASS. Their custom Layer-A check set omitted inherited mandatory worker-receipt predicates. The [independent final audit](b2_t4_re6_r3_artifacts/post_supervisor_gate_equivalence_audit.json) therefore supersedes that reported PASS for phase classification. No original result was overwritten or silently reinterpreted.

## BP. Exact counts

The inherited preflight recorded 14 pre-runtime Python subprocess invocations within that preflight (12 named gate commands plus its explicit compile/receipt paths); this is a scoped count, not an invented total for all ad hoc diagnostics. The artifact-producing R3 preflight contained one historical normalization replay, one synthetic replay, one 14-case negative matrix and one complete synthetic success-chain replay; one final readiness replay followed. Additional exploratory pure diagnostics, including an earlier full-success-chain invocation, are not included in the inherited 14-count; no all-command total is claimed. Formal supervisor/worker/retries were 1/1/0. CUDA/AppLauncher/environment/reset/persistent learner were 1/1/1/1/1. Physical/S10/ledger/bridges were 320/160/160/159; tx161 not started. PW critic/actor-factor were 6,560/640. W2E 29/12; task completions 22, coverage 11, terminal/autoreset 2. Actor backward/step 165/165, critic 1,600/1,600, ValueNorm 1,600, event returns 160, stock `compute_returns` 0. Candidate success-receipt writes 1; canonical publications 7 after validation. Checkpoint weight I/O, public activation, evaluation/playback and git add/commit/push were all 0. These raw-positive counts do not repair the missing Layer-A receipt gate.

## BQ. Retained nonclaims

No checkpoint continuation, resumed learner, long or paper-scale training, public learned-policy route, evaluation/playback quality, or general performance claim is established. PPQ-V2, W2E, PW and EP-Q reviewed authorities remain closed only within their stated scopes. This R3 learner and attempt must never be reused after the final STOP.

## BR. Final classification

The data-level results are distinct from qualification:

| Gate | Observed result |
|---|---|
| Runtime normalizer and raw crosscheck | PASS |
| W1, W2E, W3–W7 | PASS |
| PW | PASS |
| Actor, critic, factor, Adam, ValueNorm, numerical health | PASS |
| PPQ-V2 receipt, durable write, readback/digest, publication order | PASS |
| EP-Q Layer B | PASS |
| Inherited worker-receipt Layer-A predicates | **NOT ENFORCED / FAIL** |
| Gate equivalence and overall qualification | **STOP / POISONED** |

Final classification: `PHASE-B2-T4-RE6-R3-STOP-INCOMPLETE-LAYER-A-WORKER-RECEIPT-AFTER-MUTATION`. `partial_update=true`, `route_poisoned=true`, formal attempts 1, retries 0. This logical poison classification is a post-run safety decision, not a claim that the exited in-memory route object's `_poisoned` attribute was mutated retroactively.

## BS. GPT-review handoff

Review the preserved original supervisor PASS, candidate PPQ-V2 receipt, worker receipt and raw engine final alongside the independent [gate-equivalence audit](b2_t4_re6_r3_artifacts/post_supervisor_gate_equivalence_audit.json). The specific repair, if separately authorized later, is to preserve and validate the inherited Layer-A worker-receipt predicates through the R3 supervisor and qualify that **before** any new runtime. Do not repair this attempt in place, reuse its learner, launch a retry, activate the public route, stage or commit these files on this task's authority.
