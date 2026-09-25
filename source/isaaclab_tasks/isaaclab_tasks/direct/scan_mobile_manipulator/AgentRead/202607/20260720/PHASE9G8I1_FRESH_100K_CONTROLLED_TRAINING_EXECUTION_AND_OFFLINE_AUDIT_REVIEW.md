# Phase 9G-8I-1: Fresh 100k Controlled Training Execution and Offline Audit Review

Date: 2026-07-20

## Classification

~~~text
ATTRIBUTION-READY WITH NONBLOCKING LOG GAP
~~~

The user-executed fresh 100k lifecycle_contract_c run is technically complete. The existing offline audit, direct metadata inspection, independent opaque-byte artifact hashing, and independent TensorBoard inspection all pass without a hard failure.

The complete child-process console stream was not preserved. The retained PowerShell transcript records the frozen command, timestamps, and exit code 0, but omits the middle training output. This is a nonblocking console-capture evidence gap because TensorBoard and native checkpoint evidence independently establish all 333 logged rollout/update cycles and a completed final checkpoint.

The result is an Outcome A candidate. Aggregate effective participation improved substantially, but aggregate TensorBoard metrics cannot establish per-agent raw proposals or deterministic best/final load balance. Both checkpoints are ready for a separately designed attribution comparison.

## Starting Repository State

~~~text
HEAD:
  0e610f9edc403a51a285777b672b3ea996681542

git log -1 --oneline:
  0e610f9e feat(assignment): add offline training run audit tool

starting git status:
  clean

starting git diff --name-status:
  empty

starting git diff --check:
  PASS
~~~

This is accepted starting state A. The Phase 9G-8I-0A offline audit implementation was committed and no unrelated source, test, YAML, or documentation change existed.

## Exact Result And Evidence

Reviewed run:

~~~text
E:\Project\IsaacLab_HARL\results\isaaclab\Isaac-Scan-Mobile-Manipulator-Direct-v0\happo\assignment_happo_n50_phase9g8i1_fresh_100k_policy_noop_load_diagnosis\seed-00001-2026-07-20-17-40-33
~~~

Existing audit outputs:

~~~text
C:\Users\33506\AppData\Local\Temp\phase9g8i1_audit_20260720_223047\assignment_training_run_audit.json
C:\Users\33506\AppData\Local\Temp\phase9g8i1_audit_20260720_223047\assignment_training_run_audit.md
~~~

The existing audit outputs remained available, so the audit tool was not rerun.

Evidence inspected included AGENTS.md, TASK_PROGRESS.md, the Phase 9G-8I-0, 9G-8I-0A, and 9G-8H-2 reports, both audit outputs, configs.json, root and child contract metadata, best_model, models, the TensorBoard event file, progress.txt, and the retained PowerShell transcript fragment.

The run root also contains trainData.zip, created after the audit. It is supplementary and non-authoritative. No conclusion relies on that archive; the live artifacts were independently inspected and rehashed.

No actor, critic, or ValueNorm artifact was deserialized. Checkpoint files were treated as opaque bytes for existence, size, and SHA-256 checks only.

## Training Contract Reconciliation

| Contract field | Required | Observed | Result |
| --- | --- | --- | --- |
| task | Isaac-Scan-Mobile-Manipulator-Direct-v0 | same | PASS |
| algorithm | happo | happo | PASS |
| profile | lifecycle_contract_c | same | PASS |
| state type | EP | EP | PASS |
| policy sequence | feed-forward | feed-forward | PASS |
| recurrent flags | false / false | false / false | PASS |
| share_param | false | false | PASS |
| M / N | 3 / 50 | 3 / 50 | PASS |
| actor/shared/action width | 1059 / 3183 / 51 | same | PASS |
| raw/decoded noop | 50 / -1 | same | PASS |
| rollout threads | 1 | 1 | PASS |
| episode length | 300 | 300 | PASS |
| configured steps | 100000 | 100000 | PASS |
| actual final logged step | 99900 | 99900 | PASS |
| rollout/update cycles | 333 | 333 | PASS |
| save/log interval | 20 / 1 | 20 / 1 | PASS |
| seed | 1 | 1 | PASS |

