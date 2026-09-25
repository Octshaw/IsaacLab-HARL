# Phase B2-V2-PD2-R5-J — I5b Returns Observability and Oracle Revision Implementation

Date: 2026-08-31

## 1. Starting authority

```text
committed checkpoint HEAD: 14993dee344bade0230d2eb97b5f22171331f44a
B2-D:                      GPT REVIEW PASS / FROZEN
B2-I0 through B2-I6:       GPT REVIEW PASS / CLOSED
B2-V1:                     GPT REVIEW PASS / CLOSED
B2-V2:                     STOPPED / INCOMPLETE
B2-V2-PD1:                 GPT REVIEW PASS / FROZEN
PD-A:                      CURRENT-PRODUCTION-RUNTIME-VALIDATION / FROZEN
R5-G:                      GPT REVIEW PASS / CLOSED
R5-H:                      FORMAL STOP REVIEW CONFIRMED / FROZEN
R5-I:                      GPT REVIEW PASS / FROZEN
```

R5-J was explicitly authorized as test-only implementation plus pure/static/CPU-synthetic verification. Formal runtime, R5-K, B2-R, training, playback, evaluation, optimizer, backward, and commit were not authorized.

## 2. R5-I GPT review closure

R5-I's source-reconciled contract is frozen:

```text
event result DTO returns:       [T,E,1]
critic-buffer returns storage:  [T+1,E,1]
critic training slice:          returns[:-1] == result returns, exact copy, no alias
final returns slot:             structural/storage-only/diagnostic
primary decision:               HARNESS RETURNS ORACLE REVISION REQUIRED
```

R5-J implemented that contract without changing I5b, I6, HARL, ValueNorm, learner semantics, or lifecycle/runtime authority.

## 3. Authorized mutation scope

Only the reviewed test-only formal harness and documentation were changed:

- `scripts/environments/test_assignment_phase_b2_v2_pd2_production_startup_path_real_interface_smoke.py`
- this implementation report;
- the pre-R5J `TASK_PROGRESS.md` archive;
- current `TASK_PROGRESS.md`.

No helper file was required.

## 4. Files changed

Modified:

- `scripts/environments/test_assignment_phase_b2_v2_pd2_production_startup_path_real_interface_smoke.py`
- `AgentRead/TASK_PROGRESS.md`

Created:

- `AgentRead/202608/20260831/PHASE_B2_V2_PD2_R5J_I5B_RETURNS_OBSERVABILITY_AND_ORACLE_REVISION_IMPLEMENTATION_REPORT.md`
- `AgentRead/202608/20260831/TASK_PROGRESS_ARCHIVE_BEFORE_PD2_R5J_HANDOFF_20260831.md`

Production, I5a/I5b/I6, environment, wrapper, runtime facade, DirectMARLEnv, installed HARL, Kit/cache, training, and checkpoint files were not modified.

## 5. Historical R5-H preservation

R5-H remains exactly:

```text
classification:        PD2-STOP-TERMINAL-TRANSPORT-FAIL
first failing boundary: S6_I5B_RETURNS
last durable PASS:      S5 / continuation_second_step_pass
```

The R5-H JSON and report were not changed. Its artifact still did not independently record which subpredicate failed. R5-J does not retroactively pass R5-H or B2-V2.

## 6. Old returns oracle retirement

The active harness requirement that event-result shape equal `(T + 1,E,1)` was removed. Static review proves that historical conflated predicate is absent from `run_real_smoke()`.

The replacement separates four objects rather than treating a result DTO as storage.

## 7. Event result shape implementation

`PD2S6I5bReturnsEvidenceV1` records independently:

- expected and actual result shape;
- shape verdict;
- dtype, device, numel, contiguity, and `requires_grad`;
- finite verdict and bounded NaN/+Inf/-Inf evidence.

The active result contract is `(T,E,1)`, which is `(2,2,1)` for the frozen formal configuration.

## 8. Buffer storage shape implementation

