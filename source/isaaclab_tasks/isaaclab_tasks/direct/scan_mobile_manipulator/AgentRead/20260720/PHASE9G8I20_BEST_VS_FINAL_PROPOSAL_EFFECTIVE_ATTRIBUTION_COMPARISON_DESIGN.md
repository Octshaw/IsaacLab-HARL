# Phase 9G-8I-2-0: Best-vs-Final Proposal-Effective Attribution Comparison Design

Date: 2026-07-20

## 1. Classification

~~~text
ATTRIBUTION-COMPARISON-PLAN-READY
~~~

Exactly two sequential deterministic, actor-only, normal-evaluation attribution playbacks can be executed without source or configuration changes:

~~~text
A. retained 100k best_model, checkpoint kind best, generation 10
B. retained 100k models, checkpoint kind final, generation 22
~~~

Both checkpoints exist, use assignment checkpoint contract v2, bind the same canonical fingerprint, and passed the accepted Phase 9G-8I-1 integrity review. Current source explicitly selects the masked categorical mode with deterministic=True, loads only the three actors for normal_evaluation, and exposes the accepted Phase 9G-8H-1 attribution schema.

This phase is design and static preflight only. Neither checkpoint was loaded and neither playback was executed.

## 2. Starting Repository Preflight

~~~text
HEAD:
  0e610f9edc403a51a285777b672b3ea996681542

git log -1 --oneline:
  0e610f9e feat(assignment): add offline training run audit tool

allowed existing worktree changes:
  modified AgentRead/TASK_PROGRESS.md
  untracked Phase 9G-8I-1 report
  untracked Phase 9G-8I-1 TASK_PROGRESS archive

unrelated production/test/YAML/result/documentation changes:
  none

git diff --check:
  PASS
~~~

The starting state matches the instruction's allowed boundary. The reviewed Phase 9G-8I-1 documentation remains uncommitted and is preserved.

## 3. Accepted Phase 9G-8I-1 Result

Accepted classification:

~~~text
ATTRIBUTION-READY WITH NONBLOCKING LOG GAP
~~~

The fresh 100k run completed 333 logged rollout/update cycles through step 99900. All 63 expected TensorBoard tags contained 333 finite points with no missing, unexpected, or duplicate steps. The best and final checkpoint children passed contract, completion-marker, size, SHA-256, and tensor-inventory validation.

The incomplete training console transcript and empty progress.txt remain documented nonblocking evidence limitations. They do not affect this comparison design.

The 100k training result is an Outcome A candidate. Aggregate sampled-training participation improved, but per-agent deterministic behavior remains unknown. This comparison is designed to resolve that uncertainty.

## 4. Exact Training Run And Checkpoints

Training run:

~~~text
E:\Project\IsaacLab_HARL\results\isaaclab\Isaac-Scan-Mobile-Manipulator-Direct-v0\happo\assignment_happo_n50_phase9g8i1_fresh_100k_policy_noop_load_diagnosis\seed-00001-2026-07-20-17-40-33
~~~

Checkpoint A:

~~~text
path:
  E:\Project\IsaacLab_HARL\results\isaaclab\Isaac-Scan-Mobile-Manipulator-Direct-v0\happo\assignment_happo_n50_phase9g8i1_fresh_100k_policy_noop_load_diagnosis\seed-00001-2026-07-20-17-40-33\best_model

checkpoint kind:
  best

checkpoint generation:
  10
~~~

Checkpoint B:

~~~text
path:
  E:\Project\IsaacLab_HARL\results\isaaclab\Isaac-Scan-Mobile-Manipulator-Direct-v0\happo\assignment_happo_n50_phase9g8i1_fresh_100k_policy_noop_load_diagnosis\seed-00001-2026-07-20-17-40-33\models

checkpoint kind:
  final

checkpoint generation:
  22
~~~

Shared checkpoint facts:

~~~text
manifest:
  assignment_checkpoint_contract_v2

canonical fingerprint:
  19ef40b574c09c6c54b5e2ffea38e900b383188d2b48737a42b01d0db27c76e6

actors:
  robot_0
  robot_1
  robot_2

profile:
  lifecycle_contract_c

state:
  EP

sequence:
  feed_forward

share_param:
  false

M / N:
  3 / 50

actor / shared / action:
  1059 / 3183 / 51

raw / decoded noop:
  50 / -1
~~~

