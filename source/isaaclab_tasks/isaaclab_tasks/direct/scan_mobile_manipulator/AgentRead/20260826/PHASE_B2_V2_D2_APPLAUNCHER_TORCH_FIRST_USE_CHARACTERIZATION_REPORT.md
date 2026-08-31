# Phase B2-V2-D2 AppLauncher / Torch cuBLAS First-use Characterization Report

Date: 2026-08-26

Classification: `PHASE-B2-V2-D2-APPLAUNCHER-TORCH-FIRST-USE-CHARACTERIZATION-COMPLETE-AWAITING-GPT-REVIEW`

## 1. Result

The D1 failure is repeatable, but Torch module import timing alone does not explain it. The narrow observed discriminator is whether the Torch CUDA context has been initialized before AppLauncher startup:

```text
C0 plain Torch matmul/Linear:                    PASS 1/1
C1 exact D1 AppLauncher-first ordering:          FAIL 3/3
C2 official-order cleanliness oracle:             FAIL 3/3
C3 Torch preimport, no pre-App CUDA:              FAIL 3/3
C4 pre-App basic CUDA, no pre-App cuBLAS:         PASS 3/3
C5 pre-App cuBLAS:                                PASS 3/3
C6 direct minimal SimulationApp contrast:         PASS 3/3
```

All three C1 and all three C3 runs failed at the first post-AppLauncher `torch.matmul` call, before its synchronization, with the exact D1/V2 error. The original three C2 workers continued past an incomplete preconstruction-only oracle and then reached the same matmul failure; review of their recorded timelines correctly reclassifies C2 itself as an oracle failure because Torch was implicitly loaded during AppLauncher startup:

```text
RuntimeError: CUDA error: CUBLAS_STATUS_NOT_INITIALIZED
when calling `cublasCreate(handle)`
```

The C2 operational continuation first completed CUDA allocation and a basic CUDA kernel successfully after AppLauncher, then failed at its first cuBLAS call. It is useful first-use evidence but is not a clean official-order oracle PASS. C4 performed only allocation plus `x + 1` before AppLauncher—no matmul or Linear—and subsequently passed both post-AppLauncher matmul and Linear in 3/3 fresh processes. Therefore a pre-AppLauncher cuBLAS warm-up is not necessary for the observed behavior change.

Evidence-supported characterization:

```text
APPLAUNCHER_TORCH_CUDA_FIRST_USE_ORDER_SENSITIVE_BEHAVIOR
```

This is a characterization label, not a causal root-cause claim and not authorization to deploy CUDA or cuBLAS warm-up code. The frozen D1 earliest boundary remains `APP_LAUNCHER_CUDA_CONTEXT_INTERACTION`.

## 2. Starting checkpoint and frozen state

```text
branch: main
HEAD:   14993dee344bade0230d2eb97b5f22171331f44a
describe: v2.0.0-53-g14993dee-dirty

B2-D:                  REVIEW PASS / FROZEN
B2-I0 through B2-I6:   REVIEW PASS / CLOSED
B2-V1:                 GPT REVIEW PASS / CLOSED
B2-V2:                 STOPPED / INCOMPLETE
B2-V2-D1:              GPT REVIEW PASS / CLOSED
B2-R:                  BLOCKED / NOT AUTHORIZED
runtime readiness:     BLOCKED
policy readiness:      BLOCKED
learner readiness:     BLOCKED
training:              NOT AUTHORIZED
commit:                NONE
```

The D1 report, V2 STOP report, `TASK_PROGRESS.md`, and local `AgentRead/AGENTS.md` were read before execution. No I0-I6 contract was reopened.

## 3. Scope and changed files

Added test-only diagnostic:

- `scripts/environments/test_assignment_phase_b2_v2_d2_applauncher_torch_first_use_diagnostic.py`

Documentation:

- this report;
- updated `AgentRead/TASK_PROGRESS.md`.

```text
production modifications:      NONE
V2 harness modifications:      NONE
D1 harness modifications:      NONE
AppLauncher/framework changes: NONE
DirectMARLEnv changes:         NONE
installed HARL changes:        NONE
driver/package/system changes: NONE
```

