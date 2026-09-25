# Phase B2-V2-PD1 — Production-Startup-Path Validation Design

Date: 2026-08-27
Starting committed HEAD: `14993dee344bade0230d2eb97b5f22171331f44a`

```text
classification:
  PHASE-B2-V2-PD1-FINAL-CONSISTENCY-REVISION-COMPLETE-AWAITING-GPT-REVIEW

B2-V2-PD1:
  FINAL CONSISTENCY REVISION COMPLETE / AWAITING GPT REVIEW

revision R1 / R2 / R3 / R4:
  CLOSED / CLOSED / CLOSED / CLOSED

final consistency C1 / C2 / C3:
  CLOSED / CLOSED / CLOSED

preferred future mode:
  PD-A / CURRENT-PRODUCTION-RUNTIME-VALIDATION

production startup ordering:
  AUDITED

original V2 divergence:
  AUDITED

existing pre-App CUDA/cuBLAS behavior:
  EXISTING WORKAROUND-BASED PRODUCTION PATH

future PD2:
  S0 / S0R / S1-S6 FROZEN CANDIDATE
  NOT IMPLEMENTED / NOT AUTHORIZED

Isaac / CUDA / MRTA-HARL:
  NOT RUN / NOT RUN / NOT RUN

optimizer / backward:
  0 / 0

original B2-V2:
  NOT RERUN / STOPPED / INCOMPLETE

B2-R / training / commit:
  NOT AUTHORIZED / NOT AUTHORIZED / NONE
```

## 1. Scope and frozen starting state

This is a design-only source audit, now incorporating the accepted PD1 targeted revision R1-R4 and the final consistency cleanup C1-C3. It reconstructs the actual assignment train/play startup prefixes, compares them with the failing original B2-V2 harness, and specifies a future forward-only real-interface validation. It does not repair cuBLAS, continue Kit forensics, or run any runtime component.

The following conclusions remain frozen:

- B2-D is `GPT REVIEW PASS / FROZEN`.
- B2-I0 through B2-I6 and B2-V1 are `GPT REVIEW PASS / CLOSED`.
- B2-V2 is `STOPPED / INCOMPLETE`.
- D1 first isolated `APP_LAUNCHER_CUDA_CONTEXT_INTERACTION`.
- D2 characterized `APPLAUNCHER_TORCH_CUDA_FIRST_USE_ORDER_SENSITIVE_BEHAVIOR`.
- D3 core froze `APPLAUNCHER_EXPERIENCE_SUFFICIENT_BOUNDARY` as the narrowest valid CUDA boundary.
- D4-O is closed; D4-R is stopped/incomplete; D4-CI is `GPT REVIEW PASS / CLOSED`.
- D4-CI froze cache provenance as `PARTIALLY_ATTRIBUTED`, baseline restoration as `NOT_PROVABLY_RESTORABLE`, future contamination as `HIGH`, and pre-R8 equivalence as `NOT_ESTABLISHED`.
- Runtime, policy, learner, and public-route readiness remain blocked. B2-R and training remain unauthorized.

No B2 lifecycle, proposal/effective-assignment, P2, Ak, terminal-history, ACK, learner, or public-readiness contract is reopened here.

## 2. Why Kit forensics stops here

D4-CI found that R8 created 43 paired cache/link artifacts and touched eight pre-existing metadata objects without pre-R8 byte snapshots. The current shared state therefore cannot support an exact pre-R8 restoration or an uncontaminated continuation of extension/settings bisection. Additional current-state R variants would increase ambiguity while moving away from the Lifecycle-aware Dynamic MRTA objective.

PD1 consequently changes the question, not the frozen finding: it asks whether the **currently used assignment production startup ordering** can carry the already-reviewed real interface smoke past the observed CUDA boundary. A future pass would be current-runtime evidence only, never a pre-R8 reproduction or a Kit root-cause result.

## 3. Authoritative inputs and source audit

Reports read:

- `AgentRead/202608/20260827/PHASE_B2_V2_D4CI_KIT_EXTENSION_REGISTRY_CACHE_LINK_INTEGRITY_AUDIT_REPORT.md`
- `AgentRead/202608/20260827/PHASE_B2_V2_D4R_RESTARTED_HEADLESS_EXPERIENCE_NARROW_ISOLATION_REPORT.md`
- `AgentRead/202608/20260826/PHASE_B2_V2_D2_APPLAUNCHER_TORCH_FIRST_USE_CHARACTERIZATION_REPORT.md`
- `AgentRead/202608/20260826/PHASE_B2_V2_FOCUSED_REAL_ISAAC_HARL_INTERFACE_VERIFICATION_REPORT.md`
- `AgentRead/TASK_PROGRESS.md`

Source files audited, with the SHA-256 observed during this design:

| Source | SHA-256 | Audit purpose |
|---|---|---|
| `scripts/reinforcement_learning/harl/train.py` | `393ad9ea29e6fd9919b5dc5441946cce32766c901c87cf2c481348fb91941b53` | Assignment training entrypoint startup and runtime gate |
| `scripts/reinforcement_learning/harl/play_assignment.py` | `df47c4d2186a54f098b2fdf99ec091ce0ccb685e5f3032c929b40945cf41b2ba` | Assignment playback entrypoint startup and actor path |
| `scripts/reinforcement_learning/harl/play.py` | `6918c8c8cc1c608299d2ed989d6a9a6dd4bf21799643010925315d2559f4828d` | Generic playback contrast |
| `scripts/environments/test_assignment_phase_b2_v2_real_isaac_harl_interface_smoke.py` | `12566d07b2c1162fadcbd22ac47a80f72ae2d696c70d7944aad31fe8c31940d7` | Original V2 startup and real-smoke composition |
| `source/isaaclab/isaaclab/app/app_launcher.py` | `6d9caa29f7177103cbdbd217eb18db19ef00cdadc2f1ecc7c79adc9d29da44c1` | AppLauncher config/experience/SimulationApp boundary |
| `assignment_harl_training.py` | `b6f32510ae663b3e443891cdd09219dd9a5c9ceb9de9c720c73192c7488597fd` | Environment, actor, critic, runner construction |
| `assignment_event_learned_route.py` | `b883ee48dfe0a15cc01ddf01b0bd1914a17e0627e6cc145c214f8b369b4d371b` | Dormant I6 critic-first collection and public fence |
| `assignment_event_actor_collection.py` | `3a78cfd4afd94fe30dbc8cf53b0ef3595f881c2a36621a37900ef1b067d7bc45` | DVM-only actor sampling semantics |
| `agents/harl_happo_cfg.yaml` | `e84b2ee54f5ebd6d51fdf1a799a812bca4039b8cbef17b7eba3ef06337da44b5` | Production HAPPO configuration |

Installed HARL sources were read only to establish rollout mode and collection ordering:

- `harl/algorithms/actors/on_policy_base.py:136-138`: `prep_rollout()` calls `actor.eval()`.
- `harl/algorithms/critics/v_critic.py:206-208`: `prep_rollout()` calls `critic.eval()`.
- `harl/runners/on_policy_base_runner.py:334-386`: stock collection samples actors before calling the centralized critic.
- No installed HARL file was modified.

