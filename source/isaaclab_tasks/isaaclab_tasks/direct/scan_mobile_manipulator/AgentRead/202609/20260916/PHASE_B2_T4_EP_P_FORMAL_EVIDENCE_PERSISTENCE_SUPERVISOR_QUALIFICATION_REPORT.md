# Phase B2-T4-EP-P — Formal Evidence Persistence and Supervisor Qualification Report

Date: 2026-09-16  
Final classification: `PHASE-B2-T4-EP-P-STOP-PROCESS-QUIESCENCE-NOT-ESTABLISHED`

## A. Repository authority

The repository remained on branch `main`. `HEAD`, `origin/main`, and their merge-base were all `b71d85a32f51be6ada324f870813a56bb45dd396`. The pre-existing monthly archive migration remained staged as exactly 359 paths. Its staged-index SHA-256 remained `a40169043c3bfffd481a7ed1bddf3e52663d61379bedfd2610781457d11f947c`, and its monthly path-set SHA-256 remained `0f2b8f7b52148e39196cbeb40fd9f4edd94fb762b6daf8be6279a116b80a39ab`.

No `git add`, commit, push, reset, checkout, or clean operation was performed.

## B. Starting material reviewed

The complete historical B2-T4-EP report, B2-T4-RE3 report, B2-T4-ZD report, and current `TASK_PROGRESS.md` were read before implementation. Their evidence boundaries were retained. EP-P was treated solely as a test-side evidence-persistence and external-supervisor qualification task; it was not treated as RE4 or as authorization for learner work.

## C. Historical RE3 state

B2-T4-RE3 remains historical, stopped, incomplete, and unpoisoned:

`PHASE-B2-T4-RE3-STOP-PRE-ENVIRONMENT-ENTRY-POINT-RESOLUTION-NOT-COMPLETE`

RE3 performed no learner mutation. EP-P did not rewrite RE3 history or its artifacts.

## D. Historical EP state

B2-T4-EP remains historical, stopped, and not qualified:

`PHASE-B2-T4-EP-STOP-FORMAL-EVIDENCE-PERSISTENCE-ORDERING-NOT-QUALIFIED`

The historical EP report and its formal/reset/final artifacts remained byte-identical:

| Historical file | SHA-256 |
|---|---|
| `PHASE_B2_T4_EP_ENVIRONMENT_ENTRY_POINT_REGISTRATION_BOUNDARY_QUALIFICATION_REPORT.md` | `6c1d247179ee45fe15892765674c0d1e88b4dbe610499035beeebc5876f5e5eb` |
| `b2_t4_ep_artifacts/formal_environment_smoke.json` | `e4271fe6b1f8e38ed992d6abafc1b58adaea2779b2fd6aee5226c767b909c514` |
| `b2_t4_ep_artifacts/reset_structural_evidence.json` | `59091c1507ee8c190b4d59cfc13b2eb3cbfe4b9eef8efc4fc99edb644d47d5f0` |
| `b2_t4_ep_artifacts/final_result.json` | `2a1bc8f7b89bd76a0a5eac22fb1072495f756708c8c84a997271d4090e30fb52` |

## E. Retained root cause

EP's qualified entry-point root cause remains unchanged. RE3's former module-scope ZD import installed synthetic, file-less task-package shells before AppLauncher; the later canonical import encountered those cached shells and did not execute the real scan package initializer. Moving the ZD import into RE3's pure readiness function was the already-qualified minimal test-side repair. Production registration and export code was not defective and was not changed.

## F. Exact prior defect addressed by EP-P

The sole historical EP formal process wrote its formal, reset, and final JSON evidence only after calling `SimulationApp.close()`. That call terminated the process before the writes. The caught-failure path used the same ordering. Consequently, exit code 0 and external Kit output could not establish reset success, complete structure, or structured close.

EP-P was authorized only to repair that evidence-persistence ordering in a new test-side worker/supervisor harness.

## G. Historical EP ordering

In `test_assignment_phase_b2_t4_ep_environment_entry_point_registration_boundary.py`, the historical ordering was:

| Order | Historical operation | Approximate source line |
|---:|---|---:|
| 1 | Create AppLauncher | 593 |
| 2 | Resolve `gym.spec` | 611 |
| 3 | Construct environment with `gym.make` | 666 |
| 4 | Perform initial reset | 682 |
| 5 | Evaluate structural assertions | 711 |
| 6 | Call `env.close()` | 751 |
| 7 | Call `SimulationApp.close()` | 760 |
| 8 | Write formal/reset/final JSON | 772–775 |

The evidence writes therefore had no reliable opportunity to execute after application close.

## H. EP-P ordering

The new independent test-side harness, `scripts/environments/test_assignment_phase_b2_t4_ep_p_formal_evidence_persistence_supervisor.py`, has frozen SHA-256 `82491e3200ad8106f4d5d447f40fef02e0e1fa4399feac29b12abe277a85b6c6`.

Its intended and worker-observed order was:

| Order | EP-P operation | Formal evidence |
|---:|---|---|
| 1 | Construct receipt payload | PASS |
| 2 | Write a uniquely named temporary file | PASS |
| 3 | Flush and `os.fsync` | PASS |
| 4 | Close temp handle and atomically `os.replace` | PASS |
| 5 | Read final envelope and validate digest/equality | PASS |
| 6 | Call `env.close()` | PASS |
| 7 | Persist the env-close update | PASS |
| 8 | Persist `app_close_invoked=true` | PASS |
| 9 | Call `SimulationApp.close()` | invoked |
| 10 | External supervisor validates receipt and process | receipt PASS; shutdown predicate FAIL |

There are zero mandatory evidence writes after `SimulationApp.close()`.

## I. Receipt schema

The formal receipt uses an outer envelope with `schema_version`, `payload`, and `payload_sha256`. The payload binds phase, run ID, worker PID, worker status, classification, configuration, entry-point identity, reset/structure facts, receipt durability facts, close facts, and zero-learner/zero-step counters.

The formal run ID was `b2-t4-ep-p-20260916-formal01-96eeee85a87243989f7223289db785ee`; the worker PID was `15116`.

## J. Atomic persistence contract

The persistence sequence is unique-temp write → flush → `os.fsync` → handle close → atomic `os.replace` → final-file readback → envelope digest and payload-equality validation. The final formal worker receipt exists with SHA-256 `47b5a5156b95c6a829bb45d6dd844a1e281221d1aef2b15cd301b28c033f4af0`. No temporary receipt is accepted as authoritative.

## K. Supervisor authority

The formal supervisor runs outside the AppLauncher worker. It binds the expected run ID and actual child PID; validates envelope, payload schema, digest, success flags, zero exit, and zero forbidden counters; waits for the child; and separately adjudicates process quiescence. Only the supervisor may issue the overall formal classification.

## L. Exit-code nonauthority

Exit code 0 alone is explicitly non-authoritative. A successful classification additionally requires a valid matching receipt, all required success flags, and process-quiescence evidence. This distinction is material here: the worker returned 0 and its receipt qualified, but the overall result still stopped.

## M. Pure synthetic success

The synthetic success worker exited 0, persisted a complete receipt with no remaining temp files, and passed envelope, run-ID, PID, digest, configuration, reset, structure, close, durability, and zero-mutation validation. It demonstrated the success persistence path without Isaac Lab or AppLauncher.

## N. Pure synthetic failure

The synthetic failure worker exited 17 and durably persisted a structured failure receipt with `SyntheticFailure` and the intentional failure witness. The supervisor preserved the failure classification and did not reinterpret the nonzero exit as missing evidence. No temp files remained.

## O. Supervisor negative matrix

All 12 fail-closed cases passed:

| Case | Expected supervisor result |
|---|---|
| digest mismatch | malformed receipt STOP |
| malformed JSON | malformed receipt STOP |
| missing receipt | receipt not persisted STOP |
| nonzero exit plus success receipt | exit/receipt conflict STOP |
| stale previous attempt | run-ID mismatch STOP |
| success receipt with learner mutation | learner mutation nonzero STOP |
| success receipt with reset false | reset not qualified STOP |
| success receipt with structure false | structural assertion failed STOP |
| temp file without final replace | receipt not persisted STOP |
| wrong PID | PID mismatch STOP |
| wrong run ID | run-ID mismatch STOP |
| wrong schema | wrong schema STOP |

## P. Stale and wrong-run isolation

