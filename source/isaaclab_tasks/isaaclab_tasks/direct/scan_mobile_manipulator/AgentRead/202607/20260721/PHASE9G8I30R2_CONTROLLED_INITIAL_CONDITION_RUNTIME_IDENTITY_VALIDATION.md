# Phase 9G-8I-3-0R-2: Controlled Initial-Condition Runtime Identity Validation

Date: 2026-07-21

## 1. Classification

~~~text
RUNTIME-IDENTITY-FAIL
~~~

The no-selector run passed and reproduced the accepted historical `best_model`
trajectory exactly. The next run, explicit `baseline_identity`, failed before
environment construction because its project-owned request crossed two Python
module identities and failed the environment's strict type check. The frozen
sequential stop boundary was applied: no retry and no B/C run occurred.

## 2. Starting State And Preflight

~~~text
HEAD:
  167bafaac84f7f8f527af40ed786e4834a7db704

git log -1 --oneline:
  167bafaa docs(assignment): validate 100k best-final attribution comparison
~~~

The worktree contains only the accepted Phase 9G-8I-3-0, 3-0R, and 3-0R-1
documentation, implementation, test, and handoff chain. `git diff --check`
passed with line-ending warnings only. There was no relevant active playback or
training process. The six frozen output directories and six console-log paths
were absent.

GPU preflight recorded an NVIDIA GeForce RTX 4060 Ti with 8188 MiB total and
916 MiB used. No relevant assignment Python, Conda, Isaac, or Kit process was
active. The six PowerShell blocks below were parsed statically before launch:
6/6 had zero parser errors, the selector order was omitted/A/B/B/C/C, and all
six referenced `best_model` with no final `models` path.

The retained `best_model` checkpoint passed opaque-byte preflight:

~~~text
checkpoint kind:       best
checkpoint generation: 10
contract:              assignment_checkpoint_contract_v2
profile:               lifecycle_contract_c
M / N:                 3 / 50
actor/shared/action:   1059 / 3183 / 51
fingerprint:           19ef40b574c09c6c54b5e2ffea38e900b383188d2b48737a42b01d0db27c76e6
completion marker:     present
artifact size/SHA-256: PASS for three actors, critic, and ValueNorm
~~~

No actor tensor was deserialized during preflight.

## 3. Frozen Commands

All commands run from `E:\Project\IsaacLab_HARL`. Each block records
`$LASTEXITCODE` immediately after `Tee-Object` and hard-fails on nonzero exit.

### 3.1 No Selector

~~~powershell
$log = "C:\Users\33506\AppData\Local\Temp\phase9g8i30r2_noselector_best_console_20260721.log"
$output = "E:\Project\IsaacLab_HARL\results\isaaclab\Isaac-Scan-Mobile-Manipulator-Direct-v0\happo\assignment_happo_n50_phase9g8i30r2_noselector_best_runtime_identity\seed-00001"
if (Test-Path -LiteralPath $log) { throw "Console log already exists: $log" }
if (Test-Path -LiteralPath $output) { throw "Output already exists: $output" }
$args = @(
  "run", "-p", "C:\isaacenvs\isaac45_harl", "--no-capture-output",
  "python", "-u", "scripts\reinforcement_learning\harl\play_assignment.py",
  "--task", "Isaac-Scan-Mobile-Manipulator-Direct-v0",
  "--algorithm", "happo", "--assignment_rl",
  "--scenario_config", "source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\configs\scenarios\algorithm_proxy_component_mesh.yaml",
  "--num_envs", "1",
  "--dir", "E:\Project\IsaacLab_HARL\results\isaaclab\Isaac-Scan-Mobile-Manipulator-Direct-v0\happo\assignment_happo_n50_phase9g8i1_fresh_100k_policy_noop_load_diagnosis\seed-00001-2026-07-20-17-40-33\best_model",
  "--max_steps", "300", "--diagnostic_interval", "1", "--seed", "1",
  "--headless", "--device", "cuda:0", "--log_assignment_proposal_effective",
  "--assignment_proposal_effective_output_dir", $output,
  "env.assignment_lifecycle_profile=lifecycle_contract_c",
  "env.assignment_cooldown_enabled=true",
  "env.assignment_cooldown_trigger_mode=budget",
  "env.assignment_cooldown_apply_to_action_mask=false",
  "env.assignment_redirect_guardrail_enabled=false",
  "agent.device.cuda=true", "agent.device.cuda_deterministic=true",
  "agent.model.use_recurrent_policy=false",
  "agent.model.use_naive_recurrent_policy=false",
  "agent.algo.share_param=false"
)
$started = Get-Date
& "D:\miniconda3\Scripts\conda.exe" @args 2>&1 | Tee-Object -FilePath $log
$exitCode = $LASTEXITCODE
$ended = Get-Date
Write-Host "RUN_RECORD|noselector|$($started.ToString('o'))|$($ended.ToString('o'))|$(($ended-$started).TotalSeconds)|$exitCode"
if ($exitCode -ne 0) { throw "noselector failed with exit code $exitCode" }
~~~

