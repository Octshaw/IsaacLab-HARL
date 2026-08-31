# Phase B2-V2 Focused Real Isaac + HARL Interface Verification Report

Date: 2026-08-26

Classification: `PHASE-B2-V2-STOP-REAL-ISAAC-HARL-INTERFACE-GAP`

## 1. Outcome

B2-V2 stopped at the first real installed `VCritic` CUDA forward. The real Isaac environment and authoritative current I1/I2 reset interface were reached successfully, but the first `VCritic.get_values()` call failed inside the installed Torch linear layer with:

```text
RuntimeError: CUDA error: CUBLAS_STATUS_NOT_INITIALIZED
when calling `cublasCreate(handle)`
```

This is a real CUDA/HARL execution gap at the current local environment boundary. It is not evidence of an I1/I2 shape mismatch and it is not yet classified as a production semantic defect. The failure occurred before actor sampling, physical stepping, TIME_LIMIT/autoreset, terminal learner transport, or event return computation; those V2 requirements remain unverified.

Per the V2 verification-first and first-failure rules, no CPU fallback, `.cpu()`, `.cuda()`, `.to(device)`, production patch, installed-HARL patch, DirectMARLEnv patch, repeated smoke attempt, or later assertion campaign was performed.

## 2. Starting state

```text
branch: main
HEAD:   14993dee344bade0230d2eb97b5f22171331f44a

Lifecycle Runtime Backbone:        COMMITTED / CLOSED CHECKPOINT
B2-D:                              GPT REVIEW PASS / FROZEN
B2-I0 through B2-I6:              GPT REVIEW PASS / CLOSED
B2-V1:                            GPT REVIEW PASS / CLOSED
reviewed primitive composition:   IMPLEMENTED / DORMANT
public learned-policy event step: DORMANT / BLOCKED
runtime readiness:                BLOCKED
policy readiness:                 BLOCKED
learner readiness:                BLOCKED
training:                          NOT AUTHORIZED
commit:                            NONE
```

The authoritative B2-V1, I6, I5b, I5a, and I4 reports and `TASK_PROGRESS.md` were read before execution. The earlier B1W-I4-4 real-Isaac harness/report supplied the already-proven real environment construction, event-profile admission, `E=2/M=3/N=12/cuda:0`, supervised worker, and shutdown pattern.

## 3. Authorized and changed files

Added verification-only executable:

- `scripts/environments/test_assignment_phase_b2_v2_real_isaac_harl_interface_smoke.py`

Documentation:

- this report;
- `AgentRead/TASK_PROGRESS.md`.

```text
production source changes by B2-V2: NONE
DirectMARLEnv changes:              NONE
installed HARL changes:             NONE
wrapper/training changes:           NONE
public activation changes:          NONE
```

Existing uncommitted B2-D through B2-V1 artifacts were preserved.

## 4. Harness composition

The bounded worker was designed to compose, without a public route:

```text
real AppLauncher / DirectMARLEnv
  -> real environment-owned lifecycle/runtime domain
  -> reviewed I1 current evidence
  -> reviewed I2 DVM/available actions
  -> real installed per-agent HAPPO actors
  -> reviewed I3a subset collection
  -> reviewed I4-2 facade path
  -> final P2 -> Ak -> assignment_to_env_actions -> controller
  -> real DirectMARLEnv.step/autoreset
  -> reviewed I4 pre-reset terminal sidecar
  -> reviewed I5a timeout critic and event buffer
  -> reviewed I5b event returns
  -> I6 recorder-only trainer seams
```

The actual attempt stopped at the first current `VCritic` forward, before the actor/I4-2/physical part of this chain.

Optimizer `.step()` methods on the fresh actor/critic instances were guarded by harness-local counters. Actor and critic trainers were recorder seams. No optimizer or trainer seam was reached.

## 5. Exact runtime configuration

