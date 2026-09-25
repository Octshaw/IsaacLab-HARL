# Phase B2-R2 Controlled Backward / No-Step Gradient Probe Implementation Report

Date: 2026-09-01

Classification:

```text
PHASE-B2-R2-CONTROLLED-BACKWARD-NO-STEP-GRADIENT-PROBE-COMPLETE-AWAITING-GPT-REVIEW
```

## A. Repository authority

Starting and closing committed authority remained:

```text
branch:      main
HEAD:        b71d85a32f51be6ada324f870813a56bb45dd396
upstream:    origin/main
merge-base:  b71d85a32f51be6ada324f870813a56bb45dd396
relationship: HEAD == origin/main == merge-base
```

The starting dirty tree contained exactly the uncommitted B2-R0/R1 reports,
archives, four private R1 contract modules, R1 helper/tests, and the R1
`TASK_PROGRESS.md` handoff. They were preserved. No file was staged or
committed. The user-supplied starting phase authority is:

```text
B2-R0: GPT REVIEW PASS / FROZEN
B2-R1: GPT REVIEW PASS / CLOSED
B2-R2: explicitly authorized implementation/verification slice
```

## B. Frozen inputs used

B2-R2 reused the R1 update/config authority, canonical fingerprints,
ownership/disjointness validator, immutable actor/critic plans, backward-only
single-use permits, and S0-S10 state machine. A new immutable
`B2R2ProbeAuthorityV1` wraps the frozen R1 authority and binds:

- slice identity `B2-R2`;
- only backward, gradient inspection, and gradient cleanup as allowed;
- optimizer/scheduler step, live ValueNorm update, parameter/optimizer-state
  mutation, Isaac, training, checkpoint I/O, and public activation as forbidden;
- exact per-invocation expected backward counts `actor=4`, `critic=3`;
- exact expected optimizer-step and live-ValueNorm-update counts `0/0`.

The R0 actor formula was retained: real evaluation uses planned DVM rows and
the PPO loss graph uses only planned active-and-DVM rows, original behavior
logprobs, normalized controlled advantages, and full-index factor values. The
critic target remains the exact synthetic `critic_buffer.returns[:-1]` slice.
No GAE or stock `compute_returns()` was executed.

## C. Files created or modified

Created:

- `assignment_event_training_gradient_probe.py`;
- `assignment_event_training_gradient_guards.py`;
- `scripts/environments/_assignment_phase_b2_r2_gradient_probe_helpers.py`;
- `scripts/environments/test_assignment_phase_b2_r2_controlled_backward_no_step_gradient_probe.py`;
- this report;
- `AgentRead/202609/20260901/TASK_PROGRESS_ARCHIVE_BEFORE_B2_R2_HANDOFF_20260901.md`.

Modified:

- `assignment_event_training_evidence.py`: one narrow compatibility repair,
  flattening 0-dimensional tensors before byte-view hashing so the installed
  ValueNorm scalar `debiasing_term` can be fingerprinted;
- `test_assignment_phase_b2_r1_permits_ordering_static_guards_pure.py`: the R1
  public scan now excludes all explicitly private `assignment_event_training_*`
  extension modules, including R2, while retaining 57 production files;
- `AgentRead/TASK_PROGRESS.md` after its byte-exact archive.

No public wrapper, runner, lifecycle, observation, DVM, reward, resolver,
controller, profile, checkpoint implementation, or installed HARL file changed.

## D. Real versus synthetic classification

REAL:

- three installed `harl.algorithms.actors.happo.HAPPO` wrappers;
- three real installed `StochasticPolicy` actor modules and their parameters;
- three real Adam actor optimizers;
- one installed `harl.algorithms.critics.v_critic.VCritic` wrapper;
- its real installed `VNet`, parameters, and Adam optimizer;
- installed actor `evaluate_actions()` and critic `get_values()`/
  `cal_value_loss()` seams;
- real PyTorch forward graphs, `Tensor.backward()`, gradients, gradient
  fingerprints, and norms.

SYNTHETIC / CONTROLLED:

