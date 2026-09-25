# Lifecycle-aware Dynamic MRTA — Task Progress

Updated: 2026-09-08

## Current status

```text
B2-R0: GPT REVIEW PASS / FROZEN
B2-R1 through B2-R5: GPT REVIEW PASS / CLOSED
B2-R5I-RC: GPT REVIEW PASS / CLOSED
B2-R5I-VF: GPT REVIEW PASS / CLOSED

B2-R5I attempts 1/2/3: PARTIAL_UPDATE / POISONED / STOPPED / HISTORICAL

B2-R5I-CG:
  CRITIC ZERO-EFFECTIVE-GRADIENT CLASSIFICATION QUALIFICATION COMPLETE
  AWAITING GPT REVIEW
critic zero-effective semantics: QUALIFIED / AWAITING GPT REVIEW

B2-R5I: NOT COMPLETE
successful real full learner transactions: 0
real S10 entries: 0
further real Isaac reentry: NOT AUTHORIZED
real Isaac full-learner integration: NOT ESTABLISHED
training-update readiness: NOT YET ESTABLISHED
B2-R6a/R6b and B2-R7: NOT AUTHORIZED
public learned-policy route: DORMANT / BLOCKED
training / evaluation / playback: NOT AUTHORIZED
```

Classification:
`PHASE-B2-R5I-CG-CRITIC-ZERO-EFFECTIVE-GRADIENT-CLASSIFICATION-QUALIFIED-AWAITING-GPT-REVIEW`

## Latest completed work

B2-R5I-CG inspected the installed HARL VCritic/VNet, frozen R0 contract,
reviewed R2/R4/R5 seams, and all eight durable attempt-3 artifacts. The
artifacts do not preserve the real minibatch-1 numeric targets, predictions,
loss branch, `dLoss/dValues`, or per-parameter gradient state. Therefore:

```text
attempt-3 exact zero-gradient mathematical cause:
  UNRESOLVED FROM EXISTING REAL ARTIFACTS
```

This does not alter attempt 3's permanent poisoned/stopped status.

The installed clipped-value loss admits a connected finite nonzero-loss
plateau: when the prediction lies outside the clip interval and the clipped
branch wins `max`, that selected branch is locally constant in the current
prediction. A real VCritic witness produced loss `0.31999996304512024`,
`dLoss/dValues=0`, and 12/12 present finite exact-zero parameter gradients.
An independent exact-target real-VCritic witness produced exact-zero loss and
the same valid zero-gradient structure on CPU and `cuda:0`.

Frozen R0 explicitly allows a proved zero-effective critic case and says Adam
state may still mutate. The former R2/R4 all-minibatches-nonzero guard was
therefore stricter than R0. The narrow repair adds strict classifications:

- `VALID_NONZERO_UPDATE`: connected finite graph and nonzero owned gradient;
- `VALID_ZERO_EFFECTIVE_UPDATE`: connected finite exact-zero derivative,
  installed-loss branch proof, and every required owned gradient present and
  finite exact zero;
- detached/unused/missing-gradient, nonfinite, ownership, and foreign-gradient
  cases: STOP.

This is not a generic “zero is okay” relaxation. Receipts bind update/config,
epoch/minibatch, physical rows, target/prediction digests, branch math,
`dLoss/dValues`, per-parameter gradients, and Adam pre/post evidence.

## Optimizer/count decision

A proved valid-zero-effective minibatch still executes exactly one planned
Adam step, matching installed `VCritic.update` and R0. With fresh zero moments,
optimizer state/counters changed while parameters did not. After a preceding
nonzero step, the zero-current-gradient step advanced Adam `1 -> 2`, decayed
moments, and changed critic parameters.

Count rules remain one backward and one optimizer step per valid processed
minibatch, exactly one of the nonzero/zero-effective counters, and—when
enabled—one ValueNorm update before each backward. Failure after ValueNorm
still poisons the route.

## Latest controlled verification

- Relevant `py_compile`: PASS.
- Focused CG real-VCritic qualification: PASS.
  - designated nonzero witnesses: 2;
  - valid-zero witness contexts: 4;
  - CPU exact-target: 2/2 zero-effective minibatches;
  - CPU mixed Adam: nonzero then clipped-plateau zero-effective;
  - CUDA exact-target: 2/2 zero-effective minibatches on `cuda:0`;
  - detached/unused/missing-gradient faults: fail-closed;
  - NaN/Inf faults: fail-closed;
  - ownership and foreign-gradient faults: fail-closed.
