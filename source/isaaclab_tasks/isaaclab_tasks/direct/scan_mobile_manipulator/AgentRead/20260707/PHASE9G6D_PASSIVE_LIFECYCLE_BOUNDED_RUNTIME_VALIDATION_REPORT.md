# Phase 9G-6D Passive Lifecycle Bounded Runtime Validation Report

Date: 2026-07-07

## Scope

Phase 9G-6D performed bounded runtime validation of the Phase 9G-6B/6C passive shared lifecycle diagnostics.

Allowed runtime work was limited to:

- short RL playback diagnostics runs;
- short current comparison-method evaluation runs;
- offline parsing, identity comparison, schema validation, and event-consistency checks.

No training was run. No short training smoke was run. No policy checkpoint was modified. No assignment/action/mask/observation/reward/controller/env/HARL/solver behavior changed.

## Files Inspected

- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/AGENTS.md`
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md`
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260707/PHASE9G6A_ACTIVE_TASK_LIFECYCLE_TRANSITION_INTERFACE_AUDIT.md`
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260707/PHASE9G6B_PASSIVE_SHARED_LIFECYCLE_TRANSITION_LOGGER_REPORT.md`
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260707/PHASE9G6C_PASSIVE_LIFECYCLE_RUNTIME_INTEGRATION_REPORT.md`
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_lifecycle.py`
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_lifecycle_diagnostics.py`
- `scripts/environments/evaluate_assignment_rl_playback_diagnostics.py`
- `scripts/environments/evaluate_assignment_methods.py`
- `scripts/environments/test_assignment_lifecycle_transition_logger_smoke.py`
- `scripts/environments/test_assignment_lifecycle_runtime_integration_smoke.py`
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260706/PHASE9G3_FAILED_PAIR_MEMORY_PLAYBACK_VALIDATION_REPORT.md`
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260706/PHASE9G4B_FAILED_PAIR_MEMORY_D6_PLAYBACK_VALIDATION_REPORT.md`
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260705/PHASE9F5_REDIRECT_GUARDRAIL_PLAYBACK_VALIDATION_REPORT.md`

## Files Created

- `scripts/environments/analyze_phase9g6d_lifecycle_runtime_validation.py`
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260707/PHASE9G6D_PASSIVE_LIFECYCLE_BOUNDED_RUNTIME_VALIDATION_REPORT.md`
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260707/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G6D_PASSIVE_LIFECYCLE_BOUNDED_RUNTIME_VALIDATION_20260707.md`

Generated runtime/analysis outputs:

- `results/assignment_diagnostics/phase9g6d_lifecycle_runtime_validation/rl_disabled/`
- `results/assignment_diagnostics/phase9g6d_lifecycle_runtime_validation/rl_enabled/`
- `results/assignment_diagnostics/phase9g6d_lifecycle_runtime_validation/nearest_disabled/`
- `results/assignment_diagnostics/phase9g6d_lifecycle_runtime_validation/nearest_enabled/`
- `results/assignment_diagnostics/phase9g6d_lifecycle_runtime_validation/random_enabled/`
- `results/assignment_diagnostics/phase9g6d_lifecycle_runtime_validation/greedy_enabled/`
- `results/assignment_diagnostics/phase9g6d_lifecycle_runtime_validation/comparison/phase9g6d_identity_comparison.csv`
- `results/assignment_diagnostics/phase9g6d_lifecycle_runtime_validation/comparison/phase9g6d_runtime_schema_summary.json`
- `results/assignment_diagnostics/phase9g6d_lifecycle_runtime_validation/comparison/phase9g6d_event_consistency.json`
- `results/assignment_diagnostics/phase9g6d_lifecycle_runtime_validation/comparison/phase9g6d_validation_summary.json`

## Files Updated

- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md`

No runtime behavior file was changed in Phase 9G-6D. The only Python source added in this phase is the offline analyzer.

## Checkpoint / Scenario / Seed

Checkpoint:

```text
results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/assignment_happo_n50_phase9e4a_budget_m15_slack5_d5_train_100k/seed-00001-2026-07-01-14-40-47/models
```

Scenario:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh_assignment_cooldown_budget_m15_slack5_d5_redirect_guardrail.yaml
```

Runtime settings:

```text
num_envs = 1
num_episodes = 1
max_steps = 300
seed = 1
device = cuda:0
headless = true
stop_on_done = true for RL playback
```