All 27 audit configuration checks passed and none failed.

## Fresh-Start Result

~~~text
Args.dir:
  null

model_dir:
  null

continuation acknowledgement:
  false
~~~

The result is a fresh start. There is no evidence of checkpoint continuation, inherited model loading, or reuse of an earlier run directory.

## Technical Completion

| Check | Result |
| --- | --- |
| TensorBoard event files | 1 |
| expected scalar tags | 63/63 |
| points per expected tag | 333/333 |
| exact steps | 300, 600, ..., 99900 |
| missing or unexpected steps | 0 |
| duplicate points | 0 |
| incomplete tags | 0 |
| nonfinite values | 0 |
| noop plus valid-action invariant | PASS |
| invariant comparisons | 333 |
| maximum invariant residual | 5.587935447692871e-08 |
| invariant tolerance | 1e-5 |
| root contract | PASS |
| contract checks | 29 passed, 0 failed |
| artifact size failures | 0 |
| artifact SHA-256 failures | 0 |
| inventory metadata failures | 0 |
| temporary/full-model/legacy artifacts | 0 / 0 / 0 |

The exact TensorBoard sequence establishes every expected logging/update boundary through step 99900. Native completion markers and final checkpoint metadata establish that the final save completed.

## Transcript Evidence Gap

Retained transcript:

~~~text
C:\Users\33506\AppData\Local\Temp\phase9g8i1_fresh_100k_20260720_173919.log

start:
  2026-07-20T17:39:25.4885006+08:00

end:
  2026-07-20T22:23:37.3737129+08:00

reported training exit code:
  0
~~~

The transcript preserves the frozen command and terminal return, but not the child process's middle console output. Line-by-line console reconstruction is therefore unavailable and is not claimed.

This gap is nonblocking. TensorBoard contains every expected step and scalar series, while native-v2 manifests, completion markers, generations, hashes, and inventories independently prove complete checkpoint writes. Exit code 0 is reported separately as retained transcript evidence, not as the sole completion authority.

## Empty progress.txt

progress.txt exists and has size zero. Static inspection of the installed HARL logger shows that this file is written by the evaluation logging path, while evaluation was disabled. Training episode metrics were emitted through the Isaac Lab TensorBoard/console logger.

~~~text
classification:
  warning only
~~~

The empty file is not a required training-completion marker and does not override the complete TensorBoard and checkpoint evidence.

## Learning Trends

Frozen windows:

~~~text
early:
  points 1-33, steps 300-9900

middle:
  points 151-183, steps 45300-54900

late:
  points 301-333, steps 90300-99900
~~~

### Environment And Assignment Metrics

| Metric | Early mean | Middle mean | Late mean | Final | Best observed |
| --- | ---: | ---: | ---: | ---: | ---: |
| coverage_ratio | 0.215162 | 0.449275 | 0.454388 | 0.480200 | 0.552467 at 85800 |
| new_viewpoints | 0.065859 | 0.113838 | 0.114848 | 0.120000 | 0.156667 at 32100 |
| mean_reward | 0.358037 | 0.617816 | 0.624151 | 0.660066 | 0.850355 at 32100 |
| Total_Reward | -27.386697 | 88.991199 | 87.048137 | 111.566460 | 170.783157 at 32100 |
| final_reward_mean | -0.091289 | 0.296637 | 0.290160 | 0.371888 | 0.569277 at 32100 |
| noop_count | 0.004949 | 0.011111 | 0.000808 | 0.000000 | minimum 0 at 600 |
| valid_action_count | 2.995051 | 2.988889 | 2.999192 | 3.000000 | maximum 3 at 600 |
| budget_trigger_count | 1.429091 | 1.370404 | 0.866263 | 0.826667 | n/a |
| budget_ratio_mean | 0.373449 | 0.336648 | 0.338826 | 0.339728 | n/a |

Coverage, new viewpoints, and reward improved materially from the early window to the late and final measurements. The nonmonotonic best points and short horizon prevent a convergence claim. These are learning indicators, not production-quality evidence.

### Actor Metrics