The manifests do not record an exact update index for best generation 10. This plan does not equate it with any particular TensorBoard reward maximum.

## 5. Files And Source Boundaries Inspected

Read completely:

~~~text
AgentRead/AGENTS.md
AgentRead/TASK_PROGRESS.md
AgentRead/20260720/PHASE9G8I1_FRESH_100K_CONTROLLED_TRAINING_EXECUTION_AND_OFFLINE_AUDIT_REVIEW.md
AgentRead/20260720/PHASE9G8I0_POLICY_NOOP_LOAD_IMBALANCE_CONTROLLED_TRAINING_DESIGN_AND_PREFLIGHT.md
AgentRead/20260720/PHASE9G8H2_BOUNDED_PROPOSAL_EFFECTIVE_ATTRIBUTION_PLAYBACK_REPORT.md
AgentRead/20260720/PHASE9G8H1_PLAYBACK_PROPOSAL_EFFECTIVE_ATTRIBUTION_DIAGNOSTIC_IMPLEMENTATION_AND_FAKE_REGRESSION.md
AgentRead/20260720/PHASE9G8H0_PLAYBACK_PROPOSAL_EFFECTIVE_ATTRIBUTION_AND_LOAD_BALANCE_DIAGNOSTIC_DESIGN.md
~~~

Inspected statically:

~~~text
scripts/reinforcement_learning/harl/play_assignment.py
assignment_playback_attribution_diagnostics.py
assignment_harl_wrapper.py
assignment_checkpoint_load.py
assignment_checkpoint_contract.py
algorithm_proxy_component_mesh.yaml
installed HARL OnPolicyBase.act
installed HARL StochasticPolicy.forward
installed HARL ACTLayer.forward
~~~

Read-only evidence also included both checkpoint manifests/training-state manifests/fingerprint files and the existing Phase 9G-8H-2 attribution CSV/JSON artifacts.

No checkpoint tensor was deserialized.

## 6. Deterministic Action Semantics

The current action path is exact:

~~~text
play_assignment.py
  actors[agent_id].act(
      observation,
      recurrent state,
      mask,
      available_actions,
      deterministic=True,
  )

installed HARL OnPolicyBase.act
  forwards deterministic to StochasticPolicy

installed HARL StochasticPolicy.forward
  forwards deterministic to ACTLayer

installed HARL ACTLayer.forward
  deterministic true -> Categorical.mode()
  deterministic false -> Categorical.sample()
~~~

Therefore the planned runs use the mode of the masked categorical distribution. Stochastic sampling is disabled.

play_assignment.py subsequently calls evaluate_actions for the already selected action only to compute selected_action_probability. That call does not resample or replace the selected action.

The policy is feed-forward by contract, with both recurrent flags false. The script still carries zero recurrent-state tensors because that is the common HARL actor API; they do not enable recurrent execution.

## 7. Actor-Only Normal-Evaluation Load Boundary

Without an ablation flag, play_assignment.py sets:

~~~text
purpose:
  CompatibilityPurpose.NORMAL_EVALUATION
~~~

It calls load_assignment_checkpoint with only:

~~~text
actor_modules:
  robot_0 actor
  robot_1 actor
  robot_2 actor
~~~

It does not pass live critic or ValueNorm targets. In assignment_checkpoint_load.py, NORMAL_EVALUATION requires and strictly mutates the ordered actor artifacts only. Critic and ValueNorm artifacts are validated as part of native checkpoint metadata/file integrity, but are not restored into live modules.

Not restored:

~~~text
critic
ValueNorm
actor or critic optimizer
training counters
best-reward state
RNG state
environment/resolver state
rollout buffer
~~~

No continuation acknowledgement is required for normal evaluation. The commands deliberately omit:

~~~text
--assignment_checkpoint_ablation
--allow_unversioned_legacy_checkpoint
any continuation acknowledgement
~~~

Expected loader lines:

~~~text
best:
  kind=best generation=10 purpose=normal_evaluation legacy_fallback=False

final:
  kind=final generation=22 purpose=normal_evaluation legacy_fallback=False
~~~

## 8. Attribution Collector And Output Contract

Future commands enable:

~~~text
--log_assignment_proposal_effective
--assignment_proposal_effective_output_dir PATH
~~~

They deliberately omit:

~~~text
--print_assignment_proposal_effective
~~~

