# Lifecycle-aware Dynamic MRTA — Task Progress

Updated: 2026-09-16

## Current status

```text
B2-R0 through B2-R7: GPT REVIEW PASS / CLOSED
B2-T0 through B2-T3: GPT REVIEW PASS / CLOSED

B2-T4 original: STOPPED / HISTORICAL / NOT COMPLETE
B2-T4-NR: GPT REVIEW PASS / CLOSED
B2-T4-RE1: STOPPED / HISTORICAL / POISONED / NOT COMPLETE
B2-T4-SR: GPT REVIEW PASS / CLOSED
B2-T4-RE2: STOPPED / HISTORICAL / POISONED / NOT COMPLETE
B2-T4-ZD: GPT REVIEW PASS / CLOSED

B2-T4-RE3:
  STOPPED / HISTORICAL / NOT COMPLETE
  NO LEARNER MUTATION / NOT POISONED
  PHASE-B2-T4-RE3-STOP-PRE-ENVIRONMENT-ENTRY-POINT-RESOLUTION-NOT-COMPLETE

B2-T4-EP:
  STOPPED / HISTORICAL / NOT QUALIFIED
  PHASE-B2-T4-EP-STOP-FORMAL-EVIDENCE-PERSISTENCE-ORDERING-NOT-QUALIFIED

B2-T4-EP-P:
  STOPPED / NOT QUALIFIED / AWAITING INDEPENDENT GPT REVIEW
  PHASE-B2-T4-EP-P-STOP-PROCESS-QUIESCENCE-NOT-ESTABLISHED

B2-T4-RE4: NOT AUTHORIZED / NOT STARTED
checkpoint continuation: NOT ESTABLISHED
long training: NOT AUTHORIZED
public learned-policy route: DORMANT / BLOCKED
```

## Latest phase result

B2-T4-EP-P added a new independent test-side worker/supervisor harness that fixes EP's evidence ordering. The worker now persists a digest-bound receipt through unique-temp write, flush, `os.fsync`, atomic replace, and readback before App close; it also persists `env.close()` and `app_close_invoked` facts before calling `SimulationApp.close()`. The outside supervisor binds run ID and child PID and treats exit code as non-authoritative without the receipt and shutdown predicates.

Preflight passed: synthetic success and failure persistence, 12/12 fail-closed supervisor negative cases, stale/wrong-run/temp-only rejection, one fresh-process entry-point regression, and frozen source identity.

Exactly one formal supervisor launched one worker and one AppLauncher, with zero retries. The durable worker receipt passed every worker-side check: CUDA, exact entry point, real two-environment construction, initial reset, structural assertions, pre-App-close `fsync`/readback, `env.close()`, and all zero learner/step counters. The worker returned 0 and PID `15116` disappeared.

The supervisor nevertheless did not observe its required Simulation App shutdown marker in captured stdout/stderr. Thus `shutdown_observed=false` and the composite process-quiescence predicate failed, even though wait completion, return code, PID absence, no matching worker, and no timeout all passed. Per the formal stop rule, no repair or retry was made.

## Active architecture / implementation path

- Environment ID: `Isaac-Scan-Mobile-Manipulator-Direct-v0`
- Exact entry point: `isaaclab_tasks.direct.scan_mobile_manipulator:ScanMobileManipulatorEnv`
- Profile: `event_gated_local_mrta`
- Formal configuration: CUDA `cuda:0`, `num_envs=2`, robots `M=3`, viewpoints `N=12`
- EP-P authority: durable worker receipt plus outside supervisor adjudication
- Production registration/export changes: 0
- Production semantic changes: 0

## Files changed or created

- Created test-side harness: `scripts/environments/test_assignment_phase_b2_t4_ep_p_formal_evidence_persistence_supervisor.py`
- Created `202609/20260916/b2_t4_ep_p_artifacts/` with preflight and sole-formal-run evidence
- Created `202609/20260916/PHASE_B2_T4_EP_P_FORMAL_EVIDENCE_PERSISTENCE_SUPERVISOR_QUALIFICATION_REPORT.md`
- Created byte-exact pre-rewrite archive `202609/20260916/TASK_PROGRESS_ARCHIVE_BEFORE_B2_T4_EP_P_STOP_HANDOFF_20260916.md`
- Rewrote this concise handoff
- Modified production, HARL, or installed `site-packages` files: none

Historical EP artifacts and report were not modified. The EP-P harness and formal artifacts were frozen after the formal STOP.

## Latest verification

