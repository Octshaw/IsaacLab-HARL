# Phase B2-R3 Controlled Actor Optimizer Mutation and Factor Attribution Report

Date: 2026-09-01

Classification:

```text
PHASE-B2-R3-CONTROLLED-ACTOR-OPTIMIZER-MUTATION-FACTOR-ATTRIBUTION-COMPLETE-AWAITING-GPT-REVIEW
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

The accumulated uncommitted B2-R0/R1/R2 private modules, tests, reports,
archives, and `TASK_PROGRESS.md` handoff were preserved. The user-supplied
starting phase authority is:

```text
B2-R0: GPT REVIEW PASS / FROZEN
B2-R1: GPT REVIEW PASS / CLOSED
B2-R2: GPT REVIEW PASS / CLOSED
B2-R3: explicitly authorized controlled actor mutation slice
```

No file was staged or committed. Installed HARL was read and executed through
its actor interfaces but was not modified.

## B. Frozen R0/R1/R2 inputs

R3 reused without semantic change:

- R1 resolved configuration, authority digest, exact ownership audit, immutable
  actor plan, exact row partitions, distinct permit operations, full-index
  factor transition, and STOP taxonomy;
- R2 installed-HAPPO `evaluate_actions` and the one reviewed real backward
  executor;
- original proposal action and rollout logprob as behavior evidence;
- DVM as the evaluation population and active-and-DVM as the loss population;
- full canonical factor `[T,E,1]`, with exact-one off-DVM ratio;
- critic target/non-mutation and live ValueNorm non-mutation boundaries; and
- dormant/default-off public route isolation.

No stock HAPPO/VCritic `train()` or `update()` and no stock return computation
was selected.

## C. Files created or modified

Created:

- `assignment_event_training_actor_mutation.py`;
- `assignment_event_training_actor_mutation_guards.py`;
- `scripts/environments/_assignment_phase_b2_r3_actor_mutation_helpers.py`;
- `scripts/environments/test_assignment_phase_b2_r3_controlled_actor_optimizer_mutation_factor.py`;
- this report;
- `AgentRead/202609/20260901/TASK_PROGRESS_ARCHIVE_BEFORE_B2_R3_HANDOFF_20260901.md`.

Modified after the byte-exact archive:

- `AgentRead/TASK_PROGRESS.md`.

No public wrapper, runner, lifecycle, resolver, controller, DVM, reward,
profile, checkpoint, or installed-HARL source changed.

Final SHA-256 identities of the four R3 Python files are:

```text
assignment_event_training_actor_mutation.py
  4a151848915455f860a38309a473cf67095a9587a11518812448378af06a8375
assignment_event_training_actor_mutation_guards.py
  10abcfc78dad7b43d961a47ed361d57d0717651dd39cd6fcf6e2dd8e234eb51d
_assignment_phase_b2_r3_actor_mutation_helpers.py
  3b592798b93b4765950f3d328d72182acd2e3345e4458a173c036dfb9899c0f1
test_assignment_phase_b2_r3_controlled_actor_optimizer_mutation_factor.py
  d8693f1d008ff8d41bd4e0ad2255ee6c5e73a7c92451a765dd9d537432f611fa
```

## D. Real versus synthetic classification

REAL:

- three installed `HAPPO` actor wrappers and `StochasticPolicy` modules;
- three installed actor-owned Adam optimizers;
- installed `evaluate_actions` distributions and PPO/HAPPO settings;
- real PyTorch forward, backward, gradient clipping, and `optimizer.step()`;
- real actor parameter mutation and Adam state initialization/mutation;
- real pre/post actor logprob evaluation and resulting ratio change.

CONTROLLED / SYNTHETIC:

- CPU `T=2`, `E=3`, `M=3`, `N=4`, `B=6` historical rollout fixture;
- observations, available actions, original proposal/action-logprob fixtures,
  DVM/active masks, advantages, partitions, and RNG seed;
- deliberate failure claims and one post-step factor fault;
- in-memory actor/optimizer restoration for poisoned-test isolation.

This is real controlled actor mutation, not an Isaac rollout, a full learner
update, training, convergence, evaluation, or public-route evidence.

## E. Actual ownership proof

Before every nonempty actor minibatch, R1 runtime ownership validation proved:

- each actor optimizer owns exactly its actor parameters;
- the three actor parameter sets are mutually disjoint;
- critic parameters are disjoint from every actor;
- critic optimizer ownership is exact;
- shared-parameter mode is false;
- all gradients are absent; and
- actor, optimizer, critic, and live ValueNorm states are finite.

Selected initial component fingerprint digests were:

```text
actor0:         38aa3923caa9a50236d97c8eb505a3488706f75d3cec52fc44b735676273e979
actor1:         7830414349237f34b2f6ba571544dcf30b34feec1164325e1e9c62d1bfe50ba0
actor2:         c16129cda0c525d774a7f724796936f5c7547826ab1c6fdd30316a758025d579
critic:         c72e841f7ccb5b0f43a8a1917ef83d0bb186b3a738baa13703fe4363ed474dd5
live ValueNorm: 0f048b74e0894c2c1e66e03121385269fcc7bdd8c2059f4aeb52ec4d26b019fc
```

## F. Exact actor order and RNG provenance

The resolved config has `fixed_order=false`. One CPU `torch.Generator` was
seeded once with seed `7`; one `torch.randperm(3)` generated:

```text
actor order: (0, 1, 2)
generation count: 1
RNG state before:
  daf9268b18e87b0267a6ad240c6093eb98fe6f03872986bd31a497ba5ea2371a