- CPU-only `T=2`, `E=3`, `M=3`, `N=4`, `B=6` canonical row fixture;
- compact controlled observation dimensions and deterministic inputs;
- DVM/active patterns and historical proposal/logprob fixture;
- exact `[T+1,E,1]` return storage fixture;
- disposable deep-copied ValueNorm used by the installed critic loss;
- no Isaac environment, rollout, runtime terminal evidence, or training loop.

This is real autograd evidence, not real Isaac/runtime identity.

## E. Actual ownership result

Before every probe, the actual constructed topology passed the R1 hard
precondition:

- every actor optimizer owned exactly its actor module parameters;
- the three actor parameter sets were mutually disjoint;
- the critic optimizer owned exactly the critic parameters;
- critic and actor parameter sets were disjoint;
- shared-parameter mode was false;
- all gradients were absent;
- all parameters, optimizer state, and live ValueNorm state were finite.

The same hard ownership check ran again during post-probe snapshots. An
intentional cross-component graph produced a foreign gradient and was rejected
with `STOP — B2-R MUTATION_ATTRIBUTION` after backward and before cleanup.

## F. Pre-probe fingerprints

Every probe snapshot bound:

- R2 and underlying R1 authority digests;
- frozen-input and exact actor/critic plan digests;
- factor digest for actor probes;
- all actor module/mode/optimizer/gradient fingerprints;
- critic module/mode/optimizer/gradient fingerprint;
- complete live ValueNorm state;
- ownership evidence digest.

Optimizers were constructed before snapshots and retained empty Adam state.
No optimizer state was lazily initialized because no step ran.

The initial attempt was rejected before any backward because R1 byte hashing
did not support a 0-dimensional ValueNorm tensor. The narrow flatten-before-byte
repair was applied, its R1 fingerprint regression passed, and the rejected run
executed zero backward and changed no state.

## G. Actor probe cases

Per complete verification invocation:

1. Forced-only actor:
   - DVM and active-and-DVM loss populations were empty;
   - policy evaluation, loss, permit consumption, and backward were skipped;
   - backward count `0` and factor exact unchanged.
2. Mixed-DVM/nondegenerate actor:
   - planned partition rows: six;
   - DVM evaluation rows: `(0,1,3,4)`;
   - active-and-DVM loss rows: `(0,3)`;
   - rows `1` and `4` were DVM-valid but inactive;
   - rows `2` and `5` were forced/off-DVM;
   - real installed `evaluate_actions()` ran;
   - one real backward produced finite, nonzero owned gradients.
3. Excluded-row perturbation:
   - only forced/off-DVM stored sentinel values at rows `2` and `5` changed;
   - selected loss was exact equal;
   - complete owned-gradient evidence digest was exact equal;
   - this supplied machine-checkable graph exclusion evidence.

The successful mixed/nondegenerate actor aggregate gradient norm was:

```text
2.562572114267406
```

The clip seam was not executed. A no-mutation projected clipped norm was
calculated as `min(aggregate_norm, max_grad_norm)` for evidence only.

## H. Exact actor row/behavior binding

The probe checked and then indexed only immutable R1 plan fields:

- update ID and config digest;
- actor ID, epoch, and minibatch;
- partition, DVM evaluation, and active-and-DVM loss indices;
- original rollout behavior-logprob field identity and exact tensor digest;
- full-index factor input digest.

Actual DVM/active tensors were audited for exact equality with those plan rows.
Wrong partition, loss, DVM/active relation, behavior digest, actor, minibatch,
update, or config failed before backward. The off-DVM `0.0` sentinel was never
indexed by the real PPO loss.

## I. DVM graph-exclusion evidence

The real graph was constructed only from `active_and_dvm_loss_indices=(0,3)`.
DVM-but-inactive rows participated only in a no-grad DVM evaluation audit, and
off-DVM rows participated in neither evaluation nor loss. Perturbing only the
two off-DVM behavior entries changed the full frozen-input digest but changed
neither selected loss nor gradient evidence. Attempts to insert an inactive-DVM
or off-DVM row into the loss set failed with
`STOP — B2-R FORCED_ROW_POLICY_LEAK` before backward.

