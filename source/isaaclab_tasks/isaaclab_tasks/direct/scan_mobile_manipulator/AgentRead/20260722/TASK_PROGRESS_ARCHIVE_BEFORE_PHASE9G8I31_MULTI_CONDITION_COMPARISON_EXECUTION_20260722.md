# TASK_PROGRESS

## Current Status

Phase 9G-8I-3-1-0 completed the documentation-only design and static evidence
audit for a paired best-versus-final multi-condition robustness comparison.

```text
classification:
  PAIRED-MULTI-CONDITION-COMPARISON-DESIGN-READY

starting HEAD:
  9d31b15ff248d87634ae7487d0181ecf8a9349c2

starting worktree:
  clean
```

The complete controlled initial-condition implementation and validation chain
is committed at the starting baseline.

## Latest Completed Phase

The design audited the retained 100k checkpoint pair and all relevant existing
runtime artifacts without loading checkpoint tensors or starting the simulator.

Frozen reuse decisions:

```text
formal best A: explicit baseline_identity result
formal best B: explicit pose_cycle_forward B1 result
formal best C: explicit pose_cycle_reverse C1 result

B2/C2:
  deterministic identity evidence only; do not average

historical final A:
  SEMANTICALLY-REUSABLE-BUT-NOT-FORMAL-PAIR
  retain as a cross-check, not the formal final-A pair
```

Frozen minimum new execution set:

```text
explicit final A
explicit final B
explicit final C

total new runs: 3
```

## Frozen Pairing Boundary

Formal pairs require exact canonical condition-contract and fingerprint equality:

```text
A d22778fbe70a5300999c58044177f2632b3c782c931d3414e086142035c516bc
B e9b92541c293de20277a97c61037b1592c01d72e6a84e8e6ba0e3fbe68da630f
C 9f476403513ffb4377405d809fc71e537e1982f4ea30e17fad4ea3f3ec97f320
```

The future runs are final `models`, kind `final`, generation 22,
`normal_evaluation`, no legacy fallback, seed 1, one environment, 300
deterministic decisions, HAPPO/EP/feed-forward, `lifecycle_contract_c`, and
1059/3183/51 interfaces.

Fresh explicit final A must first reproduce the historical no-selector final-A
rows, segments, summary behavior, and all 300 actions. A mismatch stops the
phase before B/C. Every technical, checkpoint, manifest, or condition-pairing
failure also stops execution; no automatic retry is allowed.

## Frozen Analysis Boundary

Primary metrics are:

```text
coverage
total completions
Jain completion fairness
total zero-distance-progress rows
total budget releases
```

The report freezes final-minus-best delta directions, cross-condition win/tie
counts and ranges, per-condition Pareto classes, overall late-training classes,
and a separate checkpoint-selection alignment assessment. No weighted score,
p-value, confidence interval, or broad generalization claim is permitted.

## Files Changed In 9G-8I-3-1-0

Created:

```text
AgentRead/20260722/PHASE9G8I310_PAIRED_BEST_FINAL_MULTI_CONDITION_ROBUSTNESS_COMPARISON_DESIGN.md
AgentRead/20260722/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G8I310_MULTI_CONDITION_COMPARISON_DESIGN_20260722.md
```

Updated:

```text
AgentRead/TASK_PROGRESS.md
```

No production source, test, YAML/data, result, checkpoint, console log,
installed HARL, or Conda file changed.

## Latest Verification

```text
starting committed baseline:             PASS
starting worktree clean:                  PASS
checkpoint metadata/static hashes:       PASS
existing artifact inventory/schema:      PASS
explicit A/B/C condition fingerprints:   PASS
best A/no-selector identity evidence:     PASS
B1/B2 and C1/C2 repeat evidence:          PASS
historical final-A provenance audit:      PASS
documentation paths/date placement:       PASS
git diff --check:                         PASS
documentation-only status audit:          PASS, exactly the three expected Markdown files
```

## Known Limits / Do Not Do

The design covers one retained best/final pair, three fixed same-task pose-slot
permutations, seed 1, one environment, and 300 deterministic decisions. It is
not a convergence, random-seed generalization, statistical significance,
physical-safety, or globally optimal checkpoint result.

No AppLauncher, Isaac Sim, environment, playback, evaluation, checkpoint tensor
load, training, continuation, new seed, GUI/video, or commit occurred.

Do not execute broader evaluation or change the frozen run count, order,
pairing, metrics, or stop rules without review.

## Next Step

After review and explicit acceptance only:

```text
Phase 9G-8I-3-1:
Paired Best-vs-Final Multi-Condition Robustness Comparison Execution
```

That phase may run only the frozen explicit final A/B/C set. Do not start it
automatically.

## Detailed Reports / Archives

- `AgentRead/20260722/PHASE9G8I310_PAIRED_BEST_FINAL_MULTI_CONDITION_ROBUSTNESS_COMPARISON_DESIGN.md`
- `AgentRead/20260722/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G8I310_MULTI_CONDITION_COMPARISON_DESIGN_20260722.md`
- `AgentRead/20260722/PHASE9G8I30R2R_CONTROLLED_INITIAL_CONDITION_RUNTIME_IDENTITY_VALIDATION_RETRY.md`
- `AgentRead/20260722/PHASE9G8I30R2F1_INITIAL_CONDITION_MODULE_IDENTITY_REPAIR_AND_IMPORT_BOUNDARY_REGRESSION.md`
- `AgentRead/20260721/PHASE9G8I30R_CONTROLLED_INITIAL_CONDITION_VARIATION_INTERFACE_AND_CONTRACT_DESIGN.md`
- `AgentRead/20260720/PHASE9G8I21_SEQUENTIAL_BEST_FINAL_BOUNDED_ATTRIBUTION_PLAYBACK_EXECUTION_AND_COMPARISON.md`
