# TASK_PROGRESS

## Current Status

Phase 9G-8I-3-0R-2 attempted the bounded controlled initial-condition runtime
identity validation.

Classification:

~~~text
RUNTIME-IDENTITY-FAIL
~~~

Starting committed baseline remains:

~~~text
167bafaac84f7f8f527af40ed786e4834a7db704
167bafaa docs(assignment): validate 100k best-final attribution comparison
~~~

The accepted uncommitted Phase 9G-8I-3-0, 3-0R, and 3-0R-1 chain remains
preserved. No source was changed during R-2.

## Latest Phase Result

The first frozen run, with no initial-condition selector, passed:

~~~text
best_model, seed 1, one environment, deterministic actor-only evaluation
300/300 steps
900 robot rows / 300 decisions
exact three-file output
zero invariant, duplicate-key, unclassified, nonfinite, or log failures
~~~

Its rows and segments are byte-identical to the accepted Phase 9G-8I-2-1
historical `best_model` output. Its summary is exactly equal after normalizing
only output-path fields. Default-off runtime identity therefore passed.

The second frozen run, explicit `baseline_identity`, failed before environment
construction with:

~~~text
InitialConditionContractError:
explicit assignment_initial_condition_profile requires a project-owned
InitialConditionRequest
~~~

The sequential stop boundary was applied. No retry and no B/C run occurred.

## Root Cause

`play_assignment.py` creates the request from top-level module identity
`assignment_initial_condition`, while the package-loaded environment checks
against
`isaaclab_tasks.direct.scan_mobile_manipulator.assignment_initial_condition`.
The same source file therefore supplies two distinct
`InitialConditionRequest` class objects, and the strict environment
`isinstance` check rejects the request.

This is a project runtime import-identity defect in the new explicit-profile
handoff. It is not a checkpoint, resolver, mask, controller, pose, or numerical
failure.

## Outputs Preserved

~~~text
noselector output:
  results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/
  assignment_happo_n50_phase9g8i30r2_noselector_best_runtime_identity/
  seed-00001

noselector console:
  C:/Users/33506/AppData/Local/Temp/
  phase9g8i30r2_noselector_best_console_20260721.log

explicit A console:
  C:/Users/33506/AppData/Local/Temp/
  phase9g8i30r2_baseline_identity_best_console_20260721.log
~~~

Explicit A created no result directory. B1/B2/C1/C2 result and log paths remain
absent. No artifact was removed, renamed, overwritten, or reused.

## Constraints

Do not run B/C, retry A, compare best/final conditions, train, continue a
checkpoint, use a new seed, run GUI/video, or start a 300k continuation. Do not
patch the import boundary without a separately reviewed repair phase.

No YAML/data, reward, resolver, mask, controller, checkpoint semantic,
installed HARL, or Conda file changed. No commit was made.

## Next Step

After review and explicit acceptance only:

~~~text
Phase 9G-8I-3-0R-2F:
Initial-Condition Runtime Module-Identity Boundary Repair And Regression Design
~~~

The next phase should design the smallest canonical-import repair and a real
import-boundary regression. Runtime retry requires separate later review.

## Detailed Reports / Archives

- `AgentRead/20260721/PHASE9G8I30R2_CONTROLLED_INITIAL_CONDITION_RUNTIME_IDENTITY_VALIDATION.md`
- `AgentRead/20260721/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G8I30R2_RUNTIME_IDENTITY_VALIDATION_20260721.md`
- `AgentRead/20260721/PHASE9G8I30R1_CONTROLLED_INITIAL_CONDITION_INTERFACE_IMPLEMENTATION_AND_REGRESSION.md`
- `AgentRead/20260721/PHASE9G8I30R_CONTROLLED_INITIAL_CONDITION_VARIATION_INTERFACE_AND_CONTRACT_DESIGN.md`
- `AgentRead/20260721/PHASE9G8I30_BEST_FINAL_ROBUSTNESS_AND_LATE_TRAINING_REGRESSION_DIAGNOSIS_DESIGN.md`
- `AgentRead/20260720/PHASE9G8I21_SEQUENTIAL_BEST_FINAL_BOUNDED_ATTRIBUTION_PLAYBACK_EXECUTION_AND_COMPARISON.md`
