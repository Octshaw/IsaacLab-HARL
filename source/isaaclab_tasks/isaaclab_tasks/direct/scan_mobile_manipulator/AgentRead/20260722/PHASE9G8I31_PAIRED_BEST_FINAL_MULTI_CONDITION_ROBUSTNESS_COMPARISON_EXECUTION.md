# Phase 9G-8I-3-1: Paired Best-vs-Final Multi-Condition Robustness Comparison Execution

## 1. Classification

```text
overall:
  CONSISTENT-LATE-TRAINING-REGRESSION

checkpoint-selection alignment:
  SELECTION-ALIGNED

technical execution:
  PASS
```

Exactly three new deterministic final-checkpoint playbacks were executed in the
frozen A/B/C order. All technical, pairing, fingerprint, and historical-A gates
passed. The classifications above apply the pre-frozen rules without changing
the metrics, tolerance, precedence, or run set after observing results.

## 2. Starting Repository And Production Lineage

```text
HEAD:
  9d31b15ff248d87634ae7487d0181ecf8a9349c2

commit:
  9d31b15f - add deterministic baseline and cyclic pose-slot profiles ...

starting status:
  exactly the three allowed Phase 9G-8I-3-1-0 Markdown changes

git diff --check:
  PASS
```

Blob comparison against HEAD passed for:

```text
scripts/reinforcement_learning/harl/play_assignment.py
scripts/reinforcement_learning/harl/train.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_initial_condition.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py
```

Static source inspection confirmed the package-qualified request import, strict
environment `InitialConditionRequest` identity check, unchanged A/B/C mappings,
canonical condition JSON/SHA-256 contract, manifest/condition schema v1, and
training hard guard.

## 3. Runtime And Evidence Preflight

| Check | Result |
| --- | --- |
| Relevant active playback/Isaac processes | none |
| GPU | NVIDIA GeForce RTX 4060 Ti, driver 537.58, 8188 MiB total, 1258 MiB in use |
| Conda interpreter | `C:\isaacenvs\isaac45_harl\python.exe` |
| Final checkpoint | `models`, kind `final`, generation 22 |
| Checkpoint contract | `assignment_checkpoint_contract_v2` |
| Canonical checkpoint fingerprint | `19ef40b574c09c6c54b5e2ffea38e900b383188d2b48737a42b01d0db27c76e6`, recomputation exact |
| Declared checkpoint artifacts | all five exist; sizes and opaque-byte SHA-256 exact |
| Interface | HAPPO / EP / feed-forward / `share_param=false` / 3 / 50 / 1059 / 3183 / 51 |
| Best A/B1/C1 | exactly four files each; accepted hashes unchanged |
| Best condition fingerprints | A/B/C canonical recomputation exact |
| Historical final A | exactly three files; all accepted hashes unchanged |
| New A/B/C output paths | absent |
| New A/B/C console logs | absent |

No checkpoint tensor was deserialized during preflight.

## 4. Preserved Evidence Hashes Before Runtime

| Evidence | Manifest SHA-256 | Rows SHA-256 | Summary SHA-256 | Segments SHA-256 |
| --- | --- | --- | --- | --- |
| Best A | `f1bd7aa087950daa287f7532ceb05a3cf117934e9dba1c085a0738b3b33f4df0` | `6a331aa1ad490016161804497aca84d1dc6ea1f445872e8a29fe0f517f786499` | `ce5d56d7f4004be22f5274c943efd6fd93320f7d995dbf0f6de113eecbf47229` | `76c9d09e85dd5c7048d3b6b9f307a0f1135a79f713c92d96e7649d5f551d6362` |
| Best B1 | `0943a54dea17c962b69ac73f79a81c0c93625d5f4684a8aaeb6e7247e43c6e12` | `9abbee8be7b97f5da9cbcd8a470d9306b90d73fda807872288c2ad40fd94aa92` | `84ecb7810fa11630f78e8f6dc8c167a5959105856c1eef308f50fc034b91fbf5` | `70ce639199c8c452dab42ec7f6f42099aa71db5efa44f6cb8d2961ba5ef7309d` |
| Best C1 | `1b7c1d5ccdabaaa40abb363c91fe823074dd59850c080cc228b0da5803354433` | `a2867da6a68e1f5305266458584e6494b7588373cc26b60171593fb3009a2c7e` | `beb7b2344ea5dd4b281caddedc6f262c36a621d6e85fd9ae79477e47c9fd8461` | `177e91d41101adf36e80db395458711b78efd21b5aa1cc31257f8c02e6698abc` |