RNG state after:
  5375315acc068ef3680a237c3e08476f71853e655a5a239f80d4709160de395d
order evidence:
  b83735c8557c0f8fd95dd6c0e984edc14ca91bf12ffe20ecedf7b1d8eb4481fa
```

The freezer rejects a second generation. Duplicate, missing, and changed order
fixtures fail `STOP — B2-R AGENT_ORDER` before backward/step.

## G. Actor plan and expected step counts

The controlled plan has two epochs and two exact-coverage minibatches per
actor. Its digest is:

```text
cce949ceca02d18828e6d58bff6efda2907d9348362ef26a01dce80c27eededc
```

Derived counts for one successful sequence are:

```text
actor0: backward 4, optimizer.step 4
actor1: backward 4, optimizer.step 4
actor2: backward 0, optimizer.step 0
```

Every backward and optimizer step uses a distinct single-use permit binding
update/config, actor/order position, epoch, minibatch, exact loss-index digest,
and separate expected module and optimizer fingerprints.

## H. Forced-only actor evidence

Actor2 has no DVM or active-and-DVM rows. It performs:

```text
factor pre evaluation:  0
factor post evaluation: 0
backward:               0
optimizer.step:         0
parameter mutation:     0
optimizer mutation:     0
```

Its full factor transition is an exact unchanged skip; the accumulated factor
is not reset.

## I. Nondegenerate actor mutation evidence

Actors 0 and 1 each contain DVM-valid loss rows, DVM-valid inactive rows, and
forced/off-DVM rows. Every one of their eight successful-sequence step receipts
proved finite scalar loss, finite/nonzero owned gradients, finite installed
clip result, no foreign gradients, target parameter change, Adam state change,
and exact cleanup.

Representative deterministic backward/clip receipts per successful sequence:

```text
actor0:
  (5.130741831530489, 5.130742073059082)
  (7.564477040911175, 7.56447696685791)
  (5.061986305839844, 5.061986446380615)
  (7.572921397481928, 7.572921276092529)
actor1:
  (4.293092351151378, 4.293092250823975)
  (2.5610738633326373, 2.5610740184783936)
  (4.413721646381626, 4.413721561431885)
  (2.6334053786805134, 2.6334054470062256)
```

The tuple fields are `(aggregate pre-clip gradient norm, installed clip
result)`. All values are finite and below the configured maximum `10.0`.

## J. Sequential multi-actor mutation evidence

Actor0 completes all four authorized steps before actor1 begins. Actor1's loss
uses the factor produced by actor0. Actor1 completes all four steps before the
forced-only actor2 skip. No order is regenerated between epochs/minibatches.

Actor1 is off-DVM at canonical row `0`, where actor0 produced a non-one prior
factor. The exact witness proved actor1's ratio is one there and its
`factor_after[0]` equals the prior accumulated value, not one.

## K. Parameter pre/post fingerprints

Selected first-pre to final-post parameter digests for one successful sequence:

```text
actor0:
  a8e547ef8f8d7fde3aad602651f571ba77eb5fb639cdf6c9b71cf08544cc9988
  -> 0613dacc74e7b7a77df308333372872162988fe80b73d4312de6985de753de4c
actor1:
  498d08c600f554b89d052cfff68196fa8c690879c2d11c7dbbfa5104354600ce
  -> ec76c4d2a9c75ee92dcdb85baafb1833f6bacba50ac5a6d84a9eeddc281b37a7
```

Every individual step also has a chained exact pre/post digest pair. Each of
the eight successful-sequence steps changed its owned actor parameters and
left parameters finite.

## L. Optimizer-state pre/post fingerprints

Selected first-pre to final-post Adam digests for one successful sequence:

```text
actor0:
  387ad6a3d5f4b69e2b9ee56faa69e60b4058cf048427adb53bd49f70e604d28c
  -> 53b13d30a5a656cb0b3a1e2b354f48112629d63be4473957969ad7495f9cd9f2
