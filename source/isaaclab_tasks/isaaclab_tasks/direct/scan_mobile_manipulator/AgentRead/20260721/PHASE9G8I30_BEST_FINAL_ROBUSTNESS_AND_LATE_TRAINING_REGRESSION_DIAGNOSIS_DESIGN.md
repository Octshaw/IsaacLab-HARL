# Phase 9G-8I-3-0: Best/Final Robustness And Late-Training Regression Diagnosis Design

Date: 2026-07-21

## 1. Classification

~~~text
NOT READY
~~~

The repository and retained evidence pass static preflight, but the required
robustness experiment cannot be frozen under the current runtime contract.

The decisive blocker is:

~~~text
seed classification:
  SEED-INEFFECTIVE

currently supported same-contract initial-condition variation:
  none
~~~

`--seed 1`, `--seed 2`, and `--seed 3` reseed global random-number generators,
but the frozen assignment scenario consumes no relevant randomness during
environment construction, reset, lifecycle reset, masking, controller execution,
or deterministic policy action selection. Four seed-2/seed-3 playbacks would
therefore not be four controlled trajectory variations.

Per the phase boundary, no seed set, output path, log path, or command is frozen,
and Phase 9G-8I-3-1 is not authorized.

## 2. Starting Repository Preflight

~~~text
HEAD:
  167bafaac84f7f8f527af40ed786e4834a7db704

git log -1 --oneline:
  167bafaa docs(assignment): validate 100k best-final attribution comparison

git status --short --untracked-files=all:
  clean

git diff --name-status:
  empty

git diff --check:
  PASS
~~~

The accepted Phase 9G-8I-1, 9G-8I-2-0, and 9G-8I-2-1 documentation chain is
committed. No unrelated production, test, YAML, result, or documentation change
was present at the start of this phase.

## 3. Accepted Phase 9G-8I-2-1 Evidence

Accepted technical classification:

~~~text
BEST-FINAL-ATTRIBUTION-COMPARISON-COMPLETE
~~~

Accepted behavioral result:

~~~text
Mixed Outcome A1 + Outcome A3

A1:
  both 100k checkpoints remove the one-update deterministic noop collapse

A3:
  best_model is healthier than final models on completion distribution,
  budget burden, coverage, and robot_1/robot_2 progress quality

bounded checkpoint preference:
  prefer best_model
~~~

| Metric | One update | Best | Final |
| --- | ---: | ---: | ---: |
| Proposal noops `[r0,r1,r2]` | `[300,0,248]` | `[0,0,0]` | `[0,0,0]` |
| Executing steps `[r0,r1,r2]` | `[0,300,61]` | `[300,300,300]` | `[300,300,300]` |
| Completions `[r0,r1,r2]` | `[0,5,2]` | `[6,8,6]` | `[12,5,3]` |
| Total completions | 7 | 20 | 20 |
| First-episode coverage | 0.36 | 0.70 | 0.68 |
| Budget releases | 2 | 1 | 4 |
| Jain completion fairness | 0.5632 | 0.9804 | 0.7491 |
| Resolver rejections | 0 | 0 | 0 |

For robots 1 and 2 combined, zero-base-motion executing rows increased from 37
to 158 and zero target-distance-progress rows increased from 0 to 118 in final.
This remains accepted one-trajectory evidence. This phase does not reinterpret
it as a robust regression.

## 4. Authorities And Evidence Inspected

Read completely:

~~~text
AgentRead/AGENTS.md
AgentRead/TASK_PROGRESS.md
AgentRead/20260720/PHASE9G8I1_FRESH_100K_CONTROLLED_TRAINING_EXECUTION_AND_OFFLINE_AUDIT_REVIEW.md
AgentRead/20260720/PHASE9G8I20_BEST_VS_FINAL_PROPOSAL_EFFECTIVE_ATTRIBUTION_COMPARISON_DESIGN.md
AgentRead/20260720/PHASE9G8I21_SEQUENTIAL_BEST_FINAL_BOUNDED_ATTRIBUTION_PLAYBACK_EXECUTION_AND_COMPARISON.md
AgentRead/20260720/PHASE9G8H2_BOUNDED_PROPOSAL_EFFECTIVE_ATTRIBUTION_PLAYBACK_REPORT.md
~~~

