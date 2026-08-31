# Phase B2-V2-D4 Headless Experience Remaining Group Narrow Isolation Diagnostic Report

Date: 2026-08-27

Classification: `PHASE-B2-V2-D4-STOP-BASELINE-NONREPRODUCIBLE`

## 1. Outcome

D4 stopped at the first mandatory gate. One fresh D4-B0 direct-minimal worker completed the entire unified CUDA probe successfully, persisted its result, and began `SimulationApp.close()`. The externally persisted lifecycle ended at S14; Python control did not return to emit S15:

```text
D4-B0 repeat 1:
  constructor:                RETURNED
  enabled extensions:         CAPTURED
  basic CUDA:                 PASS
  torch.matmul:               PASS
  torch.nn.Linear:            PASS
  result persisted:           S13
  close entered:              S14
  close returned:             NOT OBSERVED
  process exit code:          0
  timeout:                    false
  worker alive after wait:    false
  D4 safe-close oracle:       FAIL — S15 absent
```

The authorized B0 baseline required `PASS 3/3`, complete S0-S15, and safe close. Therefore the supervisor correctly classified:

```text
PHASE-B2-V2-D4-STOP-BASELINE-NONREPRODUCIBLE
```

It did not launch B0 repeats 2-3, B1, or any narrow variant. This STOP is a startup-lifecycle observability incompatibility, not a CUDA baseline failure: the single executed CUDA probe passed through Linear.

## 2. Starting checkpoint and frozen inputs

```text
branch:        main
HEAD:          14993dee344bade0230d2eb97b5f22171331f44a
git describe:  v2.0.0-53-g14993dee-dirty

B2-D:          REVIEW PASS / FROZEN
B2-I0-I6:      REVIEW PASS / CLOSED
B2-V1:         GPT REVIEW PASS / CLOSED
B2-V2:         STOPPED / INCOMPLETE
B2-V2-D1:      GPT REVIEW PASS / CLOSED
B2-V2-D2:      GPT REVIEW PASS / CLOSED
B2-V2-D3 core: GPT REVIEW PASS / FROZEN
B2-V2-D3:      STOPPED / INCOMPLETE
B2-R:          NOT AUTHORIZED
training:      NOT AUTHORIZED
commit:        NONE
```

Frozen evidence retained:

```text
D1: APP_LAUNCHER_CUDA_CONTEXT_INTERACTION
D2: APPLAUNCHER_TORCH_CUDA_FIRST_USE_ORDER_SENSITIVE_BEHAVIOR
D3: APPLAUNCHER_EXPERIENCE_SUFFICIENT_BOUNDARY
```

D3 G4 remains historical, inconclusive evidence only: its broad base-Python dependency variant timed out on repeat 1 with no structured CUDA result and no demonstrated safe close. D4 did not rerun G4 or increase its timeout.

## 3. D4 scope and files

Added test-only diagnostic:

- `scripts/environments/test_assignment_phase_b2_v2_d4_headless_experience_remaining_group_narrow_isolation_diagnostic.py`

Documentation:

- this report;
- updated `AgentRead/TASK_PROGRESS.md`.

The D4 script is not registered with or imported by production.

```text
production modifications:        NONE
AppLauncher modifications:       NONE
production .kit modifications:   NONE
installed Isaac Sim changes:     NONE
installed HARL changes:          NONE
Torch/CUDA/driver changes:       NONE
V2/D1/D2/D3 harness changes:     NONE
warm-up deployment:              NONE
```

## 4. Exact runtime inventory

```text
interpreter:          C:\isaacenvs\isaac45_harl\python.exe
Python:               3.10.20
platform:             Windows-10-10.0.26100-SP0
Torch:                2.5.1+cu121
torch CUDA build:     12.1
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

## 5. Startup checkpoint protocol

Every worker was designed to atomically replace an external JSON checkpoint file after each completed stage:

```text
S0  worker_started
S1  imports_complete
S2  experience_variant_ready
S3  immediately_before_SimulationApp_constructor
S4  SimulationApp_constructor_returned
S5  extension_manager_accessible
S6  enabled_extension_summary_captured
S7  immediately_before_torch_cuda_probe
S8  basic_cuda_allocation_complete
S9  basic_cuda_kernel_sync_complete
S10 matmul_complete
S11 matmul_sync_complete
S12 linear_complete
S13 result_persisted
S14 immediately_before_SimulationApp_close
S15 SimulationApp_close_returned
```

Writes use a temporary sibling file, `flush()`, `os.fsync()`, and `os.replace()`. A supervisor timeout can therefore recover the last fully persisted checkpoint rather than infer progress from buffered output.

## 6. D4-B0 baseline evidence

Only repeat 1 was eligible and executed:

```text
completed checkpoints:
  S0,S1,S2,S3,S4,S5,S6,S7,S8,S9,S10,S11,S12,S13,S14

