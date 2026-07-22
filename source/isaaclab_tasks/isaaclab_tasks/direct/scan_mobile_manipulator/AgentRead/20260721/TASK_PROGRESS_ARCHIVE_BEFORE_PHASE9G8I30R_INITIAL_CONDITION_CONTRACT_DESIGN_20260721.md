# TASK_PROGRESS

## Current Status

Phase 9G-8I-3-0 completed the documentation-only design and static preflight for a best-versus-final robustness and late-training-regression diagnosis.

Classification:

~~~text
NOT READY
~~~

The starting repository was clean at committed HEAD:

~~~text
167bafaac84f7f8f527af40ed786e4834a7db704
167bafaa docs(assignment): validate 100k best-final attribution comparison
~~~

## Latest Findings

Evaluation seed classification:

~~~text
SEED-INEFFECTIVE
~~~

`play_assignment.py --seed` reseeds Python, NumPy, PyTorch CPU/CUDA, Warp, and Replicator through Isaac Lab. The frozen scenario nevertheless has fixed robot poses, a persisted fixed-order N=50 viewpoint CSV, no reset events, no action/observation noise, deterministic lifecycle/controller state, and masked `Categorical.mode()` policy actions. No relevant runtime state consumes the changed RNG state.

No currently supported, non-source-modifying, same-contract controlled initial-condition variation was found. Therefore seeds 2 and 3, four new output/log paths, and four playback commands were deliberately not frozen. No new execution phase is authorized.

## Best Selection And History

Best-checkpoint selection uses:

~~~text
sum over one 300-step rollout of
mean over environments and robots of assignment final_reward
~~~

The runner compares with strict `>` after every rollout/update because `log_interval=1`; ties do not overwrite and evaluation is not involved. Selection is classified:

~~~text
SELECTION-PARTIALLY-ALIGNED
~~~

Coverage/completion reward effects are represented, while per-agent progress, budget-release count, completion concentration, and fairness are indirect or absent. Selected path-cost shaping was disabled with scale 0.0.

TensorBoard record highs, runner save order, save cadence, generation sequence, and artifact timestamp recover the retained best as post-update 107, selected by rollout-107 `Total_Reward` at step 32100. Generation 10 alone was not used as the inference.

Checkpoint history classification:

~~~text
ONLY-BEST-AND-FINAL-AVAILABLE
~~~

Regular checkpoints were overwritten in `models/`, best improvements were overwritten in `best_model/`, periodic snapshots were disabled, and the archive contains only the same final best/models children. The deterministic behavior-drift onset cannot be localized between updates 107 and 333.

## Accepted Runtime Evidence

Phase 9G-8I-2-1 remains accepted unchanged:

~~~text
BEST-FINAL-ATTRIBUTION-COMPARISON-COMPLETE
Mixed Outcome A1 + Outcome A3
prefer best_model
~~~

The seed-1 best/final outputs remain authoritative baseline evidence and must not be rerun. They do not establish a robust multi-condition regression conclusion.

## Files

Created:

- `AgentRead/20260721/PHASE9G8I30_BEST_FINAL_ROBUSTNESS_AND_LATE_TRAINING_REGRESSION_DIAGNOSIS_DESIGN.md`
- `AgentRead/20260721/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G8I30_ROBUSTNESS_DIAGNOSIS_DESIGN_20260721.md`

Updated:

- `AgentRead/TASK_PROGRESS.md`

No production source, test, YAML, runtime configuration, checkpoint, result, HARL, or Conda file was modified.

## Verification

Static inspection included source, installed dependency selection/seed code, retained metadata, TensorBoard scalars, result-tree inventory, ZIP member names, and accepted attribution CSV/JSON files.

Final documentation checks:

~~~text
git diff --check:
  PASS (line-ending warning only)

git status --short --untracked-files=all:
  only TASK_PROGRESS.md plus the Phase 9G-8I-3-0 report and archive

TASK_PROGRESS archive versus committed predecessor:
  exact content match
~~~

No checkpoint tensor was deserialized and no checkpoint loader was called.

## Known Blocker

The current playback interface has no validated same-contract initial-condition selector. Alternate existing scenarios change target/component geometry, while the alternate three-robot pose file has no active component-mesh scenario/CLI selection boundary.

## Do Not Do

Do not run seed 2/3, Phase 9G-8I-3-1, playback, evaluation, training, stochastic actions, GUI/video, checkpoint continuation, or 300k continuation. Do not treat uncontrolled GPU nondeterminism as an experiment axis. Do not change reward, resolver, Contract C, controller, or checkpoint selection before a separate reviewed design.

## Next Step

After review only, recommend:

~~~text
Phase 9G-8I-3-0R:
Controlled Initial-Condition Variation Contract Design
~~~

This must establish a source-supported, recorded, same-task initial-condition identity before any paired best/final robustness execution is designed.

## Detailed Reports / Archives

- `AgentRead/20260721/PHASE9G8I30_BEST_FINAL_ROBUSTNESS_AND_LATE_TRAINING_REGRESSION_DIAGNOSIS_DESIGN.md`
- `AgentRead/20260721/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G8I30_ROBUSTNESS_DIAGNOSIS_DESIGN_20260721.md`
- `AgentRead/20260720/PHASE9G8I21_SEQUENTIAL_BEST_FINAL_BOUNDED_ATTRIBUTION_PLAYBACK_EXECUTION_AND_COMPARISON.md`
- `AgentRead/20260720/PHASE9G8I20_BEST_VS_FINAL_PROPOSAL_EFFECTIVE_ATTRIBUTION_COMPARISON_DESIGN.md`
- `AgentRead/20260720/PHASE9G8I1_FRESH_100K_CONTROLLED_TRAINING_EXECUTION_AND_OFFLINE_AUDIT_REVIEW.md`
- `AgentRead/20260720/PHASE9G8H2_BOUNDED_PROPOSAL_EFFECTIVE_ATTRIBUTION_PLAYBACK_REPORT.md`
