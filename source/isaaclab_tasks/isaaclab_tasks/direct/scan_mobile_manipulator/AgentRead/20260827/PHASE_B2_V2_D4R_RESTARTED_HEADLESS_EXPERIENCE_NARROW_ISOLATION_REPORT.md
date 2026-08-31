# Phase B2-V2-D4-R Restarted Headless Experience Narrow Isolation Report

Date: 2026-08-27

Classification:

```text
PHASE-B2-V2-D4R-STOP-SHUTDOWN-LIFECYCLE-VIOLATION
```

## 1. Outcome

D4-R restarted the direct `SimulationApp` controls from fresh B0 repeat 1 and used the reviewed D4-O shutdown classifier. The two required controls were stable:

```text
B0 direct minimal/default-base-python: CUDA_PASS 3/3
B1 exact isaaclab.python.headless.kit:  exact CUBLAS_FAIL 3/3
B0+B1 shutdown:                       EXTERNAL_CLEAN_TERMINATION 6/6
```

R1, R2, and R3 each retained the exact cuBLAS failure in two fresh processes with valid runtime oracles and safe external termination. They are therefore not necessary individually in the tested failing composition.

R8 repeat 1 failed during experience startup before the constructor returned. O4 was persisted, but O5 was not reached and the process exited with code 55. The frozen classifier therefore returned `UNSAFE_OR_INCONCLUSIVE_TERMINATION`; the mandatory STOP fired immediately. R8 repeat 2 and R5/R6/R7/R4 were not run.

No smaller CUDA boundary was established. The narrowest valid boundary remains the frozen D3 result:

```text
APPLAUNCHER_EXPERIENCE_SUFFICIENT_BOUNDARY
```

This is not a causal-root finding and is not a repair decision.

## 2. Starting checkpoint and frozen evidence

```text
starting HEAD: 14993dee344bade0230d2eb97b5f22171331f44a

D1: APP_LAUNCHER_CUDA_CONTEXT_INTERACTION
D2: APPLAUNCHER_TORCH_CUDA_FIRST_USE_ORDER_SENSITIVE_BEHAVIOR
D3 core: APPLAUNCHER_EXPERIENCE_SUFFICIENT_BOUNDARY
D3 overall: STOPPED / INCOMPLETE; historical G4 remains timeout/inconclusive
old D4: STOPPED / INCOMPLETE under the old S15-only contract
D4-O: GPT REVIEW PASS / CLOSED; shutdown classifier frozen
```

Old D4 B0 was not reused. D3 G1-G3 were not rerun, and D3 G4 was neither rerun nor reinterpreted.

## 3. Scope and files

Added test-only diagnostic:

- `scripts/environments/test_assignment_phase_b2_v2_d4r_headless_experience_narrow_isolation.py`

Documentation:

- this report;
- `AgentRead/TASK_PROGRESS.md` updated.

Production MRTA source, AppLauncher, SimulationApp source, official `.kit` files, DirectMARLEnv, installed HARL, and I0-I6 source were not edited by D4-R. No warm-up was deployed.

The diagnostic did not construct an MRTA environment and did not invoke reset, step, HARL, I0-I6, optimizer, backward, training, playback, evaluation, checkpoint, B2-R, or the original B2-V2 harness.

## 4. Diagnostic harness and fresh-process policy

Interpreter:

```text
C:\isaacenvs\isaac45_harl\python.exe
```

Every runtime observation used a separate worker process with a 180-second supervisor timeout. Before each `SimulationApp` constructor there was no explicit Torch CUDA allocation, CUDA initialization, matmul, or Linear call. All workers used the same bounded CUDA probe:

```text
device: cuda:0
dtype: float32
matrix: 8x8
seed: 260826
allocation -> x+1 -> synchronize -> matmul -> synchronize
           -> Linear(8,8) -> forward -> synchronize
```

