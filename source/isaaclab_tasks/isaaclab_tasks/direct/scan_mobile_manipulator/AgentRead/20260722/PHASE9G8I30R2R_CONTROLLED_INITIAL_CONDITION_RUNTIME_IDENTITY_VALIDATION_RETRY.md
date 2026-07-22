# Phase 9G-8I-3-0R-2R: Controlled Initial-Condition Runtime Identity Validation Retry

## Classification

```text
MULTI-CONDITION-RUNTIME-IDENTITY-READY
```

All five authorized fresh output runs exited 0. Explicit Condition A crossed
the repaired strict producer/consumer request-type boundary and reproduced the
accepted R-2 no-selector behavior exactly. Conditions B and C resolved their
frozen mappings, repeated exactly in separate processes, and produced stable,
technically valid trajectories that were behaviorally distinct from A and from
each other.

This was a bounded runtime identity validation, not checkpoint selection,
performance evaluation, or training.

## Starting State And Preflight

The runtime baseline was:

```text
HEAD: 167bafaac84f7f8f527af40ed786e4834a7db704
log:  167bafaa docs(assignment): validate 100k best-final attribution comparison
```

The worktree already contained the accepted, uncommitted Phase 9G-8I-3-0
through R-2F-1 chain. Its behavior-bearing entries were:

```text
M  scripts/reinforcement_learning/harl/play_assignment.py
M  scripts/reinforcement_learning/harl/train.py
M  source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py
?? scripts/environments/test_assignment_initial_condition_contract.py
?? source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_initial_condition.py
```

`AgentRead/TASK_PROGRESS.md` and the accepted reports/archives under
`AgentRead/20260721/` and `AgentRead/20260722/` were also modified or untracked.
No source, test, YAML, or data diff was introduced by R-2R.

Preflight results:

| Check | Result |
| --- | --- |
| Required source/config paths | PASS |
| Five output directories absent before run 1 | PASS |
| Five console logs absent before run 1 | PASS |
| Relevant playback/Isaac process absent | PASS |
| GPU | RTX 4060 Ti; 8188 MiB total, 7040 MiB free before execution |
| Retained checkpoint | `best_model`, kind `best`, generation 10, complete |
| Load contract | `normal_evaluation`, no legacy fallback |
| Lifecycle/profile contract | HAPPO, EP, feed-forward, `share_param=false`, `lifecycle_contract_c` |
| Interfaces | actor 1059, shared 3183, action 51, M=3, N=50 |
| Actor/critic/ValueNorm artifact sizes and SHA-256 | PASS |
| New-path collision | none |
| `git diff --check` | PASS; line-ending warnings only |

The checkpoint contract fingerprint was:

```text
19ef40b574c09c6c54b5e2ffea38e900b383188d2b48737a42b01d0db27c76e6
```

## Preserved R-2 Evidence

The accepted no-selector result was reused without rerunning it:

```text
results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/
assignment_happo_n50_phase9g8i30r2_noselector_best_runtime_identity/
seed-00001
```

Its hashes before and after all five runs were unchanged:

| Artifact | SHA-256 |
| --- | --- |
| `assignment_proposal_effective_rows.csv` | `6a331aa1ad490016161804497aca84d1dc6ea1f445872e8a29fe0f517f786499` |
| `assignment_proposal_effective_summary.json` | `25595055f0fbc33ffe5b099a2b73a49ff7ce681519f45d47cbd5957c34b79938` |
| `assignment_target_segments.csv` | `76c9d09e85dd5c7048d3b6b9f307a0f1135a79f713c92d96e7649d5f551d6362` |

The earlier failed explicit-A output path remained absent. The preserved
no-selector console log and failed-boundary console log were not modified.

## Frozen Runtime Contract

Every run used the same retained `best_model`, seed 1, one environment, 300
deterministic steps, HAPPO, EP state, feed-forward actors, CUDA deterministic
mode, `share_param=false`, and the same lifecycle/budget/guardrail overrides.
Only profile, output path, console path, and run label changed. Runs were
strictly sequential in A, B1, B2, C1, C2 order.

## Exact Commands

These are the five exact no-placeholder PowerShell command bodies executed from
the repository root. Each checked path absence, captured `$LASTEXITCODE`
immediately after `Tee-Object`, emitted one `RUN_RECORD`, and threw on nonzero
exit.

