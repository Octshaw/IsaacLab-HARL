# Phase B2-R5I-CG Critic Zero-Effective-Gradient Classification Report

Date: 2026-09-08 (Asia/Shanghai)

Classification:
`PHASE-B2-R5I-CG-CRITIC-ZERO-EFFECTIVE-GRADIENT-CLASSIFICATION-QUALIFIED-AWAITING-GPT-REVIEW`

This is a controlled plain-PyTorch/HARL diagnostic and narrow
classification-only qualification. It did not run Isaac, AppLauncher,
SimulationApp, a rollout, attempt 4, training, evaluation, playback, or
checkpoint weight I/O. It does not rehabilitate attempt 3 and does not
authorize a further real reentry.

## A. Repository authority

Authority captured before changes/tests:

```text
branch:                  main
HEAD:                    b71d85a32f51be6ada324f870813a56bb45dd396
origin/main:             b71d85a32f51be6ada324f870813a56bb45dd396
merge-base:              b71d85a32f51be6ada324f870813a56bb45dd396
relationship:            HEAD == origin/main == merge-base
working status lines:    393
working status SHA-256:  1b108f9d2eddf83c7c23f83a735b7c50302e92afd146659a68a4a5c4bbb0f214
staged paths:            359
staged-index SHA-256:    a40169043c3bfffd481a7ed1bddf3e52663d61379bedfd2610781457d11f947c
```

The same 359 staged paths and staged-index SHA-256 remained exact after the
implementation and controlled tests. No `git add`, `git commit`, or `git push`
was run. The existing monthly archive migration and unrelated dirty state were
not edited by this slice.

Pre-change qualified identities included:

| Source | SHA-256 |
|---|---|
| `assignment_event_training_evidence.py` | `1d9ae8c460fec99fea40fe0b0d954987d68857f19f47e71e2d7f57e6c8152ed9` |
| `assignment_event_training_gradient_probe.py` | `19c24185436962099c7f0e4b149161ce42349c017dcef4b1338e3c6a370f3a17` |
| `assignment_event_training_actor_mutation.py` | `08eb3442ac52dc4f7fd69434486ee7ec77920c64e614d0a19944f4b163b078e3` |
| `assignment_event_training_critic_mutation.py` | `a9f1e885b35fb749ffd97397d2c991698262dc9d141e30b45d7a45fb3c0bfcaa` |
| `assignment_event_training_full_transaction.py` | `ec42cb68db274f42144489f4e8ef199311c557016c4859475057c1deed417c35` |
| installed `v_critic.py` | `ae66390702efb55099d151c11f28ae533f25ef6d62697949445abd2979708bf3` |
| installed `v_net.py` | `a3760b3fdf290c73bb13a752c0b0d39f69fd6fa207560272954b44a027f427c3` |
| installed `valuenorm.py` | `a35471b136567bde0b7fc7be34a7873efa617bdabf9a9074517ff0e3ef3fb8b0` |

Post-change classifier source identities are recorded in section R.

## B. Attempt-3 failure context

Attempt 3 remains `PARTIAL_UPDATE / POISONED / STOPPED`. Its real S5 actor
sequence completed. S6 critic minibatch 0 completed one finite ValueNorm
update, one finite nonzero backward, and one Adam step. Minibatch 1, physical
rows `(2,3)`, completed the second finite ValueNorm update, then the reviewed
audit found no nonzero owned critic gradient and stopped before its optimizer
step. Real S10 remains zero.

No attempt-3 object, process, update identity, permit, buffer, component, or
state was reused in this task.

## C. Durable artifact inventory

