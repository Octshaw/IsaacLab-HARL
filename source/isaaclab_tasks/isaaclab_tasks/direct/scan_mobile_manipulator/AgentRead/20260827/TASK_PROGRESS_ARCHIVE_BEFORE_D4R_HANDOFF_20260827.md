# TASK_PROGRESS

Updated: 2026-08-27

Authoritative classification: `PHASE-B2-V2-D4R-STOP-SHUTDOWN-LIFECYCLE-VIOLATION`

## Current status

```text
committed checkpoint HEAD:         14993dee344bade0230d2eb97b5f22171331f44a
Lifecycle Runtime Backbone:        COMMITTED / CLOSED CHECKPOINT
B1W-I4-4 GPT review:               PASS / CLOSED
B2-D design:                       GPT REVIEW PASS / FROZEN
B2-I0:                             GPT REVIEW PASS / CLOSED
B2-I1:                             GPT REVIEW PASS / CLOSED
B2-I2:                             GPT REVIEW PASS / CLOSED
B2-I3a:                            GPT REVIEW PASS / CLOSED
B2-I3b:                            GPT REVIEW PASS / CLOSED
B2-I4:                             GPT REVIEW PASS / CLOSED
B2-I5a:                            GPT REVIEW PASS / CLOSED
B2-I5b:                            GPT REVIEW PASS / CLOSED
B2-I6:                            GPT REVIEW PASS / CLOSED
B2-V1:                            GPT REVIEW PASS / CLOSED
B2-V2:                            STOP — REAL VCritic CUDA FORWARD GAP
B2-V2-D1 diagnostic:              GPT REVIEW PASS / CLOSED
B2-V2-D1 first failing boundary:  APP_LAUNCHER_CUDA_CONTEXT_INTERACTION
B2-V2-D2 diagnostic:              GPT REVIEW PASS / CLOSED
B2-V2-D2 characterization:        APPLAUNCHER_TORCH_CUDA_FIRST_USE_ORDER_SENSITIVE_BEHAVIOR
B2-V2-D3 core matrix:             GPT REVIEW PASS / FROZEN
B2-V2-D3 core boundary:           APPLAUNCHER_EXPERIENCE_SUFFICIENT_BOUNDARY
B2-V2-D3 extension isolation:     STOPPED / INCOMPLETE — G4 WORKER TIMEOUT
B2-V2-D3 overall:                 STOPPED / INCOMPLETE
B2-V2-D4:                         STOPPED — BASELINE SAFE-CLOSE ORACLE NONREPRODUCIBLE
B2-V2-D4 B0 CUDA probe:           PASS 1/1 EXECUTED
B2-V2-D4 lifecycle:               S0-S14 OBSERVED / S15 NOT OBSERVED
B2-V2-D4-O:                       GPT REVIEW PASS / CLOSED
D4-O observed shutdown mode:      EXTERNAL_CLEAN_TERMINATION 8/8
D4-O in-process close return:     0/8
D4-O unsafe classifier:           PASS 12/12
B2-V2-D4-R:                       STOPPED / INCOMPLETE — R8 UNSAFE SHUTDOWN
D4-R B0 direct minimal:           CUDA PASS 3/3 / SAFE 3/3
D4-R B1 exact headless:           EXACT CUBLAS FAIL 3/3 / SAFE 3/3
D4-R R1/R2/R3:                    EXACT CUBLAS FAIL 2/2 EACH / SAFE
D4-R R8 repeat 1:                 STARTUP FAILURE / UNSAFE-INCONCLUSIVE
D4-R R8 repeat 2 + R5-R7/R4:      NOT RUN — MANDATORY STOP
D4-R narrowest valid boundary:    APPLAUNCHER_EXPERIENCE_SUFFICIENT_BOUNDARY
reviewed primitive composition:    IMPLEMENTED / DORMANT
Phase B overall:                   NOT COMPLETE
runtime readiness:                BLOCKED
policy readiness:                 BLOCKED
learner readiness:                BLOCKED
public learned-policy event step: DORMANT / BLOCKED
training:                          NOT AUTHORIZED
commit:                            NONE
```