### A: `baseline_identity_retry`

```powershell
$log = "C:\Users\33506\AppData\Local\Temp\phase9g8i30r2r_baseline_identity_best_console_20260722.log"
$output = "E:\Project\IsaacLab_HARL\results\isaaclab\Isaac-Scan-Mobile-Manipulator-Direct-v0\happo\assignment_happo_n50_phase9g8i30r2r_baseline_identity_best_runtime_identity\seed-00001"
if (Test-Path -LiteralPath $log) { throw "Console log already exists: $log" }
if (Test-Path -LiteralPath $output) { throw "Output already exists: $output" }
$args = @(
  "run", "-p", "C:\isaacenvs\isaac45_harl", "--no-capture-output",
  "python", "-u", "scripts\reinforcement_learning\harl\play_assignment.py",
  "--task", "Isaac-Scan-Mobile-Manipulator-Direct-v0", "--algorithm", "happo", "--assignment_rl",
  "--scenario_config", "source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\configs\scenarios\algorithm_proxy_component_mesh.yaml",
  "--num_envs", "1",
  "--dir", "E:\Project\IsaacLab_HARL\results\isaaclab\Isaac-Scan-Mobile-Manipulator-Direct-v0\happo\assignment_happo_n50_phase9g8i1_fresh_100k_policy_noop_load_diagnosis\seed-00001-2026-07-20-17-40-33\best_model",
  "--max_steps", "300", "--diagnostic_interval", "1", "--seed", "1",
  "--headless", "--device", "cuda:0", "--log_assignment_proposal_effective",
  "--assignment_proposal_effective_output_dir", $output,
  "--assignment_initial_condition_profile", "baseline_identity",
  "env.assignment_lifecycle_profile=lifecycle_contract_c", "env.assignment_cooldown_enabled=true",
  "env.assignment_cooldown_trigger_mode=budget", "env.assignment_cooldown_apply_to_action_mask=false",
  "env.assignment_redirect_guardrail_enabled=false", "agent.device.cuda=true",
  "agent.device.cuda_deterministic=true", "agent.model.use_recurrent_policy=false",
  "agent.model.use_naive_recurrent_policy=false", "agent.algo.share_param=false"
)
$started = Get-Date
& "D:\miniconda3\Scripts\conda.exe" @args 2>&1 | Tee-Object -FilePath $log
$exitCode = $LASTEXITCODE
$ended = Get-Date
Write-Host "RUN_RECORD|baseline_identity_retry|$($started.ToString('o'))|$($ended.ToString('o'))|$(($ended-$started).TotalSeconds)|$exitCode"
if ($exitCode -ne 0) { throw "baseline_identity_retry failed with exit code $exitCode" }
```

### B1: `pose_cycle_forward_retry_run1`