Inspected statically:

~~~text
scripts/reinforcement_learning/harl/play_assignment.py
scripts/reinforcement_learning/harl/train.py
scenario_config.py
scan_mobile_manipulator_env.py
assignment_harl_wrapper.py
assignment_lifecycle_resolver.py
assignment_lifecycle_resolver_runtime.py
assignment_harl_training.py
assignment_checkpoint_save.py
source/isaaclab/isaaclab/envs/direct_marl_env.py
source/isaaclab/isaaclab/envs/direct_marl_env_cfg.py

configs/scenarios/algorithm_proxy_component_mesh.yaml
configs/scenarios/algorithm_proxy_bbox.yaml
configs/robots/robots_real_proxy.yaml
configs/robots/robots_three_proxy.yaml
configs/viewpoints/component_mesh_jittered_n50.csv

installed HARL on_policy_base_runner.py
installed HARL ACTLayer, StochasticPolicy, OnPolicyBase, seed, and device utilities
installed Isaac Sim torch seed utility
~~~

Read-only retained evidence:

~~~text
the 100k configs.json
the TensorBoard event file and scalar tags
best_model and models contract/training-state JSON metadata
the complete 100k result-tree inventory
trainData.zip member names
the accepted best/final attribution CSV and JSON files
~~~

No actor, critic, or ValueNorm tensor was deserialized. No checkpoint loader was
called.

## 5. Evaluation Seed Propagation Trace

### 5.1 CLI To Environment

The exact path is:

~~~text
play_assignment.py:66
  --seed parsed as int or None

play_assignment.py:394-396
  env_cfg.scene.num_envs = args_cli.num_envs
  env_cfg.seed = args_cli.seed when supplied

play_assignment.py:397-399
  scenario settings are applied after the seed assignment;
  the scenario does not replace seed

play_assignment.py:404
  make_assignment_harl_env(..., cfg=env_cfg)

DirectMARLEnv.__init__:86-90
  self.seed(cfg.seed) before simulation construction

DirectMARLEnv.seed:449-457
  Replicator global seed
  Isaac Sim torch_utils.set_seed(seed)

play_assignment.py:433-434
  wrapper.reset(seed=args_cli.seed)

DirectMARLEnv.reset:313-319
  self.seed(seed) again, then _reset_idx(all envs)
~~~

Isaac Sim `torch_utils.set_seed` changes:

~~~text
Python random state
NumPy random state
PyTorch CPU seed
PyTorch CUDA seed and all-device CUDA seeds
PYTHONHASHSEED environment variable
Warp random state
cuDNN benchmark/deterministic settings at that call site
~~~

`DirectMARLEnv.seed` also changes the Replicator global seed. The playback entry
does not call HARL's training `set_seed(args)` directly; the Isaac Lab seed path
nonetheless seeds Python, NumPy, PyTorch CPU/CUDA, and Warp. Later HARL
`init_device` applies the configured cuDNN deterministic flags.

### 5.2 Policy Determinism

The action path is:

~~~text
play_assignment.py actor.act(..., deterministic=True)
  -> OnPolicyBase.act
  -> StochasticPolicy.forward
  -> ACTLayer.forward
  -> masked Categorical.mode()
~~~

The selected action is an argmax/mode, not a sample. The following
`evaluate_actions` call computes the probability of that already selected action
and does not resample it.

Actor modules are instantiated after environment seeding, so their temporary
pre-load initialization can differ by seed. Normal evaluation then strictly
loads every actor state-dict parameter from the checkpoint. The temporary random
initialization is not a trajectory variable after a successful load.

### 5.3 Environment And Reset Determinism

