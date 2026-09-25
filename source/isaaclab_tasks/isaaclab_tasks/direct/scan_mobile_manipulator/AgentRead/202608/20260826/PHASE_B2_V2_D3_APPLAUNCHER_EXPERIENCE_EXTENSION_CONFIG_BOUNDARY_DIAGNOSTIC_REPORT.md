# Phase B2-V2-D3 AppLauncher Experience / Extension / Config Boundary Diagnostic Report

Date: 2026-08-26

Overall classification: `PHASE-B2-V2-D3-STOP-DIAGNOSTIC-BOUNDARY-VIOLATION`

## 1. Outcome

The formal B0-B4 core matrix completed and isolated a narrower, repeatable boundary:

```text
B0 direct minimal SimulationApp:             PASS 3/3
B1 exact AppLauncher control:                FAIL 3/3
B2 direct + AppLauncher experience only:     FAIL 3/3
B3 direct + AppLauncher config only:         PASS 3/3
B4 direct + AppLauncher experience + config: FAIL 3/3
```

Every B1/B2/B4 failure was the exact D1/D2/V2 error at `matmul_call`, after basic CUDA allocation/kernel/synchronization had completed:

```text
CUDA error: CUBLAS_STATUS_NOT_INITIALIZED
when calling `cublasCreate(handle)`
```

Evidence-supported completed core boundary:

```text
APPLAUNCHER_EXPERIENCE_SUFFICIENT_BOUNDARY
```

Precise meaning: in this tested direct `SimulationApp` contrast, selecting the exact experience chosen by AppLauncher was sufficient to reproduce the observed failure without the AppLauncher Python wrapper and without AppLauncher's resolved config. AppLauncher wrapper code is therefore not necessary for reproduction in this contrast; the resolved config alone was not sufficient.

The authorized extension-group follow-up then completed three stable subtraction variants, all still failing. A fourth broad `isaacsim.exp.base.python` group variant exceeded the 180-second worker timeout without persisting a post-startup/result artifact. The supervisor terminated the process tree; it was no longer alive, but safe `SimulationApp.close()` was not demonstrated. Per the mandatory stop rule, no retry, timeout increase, or further isolation was performed.

Therefore:

```text
D3 core matrix:               COMPLETE
experience boundary:          ISOLATED
extension-group isolation:    STOPPED / INCOMPLETE
D3 overall:                   STOPPED / INCOMPLETE
causal root cause:             NOT ESTABLISHED
```

## 2. Starting checkpoint and frozen status

```text
branch: main
HEAD:   14993dee344bade0230d2eb97b5f22171331f44a
describe at start: v2.0.0-53-g14993dee-dirty

B2-D:                REVIEW PASS / FROZEN
B2-I0 through B2-I6: REVIEW PASS / CLOSED
B2-V1:               GPT REVIEW PASS / CLOSED
B2-V2:               STOPPED / INCOMPLETE
B2-V2-D1:            GPT REVIEW PASS / CLOSED
B2-V2-D2:            GPT REVIEW PASS / CLOSED
B2-R:                NOT AUTHORIZED
runtime readiness:   BLOCKED
policy readiness:    BLOCKED
learner readiness:   BLOCKED
training:            NOT AUTHORIZED
commit:              NONE
```

Frozen D1 boundary: `APP_LAUNCHER_CUDA_CONTEXT_INTERACTION`.

Frozen D2 characterization: `APPLAUNCHER_TORCH_CUDA_FIRST_USE_ORDER_SENSITIVE_BEHAVIOR`.

No upstream MRTA, lifecycle, P2/Ak, wrapper, learner, or HARL contract was reopened.

## 3. Scope and files

Added test-only diagnostic:

- `scripts/environments/test_assignment_phase_b2_v2_d3_applauncher_experience_extension_config_diagnostic.py`

Documentation:

- this report;
- updated `AgentRead/TASK_PROGRESS.md`.