## Runtime Commands

### RL disabled

```powershell
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/evaluate_assignment_rl_playback_diagnostics.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --algorithm happo --assignment_rl --num_envs 1 --headless --device cuda:0 --scenario_config source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh_assignment_cooldown_budget_m15_slack5_d5_redirect_guardrail.yaml --dir results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/assignment_happo_n50_phase9e4a_budget_m15_slack5_d5_train_100k/seed-00001-2026-07-01-14-40-47/models --num_episodes 1 --max_steps 300 --seed 1 --output_dir results/assignment_diagnostics/phase9g6d_lifecycle_runtime_validation/rl_disabled --stop_on_done
```

### RL enabled

```powershell
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/evaluate_assignment_rl_playback_diagnostics.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --algorithm happo --assignment_rl --num_envs 1 --headless --device cuda:0 --scenario_config source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh_assignment_cooldown_budget_m15_slack5_d5_redirect_guardrail.yaml --dir results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/assignment_happo_n50_phase9e4a_budget_m15_slack5_d5_train_100k/seed-00001-2026-07-01-14-40-47/models --num_episodes 1 --max_steps 300 --seed 1 --output_dir results/assignment_diagnostics/phase9g6d_lifecycle_runtime_validation/rl_enabled --stop_on_done --log_assignment_lifecycle --assignment_lifecycle_output_dir results/assignment_diagnostics/phase9g6d_lifecycle_runtime_validation/rl_enabled/lifecycle
```

### Nearest disabled

```powershell
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/evaluate_assignment_methods.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --methods nearest --num_envs 1 --num_episodes 1 --max_steps 300 --seed 1 --headless --device cuda:0 --scenario_config source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh_assignment_cooldown_budget_m15_slack5_d5_redirect_guardrail.yaml --output_dir results/assignment_diagnostics/phase9g6d_lifecycle_runtime_validation/nearest_disabled
```

### Nearest enabled

```powershell
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/evaluate_assignment_methods.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --methods nearest --num_envs 1 --num_episodes 1 --max_steps 300 --seed 1 --headless --device cuda:0 --scenario_config source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh_assignment_cooldown_budget_m15_slack5_d5_redirect_guardrail.yaml --output_dir results/assignment_diagnostics/phase9g6d_lifecycle_runtime_validation/nearest_enabled --log_assignment_lifecycle --assignment_lifecycle_output_dir results/assignment_diagnostics/phase9g6d_lifecycle_runtime_validation/nearest_enabled/lifecycle
```

### Random enabled

```powershell
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/evaluate_assignment_methods.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --methods random --num_envs 1 --num_episodes 1 --max_steps 300 --seed 1 --headless --device cuda:0 --scenario_config source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh_assignment_cooldown_budget_m15_slack5_d5_redirect_guardrail.yaml --output_dir results/assignment_diagnostics/phase9g6d_lifecycle_runtime_validation/random_enabled --log_assignment_lifecycle --assignment_lifecycle_output_dir results/assignment_diagnostics/phase9g6d_lifecycle_runtime_validation/random_enabled/lifecycle
```

### Greedy enabled

```powershell
conda run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/evaluate_assignment_methods.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --methods greedy --num_envs 1 --num_episodes 1 --max_steps 300 --seed 1 --headless --device cuda:0 --scenario_config source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh_assignment_cooldown_budget_m15_slack5_d5_redirect_guardrail.yaml --output_dir results/assignment_diagnostics/phase9g6d_lifecycle_runtime_validation/greedy_enabled --log_assignment_lifecycle --assignment_lifecycle_output_dir results/assignment_diagnostics/phase9g6d_lifecycle_runtime_validation/greedy_enabled/lifecycle
```

## Offline Analyzer Command

```powershell
conda run -p C:\isaacenvs\isaac45_harl python scripts/environments/analyze_phase9g6d_lifecycle_runtime_validation.py --root results/assignment_diagnostics/phase9g6d_lifecycle_runtime_validation --output_dir results/assignment_diagnostics/phase9g6d_lifecycle_runtime_validation/comparison
```

The first analyzer run exposed only an analyzer comparator bug: it compared a sorted runtime event key set against an unsorted expected field list. The helper was corrected to compare sorted field sets. This fix is offline validation-only and does not affect runtime diagnostics or assignment behavior.