actor1:
  35bdb1ac88a9bf4df895033396a86f2ebb05907ab317f52df11dc1985400feec
  -> b4ba52cf4d37a3c0aa20cd201ce9151338d5bb4e72efd11eaad569cd561f6f7e
```

Every owned per-parameter Adam step value advanced by exactly one per receipt;
first/second moments and all scalar/tensor state remained finite. Actor2's
optimizer stayed exactly unchanged and uninitialized.

## M. Exact backward and step receipts

Each nonempty minibatch emitted distinct backward and step permit IDs. The
step gate consumed only `operation=optimizer_step` after the corresponding
backward, gradient audit, clip, and pre-step fingerprint check. The central
step seam emitted one receipt per real Adam step and the observed counts match
the immutable plan.

## N. Factor-pre evidence

For each updating actor, exactly one no-grad factor-pre evaluation ran before
its first step, over that actor's complete canonical DVM population using the
historical observation, available mask, original proposal action, and pre-
segment actor parameters. It was not refreshed per epoch or minibatch.

The three field identities remain distinct:

```text
original_rollout_behavior_logprob
factor_pre_logprob
factor_post_logprob
```

## O. Factor-post evidence

Exactly one factor-post evaluation ran after all four steps for each updating
actor, on the same historical inputs/actions/masks and exact same DVM rows as
factor-pre, using the updated actor parameters. Actor2 required neither
evaluation.

## P. Ratio-full evidence

Every factor transition has shape `[2,3,1]`. DVM ratios are finite and strictly
positive; every off-DVM element is exact one bit-for-bit. Selected ratio-full
digests are:

```text
actor0: ed7d434ff80c10a2acb035eeb7d77d9be72ee8551069b5a43ecb7513641d1913
actor1: 52bba6def20c8d05949f08e3a0d11fc956b6396dc9d7ceb7203904a0374191e1
actor2: f46913286d895f62d646314f400fc3d7a543cf34eb4ae56df87f43dc4582a36b
```

Actor2's digest is the exact full-grid ones tensor.

## Q. Factor recurrence across actors

Exact transition digests are:

```text
F0:
  f46913286d895f62d646314f400fc3d7a543cf34eb4ae56df87f43dc4582a36b
after actor0 / before actor1:
  ed7d434ff80c10a2acb035eeb7d77d9be72ee8551069b5a43ecb7513641d1913
after actor1 / before actor2 / after actor2:
  9b492e810a369041bbd4a8a568a5e52e163a24c637a7ffb378ea1aed4937e34d
