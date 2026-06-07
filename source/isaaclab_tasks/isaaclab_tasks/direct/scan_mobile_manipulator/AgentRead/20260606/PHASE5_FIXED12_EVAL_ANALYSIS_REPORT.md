# Phase 5 Fixed-12 Evaluation Analysis Report

## 1. Evaluation Setup

This report analyzes the fixed 12-viewpoint assignment-RL MVP evaluation outputs:

```text
results/assignment_eval/fixed12_phase5/per_episode.csv
results/assignment_eval/fixed12_phase5/summary.csv
```

Evaluated methods:

```text
random
nearest
greedy
assignment_rl
```

The comparison uses the fixed 12-viewpoint MVP scenario. All methods use the same scan environment, same fixed viewpoint set, same current `feasible_mask` / `available_mask` semantics, and the same coverage accounting from the scan environment.

Important scope notes:

- This result only applies to the fixed 12-viewpoint MVP scenario.
- `robot_2 -> viewpoint_5` is a fixed-12 MVP scenario-level capability override.
- The result does not demonstrate arbitrary viewpoint-set generalization.
- Phase 6 sequential duplicate avoidance was not implemented for this evaluation.

## 2. CSV Completeness Check

`per_episode.csv` completeness:

```text
total rows: 20
random: 5 episodes
nearest: 5 episodes
greedy: 5 episodes
assignment_rl: 5 episodes
```

`summary.csv` completeness:

```text
total rows: 4
methods: random, nearest, greedy, assignment_rl
```

Required summary fields are present:

```text
method
success_rate
mean_return
mean_final_coverage
mean_steps_to_full_coverage
mean_coverage_auc
mean_duplicate_count
mean_noop_rate
mean_valid_action_rate
```

No CSV completeness issue was found.

## 3. Summary Table

| method | episodes | success_rate | mean_return | mean_final_coverage | mean_steps_to_full_coverage | mean_coverage_auc | mean_duplicate_count | mean_noop_rate | mean_valid_action_rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| random | 5 | 1.000 | 8.440 | 1.000 | 299.0 | 0.052 | 0.000 | 0.000 | 1.000 |
| nearest | 5 | 1.000 | 175.585 | 1.000 | 126.0 | 0.612 | 0.000 | 0.243 | 1.000 |
| greedy | 5 | 1.000 | 175.585 | 1.000 | 126.0 | 0.612 | 0.000 | 0.243 | 1.000 |
| assignment_rl | 5 | 1.000 | 198.785 | 1.000 | 118.0 | 0.485 | 0.415 | 0.031 | 1.000 |

## 4. Per-Method Observations

### random

Random reached 100% final coverage in all 5 episodes, but it is slow and inefficient:

```text
mean_steps_to_full_coverage: 299.0
mean_coverage_auc: 0.052
mean_return: 8.440
```

The low AUC indicates coverage remains low for most of the episode and only reaches full coverage late.

### nearest

Nearest reached 100% final coverage in all 5 episodes:

```text
mean_steps_to_full_coverage: 126.0
mean_coverage_auc: 0.612
mean_return: 175.585
mean_duplicate_count: 0.000
mean_noop_rate: 0.243
```

The no-op rate is expected after the solver runs out of useful uncovered targets for some agents near the end of the episode. Duplicate assignment is zero.

### greedy

Greedy matched nearest exactly in this fixed scenario:

```text
mean_steps_to_full_coverage: 126.0
mean_coverage_auc: 0.612
mean_return: 175.585
mean_duplicate_count: 0.000
mean_noop_rate: 0.243
```

For the current score definition, greedy behaves equivalently to nearest in the fixed 12-viewpoint MVP layout.

### assignment_rl

Assignment-RL reached 100% final coverage in all 5 episodes:

```text
mean_steps_to_full_coverage: 118.0
mean_coverage_auc: 0.485
mean_return: 198.785
mean_duplicate_count: 0.415
mean_noop_rate: 0.031
mean_valid_action_rate: 1.000
```

It is faster than nearest/greedy by 8 steps on average and much faster than random. It also has the highest mean return. However, it has nonzero duplicate assignment and lower AUC than nearest/greedy.

