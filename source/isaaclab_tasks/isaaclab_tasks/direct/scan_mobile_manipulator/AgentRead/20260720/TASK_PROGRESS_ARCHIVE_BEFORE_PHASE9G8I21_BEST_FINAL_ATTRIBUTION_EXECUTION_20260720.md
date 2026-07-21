# TASK_PROGRESS

## Current Status

Phase 9G-8I-2-0 completed the documentation-only design and static preflight for two controlled deterministic proposal/effective attribution playbacks of the fresh 100k best and final checkpoints.

Classification:

~~~text
ATTRIBUTION-COMPARISON-PLAN-READY
~~~

The existing Phase 9G-8I-1 documentation remains uncommitted and was preserved.

## Frozen Checkpoints

~~~text
training run:
  results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/
  assignment_happo_n50_phase9g8i1_fresh_100k_policy_noop_load_diagnosis/
  seed-00001-2026-07-20-17-40-33

checkpoint A:
  best_model
  kind best
  generation 10

checkpoint B:
  models
  kind final
  generation 22

shared fingerprint:
  19ef40b574c09c6c54b5e2ffea38e900b383188d2b48737a42b01d0db27c76e6
~~~

Both are native contract-v2 lifecycle_contract_c checkpoints with three independent feed-forward actors and interfaces 1059/3183/51.

## Frozen Playback Boundary

Both future runs use:

~~~text
HAPPO
normal_evaluation
actor-only checkpoint loading
Categorical mode through deterministic=True
one environment
seed 1
300 decisions
same scenario
lifecycle_contract_c
feed-forward recurrent flags false
share_param false
headless cuda:0
existing Phase 9G-8H attribution schema
~~~

Critic and ValueNorm are not restored. No stochastic sampling, ablation, legacy fallback, continuation, video, GUI, or training option is present.

Future outputs are separate and currently absent:

~~~text
best:
  results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/
  assignment_happo_n50_phase9g8i21_best_100k_proposal_effective_attribution/
  seed-00001

final:
  results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/
  assignment_happo_n50_phase9g8i21_final_100k_proposal_effective_attribution/
  seed-00001
~~~

Each must contain exactly the rows CSV, summary JSON, and segments CSV under schema phase9g8h1_assignment_proposal_effective_attribution_v1.

## Comparison Contract

The design freezes:

~~~text
exact best and final commands
sequential execution only
best validation before final starts
900 robot rows and 300 unique decisions per run
proposal/effective/controller invariants
per-agent noop, execution, completion, rejection, streak, segment,
budget, command, and base-motion metrics
team active-count and Jain diagnostics
the exact Phase 9G-8H-2 one-update baseline
low-entropy deterministic-collapse checks
one-update/best/final comparison table
checkpoint preference order
no automatic retry
~~~

The current schema supports XY base-motion attribution but not rotational-motion steps. Unsupported values must not be inferred.

## Safety Boundary

No source, test, YAML, attribution collector, checkpoint, reward, observation, mask, resolver, Contract C, ownership, controller, environment, HARL, or Conda behavior changed.

No checkpoint load, AppLauncher, Isaac Sim, environment construction, playback, training, evaluation, GUI/video, second seed, or 300k continuation ran. No result artifact was modified. No commit was made.

A harmless PowerShell 7.6.3 probe confirmed that LASTEXITCODE remains the native exit code after Tee-Object; no project runtime was invoked.

## Next Step

After review only:

~~~text
Phase 9G-8I-2-1:
Sequential Best-and-Final Bounded Attribution Playback Execution
~~~

That phase may run best once, validate it, run final once, validate it, and populate the frozen comparison. If best fails, final must not start automatically. Neither run may be retried automatically.

Do not begin Phase 9G-8I-2-1 without explicit authorization.

## Detailed Reports / Archives

- AgentRead/20260720/PHASE9G8I20_BEST_VS_FINAL_PROPOSAL_EFFECTIVE_ATTRIBUTION_COMPARISON_DESIGN.md
- AgentRead/20260720/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G8I20_BEST_FINAL_ATTRIBUTION_DESIGN_20260720.md
- AgentRead/20260720/PHASE9G8I1_FRESH_100K_CONTROLLED_TRAINING_EXECUTION_AND_OFFLINE_AUDIT_REVIEW.md
- AgentRead/20260720/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G8I1_TRAINING_RESULT_REVIEW_20260720.md
- AgentRead/20260720/PHASE9G8H2_BOUNDED_PROPOSAL_EFFECTIVE_ATTRIBUTION_PLAYBACK_REPORT.md

