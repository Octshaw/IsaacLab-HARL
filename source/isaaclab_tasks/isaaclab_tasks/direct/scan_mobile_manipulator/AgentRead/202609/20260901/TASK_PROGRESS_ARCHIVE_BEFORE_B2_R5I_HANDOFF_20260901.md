# Lifecycle-aware Dynamic MRTA — Task Progress

Updated: 2026-09-01

## Current status

B2-R0: GPT REVIEW PASS / FROZEN

B2-R1: GPT REVIEW PASS / CLOSED

B2-R2: GPT REVIEW PASS / CLOSED

B2-R3: GPT REVIEW PASS / CLOSED

B2-R4: GPT REVIEW PASS / CLOSED

B2-R5:
  CONTROLLED PRIVATE FULL LEARNER TRANSACTION IMPLEMENTATION COMPLETE
  AWAITING GPT REVIEW

controlled private full-learner integration:
  COMPLETE / AWAITING GPT REVIEW

real Isaac full-learner integration:
  NOT AUTHORIZED / NOT ESTABLISHED

training-update readiness:
  NOT YET ESTABLISHED

public learned-policy route:
  DORMANT / BLOCKED

training / long training:
  NOT AUTHORIZED

classification:
  PHASE-B2-R5-CONTROLLED-PRIVATE-FULL-LEARNER-TRANSACTION-INTEGRATION-COMPLETE-AWAITING-GPT-REVIEW

## Documentation-only archive hierarchy migration

Classification:
`AGENTREAD-MONTHLY-ARCHIVE-HIERARCHY-MIGRATION-COMPLETE-AWAITING-GPT-REVIEW`

- Migrated all 42 top-level daily archive directories from `YYYYMMDD` to
  `YYYYMM/YYYYMMDD` across months `202606`, `202607`, `202608`, and `202609`.
- Preserved every date directory and its internal filenames and structure.
- Updated `AGENTS.md` so all future plans, reports, design notes,
  investigations, phase summaries, and `TASK_PROGRESS.md` archives use the
  monthly-grouped daily hierarchy permanently.
- Repaired repository path references and the relative Markdown links whose
  targets moved one level deeper.
- Verified that no top-level eight-digit date directory or active old-style
  path reference remains; the 373 pre-existing archive files were preserved
  byte-for-byte through the move before reference-only edits.
- This task changed documentation/archive structure only. No runtime, RL,
  HARL, environment, controller, wrapper, solver, reward, observation/action,
  training, or scenario behavior changed. No training or simulation was run,
  and installed `site-packages` were not modified.

## Latest completed phase

The private R5 coordinator composes the reviewed R1 authority/plans, R2 unique
backward, R3 actor/factor mutation sequence and R4 critic/live-ValueNorm
sequence into one S0-S10 transaction. It then performs the guarded order:

```text
S7 full audit
-> S8 rollout-mode restore
-> critic_buffer.after_update
-> terminal-ledger reset
-> three actor-storage rebuilds from final current slots
-> S10 QUIESCENT
```

The successful transaction used controlled CPU `T=2,E=3,M=3,N=4`: actors
0/1 executed `4/4` backward/steps, forced actor2 `0/0`, critic `1/1`, and live
ValueNorm `1`. It reached S10 with zero gradients, permits, terminal keys,
incomplete receipts or poison. Checkpoint boundary eligibility was evidence
only; checkpoint I/O was 0.

Integrated failure transactions passed at S0, S5 actor post-step, S6
post-ValueNorm, S6 post-critic-step and S7 post-audit. Every post-mutation fault
poisoned the route and denied S8/S9/S10, rollover and ledger reset.

## Exact authoritative harness counts

- successful full transactions / S10: `1 / 1`
- actor backward/step: `33 / 33`; per actor `17/17, 16/16, 0/0`
- critic backward/step: `3 / 3`
- live ValueNorm updates: `4`
- training-mode entries / rollout restorations: `5 / 1`
- critic rollover / ledger reset / actor rollovers: `1 / 1 / 3`
- pre-mutation failed transactions: `1`
- actor-post-step, post-ValueNorm, post-critic-step, post-audit poison: `1` each
- pure integrated faults: `33`; static/public faults: `9`
- Isaac/runtime rollout, training, evaluation/playback, checkpoint I/O,
  scheduler step, public activation: all `0`

Two diagnostic runs each reached one disposable S10 before a test assertion
bug. Transparent task-wide totals are successful/S10 `3/3`, actor `49/49`,
critic `5/5`, ValueNorm `6`, critic rollover/ledger reset/actor rollovers
`3/3/9`. No state was saved.

## Static and regression evidence

The explicit private graph has 18 allowlisted edges. Unique executor counts are
R2 backward 1, R3 actor step 1, R4 critic step 1, R4 ValueNorm update 1; R5 has
one R3 and one R4 sequence call and no executor duplicate. Fifty-seven
production files have zero R5 references. Three R1 pure suites plus bounded
R2/R3/R4 static guards passed; standalone earlier-phase mutation harnesses were
not replayed.

## Key files

- `assignment_event_training_full_transaction.py`
- `assignment_event_training_full_transaction_guards.py`
- `scripts/environments/_assignment_phase_b2_r5_full_transaction_helpers.py`
- `scripts/environments/test_assignment_phase_b2_r5_controlled_private_full_learner_transaction.py`

## Detailed reports / archives

- `202609/20260901/PHASE_B2_R5_CONTROLLED_PRIVATE_FULL_LEARNER_TRANSACTION_INTEGRATION_REPORT.md`
- `202609/20260901/TASK_PROGRESS_ARCHIVE_BEFORE_B2_R5_HANDOFF_20260901.md`
- `202609/20260901/AGENTREAD_MONTHLY_ARCHIVE_HIERARCHY_MIGRATION_REPORT.md`

The archive is byte-exact to the pre-R5 handoff: SHA-256
`3e58607b3b2d77b638d39a4a0ac57007edaa31040aa52be19d7cbc49961e88ef`,
3,418 bytes.

## Known issues / blockers

No controlled R5 implementation blocker remains. The usual installed Gym
deprecation notice appears during HARL imports and did not affect results.

## Do not do

Do not run real Isaac, start training, begin R6a/R6b or R7, perform checkpoint
weight I/O, activate the public learned-policy route, stage, commit or push.

## Next step

Independent GPT review of controlled B2-R5 only. After review, the user will
separately decide whether a real Isaac single transaction is required before
R7. Do not make that readiness decision in this phase.