- Full prior R4 regression: PASS, critic backward/step `10/10`, ValueNorm `9`,
  enabled/disabled/remainder sequences, post-ValueNorm poison, and post-step
  poison retained.
- Focused mixed R5 transaction: PASS to S10 with critic classes
  `(VALID_NONZERO_UPDATE, VALID_ZERO_EFFECTIVE_UPDATE)` and counts `(2,2,0)`.
- Full prior R5 regression: PASS to S10 with `(1,1,1)` critic counts and the
  existing integrated poison/fault matrix.
- Static cardinality: backward/actor-step/critic-step/ValueNorm `1/1/1/1`, R5
  actor/critic coordinator calls `1/1`, private edges `18`, public refs `0`.
- The historical standalone R2 aggregate still reports its documented
  static-guard false positive on a later private R3 dependency; production,
  R4, and R5 static guards pass. No allowlist broadening was made.

## Files changed for B2-R5I-CG

Modified:

- `assignment_event_training_gradient_probe.py`
- `assignment_event_training_critic_mutation.py`
- `scripts/environments/_assignment_phase_b2_r4_critic_mutation_helpers.py`
- `scripts/environments/_assignment_phase_b2_r5_full_transaction_helpers.py`
- `AgentRead/TASK_PROGRESS.md`

Created:

- `scripts/environments/test_assignment_phase_b2_r5i_cg_critic_zero_gradient_classification.py`
- `202609/20260908/PHASE_B2_R5I_CG_CRITIC_ZERO_EFFECTIVE_GRADIENT_CLASSIFICATION_REPORT.md`
- `202609/20260908/TASK_PROGRESS_ARCHIVE_BEFORE_B2_R5I_CG_HANDOFF_20260908.md`

The archive is byte-exact to the pre-rewrite progress file:

```text
bytes:  6358
sha256: 9bca3c47a2473bc19ffae6295f45e99d28095969b7dbb243b02146ee1688f2a0
```

The 359 pre-existing staged monthly-archive paths remain exact. Staged-index
SHA-256 remains
`a40169043c3bfffd481a7ed1bddf3e52663d61379bedfd2610781457d11f947c`.
No installed HARL source was modified.

## Retained nonclaims

- Attempts 1/2/3 remain historical poisoned and cannot be reused.
- Attempt 3 is not retrospectively claimed to have been a clipped plateau.
- Successful real transactions and real S10 remain zero.
- B2-R5I is not complete.
- No Isaac/AppLauncher/SimulationApp, attempt 4, checkpoint I/O, training,
  evaluation, playback, public-route activation, B2-R6, or B2-R7 occurred.
- No stage, commit, or push occurred.

## Next step

Independent GPT review of B2-R5I-CG. Wait for explicit authorization. Do not
run attempt 4, begin B2-R6/B2-R7, or start training.

## Detailed reports / archives

- `202609/20260908/PHASE_B2_R5I_CG_CRITIC_ZERO_EFFECTIVE_GRADIENT_CLASSIFICATION_REPORT.md`
- `202609/20260908/TASK_PROGRESS_ARCHIVE_BEFORE_B2_R5I_CG_HANDOFF_20260908.md`
- `202609/20260908/PHASE_B2_R5I_REAL_ISAAC_SINGLE_TRANSACTION_ATTEMPT3_REPORT.md`
- `202609/20260902/PHASE_B2_R5I_VF_VALUENORM_RUNTIME_FINGERPRINT_COMPATIBILITY_QUALIFICATION_REPORT.md`
- `202609/20260902/PHASE_B2_R5I_RC_POST_REPAIR_CONTROLLED_REGRESSION_QUALIFICATION_REPORT.md`
- `202609/20260901/PHASE_B2_R5_CONTROLLED_PRIVATE_FULL_LEARNER_TRANSACTION_INTEGRATION_REPORT.md`
- `202609/20260901/PHASE_B2_R4_CONTROLLED_CRITIC_OPTIMIZER_AND_LIVE_VALUENORM_MUTATION_REPORT.md`