Per-robot console printing is unnecessary for correctness and would add 900 lines per run. The normal aggregate diagnostic remains at diagnostic_interval=1, so the captured console should contain one aggregate line for each of the 300 playback loop iterations.

Authoritative schema:

~~~text
phase9g8h1_assignment_proposal_effective_attribution_v1
~~~

Each output directory must contain exactly:

~~~text
assignment_proposal_effective_rows.csv
assignment_proposal_effective_summary.json
assignment_target_segments.csv
~~~

The collector remains default-off outside these explicit flags. It reads the wrapper's clone-owned lifecycle payload and never drains resolver events itself.

There is no separate comparison-label CLI. Both summaries use method_name=happo; unambiguous checkpoint identity is carried by the separate frozen output parents and captured loader lines.

## 9. Frozen Playback Contract

Both future runs use exactly:

| Field | Frozen value |
| --- | --- |
| task | Isaac-Scan-Mobile-Manipulator-Direct-v0 |
| algorithm | happo |
| assignment mode | enabled |
| scenario | algorithm_proxy_component_mesh.yaml |
| num_envs | 1 |
| max_steps | 300 |
| seed | 1 |
| device | cuda:0 |
| headless | true |
| lifecycle profile | lifecycle_contract_c |
| policy sequence | feed-forward |
| recurrent flags | false / false |
| share_param | false |
| M / N | 3 / 50 |
| actor/shared/action width | 1059 / 3183 / 51 |
| raw noop | 50 |
| cooldown | enabled, budget trigger |
| cooldown action-mask overlay | false |
| redirect guardrail | false |
| diagnostic interval | 1 |
| stop on done | false |
| attribution row printing | false |
| video/GUI/training/evaluation | disabled |

Only checkpoint path, attribution output path, console-log path, and the corresponding best/final variable label differ.

## 10. Frozen Output Paths

Best output:

~~~text
E:\Project\IsaacLab_HARL\results\isaaclab\Isaac-Scan-Mobile-Manipulator-Direct-v0\happo\assignment_happo_n50_phase9g8i21_best_100k_proposal_effective_attribution\seed-00001
~~~

Final output:

~~~text
E:\Project\IsaacLab_HARL\results\isaaclab\Isaac-Scan-Mobile-Manipulator-Direct-v0\happo\assignment_happo_n50_phase9g8i21_final_100k_proposal_effective_attribution\seed-00001
~~~

Console logs:

~~~text
C:\Users\33506\AppData\Local\Temp\phase9g8i21_best_attribution_console_20260720.log
C:\Users\33506\AppData\Local\Temp\phase9g8i21_final_attribution_console_20260720.log
~~~

All four paths were absent during this static preflight. They must be rechecked immediately before future execution. The output paths are outside best_model, models, and the 8H-2 baseline. Neither run can overwrite the other.

The 9G8I21 token denotes the future execution phase. This report uses the required 9G8I20 filename token for the current design phase.

## 11. Console-Capture Verification

A harmless non-Isaac PowerShell probe was run under PowerShell 7.6.3:

~~~text
native test command exit:
  7

LASTEXITCODE after piping through Tee-Object:
  7
~~~

This confirms that, in the current PowerShell environment, the native process exit code remains available after the Tee-Object pipeline. No AppLauncher, Isaac Sim, environment, checkpoint, playback, or evaluation path was invoked by the probe.

Each frozen command records the exit code immediately after Tee-Object. The CSV/JSON artifacts remain authoritative even if console capture is incomplete.

## 12. Exact Future Command A: Best Checkpoint

Run from E:\Project\IsaacLab_HARL only after the execution phase is explicitly authorized:

~~~powershell
$bestLog = "C:\Users\33506\AppData\Local\Temp\phase9g8i21_best_attribution_console_20260720.log"
$bestOutput = "E:\Project\IsaacLab_HARL\results\isaaclab\Isaac-Scan-Mobile-Manipulator-Direct-v0\happo\assignment_happo_n50_phase9g8i21_best_100k_proposal_effective_attribution\seed-00001"
if (Test-Path -LiteralPath $bestLog) { throw "Best console log already exists: $bestLog" }
if (Test-Path -LiteralPath $bestOutput) { throw "Best attribution output already exists: $bestOutput" }
$bestArgs = @(
  "run"
  "-p"
  "C:\isaacenvs\isaac45_harl"
  "--no-capture-output"
  "python"
  "-u"
  "scripts\reinforcement_learning\harl\play_assignment.py"
  "--task"
  "Isaac-Scan-Mobile-Manipulator-Direct-v0"
  "--algorithm"
  "happo"
  "--assignment_rl"
  "--scenario_config"
  "source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\configs\scenarios\algorithm_proxy_component_mesh.yaml"
  "--num_envs"
  "1"
  "--dir"
  "E:\Project\IsaacLab_HARL\results\isaaclab\Isaac-Scan-Mobile-Manipulator-Direct-v0\happo\assignment_happo_n50_phase9g8i1_fresh_100k_policy_noop_load_diagnosis\seed-00001-2026-07-20-17-40-33\best_model"
  "--max_steps"
  "300"
  "--diagnostic_interval"
  "1"
  "--seed"
  "1"
  "--headless"
  "--device"
  "cuda:0"
  "--log_assignment_proposal_effective"
  "--assignment_proposal_effective_output_dir"
  $bestOutput
  "env.assignment_lifecycle_profile=lifecycle_contract_c"
  "env.assignment_cooldown_enabled=true"
  "env.assignment_cooldown_trigger_mode=budget"
  "env.assignment_cooldown_apply_to_action_mask=false"
  "env.assignment_redirect_guardrail_enabled=false"
  "agent.device.cuda=true"
  "agent.device.cuda_deterministic=true"
  "agent.model.use_recurrent_policy=false"
  "agent.model.use_naive_recurrent_policy=false"
  "agent.algo.share_param=false"
)
& "D:\miniconda3\Scripts\conda.exe" @bestArgs 2>&1 | Tee-Object -FilePath $bestLog
$bestExitCode = $LASTEXITCODE
Write-Host "Best attribution exit code: $bestExitCode"
if ($bestExitCode -ne 0) { throw "Best attribution failed with exit code $bestExitCode" }
~~~

## 13. Exact Future Command B: Final Checkpoint

Run only after Command A and all best-output technical checks pass:

~~~powershell
$finalLog = "C:\Users\33506\AppData\Local\Temp\phase9g8i21_final_attribution_console_20260720.log"
$finalOutput = "E:\Project\IsaacLab_HARL\results\isaaclab\Isaac-Scan-Mobile-Manipulator-Direct-v0\happo\assignment_happo_n50_phase9g8i21_final_100k_proposal_effective_attribution\seed-00001"
if (Test-Path -LiteralPath $finalLog) { throw "Final console log already exists: $finalLog" }
if (Test-Path -LiteralPath $finalOutput) { throw "Final attribution output already exists: $finalOutput" }
$finalArgs = @(
  "run"
  "-p"
  "C:\isaacenvs\isaac45_harl"
  "--no-capture-output"
  "python"
  "-u"
  "scripts\reinforcement_learning\harl\play_assignment.py"
  "--task"
  "Isaac-Scan-Mobile-Manipulator-Direct-v0"
  "--algorithm"
  "happo"
  "--assignment_rl"
  "--scenario_config"
  "source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\configs\scenarios\algorithm_proxy_component_mesh.yaml"
  "--num_envs"
  "1"
  "--dir"
  "E:\Project\IsaacLab_HARL\results\isaaclab\Isaac-Scan-Mobile-Manipulator-Direct-v0\happo\assignment_happo_n50_phase9g8i1_fresh_100k_policy_noop_load_diagnosis\seed-00001-2026-07-20-17-40-33\models"
  "--max_steps"
  "300"
  "--diagnostic_interval"
  "1"
  "--seed"
  "1"
  "--headless"
  "--device"
  "cuda:0"
  "--log_assignment_proposal_effective"
  "--assignment_proposal_effective_output_dir"
  $finalOutput
  "env.assignment_lifecycle_profile=lifecycle_contract_c"
  "env.assignment_cooldown_enabled=true"
  "env.assignment_cooldown_trigger_mode=budget"
  "env.assignment_cooldown_apply_to_action_mask=false"
  "env.assignment_redirect_guardrail_enabled=false"
  "agent.device.cuda=true"
  "agent.device.cuda_deterministic=true"
  "agent.model.use_recurrent_policy=false"
  "agent.model.use_naive_recurrent_policy=false"
  "agent.algo.share_param=false"
)
& "D:\miniconda3\Scripts\conda.exe" @finalArgs 2>&1 | Tee-Object -FilePath $finalLog
$finalExitCode = $LASTEXITCODE
Write-Host "Final attribution exit code: $finalExitCode"
if ($finalExitCode -ne 0) { throw "Final attribution failed with exit code $finalExitCode" }
~~~

