# Phase B2-R4 Controlled Critic Optimizer and Live ValueNorm Mutation Report

Date: 2026-09-01

Classification: `PHASE-B2-R4-CONTROLLED-CRITIC-OPTIMIZER-LIVE-VALUENORM-MUTATION-COMPLETE-AWAITING-GPT-REVIEW`

## A. Repository authority

- Branch/upstream: `main` / `origin/main`.
- HEAD, `origin/main`, and merge-base:
  `b71d85a32f51be6ada324f870813a56bb45dd396`.
- Working tree: reviewed accumulated uncommitted B2-R0 through B2-R3 private
  artifacts plus the authorized private B2-R4 work.
- Staging, commit, and push actions: 0.

## B. Frozen B2-R0 through B2-R3 inputs

B2-R0 is GPT REVIEW PASS / FROZEN; B2-R1, R2, and R3 are GPT REVIEW PASS /
CLOSED. R4 reuses the R1 authority/critic plan and R2 unique backward seam. No
R0-R3 contract was changed and the R3 actor mutation path was not executed.

## C. Files created or modified

Created: `assignment_event_training_critic_mutation.py`,
`assignment_event_training_critic_mutation_guards.py`,
`_assignment_phase_b2_r4_critic_mutation_helpers.py`,
`test_assignment_phase_b2_r4_controlled_critic_optimizer_live_valuenorm.py`,
this report, and `TASK_PROGRESS_ARCHIVE_BEFORE_B2_R4_HANDOFF_20260901.md`.
Modified: `AgentRead/TASK_PROGRESS.md`.

Verified R4 SHA-256 values:

- seam: `123508a4beb95782206c0b7a511df6d1bfe81d8e00cfa5a368c06c5bd67404aa`
- guards: `690d1cb0902b396cff89ac7834763e6db850727b078fa4b6b9bd3d28c0a6faa4`
- fixtures: `36adc3419b6655189a58a444b1ed113de7574b84b0a243df0794da988696e207`
- harness: `fd38e946cffe6e713829bd405a80526f4a4a90ec6e1859ce9984bd9ee6b14624`

The pre-rewrite progress archive is byte-exact: SHA-256
`af10eb34a544796ebceba50864001039efe4fbf22d4c12cda07ba89e5cd2cac6`,
8,820 bytes for both files.

## D. Real versus controlled/synthetic evidence

REAL: installed HARL VCritic/VNet/Adam and ValueNorm; real forward, clipped
Huber loss, backward, critic-only clipping, optimizer step, and real
critic/Adam/ValueNorm mutation. Installed `v_critic.py` SHA-256 is
`ae66390702efb55099d151c11f28ae533f25ef6d62697949445abd2979708bf3`;
`valuenorm.py` is
`a35471b136567bde0b7fc7be34a7873efa617bdabf9a9074517ff0e3ef3fb8b0`.

CONTROLLED/SYNTHETIC: deterministic CPU observations, `[T+1,E,1]` returns,
frozen evidence, canonical partitions, injected faults, and restoration
snapshots. No Isaac, terminal-runtime, convergence, or policy-quality evidence.

## E. Ownership proof

Before each minibatch the seam fingerprints critic/optimizer, every
actor/optimizer, live ValueNorm, gradients, target and plan. The critic
optimizer owns exactly critic parameters; actor/critic and actor/actor sets are
disjoint; gradients begin clean and all relevant states are finite. Ownership
failure is pre-mutation.

## F. Critic plan and row coverage

Enabled: `B=T*E=2*3=6`, two epochs, partitions
`[(0,1,2),(3,4,5)]` per epoch. Remainder-safe: `B=7`, partition sizes
`[3,2,2]`, exact rows `(0..6)`. Missing, duplicate, out-of-range, structural,
and floor-division remainder omissions fail before mutation.

## G. Target identity

The target is exactly `returns_storage[:-1]`; enabled digest:
`48e4067ea7c9b2e6c86867219c26e2222257eea9f04411e276fbf860e19c1e4e`.
Plan, frozen evidence, update ID, and config digest bind the same identity.

## H. Final-slot exclusion

The final slot sentinel is `321.0`, digest
`5067e343f46725a41b118a8c35eb2ac80b169e5a6f8575c8c176dc2c38b4ee2a`.
It is outside `B` and never sampled, normalized, or used in loss.

## I. Expected count derivation

- enabled: `2*2 = 4` backward/step/update;
- ValueNorm disabled: `1*2 = 2` backward/step, 0 update;
- remainder-safe: `1*3 = 3` backward/step/update;
- post-ValueNorm fault: `0/0/1`;
- post-step fault: `1/1/1`;
- final passing harness: `10/10/9`.

## J. Per-minibatch raw identity

Rows `(0,1,2)` digest to
`011d825e9838eb0983aa1a0e2ab9dc15c8f1ad2553b00f763f522e85f06f47b0`;
rows `(3,4,5)` digest to
`3e134c74ab31abe872f47d4d1490a292e54f2d6b217b1af94566563e08b085f3`.

## K. ValueNorm fingerprints

The enabled pre-to-final chain is
`0f048b...19fc -> fba699...e9a8 -> d4f2ff...71c6 -> 4c99c9...3e50 ->
64c0f9...a8959`.

## L. ValueNorm receipts and order

Every receipt binds a single-use permit, raw digest, rows, update/config,
pre/post state, running mean, running mean-square, debiasing term, finiteness,
mutation, and update index. The only live callsite is
`self.value_normalizer.update(input_vector)`.