Eight read-only `%TEMP%` attempt-3 artifacts were inspected:

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `b2_r5i_re2_attempt3_pre_mutation_20260907_01.json` | 201525 | `0e90e607755c2de5e5188637623a0fdbf9f65d36e87ca668ce4f6efc9ef695ef` |
| `b2_r5i_re2_attempt3_factor_progress_20260907_01.json` | 6295 | `03b9cf1dbd95e2873fbacd010fa53d21b1c2aa2017406149765686ae568d5937` |
| `b2_r5i_re2_attempt3_critic_progress_20260907_01.json` | 21610 | `4d991a517df679602cf740c5c86f51116887ff34db8f88d3df011dd8c39615bc` |
| `b2_r5i_re2_attempt3_static_pre_20260907_01.json` | 191462 | `b05f3aa3cd4a594dab4b9a880b796e9f44da6ff172e9194623d0f0c5346b0583` |
| `b2_r5i_re2_attempt3_static_post_20260908_01.json` | 191462 | `b05f3aa3cd4a594dab4b9a880b796e9f44da6ff172e9194623d0f0c5346b0583` |
| `b2_r5i_re2_attempt3_post_failure_20260907_01.json` | 2033 | `b76fa048f871d907eea4c20478455c56bb0b8ec8589e3b777fc9062755cba482` |
| `b2_r5i_re2_attempt3_final_receipt_20260907_01.json` | 2033 | `b76fa048f871d907eea4c20478455c56bb0b8ec8589e3b777fc9062755cba482` |
| `b2_r5i_re2_attempt3_result_20260907_01.json` | 217678 | `81370b417e535353352c0f09f748e48af6050a72fba3f1f005843ad2a9e16815` |

## D. Installed VCritic/value-loss source audit

The installed path is source-faithfully:

```text
value_pred_clipped = old_value_pred
                   + clamp(current_value - old_value_pred, -clip_param, +clip_param)
normalized_target = ValueNorm.normalize(raw_return) after ValueNorm.update(raw_return)
error_original     = normalized_target - current_value
error_clipped      = normalized_target - value_pred_clipped
loss_original      = Huber(error_original) or MSE(error_original)
loss_clipped       = Huber(error_clipped) or MSE(error_clipped)
loss_per_row       = max(loss_original, loss_clipped) when clipping is enabled
value_loss         = mean(loss_per_row) * value_loss_coef
```

Installed settings exercised were `use_clipped_value_loss=True`,
`use_huber_loss=True`, `clip_param=0.2`, `huber_delta=10.0`, and
`value_loss_coef=1.0`. `VCritic.update` performs zero-grad, backward, optional
gradient clipping, and then an unconditional Adam step for the processed
minibatch. No installed HARL source or loss formula was changed.

## E. Current R2/R4 gradient-audit semantics

The pre-CG audit treated a backward as valid only when at least one owned
parameter gradient was nonzero. The attempt-3 STOP therefore proved only
`any_nonzero == false`; its durable record did not preserve the per-parameter
distinction between all `grad is None`, all present exact-zero tensors, or a
mixture. Source order proves the audit ran immediately after backward and
before exception cleanup, so the historical witness was not an
after-unintended-clearing observation.

The CG seam retains the unique backward executor and adds graph and
per-parameter classification evidence around it.

## F. Grad None/zero/nonzero taxonomy

The implemented taxonomy is strict:

| Class | Required evidence | Decision |
|---|---|---|
| `VALID_NONZERO_UPDATE` | connected finite scalar loss; finite nonzero `dLoss/dValues`; at least one finite nonzero owned parameter gradient | accept |
| `VALID_ZERO_EFFECTIVE_UPDATE` | connected finite loss; present finite exact-zero `dLoss/dValues`; installed-loss mathematical branch proof; every required owned gradient present, finite, exact zero | accept |
| `GRAPH_DISCONNECT_OR_UNUSED` | detached loss/current value, unused current value, unexpected required `grad is None`, or graph contradiction | STOP |
| `NONFINITE` | nonfinite loss, derivative, parameter gradient, parameter, or optimizer state | STOP |
| `OWNERSHIP_OR_FOREIGN_GRADIENT_FAILURE` | overlapping/wrong optimizer ownership or any foreign gradient | STOP |

