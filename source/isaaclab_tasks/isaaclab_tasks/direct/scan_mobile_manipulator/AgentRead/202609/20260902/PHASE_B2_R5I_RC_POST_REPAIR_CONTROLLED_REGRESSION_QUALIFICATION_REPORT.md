# Phase B2-R5I-RC Post-Repair Controlled Regression Qualification Report

Date: 2026-09-02 (Asia/Shanghai)

## Classification

```text
PHASE-B2-R5I-RC-POST-REPAIR-CONTROLLED-REGRESSION-QUALIFIED-AWAITING-GPT-REVIEW

B2-R5I-RC:
  POST-REPAIR CONTROLLED REGRESSION QUALIFICATION COMPLETE
  AWAITING GPT REVIEW

B2-R5I:
  NOT COMPLETE

historical real route:
  PARTIAL_UPDATE / POISONED / PROCESS STOPPED

real Isaac reentry:
  NOT AUTHORIZED
```

The narrow `[B,1]` canonical-row repair passed the required pure, controlled
R3 real-mutation, controlled R5 full-transaction, and static/private/public
qualification gates. This result qualifies the local repair only. It neither
retries nor completes real B2-R5I.

## A. Starting authority and scope

```text
branch:       main
HEAD:         b71d85a32f51be6ada324f870813a56bb45dd396
origin/main:  b71d85a32f51be6ada324f870813a56bb45dd396
merge-base:   b71d85a32f51be6ada324f870813a56bb45dd396
relationship: HEAD == origin/main == merge-base
```

- B2-R0: GPT REVIEW PASS / FROZEN.
- B2-R1 through B2-R5: GPT REVIEW PASS / CLOSED.
- B2-R5I: NOT COMPLETE; the failed real route remains historical,
  partial-update, poisoned, and stopped.
- The accumulated dirty tree, including the monthly archive migration and
  earlier private artifacts, was preserved.
- No `git add`, commit, push, Isaac, AppLauncher, training, evaluation,
  playback, or checkpoint command was run.

## B. Required reads and repair under qualification

The B2-R5I failure report, current `TASK_PROGRESS.md`, reviewed R3 report,
reviewed R5 report, `AGENTS.md`, repaired R3 source, and exact repaired source
sites were read before mutation testing.

The production repair under qualification is:

```python
if mask.ndim not in (1, 2) or (mask.ndim == 2 and mask.shape[1] != 1):
    fail_closed(...)
return tuple(mask.reshape(-1).nonzero(as_tuple=False).flatten().tolist())
```

Both factor-pre/post DVM evaluation and off-DVM prior-accumulation witness
selection call that same extractor. Its source SHA-256 remained:

```text
08eb3442ac52dc4f7fd69434486ee7ec77920c64e614d0a19944f4b163b078e3
```

No production semantic source was modified in B2-R5I-RC. Test-only fixtures
and evidence output were strengthened so the controlled R3 and R5 paths use
`[B,1]` masks and reproduce the failed real geometry.

## C. Files modified and created

Test-only files modified:

- `scripts/environments/test_assignment_phase_b2_r5i_real_shape_binding_pure.py`
- `scripts/environments/_assignment_phase_b2_r3_actor_mutation_helpers.py`
- `scripts/environments/test_assignment_phase_b2_r3_controlled_actor_optimizer_mutation_factor.py`
- `scripts/environments/_assignment_phase_b2_r5_full_transaction_helpers.py`
- `scripts/environments/test_assignment_phase_b2_r5_controlled_private_full_learner_transaction.py`

Documentation created or updated:

- this report;
- `TASK_PROGRESS_ARCHIVE_BEFORE_B2_R5I_RC_HANDOFF_20260902.md`;
- top-level `AgentRead/TASK_PROGRESS.md` after the byte-exact archive.

No installed HARL file was modified. Verified installed identities:

```text
happo.py:    dd44fe7842160aa215b2d220726f6dd5e70b251c1a2e9c50cfeb6bd00535cf96
v_critic.py: ae66390702efb55099d151c11f28ae533f25ef6d62697949445abd2979708bf3
valuenorm.py:a35471b136567bde0b7fc7be34a7873efa617bdabf9a9074517ff0e3ef3fb8b0
```

## D. Pure `[B]` / `[B,1]` shape evidence

One dedicated pure test invocation passed:

```text
accepted logical encodings:      2  ([B], [B,1])
true-row cases:                  2
off-DVM/false-row cases:         2
wider fail-closed cases:         1  ([B,2])
duplicate canonical rows:        0
out-of-range canonical rows:     0
false row-0 injections:          0
learner mutations:               0
Isaac/runtime actions:           0
```

For both encodings:

```text
DVM rows:     (0,1)
off-DVM rows: (2,3)
```

Thus `[B]` and `[B,1]` produce identical logical row sets, row 0 is excluded
from the real-failure off-DVM witness pattern, and `[B,2]` fails with the
factor STOP authority.

## E. R1 plan/factor regression

