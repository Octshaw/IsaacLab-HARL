# TASK_PROGRESS

## Current Status

Phase 9G-8I-3-2-0 completed the multi-condition best-final evidence synthesis
and commit-readiness review.

```text
classification:
  COMMIT-READY

overall comparison:
  CONSISTENT-LATE-TRAINING-REGRESSION

checkpoint-selection alignment:
  SELECTION-ALIGNED

committed baseline:
  9d31b15ff248d87634ae7487d0181ecf8a9349c2
```

## Independent Review Result

Read-only recalculation reproduced the formal A/B/C condition pairings,
canonical fingerprints, five primary metrics, per-condition Pareto classes,
overall classification, selection-alignment assessment, and historical Final-A
identity.

```text
Condition A: BEST-DOMINANT
Condition B: BEST-DOMINANT
Condition C: MIXED
```

Best is dominant under A and B. C is mixed because Final improves coverage,
while Best retains advantages in total completions, completion fairness,
zero-progress rows, and budget releases.

Across all conditions, both checkpoints keep all three robots executing for all
300 decisions. Final nevertheless has less balanced productive completion and
substantially more zero-progress, zero-base-motion, and budget-release evidence.
Execution participation alone is therefore not productive load balance.

Production/source blob identity, immutable input hashes, all 27 formal and
historical attribution hashes, best/final checkpoint manifests and opaque file
hashes, condition contracts, and historical Final-A reproduction all passed.
Best and Final share the same checkpoint/inference contract but contain
different actor weights.

## Commit Boundary

The exact seven-document staging set and this documentation commit message are
frozen in the detailed report:

```text
docs(assignment): validate multi-condition late-training regression
```

Result directories, console logs, and checkpoints remain local evidence and
must not be staged. The review covers one checkpoint pair, seed 1, three fixed
start-pose permutations, one environment, and 300 deterministic decisions; it
does not establish statistical or broad generalization.

No source, test, YAML/data, result, checkpoint, console-log, installed HARL, or
Conda behavior changed. No AppLauncher, Isaac Sim, environment, playback,
evaluation, checkpoint load, training, continuation, new seed, new condition,
GUI/video, staging, or commit occurred.

## Next Step

After GPT review, the user may manually stage exactly the seven Markdown files
listed in the report and manually commit them. Do not begin another experiment
automatically; subsequent work requires a separate roadmap decision.

## Detailed Reports / Archives

- `AgentRead/20260722/PHASE9G8I320_MULTI_CONDITION_BEST_FINAL_EVIDENCE_SYNTHESIS_AND_COMMIT_READINESS_REVIEW.md`
- `AgentRead/20260722/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G8I320_EVIDENCE_SYNTHESIS_COMMIT_READINESS_20260722.md`
- `AgentRead/20260722/PHASE9G8I31_PAIRED_BEST_FINAL_MULTI_CONDITION_ROBUSTNESS_COMPARISON_EXECUTION.md`
- `AgentRead/20260722/PHASE9G8I310_PAIRED_BEST_FINAL_MULTI_CONDITION_ROBUSTNESS_COMPARISON_DESIGN.md`
- `AgentRead/20260722/PHASE9G8I30R2R_CONTROLLED_INITIAL_CONDITION_RUNTIME_IDENTITY_VALIDATION_RETRY.md`
- `AgentRead/20260720/PHASE9G8I21_SEQUENTIAL_BEST_FINAL_BOUNDED_ATTRIBUTION_PLAYBACK_EXECUTION_AND_COMPARISON.md`
