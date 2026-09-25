# Phase-B Final Closure-Readiness Audit

Date: 2026-09-24 (Asia/Shanghai)

Task: `PHASE-B-FINAL-CLOSURE-READINESS-AUDIT`

Classification: **PHASE-B-FINAL-CLOSURE-READINESS-AUDIT-READY**

## 1. Verdict and scope

**Checkpoint-continuation-only hypothesis: CONFIRMED**, for the inspected fixed-scale, reviewed event-training backbone. No additional unresolved production/runtime semantic blocker was identified. The remaining closure demonstration is a bounded, real, fresh-process optimization checkpoint continuation, including restored Adam, ValueNorm, progression/LR and safe shutdown. Class A items: **0**. Class B items: **1 bundled smoke**.

This is an independent source/evidence audit, not a new runtime qualification, proof of absence of all possible bugs, or a Phase-B completion declaration. No code or harness was changed and no runtime was imported or executed. CSR1, CKPT1 and HR1 are treated as user-reviewed PASS/CLOSED; their old report wording is not rewritten. CKPT2/R1-R6 and R14 retain their historical STOP classifications. R14's learner/authority is never reusable.

Phase B should establish a usable lifecycle-aware learned training/runtime backbone for first-paper **fixed-scale** experiments. It need not establish a perfect forensic framework, policy convergence, an experiment campaign, public CLI readiness, arbitrary configuration migration, or variable-cardinality policies.

## 2. Audit method and direct evidence

Read the current handoff, B2-R0 architecture/R7 closure, T0-RE1 repeated continuity, T1/T2/T3, CSR1, CKPT1, CKPT2/R1-R6 and HR1 reports as maps. Then inspected production function bodies, the real adapter, the composed R6/R5/R4/R1 harness path, CKPT1 test assertions, installed HARL critic/ValueNorm semantics, and retained JSON/JSONL. No PASS label alone was used as proof.

Current source hashes exactly match the relevant retained evidence:

| Source | SHA-256 | Retained anchor |
|---|---|---|
| environment | `f96f6b6e9a530cd0b438344a11dc67670559206f3521d641d776d4bd475c6363` | R14 production snapshot |
| full transaction | `a45db23b863c51334b15205b3c50fa5997ab8f5e4a32f8c4a801242365b583d7` | R14 production snapshot |
| real Isaac adapter | `57419d52caa77160609f77b289979ed6785fc645eab1b17320e9cbda1e9500ac` | R14 production snapshot |
| optimization checkpoint | `b0fec513bad87af961450345f1ee5849cca04c4da5429a483af5f31f8a6e76b9` | CKPT1 / retained CKPT2-R5 |
| assignment runner | `31295d60a01d11657b924e6d8332f160b278eeeb236109b59409bfbf55f7e787` | CKPT1 / retained CKPT2-R5 |

R14 direct ledger arithmetic was recomputed read-only: **160 transactions, 159 bridges, 165 actor steps, 1600 critic steps, 1600 ValueNorm updates**; zero nonfinite rows, zero false S7-S10 rows, and zero event-return count/stock-return violations. All 159 bridge rows report persistent object identity, exact post-to-pre learner state and collection immutability. These are retained subsystem observations, not a reclassification of R14.

The completion witness was checked against raw lifecycle rows, not just W2's PASS: env1/robot1/task10 is owned at physical step23 (tx12), emits `task_completed` and `robot_needs_assignment` at step30 (tx15), clears ownership to -1, and has a reopened decision at step31 (tx16). W2 includes 12 valid complete witnesses; rejected/incomplete candidates are not claimed as passing. Completing a task does not require reopening when no eligible work remains.

W3 records tx2 actor0 DVM=0, backward/step=0, unchanged Adam/weights and identity factor. W5 records exact pre-reset terminal keys `(0,0,298)` and `(1,0,298)` in tx150; W6 records fresh learned tx151. R14 config retains the actual 30-second / 300-step environment horizon, distinct from rollout T=2. Process quiescence is supported by wait/PID absence; no nonexistent shutdown marker is inferred.

Evidence roots: [R14 raw evidence](E:/Project/IsaacLab_HARL/source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/202609/20260923/b2_t4_re6_r14_artifacts/b2-t4-re6-r14-20260923-formal01-d21c8c835a4944af8395b7a03dee5b6c), [CKPT1 retained qualification](E:/Project/IsaacLab_HARL/source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/202609/20260923/b2_t4_ckpt1_artifacts), [RE1 continuity](E:/Project/IsaacLab_HARL/source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/202609/20260910/PHASE_B2_T0_RE1_BOUNDED_REPEATED_UPDATE_CONTINUITY_REPORT.md), [CSR1 scope reduction](E:/Project/IsaacLab_HARL/source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/202609/20260923/PHASE_B2_T4_CSR1_CLOSURE_SCOPE_REDUCTION_REPORT.md), [HR1 reconciliation](E:/Project/IsaacLab_HARL/source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/202609/20260924/PHASE_B2_T4_CKPT2_R6_HR1_HISTORICAL_R5_ARTIFACT_DRIFT_RECONCILIATION_REPORT.md).

