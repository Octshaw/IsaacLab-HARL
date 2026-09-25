# Lifecycle-aware Dynamic MRTA — TASK_PROGRESS

Updated: 2026-09-21

## Current status

B2-T4-PPQ-V2-R1 is **COMPLETE / AWAITING GPT REVIEW**, classification `PHASE-B2-T4-PPQ-V2-R1-FORMAL-SOURCE-PHASE-BINDING-GENERALIZED-AWAITING-GPT-REVIEW`.

The pure/offline candidate replaces concrete attempt-name enumeration only in the new v2.1 contract. Formal-shaped success now requires exact equality among `receipt.source_phase`, the caller expectation, and one externally supplied authority instance, plus a run-specific binding across authority digest, phase, run ID, worker PID, config digest, and artifact namespace. Formal, synthetic qualification, and historical replay modes are separate. Grammar is necessary but never sufficient authority.

PPQ-V2 remains **GPT REVIEW PASS / CLOSED** with its original source-phase scope unchanged. LAQ-R1 remains **GPT REVIEW PASS / CLOSED**. Historical RE6-R4 remains **GPT REVIEW STOP CONFIRMED / PRE-RUNTIME / FORMAL ATTEMPTS 0 / NOT POISONED**. RE6-R3 remains historical and poisoned; never reuse its learner.

RE6-R5 is **NOT AUTHORIZED**. Checkpoint continuation is **NOT ESTABLISHED**; long/paper-scale training is **NOT AUTHORIZED**; the public learned-policy route remains **DORMANT / BLOCKED**.

## Latest completed work

- Added the pure helper `scripts/environments/_assignment_phase_b2_t4_ppq_v2_r1_phase_binding.py`.
- Added the pure qualification runner `scripts/environments/test_assignment_phase_b2_t4_ppq_v2_r1_phase_binding.py`.
- Preserved all old PPQ-V2 non-phase predicates by import/composition through a phase/identity-only legacy projection; no old global or `FRESH_PHASES` monkeypatch was used.
- Defined strict canonical authority and run-binding schemas, non-circular SHA-256 construction, exact path/content policy, formal phase grammar, namespace binding, and a four-field receipt delta.
- Passed 3/3 formal-shaped offline positives, including R5 and R17, and 34/34 authority negatives with unexpected PASS = 0.
- Reproduced the frozen old PPQ-V2 R4 `PPQV2Stop: SOURCE-PHASE` result exactly.
- Passed offline capability fixtures for R4 and future R5, and attempt-number decoupling for R5/R6/R17/R101. These are contract capabilities, not runtime grants.
- Passed one non-phase positive replay and seven representative non-phase negative categories.
- Froze helper, runner, receipt schema, authority schema, and registry before the final controls.
- Executed exactly one frozen durable positive dry run and exactly one subsequent decisive authority-digest negative, which STOPPED as expected.
- Verified protected production, PPQ-V2, LAQ-R1, W2E/W2I/PW, normalizer, historical R1/R2/R3/R4, and failed-LAQ identities before and after: modifications 0.

## Exact execution boundary

- approved-interpreter Python invocations: 8, including one expected fail-closed development check;
- `py_compile` invocations: 2, both PASS;
- positive formal fixtures: 3/3 PASS;
- phase-authority negatives: 34/34 STOP, unexpected PASS 0;
- attempt-number decoupling: 4 authorized PASS and 4 unauthorized STOP;
- non-phase positive/negative replays: 1 PASS / 7 STOP;
- final frozen positive dry runs: exactly 1;
- final decisive negative controls: exactly 1;
- AppLauncher/environment/learner/CUDA/formal worker: 0/0/0/0/0;
- RE6-R5 formal attempts: 0;
- checkpoint/public activation/evaluation-playback: 0/0/0;
- production/old PPQ-V2/LAQ-R1/historical R4 modifications: 0/0/0/0;
- git add/commit/push: 0/0/0.