The D2 script is not registered or imported by production. It contains no environment construction or HARL path.

## 4. D1 and V2 actual import/first-use audit

### V2 harness

The V2 worker imports and constructs AppLauncher at `test_assignment_phase_b2_v2_real_isaac_harl_interface_smoke.py:614-616`. Only the subsequently called `run_real_smoke()` explicitly imports Torch at line 285. Its first `torch.cuda.manual_seed_all()` and CUDA availability/device checks occur later, after AppLauncher startup.

Static answers for the V2 worker before AppLauncher construction:

```text
explicit torch import:                    NO
explicit torch.cuda availability query:  NO
explicit CUDA tensor allocation:         NO
explicit cuBLAS operation:                NO
```

### D1 D3 harness

The formal D1 D3 path uses `run_app_stage(stage="D3", warmup_before_app=False)`. It imports AppLauncher at line 381, constructs it at line 383, explicitly imports Torch at line 384, and then calls `tiny_cublas()`. The optional prewarm branch was false and D7B was not run.

Static answers for formal D1 D3 before AppLauncher construction are likewise all `NO`.

### Runtime `sys.modules` correction to visual source order

D2 C1/C2 recorded:

```text
process startup:                         torch absent
immediately before AppLauncher import:   torch absent
immediately before construction:         torch absent
immediately after SimulationApp startup: torch present, torch.cuda.is_initialized() == false
before explicit post-startup import:      torch already present, CUDA still uninitialized
before first cuBLAS op:                   Torch CUDA initialized by tensor allocation
```

Thus the scripts follow AppLauncher-first at the source level, but the exact clean C2 oracle is **not** satisfied: AppLauncher/Kit startup indirectly loads the Torch module before the script's explicit post-startup `import torch`. It does not initialize the Torch CUDA runtime in these observations. Import, CUDA first-use, and cuBLAS first-use remain distinct.

## 5. Local AppLauncher source audit

Audited:

- `source/isaaclab/isaaclab/app/__init__.py`;
- `source/isaaclab/isaaclab/app/app_launcher.py`;
- `source/isaaclab/isaaclab/app/runners.py`.

Findings:

```text
direct `import torch` in AppLauncher module: NO
direct torch.cuda query in AppLauncher:      NO
top-level simulator import:                  from isaacsim import SimulationApp
resolved device_id:                          0
resolved physics_gpu:                        0
resolved active_gpu:                         0
distributed/multi_gpu requested:             NO / key absent in final config
headless:                                    true
experience:                                  apps/isaaclab.python.headless.kit
```

`AppLauncher._resolve_device_settings()` writes `physics_gpu` and `active_gpu` from `device_id`; `multi_gpu=False` is written only inside its distributed branch. `_create_app()` passes `_sim_app_config` and the resolved experience file to `SimulationApp`.

`git diff v2.0.0 -- source/isaaclab/isaaclab/app/app_launcher.py` was empty. The local AppLauncher file therefore matches this repository's `v2.0.0` tag for the inspected startup behavior.

The official Isaac Lab 2.0 tutorial pattern constructs AppLauncher before the tutorial's explicit Torch import, as shown in the [Isaac Lab v2.0 deformable-object tutorial](https://isaac-sim.github.io/IsaacLab/v2.0.0/source/tutorials/01_assets/run_deformable_object.html). Local V2/D1 source ordering matches that documented structure. The D2 result shows that this documented ordering still fails for first post-AppLauncher cuBLAS use in the exact local installation.

## 6. Formal fresh-process matrix

Every case and repeat used `C:\isaacenvs\isaac45_harl\python.exe` in a new child process. Common parameters were:

```text
GPU/device: cuda:0 / NVIDIA GeForce RTX 4060 Ti
matrix:     [8,8] x [8,8]
dtype:      torch.float32
seed:       260826
headless:   true
```

Each allocation, basic kernel, matmul, and Linear stage was followed by `torch.cuda.synchronize()` where execution reached that point. Exceptions record whether they arose in the operation call or synchronization.

