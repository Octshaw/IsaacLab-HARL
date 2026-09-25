# Lifecycle-aware Dynamic MRTA — Task Progress

Updated: 2026-09-12

## Current status

```text
B2-R0 through B2-R7: GPT REVIEW PASS / CLOSED
B2-T0-LD: GPT REVIEW PASS / CLOSED
B2-T0-RE1: GPT REVIEW PASS / CLOSED
B2-T0: GPT REVIEW PASS / CLOSED
B2-T1: GPT REVIEW PASS / CLOSED

B2-T2:
  MEDIUM-LENGTH TRAINING OBSERVABILITY/STABILITY COMPLETE
  AWAITING GPT REVIEW

successful medium updates: 300 / 300
S10: 300 / 300
cross-transaction bridges: 299 / 299 PASS

medium-length training stability: COMPLETE / AWAITING GPT REVIEW
training observability: QUALIFIED / AWAITING GPT REVIEW

long training: NOT AUTHORIZED
checkpoint continuation: NOT ESTABLISHED
B2-R6: NOT AUTHORIZED
public learned-policy route: DORMANT / BLOCKED
```

Classification:
`PHASE-B2-T2-MEDIUM-LENGTH-TRAINING-OBSERVABILITY-STABILITY-QUALIFIED-AWAITING-GPT-REVIEW`

## Latest completed phase

Phase B2-T2 executed exactly 300 consecutive successful real learner updates
in one fresh mutation-bearing process, one AppLauncher, one real environment,
and one persistent learner. Formal run ID was
`b2-t2-medium-training-12584`, PID 12584, with no retry after learner
mutation and worker exit code 0. Tx300 S10 was followed by one final read-only
quiescence check; tx301 was not started.

Runtime resolution remained `T/E/M/N = 2/2/3/12`, actor and critic
epochs/minibatches `5/2`, ValueNorm enabled, `fixed_order=false`, device
`cuda:0`, and private profile `event_gated_local_mrta`. Exactly 300 fresh
rollout batches used 600 physical environment steps.

## Lifecycle and transaction result

Six hundred decision-boundary receipts covered 3,600 rows:

```text
policy-required: 1861
continuation: 1739
forced-noop/nondecision: 0
actor policy-call faults: 0
missing / duplicate / continuation-resample faults: 0 / 0 / 0
```

All 300 transactions contained asynchronous mixtures of policy-required and
continuation rows: `(6,6,0)` 253 times, `(7,5,0)` 33 times, and `(8,4,0)`
14 times. Physical step was not decision authority. All 299 bridges passed
exact learner/object/parameter/optimizer/Adam/ValueNorm continuity plus clean
ledger/permit/gradient/cursor/rollout/compute-once/fresh-provenance checks.

## Learner counts and numerical health

```text
actor backward / optimizer.step: 4750 / 4750
actor totals by actor: 1655 / 1500 / 1595
factor audits: 900
critic minibatches / backward / optimizer.step: 3000 / 3000 / 3000
VALID_NONZERO_UPDATE: 2979
VALID_ZERO_EFFECTIVE_UPDATE: 21
ValueNorm.update: 3000
critic rollovers / ledger resets / actor rollovers: 300 / 300 / 900
event-return computations / stock compute_returns: 300 / 0
S7 / S8 / S9 / S10: 300 / 300 / 300 / 300
```

All six actor orders occurred. Actor Adam ended at `(1655,1500,1595)` and
critic Adam at 3000, exactly matching executed plans. Parameters, optimizer
state, ValueNorm, losses, gradients, returns, ratios, and factors remained
finite. Final state was unpoisoned, in rollout mode, gradient/ledger clean,
cursor/compute-once reset, and quiescent.

## Read-only observability result

The 24-row observer schema was pure-qualified before AppLauncher and produced
zero mutations across 600 formal steps. Available authoritative/read-only
metrics include team/per-agent reward, coverage, canonical task-state counts,
completion/release/failure events, lifecycle row mix, terminal reasons,
duplicate/reach diagnostics, learner losses/gradient norms, critic classes,
and raw/effective action histograms. Exact reassignment events and policy
entropy are `NOT AVAILABLE`; neither was inferred or recomputed.

Diagnostic-only results:

```text
team reward per update: mean -0.0662064, range [-0.0715446,-0.0573333]
coverage: 0 across 600 observations
completed viewpoints/events: 0 / 0
release / failure / new failed-pair events: 0 / 0 / 0
duplicate scans / reach violations: 0 / 0
actor loss: mean -0.0489670, range [-1.4877584,1.1328919]
critic loss: mean 0.00599559, range [3.48e-13,2.7138209]
```

These observations establish instrumentation/stability only. They do not
establish convergence, task performance, policy quality, or improvement.

## Process and preflight accounting

One `formal01` diagnostic worker (PID 15628) stopped before AppLauncher,
environment, reset, learner, or update because a schema artifact preceded the
base artifact guard. It contributed zero updates. The narrowly corrected
`formal02` route used exactly one mutation-bearing worker and no retry after
mutation.