last completed checkpoint:
  S14 immediately_before_SimulationApp_close

S15:
  NOT OBSERVED
```

CUDA evidence before shutdown:

```text
allocation:
  device: cuda:0
  dtype:  torch.float32
  shape:  [8,8]

basic x + 1:
  finite: true
  sum:    128.0

matmul:
  finite: true
  sum:    16128.0

Linear(8,8):
  output shape: [2,8]
  finite:       true
```

Worker lifecycle:

```text
elapsed:                   26.204 seconds
process exit code:         0
timeout:                   false
constructor returned:      true
CUDA probe reached:        true
worker terminated:         true
worker alive after wait:   false
safe close under D4 rule:  false — S15 absent
```

The captured stdout ends with `Simulation App Shutting Down`. The installed source then calls `_app.shutdown()` and `_framework.unload_all_plugins()`. In this observed process, control did not return to the following Python statement that would emit S15. This is an evidence-supported control-flow observation only. It does not prove an Isaac framework defect, unclean GPU release, or system-level resource leak.

Because B0 required all three repeats plus S0-S15, repeats 2-3 were correctly not run.

## 7. D4-B1 failing control

```text
status: NOT RUN — gated by D4-B0 safe-close oracle failure
```

The frozen D3 headless-experience failure remains authoritative; D4 produced no new B1 CUDA evidence.

## 8. Normalized static experience diff

The static audit normalized the standalone failing experience against the effective passing chain:

```text
PASSING:
  isaacsim.exp.base.python.kit
  -> isaacsim.exp.base.kit

FAILING:
  isaaclab.python.headless.kit
