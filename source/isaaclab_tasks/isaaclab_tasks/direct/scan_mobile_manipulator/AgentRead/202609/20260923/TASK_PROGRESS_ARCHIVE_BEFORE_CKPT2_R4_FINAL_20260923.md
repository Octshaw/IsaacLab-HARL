# TASK_PROGRESS

## Current status

Phase `B2-T4-CKPT2-R4` is active at the pre-runtime boundary. The R4 harness is implemented and syntax/import-isolation checks pass. The one authorized real CUDA/Isaac continuation attempt has **not started** yet.

## Latest completed work

- Preserved CKPT2/R1/R2/R3 as historical evidence; no historical harness, artifact, or report was edited.
- Added an import-isolated R4 harness with one orchestration parent, one clean-interpreter baseline child, one pure production-schema qualification child, and fresh A/B worker interpreters.
- Kept the R3 `ONE_TO_ONE_BOUND`, CASE C ledger, returned `update_id`, and `transaction.real_audit.event_return_compute_count` contracts.
- Added real package identity, Gym registration, and environment-creation gates after AppLauncher initialization and before/after `gym.make`.

## Active architecture / implementation path

- Parent: standard-library orchestration and side-effect-free harness definitions only.
- Pure qualification: short-lived subprocess; it may reproduce the R3 synthetic-package failure and inspect production dataclasses, then must exit before A.
- Runtime A/B: no synthetic package shims; import the real registered task package after AppLauncher.
- A owns tx001-tx003 and one checkpoint save. B is allowed only after A's semantic gate and owns tx004-tx006 with one checkpoint load.
- Retry budget: zero. Once A starts, no source edits or repair are authorized.

## Key files

- `scripts/environments/test_assignment_phase_b2_t4_ckpt2_r4_real_fresh_process_checkpoint_continuation.py`
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/202609/20260923/b2_t4_ckpt2_r4_artifacts/`
- Planned report: `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/202609/20260923/PHASE_B2_T4_CKPT2_R4_REAL_FRESH_PROCESS_CHECKPOINT_CONTINUATION_REPORT.md`

## Latest verification

- Expected interpreter: `C:\isaacenvs\isaac45_harl\python.exe` — PASS.
- `py_compile` on the R4 harness — PASS.
- CLI help/argument construction — PASS.
- Import-safe transformed runtime construction — PASS; task-package modules before/after: `[]` / `[]`.

## Known issues / blockers

- None at the pre-runtime boundary.
- The real CUDA/Isaac result is not yet known and no success/readiness claim is made.

## Do not do

- Do not edit frozen CKPT2/R1/R2/R3 sources or historical evidence.
- Do not modify CKPT1 production files or installed HARL.
- Do not use same-runtime `sys.modules` cleanup as the isolation mechanism.
- Do not retry R4, start tx007, run R15, evaluation, playback, paper-scale training, or activate the public learned-policy route.
- Do not stage, commit, push, reset, checkout, or clean.

## Next step

Run the CKPT1 focused suite into the R4 artifact root, then launch the R4 parent exactly once. The parent must complete clean/pure subprocess qualification and freeze sources before it creates A. After the attempt, adjudicate without repair/retry, produce the R4 report, and archive this handoff byte-exactly before the final rewrite.

## Detailed reports / archives

- `AgentRead/202609/20260923/TASK_PROGRESS_ARCHIVE_BEFORE_CKPT2_R4_START_20260923.md` — byte-exact pre-R4-start handoff archive.
- `AgentRead/202609/20260923/PHASE_B2_T4_CKPT2_R3_REAL_FRESH_PROCESS_CHECKPOINT_CONTINUATION_REPORT.md` — historical R3 STOP report.