Historical final A:

```text
rows:     f02c5b236bb81db1221cba713b245aa385724b2052a1bae32f24d412cf7cfbf1
summary:  4f95ada2ea130ad37fb00de31160e533493954bcfe7c65ebf634d015d528bad6
segments: f3d85fc0bb14492f3f10046e13de6f82a195e7d7de234022ca5dd8974d96df15
```

## 5. Exact Frozen Commands

All commands run from `E:\Project\IsaacLab_HARL`. They use final `models`,
never `best_model`.

### 5.1 Final A: `baseline_identity`

```powershell
$log = "C:\Users\33506\AppData\Local\Temp\phase9g8i31_baseline_identity_final_console_20260722.log"
$output = "E:\Project\IsaacLab_HARL\results\isaaclab\Isaac-Scan-Mobile-Manipulator-Direct-v0\happo\assignment_happo_n50_phase9g8i31_baseline_identity_final_multi_condition\seed-00001"
if (Test-Path -LiteralPath $log) { throw "Console log already exists: $log" }
if (Test-Path -LiteralPath $output) { throw "Output already exists: $output" }
$args = @(
  "run", "-p", "C:\isaacenvs\isaac45_harl", "--no-capture-output",
  "python", "-u", "scripts\reinforcement_learning\harl\play_assignment.py",
  "--task", "Isaac-Scan-Mobile-Manipulator-Direct-v0", "--algorithm", "happo", "--assignment_rl",
  "--scenario_config", "source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\configs\scenarios\algorithm_proxy_component_mesh.yaml",
  "--num_envs", "1",
  "--dir", "E:\Project\IsaacLab_HARL\results\isaaclab\Isaac-Scan-Mobile-Manipulator-Direct-v0\happo\assignment_happo_n50_phase9g8i1_fresh_100k_policy_noop_load_diagnosis\seed-00001-2026-07-20-17-40-33\models",
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
Write-Host "RUN_RECORD|baseline_identity_final|$($started.ToString('o'))|$($ended.ToString('o'))|$(($ended-$started).TotalSeconds)|$exitCode"
if ($exitCode -ne 0) { throw "baseline_identity_final failed with exit code $exitCode" }
```

### 5.2 Final B: `pose_cycle_forward`

```powershell
$log = "C:\Users\33506\AppData\Local\Temp\phase9g8i31_pose_cycle_forward_final_console_20260722.log"
$output = "E:\Project\IsaacLab_HARL\results\isaaclab\Isaac-Scan-Mobile-Manipulator-Direct-v0\happo\assignment_happo_n50_phase9g8i31_pose_cycle_forward_final_multi_condition\seed-00001"
if (Test-Path -LiteralPath $log) { throw "Console log already exists: $log" }
if (Test-Path -LiteralPath $output) { throw "Output already exists: $output" }
$args = @(
  "run", "-p", "C:\isaacenvs\isaac45_harl", "--no-capture-output",
  "python", "-u", "scripts\reinforcement_learning\harl\play_assignment.py",
  "--task", "Isaac-Scan-Mobile-Manipulator-Direct-v0", "--algorithm", "happo", "--assignment_rl",
  "--scenario_config", "source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\configs\scenarios\algorithm_proxy_component_mesh.yaml",
  "--num_envs", "1",
  "--dir", "E:\Project\IsaacLab_HARL\results\isaaclab\Isaac-Scan-Mobile-Manipulator-Direct-v0\happo\assignment_happo_n50_phase9g8i1_fresh_100k_policy_noop_load_diagnosis\seed-00001-2026-07-20-17-40-33\models",
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
Write-Host "RUN_RECORD|pose_cycle_forward_final|$($started.ToString('o'))|$($ended.ToString('o'))|$(($ended-$started).TotalSeconds)|$exitCode"
if ($exitCode -ne 0) { throw "pose_cycle_forward_final failed with exit code $exitCode" }
```

### 5.3 Final C: `pose_cycle_reverse`