```

Counts:

| Category | Count |
|---|---:|
| failing direct dependencies | 17 |
| passing inherited direct dependencies | 114 |
| shared direct dependencies | 8 |
| FAIL-only direct dependencies | 9 |
| shared settings | 17 |
| different-value settings | 5 |
| FAIL-only settings | 54 |
| PASS-only settings | 71 |

### Dependency comparison

Shared direct declarations:

```text
isaacsim.core.api
isaacsim.core.cloner
isaacsim.core.utils
isaacsim.core.version
isaacsim.simulation_app
omni.kit.telemetry
omni.physx.tensors
omni.warp.core
```

FAIL-only direct declarations:

```text
isaaclab
isaaclab_assets
isaaclab_mimic
isaaclab_rl
isaaclab_tasks
omni.kit.loop
omni.physx
omni.physx.fabric
usdrt.scenegraph
```

The five Isaac Lab extensions and `omni.physx.fabric` are already excluded as necessary elements by frozen D3 G1-G3 evidence. Their presence in this normalized list does not reopen them.

PASS-only dependencies are the 106 direct declarations inherited from base/base-Python but absent from the standalone headless file. They form these actual source groups rather than one undifferentiated G4 dependency:

- Isaac Sim app/core/simulation-manager/throttling, GUI, robot, sensor, replicator, storage, and importer extensions;
- deprecated compatibility extensions;
- Kit editor, viewport, window, graph, material, menu, and manipulation extensions;
- renderer/hydra/RTX extensions;
- `omni.kit.loop-isaac`;
- `omni.physx.bundle` and `omni.physx.stageupdate`;
- replicator/synthetic-data/semantics extensions;
- the `isaacsim.exp.base` inheritance declaration itself.

No broad PASS-only dependency group was executed in D4.

### Shared settings

```text
app.asyncRendering
app.asyncRenderingLowLatency
app.settings.fabricDefaultStageFrameHistoryCount
app.version
app.vulkan
exts.omni.kit.registry.nucleus.registries
omni.replicator.asyncRendering
persistent.app.primCreation.DefaultXformOpOrder
persistent.app.primCreation.DefaultXformOpType
persistent.app.primCreation.typedDefaults.camera.clippingRange
persistent.app.stage.upAxis
persistent.app.viewport.camMoveVelocity
persistent.app.viewport.gizmo.scale
persistent.app.viewport.grid.scale
persistent.omni.replicator.captureOnPlay
persistent.renderer.startupMessageDisplayed
persistent.simulation.defaultMetersPerUnit
```

Both paths resolve the declared `app.vulkan` value to `true`; it is shared and was not selected as a discriminator.

### Different-value settings

| Key | Failing | Passing |
|---|---|---|
| `app.content.emptyStageOnStart` | `false` | `true` |
| `app.exts.folders` | repo/Kit/Isaac search set | installed base/base-Python additive search set |
| `app.name` | `Isaac-Sim` | `Isaac-Sim Python` |
| `app.settings.persistent` | `true` | `false` |
| `app.versionFile` | `${exe-path}/VERSION` | `${app}/../VERSION` |

### FAIL-only settings

Normalized keys fall into these exact semantic families:

- renderer/headless: `renderer.enabled`, `renderer.multiGpu.*`, `rtx-transient.resourcemanager.enableTextureStreaming`, render-loop/viewport controls, audio, NGX, extension-window controls;
- physics/runtime: `physics.update*`, `physics.fabricUpdate*`, velocity/cache/joint settings, simulation/omnigraph/omnihydra settings;
- startup/Python: stdout interception/logging, registry flags, toolbar/replicator startup flags, crash reporter and ROS bridge selection;
- persistent stage/UI/assets: stage/reference/material behavior, viewport/UI preferences, and three Isaac asset roots.

The full normalized exact-key count is 54 and is preserved by the D4 script's static result and semantic-group manifest; raw TOML was not duplicated into this report.

### PASS-only settings

Normalized keys form these source-backed families:

- base app shutdown/hang detector/font/window configuration;
- renderer resolution, viewport, UI/menu/material settings;
- `renderer.asyncInit`, `renderer.gpuEnumeration.glInterop.enabled`, RTX/DLSS/MDL startup settings;
- persistent stage/physics/navigation defaults;
- telemetry and platform-filtered ROS settings.

The full normalized exact-key count is 71. No PASS-only settings were applied at runtime because the B0 stop preceded variant materialization.

## 9. Planned semantic groups and bounded matrix

The following eight groups were derived statically, satisfying the authorized maximum. None ran.

| Variant | Exact semantic change | Result |
|---|---|---|
| R1 | remove 14 renderer/headless settings | NOT RUN |
| R2 | remove 19 physics/runtime settings | NOT RUN |
| R3 | remove 16 startup/Python settings | NOT RUN |
| R4 | remove 30 persistent stage/asset settings | NOT RUN |
| R5 | add 6 base renderer-startup settings | NOT RUN |
| R6 | add `omni.kit.loop-isaac` dependency | NOT RUN |
| R7 | add `omni.physx.bundle` dependency | NOT RUN |
| R8 | remove `app.exts.folders` setting | NOT RUN |

R1 exact keys include `renderer.*`, render-loop/viewport flags, `rtx-transient.resourcemanager.enableTextureStreaming`, async/hydra wait, audio, extension-window, and NGX declarations.

R2 exact keys include the 11 `physics.*` update/fabric/cache/visualization keys plus the headless simulation, omnigraph, omnihydra, and frame-history settings.

R3 exact keys include app identity/version/content, stdout/Python, persistence/dev-build, toolbar, replicator-orchestrator, registry, ROS bridge, and crash-reporter settings.

R4 contains every exact `persistent.*` declaration from the failing experience, including stage, viewport, prim-creation, simulation, omnigraph, replicator, renderer, and asset-root keys.

R5 exact additions were:

```text
renderer.asyncInit
renderer.gpuEnumeration.glInterop.enabled
rtx-transient.dlssg.enabled
rtx.hydra.mdlMaterialWarmup
rtx.post.dlss.execMode
exts.omni.kit.renderer.core.present.enabled
```

Runtime extension/settings confirmations were not attempted because no variant worker was launched. No CUDA inference may be drawn for R1-R8.

## 10. Smallest evidence-supported boundary

D4 isolated no smaller extension or settings boundary. Its only runtime result was the B0 shutdown-observability STOP.

Therefore the narrowest valid CUDA reproduction boundary remains the frozen D3 result:

```text
APPLAUNCHER_EXPERIENCE_SUFFICIENT_BOUNDARY
```

This is not `NO_SMALL_GROUP_ISOLATED_WITHIN_AUTHORIZED_BUDGET`; the group budget was not entered.

## 11. Timeout and shutdown accounting

```text
fresh workers launched:         1
worker timeouts:                0
workers alive after supervisor: 0
constructor returned:           1
CUDA probe reached:             1
S14 reached:                    1
S15 reached:                    0

