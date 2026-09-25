# Lifecycle-aware Dynamic MRTA — Task Progress

Updated: 2026-09-10

## Current status

```text
B2-R0: GPT REVIEW PASS / FROZEN
B2-R1 through B2-R7: GPT REVIEW PASS / CLOSED
B2-T0-LD: GPT REVIEW PASS / CLOSED

B2-T0 run03:
  PARTIAL_UPDATE / POISONED / STOPPED / HISTORICAL

B2-T0-RE1:
  COMPLETE / AWAITING GPT REVIEW

successful B2-T0-RE1 transactions: 3 / 3
B2-T0-RE1 S10: 3 / 3
durable S10 -> next-S0 bridges: 2 / 2 PASS
lifecycle decision gating: REAL REPEATED-RUN PASS / AWAITING GPT REVIEW
repeated-update continuity: COMPLETE / AWAITING GPT REVIEW

training-update readiness: REVIEW PASS / ESTABLISHED
real Isaac single-transaction integration: REVIEW PASS / ESTABLISHED
checkpoint weight I/O: 0
public learned-policy route: DORMANT / BLOCKED
B2-R6a/R6b: NOT AUTHORIZED
long training / evaluation / playback: NOT AUTHORIZED
```

Classification:
`PHASE-B2-T0-RE1-BOUNDED-REPEATED-UPDATE-CONTINUITY-COMPLETE-AWAITING-GPT-REVIEW`

## Latest completed phase

Phase B2-T0-RE1 executed exactly three consecutive real learner transactions
in one fresh Python process, one AppLauncher lifetime, one Isaac environment,
and one persistent learner construction. The formal worker was PID 16980 with
run ID `b2-t0-re1-repeated-smoke-16980`; it returned exit code 0 with no retry.

The runtime-resolved bounded profile remained `T/E/M/N = 2/2/3/12`, actor and
critic epochs/minibatches `5/2`, ValueNorm enabled, and `fixed_order=false`.
Exactly six physical steps produced three fresh rollout batches. No tx4 was
started.

## Lifecycle decision evidence

Six durable boundary receipts covered 36 environment/robot rows:

```text
policy-required rows: 20
continuation rows: 16
forced-noop rows: 0
missing / duplicate / continuation-resample faults: 0 / 0 / 0
```

Tx2 collection 4 produced the asynchronous call geometry
`(0,0,1,0,0,0)`: env0 robot2 was a current reopened
`NEEDS_ASSIGNMENT/POLICY_DECISION_ROW`, while the other five rows were forced
continuations. Tx3 collection 6 independently produced `(0,0,0,1,0,0)`.
Physical step was not used as decision authority.

## Repeated-update and bridge result

Transaction actor orders were `(1,2,0)`, `(0,2,1)`, and `(1,0,2)`. Actor
backward/optimizer counts were `15/15`, `20/20`, and `20/20`; aggregate
`55/55`. Critic backward/step and ValueNorm update were `10/10/10` per
transaction, aggregate `30/30/30`. Critic classes were 17
`VALID_NONZERO_UPDATE` plus 13 `VALID_ZERO_EFFECTIVE_UPDATE`.

Both bridges have durable two-stage evidence:

- bridge 1 pre receipt was written after global step 2 and before step 3;
- bridge 1 post receipt was written after tx2 collection validation and before
  tx2 mutation;
- bridge 2 pre receipt was written after global step 4 and before step 5;
- bridge 2 post receipt was written after tx3 collection validation and before
  tx3 mutation.

Across both bridges, actor/critic parameters, actor/critic optimizer state,
Adam counters, and ValueNorm matched exactly from previous post-update to next
pre-collection and stayed unchanged during collection. Learner object IDs were
stable; ledgers, permits, gradients, cursors, rollout modes, and compute-once
state satisfied the bridge/S10 guards. Both next S0 entries were established.

## Terminal, rollover, and quiescence

Six natural timeout/autoreset events had unique historical keys. Runtime ACK
did not consume learner evidence; the ledger survived to S9 and reset once per
transaction. Totals were three critic rollovers, three ledger-reset
invocations, and nine actor rollovers.

Reviewed event returns executed exactly three times; stock HARL
`compute_returns` executed zero times. S7/S8/S9/S10 were each `3/3 PASS`.
The final read-only check found the route unpoisoned, learner finite, models in
rollout mode, gradients clear, ledger empty, permits zero, cursors reset, and
current runtime state valid.

## Historical failures preserved

- B2-R5I attempt 1: post-actor-mutation `[B,1]` factor-audit failure;
  `PARTIAL_UPDATE / POISONED / STOPPED / HISTORICAL`.
- B2-R5I attempt 2: CUDA live ValueNorm fingerprint observability failure;
  `PARTIAL_UPDATE / POISONED / STOPPED / HISTORICAL`.