## Output Isolation

Lifecycle outputs were isolated:

```text
rl_enabled/lifecycle/assignment_lifecycle_events.jsonl
rl_enabled/lifecycle/assignment_lifecycle_summary.json
nearest_enabled/lifecycle/nearest/assignment_lifecycle_events.jsonl
nearest_enabled/lifecycle/nearest/assignment_lifecycle_summary.json
random_enabled/lifecycle/random/assignment_lifecycle_events.jsonl
random_enabled/lifecycle/random/assignment_lifecycle_summary.json
greedy_enabled/lifecycle/greedy/assignment_lifecycle_events.jsonl
greedy_enabled/lifecycle/greedy/assignment_lifecycle_summary.json
```

Result:

```text
output_isolation_ok = true
```

The comparison-method script writes method-specific lifecycle subdirectories under the requested lifecycle root. No method overwrote another method's lifecycle files.

## Identity Results

Identity artifacts:

```text
results/assignment_diagnostics/phase9g6d_lifecycle_runtime_validation/comparison/phase9g6d_identity_comparison.csv
```

| comparison | assignment_history same hash | rows | per_episode same hash | summary same hash | final coverage disabled/enabled | coverage AUC disabled/enabled | episode length disabled/enabled | noop rate disabled/enabled | budget triggers disabled/enabled |
| --- | --- | ---: | --- | --- | --- | --- | --- | --- | --- |
| RL enabled vs disabled | true | 897 / 897 | true | true | 0.5 / 0.5 | 0.33043458868428616 / 0.33043458868428616 | 299.0 / 299.0 | 0.0 / 0.0 | 6.0 / 6.0 |
| nearest enabled vs disabled | true | 897 / 897 | true | true | 0.88 / 0.88 | 0.7301014065742493 / 0.7301014065742493 | 299 / 299 | 0.0 / 0.0 | n/a |

Result:

```text
RL identity: PASS
nearest identity: PASS
```

Enabled lifecycle diagnostics did not change assignment histories, per-episode records, summaries, coverage, coverage AUC, episode length, noop rate, or budget trigger count for the deterministic identity pairs.

## Runtime Lifecycle Summary Table

Source:

```text
results/assignment_diagnostics/phase9g6d_lifecycle_runtime_validation/comparison/phase9g6d_runtime_schema_summary.json
```

| run | events | steps observed | started | continued | switch | completed | active became covered | budget | release | exact conflict | reset | invalid | behavior changed |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| rl_enabled | 962 | 299 | 27 | 819 | 51 | 17 | 8 | 6 | 6 | 22 | 6 | 0 | false |
| nearest_enabled | 947 | 299 | 42 | 854 | 1 | 39 | 5 | 0 | 0 | 0 | 6 | 0 | false |
| random_enabled | 903 | 299 | 3 | 20 | 874 | 0 | 0 | 0 | 0 | 0 | 6 | 0 | false |
| greedy_enabled | 947 | 299 | 42 | 854 | 1 | 39 | 5 | 0 | 0 | 0 | 6 | 0 | false |

All summaries used:

```text
schema_version = phase9g6c_assignment_lifecycle_diagnostics_v1
num_envs = 1
num_robots = 3
num_tasks = 50
```

## Cross-Method Schema Result

Result:

```text
schema_ok = true
event_field_set_count = 1
summary_key_set_count = 1
behavior_changed = false for every event and summary
invalid_assignment_proposal_proxy_count = 0 for every enabled run
```

RL/HAPPO, nearest, random, and greedy lifecycle outputs share the same event and summary schema. Method names differ only as metadata.

Future method compatibility remains interface-level in this phase; no `future_sota_placeholder` runtime run was performed because no real future-method adapter exists yet. Phase 9G-6C smoke coverage remains the validation point for arbitrary method names.

## Completion Consistency

Source:

```text
results/assignment_diagnostics/phase9g6d_lifecycle_runtime_validation/comparison/phase9g6d_event_consistency.json
```

| run | newly covered targets | lifecycle completion events | consistent |
| --- | ---: | ---: | --- |
| rl_enabled | 25 | 25 | true |
| nearest_enabled | 44 | 44 | true |
| random_enabled | 0 | 0 | true |
| greedy_enabled | 44 | 44 | true |