## 3. Source-first findings

### Lifecycle and runtime authority

L1 checks NEEDS_ASSIGNMENT, AVAILABLE/unowned tasks, duplicate claims and failed-pair exclusion before ownership changes. L3 resolves proposals, commits zero/one claim batch, and admits the physical step from the final P2 publication. Original actor proposals/log probabilities remain learner inputs; effective controller assignments are separate.

L2 derives completion, release, cumulative failed pairs, team infeasibility and next robot state. Completion clears ownership; failure/forced release/unavailability releases unfinished work; eligible surviving robots can claim it through the same authority. This is legal release-and-reclaim semantics, not an unsupported inference that every owner change is a reassignment event. Failed pairs persist within the episode and clear on episode rebuild. Disturbance performance/measurement belongs to paper experiments.

L4 makes DVM true only on policy decision rows. Forced continuation exposes the owned task as a singleton action, without becoming a sampled decision. Waiting/unavailable/no-legal-target rows are forced no-op. Available-action masks, active masks and DVM are not interchangeable. E1 captures historical terminal facts before E2's automatic reset; current reset observations cannot replace that history.

### Real update, repetition and quiescence

The current equivalent of the design's update coordinator is the **real adapter plus `execute_full_learner_transaction_v1` and the S0-S10 state machine** (T5-T7), not a class-name assumption or stock HARL training loop.

T1 derives actor counts from nonempty frozen active-and-DVM minibatches. T2 uses the original behavior logprob for PPO ratios, clipped surrogate/entropy and sequential factor accumulation; zero-plan actors skip mutation while preserving prior factor. T3 applies live ValueNorm to the same raw target before critic loss/backward/Adam; valid-zero connected gradients remain legal. T4 separates timeout bootstrap from trace termination and both true-terminal categories from ordinary continuation.

T5 freezes inputs/plan, sequences actors then critic, audits mutations, restores rollout mode, rolls critic buffer, resets terminal ledger, rolls actor storage, and checks S10 gradients/cursors/permits/poison/compute-once reset. T6 accepts existing actors/critic/ValueNorm; rollover replaces rollout storage, not optimizers. R14 and RE1 supply persistent-state/Adam evidence across actual repeated calls.

No current additional semantic defect was found in these paths. Older T2's zero progress under its ultra-short fixture is not a normal-horizon defect; T3 and R14 supply the separate horizon/completion evidence.

### Important runner boundary

C2 exposes optimization APIs for the native assignment runner, whose `train()` still delegates to its inherited HA path. The validated event learner is T5/T6. **Do not assume calling generic `runner.run()` or `restore()` activates event updates or resumes its loop index/LR.** A paper campaign entry must explicitly retain the reviewed event coordinator and consume saved progression. This is a paper-entry/authorization integration task, not evidence that the reviewed callable backbone is semantically broken. This audit does not qualify or activate the public route.

## 4. Phase-B claim matrix

Source IDs resolve in section 11 and in the JSON source catalog. “Must block” refers to closure now; rows17-21 are all parts of the same B1 smoke, not five new defects.