Observed runtime versions in the CUDA artifacts were Torch `2.5.1+cu121` and Torch CUDA `12.1`. `nvidia-smi` identified an NVIDIA GeForce RTX 4060 Ti with driver 537.58.

The D4-R script imports the reviewed D4-O test-only classifier and D4's static parser/materializer without modifying either historical harness.

## 5. Static source revalidation

The current sources and inherited experiences retained the frozen hashes:

| Source | SHA-256 |
|---|---|
| `apps/isaaclab.python.headless.kit` | `475bb23c5941fbaaf0186991bf6e5445a267b1e0fd8bbab333cc78dc2e1bc795` |
| `isaacsim.exp.base.python.kit` | `1806f0bff51b49af8754b5d150fe64f5942f9b49a22bcfd67ed5d40b4cfddea9` |
| `isaacsim.exp.base.kit` | `ba9b7e23f5a3bc320ed8d7e3391d2080649b606cff15444b9e751ee16331f9b3` |
| frozen D4 harness | `3847a28e91e0576646514f1efc08fd853360f1b4255f00f38aa27db31762a807` |
| frozen D4-O harness | `1ccc9163725a40b10bcf10e423aa389c3bb024db23093bbb8b88104d01b03ff5` |

Normalized static counts:

```text
dependencies: failing direct 17; passing inherited 114; shared 8; FAIL-only 9
settings:     shared 17; different value 5; FAIL-only 54; PASS-only 71
app.vulkan:   true on both paths
```

All eight group cardinalities matched the source-backed frozen plan: R1 14 settings, R2 19, R3 16, R4 30, R5 6, R6 one dependency, R7 one dependency, and R8 one setting.

## 6. Shutdown classifier parity

Before any Isaac worker, the complete frozen D4-O synthetic oracle passed. The required D4-R parity branches also matched exactly:

```text
in-process return:  IN_PROCESS_CLOSE_RETURN
external clean:     EXTERNAL_CLEAN_TERMINATION
timeout:            UNSAFE_OR_INCONCLUSIVE_TERMINATION
worker survivor:    UNSAFE_OR_INCONCLUSIVE_TERMINATION
child survivor:     UNSAFE_OR_INCONCLUSIVE_TERMINATION
missing O4:         UNSAFE_OR_INCONCLUSIVE_TERMINATION
missing O5:         UNSAFE_OR_INCONCLUSIVE_TERMINATION
corrupt result:     UNSAFE_OR_INCONCLUSIVE_TERMINATION
unexpected exit:    UNSAFE_OR_INCONCLUSIVE_TERMINATION
cleanup failure:    UNSAFE_OR_INCONCLUSIVE_TERMINATION
```

Parity result: PASS.

## 7. Exact semantic group manifest

The source-backed manifest was regenerated before runtime. The actual and planned groups were:

### R1 — remove renderer/headless settings

`app.runLoops.rendering_0.fillResolution`, `exts.omni.kit.window.viewport.blockingGetViewportDrawable`, `renderer.multiGpu.enabled`, `renderer.multiGpu.autoEnable`, `rtx-transient.resourcemanager.enableTextureStreaming`, `app.asyncRendering`, `app.asyncRenderingLowLatency`, `app.hydraEngine.waitIdle`, `omni.replicator.asyncRendering`, `renderer.enabled`, `app.audio.enabled`, `exts.omni.kit.window.extensions.hideNonToggleableExts`, `exts.omni.kit.window.extensions.showFeatureOnly`, `ngx.enabled`.

Materialized variant SHA-256: `bc305b75dcd5657ad368ff92cc43cdf07341f7588053866e34cda3a800dc2e37`.

### R2 — remove physics/runtime settings