These commands contain no training, video, GUI, stochastic-action, ablation, legacy-fallback, continuation, critic, or ValueNorm option.

## 14. Frozen Sequential Execution Order

~~~text
1. Confirm reviewed repository state and no stale Python/conda/Isaac process.
2. Revalidate checkpoint A metadata, fingerprint, completion marker, and kind/generation.
3. Revalidate checkpoint B metadata, fingerprint, completion marker, and kind/generation.
4. Require both exact attribution output paths and both log paths to be absent.
5. Run Command A exactly once in the foreground.
6. Record best process exit code and validate all best artifacts.
7. Stop if any best technical check fails.
8. Run Command B exactly once only after best passes.
9. Record final process exit code and validate all final artifacts.
10. Build the frozen one-update/best/final comparison.
~~~

The playbacks must not run concurrently.

If best fails, final must not start automatically. If best passes and final fails, preserve both output states and classify the comparison incomplete. Neither command may be retried automatically.

## 15. Per-Run Technical Validation

Each run must satisfy:

~~~text
process exit code:
  0

checkpoint load:
  expected kind and generation
  purpose=normal_evaluation
  legacy_fallback=False

playback:
  completed steps=300, max_steps=300
  no traceback or runtime error

artifacts:
  exactly the frozen three files
  schema phase9g8h1_assignment_proposal_effective_attribution_v1
  900 robot rows
  300 unique environment decisions
  exactly robot ids 0,1,2 per decision
  no duplicate episode/env/decision/robot key
  summary row_count=900
  invariant_failures empty

row invariants:
  raw action decodes to decoded proposal
  proposal/effective changed flag exact
  controller assignment equals effective assignment
  selected probability finite and in [0,1]
  no unclassified primary attribution
  no duplicate effective target within a decision
  no nonfinite non-null physical value

segments:
  segment count is data-dependent
  every segment has valid identity, duration, continuity, and release type
  attempt_started count equals segment-start count
  no invariant_break release
~~~

A zero-segment run is technically valid and behaviorally diagnostic of collapse; the segment count is never frozen to 12.

## 16. Reset And Decision Semantics

The accepted 8H-2 run established the current source behavior:

~~~text
global playback iterations:
  300

collector episode 0:
  299 decisions

episode-0 decision 299:
  done/reset decision
  3 robot rows with done=true and reset=true
  post_state_pre_reset_available=false

global playback iteration 300:
  collector episode 1, decision_step=1
  first decision after automatic reset
~~~

The collector attaches reset to the decision that caused the reset, increments episode identity afterward, and restarts decision_step at 1. It never substitutes reset state for the executed post state.

Policy-dependent early completion could create a different number of source-consistent reset groups. Therefore the future hard requirement is:

~~~text
every done environment decision has exactly M reset rows
episode id increments once afterward
decision_step restarts at 1
post-reset physical nullability follows the schema
total unique decisions remains 300
total robot rows remains 900
~~~

An exact reset-row count or exact target-segment count is not frozen.

## 17. Per-Agent Metric Plan And Exact Derivations

All horizon totals are recomputed from rows across the full 300 global decisions. The summary JSON is per episode, so ratios from separate episode summaries must not be averaged naively.

Direct row or summary counts:

~~~text
raw proposal noop:
  count(decoded_proposal == -1)

raw proposal target:
  count(decoded_proposal >= 0)

effective idle:
  count(effective_assignment == -1)

effective executing:
  count(effective_assignment >= 0)

proposal/effective changed:
  count(proposal_effective_changed)

attempt started:
  count attempt_started in resolver_event_types

same-target continuation:
  count attempt_continued_same_target

Contract-C continuation:
  count attempt_continued_noop_contract_c

target completed:
  count target_completed_this_step

budget failure:
  count budget_failure_this_step

budget release:
  count release_budget_failure_this_step

reset:
  count reset

resolver rejections:
  count proposal_rejected, grouped by proposal_rejected_reason

exact conflict loss/win:
  count claim_conflict with claim_loser/claim_winner
~~~

Required rejection groups:

~~~text
claim loss
owned-target rejection
covered-target rejection
failed-pair rejection
unavailable-target rejection
switch rejection
other canonical reason if observed
~~~

Streak and segment derivations:

~~~text
longest idle streak:
  maximum consecutive effective_assignment == -1 within one episode

longest raw-noop streak:
  maximum consecutive decoded_proposal == -1 within one episode

longest same-target proposal streak:
  maximum consecutive identical decoded_proposal >= 0 within one episode

target segment count:
  count segment rows by robot

longest executing segment:
  maximum duration_steps by robot; zero when no segment
~~~

Streaks break at episode boundaries. They are not joined across automatic reset.

Physical derivations:

~~~text
steps with valid post-state:
  count post_state_pre_reset_available

steps with translational base motion:
  count valid rows where base_motion_distance > 1e-8

zero-command steps:
  count controller_action_l2_norm <= 1e-8

zero-base-motion while executing:
  count effective_assignment >= 0, valid post-state,
        and base_motion_distance <= 1e-8

zero target-distance progress:
  count finite distance_progress with abs(value) <= 1e-8
~~~

The current row schema has no orientation delta and does not expose the 9D command vector, only its norm. Therefore rotational-motion steps and separate translational/rotational command components are unavailable. They must be reported as unsupported, not inferred. Zero base motion does not imply that every scanner, arm, or joint component was stationary.

## 18. Team Metric Plan

For each checkpoint report:

~~~text
executing steps by robot
idle steps by robot
target starts by robot
target completions by robot
budget releases by robot
total starts
total completions
total budget releases
total resolver rejections
total Contract-C continuations
~~~

For each unique environment decision:

~~~text
active_robot_count =
  count(effective_assignment >= 0)

mean_active_robots =
  mean(active_robot_count over 300 decisions)

steps_all_three_active =
  count(active_robot_count == 3)

steps_two_active =
  count(active_robot_count == 2)

steps_one_active =
  count(active_robot_count == 1)

steps_zero_active =
  count(active_robot_count == 0)
~~~

Fairness diagnostics over full-horizon vectors:

~~~text
Jain(x) =
  sum(x)^2 / (M * sum(x^2))

Jain executing:
  x = full-horizon executing steps by robot

Jain completion:
  x = full-horizon target completions by robot

zero-total vector:
  report null
~~~

Coverage/completion derivation for the first completed episode:

~~~text
1. Collect unique target_completed target ids from projected resolver_events.
2. Add unique target_completed ids from unprojected_environment_events.
3. Deduplicate by episode, environment, and target id.
4. coverage_gain_count = unique id count.
5. final coverage ratio = coverage_gain_count / N when initial reset coverage is zero.
6. Cross-check against the last finite row coverage_ratio before reset.
7. If done-step nullability prevents exact agreement, report both the
   authoritative completion-event count and last observable finite ratio.
~~~

Do not sum replicated per-robot coverage_delta_count values as robot credit.

## 19. Frozen One-Update Baseline

Accepted Phase 9G-8H-2 totals:

| Metric | robot_0 | robot_1 | robot_2 |
| --- | ---: | ---: | ---: |
| proposal noop | 300 | 0 | 248 |
| proposal target | 0 | 300 | 52 |
| effective idle | 300 | 0 | 239 |
| effective executing | 0 | 300 | 61 |
| starts | 0 | 8 | 4 |
| completions | 0 | 5 | 2 |
| budget releases | 0 | 1 | 1 |
| Contract-C continuations | 0 | 0 | 9 |
| longest idle streak within episode | 299 | 0 | 153 |
| longest raw-noop streak within episode | 299 | 0 | 162 |
| longest real-target proposal streak | 0 | 61 | 46 |
| longest executing segment | 0 | 61 | 46 |

Accepted team baseline:

~~~text
executing steps:
  [0,300,61]

idle steps:
  [300,0,239]

completions:
  [0,5,2]

total completions:
  7

first completed episode coverage:
  18 / 50 = 0.36

budget releases:
  2

Contract-C continuations:
  9

resolver rejections:
  0

Jain executing fairness:
  0.4635069337

Jain completion fairness:
  0.5632183908

mean active robots:
  1.2033333333

steps with all three active:
  0

steps with two active:
  61

steps with one active:
  239

steps with zero active:
  0
~~~

The streaks were independently derived from the accepted 900 rows with episode boundaries respected. The active-count distribution was independently derived from the 300 unique decision groups.