### 3.2 Explicit Baseline Identity

~~~powershell
$log = "C:\Users\33506\AppData\Local\Temp\phase9g8i30r2_baseline_identity_best_console_20260721.log"
$output = "E:\Project\IsaacLab_HARL\results\isaaclab\Isaac-Scan-Mobile-Manipulator-Direct-v0\happo\assignment_happo_n50_phase9g8i30r2_baseline_identity_best_runtime_identity\seed-00001"
if (Test-Path -LiteralPath $log) { throw "Console log already exists: $log" }
if (Test-Path -LiteralPath $output) { throw "Output already exists: $output" }
$args = @(
  "run", "-p", "C:\isaacenvs\isaac45_harl", "--no-capture-output",
  "python", "-u", "scripts\reinforcement_learning\harl\play_assignment.py",
  "--task", "Isaac-Scan-Mobile-Manipulator-Direct-v0",
  "--algorithm", "happo", "--assignment_rl",
  "--scenario_config", "source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\configs\scenarios\algorithm_proxy_component_mesh.yaml",
  "--num_envs", "1",
  "--dir", "E:\Project\IsaacLab_HARL\results\isaaclab\Isaac-Scan-Mobile-Manipulator-Direct-v0\happo\assignment_happo_n50_phase9g8i1_fresh_100k_policy_noop_load_diagnosis\seed-00001-2026-07-20-17-40-33\best_model",
  "--max_steps", "300", "--diagnostic_interval", "1", "--seed", "1",
  "--headless", "--device", "cuda:0", "--log_assignment_proposal_effective",
  "--assignment_proposal_effective_output_dir", $output,
  "--assignment_initial_condition_profile", "baseline_identity",
  "env.assignment_lifecycle_profile=lifecycle_contract_c",
  "env.assignment_cooldown_enabled=true",
  "env.assignment_cooldown_trigger_mode=budget",
  "env.assignment_cooldown_apply_to_action_mask=false",
  "env.assignment_redirect_guardrail_enabled=false",
  "agent.device.cuda=true", "agent.device.cuda_deterministic=true",
  "agent.model.use_recurrent_policy=false",
  "agent.model.use_naive_recurrent_policy=false",
  "agent.algo.share_param=false"
)
$started = Get-Date
& "D:\miniconda3\Scripts\conda.exe" @args 2>&1 | Tee-Object -FilePath $log
$exitCode = $LASTEXITCODE
$ended = Get-Date
Write-Host "RUN_RECORD|baseline_identity|$($started.ToString('o'))|$($ended.ToString('o'))|$(($ended-$started).TotalSeconds)|$exitCode"
if ($exitCode -ne 0) { throw "baseline_identity failed with exit code $exitCode" }
~~~

### 3.3 Pose Cycle Forward Run 1

