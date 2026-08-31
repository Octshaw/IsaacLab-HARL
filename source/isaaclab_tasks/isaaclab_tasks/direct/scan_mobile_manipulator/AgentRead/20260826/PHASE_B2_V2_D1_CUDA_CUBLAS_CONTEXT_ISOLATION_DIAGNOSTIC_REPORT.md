# Phase B2-V2-D1 CUDA/cuBLAS Context Isolation Diagnostic Report

Date: 2026-08-26

Classification: `PHASE-B2-V2-D1-CUDA-CUBLAS-CONTEXT-DIAGNOSTIC-COMPLETE-AWAITING-GPT-REVIEW`

## 1. Result

The earliest reproducible boundary is:

```text
APP_LAUNCHER_CUDA_CONTEXT_INTERACTION
```

Stage matrix:

```text
D0 static/runtime inventory:             PASS
D1 plain Torch CUDA allocation/kernel:   PASS
D2 plain Torch CUDA matmul:              PASS
D2 plain Torch CUDA nn.Linear:           PASS
D3 AppLauncher only + tiny matmul:        FAIL
D3 tiny nn.Linear:                        NOT REACHED
D4 environment/reset + trivial cuBLAS:    NOT RUN — gated by D3 failure
D5 environment + VCritic synthetic:       NOT RUN — gated by D3 failure
D6 environment + real I1 + VCritic:       NOT RUN — gated by D3 failure
D7 startup-order contrast:                NOT RUN — only allowed if D2-D6 pass
D8 repeatability:                         NOT RUN — only allowed if D1-D7 pass
```

The D3 worker launched `AppLauncher(headless=True)` but did not construct an Isaac environment. Its first tiny `torch.matmul` failed with the same error as the original V2 attempt:

```text
RuntimeError: CUDA error: CUBLAS_STATUS_NOT_INITIALIZED
when calling `cublasCreate(handle)`
```

Therefore the failure does not require the real environment, installed VCritic, or real I1 critic observation to appear. This diagnostic does **not** establish a causal Isaac bug, Torch bug, driver bug, resource-exhaustion cause, or HARL defect. It establishes only that plain Torch cuBLAS works in a fresh process and the same operation first fails after AppLauncher initialization in a separate fresh process.

## 2. Starting checkpoint and frozen state

```text
branch: main
HEAD:   14993dee344bade0230d2eb97b5f22171331f44a

B2-D:                              REVIEW PASS / FROZEN
B2-I0 through B2-I6:              REVIEW PASS / CLOSED
B2-V1:                            GPT REVIEW PASS / CLOSED
B2-V2:                            STOPPED / INCOMPLETE
public learned-policy event step: DORMANT / BLOCKED
runtime/policy/learner readiness: BLOCKED
training:                          NOT AUTHORIZED
commit:                            NONE
```

The authoritative B2-V2 STOP report and `TASK_PROGRESS.md` were read first. Current evidence continues not to establish an I0-I6 semantic defect, and no frozen contract was reopened.

## 3. Diagnostic scope and files

Added test-only supervisor/worker:

- `scripts/environments/test_assignment_phase_b2_v2_d1_cuda_cublas_context_diagnostic.py`

Documentation:

- this report;
- `AgentRead/TASK_PROGRESS.md`.

```text
production source changes by D1: NONE
DirectMARLEnv changes:            NONE
installed HARL changes:           NONE
environment/wrapper changes:      NONE
system/package/driver changes:     NONE
```

The script is not imported or registered by production and is not a training entrypoint.

## 4. Fresh-process policy and supervisor

Every executed stage used a new child process under the same interpreter. The supervisor:

- launched one worker per stage;
- captured stdout/stderr, structured evidence, exceptions, and process exit;
- imposed a 180-second timeout on each stage;
- stopped the decision tree at the first failing boundary;
- compared 26 protected files before and after;
- verified every worker was no longer alive and no timeout occurred.

Executed fresh processes: `4` (`D0`, `D1`, `D2`, `D3`).

The first authoring run exposed a test-harness persistence-order issue: D3 closed SimulationApp before writing its structured stage result, producing an inconclusive `MissingResult` despite child exit 0. That outcome was not accepted as CUDA evidence. Only the diagnostic script was changed so a stage result is persisted before `SimulationApp.close()`, following the already-established real-Isaac safe reporting pattern. The complete decision tree was then run again; the formal results in this report are from that corrected run.