The reviewed R1 update-plan/factor pure suite passed after the test-only
fixture changes:

```text
actor-plan faults:             8
critic-plan faults:           10
factor faults:                 9
full-index transitions:        2
executed mutations:            0
off-DVM exact one:           true
```

## F. Controlled R3 real-mutation qualification

One authoritative controlled R3 harness invocation passed using installed
HAPPO actors, their real Adam optimizers, the reviewed backward seam, and the
actual repaired R3 source.

All actor DVM and active masks used logical shape `[6,1]`. Canonical rows were:

```text
actor  DVM             off-DVM
0      (0,1,3,4)       (2,5)
1      (0,1,4,5)       (2,3)
2      ()              (0,1,2,3,4,5)
```

Actor order was `(0,1,2)`. Actor 0 created a non-one accumulated factor on row
3. Actor 1 was then off-DVM on rows `(2,3)` while row 0 remained DVM-valid.
The repaired same-source extractor selected `(2,3)` exactly, did not inject row
0, preserved actor 0's row-3 accumulation, and completed actor 1's factor
post-audit without `STOP — B2-R FACTOR`.

Successful-sequence mutation counts:

```text
actor backward / optimizer.step: 8 / 8
per actor:                        4/4, 4/4, 0/0
distinct actor parameters mutated:      2
distinct actor optimizer states mutated:2
factor-pre evaluations:          1,1,0
factor-post evaluations:         1,1,0
factor post-audit PASS:          2
factor updates:                  1,1,1
```

The forced-only actor remained exact zero-step. Original behavior logprob,
factor-pre logprob, and factor-post logprob retained distinct roles. No new
training row appeared from shape normalization.

Factor pre/post logprob digests:

```text
actor0 pre:  515035a7443a89530f4ffdff8ae352faa7f1794636bfa0f63c4251dac6927812
actor0 post: a6fd5244b57e5cfab698d5accc4308d8e3a5c831e1baf09817aaf7935d4eb128
actor1 pre:  1922d258b65ce81473b400bd0cef1098b58040195304703e66df78f493e54aeb
actor1 post: a8adb38d7f9000b2ee1bd4ad8f543e3c93a5d1a169878e2dbedb85f8a2407135
```

Full-index factor recurrence digests:

```text
F0 / actor0 before:
  f46913286d895f62d646314f400fc3d7a543cf34eb4ae56df87f43dc4582a36b
actor0 ratio / after / actor1 before:
  ed7d434ff80c10a2acb035eeb7d77d9be72ee8551069b5a43ecb7513641d1913
actor1 ratio:
  cded5d1a1065273133ea2aa23dd4bb1336bdf4ac67b03a71cd6948aa6f59f3c0
actor1 after / actor2 before and after:
  e9e337b9f2f01860fc8472bb2c17dcc27521db55b0e856dc81d2e396709b1f4f
actor2 exact-one ratio:
  f46913286d895f62d646314f400fc3d7a543cf34eb4ae56df87f43dc4582a36b
```

Every transition passed `F_after = F_before * ratio_full`; off-DVM ratios were
exact one; the current actor's loss used only the preceding completed factor;
and factor updated once per actor segment.

Foreign-state isolation passed: the non-target actors, their optimizers,
critic, critic optimizer, and live ValueNorm remained unchanged at each actor
step; gradients were clean. All authorized parameter and optimizer states were
finite.

Task-wide R3 invocation counts include the required disposable post-step
poison case:

```text
successful mutation sequences:          1
actor backward / optimizer.step:         9 / 9
per actor:                               5/5, 4/4, 0/0
factor post-audit PASS in success:        2
pre-step failure assertions:             48
post-step poisoned failures:              1
unauthorized step attempts trapped:      14
critic optimizer steps:                   0
live ValueNorm updates:                    0
```

There were no diagnostic R3 reruns.

## G. Controlled R5 full-transaction qualification

After R3 passed, one authoritative controlled R5 harness invocation passed
using the repaired R3 source and `[6,1]` factor masks. One successful full
transaction traversed exactly:

```text
S0_ROLLOUT_COMPLETE
-> S1_FINAL_VALUE_EVALUATED
-> S2_EVENT_RETURNS_FROZEN
-> S3_UPDATE_PLAN_FROZEN
-> S4_TRAINING_MODE_ENTERED
-> S5_ACTOR_SEQUENCE
-> S6_CRITIC_SEQUENCE
-> S7_POST_UPDATE_AUDIT
-> S8_ROLLOUT_MODE_RESTORED
-> S9_ROLLOVER_COMPLETE
-> S10_QUIESCENT
```

Successful-transaction counts:

```text
actor backward / optimizer.step:     8 / 8
per actor:                           4/4, 4/4, 0/0
critic backward / optimizer.step:    1 / 1
live ValueNorm.update:               1
factor post-audit PASS:              2
training-mode entry / restoration:   1 / 1
critic rollover:                     1
terminal-ledger reset:               1
actor storage rollover:              3
successful full transactions:        1
S10 entries:                          1
```