```powershell
$log = "C:\Users\33506\AppData\Local\Temp\phase9g8i30r2r_pose_cycle_forward_run1_best_console_20260722.log"
$output = "E:\Project\IsaacLab_HARL\results\isaaclab\Isaac-Scan-Mobile-Manipulator-Direct-v0\happo\assignment_happo_n50_phase9g8i30r2r_pose_cycle_forward_run1_best_runtime_identity\seed-00001"
if (Test-Path -LiteralPath $log) { throw "Console log already exists: $log" }
if (Test-Path -LiteralPath $output) { throw "Output already exists: $output" }
$args = @(
  "run", "-p", "C:\isaacenvs\isaac45_harl", "--no-capture-output",
  "python", "-u", "scripts\reinforcement_learning\harl\play_assignment.py",
  "--task", "Isaac-Scan-Mobile-Manipulator-Direct-v0", "--algorithm", "happo", "--assignment_rl",
  "--scenario_config", "source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\configs\scenarios\algorithm_proxy_component_mesh.yaml",
  "--num_envs", "1",
  "--dir", "E:\Project\IsaacLab_HARL\results\isaaclab\Isaac-Scan-Mobile-Manipulator-Direct-v0\happo\assignment_happo_n50_phase9g8i1_fresh_100k_policy_noop_load_diagnosis\seed-00001-2026-07-20-17-40-33\best_model",
  "--max_steps", "300", "--diagnostic_interval", "1", "--seed", "1",
  "--headless", "--device", "cuda:0", "--log_assignment_proposal_effective",
  "--assignment_proposal_effective_output_dir", $output,
  "--assignment_initial_condition_profile", "pose_cycle_forward",
  "env.assignment_lifecycle_profile=lifecycle_contract_c", "env.assignment_cooldown_enabled=true",
  "env.assignment_cooldown_trigger_mode=budget", "env.assignment_cooldown_apply_to_action_mask=false",
  "env.assignment_redirect_guardrail_enabled=false", "agent.device.cuda=true",
  "agent.device.cuda_deterministic=true", "agent.model.use_recurrent_policy=false",
  "agent.model.use_naive_recurrent_policy=false", "agent.algo.share_param=false"
)
$started = Get-Date
& "D:\miniconda3\Scripts\conda.exe" @args 2>&1 | Tee-Object -FilePath $log
$exitCode = $LASTEXITCODE
$ended = Get-Date
Write-Host "RUN_RECORD|pose_cycle_forward_retry_run1|$($started.ToString('o'))|$($ended.ToString('o'))|$(($ended-$started).TotalSeconds)|$exitCode"
if ($exitCode -ne 0) { throw "pose_cycle_forward_retry_run1 failed with exit code $exitCode" }
```

### B2: `pose_cycle_forward_retry_run2`

```powershell
$log = "C:\Users\33506\AppData\Local\Temp\phase9g8i30r2r_pose_cycle_forward_run2_best_console_20260722.log"
$output = "E:\Project\IsaacLab_HARL\results\isaaclab\Isaac-Scan-Mobile-Manipulator-Direct-v0\happo\assignment_happo_n50_phase9g8i30r2r_pose_cycle_forward_run2_best_runtime_identity\seed-00001"
if (Test-Path -LiteralPath $log) { throw "Console log already exists: $log" }
if (Test-Path -LiteralPath $output) { throw "Output already exists: $output" }
$args = @(
  "run", "-p", "C:\isaacenvs\isaac45_harl", "--no-capture-output",
  "python", "-u", "scripts\reinforcement_learning\harl\play_assignment.py",
  "--task", "Isaac-Scan-Mobile-Manipulator-Direct-v0", "--algorithm", "happo", "--assignment_rl",
  "--scenario_config", "source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\configs\scenarios\algorithm_proxy_component_mesh.yaml",
  "--num_envs", "1",
  "--dir", "E:\Project\IsaacLab_HARL\results\isaaclab\Isaac-Scan-Mobile-Manipulator-Direct-v0\happo\assignment_happo_n50_phase9g8i1_fresh_100k_policy_noop_load_diagnosis\seed-00001-2026-07-20-17-40-33\best_model",
  "--max_steps", "300", "--diagnostic_interval", "1", "--seed", "1",
  "--headless", "--device", "cuda:0", "--log_assignment_proposal_effective",
  "--assignment_proposal_effective_output_dir", $output,
  "--assignment_initial_condition_profile", "pose_cycle_forward",
  "env.assignment_lifecycle_profile=lifecycle_contract_c", "env.assignment_cooldown_enabled=true",
  "env.assignment_cooldown_trigger_mode=budget", "env.assignment_cooldown_apply_to_action_mask=false",
  "env.assignment_redirect_guardrail_enabled=false", "agent.device.cuda=true",
  "agent.device.cuda_deterministic=true", "agent.model.use_recurrent_policy=false",
  "agent.model.use_naive_recurrent_policy=false", "agent.algo.share_param=false"
)
$started = Get-Date
& "D:\miniconda3\Scripts\conda.exe" @args 2>&1 | Tee-Object -FilePath $log
$exitCode = $LASTEXITCODE
$ended = Get-Date
Write-Host "RUN_RECORD|pose_cycle_forward_retry_run2|$($started.ToString('o'))|$($ended.ToString('o'))|$(($ended-$started).TotalSeconds)|$exitCode"
if ($exitCode -ne 0) { throw "pose_cycle_forward_retry_run2 failed with exit code $exitCode" }
```

### C1: `pose_cycle_reverse_retry_run1`