`app.settings.fabricDefaultStageFrameHistoryCount`, `persistent.simulation.minFrameRate`, `persistent.simulation.defaultMetersPerUnit`, `persistent.omnigraph.updateToUsd`, `persistent.omnigraph.useSchemaPrims`, `persistent.omnigraph.disablePrimNodes`, `persistent.omnihydra.useSceneGraphInstancing`, `physics.updateToUsd`, `physics.updateParticlesToUsd`, `physics.updateVelocitiesToUsd`, `physics.updateForceSensorsToUsd`, `physics.outputVelocitiesLocalSpace`, `physics.useFastCache`, `physics.visualizationDisplayJoints`, `physics.fabricUpdateTransformations`, `physics.fabricUpdateVelocities`, `physics.fabricUpdateForceSensors`, `physics.fabricUpdateJointStates`, `physics.resourcemonitor.timeBetweenQueries`.

Materialized variant SHA-256: `3c6887f0980a6fa3b61ed747678cbe3d4f3a6f0a9ef499714ad838ac26f32de2`.

### R3 — remove startup/Python settings

`app.versionFile`, `app.folder`, `app.name`, `app.version`, `app.content.emptyStageOnStart`, `app.enableStdoutOutput`, `exts.omni.kit.widget.toolbar.PlayButton.enabled`, `exts.omni.replicator.core.Orchestrator.enabled`, `app.settings.persistent`, `app.settings.dev_build`, `app.python.interceptSysStdOutput`, `app.python.logSysStdOutput`, `isaac.startup.ros_bridge_extension`, `app.extensions.skipPublishVerification`, `app.extensions.registryEnabled`, `crashreporter.data.experience`.

Materialized variant SHA-256: `83581fed2a4f686b7b411898721d57b6eec06e07f067fc18a52b0eeadab772c9`.

### R8 — remove extension-folder setting

`app.exts.folders` only. Its declared headless value contained 12 `${exe-path}`/`${app}` entries; the generated file rewrote `${app}` to the authoritative absolute apps directory so relocating the test-only `.kit` did not silently relocate that token.

Materialized variant SHA-256: `992a40f9be1eb535739186476c6eb163a841e90f9795a087f6a40a24c21b6edc`.

### Defined but not run after the mandatory STOP

- R5 adds `renderer.asyncInit`, `renderer.gpuEnumeration.glInterop.enabled`, `rtx-transient.dlssg.enabled`, `rtx.hydra.mdlMaterialWarmup`, `rtx.post.dlss.execMode`, and `exts.omni.kit.renderer.core.present.enabled`.
- R6 adds dependency `omni.kit.loop-isaac`.
- R7 adds dependency `omni.physx.bundle`.
- R4 removes the 30 source-backed persistent stage/asset settings: `persistent.app.file.recentFiles`, `persistent.app.stage.upAxis`, `persistent.app.stage.movePrimInPlace`, `persistent.app.stage.instanceableOnCreatingReference`, `persistent.app.stage.materialStrength`, `persistent.app.transform.gizmoUseSRT`, `persistent.app.viewport.grid.scale`, `persistent.app.viewport.pickingMode`, `persistent.app.viewport.camMoveVelocity`, `persistent.app.viewport.gizmo.scale`, `persistent.app.viewport.previewOnPeek`, `persistent.app.viewport.snapToSurface`, `persistent.app.viewport.displayOptions`, `persistent.app.window.uiStyle`, `persistent.app.primCreation.DefaultXformOpType`, `persistent.app.primCreation.DefaultXformOpOrder`, `persistent.app.primCreation.typedDefaults.camera.clippingRange`, `persistent.simulation.minFrameRate`, `persistent.simulation.defaultMetersPerUnit`, `persistent.omnigraph.updateToUsd`, `persistent.omnigraph.useSchemaPrims`, `persistent.omnigraph.disablePrimNodes`, `persistent.omni.replicator.captureOnPlay`, `persistent.omnihydra.useSceneGraphInstancing`, `persistent.renderer.startupMessageDisplayed`, `persistent.app.omniverse.content_browser.options_menu.show_details`, `persistent.app.omniverse.filepicker.options_menu.show_details`, `persistent.isaac.asset_root.default`, `persistent.isaac.asset_root.cloud`, and `persistent.isaac.asset_root.nvidia`.