- B2-R5I attempt 3: old nonzero-only critic guard rejection after ValueNorm
  mutation; `PARTIAL_UPDATE / POISONED / STOPPED / HISTORICAL`.
- B2-R5I attempt 4: real single transaction and S10; `GPT REVIEW PASS / CLOSED`.
- B2-T0 run03: tx1 S0-S10 completed, tx2 stopped during collection under the
  old physical-step harness overconstraint; poisoned and permanently historical.
- Run03 tx2 actor-2 exact historical cause remains
  `UNRESOLVED FROM EXISTING DURABLE ARTIFACTS`.

RE1 does not reuse or reclassify any historical route.

## Files changed or created

Modified before formal learner mutation:

- `scripts/environments/test_assignment_phase_b2_t0_bounded_repeated_update_training_smoke.py` — RE1-only harness/observer logging, two-stage bridge durability, provenance, and artifact binding.

Documentation:

- `AgentRead/TASK_PROGRESS.md`;
- `202609/20260910/PHASE_B2_T0_RE1_BOUNDED_REPEATED_UPDATE_CONTINUITY_REPORT.md`;
- `202609/20260910/TASK_PROGRESS_ARCHIVE_BEFORE_B2_T0_RE1_HANDOFF_20260910.md`.

Production semantic source modifications by RE1: **0**. Installed HARL
modifications: **0**.

## Latest verification

All preflight checks passed: approved interpreter; 13-file `py_compile`;
`[B]`/`[B,1]` geometry; ValueNorm 53 assertions; CG critic classification;
LD 13/13 matrix; and static/private/public authority.

```text
backward / actor step / critic step / ValueNorm executors: 1 / 1 / 1 / 1
R5 actor / critic sequence calls: 1 / 1
scheduler steps: 0
reviewed private dependency edges: 18
public activation references: 0
```

Production and installed HARL hashes matched R7. LD helper SHA-256 remained
`af607d6d24c908f7c78e1af3ed3843bd2c87921309a6eb36514e37be95aa6052`;
RE1 harness SHA-256 was
`a77c5caa8847980973aba718f19e7e1f8533cbb0c6756856272e8d29f5bfb95f`.

Repository authority remained `main` at
`b71d85a32f51be6ada324f870813a56bb45dd396`, equal to `origin/main` and the
merge-base. The 359 staged monthly-migration paths, staged-index SHA-256
`a40169043c3bfffd481a7ed1bddf3e52663d61379bedfd2610781457d11f947c`,
and monthly path-set SHA-256
`0f2b8f7b52148e39196cbeb40fd9f4edd94fb762b6daf8be6279a116b80a39ab`
were preserved.

The pre-rewrite archive is byte-exact to the prior progress file:

```text
bytes: 8242
sha256: 020a64a2faf11d391271942b876e53b66a0bfe2f2abdfdf0135cc1249c9b6b26
```

No stage, commit, or push occurred.

## Known issues and retained nonclaims

B2-T0-RE1 is a bounded continuity/integration gate. It does not establish long
training stability, convergence, policy quality, reward/coverage improvement,
multi-seed robustness, arbitrary cardinality, checkpoint continuation/exact
resume, evaluation/playback readiness, or public learned-policy readiness.

## Do not do

Do not start B2-R6, checkpoint work, long training, evaluation/playback, public
route activation, staging, commit, or push without new explicit authorization.
Do not reuse run03 or any B2-R5I poisoned route.

## Next step

Independent GPT review of the B2-T0-RE1 report and durable JSON artifacts.
Do not self-classify `GPT REVIEW PASS`.

## Detailed reports / archives

- `202609/20260910/PHASE_B2_T0_RE1_BOUNDED_REPEATED_UPDATE_CONTINUITY_REPORT.md`
- `202609/20260910/TASK_PROGRESS_ARCHIVE_BEFORE_B2_T0_RE1_HANDOFF_20260910.md`
- `202609/20260910/PHASE_B2_T0_LD_LIFECYCLE_DECISION_GATING_QUALIFICATION_REPORT.md`
- `202609/20260910/TASK_PROGRESS_ARCHIVE_BEFORE_B2_T0_LD_HANDOFF_20260910.md`
- `202609/20260909/PHASE_B2_T0_BOUNDED_REPEATED_UPDATE_TRAINING_SMOKE_REPORT.md`
- `202609/20260909/PHASE_B2_R7_TRAINING_UPDATE_READINESS_FINAL_CLOSURE_REPORT.md`
- `202609/20260909/PHASE_B2_R5I_REAL_ISAAC_SINGLE_TRANSACTION_ATTEMPT4_REPORT.md`
- `202609/20260908/PHASE_B2_R5I_CG_CRITIC_ZERO_EFFECTIVE_GRADIENT_CLASSIFICATION_REPORT.md`