PD1-R additionally read, without import or execution:

- installed `harl/utils/envs_tools.py:242-251` for the production HARL seed API/order;
- `source/isaaclab/isaaclab/envs/direct_marl_env.py:86-90, 449-457` and installed `isaacsim.core.utils.torch.maths.py:103-126` for environment/Replicator/Torch/CUDA/Warp reseeding;
- `apps/isaaclab.python.headless.kit:23-30, 175-191` and project/installed `config/extension.toml` manifests for the S0R critical set;
- the reviewed D4 extension-manager collector at `test_assignment_phase_b2_v2_d4_headless_experience_remaining_group_narrow_isolation_diagnostic.py:589-600` plus installed uses of `get_enabled_extension_id`, `get_extension_path`, and `get_extension_dict` for the read-only S0R API contract.

## 4. Exact `train.py` startup timeline

The labels below preserve the requested audit checkpoints. Where a later-numbered semantic checkpoint occurs first, the ordering column is authoritative.

| Order | Requested checkpoint | Static result and source |
|---:|---|---|
| 0 | T0 process start | Python begins the entrypoint. Runtime details are not statically observable. |
| 1 | T1 imports/preflight | Standard library, repository path setup, scenario/initial-condition helpers, and `AppLauncher` are imported before CLI parsing completes (`train.py:8-128`). Import-time transitive behavior is `RUNTIME-DEPENDENT / NOT STATICALLY PROVEN`. |
| 2 | T2 Torch import | `torch` is imported inside `_warm_start_torch_cuda` at `train.py:137`, after `from isaaclab.app import AppLauncher` has been evaluated but before an `AppLauncher` object is constructed. |
| 3 | T3 CUDA allocation/basic activity | For a CUDA device with `torch.cuda.is_available()`, the helper selects the exact device and allocates `torch.zeros((1, 1), device=device)` (`train.py:131-145`). There is no separate add/basic-kernel probe. |
| 4 | T4 cuBLAS first use | `torch.nn.Linear(1, 1).to(device)` performs one forward on the probe, followed by `torch.cuda.synchronize(device)` (`train.py:145-150`). There is no explicit `torch.matmul`. |
| 5 | T5 AppLauncher construction | `AppLauncher(args_cli)` at `train.py:175`. |
| 6 | T6 SimulationApp startup | Inside AppLauncher, the resolved experience is passed to `SimulationApp` (`app_launcher.py:670-715, 780`). Constructor-internal timing is runtime-dependent. |
| 7 | T7 Isaac/HARL imports | HARL runner registry, Isaac tasks, environment configuration, and assignment runner imports occur only after AppLauncher returns (`train.py:178-195`). |
| 8 | T9 wrapper/profile admission | For an assignment profile, the formal runtime-ready gate executes at `train.py:209-223`, before runner/output/environment/actor/checkpoint work. The event profile is rejected by `assignment_profile_contract.py:1222-1250`. |
| 9 | T8/T10 environment and networks | Only an admitted profile reaches runner construction. The runner repeats the ready barrier before RNG/device/env/actor/critic (`assignment_harl_training.py:487-495`), constructs the environment before actors/critic, then creates distinct actors and one VCritic (`assignment_harl_training.py:564-571, 618-667`). The event profile never reaches these points through the current public train path. |
| 10 | T12 first actor forward | On an admitted stock runner path, installed HARL `collect()` samples actors first (`on_policy_base_runner.py:342-370`). Exact runtime timing is not statically executed in PD1. |
| 11 | T11 first VCritic forward | Stock `collect()` calls `critic.get_values()` after actor sampling (`on_policy_base_runner.py:372-386`). Thus the requested T11/T12 labels are not chronological for stock HARL. |
| 12 | T13 physical step | `runner.run()` is called at `train.py:323`; the stock run loop later calls the environment step. Calling this path would also enter rollout/training orchestration and is prohibited for PD2. |

Additional facts:

- `_warm_start_torch_cuda(args_cli)` is called unconditionally at module scope. Its internal CPU/non-CUDA/unavailable guards are the only gates (`train.py:131-150`).
- It is not gated by `--assignment_rl`, profile selection, the event readiness barrier, or runner construction.
- `--video` can alter the camera flag before startup; a future equivalent smoke must prohibit video and freeze `enable_cameras=False`.

## 5. Exact `play_assignment.py` startup timeline

| Order | Checkpoint | Static result and source |
|---:|---|---|
| 0 | process/imports | `torch` is imported at module line 22, before `AppLauncher` is imported later in the pre-App source sequence. No explicit CUDA operation occurs at the import statement itself; transitive runtime effects remain unproven statically. |
| 1 | CLI/profile preflight | Repository helpers, scenario resolution, parser configuration, and profile preflight run before startup (`play_assignment.py:24-195`). |
| 2 | pre-App CUDA/cuBLAS | `_warm_start_torch_cuda` applies the same device guards, set-device call, `[1,1]` zero allocation, `Linear(1,1)` forward, and one exact-device synchronization (`play_assignment.py:198-214`). No explicit matmul exists. |
| 3 | AppLauncher/SimulationApp | `AppLauncher(args_cli)` is constructed at `play_assignment.py:216`; SimulationApp is reached through AppLauncher. |
| 4 | post-App imports | Installed actor registry, device helper, Isaac task modules, wrapper builder, and profile contract are imported after App startup (`play_assignment.py:219-252`). |
| 5 | profile admission | The event profile is rejected by the post-App pre-model/output/env/actor/checkpoint/playback barrier (`play_assignment.py:608-622`). |
| 6 | environment/wrapper | An admitted existing profile reaches `make_assignment_harl_env` (`play_assignment.py:642-651`), whose production path also performs runtime-ready admission before `gym.make`. The event profile cannot reach it publicly. |
| 7 | actors/checkpoint/mode | Playback constructs installed actors, validates/loads a checkpoint, and calls `prep_rollout()` (`play_assignment.py:374-427`). This path does not construct VCritic. |
| 8 | reset/actor/step | Reset occurs at `play_assignment.py:692-697`; each admitted agent executes deterministic `act` and `evaluate_actions` under inference mode at lines 718-746; `wrapper.step` occurs at line 754. |

`play_assignment.py` is therefore a valid reference for the pre-App startup prefix and real actor playback mode, but not for a real VCritic call or for the dormant event route.

## 6. Generic `play.py` contrast

The generic `play.py` imports Torch and AppLauncher but contains no pre-App CUDA allocation or Linear forward (`play.py:16-65`). It rejects assignment tasks before constructing AppLauncher and is not an assignment production reference. Its later CUDA tensors are post-App and unrelated to the required startup prefix.

## 7. Original B2-V2 startup timeline

