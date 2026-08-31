# Phase B2-V2-PD2-R2 S0R Adapter Correction and Re-entry Report

Date: 2026-08-28  
Location: `AgentRead/20260828/`, following the current-date folder rule in `AgentRead/AGENTS.md`.

```text
classification:
  PD2-STOP-RUNTIME-EXTENSION-IDENTITY-MISMATCH

first authoritative boundary:
  S0R_CRITICAL_usdrt.scenegraph

R2-A:
  PHASE-B2-V2-PD2-R2-S0R-ADAPTER-CORRECTION-PASS-ELIGIBLE-FOR-FORMAL-REENTRY

R2-B formal executions:       1
formal workers:               1
AppLauncher lifetimes:        1
Isaac environments:           0
environment reset / step:     0 / 0

B2-V2-PD2 initial STOP:       REVIEW CONFIRMED / RETAINED
B2-V2-PD2-R1:                 REVIEW PASS / CLOSED AS HISTORICAL S0R ADAPTER STOP
B2-V2-PD2-R2:                 STOPPED AT S0R
B2-V2:                        STOPPED / INCOMPLETE
runtime / policy / learner:   BLOCKED / BLOCKED / BLOCKED
public learned-policy route:  DORMANT / BLOCKED
B2-R / training:              NOT AUTHORIZED / NOT AUTHORIZED
commit:                       NONE
```

## 1. Starting authority

Starting committed HEAD:

```text
14993dee344bade0230d2eb97b5f22171331f44a
```

The frozen PD1 design, historical initial PD2 report, reviewed PD2-R1 report, D4-CI audit, D4-O shutdown contract, current `TASK_PROGRESS.md`, and current test-only harness were used as authority.

The historical initial PD2 classification remains:

```text
PD2-STOP-SHARED-STATE-PRELAUNCH-MISMATCH
```

Its reviewed actual blocker remains the now-closed test-only Windows Junction predicate defect. The historical R1 artifact remains:

```text
PD2-STOP-STARTUP-EQUIVALENCE-MISMATCH
```

GPT review established that R1's actual blocker was a test-only single-argument field-adapter call on `carb.dictionary.Item`, not a runtime extension identity mismatch. Neither historical report was modified.

## 2. Authorized scope and files

R2 was limited to:

1. a generic read-only test-only S0R metadata adapter;
2. correct S0R failure mapping to the frozen runtime-extension STOP class;
3. durable incremental S0R checkpoint evidence;
4. static/synthetic/read-only R2-A verification;
5. only after R2-A PASS, one fresh formal supervisor execution.

Only this code file changed:

```text
scripts/environments/
test_assignment_phase_b2_v2_pd2_production_startup_path_real_interface_smoke.py

formal-execution SHA-256:
77ad85ae71ea5babfa5215b5ac621a6fa4219998f4e358e821aa696c1697ec39
```

Documentation added or updated:

- this report;
- top-level `AgentRead/TASK_PROGRESS.md`.

Production, I0-I6, lifecycle, P2/Ak, DirectMARLEnv, wrapper, installed HARL, official Kit, shared cache/registry/Junction state, driver, and environment source changes: **NONE**.

## 3. Old adapter defect

R1 reached the first critical S0R row and called:

```python
extension.get("version")
```

The actual object was `carb.dictionary.Item`, whose installed binding requires `get(key, default)`. The raw `TypeError` escaped S0R and inherited the worker's startup fallback classification. R2 does not reinterpret the historical emitted label; it corrects the future test-only boundary.

## 4. New read-only adapter

The bounded helper `_read_extension_field(value, key, default)` now has two explicit paths:

- `Mapping`: membership/index semantics for a required field and `.get(key, default)` for an optional field;
- non-`Mapping` dict-like/`carb.dictionary.Item`: one callable `get(key, sentinel)` read.

It performs no set, write-back, conversion-and-replacement, extension enable/disable, path change, or manager mutation. Unsupported types, incompatible `get` signatures, and absent required fields raise a test-only `ExtensionFieldReadError`.

`_manager_version()` uses the same helper for both direct `version` and nested `package.version`; therefore the correction does not leave a second single-argument nested-Item call behind.

## 5. Required-field and formal mapping semantics

The adapter does not weaken the frozen S0R identity contract. Missing or unreadable required metadata never becomes an ignored check. Runtime S0R now catches otherwise-unclassified field/API exceptions, persists the precise failing field and object/API boundary when possible, and raises:

```text
PD2-STOP-RUNTIME-EXTENSION-IDENTITY-MISMATCH
```

S0 startup-prefix/App configuration failures continue to map to:

```text
PD2-STOP-STARTUP-EQUIVALENCE-MISMATCH
```

The formal ten-item PD2 STOP taxonomy is unchanged and was statically verified exact 10/10.

## 6. Durable S0R design

The runtime gate now checkpoints evidence in this order:

```text
capture complete-set A
-> capture complete-set B
-> validate A == B
-> persist both complete snapshots and equality
-> for each critical row:
     persist STARTED
     read and validate
     persist PASS or FAILED_AT_FIELD immediately
-> after every critical row passes:
     persist overall S0R PASS
```

If row N fails, prior passed rows and the complete-set snapshots remain in the supervisor-owned checkpoint artifact. A failed row is never labeled PASS. The enclosing worker DTO may still lack `evidence["s0r"]` because the function did not return; durable checkpoint events are the authority for partial S0R evidence.

## 7. R2-A synthetic adapter tests

All six required cases passed without AppLauncher, Isaac, CUDA, HARL, or MRTA:

| Case | Contract | Result |
|---|---|---|
| A | plain Python mapping version read, no mutation | PASS |
| B | missing mapping key returns exact supplied default | PASS |
| C | fake object exposing only `get(key, default)` | PASS |
| D | unsupported object fails closed | PASS |
| E | missing required field maps to runtime-extension STOP candidate | PASS |
| F | nested `package.version` through two-argument getters | PASS |

Static checks also established:

- no remaining `_manager_version()` single-argument `.get("version")` call;
- the generic non-Mapping path invokes a two-argument getter;
- every explicit runtime S0R `require`/`PD2Stop` classification is `STOP_EXTENSION`;
- `STOP_STARTUP` is absent from `runtime_extension_gate()`;
- complete-set, per-row, and overall-pass persistence labels occur in the required order.

Static artifact:

```text
C:\Users\33506\AppData\Local\Temp\b2_v2_pd2_r2_static_20260828.json
SHA-256: 05ad6b8c0dd1d046b8fcea84241a3ea7629dbe9bd5c035194595ebb4e0b9fa78
```

## 8. R2-A read-only preflight

R2-A artifact:

```text
C:\Users\33506\AppData\Local\Temp\b2_v2_pd2_r2a_20260828.json
SHA-256: e6defbc2cf76646f35d2cac2593badf3f8c8acb13bf71bbb9e99c6f34dbd8608
```

| Gate | Result |
|---|---|
| exact interpreter | `C:\isaacenvs\isaac45_harl\python.exe` / PASS |
| adapter synthetic tests | 6/6 PASS |
| S0R mapping/order static checks | PASS |
| production warm-up AST equivalence | PASS |
| corrected Junction detector static guard | PASS |
| source hashes | 45/45 EXACT |
| critical static manifests | PASS |
| frozen STOP taxonomy | 10/10 EXACT |
| 103-row fingerprint | `ebdfb41...deb846f` / EXACT |
| primary Win32 Junction oracle | 43/43 PASS |
| independent PowerShell oracle | 43/43 PASS |
| oracle mapping agreement | PASS |
| startup environment | PASS |
| `git diff --check` | PASS; line-ending warnings only |

R2-A classification:

```text
PHASE-B2-V2-PD2-R2-S0R-ADAPTER-CORRECTION-PASS-ELIGIBLE-FOR-FORMAL-REENTRY
```

R2-A counters were worker/AppLauncher/SimulationApp/Isaac/CUDA/HARL/MRTA = `0/0/0/0/0/0/0`. This was eligibility evidence, not PD2 PASS.

## 9. Formal execution count and artifact

Only after the R2-A PASS, exactly one fresh formal supervisor execution was started:

```text
C:\Users\33506\AppData\Local\Temp\b2_v2_pd2_r2_formal_20260828.json
SHA-256: f26ffa2d5d4317ab0bc9696fbba9b47e721637a6d1d9c6566fb4b7fa7153e01b

formal supervisor executions: 1
formal workers:               1
AppLauncher lifetimes:        1
retry:                        0
elapsed:                      98.813 seconds
timeout / supervisor kill:    false / false
```

No second formal execution was attempted after STOP.

## 10. Formal PRELAUNCH

Formal PRELAUNCH independently passed again before worker startup:

- committed HEAD exact;
- 45/45 protected/audited source hashes exact;
- 103/103 shared-state rows exact at the frozen digest;
- Win32 and PowerShell Junction oracles each 43/43 with exact pair mapping;
- critical static manifests exact;
- startup environment exact.