The latest authorized slice, B2-V2-D4-R, used the reviewed/frozen D4-O classifier and restarted from fresh B0 repeat 1. B0 passed CUDA and safe shutdown `3/3`; B1 reproduced the exact cuBLAS failure and safe shutdown `3/3`. R1, R2, and R3 reproduced the exact failure `2/2` each with valid runtime oracles and safe shutdown, so none of those groups is individually necessary in the tested failing composition. R8 repeat 1 failed during startup, persisted O4 but not O5, and exited 55; the D4-O classifier returned `UNSAFE_OR_INCONCLUSIVE_TERMINATION`, so the mandatory STOP fired. R8 repeat 2 and R5/R6/R7/R4 were not run. No smaller CUDA boundary was isolated; D3's `APPLAUNCHER_EXPERIENCE_SUFFICIENT_BOUNDARY` remains the narrowest valid evidence. B2-V2 remains stopped/incomplete; B2-R, public activation, repair, and training remain unauthorized.

R8's startup log also showed automatic Kit registry downloads into the user extension cache and link creation under the installed Isaac Sim extension area before dependency-solver exit. Protected source/HARL hashes remained unchanged, but global Kit extension-cache/link state is not claimed unchanged. No cleanup or repair of that shared cache is authorized or performed.

## Latest work — B2-V2-D4-R mandatory STOP

```text
classification:
  PHASE-B2-V2-D4R-STOP-SHUTDOWN-LIFECYCLE-VIOLATION

B0 direct minimal/default-base-python:
  CUDA_PASS 3/3
  EXTERNAL_CLEAN_TERMINATION 3/3

B1 exact isaaclab.python.headless.kit:
  exact CUBLAS_FAIL at matmul_call 3/3
  EXTERNAL_CLEAN_TERMINATION 3/3

R1 remove renderer/headless settings:
  exact CUBLAS_FAIL 2/2 / oracle valid / safe 2/2

R2 remove physics/runtime settings:
  exact CUBLAS_FAIL 2/2 / oracle valid / safe 2/2

R3 remove startup/Python settings:
  exact CUBLAS_FAIL 2/2 / oracle valid / safe 2/2

R8 remove app.exts.folders repeat 1:
  STARTUP_FAILURE / constructor not returned / exit 55
  O4 yes / O5 no / O6 no
  UNSAFE_OR_INCONCLUSIVE_TERMINATION

R8 repeat 2 and R5/R6/R7/R4:
  NOT RUN — mandatory STOP
```

The static revalidation matched all frozen hashes, normalized counts, and R1-R8 group cardinalities. D4-O classifier parity passed before Isaac. There were 13 formal fresh workers: 12 safe external terminations and one unsafe/inconclusive R8 startup. Timeouts, supervisor kills, main survivors, and known-child survivors were all zero; cleanup passed for every worker. Protected hashes remained `37/37 unchanged`, and temporary `.kit` variants were removed. MRTA environment/reset/step, HARL, I0-I6, optimizer/backward, original B2-V2, warm-up, training, playback, and evaluation were not run.

## Latest completed work — B2-V2-D4-O shutdown contract

```text
shutdown_result domain:
  IN_PROCESS_CLOSE_RETURN
  EXTERNAL_CLEAN_TERMINATION
  UNSAFE_OR_INCONCLUSIVE_TERMINATION

safe_shutdown:
  IN_PROCESS_CLOSE_RETURN or EXTERNAL_CLEAN_TERMINATION

T0 minimal/no-op:
  NOOP_PASS + EXTERNAL_CLEAN_TERMINATION 3/3

T1 minimal/CUDA:
  CUDA_PASS + EXTERNAL_CLEAN_TERMINATION 3/3

T2 expected diagnostic failure:
  EXPECTED_TEST_FAILURE + EXTERNAL_CLEAN_TERMINATION 2/2

O6 / timeout / kill / main survivor / known-child survivor:
  0 / 0 / 0 / 0 / 0
```

The pure classifier passed 12/12 safe/unsafe cases. O6 remains exact in-process-return evidence but is not a universal clean requirement in the proposed contract. Stdout shutdown text is supporting only. Process-tree evidence covers recursive children known at O5 and honestly does not claim descendants created afterward. Protected hashes remained `36/36 unchanged`; supervisor cleanup passed `8/8`.

## Latest work — B2-V2-D4 baseline STOP