## J. Actor gradient audit

For every owned actor parameter after real backward, evidence recorded:

- absent/present state;
- shape, dtype, CPU device classification;
- finite result, exact byte digest, norm, and zero/nonzero classification.

Aggregate norm was finite and at least one owned gradient was nonzero. One
custom finite-forward/infinite-backward graph was safely rejected as
`STOP — B2-R NONFINITE_GRADIENT`; cleanup and exact post-state restoration
still passed.

## K. Critic target binding

The controlled storage had exact shape `[T+1,E,1]`. Only
`returns_storage[:-1]`, flattened to six canonical physical rows, was digested
and accepted. The final structural slot contained the distinct diagnostic value
`123.0` and was excluded. All six rows were in the one approved exact-coverage
minibatch. Wrong target digest and nonfinite raw target fixtures failed before
backward.

## L. Critic gradient evidence

The real installed `VCritic.get_values()` forward and
`VCritic.cal_value_loss()` math ran on the six planned rows. One successful
backward produced finite, nonzero critic-owned gradients with aggregate norm:

```text
20.694203037154438
```

One cross-actor dependency was rejected as a foreign gradient, and one
finite-forward/infinite-backward critic fixture was rejected as nonfinite.
Both failure paths cleared every gradient and restored exact state.

## M. Foreign-gradient audit

Successful actor backward left both other actors and the critic without any
gradient. Successful critic backward left all actors without any gradient.
A present foreign gradient is rejected even when its numeric value is zero,
preventing hidden cross-component graph dependencies.

## N. Optimizer-step trap

Actor and critic step attempts each called a rejecting
`B2ROptimizerStepTrapV1`. The trap increments an attempt counter and raises
`STOP — B2-R UNAUTHORIZED_OPTIMIZER_STEP` before any delegation. Exact
component fingerprints before/after each rejection were equal.

Per verification invocation:

```text
optimizer-step attempts trapped: 2
optimizer.step executed:         0
```

Across both passing R2 invocations, four attempts were trapped and zero steps
executed.

## O. ValueNorm safety

The installed critic loss was given a disposable deep copy of the live
ValueNorm. The disposable copy changed, proving installed update/normalize loss
semantics were exercised. The live object's complete pre/post fingerprints
remained exact equal.

A deliberate call to `B2RLiveValueNormTrapV1.update()` raised
`STOP — B2-R VALUENORM` before delegating. Per invocation one attempt was
trapped and zero live updates executed; cumulatively two attempts were trapped
and zero live updates executed.

This does not redefine or prove the future R4 live training-update schedule.

## P. Gradient cleanup and no-mutation audit

Every successful or post-backward failed probe cleared all actor and critic
gradients to `None` before returning/raising. Dirty-gradient probe start and an
explicit incomplete-cleanup fixture were rejected with
`STOP — B2-R MUTATION_ATTRIBUTION`.

After cleanup, the full topology snapshot was exact equal to its pre-probe
snapshot. The initial snapshot before the complete matrix and final snapshot
after all probes/traps were also exact equal. Therefore:

- actor parameters changed: `0`;
- critic parameters changed: `0`;
- optimizer state changes: `0`;
- live ValueNorm state changes: `0`;
- module mode changes: `0`.

## Q. Fault-injection matrix

Each complete invocation passed 32 precise expected-STOP assertions:

- permit/authority: no permit, duplicate, wrong actor, wrong minibatch, stale
  config, and stale update;
- actor graph: forced-only attempted backward, off-DVM insertion, inactive-DVM
  insertion, behavior mismatch, wrong partition, nonfinite loss, and nonfinite
  gradient;
- foreign actor-to-critic dependency;
- dirty start, incomplete cleanup, pre-S3/S5 ordering, and continuation after
  poison;
- critic: wrong target digest, nonfinite target, nonfinite loss, nonfinite
  gradient, and critic-to-actor dependency;