No baseline refresh or shared-state repair occurred.

## 11. Formal S0

S0 independently repeated the exact frozen production prefix and passed:

```text
device:                  cuda:0
zeros:                   [1,1], default float32
Linear:                  [1,1]
forward / synchronize:   1 / 1
matmul / retry:          0 / 0
seed before warm-up:     0
headless:                true
enable_cameras:          false
livestream / XR:         0 / false
experience override:     empty
resolved experience:     apps/isaaclab.python.headless.kit
experience SHA-256:      475bb23c5941fbaaf0186991bf6e5445a267b1e0fd8bbab333cc78dc2e1bc795
```

AppLauncher returned and the exact 19-event S0 ledger passed. This remains positive evidence only for the current workaround-based startup prefix; it does not establish warm-up necessity or a CUDA/cuBLAS root cause.

## 12. Formal S0R complete-set durable evidence

Two consecutive enabled-extension snapshots were captured, compared, and durably persisted before critical-row processing:

```text
snapshot A count:      67
snapshot B count:      67
snapshot A SHA-256:    0f12ff19f4044ec0293a23da1d190759102114e345b063671815a204f3335405
snapshot B SHA-256:    0f12ff19f4044ec0293a23da1d190759102114e345b063671815a204f3335405
A == B:                true
persistence status:    PASS
```

This closes the R1 evidence-lifetime gap for complete-set snapshots.

## 13. Formal S0R critical-row evidence

Eleven critical rows completed exact validation and were each durably persisted as PASS:

1. `isaaclab`
2. `isaaclab_assets`
3. `isaaclab_tasks`
4. `isaaclab_rl`
5. `isaacsim.simulation_app`
6. `isaacsim.core.api`
7. `isaacsim.core.cloner`
8. `isaacsim.core.utils`
9. `omni.physx`
10. `omni.physx.tensors`
11. `omni.physx.fabric`

The twelfth row, `usdrt.scenegraph`, was durably persisted with `status=FAILED`, `failed_at_field=identity_comparison`, and `pass=false`. `omni.warp.core`, the remaining thirteenth row, was not attempted.

The corrected adapter successfully read the failed row. The following fields matched the frozen manifest:

```text
enabled ID:        usdrt.scenegraph-7.5.1
enabled:           true
manager version:   7.5.1
manifest version:  7.5.1
link flag/target:  matched frozen row
```

The first mismatching identity fields were:

| Field | Frozen expected | Current runtime observed |
|---|---|---|
| resolved root | `C:\isaacenvs\isaac45_harl\Lib\site-packages\isaacsim\extscache\usdrt.scenegraph-7.5.1+d02c707b.wx64.r.cp310` | `c:/isaacenvs/isaac45_harl/lib/site-packages/omni/data/kit/isaac-sim/4.5/exts/3/usdrt.scenegraph-7.5.1+d02c707b.wx64.r.cp310` |
| manifest path | frozen `isaacsim/extscache/.../config/extension.toml` | current `omni/data/Kit/Isaac-Sim/4.5/exts/3/.../config/extension.toml` |
| manifest SHA-256 | `a52a69b609100538429406619e9576e81fb1a18a279ddc40628d9fa932358818` | `e155eeba2044deb2602bc229f68fe57b7f60e1f5adacc5283737488918a0d5fe` |

Therefore S0R overall PASS was not emitted, S1 was not entered, and the exact formal classification is:

```text
PD2-STOP-RUNTIME-EXTENSION-IDENTITY-MISMATCH
first_boundary = S0R_CRITICAL_usdrt.scenegraph
```

This is evidence that the current runtime-resolved `usdrt.scenegraph` identity differs from the frozen S0R authority at those fields. It is not, by itself, a causal attribution to Isaac, Kit, cache, Junction, or production source code.

## 14. S0-S6 and snapshot matrix