```powershell
$log = "C:\Users\33506\AppData\Local\Temp\phase9g8i30r2r_pose_cycle_reverse_run1_best_console_20260722.log"
$output = "E:\Project\IsaacLab_HARL\results\isaaclab\Isaac-Scan-Mobile-Manipulator-Direct-v0\happo\assignment_happo_n50_phase9g8i30r2r_pose_cycle_reverse_run1_best_runtime_identity\seed-00001"
if (Test-Path -LiteralPath $log) { throw "Console log already exists: $log" }
if (Test-Path -LiteralPath $output) { throw "Output already exists: $output" }
$args = @(
  "run", "-p", "C:\isaacenvs\isaac45_harl", "--no-capture-output",
  "python", "-u", "scripts\reinforcement_learning\harl\play_assignment.py",
  "--task", "Isaac-Scan-Mobile-Manipulator-Direct-v0", "--algorithm", "happo", "--assignment_rl",
  "--scenario_config", "source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\configs\scenarios\algorithm_proxy_component_mesh.yaml",
  "--num_envs", "1",
  "--dir", "E:\Project\IsaacLab_HARL\results\isaaclab\Isaac-Scan-Mobile-Manipulator-Direct-v0\happo\assignment_happo_n50_phase9g8i1_fresh_100k_policy_noop_load_diagnosis\seed-00001-2026-07-20-17-40-33\best_model",
  "--max_steps", "300", "--diagnostic_interval", "1", "--seed", "1",
  "--headless", "--device", "cuda:0", "--log_assignment_proposal_effective",
  "--assignment_proposal_effective_output_dir", $output,
  "--assignment_initial_condition_profile", "pose_cycle_reverse",
  "env.assignment_lifecycle_profile=lifecycle_contract_c", "env.assignment_cooldown_enabled=true",
  "env.assignment_cooldown_trigger_mode=budget", "env.assignment_cooldown_apply_to_action_mask=false",
  "env.assignment_redirect_guardrail_enabled=false", "agent.device.cuda=true",
  "agent.device.cuda_deterministic=true", "agent.model.use_recurrent_policy=false",
  "agent.model.use_naive_recurrent_policy=false", "agent.algo.share_param=false"
)
$started = Get-Date
& "D:\miniconda3\Scripts\conda.exe" @args 2>&1 | Tee-Object -FilePath $log
$exitCode = $LASTEXITCODE
$ended = Get-Date
Write-Host "RUN_RECORD|pose_cycle_reverse_retry_run1|$($started.ToString('o'))|$($ended.ToString('o'))|$(($ended-$started).TotalSeconds)|$exitCode"
if ($exitCode -ne 0) { throw "pose_cycle_reverse_retry_run1 failed with exit code $exitCode" }
```

### C2: `pose_cycle_reverse_retry_run2`

```powershell
$log = "C:\Users\33506\AppData\Local\Temp\phase9g8i30r2r_pose_cycle_reverse_run2_best_console_20260722.log"
$output = "E:\Project\IsaacLab_HARL\results\isaaclab\Isaac-Scan-Mobile-Manipulator-Direct-v0\happo\assignment_happo_n50_phase9g8i30r2r_pose_cycle_reverse_run2_best_runtime_identity\seed-00001"
if (Test-Path -LiteralPath $log) { throw "Console log already exists: $log" }
if (Test-Path -LiteralPath $output) { throw "Output already exists: $output" }
$args = @(
  "run", "-p", "C:\isaacenvs\isaac45_harl", "--no-capture-output",
  "python", "-u", "scripts\reinforcement_learning\harl\play_assignment.py",
  "--task", "Isaac-Scan-Mobile-Manipulator-Direct-v0", "--algorithm", "happo", "--assignment_rl",
  "--scenario_config", "source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\configs\scenarios\algorithm_proxy_component_mesh.yaml",
  "--num_envs", "1",
  "--dir", "E:\Project\IsaacLab_HARL\results\isaaclab\Isaac-Scan-Mobile-Manipulator-Direct-v0\happo\assignment_happo_n50_phase9g8i1_fresh_100k_policy_noop_load_diagnosis\seed-00001-2026-07-20-17-40-33\best_model",
  "--max_steps", "300", "--diagnostic_interval", "1", "--seed", "1",
  "--headless", "--device", "cuda:0", "--log_assignment_proposal_effective",
  "--assignment_proposal_effective_output_dir", $output,
  "--assignment_initial_condition_profile", "pose_cycle_reverse",
  "env.assignment_lifecycle_profile=lifecycle_contract_c", "env.assignment_cooldown_enabled=true",
  "env.assignment_cooldown_trigger_mode=budget", "env.assignment_cooldown_apply_to_action_mask=false",
  "env.assignment_redirect_guardrail_enabled=false", "agent.device.cuda=true",
  "agent.device.cuda_deterministic=true", "agent.model.use_recurrent_policy=false",
  "agent.model.use_naive_recurrent_policy=false", "agent.algo.share_param=false"
)
$started = Get-Date
& "D:\miniconda3\Scripts\conda.exe" @args 2>&1 | Tee-Object -FilePath $log
$exitCode = $LASTEXITCODE
$ended = Get-Date
Write-Host "RUN_RECORD|pose_cycle_reverse_retry_run2|$($started.ToString('o'))|$($ended.ToString('o'))|$(($ended-$started).TotalSeconds)|$exitCode"
if ($exitCode -ne 0) { throw "pose_cycle_reverse_retry_run2 failed with exit code $exitCode" }
```