## 5. D0 inventory

```text
Python executable:      C:\isaacenvs\isaac45_harl\python.exe
Python:                 3.10.20
Torch:                  2.5.1+cu121
torch.version.cuda:     12.1
torch CUDA available:   true
torch CUDA devices:     1
current CUDA device:    0
GPU 0:                  NVIDIA GeForce RTX 4060 Ti
Isaac Sim:              4.5.0.0
Isaac Lab:              0.36.23
isaaclab-tasks:         0.10.31
HARL:                   1.0.0
HARL source:            C:\isaacenvs\isaac45_harl\Lib\site-packages\harl\__init__.py
VCritic source:         C:\isaacenvs\isaac45_harl\Lib\site-packages\harl\algorithms\critics\v_critic.py
CUDA-related env vars:  none present
```

D0 executed no cuBLAS operation.

Read-only `nvidia-smi` near D0:

```text
GPU:          NVIDIA GeForce RTX 4060 Ti
driver:       537.58
memory total: 8188 MiB
memory used:  727 MiB
memory free:  7235 MiB
utilization:  4%
```

The inventory is observational. In particular, the Torch CUDA build version and the displayed driver do not by themselves identify causation.

## 6. D1 plain Torch basic CUDA

Fresh process; no AppLauncher or Isaac import was used for the operation.

```python
x = torch.ones((8, 8), dtype=torch.float32, device="cuda:0")
y = x + 1.0
torch.cuda.synchronize()
```

Result:

```text
allocation:       PASS
basic CUDA kernel: PASS
device:           cuda:0
dtype:            float32
finite:           true
sum:              128.0
synchronize:      PASS
memory allocated: 1,024 bytes
memory reserved:  2,097,152 bytes
```

Conclusion: `CUDA_BASE_CONTEXT_GAP` is not the first observed boundary.

## 7. D2 plain Torch cuBLAS baseline

Fresh process; no AppLauncher or environment.

Fixed seed: `260826`.

### D2a matmul

```text
torch.matmul [8,8] x [8,8]: PASS
device:                         cuda:0
finite:                         true
sum:                            16128.0
synchronize:                    PASS
```

### D2b nn.Linear

```text
torch.nn.Linear(8,8), input [2,8]: PASS
output shape:                       [2,8]
device:                             cuda:0
finite:                             true
synchronize:                        PASS
```

After the two D2 operations:

```text
torch memory allocated: 8,523,264 bytes
torch memory reserved:  23,068,672 bytes
nvidia-smi memory used:  894 MiB
nvidia-smi memory free:  7068 MiB
```

Conclusion: `PLAIN_TORCH_CUBLAS_GAP` is not the first observed boundary.

## 8. D3 AppLauncher-only cuBLAS

Fresh process sequence:

```text
AppLauncher(headless=True)
-> no environment construction
-> create small float32 CUDA matrices
-> first torch.matmul
-> intended tiny nn.Linear
-> safe SimulationApp shutdown
```

The first `torch.matmul` raised:

```text
exception type: RuntimeError
exception message:
  CUDA error: CUBLAS_STATUS_NOT_INITIALIZED
  when calling `cublasCreate(handle)`

relevant frames:
  run_app_stage
    result = {"app_launcher": "PASS", "cublas": tiny_cublas(torch)}
  tiny_cublas
    product = torch.matmul(a, b)
```

This is an exact/near-exact match to the original V2 failure text. D3 `nn.Linear` was not attempted after the failed matmul in the same process.

Memory observations:

```text
nvidia-smi immediately before D3 worker: 727 MiB used / 7235 MiB free
nvidia-smi after failure, before exit:   2044 MiB used / 5918 MiB free
nvidia-smi after worker shutdown:         778 MiB used / 7184 MiB free
```

These values show cleanup after exit but do not prove or exclude a resource cause. No CUDA-related environment variable was set or changed.

## 9. First-boundary decision

Evidence-supported classification:

```text
D2 plain Torch cuBLAS: PASS
D3 AppLauncher + same tiny cuBLAS class: FAIL

first failing boundary:
  APP_LAUNCHER_CUDA_CONTEXT_INTERACTION
```

Precise meaning:

> In this local environment, the first tested layer at which cuBLAS stopped working was after headless AppLauncher initialization and before any environment construction.

