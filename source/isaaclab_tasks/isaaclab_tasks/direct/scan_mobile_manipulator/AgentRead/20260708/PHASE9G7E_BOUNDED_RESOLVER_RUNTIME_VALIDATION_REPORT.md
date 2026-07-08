# Phase 9G-7E Bounded Resolver Runtime Validation Report

Date: 2026-07-08

Classification: PASS

Phase 9G-7E performed bounded runtime validation of the default-off `AssignmentLifecycleResolver` runtime integration. This phase ran short playback/evaluation episodes only. No training or short training smoke was run. No performance conclusion is made from the enabled resolver trajectories.

## Files Inspected

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/AGENTS.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260708/PHASE9G7A_EFFECTIVE_ASSIGNMENT_RESOLVER_ACTIVE_TARGET_LATCH_DESIGN_AUDIT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260708/PHASE9G7B_SHARED_EFFECTIVE_ASSIGNMENT_RESOLVER_PROTOTYPE_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260708/PHASE9G7C_DEFAULT_OFF_RESOLVER_RUNTIME_INTEGRATION_DESIGN_READINESS_AUDIT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260708/PHASE9G7D_DEFAULT_OFF_RESOLVER_RUNTIME_ADAPTER_INTEGRATION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260707/PHASE9G6D_PASSIVE_LIFECYCLE_BOUNDED_RUNTIME_VALIDATION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_lifecycle_resolver.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_lifecycle_resolver_runtime.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_lifecycle_diagnostics.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_wrapper.py
scripts/environments/evaluate_assignment_rl_playback_diagnostics.py
scripts/environments/evaluate_assignment_methods.py
scripts/environments/test_assignment_lifecycle_resolver_smoke.py
scripts/environments/test_assignment_lifecycle_resolver_runtime_smoke.py
```

## Files Created Or Updated

Created:

```text
scripts/environments/analyze_phase9g7e_resolver_runtime_validation.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260708/PHASE9G7E_BOUNDED_RESOLVER_RUNTIME_VALIDATION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260708/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G7E_BOUNDED_RESOLVER_RUNTIME_VALIDATION_20260708.md
```

Updated:

```text
scripts/environments/evaluate_assignment_rl_playback_diagnostics.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_wrapper.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_lifecycle_diagnostics.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
```

Diagnostic-only fixes made during Phase 9G-7E:

```text
1. Exposed RL playback CLI flags for the wrapper-owned resolver runtime adapter:
   --assignment_lifecycle_resolver_enabled
   --log_assignment_lifecycle_resolver
   --assignment_lifecycle_resolver_output_dir

2. Added wrapper-owned resolver finalization access so resolver summaries are written reliably.

3. Kept the RL playback path from constructing a second resolver instance; it reads the wrapper-owned resolver diagnostics.

4. Added the offline Phase 9G-7E analyzer for SHA identity, schema, event, invariant, and monitor checks.

5. Fixed passive lifecycle diagnostics metadata propagation so enabled passive streams are labeled
   effective_assignment_from_resolver instead of falling back to the adapter default proposal_type.
```

No resolver behavior contract was changed. No production scenario YAML was modified.

## Runtime Setup

Checkpoint:

```text
results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/assignment_happo_n50_phase9e4a_budget_m15_slack5_d5_train_100k/seed-00001-2026-07-01-14-40-47/models
```

Old-path baseline source:

```text
results/assignment_diagnostics/phase9g6d_lifecycle_runtime_validation/
```

The Phase 9G-6D baseline was used because checkpoint, scenario, seed, `num_envs`, `num_episodes`, `max_steps`, and output schema were compatible with the Phase 9G-7E resolver-disabled runs.

Disabled scenario/config:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh_assignment_cooldown_budget_m15_slack5_d5_redirect_guardrail.yaml
```

Enabled run-local scenario/config:

```text
results/assignment_diagnostics/phase9g7e_resolver_runtime_validation/configs/phase9g7e_resolver_enabled_no_redirect_no_legacy_failed_pair.yaml
```

The enabled run-local config preserved the Phase 9G-6D scenario and changed only the validation boundary needed for resolver runtime semantics:

```text
assignment_redirect_guardrail.enabled = false
assignment_failed_pair_memory.enabled = false
cooldown budget diagnostics preserved
```

Fixed settings:

```text
num_envs = 1
num_episodes = 1
max_steps = 300
seed = 1
device = cuda:0
headless = true
stop_on_done = true for RL playback
```

Runtime output root:

```text
results/assignment_diagnostics/phase9g7e_resolver_runtime_validation/
```

Generated runtime artifacts under `results/` are validation outputs and should not be committed by default.

## Runtime Commands

RL disabled:

```powershell
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/evaluate_assignment_rl_playback_diagnostics.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --algorithm happo --assignment_rl --num_envs 1 --headless --device cuda:0 --scenario_config source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh_assignment_cooldown_budget_m15_slack5_d5_redirect_guardrail.yaml --dir results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/assignment_happo_n50_phase9e4a_budget_m15_slack5_d5_train_100k/seed-00001-2026-07-01-14-40-47/models --num_episodes 1 --max_steps 300 --seed 1 --output_dir results/assignment_diagnostics/phase9g7e_resolver_runtime_validation/rl_disabled --stop_on_done
```

RL enabled:

```powershell
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/evaluate_assignment_rl_playback_diagnostics.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --algorithm happo --assignment_rl --num_envs 1 --headless --device cuda:0 --scenario_config results/assignment_diagnostics/phase9g7e_resolver_runtime_validation/configs/phase9g7e_resolver_enabled_no_redirect_no_legacy_failed_pair.yaml --dir results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/assignment_happo_n50_phase9e4a_budget_m15_slack5_d5_train_100k/seed-00001-2026-07-01-14-40-47/models --num_episodes 1 --max_steps 300 --seed 1 --output_dir results/assignment_diagnostics/phase9g7e_resolver_runtime_validation/rl_enabled --stop_on_done --assignment_lifecycle_resolver_enabled --log_assignment_lifecycle_resolver --assignment_lifecycle_resolver_output_dir results/assignment_diagnostics/phase9g7e_resolver_runtime_validation/rl_enabled/resolver --log_assignment_lifecycle --assignment_lifecycle_output_dir results/assignment_diagnostics/phase9g7e_resolver_runtime_validation/rl_enabled/lifecycle
```

Nearest disabled:

```powershell
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/evaluate_assignment_methods.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --methods nearest --num_envs 1 --num_episodes 1 --max_steps 300 --seed 1 --headless --device cuda:0 --scenario_config source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh_assignment_cooldown_budget_m15_slack5_d5_redirect_guardrail.yaml --output_dir results/assignment_diagnostics/phase9g7e_resolver_runtime_validation/nearest_disabled
```

Nearest enabled:

```powershell
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/evaluate_assignment_methods.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --methods nearest --num_envs 1 --num_episodes 1 --max_steps 300 --seed 1 --headless --device cuda:0 --scenario_config results/assignment_diagnostics/phase9g7e_resolver_runtime_validation/configs/phase9g7e_resolver_enabled_no_redirect_no_legacy_failed_pair.yaml --output_dir results/assignment_diagnostics/phase9g7e_resolver_runtime_validation/nearest_enabled --assignment_lifecycle_resolver_enabled --log_assignment_lifecycle_resolver --assignment_lifecycle_resolver_output_dir results/assignment_diagnostics/phase9g7e_resolver_runtime_validation/nearest_enabled/resolver --log_assignment_lifecycle --assignment_lifecycle_output_dir results/assignment_diagnostics/phase9g7e_resolver_runtime_validation/nearest_enabled/lifecycle
```

Random enabled:

```powershell
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/evaluate_assignment_methods.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --methods random --num_envs 1 --num_episodes 1 --max_steps 300 --seed 1 --headless --device cuda:0 --scenario_config results/assignment_diagnostics/phase9g7e_resolver_runtime_validation/configs/phase9g7e_resolver_enabled_no_redirect_no_legacy_failed_pair.yaml --output_dir results/assignment_diagnostics/phase9g7e_resolver_runtime_validation/random_enabled --assignment_lifecycle_resolver_enabled --log_assignment_lifecycle_resolver --assignment_lifecycle_resolver_output_dir results/assignment_diagnostics/phase9g7e_resolver_runtime_validation/random_enabled/resolver --log_assignment_lifecycle --assignment_lifecycle_output_dir results/assignment_diagnostics/phase9g7e_resolver_runtime_validation/random_enabled/lifecycle
```

Greedy enabled:

```powershell
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/evaluate_assignment_methods.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --methods greedy --num_envs 1 --num_episodes 1 --max_steps 300 --seed 1 --headless --device cuda:0 --scenario_config results/assignment_diagnostics/phase9g7e_resolver_runtime_validation/configs/phase9g7e_resolver_enabled_no_redirect_no_legacy_failed_pair.yaml --output_dir results/assignment_diagnostics/phase9g7e_resolver_runtime_validation/greedy_enabled --assignment_lifecycle_resolver_enabled --log_assignment_lifecycle_resolver --assignment_lifecycle_resolver_output_dir results/assignment_diagnostics/phase9g7e_resolver_runtime_validation/greedy_enabled/resolver --log_assignment_lifecycle --assignment_lifecycle_output_dir results/assignment_diagnostics/phase9g7e_resolver_runtime_validation/greedy_enabled/lifecycle
```

Offline analyzer:

```powershell
conda run -p C:\isaacenvs\isaac45_harl python scripts/environments/analyze_phase9g7e_resolver_runtime_validation.py --root results/assignment_diagnostics/phase9g7e_resolver_runtime_validation --baseline_root results/assignment_diagnostics/phase9g6d_lifecycle_runtime_validation --output_dir results/assignment_diagnostics/phase9g7e_resolver_runtime_validation/comparison
```

## Result Files

```text
results/assignment_diagnostics/phase9g7e_resolver_runtime_validation/comparison/phase9g7e_validation_summary.json
results/assignment_diagnostics/phase9g7e_resolver_runtime_validation/comparison/phase9g7e_validation_summary.csv
results/assignment_diagnostics/phase9g7e_resolver_runtime_validation/comparison/phase9g7e_enabled_runtime_table.csv
```

## Disabled Identity Result

Old-path baseline versus resolver-disabled current path passed exact SHA-256 identity.

| Run | assignment_history.csv | per_episode.csv | summary.csv | Parsed metrics |
| --- | --- | --- | --- | --- |
| RL disabled | exact SHA match | exact SHA match | exact SHA match | matched |
| nearest disabled | exact SHA match | exact SHA match | exact SHA match | matched |

SHA details:

```text
RL assignment_history.csv:
  0196244f14a5f565d4d726c5ca717b852c0860fa16dc7a6c740750f31ffe9e54
RL per_episode.csv:
  9e4ac413c4797022f1eed2e4518e495cb8d6d222b12fd063c66970bee8cc38a0
RL summary.csv:
  f9efa72f8d71892bf3e4b16d4cfb8342225594024d263deb125c4837fddc20e7

Nearest assignment_history.csv:
  d6e3828e35e27fcd14b6da304ba10066e275c80bd23004b515f6e4d56582a7ce
Nearest per_episode.csv:
  501fe00266a5d09ecb49a8f60d03d779dfb9caaafb8d44ce55d0a96578355868
Nearest summary.csv:
  e4d6769cd6da3f6755f7ff2f1f8269f394482dc79ac0a23166a006590a43a76e
```

Resolver-disabled state/event checks passed:

```text
resolver files in disabled runs: none
proposal == effective_assignment by disabled pass-through contract
resolver event count: 0
behavior_changed: false
```

## Enabled Runtime Summary

Coverage and AUC are observational only. They are not used to rank methods or claim performance.

| Run | Resolver | Final coverage | AUC | Episode length | Proposal/effective changed | Noop continue | Switch rejected | Budget release | Infeasible max streak | Stranded max streak | Result |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| rl_enabled | enabled | 0.50 | 0.33096971798899977 | 299 | 179 | 0 | 76 | 2 | 0 | 0 | PASS |
| nearest_enabled | enabled | 0.88 | 0.7301014065742493 | n/a | 432 | 0 | 216 | 0 | 0 | 0 | PASS |
| random_enabled | enabled | 0.08 | 0.056521691381931305 | n/a | 874 | 0 | 874 | 0 | 0 | 0 | PASS |
| greedy_enabled | enabled | 0.88 | 0.7301014065742493 | n/a | 432 | 0 | 216 | 0 | 0 | 0 | PASS |

Enabled event counts:

| Run | Total events | Started | Continued same target | Switch rejected | Owned rejected | Failed-pair rejected | Target completed | Budget failure | Release budget | Reset |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| rl_enabled | 932 | 20 | 698 | 76 | 18 | 85 | 25 | 2 | 2 | 6 |
| nearest_enabled | 947 | 41 | 424 | 216 | 216 | 0 | 44 | 0 | 0 | 6 |
| random_enabled | 907 | 4 | 19 | 874 | 0 | 0 | 4 | 0 | 0 | 6 |
| greedy_enabled | 947 | 41 | 424 | 216 | 216 | 0 | 44 | 0 | 0 | 6 |

Proposal/effective explanation consistency:

```text
RL changed rows: 179; unexplained: 0
Nearest changed rows: 432; unexplained: 0
Random changed rows: 874; unexplained: 0
Greedy changed rows: 432; unexplained: 0
```

Explanation counts:

```text
RL:
  failed_pair_reclaim_rejected = 85
  owned_target_rejected = 18
  switch_rejected = 76

Nearest:
  owned_target_rejected = 216
  switch_rejected = 216

Random:
  switch_rejected = 874

Greedy:
  owned_target_rejected = 216
  switch_rejected = 216
```

## Semantic Invariants

Controller/effective consistency:

```text
passed where logged by the runtime adapter and script wiring
comparison methods send effective_assignment into viewpoint_assignment_to_actions()
RL playback uses the wrapper-owned resolver result and records proposal/effective separation
no second resolver instance was constructed in playback
```

Ownership invariants:

```text
one active target per robot: passed
one owner per task: passed
ownership failure count: 0 for all enabled runs
```

Completion consistency:

```text
RL newly covered targets = 25; resolver target_completed = 25
Nearest newly covered targets = 44; resolver target_completed = 44
Random newly covered targets = 4; resolver target_completed = 4
Greedy newly covered targets = 44; resolver target_completed = 44
```

Budget/release consistency:

```text
RL budget_failure = 2
RL release_budget_failure = 2
budget effective-target identity: passed
nearest/random/greedy had no supplied budget trigger events in these bounded runs
```

Reset ordering:

```text
passed
post-step completion/budget/release evidence was preserved before reset events
reset count = 6 for each enabled run
```

Passive logger coexistence:

```text
passed
transition passive proposal_type = effective_assignment_from_resolver for all enabled runs
reset passive proposal_type remains the adapter default metadata and is not treated as transition input
```

Active-target infeasibility monitoring:

```text
active_target_infeasible_step_count = 0 for all enabled runs
active_target_infeasible_max_streak = 0 for all enabled runs
monitoring remained diagnostics-only
```

Stranded failed-pair monitoring:

```text
stranded_failed_pair_started_count = 0 for all enabled runs
stranded_failed_pair_recovered_count = 0 for all enabled runs
stranded_failed_pair_max_streak = 0 for all enabled runs
detector remained diagnostics-only
```

Schema and output isolation:

```text
schema_version = phase9g7d_assignment_lifecycle_resolver_runtime_v1
event field set: consistent
row field set: consistent
summary counters matched parsed event counts
output isolation: passed
invalid proposals: none reported by analyzer
```

## Validation Commands

Syntax checks:

```powershell
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_lifecycle_resolver.py
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_lifecycle_resolver_runtime.py
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_lifecycle_diagnostics.py
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_wrapper.py
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/evaluate_assignment_rl_playback_diagnostics.py
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/evaluate_assignment_methods.py
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/analyze_phase9g7e_resolver_runtime_validation.py
```

Result:

```text
passed
```

Pure regression smokes:

```powershell
conda run -p C:\isaacenvs\isaac45_harl python scripts/environments/test_assignment_lifecycle_resolver_smoke.py --json
conda run -p C:\isaacenvs\isaac45_harl python scripts/environments/test_assignment_lifecycle_resolver_runtime_smoke.py --json
conda run -p C:\isaacenvs\isaac45_harl python scripts/environments/test_assignment_lifecycle_transition_logger_smoke.py
conda run -p C:\isaacenvs\isaac45_harl python scripts/environments/test_assignment_lifecycle_runtime_integration_smoke.py
```

Result:

```text
passed
```

Offline analyzer:

```powershell
conda run -p C:\isaacenvs\isaac45_harl python scripts/environments/analyze_phase9g7e_resolver_runtime_validation.py --root results/assignment_diagnostics/phase9g7e_resolver_runtime_validation --baseline_root results/assignment_diagnostics/phase9g6d_lifecycle_runtime_validation --output_dir results/assignment_diagnostics/phase9g7e_resolver_runtime_validation/comparison
```

Result:

```text
PASS
```

Repository checks:

```powershell
git diff --check
git status --short --untracked-files=all
```

Result:

```text
git diff --check passed
git status completed; expected Phase 9G-7A through 9G-7E uncommitted files remain present
```

## Known Limitations

```text
Enabled resolver runtime behavior is validated semantically only; no performance claim is made.
The policy still cannot observe behavior-driving lifecycle state, so resolver-enabled training remains prohibited.
No long training was run.
No short training smoke was run.
Episode-persistent failed-pair rejection remains a known stranded-task risk even though no stranded case occurred in these bounded runs.
Active-target infeasibility remains deferred/log-only; no infeasible streak occurred in these bounded runs.
Legacy failed-pair memory and redirect guardrail were disabled for resolver-enabled validation to avoid competing behavior mechanisms.
Generated runtime result artifacts under results/ are not intended for commit by default.
```

## Conclusion

Phase 9G-7E is PASS.

Resolver-disabled runtime identity passed exactly for RL and nearest against the Phase 9G-6D old-path baseline. Resolver-enabled bounded runtime validation passed semantic checks for RL, nearest, random, and greedy. Proposal/effective differences were fully explained, controller/effective wiring was validated where logged, ownership invariants held, completion and budget/release consistency passed, reset ordering passed, passive logger coexistence passed, output schema/isolation passed, and diagnostics-only monitors did not alter behavior.

No training was run. No short training smoke was run. No performance conclusion was made. No commit was made.

## Recommended Next Phase

Recommended next phase:

```text
Phase 9G-7F:
commit-readiness review for Phase 9G-7A through Phase 9G-7E
```

Phase 9G-7F should not rerun runtime episodes unless a specific inconsistency is found. It should review changed source/scripts/docs, generated artifacts to exclude, default-off guarantees, validation evidence, and the exact manual staging list.
