# Phase B2-V2-PD2 Current-Production-Startup Real Isaac/HARL Interface Validation Report

Date: 2026-08-27

```text
classification:
  PD2-STOP-SHARED-STATE-PRELAUNCH-MISMATCH

first authoritative boundary:
  PRELAUNCH-EXACT-BASELINE-GATE

worker started:             NO
AppLauncher lifetimes:      0
SimulationApp lifetimes:    0
Isaac environment runs:     0
CUDA worker runtime:        0

B2-V2-PD2:                  STOPPED AT PRELAUNCH-EXACT-BASELINE-GATE
B2-V2:                      STOPPED / INCOMPLETE
runtime readiness:          BLOCKED
policy readiness:           BLOCKED
learner readiness:          BLOCKED
public learned-policy route: DORMANT / BLOCKED
B2-R:                       NOT AUTHORIZED
training:                   NOT AUTHORIZED
commit:                     NONE
```

## 1. Starting authority and claim boundary

The committed starting checkpoint was:

```text
14993dee344bade0230d2eb97b5f22171331f44a
```

The implementation authority was the frozen `PHASE_B2_V2_PD1_PRODUCTION_STARTUP_PATH_VALIDATION_DESIGN.md`. Supporting authorities were the D4-CI shared-state audit, the D4-O shutdown contract, the original B2-V2 report, and `TASK_PROGRESS.md`.

The authorized mode was strictly:

```text
PD-A / CURRENT-PRODUCTION-RUNTIME-VALIDATION
```

This mode could only have established behavior of the current workaround-based production startup path in the reviewed post-R8 state. It could not establish pre-R8 equivalence, a cuBLAS root cause, intrinsic warm-up necessity, public-route readiness, training readiness, or Phase B completion.

## 2. Authorized implementation

One test-only harness was added:

```text
scripts/environments/
test_assignment_phase_b2_v2_pd2_production_startup_path_real_interface_smoke.py

SHA-256:
a47dd3358d87033f8a19f5a28fe19613215dc317bc5b269e5b1545f1388a0392
```

It is not imported by production, registered in a package, used by train/play, or connected to the public route. No production, I0-I6, installed HARL, official Kit, DirectMARLEnv, wrapper, or lifecycle source was changed by PD2.

The harness contains the reviewed external-supervisor/fresh-worker structure, exact `TRAIN_STARTUP_PREFIX_V1` copy, S0/S0R/S1-S6 gates, Snapshot A/B guards, D4-O shutdown classification, postrun integrity classifier, and the exact frozen ten-item STOP taxonomy. None of its worker-side runtime path was reached in the formal execution.

## 3. Static implementation verification

The exact interpreter was:

```text
C:\isaacenvs\isaac45_harl\python.exe
Python 3.10.20
```

Static verification results:

| Check | Result |
|---|---|
| `py_compile` | PASS |
| starting HEAD | EXACT |
| protected/audited source hashes | 45/45 EXACT |
| PD1 nine-file source authority | EXACT within the protected set |
| installed HARL audited sources | EXACT |
| official Kit/application sources | EXACT |
| critical static extension manifests | PASS |
| production/harness warm-up AST semantics | EXACT |
| Snapshot A/reset/collect/finish/Snapshot B order | PASS |
| reviewed D4-O classifier hash | EXACT |
| frozen ten-item STOP taxonomy | EXACT |
| `git diff --check` | PASS, exit 0; line-ending warnings only |

An initial static-only invocation stopped before any worker because the harness checker expected the nested `Linear(...).to(device)` AST nodes in the opposite source-column order. Production and harness AST traces were already identical. The test-only expected ordering was corrected, `py_compile` and static-only verification were repeated, and all static gates then passed. This was before the one formal supervisor execution; AppLauncher/SimulationApp/Isaac/CUDA worker counts remained zero.

## 4. Formal execution count

Exactly one formal supervisor execution reached PD2 prelaunch evaluation. An earlier PTY request was rejected by the command host at Windows process creation with access denied; it did not enter Python and created no supervisor, worker, AppLauncher, SimulationApp, Isaac, or CUDA lifetime. The authorized formal execution was then launched without a PTY.