`grad is None` and a present finite zero tensor are separate evidence states.
Every controlled real-VCritic zero receipt records name, `requires_grad`,
presence, shape, dtype, device, finite flag, exact-zero/nonzero flag, norm, and
digest for all 12 critic parameters.

## G. Graph-connectivity diagnostics

Before the unique backward, the classifier records
`current_values.requires_grad`, both grad-function names,
`value_loss.requires_grad`, and the frozen-prediction/normalized-target grad
flags. It then executes the nonmutating diagnostic:

```python
torch.autograd.grad(
    value_loss, current_values, retain_graph=True, allow_unused=True
)
```

The derivative receipt records presence, shape, dtype, device, finite flag,
exact-zero flag, norm, and digest. Frozen rollout predictions and normalized
targets are evidence inputs and do not require gradients. A stride-zero
autograd derivative view is copied into a canonical contiguous tensor before
byte fingerprinting; this changes evidence representation only, not math.

## H. Source-faithful loss decomposition

R4 now binds each receipt to epoch/minibatch, physical rows, raw-target digest,
normalized-target digest, frozen value-prediction digest, current-value digest,
installed settings, selected branch, and `dLoss/dValue`. For each bounded row
it records raw/normalized target, old/current/clipped predictions, delta,
unclipped/clipped errors, both Huber branch losses, selected/max branch, local
derivative, and the mathematical zero reason.

The enclosing mutation receipt also binds update/config through its authority
and single-use permits; the graph, loss, and parameter-gradient evidence are
therefore not free-floating assertions.

## I. Clipped-value-loss derivative analysis

The installed loss admits a genuine connected plateau. When
`abs(current-old) > clip_param`, the clipped prediction is locally constant.
If `loss_clipped > loss_original`, `max` selects that constant branch and the
local derivative is exactly zero even when the selected loss is nonzero.

The real-VCritic CPU witness selected physical rows `(3,4,5)`. Representative
values were:

```text
old prediction:          -2.7244994640
current prediction:      -1.6456494331
current-old delta:        1.0788500309
clipped prediction:      -2.5244994164
normalized/raw target:   -1.7244994640
unclipped branch loss:    0.0031086637
clipped branch loss:      0.3199999630
selected branch:          clipped
d(final loss)/d(current): 0.0
```

The batch loss was finite and nonzero (`0.31999996304512024`), the graph was
connected, all 12 owned gradients were present finite exact-zero tensors, and
the class was `VALID_ZERO_EFFECTIVE_UPDATE`. No detach was used.

## J. Exact-target derivative analysis

With a real VCritic whose controlled predictions, frozen predictions, and raw
targets were all exact zero and ValueNorm disabled, both Huber branches were
zero at their minimum. The connected scalar loss and `dLoss/dValues` norm were
exactly zero. All 12 required parameter gradients were present, finite, and
exact zero. Both CPU minibatches and both CUDA minibatches classified
`VALID_ZERO_EFFECTIVE_UPDATE`.

## K. Attempt-3 reconstructable evidence

The durable artifacts establish:

- S6 minibatch identity `epoch=0, minibatch=1, rows=(2,3)`;
- minibatch 0 had a nonzero finite critic backward and one Adam step;
- two canonical ValueNorm updates completed, with finite pre/post field
  receipts and state mutation;
- the minibatch-1 backward was attempted before the no-nonzero-gradient STOP;
- its optimizer step was not executed;
- route poison, partial-update state, completed counts, source identities, and
  static executor cardinality.

## L. Attempt-3 unrecoverable evidence

The artifacts do not retain the minibatch-1 raw numeric targets, normalized
numeric targets, frozen rollout predictions, current critic predictions after
minibatch 0, selected loss branch, scalar loss decomposition, `dLoss/dValues`,
or per-parameter `grad None` versus exact-zero tensors. Component and source
digests cannot reconstruct these missing floats or graph facts.