```text
production modifications:       NONE
AppLauncher/framework changes:  NONE
production .kit changes:        NONE
DirectMARLEnv changes:          NONE
installed Isaac Sim changes:    NONE
installed HARL changes:         NONE
driver/Torch/CUDA changes:      NONE
```

Temporary test-only `.kit` variants were generated under a system temporary directory, were never registered by production, and were removed when the isolation supervisor exited.

## 4. Exact runtime inventory

```text
interpreter:          C:\isaacenvs\isaac45_harl\python.exe
Python:               3.10.20
OS API:               Windows-10-10.0.26100-SP0 (Windows 11 build 26100)
Torch:                2.5.1+cu121
torch.version.cuda:   12.1
GPU:                  NVIDIA GeForce RTX 4060 Ti
driver:               537.58
VRAM:                 8188 MiB
Isaac Sim:            4.5.0.0
isaaclab metadata:    0.36.23
isaaclab-tasks:       0.10.31
HARL:                 1.0.0
device/dtype/matrix:  cuda:0 / float32 / 8x8
seed:                 260826
worker timeout:       180 seconds
CUDA env variables:  none present
```

The documented-compatibility conclusions frozen by D2 were not reopened.

## 5. SimulationApp API audit

Installed source:

```text
C:\isaacenvs\isaac45_harl\Lib\site-packages\isaacsim\exts\
  isaacsim.simulation_app\isaacsim\simulation_app\simulation_app.py
```

SHA-256:

```text
7d9ac4310913d776c17abe9f8cd0041b3d4d62cfcf6cd1a7d0548e85c2dd5b69
```

The local Isaac Sim 4.5 constructor is:

```python
SimulationApp(launch_config: dict = None, experience: str = "")
```

When `experience=""`, it checks its installed `EXP_PATH` candidates and selects the first existing file. In this environment the resolved default is:

```text
C:\isaacenvs\isaac45_harl\Lib\site-packages\isaacsim\apps\
  isaacsim.exp.base.python.kit
```

No constructor patch or monkeypatch was used.

## 6. Exact AppLauncher inputs and hashes

Local AppLauncher source:

```text
source/isaaclab/isaaclab/app/app_launcher.py
SHA-256: 6d9caa29f7177103cbdbd217eb18db19ef00cdadc2f1ecc7c79adc9d29da44c1
```

All three B1 workers captured identical runtime resolution:

```text
call:                AppLauncher(headless=True)
experience:          E:\Project\IsaacLab_HARL\apps\isaaclab.python.headless.kit
headless:            true
device_id:           0
livestream:          0
enable_cameras:      false
offscreen_render:    false
render_viewport:     false
xr:                  false
```

Exact `_sim_app_config` passed by AppLauncher:

```json
{
  "active_gpu": 0,
  "headless": true,
  "hide_ui": true,
  "physics_gpu": 0
}
```

The resulting `SimulationApp.config` also contains SimulationApp defaults, including `multi_gpu=true` and `create_new_stage=true`; those keys were not present in AppLauncher's captured `_sim_app_config`.

Selected experience:

```text
E:\Project\IsaacLab_HARL\apps\isaaclab.python.headless.kit
SHA-256: 475bb23c5941fbaaf0186991bf6e5445a267b1e0fd8bbab333cc78dc2e1bc795
```

Direct-default experience chain:

```text
isaacsim.exp.base.python.kit
  SHA-256: 1806f0bff51b49af8754b5d150fe64f5942f9b49a22bcfd67ed5d40b4cfddea9
  dependency -> isaacsim.exp.base

isaacsim.exp.base.kit
  SHA-256: ba9b7e23f5a3bc320ed8d7e3391d2080649b606cff15444b9e751ee16331f9b3
```