The active `ScanMobileManipulatorEnvCfg` is a task-space tensor skeleton. The
retained `configs.json` records:

~~~text
events = None
observation_noise_model = None
action_noise_model = None
seed = 1
~~~

Static source search found no `torch.rand`, `torch.randn`, `np.random`, Python
`random`, `randperm`, multinomial, or sampling call in the environment, wrapper,
resolver, or resolver runtime used by this path.

`ScanMobileManipulatorEnv._reset_idx` deterministically:

~~~text
copies base_start_poses into every reset environment
copies base yaw from the same poses
sets scanner position to base position plus fixed scanner offsets
sets scanner quaternion to [1,0,0,0]
clears coverage and dwell counters
clears reward bookkeeping
zeros current and previous actions
~~~

The wrapper then deterministically clears assignment diagnostics and budget
state, resets the lifecycle resolver, advances episode metadata, captures the
new lifecycle snapshot, and builds observations/masks.

The scenario loads fixed artifacts:

~~~text
robots:
  robots_real_proxy.yaml
  fixed poses [-4,-2], [0,3.5], [4,-2]

viewpoints:
  component_mesh_jittered_n50.csv
  fixed persisted order and ids 0..49

component/capabilities:
  fixed mesh, proxy, capability profiles, tolerances, and step scales
~~~

The word `jittered` describes how the CSV was generated offline. Playback reads
the persisted CSV and does not regenerate or shuffle it from `--seed`.

The accepted best and final CSVs provide supporting, not substitute, evidence:
after the automatic reset, episode-1 decision 1 selected exactly the same three
actions as episode-0 decision 1 for each checkpoint.

## 6. Seed Meaningfulness Decision

~~~text
SEED-INEFFECTIVE
~~~

What changes with `--seed`:

~~~text
env_cfg.seed and seed diagnostics
Python/NumPy/PyTorch/Warp/Replicator RNG states
temporary actor initialization before strict checkpoint loading
~~~

What remains fixed for the relevant trajectory:

~~~text
checkpoint actor weights after loading
deterministic masked mode action semantics
robot count, identities, capabilities, poses, yaw, and scanner offsets
component geometry and proxy
all 50 viewpoint poses, identities, and ordering
coverage, dwell, action, resolver, ownership, pair, and budget reset state
feasibility and availability construction
controller equations and task-space state transitions
episode length and lifecycle Contract C
~~~

Changing an unused RNG state does not constitute a controlled initial-condition
variation. Any residual low-level device nondeterminism would be uncontrolled
implementation noise, not a seed-defined experiment axis.

Therefore seeds 1, 2, and 3 are not frozen as a robustness set.

## 7. Supported Initial-Condition Variation Audit

| Candidate | Current source support | Same frozen contract? | Decision |
| --- | --- | --- | --- |
| Change `--seed` | CLI supported | Yes, but no relevant random consumer | Ineffective |
| Run another episode | Supported | Yes | Reset recreates the same state |
| Increase `--num_envs` | Supported | No, frozen E is 1; clones receive broadcast fixed state | Not a controlled variation |
| Use stochastic actions | Not the requested initial-state axis | No | Prohibited and confounds policy sampling |
| Use `algorithm_proxy_bbox.yaml` | Scenario selectable | No, component/viewpoint task changes | Not an initial-condition-only comparison |
| Use `robots_three_proxy.yaml` | File exists | No active scenario/CLI selection path under the frozen component-mesh command | Requires a reviewed config/interface change |
| Depend on GPU nondeterminism | Not controlled | No | Invalid diagnostic design |

All existing component-mesh scenarios select `robots_real_proxy.yaml`. The play
parser does not expose `robot_config_path`, base poses, viewpoint ordering, or a
reset-randomization profile as a validated CLI option. In addition,
`apply_scenario_config_to_env_cfg` applies the scenario's robot/viewpoint paths
after Hydra configuration construction, so an ordinary low-level override does
not establish an accepted same-contract variation boundary.