Therefore:

```text
attempt-3 exact zero-gradient mathematical cause:
  UNRESOLVED FROM EXISTING REAL ARTIFACTS
```

The controlled witnesses prove legal possibility and the need for the
classifier; they are not presented as proof of attempt 3's exact branch.

## M. Controlled real-VCritic normal nonzero witness

Two designated real-VCritic mixed-sequence witnesses passed: one direct R4
sequence and one R5 S0-S10 transaction. In each, minibatch 0 classified
`VALID_NONZERO_UPDATE`, retained normal parameter mutation, and was followed
by the proved clipped plateau. Existing R4 regression also retained four
nondegenerate enabled minibatches plus disabled/remainder witnesses.

## N. Controlled valid-zero-effective witness

Four first-class witness contexts passed:

1. CPU exact-target real VCritic;
2. CPU clipped-plateau real VCritic after one nonzero Adam step;
3. R5 nonzero-then-clipped-zero transaction to S10;
4. CUDA exact-target real VCritic on `cuda:0`.

Across focused R4 sequences, five minibatch-level valid-zero receipts were
issued: two CPU exact-target, one mixed plateau, and two CUDA exact-target.
The R5 mixed transaction issued one additional zero receipt.

## O. Invalid graph-disconnect witness

The focused negative matrix fail-closed for detached loss, detached current
values, an unused current-value tensor (`autograd.grad` returned `None`), and a
module whose all required parameter gradients remained `None`. All used
`STOP — B2-R MUTATION_ATTRIBUTION`; none reached an optimizer step.

It also rejected a foreign actor gradient and deliberately broken optimizer
ownership. An all-zero derivative without installed-branch proof was rejected.

## P. Nonfinite witness

A NaN scalar loss stopped with `STOP — B2-R NONFINITE_LOSS`. A custom finite
forward/nonfinite-backward diagnostic made `dLoss/dValues` infinite and
stopped with `STOP — B2-R NONFINITE_GRADIENT`. Existing R4 finite
parameter/optimizer/clip guards also remained passing.

## Q. R0 contract alignment

Frozen R0 says:

- all approved nonempty critic minibatches carry the derived planned count;
- a proved zero-effective critic case may execute when explicitly targeted;
- parameter no-change is allowed only with exact zero-effective evidence, and
  optimizer state may still mutate;
- a deliberate zero-gradient case must be classified explicitly.

Therefore the old implementation rule “every authorized critic backward must
contain a nonzero owned gradient” was stricter than R0. There is no R0
contract contradiction. R0 was not edited.

## R. Files created/modified

Created:

- `scripts/environments/test_assignment_phase_b2_r5i_cg_critic_zero_gradient_classification.py`
- `AgentRead/202609/20260908/PHASE_B2_R5I_CG_CRITIC_ZERO_EFFECTIVE_GRADIENT_CLASSIFICATION_REPORT.md`
- `AgentRead/202609/20260908/TASK_PROGRESS_ARCHIVE_BEFORE_B2_R5I_CG_HANDOFF_20260908.md`

Modified:

- `assignment_event_training_gradient_probe.py`
- `assignment_event_training_critic_mutation.py`
- `scripts/environments/_assignment_phase_b2_r4_critic_mutation_helpers.py`
- `scripts/environments/_assignment_phase_b2_r5_full_transaction_helpers.py`
- `AgentRead/TASK_PROGRESS.md`

Qualified post-change source SHA-256 values:

| Source | SHA-256 |
|---|---|
| `assignment_event_training_gradient_probe.py` | `5501947f64ebe33c003b0e08b2fbacd6ccd826c3e5e78d115401ed11061dd985` |
| `assignment_event_training_critic_mutation.py` | `9719bcd059cfe9a670cc9715117ef00e965f708c82134a59c3a1f77296173dde` |
| `_assignment_phase_b2_r4_critic_mutation_helpers.py` | `fb0a343cb34ee4b9b254c83d7a0faad3e73275e42ac5f822bc4bc75db9a7ca83` |
| `_assignment_phase_b2_r5_full_transaction_helpers.py` | `45f6a9bc51e5ff027deb1d4c0c0afe7d60f43e02827d88cd90bf2aeb80da3dba` |
| `test_assignment_phase_b2_r5i_cg_critic_zero_gradient_classification.py` | `08951030ffde5928074dc908ac9ffbe50b28eb98090626c30e422aa2a4e52517` |

## S. Narrow classifier design/implementation

The repair adds immutable loss-graph and parameter-gradient evidence DTOs,
explicit class constants, source-faithful loss decomposition, valid-nonzero /
valid-zero counters, and Adam state evidence. Zero is accepted only when the
graph classifier proves the installed loss's exact target or strict clipped
plateau and every required owned parameter gradient is present finite zero.

No second backward, critic-step, ValueNorm-update, or R5 coordinator executor
was introduced. No critic, actor, factor, return, terminal, lifecycle, or
ValueNorm math changed.

## T. Valid-zero receipt evidence

Each valid-zero receipt includes authority/permit binding, physical rows,
raw/normalized/frozen/current digests, settings and branch evidence,
`dLoss/dValues`, all parameter gradients, pre/post component digests,
optimizer-step vectors, Adam state, actor freeze, and cleanup. This prevents
“all grads zero” from being sufficient on its own.

## U. Optimizer-step semantic decision

Decision: a proved valid-zero-effective minibatch still executes exactly one
optimizer step.

This follows both installed `VCritic.update` ordering and R0's planned-count
contract. The receipt distinguishes current-gradient effectiveness,
parameter movement, and optimizer-state movement. A fresh zero-moment exact
target changed Adam state/counters but not parameters. A zero current gradient
after a nonzero minibatch changed both state and parameters through retained
moments.

## V. Adam existing-moment zero-gradient experiment

The CPU R4 sequence performed a nonzero update, then the connected clipped
plateau. Before the zero step all 12 Adam parameter states were present with
nonzero `exp_avg`; counters were `1`. After the step all counters were `2`,
`exp_avg`/`exp_avg_sq` digests changed by decay/update, optimizer state changed,
and critic parameters changed despite exact-zero current gradients.

The mixed R5 transaction independently showed the same `1 -> 2` Adam counter,
optimizer mutation, and parameter movement at its zero-effective minibatch.

## W. Critic/ValueNorm count semantics

For each processed authorized critic minibatch:

- processed count increments once;
- backward count increments once after the unique backward;
- exactly one of valid-nonzero or valid-zero-effective increments;
- optimizer-step count increments once for either valid class;
- when ValueNorm is enabled, its update count increments once before backward;
- when disabled, it remains zero and raw targets are used directly.

Existing enabled R4 regression retained exact `(backward, step, ValueNorm)`
counts `(4,4,4)`; disabled retained `(2,2,0)`; remainder retained `(3,3,3)`.
The focused R5 mixed transaction intentionally used disabled ValueNorm to make
the plateau numerically exact and retained `(2,2,0)`.

## X. Poisoning semantics

The irreversible boundary is unchanged. A classification failure after live
ValueNorm mutation remains `partial_update=true`, `route_poisoned=true`, with
no rollover/checkpoint/next-rollout/public use. Existing R4 post-ValueNorm and
post-step poison tests and R5 poison matrix passed unchanged. A proved valid
zero class continues through the planned step; an unproved/disconnected zero
still poisons when it occurs after ValueNorm mutation.

## Y. R4 post-change qualification

The complete prior R4 harness passed:

```text
critic backward / step: 10 / 10
live ValueNorm updates:  9
successful normal sequences: enabled + disabled + remainder = 3
post-ValueNorm poison:  PASS
post-step poison:       PASS
static public faults:   9 PASS
```

