# Phase B2-V2-PD2-R1 Windows Junction Predicate Correction and Re-entry Report

Date: 2026-08-28  
Location: `AgentRead/202608/20260828/`, following the current-date folder rule in `AgentRead/AGENTS.md`.

```text
classification:
  PD2-STOP-STARTUP-EQUIVALENCE-MISMATCH

first authoritative boundary:
  S0R

R1-A junction correction:
  PHASE-B2-V2-PD2-R1-JUNCTION-PREDICATE-CORRECTION-PASS-ELIGIBLE-FOR-FORMAL-REENTRY

R1-B formal executions:       1
formal workers:               1
AppLauncher lifetimes:        1
Isaac environments:           0
environment reset / step:     0 / 0

B2-V2-PD2 initial STOP:       REVIEW CONFIRMED / RETAINED
B2-V2-PD2-R1:                 STOPPED AT S0R
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

Authoritative inputs were read completely:

- frozen PD1 production-startup validation design;
- historical initial PD2 STOP report, preserved without edits;
- reviewed D4-CI shared-state audit;
- reviewed D4-O shutdown contract;
- current `TASK_PROGRESS.md`;
- the current test-only PD2 harness.

GPT review froze the initial PD2 interpretation as:

```text
PHASE-B2-V2-PD2-STOP-REVIEW-CONFIRMED-TEST-ONLY-JUNCTION-PREDICATE-DEFECT
```

The historical formal classification remains `PD2-STOP-SHARED-STATE-PRELAUNCH-MISMATCH`. Its fail-closed behavior was correct; the reviewed actual blocker was the test-only Windows NTFS Junction predicate. Shared-state structural mutation was not established.

## 2. Scope and production immutability

The only code modified was the existing test-only harness:

```text
scripts/environments/
test_assignment_phase_b2_v2_pd2_production_startup_path_real_interface_smoke.py

formal-execution SHA-256:
bf613f0d8de03f1a5de75bdf9ac707515772057fffe842cc7f424de535f8c860
```

No production, I0-I6, lifecycle, P2/Ak, DirectMARLEnv, wrapper, installed HARL, official Kit, cache, registry, junction, driver, or environment source was modified. The original 103-row fingerprint representation and serialization algorithm remained unchanged.

## 3. Old predicate and reviewed defect

The old pair reader used:

```python
os.path.islink(path)
```

On Python 3.10/Windows it returned false for the 43 NTFS Junctions, producing zero pair DTOs. It was insufficient because a Junction is a mount-point reparse point and is not necessarily reported as a symbolic link by `os.path.islink()`.

The old predicate remains only inside the frozen 103-row fingerprint representation, where changing it would have changed the reviewed blob. It is no longer used as the 43-pair identity authority.

## 4. New bounded Win32 predicate

The test-only primary reader now performs read-only Windows reparse inspection:

```text
GetFileAttributesW
  -> require FILE_ATTRIBUTE_REPARSE_POINT
CreateFileW
  desired access = 0
  share read/write/delete
  OPEN_EXISTING
  FILE_FLAG_OPEN_REPARSE_POINT
  FILE_FLAG_BACKUP_SEMANTICS
DeviceIoControl(FSCTL_GET_REPARSE_POINT)
  -> parse REPARSE_DATA_BUFFER
  -> require IO_REPARSE_TAG_MOUNT_POINT (0xA0000003)
  -> parse substitute and print names
  -> canonicalize only NT path prefix/case/separator/absolute form
  -> compare exact frozen target