No currently supported non-source-modifying, same-contract controlled
initial-condition variation was found. This directly requires `NOT READY` under
the user-provided classification rule.

## 8. Exact Best-Checkpoint Selection

### 8.1 Metric

The assignment runner installs `AssignmentIsaacLabLogger` with the exact
whitelist:

~~~text
ASSIGNMENT_REWARD_ACCUMULATOR_KEYS = {
  "assignment_rl_reward/final_reward_mean"
}
~~~

At each environment step, `_flatten_assignment_reward_log` converts the
`final_reward` tensor to one scalar by taking its mean. For the retained run,
`E=1` and `M=3`, so this is the mean over the three agent rewards. At the end of
each 300-step rollout, `_compute_reward_accumulator_total` sums those 300 scalar
means:

~~~text
Total_Reward(rollout q) =
  sum over t=1..300 of
    mean over envs and robots of final_reward[q,t]
~~~

Higher is preferred.

`final_reward` is:

~~~text
base environment reward
+ repeated-same-target/no-global-gain adjustment
+ global-no-coverage-progress adjustment
+ selected-path-cost adjustment
~~~

The base environment reward includes global coverage gain, own coverage gain,
duplicate scans, reach violation, action-rate change, and elapsed-time cost. The
retained run configured selected-path-cost penalty scale to `0.0`.

### 8.2 Selection Algorithm And Timing

Installed `OnPolicyBaseRunner.run` performs, for every rollout:

~~~text
collect 300 steps
compute returns
train actors and critic
episode_log when episode % log_interval == 0

if logger.total_reward > best_avg_reward:
    best_avg_reward = logger.total_reward
    save(run_root / "best_model")

if episode % eval_interval == 0:
    run eval only when use_eval is true
    save(run_root / "models")
~~~

For this run:

~~~text
log_interval = 1
eval_interval = 20
use_eval = false
~~~

Consequences:

~~~text
best is checked after every completed rollout/update
comparison is strict >
ties do not overwrite best_model
evaluation does not select best_model
regular models saves occur every 20 rollouts even though evaluation is disabled
~~~

The checkpoint contains post-update weights, while the compared reward was
collected by the pre-update policy for that rollout. This one-update association
is important when interpreting the retained checkpoint as the exact behavior
that earned the score.

### 8.3 Recovering The Best Save Point

The training-state manifest alone cannot recover the update:

~~~text
best checkpoint generation = 10
episode_or_update_index = null
training counters unavailable
~~~

Generation 10 is not treated as a training-step number. The exact retained save
point is recoverable only by combining the runner ordering, configured save
cadence, strict TensorBoard record highs, and artifact timestamp.

TensorBoard contains 333 `Total_Reward` points from step 300 through 99900. Its
strict record highs are:

| Rollout/update | Step | Total_Reward |
| ---: | ---: | ---: |
| 1 | 300 | 21.9448433 |
| 5 | 1500 | 39.1862526 |
| 7 | 2100 | 87.2438812 |
| 66 | 19800 | 104.8846970 |
| 71 | 21300 | 127.2712021 |
| 107 | 32100 | 170.7831573 |

The final record at step 32100 was written at
`2026-07-20T18:12:07.907400+08:00`; all retained best actor files and its
completion marker have the matching 18:12:07 modification time. Interleaved
regular saves at rollouts 20, 40, 60, 80, and 100 make the rollout-107 best save
global checkpoint generation 10. Thus:

~~~text
best_model:
  post-update-107 weights
  selected by rollout-107 Total_Reward
  training step label 32100

final models:
  post-update-333 weights
  final logged step 99900
~~~

This conclusion is not inferred from generation 10 alone.

## 9. Best-Selection Alignment

~~~text
SELECTION-PARTIALLY-ALIGNED
~~~