~~~powershell
$log = "C:\Users\33506\AppData\Local\Temp\phase9g8i30r2_pose_cycle_forward_run1_best_console_20260721.log"
$output = "E:\Project\IsaacLab_HARL\results\isaaclab\Isaac-Scan-Mobile-Manipulator-Direct-v0\happo\assignment_happo_n50_phase9g8i30r2_pose_cycle_forward_run1_best_runtime_identity\seed-00001"
if (Test-Path -LiteralPath $log) { throw "Console log already exists: $log" }
if (Test-Path -LiteralPath $output) { throw "Output already exists: $output" }
$args = @(
  "run", "-p", "C:\isaacenvs\isaac45_harl", "--no-capture-output",
  "python", "-u", "scripts\reinforcement_learning\harl\play_assignment.py",
  "--task", "Isaac-Scan-Mobile-Manipulator-Direct-v0",
  "--algorithm", "happo", "--assignment_rl",
  "--scenario_config", "source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\configs\scenarios\algorithm_proxy_component_mesh.yaml",
  "--num_envs", "1",
  "--dir", "E:\Project\IsaacLab_HARL\results\isaaclab\Isaac-Scan-Mobile-Manipulator-Direct-v0\happo\assignment_happo_n50_phase9g8i1_fresh_100k_policy_noop_load_diagnosis\seed-00001-2026-07-20-17-40-33\best_model",
  "--max_steps", "300", "--diagnostic_interval", "1", "--seed", "1",
  "--headless", "--device", "cuda:0", "--log_assignment_proposal_effective",
  "--assignment_proposal_effective_output_dir", $output,
  "--assignment_initial_condition_profile", "pose_cycle_forward",
  "env.assignment_lifecycle_profile=lifecycle_contract_c",
  "env.assignment_cooldown_enabled=true",
  "env.assignment_cooldown_trigger_mode=budget",
  "env.assignment_cooldown_apply_to_action_mask=false",
  "env.assignment_redirect_guardrail_enabled=false",
  "agent.device.cuda=true", "agent.device.cuda_deterministic=true",
  "agent.model.use_recurrent_policy=false",
  "agent.model.use_naive_recurrent_policy=false",
  "agent.algo.share_param=false"
)
$started = Get-Date
& "D:\miniconda3\Scripts\conda.exe" @args 2>&1 | Tee-Object -FilePath $log
$exitCode = $LASTEXITCODE
$ended = Get-Date
Write-Host "RUN_RECORD|pose_cycle_forward_run1|$($started.ToString('o'))|$($ended.ToString('o'))|$(($ended-$started).TotalSeconds)|$exitCode"
if ($exitCode -ne 0) { throw "pose_cycle_forward_run1 failed with exit code $exitCode" }
~~~

### 3.4 Pose Cycle Forward Run 2

~~~powershell
$log = "C:\Users\33506\AppData\Local\Temp\phase9g8i30r2_pose_cycle_forward_run2_best_console_20260721.log"
$output = "E:\Project\IsaacLab_HARL\results\isaaclab\Isaac-Scan-Mobile-Manipulator-Direct-v0\happo\assignment_happo_n50_phase9g8i30r2_pose_cycle_forward_run2_best_runtime_identity\seed-00001"
if (Test-Path -LiteralPath $log) { throw "Console log already exists: $log" }
if (Test-Path -LiteralPath $output) { throw "Output already exists: $output" }
$args = @(
  "run", "-p", "C:\isaacenvs\isaac45_harl", "--no-capture-output",
  "python", "-u", "scripts\reinforcement_learning\harl\play_assignment.py",
  "--task", "Isaac-Scan-Mobile-Manipulator-Direct-v0",
  "--algorithm", "happo", "--assignment_rl",
  "--scenario_config", "source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\configs\scenarios\algorithm_proxy_component_mesh.yaml",
  "--num_envs", "1",
  "--dir", "E:\Project\IsaacLab_HARL\results\isaaclab\Isaac-Scan-Mobile-Manipulator-Direct-v0\happo\assignment_happo_n50_phase9g8i1_fresh_100k_policy_noop_load_diagnosis\seed-00001-2026-07-20-17-40-33\best_model",
  "--max_steps", "300", "--diagnostic_interval", "1", "--seed", "1",
  "--headless", "--device", "cuda:0", "--log_assignment_proposal_effective",
  "--assignment_proposal_effective_output_dir", $output,
  "--assignment_initial_condition_profile", "pose_cycle_forward",
  "env.assignment_lifecycle_profile=lifecycle_contract_c",
  "env.assignment_cooldown_enabled=true",
  "env.assignment_cooldown_trigger_mode=budget",
  "env.assignment_cooldown_apply_to_action_mask=false",
  "env.assignment_redirect_guardrail_enabled=false",
  "agent.device.cuda=true", "agent.device.cuda_deterministic=true",
  "agent.model.use_recurrent_policy=false",
  "agent.model.use_naive_recurrent_policy=false",
  "agent.algo.share_param=false"
)
$started = Get-Date
& "D:\miniconda3\Scripts\conda.exe" @args 2>&1 | Tee-Object -FilePath $log
$exitCode = $LASTEXITCODE
$ended = Get-Date
Write-Host "RUN_RECORD|pose_cycle_forward_run2|$($started.ToString('o'))|$($ended.ToString('o'))|$(($ended-$started).TotalSeconds)|$exitCode"
if ($exitCode -ne 0) { throw "pose_cycle_forward_run2 failed with exit code $exitCode" }
~~~