## Run Results

| Run | Start | End | Exit | Elapsed (s) | Loader | Decisions / rows | Files | Result |
| --- | --- | --- | ---: | ---: | --- | ---: | ---: | --- |
| A | 2026-07-22 10:01:34.6257563 +08:00 | 10:04:33.6396909 | 0 | 179.014 | best/g10 | 300 / 900 | 4 | PASS |
| B1 | 2026-07-22 10:08:42.3102178 +08:00 | 10:11:26.2281847 | 0 | 163.918 | best/g10 | 300 / 900 | 4 | PASS |
| B2 | 2026-07-22 10:11:51.5202402 +08:00 | 10:14:13.5352282 | 0 | 142.015 | best/g10 | 300 / 900 | 4 | PASS |
| C1 | 2026-07-22 10:16:23.6246461 +08:00 | 10:20:01.4395772 | 0 | 217.815 | best/g10 | 300 / 900 | 4 | PASS |
| C2 | 2026-07-22 10:20:48.0256917 +08:00 | 10:22:50.6944380 | 0 | 122.669 | best/g10 | 300 / 900 | 4 | PASS |

Every loader line reported:

```text
validated assignment checkpoint kind=best generation=10
purpose=normal_evaluation legacy_fallback=False
```

Every run reached `[OK] assignment play smoke completed steps=300,
max_steps=300` and shut down normally.

## Output And Log Paths

| Run | Output directory | Console log |
| --- | --- | --- |
| A | `results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/assignment_happo_n50_phase9g8i30r2r_baseline_identity_best_runtime_identity/seed-00001` | `C:\Users\33506\AppData\Local\Temp\phase9g8i30r2r_baseline_identity_best_console_20260722.log` |
| B1 | `results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/assignment_happo_n50_phase9g8i30r2r_pose_cycle_forward_run1_best_runtime_identity/seed-00001` | `C:\Users\33506\AppData\Local\Temp\phase9g8i30r2r_pose_cycle_forward_run1_best_console_20260722.log` |
| B2 | `results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/assignment_happo_n50_phase9g8i30r2r_pose_cycle_forward_run2_best_runtime_identity/seed-00001` | `C:\Users\33506\AppData\Local\Temp\phase9g8i30r2r_pose_cycle_forward_run2_best_console_20260722.log` |
| C1 | `results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/assignment_happo_n50_phase9g8i30r2r_pose_cycle_reverse_run1_best_runtime_identity/seed-00001` | `C:\Users\33506\AppData\Local\Temp\phase9g8i30r2r_pose_cycle_reverse_run1_best_console_20260722.log` |
| C2 | `results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/assignment_happo_n50_phase9g8i30r2r_pose_cycle_reverse_run2_best_runtime_identity/seed-00001` | `C:\Users\33506\AppData\Local\Temp\phase9g8i30r2r_pose_cycle_reverse_run2_best_console_20260722.log` |

## Artifact And Manifest Validation

