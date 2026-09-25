# Phase B2-R5I-VF ValueNorm Runtime-Fingerprint Compatibility Qualification Report

Date: 2026-09-02

Classification:
`PHASE-B2-R5I-VF-VALUENORM-RUNTIME-FINGERPRINT-COMPATIBILITY-QUALIFIED-AWAITING-GPT-REVIEW`

This slice repairs and qualifies only ValueNorm state observability. It did not
run Isaac, retry B2-R5I, or change ValueNorm/critic mathematics.

## A. Repository authority

```text
branch:      main
HEAD:        b71d85a32f51be6ada324f870813a56bb45dd396
origin/main: b71d85a32f51be6ada324f870813a56bb45dd396
merge-base:  b71d85a32f51be6ada324f870813a56bb45dd396
staged paths at entry/exit: 359 pre-existing monthly archive migrations
```

The accumulated R0-R5/R5I/RC dirty tree and all unrelated staged state were
preserved. No staging, commit, push, package installation, or installed-HARL
modification occurred.

## B. B2-R5I attempt-2 failure context

Real attempt 2 completed S5 with actor backward/step `15/15`, entered S6, and
physically invoked one live ValueNorm update. Its old pre/post fingerprint was
equal, so R4 issued `STOP — B2-R MUTATION_ATTRIBUTION`; the process stopped
before critic backward/step or S10. That route remains permanently poisoned.

## C. Installed ValueNorm source audit

Installed source:
`C:\isaacenvs\isaac45_harl\Lib\site-packages\harl\common\valuenorm.py`,
SHA-256
`a35471b136567bde0b7fc7be34a7873efa617bdabf9a9074517ff0e3ef3fb8b0`.

The source constructs exactly three mutable fields, in logical order:

1. `running_mean`, shape `input_shape`;
2. `running_mean_sq`, shape `input_shape`;
3. `debiasing_term`, scalar shape `()`.

All are initially written as `nn.Parameter(..., requires_grad=False).to(**tpdv)`.
`update()` mutates the three live attributes in place. With `beta=0.99999`, a
fresh zero batch leaves both running moments at zero but advances
`debiasing_term` from `0` to approximately `1e-5`.

## D. Runtime representation matrix

| Representation | Live field type | Native `state_dict()` keys | Canonical fields | Device |
| --- | --- | --- | --- | --- |
| CPU default float32 | `Parameter` x3 | all three | all three | CPU |
| CPU forced-conversion runtime style | ordinary `Tensor` x3 | empty | all three | CPU |
| CUDA runtime style | ordinary `Tensor` x3 | empty | all three | `cuda:0` |

No installed registered-buffer representation exists, so buffer behavior is
not claimed. Parameter and ordinary-Tensor representations were both executed.

## E. Current B2-R fingerprint root cause

The pre-repair R1 implementation read only `value_normalizer.state_dict()`.
For an installed forced-conversion CPU object, one legitimate update changed
all three live attributes while the native mapping stayed empty. The old B2-R
fingerprint remained
`e15ea1fc6df0c34878fde186fcab94b834f266adf522f1d435f04bac855c3365`
before and after, with zero ValueNorm state entries.

Therefore attempt 2's reported no-mutation conclusion was caused by an
incomplete registration-based observation. This does not retroactively make
that attempt successful.

## F. Canonical live mutable state definition

The new read-only extractor reuses the reviewed checkpoint adapter's installed
implementation inspection and frozen state-key definition. It reads the three
actual attributes directly, validates source-confirmed shapes and homogeneous
dtype/device, requires finiteness, detaches and clones without moving device or
changing dtype, and preserves the frozen field order. It never calls
`state_dict()` and never mutates the ValueNorm object.

The B2-R component fingerprint now fingerprints those canonical clones. Its
logical field evidence is independent of whether the attributes are Parameter
or ordinary Tensor and cannot become empty due to registration loss.

## G. Immutable config/state separation

Mutable mutation attribution contains only the three live tensors. Immutable
identity remains separately covered by the reviewed
`ValueNormalizerTargetInventory`/checkpoint contract: implementation ID,
`input_shape`, `norm_axes`, `beta`, `epsilon`, `per_element_update`, tensor
dtype policy, adapter version, and canonical key order. Config-only identity
cannot satisfy mutation attribution.

## H. Files created/modified

Modified production/evidence files:

- `assignment_value_normalizer_checkpoint.py`;
- `assignment_event_training_evidence.py`;
- `assignment_event_training_gradient_probe.py`;
- `assignment_event_training_critic_mutation.py`.

Modified test support/tests:

- `_assignment_phase_b2_r1_contract_helpers.py`;
- `test_assignment_phase_b2_r1_authority_ownership_fingerprint_pure.py`.