### 3.5 Pose Cycle Reverse Run 1

~~~powershell
$log = "C:\Users\33506\AppData\Local\Temp\phase9g8i30r2_pose_cycle_reverse_run1_best_console_20260721.log"
$output = "E:\Project\IsaacLab_HARL\results\isaaclab\Isaac-Scan-Mobile-Manipulator-Direct-v0\happo\assignment_happo_n50_phase9g8i30r2_pose_cycle_reverse_run1_best_runtime_identity\seed-00001"
if (Test-Path -LiteralPath $log) { throw "Console log already exists: $log" }
if (Test-Path -LiteralPath $output) { throw "Output already exists: $output" }
$args = @(
  "run", "-p", "C:\isaacenvs\isaac45_harl", "--no-capture-output",
  "python", "-u", "scripts\reinforcement_learning\harl\play_assignment.py",
  "--task", "Isaac-Scan-Mobile-Manipulator-Direct-v0",
  "--algorithm", "happo", "--assignment_rl",
  "--scenario_config", "source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\configs\scenarios\algorithm_proxy_component_mesh.yaml",
  "--num_envs", "1",
  "--dir", "E:\Project\IsaacLab_HARL\results\isaaclab\Isaac-Scan-Mobile-Manipulator-Direct-v0\happo\assignment_happo_n50_phase9g8i1_fresh_100k_policy_noop_load_diagnosis\seed-00001-2026-07-20-17-40-33\best_model",
  "--max_steps", "300", "--diagnostic_interval", "1", "--seed", "1",
  "--headless", "--device", "cuda:0", "--log_assignment_proposal_effective",
  "--assignment_proposal_effective_output_dir", $output,
  "--assignment_initial_condition_profile", "pose_cycle_reverse",
  "env.assignment_lifecycle_profile=lifecycle_contract_c",
  "env.assignment_cooldown_enabled=true",
  "env.assignment_cooldown_trigger_mode=budget",
  "env.assignment_cooldown_apply_to_action_mask=false",
  "env.assignment_redirect_guardrail_enabled=false",
  "agent.device.cuda=true", "agent.device.cuda_deterministic=true",
  "agent.model.use_recurrent_policy=false",
  "agent.model.use_naive_recurrent_policy=false",
  "agent.algo.share_param=false"
)
$started = Get-Date
& "D:\miniconda3\Scripts\conda.exe" @args 2>&1 | Tee-Object -FilePath $log
$exitCode = $LASTEXITCODE
$ended = Get-Date
Write-Host "RUN_RECORD|pose_cycle_reverse_run1|$($started.ToString('o'))|$($ended.ToString('o'))|$(($ended-$started).TotalSeconds)|$exitCode"
if ($exitCode -ne 0) { throw "pose_cycle_reverse_run1 failed with exit code $exitCode" }
~~~

### 3.6 Pose Cycle Reverse Run 2