```powershell
$log = "C:\Users\33506\AppData\Local\Temp\phase9g8i31_pose_cycle_reverse_final_console_20260722.log"
$output = "E:\Project\IsaacLab_HARL\results\isaaclab\Isaac-Scan-Mobile-Manipulator-Direct-v0\happo\assignment_happo_n50_phase9g8i31_pose_cycle_reverse_final_multi_condition\seed-00001"
if (Test-Path -LiteralPath $log) { throw "Console log already exists: $log" }
if (Test-Path -LiteralPath $output) { throw "Output already exists: $output" }
$args = @(
  "run", "-p", "C:\isaacenvs\isaac45_harl", "--no-capture-output",
  "python", "-u", "scripts\reinforcement_learning\harl\play_assignment.py",
  "--task", "Isaac-Scan-Mobile-Manipulator-Direct-v0", "--algorithm", "happo", "--assignment_rl",
  "--scenario_config", "source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\configs\scenarios\algorithm_proxy_component_mesh.yaml",
  "--num_envs", "1",
  "--dir", "E:\Project\IsaacLab_HARL\results\isaaclab\Isaac-Scan-Mobile-Manipulator-Direct-v0\happo\assignment_happo_n50_phase9g8i1_fresh_100k_policy_noop_load_diagnosis\seed-00001-2026-07-20-17-40-33\models",
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
Write-Host "RUN_RECORD|pose_cycle_reverse_final|$($started.ToString('o'))|$($ended.ToString('o'))|$(($ended-$started).TotalSeconds)|$exitCode"
if ($exitCode -ne 0) { throw "pose_cycle_reverse_final failed with exit code $exitCode" }
```

## 6. Static Command Audit

PASS. A parser found exactly three PowerShell blocks in A/B/C order. Each uses
the final `models` path exactly once, contains no `best_model`, fixes seed 1,
one environment, 300 steps, its explicit profile, all frozen lifecycle/HARL
overrides, output/log absence guards, immediate `$LASTEXITCODE` capture,
`RUN_RECORD`, and nonzero-exit throw. No video, evaluation, or stochastic flag
is present.

## 7. Run Results

| Run | Exit | Elapsed | Loader | Decisions/rows | Files | Technical result |
| --- | ---: | ---: | --- | --- | ---: | --- |
| Final A | 0 | 218.925 s | `models/final/22`, normal evaluation, no fallback | 300 / 900 | 4 | PASS |
| Final B | 0 | 204.406 s | `models/final/22`, normal evaluation, no fallback | 300 / 900 | 4 | PASS |
| Final C | 0 | 161.149 s | `models/final/22`, normal evaluation, no fallback | 300 / 900 | 4 | PASS |

## 8. Pairing, Metrics, And Classification

### 8.1 Final A Gate

```text
start:   2026-07-22T14:41:35.2059866+08:00
end:     2026-07-22T14:45:14.1312032+08:00
elapsed: 218.9252166 seconds
exit:    0
```

Final A produced 30 segments. Duplicate row keys, duplicate effective targets,
invariant failures, unclassified rows, nonfinite applicable values, controller/
effective mismatches, and segment/reset errors were all zero. The reset grouping
was the accepted 897 episode-0 rows plus three clean episode-1 rows with idle
pre-decision state and new claims.

The full final-A condition contract equals best A. Canonical recomputation
matched:

```text
d22778fbe70a5300999c58044177f2632b3c782c931d3414e086142035c516bc
```

The expected nonsemantic source-provenance difference is explicit:

```text
best A repository_commit:  167bafaac84f7f8f527af40ed786e4834a7db704
final A repository_commit: 9d31b15ff248d87634ae7487d0181ecf8a9349c2
```

Fresh final A passed the mandatory historical no-selector cross-check:

| Comparison | Rows | Segments | Summary | Actions | Outcome |
| --- | --- | --- | --- | --- | --- |
| Fresh explicit final A vs historical final A | byte exact | byte exact | exact after `artifact_paths` removal | all 900 robot rows exact | PASS |

Because the rows are byte exact, proposal, effective, controller, position,
distance, motion, event, coverage, completion, budget, resolver, and all 300
joint action decisions are exact. B is therefore authorized by the frozen gate.

Primary A result:

| Metric | Best | Final | Final-Best | Favored checkpoint |
| --- | ---: | ---: | ---: | --- |
| Coverage | 0.699999988079071 | 0.6800000071525574 | -0.0199999809265136 | Best |
| Total completions | 20 | 20 | 0 | Tie |
| Jain completion fairness | 0.9803921568627451 | 0.7490636704119851 | -0.2313284864507600 | Best |
| Zero-distance-progress rows | 31 | 129 | +98 | Best |
| Budget releases | 1 | 4 | +3 | Best |

Condition A class is `BEST-DOMINANT`.

### 8.2 Final B Gate

```text
start:   2026-07-22T14:49:23.5459473+08:00
end:     2026-07-22T14:52:47.9516706+08:00
elapsed: 204.4057233 seconds
exit:    0
```

Final B produced 30 segments. Duplicate row keys, duplicate effective targets,
invariant failures, unclassified rows, nonfinite applicable values, controller/
effective mismatches, and segment/reset errors were all zero. The artifact has
the required 897 episode-0 rows, its three terminal reset rows, and three clean
episode-1 new-claim rows.

The full final-B condition contract equals best B1. Canonical recomputation,
using the frozen identity mapping that excludes only `profile_description`,
matched:

```text
e9b92541c293de20277a97c61037b1592c01d72e6a84e8e6ba0e3fbe68da630f
```

The loader was `models/final/generation 22`, purpose `normal_evaluation`, with
no legacy fallback. The mapping was exactly `robot_0->S1`, `robot_1->S2`, and
`robot_2->S0`.

Primary B result:

| Metric | Best | Final | Final-Best | Favored checkpoint |
| --- | ---: | ---: | ---: | --- |
| Coverage | 0.699999988079071 | 0.6800000071525574 | -0.0199999809265136 | Best |
| Total completions | 22 | 19 | -3 | Best |
| Jain completion fairness | 0.9379844961240310 | 0.7037037037037037 | -0.2342807924203273 | Best |
| Zero-distance-progress rows | 15 | 113 | +98 | Best |
| Budget releases | 1 | 5 | +4 | Best |

Condition B class is `BEST-DOMINANT`. C is therefore authorized by the frozen
sequential gate.

### 8.3 Final C Gate

```text
start:   2026-07-22T14:58:07.0228738+08:00
end:     2026-07-22T15:00:48.1720601+08:00
elapsed: 161.1491863 seconds
exit:    0
```

Final C produced 25 segments. Duplicate row keys, duplicate effective targets,
invariant failures, unclassified rows, nonfinite applicable values, controller/
effective mismatches, and segment/reset errors were all zero. It has the same
valid 897-row episode-0 plus three-row episode-1 grouping as A and B.

The full final-C condition contract equals best C1. Canonical recomputation
matched:

```text
9f476403513ffb4377405d809fc71e537e1982f4ea30e17fad4ea3f3ec97f320
```

The loader was `models/final/generation 22`, purpose `normal_evaluation`, with
no legacy fallback. The mapping was exactly `robot_0->S2`, `robot_1->S0`, and
`robot_2->S1`.

Primary C result:

| Metric | Best | Final | Final-Best | Favored checkpoint |
| --- | ---: | ---: | ---: | --- |
| Coverage | 0.6200000047683716 | 0.6800000071525574 | +0.0600000023841858 | Final |
| Total completions | 17 | 15 | -2 | Best |
| Jain completion fairness | 0.9003115264797508 | 0.7575757575757576 | -0.1427357689039932 | Best |
| Zero-distance-progress rows | 15 | 95 | +80 | Best |
| Budget releases | 0 | 4 | +4 | Best |

Condition C class is `MIXED`: final wins coverage, while best wins the other
four available primary metrics.

## 9. Pair Identity And Artifact Validation

| Condition | Best fingerprint | Final fingerprint | Contract equal | Runtime equal | Pair valid |
| --- | --- | --- | --- | --- | --- |
| A | `d22778f...516bc` | `d22778f...516bc` | yes | yes | PASS |
| B | `e9b9254...da630f` | `e9b9254...da630f` | yes | yes | PASS |
| C | `9f47640...97f320` | `9f47640...97f320` | yes | yes | PASS |

Runtime equality covers seed 1, deterministic actor mode, one environment,
300 decisions, lifecycle Contract C overrides, feed-forward HAPPO/EP,
`share_param=false`, 1059/3183/51 interfaces, attribution schema, and explicit
condition profile. The intentional pair difference is checkpoint identity:
best is `best_model/best/generation 10`; final is `models/final/generation 22`.