```text
interpreter:       C:\isaacenvs\isaac45_harl\python.exe
Python:            3.10.20
environment ID:    Isaac-Scan-Mobile-Manipulator-Direct-v0
environment type:  ScanMobileManipulatorEnv
profile:           event_gated_local_mrta
device:            cuda:0
E/M/N/T:           2 / 3 / 12 / 2
fixture horizon:   3 control steps
control step:      0.1 s
episode_length_s:  0.3 s
base seed:         260826
actor seeds:       260836, 260837, 260838
critic seed:       260846
headless:          true
worker timeout:    240 s
```

The three-control-step horizon is test-only. With the current `episode_length_buf >= max_episode_length - 1` implementation it was intended to make transition slot 0 ordinary and slot 1 TIME_LIMIT. It is not one of the eleven MRTA numeric TBDs and did not modify terminal priority.

Post-shutdown `nvidia-smi` evidence:

```text
GPU:          NVIDIA GeForce RTX 4060 Ti
driver:       537.58
memory total: 8188 MiB
memory used:  1900 MiB
memory free:  6062 MiB
utilization:  2%
```

This post-shutdown observation does not establish the exact memory/context state at the failing call.

## 6. Evidence completed before the gap

### R0 — real startup

PASS:

- `AppLauncher(headless=True)` initialized;
- Isaac selected `cuda:0`;
- real `ScanMobileManipulatorEnv` constructed with `E=2`, `M=3`, `N=12`;
- event-profile admission and canonical real reset completed;
- environment reported physics `dt=1/60`, decimation-derived control step `0.1 s`.

### R1 — real reset and current I1/I2

PASS:

```text
wrapper admitted-reset return arity: 3
actor observation:                   [2, 3, 421], float32, cuda:0
runner share observation:            [2, 3, 418], float32, cuda:0
available actions:                   [2, 3, 13], cuda:0
initial DVM policy rows:              6
P2 publication binding:              exact current identity
```

The canonical reset therefore produced real policy-decision rows and satisfied the V2 no-DVM-row stop guard.

### Public fence before collection

PASS:

- normal public event `wrapper.step` raised the expected `not runtime-ready` failure;
- the blocked call did not advance `raw_env.common_step_counter`.

## 7. First failing stage

```text
stage: R2 current real critic V(t)
call:  EventDormantLearnedPolicyRouteV2.collect_step()
       -> CriticRecorder.get_values()
       -> installed VCritic.get_values()
       -> installed VNet / MLP / torch.nn.Linear
error: CUDA error: CUBLAS_STATUS_NOT_INITIALIZED
       when calling cublasCreate(handle)
```

The input had already passed I6's current-slot construction and had the audited critic dimension `418` on `cuda:0`. No value tensor was returned. Consequently this attempt cannot claim real `VCritic` interface PASS.

The worker traceback reported `failure_code: null` because the low-level Torch exception was not converted into a harness assertion code. The exact source stage is unambiguous from the call path above; the top-level classification correctly remained the required V2 STOP classification.

## 8. Required V2 matrix

| Requirement | Result |
|---|---|
| real Isaac/AppLauncher startup | PASS |
| exact `E=2/M=3/N=12/cuda:0` | PASS |
| real reset | PASS |
| production I1/I2 current identity, shapes, device | PASS |
| at least one real DVM row exists | PASS (`6`) |
| real current VCritic finite forward | **STOP / GAP** |
| real HAPPO actor forward/sampling | NOT REACHED |
| masked action/logprob contract | NOT REACHED |
| forced-row bypass in real state | NOT REACHED |
| physical step and final P2 -> Ak -> controller | NOT REACHED |
| six-element step return | NOT REACHED |
| real TIME_LIMIT/autoreset | NOT REACHED |
| pre-reset I4 terminal sidecar | NOT REACHED |
| pre-reset/post-reset fingerprint separation | NOT REACHED |
| runtime exact ACK ordering | NOT REACHED |
| timeout critic exactly once | NOT REACHED |
| event actor/critic slot insertion | NOT REACHED |
| ordinary final next value | NOT REACHED |
| I5b event returns | NOT REACHED |
| stock `compute_returns` exclusion in completed rollout | NOT REACHED |
| actor/critic optimizer calls | `0` before stop |
| backward calls | `0` |
| public readiness remains blocked | PASS at pre-collection check; no activation occurred |
| safe environment/SimulationApp shutdown | PASS |
| protected hashes unchanged | PASS (`26/26`) |