## 5. Assignment-RL Behavior Analysis

Assignment-RL is stable with respect to final task completion in this fixed scenario:

```text
success_rate: 1.0
mean_final_coverage: 1.0
final_covered_count: 12 for every recorded episode
```

It completes full coverage in 118 steps across all 5 recorded episodes. This is faster than nearest/greedy at 126 steps and random at 299 steps.

The policy is also valid under the current mask:

```text
mean_valid_action_rate: 1.0
```

The main quality issue is duplicate assignment:

```text
mean_duplicate_count: 0.415
```

This means the policy still sometimes sends multiple agents to the same viewpoint in a single step. It does not prevent task success in the current fixed MVP, but it likely explains part of the lower coverage AUC relative to nearest/greedy.

No-op does not look excessive:

```text
mean_noop_rate: 0.031
```

Assignment-RL uses no-op far less often than nearest/greedy. The baseline no-op rate of 0.243 likely comes from agents having no useful unique target late in the episode. Assignment-RL's low no-op rate suggests it tends to keep assigning active viewpoints, sometimes redundantly.

## 6. Comparison Against Random / Nearest / Greedy

Compared with random:

- Assignment-RL is much faster: 118 vs 299 steps to full coverage.
- Assignment-RL has much higher return: 198.785 vs 8.440.
- Assignment-RL has higher coverage AUC: 0.485 vs 0.052.

Compared with nearest/greedy:

- Assignment-RL is faster to full coverage: 118 vs 126 steps.
- Assignment-RL has higher return: 198.785 vs 175.585.
- Assignment-RL has lower coverage AUC: 0.485 vs 0.612.
- Assignment-RL has higher duplicate count: 0.415 vs 0.000.
- Assignment-RL has lower no-op rate: 0.031 vs 0.243.

Interpretation:

Assignment-RL appears to finish slightly earlier and collect higher return, but nearest/greedy maintain better average coverage over time. The RL policy may spend earlier steps moving toward targets that become productive later, while nearest/greedy accumulate coverage more steadily. Duplicate assignments remain a visible inefficiency in the RL behavior.

## 7. Phase 6 Duplicate Avoidance Recommendation

Phase 6 duplicate avoidance is useful, but it does not need to be immediate.

Reasons not to make it mandatory yet:

- Assignment-RL already reaches 100% coverage in all 5 fixed-scenario episodes.
- Assignment-RL is faster than nearest/greedy in mean steps to full coverage.
- Valid action rate is already 1.0.
- No-op rate is low and does not look like the main bottleneck.

Reasons to keep Phase 6 as a serious optional optimization:

- Duplicate assignment is clearly nonzero for assignment-RL.
- nearest/greedy achieve zero duplicate assignment.
- Duplicate choices may be contributing to assignment-RL's lower coverage AUC.
- Duplicate avoidance may improve sample efficiency, coverage smoothness, and multi-robot coordination once training length increases.

Recommendation:

Keep Phase 6 duplicate avoidance as an optional optimization for now. The next step should first analyze behavior over more seeds/checkpoints or inspect per-step diagnostics before adding sequential duplicate masks.

## 8. Current Limitations

- Only the fixed 12-viewpoint MVP scenario was evaluated.
- `robot_2 -> viewpoint_5` is a scenario-level override, not a learned or general feasibility model.
- The evaluation does not test arbitrary or variable viewpoint counts.
- The scan environment remains a high-level task-space skeleton, not a physical robot IK/collision stack.
- The assignment-RL checkpoint evaluated here is compatible with the assignment-mode Discrete/Categorical path only; old 9D continuous checkpoints are not valid for this path.
- Phase 6 duplicate sequential masking was not implemented.

## 9. Recommended Next Step

Recommended next step:

Analyze per-step assignment-RL diagnostics or run a small number of additional bounded fixed-12 evaluation seeds/checkpoints before implementing Phase 6.

If the same duplicate pattern persists, implement Phase 6 as an optional mask/controller-side coordination optimization and compare:

```text
assignment_rl
assignment_rl + duplicate avoidance
nearest
greedy
```

Do not start arbitrary viewpoint-count support yet; the current MVP evidence is fixed-scenario only.
