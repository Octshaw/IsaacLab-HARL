# TASK_PROGRESS

## Current Status

Phase 9G-8I-3-0R completed the documentation-only controlled
initial-condition variation interface and contract design.

Classification:

~~~text
INITIAL-CONDITION-CONTRACT-DESIGN-READY
~~~

Pose-axis classification:

~~~text
POSE-PERMUTATION-SUPPORTED-WITH-RUNTIME-VALIDATION
~~~

Starting committed baseline:

~~~text
167bafaac84f7f8f527af40ed786e4834a7db704
167bafaa docs(assignment): validate 100k best-final attribution comparison
~~~

## Frozen Design

The selected axis permutes the three existing complete base start-pose slots
among fixed robot identities. It preserves the component, ordered N=50
viewpoints, robot order/capabilities, actor mapping, lifecycle contract, reward,
mask, resolver, controller, and checkpoint compatibility.

~~~text
Condition A baseline_identity:
  robot_0->S0, robot_1->S1, robot_2->S2

Condition B pose_cycle_forward:
  robot_0->S1, robot_1->S2, robot_2->S0

Condition C pose_cycle_reverse:
  robot_0->S2, robot_1->S0, robot_2->S1
~~~

Selected architecture:

~~~text
dedicated playback CLI profile
code-owned versioned A/B/C profile registry
default selector = None
one uniform fixed profile per process
strict pre-DirectMARLEnv validation
training hard guard
no new YAML/config file
~~~

The frozen schema is `assignment_initial_condition_contract_v1`. Its canonical
SHA-256 condition fingerprint is separate from checkpoint compatibility and
excludes checkpoint identity/run provenance. Explicit-profile attribution
outputs intentionally add `assignment_initial_condition_manifest.json` beside
the unchanged three attribution artifacts. No-selector historical behavior
remains the exact three-file contract.

## Accepted Prior Evidence

Phase 9G-8I-3-0 remains accepted as `NOT READY`, `SEED-INEFFECTIVE`,
`SELECTION-PARTIALLY-ALIGNED`, and `ONLY-BEST-AND-FINAL-AVAILABLE`. The new
contract resolves only the missing design boundary; it does not authorize a
playback run.

Phase 9G-8I-2-1 remains accepted as:

~~~text
BEST-FINAL-ATTRIBUTION-COMPARISON-COMPLETE
Mixed Outcome A1 + Outcome A3
prefer best_model
~~~

## Files

Created in this phase:

- `AgentRead/20260721/PHASE9G8I30R_CONTROLLED_INITIAL_CONDITION_VARIATION_INTERFACE_AND_CONTRACT_DESIGN.md`
- `AgentRead/20260721/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G8I30R_INITIAL_CONDITION_CONTRACT_DESIGN_20260721.md`

Updated:

- `AgentRead/TASK_PROGRESS.md`

No production source, test, YAML, runtime config, checkpoint, result, HARL, or
Conda behavior changed.

## Verification

~~~text
git diff --check:
  PASS (line-ending warning only)

git status --short --untracked-files=all:
  only the accepted Phase 9G-8I-3-0 documentation chain,
  this Phase 9G-8I-3-0R report/archive,
  and TASK_PROGRESS.md

unexpected changed paths:
  none
~~~

No Python test was required for this documentation-only phase.

## Do Not Do

Do not run playback/evaluation, seed 2/3, training, GUI/video, checkpoint
continuation, a best/final multi-condition comparison, or 300k continuation.
Do not implement random starts, sampled profiles, new coordinates, reward,
resolver, mask, controller, or checkpoint changes.

## Next Step

After review and explicit acceptance only:

~~~text
Phase 9G-8I-3-0R-1:
Controlled Initial-Condition Variation Interface Implementation And Regression
~~~

R-1 may implement only the frozen interface, strict validation,
fingerprint/manifest, training guard, and pure/fake/static regressions. It must
not launch Isaac Sim or run playback/evaluation/training.

## Detailed Reports / Archives

- `AgentRead/20260721/PHASE9G8I30R_CONTROLLED_INITIAL_CONDITION_VARIATION_INTERFACE_AND_CONTRACT_DESIGN.md`
- `AgentRead/20260721/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G8I30R_INITIAL_CONDITION_CONTRACT_DESIGN_20260721.md`
- `AgentRead/20260721/PHASE9G8I30_BEST_FINAL_ROBUSTNESS_AND_LATE_TRAINING_REGRESSION_DIAGNOSIS_DESIGN.md`
- `AgentRead/20260721/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G8I30_ROBUSTNESS_DIAGNOSIS_DESIGN_20260721.md`
- `AgentRead/20260720/PHASE9G8I21_SEQUENTIAL_BEST_FINAL_BOUNDED_ATTRIBUTION_PLAYBACK_EXECUTION_AND_COMPARISON.md`
- `AgentRead/20260720/PHASE9G8I20_BEST_VS_FINAL_PROPOSAL_EFFECTIVE_ATTRIBUTION_COMPARISON_DESIGN.md`