`isaaclab.python.headless.kit` is a standalone experience rather than an inheritance of `isaacsim.exp.base.python`. It declares a smaller physics/warp/Kit core set, selected Isaac Sim core extensions, and the five Isaac Lab extensions; it also supplies headless/rendering/physics/extension-folder settings. Both experience paths explicitly enable the platform's Vulkan setting in their respective config structure.

## 7. B0-B4 definitions and parity

| Property | B0 | B1 | B2 | B3 | B4 |
|---|---|---|---|---|---|
| AppLauncher wrapper | no | yes | no | no | no |
| experience | SimulationApp default/base-python | AppLauncher exact | AppLauncher exact | default/base-python | AppLauncher exact |
| constructor config | `{"headless":true}` | AppLauncher exact | `{"headless":true}` | AppLauncher exact | AppLauncher exact |
| explicit pre-startup Torch CUDA | no | no | no | no | no |
| repeats | 3 | 3 | 3 | 3 | 3 |

All cases used the same worker, device, dtype, matrix, seed, and operation sequence:

```text
basic CUDA allocation
-> x + 1
-> synchronize
-> matmul 8x8
-> synchronize
-> Linear(8,8) forward
-> synchronize
```

Linear was not attempted after a matmul failure in the same process.

## 8. Formal core result matrix

| Case | Result | Exact outcome | Enabled extensions |
|---|---:|---|---:|
| B0 direct minimal | PASS 3/3 | basic/matmul/Linear finite | 300, identical set hash across repeats |
| B1 AppLauncher | FAIL 3/3 | exact error at `matmul_call` | 67, identical set hash |
| B2 experience only | FAIL 3/3 | exact error at `matmul_call` | same 67/set hash as B1 |
| B3 config only | PASS 3/3 | basic/matmul/Linear finite | same 300/set hash as B0 |
| B4 experience+config | FAIL 3/3 | exact error at `matmul_call` | same 67/set hash as B1/B2 |

No case was mixed. Core timeouts and surviving workers were both zero; every core worker persisted its artifact and terminated after the shutdown path.

### Core decision

```text
B0 PASS
B1 FAIL
B2 FAIL
B3 PASS
B4 FAIL
```

This is the authorized Scenario A pattern. The experience path/experience-loaded startup composition is sufficient in the direct contrast; AppLauncher wrapper behavior and resolved config are not necessary for reproduction. This does not mean the experience is defective.

## 9. Torch loading and CUDA timeline

All B0-B4 representative timelines agreed on:

```text
process start:                   torch absent
before simulator constructor:    torch absent
immediately after startup:       torch present
Torch CUDA immediately after:    uninitialized
before explicit Torch access:    torch present, CUDA uninitialized
before CUDA allocation:          CUDA uninitialized
before matmul:                    CUDA initialized
```

Representative state immediately before matmul in both passing and failing cases:

```text
memory allocated: 1,536 bytes
memory reserved:  2,097,152 bytes
basic CUDA:       already completed and synchronized
```

Thus implicit Torch import and basic post-startup CUDA allocation occur on both sides of the B0/B2 boundary. Neither distinguishes PASS from FAIL here.

## 10. Experience/extension static and runtime comparison

Runtime enabled-extension set sizes:

```text
B0/B3 base-python experience:       300
B1/B2/B4 Isaac Lab headless:         67
```

The B2-only enabled set relative to B0 contained:

```text
isaaclab
isaaclab_assets
isaaclab_tasks
isaaclab_mimic
isaaclab_rl
isaaclab.python.headless experience package
omni.physx.fabric
```

B0 had a much larger base/GUI/rendering/robot/sensor/replicator/deprecated-extension composition. The report does not dump that full list; its exact enabled-set hash and full IDs remain in the temporary structured core result used to produce this report.

## 11. Bounded test-only extension variants

The variants copied the exact headless experience into a system temporary directory, rewrote only `${app}` to the original absolute repository `apps` root so extension-folder semantics remained anchored, and then removed or added the declared dependency group. Production `.kit` files were never edited.