| Phase-B capability | Current implementation | Best direct evidence | Source inspected | Status | Must block closure? |
|---|---|---|---|---|---|
| 1. Lifecycle claim/continue/complete/release/reassign | P2-only claim and lifecycle authority; release reopens eligible rows, reassignment is a later legal claim, not an actor-side owner overwrite | R14 W1/W2 and raw lifecycle steps 23/30/31; inherited reviewed lifecycle contracts. Disturbance campaign performance not claimed. | L1, L2, L3 | SUFFICIENT_FOR_PHASE_B | NO |
| 2. Proposal/effective separation | Proposal resolution commits zero/one claim batch; physical step uses final P2 | R14 raw_action_ids vs effective_assignment, W7 160 immutable updates; R7 inherited interface contracts | L3, L4 | CLOSED | NO |
| 3. Asynchronous event-gated decisions | Row-local NEEDS_ASSIGNMENT and legal-target gating; EXECUTING does not resample | RE1 tx2 (0,0,1,0,0,0), tx3 (0,0,0,1,0,0); R14 lifecycle rows | L4, T8 | CLOSED | NO |
| 4. Lifecycle DVM/action admission | DVM iff policy row; action availability does not imply a learner decision | R14 W3: tx2 actor0 DVM=0, backward/step=0, Adam/weights unchanged | L4, T1, T2 | CLOSED | NO |
| 5. Actor PPO and sequential HAPPO factor | Behavior logprob ratio, clipped surrogate, active AND DVM loss, pre/post segment factor | R3/R7 reviewed qualification; RE1 dynamic counts; R14 actor progress/transaction ledger | T1, T2 | CLOSED | NO |
| 6. Critic update | Raw event-return targets; source-faithful clipped/Huber loss; finite connected valid-zero or nonzero gradients | R4/R7 reviewed qualification; R14 1600 critic steps | T3, T5 | CLOSED | NO |
| 7. Event returns | Separate NONE / true-terminal / TIME_LIMIT bootstrap and trace semantics; compute once; returns[:-1] | R14 160 rows each event_returns=1, stock_compute_returns=0; W4/W5 | T4, T5, E1, E2 | CLOSED | NO |
| 8. Live ValueNorm update | Canonical raw minibatch update then two same-state normalizations | R14 1600 live updates and 159 exact learner bridges; installed ValueNorm fields inspected | T3, C4 | CLOSED | NO |
| 9. S0-S10 transaction | Frozen plan, actor then critic, audit, rollout mode, ordered rollover, quiescence | R14 all 160 S7/S8/S9/S10 flags true; R7 real transaction | T5, T6, T7 | CLOSED | NO |
| 10. Repeated learner updates | Same learner handles, transaction-local authority, new rollout | RE1 3 updates; T1 30; T2 300; R14 raw 160 transactions | T5, T6, T8 | CLOSED | NO |
| 11. Persistent in-process optimizer continuity | Passed learner objects are mutated in place; buffer rollover does not reconstruct optimizers | R14 159 bridges: exact state, persistent object identity, collection immutability all true; RE1 actor Adam 0->(5,5,5)->(10,10,15)->(20,15,20), critic 0->10->20->30 | T2, T3, T6 | CLOSED | NO |
| 12. Normal-horizon runtime | 30 seconds / 300 environment steps, independent of rollout T=2 | R14 config plus 160 transactions / 320 physical transitions; T3 horizon authority | E1, T6 | SUFFICIENT_FOR_PHASE_B | NO |
| 13. Terminal/autoreset handling | Environment-owned pre-reset history retained separately from current reset publication | R14 W5 tx150 keys (0,0,298)/(1,0,298), no missing/extra/duplicate; W6 tx151 | E1, E2, T4, T6 | CLOSED | NO |
| 14. Task completion and decision reopening | Complete clears ownership; only eligible work reopens NEEDS_ASSIGNMENT | R14 W2 selected env1 robot1 task10: claim step23/tx12, complete step30/tx15, reopen step31/tx16; raw rows independently inspected | L1, L2, L4 | SUFFICIENT_FOR_PHASE_B | NO |
| 15. Zero-DVM / forced continuation | Skip actor mutation without resetting accumulated factor; critic still updates | R14 W3 plus transaction ledger tx2; source expected_steps==0 branch | T1, T2, T6 | CLOSED | NO |
| 16. Real environment and learner construction | Private event route plus real HARL actors/critic/ValueNorm | R14 and CKPT2-R4/R5 actual construction/learner evidence; not R3 intended counters | T6, T8, H3 | CLOSED | NO |
| 17. Optimization checkpoint save | Complete Adam/model/VN/progression/config state; staged generation and atomic pointer | CKPT1 exact CPU tests 1/3, retained roundtrip/atomicity; no real CUDA checkpoint save yet | C1, C2, C4, Q1 | IMPLEMENTED_BUT_RUNTIME_NOT_ESTABLISHED | YES — B1 |
| 18. Optimization strict load | Validate before mutation; exact compatibility; full rollback / poison on incomplete rollback | CKPT1 tests 1/4/5 and retained rollback result; no successful real B load yet | C1, C2, C3, C4, Q1 | IMPLEMENTED_BUT_RUNTIME_NOT_ESTABLISHED | YES — B1 |
| 19. Fresh-process optimizer continuation | All actor Adam plus critic Adam load implemented | CKPT1 CPU same-input continuation only; all CKPT2/R* stop before successful B update | C1, H3, H4 | NOT_ESTABLISHED | YES — B1 |
| 20. Fresh-process ValueNorm continuation | Project adapter preserves mean, mean-square, debiasing term | CKPT1 CPU exact state and controlled next update only | C1, C4, H3 | NOT_ESTABLISHED | YES — B1 |
| 21. Fresh-process progression/LR continuation | completed/next/total/next-LR position; caller applies next scheduled LR | CKPT1 CPU p=1->2 of12; no real A-to-B proof | C1, C2, H3, H4 | NOT_ESTABLISHED | YES — B1 |
| 22. Clean shutdown and quiescence | S10 plus environment close, process wait and semantic A-to-B gate | R14 process_quiescence/env_close; R1-R5 correctly deny B without checkpoint | T5, T7, H3 | SUFFICIENT_FOR_PHASE_B | NO |
| 23. Full simulator/RNG/rollout exact resume | Excluded: fresh environment/rollout boundary is intentional | CSR1/CKPT1 scope and checkpoint payload inspection | C1 | NOT_REQUIRED_FOR_PHASE_B | NO |
| 24. Public CLI / paper campaign packaging | Dormant public route; use reviewed event coordinator, not stock runner.train/run as an event equivalent | R7 and current separate event/native runner APIs; authorization/packaging not a newly found semantic defect | T5, T6, C2 | FUTURE/PAPER-EXPERIMENT | NO |
| 25. Variable cardinality / Transformer | Not needed for first fixed-scale paper | Current fixed M/N contract | L4, T1 | FUTURE/PAPER-EXPERIMENT | NO |