Each directory contains exactly these four files and no temporary or extra
diagnostic file:

```text
assignment_proposal_effective_rows.csv
assignment_proposal_effective_summary.json
assignment_target_segments.csv
assignment_initial_condition_manifest.json
```

The three attribution schemas were unchanged. Each run had 900 unique robot
rows, 300 episode-aware decision groups, robot ids exactly 0/1/2 per group, no
duplicate effective target, no invariant failure, no unclassified row, valid
segment continuity, and no `invariant_break` release.

One first invocation of the read-only C1 validator omitted its required final
comparison-placeholder argument and raised `IndexError` before inspecting the
artifacts. The corrected invocation supplied the `-` sentinel and passed the
same existing C1 output. C1 playback was not rerun, and this analysis-call
mistake did not alter runtime evidence.

All five manifests passed:

```text
manifest_schema_version = assignment_initial_condition_manifest_v1
condition schema         = assignment_initial_condition_contract_v1
task                     = Isaac-Scan-Mobile-Manipulator-Direct-v0
M / N                    = 3 / 50
profile                  = lifecycle_contract_c
algorithm / state        = HAPPO / EP
sequence mode            = feed-forward
share_param              = false
interfaces               = 1059 / 3183 / 51
checkpoint               = best_model, best, generation 10
load purpose             = normal_evaluation
legacy fallback          = false
seed                     = 1
```

Scenario, component, viewpoint, robot, and capability paths and hashes matched
the frozen contract. Independent canonical-JSON SHA-256 recomputation matched
each stored condition fingerprint.

| Run | Manifest SHA-256 | Rows SHA-256 | Summary SHA-256 | Segments SHA-256 |
| --- | --- | --- | --- | --- |
| A | `f1bd7aa087950daa287f7532ceb05a3cf117934e9dba1c085a0738b3b33f4df0` | `6a331aa1ad490016161804497aca84d1dc6ea1f445872e8a29fe0f517f786499` | `ce5d56d7f4004be22f5274c943efd6fd93320f7d995dbf0f6de113eecbf47229` | `76c9d09e85dd5c7048d3b6b9f307a0f1135a79f713c92d96e7649d5f551d6362` |
| B1 | `0943a54dea17c962b69ac73f79a81c0c93625d5f4684a8aaeb6e7247e43c6e12` | `9abbee8be7b97f5da9cbcd8a470d9306b90d73fda807872288c2ad40fd94aa92` | `84ecb7810fa11630f78e8f6dc8c167a5959105856c1eef308f50fc034b91fbf5` | `70ce639199c8c452dab42ec7f6f42099aa71db5efa44f6cb8d2961ba5ef7309d` |
| B2 | `e3a755ba538d3e4317f9a743059aece3af7b871d995c8510f9d5a0af0b7ea479` | `9abbee8be7b97f5da9cbcd8a470d9306b90d73fda807872288c2ad40fd94aa92` | `0627c995415a332792213b16b03d679b1fc69f0224e52028eb4eddaca16b782f` | `70ce639199c8c452dab42ec7f6f42099aa71db5efa44f6cb8d2961ba5ef7309d` |
| C1 | `1b7c1d5ccdabaaa40abb363c91fe823074dd59850c080cc228b0da5803354433` | `a2867da6a68e1f5305266458584e6494b7588373cc26b60171593fb3009a2c7e` | `beb7b2344ea5dd4b281caddedc6f262c36a621d6e85fd9ae79477e47c9fd8461` | `177e91d41101adf36e80db395458711b78efd21b5aa1cc31257f8c02e6698abc` |
| C2 | `dd2c8607c705e6595c5181ac16848ae20908f21e086d0e9ac294ec86568a56c2` | `a2867da6a68e1f5305266458584e6494b7588373cc26b60171593fb3009a2c7e` | `0e5fa37ff47dc3acd974ac19a1620bd58944126f3a82672eb47999912ffc567f` | `177e91d41101adf36e80db395458711b78efd21b5aa1cc31257f8c02e6698abc` |

Raw repeat manifests and summaries retain allowed run/output provenance, hence
their whole-file hashes differ. Their fingerprinted condition payloads and
summaries after removing only `artifact_paths` are exactly equal.