| Variant | Exact group difference | Runtime set confirmation | Result |
|---|---|---|---:|
| G1 | remove all five Isaac Lab dependencies | all five absent; fabric remains; 62 enabled | FAIL 2/2 |
| G2 | remove `omni.physx.fabric` | fabric absent; five Isaac Lab extensions remain; 66 enabled | FAIL 2/2 |
| G3 | remove both groups | all six absent; 61 enabled | FAIL 2/2 |
| G4 | add `isaacsim.exp.base.python` dependency group | no post-startup structured set captured | TIMEOUT 1/1; second repeat not run |

G1-G3 all reproduced the exact error at `matmul_call`, with no timeout and safe worker termination. Therefore the five Isaac Lab extension group, `omni.physx.fabric`, and their joint inclusion are each not necessary for the observed failure in these tested variants.

This does not prove those extensions can never influence CUDA behavior in other compositions.

## 12. Mandatory STOP at G4

G4 was the gated broad-group contrast used only because G1-G3 all remained failing. It added:

```text
"isaacsim.exp.base.python" = {}
```

to the test-only copy of the failing headless experience. Its first worker:

```text
PID:                         24988
timeout limit:               180 seconds
elapsed before termination:  180.766 seconds
structured worker result:    NOT PERSISTED
CUDA probe result:            NOT REACHED / UNKNOWN
process exit after taskkill:  1
worker alive after wait:      false
safe SimulationApp shutdown: NOT DEMONSTRATED
second repeat:                NOT RUN
```

The captured output showed extension startup/deprecation messages and RTX scene-database warnings through approximately 12.8 seconds, then no result artifact before timeout. Because the worker did not persist a post-startup checkpoint, the exact internal stall location cannot be claimed; it may be within or after constructor startup but before the result path. No cuBLAS outcome exists for G4.

This timeout is not evidence that the base-python group passes, fails, or causes a hang. It only establishes an unsafe/inconclusive variant lifecycle requiring the mandatory diagnostic stop.

## 13. Narrowest valid evidence and unresolved boundary

Valid completed evidence:

```text
AppLauncher exact experience path:
  sufficient to reproduce in direct SimulationApp, 3/3

AppLauncher exact config alone:
  insufficient, PASS 3/3

AppLauncher wrapper:
  not necessary for reproduction

Isaac Lab extension group:
  not necessary in G1, FAIL 2/2 after removal

omni.physx.fabric:
  not necessary in G2, FAIL 2/2 after removal

both groups jointly:
  not necessary in G3, FAIL 2/2 after removal
```

Not isolated because of the STOP:

```text
specific remaining extension group
specific headless experience setting
absence of a base-python extension group
experience setting/extension interaction
causal source of cuBLAS handle failure
```

## 14. Protected hashes and filesystem integrity

Protection covered 34 files:

- D2's 28 production/DirectMARLEnv/installed-HARL/V2/D1 files;
- D2 harness;
- local AppLauncher;
- production Isaac Lab headless experience;
- installed base-python and base experiences;
- installed SimulationApp source.

Results:

```text
core before/after:       34/34 unchanged
extension before/after:  34/34 unchanged
temporary variants:      removed
production .kit changes: none
```

## 15. Worker, shutdown, and execution accounting

```text
formal core workers:              15
completed extension workers:       6
timed-out extension workers:       1
total launched:                   22
normal worker timeouts:            0
G4 timeout:                        1
workers alive after supervisor:    0
core/G1-G3 safe shutdown:          PASS
G4 safe shutdown:                  NOT DEMONSTRATED

environment constructed:           0
environment reset/step:             0 / 0
HARL calls:                         0
I0-I6 calls:                        0
optimizer/backward:                 0 / 0
training/playback/evaluation:       NOT RUN
checkpoint operations:              NONE
public route activation:            NONE
original B2-V2:                     NOT RERUN
```