~~~powershell
$log = "C:\Users\33506\AppData\Local\Temp\phase9g8i30r2_pose_cycle_reverse_run2_best_console_20260721.log"
$output = "E:\Project\IsaacLab_HARL\results\isaaclab\Isaac-Scan-Mobile-Manipulator-Direct-v0\happo\assignment_happo_n50_phase9g8i30r2_pose_cycle_reverse_run2_best_runtime_identity\seed-00001"
if (Test-Path -LiteralPath $log) { throw "Console log already exists: $log" }
if (Test-Path -LiteralPath $output) { throw "Output already exists: $output" }
$args = @(
  "run", "-p", "C:\isaacenvs\isaac45_harl", "--no-capture-output",
  "python", "-u", "scripts\reinforcement_learning\harl\play_assignment.py",
  "--task", "Isaac-Scan-Mobile-Manipulator-Direct-v0",
  "--algorithm", "happo", "--assignment_rl",
  "--scenario_config", "source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\configs\scenarios\algorithm_proxy_component_mesh.yaml",
  "--num_envs", "1",
  "--dir", "E:\Project\IsaacLab_HARL\results\isaaclab\Isaac-Scan-Mobile-Manipulator-Direct-v0\happo\assignment_happo_n50_phase9g8i1_fresh_100k_policy_noop_load_diagnosis\seed-00001-2026-07-20-17-40-33\best_model",
  "--max_steps", "300", "--diagnostic_interval", "1", "--seed", "1",
  "--headless", "--device", "cuda:0", "--log_assignment_proposal_effective",
  "--assignment_proposal_effective_output_dir", $output,
  "--assignment_initial_condition_profile", "pose_cycle_reverse",
  "env.assignment_lifecycle_profile=lifecycle_contract_c",
  "env.assignment_cooldown_enabled=true",
  "env.assignment_cooldown_trigger_mode=budget",
  "env.assignment_cooldown_apply_to_action_mask=false",
  "env.assignment_redirect_guardrail_enabled=false",
  "agent.device.cuda=true", "agent.device.cuda_deterministic=true",
  "agent.model.use_recurrent_policy=false",
  "agent.model.use_naive_recurrent_policy=false",
  "agent.algo.share_param=false"
)
$started = Get-Date
& "D:\miniconda3\Scripts\conda.exe" @args 2>&1 | Tee-Object -FilePath $log
$exitCode = $LASTEXITCODE
$ended = Get-Date
Write-Host "RUN_RECORD|pose_cycle_reverse_run2|$($started.ToString('o'))|$($ended.ToString('o'))|$(($ended-$started).TotalSeconds)|$exitCode"
if ($exitCode -ne 0) { throw "pose_cycle_reverse_run2 failed with exit code $exitCode" }
~~~

## 4. Runtime Results

### 4.1 Sequential Run Record

| Order | Run | Start | End | Elapsed (s) | Exit | Loader | Result |
| ---: | --- | --- | --- | ---: | ---: | --- | --- |
| 1 | `noselector` | `2026-07-21T17:26:07.6445096+08:00` | `2026-07-21T17:29:49.2739628+08:00` | 221.629 | 0 | best, generation 10, normal evaluation, no fallback | PASS |
| 2 | `baseline_identity` | `2026-07-21T17:30:47.4826707+08:00` | `2026-07-21T17:37:27.2950019+08:00` | 399.812 | 1 | Not reached | FAIL before environment construction |
| 3 | `pose_cycle_forward_run1` | Not run | Not run | N/A | N/A | Not reached | Stopped by order-2 failure |
| 4 | `pose_cycle_forward_run2` | Not run | Not run | N/A | N/A | Not reached | Stopped by order-2 failure |
| 5 | `pose_cycle_reverse_run1` | Not run | Not run | N/A | N/A | Not reached | Stopped by order-2 failure |
| 6 | `pose_cycle_reverse_run2` | Not run | Not run | N/A | N/A | Not reached | Stopped by order-2 failure |

No run was retried. No command was changed after execution began.

### 4.2 No-Selector Technical Result

~~~text
process exit:              0
loader:                    kind=best, generation=10
load purpose:              normal_evaluation
legacy fallback:           False
completed/max steps:       300 / 300
robot rows/decisions:      900 / 300
robot ids per decision:    exactly 0,1,2
duplicate row keys:        0
summary invariant failures: 0
unclassified rows:         0
nonfinite selected probabilities: 0
segments:                  27
segment invariant_break:   0
file count:                exactly 3
traceback/runtime/assertion/shutdown matches: 0
~~~

Artifacts:

~~~text
E:\Project\IsaacLab_HARL\results\isaaclab\
Isaac-Scan-Mobile-Manipulator-Direct-v0\happo\
assignment_happo_n50_phase9g8i30r2_noselector_best_runtime_identity\
seed-00001\
~~~

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| `assignment_proposal_effective_rows.csv` | 832226 | `6a331aa1ad490016161804497aca84d1dc6ea1f445872e8a29fe0f517f786499` |
| `assignment_proposal_effective_summary.json` | 26272 | `25595055f0fbc33ffe5b099a2b73a49ff7ce681519f45d47cbd5957c34b79938` |
| `assignment_target_segments.csv` | 7641 | `76c9d09e85dd5c7048d3b6b9f307a0f1135a79f713c92d96e7649d5f551d6362` |

Console log:

~~~text
C:\Users\33506\AppData\Local\Temp\
phase9g8i30r2_noselector_best_console_20260721.log
~~~

No `assignment_initial_condition_manifest.json` was emitted. This is the exact
required default-off three-file behavior.

### 4.3 Explicit A Failure

The process reached Hydra configuration resolution and invoked
`make_assignment_harl_env`, but failed inside
`_prepare_assignment_initial_condition_cfg` before `DirectMARLEnv.__init__`,
scene/environment construction, checkpoint loading, reset, or policy steps.

Exact exception:

~~~text
InitialConditionContractError:
explicit assignment_initial_condition_profile requires a project-owned
InitialConditionRequest
~~~

The explicit-A result directory was not created and no attribution or condition
manifest file exists. Its preserved console log is:

~~~text
C:\Users\33506\AppData\Local\Temp\
phase9g8i30r2_baseline_identity_best_console_20260721.log
~~~

There is no A loader identity because actor checkpoint loading occurs only
after successful wrapper/environment construction.

## 5. Failure Diagnosis

The failure is a project source regression in the newly added runtime handoff,
not a checkpoint, resolver, mask, controller, pose, or GPU numerical failure.

Static source trace:

1. `play_assignment.py` inserts the scan task source directory directly into
   `sys.path` and imports `make_initial_condition_request` from the top-level
   module name `assignment_initial_condition`.
2. That factory returns the top-level module's
   `assignment_initial_condition.InitialConditionRequest` class.
3. `scan_mobile_manipulator_env.py` is imported through the task package and
   imports `.assignment_initial_condition`, whose class identity is
   `isaaclab_tasks.direct.scan_mobile_manipulator.assignment_initial_condition.InitialConditionRequest`.
4. `_prepare_assignment_initial_condition_cfg` performs strict
   `isinstance(request, InitialConditionRequest)` against the package-relative
   class. Python treats the two classes as distinct even though they originate
   from the same file.
5. The strict check therefore rejects the valid request before condition
   resolution.

The pure/fake R-1 tests did not exercise this real mixed import-identity
boundary. No source was patched in this phase.

## 6. Historical Default-Off Cross-Check

Compared against the accepted Phase 9G-8I-2-1 `best_model` output:

~~~text
results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/
assignment_happo_n50_phase9g8i21_best_100k_proposal_effective_attribution/
seed-00001
~~~

Results:

| Comparison | Result |
| --- | --- |
| Rows CSV bytes and SHA-256 | Exact equality |
| Segment CSV bytes and SHA-256 | Exact equality |
| Summary after removing only `artifact_paths` | Exact semantic equality |
| Proposal/effective sequence | Exact equality through all 300 decisions |
| Completion, coverage, budget, resolver events | Exact equality |

This proves that the newly added no-selector path preserved historical runtime
behavior. It does not rescue the broken explicit-profile path.

## 7. Condition And Comparison Tables

### 7.1 Condition Identity

| Condition | Profile | Fingerprint | Mapping | File count | Technical result |
| --- | --- | --- | --- | ---: | --- |
| Default | selector omitted | N/A by contract | Historical S0/S1/S2 | 3 | PASS |
| A | `baseline_identity` | Unavailable | Intended `r0->S0,r1->S1,r2->S2` | 0 | RUNTIME-INVALID: request type boundary |
| B1 | `pose_cycle_forward` | Not produced | Intended `r0->S1,r1->S2,r2->S0` | N/A | Not run |
| B2 | `pose_cycle_forward` | Not produced | Intended `r0->S1,r1->S2,r2->S0` | N/A | Not run |
| C1 | `pose_cycle_reverse` | Not produced | Intended `r0->S2,r1->S0,r2->S1` | N/A | Not run |
| C2 | `pose_cycle_reverse` | Not produced | Intended `r0->S2,r1->S0,r2->S1` | N/A | Not run |