The actor factor began at
`f46913286d895f62d646314f400fc3d7a543cf34eb4ae56df87f43dc4582a36b`
and ended at
`e9e337b9f2f01860fc8472bb2c17dcc27521db55b0e856dc81d2e396709b1f4f`.
Critic exact physical-row coverage was `(0,1,2,3,4,5)` once. Critic and live
ValueNorm mutations passed source-faithful attribution and finiteness audits.

S7 passed before S8. The exact S9 order was:

```text
critic_buffer.after_update
terminal_ledger.reset
actor_storage[0].rollover
actor_storage[1].rollover
actor_storage[2].rollover
```

Terminal keys changed from `((0,0,10),(1,0,11),(2,1,12))` to empty only at
the authorized reset. S10 proved zero gradients, permits, terminal keys,
incomplete receipts and poison; cursors and rollout modes were valid.

Successful transaction evidence:

```text
plan digest:       4033e8a40af452de99f0971145f76c9714f952b348e4a431572157d0ed4086b3
evidence digest:   7ed3d312a18f6d69cd6a7e16c95a4190d3603a542bb23558ca54baab36bac5f7
quiescence digest: 7a38f1be0d56c44379566835774b4b503181f805561902e28c3aec288e4229fb
```

Task-wide R5 invocation counts include the mandatory pre-mutation and four
post-mutation failure transactions:

```text
successful full transactions / S10: 1 / 1
actor backward / optimizer.step:    33 / 33
per actor:                          17/17, 16/16, 0/0
critic backward / optimizer.step:    3 / 3
live ValueNorm.update:               4
training-mode entries / restore:     5 / 1
critic rollover / ledger reset:      1 / 1
actor storage rollover:              3
pre-mutation failed transactions:    1
post-mutation poisoned transactions: 4
pure integrated fault assertions:   33
static/public faults:                 9
```

There were no diagnostic R5 reruns.

## H. Static, private, and public guards

The R3 and R5 harnesses re-ran their reviewed static guards. The R5I harness
was invoked with `--static-only`; its worker/supervisor transaction path was
not entered.

```text
reviewed backward executors:             1
reviewed actor optimizer.step executors: 1
reviewed critic optimizer.step executors:1
reviewed live ValueNorm.update executors:1
R5 actor / critic sequence calls:        1 / 1
private dependency edges:                18
R5I adapter R5 coordinator calls:        1
R5I adapter event-return calls:          1
new R5I backward/step/ValueNorm calls:   0 / 0 / 0
environment reset/step/make in adapter:  0
public production files scanned:         57
public private-route references:         0
scheduler steps:                          0
```

## I. Verification commands and results

All commands used `C:\isaacenvs\isaac45_harl\python.exe` through the approved
conda executable.

1. Interpreter identity: PASS.
2. `py_compile` for the repaired R3 source and five modified qualification
   test/helper files: PASS.
3. Dedicated `[B]`/`[B,1]` pure shape test: PASS.
4. R1 update-plan/factor pure regression: PASS.
5. Controlled R3 actor-mutation/factor regression: PASS.
6. Controlled R5 private full-transaction regression: PASS; S10 reached once.
7. R5I `--static-only` private/public guard: PASS.
8. R3/R5 static guards embedded in their controlled harnesses: PASS.

The installed Gym deprecation notice remained non-fatal and did not affect
the results.

## J. Exact qualification action counts and nonclaims

```text
pure shape test invocations:                 1
controlled R3 successful mutation sequences:1
R3 actor backward / optimizer.step:          9 / 9 task-wide
R3 factor post-audit PASS:                   2 authoritative success
controlled R5 successful full transactions: 1
R5 S10 entries:                              1
R5 actor optimizer.step:                     8 success / 33 task-wide
R5 critic optimizer.step:                    1 success / 3 task-wide
R5 live ValueNorm.update:                    1 success / 4 task-wide
R5 critic rollover:                          1
R5 terminal-ledger reset:                    1
R5 actor storage rollover:                   3
Isaac/AppLauncher launches or actions:       0
checkpoint weight I/O:                       0
training campaigns:                          0
evaluation/playback:                         0
public route activations:                    0
```

This qualification does not establish a successful real B2-R5I transaction,
real-runtime learner integration, training-update readiness, convergence,
policy quality, checkpoint recovery, public-route readiness, B2-R6, or B2-R7.
The public learned-policy route remains DORMANT / BLOCKED.

## K. Handoff archive and next boundary

The pre-RC `TASK_PROGRESS.md` archive is byte-exact:

```text
source/archive bytes: 5274 / 5274
SHA-256: 9347ea71da92b94dcf947b4ea527786532ed50bbfa8312f4498a63de3151cd25
byte equality: true
```

Next is independent GPT review of this post-repair controlled qualification.
Do not rerun real Isaac, begin R6/R7, train, evaluate/play back, save/load
weights, activate the public route, stage B2-R5I-RC paths, or commit.
