# Lifecycle-aware Dynamic MRTA — Task Progress

Updated: 2026-09-02

## Current status

```text
B2-R0: GPT REVIEW PASS / FROZEN
B2-R1 through B2-R5: GPT REVIEW PASS / CLOSED
B2-R5I-RC: GPT REVIEW PASS / CLOSED

B2-R5I attempt 1: PARTIAL_UPDATE / POISONED / STOPPED
B2-R5I attempt 2: PARTIAL_UPDATE / POISONED / STOPPED
B2-R5I-VF:
  VALUENORM RUNTIME-FINGERPRINT COMPATIBILITY QUALIFICATION COMPLETE
  AWAITING GPT REVIEW
ValueNorm fingerprint: CANONICAL LIVE-STATE QUALIFIED / AWAITING GPT REVIEW

B2-R5I: NOT COMPLETE
successful real full learner transactions / real S10: 0 / 0
further real Isaac reentry: NOT AUTHORIZED
real Isaac full-learner integration: NOT ESTABLISHED
training-update readiness: NOT YET ESTABLISHED
B2-R6a/R6b and B2-R7: NOT AUTHORIZED
public learned-policy route: DORMANT / BLOCKED
training / long training: NOT AUTHORIZED
```

Classification:
`PHASE-B2-R5I-VF-VALUENORM-RUNTIME-FINGERPRINT-COMPATIBILITY-QUALIFIED-AWAITING-GPT-REVIEW`

## Latest completed work

Installed HARL ValueNorm loses Parameter registration when its construction
`.to(**tpdv)` is an effective conversion: forced CPU and CUDA runtime objects
hold ordinary Tensor attributes and expose an empty native `state_dict()`.
The old B2-R fingerprint therefore observed no live fields and missed a real
mutation.

The reviewed checkpoint adapter now exposes a read-only, device-preserving
runtime extractor. B2-R fingerprints and R4 receipts use its canonical live
attributes in frozen order: `running_mean`, `running_mean_sq`,
`debiasing_term`. Shapes, dtype/device and finiteness are checked; immutable
configuration remains separately bound. ValueNorm and critic mathematics are
unchanged.

## Qualification evidence

```text
CPU default / runtime-style / CUDA probes: 1 / 1 / 1
CPU / CUDA representation-probe updates: 2 / 1
canonical mutations detected, including R4 CUDA: 5
native state_dict blind-spot witnesses: 2
dedicated R1 canonical assertions: 6
focused VF assertions: 53
checkpoint adapter suite: 8 passed
R4 controlled backward / step / ValueNorm: 10 / 10 / 9
R4 CUDA success receipts / permit faults: 1 / 5
R5 successful full transactions / S10: 1 / 1
R5 task-wide actor / critic / ValueNorm steps: 33 / 3 / 4
executor cardinality backward/actor/critic/ValueNorm: 1/1/1/1
private dependency edges / public references: 18 / 0
Isaac/AppLauncher / checkpoint I/O / training-eval-playback: 0 / 0 / 0
```

CPU registered and CPU ordinary-Tensor objects with equal live values produced
equal canonical fingerprints. On CUDA the controlled update changed all three
fields and R4 produced one finite canonical receipt. Missing fields, wrong
shape/type, nonfinite fields, stale/wrong prestate, wrong minibatch/raw digest,
and duplicate permit all failed closed. R4/R5 poisoning regressions remained
unchanged.

## Files

Production/evidence modified:

- `assignment_value_normalizer_checkpoint.py`
- `assignment_event_training_evidence.py`
- `assignment_event_training_gradient_probe.py`
- `assignment_event_training_critic_mutation.py`

Test support modified/created:

- `_assignment_phase_b2_r1_contract_helpers.py`
- `test_assignment_phase_b2_r1_authority_ownership_fingerprint_pure.py`
- `test_assignment_phase_b2_r5i_vf_valuenorm_runtime_fingerprint.py`

Detailed records:

- `202609/20260902/PHASE_B2_R5I_VF_VALUENORM_RUNTIME_FINGERPRINT_COMPATIBILITY_QUALIFICATION_REPORT.md`
- `202609/20260902/TASK_PROGRESS_ARCHIVE_BEFORE_B2_R5I_VF_HANDOFF_20260902.md`

The archive is byte-exact: 3,452 bytes, SHA-256
`9d431844c8944b7c61b676ad81c32d701ca66fc16da0adfee05554c289ae23b5`.
No installed HARL file was modified.

## Do not do

Both historical real routes remain permanently poisoned. Do not run Isaac,
AppLauncher or another B2-R5I reentry without new authorization. Do not begin
B2-R6 or B2-R7, train, evaluate/play back, perform checkpoint weight I/O,
activate the public route, stage, commit, or push.

## Next step

Independent GPT review of B2-R5I-VF.
