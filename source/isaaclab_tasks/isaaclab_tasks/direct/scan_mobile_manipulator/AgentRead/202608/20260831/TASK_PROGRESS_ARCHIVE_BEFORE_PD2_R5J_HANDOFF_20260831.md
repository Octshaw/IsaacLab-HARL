# TASK_PROGRESS

Updated: 2026-08-31

Authoritative current classification: `PHASE-B2-V2-PD2-R5I-I5B-RETURNS-CONTRACT-AND-OBSERVABILITY-DESIGN-PASS-AWAITING-GPT-REVIEW`

## Current status

```text
committed checkpoint HEAD:         14993dee344bade0230d2eb97b5f22171331f44a
Lifecycle Runtime Backbone:        COMMITTED / CLOSED CHECKPOINT
B1W-I4-4:                          GPT REVIEW PASS / CLOSED
B2-D:                              GPT REVIEW PASS / FROZEN
B2-I0 through B2-I6:               GPT REVIEW PASS / CLOSED
B2-V1:                             GPT REVIEW PASS / CLOSED
B2-V2-PD1:                         GPT REVIEW PASS / FROZEN
PD-A mode:                         CURRENT-PRODUCTION-RUNTIME-VALIDATION / FROZEN
B2-V2-PD2-R5-G:                    GPT REVIEW PASS / CLOSED
B2-V2-PD2-R5-H:                    FORMAL STOP REVIEW CONFIRMED / FROZEN

B2-V2-PD2-R5-I:                    DESIGN PASS / AWAITING GPT REVIEW
primary reconciliation:            HARNESS RETURNS ORACLE REVISION REQUIRED
artifact classification:           PD2-STOP-TERMINAL-TRANSPORT-FAIL
first failing boundary:             S6_I5B_RETURNS
last durable formal PASS:           S5 / continuation_second_step_pass

B2-V2:                             STOPPED / INCOMPLETE
runtime readiness:                 BLOCKED
policy readiness:                  BLOCKED
learner readiness:                 BLOCKED
public learned-policy event route: DORMANT / BLOCKED
B2-R:                              NOT AUTHORIZED
training:                          NOT AUTHORIZED
commit:                            NONE
```

R5-I was design-only, source-audit-only, and documentation-only. It did not run or modify the formal harness, Isaac, CUDA, HARL, the environment, production, training, Kit/cache, or frozen lifecycle contracts.

## Latest completed work — R5-I returns reconciliation design

R5-H stopped at this combined harness predicate:

```python
tuple(rollout.event_returns_result.returns.shape) == (T + 1, E, 1)
and bool(torch.isfinite(rollout.event_returns_result.returns).all())
```

The R5-H artifact did not independently persist shape and finiteness, so its artifact-only subcause remains unknown. R5-I then reconciled the exact protected source and established:

```text
EventGAEReturnComputationV2.returns: [T,E,1]
critic_buffer.returns storage:       [T+1,E,1]
critic training target:              critic_buffer.returns[:-1] == result.returns
final buffer returns slot:           storage-only / not written by event compute /
                                     not consumed by event advantages or critic training
```

For the frozen `T=2,E=2` horizon:

```text
event result returns:    [2,2,1]
buffer returns storage:  [3,2,1]
training target slice:   [2,2,1] -> flattened return_batch [4,1]
```

The current harness expected the buffer-storage shape on the event result DTO. Under the exact protected source, a successfully returned DTO has already passed I5b's finite validation. Therefore the source-reconciled failure is the result-shape subpredicate, caused by result/storage contract conflation.

This establishes a test-harness oracle revision requirement. It does **not** establish an I5b implementation defect, I6 composition defect, ValueNorm defect, GAE defect, or learner defect.

## Active contract

The future test-only oracle must treat four objects separately:

1. event result DTO: `[T,E,1]`, detached and finite;
2. buffer storage: `[T+1,E,1]`;
3. training slice: `buffer.returns[:-1]`, `[T,E,1]`, finite and exact-value-equal to the result without aliasing;
4. final storage slot: `[E,1]`, structurally present but not an event learner target or bootstrap holder.

The unused final slot may be recorded diagnostically, but its value is not an `S6_I5B_RETURNS` finite-pass authority under the current contract.

The future bounded evidence design records result, storage, training-slice, advantages, ValueNorm mode, timeout-call identity, independent finite counts, and first nonfinite location before any assertion. It preserves the frozen top-level class and boundary:

```text
classification: PD2-STOP-TERMINAL-TRANSPORT-FAIL
first_boundary: S6_I5B_RETURNS
```

More precise failures belong in bounded `failure_detail`; no new top-level STOP class is authorized.

## ValueNorm and TIME_LIMIT findings

- ValueNorm OFF: returns and targets remain on native unnormalized scale.
- ValueNorm ON: I5b denormalizes rollout and selected timeout values exactly once, computes unnormalized returns, and does not update normalizer state.
- Only future real critic training may update ValueNorm statistics from the unnormalized `return_batch`; R5-H used recorders and ran no optimizer/backward.
- `TIME_LIMIT` uses the exactly correlated pre-reset terminal critic value for bootstrap while stopping the trace.
- true terminals (`ALL_TASKS_COMPLETED`, `NO_FEASIBLE_TASKS_REMAIN`) use zero bootstrap and stop the trace.
- `NONE` uses the ordinary next current value/liveness path and continues the trace.

