# TASK_PROGRESS

## Current Status

Phase 9G-8I-3-0R-1 implemented the frozen controlled initial-condition
variation interface and completed pure/fake/static regression.

Classification:

~~~text
RUNTIME-IDENTITY-VALIDATION-READY
~~~

Starting committed baseline:

~~~text
167bafaac84f7f8f527af40ed786e4834a7db704
167bafaa docs(assignment): validate 100k best-final attribution comparison
~~~

The user intentionally left the Phase 9G-8I-3-0 and 9G-8I-3-0R documentation
uncommitted before this implementation. Those files remain preserved.

## Latest Completed Phase

The playback-only interface supports exactly:

~~~text
baseline_identity:
  robot_0->S0, robot_1->S1, robot_2->S2

pose_cycle_forward:
  robot_0->S1, robot_1->S2, robot_2->S0

pose_cycle_reverse:
  robot_0->S2, robot_1->S0, robot_2->S1
~~~

The default selector is `None`. Explicit profiles require attribution logging
and a new/empty output directory. They preserve robot identities, capabilities,
scanner offsets, actor mapping, component, ordered N=50 viewpoints, lifecycle
behavior, policy dimensions, and checkpoint compatibility.

Implemented condition schemas:

~~~text
assignment_initial_condition_contract_v1
assignment_initial_condition_manifest_v1
~~~

The condition SHA-256 is independent of checkpoint/run provenance. Successful
explicit-profile attribution adds one atomic
`assignment_initial_condition_manifest.json`; no-selector output remains the
historical exact three-file contract.

## Files

Created:

- `assignment_initial_condition.py`
- `scripts/environments/test_assignment_initial_condition_contract.py`
- `AgentRead/20260721/PHASE9G8I30R1_CONTROLLED_INITIAL_CONDITION_INTERFACE_IMPLEMENTATION_AND_REGRESSION.md`
- `AgentRead/20260721/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G8I30R1_INITIAL_CONDITION_IMPLEMENTATION_20260721.md`

Modified:

- `scripts/reinforcement_learning/harl/play_assignment.py`
- `scripts/reinforcement_learning/harl/train.py`
- `scan_mobile_manipulator_env.py`
- `AgentRead/TASK_PROGRESS.md`

No YAML/data, wrapper, attribution collector, checkpoint module, reward,
resolver, mask, controller, installed HARL, or Conda file changed.

## Active Architecture

~~~text
playback CLI choice (default None)
-> post-scenario immutable request
-> robot/component/diagnostic/viewpoint preparation
-> strict pure condition resolution and five-file hash validation
-> replace only cfg.base_start_poses
-> DirectMARLEnv construction
-> wrapper identity/interface validation
-> unchanged checkpoint loader
-> unchanged attribution collector
-> explicit-profile fourth manifest after three-file finalization
~~~

Training has no profile CLI. A low-level profile/request hard-fails before
runner registration/construction and environment construction.

## Verification

~~~text
new initial-condition tests:               PASS 8/8
playback attribution diagnostics:          PASS 16/16
checkpoint contract core:                  PASS 28/28
lifecycle observation integration:         PASS 6/6
lifecycle mask/HARL replay:                 PASS 11/11
viewpoint CSV loader:                       PASS
scenario/robot pure load:                   PASS
py_compile (five changed/new Python files): PASS
git diff --check:                           PASS (line-ending warning only)
forbidden production/YAML paths unchanged: PASS
~~~

No Isaac Lab runtime import was needed by the new suite.

## Known Limitations

Static readiness does not establish physical or behavioral validity for the B/C
pose permutations. Initial/reset tensors, finite observations, immediate
diagnostics, deterministic repeatability, and meaningful trajectory difference
remain runtime-deferred.

The contract is deliberately fixed to M=3, N=50, the current five source hashes,
and the lifecycle Contract C HAPPO/EP/feed-forward interface.

## Do Not Do

Do not run a best/final multi-condition comparison, new seed, training,
checkpoint continuation, GUI/video, or 300k continuation. Do not modify the
profile mappings, coordinates, task files, reward, resolver, mask, controller,
or checkpoint semantics.

## Next Step

After review and explicit acceptance only:

~~~text
Phase 9G-8I-3-0R-2:
Controlled Initial-Condition Runtime Identity Validation
~~~

R-2 may perform only the separately reviewed bounded runtime identity checks.
No runtime validation was started in R-1.

## Detailed Reports / Archives

- `AgentRead/20260721/PHASE9G8I30R1_CONTROLLED_INITIAL_CONDITION_INTERFACE_IMPLEMENTATION_AND_REGRESSION.md`
- `AgentRead/20260721/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G8I30R1_INITIAL_CONDITION_IMPLEMENTATION_20260721.md`
- `AgentRead/20260721/PHASE9G8I30R_CONTROLLED_INITIAL_CONDITION_VARIATION_INTERFACE_AND_CONTRACT_DESIGN.md`
- `AgentRead/20260721/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G8I30R_INITIAL_CONDITION_CONTRACT_DESIGN_20260721.md`
- `AgentRead/20260721/PHASE9G8I30_BEST_FINAL_ROBUSTNESS_AND_LATE_TRAINING_REGRESSION_DIAGNOSIS_DESIGN.md`
- `AgentRead/20260721/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G8I30_ROBUSTNESS_DIAGNOSIS_DESIGN_20260721.md`
- `AgentRead/20260720/PHASE9G8I21_SEQUENTIAL_BEST_FINAL_BOUNDED_ATTRIBUTION_PLAYBACK_EXECUTION_AND_COMPARISON.md`