```text
classification:
  PHASE-B2-V2-D4-STOP-BASELINE-NONREPRODUCIBLE

D4-B0 repeat 1 CUDA:
  allocation/basic/matmul/Linear PASS

checkpoints:
  S0-S14 persisted
  S15 SimulationApp_close_returned NOT OBSERVED

process:
  exit code 0 / timeout false / alive after wait false

D4-B0 required baseline:
  NOT ESTABLISHED — repeats 2-3 not run

D4-B1 / narrow variants:
  NOT RUN / 0 of 8 run
```

The normalized static audit completed before runtime: direct dependencies were `17 failing / 114 passing-inherited / 8 shared / 9 FAIL-only`; settings were `17 shared / 5 different-value / 54 FAIL-only / 71 PASS-only`. Both experiences declare `app.vulkan=true`. Eight source-backed semantic groups were defined but not materialized or executed after the B0 STOP. Protected hashes remained `36/36 unchanged`; temporary artifacts were removed. The narrowest valid CUDA boundary remains frozen D3 `APPLAUNCHER_EXPERIENCE_SUFFICIENT_BOUNDARY`.

## Latest work — B2-V2-D3 diagnostic STOP

The formal fresh-process core matrix established:

```text
B0 direct minimal SimulationApp:             PASS 3/3
B1 exact AppLauncher control:                FAIL 3/3
B2 direct + AppLauncher experience only:     FAIL 3/3
B3 direct + AppLauncher config only:         PASS 3/3
B4 direct + experience + config:             FAIL 3/3
```

Every B1/B2/B4 failure reproduced the exact original `CUBLAS_STATUS_NOT_INITIALIZED` at `matmul_call`, after basic CUDA had passed. The narrowest completed evidence is `APPLAUNCHER_EXPERIENCE_SUFFICIENT_BOUNDARY`: the selected experience is sufficient in this direct contrast, but causality and repair are not established.

Runtime extension contrasts against the failing experience showed:

```text
G1 remove five Isaac Lab extensions:  exact failure 2/2
G2 remove omni.physx.fabric:          exact failure 2/2
G3 remove both groups:                exact failure 2/2
G4 add base-Python experience group:  TIMEOUT on first worker
```

G4 produced no structured worker/CUDA result, was terminated after the authorized 180-second timeout, and did not demonstrate safe `SimulationApp` shutdown. The worker was confirmed no longer alive; repeat 2 and any later variants were not run. The temporary experience variants were removed. Protected sources remained `34/34 unchanged`. No MRTA environment, reset/step, HARL, I0-I6 route, optimizer, backward, original V2 retry, training, playback, evaluation, checkpoint, public activation, repair, or warm-up deployment occurred.

## Latest completed work — B2-V2-D2 diagnostic

The formal fresh-process matrix established:

```text
C0 plain Torch matmul/Linear:                     PASS 1/1
C1 exact D1 AppLauncher-first ordering:           FAIL 3/3
C2 strict official-order cleanliness oracle:      FAIL 3/3
C3 Torch preimport, no pre-App CUDA:               FAIL 3/3
C4 pre-App basic CUDA, no pre-App cuBLAS:          PASS 3/3
C5 pre-App cuBLAS:                                 PASS 3/3
C6 direct minimal SimulationApp contrast:          PASS 3/3
```

C1 and C3 failed with the exact original error at `post_app.matmul_call` 3/3 each. The original C2 workers continued past an incomplete preconstruction-only oracle and reached the same error, but their timelines reclassify C2 itself as an official-order cleanliness-oracle failure:

```text
CUDA error: CUBLAS_STATUS_NOT_INITIALIZED
when calling `cublasCreate(handle)`
```

Torch was absent from `sys.modules` before AppLauncher construction but present immediately after startup, before the script's explicit Torch import, in all three C2 timelines. Therefore `OFFICIAL_ORDER_NOT_CLEANLY_REPRODUCED` is the authoritative C2 result. The original operational continuation still showed post-App basic CUDA PASS before matmul failed. Torch preimport alone did not change the result. Pre-App basic CUDA initialization without cuBLAS changed the observed post-App result to matmul/Linear PASS 3/3; pre-App cuBLAS also passed 3/3. These are diagnostic contrasts, not authorized warm-up fixes.

Conditional direct minimal `SimulationApp({"headless": True})` passed 3/3, so that minimal startup is insufficient to reproduce the AppLauncher result. It did not reproduce AppLauncher's custom headless experience/extensions and does not prove a wrapper or Kit bug.