No frozen termination priority, terminal/current separation, timeout-call identity, P2 authority, proposal/effective separation, or `P2 -> Ak -> controller` contract was reopened.

## Files changed in R5-I

Created:

- `AgentRead/202608/20260831/PHASE_B2_V2_PD2_R5I_I5B_RETURNS_CONTRACT_AND_FAILURE_OBSERVABILITY_RECONCILIATION_DESIGN.md`
- `AgentRead/202608/20260831/TASK_PROGRESS_ARCHIVE_BEFORE_PD2_R5I_HANDOFF_20260831.md`

Updated:

- this file.

```text
production changes:           NONE
harness changes:              NONE
I5a/I5b/I6 changes:           NONE
installed HARL changes:       NONE
Kit/cache edits:              NONE
optimizer/backward:           0 / 0
Isaac/CUDA/HARL runtime:      NOT RUN
training/playback/evaluation: NOT RUN
checkpoint changes:           NONE
commit:                       NONE
```

## Latest verification

- Read-only static source/call-path audit of I5b GAE, event critic buffer, I6 route, installed EP critic buffer, ValueNorm, VCritic, HA runner, and base runner.
- The archived pre-R5-I handoff has the exact pre-update SHA-256 `80859d25bbfd315d8e1ed9556b4f7c3981f19439d3eb78f723572cbf6e0e61d5`.
- Protected production, harness, I5/I6, installed HARL, and prior-report hashes remained unchanged across documentation work.
- `git diff --check`: PASS.
- No Python tests or runtime commands were executed because R5-I was pure read-only analysis plus documentation.

## Known issues / blockers

- R5-H / B2-V2 remains stopped and incomplete at `S6_I5B_RETURNS`.
- The formal artifact still lacks independent returns shape/finiteness evidence; R5-I resolves the protected-source contract but does not rewrite the frozen artifact.
- The reviewed test-only harness still contains the incorrect combined returns oracle; R5-I does not implement its revision.
- I5b complete formal adjudication, rollover, Snapshot B, and final mutation comparison remain unreached.
- Runtime, policy, learner, and training readiness remain blocked.

## Do not do

- Do not implement the R5-I DTO/oracle design without a new explicit authorization.
- Do not rerun R5-H, retry B2-V2, or enter a formal reentry.
- Do not modify production, I5a/I5b/I6, the reviewed harness, installed HARL, DirectMARLEnv, lifecycle contracts, Kit, or cache.
- Do not activate the public route or enter B2-R.
- Do not run Isaac, CUDA, HARL runtime, optimizer, backward, training, playback, evaluation, or checkpoint work.
- Do not stage or commit.
- Do not claim B2-V2, runtime, policy, learner, or training readiness.

## Next step

Stop for GPT independent review of the R5-I design.

Only after review PASS and new explicit user authorization may a candidate `B2-V2-PD2-R5-J` implement the bounded evidence and returns-oracle revision in the test-only harness, with pure/static tests. R5-J implementation, formal R5-K reentry, learner repair, runtime, B2-R, and training are not authorized now.

## Detailed reports / archives

- `AgentRead/202608/20260831/PHASE_B2_V2_PD2_R5I_I5B_RETURNS_CONTRACT_AND_FAILURE_OBSERVABILITY_RECONCILIATION_DESIGN.md`
- `AgentRead/202608/20260831/TASK_PROGRESS_ARCHIVE_BEFORE_PD2_R5I_HANDOFF_20260831.md`
- `AgentRead/202608/20260831/PHASE_B2_V2_PD2_R5H_ONE_CONTROLLED_FORMAL_REENTRY_REPORT.md`
- `AgentRead/202608/20260831/TASK_PROGRESS_ARCHIVE_BEFORE_PD2_R5H_FORMAL_REENTRY_20260831.md`
- `AgentRead/202608/20260831/PHASE_B2_V2_PD2_R5G_INTEGRAL_HORIZON_FIXTURE_AND_S1_BOUNDARY_IMPLEMENTATION_REPORT.md`
- `AgentRead/202608/20260829/PHASE_B2_V2_PD2_R5F_INTEGRAL_HORIZON_TIMING_AND_S1_BOUNDARY_RECONCILIATION_DESIGN.md`
- `AgentRead/202608/20260829/PHASE_B2_V2_PD2_R5E_ONE_CONTROLLED_FORMAL_REENTRY_REPORT.md`
- `AgentRead/202608/20260829/PHASE_B2_V2_PD2_R5D_TR2_TIMEOUT_CRITIC_INVOCATION_IDENTITY_REPORT.md`
- `AgentRead/202608/20260829/PHASE_B2_V2_PD2_R5D_TR_S6_EXACT_TIMEOUT_CRITIC_INPUT_CORRELATION_REPORT.md`