| Order | Checkpoint | Static result and source |
|---:|---|---|
| 0 | worker start | The supervisor starts the real-smoke worker. |
| 1 | AppLauncher import/construction | The worker imports AppLauncher and immediately calls `AppLauncher(headless=True)` (`test_assignment_phase_b2_v2_real_isaac_harl_interface_smoke.py:608-618`). |
| 2 | SimulationApp startup | AppLauncher resolves and starts the headless experience. No explicit Torch CUDA/cuBLAS operation has occurred in the worker first. |
| 3 | Torch/HARL/Isaac imports | `run_real_smoke()` imports Torch, installed HAPPO/VCritic, Isaac tasks, and wrapper/route modules only after AppLauncher returns (`...real_isaac_harl_interface_smoke.py:283-300`). |
| 4 | first explicit CUDA activity | Seed/device checks and CUDA tensors occur after App startup (`...smoke.py:302-317`). |
| 5 | environment/wrapper | The canonical `E=2, M=3, N=12, cuda:0` environment, event wrapper, and private runtime facade are constructed/reset (`...smoke.py:322-399, 447-458`). |
| 6 | HARL components | Three installed HAPPO actors and one VCritic are built with test-only `[32,32]` hidden sizes and placed into rollout mode (`...smoke.py:400-414`). |
| 7 | dormant I6 first call | `route.collect_step()` is called (`...smoke.py:470`). I6 invokes current VCritic before DVM actor sampling (`assignment_event_learned_route.py:457-491`). |
| 8 | observed stop | VCritic reached a CUDA Linear and raised `CUBLAS_STATUS_NOT_INITIALIZED` during `cublasCreate(handle)`. Actor and physical step were not reached. |

The exact current critic semantics are:

- I1 produces runner share observation `[E,M,S] = [2,3,418]`.
- I6 copies the EP centralized state `share[:,0]` into the critic buffer (`assignment_event_learned_route.py:424-432`).
- Installed `VCritic.get_values()` therefore receives `[E,S] = [2,418]`, plus its actual `[E,recurrent_n,H]` RNN state and `[E,1]` mask, and must produce finite `[2,1]` values.

## 8. Exact divergence matrix

| Boundary | `train.py` | `play_assignment.py` | original B2-V2 | PD2 requirement |
|---|---|---|---|---|
| Torch import | Inside warm-up after AppLauncher module import | Top-level before AppLauncher module import | After AppLauncher object returns | Select one explicit production oracle; recommended `TRAIN_STARTUP_PREFIX_V1`, and record the play import-timing difference rather than claiming both are identical |
| First explicit CUDA allocation | Before AppLauncher construction, `[1,1]` zeros | Before AppLauncher construction, `[1,1]` zeros | After AppLauncher construction | Exact production ordering required |
| First explicit cuBLAS | Pre-App `Linear(1,1)` forward | Pre-App `Linear(1,1)` forward | Current VCritic Linear after App/env/reset | Exact production ordering required; no added warm-up |
| Explicit matmul | None | None | None before failure | Must remain absent |
| Synchronization | One pre-App exact-device sync | One pre-App exact-device sync | No pre-App sync | Exactly one, matching the selected production helper |
| App config | CLI-derived | CLI-derived | `headless=True` convenience call | Freeze equivalent `headless=True`, `device=cuda:0`, cameras/livestream/XR off, empty experience override |
| Experience | Default headless experience for those flags | Same | Default headless experience | Resolve and record exact `isaaclab.python.headless.kit` path/hash |
| Public event admission | Blocked before runner | Blocked before model/env | Intentionally private test-only admission | Keep public gate closed; startup-prefix equivalence only |
| HARL actor | Production config; stochastic stock collection | Production config/checkpoint; deterministic playback | Installed class, test-only `[32,32]`, stochastic DVM rows | Use installed class/API and exact I3a DVM semantics; list model-config choice explicitly |
| HARL critic | Production runner creates VCritic | Not present | Installed VCritic, test-only `[32,32]` | Use exact I1/I6 `[2,418]` input; no claim that playback itself has a critic |
| Collection order | Stock actors then critic | Actor only | Dormant route critic then actor | Preserve dormant I6 order because it is the blocker under test; do not call stock runner |
| Physical route | Stock runner/environment | Legacy wrapper step | Private dormant I4-2/P2/Ak route | Preserve existing private I6 route and public fence |

The future harness cannot be exactly equivalent to both production entrypoints: their Torch import timing differs, play has no critic, and the event profile is publicly blocked in both. These are declared divergences, not hidden under a broad “production-equivalent” label.

## 9. Existing pre-App CUDA/cuBLAS block audit

The train and assignment-play helpers were introduced together by commit `fada0f67af98e7ce8beebe0322dba23e0e3402fc` on 2026-06-07. Their docstring states that they initialize PyTorch/cuBLAS before Isaac Kit takes over the CUDA context. Operationally they:

1. read the requested device (default `cuda:0`),
2. return for CPU/non-CUDA or unavailable CUDA,
3. set the CUDA device,
4. allocate one default-float32 `[1,1]` zero tensor,
5. construct and move `nn.Linear(1,1)` to that device,
6. execute one forward,
7. synchronize that device once.

They do not set a seed, check finiteness, retry, catch exceptions, run explicit matmul, or vary tensor shape/dtype. The CUDA path executes by default and is not assignment-profile gated.

Behavior classification:

```text
intrinsic AppLauncher/Isaac/HARL requirement:  NOT ESTABLISHED
test-only diagnostic:                         NO
currently executed production behavior:       YES
historical defensive workaround:              YES
authoritative label:
  EXISTING WORKAROUND-BASED PRODUCTION PATH
```

This is not a native root-cause repair. Nevertheless, validating the exact path is legitimate because it is the path the current assignment train/play entrypoints actually run.

## 10. Production-equivalence claim boundary

PD2 must use the following narrow definition:

> `PRODUCTION-STARTUP-PREFIX EQUIVALENCE` means exact equivalence to the selected current assignment entrypoint from process/import ordering through the existing pre-App CUDA/cuBLAS block and AppLauncher/experience/device resolution. It does not mean equivalence to a publicly admitted event-profile train/play rollout.

The recommended oracle is `TRAIN_STARTUP_PREFIX_V1`, because train is the only production path that later constructs both installed actors and VCritic. The oracle must bind:

- source hashes of `train.py`, `play_assignment.py`, AppLauncher, original V2, and the reviewed I0-I6 modules;
- selected Torch import timing;
- exact warm-up statement/operation trace, including shape, dtype default, device, one Linear forward, one synchronization, and absence of extra ops/retry;
- `headless=True`, `device=cuda:0`, `enable_cameras=False`, livestream/XR off, and no video;
- empty experience override resolving to the exact official `isaaclab.python.headless.kit` path and hash;
- AppLauncher constructor entry/return and `torch.cuda.is_initialized()` observations around every boundary;
- unchanged public event-profile readiness rejection.

Static AST/source comparison must prove that the test-only copy of the warm-up has the same operational statements as the selected production helper. Runtime event records must then prove the order. Importing `train.py` merely to call its helper is forbidden because the module has top-level AppLauncher and runner behavior; no shared import-safe helper exists today. PD2 may contain a test-only exact copy, but may not add, change, or factor a production helper without separate review.