```

Each transition passed exact equality
`factor_after = factor_before * ratio_full`, finiteness, strict positivity,
canonical scatter, and off-DVM exact-one checks.

## R. Previous-actor factor temporal direction

Every step receipt records the exact `factor_before` digest used by the loss.
All four actor0 losses use `F0`; all four actor1 losses use the completed actor0
factor. No actor loss uses its own post-update ratio. Factor is updated once at
actor-segment completion, not after a minibatch.

## S. Foreign-component non-mutation

After every real actor step, exact state digests proved:

- all other actor modules and optimizers unchanged;
- critic module and optimizer unchanged;
- live ValueNorm unchanged; and
- no foreign gradient present.

At sequence end actor0/actor1 were the only expected changed owners; actor2,
critic, critic optimizer, and live ValueNorm remained exact unchanged.

## T. Critic and live ValueNorm freeze

```text
critic backward:                 0
critic optimizer.step executed:  0
critic parameter mutation:       0
critic optimizer-state mutation: 0
live ValueNorm updates:           0
live ValueNorm state mutation:    0
```

One critic-step trap and one live-ValueNorm trap were exercised per complete
test invocation and rejected before delegation.

## U. Gradient cleanup

Every actor minibatch begins from exact absent gradients. Each success and
post-step failure clears all actor and critic gradients to `None`. Every next
minibatch/actor start revalidates gradient quiescence and full ownership.

## V. Pre-step failure evidence

Per complete invocation, 48 precise fail-before/without-step assertions passed:

- authority/order: 4;
- optimizer-step permit: 14;
- pre-step state: 5;
- mutation-attribution claims: 5;
- factor identity/recurrence: 10;
- critic/ValueNorm traps: 2;
- static/public paths: 8.

They cover stale authority/config, missing/duplicate/misbound/empty permits,
stale gradient, nonfinite loss/gradient/clip, foreign gradient/state, wrong
expected step counts, wrong evidence identities/rows, ratio/factor failures,
and forbidden source paths. None of these assertions executed an actor step.

## W. Post-step poisoning evidence

An independent disposable context executed one legitimate actor0 backward,
clip, and Adam step, then deliberately failed before factor completion.
Evidence was exactly:

```text
partial_update:       true
route_poisoned:       true
rollover_allowed:     false
checkpoint_allowed:   false
next_rollout_allowed: false
public_use_allowed:   false
later actor steps:    0
```

In-memory actor/optimizer restoration was exact for test isolation, but the
logical route state remained poisoned and partial. Restoration did not convert
the failed update to success.

## X. Fault-injection matrix

The required authority/order, step authorization, pre-step, attribution,
factor, poisoning, critic/ValueNorm, stock-path, and public-import categories
all passed their exact STOP assertions. Per invocation there were 48
fail-before/without-step assertions plus one post-step poisoned failure. The
complete matrix ran twice: cumulative 96 and 2 respectively.

## Y. Static and public guards

The final R3 AST guard found:

```text
reviewed actor optimizer.step call sites: 1
new R3 backward call sites:                0
scheduler.step call sites:                 0
live ValueNorm.update call sites:          0
stock HAPPO/VCritic/returns call sites:     0
```

R3 reuses the one reviewed R2 `loss.backward()` call site. Four R3 source/test
files were guarded. Public isolation scanned all 57 production files and found
zero reference to either R3 private module. Both modules export nothing.

All three R1 regression suites passed after R3 implementation, and the R2 AST
guard still found exactly one centralized backward call and zero violations.

## Z. Exact execution counts and retained nonclaims

One complete R3 test invocation observed:

```text
actor backward executed:               9
actor optimizer.step executed:         9
per-actor backward:                    actor0=5, actor1=4, actor2=0
per-actor optimizer.step:              actor0=5, actor1=4, actor2=0
owned actor parameter mutation events: 9
owned actor optimizer mutation events: 9
critic backward executed:              0
critic optimizer.step executed:        0
critic parameter mutations:            0
critic optimizer-state mutations:      0
live ValueNorm updates:                 0
scheduler.step executed:               0
Isaac/runtime rollout actions:          0
training actions:                       0
evaluation/playback actions:            0
checkpoint weight I/O:                  0
public route activations:               0
```

The complete invocation ran twice, once before and once after adding exact
fingerprint output. Cumulative B2-R3 task counts are therefore:

```text
actor backward executed:                18
actor optimizer.step executed:          18
per-actor backward:                     actor0=10, actor1=8, actor2=0
per-actor optimizer.step:               actor0=10, actor1=8, actor2=0
owned actor parameter mutation events:  18
owned actor optimizer mutation events:  18
distinct actors mutated per success:     2
critic backward executed:                0
critic optimizer.step attempts trapped:  2
critic optimizer.step executed:          0
critic parameter mutations:              0
critic optimizer-state mutations:        0
live ValueNorm attempts trapped:          2
live ValueNorm updates:                   0
scheduler.step executed:                  0
unauthorized actor step attempts trapped: 28
fail-before/without-step assertions:      96
post-step poisoned failures:              2
Isaac/runtime rollout actions:            0
training actions:                         0
evaluation/playback actions:              0
checkpoint weight I/O:                    0
public route activations:                 0
```

Before rewriting `TASK_PROGRESS.md`, its prior B2-R2 handoff was copied byte
for byte:

```text
source/archive bytes: 7324 / 7324
byte equality: true
SHA-256: c64675600a820d1cb13652074d665fba81a64eb00b4aff783bdfb01702e7ec70
Git blob: 4e1ae30fb89880f2f344f854634016ebd948d18b
```

B2-R3 does not establish critic mutation, live ValueNorm training mutation, a
full learner update, rollover/quiescence readiness, B2-R4, Isaac rollout
integration, training-update readiness, convergence, policy quality,
checkpoint continuation/resume, or public-route readiness.

```text
B2-R0: GPT REVIEW PASS / FROZEN
B2-R1: GPT REVIEW PASS / CLOSED
B2-R2: GPT REVIEW PASS / CLOSED
B2-R3: IMPLEMENTATION COMPLETE / CONTROLLED ACTOR OPTIMIZER MUTATION AND
       FACTOR VERIFICATION COMPLETE / AWAITING GPT REVIEW
B2-R4: NOT AUTHORIZED
actor optimizer-mutation readiness: NOT YET GPT-CLOSED
critic/ValueNorm mutation readiness: NOT ESTABLISHED
training-update readiness: NOT YET ESTABLISHED
public learned-policy route: DORMANT / BLOCKED
training: NOT AUTHORIZED
commit: NONE
next: independent GPT review of B2-R3
```

Stop here. Do not begin B2-R4, mutate critic or live ValueNorm, run training,
activate the public route, perform checkpoint weight I/O, stage, or commit.