- actor/critic optimizer-step traps and live ValueNorm trap;
- AST faults for unreviewed backward, optimizer step, ValueNorm update, stock
  HAPPO, stock VCritic, and stock returns.

All failures retained exact STOP category and bounded stage/field evidence.
No irreversible learner mutation occurred.

## R. Static/public guards

The R2 source guard scanned the probe, guard, helper, and test files and found:

```text
centralized executable backward call sites: 1
untrapped optimizer/scheduler step sites:    0
untrapped live ValueNorm update sites:       0
stock train/update/returns sites:             0
```

The one reviewed call is exactly `loss.backward()` inside
`_execute_backward_v1`. Two test calls target step-trap objects and one targets
the live-ValueNorm trap; none can delegate.

Public isolation scanned 61 non-R2 repo-local Python files, including all 57
production files, and found zero reference to either private R2 module. Both R2
modules export nothing. All three R1 suites were rerun and passed, including the
57-file R1 public isolation guard.

## S. Verification commands

The approved interpreter was confirmed as:

```text
C:\isaacenvs\isaac45_harl\python.exe
```

Passing checks:

```text
python -m py_compile <four R2 Python files>                         PASS
R2 read-only AST preflight                                         PASS
test_assignment_phase_b2_r1_authority_ownership_fingerprint_pure.py PASS
test_assignment_phase_b2_r1_update_plans_factor_pure.py             PASS
test_assignment_phase_b2_r1_permits_ordering_static_guards_pure.py  PASS
test_assignment_phase_b2_r2_controlled_backward_no_step_gradient_probe.py PASS (twice)
```

HARL emitted its existing Gym deprecation notice during imports. It did not
affect the CPU PyTorch result.

## T. Exact execution counts

One complete passing R2 invocation observed:

```text
actor backward executed:             4
critic backward executed:            3
total backward executed:             7
optimizer.step executed:             0
scheduler.step executed:             0
actor parameter mutations:           0
critic parameter mutations:          0
optimizer-state mutations:           0
live ValueNorm updates:               0
Isaac/runtime rollout actions:        0
training actions:                     0
evaluation/playback actions:          0
checkpoint weight I/O:                0
public route activations:             0
```

The complete passing invocation was intentionally repeated after R1 regression
verification. Cumulative exact counts for this B2-R2 task were therefore:

```text
actor backward executed:             8
critic backward executed:            6
total backward executed:            14
optimizer.step executed:             0
scheduler.step executed:             0
actor parameter mutations:           0
critic parameter mutations:          0
optimizer-state mutations:           0
live ValueNorm updates:               0
Isaac/runtime rollout actions:        0
training actions:                     0
evaluation/playback actions:          0
checkpoint weight I/O:                0
public route activations:             0
```

The earlier 0-dimensional-fingerprint rejection occurred before backward and
adds zero to these counts.

## U. Archive, nonclaims, and handoff

Before rewriting `TASK_PROGRESS.md`, its prior R1 handoff was copied byte for
byte:

```text
source/archive bytes: 7016 / 7016
byte equality: true
SHA-256: 9943511ac40917ec474e72dec4153fb9f87e32cf25c70fc5f6b39ed2fc2d24f6
Git blob: 2dee70dd34e28f8918ba6f8af605745f2217cd69
```

B2-R2 does not establish optimizer-mutation readiness, a full learner update,
live ValueNorm training mutation, R4 source-faithful schedule readiness,
training-update readiness, real Isaac rollout integration, convergence, policy
quality, checkpoint continuation/resume, or public-route readiness.

```text
B2-R0: GPT REVIEW PASS / FROZEN
B2-R1: GPT REVIEW PASS / CLOSED
B2-R2: IMPLEMENTATION COMPLETE / CONTROLLED BACKWARD NO-STEP VERIFICATION COMPLETE /
       AWAITING GPT REVIEW
B2-R3: NOT AUTHORIZED
training-update readiness: NOT YET ESTABLISHED
public learned-policy route: DORMANT / BLOCKED
training: NOT AUTHORIZED
commit: NONE
next: independent GPT review of B2-R2
```