These four unrun variants have no runtime oracle, runtime result, or materialized runtime SHA claim.

## 8. Execution order rationale

The fixed order was R1, R2, R3, R8, R5, R6, R7, R4. Subtractions were prioritized before additions; the renderer, physics, and startup groups preceded extension-folder resolution; small base-side additions preceded the broad 30-key persistent removal. R4 was deliberately last because it was the broadest candidate. This order did not repeat historical G1-G4.

## 9. Runtime matrix

| Case | Fresh runs | Diagnostic | CUDA failure stage | Runtime oracle | Shutdown | O4/O5/O6 | Timeout/kill/main/child survivor | Cleanup |
|---|---:|---|---|---|---|---|---|---|
| B0 direct minimal | 3 | `CUDA_PASS` 3/3 | none | enabled set stable: 300, hash `26c0e00e...b29` | external clean 3/3 | yes/yes/no 3/3 | 0/0/0/0 | 3/3 |
| B1 exact headless | 3 | exact `CUBLAS_FAIL` 3/3 | `matmul_call` | enabled set stable: 67, hash `b398134a...ada` | external clean 3/3 | yes/yes/no 3/3 | 0/0/0/0 | 3/3 |
| R1 remove renderer/headless | 2 | exact `CUBLAS_FAIL` 2/2 | `matmul_call` | valid; targeted resolved settings changed; stable extension hash `dc4073d0...ea3` | external clean 2/2 | yes/yes/no 2/2 | 0/0/0/0 | 2/2 |
| R2 remove physics/runtime | 2 | exact `CUBLAS_FAIL` 2/2 | `matmul_call` | valid; targeted resolved settings changed; stable extension hash `5895010e...11e` | external clean 2/2 | yes/yes/no 2/2 | 0/0/0/0 | 2/2 |
| R3 remove startup/Python | 2 | exact `CUBLAS_FAIL` 2/2 | `matmul_call` | valid; targeted resolved settings changed; stable extension hash `3f6fdcc1...f69` | external clean 2/2 | yes/yes/no 2/2 | 0/0/0/0 | 2/2 |
| R8 remove `app.exts.folders` | 1 | `STARTUP_FAILURE` | CUDA not reached | unavailable; constructor did not return | unsafe/inconclusive 1/1 | yes/no/no | 0/0/0/0 | 1/1 |
| R5/R6/R7/R4 | 0 | NOT RUN | NOT RUN | NOT RUN | NOT RUN | NOT RUN | NOT RUN | NOT RUN |

All B1/R1/R2/R3 failures were the exact original exception after basic CUDA had passed:

```text
RuntimeError: CUDA error: CUBLAS_STATUS_NOT_INITIALIZED
when calling `cublasCreate(handle)`
```

## 10. R8 STOP evidence

R8 did not provide CUDA evidence. The direct constructor did not return, so no enabled-extension or resolved-setting oracle could be captured. The persisted diagnostic domain was `STARTUP_FAILURE`, not `CUDA_PASS` or `CUBLAS_FAIL`.

```text
checkpoints: O0, O1, O3, O4
O2 constructor-returned: absent
O5 before-close:         absent
O6 close-returned:       absent
process exit code:       55
timeout:                 false
supervisor kill:         false
worker alive afterward: false
known child survivors:  0
supervisor cleanup:      PASS
shutdown classifier:     UNSAFE_OR_INCONCLUSIVE_TERMINATION
reasons:                 missing O5; unexpected non-zero exit
```

The captured startup log reports a dependency-solver failure because `isaaclab-4.5.22` was considered untrusted after extension-folder removal. This supports only a startup-resolution failure; it says nothing about cuBLAS behavior for R8.