## 11. HARL construction scope

“Same HARL construction” is separated from startup equivalence:

- Required: installed HAPPO and VCritic classes, wrapper-derived observation/action spaces, `cuda:0`, `prep_rollout()`, and `torch.inference_mode()`.
- Required: three distinct actors because the production config has `share_param: false`.
- Required: the runner-compatible EP critic input `[2,418]`, not `[2,3,418]` passed directly to VCritic.
- Required: the current runner transformation, which assigns `hidden_sizes_critic` from `model.hidden_sizes` at `assignment_harl_training.py:525-528`; the raw YAML `hidden_sizes_critic: [512,256]` is not what this runner currently uses.
- Recommended for the production-validation claim: resolve the canonical agent config and construct actor/critic with the production runner’s effective `[256,256]` hidden sizes. No checkpoint is loaded.
- Declared divergence from original V2: the old smoke used test-only `[32,32]`. This changes model width while retaining interface dimensions and installed component APIs. PD2 must record it as a deliberate production-construction correction, not conceal it as a pure one-variable replay.

GPT review accepted the production-effective `[256,256]` construction. PD2 must not add a strict `[32,32]` causal-control sub-slice.

## 12. PD-A versus PD-B

| Option | Evidence target | Strength | Limitation |
|---|---|---|---|
| PD-A — current post-R8 environment | `CURRENT-PRODUCTION-RUNTIME-VALIDATION` | Tests the machine/environment the user would actually run now; keeps research focus on MRTA interfaces | Cannot establish pre-R8 equivalence; postrun structural or ambiguous change invalidates closure, while proven metadata-only refresh is disclosed separately |
| PD-B — clean cloned diagnostic environment | `CLEAN-CLONE-PRODUCTION-ORDER-VALIDATION` | Cleaner forensic baseline | Requires separately authorized environment/deployment work, costs time/storage, and may diverge from the current machine |

Preferred future mode: **PD-A**.

Rationale: the desired decision is whether the current assignment production startup path can execute the blocked MRTA/HARL interface, not which Kit extension caused the original failure. PD-A answers that question directly and does not pretend to reconstruct pre-R8 state.

PD-A authorization must explicitly accept the bounded risk that one App startup can touch shared metadata. The revised guard is not one-bit equality: an exact prelaunch baseline gate runs before Isaac, while a supervisor-only postrun integrity gate classifies raw deltas as no change, metadata-only refresh, structural resolution mutation, or ambiguous delta. The **Shared-State Guard Contract** and **Runtime Extension-Resolution Identity Oracle** are authoritative. If the reviewer does not accept that risk, PD-B needs its own design/authorization instead of silently changing PD2.

## 13. Future PD2 harness architecture

Proposed test-only file (not created in PD1):

`scripts/environments/test_assignment_phase_b2_v2_pd2_production_startup_path_real_interface_smoke.py`

Architecture:

- one external supervisor;
- one fresh worker process using `C:\isaacenvs\isaac45_harl\python.exe`;
- a supervisor-side exact prelaunch baseline gate that can stop before worker/App startup;
- a single AppLauncher/SimulationApp lifetime;
- durable stage checkpoints and bounded stdout/stderr/result capture;
- one post-App, pre-environment S0R runtime extension-resolution identity gate;
- stage observers around the existing dormant I6 `collect_step`, not duplicate calls that would mutate lifecycle state;
- `env.close()` then `SimulationApp.close()` in `finally`;
- D4-O’s reviewed O0-O6 shutdown evidence domain and external supervisor classification;
- a supervisor-only `POSTRUN-INTEGRITY-GATE` after confirmed worker death;
- no import/registration into production packages.

One process is preferred because repeated App startups would introduce extra current-state changes and would cease to represent one production launch. S2-S4 must therefore be observers within one first `collect_step`, and S5-S6 within the second bounded transition.

## 14. Future PD2 stage plan

### PD2-S0 — startup-order equivalence oracle

Inputs:

- frozen source hashes and D4-CI current-state fingerprint;
- `TRAIN_STARTUP_PREFIX_V1` source/AST oracle;
- exact interpreter, headless/device/camera/livestream/XR/experience arguments.

Runtime checkpoints:

1. process start and imports;
2. AppLauncher module import completed, but no object constructed;
3. explicit Torch import timing;
4. before/after CUDA availability check;
5. before/after set-device, `[1,1]` zeros, Linear move/forward, and synchronize;
6. AppLauncher constructor entry/return;
7. resolved experience path/hash and device/config;
8. CUDA-initialized state at each checkpoint.

Output: one exact ordered event ledger. Any missing/extra CUDA operation, retry, wrong shape/dtype/device/sync count, wrong experience, or source hash mismatch stops before environment construction with `PD2-STOP-STARTUP-EQUIVALENCE-MISMATCH`.

### PD2-S0R — runtime extension-resolution identity oracle

Only after AppLauncher returns and S0 passes, but before environment construction, capture the actual enabled-extension identity through Kit's extension manager. The complete enabled extension set is a **within-worker stability audit only**: capture sorted enabled IDs, count, and canonical SHA-256 twice consecutively with no intervening update or extension operation, then require snapshot A == snapshot B. There is no pre-existing golden count/hash and no comparison with a pre-R8 or reviewed expected complete-set value. Separately, the critical extension subset is an **exact identity gate**: require each critical extension's enabled ID/state, version, resolved path, manifest path/hash, authority category, and link target to match the **Critical Extension Identity Manifest**.

S0R is read-only. It must not enable, disable, relink, install, or resolve an additional extension. Missing or unexpected critical identity stops before S1 as `PD2-STOP-RUNTIME-EXTENSION-IDENTITY-MISMATCH`.

### PD2-S1 — real AppLauncher/environment reset and I1/I2

Only after S0 and S0R pass:

- resolve the canonical seed from the existing train/config path, apply the production HARL seed sequence at its production-equivalent post-App point, and log the exact order/value;
- construct `Isaac-Scan-Mobile-Manipulator-Direct-v0` with `E=2, M=3, N=12, T=2, cuda:0` and the same canonical fixture used by original V2;
- retain `ScanMobileManipulatorEnvCfg.seed` so DirectMARLEnv performs the production environment/Replicator/Warp reseed during construction; require it to equal the resolved canonical HARL seed for this smoke;
- construct distinct installed HAPPO actors in agent order 0, 1, 2, then the installed VCritic and ValueNorm when required, with production-effective `[256,256]`, `share_param=false`, and no checkpoint;
- retain all naturally constructor-created optimizer objects, install the no-update guards, and call the required actor/critic `prep_rollout()` methods;
- capture `SNAPSHOT A` after all protected components and optimizers exist and after `prep_rollout()`, but before any actor or critic forward;
- use the existing private event-profile admission/facade; assert the public route still rejects the event profile;
- reset once without injecting a new reset seed, matching the selected production training warmup path;
- verify exact I1 actor observation `[2,3,421]`, runner share observation `[2,3,418]`, available-actions `[2,3,13]`, dtype/device/finiteness, P2/window/generation identity, I2 row plan, and six decision-valid rows expected by the fixture.

