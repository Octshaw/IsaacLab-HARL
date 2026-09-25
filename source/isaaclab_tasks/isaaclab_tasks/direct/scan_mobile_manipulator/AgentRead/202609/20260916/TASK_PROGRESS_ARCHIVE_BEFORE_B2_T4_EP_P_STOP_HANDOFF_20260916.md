# Lifecycle-aware Dynamic MRTA — Task Progress

Updated: 2026-09-15

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
  STOPPED / NOT QUALIFIED / AWAITING INDEPENDENT GPT REVIEW
  PHASE-B2-T4-EP-STOP-FORMAL-EVIDENCE-PERSISTENCE-ORDERING-NOT-QUALIFIED

entry-point root cause: QUALIFIED
test-side import-order repair: APPLIED; pure fresh-process matrix PASS
real environment construction: REACHED ONCE
reset / complete structure / structured clean close: NOT ESTABLISHED
learner construction / mutation: 0 / 0
B2-T4-RE4: NOT AUTHORIZED
checkpoint continuation: NOT ESTABLISHED
long training: NOT AUTHORIZED
public learned-policy route: DORMANT / BLOCKED
```

## Latest phase result

B2-T4-EP proved the RE2-versus-RE3 cause. RE3's former module-scope ZD import traversed ZD→NR/R5→R1 and installed file-less, spec-less synthetic `isaaclab_tasks` package shells before AppLauncher. The later canonical import hit those cached shells, so the real scan package initializer never exported `ScanMobileManipulatorEnv`. RE2 did not import ZD at module scope and reached AppLauncher with the task package absent.

The production registration/export contract was already correct: ID `Isaac-Scan-Mobile-Manipulator-Direct-v0`, entry point `isaaclab_tasks.direct.scan_mobile_manipulator:ScanMobileManipulatorEnv`, package export at `scan_mobile_manipulator/__init__.py:15`, and canonical class definition at `scan_mobile_manipulator_env.py:1468`. Production registration/export changes were 0. The minimal test-side repair moved the ZD import into RE3's pure readiness function.

Four independent positive pure processes passed canonical, repaired-RE3, repeated repaired-RE3, and RE2 comparison sequences. One negative process passed wrong-attribute, wrong-module, and missing-registration diagnostics. The repaired RE3 sequence left all relevant task-package modules absent before canonical registration.

The sole formal EP process launched one AppLauncher and reached one real 2-environment construction. Kit logged normal shutdown. However, the test wrote its formal/reset/close receipts after `SimulationApp.close()`, and that close ended the process before the writes. Because the caught-exception path used the same ordering, exit code 0 cannot establish reset success or all structural assertions. The required evidence is therefore STOP, and no retry was made.

## Files changed or created

- Modified test-side RE3 runner: `scripts/environments/test_assignment_phase_b2_t4_re3_normal_horizon_learned_training_integration.py`
- Created dedicated EP test: `scripts/environments/test_assignment_phase_b2_t4_ep_environment_entry_point_registration_boundary.py`
- Created EP report and `202609/20260915/b2_t4_ep_artifacts/`
- Rewrote this handoff after creating a byte-exact archive
- Production semantic files changed: 0
- Production registration/export files changed: 0
- Installed `site-packages` files changed: 0

## Verification and exact counts

```text
py_compile of RE3 and EP tests: PASS
pure/static Python invocations: 11
fresh-process entry-point probes: 8
successful fresh-process entry-point probes: 7
failed diagnostic probes: 1
positive resolution matrix: 4 / 4 PASS
negative diagnostic cases: 3 / 3 PASS
formal AppLauncher smokes / lifetimes / retries: 1 / 1 / 0
environment constructions: 1
initial reset: NOT ESTABLISHED
physical environment steps: 0
persistent learner constructions / updates: 0 / 0
actor backward/step: 0 / 0
critic backward/step: 0 / 0
ValueNorm updates: 0
checkpoint I/O / public activation / evaluation-playback: 0 / 0 / 0
B2-T4-RE4 started: 0
git add / commit / push: 0 / 0 / 0
```

Protected production hashes remained exact:

- `assignment_event_training_full_transaction.py`: `a45db23b863c51334b15205b3c50fa5997ab8f5e4a32f8c4a801242365b583d7`
- `assignment_event_training_real_isaac_adapter.py`: `57419d52caa77160609f77b289979ed6785fc645eab1b17320e9cbda1e9500ac`

## Repository preservation

Branch `main`, HEAD/origin/main/merge-base `b71d85a32f51be6ada324f870813a56bb45dd396`. The staged monthly migration remains 359 paths with staged-index SHA-256 `a40169043c3bfffd481a7ed1bddf3e52663d61379bedfd2610781457d11f947c` and monthly path-set SHA-256 `0f2b8f7b52148e39196cbeb40fd9f4edd94fb762b6daf8be6279a116b80a39ab`.

The byte-exact pre-rewrite archive is `202609/20260915/TASK_PROGRESS_ARCHIVE_BEFORE_B2_T4_EP_EVIDENCE_STOP_HANDOFF_20260915.md`: 6,313 bytes, SHA-256 `4c24b466df137e41828d2db7df4fa670a0541d450fb2bf8c7f9b24b67a283ac7`.

No `git add`, commit, push, reset, checkout, or clean operation occurred.

## Known issue / blocker

The formal worker must persist success/failure and reset evidence before App close, with a separate supervisor adjudicating process exit and shutdown. That redesign and any new AppLauncher attempt require new explicit authorization. The existing sole formal attempt must not be retried under B2-T4-EP.

## Detailed reports / archives

- `202609/20260915/PHASE_B2_T4_EP_ENVIRONMENT_ENTRY_POINT_REGISTRATION_BOUNDARY_QUALIFICATION_REPORT.md`
- `202609/20260915/b2_t4_ep_artifacts/registration_source_trace.json`
- `202609/20260915/b2_t4_ep_artifacts/source_identity_manifest.json`
- `202609/20260915/b2_t4_ep_artifacts/fresh_process_resolution_matrix.json`
- `202609/20260915/b2_t4_ep_artifacts/re2_re3_import_comparison.json`
- `202609/20260915/b2_t4_ep_artifacts/formal_environment_smoke.json`
- `202609/20260915/b2_t4_ep_artifacts/reset_structural_evidence.json`
- `202609/20260915/b2_t4_ep_artifacts/final_result.json`
- `202609/20260915/TASK_PROGRESS_ARCHIVE_BEFORE_B2_T4_EP_EVIDENCE_STOP_HANDOFF_20260915.md`
- `202609/20260915/PHASE_B2_T4_RE3_NORMAL_HORIZON_LEARNED_TRAINING_INTEGRATION_QUALIFICATION_REPORT.md`

## Next step

Await independent GPT review of the B2-T4-EP STOP. Do not retry AppLauncher, start B2-T4-RE4, construct a learner, begin B2-R6, perform checkpoint I/O, activate the public learned-policy route, run evaluation/playback, or begin long/paper-scale training without new explicit authorization.