Preflight passed the approved interpreter, 19-file `py_compile`, geometry,
ValueNorm 53 assertions, CG, LD 13/13, observer nonmutation, synthetic
ledger/window/compaction probes, and static/private/public guards. Frozen
preflight and immediate post-run static artifacts were byte-identical at
SHA-256 `921fc83d...832`.

The formal observer SHA-256 was `b93ccbad...1e356`; the formal harness was
`f542ab00...c6ce`. After worker exit, a test-only repair moved success artifact
postprocessing outside the worker because `simulation_app.close()` terminates
that process before caller resumption. The repaired harness is
`b842dad5...d8943`; static checks still pass with all qualified production,
installed, LD, T0, and T1 identities exact. Production semantic modifications:
**0**.

## Evidence artifacts

Artifacts are under `%TEMP%` with prefix
`b2_t2_medium_training_20260911_formal02_`.

```text
transaction summaries: 300
bridge summaries: 299
lifecycle aggregates: 300
training metric rows: 300
task-progress rows: 300
rolling health rows: 10
```

Rolling rows exist at tx001/010/025/050/075/100/150/200/250/300. Full detail
is retained for sentinel tx001/030/100/200/300. Success-only compaction removed
2,073 redundant files and retained 36 bounded artifacts; no model weights were
written. Key SHA-256 values:

- compact final result: `9b747d0380dcc9d6a9b9ec15d83b3fb390b3edce6a60bfb1a25929ef19a422f8`;
- supervisor: `70d7d3c5a5b1db86bdf28ed9127cf5ecbe974734c0bf29eb3db1196c65494079`;
- transaction ledger: `914c21179a6eeb1e3d096ee47926205ceff400eb55ad58a26c6c1dab3f11bc9a`;
- bridge ledger: `cbc49e911a3b134792246503f2249b27304290a0ace7a5ab68ae399f19daa103`;
- artifact manifest: `cbe24beb08952799824b79747367cbbcb0799aa16c54a60018df476dfe02b20b`;
- observability schema: `6c8ed69b48ae6b5eebe4fc4ebd2ed65e30597866e6c1bd1c877d77e41b65a9f3`.

## Repository preservation

Formal authority remained `main` at
`b71d85a32f51be6ada324f870813a56bb45dd396`, equal to origin/main and the
merge-base. The 359 staged monthly-migration paths, staged-index SHA-256
`a40169043c3bfffd481a7ed1bddf3e52663d61379bedfd2610781457d11f947c`,
and monthly path-set SHA-256
`0f2b8f7b52148e39196cbeb40fd9f4edd94fb762b6daf8be6279a116b80a39ab`
were preserved.

The pre-rewrite archive is byte-exact to the prior progress file: 7,347 bytes,
SHA-256
`a1a76037b6e180a03d1ac4ba18752c3f6f4fd5bb1d69a76bd683512973f29669`.

## Historical failures preserved

B2-R5I attempts 1/2/3 and B2-T0 run03 remain poisoned/stopped/historical and
were not reused or reclassified. Run03 tx2 actor-2's exact historical cause
remains `UNRESOLVED FROM EXISTING DURABLE ARTIFACTS`. B2-T0-LD, B2-T0-RE1,
B2-T0, and B2-T1 evidence and reports remain retained.

## Retained nonclaims

B2-T2 does not establish convergence, policy quality, reward/coverage
improvement, task completion performance, multi-seed robustness, paper-scale
or long-run stability, arbitrary/variable cardinality, checkpoint continuation
or exact resume, evaluation/playback readiness, B2-R6 readiness, or public
learned-policy-route readiness.

## Do not do

Do not start tx301, long/paper-scale training, B2-R6, checkpoint save/load,
evaluation, playback, public-route activation, staging, commit, or push without
new explicit authorization. Never reuse a poisoned historical route.

## Next step

Independent GPT review of B2-T2. Do not self-classify `GPT REVIEW PASS`.

## Detailed reports / archives

- `202609/20260911/PHASE_B2_T2_MEDIUM_LENGTH_TRAINING_OBSERVABILITY_STABILITY_QUALIFICATION_REPORT.md`
- `202609/20260911/TASK_PROGRESS_ARCHIVE_BEFORE_B2_T2_HANDOFF_20260911.md`
- `202609/20260911/PHASE_B2_T1_BOUNDED_SHORT_TRAINING_STABILITY_QUALIFICATION_REPORT.md`
- `202609/20260910/PHASE_B2_T0_RE1_BOUNDED_REPEATED_UPDATE_CONTINUITY_REPORT.md`
- `202609/20260910/PHASE_B2_T0_LD_LIFECYCLE_DECISION_GATING_QUALIFICATION_REPORT.md`
- `202609/20260909/PHASE_B2_R7_TRAINING_UPDATE_READINESS_FINAL_CLOSURE_REPORT.md`