This is a private dormant-route test divergence from public production admission. It does not activate or imply public readiness.

### PD2-S2 — real current VCritic gate

Only after S1 passes:

- use the already-constructed and prepared installed VCritic from S1; S2 performs no construction, seed call, reset, actor call, or physical step;
- enter `torch.inference_mode()`;
- through the existing I6 preparation path, call `get_values` once with exact `[2,418]` current critic observation, real RNN state, and masks;
- require `cuda:0`, float32, finite input/output, output `[2,1]`, and no exception.

The observer must classify the same/near-exact `CUBLAS_STATUS_NOT_INITIALIZED` separately and stop immediately as `PD2-STOP-VCritic-CUDA-FAIL`. Actor and physical step remain unexecuted on this branch.

### PD2-S3 — real actor gate

Only if the same first `collect_step` passes S2:

- call the three installed HAPPO actors only for I2 decision-valid DVM rows;
- preserve I3a `deterministic=False`, available-action subsets, original proposal IDs, original logprobs, and proposal-source identity;
- require forced-continuation/noop/terminal rows to bypass actor sampling and PPO participation;
- validate fixed `[E,M]` storage reconstruction without converting forced rows into synthetic policy samples.

Failure stops before I4-2/physical execution as `PD2-STOP-ACTOR-FORWARD-FAIL`.

### PD2-S4 — one real physical event-route step

Only if S3 passes, allow the same `collect_step` call to continue through:

```text
original actor proposal/logprob
-> I4-2 proposal adapter
-> resolver/arbitration candidate
-> zero-or-one M1/B1 transaction
-> authoritative current P2
-> Ak
-> controller
-> one physical environment step
```

Require the HARL six-tuple, a nonterminal first transition, unchanged P2/Ak authority, and no public wrapper-step opening. Failure is `PD2-STOP-PHYSICAL-STEP-FAIL`.

### PD2-S5 — second step and lifecycle continuation

Only after S4 passes, execute the second and final bounded `collect_step`:

- verify ownership continuation from current P2;
- verify continuation is not a repeated B1 claim;
- verify forced continuation/noop rows remain outside actor sampling;
- preserve original proposal-source and open-window identity for any genuine decision rows.

### PD2-S6 — bounded TIME_LIMIT/autoreset/learner transport

S6 is **mandatory for a complete PD2 success**, not optional after the prefix gates pass. With `T=2` and the reviewed deterministic fixture, require the second transition to exercise:

- TIME_LIMIT termination without changing frozen reason priority;
- authoritative pre-reset I4 terminal critic sidecar;
- terminal historical/current post-autoreset separation;
- safe historical copy before exact runtime ACK;
- exactly one timeout critic evaluation;
- I5a learner/buffer insertion;
- I5b return/GAE/ValueNorm semantics;
- clean buffer rollover.

This remains a two-transition forward-only smoke, not a learning rollout. A pass through only S4 or S5 is a useful prefix result but cannot close PD2 or original B2-V2.

## 15. Network mode and no-training guards

Production rollout semantics use `prep_rollout()`, which calls `eval()` for installed actors and VCritic. PD2 must use those public component methods, then wrap forwards in `torch.inference_mode()`. Stochastic actor proposals remain stochastic through `deterministic=False`; eval mode does not convert them to deterministic playback.

The authoritative mutation snapshots are taken only after the protected objects exist:

- `SNAPSHOT A`: after all actors, VCritic, ValueNorm, and any constructor-created optimizers exist and after required `prep_rollout()`, but before the first model forward;
- `SNAPSHOT B`: after successful S6 and before component teardown;
- require A == B for every mutation-protected state item.

The A/B guard must prove:

- actor optimizer `.step` calls: 0;
- critic optimizer `.step` calls: 0;
- `backward` calls: 0;
- actor/critic gradients: all `None`;
- actor/critic state-dict parameter and registered-buffer fingerprints: exact match;
- RNN module state included by actor/critic state dict: exact match;
- parameter tensor version counters and storage identity, where safe to retain: supporting evidence only;
- optimizer state-dict fingerprints: exact match;
- ValueNorm parameters/buffers/statistics: exact match and update calls 0;
- checkpoint loads/saves: 0/0;
- stock `compute_returns`, stock `happo.train`, runner `run`, playback loop, and evaluation loop: 0.

Install fail-fast instance guards around optimizer steps and any update-capable ValueNorm seam. Use recorder-only actor/critic trainer seams already accepted by I5; never instantiate/call a real trainer. Any mutation yields `PD2-STOP-PARAMETER-MUTATION` even if forward outputs are finite.

Expected runtime actor/critic RNN hidden-state tensors are rollout state, not model state, and are excluded from A/B mutation equality. Optimizer objects may exist, but their step count and state dict must remain unchanged; a legitimately empty pre-forward optimizer state must remain empty. State-dict/buffer fingerprints are authoritative, not version counters alone.

No CPU fallback, device remap, mixed-device transfer, dtype change, reduced observation dimension, additional warm-up, or retry is allowed.

## 16. Shutdown and current-state integrity design

The future supervisor must apply the reviewed D4-O classification, not infer success from `close()` returning:

- persist primary result and O4 before shutdown;
- capture the known process tree and persist O5 immediately before close;
- call `env.close()` first, then `SimulationApp.close()` in `finally`;
- O6 is evidence only if close returns in-process;
- require the worker dead, no known pre-close descendant survivor, no supervisor kill, no timeout, and an allowed exit code;
- accept only D4-O safe classes (`IN_PROCESS_CLOSE_RETURN` or `EXTERNAL_CLEAN_TERMINATION`); otherwise `PD2-STOP-SHUTDOWN-UNSAFE`.

Before launching the worker, the supervisor must require exact equality with the reviewed bounded post-R8 baseline for protected source hashes, the D4-CI shared-state fingerprint, expected junction/cache structural inventory, and critical extension namespace identities. Any mismatch is `PD2-STOP-SHARED-STATE-PRELAUNCH-MISMATCH`, and Isaac must not start.

After confirmed worker death and D4-O shutdown classification, the supervisor captures the same raw inventory again and runs `POSTRUN-INTEGRITY-GATE`. It must classify the delta using the **Postrun Structural vs Metadata Delta Classification** rather than equating every byte/timestamp change with a structural failure. Structural resolution mutation or ambiguous delta produces `PD2-STOP-SHARED-STATE-ASSUMPTION-VIOLATION`; a proven metadata-only refresh is recorded and disclosed without erasing otherwise valid S0-S6 functional evidence. No branch cleans, relinks, restores, installs, or retries.

## 17. Future success matrix

Full PD2 success requires every row:

| Gate | Required result |
|---|---|
| prelaunch shared-state baseline | exact reviewed post-R8 baseline; otherwise Isaac not started |
| S0 production startup prefix | Exact oracle PASS |
| S0R complete enabled-set stability | two consecutive read-only snapshots have identical sorted IDs/count/canonical SHA-256; no external golden comparison |
| S0R critical extension identity | every critical ID/state/version/path/manifest/authority/link target exact |
| S1 App/components/reset and I1/I2 | environment, actors 0/1/2, VCritic, optional ValueNorm, natural optimizers, `prep_rollout()`, reset, I1, and I2 PASS |
| SNAPSHOT A timing | captured after component construction/`prep_rollout()` and before first model forward |
| S2 first real installed VCritic current V(t) | existing critic; one finite `[2,1]` forward PASS; no construction/seed/reset/actor/step |
| S3 real installed HAPPO actor | DVM-only proposals/logprobs PASS |
| S4 first physical event step | nonterminal six-tuple PASS |
| S5 continuation/second step | PASS, no repeated claim |
| S6 TIME_LIMIT I4/I5a/I5b | PASS |
| SNAPSHOT B and parameter/state immutability | B captured after S6 and before teardown; SNAPSHOT A == SNAPSHOT B |
| optimizer/backward/update guards | 0/0/0 |
| public route fence | remains closed |
| shutdown | D4-O safe classification |
| postrun structural resolution | unchanged |
| postrun metadata | none or explicitly classified benign refresh |

Even full success means only that the current workaround-based production startup path avoided/reordered the observed failure and completed the intended bounded real interface smoke. It does not establish a cuBLAS root cause, a native fix, pre-R8 reproduction, public-route readiness, training readiness, or B2-R authorization.

## 18. Future STOP criteria

The future harness is fail-closed and must emit exactly one first-boundary classification:

- `PD2-STOP-STARTUP-EQUIVALENCE-MISMATCH`
- `PD2-STOP-SHARED-STATE-PRELAUNCH-MISMATCH`
- `PD2-STOP-RUNTIME-EXTENSION-IDENTITY-MISMATCH`
- `PD2-STOP-VCritic-CUDA-FAIL`
- `PD2-STOP-ACTOR-FORWARD-FAIL`
- `PD2-STOP-PHYSICAL-STEP-FAIL`
- `PD2-STOP-TERMINAL-TRANSPORT-FAIL`
- `PD2-STOP-PARAMETER-MUTATION`
- `PD2-STOP-SHUTDOWN-UNSAFE`
- `PD2-STOP-SHARED-STATE-ASSUMPTION-VIOLATION`

The current call must not continue to a later stage after its gate fails. There is no silent fallback, warm-up enhancement, retry, cleanup, source patch, installed-HARL patch, public-route activation, or second full V2 run.

## 19. Shared-State Guard Contract

### 19.1 Prelaunch Exact Baseline Gate

The supervisor, before creating the runtime worker, must compare the current machine with the **reviewed bounded D4-CI post-R8 baseline**. The gate is exact and covers:

- every protected D4-CI source plus the PD1 nine-file source set;
- the complete 103-row D4-CI bounded fingerprint (45 installed-root rows, 50 cache-root rows, and eight metadata rows);
- the 43 attributed installed-junction/cache-package pairs, including junction target, package directory identity, and manifest hash;
- installed extension namespace membership within the bounded roots;
- the expected critical extension manifest paths, versions, and hashes in the **Critical Extension Identity Manifest**.

All raw metadata hashes are exact at prelaunch; the metadata/structural distinction applies only to a delta caused or observed across the authorized worker lifetime. If any prelaunch field differs, classification is `PD2-STOP-SHARED-STATE-PRELAUNCH-MISMATCH`; the supervisor must not start the worker, AppLauncher, SimulationApp, or Isaac.

### 19.2 Postrun Structural vs Metadata Delta Classification

After the worker is confirmed dead and shutdown is safely classified, the supervisor recaptures the same raw inventory. It must preserve the complete before/after diff and classify each changed object before deciding consequence.

| State change type | Examples | Allowed? | PD2 consequence |
|---|---|---:|---|
| `NO_OBSERVED_STATE_CHANGE` | All bounded files, links, targets, manifests, namespace membership, and critical runtime identities unchanged | Yes | Functional S0-S6 result remains eligible for full PD2 assessment |
| `MUTABLE_METADATA_REFRESH` | Registry index timestamp/content refresh, registry lock refresh, cache bookkeeping timestamp, or `cache_db` non-resolution bookkeeping change, with exact proof that critical identity/version/path, namespace membership, junction targets, package manifests, and runtime enabled identities did not change | Conditionally | Record raw delta and proof; functional S0-S6 evidence remains eligible; final report must disclose `PASS_WITH_CLASSIFIED_BENIGN_METADATA_REFRESH` or equivalent separate metadata result |
| `STRUCTURAL_RESOLUTION_MUTATION` | New/removed/replaced installed junction, changed target, new resolution-participating cache package, package identity/version change, changed critical resolved path/version/manifest, or changed installed namespace membership | No | `PD2-STOP-SHARED-STATE-ASSUMPTION-VIOLATION`; not eligible for full closure |
| `AMBIGUOUS_STATE_DELTA` | A changed object cannot be proven metadata-only, classification inputs are incomplete, or content may influence extension selection/resolution | No | Fail closed as `PD2-STOP-SHARED-STATE-ASSUMPTION-VIOLATION` |

A metadata refresh is benign only by positive evidence, never by filename or timestamp alone. In particular, any `cache_db` or registry-index content change must be parsed/diffed sufficiently to show no extension candidate, mapping, version, path, trust, namespace, or manifest-selection effect. Otherwise it is ambiguous.

S0R and the postrun audit have distinct authority: S0R records what the worker actually loaded; the postrun audit records whether the surrounding resolution namespace changed during that lifecycle. Neither may be replaced by one aggregate hash.

## 20. Runtime Extension-Resolution Identity Oracle

### 20.1 S0R capture contract

S0R runs in the worker immediately after AppLauncher returns and before environment construction. Static source supports the following read-only API chain:

```text
omni.kit.app.get_app().get_extension_manager()
-> get_extensions()
-> is_extension_enabled(id)
-> get_enabled_extension_id(base_name)
-> get_extension_path(enabled_id)
-> get_extension_dict(enabled_id)
```

For the complete enabled set, S0R records the sorted enabled IDs, count, and SHA-256 over a canonical UTF-8 representation. It takes two back-to-back read-only snapshots without an app update or extension operation between them; the two snapshots' IDs/count/hash must be exactly equal. This is only a within-worker stability audit. No pre-existing golden count/hash exists, no pre-R8 enabled count/hash may be used as a golden, and this complete-set audit does not compare against a reviewed expected value.

For each critical entry, S0R records and validates:

- requested base extension ID and actual enabled extension ID;
- enabled state;
- package version from the extension dictionary;
- normalized resolved extension root/path;
- resolved `config/extension.toml` path when present;
- manifest/config SHA-256;
- expected authority category (`PROJECT_LOCAL_SOURCE`, `OFFICIAL_INSTALLED`, or `OFFICIAL_INSTALLED_CACHE`);
- whether the path is a junction/link and, if so, its final target.

Any unavailable required field is an oracle failure, not permission to compare fewer fields.