### 7.2 Repeatability

| Pair | Fingerprint equal | Rows equal | Segments equal | Summary equal | Result |
| --- | ---: | ---: | ---: | ---: | --- |
| B1 vs B2 | N/A | N/A | N/A | N/A | Not run after A failure |
| C1 vs C2 | N/A | N/A | N/A | N/A | Not run after A failure |

### 7.3 A Compatibility

| Comparison | Poses | First actions | Rows | Segments | Summary | Result |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| no-selector vs explicit A | N/A | N/A | N/A | N/A | N/A | A failed before reset |
| historical best vs current no-selector | Same | Same | Exact | Exact | Exact after path normalization | PASS |

### 7.4 Behavioral Distinctness

| Comparison | Pose differs | First action differs | Trajectory differs | Segment differs | Outcome |
| --- | ---: | ---: | ---: | ---: | --- |
| A vs B | N/A | N/A | N/A | N/A | Not run |
| A vs C | N/A | N/A | N/A | N/A | Not run |
| B vs C | N/A | N/A | N/A | N/A | Not run |

No A/B/C condition fingerprint, pose/scanner/reset identity, repeatability, or
behavioral-distinctness claim can be made from this failed phase.

## 8. Available Headline Metrics

Only the technically successful no-selector run produced metrics:

| Metric | robot_0 | robot_1 | robot_2 |
| --- | ---: | ---: | ---: |
| Proposal noop | 0 | 0 | 0 |
| Executing steps | 300 | 300 | 300 |
| Assigned completions | 6 | 8 | 6 |
| Budget releases | 1 | 0 | 0 |
| Resolver proposal rejections | 0 | 0 | 0 |

~~~text
episode-0 terminal coverage: 0.70 (35/50)
mean active robots:          3.0
Jain completion fairness:    0.9803921568627451
~~~

These are diagnostics only. A/B/C metrics are unavailable and no checkpoint
selection was performed.

## 9. Runtime Safety And Diagnostics

The no-selector run had finite selected probabilities and physical row values,
zero attribution invariant failures, no duplicate effective target, no invalid
action, no traceback, and normal shutdown. It exactly reproduced the already
accepted historical trajectory.

Explicit A never reached reset or runtime state construction, so no pose,
scanner-offset, overlap, collision, finite-observation, action, or reset-safety
claim is available for A/B/C. The failure occurred before checkpoint load and
does not implicate checkpoint contents.

## 10. Output And Process Preservation

After the hard stop:

~~~text
noselector output: present, exactly three files
explicit A output: absent
B1/B2/C1/C2 outputs: absent
noselector log: present
explicit A log: present
B1/B2/C1/C2 logs: absent
relevant playback/training processes: 0
~~~

No result or log was deleted, renamed, overwritten, or reused.

## 11. Limitations

This phase validates only default-off identity. It does not validate explicit A,
either pose cycle, condition manifests/fingerprints, runtime pose/scanner/reset
identity, deterministic repeats, or behavioral distinctness. It therefore does
not authorize a multi-condition best/final comparison.

## 12. Next Recommendation

Recommend only a narrow design/repair phase:

~~~text
Phase 9G-8I-3-0R-2F:
Initial-Condition Runtime Module-Identity Boundary Repair And Regression Design
~~~

That phase should establish one canonical project module identity across the
playback request producer and environment consumer, and add a regression for
the real import boundary. It must not automatically rerun these frozen outputs
or broaden condition semantics. A separately reviewed runtime retry would be
required after repair.

## 13. Explicit Non-Actions

~~~text
No source, test, YAML, data, reward, resolver, mask, controller, checkpoint,
profile mapping, or condition coordinate was modified.
No final-model playback or best/final comparison ran.
No B or C playback ran.
No retry ran.
No training or checkpoint continuation ran.
No new seed, stochastic action, GUI/video, or 300k continuation ran.
No installed HARL or Conda file was modified.
No commit was made.
~~~