For all three pairs, baseline/resolved poses, scenario, component, viewpoints,
robot/capability identities and hashes, M/N, and policy interface are exact.
The accepted best artifacts record repository commit `167bafa...`; the new
final artifacts record `9d31b15...`. This provenance difference is outside the
canonical condition contract and is reported, not normalized into that contract.

New artifact hashes:

| Condition | Manifest | Rows | Summary | Segments |
| --- | --- | --- | --- | --- |
| A | `ec258497...d42` | `f02c5b23...bf1` | `2397b87c...258` | `f3d85fc0...f15` |
| B | `8ed81d6c...e6f` | `602b13b3...397` | `a63445dd...263` | `f496013b...09e6` |
| C | `38eaee04...2c1` | `2c1d9b9f...e485` | `c587355c...0b9` | `f339ba2a...93f` |

Each directory contains exactly the four required artifacts and no temporary or
additional file. Every final run has 900 unique robot rows, 300 unique joint
decision keys, and exactly robot ids 0/1/2 at each key.

## 10. Combined Primary Metrics

The delta is always `final - best`; integer counts are exact and the frozen
floating tie tolerance is `1e-12`.

| Condition | Metric | Best | Final | Final-Best | Favored checkpoint |
| --- | --- | ---: | ---: | ---: | --- |
| A | Coverage | 0.699999988079071 | 0.6800000071525574 | -0.0199999809265136 | Best |
| A | Total completions | 20 | 20 | 0 | Tie |
| A | Jain completion fairness | 0.9803921568627451 | 0.7490636704119851 | -0.2313284864507600 | Best |
| A | Zero-distance-progress rows | 31 | 129 | +98 | Best |
| A | Budget releases | 1 | 4 | +3 | Best |
| B | Coverage | 0.699999988079071 | 0.6800000071525574 | -0.0199999809265136 | Best |
| B | Total completions | 22 | 19 | -3 | Best |
| B | Jain completion fairness | 0.9379844961240310 | 0.7037037037037037 | -0.2342807924203273 | Best |
| B | Zero-distance-progress rows | 15 | 113 | +98 | Best |
| B | Budget releases | 1 | 5 | +4 | Best |
| C | Coverage | 0.6200000047683716 | 0.6800000071525574 | +0.0600000023841858 | Final |
| C | Total completions | 17 | 15 | -2 | Best |
| C | Jain completion fairness | 0.9003115264797508 | 0.7575757575757576 | -0.1427357689039932 | Best |
| C | Zero-distance-progress rows | 15 | 95 | +80 | Best |
| C | Budget releases | 0 | 4 | +4 | Best |

No weighted composite score was formed.

## 11. Frozen Classifications

| Condition | Outcome wins | Balance wins | Stagnation wins | Class |
| --- | --- | --- | --- | --- |
| A | Best 1, tie 1 | Best 1 | Best 2 | `BEST-DOMINANT` |
| B | Best 2 | Best 1 | Best 2 | `BEST-DOMINANT` |
| C | Best 1, Final 1 | Best 1 | Best 2 | `MIXED` |

Cross-condition aggregation:

| Metric | Best wins | Final wins | Ties | Best range | Final range | Interpretation |
| --- | ---: | ---: | ---: | --- | --- | --- |
| Coverage | 2 | 1 | 0 | `[0.6200000048, 0.6999999881]`, span `0.0799999833` | `[0.6800000072, 0.6800000072]`, span `0` | Final advantage is confined to C |
| Total completions | 2 | 0 | 1 | `[17, 22]`, span `5` | `[15, 20]`, span `5` | Best wins B/C; A ties |
| Jain completion fairness | 3 | 0 | 0 | `[0.9003115265, 0.9803921569]`, span `0.0800806304` | `[0.7037037037, 0.7575757576]`, span `0.0538720539` | Best wins every condition |
| Zero-distance-progress rows | 3 | 0 | 0 | `[15, 31]`, span `16` | `[95, 129]`, span `34` | Best has less stagnation everywhere |
| Budget releases | 3 | 0 | 0 | `[0, 1]`, span `1` | `[4, 5]`, span `1` | Best has fewer releases everywhere |