### 20.2 Critical Extension Identity Manifest

The minimum critical set is intentionally smaller than the full enabled graph. It covers local Isaac Lab identities, the explicit headless startup/runtime dependencies used by the selected route, and CUDA/physics-adjacent extensions. Versions and manifest hashes below are the current static expected identities; future PD2 prelaunch must recheck them exactly rather than assuming this document is still current.

| Extension | Expected version | Expected authority/path | Manifest SHA-256 | Why critical |
|---|---:|---|---|---|
| `isaaclab` | `0.36.23` | project `source/isaaclab` | `ad9c0fe4f7bfde023afc95290e5578f95c5b101d332095cdc75d7858c1f3a151` | Direct environment/framework source |
| `isaaclab_assets` | `0.2.2` | project `source/isaaclab_assets` | `777900c0c5ae96f5f9e88d7824c867062a930f9b27db4db58c2097e86d5d066e` | `isaaclab_tasks` dependency and robot assets |
| `isaaclab_tasks` | `0.10.31` | project `source/isaaclab_tasks` | `984cd22b00925a50e70aa04a7a8a53da1bde53927adbc8b0c1704ad4cdf4c8cb` | Selected task registration/runtime |
| `isaaclab_rl` | `0.1.4` | project `source/isaaclab_rl` | `17611e8fcca9297f88ff5c080e85ecaf7684015a1a75e5b4232261ade763df16` | Explicit official headless-experience dependency; not a claim that PD2 imports its Python API |
| `isaacsim.simulation_app` | `2.4.2` | installed `isaacsim/exts/isaacsim.simulation_app` | `6609623fbf15a3355a915232069a7e5e6279cd00edde39df84167c5a014f5893` | App startup authority |
| `isaacsim.core.api` | `4.2.16` | installed `isaacsim/exts/isaacsim.core.api` | `5304880f3b029092febc3678c796177be24fd508e20a8dceabfa887091a9b525` | Explicit experience/core simulation dependency |
| `isaacsim.core.cloner` | `1.3.4` | installed `isaacsim/exts/isaacsim.core.cloner` | `77de0a78118b6af2b0ff5225966a89507f95117e29ebad7c24e20bb8aa5a311b` | Explicit experience and multi-environment cloning dependency |
| `isaacsim.core.utils` | `2.2.8` | installed `isaacsim/exts/isaacsim.core.utils` | `7202eeb2c1d9145b5d691c33a5c28f5af66c07cadc4443c843dc5395e15eeffd` | Environment seed/core utility path |
| `omni.physx` | `106.5.7` | installed `isaacsim/extsPhysics/omni.physx` | `97516dcee1b6271943fca495a6080a83f23897ef0e11cb9728ca2f17e6a0fa95` | Explicit experience physics runtime |
| `omni.physx.tensors` | `106.5.7` | installed `isaacsim/extsPhysics/omni.physx.tensors` | `295ac7632a08c7fdf4111b267fc31fd552bd504504a1f9f76b2f2b0709069568` | Explicit experience tensor physics runtime |
| `omni.physx.fabric` | `106.5.7` | installed `isaacsim/extsPhysics/omni.physx.fabric` | `9fc842ed58cb46b9c356b462ff0173664d8066bae28b3c4aa19ddddb57f20f21` | Explicit experience Fabric bridge |
| `usdrt.scenegraph` | `7.5.1` | installed cache `usdrt.scenegraph-7.5.1+d02c707b...` | `a52a69b609100538429406619e9576e81fb1a18a279ddc40628d9fa932358818` | Explicit experience real-time scene graph |
| `omni.warp.core` | `1.5.0` | installed cache `omni.warp.core-1.5.0+wx64` | `62d55511ee3d3d9e150f34c5b6196f983af8915e5cf5afe17fe97e96348408df` | Explicit experience dependency and environment seed Warp state |

The expected authority is the current reviewed post-R8 state plus these project-local/official installed paths and manifest identities. It is not pre-R8 authority. An unexpected registry-selected replacement, wrong junction target, missing project-local extension, unexpected path/version, disabled critical item, or untrusted unexpected package actually used yields `PD2-STOP-RUNTIME-EXTENSION-IDENTITY-MISMATCH`; S1 environment construction is not run.

## 21. Production RNG / Seed Audit and Frozen PD2 Seed Contract

### 21.1 Static production audit

The selected `TRAIN_STARTUP_PREFIX_V1` does not seed before the existing CUDA/cuBLAS warm-up. The production training order supported by source is:

1. `train.py` parses `--seed` with default `1` (`train.py:55`).
2. The exact pre-App warm-up executes without a seed call (`train.py:131-150`).
3. AppLauncher/SimulationApp start.
4. `train.py` writes the CLI value into `algo_args["seed"]["seed"]` (`train.py:261-262`). It adds `specify_seed=True`, while the YAML's actual `seed_specify=True` remains present; PD2 must not repair or reinterpret this source detail.
5. After the assignment runtime-ready barrier and before device/output/environment/actor/critic construction, the assignment runner calls installed HARL `set_seed(algo_args["seed"])` (`assignment_harl_training.py:491-537`).
6. Installed HARL `set_seed` executes, in order: `random.seed`, `numpy.random.seed`, sets `PYTHONHASHSEED`, `torch.manual_seed`, `torch.cuda.manual_seed`, and `torch.cuda.manual_seed_all` (`harl/utils/envs_tools.py:242-251`). Setting `PYTHONHASHSEED` after process start is recorded production behavior, but is not claimed to retroactively control interpreter hash randomization.
7. The assignment environment factory receives the HARL seed argument but the assignment-specific branch constructs from `env_args["config"]` (`assignment_harl_training.py:429-445`). `ScanMobileManipulatorEnvCfg.seed` is independently `1` (`scan_mobile_manipulator_env.py:115`).
8. During DirectMARLEnv construction, `cfg.seed` is applied before scene/runtime setup (`direct_marl_env.py:86-90`). The seed path calls Replicator global seed and Isaac Sim Torch utilities (`direct_marl_env.py:449-457`). Those utilities execute `random.seed`, `numpy.random.seed`, `torch.manual_seed`, set `PYTHONHASHSEED`, call `torch.cuda.manual_seed`, `torch.cuda.manual_seed_all`, and `wp.rand_init` (`isaacsim.core.utils.torch.maths.py:103-117`).
9. Only after environment construction are the three actors and VCritic constructed (`assignment_harl_training.py:564-667`). Production runner warmup later resets the environment without a seed argument (`on_policy_base_runner.py:316-320`).

`play_assignment.py` is not the selected seed oracle: its CLI seed defaults to `None`, it optionally writes `env_cfg.seed`, and it optionally passes the seed again to reset (`play_assignment.py:117, 635-637, 692-693`).

### 21.2 Frozen future PD2 seed contract

The canonical seed is the existing production/config value `1`. The future harness must also log the exact runtime-resolved values and apply this precedence:

```text
selected train CLI/config seed (default 1)
  > agent YAML seed value for HARL arguments

environment seed authority:
  ScanMobileManipulatorEnvCfg.seed

PD2 admission requirement:
  resolved HARL seed == resolved environment cfg.seed == 1
```