```

It performs no create, delete, relink, rename, retarget, ACL, registry, cache, or content operation.

The 43 expected installed names, cache target names, and manifest SHA-256 values were frozen into the harness from the already-reviewed initial PD2 formal artifact and its D4-CI `cache_db` mapping. The retained source artifact had SHA-256 `e4fd6592cb8be48bf3a40faf30027cd79b00450b0b0d2ad9e0a5e137a3022d2c`. No current scan was promoted to a new baseline.

## 5. Independent PowerShell oracle

The secondary oracle uses only:

```powershell
Get-ChildItem -LiteralPath <frozen installed root> -Force
Where-Object { $_.LinkType -eq 'Junction' }
FullName / Name / LinkType / Target
ConvertTo-Json
```

It contains no write cmdlet and runs as an independent read-only subprocess. It does not replace the Win32 reparse reader; both must agree with each other and the frozen inventory.

## 6. R1-A static verification

| Check | Result |
|---|---|
| exact interpreter `C:\isaacenvs\isaac45_harl\python.exe` | PASS |
| Python | 3.10.20 |
| `py_compile` | PASS |
| test-only Win32 helper static contract | PASS |
| expected pair constants | 43, unique installed paths and targets |
| manifest digest format | 43/43 valid SHA-256 |
| production warm-up AST equivalence | PASS |
| 45-file source hashes | EXACT |
| critical static manifests | PASS |
| Snapshot order static guard | PASS |
| frozen ten-item formal STOP taxonomy | EXACT |
| D4-O classifier hash | EXACT |
| `git diff --check` | PASS; existing line-ending warnings only |

Static evidence artifact:

```text
C:\Users\33506\AppData\Local\Temp\b2_v2_pd2_r1_static_20260828.json
SHA-256: 34d0068ab338fc014df3f380d5eee58b6c836c07dd636bd48e1d6e9c97bf4974
```

No worker, AppLauncher, SimulationApp, Isaac, Torch CUDA, HARL, or MRTA operation occurred during static verification.

## 7. R1-A detector-only dual-oracle result

Detector-only artifact:

```text
C:\Users\33506\AppData\Local\Temp\b2_v2_pd2_r1_detector_only_20260828.json
SHA-256: 27cb175b67e3c5c04e04347c62d9af3448f10309e47ebf8b8594f4a471a31a75
```

| Contract | Python/Win32 | PowerShell | Joint result |
|---|---:|---:|---:|
| expected/observed Junction count | 43/43 | 43/43 | PASS |
| exact installed path set | PASS | PASS | PASS |
| exact target set | PASS | PASS | PASS |
| pair mapping | 43/43 | 43/43 | PASS |
| mount-point reparse tag | 43/43 `0xA0000003` | `LinkType=Junction` 43/43 | PASS |
| exact manifest identity | 43/43 | supporting target oracle | PASS by primary |
| installed-path duplicates | 0 | 0 | PASS |
| target duplicates | 0 | 0 | PASS |
| unexpected Junctions | 0 | 0 | PASS |
| primary vs PowerShell mapping | — | — | EXACT |
| mutation operations | 0 | 0 | PASS |

The same detector-only invocation also established:

```text
45-file protected/audited hashes: EXACT
103-row fingerprint expected:
  ebdfb41e35d85b55eb7d86acf2ab78b33229ca0bec30623d1c88ec297deb846f
103-row fingerprint observed:
  ebdfb41e35d85b55eb7d86acf2ab78b33229ca0bec30623d1c88ec297deb846f