Official compatibility audit found the current 537.58 driver meets the documented Isaac Sim 4.5 Windows GameReady/Studio value, while Torch 2.5.1+cu121 and Python 3.10 match the documented Isaac Lab 2.0/Isaac Sim 4.5 generation. This does not prove exact local binary/runtime compatibility or exclude those layers causally. No safely runnable local Compatibility Checker package was found, so none was installed or executed.

Formal workers totaled 19, followed by one supplemental config-capture C2 probe and one final strict-oracle C2 probe (five total C2 observations, within the authorized ceiling). Timeouts and surviving workers were `0 / 0`; 28 protected production/framework/HARL/V2/D1 files remained unchanged before/after and at the final recheck. No environment, HARL component, optimizer, backward, public route, training, playback, evaluation, checkpoint, or original V2 path ran.

## Latest completed work — B2-V2-D1 diagnostic

The fresh-process decision tree established:

```text
D0 inventory:                           PASS
D1 plain Torch CUDA allocation/kernel: PASS
D2 plain Torch matmul:                  PASS
D2 plain Torch nn.Linear:               PASS
D3 AppLauncher only + tiny matmul:      FAIL — exact original cuBLAS error
D4-D8:                                  NOT RUN — gated after D3 failure
```

Exact D3 failure, before environment construction:

```text
RuntimeError: CUDA error: CUBLAS_STATUS_NOT_INITIALIZED
when calling `cublasCreate(handle)`
```

Evidence-supported boundary: `APP_LAUNCHER_CUDA_CONTEXT_INTERACTION`. This is not a causal claim about Isaac, Torch, the driver, or resources. It proves only that plain Torch cuBLAS works in a fresh process and first fails after AppLauncher initialization in a separate fresh process.

Four formal fresh workers ran (`D0`–`D3`); none timed out or remained alive. D3 closed SimulationApp cleanly. No environment was constructed in the formal boundary stage, no `env.step()` occurred, and no actor, VCritic, optimizer, backward, training, playback, evaluation, or checkpoint path ran. The original V2 was not retried. Protected hashes remained `26/26 unchanged`.

A preliminary authoring run exposed an inconclusive harness persistence-order issue at D3 (`MissingResult` after clean child exit); it was not treated as CUDA evidence. The test-only script was corrected to persist the stage result before SimulationApp shutdown, then the complete decision tree was rerun to produce the formal result above. No production/HARL file changed.

## Latest work — B2-V2 STOP

B2-V2 added one verification-only supervised real-Isaac harness and attempted the exact `E=2/M=3/N=12/T=2/cuda:0` dormant I6 composition.

Completed before the gap:

- real headless AppLauncher and `ScanMobileManipulatorEnv` startup;
- event-profile admission and canonical reset;
- exact current I1/I2 binding to current P2/OPEN;
- actor obs `[2,3,421]`, share obs `[2,3,418]`, available actions `[2,3,13]`, all on `cuda:0`;
- six initial DVM policy rows;
- pre-collection public event `wrapper.step` remained fail-closed and did not advance the environment;
- fresh real installed HAPPO actors, VCritic, ValueNorm, and repo-local event critic buffer constructed;
- clean environment/SimulationApp shutdown;
- `26/26` protected repo/DirectMARLEnv/installed-HARL source hashes unchanged.

First failure:

```text
I6 collect_step current critic V(t)
-> installed VCritic.get_values()
-> installed VNet/MLP/torch.nn.Linear
-> RuntimeError: CUDA error: CUBLAS_STATUS_NOT_INITIALIZED
   when calling cublasCreate(handle)
```

The failure occurred before real HAPPO sampling, any physical step, TIME_LIMIT/autoreset, I4 terminal sidecar transport, I5a buffer insertion, or I5b returns. No fallback, conversion workaround, production/installed-HARL patch, repeated smoke attempt, or later regression campaign was performed. Actor/critic optimizer calls and backward calls remained zero.

B2-V2 changed no production source, DirectMARLEnv, wrapper/training route, or installed HARL file. It does not establish a frozen semantic incompatibility; it establishes an unresolved real CUDA/HARL execution boundary that prevents V2 completion.

## Latest completed work — B2-V1

B2-V1 verified the reviewed, dormant I1–I6 composition without adding production semantics:

```text
V1-A static authority / public-default isolation / scale-device-hash gate
V1-B T=3 lifecycle / DVM / conflict / noop / actor-slot gate
V1-C terminal-history / I4-I5a-I5b / ledger / rollover gate
V1-D pre-step clean failure / post-step poison / readiness attack gate
```

Key outcomes:

- two production-composed scales passed: `E=4,M=3,N=4,T=3` and `E=2,M=2,N=4,T=2`;
- scale A proves NEEDS -> claim -> EXECUTING -> continuation -> completion/release -> later policy/reassignment;
- conflict winner/loser retains original proposals/logprobs while current P2 alone owns the effective result;
- policy noop is sampled again later; forced noop can become a clean future policy row;
- partial-E `NONE/TIME_LIMIT/ALL_TASKS_COMPLETED/NONE`, autoreset, and a second TIME_LIMIT for the same env use exact independent generations/keys;
- TIME_LIMIT uses pre-reset critic evidence A and trace stop; true terminal uses zero bootstrap and trace stop; next actor/critic state uses post-reset B;
- `DVM=true, active=false` retains proposal evidence, is excluded from actor loss, and remains a critic transition;
- actor/critic slots and full canonical `[T,E,1]`, `k=t*E+e` factor align across a complete rollout;
- successful `after_update` clears event fields/keys and supports the next rollout's first step;
- stale P2/OPEN/generation/I2/actor/I4-source failures commit nothing before physical execution;
- next-I1/next-I2/DTO/critic-insert/actor-insert failures poison after physical execution; deliberate critic/actor partial commit cannot continue;
- wrapper, env factory, runner, direct constructor, profile, and import attacks leave public readiness blocked;
- stock full-row actor sampling, stock HAPPO train, stock `compute_returns`, optimizer calls, and hidden fallbacks remain zero;
- 17 reviewed repo sources, DirectMARLEnv, and 7 installed HARL files retained exact hashes.

No production source was changed by B2-V1 and no integration defect required a repair.

## B2-V1 files

Verification:

- `scripts/environments/_assignment_phase_b2_v1_event_route_helpers.py`
- `scripts/environments/test_assignment_phase_b2_v1_a_static_scale_contract_gate_pure.py`
- `scripts/environments/test_assignment_phase_b2_v1_b_multistep_lifecycle_actor_gate_pure.py`
- `scripts/environments/test_assignment_phase_b2_v1_c_terminal_learner_rollover_gate_pure.py`
- `scripts/environments/test_assignment_phase_b2_v1_d_failure_readiness_gate_pure.py`

Documentation:

- `AgentRead/20260826/PHASE_B2_V1_PURE_STATIC_SYNTHETIC_INTEGRATION_VERIFICATION_REPORT.md`
- this file.

All earlier uncommitted B2-D through I6 artifacts remain preserved. B2-V1 did not modify reviewed production, wrapper, training/runner, environment, lifecycle, proposal adapter, DirectMARLEnv, package exports, or installed HARL.

## Active architecture / invariants

- P2 remains the sole current lifecycle/ownership authority.
- Proposal remains distinct from effective assignment; actor action/logprob remains the original proposal.
- M1/B1 remains the only proposal-driven ownership mutation authority; final current P2 -> Ak -> controller only.
- EXECUTING continuation remains persistent P2 ownership, never repeated actor selection or B1.
- I1 owns physical/lifecycle observation evidence; I2 owns legality, DVM, and forced routing.
- DVM is not `active_masks`; forced rows are absent from actor math but remain critic transitions.
- I4 owns pre-reset terminal sidecars, safe historical copy, and runtime ACK lifetime.
- ACK remains independent of learner consumption, critic evaluation, buffer insertion, and training.
- Terminal fields describe transition `t`; returned current state describes `t+1`.
- TIME_LIMIT uses pre-reset bootstrap and stops the trace; true terminals use zero bootstrap and stop the trace.
- I5b remains the event GAE/return/ValueNorm authority; I3b remains the decision-valid HAPPO authority.
- Public/default routes remain isolated and fail closed; installed HARL remains unchanged.
- Fixed M/N remains the only supported cardinality.

## Latest verification

Interpreter:

```text
C:\isaacenvs\isaac45_harl\python.exe
Python 3.10.20
```