The same log also shows that Kit's enabled registry automatically downloaded extension archives into the user's Kit extension cache and created links under the installed Isaac Sim extension area before the solver stopped. This was an unintended runtime side effect of the R8 startup path. It was not initiated as a package-management command, was not used as evidence, is outside the 37-file hash set, and was not deleted or repaired because cleanup of shared caches was not authorized. Consequently, the claim here is limited to: protected production/framework source and HARL files were unchanged; global Kit extension-cache/link state is not claimed unchanged.

## 11. Bounded interpretation

Evidence-supported statements:

- the R1 renderer/headless settings group is not necessary in the tested failing composition;
- the R2 physics/runtime settings group is not necessary in the tested failing composition;
- the R3 startup/Python settings group is not necessary in the tested failing composition;
- R8 is invalid as CUDA boundary evidence because it failed startup and violated the safe-shutdown gate;
- no authorized smaller necessary or sufficient CUDA group was isolated before the mandatory STOP.

Not established:

- that any R1/R2/R3 setting is globally unrelated;
- that `app.exts.folders` causes the cuBLAS failure;
- that Isaac, Kit, Torch, the driver, or any extension contains a bug;
- that a warm-up, experience change, extension disablement, or cache change is an acceptable repair;
- that B2-V2, runtime readiness, policy readiness, learner readiness, or training readiness passes.

## 12. Integrity and cleanup

```text
protected hash set:       37 files
protected hashes:         37/37 unchanged
temporary variant paths:  removed
worker timeouts:          0
supervisor kills:         0
surviving main workers:   0
known child survivors:    0
MRTA environments:        0
environment resets/steps: 0/0
HARL calls:               0
I0-I6 calls:              0
optimizer/backward:       0/0
original B2-V2 rerun:     no
pre-App CUDA warm-up:     no
training/playback/eval:   not run
commit:                   none
```

The protected set includes the D4-O harness in addition to D4-O's reviewed 36-file set. It covers production lifecycle/runtime/environment/wrapper/training sources, DirectMARLEnv, installed HARL, AppLauncher, SimulationApp source, official experiences, and historical diagnostic harnesses. It does not cover mutable Kit extension caches, as disclosed above.

All per-worker checkpoint/result directories and generated `.kit` variants were removed by supervisor cleanup. Two top-level JSON evidence outputs remain under `%TEMP%` (`b2_v2_d4r_static_parity_20260827_a.json` and `b2_v2_d4r_formal_result_20260827_a.json`): an exact-path deletion attempt was blocked by the execution policy, and no bypass was attempted. They contain diagnostic evidence only and are not imported or registered anywhere.

## 13. Verification

```text
new D4-R script py_compile:       PASS
static hash/manifest validation:  PASS
shutdown classifier parity:       PASS
formal supervisor:                expected nonzero STOP classification
protected hashes:                 PASS 37/37
temporary variant directory:      removed
git diff --check:                 PASS (existing line-ending warnings only)
```

One attempted PTY launch was rejected by Windows before any Python process existed. The actual formal matrix then ran once under a non-PTY supervisor; this is not an extra runtime repeat.

## 14. Recommended next decision

Stop for GPT/user review. Do not retry R8, do not continue R5/R6/R7/R4, and do not clean or mutate the shared Kit extension cache without explicit authorization. Review should first decide how to handle the R8 startup-resolution/shutdown violation and the observed cache/link side effect. Any further diagnostic or repair slice, B2-V2 retry, B2-R, warm-up deployment, production experience change, or training remains unauthorized.

## 15. Final status

```text
B2-V2-D4-R:       STOPPED / INCOMPLETE — SHUTDOWN LIFECYCLE VIOLATION
B2-V2:            STOPPED / INCOMPLETE
narrowest valid:  APPLAUNCHER_EXPERIENCE_SUFFICIENT_BOUNDARY
repair:            NOT PERFORMED
production source: UNCHANGED
installed HARL:    UNCHANGED
environment/HARL:  NOT RUN / NOT RUN
I0-I6:             NOT RUN
B2-R:              NOT AUTHORIZED
training:          NOT AUTHORIZED
commit:            NONE
```