critical manifests: PASS
startup environment: PASS
worker/AppLauncher/Isaac/CUDA: 0/0/0/0
```

R1-A classification:

```text
PHASE-B2-V2-PD2-R1-JUNCTION-PREDICATE-CORRECTION-PASS-ELIGIBLE-FOR-FORMAL-REENTRY
```

This made R1-B eligible; it was not a PD2 runtime PASS.

## 8. R1-B formal execution accounting

Exactly one newly authorized formal supervisor execution was run. There was no retry, alternate configuration, extra warm-up, CPU fallback, comparison worker, or second AppLauncher lifetime.

Formal artifact:

```text
C:\Users\33506\AppData\Local\Temp\b2_v2_pd2_r1_formal_result_20260828.json
SHA-256: 03d3574f7562e23ece965b6468a45b1e02448faf4d2c4eb25354f1f32fe61946
elapsed: 119.109 seconds
```

Formal PRELAUNCH reran the entire gate and passed:

```text
45-file hashes:                  EXACT
103-row fingerprint:            EXACT
Win32 Junction pairs:           43/43 PASS
PowerShell Junction pairs:      43/43 PASS
dual-oracle mapping:             EXACT
critical manifests:             PASS
startup environment:            PASS
```

## 9. S0 exact production-startup evidence

S0 passed. The durable ordered event ledger contained 19 events:

```text
worker_started
app_launcher_module_import_complete
torch_import_begin
torch_import_complete
cuda_is_available_begin
cuda_is_available_end
set_device_begin
set_device_end
zeros_begin
zeros_end
linear_construct_move_begin
linear_construct_move_end
linear_forward_begin
linear_forward_end
synchronize_begin
synchronize_end
app_launcher_constructor_entry
app_launcher_constructor_returned
startup_config_validated
```

Exact warm-up trace:

```text
device:             cuda:0
allocation:         torch.zeros((1,1)), default float32
Linear:             nn.Linear(1,1), one forward
synchronize:        exactly one
explicit matmul:    0
retry:              0
seed before warmup: 0
```

AppLauncher returned. Runtime configuration was exact:

```text
headless:           true
device:             cuda:0
enable_cameras:     false
livestream:         0
XR:                 false
experience override: empty
resolved experience:
  E:\Project\IsaacLab_HARL\apps\isaaclab.python.headless.kit
experience SHA-256:
  475bb23c5941fbaaf0186991bf6e5445a267b1e0fd8bbab333cc78dc2e1bc795
```

This establishes that the current exact workaround-based production startup prefix and AppLauncher return completed in this one worker. It does not establish warm-up necessity, a cuBLAS root cause, environment/VCritic success, or pre-R8 equivalence.

## 10. First formal STOP at S0R

S0R captured two consecutive complete enabled-set snapshots and passed the in-function equality assertion before entering critical-row processing. However, the raw snapshot DTO was not durably assigned to the worker result because the function failed before returning; therefore no enabled ID list/count/hash is claimed as persisted S0R evidence.

The first critical entry was `isaaclab`. Kit returned `get_extension_dict()` as a `carb.dictionary.Item`. The test-only adapter then called:

```python
extension.get("version")
```

The installed API requires:

```text
get(key, default)
```

Exact exception class/message boundary:

```text
TypeError: get(): incompatible function arguments
supported signature:
  carb.dictionary._dictionary.Item.get(self, str, object) -> object
invoked with:
  <carb.dictionary.Item>, "version"
```

Trace boundary:

```text
runtime_extension_gate
-> _manager_version(extension)
-> extension.get("version")
-> TypeError
```

No critical runtime identity row was durably completed, so S0R is not PASS. This is evidence of a test-only S0R adapter/API incompatibility; it is not evidence that `isaaclab` version/path/manifest identity mismatched.

The formal artifact retained its emitted frozen-taxonomy classification and first boundary:

```text
classification:
  PD2-STOP-STARTUP-EQUIVALENCE-MISMATCH

first_boundary:
  S0R
```

Per the one-run/no-retry rule, the adapter was not corrected after this result and formal PD2 was not rerun.

## 11. S0-S6 and snapshot matrix

| Stage | Result | Evidence |
|---|---|---|
| PRELAUNCH | PASS | hashes/fingerprint/43-pair dual oracle/manifests/environment exact |
| S0 | PASS | exact warm-up, AppLauncher return, experience/config ledger |
| S0R complete-set comparison | prefix assertion passed; full stage NOT PASS | raw snapshots not durably returned |
| S0R critical identity | **STOP** | first `carb.dictionary.Item` version-read adapter call raised `TypeError` |
| S1 seed/environment/components/reset/I1/I2 | NOT RUN | stopped at S0R |
| Snapshot A | NOT CAPTURED | components not constructed |
| S2 installed VCritic `[2,418] -> [2,1]` | NOT RUN | original blocker not reached |
| S3 HAPPO actor | NOT RUN | no actor constructed/forwarded |
| S4 physical event-route step | NOT RUN | no environment |
| S5 continuation | NOT RUN | no environment |
| S6 TIME_LIMIT/I4/I5a/I5b | NOT RUN | no environment |
| Snapshot B | NOT CAPTURED | S6 not reached |

No seed/RNG ledger beyond the S0 no-seed assertion, environment configuration, DVM rows, proposal/logprob, P2/Ak, terminal sidecar, ACK, buffer, GAE, or ValueNorm runtime evidence was produced.

## 12. Shutdown evidence

D4-O evidence was safely classified:

```text
primary result valid:              yes
O4 primary persisted:              yes
O5 immediately before close:       yes
O6 close returned:                 absent; no in-process return claim
worker exit code:                  0
timeout / supervisor kill:         false / false
worker alive after wait:           false
known child survivors:             0
supervisor cleanup:                PASS
shutdown class:
  EXTERNAL_CLEAN_TERMINATION