## 5. Open-item classification

Each issue has exactly one class. A harness prerequisite may prevent an executable smoke without becoming a production defect.

| ID | Class | Remaining work |
|---|---|---|
| B1 | B | Real fresh-process optimization continuation: Real A update -> clean save/exit -> new B strict load -> exact state equality -> real resumed update/S10/exit. Includes CUDA placement and Adam/ValueNorm/progression continuity. |
| C1 | C | R6 historical inventory gate remains stale: HR1 reconciles literal backslash-n vs LF; current R6 still compares the old aggregate. Repair only prospective final-smoke preflight under new authority; do not alter historical R5/R6 evidence. |
| C2 | C | Compact final-smoke orchestration and receipt readiness: Adapt transaction count/start IDs coherently; source-first DTO binding; pure/runtime process isolation; durable semantic A-to-B gate; only a small targeted preflight for changed harness seams. R6 pure checks remain NOT RUN. |
| C3 | C | Effective config and schedule binding in final smoke: Freeze same actual learner config/source in A/B, including initial LR and loss/normalizer knobs. R6's compact semantic dictionary is a bounded fixture, not a generalized compatibility validator; production checkpoint API compares caller-supplied config. |
| C4 | C | Optional forensic/report cleanup: Large inventories, redundant PPQ/Layer-A/Layer-B envelopes, historical per-file reconstruction and diagnostic serialization are advisory unless required to establish B1. Preserve historical STOP labels. |
| D1 | D | Paper experiment protocol and runnable campaign entry: Baseline/ablation/disturbance, multiple fixed M/N, multiseed, canonical metrics/statistics, checkpoint-based evaluation. Explicitly wire reviewed event update and saved progression; do not assume generic inherited runner.run resumes them. Public activation separately authorized. |
| E1 | E | Generalized resume and checkpoint scope: Exact simulator/RNG/mid-rollout restoration, variable cardinality/Transformer, arbitrary inactive/uninitialized-Adam saves and concurrent-writer checkpoint services are outside this fixed-scale clean-boundary closure. |

The source/evidence test of the hypothesis is therefore: lifecycle and event-training paths have closed/bounded direct evidence; normal-horizon evidence is reusable under reviewed CSR1; optimization implementation has exact CPU evidence; **none of the real attempts completed successful B load + resumed update**. This leaves B1, not a newly discovered A item. R6's stale historical gate must not be mistaken for production breakage.

## 6. CKPT2 / R1-R6 root causes

| Attempt | Root cause class | What the STOP actually established | New production defect? |
|---|---|---|---|
| CKPT2 | HARNESS DEFECT; ORCHESTRATION DEFECT | LR hook ran after pre-collection fingerprint; optimizer LR difference tripped collection guard before learner mutation. Parent also trusted exit code 0 after SimulationApp.close and launched B without a checkpoint. | NO |
| R1 | HARNESS DEFECT | Post-return ledger indexed exact_execution_counts['event_return_computations'], an aggregate-only key; one real learner transaction had returned. | NO |
| R2 | HARNESS DEFECT | Ledger read r5_transaction.transaction_id, absent from B2RFullLearnerUpdateEvidenceV1; returned identity is quiescence_evidence.update_id. | NO |
| R3 | HARNESS DEFECT; ORCHESTRATION DEFECT | Synthetic package installation for pure DTO imports polluted the runtime interpreter; Gym could not resolve ScanMobileManipulatorEnv. | NO |
| R4 | HARNESS DEFECT | Valid tx2 actor steps (5,5,10) rejected by fixed (5,5,5) ledger predicate. | NO |
| R5 | HARNESS DEFECT | Pre-mutation observer treated B2RResolvedConfigV1 as Mapping; epoch_count fallback0 caused PRE-MUTATION-PLAN-POLICY. | NO |
| R6 | EVIDENCE/FORENSIC DEFECT | Historical aggregate lock used literal 5c6e while _inventory appended LF0a; stopped before pure child/A/B. | NO |