## Condition Identity

Frozen slot poses were:

| Slot | Source pose WXYZ | Reset-effective XYZYaw |
| --- | --- | --- |
| S0 | `[-4,-2,0,1,0,0,0]` | `[-4,-2,0,0]` |
| S1 | `[0,3.5,0,0.70710678,0,0,-0.70710678]` | `[0,3.5,0,-1.5707963267948968]` |
| S2 | `[4,-2,0,0,0,0,1]` | `[4,-2,0,3.141592653589793]` |

| Condition | Profile | Fingerprint | Mapping | Technical result | Behavioral classification |
| --- | --- | --- | --- | --- | --- |
| A | `baseline_identity` | `d22778fbe70a5300999c58044177f2632b3c782c931d3414e086142035c516bc` | r0:S0, r1:S1, r2:S2 | PASS | Baseline authority |
| B | `pose_cycle_forward` | `e9b92541c293de20277a97c61037b1592c01d72e6a84e8e6ba0e3fbe68da630f` | r0:S1, r1:S2, r2:S0 | PASS x2 | TECHNICALLY-VALID-AND-BEHAVIORALLY-DISTINCT |
| C | `pose_cycle_reverse` | `9f476403513ffb4377405d809fc71e537e1982f4ea30e17fad4ea3f3ec97f320` | r0:S2, r1:S0, r2:S1 | PASS x2 | TECHNICALLY-VALID-AND-BEHAVIORALLY-DISTINCT |

All pairwise fingerprints differ; B1=B2 and C1=C2. The resolved pose multiset
in every condition equals the baseline slot multiset.

Scanner positions retain robot-local offsets rather than moving capabilities
with slots:

| Condition | robot_0 scanner XYZ | robot_1 scanner XYZ | robot_2 scanner XYZ |
| --- | --- | --- | --- |
| A | `[-3.3,-2,0.85]` | `[0.9,3.5,1.05]` | `[4.6,-2,0.75]` |
| B | `[0.7,3.5,0.85]` | `[4.9,-2,1.05]` | `[-3.4,-2,0.75]` |
| C | `[4.7,-2,0.85]` | `[-3.1,-2,1.05]` | `[0.6,3.5,0.75]` |

All runs grouped the episode-0 reset at decision step 299 across all three
robots and then emitted episode-1 decision step 1. For A, B, and C, the first
post-reset action, proposal, selected probability, initial target distance, and
base-motion value exactly equal the first decision of the run. This is direct
evidence that the selected condition and reset state persisted across the
automatic episode boundary.

## Repaired Type Boundary

Explicit A printed the canonical startup profile, fingerprint, and ordered
mapping, reached environment and wrapper construction, reached the validated
checkpoint loader, and completed all 300 steps. It emitted no
`InitialConditionContractError`, traceback, assertion, or request-type error.
The environment's strict request `isinstance` check remained active; it was not
relaxed or bypassed.

## A Compatibility

| Comparison | Rows | Segments | Summary | Actions | Outcome |
| --- | ---: | ---: | ---: | ---: | --- |
| accepted no-selector vs explicit A | byte equal | byte equal | exact after `artifact_paths` only | all 300 equal | PASS |

The first action vector was `[13,47,49]`. All action probabilities,
proposal/effective/controller assignments, positions, distances, motion,
events, episode/decision ids, coverage, completion, budget, and resolver fields
were unchanged. Explicit A added only the condition manifest and nonbehavioral
profile/path provenance.

## Repeatability

| Pair | Fingerprint | Rows | Segments | Summary | Outcome |
| --- | ---: | ---: | ---: | ---: | --- |
| B1 vs B2 | exact | byte equal | byte equal | exact after `artifact_paths` | PASS |
| C1 vs C2 | exact | byte equal | byte equal | exact after `artifact_paths` | PASS |

This includes all 300 action vectors, proposal/effective trajectories,
coverage/completion/budget/resolver outcomes, resolved poses, and first actions.
No device nondeterminism was accepted as an axis.

## Behavioral Distinctness

All three conditions initially selected `[13,47,49]`; therefore the first
action alone does not establish distinctness. Initial distances and motion
already differed at decision 1, and subsequent policy/lifecycle behavior
diverged substantially.