| Desired evidence | Relationship to Total_Reward |
| --- | --- |
| Coverage | Direct through per-step global/own coverage gain; final coverage ratio is not directly compared |
| Completion | Direct when completion produces coverage gain; incidental/team coverage can blur actor credit |
| Useful participation | Indirect through coverage and no-progress/repeated-target penalties |
| Robot 1/2 distance progress | Indirect only; distance progress itself is not a reward term |
| Budget releases | Indirect through prolonged no-progress/fewer gains; release count is not a term |
| Completion concentration/Jain fairness | Absent |
| Selected path cost | Structurally present, but absent in this run because scale is 0.0 |
| Entropy | Absent from best selection |

The current criterion did retain the checkpoint that also looked healthier in
the accepted deterministic seed-1 attribution. The source-traced training
values are consistent with that direction:

| TensorBoard scalar | Step 32100 | Step 99900 |
| --- | ---: | ---: |
| `Total_Reward` | 170.7831573 | 111.5664597 |
| `coverage_ratio` | 0.4254 | 0.4802 |
| `new_viewpoints` | 0.156667 | 0.120000 |
| `base_env_reward_mean` | 0.850355 | 0.660066 |
| `final_reward_mean` | 0.569277 | 0.371888 |
| repeated-target adjustment | -0.231744 | -0.238844 |
| global no-progress adjustment | -0.049333 | -0.049333 |
| selected-path-cost adjustment | 0.0 | 0.0 |
| budget trigger count | 0.023333 | 0.826667 |

These are sampled training-rollout aggregates, not deterministic playback
metrics. The criterion can react to coverage/reward degradation, but it cannot
directly detect completion concentration, per-agent progress quality, or budget
burden. It is therefore partially aligned rather than fully aligned or wholly
misaligned.

Candidate future selection evidence, without a new scalar formula, is:

~~~text
team reward
coverage and total completions
budget failures/releases
minimum and per-agent completions
motion/progress quality
paired deterministic validation behavior
~~~

## 10. Intermediate Checkpoint Availability And Drift Localization

~~~text
ONLY-BEST-AND-FINAL-AVAILABLE
~~~

The retained run root contains only:

~~~text
best_model/
logs/
models/
assignment contract files
configs.json
empty progress.txt
trainData.zip
~~~

There is no `models/checkpoints/`, generation-specific actor directory, best
history, temporary actor copy, renamed checkpoint, or console transcript. The
configuration has `save_checkpoints` unset. Regular saves target the same
`models/` directory every 20 rollouts; the explicit final save overwrites that
directory. Strict best improvements overwrite the same `best_model/` directory.

`trainData.zip` contains a snapshot of the same final `best_model`, `models`,
logs, and root metadata. It contains no additional actor history.

Therefore:

~~~text
The current artifacts can establish a best-versus-final regression candidate,
but cannot locate the exact update at which the behavior changed.
~~~

The retained best point itself can be localized to post-update 107 as described
above. The onset of the deterministic completion/progress difference can only be
bracketed after update 107 and by final update 333. TensorBoard can show reward
history but cannot reconstruct missing intermediate actor policies.

## 11. Target Difficulty And Execution Evidence

The current attribution schema supports:

~~~text
target id and per-robot distinct target count
segment start/end/duration
start, final, and minimum target distance
cumulative positive target-distance progress
zero-progress and zero-base-motion step counts
active-infeasible step count
completion, budget release, reset, or truncation release type
terminal resolver event types
per-step base XY motion, which can be summed over a segment
~~~

It does not support:

~~~text
selected path cost
exact budget allocation
budget steps consumed or remaining per segment
orientation/FOV error
scanner/arm/joint motion
rotation progress
~~~

The exact future per-segment table, once a valid initial-condition axis exists,
should be:

| Condition | Checkpoint | Robot | Target | Duration | Start distance | Final/min distance | Positive distance progress | Summed base motion | Completion/release | Release reason |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |

`summed base motion` is derived by joining row data to the segment on episode,
environment, robot, and inclusive decision-step bounds. Unsupported path-cost
and budget-allocation columns must remain explicitly unavailable.