```text
py_compile of EP-P harness: PASS before formal run
preformal pure/static Python invocations: 11
synthetic worker persistence processes: 6
synthetic persisted success/failure exemplars: 2
supervisor negative cases: 12 / 12 fail closed
fresh-process entry-point regression: 1 / 1 PASS
formal supervisors / workers / retries: 1 / 1 / 0
CUDA readiness / AppLauncher / environment construction / reset: 1 / 1 / 1 / 1
worker receipt schema/run/PID/digest/success checks: PASS
worker receipt pre-App-close / fsync / readback / env.close: PASS / PASS / PASS / PASS
worker wait complete / return code / PID absent / timeout: true / 0 / true / false
shutdown marker observed / composite process quiescence: false / false
physical environment steps: 0
persistent learner constructions / mutations / updates: 0 / 0 / 0
actor backward/step / critic backward/step / ValueNorm updates: 0/0 / 0/0 / 0
checkpoint I/O / public activation / evaluation-playback: 0 / 0 / 0
B2-T4-RE4 started: 0
git add / commit / push: 0 / 0 / 0
```

Formal receipt SHA-256: `47b5a5156b95c6a829bb45d6dd844a1e281221d1aef2b15cd301b28c033f4af0`.

Protected hashes remained exact:

- `assignment_event_training_full_transaction.py`: `a45db23b863c51334b15205b3c50fa5997ab8f5e4a32f8c4a801242365b583d7`
- `assignment_event_training_real_isaac_adapter.py`: `57419d52caa77160609f77b289979ed6785fc645eab1b17320e9cbda1e9500ac`
- scan environment: `f96f6b6e9a530cd0b438344a11dc67670559206f3521d641d776d4bd475c6363`
- EP-P harness: `82491e3200ad8106f4d5d447f40fef02e0e1fa4399feac29b12abe277a85b6c6`

## Repository preservation

Branch `main`; `HEAD`, `origin/main`, and merge-base remain `b71d85a32f51be6ada324f870813a56bb45dd396`. The pre-existing staged monthly migration remains 359 paths with staged-index SHA-256 `a40169043c3bfffd481a7ed1bddf3e52663d61379bedfd2610781457d11f947c` and monthly path-set SHA-256 `0f2b8f7b52148e39196cbeb40fd9f4edd94fb762b6daf8be6279a116b80a39ab`.

The byte-exact pre-rewrite archive is 6,518 bytes with SHA-256 `aeaf42a36ded14c513c70495ddd18e6096b78a1338f2b8f0b4bddcc6f01604fc`.

No `git add`, commit, push, reset, checkout, or clean operation occurred.

## Known issue / blocker

The formal supervisor contract required both process disappearance and observation of the Simulation App shutdown marker in captured worker output. The sole formal worker fully terminated, but the marker was absent from captured streams. The already-adjudicated formal result must remain STOP; it cannot be repaired or retried under EP-P.

## Do not do

Do not patch the frozen EP-P harness or formal artifacts, retry AppLauncher, start B2-T4-RE4, construct a learner, perform checkpoint I/O, activate the public learned-policy route, run evaluation/playback, or start long/paper-scale training without new explicit authorization.

## Next step

Await independent GPT review of the preserved B2-T4-EP-P STOP. Any revised shutdown-observation contract or new formal attempt requires a new explicit instruction.

## Detailed reports / archives

- `202609/20260916/PHASE_B2_T4_EP_P_FORMAL_EVIDENCE_PERSISTENCE_SUPERVISOR_QUALIFICATION_REPORT.md`
- `202609/20260916/b2_t4_ep_p_artifacts/formal_worker_receipt.json`
- `202609/20260916/b2_t4_ep_p_artifacts/formal_supervisor_result.json`
- `202609/20260916/b2_t4_ep_p_artifacts/reset_structural_evidence.json`
- `202609/20260916/b2_t4_ep_p_artifacts/process_quiescence.json`
- `202609/20260916/b2_t4_ep_p_artifacts/final_result.json`
- `202609/20260916/TASK_PROGRESS_ARCHIVE_BEFORE_B2_T4_EP_P_STOP_HANDOFF_20260916.md`
- `202609/20260915/PHASE_B2_T4_EP_ENVIRONMENT_ENTRY_POINT_REGISTRATION_BOUNDARY_QUALIFICATION_REPORT.md`
- `202609/20260915/PHASE_B2_T4_RE3_NORMAL_HORIZON_LEARNED_TRAINING_INTEGRATION_QUALIFICATION_REPORT.md`