**Production defects established by these attempts: 0. Exact items: none.** This does not turn the attempts into successes: all retain STOP; no successful real optimization continuation resulted. R1/R2 each returned one real learner transaction and R4 returned two, but evidence hooks prevented checkpoint publication. R5 failed before learner mutation; R6 failed before its pure child or either worker.

These causes are supported by the mismatched field access and Mapping branch in inherited source, actual returned DTO definitions, plan-count construction, parent gate code and retained failure receipts/reports. HR1 reconciled R6's inventory algorithm, not checkpoint content.

## 7. CKPT1 production readiness

Verdict: **CHECKPOINT IMPLEMENTATION READY FOR FINAL SMOKE**.

A. Complete scoped optimization state is represented: every ordered actor weight and Adam state_dict (moments, steps, groups), critic weights and Adam, explicit ValueNorm mutable fields, completed/next/total/LR position and semantic reconstruction config. There is no separate scheduler object in this scoped HARL route.

B. No missing mutable state was identified that would invalidate a passing scoped smoke. Initial LR, schedule enablement, architecture, loss/return/normalizer knobs must be identically reconstructed. The production API compares caller-provided semantic config; it does not magically discover every caller's config. C3 captures native effective runtime parameters; the smaller R6 fixture dictionary is only valid with its same frozen construction/config. Bind actual effective settings in the final harness rather than claiming arbitrary cross-config compatibility.

C. Exact simulator/environment/RNG state is **not required** at the intended clean fresh-rollout boundary. This is optimization continuation, not bit-identical trajectory replay.

D. A fresh environment and fresh buffers/RNN rollout state are valid after the previous update is complete. No partial rollout is resumed and no old terminal ledger/authority is reused. Record the restarted environment/seed protocol for paper reproducibility.

E. **No production checkpoint change is identified as required before the scoped smoke.** Real CUDA serialization/restoration and continued training remain unestablished, which is precisely B1.

C1 rejects dirty/poisoned boundaries before saving, writes components before the manifest, validates readback and atomically publishes generation/pointer. Strict load validates schema/digests/counts/identities/config/shapes/Adam moments/progression before target mutation. Application backups include all models, optimizers, VN and progression; failure rolls back, incomplete rollback poisons. C4 copies explicit VN fields into their existing device-resident objects, not generic Module state.

CKPT1 tests inspected at Q1 compare recursive exact states before/after load and after identical controlled inputs/LR, inject failure after actor-optimizer load, and compare exact rollback. Retained results: 6 tests, 25 expected negative rejections. **Not rerun here.**

Limits are explicit: the validator requires populated Adam states; a never-updated actor's empty state is rejected rather than silently reinitialized. Therefore populate every actor in A before this checkpoint. Generalizing zero-history saves, concurrent writers, configuration migration or exact simulator resume is not required to prove this boundary. Ordinary noncapturable Adam's scalar `step` may remain on CPU; moment tensors must follow target parameter devices.

## 8. R6 direct-plan static audit

Verdict: **R6 DIRECT-PLAN REPAIR STATICALLY SOUND**, limited to the requested receipt/count repair.

H1 installs `_runtime_plan_receipt` over the inherited R5 callback. It reads `expected_actor_backward` and `expected_actor_optimizer_step` directly from the producer payload. The producer (T6) populated them from the frozen actor plan; T1 computed the plan before mutation. `resolved_config` is checked only for provenance/type. No Mapping-only count derivation, epoch-count zero fallback, observed-as-expected path, or fixed `(5,5,5)` **acceptance predicate** remains on that active path.

H2's inherited ledger compares the pre-mutation expected counts with returned audit expectations, actual execution counts and Adam deltas. Historical fixed tuples still occur in diagnostics/fixtures; their presence is not an active acceptance rule. R6 also inherits actual pure/runtime process isolation and H3's semantic A-to-B gate, not return-code-only authorization.

Caveats: the adapter stamps its source/frozen flags and compares a plan digest passed from the same payload. Those checks are not an independent cryptographic provenance oracle; source authority and the production immutable-plan audit provide the trust boundary. R6 pure qualification and real execution remain **NOT RUN**. H1's historical inventory gate is still stale after HR1: unmodified R6 is neither executable-ready nor authorized just because the direct binder is statically sound.

## 9. Minimum final closure experiment

**Recommended minimum: 1 real A update + 1 real resumed B update.** No run is launched or authorized by this recommendation.

Reuse the reviewed fixed event configuration: T/E/M/N=2/2/3/12, independent actors, ValueNorm on, actor/critic 5 epochs and 2 minibatches, a declared nonzero linear-LR horizon (e.g.12). A reviewed checkpoint-focused environment horizon may be reused; normal-horizon behavior is already separately established.