Seed-1 descriptive evidence already shows why target identity alone is
insufficient. Across episode-0 segments, unweighted mean start distances were:

| Checkpoint | robot_0 | robot_1 | robot_2 |
| --- | ---: | ---: | ---: |
| Best | 2.7850 | 3.5868 | 3.9954 |
| Final | 1.9315 | 2.6678 | 4.1795 |

Final robot 1 had closer starts on this crude measure yet incurred three budget
releases versus none for best. Every observed budget-failure segment reached a
reported final distance of zero, showing that distance alone cannot explain scan
success in a task that also checks orientation, range/FOV, workspace, and dwell.
Because those missing conditions and selected path cost are not in the schema,
target/execution difficulty remains only partially diagnosable. Different target
ids must never be labeled harder solely from their ids.

## 12. Robustness Diagnosis Contract Status

### 12.1 Evaluation Set And Run Count

~~~text
existing seed-1 evidence:
  retained as authoritative baseline evidence
  must not be rerun

frozen new evaluation seeds:
  none

seed 2 and seed 3:
  explicitly rejected as meaningful trajectory variants

authorized future playback count from this report:
  0
~~~

### 12.2 Output Paths, Logs, And Commands

The four requested path/command slots are deliberately not frozen:

| Slot | Output path | Console log | Exact command |
| --- | --- | --- | --- |
| seed-2 best | NOT FROZEN | NOT FROZEN | NOT PROVIDED |
| seed-2 final | NOT FROZEN | NOT FROZEN | NOT PROVIDED |
| seed-3 best | NOT FROZEN | NOT FROZEN | NOT PROVIDED |
| seed-3 final | NOT FROZEN | NOT FROZEN | NOT PROVIDED |

Providing executable blocks after proving the seed axis ineffective would
violate the phase instruction. No candidate output or log path was created or
reserved.

### 12.3 Execution Order

No execution order is authorized. If a future reviewed phase establishes three
meaningfully distinct initial-condition identities, the required order remains
paired by condition:

~~~text
condition B best -> validate -> condition B final -> compare
condition C best -> validate -> condition C final -> compare
then combine with the accepted baseline condition A
~~~

Best and final must never be compared under different conditions.

## 13. Conditional Technical Validation Plan

The technical contract is ready for reuse only after the variation blocker is
resolved. Every future run must require:

~~~text
exit code 0
correct checkpoint kind/generation/purpose
legacy_fallback=False
300 unique environment decisions
900 robot rows
exactly three attribution artifacts
schema phase9g8h1_assignment_proposal_effective_attribution_v1
zero duplicate row keys
zero duplicate effective targets
zero invariant failures
zero unclassified rows
zero nonfinite applicable values
valid segment continuity and reset ordering
controller assignment equals effective assignment
~~~

Segment count, completion count, coverage, and exact reset count beyond
source-consistent structure remain data-dependent.

## 14. Conditional Paired Metric Plan

For each valid condition and each checkpoint, report:

~~~text
proposal noops by robot
executing steps by robot
completion vector and total completions
first-episode coverage
budget releases by robot and total
resolver rejections and Contract-C continuations
target starts, segment count, longest segment
longest noop and idle streak
base-motion rows by robot
zero-base-motion while executing
zero target-distance progress
Jain executing and completion fairness
mean active robots and all-three-active steps
~~~

Primary paired difference remains:

~~~text
delta(condition) = final_metric(condition) - best_metric(condition)
~~~

Primary paired metrics are coverage, total and per-agent completions, budget
releases, robot-1/robot-2 zero progress, and Jain completion fairness. Proposal
noop and executing counts remain hard collapse diagnostics. Rotation, arm motion,
and joint progress remain unsupported.

## 15. Conditional Aggregation And Decision Framework

Once three genuinely distinct controlled conditions exist:

~~~text
report every condition separately
report every paired final-minus-best delta
report medians and ranges across the three conditions
report best/final win counts for each major metric
preserve robot identities
never hide a failed condition inside an aggregate
do not claim statistical significance or confidence intervals
do not create an undocumented composite score
~~~