The formal result was retained at:

```text
C:\Users\33506\AppData\Local\Temp\b2_v2_pd2_formal_result_20260827.json

SHA-256:
e4fd6592cb8be48bf3a40faf30027cd79b00450b0b0d2ad9e0a5e137a3022d2c
```

No retry, comparison run, fallback run, alternate model width, extra warm-up, cache cleanup, baseline refresh, or second formal worker was performed.

## 5. PRELAUNCH-EXACT-BASELINE-GATE result

The supervisor failed closed before worker creation.

| Prelaunch item | Expected | Observed | Result |
|---|---:|---:|---|
| protected/audited files | 45 | 45 exact | PASS |
| critical extension manifests | reviewed paths/versions/hashes | exact | PASS |
| startup environment (`LIVESTREAM`, `ENABLE_CAMERAS`, `XR`) | absent/empty/zero | all absent | PASS |
| bounded fingerprint | `ebdfb41e35d85b55eb7d86acf2ab78b33229ca0bec30623d1c88ec297deb846f` | same | PASS |
| bounded inventory rows | 103 | 103 | PASS |
| installed-root rows | 45 | 45 | PASS |
| cache-root rows | 50 | 50 | PASS |
| metadata rows | 8 | 8 | PASS |
| installed junction/cache pairs | 43 | 0 according to the harness pair enumerator | **FAIL** |

The harness constructed its pair inventory by filtering the Windows installed namespace with Python 3.10 `os.path.islink()`. In this environment that predicate returned false for the NTFS junctions, so the harness produced zero pair DTOs and `pair_contract_pass=false`. A separate read-only PowerShell inventory after the stop reported the same 45 installed-root members as 43 `LinkType=Junction` entries plus two entries with null `LinkType`, consistent with D4-CI. No junction was removed, recreated, retargeted, or repaired.

Therefore the observed evidence supports these narrow statements:

- the reviewed 103-row raw fingerprint itself was exact;
- the formal harness did not satisfy the separately required 43-pair validation contract;
- the first authoritative formal failure is the prelaunch exact-baseline gate;
- current evidence does **not** establish a shared-state structural mutation during PD2, because no worker ran and the raw fingerprint was exact;
- current evidence also cannot promote PD2 to PASS, because every prelaunch sub-gate was mandatory.

The formal classification remains exactly:

```text
PD2-STOP-SHARED-STATE-PRELAUNCH-MISMATCH
```

The result is not relabeled as `PD2-STOP-SHARED-STATE-ASSUMPTION-VIOLATION`; that class belongs to a postrun state delta. No postrun gate existed here because worker creation was forbidden after the prelaunch failure.

## 6. Stage matrix and first-boundary rule

| Stage | Result | Evidence |
|---|---|---|
| STATIC | PASS | compile, hashes, AST, manifest logic, snapshot order, STOP taxonomy, D4-O integration, diff check |
| PRELAUNCH | **STOP** | 103-row hash exact; required 43-pair harness validation reported 0 and failed |
| S0 production warm-up/AppLauncher | NOT RUN | worker not started |
| S0R runtime extension identity | NOT RUN | worker not started |
| S1 seed/environment/actor/critic construction/reset/I1/I2 | NOT RUN | worker not started |
| S2 real VCritic | NOT RUN | worker not started |
| S3 real HAPPO actor | NOT RUN | worker not started |
| S4 physical event-route step | NOT RUN | worker not started |
| S5 continuation | NOT RUN | worker not started |
| S6 TIME_LIMIT/I4/I5a/I5b | NOT RUN | worker not started |
| Snapshot B | NOT RUN | worker not started |
| D4-O shutdown | NOT APPLICABLE | no worker or SimulationApp existed |
| POSTRUN-INTEGRITY-GATE | NOT ENTERED | prelaunch failure; no worker lifetime |