- B2-V1-A static/scale: `6/6 PASS` normal and `6/6 PASS` under `-I -B`.
- B2-V1-B lifecycle/actor: `5/5 PASS` normal and `5/5 PASS` under `-I -B`.
- B2-V1-C terminal/learner/rollover: `6/6 PASS` normal and `6/6 PASS` under `-I -B`.
- B2-V1-D failure/readiness: `7/7 PASS` normal and `7/7 PASS` under `-I -B`.
- Dedicated B2-V1 total: `24/24 PASS` in each mode.
- B2-I6 regression: `10/10 PASS` normal and `10/10 PASS` under `-I -B`.
- B2-I4 regression: `6/6 PASS` normal and `6/6 PASS` under `-I -B`.
- B2-I5a regression: `11/11 PASS` normal and `11/11 PASS` under `-I -B`.
- B2-I5b regression: `14/14 PASS` normal and `14/14 PASS` under `-I -B`.
- Phase-A default-off identity: `16/16 PASS` in each mode.
- profile contract: `16/16 PASS` in each mode.
- historical event schema: `9/9 PASS` in each mode.
- profile production wiring: `10/10 PASS` in each mode.
- reviewed repo sources protected: `17/17 unchanged`; DirectMARLEnv unchanged.
- installed HARL sources protected: `7/7 unchanged`.
- V1 helper/four fixtures `py_compile`: PASS.
- `git diff --check`: PASS.

The main synthetic oracle used `E=4`, `M=3`, `N=4`, `T=3`; the cross-scale oracle used `E=2`, `M=2`, `N=4`, `T=2`. Trainers and actor/critic outputs were recorders/fakes with zero optimizer calls; the production I1–I6 primitives were used directly.

No I3b optimizer fixture was rerun. No Isaac runtime, AppLauncher, real environment/HARL rollout, real actor/critic network, actor/critic optimizer, training, playback, evaluation, CUDA, or checkpoint operation was run. One read-only source-path probe failed on missing `omni.kit` before any Isaac runtime/AppLauncher was created; it is not runtime evidence. No commit was created.

B2-V2 additions:

- V2 harness `py_compile`: PASS.
- real AppLauncher/environment reset/current I1/I2: PASS.
- first real VCritic CUDA forward: STOP with `CUBLAS_STATUS_NOT_INITIALIZED`.
- physical steps: `0`; completed six-element route steps: `0`.
- actor sampling / timeout / event returns: NOT REACHED.
- actor optimizer / critic optimizer / backward: `0 / 0 / 0`.
- protected before/after hashes: `26/26 unchanged`.
- supervisor timeout: false; worker process alive after wait: false; safe shutdown observed.
- post-stop `git diff --check`: PASS (line-ending warnings only).
- post-stop `nvidia-smi`: RTX 4060 Ti, driver 537.58, 8188 MiB total, 6062 MiB free after shutdown.

The older V1 paragraph above remains historical V1 evidence; unlike V1, B2-V2 did launch Isaac and construct real installed actor/critic components. No training, playback, evaluation, checkpoint, optimizer, or commit operation occurred.

B2-V2-D1 verification:

- diagnostic script `py_compile`: PASS;
- D0/D1/D2/D3 used four separate formal child processes;
- D1 basic CUDA and D2 matmul/Linear: PASS on `cuda:0`;
- D3 AppLauncher-only first matmul: exact `CUBLAS_STATUS_NOT_INITIALIZED` reproduced;
- D4-D8: correctly skipped after the first failing boundary;
- timeouts / surviving workers: `0 / 0`;
- protected hashes: `26/26 unchanged`;
- optimizer / backward / environment steps: `0 / 0 / 0`;
- final `git diff --check`: PASS (existing line-ending warnings only).

B2-V2-D2 verification:

- exact interpreter and diagnostic script `py_compile`: PASS;
- formal fresh workers: `19`; supplemental config probe: `1`; corrected strict-oracle probe: `1`;
- C0 plain Torch: PASS `1/1`;
- C1 exact D1 and C3 Torch-preimport-only: exact post-App first-matmul failure `3/3` each;
- C2 strict clean-order oracle: `OFFICIAL_ORDER_NOT_CLEANLY_REPRODUCED 3/3`; original continuations passed post-App basic CUDA before each cuBLAS failure;
- C4 pre-App basic CUDA without cuBLAS: post-App matmul/Linear PASS `3/3`;
- C5 pre-App cuBLAS: post-App matmul/Linear PASS `3/3`;
- conditional C6 direct minimal SimulationApp: PASS `3/3`;
- AppLauncher config capture: headless, device/active/physics GPU `true / 0 / 0 / 0`;
- timeouts / surviving workers: `0 / 0`;
- protected hashes: `28/28 unchanged`, including original V2 and D1 harnesses;
- environment construction/steps, HARL, optimizer/backward: `0 / 0`, not executed, `0 / 0`;
- original B2-V2: NOT RERUN;
- driver/Torch/Python official-documentation comparison: current versions not obviously outside cited documented configuration;
- D2 script `py_compile`: PASS;
- final `git diff --check`: PASS (line-ending warnings only).

B2-V2-D3 verification:

- diagnostic script `py_compile`: PASS;
- B0-B4 used independent fresh workers and completed the authorized `3/3` matrix;
- B1/B2/B4 reproduced the exact original cuBLAS error `3/3`; B0/B3 passed `3/3`;
- B1 exact resolved config/experience and runtime enabled-extension sets were captured;
- G1/G2/G3 used temporary test-only experience variants and reproduced the exact failure `2/2` each;
- G4 first worker timed out after 180 seconds with no structured result; safe shutdown was not demonstrated, so the mandatory STOP fired;
- timed-out G4 worker alive after termination: false; G4 repeat 2 and later narrowing: NOT RUN;
- temporary experience variants: REMOVED;
- protected hashes: `34/34 unchanged`;
- MRTA environment/reset/step, HARL, I0-I6, optimizer/backward: NOT RUN / `0 / 0`;
- original B2-V2: NOT RERUN.

B2-V2-D4 verification:

- D4 diagnostic script `py_compile`: PASS;
- normalized static experience diff and eight-group definition: PASS;
- D4-B0 repeat 1 allocation/basic CUDA/matmul/Linear: PASS;
- persisted checkpoints: S0-S14; required S15 after `SimulationApp.close()`: NOT OBSERVED;
- B0 repeat 1 process exit / timeout / survivor: `0 / false / false`;
- required B0 `PASS 3/3 + S0-S15`: NOT ESTABLISHED; repeats 2-3 correctly skipped;
- B1 / narrow variants: NOT RUN / `0/8`;
- protected hashes: `36/36 unchanged`, including D3 and D4 harnesses;
- temporary `.kit` variants materialized/remaining: `0 / 0`;
- MRTA environment/reset/step, HARL, I0-I6, optimizer/backward: NOT RUN / `0 / 0`;
- original B2-V2: NOT RERUN.

B2-V2-D4-O verification:

- D4-O test-only script `py_compile`: PASS;
- pure shutdown classifier: PASS `12/12`;
- T0 minimal/no-op: `NOOP_PASS + EXTERNAL_CLEAN_TERMINATION 3/3`;
- T1 minimal/CUDA: `CUDA_PASS + EXTERNAL_CLEAN_TERMINATION 3/3`;
- T2 expected diagnostic artifact: `EXPECTED_TEST_FAILURE + EXTERNAL_CLEAN_TERMINATION 2/2`;
- O6 / timeout / supervisor kill / main survivor / known-child survivor: `0 / 0 / 0 / 0 / 0`;
- supporting shutdown marker / supervisor cleanup: `8/8 / 8/8`;
- protected hashes: `36/36 unchanged`;
- final `git diff --check`: PASS (existing line-ending warnings only);
- fast-shutdown override / monkeypatch / atexit workaround: NONE / NONE / NONE;
- MRTA environment/reset/step, custom experience, AppLauncher, HARL, I0-I6: NOT RUN;
- optimizer/backward: `0 / 0`;
- old D4 retroactive pass / D3 G4 reinterpretation: NO / NO;
- original B2-V2: NOT RERUN.

## Remaining blockers