Stale-previous-attempt and wrong-run-ID receipts both failed closed on run-ID mismatch. A temp-only write without final atomic replace was treated as no persisted receipt. Thus neither stale final evidence nor incomplete temporary evidence can qualify a new attempt.

## Q. Entry-point regression

One fresh-process regression passed. `gym.spec` resolved exactly to `isaaclab_tasks.direct.scan_mobile_manipulator:ScanMobileManipulatorEnv`; the package export and defining-module class identities matched; and the repaired RE3 pre-AppLauncher module state remained unpolluted.

## R. Source identities

The preformal source identity manifest passed. Frozen identities were:

| Source | SHA-256 |
|---|---|
| root task initializer | `e10fe2f377265733b534b38ea85b5e83c8ec3d116a49376a445410d69f8ab0d9` |
| direct initializer | `29f633f50248f8d7c6827e64b9036c8a88cc58680cffc0bacce8d5e4bfc02907` |
| scan package initializer | `c72daa4adfdbc2d98265956207ee5b75e53c3dbf92ad58b64b915b13a0e9ff46` |
| scan environment | `f96f6b6e9a530cd0b438344a11dc67670559206f3521d641d776d4bd475c6363` |
| repaired RE3 runner | `02fcba5b1798c9c77be0af7d9ae4de9ce1ea7c392e9ea69c1cf52eb1e33f0ce1` |
| protected full transaction | `a45db23b863c51334b15205b3c50fa5997ab8f5e4a32f8c4a801242365b583d7` |
| protected real adapter | `57419d52caa77160609f77b289979ed6785fc645eab1b17320e9cbda1e9500ac` |
| EP-P worker/supervisor | `82491e3200ad8106f4d5d447f40fef02e0e1fa4399feac29b12abe277a85b6c6` |

Production registration Git status was clean. The manifest itself has SHA-256 `23cabdf0383305a366b968d3843985482ef8b6628694a10d67a41b83b5bcef6e`.

## S. Formal worker launch

Exactly one external formal supervisor launched exactly one formal worker with retry count 0. The worker PID was `15116`. The worker completed with return code 0, and no second formal attempt was made.

## T. CUDA readiness

The sole CUDA readiness probe passed on `cuda:0`, including the recorded matrix multiplication result `[[7.0, 10.0], [15.0, 22.0]]`.

## U. AppLauncher lifetime

Exactly one AppLauncher lifetime was created. The worker receipt records `app_launcher_started=true` and `app_close_invoked=true`. No retry or second lifetime occurred.

## V. `gym.spec` qualification

`gym.spec` passed and resolved the exact required entry point `isaaclab_tasks.direct.scan_mobile_manipulator:ScanMobileManipulatorEnv`. The resolved class was `ScanMobileManipulatorEnv` in the canonical defining module.

## W. Environment construction

Exactly one real environment construction passed with `num_envs=2`, profile `event_gated_local_mrta`, and device `cuda:0`. The outer environment type was `gymnasium.wrappers.common.OrderEnforcing`; the unwrapped type was the canonical `ScanMobileManipulatorEnv`.

## X. Initial reset

The worker durably established `reset_attempted=true` and `reset_pass=true` before App close. The reset evidence records episode-generation shape `[2]` with values `[0, 0]`. This repairs EP's evidence gap for the reset fact, but it does not override the supervisor's later shutdown-layer failure.

## Y. Structural evidence

The durable structural evidence passed:

- robots `M=3`, viewpoints `N=12`;
- episode length `30.0 s`, maximum episode length `300`, control step `0.1 s`;
- robot observation shapes `robot_0`, `robot_1`, and `robot_2`: `[2, 96]` each;
- shared observation shape `[2, 3, 288]`;
- available-actions shape absent as expected at the I4 boundary;
- P2 current publication type `_EventRuntimeCurrentPublication`, event runtime initialized.

## Z. Pre-App-close persistence

The formal worker receipt was present and valid before App close. The receipt table is authoritative for worker-side facts:

| Receipt predicate | Result |
|---|---|
| envelope and payload schema valid | PASS |
| run ID matches supervisor | PASS |
| worker PID matches child | PASS |
| payload digest matches | PASS |
| worker status success | PASS |
| receipt written before App close | PASS |
| flush/`fsync` completed | PASS |
| final-file readback completed | PASS |
| reset and structure passed | PASS |
| physical steps zero | PASS |
| learner construction/mutation zero | PASS |
| worker return code zero | PASS |
| worker receipt qualification | PASS |

## AA. Environment close

The worker receipt records `env_close_attempted=true` and `env_close_pass=true`. The env-close update was durably persisted before the App close call.

## AB. Process shutdown observation

The external supervisor waited for the worker, received return code 0, found PID `15116` absent from `tasklist`, found no matching formal-worker PIDs, and did not time out. However, its required `shutdown_observed` predicate searched the captured worker streams for the Simulation App shutdown marker and did not find it. Therefore `shutdown_observed=false`.

This report does not infer the missing predicate from return code or PID disappearance and does not retroactively repair the adjudication.

## AC. Supervisor adjudication

The supervisor accepted the worker receipt but rejected overall qualification because every required layer must pass. Its one and only formal adjudication was:

`PHASE-B2-T4-EP-P-STOP-PROCESS-QUIESCENCE-NOT-ESTABLISHED`

The failure was preserved before the supervisor raised. Per authorization, there was no repair and no retry after this formal failure.

## AD. Process quiescence

Process evidence was:

| Predicate | Result |
|---|---|
| worker wait completed | true |
| timeout | false |
| worker return code | 0 |
| worker PID active in tasklist | false |
| matching formal-worker PIDs | none |
| shutdown marker observed | false |
| composite process-quiescence pass | false |

The composite is false solely because the formal supervisor contract required the shutdown marker in addition to process disappearance.

## AE. Learner and mutation zero

Persistent learner constructions, learner mutations, learner updates, actor backward/optimizer steps, critic backward/optimizer steps, and ValueNorm updates were all 0. Physical environment steps were 0. Checkpoint I/O, public activation, and evaluation/playback were 0.

## AF. Source preservation

EP-P changed no production semantic file, production registration/export file, HARL file, or installed `site-packages` file. The historical EP artifacts and report remained immutable. After the formal STOP, the frozen EP-P harness and formal artifacts were not patched.

## AG. Exact execution counts

```text
preformal pure/static Python invocations: 11
synthetic worker persistence processes: 6
synthetic persisted success/failure exemplars: 2
supervisor negative cases: 12 / 12 fail closed
fresh-process entry-point regression probes: 1 / 1 PASS
formal supervisors / workers / retries: 1 / 1 / 0
CUDA readiness probes: 1
AppLauncher lifetimes: 1
environment constructions: 1
initial resets: 1
physical environment steps: 0
formal worker receipts / supervisor adjudications: 1 / 1
persistent learner constructions / learner mutations / learner updates: 0 / 0 / 0
actor backward / optimizer steps: 0 / 0
critic backward / optimizer steps: 0 / 0
ValueNorm updates: 0
checkpoint I/O / public activation / evaluation-playback: 0 / 0 / 0
production files changed: 0
B2-T4-RE4 started: 0
git add / commit / push: 0 / 0 / 0
```

## AH. Non-claims

EP-P does not establish B2-T4-RE4 readiness, learner or optimizer correctness, ValueNorm update correctness, checkpoint continuation, training quality, public learned-policy readiness, evaluation/playback readiness, long-horizon stability, or paper-scale training readiness. The worker-side reset/structure receipt passing does not turn the failed supervisor shutdown predicate into a pass.

## AI. Final classification

The only authorized formal run failed the required supervisor-level shutdown/process-quiescence conjunction. The immutable final classification is:

`PHASE-B2-T4-EP-P-STOP-PROCESS-QUIESCENCE-NOT-ESTABLISHED`

Status: stopped, not qualified, awaiting independent GPT review. The nominal success classification is not earned.

## AJ. Handoff

Do not patch the frozen EP-P harness, edit the formal artifacts, or retry AppLauncher under this authorization. Do not start B2-T4-RE4, construct a learner, perform checkpoint I/O, activate the public learned-policy route, run evaluation/playback, or begin long training.

Any investigation or revised shutdown-observation contract requires a new explicit instruction. The next action is independent review of the preserved STOP evidence in `202609/20260916/b2_t4_ep_p_artifacts/`.