The post-termination GPU remained visible; read-only `nvidia-smi` reported 1085 MiB used and 6877 MiB free. This is cleanup evidence, not a resource-causality claim.

## 16. Commands and checks

Syntax:

```powershell
C:\isaacenvs\isaac45_harl\python.exe -m py_compile \
  scripts\environments\test_assignment_phase_b2_v2_d3_applauncher_experience_extension_config_diagnostic.py
```

Core matrix:

```powershell
C:\isaacenvs\isaac45_harl\python.exe -u \
  scripts\environments\test_assignment_phase_b2_v2_d3_applauncher_experience_extension_config_diagnostic.py \
  --repeat 3 --timeout-seconds 180 --json-output <temporary-core-result>
```

Gated extension isolation:

```powershell
C:\isaacenvs\isaac45_harl\python.exe -u \
  scripts\environments\test_assignment_phase_b2_v2_d3_applauncher_experience_extension_config_diagnostic.py \
  --extension-isolation-core-result <temporary-core-result> \
  --repeat 2 --timeout-seconds 180 --json-output <temporary-extension-result>
```

The G4 timeout caused supervisor classification `PHASE-B2-V2-D3-STOP-DIAGNOSTIC-BOUNDARY-VIOLATION`; no command was rerun after that stop.

Final `py_compile`, protected-hash comparison, `git diff --check`, and status checks are recorded in `TASK_PROGRESS.md`.

## 17. Causal non-claims

This diagnostic does not prove:

- that the AppLauncher experience or any extension is buggy;
- that any specific extension causes the cuBLAS failure;
- whether a missing base-python extension would restore correct behavior;
- that G4 itself hangs deterministically;
- that the driver, Torch, CUDA, Kit, rendering, physics, or memory is causal;
- that pre-App CUDA initialization is a valid repair;
- any MRTA, I0-I6, HARL, wrapper, learner, or policy semantic defect;
- B2-V2 or any readiness gate.

## 18. Recommended next decision

Do not retry G4, change its timeout, add warm-up, repair V2, or continue extension bisection without a new review.

GPT/user should first review two separate facts:

1. the valid completed core result, which isolates the exact AppLauncher-selected experience as sufficient in a direct contrast;
2. the G4 lifecycle violation, which prevents D3 from claiming completed extension-group isolation.

If further diagnosis is authorized, it should be a new narrowly bounded slice that avoids the broad combined base-python experience dependency and decides whether to:

- characterize the G4 startup timeout itself; or
- use smaller, statically selected base-python extension/settings groups with an explicit shutdown oracle.

No repair decision should precede that review.

## 19. Final classification

```text
classification:
  PHASE-B2-V2-D3-STOP-DIAGNOSTIC-BOUNDARY-VIOLATION

B2-V2-D3 core:
  COMPLETE

baseline minimal SimulationApp:
  PASS 3/3

AppLauncher control:
  exact cuBLAS FAIL 3/3

experience-only:
  exact cuBLAS FAIL 3/3

config-only:
  PASS 3/3

experience+config:
  exact cuBLAS FAIL 3/3

narrowest completed boundary:
  APPLAUNCHER_EXPERIENCE_SUFFICIENT_BOUNDARY

extension isolation:
  G1-G3 COMPLETE / G4 TIMEOUT / OVERALL INCOMPLETE

B2-V2-D3 overall:
  STOPPED / INCOMPLETE / AWAITING GPT REVIEW

causal root cause:
  NOT ESTABLISHED / NOT OVERCLAIMED

repair / warm-up:
  NOT PERFORMED / NOT DEPLOYED

production/framework/HARL changes:
  NONE

environment / HARL:
  NOT CONSTRUCTED / NOT RUN

optimizer/backward:
  0 / 0

original B2-V2:
  NOT RERUN / STOPPED / INCOMPLETE

B2-R:
  NOT AUTHORIZED

training:
  NOT AUTHORIZED

commit:
  NONE
```

Stop here for GPT/user review.