| Metric | Early mean | Middle mean | Late mean | Final | Observed range |
| --- | ---: | ---: | ---: | ---: | ---: |
| agent0/policy_loss | -0.007253 | -0.004088 | -0.002472 | -0.003202 | -0.020623 to 0.000706 |
| agent1/policy_loss | -0.028221 | -0.021629 | -0.011207 | -0.013116 | -0.106929 to -0.000244 |
| agent2/policy_loss | -0.048189 | -0.035127 | -0.019548 | -0.020388 | -0.158098 to -0.002600 |
| agent0/dist_entropy | 0.544863 | 0.275940 | 0.255104 | 0.030011 | 0.004955 to 0.753698 |
| agent1/dist_entropy | 0.543182 | 0.261058 | 0.120117 | 0.429972 | 0.011294 to 0.769756 |
| agent2/dist_entropy | 0.556837 | 0.182630 | 0.185127 | 0.022050 | 0.011506 to 0.757230 |
| agent0/actor_grad_norm | 0.758888 | 0.432047 | 0.314854 | 0.111583 | 0.030969 to 1.356912 |
| agent1/actor_grad_norm | 0.849208 | 0.415123 | 0.172756 | 0.446698 | 0.039286 to 1.644309 |
| agent2/actor_grad_norm | 0.789401 | 0.323467 | 0.285975 | 0.074642 | 0.016083 to 1.610695 |

All actor metrics are finite and bounded in the observed run. Their magnitudes alone do not establish policy usefulness.

Robots 0 and 2 finish with low entropy, while robot 1's entropy rebounds to about 0.43. Low entropy may mean a useful stable policy or a narrow action collapse; entropy alone cannot decide.

The next attribution phase must answer:

~~~text
Does robot 0 deterministically choose useful targets or noop?
Does robot 2 choose useful targets, remain idle, or repeat a narrow pattern?
Why does robot 1 retain materially higher final entropy?
How do these behaviors differ between best_model and final models?
~~~

### Critic And Numerical Health

| Metric | Early mean | Middle mean | Late mean | Final | Notable point |
| --- | ---: | ---: | ---: | ---: | ---: |
| critic/value_loss | 0.235855 | 0.009513 | 0.005211 | 0.004382 | minimum 0.002130 at 75900 |
| critic/critic_grad_norm | 3.879257 | 0.667100 | 0.443631 | 0.426683 | finite initial peak 27.314594 at 300 |
| critic/average_step_rewards | -0.042365 | 0.370042 | 0.429293 | 0.505854 | maximum 0.628213 at 51300 |

The critic stabilized substantially after the initial phase. The initial finite gradient peak was followed by sustained reduction and is not a numerical failure. No emitted scalar contains NaN, positive infinity, or negative infinity.

## Aggregate Participation And 8H-2 Comparison

Phase 9G-8H-2 deterministic one-update baseline:

~~~text
proposal noop:
  [300, 0, 248]

effective idle:
  [300, 0, 239]

executing steps:
  [0, 300, 61]

target completions:
  [0, 5, 2]

Jain executing fairness:
  0.4635069337

Jain completion fairness:
  0.5632183908

resolver rejections:
  all zero
~~~

The 100k sampled-training logs show aggregate effective noop near zero in the late window (0.000808) and zero at the final point. Aggregate valid actions are nearly three and finally exactly three.

This is strong evidence that sampled training improved aggregate effective participation relative to the one-update baseline. It does not prove:

~~~text
robot 0 independently learned useful raw target proposals
robot 2 eliminated long deterministic idle periods
deterministic playback is balanced
per-agent completion fairness improved
noop proposals disappeared, because executing noop is Contract C continuation
~~~

The contexts differ: 8H-2 was deterministic attribution playback, while the 100k metrics were sampled during training. Per-agent proposal/effective attribution is required before a deterministic load-balance conclusion.

## Budget Trend

Budget trigger count fell from an early mean of 1.429091 to a late mean of 0.866263. Budget ratio moved from 0.373449 to 0.338826.

This suggests lower aggregate budget pressure, but does not identify the robot, target, or release reason. It provides no basis to reopen resolver, cooldown, retry, or release semantics. Exact release attribution remains a playback question.

