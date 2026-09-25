# Phase B2-T4-EP Environment Entry-Point / Registration Boundary Qualification Report

## A. repository authority

Branch `main`, HEAD/origin/main/merge-base `b71d85a32f51be6ada324f870813a56bb45dd396`. The pre-edit working-tree porcelain SHA-256 was `ab65573d1e9bcec7a21ca32c117c6bfbd42a451cc5bf2dbb485c8a21dcfa1b5b`. The existing staged migration remained 359 paths with staged-index SHA-256 `a40169043c3bfffd481a7ed1bddf3e52663d61379bedfd2610781457d11f947c`; monthly path-set SHA-256 remained `0f2b8f7b52148e39196cbeb40fd9f4edd94fb762b6daf8be6279a116b80a39ab`. No index-changing Git command was run.

## B. starting reviewed authority

B2-R0–R7 and B2-T0–T3 were closed. B2-T4 original, RE1, RE2, and RE3 remained historical STOPs; NR, SR, and ZD were closed. B2-T4-RE4, B2-R6, checkpoint continuation, public activation, evaluation/playback, and long training were not authorized.

## C. historical RE3 preservation

Historical RE3 remains `PHASE-B2-T4-RE3-STOP-PRE-ENVIRONMENT-ENTRY-POINT-RESOLUTION-NOT-COMPLETE`, `partial_update=false`, `route_poisoned=false`, environment 0, learner 0, mutation 0. Its reviewed wrapper SHA-256 `b6325c78189ab5b62c7daaf7452745c036eb7acd629f3c705cbded24eda86f6c` remains recorded in the RE3 report and EP source manifest. EP did not rewrite historical artifacts or retry RE3.

## D. exact RE3 traceback boundary

The retained traceback was `AttributeError: module 'isaaclab_tasks.direct.scan_mobile_manipulator' has no attribute 'ScanMobileManipulatorEnv'`, inside Gymnasium entry-point loading before environment construction.

## E. Gym environment registration source

`scan_mobile_manipulator/__init__.py:19` calls `gym.register`; importing the real package both exports the class and registers the task. The higher-level `isaaclab_tasks/__init__.py` invokes package discovery through `import_packages`.

## F. registered entry-point string

Environment ID: `Isaac-Scan-Mobile-Manipulator-Direct-v0`. Entry point: `isaaclab_tasks.direct.scan_mobile_manipulator:ScanMobileManipulatorEnv`. Gym therefore imports the package module and requests its `ScanMobileManipulatorEnv` attribute.

## G. canonical environment class definition

The class is defined at `scan_mobile_manipulator_env.py:1468`, canonical module `isaaclab_tasks.direct.scan_mobile_manipulator.scan_mobile_manipulator_env`, source SHA-256 `f96f6b6e9a530cd0b438344a11dc67670559206f3521d641d776d4bd475c6363`. The class was not moved.

## H. package export state

The real package initializer imports `ScanMobileManipulatorEnv` and `ScanMobileManipulatorEnvCfg` from the defining module at line 15. `__all__` is not defined and is not needed for explicit attribute loading. The registered entry point is consistent with the real package export contract.

## I. RE2 successful import sequence

Fresh-process evidence showed that importing the RE2 wrapper left all four relevant task-package modules absent before AppLauncher. Historical RE2 then launched AppLauncher, imported canonical `isaaclab_tasks`, resolved the entry point, constructed the environment, and reset it.

## J. RE3 failed import sequence

Before EP, importing RE3 at module scope imported ZD. ZD imported NR/R5 helpers, which imported `_assignment_phase_b2_r1_contract_helpers.py`. That helper installed file-less, spec-less synthetic modules for `isaaclab_tasks`, `isaaclab_tasks.direct`, and `isaaclab_tasks.direct.scan_mobile_manipulator`. The scan package had no env attribute and the defining env module was absent. AppLauncher did not replace cached `sys.modules` entries, and the later canonical import therefore did not execute the real package initializer.