## 20. Frozen Three-Way Comparison Table

The execution report must populate every TBD cell:

| Metric | One-update baseline | 100k best_model | 100k final models | Preferred direction | Interpretation |
| --- | ---: | ---: | ---: | --- | --- |
| robot_0 proposal noop | 300 | TBD | TBD | materially lower | tests prior full collapse |
| robot_1 proposal noop | 0 | TBD | TBD | contextual | noop can be active continuation |
| robot_2 proposal noop | 248 | TBD | TBD | lower idle-noop burden | separate Contract C continuation |
| robot_0 executing steps | 0 | TBD | TBD | useful increase | require nontrivial segments |
| robot_1 executing steps | 300 | TBD | TBD | maintain useful work | equality is not required |
| robot_2 executing steps | 61 | TBD | TBD | useful increase | inspect segment quality |
| robot_0 longest idle streak | 299 | TBD | TBD | materially lower | episode-bounded |
| robot_1 longest idle streak | 0 | TBD | TBD | low | avoid needless idle |
| robot_2 longest idle streak | 153 | TBD | TBD | materially lower | primary prior asymmetry |
| robot_0 completions | 0 | TBD | TBD | nonzero if capable | capability-aware |
| robot_1 completions | 5 | TBD | TBD | contextual | concentration alone is not failure |
| robot_2 completions | 2 | TBD | TBD | maintain or improve | inspect task difficulty |
| total completions | 7 | TBD | TBD | higher | compare with coverage |
| first-episode coverage | 0.36 | TBD | TBD | higher | event/finite-ratio cross-check |
| budget releases | 2 | TBD | TBD | lower when completion holds | pressure is contextual |
| Contract-C continuations | 9 | TBD | TBD | contextual | valid execution, not idle |
| resolver rejections | 0 | TBD | TBD | zero or rare | investigate only if material |
| Jain executing fairness | 0.4635069337 | TBD | TBD | higher diagnostically | not an optimizer objective |
| Jain completion fairness | 0.5632183908 | TBD | TBD | higher diagnostically | capability-aware |
| mean active robots | 1.2033333333 | TBD | TBD | higher useful parallelism | motion/segments must support |
| all-three-active steps | 0 | TBD | TBD | increase when useful | exact equality not required |

No checkpoint is selected from a single cell.

## 21. Deterministic Collapse Checks

### Robot 0

Flag for review when any pattern occurs:

~~~text
all or near-all raw noop proposals
zero real-target starts
zero completions
one real target proposed for most of an episode
one narrow segment pattern with no useful progress
long executing segment dominated by zero base motion
repeated unavailable or rejected proposal
~~~

Low entropy alone is not collapse. Collapse requires observed deterministic behavior.

### Robot 2

Flag for review:

~~~text
long raw-noop streak
long effective-idle streak
narrow repeated target pattern
Contract-C continuations dominating apparent execution
repeated budget-release loops
executing rows dominated by zero command or zero base motion
zero or reduced completion despite high execution
~~~

### Robot 1

Flag for review:

~~~text
high proposal switching
many short unstable segments
repeated budget failures
high proposal variability without completion or coverage gain
excessive workload concentration caused by other robots collapsing
~~~

The final training entropies motivate these questions but do not answer them.

## 22. Outcome Decision Framework

### Outcome A1: Deterministic Participation Improvement

Required evidence:

~~~text
all three robots propose real targets
all three execute meaningful target segments
robot_0 is no longer near-100 percent noop
robot_2's long idle streak is materially reduced
completion distribution is less concentrated
coverage/completions do not materially regress
resolver invariants remain intact
~~~

Recommendation: accept ordinary training as resolving the primary one-update noop artifact, select the stronger checkpoint for broader evaluation, and do not modify reward or resolver.

### Outcome A2: Aggregate Training Improved, Deterministic Collapse Persists

Evidence: training TensorBoard showed near-zero aggregate effective noop, but best and/or final deterministic playback retains robot_0 or robot_2 collapse.

Recommendation: enter a policy-noop/deterministic-collapse diagnosis focused on sampled-training versus modal-action behavior. Do not modify resolver and do not extend automatically to 300k.

### Outcome A3: Best Healthy, Final Regressed

Evidence: best gives stronger useful participation, completion, coverage, or fairness while final shows collapse, excessive idleness, or poorer segment quality.