Created:

- `test_assignment_phase_b2_r5i_vf_valuenorm_runtime_fingerprint.py`;
- this report;
- `TASK_PROGRESS_ARCHIVE_BEFORE_B2_R5I_VF_HANDOFF_20260902.md`.

Updated after the archive: top-level `AgentRead/TASK_PROGRESS.md`.

No installed HARL, ValueNorm algorithm, critic/actor/factor math, lifecycle,
P2, GAE, terminal transport, R5 ordering, or public-route source was modified.

## I. CPU default representation evidence

The installed default CPU object exposed three Parameters and the three native
keys. A fresh zero-batch update changed only `debiasing_term`, proving the
field-complete witness does not rely on the running mean changing. Canonical
fingerprint:

```text
pre:  2e6cbacea05b1389dce898cfe467df5f21eb8dcf9d7e4496dcf57d362e17753f
post: 5a95806de0b054c207f0dc73b7bf90bdec423e6e68766b8f5ca4d1e42a76a1e8
```

## J. CPU runtime-style representation evidence

Creating installed ValueNorm while the effective conversion is non-noop on
CPU produced three ordinary float32 Tensors, no registered parameters, and an
empty native `state_dict()`. Canonical fields/shapes remained
`running_mean[1]`, `running_mean_sq[1]`, `debiasing_term[]`. The same zero-batch
witness produced the same canonical pre/post fingerprints as CPU default and
identified only `debiasing_term` as changed.

## K. CUDA runtime-style representation evidence

CUDA was available with PyTorch `2.5.1+cu121`. Installed ValueNorm on `cuda:0`
held three ordinary float32 Tensors and an empty native state mapping. A finite
batch `[1.0, -2.0, 3.5]` changed all three fields:

```text
pre:  ade87b50d42654800d34babd0b0942a9901b1e91a7e6c12728a3d64b3bc6b0d9
post: 890460638f838f48d4a726ba02dbb352032985ab74365e9f4e9402c1856f8661
```

All canonical pre/post fields were finite and remained on `cuda:0`.

## L. Native state_dict blind-spot witness

Two first-class witnesses passed: forced-conversion CPU and CUDA. In both,
native pre/post mappings were empty/equal while live state changed and the new
canonical fingerprint changed. The old/native-only observation detected
nothing; the repaired runtime observation detected mutation.

## M. Canonical pre/post mutation fingerprints

CPU registered and CPU ordinary-Tensor objects with identical logical values
produced identical fingerprints. A one-field running-mean change and a scalar
debiasing-term change each changed the fingerprint. Repeated unchanged reads
were deterministic. Exact CPU/CUDA pre/post digests are recorded in sections I
and K.

## N. Per-field mutation evidence

- CPU default zero batch: `debiasing_term` changed; both moments unchanged.
- CPU runtime-style zero batch: `debiasing_term` changed; both moments unchanged.
- CUDA controlled batch: all three fields changed.
- R4 CUDA receipt values after one update: running mean
  `8.333333425980527e-06`, running mean square
  `5.749999763793312e-05`, debiasing term
  `9.999999747378752e-06`.

## O. Finiteness evidence

Every CPU/CUDA canonical field was finite before and after update. Dedicated
faults injected Inf independently into each of the three live fields; all
three failed closed with `STOP — B2-R NONFINITE_VALUENORM_STATE`. Registration
loss can no longer hide a nonfinite field.

## P. R1 fingerprint regressions

The three existing R1 suites passed. The authority/ownership suite now adds six
dedicated canonical ValueNorm assertions: deterministic repeat, complete field
set, frozen order, Parameter/Tensor logical equality, scalar-shape support, and
scalar mutation detection. The focused VF suite added 53 assertions across
representation, fingerprint, failure, and R4 CUDA evidence.

The failure matrix passed three missing-field faults, one wrong-shape fault,
one unsupported non-Tensor fault, three nonfinite-field faults, one-field
mutation detection, and scalar mutation detection.

## Q. Permit/prestate regressions

The focused CUDA R4 path accepted the correct canonical prestate. It rejected
stale prestate, wrong prestate, wrong minibatch, wrong raw-return digest, and a
duplicate permit. The duplicate witness executed one authorized update before
the second use was rejected; it did not execute a second update. Existing R4
permit regressions also passed.

## R. R4 controlled post-repair qualification

One R4 harness invocation passed using the actual repaired source. It retained
exact `returns[:-1]`, row coverage, raw-target update then same-raw
normalization, finite losses/gradients, real backward/critic Adam steps, actor
freeze, and poisoning behavior.