## K. RE2-vs-RE3 comparison

| Property | RE2 | RE3 before EP | EP-qualified state |
|---|---|---|---|
| Env ID | `Isaac-Scan-Mobile-Manipulator-Direct-v0` | same | same |
| Entry point | package root + env attribute | same | same |
| Package module before AppLauncher | absent | synthetic, `__file__=None`, `__spec__=None` | absent |
| Env defining module imported before AppLauncher | no | no | no |
| Package exports env class after canonical registration | yes | canonical initializer not executed | yes in pure source model |
| `gym.spec` resolves | yes historically | no at formal make boundary | PASS in pure probes |
| `gym.make` constructs | yes | no | reached construction in the sole EP formal attempt |
| reset | yes | not reached | not established because formal receipt was not persisted |
| Runner transform difference | no ZD top-level import | ZD top-level import | ZD local to pure readiness only |

## L. sys.modules/module-state audit

The pre-repair RE3 probe found a present scan package with `__file__=None`, `__spec__=None`, no env class, and no defining module. RE2 found the package absent. Two independent repaired-RE3 probes found all relevant task-package modules absent before canonical registration, then found the real package initializer source model exporting the same class object as the defining module.

## M. source-identity coverage audit

RE2/RE3 `qualified_source_identity.repo_hashes` did not include the root initializer, direct initializer, scan package initializer, or env defining module. EP makes all four first-class future authority: `e10fe2f...ab0d9`, `29f633f...02907`, `c72daa4a...e9ff46`, and `f96f6b6e...5c6363`; full values are in `source_identity_manifest.json`.

## N. root-cause classification

`TEST-SIDE IMPORT ORDER / SYS.MODULES CACHE POISONING`. This was not a production export or registration defect.

## O. repair decision

Repair type: `TEST-SIDE`. The RE3 wrapper now imports ZD only inside `run_runner_readiness_replay`; formal module import no longer triggers the pure-test placeholder chain. Production registration/export modifications: 0.

## P. production/test-side files changed

Production semantic and registration/export files changed: 0. Test-side runner files modified: `test_assignment_phase_b2_t4_re3_normal_horizon_learned_training_integration.py` (one import relocation). Dedicated test files created: `test_assignment_phase_b2_t4_ep_environment_entry_point_registration_boundary.py`. Documentation and bounded artifacts were added separately.

## Q. before/after registration contract

BEFORE: RE3's module-scope ZD dependency installed a synthetic cached scan package without the env export, so the real initializer could not run and Gym could not obtain its requested attribute.

AFTER: formal RE3 import leaves the task package absent; AppLauncher setup precedes canonical `isaaclab_tasks` import, which can execute the real scan initializer, register the ID, and export the exact defining class.

## R. fresh-process resolution matrix

Four positive child processes passed: canonical source-model registration, exact repaired RE3 sequence, a fresh repeat of repaired RE3, and RE2 comparison. A fifth child passed three negatives: wrong attribute→`AttributeError`, wrong module→`ModuleNotFoundError`, missing registration→`NameNotFound`. Duplicate registration was not mutated because Gymnasium warns and overwrites rather than supplying a project fail-closed detector.

## S. exact formal import-sequence qualification

Pure qualification passed twice in independent processes. Each imported the repaired RE3 wrapper before registration and proved no relevant task package was cached, then executed the real package initializer against identity-preserving lightweight defining-module sentinels and resolved the same object through the defining module, package export, and Gym entry point.

## T. AppLauncher bounded smoke

Exactly one formal fresh process and one AppLauncher lifetime were used. AppLauncher started on `cuda:0`; logs show the 2-environment scene and completed environment setup. The Kit log recorded normal shutdown for PID 27328. No retry occurred. Qualification nevertheless STOPPED because the script placed formal JSON persistence after `SimulationApp.close()`, which ended the worker before those writes.

## U. gym.spec result