The frozen interpretation categories are conditional on that prerequisite:

| Code | Evidence | Interpretation |
| --- | --- | --- |
| R1 | Best healthier on at least two of three conditions with coverage/completion/budget/progress support | Repeatable late-training-regression candidate; retain best |
| R2 | Added conditions are equal or favor final | Original A3 is condition-specific |
| R3 | Best/final alternate by condition or metric | Mixed trade-off; retain both |
| R4 | Final consistently improves useful outcomes | Original A3 is not robust |
| R5 | Both remain healthy and differences are small/target-dependent | Best/final difference is secondary |
| R6 | Both fail on some conditions through budget/progress/controller evidence | Investigate environment/execution rather than policy drift alone |

Mixed classifications remain allowed. None can be assigned from seed 1 alone.

## 16. Failure And No-Retry Boundary

For any eventual paired execution:

~~~text
best run fails:
  preserve evidence
  do not run paired final

best passes and final fails:
  preserve both output states
  stop before the next condition

always:
  no automatic retry
  no output rename
  no code/config patch and relaunch
  no concurrent checkpoint runs
~~~

In the current phase, the pre-execution failure is semantic: no valid variation
axis exists. Therefore zero commands may run.

## 17. Explicit Limitations

- Seed 1 is one deterministic 300-decision trajectory per checkpoint.
- The current evidence does not establish robust expected performance,
  generalization, or statistical significance.
- The selected best weights are post-update weights scored by the preceding
  pre-update rollout.
- Only best and final actor artifacts remain, so deterministic policy drift
  onset cannot be localized.
- Target distance and base XY motion do not expose orientation, FOV, scanner,
  arm, or joint execution quality.
- The attribution schema lacks selected path cost and exact per-attempt budget
  allocation/use.
- The checkpoint selection metric is team-mean reward and cannot directly
  measure load balance or per-agent progress quality.

## 18. Explicit Non-Actions

~~~text
No production source behavior was modified.
No test or YAML file was modified.
No checkpoint tensor was loaded or deserialized.
No checkpoint loader was called.
No AppLauncher or Isaac Sim process was launched.
No assignment environment was constructed.
No playback or evaluation was run.
No new seed was executed.
No training or 300k continuation ran.
No GUI or video operation ran.
No result or checkpoint artifact was modified, moved, renamed, or deleted.
No installed HARL or Conda file was modified.
No commit was made.
~~~

## 19. Next-Phase Recommendation

Do not start Phase 9G-8I-3-1.

Recommend only a bounded design phase:

~~~text
Phase 9G-8I-3-0R:
Controlled Initial-Condition Variation Contract Design
~~~

Its sole purpose should be to establish a reviewed, same-task, same-M/N,
deterministic initial-condition identity that the playback entry can select and
record without conflating target geometry, checkpoint, stochastic action
sampling, reward, resolver, or controller changes. No playback execution is
authorized until that design is accepted.

## 20. Documentation Validation

~~~text
git diff --check:
  PASS (line-ending warning only)

git status --short --untracked-files=all:
  modified AgentRead/TASK_PROGRESS.md
  untracked Phase 9G-8I-3-0 report
  untracked Phase 9G-8I-3-0 TASK_PROGRESS archive

unexpected changed paths:
  none

archive versus committed TASK_PROGRESS predecessor:
  exact content match

trailing whitespace:
  none in all three documentation files

Markdown fence parity and final newline:
  PASS in all three documentation files
~~~

No Python compilation or test was required because this phase changed
documentation only.

## 21. Final Decision

Phase 9G-8I-3-0 is complete as a documentation-only static preflight and is
classified `NOT READY`. The best-selection and retained-history questions are
resolved, the metrics and decision logic are conditionally specified, and the
seed axis is rejected. The missing controlled initial-condition variation must
be resolved before an execution plan can legitimately freeze four runs.