The frozen first-boundary rule was honored. No later gate was evaluated to collect additional runtime evidence.

## 7. Required runtime evidence not produced

Because PRELAUNCH stopped execution, the following required report fields are intentionally `NOT RUN / NOT AVAILABLE`, not omitted claims:

```text
S0 exact event ledger:                 NOT PRODUCED
warm-up operation runtime trace:       NOT RUN
resolved experience path/hash:         NOT RESOLVED AT RUNTIME
S0R complete-set snapshots:            NOT CAPTURED
S0R critical runtime identity table:   NOT CAPTURED
seed/RNG runtime ledger:               NOT PRODUCED
environment E=2/M=3/N=12/T=2:         NOT CONSTRUCTED
actor0/actor1/actor2/VCritic:          NOT CONSTRUCTED
Snapshot A:                            NOT CAPTURED
I1 actor obs [2,3,421]:                NOT OBSERVED
I1 share obs [2,3,418]:                NOT OBSERVED
I2 available actions [2,3,13]:         NOT OBSERVED
I2 six DVM rows:                       NOT OBSERVED
VCritic input/output:                  NOT RUN
actor proposal/logprob evidence:       NOT RUN
S4 proposal/effective/P2/Ak evidence:  NOT RUN
S5 continuation evidence:              NOT RUN
S6 TIME_LIMIT/I4/I5a/I5b evidence:     NOT RUN
Snapshot B:                            NOT CAPTURED
shutdown classification:               NOT APPLICABLE
postrun raw diff/delta class:           NOT APPLICABLE
```

## 8. No-training and mutation accounting

```text
worker processes:             0
AppLauncher lifetimes:        0
SimulationApp lifetimes:      0
Isaac environments:           0
environment reset/step:       0 / 0
CUDA worker operations:       0
VCritic forwards:             0
actor forwards:               0
optimizer step:               0
backward:                     0
ValueNorm update:             0
checkpoint load/save:         0 / 0
training/playback/evaluation: 0 / 0 / 0
public route activation:      0
production changes:           NONE
installed HARL changes:       NONE
official Kit changes:         NONE
I0-I6 changes:                NONE
shared-state cleanup/repair:  NONE
commit:                       NONE
```

The 45-file protected hash set remained exact at the formal prelaunch gate. Since no worker was created, there was no worker-induced postrun state to classify. Final `git diff --check` remained PASS with existing line-ending warnings only.

## 9. Causal non-claims

This STOP does not establish that:

- the reviewed shared-state fingerprint changed;
- an installed junction or cache target changed;
- the current production warm-up succeeds or fails;
- the original VCritic cuBLAS blocker reproduces or is resolved;
- HAPPO actor sampling or physical lifecycle stepping works in the current runtime;
- TIME_LIMIT terminal transport works in real Isaac;
- pre-R8 behavior has been reproduced;
- the public learned-policy route, runtime, policy, learner, B2-R, or training is ready.

It establishes only that the formal PD2 execution failed closed at its first mandatory prelaunch boundary because the test-only pair enumerator did not validate the required 43 Windows junction/cache pairs.

## 10. Recommended next decision

Stop and obtain GPT/user review. Do not rerun PD2 under the current authorization.

If a later slice is explicitly authorized, it should be limited first to reviewing and correcting the **test-only** Windows junction identity predicate while preserving the frozen 103-row fingerprint algorithm, expected baseline, paths, hashes, pair targets, and all production sources. A new formal PD2 execution would require separate authorization. The expected baseline must not be refreshed merely to continue, and no cache/junction cleanup or repair is justified by this result.

Until that review:

```text
B2-V2-PD2:                  STOPPED AT PRELAUNCH-EXACT-BASELINE-GATE
B2-V2:                      STOPPED / INCOMPLETE
runtime/policy/learner:     BLOCKED / BLOCKED / BLOCKED
public learned-policy route: DORMANT / BLOCKED
B2-R:                       NOT AUTHORIZED
training:                   NOT AUTHORIZED
implementation beyond harness: NOT STARTED
commit:                     NONE
```