The focused CG harness added three successful R4 sequences: CPU exact target,
CPU nonzero-to-plateau, and CUDA exact target. Both the old nondegenerate case
and new valid-zero class coexist.

## Z. R5 post-change S10 qualification

The complete prior R5 harness passed one controlled ValueNorm-enabled S0-S10
transaction with exact critic counts `(1,1,1)` and all existing fault/poison
checks.

The focused mixed R5 transaction passed S6, S7, S8, S9 rollover, and S10 with
classes `(VALID_NONZERO_UPDATE, VALID_ZERO_EFFECTIVE_UPDATE)`, critic counts
`(2,2,0)`, Adam `1 -> 2`, and one successful transaction. Thus two controlled
R5 transactions reached S10 in this task's verification set; real S10 remains
zero.

## AA. CUDA controlled qualification

CUDA was feasible. A plain installed-HARL real VCritic ran on `cuda:0` without
Isaac/AppLauncher. Two exact-target minibatches had connected graphs, finite
zero loss, exact-zero `dLoss/dValues`, 12/12 present finite zero parameter
gradients on CUDA, two source-faithful Adam steps, and unchanged parameters
with mutated optimizer state. Classification was
`VALID_ZERO_EFFECTIVE_UPDATE` for both.

## AB. Static/private/public guards

The post-change R5 static audit passed:

```text
backward executor:          1
actor-step executor:        1
critic-step executor:       1
ValueNorm-update executor:  1
R5 actor-sequence calls:    1
R5 critic-sequence calls:   1
private dependency edges:  18 (unchanged)
public references:          0
scheduler steps:            0
```

The standalone historical R2 aggregate script still reaches its already
documented legacy static-guard false positive because it treats the later
private R3 import of R2 as public. Its real probe portion ran before that
aggregate failure; the current production/R4/R5 static guards passed. This
slice did not broaden the frozen private dependency allowlist merely to hide
that known aggregate issue.

## AC. Exact execution counts

Units are explicitly separated between first-class witness contexts and
minibatch receipts:

```text
attempt-3 artifacts inspected:                       8
designated controlled nonzero critic witnesses:      2
first-class valid-zero-effective witness contexts:   4
graph-disconnect faults:                             3
grad-none/missing-required-gradient faults:          1
nonfinite faults:                                    2
dLoss/dValues first-class cases:
  nonzero:                                           2
  exact zero:                                        4
  None:                                              1
Adam existing-state zero-gradient probes:            2
focused R4 successful controlled sequences:          3
prior R4 regression successful normal sequences:     3
focused R4 valid-zero minibatch receipts:             5
focused R5 successful full transactions / S10:       1 / 1
prior R5 regression successful transactions / S10:   1 / 1
CUDA critic classification probes:                   1
Isaac/AppLauncher/SimulationApp:                      0
checkpoint weight I/O:                               0
training/evaluation/playback:                        0
public route activation:                             0
attempt 4:                                           0
```

## AD. Retained historical poison/nonclaims

- Attempts 1, 2, and 3 remain historical poisoned stopped routes.
- Successful real full learner transactions remain `0`; real S10 remains `0`.
- Attempt-3 exact mathematical cause remains unresolved.
- B2-R5I is not complete.
- Real Isaac full-learner integration is not established.
- Training-update readiness is not yet established.
- B2-R6a/R6b and B2-R7 are not authorized.
- The public learned-policy route remains dormant/blocked.
- This qualification does not authorize attempt 4.

## AE. GPT-review boundary

B2-R5I-CG's controlled classification slice is complete and awaits independent
GPT review. No commit was made. The next authorized action is review of this
classifier, its R0 alignment, loss/graph receipts, Adam semantics, regressions,
and nonclaims. Stop here; do not run attempt 4, begin B2-R6/B2-R7, or start
training without a new explicit authorization.
