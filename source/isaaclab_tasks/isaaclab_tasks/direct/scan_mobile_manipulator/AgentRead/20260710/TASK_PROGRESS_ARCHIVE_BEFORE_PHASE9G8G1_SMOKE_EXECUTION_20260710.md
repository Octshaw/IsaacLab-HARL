# TASK_PROGRESS

Compact handoff for assignment-based scan-mobile-manipulator lifecycle training.

## Current Status

Phase 9G-8G-0 completed the design and static preflight for the first
resolver-enabled `lifecycle_contract_c` controlled training smoke.

Classification:

```text
SMOKE-PLAN-READY
```

The reviewed Phase 9G-8 implementation was committed before this design phase:

```text
8a5f46cb feat(assignment): complete lifecycle training checkpoint readiness
```

No training or environment process ran in Phase 9G-8G-0.

## Frozen Smoke Plan

```text
fresh start; no --dir
profile: lifecycle_contract_c
algorithm/state: HAPPO / EP
policy: feed-forward; both recurrent flags false
share_param: false
checkpoint: state_dict; save_entire_model false
M=3 robots; N=50 viewpoints
num_envs: 1
HARL episode_length: 300
num_env_steps: 300
completed rollout/update cycles: 1
log_interval: 1
save_interval: 1
seed: 1
headless CUDA 0
video/evaluation: disabled
```

Installed HARL calculation:

```text
episodes = floor(300 / 300 / 1) = 1
actor/critic feed-forward batch = 300
actor and critic minibatches = 2, size 150 each
```

Expected native save order:

```text
best_model generation 0
models regular generation 1
models explicit final generation 2
```

## Experiment Name

```text
assignment_happo_n50_phase9g8g1_controlled_lifecycle_contract_c_smoke_fresh
```

Expected result pattern:

```text
results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/
assignment_happo_n50_phase9g8g1_controlled_lifecycle_contract_c_smoke_fresh/
seed-00001-*/
```

The semantic experiment parent did not exist during preflight. Recheck before
execution; never overwrite or delete a prior run.

## Latest Verification

```text
clean committed baseline confirmed: PASS
Python interpreter under C:\isaacenvs\isaac45_harl: PASS
scenario/config/data path checks: PASS
N=50 CSV and M=3 robot config checks: PASS
installed HARL update/minibatch/save formulas inspected: PASS
experiment-name collision check: PASS, absent
git diff --check before documentation edits: PASS
TASK_PROGRESS archive matches committed pre-edit handoff: PASS
final documentation git diff --check: PASS, line-ending warning only
```

## Telemetry Boundary

Existing logs expose environment/reward, assignment/noop, cooldown budget,
HAPPO loss/entropy/gradient norm/ratio, and VCritic loss/gradient norm/reward
metrics.

Raw observations, raw critic values, and per-event resolver rows are not
persisted by the current training logger. Their health is inferred from the
active contract, runtime assertions, successful finite update path, and available
logged statistics. Do not claim exhaustive resolver or raw-tensor telemetry.

## Prohibited

Until the first smoke result is reviewed, do not run:

```text
general or long resolver-enabled training
multiple seeds
playback or evaluation
checkpoint continuation or loading
performance comparisons
recurrent, FP, share_param=true, HATRPO, or HAA2C lifecycle training
```

Do not modify installed HARL or the Conda environment.

## Next Step

The next phase may execute exactly one bounded fresh-start smoke using the
reviewed command in the Phase 9G-8G-0 report, then stop for result review.

Expected successful stop:

```text
configured 300 steps reached
one actor/critic update completed
explicit final checkpoint save completed
process exit code 0
```

General or long resolver-enabled training remains prohibited until that result is
reviewed.

## Phase 9G-8G-0 Non-Execution Confirmation

```text
training: no
AppLauncher / Isaac Sim: no
assignment environment construction/reset/step: no
checkpoint creation/load: no
playback/evaluation: no
production/test/YAML behavior modification: no
installed HARL/Conda modification: no
commit: no
```

## Detailed Reports / Archives

```text
AgentRead/20260710/PHASE9G8G0_CONTROLLED_TRAINING_SMOKE_DESIGN_AND_PREFLIGHT.md
AgentRead/20260710/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G8G0_SMOKE_DESIGN_20260710.md
AgentRead/20260710/PHASE9G8F6R_CONTROLLED_TRAINING_GATE_ACTIVATION_AND_REVIEW_CLOSURE.md
AgentRead/20260709/PHASE9G8F5_CHECKPOINT_SAVE_LOAD_CONTINUATION_SMOKE_REPORT.md
AgentRead/20260709/PHASE9G8F4_ACTOR_CRITIC_BUFFER_FORWARD_BACKWARD_READINESS_REPORT.md
```