Pure `gym.spec` was PASS in all four positive probes. The real formal sequence necessarily resolved `gym.spec` and the class before `gym.make`, and real construction was reached. The exact registered string remained unchanged.

## V. environment construction

Real environment construction count: 1. Logs recorded device `cuda:0`, 2 environments, physics step 1/60 s, and environment/control step 0.1 s. The production class initializer emitted scan configuration diagnostics. This is construction evidence only.

## W. reset qualification

`NOT ESTABLISHED`. Reset evidence was kept in memory and scheduled for persistence after `SimulationApp.close()`. Because both success and caught-exception paths used that ordering, process exit 0 cannot discriminate reset success from a caught pre-persistence failure. The formal attempt cannot be retried under this authorization.

## X. resolved environment structure/config

Established from real logs/source: `cuda:0`, `num_envs=2`, control step 0.1 s, scan environment construction. Configured by the formal source: profile `event_gated_local_mrta`, M=3, N=12, episode length 30.0 s. The complete runtime structural receipt, including observation shapes, max episode length, P2 initialization, and episode generation, is not promoted to PASS because it was not persisted.

## Y. learner/train mutation zero audit

Persistent learner constructions, actor/critic optimizer constructions, ValueNorm training state, learner S0–S10, actor backward/step, critic backward/step, ValueNorm updates, and formal training updates were all 0. The EP formal source contains no learner construction or environment-step call.

## Z. process/resource close audit

Formal PID 27328 was absent after supervisor return. Kit logged `Simulation App Shutting Down`. Environment close was called before App close in `finally`, but its per-resource structured receipt was also after App close and was not persisted. Therefore process quiescence is PASS, shutdown is observed, and full structured clean-close qualification is not established.

## AA. static/private/public guards

`py_compile` passed for both test-side files. Static source trace, export contract, protected production hashes, clean production registration files, pure resolution identity, and three fail-closed negatives passed. Private learner construction and mutation were 0. Public learned-policy activation, checkpoint I/O, evaluation/playback, and baseline execution were 0.

## AB. exact execution counts

```text
pure/static Python invocations: 11
fresh-process entry-point probes: 8
successful fresh-process entry-point probes: 7
failed diagnostic probes: 1 (direct canonical import without AppLauncher; expected omni.kit absence)
formal AppLauncher smokes / lifetimes: 1 / 1
formal retries: 0
environment constructions: 1
initial resets: NOT ESTABLISHED
physical environment steps: 0
persistent learner constructions / updates: 0 / 0
actor backward/step: 0 / 0
critic backward/step: 0 / 0
ValueNorm updates: 0
checkpoint I/O / public activation / evaluation-playback: 0 / 0 / 0
production training semantic files changed: 0
registration/export production files changed: 0
test-side files changed/created: 2
B2-T4-RE4 started: 0
git add / commit / push: 0 / 0 / 0
```

## AC. retained nonclaims

EP does not establish completed environment reset/structure qualification, normal-horizon learned-training integration, W1–W7, continuation, learner behavior, long-training readiness, checkpoint continuation, evaluation quality, or public learned-policy readiness. Historical RE3 is not reclassified. The public route remains dormant/blocked.

## AD. final classification

`PHASE-B2-T4-EP-STOP-FORMAL-EVIDENCE-PERSISTENCE-ORDERING-NOT-QUALIFIED`

The registration root cause and test-side repair are qualified by pure evidence, and real construction was reached once, but the overall EP success classification is withheld because required reset and close receipts were not persisted.

## AE. GPT-review handoff

Independent GPT review should verify the test-side root cause, the pure fresh-process matrix, the one-attempt evidence boundary, and the refusal to infer reset PASS from exit code 0. A future explicitly authorized task may redesign the formal worker/supervisor persistence order before any new AppLauncher attempt. Do not start B2-T4-RE4, construct a learner, begin B2-R6, perform checkpoint I/O, activate the public route, or start evaluation/playback or long training.