## Frozen candidate identities

- helper SHA-256: `bd057efaeac73154b49b1e8307c9c7585f0feb449aaad3fbf4813a361a31b8a0`
- runner SHA-256: `fe420687da10b82df4c66e376cd6959f3d0199553e706f3f4eacd23d79e15433`
- receipt schema SHA-256: `d9e28e050616bc1e2f38abfdc32d21ba884b282311d6f141a1c240632582adef`
- phase-authority schema SHA-256: `874bc9dee78d9d118878bdc7ea3357b70daff1715f098d8876c9d69011938c3e`
- phase-authority registry SHA-256: `534f7561a8ceb9567e37793a14a74b1ca023ae2c479f7e3128bbf60a5e55ddd2`
- final positive receipt SHA-256: `1812304af102cc0e6c81323eeb8179e9a961c6d587fd73a2bcfb3e150c3e35da`

## Key files

- [Detailed PPQ-V2-R1 report](202609/20260921/PHASE_B2_T4_PPQ_V2_R1_FORMAL_SOURCE_PHASE_BINDING_GENERALIZATION_REPORT.md)
- [PPQ-V2-R1 machine evidence](202609/20260921/b2_t4_ppq_v2_r1_artifacts/)
- [Final result](202609/20260921/b2_t4_ppq_v2_r1_artifacts/final_result.json)
- [Candidate identity manifest](202609/20260921/b2_t4_ppq_v2_r1_artifacts/ppq_v2_r1_source_identity_manifest.json)
- [Negative matrix](202609/20260921/b2_t4_ppq_v2_r1_artifacts/source_phase_authority_negative_matrix.json)
- [Final positive result](202609/20260921/b2_t4_ppq_v2_r1_artifacts/final_positive_dry_run_result.json)
- [Final decisive negative](202609/20260921/b2_t4_ppq_v2_r1_artifacts/final_decisive_negative_control.json)

## Known issues / blockers

No PPQ-V2-R1 qualification failure remains. The only gate is independent GPT review. This candidate does not itself authorize a live phase authority, RE6-R5, a worker, an environment, or a learner.

## Do not do

Do not modify the frozen PPQ-V2-R1 helper, runner, schemas, or registry before review. Do not modify old PPQ-V2 or LAQ-R1, reclassify/rerun historical R4, reuse the R3 learner, launch RE6-R5, start AppLauncher/environment/learner, perform checkpoint I/O, begin evaluation/playback or long training, activate the public route, stage, commit, or push without separate authorization.

## Next step

Independent GPT review of B2-T4-PPQ-V2-R1. If and only if it receives review pass and a later instruction separately authorizes RE6-R5, use the reviewed v2.1 helper with an exact reviewed R5 authority instance and a supervisor-created unique run binding. Do not launch RE6-R5 from this handoff.

## Detailed reports / archives

- [PPQ-V2-R1 generalization report](202609/20260921/PHASE_B2_T4_PPQ_V2_R1_FORMAL_SOURCE_PHASE_BINDING_GENERALIZATION_REPORT.md)
- [Byte-exact pre-PPQ-V2-R1 archive](202609/20260921/TASK_PROGRESS_ARCHIVE_BEFORE_B2_T4_PPQ_V2_R1_20260921.md), 4,903 bytes, SHA-256 `f9938df9089334dbfd03922b95aa4baafaf0f33cd62cc5143f6273f2404f7c88`
- [RE6-R4 pre-runtime STOP report](202609/20260921/PHASE_B2_T4_RE6_R4_LAQ_R1_BOUND_NORMAL_HORIZON_LEARNED_TRAINING_INTEGRATION_QUALIFICATION_REPORT.md)
- [LAQ-R1 review candidate report](202609/20260921/PHASE_B2_T4_LAQ_R1_RAW_RECEIPT_AUTHORITY_BINDING_REQUALIFICATION_REPORT.md)