- B2-V2 focused real Isaac + HARL interface smoke — STOPPED / incomplete at real VCritic CUDA forward.
- AppLauncher/Torch CUDA first-use ordering interaction — repeatably characterized by D2; causal source and repair not established or authorized.
- AppLauncher custom headless experience is sufficient to reproduce the observed direct-`SimulationApp` failure; the causal extension/settings subset remains unresolved because D3 stopped at the G4 timeout.
- D4 S15 shutdown checkpoint contract is not reproducible with the observed installed `SimulationApp.close()` control flow; a new review is required before redefining external clean-exit versus in-process close-return evidence.
- D4-O shutdown contract is GPT review pass/closed. D4-R stopped on R8's unsafe/inconclusive startup lifecycle before a smaller CUDA group was isolated.
- R8 triggered automatic Kit extension-registry cache downloads/link creation before dependency-solver exit; protected sources are unchanged, but shared cache/link state requires review and must not be cleaned or reused as evidence without authorization.
- B2-R final runtime/training-readiness review — not authorized.
- public learned-policy event step activation.
- runtime, policy, learner, and training readiness.

External path/local/retry producers and all eleven numeric TBDs remain separate dependencies. Transformer/GNN/Set Transformer, recurrent redesign, variable cardinality, arbitrary-cardinality checkpoints, training, playback, and evaluation remain deferred.

## Do not do

- Do not mark B2-V2 PASS, GPT REVIEW PASS, or CLOSED.
- Do not rerun or repair B2-V2 or extend D1/D2/D3/D4/D4-O/D4-R diagnostics without a new explicit user/GPT decision.
- Do not retry R8 repeat 1, run R8 repeat 2, or continue R5/R6/R7/R4 after the mandatory D4-R STOP.
- Do not clean, mutate, or treat the shared Kit extension cache/link state as unchanged without explicit review and authorization.
- Do not add pre-App CUDA/cuBLAS warm-up to V2, production, or framework files from D2 evidence.
- Do not enter B2-R without explicit user authorization after a completed/reviewed V2.
- Do not activate the public learned-policy event route or readiness gate.
- Do not modify frozen I1–I5b, lifecycle/P2/Ak, DirectMARLEnv, or installed HARL semantics.
- Do not run Isaac, AppLauncher, real rollout, optimizer, training, playback, evaluation, checkpoint work, or commit.

## Next step

Wait for GPT independent review of the B2-V2-D4-R shutdown-lifecycle STOP and the disclosed R8 extension-registry cache/link side effect. The review should decide whether any narrowly redesigned startup-resolution diagnostic or cache-integrity action is justified. Do not retry R8, continue R5/R6/R7/R4, clean shared caches, deploy a warm-up, or rerun original B2-V2 without new explicit authorization.

```text
next action: GPT/user review of D4-R mandatory STOP and R8 cache/link side effect
recommended future diagnostic/repair slice: NOT AUTHORIZED
all further diagnostic or repair work: NOT AUTHORIZED
```

## Detailed report

- `AgentRead/20260827/PHASE_B2_V2_D4R_RESTARTED_HEADLESS_EXPERIENCE_NARROW_ISOLATION_REPORT.md`
- `AgentRead/20260827/PHASE_B2_V2_D4O_SIMULATIONAPP_SHUTDOWN_OBSERVABILITY_CONTRACT_REPORT.md`
- `AgentRead/20260827/PHASE_B2_V2_D4_HEADLESS_EXPERIENCE_REMAINING_GROUP_NARROW_ISOLATION_DIAGNOSTIC_REPORT.md`
- `AgentRead/20260826/PHASE_B2_V2_D3_APPLAUNCHER_EXPERIENCE_EXTENSION_CONFIG_BOUNDARY_DIAGNOSTIC_REPORT.md`
- `AgentRead/20260826/PHASE_B2_V2_D2_APPLAUNCHER_TORCH_FIRST_USE_CHARACTERIZATION_REPORT.md`
- `AgentRead/20260826/PHASE_B2_V2_D1_CUDA_CUBLAS_CONTEXT_ISOLATION_DIAGNOSTIC_REPORT.md`
- `AgentRead/20260826/PHASE_B2_V2_FOCUSED_REAL_ISAAC_HARL_INTERFACE_VERIFICATION_REPORT.md`
- `AgentRead/20260826/PHASE_B2_V1_PURE_STATIC_SYNTHETIC_INTEGRATION_VERIFICATION_REPORT.md`
- `AgentRead/20260826/PHASE_B2_I6_DORMANT_LEARNED_POLICY_EVENT_ROUTE_COMPOSITION_IMPLEMENTATION_REPORT.md`
- Earlier authoritative reports remain under their dated `AgentRead/` folders.