A starts fresh, applies LR position1 before its collection fingerprint, completes one S0-S10 update and verifies all Adam states populated. It saves completed=1 / next=2 / LR position=2 at a declared optimizer-LR snapshot boundary, validates the checkpoint and exits. If LR2 is primed before save, the pre-save comparison snapshot must be taken after priming.

B starts in a separate fresh interpreter with no shared Python learner objects, reconstructs identical effective config, strictly loads **before collecting**, and checks equality before any new mutation. It uses update/LR position2 of12 (not1), collects a new rollout, completes one S0-S10 update and ends with completed=2 / next=3 / LR position=3. Both processes close cleanly.

One A update is enough to make scoped Adam/VN/progression nontrivial; one B update exercises restored state. Repeated in-process updates and rollover were already proven. Neither 3+3 nor another 160-update campaign is necessary. If the all-actors-populated fixture prerequisite is not met, reject it; do not silently expand the run budget. A second B update is optional robustness, not a closure gate.

Required hard gates:

1. **G1** — Same effective fixed-scale event configuration and source in A/B; separate fresh OS processes; no old learner reuse or pure-import namespace pollution.
2. **G2** — A completes one real S0-S10 update, every actor Adam and critic Adam populated, ValueNorm nontrivial, all required learner state finite; expected counts come from each frozen plan.
3. **G3** — Save only at actual S10: no partial update, poison, pending permits, gradients, active optimizer/load or writer. Save does not change learner state.
4. **G4** — One complete checkpoint generation atomically published and strictly validated, including all models/Adam/VN/progression/effective semantic configuration.
5. **G5** — A exits and becomes inactive; parent requires durable semantic success plus validated checkpoint, never exit code alone, before launching B.
6. **G6** — B strictly loads before collecting/training; all model tensors, Adam groups/moments/steps, VN fields and progression equal A's same-boundary snapshot, with correct device placement (ordinary Adam scalar step may stay CPU).
7. **G7** — B uses saved next update p+1 and saved total horizon; nonzero expected LR from original base LR, applied before pre-collection fingerprint; no scheduler restart or LR mutation inside collection.
8. **G8** — One fresh B rollout and real S0-S10 update succeeds under reviewed event-return/DVM contracts; plan-derived actor and critic Adam deltas match actual steps and do not reset; legitimate zero-plan actors remain unchanged.
9. **G9** — B ValueNorm progresses from the loaded state with exactly planned updates; completed/next/LR position advances once; all required learner/optimizer state remains finite.
10. **G10** — B ends at S10, environment/application close and worker inactivity established; durable core results suffice to adjudicate, with no uncontrolled further update/retry.

No new lifecycle/actor-count/event-return/identity theory matrix, exhaustive historical inventory, duplicate forensic envelope, convergence threshold, matched stochastic trajectory, or second checkpoint generation is required.

### Practical repair policy

The proposed policy is **safe only with qualifications**. Before the first learner mutation, explicitly authorized local harness/path/type/serialization/receipt repairs may be logged and fixed in place, then narrowly preflighted and frozen; no new numbered historical phase is necessary. Restart the process if imports/construction were contaminated.

After mutation, do not hot-patch the active learner/harness, alter expectations to match observations, or retry an update. Stop for semantic, checkpoint, restore, optimizer/VN/progression or production-runtime defects. Also stop acceptance when **required core evidence is missing or ambiguous**, or quiescence is unknown: “only semantic failures” cannot safely mean continuing blind. This is a Class-C evidence obstacle, not automatic proof of a Class-A defect.

A purely diagnostic publication error may be repaired offline from immutable sufficient raw evidence without poisoning a demonstrably complete learner. Poison depends on partial/ambiguous mutation or incomplete rollback, not on formatting failure alone. No repair or runtime retry is authorized in this audit; historical labels remain unchanged.

## 10. Definitive exit and paper handoff

1. Lifecycle P2 authority, proposal/effective separation, asynchronous DVM admission and terminal pre-reset semantics remain established. **Current: SATISFIED.**
2. Real persistent actor/critic/Adam/ValueNorm and S0-S10 repeated-update backbone remains established. **Current: SATISFIED.**
3. Normal-horizon ownership, completion/reopen, nonterminal bootstrap, zero-DVM and post-autoreset learning have direct retained evidence. **Current: SATISFIED.**
4. Complete optimization checkpoint format, strict validation, legal save boundary and failed-load safety are implementation-qualified. **Current: SATISFIED (CPU/static; real integration belongs to item5).**
5. Bounded fresh-process final smoke passes G1-G10 with exact restore and resumed optimizer/VN/progression, both processes quiescent; core evidence and source/index preservation handed off for explicit closure review. **Current: OPEN B1.**