There are two `BEST-DOMINANT` conditions, no `FINAL-DOMINANT` condition, and
no primary metric favors final in two conditions. Frozen precedence rule 2
therefore yields:

```text
CONSISTENT-LATE-TRAINING-REGRESSION
```

This is descriptive for the three frozen conditions only. It does not assert a
population-level or statistical regression.

The checkpoint-selection class is:

```text
SELECTION-ALIGNED
```

`best_model` was selected from rollout `Total_Reward` on the training
trajectory, not from the A/B/C multi-condition evaluation. The alignment result
does not claim that this selection rule is globally optimal.

## 12. Historical Final-A Reproduction

| Comparison | Rows | Segments | Summary | Actions | Outcome |
| --- | --- | --- | --- | --- | --- |
| Fresh explicit final A vs historical no-selector final A | byte exact | byte exact | exact after `artifact_paths` removal | all 900 robot rows and 300 joint decisions exact | PASS |

The accepted historical hashes remained `f02c5b23...bf1` for rows,
`f3d85fc0...f15` for segments, and `4f95ada2...bad6` for summary. No first
difference exists. This mandatory gate passed before B was launched.

## 13. Secondary Diagnostics

| Condition | Checkpoint | Completions | Coverage | Zero-motion | Zero-progress | Budget releases | Longest segments |
| --- | --- | --- | ---: | --- | --- | --- | --- |
| A | Best | `[6,8,6]` (20) | 0.7000 | `[63,7,30]` (100) | `[31,0,0]` (31) | `[1,0,0]` (1) | `[71,55,70]` |
| A | Final | `[12,5,3]` (20) | 0.6800 | `[43,76,82]` (201) | `[11,63,55]` (129) | `[0,3,1]` (4) | `[64,68,101]` |
| B | Best | `[6,10,6]` (22) | 0.7000 | `[52,17,25]` (94) | `[15,0,0]` (15) | `[1,0,0]` (1) | `[64,61,79]` |
| B | Final | `[11,7,1]` (19) | 0.6800 | `[51,57,108]` (216) | `[11,28,74]` (113) | `[0,1,4]` (5) | `[63,64,197]` |
| C | Best | `[7,7,3]` (17) | 0.6200 | `[25,11,38]` (74) | `[0,0,15]` (15) | `[0,0,0]` (0) | `[58,54,105]` |
| C | Final | `[7,7,1]` (15) | 0.6800 | `[31,51,97]` (179) | `[0,32,63]` (95) | `[0,1,3]` (4) | `[106,64,194]` |

All six artifacts have mean active robots `3.0`, executing-step vector
`[300,300,300]`, and Jain execution fairness `1.0`. Thus the completion
imbalance is not explained by one robot simply being idle. Completion ranges
best/final are A `2/9`, B `4/10`, and C `4/6`; dominant completion fractions
are A `0.40/0.60`, B `0.4545/0.5789`, and C `0.4118/0.4667`.

Per-robot mean/median segment durations:

| Condition | Best mean / median | Final mean / median |
| --- | --- | --- |
| A | `[33.33,30,37.50] / [28,28.5,38.5]` | `[21.43,30,50] / [18,25,44.5]` |
| B | `[33.33,25,37.50] / [29,24,33.5]` | `[23.08,30,42.86] / [14,37,17]` |
| C | `[33.33,33.33,60] / [29,31,54]` | `[33.33,30,50] / [26,39,14]` |

Segment counts best/final are A `27/30`, B `29/30`, and C `23/25`.
Same-target continuation vectors best/final are A `[291,290,292]` versus
`[286,290,294]`, B `[291,288,292]` versus `[287,290,293]`, and C
`[291,291,295]` versus `[291,290,294]`. Contract-C noop continuations are zero
for every robot and artifact. Every robot has exactly one repeated-target
attempt in every artifact.

Proposal-noop and resolver-rejection vectors are `[0,0,0]` throughout. Best's
first raw-action vector is `[13,47,49]`; final's is `[13,7,49]` in all three
conditions. The first trajectory divergence is `(env=0, episode=0,
decision=1, robot=1)`, `47` versus `7`. Raw/proposal/effective/controller
differences are respectively `800/800/800/800` rows in A, `678/678/678/678`
in B, and `758/758/758/758` in C. Within each artifact, effective and
controller assignments are exact.