| Case | Ordering distinction | Formal result | Exact boundary |
|---|---|---:|---|
| C0 | plain Torch, no Isaac/AppLauncher | PASS 1/1 | matmul and Linear finite |
| C1 | exact D1: AppLauncher, explicit Torch import, first matmul | FAIL 3/3 | `post_app.matmul_call` |
| C2 | official AppLauncher-first structure with strict no-implicit-Torch oracle | ORACLE FAIL 3/3 | Torch present immediately after startup; initial continuation later failed at matmul |
| C3 | Torch preimport only; CUDA uninitialized before AppLauncher | FAIL 3/3 | `post_app.matmul_call` |
| C4 | pre-App basic CUDA allocation/kernel, no cuBLAS | PASS 3/3 | post-App matmul and Linear PASS |
| C5 | pre-App matmul/cuBLAS | PASS 3/3 | post-App matmul and Linear PASS |
| C6 | direct `SimulationApp({"headless": True})`, no AppLauncher | PASS 3/3 | post-startup basic/matmul/Linear PASS |

One supplemental C2 config-capture process ran after the formal matrix because the first report artifact queried `_config` instead of the correct `_sim_app_config`. Only this D2 metadata accessor was corrected. It confirmed `headless=true`, `active_gpu=0`, `physics_gpu=0`, `device_id=0`, and again produced the same failure after basic CUDA passed.

Final oracle review then found that the original C2 implementation enforced absence of Torch immediately before construction but not again immediately after startup. The three original timelines all show Torch becoming present during startup, so they are reclassified `OFFICIAL_ORDER_NOT_CLEANLY_REPRODUCED` 3/3. The D2-only oracle was corrected, and one final fifth C2 observation verified fail-closed at the strict oracle before any Torch CUDA operation. No critical case exceeded the authorized five-observation ceiling.

## 7. Case evidence and first-use timing

### C0 plain control

```text
matmul: PASS
Linear: PASS
matmul finite/sum: true / 16128.0
```

This reconfirms that plain Torch cuBLAS is available in a fresh process.

### C1 exact D1

All 3 runs:

```text
torch before AppLauncher construction: false
torch immediately after startup:       true
Torch CUDA immediately after startup:  uninitialized
first CUDA allocations:                PASS
first matmul call:                      exact CUBLAS_STATUS_NOT_INITIALIZED
```

The failure is `REPEATABLE_IN_3_OF_3_FORMAL_RUNS`; no universal-determinism claim is made.

### C2 official-order cleanliness oracle

Torch was absent immediately before AppLauncher construction in 3/3 runs, but present immediately after AppLauncher/SimulationApp startup and before the script's explicit Torch import in 3/3 runs. Under the task's exact requirement, this is:

```text
OFFICIAL_ORDER_NOT_CLEANLY_REPRODUCED: 3/3
```

The original three workers continued diagnostically after the incomplete preconstruction check and produced:

```text
post-App CUDA allocation: PASS
post-App basic x + 1:     PASS
post-App synchronize:    PASS
first post-App matmul:    exact cuBLAS failure
```

This continuation shows that post-App basic CUDA initialization is insufficient in this local stack, but it must not be called a clean official-order reproduction. The corrected strict oracle probe failed before any CUDA operation and closed SimulationApp safely.

### C3 Torch preimport only

`torch.cuda.is_initialized()` was false before AppLauncher in each observed run. C3 then failed 3/3 at the same post-App matmul call. Merely importing the Torch module before AppLauncher did not change the result.

### C4 pre-App basic CUDA only

C4 deliberately used no pre-App matmul or Linear. Its pre-App allocation and `x + 1` initialized Torch CUDA and synchronized successfully. Post-App matmul and Linear both passed in 3/3 runs.

This is the narrowest tested behavior-changing contrast. It is diagnostic evidence only, not a production prescription.

### C5 pre-App cuBLAS

Pre-App and post-App matmul both passed, and post-App Linear passed, in all 3 runs. Since C4 already passes without pre-App cuBLAS, a pre-created cuBLAS handle is not necessary for the observed pass outcome.

### C6 direct SimulationApp

Official-order C2 failed, so the conditional direct contrast was authorized. Direct minimal `SimulationApp({"headless": True})` passed post-startup basic CUDA, matmul, and Linear in 3/3 fresh processes.