| Stage | Result | Evidence |
|---|---|---|
| PRELAUNCH | PASS | 45 hashes, 103 rows, dual 43-pair oracle, manifests, environment exact |
| S0 | PASS | exact warm-up, AppLauncher return, experience/config/event ledger |
| S0R complete set | PASS / DURABLE | 67 IDs; A/B exact and persisted |
| S0R critical rows | **STOP** | 11 durable PASS rows; row 12 `usdrt.scenegraph` durable identity mismatch |
| S0R overall | NOT PASS | no overall-pass checkpoint |
| S1 seed/environment/components/reset/I1/I2 | NOT RUN | stopped before environment construction |
| Snapshot A | NOT CAPTURED | components not constructed |
| S2 installed VCritic `[2,418] -> [2,1]` | NOT RUN | original blocker not reached |
| S3 HAPPO actor | NOT RUN | actor not constructed/forwarded |
| S4 physical event-route step | NOT RUN | no environment |
| S5 continuation | NOT RUN | no environment |
| S6 TIME_LIMIT/I4/I5a/I5b | NOT RUN | no environment |
| Snapshot B | NOT CAPTURED | S6 not reached |

No DVM, proposal/logprob, P2/Ak, terminal sidecar, ACK, buffer, GAE, or ValueNorm runtime evidence was produced.

## 15. Shutdown evidence

The reviewed D4-O joint classifier returned:

```text
primary result valid:          yes
checkpoint artifact valid:     yes
O4 primary persisted:          yes
O5 before close:               yes
O6 close returned:             absent; no in-process return claim
process exit code:             0
timeout / supervisor kill:     false / false
worker alive after wait:       false
known child survivors:         0
supervisor cleanup:            PASS
shutdown class:                EXTERNAL_CLEAN_TERMINATION
safe shutdown:                 true
```

The functional STOP comes from the persisted primary result, not process exit code 0.

## 16. Postrun and source integrity

The supervisor recaptured state only after worker death:

```text
before fingerprint:            ebdfb41e35d85b55eb7d86acf2ab78b33229ca0bec30623d1c88ec297deb846f
after fingerprint:             ebdfb41e35d85b55eb7d86acf2ab78b33229ca0bec30623d1c88ec297deb846f
before/after rows:              103 / 103
before/after Win32 pairs:       43 / 43
before/after PowerShell pairs:  43 / 43
dual-oracle mapping:            PASS / PASS
bounded row changes:            0
protected hashes:               unchanged
postrun class:                  NO_OBSERVED_STATE_CHANGE
postrun eligible:               true
```

This establishes bounded current-state equality across this worker lifetime. It does not establish pre-R8 restoration or equivalence.

## 17. No-training and no-production counters

```text
production source changes:          NONE
installed HARL changes:             NONE
I0-I6 changes:                      NONE
official Kit changes:               NONE
shared cache/registry/Junction writes: NONE

Isaac environment construction:     0
environment reset / step:           0 / 0
VCritic / actor forward:             0 / 0
optimizer.step / backward:           0 / 0
ValueNorm updates:                   0
checkpoint load / save:              0 / 0
training / playback / evaluation:    NOT RUN
public route activation:             0
B2-R:                                NOT AUTHORIZED
commit:                              NONE
```

## 18. Causal non-claims

PD2-R2 does not establish:

- pre-R8 restoration, equivalence, or a clean shared Kit environment;
- why runtime `usdrt.scenegraph` resolves to the observed installed namespace path;
- that the frozen expected path or current resolved path should be changed;
- a defect in Isaac, Kit, cache, Junction, HARL, MRTA, or production source;
- whether the original VCritic CUDA blocker reproduces;
- real actor, physical lifecycle, continuation, or TIME_LIMIT transport success;
- public-route, runtime, policy, learner, B2-R, or training readiness.

It establishes that the R2 test-only adapter and durable evidence design work at real S0R, and that the first current formal mismatch is the `usdrt.scenegraph` runtime identity row described above.

## 19. Final decision and stop

Stop for GPT/user review. Do not change the frozen critical manifest, resolve/normalize away the path mismatch, refresh the baseline, repair shared state, or rerun formal PD2 under this authorization.

The recommended next decision is a read-only review of the frozen PD1 authority for cache-backed critical extensions against the current extension-manager resolution semantics and D4-CI provenance. That review must decide whether the observation represents an expected current-path indirection or an authoritative runtime identity mismatch. It is not authorized here, and no repair is proposed.

```text
final classification:
  PD2-STOP-RUNTIME-EXTENSION-IDENTITY-MISMATCH

first authoritative boundary:
  S0R_CRITICAL_usdrt.scenegraph

B2-V2-PD2-R2:
  STOPPED / AWAITING GPT REVIEW

B2-V2:
  STOPPED / INCOMPLETE

runtime / policy / learner:
  BLOCKED / BLOCKED / BLOCKED

public route:
  DORMANT / BLOCKED

B2-R / training / commit:
  NOT AUTHORIZED / NOT AUTHORIZED / NONE
```
