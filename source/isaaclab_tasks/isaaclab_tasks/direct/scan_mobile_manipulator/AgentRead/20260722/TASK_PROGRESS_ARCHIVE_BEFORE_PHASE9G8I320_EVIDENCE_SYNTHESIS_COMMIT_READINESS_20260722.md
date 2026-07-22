# TASK_PROGRESS

## Current Status

Phase 9G-8I-3-1 completed the paired best-versus-final multi-condition
robustness comparison.

```text
overall classification:
  CONSISTENT-LATE-TRAINING-REGRESSION

checkpoint-selection alignment:
  SELECTION-ALIGNED

starting HEAD:
  9d31b15ff248d87634ae7487d0181ecf8a9349c2
```

The controlled initial-condition implementation and the compared 100k
checkpoint pair were committed before this phase.

## Latest Completed Phase

Exactly three new deterministic final-checkpoint playbacks ran sequentially:

```text
A: baseline_identity
B: pose_cycle_forward
C: pose_cycle_reverse
```

Existing explicit best A, best B1, and best C1 artifacts were reused; no best
checkpoint was rerun. Every final run exited 0 with 300 joint decisions, 900
robot rows, four required artifacts, `models/final/generation 22`, normal
evaluation, and no legacy fallback.

Fresh explicit final A reproduced the accepted historical final-A behavior:

```text
rows:      byte exact
segments:  byte exact
summary:   exact after artifact_paths removal
actions:   all 900 robot rows exact
```

Every formal best/final pair matched the same canonical condition contract and
fingerprint. Duplicate keys/targets, invariant failures, unclassified rows,
nonfinite values, controller mismatches, and segment/reset errors were zero.

## Frozen Results

```text
Condition A: BEST-DOMINANT
Condition B: BEST-DOMINANT
Condition C: MIXED
```

Best won completion fairness, zero-progress count, and budget releases in all
three conditions. Best won coverage in A/B, while final won coverage in C.
Best won total completions in B/C and tied A. The pre-frozen precedence rules
therefore produce `CONSISTENT-LATE-TRAINING-REGRESSION` for these three
descriptive deterministic conditions.

`best_model` was selected from rollout `Total_Reward` on the training
trajectory, not the A/B/C suite. Under the frozen rule, the result is
`SELECTION-ALIGNED`; this is not a claim of global optimality.

## Changes In 9G-8I-3-1

Created documentation:

```text
AgentRead/20260722/PHASE9G8I31_PAIRED_BEST_FINAL_MULTI_CONDITION_ROBUSTNESS_COMPARISON_EXECUTION.md
AgentRead/20260722/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G8I31_MULTI_CONDITION_COMPARISON_EXECUTION_20260722.md
```

Updated:

```text
AgentRead/TASK_PROGRESS.md
```

Created runtime evidence only in the three new Phase 9G-8I-3-1 result
directories and frozen console-log paths. No source, test, YAML/data,
checkpoint, existing result, installed HARL, or Conda file changed.

## Limits / Do Not Do

The result covers one checkpoint pair, seed 1, three fixed robot-slot
conditions, one environment, and 300 deterministic decisions. It is not a
statistical, convergence, physical-safety, or broad generalization claim.

No training, continuation, new seed, stochastic action, GUI/video, best rerun,
final repeat, automatic retry, or commit occurred. Do not authorize broader
runtime work from this result without review.

## Next Step

After review and explicit acceptance only:

```text
Phase 9G-8I-3-2-0:
Multi-Condition Best-Final Evidence Synthesis And Commit Readiness Review
```

That phase should be documentation/review only.

## Detailed Reports / Archives

- `AgentRead/20260722/PHASE9G8I31_PAIRED_BEST_FINAL_MULTI_CONDITION_ROBUSTNESS_COMPARISON_EXECUTION.md`
- `AgentRead/20260722/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G8I31_MULTI_CONDITION_COMPARISON_EXECUTION_20260722.md`
- `AgentRead/20260722/PHASE9G8I310_PAIRED_BEST_FINAL_MULTI_CONDITION_ROBUSTNESS_COMPARISON_DESIGN.md`
- `AgentRead/20260722/PHASE9G8I30R2R_CONTROLLED_INITIAL_CONDITION_RUNTIME_IDENTITY_VALIDATION_RETRY.md`
- `AgentRead/20260720/PHASE9G8I21_SEQUENTIAL_BEST_FINAL_BOUNDED_ATTRIBUTION_PLAYBACK_EXECUTION_AND_COMPARISON.md`