This shows only that the minimal direct SimulationApp configuration used by C6 is insufficient to reproduce the failure. C6 did not load AppLauncher's custom `isaaclab.python.headless.kit` experience or reproduce all AppLauncher extension/config behavior, so it does not prove an AppLauncher Python-wrapper bug or a Kit bug.

## 8. AppLauncher config parity

C1 and the C2 operational continuation used the same fixture call, `AppLauncher(headless=True)`, same interpreter, same working directory, same GPU, and same tensor parameters. The corrected supplemental capture established:

```text
headless:    true
device_id:   0
active_gpu:  0
physics_gpu: 0
multi_gpu:   absent / not requested
```

C6 is intentionally a minimal underlying contrast and not configuration parity: it used direct `SimulationApp({"headless": True})` without AppLauncher's resolved experience. Its result must not be used to attribute causation to the wrapper alone.

## 9. CUDA memory/context observations

Representative observations:

```text
C1/C2 after AppLauncher, before Torch CUDA first-use:
  torch.cuda.is_initialized: false
  allocated/reserved:        0 / 0 bytes

C2 after post-App basic CUDA:
  allocated/reserved:        1,024 / 2,097,152 bytes
  basic CUDA:                 finite / synchronized
  next matmul:                FAIL

C4 after pre-App basic CUDA:
  allocated/reserved:        1,024 / 2,097,152 bytes
  post-App matmul memory:     about 8.5 MB allocated / 23 MB reserved
  post-App matmul/Linear:     PASS
```

Read-only `nvidia-smi` observations showed an 8188 MiB GPU with varying process/system use during Kit startup. The formal inventory near completion showed 1001 MiB used and 6961 MiB free. These values are context evidence only; they neither prove nor exclude a resource cause.

## 10. Installed software inventory

```text
Windows:            Windows 11 Home China, 10.0.26100, build 26100
Python executable:  C:\isaacenvs\isaac45_harl\python.exe
Python:             3.10.20
Torch:              2.5.1+cu121
torch.version.cuda: 12.1
Torch CUDA:         available
GPU:                NVIDIA GeForce RTX 4060 Ti
VRAM:               8188 MiB reported by nvidia-smi
driver:             537.58
Isaac Sim:          4.5.0.0
isaaclab metadata:  0.36.23
isaaclab-tasks:     0.10.31
HARL:               1.0.0
repository:         v2.0.0-53-g14993dee-dirty
HEAD:               14993dee344bade0230d2eb97b5f22171331f44a
CUDA env variables: none present
```

The package metadata versions are recorded as installed facts and are not used to guess the repository release; the git tag/describe and HEAD are recorded separately.

## 11. Authoritative compatibility audit

### NVIDIA driver