Recommendation: retain best as the evaluation candidate and investigate late-training policy drift.

### Outcome A4: Final Healthier Than Best

Evidence: final improves useful participation, completion, or coverage without materially worse budget/rejection pressure.

Recommendation: use final as the evaluation candidate.

### Outcome B: Participation Present, Completion Concentrated

All robots execute, but one robot owns most completions. This may reflect heterogeneous capability and path cost and is not automatically a failure. Review avoidability before considering fairness shaping.

### Outcome C: Budget Failure Dominates

Investigate task feasibility, completion thresholds, controller execution, and cost versus execution difficulty. Do not classify it as resolver failure without attribution evidence.

### Outcome D: Resolver Rejection Appears

Investigate only when useful proposals are materially rejected. Zero or rare rejection does not reopen resolver design.

## 23. Checkpoint Preference Rule

Evaluate in this order:

~~~text
1. technical integrity and resolver invariants
2. useful participation by all capable robots
3. completions and first-episode coverage
4. absence of deterministic noop/idle collapse
5. budget-failure burden
6. load concentration and Jain diagnostics
7. segment continuity, motion, and policy stability
~~~

Reward-selected best_model is not automatically preferred. Newer final models is not automatically preferred. Equal work, exactly one-third of completions, and Jain fairness 1.0 are not requirements.

If both are technically healthy but trade off coverage and balance, retain both conclusions and request review rather than forcing a scalar ranking.

## 24. Technical Failure, Warning, And Retry Boundary

Hard per-run failure:

~~~text
nonzero process exit
checkpoint kind/generation/purpose mismatch
legacy fallback
contract or dimension mismatch
not exactly 300 unique decisions or 900 rows
missing or extra attribution artifact
duplicate row key
controller/effective mismatch
duplicate effective target
invariant_break or nonempty invariant_failures
unclassified row
nonfinite selected probability or non-null physical value
malformed reset/episode transition
collector finalization failure
traceback or application shutdown failure
~~~

Behavioral warnings, not technical failures by themselves:

~~~text
low coverage or completion
many raw noops
long idle streak
low fairness
many Contract-C continuations
finite zero-motion execution
finite budget releases
narrow deterministic action pattern
~~~

Failure handling:

~~~text
best fails:
  preserve log/output
  do not run final
  do not retry

best passes and final fails:
  preserve both states
  do not retry
  classify comparison incomplete

either run fails:
  do not patch source/config and relaunch
  record last successful stage and exact evidence
~~~

## 25. Explicit Non-Goals

This design does not authorize or perform:

~~~text
source, test, or YAML modification
attribution schema change
checkpoint save/load behavior change
reward, observation, mask, resolver, Contract C, ownership, controller,
or environment change
training or 300k continuation
checkpoint continuation
stochastic evaluation
second seed
automatic retry
concurrent playback
GUI or video
performance/convergence claim
HARL or Conda modification
commit
~~~

One deterministic 300-decision trajectory per checkpoint is an attribution comparison, not a statistical performance evaluation.

## 26. Next-Phase Boundary

After this report is reviewed and explicitly accepted, recommend only:

~~~text
Phase 9G-8I-2-1:
Sequential Best-and-Final Bounded Attribution Playback Execution
~~~

That phase may:

~~~text
run best exactly once
validate best before proceeding
run final exactly once
validate final
produce the frozen three-way comparison
~~~

It must not retry automatically, modify code/configuration, train, run a second seed, launch GUI/video, continue to 300k, modify reward/resolver, or commit.

Phase 9G-8I-2-1 was not started automatically.

## 27. Boundary Confirmation

~~~text
No production source behavior was modified.
No test or YAML file was modified.
No checkpoint was loaded or restored.
No checkpoint tensor was deserialized.
No AppLauncher or Isaac Sim process was launched.
No assignment environment was constructed.
No playback was run.
No training or evaluation was run.
No GUI or video operation was performed.
No 300k continuation or second seed was started.
No installed HARL or Conda file was modified.
No result artifact or prior output was modified.
No commit was made.
~~~

## 28. Final Recommendation

Accept Phase 9G-8I-2-0 as ATTRIBUTION-COMPARISON-PLAN-READY. Execute nothing until review. If accepted, the next phase may run the two frozen commands sequentially under the stated stop-on-failure boundary and then populate the frozen comparison table.