No clean-worktree reset or commit is required as a runtime semantic gate. Preserve unrelated work and the pre-existing index; keep a reproducible source/config record and explicit review decision.

After successful closure, begin **paper-1 experiment implementation/protocol and evaluation**, under separate authorization: baseline implementations/evaluation; lifecycle ablations; robot-failure, stuck-task, release/reassign disturbances; separately fixed M/N configurations; prespecified seeds/budgets; completion/coverage, delay/makespan, failure recovery, allocation churn and compute/runtime metrics; uncertainty/statistical reporting; immutable configs and checkpoint-based reproducible evaluation. Do not claim trained policy quality from stability evidence, or exact reassignment counts from ambiguous owner-change proxies. Do not start variable-cardinality Transformer work.

## 11. Source and artifact index

- **L1** — [assignment_initial_claim_runtime.py](E:/Project/IsaacLab_HARL/source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_initial_claim_runtime.py:647): InitialClaimDeriver.derive_candidate (inspected lines 647-777).
- **L2** — [assignment_lifecycle_transaction_runtime.py](E:/Project/IsaacLab_HARL/source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_lifecycle_transaction_runtime.py:2212): LifecycleAuthorityTransactionCoordinator; authority candidate equations (inspected lines 2212-2310;4148-4375;4591-4715).
- **L3** — [assignment_event_runtime_facade.py](E:/Project/IsaacLab_HARL/source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_event_runtime_facade.py:609): step_resolved_proposals (inspected lines 609-716).
- **L4** — [assignment_event_policy_decision.py](E:/Project/IsaacLab_HARL/source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_event_policy_decision.py:569): legal targets, forced rows, decision_valid_mask (inspected lines 569-655).
- **T1** — [assignment_event_training_plans.py](E:/Project/IsaacLab_HARL/source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_event_training_plans.py:443): build_actor_update_plan_v1; factor transition; critic plan (inspected lines 443-561;634-754;869-921).
- **T2** — [assignment_event_training_actor_mutation.py](E:/Project/IsaacLab_HARL/source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_event_training_actor_mutation.py:653): _actor_loss_v1; execute_actor_sequence_v1 (inspected lines 653-685;819-1149).
- **T3** — [assignment_event_training_critic_mutation.py](E:/Project/IsaacLab_HARL/source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_event_training_critic_mutation.py:1103): execute_critic_sequence_v1 (inspected lines 1103-1475).
- **T4** — [assignment_event_gae_returns.py](E:/Project/IsaacLab_HARL/source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_event_gae_returns.py:236): compute_event_gae_returns_v2 (inspected lines 236-442).
- **T5** — [assignment_event_training_full_transaction.py](E:/Project/IsaacLab_HARL/source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_event_training_full_transaction.py:789): execute_full_learner_transaction_v1; validate_quiescence_claim_v1 (inspected lines 789-948;996-1160).
- **T6** — [assignment_event_training_real_isaac_adapter.py](E:/Project/IsaacLab_HARL/source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_event_training_real_isaac_adapter.py:529): execute_real_isaac_single_transaction_v1; pre-mutation observer; real rollover (inspected lines 529-558;638-765;1001-1105;1450-1555).
- **T7** — [assignment_event_training_control.py](E:/Project/IsaacLab_HARL/source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_event_training_control.py:594): S0-S10 state machine and checkpoint eligibility (inspected lines 594-688).
- **T8** — [assignment_event_learned_route.py](E:/Project/IsaacLab_HARL/source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_event_learned_route.py:457): collect_step (inspected lines 457).
- **E1** — [scan_mobile_manipulator_env.py](E:/Project/IsaacLab_HARL/source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py:3100): pre-reset scan/critic snapshot; event termination/reset (inspected lines 3100-3146;3230-3295).
- **E2** — [direct_marl_env.py](E:/Project/IsaacLab_HARL/source/isaaclab/isaaclab/envs/direct_marl_env.py:389): dones/rewards before automatic reset (inspected lines 389-396).
- **C1** — [assignment_optimization_checkpoint.py](E:/Project/IsaacLab_HARL/source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_optimization_checkpoint.py:64): boundary; progression; Adam validation; save/validate/load (inspected lines 64-260;407-465;512-920).
- **C2** — [assignment_harl_training.py](E:/Project/IsaacLab_HARL/source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_training.py:727): runner guard, progression, optimization APIs and LR helper (inspected lines 727-894).
- **C3** — [assignment_checkpoint_save.py](E:/Project/IsaacLab_HARL/source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_checkpoint_save.py:120): semantic manifest construction and effective runtime capture (inspected lines 120-155;207-264;1095-1215).
- **C4** — [assignment_value_normalizer_checkpoint.py](E:/Project/IsaacLab_HARL/source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_value_normalizer_checkpoint.py): export/validate/restore_value_normalizer_checkpoint_state.
- **H1** — [test_assignment_phase_b2_t4_ckpt2_r6_real_fresh_process_checkpoint_continuation.py](E:/Project/IsaacLab_HARL/scripts/environments/test_assignment_phase_b2_t4_ckpt2_r6_real_fresh_process_checkpoint_continuation.py:82): _load_base; _bind_receipt; _runtime_plan_receipt; history gate (inspected lines 82-204;313-389).
- **H2** — [test_assignment_phase_b2_t4_ckpt2_r5_real_fresh_process_checkpoint_continuation.py](E:/Project/IsaacLab_HARL/scripts/environments/test_assignment_phase_b2_t4_ckpt2_r5_real_fresh_process_checkpoint_continuation.py:181): old Mapping bug; current inherited plan ledger and hook installation (inspected lines 181-229;243-303;331-386).
- **H3** — [test_assignment_phase_b2_t4_ckpt2_r1_real_fresh_process_checkpoint_continuation.py](E:/Project/IsaacLab_HARL/scripts/environments/test_assignment_phase_b2_t4_ckpt2_r1_real_fresh_process_checkpoint_continuation.py:84): inherited A/B construction/load, LR boundary, save and semantic launch gate (inspected lines 84-105;341-403;404-465;506-550;707-754).
- **H4** — [test_assignment_phase_b2_t4_ckpt2_real_fresh_process_checkpoint_continuation.py](E:/Project/IsaacLab_HARL/scripts/environments/test_assignment_phase_b2_t4_ckpt2_real_fresh_process_checkpoint_continuation.py:193): state snapshots, Adam device classification, LR helper (inspected lines 193-274;336).
- **Q1** — [test_assignment_phase_b2_t4_ckpt1_optimization_checkpoint.py](E:/Project/IsaacLab_HARL/scripts/environments/test_assignment_phase_b2_t4_ckpt1_optimization_checkpoint.py:211): exact roundtrip, same-input update, atomicity, rollback tests (inspected lines 211-291).

