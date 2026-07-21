# TASK_PROGRESS

## Current Status

Phase 9G-8I-2-1 executed and validated the frozen sequential deterministic attribution playbacks for the fresh 100k `best_model` and final `models` checkpoints.

Classification:

~~~text
BEST-FINAL-ATTRIBUTION-COMPARISON-COMPLETE
~~~

Both runs used actor-only `normal_evaluation`, deterministic masked `Categorical.mode()`, one environment, seed 1, 300 decisions, `lifecycle_contract_c`, feed-forward actors, `share_param=false`, and the existing Phase 9G-8H attribution schema.

## Latest Results

Both playbacks exited 0 and independently produced:

~~~text
900 robot rows
300 environment decisions
exactly three attribution artifacts
schema phase9g8h1_assignment_proposal_effective_attribution_v1
zero duplicate row keys
zero duplicate effective targets
zero invariant failures
zero unclassified rows
zero nonfinite applicable values
valid segment/reset continuity
~~~

Checkpoint identities:

~~~text
best_model:
  kind best
  generation 10

models:
  kind final
  generation 22

purpose:
  normal_evaluation

legacy_fallback:
  false
~~~

The runs were sequential. Best passed all technical checks before final started. Neither run was retried.

## Comparison Decision

The frozen one-update/best/final comparison supports:

~~~text
Mixed Outcome A1 + Outcome A3

A1:
  both 100k checkpoints remove the prior deterministic robot_0 noop collapse
  and robot_2 idle-noop asymmetry

A3:
  best_model is healthier than final models on completion balance,
  budget burden, coverage, and robot_1/robot_2 progress quality
~~~

Headline values:

| Metric | One update | Best | Final |
| --- | --- | --- | --- |
| Proposal noops `[r0,r1,r2]` | `[300,0,248]` | `[0,0,0]` | `[0,0,0]` |
| Executing `[r0,r1,r2]` | `[0,300,61]` | `[300,300,300]` | `[300,300,300]` |
| Completions `[r0,r1,r2]` | `[0,5,2]` | `[6,8,6]` | `[12,5,3]` |
| Total completions | 7 | 20 | 20 |
| First-episode coverage | 0.36 | 0.70 | 0.68 |
| Budget releases | 2 | 1 | 4 |
| Jain completion fairness | 0.5632 | 0.9804 | 0.7491 |
| Mean active robots | 1.2033 | 3.0 | 3.0 |

Checkpoint preference:

~~~text
prefer best_model
~~~

Final is technically healthy and robot 0 improves, but robots 1 and 2 show more zero-motion/zero-progress execution and greater budget pressure. Resolver rejection remains zero in both runs.

## Active Architecture

The committed Phase 9G-8 lifecycle architecture remains unchanged:

~~~text
lifecycle_contract_c
actor observation 1059
shared observation 3183
action dimension 51
feed-forward HAPPO
three independent actors
shared centralized critic
historical lifecycle mask replay
native checkpoint contract v2
~~~

No source, test, YAML, reward, observation, mask, resolver, Contract C, ownership, controller, environment, checkpoint, HARL, or Conda behavior changed in Phase 9G-8I-2-1.

## Files

Created:

- `AgentRead/20260720/PHASE9G8I21_SEQUENTIAL_BEST_FINAL_BOUNDED_ATTRIBUTION_PLAYBACK_EXECUTION_AND_COMPARISON.md`
- `AgentRead/20260720/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G8I21_BEST_FINAL_ATTRIBUTION_EXECUTION_20260720.md`

Updated:

- `AgentRead/TASK_PROGRESS.md`

Runtime results remain only under their separate `results/.../phase9g8i21_*` directories. Console logs remain under the two frozen `%TEMP%` paths.

## Latest Verification

~~~text
starting repository/worktree preflight:
  PASS

best checkpoint metadata/artifact preflight:
  PASS

best bounded attribution playback:
  exit 0
  PASS

best full technical artifact validation:
  PASS

final checkpoint metadata/artifact preflight:
  PASS

final bounded attribution playback:
  exit 0
  PASS

final full technical artifact validation:
  PASS

three-way offline comparison:
  COMPLETE

post-run relevant process check:
  none active

git diff --check:
  PASS (line-ending warning only)
~~~

## Known Limits

This is one deterministic 300-decision trajectory per checkpoint and one seed. It is not a convergence, statistical performance, stochastic-policy, or generalization result. The current attribution schema supports base XY displacement but not rotation, arm motion, or joint-level attribution.

## Do Not Do

Do not automatically run a second seed, stochastic evaluation, GUI/video, checkpoint continuation, 300k training, reward/resolver modification, or broader evaluation. Do not infer that equal execution means equal capability or required equal completion.

## Next Step

After review only, the single recommended bounded phase is:

~~~text
Phase 9G-8I-3-0:
Late-Training Policy-Drift Diagnosis Design Using best_model As Candidate
~~~

Do not start it automatically.

## Detailed Reports / Archives

- `AgentRead/20260720/PHASE9G8I21_SEQUENTIAL_BEST_FINAL_BOUNDED_ATTRIBUTION_PLAYBACK_EXECUTION_AND_COMPARISON.md`
- `AgentRead/20260720/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G8I21_BEST_FINAL_ATTRIBUTION_EXECUTION_20260720.md`
- `AgentRead/20260720/PHASE9G8I20_BEST_VS_FINAL_PROPOSAL_EFFECTIVE_ATTRIBUTION_COMPARISON_DESIGN.md`
- `AgentRead/20260720/PHASE9G8I1_FRESH_100K_CONTROLLED_TRAINING_EXECUTION_AND_OFFLINE_AUDIT_REVIEW.md`
- `AgentRead/20260720/PHASE9G8H2_BOUNDED_PROPOSAL_EFFECTIVE_ATTRIBUTION_PLAYBACK_REPORT.md`