If a future authorized invocation resolves a different existing config value, PD2 must log it and require HARL/environment equality; it must not invent a new seed. A mismatch is `PD2-STOP-STARTUP-EQUIVALENCE-MISMATCH` before environment construction.

Exact PD2 order:

1. no Python/NumPy/Torch/CUDA/environment seed call before or inside the production warm-up;
2. AppLauncher returns and S0/S0R pass;
3. resolve/log the existing seed and call installed HARL `set_seed` with `seed_specify=True` and that value;
4. construct the environment with the matching `cfg.seed`, allowing DirectMARLEnv to perform the production Replicator/Torch/CUDA/Warp reseed;
5. construct distinct actors in agent order 0, 1, 2, then VCritic and ValueNorm, using production-effective `[256,256]`, `share_param=false`, and no checkpoint;
6. call required `prep_rollout()`, take SNAPSHOT A, then reset through the dormant route without a new reset seed;
7. preserve `deterministic=False` for I3a proposal sampling and perform no later reseed.

This order controls actor/critic initialization and stochastic proposal sampling without pretending they are deterministic by mode. PD2 evidence must include the resolved seed, ordered RNG events, environment seed returned/logged by the environment, actor and critic initial state fingerprints, first proposal IDs, and first proposal logprobs. Different proposal evidence can then be separated from a functional interface failure.

## 22. Correct Parameter Snapshot Timing and Scope

The phrase “before construction fingerprint” is withdrawn. Components cannot be fingerprinted before they exist.

`SNAPSHOT A` is captured after actor/VCritic/ValueNorm construction and after all required `prep_rollout()` calls, but before the first actor or critic forward. `SNAPSHOT B` is captured after successful S6 and before component teardown. A == B is required for:

- all actor parameters and registered buffers;
- all critic parameters and registered buffers;
- any RNN module state included in actor/critic state dicts;
- ValueNorm parameters, buffers, and running statistics;
- every constructor-created optimizer state dict.

Optimizer objects are allowed to exist. Their `.step` count is zero, and an empty optimizer state at A must remain empty at B. ValueNorm update calls are zero and its statistics remain unchanged; I5b may read/denormalize but cannot update running state. Expected rollout RNN hidden-state tensors are mutable transition state and are explicitly excluded from model-parameter equality.

Canonical serialized state-dict/buffer hashes are the authoritative guard. Parameter tensor version counters and storage identity may be recorded as additional evidence when safe, but never replace the authoritative fingerprints.

## 23. Revised PD2 Stage and Postrun Contract

```text
PRELAUNCH-EXACT-BASELINE-GATE (supervisor; no worker/Isaac on failure)
  -> S0   production startup prefix equivalence
  -> S0R  complete enabled-set within-worker stability audit;
          critical extension exact identity gate
  -> S1   production seed sequence; environment construction;
          actors 0/1/2, VCritic, optional ValueNorm, natural optimizers;
          prep_rollout();
          SNAPSHOT A; reset/I1/I2
  -> S2   first real VCritic current V(t) forward only
  -> S3   real DVM-only actors, deterministic=False
  -> S4   first physical event-route step
  -> S5   continuation/second step
  -> S6   TIME_LIMIT/I4/I5a/I5b
  -> SNAPSHOT B and worker result persistence
  -> D4-O safe shutdown
  -> POSTRUN-INTEGRITY-GATE (supervisor after worker death)
```

`POSTRUN-INTEGRITY-GATE` is not S7: it cannot run inside the worker whose death and shutdown classification it audits. Full PD2 success requires S0, S0R, and S1-S6 PASS; A == B; optimizer/backward/update counts 0/0/0; the public route blocked as expected; safe D4-O shutdown; exact prelaunch state; unchanged postrun structural resolution; and either no metadata delta or a disclosed, positively proven benign metadata refresh.

## 24. Targeted and Final Consistency Revision Closure

| GPT issue | Revision | Closure evidence | Status |
|---|---|---|---|
| 1 | R1 shared-state guard refinement | Exact prelaunch gate plus four-way postrun classification and supervisor-only integrity gate | CLOSED |
| 2 | R2 runtime extension identity | S0R API/fields, critical manifest, complete enabled-set stability hash, fail-before-environment rule | CLOSED |
| 3 | R3 production RNG/seed | Static train/HARL/environment seed order, canonical value/precedence, stochastic actor evidence | CLOSED |
| 4 | R4 fingerprint timing | Snapshot A/B timing and authoritative state/optimizer/ValueNorm scope | CLOSED |
| C1 | S0R complete-set authority | Complete set is within-worker stability only; critical subset alone uses an exact identity manifest | CLOSED |
| C2 | S1/S2 construction ordering | S1 owns environment/components/prep/Snapshot A/reset/I1/I2; S2 owns only the first VCritic forward | CLOSED |
| C3 | Cross-reference consistency | Mutable numeric section references replaced with authoritative title references | CLOSED |

No runtime, implementation, production mutation, installed-HARL mutation, or shared-state mutation was used to close R1-R4 or C1-C3.

## 25. Causal non-claims and phase relations

PD2, if later authorized, is a reviewed resumption path for the intended B2-V2 real Isaac/HARL interface evidence under current production startup ordering. It is not a new feature and does not alter I0-I6.

Explicit non-claims:

- It does not prove the production warm-up is intrinsically required.
- It does not prove Isaac, Kit, Torch, HARL, or the driver is defective or fixed.
- It does not reproduce the pre-R8 environment.
- It does not make the private dormant event route public.
- It does not authorize B2-R, training, playback, evaluation, checkpoint work, or a commit.
- A PD2 pass would make B2-V2 closure eligible for GPT review; it would not close B2-V2 automatically.

## 26. Recommended next slice

Stop after this report and wait for GPT independent design review.

If and only if separately authorized after review, the next slice should be:

```text
B2-V2-PD2
Current-Production-Startup Real Isaac/HARL Interface Validation

mode:
  PD-A / CURRENT-PRODUCTION-RUNTIME-VALIDATION

scope:
  test-only harness implementation and one bounded supervised execution
```

PD2 must implement the prelaunch gate, S0/S0R/S1-S6, and postrun integrity contract above without changing production sources. If the reviewer rejects PD-A’s shared-state risk, stop and design PD-B separately; do not substitute it implicitly.

## 27. No implementation / no execution statement

```text
production Python changes:       NONE
test harness implementation:     NOT STARTED
train.py / play_assignment.py:   NOT MODIFIED
AppLauncher / SimulationApp:     NOT RUN
Isaac / CUDA / matmul / Linear:  NOT RUN
HARL / VCritic / HAPPO / MRTA:   NOT RUN
I0-I6 runtime calls:             0
optimizer / backward:            0 / 0
training / playback / evaluation: NOT RUN
checkpoint changes:              NONE
shared Kit cleanup/mutation:     NONE BY PD1-RF
installed package changes:       NONE
commit:                          NONE
```