STARTUP_CONSTRUCTOR_TIMEOUT:                  0
POST_STARTUP_EXTENSION_OR_CHECKPOINT_TIMEOUT: 0
CUDA probe timeout:                            0
```

This is not a timeout classification. The process exited normally from the supervisor's perspective, but it did not satisfy the explicitly required in-process S15 return checkpoint.

## 12. Temporary `.kit` lifecycle

The supervisor created a system temporary directory and a settings-spec artifact. It did not materialize a `.kit` variant because B1/variant gates were never reached. The temporary directory was removed.

```text
production registration: NONE
production .kit edits:   NONE
temporary variants left: 0
cleanup oracle:          PASS
```

## 13. Protected hashes

Protection covered D3's 34 files plus the D3 and D4 harnesses, for 36 total protected files. This includes I0-I6/runtime/lifecycle/env/wrapper/training, DirectMARLEnv, installed HARL, V2/D1/D2/D3 harnesses, AppLauncher, the three authoritative experience files, and installed SimulationApp source.

```text
before/after: 36/36 unchanged
```

## 14. Verification and execution accounting

Commands:

```powershell
C:\isaacenvs\isaac45_harl\python.exe -m py_compile \
  scripts\environments\test_assignment_phase_b2_v2_d4_headless_experience_remaining_group_narrow_isolation_diagnostic.py

C:\isaacenvs\isaac45_harl\python.exe -u \
  scripts\environments\test_assignment_phase_b2_v2_d4_headless_experience_remaining_group_narrow_isolation_diagnostic.py \
  --static-only --json-output <temporary-static-result>

C:\isaacenvs\isaac45_harl\python.exe -u \
  scripts\environments\test_assignment_phase_b2_v2_d4_headless_experience_remaining_group_narrow_isolation_diagnostic.py \
  --core-repeats 3 --variant-repeats 2 --timeout-seconds 180 \
  --json-output <temporary-formal-result>
```

The first attempted orchestration command requested a PTY and was rejected by the Windows PowerShell launcher before any Python process was created. It is not a diagnostic observation. The same formal command then ran without a PTY and produced the STOP above.

```text
diagnostic py_compile:       PASS
static normalization:       PASS
formal supervisor:          STOP at first B0 safe-close gate
protected hashes:           36/36 unchanged
temporary cleanup:          PASS
worker timeout/survivor:    0 / 0

MRTA environment:           0
reset/step:                 0 / 0
HARL calls:                 0
I0-I6 calls:                0
optimizer/backward:         0 / 0
training/playback/eval:     NOT RUN
checkpoint operations:      NONE
public route activation:    NONE
original B2-V2:             NOT RERUN
commit:                     NONE
```

## 15. Causal non-claims

This report does not establish:

- that `SimulationApp.close()` is defective;
- that process exit after S14 leaked CUDA, Kit, or GPU resources;
- any smaller settings/extension reproduction boundary;
- whether R1-R8 pass, fail, or time out;
- that the broad historical G4 would behave differently;
- a causal cuBLAS source or production repair;
- any MRTA, I0-I6, HARL, policy, learner, or lifecycle defect;
- B2-V2 or readiness completion.

## 16. Recommended next decision

GPT/user review should decide whether a separately authorized diagnostic may revise the shutdown observability contract. A future design could distinguish:

```text
in-process close-return evidence:
  S15 after SimulationApp.close()

external clean-termination evidence:
  S14 persisted
  "Simulation App Shutting Down" observed
  process exits without timeout
  process tree absent
```

That is a new diagnostic-contract decision. D4 did not relax S15, patch SimulationApp, wrap shutdown, or rerun the baseline. No further D4 or B2-V2 action is authorized.

## 17. Final classification

```text
classification:
  PHASE-B2-V2-D4-STOP-BASELINE-NONREPRODUCIBLE

D4-B0 CUDA probe:
  PASS 1/1 EXECUTED

D4-B0 required baseline:
  NOT ESTABLISHED — required 3/3 and S0-S15

startup checkpoint observability:
  S0-S14 OBSERVED
  S15 NOT OBSERVED

D4-B1:
  NOT RUN

narrow variants:
  0/8 RUN

narrowest CUDA boundary:
  APPLAUNCHER_EXPERIENCE_SUFFICIENT_BOUNDARY (D3 frozen, unchanged)

causal root cause:
  NOT ESTABLISHED / NOT OVERCLAIMED

repair / warm-up:
  NOT PERFORMED / NOT DEPLOYED

production/framework/HARL:
  UNCHANGED

environment / HARL / I0-I6:
  0 / 0 / 0

optimizer/backward:
  0 / 0

original B2-V2:
  NOT RERUN / STOPPED / INCOMPLETE

B2-R:
  NOT AUTHORIZED

runtime/policy/learner readiness:
  BLOCKED

training:
  NOT AUTHORIZED

commit:
  NONE
```

Stop here for GPT/user review.