Eight compact audit artifacts:

- [phase_b_claim_matrix.json](phase_b_final_closure_readiness_audit_artifacts/phase_b_claim_matrix.json)
- [open_item_classification.json](phase_b_final_closure_readiness_audit_artifacts/open_item_classification.json)
- [ckpt2_r1_r6_root_cause_summary.json](phase_b_final_closure_readiness_audit_artifacts/ckpt2_r1_r6_root_cause_summary.json)
- [checkpoint_production_readiness.json](phase_b_final_closure_readiness_audit_artifacts/checkpoint_production_readiness.json)
- [r6_direct_plan_static_audit.json](phase_b_final_closure_readiness_audit_artifacts/r6_direct_plan_static_audit.json)
- [minimum_final_closure_experiment.json](phase_b_final_closure_readiness_audit_artifacts/minimum_final_closure_experiment.json)
- [phase_b_exit_criteria.json](phase_b_final_closure_readiness_audit_artifacts/phase_b_exit_criteria.json)
- [final_recommendation.json](phase_b_final_closure_readiness_audit_artifacts/final_recommendation.json)

## 12. Preservation, checks and stop

TASK_PROGRESS was archived **before rewrite**, with byte-exact SHA-256 `fc2c9ad4f36a9ada089548d6add98137f7776cb813864d4aa838926a21adccd2`: [prior handoff](TASK_PROGRESS_ARCHIVE_BEFORE_PHASE_B_FINAL_CLOSURE_READINESS_AUDIT_20260924.md). The new handoff records HR1 as user-reviewed PASS/CLOSED and this audit's actual READY verdict.

Verification is documentation-only: PowerShell JSON parsing and retained-ledger arithmetic, source SHA checks, archive byte equality, output/source-reference existence, and read-only repository/source/index preservation comparison. No tests, production imports, checkpoint tensor reads, CUDA/Isaac/learner execution or checkpoint save/load were performed. Checkpoint JSON reports were read as historical audit evidence, not loaded as model checkpoints.

Final document checks: 8/8 JSON files parse; all 25 claims use the specified status vocabulary; report/handoff local links resolve. The 186-file production/harness/installed-source hash inventory, HEAD and raw git-index hash are unchanged across document writes. No staged migration or unrelated source was modified.

Production/checkpoint/HARL/harness/history modifications: **0/0/0/0/0**. CUDA / Isaac / learner: **0/0/0**. Checkpoint I/O: **0**. Git add/commit/push/reset/checkout/clean: **0/0/0/0/0/0**.

**Next: stop and return this audit for GPT/user review.** Phase B is not declared complete; no R6 retry, R7, R15, public activation, training or evaluation is authorized.