The actual `critic_buffer.returns` object is inspected separately. Its structural contract remains `(T+1,E,1)`, or `(3,2,1)` for frozen formal R5-H configuration.

This check is no longer applied to `event_returns_result.returns`.

## 9. Training-slice oracle

The harness inspects the actual `critic_buffer.returns[:-1]` view. It requires:

```text
shape:             [T,E,1]
all finite:        true
result equality:   exact
result aliasing:   false
```

The installed critic-buffer source remains protected and all three generator paths consume `returns[:-1]` rather than the unused final storage slot.

## 10. Exact-value equality oracle

The implementation uses:

```python
torch.equal(training_slice, result_tensor)
```

It does not use `allclose`, tolerance, rounding, normalization, or value reconstruction. This mirrors the current protected `copy_` path exactly.

## 11. No-alias oracle

The implementation compares underlying Torch storage identities using `untyped_storage().data_ptr()` with a compatibility fallback. It does not mutate either tensor.

The oracle therefore detects shared storage even when two views have different offsets/data pointers.

## 12. Final-slot diagnostic semantics

`critic_buffer.returns[T]` must structurally have shape `[E,1]`. The DTO records its finite state, NaN/+Inf/-Inf counts, and all-zero diagnostic.

Its value is not used in the I5b fail-closed PASS predicate. A nonfinite or nonzero final slot produces only:

```text
S6_I5B_RETURNS_FINAL_SLOT_DIAGNOSTIC
```

The implementation explicitly records:

```text
final_slot_written_by_event_compute: false
final_slot_training_consumed:        false
final_slot_semantics:                STORAGE_ONLY_DIAGNOSTIC_NOT_EVENT_RESULT_OR_LEARNER_TARGET
```

It is not relabeled as bootstrap, next value, TIME_LIMIT value, or rollover authority.

## 13. `PD2S6I5bReturnsEvidenceV1`

The harness-local DTO is `@dataclass(frozen=True, slots=True)` and implements the exact frozen R5-I field set. It groups bounded evidence for:

- capture status and producer failure identity;
- result tensor contract and finite localization;
- buffer storage contract;
- training-slice contract, exact equality, and no-alias;
- final-slot structural/diagnostic state;
- I5b advantages;
- value-pred storage/training/final shapes and finiteness;
- arithmetic value predictions;
- event-slot completeness;
- ValueNorm mode;
- timeout-call identity linkage.

Durable values are only nulls, primitive scalars, small strings, and small tuples. No tensor, NumPy array, rollout, buffer, result DTO, ValueNorm, environment, critic, or actor object is retained.

## 14. Bounded nonfinite evidence

The pure helper independently counts NaN, +Inf, and -Inf. For result/training tensors it records only the first row-major flat index and `(t,env,component)` coordinate plus one of `NAN`, `POSINF`, or `NEGINF`.

Finite tensors retain null location fields. Mean, min, max, standard deviation, and full tensor payloads are omitted.

## 15. Typed producer failure evidence

The real harness now catches the protected `EventGAEReturnsError` type separately. If its exact `failure_code` is `returns_nonfinite` and `actual` is a tensor, the harness inspects that actual payload only long enough to build bounded evidence.

It persists:

```text
capture_status:        TYPED_EVENT_GAE_FAILURE
producer_failure_code
producer_failure_stage
bounded shape/finite/nonfinite metadata
buffer_commit_performed: false
```

The tensor and exception object are not persisted, and returns are not recomputed.

## 16. Evidence-before-assertion ordering

The existing I6 observer point is reused; no production callback or API changed:

```text
single compute_event_returns
-> existing I5b_compute_event_returns observer
-> inspect actual result and actual buffer
-> build bounded DTO
-> atomic checkpoint: i5b_returns_evidence_captured
-> adjudicate independent predicates
-> I6 advantage/trainer/rollover path
```

The typed-producer-error catch uses the same persistence-before-adjudication ordering. Static guards prove the checkpoint write precedes the first R5-J adjudicator call.

## 17. Failure-detail ordering

The top-level historical taxonomy remains ten classes and the boundary remains `S6_I5B_RETURNS`. The first detail is selected in this order after all DTO verdicts are captured:

1. `S6_I5B_RETURNS_RESULT_SHAPE`
2. `S6_I5B_RETURNS_RESULT_NONFINITE`
3. `S6_I5B_RETURNS_BUFFER_STORAGE_SHAPE`
4. `S6_I5B_RETURNS_TRAINING_SLICE_SHAPE`
5. `S6_I5B_RETURNS_TRAINING_SLICE_NONFINITE`
6. `S6_I5B_RETURNS_RESULT_BUFFER_MISMATCH`
7. `S6_I5B_RETURNS_RESULT_BUFFER_ALIAS`

The chosen detail is also propagated as bounded `failure_detail` in the worker primary result. No eleventh top-level STOP class was added.

## 18. ValueNorm non-interference

The DTO records only `valuenorm_enabled`. The observer performs no normalization, denormalization, update, state mutation, optimizer action, or backward call.

ValueNorm OFF retains native unnormalized values. ValueNorm ON retains the single existing protected denormalization/unnormalized-return path. R5-J does not reinterpret either mode.

## 19. Timeout identity linkage

The DTO copies only the already-established bounded timeout identity schema, exact-one call count, and identity verdict. It does not select a timeout call, compare the timeout tensor again, or invoke the critic.

The frozen designated-call, exact `torch.equal`, digest, and exactly-one-forward timeout contracts are unchanged.

## 20. RA–RO synthetic results

All 15 required CPU-only cases passed:

| Case | Contract exercised | Result |
|---|---|---|
| RA | canonical result/storage/training/no-alias and bounded DTO | PASS |
| RB | wrong finite result shape | PASS: shape detail |
| RC | one NaN with exact first location | PASS: result nonfinite detail |
| RD | one +Inf | PASS |
| RE | one -Inf | PASS |
| RF | wrong shape plus nonfinite | PASS: both observed, shape first |
| RG | final-slot-only nonfinite | PASS: diagnostic only, no STOP |
| RH | training-slice nonfinite | PASS: training nonfinite detail |
| RI | all four shape contracts | PASS |
| RJ | exact result/buffer mismatch | PASS: mismatch detail |
| RK | shared-storage alias | PASS: alias detail |
| RL | ValueNorm OFF evidence | PASS / zero updates |
| RM | ValueNorm ON evidence | PASS / zero updates |
| RN | typed producer nonfinite failure | PASS / bounded payload / no recompute |
| RO | no-extra-work counters and static source guard | PASS |

R5-J result:

```text
case_count: 15
failed_cases: none
torch.cuda.is_initialized before/after: false / false
```

## 21. R5-D regression

Command:

```text
C:\isaacenvs\isaac45_harl\python.exe <harness> --r5d-only
```

Result:

```text
PASS
classification: PHASE-B2-V2-PD2-R5D-TR2-TIMEOUT-CALL-IDENTITY-PASS-AWAITING-GPT-REVIEW
pure synthetic cases: 38 / 38 PASS
```

S5, timeout correlation, timeout-call identity, evidence ordering, proposal/effective separation, forced-row bypass, and P2/Ak contracts did not regress.

## 22. R5-G regression

Command:

```text
C:\isaacenvs\isaac45_harl\python.exe <harness> --r5g-only
```

Result:

```text
PASS
classification: PHASE-B2-V2-PD2-R5G-INTEGRAL-HORIZON-AND-S1-BOUNDARY-IMPLEMENTATION-PASS-AWAITING-GPT-REVIEW
R5-D non-timing regression: PASS
```

Integral-horizon Gate A/B and S1 boundary contracts did not regress.

## 23. Static guards

`--static-only` passed. It proves at least:

- result DTO uses `[T,E,1]` and the active old `[T+1,E,1]` result oracle is absent;
- buffer storage uses `[T+1,E,1]`;
- training slice is actual `returns[:-1]`, `[T,E,1]`;
- exact equality and storage no-alias are active;
- final-slot finite/zero values are post-adjudication diagnostics only;
- bounded evidence is persisted before adjudication;
- typed failure has the same ordering;
- no returns recomputation, critic/actor forward, denormalization, ValueNorm update, or backward call was added;
- protected I5b copies only into `self.returns[:-1]`;
- installed learner generators consume `self.returns[:-1]`;
- STOP taxonomy is still exactly ten classes;
- the frozen R5-I report hash is protected.

## 24. No-runtime counters

```text
formal supervisor:      0
worker:                 0
AppLauncher:            0
SimulationApp:          0
Isaac:                  0
gym.make:               0
CUDA runtime:           0
real HARL:              0
real VCritic:           0
real actor:             0
environment construct: 0
reset:                  0
step:                   0
optimizer:              0
backward:               0
training:               0
```

Only CPU Torch synthetic tensors were used. CUDA remained uninitialized.

## 25. Protected integrity

The pre/post protected set contained 23 rows: harness baseline; I5b/I6/terminal transport/runtime sources; environment, wrapper, DirectMARLEnv; installed HARL buffer, ValueNorm, VCritic, HA/base runners; and R5-C through R5-I reports.

Pre/post comparison:

```text
HEAD before/after: 14993dee344bade0230d2eb97b5f22171331f44a / exact
rows compared:     23
authorized change: harness only
all other rows:    exact / unchanged
```

The R5-H report remains `a5549e16392ba3bac99d89bf93c37436aa915e902d04ee0e269465a0306d7353`. The R5-I report remains `ef03379e94906e544604fd0fe62b68a2cd542c0b466773e2800e6a4841bdd99b`.

The exact pre-R5J handoff was archived with SHA-256 `3c8db4bda1e9201898333e64400d90c7000dbcb6f4f17a1e24d20f86256dc856`.

## 26. Harness pre/post SHA

```text
pre-R5J:  593fad7a980d584954e7a55cecb4a91234ad16e7dc4064c96c75f59e9bcccd34
post-R5J: 28b98443c0e0612101738c9b32742416fe00ccb6cc0d391f174d59d816bee8e3
```

## 27. Verification and `git diff --check`

Executed with the exact interpreter `C:\isaacenvs\isaac45_harl\python.exe`:

```text
-m py_compile <updated harness>: PASS
--static-only:                     PASS
--r5d-only:                        PASS
--r5g-only:                        PASS
--r5j-only:                        PASS
git diff --check:                  PASS (exit 0; pre-existing line-ending warnings only)
protected hash comparison:         PASS
```

No AppLauncher, Isaac, CUDA runtime, environment, real HARL, rollout, training, optimizer, or backward command ran.

## 28. Final classification

```text
classification:
  PHASE-B2-V2-PD2-R5J-I5B-RETURNS-OBSERVABILITY-AND-ORACLE-REVISION-PASS-AWAITING-GPT-REVIEW

R5-J:
  IMPLEMENTATION PASS / AWAITING GPT REVIEW

old event-result T+1 oracle:
  RETIRED

bounded observability:
  IMPLEMENTED / PURE+STATIC VERIFIED

B2-V2:
  STOPPED / INCOMPLETE

formal runtime / R5-K:
  NOT RUN / NOT AUTHORIZED

runtime / policy / learner readiness:
  BLOCKED / BLOCKED / BLOCKED

B2-R / training / commit:
  NOT AUTHORIZED / NOT AUTHORIZED / NONE
```

R5-J PASS means only that the test-only harness now uses the source-faithful returns contract and will retain bounded evidence before future S6 returns adjudication. It does not establish a real I5b/S6 PASS, rollover, Snapshot B, final parameter comparison, B2-V2 completion, or readiness.

## 29. Recommended next step

Stop for GPT independent implementation review.

Only after GPT review PASS and separate explicit user authorization may a candidate `B2-V2-PD2-R5-K` perform one controlled formal reentry using the reviewed post-R5J harness identity. R5-K, learner repair, B2-R, runtime readiness, training, playback, evaluation, checkpoint work, staging, and commit are not authorized by R5-J.