Lifecycle completion event count is:

```text
target_completed_proxy_count
+ target_completed_by_teammate_proxy_count
+ active_target_became_covered_proxy_count
```

The runtime path did not fabricate teammate attribution. `target_completed_by_teammate_proxy_count` was 0 in these bounded runs.

## Budget / Release Consistency

RL enabled:

```text
budget_history_count = 6
budget_lifecycle_event_count = 6
budget_pair_identity_consistent = true
release_proxy_count = 6
release_matches_budget_count = true
```

The six RL budget failure proxy events aligned with wrapper history by env id, logger step, robot id, and target id. The comparison-method runs did not supply budget trigger diagnostics, so their budget and release counts were correctly 0.

## Reset Ordering

Result:

```text
reset_order_ok = true for all enabled runs
```

The logger emits initial reset events at logger step 0 before the first proposal. Non-initial reset events occur after final post-step transition evidence for the done env. No final transition was reconstructed from a reset problem.

## Exact Conflict Findings

RL enabled:

```text
exact_claim_conflict_proxy_count = 22
hypothetical_conflict_loser_count = 22
exact_conflict_passive = true
behavior_changed = false
```

Nearest, random, and greedy had zero exact conflict events in this bounded matrix. No run applied hypothetical arbitration, changed proposals, changed env actions, or modified masks.

## Invalid / Unavailable Proposal Findings

All enabled runs:

```text
invalid_assignment_proposal_proxy_count = 0
unavailable_target_proposal_proxy_count = 0
```

No raw HARL noop id reached the logger in the RL enabled run.

## Behavior Changed Validation

All enabled lifecycle event files and summaries report:

```text
behavior_changed = false
```

Exact enabled/disabled identity checks show that lifecycle diagnostics did not alter deterministic RL or nearest outputs.

## Validation Commands And Results

Syntax and smoke validation:

```powershell
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_lifecycle.py
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_lifecycle_diagnostics.py
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/test_assignment_lifecycle_transition_logger_smoke.py
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/test_assignment_lifecycle_runtime_integration_smoke.py
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/evaluate_assignment_rl_playback_diagnostics.py
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/evaluate_assignment_methods.py
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/analyze_phase9g6d_lifecycle_runtime_validation.py
conda run -p C:\isaacenvs\isaac45_harl python scripts/environments/test_assignment_lifecycle_transition_logger_smoke.py
conda run -p C:\isaacenvs\isaac45_harl python scripts/environments/test_assignment_lifecycle_runtime_integration_smoke.py
```

Results:

```text
all py_compile commands: PASS
test_assignment_lifecycle_transition_logger_smoke.py: PASS
test_assignment_lifecycle_runtime_integration_smoke.py: PASS
analyze_phase9g6d_lifecycle_runtime_validation.py: PASS after offline comparator fix
```

Final repository checks:

```powershell
git diff --check
git status --short --untracked-files=all
```

Results:

```text
git diff --check: PASS, with LF-to-CRLF warnings only
git status --short --untracked-files=all: completed
```

## Explicit Non-Changes

Phase 9G-6D did not change:

- assignment proposals;
- decoded assignments;
- effective assignments;
- action ids;
- action semantics;
- available actions;
- available masks;
- observations;
- rewards;
- controller commands;
- env actions;
- env dynamics;
- task completion behavior;
- HARL code or behavior;
- random, nearest, greedy, or other solver behavior;
- scenario YAML;
- cooldown behavior;
- redirect guardrail behavior;
- failed-pair memory behavior;
- policy checkpoints.

No training was run. No short training smoke was run.

## Conclusion

```text
PASS
```

Phase 9G-6D validated that passive lifecycle diagnostics can run in bounded real runtime paths for RL playback and current comparison methods while remaining behavior-neutral.

## Recommendation

Recommended next phase:

```text
Phase 9G-6E: commit-readiness review for the complete Phase 9G-6 block.
```

Phase 9G-6E should review:

- Phase 9G-6A interface audit;
- Phase 9G-6B passive logger;
- Phase 9G-6C runtime integration;
- Phase 9G-6D bounded runtime validation;
- changed source/scripts/docs;
- generated result artifacts to include or exclude;
- default-off guarantees;
- behavior-neutral evidence;
- test coverage;
- final `git status` before the user manually commits.

Do not automatically commit.