## 9. Shutdown and mutation evidence

The environment close ran from the harness `finally` block. `SimulationApp.close()` then completed, the worker process was no longer alive after supervisor wait, and there was no timeout.

```text
supervisor final exit:     1 (expected for STOP)
worker child exit observed: 0
worker process alive:      false
timeout:                   false
shutdown observed:         true
```

Although the SimulationApp-managed child returned code 0 after emitting the failure artifact, the supervisor honored `status=failed`, returned exit 1, and did not misclassify the attempt as PASS.

Protected before/after SHA-256 comparison covered 26 files:

- all reviewed I0-I6 modules;
- runtime facade and proposal adapter;
- lifecycle transaction and authority;
- real environment, wrapper, and training module;
- `DirectMARLEnv`;
- installed HAPPO and actor base;
- installed VCritic and ValueNorm;
- installed actor/critic buffers;
- installed on-policy base and HA runners.

Result: `26/26 unchanged`.

## 10. Commands and checks

Interpreter and syntax:

```powershell
D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python -c "import sys; print(sys.executable); print(sys.version)"
D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts\environments\test_assignment_phase_b2_v2_real_isaac_harl_interface_smoke.py
```

Result: PASS.

Real bounded smoke:

```powershell
D:\miniconda3\Scripts\conda.exe run --no-capture-output -p C:\isaacenvs\isaac45_harl python scripts\environments\test_assignment_phase_b2_v2_real_isaac_harl_interface_smoke.py --timeout-seconds 240 --json
```

Result: STOP at real VCritic CUDA forward, supervisor exit 1, safe shutdown.

Post-stop read-only checks:

```powershell
nvidia-smi --query-gpu=name,driver_version,memory.total,memory.used,memory.free,utilization.gpu --format=csv,noheader
git status --short
git diff --check
```

Results: GPU visible after shutdown; working tree preserved; `git diff --check` PASS (line-ending warnings only).

No B2-V1 or I4/I5a/I5b/I6 regression was run after the STOP. The authorization explicitly required immediate termination after the first real-smoke failure. I3b optimizer oracle was not run.

## 11. Non-claims and next decision

This result does not prove that the frozen composition is semantically incompatible. It proves that the current real Isaac process could not initialize cuBLAS for the first installed `VCritic` forward, so the mandatory V2 interface matrix could not be completed without a new diagnostic decision.

Do not infer or activate:

```text
B2-V2 PASS / CLOSED
RUNTIME_VERIFIED
POLICY_INTERFACE_READY
LEARNER_INTERFACE_READY
TRAINING_READY
public learned-policy event step
B2-R
```

Any next attempt should be separately authorized and should first isolate whether cuBLAS failure is caused by the local Isaac/Torch CUDA context, driver/runtime compatibility, or process startup/resource interaction. It must not use CPU as V2 evidence and must not patch production, DirectMARLEnv, or installed HARL without an explicitly reviewed upstream slice.

## 12. Final classification

```text
classification:
  PHASE-B2-V2-STOP-REAL-ISAAC-HARL-INTERFACE-GAP

B2-D through B2-I6:
  REVIEW PASS / FROZEN OR CLOSED

B2-V1:
  GPT REVIEW PASS / CLOSED

B2-V2:
  STOPPED AT FIRST REAL VCRITIC CUDA FORWARD

production changes:
  NONE

Isaac:
  STARTUP + RESET + I1/I2 PASS; ROLLOUT NOT COMPLETED

HARL actor:
  CONSTRUCTED; FORWARD NOT REACHED

HARL critic:
  CONSTRUCTED; FIRST CUDA FORWARD FAILED

HARL rollout training:
  NOT RUN

optimizer/backward:
  NOT RUN

training/playback/evaluation:
  NOT RUN

public learned-policy event step:
  DORMANT / BLOCKED

runtime/policy/learner readiness:
  BLOCKED

commit:
  NONE
```

Stop here for GPT/user review. B2-R is not authorized.