The [Isaac Sim 4.5 requirements](https://docs.isaacsim.omniverse.nvidia.com/4.5.0/installation/requirements.html) list Windows driver 537.58 as both recommended and minimum for GameReady/Studio drivers (and 537.70 for RTX/Quadro/Grid). The local GeForce driver is exactly 537.58.

```text
DRIVER_VERSION_MEETS_DOCUMENTED_ISAAC_SIM_4_5_REQUIREMENT
```

This proves only that the version is not below the documented value. It does not prove that the driver or local runtime cannot participate in the observed failure.

### Torch / CUDA / Isaac generation

The [Isaac Lab v2.0 release notes](https://isaac-sim.github.io/IsaacLab/v2.0.0/source/refs/release_notes.html) pair Isaac Lab 2.0 with Isaac Sim 4.5 and record the Torch dependency update to 2.5.1. The official [Isaac Lab 2.0.2 pip installation guide](https://isaac-sim.github.io/IsaacLab/v2.0.2/source/setup/installation/pip_installation.html) specifies Torch 2.5.1 from the `cu121` index for Windows/CUDA 12, and the [PyTorch official previous-versions page](https://docs.pytorch.org/get-started/previous-versions/) lists the same 2.5.1/cu121 Windows wheel configuration. Isaac Sim 4.5's [Python installation page](https://docs.isaacsim.omniverse.nvidia.com/4.5.0/installation/install_python.html) requires Python 3.10.

```text
CURRENT_TORCH_CUDA_BUILD_MATCHES_DOCUMENTED_CONFIGURATION
CURRENT_PYTHON_MAJOR_MINOR_MATCHES_DOCUMENTED_CONFIGURATION
```

The installed `torch 2.5.1+cu121`, CUDA build 12.1, Isaac Sim 4.5.0.0, and Python 3.10.20 are therefore not obviously outside the cited documented configuration. This does not prove binary/runtime compatibility in this exact environment and does not establish a version-independent cause.

### Compatibility Checker

A bounded filesystem search found only residual Compatibility Checker user configuration and extension-index metadata under `C:\Users\33506\AppData\Local\ov`; no runnable checker script/package was found under the conda environment, `C:\isaacsim`, or Downloads. It was not executed because no already-installed, clearly bounded standalone executable was available. No download, installation, extension acquisition, or system mutation was attempted.

## 12. Production entrypoint import/first-use audit

| Entrypoint | Torch import / CUDA first-use before AppLauncher | Characterization only |
|---|---|---|
| `scripts/reinforcement_learning/harl/train.py` | function-local Torch import followed by `torch.zeros`, `nn.Linear` forward, synchronize before AppLauncher | pre-App cuBLAS path, C5-like |
| `scripts/reinforcement_learning/harl/play_assignment.py` | top-level Torch import plus the same pre-App Linear warm-up | pre-App cuBLAS path, C5-like |
| `scripts/reinforcement_learning/harl/play.py` | top-level Torch import, no explicit pre-App CUDA operation | C3-like; generic script rejects assignment checkpoints |
| V2 real smoke harness | AppLauncher first; no pre-App Torch CUDA | C1-like and observed failing |
| D1 D3 harness | AppLauncher first; no pre-App Torch CUDA | C1 exact and observed failing |

The pre-App warm-up functions already existed before D2 and were neither added nor changed. D2 did not execute any production entrypoint.

### Harness-versus-production assessment

Current evidence does not support the simple claim that V2/D1 visually violate official explicit import ordering: they match the documented AppLauncher-first source structure. However, C2 proves that the stricter official-order oracle cannot be cleanly reproduced because AppLauncher/Kit itself loads Torch during startup. Nor does D2 support a production learned-policy defect, because it did not execute production and the assignment train/play entrypoints already use a different pre-App CUDA/cuBLAS first-use pattern.

The evidence instead establishes:

```text
V2/D1 verification harness:
  uses a locally failing no-pre-App-CUDA startup path
  AppLauncher startup implicitly loads Torch before the script import

assignment train/play entrypoints:
  statically use pre-App CUDA/cuBLAS initialization

public learned-policy runtime behavior:
  NOT TESTED / STILL BLOCKED
```

A V2 harness correction is not yet justified as a mere official-order repair, because the official-order case itself failed. Adding warm-up to V2 now would be an unauthorized workaround and could conceal the remaining AppLauncher experience/config boundary.

## 13. Repeatability, supervisor, and shutdown

Formal workers:

```text
C0: 1
C1-C6: 3 each
total formal fresh processes: 19
supplemental C2 config probe: 1
strict corrected C2 oracle probe: 1
timeouts: 0
workers alive after wait: 0
```

Every AppLauncher/SimulationApp worker persisted its structured pass/fail artifact before calling `SimulationApp.close()` in `finally`. SimulationApp-managed failure children can return process code 0 during shutdown, so the supervisor correctly treats the persisted `status=failed` artifact—not child exit code alone—as the CUDA oracle. No formal or supplemental process remained alive.

## 14. Protected hashes and mutation evidence

Protection covered the D1/V2 26-file set plus both original harnesses:

```text
reviewed I0-I6/runtime/lifecycle/environment/wrapper/training: protected
DirectMARLEnv:                                               protected
installed HARL actor/critic/buffers/runners/ValueNorm:       protected
original V2 harness:                                         protected
original D1 harness:                                         protected
formal before/after result:                                  28/28 unchanged
post-supplemental recheck against formal after-hashes:        28/28 unchanged
```

No protected source changed.

## 15. Commands and verification

Interpreter and syntax:

```powershell
D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python -c "import sys; print(sys.executable); print(sys.version)"
C:\isaacenvs\isaac45_harl\python.exe -m py_compile scripts\environments\test_assignment_phase_b2_v2_d2_applauncher_torch_first_use_diagnostic.py
```

Formal matrix:

```powershell
C:\isaacenvs\isaac45_harl\python.exe -u scripts\environments\test_assignment_phase_b2_v2_d2_applauncher_torch_first_use_diagnostic.py --repeat 3 --timeout-seconds 180 --json-output <temporary-result-path>
```

Additional read-only checks included git tag/HEAD/source diff, installed metadata, `torch.version.cuda`, Windows version, `nvidia-smi`, CUDA-related environment variables, local Compatibility Checker candidates, current protected hashes, and `git diff --check`.

Results:

```text
diagnostic py_compile: PASS
formal matrix:         COMPLETE
protected hashes:      PASS, 28/28 unchanged
worker shutdown:       PASS, 0 timeout / 0 surviving
git diff --check:      PASS for D2 script before documentation finalization
```

Final documentation-wide `git diff --check` is recorded in `TASK_PROGRESS.md` after both Markdown updates.

## 16. Explicit execution boundary and non-claims

```text
Isaac environment constructed: 0
environment reset/step:         0 / 0
I0-I6 executed:                 NO
HARL/VCritic/actor executed:    NO
optimizer/backward:             0 / 0
training/playback/evaluation:   NOT RUN
checkpoint operation:           NONE
public route activation:        NONE
original B2-V2 retry:           NOT RUN
production repair:              NONE
```

This diagnostic does not prove:

- an AppLauncher, SimulationApp, Kit, Torch, CUDA, driver, or extension bug;
- a resource-exhaustion cause;
- that a warm-up is a valid production fix;
- that actual production training/playback is working;
- any I0-I6 or MRTA semantic defect;
- B2-V2, runtime, policy, learner, or training readiness.

## 17. Recommended next decision

Do not retry V2 and do not add a production or harness warm-up from D2 evidence alone.

The next narrowly reviewed diagnostic should isolate the difference between:

```text
direct minimal SimulationApp (C6 PASS)
and
AppLauncher + isaaclab.python.headless.kit experience/extensions (C1 FAIL; C2 oracle FAIL)
```

A suitable provisional next slice is:

```text
B2-V2-D3
AppLauncher Experience / Extension / SimulationApp Config Boundary Diagnostic
```

It should remain environment-free and production-read-only, compare exact SimulationApp config/experience startup boundaries, and stop before proposing a repair. Only after that review should the user decide whether a V2-harness startup change or a broader runtime-entrypoint review is warranted.

## 18. Final classification

```text
classification:
  PHASE-B2-V2-D2-APPLAUNCHER-TORCH-FIRST-USE-CHARACTERIZATION-COMPLETE-AWAITING-GPT-REVIEW

B2-V2-D2:
  COMPLETE / AWAITING GPT REVIEW

repeatability:
  C1/C3 exact post-App first-cuBLAS failure:      3/3 each
  C2 strict official-order cleanliness oracle:    FAIL 3/3
  C4 pre-App basic CUDA, no cuBLAS:              PASS 3/3
  C5 pre-App cuBLAS:                             PASS 3/3
  C6 direct minimal SimulationApp:               PASS 3/3

startup/import order:
  explicit Torch preimport alone does not explain failure

first-use sensitivity:
  pre-App Torch CUDA context initialization changes observed result

documented compatibility:
  driver meets documented Isaac Sim 4.5 Windows value
  Torch 2.5.1+cu121 matches documented configuration

causal root cause:
  NOT ESTABLISHED / NOT OVERCLAIMED

production changes:
  NONE

installed HARL / IsaacLab framework:
  UNCHANGED

environment steps:
  0

optimizer/backward:
  0 / 0

original B2-V2:
  NOT RERUN; STOPPED / INCOMPLETE

B2-R:
  NOT AUTHORIZED

training:
  NOT AUTHORIZED

commit:
  NONE
```

Stop here for GPT/user review.