safe shutdown:                     true
```

No result is inferred from exit code 0 alone; the joint D4-O evidence above is the authority.

## 13. Postrun integrity

The supervisor recaptured the same 103 rows and the corrected dual Junction oracles only after worker death:

```text
before fingerprint:
  ebdfb41e35d85b55eb7d86acf2ab78b33229ca0bec30623d1c88ec297deb846f
after fingerprint:
  ebdfb41e35d85b55eb7d86acf2ab78b33229ca0bec30623d1c88ec297deb846f
raw row changes:                 0
before/after Win32 pair oracle:  PASS / PASS
before/after PowerShell oracle:  PASS / PASS
postrun mapping equality:        PASS
protected hashes:                unchanged
postrun class:
  NO_OBSERVED_STATE_CHANGE
postrun eligible:                true
```

This is current reviewed post-R8 state equality across the bounded worker lifetime. It is not a clean-environment or pre-R8-equivalence claim.

## 14. Source and no-training integrity

```text
production source changes:          NONE
PD1/D4-CI audited source set:        EXACT
installed HARL changes:              NONE
I0-I6 changes:                       NONE
official Kit changes:                NONE
shared cache/registry/Junction writes: NONE
only code changed:                   test-only PD2 harness

Isaac environment construction:      0
environment reset / step:            0 / 0
actor / VCritic forward:              0 / 0
optimizer.step / backward:            0 / 0
ValueNorm updates:                    0
checkpoint load / save:               0 / 0
training / playback / evaluation:     NOT RUN
public route activation:              0
B2-R:                                 NOT AUTHORIZED
commit:                               NONE
```

Final `py_compile` and `git diff --check` passed; line-ending notices concern the pre-existing dirty worktree.

## 15. Causal non-claims

PD2-R1 does not establish:

- pre-R8 restoration or equivalence;
- a clean Kit/shared environment;
- that the pre-App warm-up is intrinsically required;
- that a CUDA, cuBLAS, Isaac, Torch, Kit, HARL, or MRTA defect is fixed;
- whether the original VCritic blocker reproduces under the production startup prefix;
- real actor, physical lifecycle, continuation, or TIME_LIMIT transport success;
- public-route, runtime, policy, learner, B2-R, or training readiness.

It establishes only that the corrected test-only dual Junction oracle observed the frozen post-R8 43-pair inventory exactly, formal PRELAUNCH and S0 passed, and the single re-entry stopped at a new test-only S0R version-reader API boundary.

## 16. Final decision and stop

Stop for GPT/user review. Do not repair `_manager_version()` or rerun formal PD2 under this authorization.

If a future slice is explicitly authorized, its narrow first task should be to correct and statically/synthetically verify the test-only `carb.dictionary.Item` field adapter against the installed read-only extension-manager API, while preserving the corrected Junction reader, frozen baseline, S0R identity fields, production sources, and no-retry discipline. A new formal execution requires separate authorization.

```text
final classification:
  PD2-STOP-STARTUP-EQUIVALENCE-MISMATCH

first authoritative boundary:
  S0R

B2-V2-PD2-R1:
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