| Comparison | Pose differs | First action differs | Action decisions differing | Proposal/effective decisions differing | Motion decisions differing | Segment differs | Outcome |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| A vs B | yes | no | 267/300 | 271/300 | 300/300 | yes | distinct |
| A vs C | yes | no | 278/300 | 279/300 | 300/300 | yes | distinct |
| B vs C | yes | no | 275/300 | 276/300 | 300/300 | yes | distinct |

Coverage trajectories also differed in 241 A/B, 283 A/C, and 264 B/C
decisions. A/B and A/C first action divergence occurred at decision 22; B/C
first action divergence occurred at decision 25. Thus B and C are not merely
different manifests over the same behavior.

## Headline Metrics

B1 and C1 are shown; B2 and C2 reproduced them exactly.

| Metric | A | B | C |
| --- | --- | --- | --- |
| Proposal noop vector | `[0,0,0]` | `[0,0,0]` | `[0,0,0]` |
| Executing-step vector | `[300,300,300]` | `[300,300,300]` | `[300,300,300]` |
| Completion vector | `[6,8,6]` | `[6,10,6]` | `[7,7,3]` |
| Total completions | 20 | 22 | 17 |
| Episode-0 maximum coverage | 0.70 | 0.70 | 0.62 |
| Budget releases by robot / total | `[1,0,0]` / 1 | `[1,0,0]` / 1 | `[0,0,0]` / 0 |
| Resolver rejections | `[0,0,0]` | `[0,0,0]` | `[0,0,0]` |
| Contract-C continuations | `[291,290,292]` | `[291,288,292]` | `[291,291,295]` |
| Mean active robots | 3.0 | 3.0 | 3.0 |
| Jain execution fairness | 1.000000 | 1.000000 | 1.000000 |
| Jain completion fairness | 0.980392 | 0.937984 | 0.900312 |
| Target segment counts | `[9,10,8]` | `[9,12,8]` | `[9,9,5]` |
| Longest segment | `[71,55,70]` | `[64,61,79]` | `[58,54,105]` |
| Zero-base-motion executing rows | `[63,7,30]` | `[52,17,25]` | `[25,11,38]` |
| Zero target-distance-progress rows | `[31,0,0]` | `[15,0,0]` | `[0,0,15]` |

These are diagnostic observations only and are not checkpoint-ranking or
performance conclusions.

## Runtime Safety And Diagnostics

For every run:

```text
selected probabilities and applicable distance/motion values finite: PASS
nonfinite applicable values:                                      0
duplicate row keys / effective targets:                           0 / 0
invariant failures / unclassified rows:                           0 / 0
invariant_break segment releases:                                 0
traceback/assertion/contract/interface mismatch:                   0
immediate overlap/collision event matches:                         0
normal completion and shutdown:                                   PASS
```

The three null base-motion/coverage rows per run are the expected done/reset
rows; all other 897 post-state availability rows are populated. Diagnostic-only
mesh/inter-robot facilities remained configured, but no immediate overlap or
collision event was emitted. This does not prove physical safety for future
articulated robot implementations.

## Limitations

- One retained best checkpoint, one seed, one environment, and 300 decisions
  per process were tested.
- B/C repeatability establishes deterministic runtime identity under this
  machine and frozen command, not broad stochastic robustness.
- The initial action vector did not change; behavioral sensitivity appeared in
  initial geometry/motion and later policy/lifecycle trajectories.
- These task-space proxy diagnostics do not establish articulated-robot
  collision safety, convergence, or checkpoint superiority.
- No final checkpoint was run, so no best-vs-final conclusion is available.

## Explicit Non-Actions

No source, test, YAML, data, profile, mapping, pose, condition schema,
fingerprint, manifest, reward, resolver, mask, controller, or checkpoint
semantic was modified. The no-selector case was not rerun. No final checkpoint,
best/final comparison, training, continuation, new seed, stochastic action,
GUI/video, 300k continuation, automatic retry, installed HARL/Conda change, or
commit occurred.

## Next Phase Boundary

The only recommended next phase is:

```text
Phase 9G-8I-3-1-0:
Paired Best-vs-Final Multi-Condition Robustness Comparison Design
```

That phase may design the minimum evidence set, but it was not started here.