```text
critic backward:                  10
critic optimizer.step:            10
live ValueNorm.update:              9
enabled sequence counts:         4/4/4
disabled sequence counts:        2/2/0
remainder-safe sequence counts:  3/3/3
post-ValueNorm poison tests:        1
post-critic-step poison tests:      1
```

## S. CUDA-style R4 ValueNorm evidence

The real R4 permit/proxy/receipt machinery ran on installed CUDA runtime-style
ValueNorm without Isaac. One successful receipt bound the correct prestate,
performed one live update, normalized the same raw object/content twice, and
reported finite changed state:

```text
pre:  ade87b50d42654800d34babd0b0942a9901b1e91a7e6c12728a3d64b3bc6b0d9
post: 890460638f838f48d4a726ba02dbb352032985ab74365e9f4e9402c1856f8661
```

Across the success and duplicate-permit witness, physical CUDA R4 updates were
2; successful receipts were 1; permit faults were 5.

## T. R5 full controlled transaction

One reviewed R5 harness invocation passed with the repaired fingerprint source.
Its authoritative successful transaction completed actor/factor, critic/live
ValueNorm, S7, mode restoration, critic rollover, terminal-ledger reset, three
actor rollovers, and S10.

Successful transaction counts were actor step 8, critic step 1, and live
ValueNorm update 1. Task-wide counts including required disposable failures
were actor step 33, critic step 3, and live ValueNorm update 4.

## U. S10 evidence

Successful controlled R5 transactions: 1. S10 entries: 1. Quiescence digest:
`7a38f1be0d56c44379566835774b4b503181f805561902e28c3aec288e4229fb`.

## V. Poisoning regressions

R4 post-ValueNorm and post-step poison tests each passed once. R5 actor-step,
post-ValueNorm, post-critic-step, and post-update-audit poison transactions each
passed once. No poisoned transaction reached rollover or S10. The genuine
no-change safety classification remains active through the existing
`mutated=false -> STOP — B2-R MUTATION_ATTRIBUTION` regression.

## W. Static/private/public guards

```text
reviewed backward executors:              1
reviewed actor optimizer.step executors:  1
reviewed critic optimizer.step executors: 1
reviewed live ValueNorm executors:         1
R5 actor / critic sequence calls:        1 / 1
private dependency edges:                  18
scheduler steps:                             0
R5I adapter new backward/step/VN calls: 0 / 0 / 0
R5I adapter env reset/step/make calls:        0
public production files scanned:             57
public private-route references:               0
```

The new extractor is read-only evidence utility and introduces no mutation
authority or public/private route leak.

## X. Exact execution counts

```text
ValueNorm representation probes:
  CPU default:             1
  CPU runtime-style:       1
  CUDA runtime-style:      1
representation live ValueNorm.update:
  CPU:                     2
  CUDA:                    1
focused R4 CUDA live updates:
  success + duplicate witness: 2
canonical mutations detected:
  representation + R4 CUDA: 5
native state_dict blind-spot witnesses: 2
dedicated R1 canonical assertions: 6
focused VF assertions: 53
checkpoint adapter pytest: 8 passed
R4 controlled harness invocations: 1
R4 successful non-poison sequences: 3
R4 critic backward / step / ValueNorm: 10 / 10 / 9
R4 post-ValueNorm / post-step poison: 1 / 1
R4 CUDA successful receipts / permit faults: 1 / 5
R5 successful full transactions / S10: 1 / 1
R5 success actor / critic / ValueNorm steps: 8 / 1 / 1
R5 task-wide actor / critic / ValueNorm steps: 33 / 3 / 4
Isaac/AppLauncher/SimulationApp actions: 0
checkpoint weight I/O: 0
training/evaluation/playback: 0
public route activations: 0
```

## Y. Retained historical poison/nonclaims

Attempts 1 and 2 remain `PARTIAL_UPDATE / POISONED / STOPPED`; neither is
rehabilitated or rewritten as success. B2-R5I remains NOT COMPLETE. This
qualification does not establish a successful real full learner transaction,
real integration, training-update readiness, convergence, policy quality,
checkpoint continuation, B2-R6, B2-R7, or public-route readiness.

## Z. GPT-review boundary

B2-R5I-VF is qualification complete and awaiting independent GPT review. A
further real Isaac reentry is NOT AUTHORIZED. B2-R6a/R6b, B2-R7, training,
long training, evaluation/playback, checkpoint I/O, public activation,
staging, commit, and push remain outside this slice.

The pre-handoff archive is byte-exact: 3,452 bytes, SHA-256
`9d431844c8944b7c61b676ad81c32d701ca66fc16da0adfee05554c289ae23b5`.