## Checkpoint Integrity

Canonical contract fingerprint:

~~~text
19ef40b574c09c6c54b5e2ffea38e900b383188d2b48737a42b01d0db27c76e6
~~~

### Best Checkpoint

~~~text
directory:
  best_model/

kind / generation:
  best / 10

contract:
  assignment_checkpoint_contract_v2

artifacts:
  actor_agent_robot_0.pt
  actor_agent_robot_1.pt
  actor_agent_robot_2.pt
  critic_agent.pt
  value_normalizer.pt

completion marker:
  valid

size, SHA-256, inventory metadata:
  valid
~~~

### Final Checkpoint

~~~text
directory:
  models/

kind / generation:
  final / 22

contract:
  assignment_checkpoint_contract_v2

artifacts:
  actor_agent_robot_0.pt
  actor_agent_robot_1.pt
  actor_agent_robot_2.pt
  critic_agent.pt
  value_normalizer.pt

completion marker:
  valid

size, SHA-256, inventory metadata:
  valid
~~~

Both children bind to the same fingerprint. Final generation 22 is newer than best generation 10 and exceeds the source-derived minimum final generation 17.

Independent opaque-byte checks recomputed all 10 checkpoint artifact sizes and SHA-256 values with zero mismatches. The recursive scan found no temporary artifact, full-model artifact, legacy numeric actor filename, wrong contract version, or unversioned native lifecycle checkpoint.

Both are classified as validated_weight_continuation_candidate, not exact-resume checkpoints. Optimizer, counter, RNG, environment/resolver, and rollout-buffer state are absent.

The metadata does not record the exact update for best generation 10. This review therefore does not equate it with the TensorBoard reward maximum at step 32100. best_model is retained by the runner's reward criterion; models represents the final update. Reward, coverage, entropy, and fairness may rank them differently.

## Outcome Classification

~~~text
Outcome A candidate
~~~

Technical completion and aggregate learning evidence pass. Sampled training strongly suggests that the prior aggregate effective-idle pattern improved. The result remains a candidate because current evidence cannot show per-agent raw proposals, proposal-to-effective translation, deterministic idle streaks, per-agent completions, or fairness.

## Remaining Uncertainty

~~~text
best versus final per-agent raw target/noop proposals
best versus final per-agent effective idle and execution
per-agent completion distribution and Jain fairness
longest deterministic idle streak by robot
resolver acceptance/rejection attribution by robot and reason
Contract C continuation contribution to low effective noop counts
whether low entropy for robots 0 and 2 is specialization or collapse
whether final is preferable to retained best
~~~

These facts cannot be recovered from aggregate training TensorBoard metrics and must not be inferred.

## Attribution Readiness

Both best_model and models are technically ready for separate actor-only normal-evaluation attribution playback. This means structural/evaluation compatibility and artifact integrity only; no checkpoint was loaded in this phase.

Recommended next phase:

~~~text
Phase 9G-8I-2-0:
Best-vs-Final Proposal-Effective Attribution Comparison Design
~~~

That phase may design, but must not execute, exactly two deterministic 300-step playbacks with separate noncolliding outputs and otherwise identical seed, scenario, lifecycle profile, and maximum-step settings.

This review does not authorize playback execution, 300k continuation, another seed, reward changes, resolver changes, or broader training.

## Explicit Non-Actions

~~~text
No production source behavior was modified.
No test or YAML file was modified.
The offline audit tool was not modified or rerun.
No training or retry was run.
No playback or attribution playback was run.
No evaluation was run.
No checkpoint was loaded or restored.
No checkpoint tensor was deserialized.
No AppLauncher or Isaac Sim process was launched.
No environment was constructed.
No GUI or video operation was performed.
No 300k continuation or new seed was started.
No result file was deleted, renamed, or modified.
No HARL or Conda environment was modified.
No commit was made.
~~~

## Final Recommendation

Accept Phase 9G-8I-1 as ATTRIBUTION-READY WITH NONBLOCKING LOG GAP. Preserve the incomplete console transcript and empty progress.txt warning as documented limitations. Proceed only to the design boundary of Phase 9G-8I-2-0 before any best/final playback is executed.