The deduplicated episode-0 team coverage trajectories contain best/final
milestone counts A `31/31`, B `33/30`, and C `25/31`. Their maxima are first
reached at decision A `271/235`, B `292/285`, and C `281/249`, respectively.

Completion-event timing by robot (`r0 / r1 / r2`) is:

| Condition | Checkpoint | Completion decisions by robot |
| --- | --- | --- |
| A | Best | `[23,31,95,118,175,228] / [55,88,117,145,164,184,232,271] / [21,84,154,205,231,246]` |
| A | Final | `[23,31,60,73,81,89,118,120,126,153,185,235] / [56,77,85,128,157] / [21,110,198]` |
| B | Best | `[62,70,134,157,214,267] / [61,95,123,151,170,190,213,238,248,292] / [30,53,132,204,247,262]` |
| B | Final | `[62,70,99,112,120,128,159,187,219,222,285] / [37,61,69,111,119,160,197] / [30]` |
| C | Best | `[54,112,166,188,199,228,281] / [24,55,84,112,165,219,267] / [54,106,194]` |
| C | Final | `[106,114,140,148,156,195,249] / [47,53,57,107,115,156,193] / [72]` |

The completion vectors above are the exact sums of these events.
Release types cross-check the primary counts: budget failure best/final is A
`1/4`, B `1/5`, and C `0/4`; other terminal segment types are completion,
reset, and playback truncation.

## 14. Output Locations

The three new output children are:

```text
results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/
  assignment_happo_n50_phase9g8i31_baseline_identity_final_multi_condition/seed-00001
  assignment_happo_n50_phase9g8i31_pose_cycle_forward_final_multi_condition/seed-00001
  assignment_happo_n50_phase9g8i31_pose_cycle_reverse_final_multi_condition/seed-00001
```

Console evidence is preserved at the three frozen
`C:\Users\33506\AppData\Local\Temp\phase9g8i31_*_console_20260722.log`
paths. No result or console path was reused or overwritten.

## 15. Limitations

- One checkpoint pair, one seed, three deterministic initial robot-slot
  assignments, one vector environment, and 300 decisions support descriptive
  robustness evidence only; they do not provide confidence intervals or broad
  generalization.
- Coverage includes environment events that cannot always be attributed to one
  robot. Completion and coverage therefore remain separate primary metrics.
- The artifacts do not support claims about arm/joint motion, rotation quality,
  physical collision safety, or exact selected-path optimality.
- The result does not authorize more seeds, more conditions, intermediate
  checkpoints, continuation, new training, GUI/video, or real-robot work.

## 16. Explicit Non-Actions

No production source, test, YAML/data, checkpoint, existing result, installed
HARL, or Conda environment was modified. No best checkpoint was rerun. Each
final condition ran exactly once; there was no fourth condition, new seed,
stochastic evaluation, training, continuation, GUI/video, automatic retry, or
post-result source/config patch. No commit was made.

## 17. Next Recommendation

The next phase should be documentation/review only:

```text
Phase 9G-8I-3-2-0:
Multi-Condition Best-Final Evidence Synthesis And Commit Readiness Review
```

It should review the 3-1-0 design, this execution report, and the three new
result directories for closure and commit readiness. It must not automatically
start broader runtime work.

## 18. Post-Run Repository Verification

```text
production blobs equal HEAD:              PASS, 4/4
preserved best/historical hashes:         PASS, 15/15
final checkpoint opaque-byte integrity:   PASS, 5/5 artifacts
final checkpoint identity:                final / generation 22 / fingerprint exact
relevant playback/Isaac processes:        none
git diff --check:                          PASS
repository diff scope:                    Markdown only
```

`git status --short --untracked-files=all` contains exactly the three existing
Phase 9G-8I-3-1-0 documentation entries plus this report, its TASK_PROGRESS
archive, and the updated `TASK_PROGRESS.md`. Result directories are runtime
evidence under the established ignored results root and are not source diffs.

Files created in this phase:

```text
AgentRead/20260722/PHASE9G8I31_PAIRED_BEST_FINAL_MULTI_CONDITION_ROBUSTNESS_COMPARISON_EXECUTION.md
AgentRead/20260722/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G8I31_MULTI_CONDITION_COMPARISON_EXECUTION_20260722.md
```

Updated:

```text
AgentRead/TASK_PROGRESS.md
```