## M. Same raw batch proof

Every live update is followed immediately by two audit normalizations of the
same tensor object and digest. All enabled receipts report same-object and
same-digest true. Different object/content faults are rejected.

## N. Critic forward/loss

The seam reproduces installed VCritic-compatible clipped/unclipped Huber math.
The clipped baseline uses frozen real pre-update critic predictions to keep the
probe nondegenerate. Enabled losses: `0.5530570`, `0.3147897`, `0.5178278`,
`0.3130606`; all finite.

## O. Critic backward

Every backward has a separate permit and executes through the reviewed R2
seam. Final passing harness backward count: 10.

## P. Gradient audit

Per-parameter evidence includes presence, shape, dtype, device, finiteness,
digest, norm and zero classification. Enabled aggregate norms were
`2.9269971`, `5.7055448`, `7.9755650`, and `5.6768403`; all finite/nonzero.
Every actor remained gradient-free.

## Q. Clip evidence

Only critic-owned gradients are clipped. Results were finite and no parameter
or optimizer state changed before the permitted step.

## R. Optimizer-step receipts

Each distinct single-use step permit binds update/config, critic owner,
epoch/minibatch, rows, raw target, pre-critic, pre-optimizer, and post-ValueNorm
fingerprints. Exactly one reviewed direct critic step callsite exists.

## S. Critic parameter mutation

Enabled critic fingerprint changed from
`84392b6883cea2295662dac7acafd6ede7571faa2bca4f47e925b3308a495c44` to
`fb7a9b82cd65a96c955dd3c500c81993fce7186b95049d9e1cc868d4d06168d4`.
Every successful step mutated finite critic parameters.

## T. Optimizer-state mutation

Enabled optimizer fingerprint changed from
`910cbceed4d8de45e56681172b01ea6152d8034a3bd9b2ee12ff41d0367d93a7`
to `d6c14369aa89ed60bd8e69fc2eff1e177e597bfe267dfa40297298bd59de47bf`.
Adam tensors/scalars stayed finite and step counters advanced exactly once.

## U. Actor hard freeze

Actor modules and optimizers were exact unchanged throughout. Actor backward,
step execution, parameter mutation, and optimizer mutation were all 0. One
synthetic actor-step attempt was trapped before execution.

## V. Gradient cleanup

Critic gradients were clean after every successful minibatch and controlled
failure cleanup.

## W. ValueNorm-disabled case

One probe passed with 2 real backward/steps, 0 live updates, exact unchanged
ValueNorm state, and direct raw-target use.

## X. Remainder-safe case

Seven rows passed 3 backward/step/update triplets with `[3,2,2]` partitions and
exact-once coverage.

## Y. Pre-mutation failures

Fifty-five assertions passed across authority, target/coverage, ValueNorm,
critic permits/state, counts, actor freeze, and static/public guards.

## Z. Post-ValueNorm poison

One legitimate update followed by failure produced delta `0/0/1`,
`partial_update=true`, poison true, and rollover/checkpoint/next-rollout/public
false. Exact test restoration did not clear logical poison.

## AA. Post-step poison

One update/backward/step followed by failure produced `1/1/1`, no later
minibatch, and the same poison denials after exact test restoration.

## AB. Fault matrix

Authority/target 9; ValueNorm 15; critic 17; count/actor 5; static/public 9;
post-ValueNorm poison 1; post-step poison 1. Covered stale/missing/duplicate/
misbound permits, bad rows/digests/state, nonfinite claims, foreign gradient,
count mismatch, actor mutation, and forbidden stock/public calls.

## AC. Static/public guards and regressions

R4: critic step callsites 1, live ValueNorm update callsites 1, R4 backward
callsites 0, scheduler callsites 0, violations 0, and no R4 reference in 57
production files. Three R1 pure suites passed. R2 source guard passed with one
central backward callsite and production-only isolation passed over 57 files.
R3 static/public passed with one reviewed actor step and zero R3 backward calls.

The old R2 aggregate helper additionally assumes all later private training
extensions cannot reference R2; it flags R3's already reviewed R2 reuse. This
is not a production leak, as the production-only check passed. Frozen R2 was
not modified.

## AD. Exact execution counts

Final passing harness: critic backward 10; critic step 10; live ValueNorm update
9; critic parameter mutation 10; optimizer-state mutation 10; ValueNorm
mutation 9; actor backward 0; actor step attempted/executed 1/0; actor and actor
optimizer mutations 0; scheduler step 0; disabled probes 1; pre-mutation
failures 55; poisoned failures 1+1. Isaac/runtime, training,
evaluation/playback, checkpoint weight I/O, and public activation were all 0.

Transparent task-wide total across three R4 harness invocations, including two
diagnostic runs stopped before final PASS: critic backward 20, critic step 20,
live ValueNorm update 18, and corresponding critic/optimizer/ValueNorm mutation
events 20/20/18. Invocation deltas were `1/1/2`, `9/9/7`, and `10/10/9`.
Actor/scheduler executions stayed 0. All objects were disposable in-memory CPU
fixtures; no weights were saved.

## AE. Retained nonclaims

R4 is controlled critic/ValueNorm mutation evidence pending independent GPT
review. It does not establish a full learner update, training-update readiness,
rollover, Isaac integration, convergence, evaluation, checkpoint compatibility,
or public learned-policy readiness. Public route: DORMANT / BLOCKED. B2-R5,
training, long training, Isaac, playback/evaluation, checkpoint I/O, staging and
commit remain NOT AUTHORIZED. Stop after R4.