This is a boundary label, not a causal diagnosis. No claim is made that AppLauncher source is defective.

Original error reproduced: `YES`.

Determinism:

```text
same error observed in original V2: YES
same error reproduced in formal D3: YES
dedicated D3 repeatability campaign: NOT RUN
deterministic frequency established: NO
```

D8 repeatability was not eligible because the decision tree requires D1-D7 all PASS. The preliminary authoring run's missing result is not counted as a repeat.

## 10. Gated stages not executed

Because D3 failed:

- D4 did not construct/reset a real environment;
- D5 did not construct installed VCritic;
- D6 did not capture or evaluate real I1 critic evidence;
- D7 did not compare CUDA-first-use ordering;
- D8 did not repeat the reproducer;
- no actor component or actor forward was used;
- no environment physical step occurred.

The original B2-V2 smoke was not rerun.

## 11. Safety, hashes, and non-mutation

```text
fresh workers:                    4
worker timeouts:                  0
workers alive after wait:         0
safe process shutdown:            PASS
D3 SimulationApp shutdown:        PASS
environment constructed:          NO
environment steps:                0
optimizer calls:                  0
backward calls:                   0
training/playback/evaluation:     NOT RUN
checkpoint operations:            NONE
public route activation:          NONE
```

Protected hash result:

```text
I0-I6/runtime/lifecycle/env/wrapper/training: unchanged
DirectMARLEnv:                              unchanged
installed HARL actor/critic/buffers/runners/ValueNorm: unchanged
total:                                      26/26 unchanged
```

No package, driver, toolkit, PATH, registry, environment-variable, or system setting was changed.

## 12. Verification commands

Syntax and whitespace:

```powershell
D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts\environments\test_assignment_phase_b2_v2_d1_cuda_cublas_context_diagnostic.py
git diff --check -- scripts\environments\test_assignment_phase_b2_v2_d1_cuda_cublas_context_diagnostic.py
```

Result: PASS before and after the harness-only reporting correction.

Formal diagnostic:

```powershell
D:\miniconda3\Scripts\conda.exe run --no-capture-output -p C:\isaacenvs\isaac45_harl python scripts\environments\test_assignment_phase_b2_v2_d1_cuda_cublas_context_diagnostic.py --timeout-seconds 180 --json --output C:\Users\33506\AppData\Local\Temp\b2_v2_d1_20260826_final.json
```

Result: diagnostic complete, supervisor exit 0, first failure D3, all workers stopped without timeout, protected hashes unchanged.

Final repository check:

```powershell
git diff --check
```

Result: PASS; existing line-ending warnings only.

## 13. Recommended next decision

Do not repair or retry B2-V2 from this result alone. The next separately reviewed diagnostic decision should focus below the MRTA/HARL layer on the AppLauncher/Torch CUDA first-use boundary. Candidate questions for user/GPT review include:

- whether to authorize a minimal startup-order contrast that is allowed even though D3 fails (plain Torch cuBLAS warmup before AppLauncher versus no warmup);
- whether local Isaac Sim 4.5 / Torch CUDA 12.1 / NVIDIA driver 537.58 compatibility should be checked against authoritative compatibility documentation;
- whether to authorize a repeatability-only D3 reproducer.

Any warmup would be diagnostic contrast only, not a production fix. No driver, Torch, Isaac, CUDA, HARL, production, or environment mutation should occur without separate authorization.

Do not enter B2-R and do not mark B2-V2 complete.

## 14. Final classification

```text
classification:
  PHASE-B2-V2-D1-CUDA-CUBLAS-CONTEXT-DIAGNOSTIC-COMPLETE-AWAITING-GPT-REVIEW

diagnostic:
  COMPLETE

first failing boundary:
  APP_LAUNCHER_CUDA_CONTEXT_INTERACTION

original error reproduced:
  YES

dedicated repeatability/determinism:
  NOT ESTABLISHED

B2-V2:
  STOPPED / INCOMPLETE

production changes:
  NONE

installed HARL changes:
  NONE

optimizer/backward:
  0 / 0

training/playback/evaluation:
  NOT RUN

runtime/policy/learner readiness:
  BLOCKED

B2-R:
  NOT AUTHORIZED

commit:
  NONE
```

Stop here pending GPT independent review.
