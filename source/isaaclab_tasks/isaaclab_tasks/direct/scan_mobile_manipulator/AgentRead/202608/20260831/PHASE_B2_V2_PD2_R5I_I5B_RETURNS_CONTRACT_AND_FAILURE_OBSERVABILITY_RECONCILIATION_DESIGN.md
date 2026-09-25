# Phase B2-V2-PD2-R5-I — I5b Returns Contract and Failure-Observability Reconciliation Design

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
```

R5-I is design-only, source-audit-only, and documentation-only. It does not modify the formal harness, I5a/I5b/I6, production, installed HARL, environment, wrapper, DirectMARLEnv, Kit/cache, or any frozen lifecycle/P2/Ak contract.

## 2. R5-H formal review closure

R5-H remains frozen as:

```text
artifact classification: PD2-STOP-TERMINAL-TRANSPORT-FAIL
first boundary:          S6_I5B_RETURNS
last durable PASS:       S5 / continuation_second_step_pass
supervisor/worker/AppLauncher: 1/1/1
retry/repair/second run:      0/0/0
shutdown:                EXTERNAL_CLEAN_TERMINATION / safe=true
postrun:                 NO_OBSERVED_STATE_CHANGE
```

R5-I does not change the formal artifact or retroactively label R5-H PASS. It reconciles the failed harness predicate against the exact protected source that produced the R5-H object.

## 3. What R5-H really proves

- S0, S0R, S1_ENTER, Gate A, environment construction, Gate B, reset, I1/I2, S2, S3, S4, and S5 are real PASS evidence and remain frozen.
- S5 is the first real lifecycle-continuation PASS: six forced continuation rows, no policy rows, no second-step actor calls, no proposals, no claim mutations, and exact P2 -> Ak -> controller continuation.
- Timeout-call identity and exactly-one timeout call are durable PASS evidence.
- `finish_rollout()` returned before the failed `require`.
- The route's advantage contract returned and the harness independently observed `[T,E,1]` finite advantages.
- The combined returns predicate evaluated false.
- Shutdown was safe for R5-H and protected postrun state was unchanged.

## 4. What R5-H does not prove by artifact alone

The JSON artifact did not durably preserve:

- actual event-result returns shape;
- independent shape and finite predicate results;
- NaN/+Inf/-Inf counts or locations;
- buffer storage shape, training slice, or final slot;
- a complete S6 summary/checkpoint;
- Snapshot B or the final parameter comparison.

Therefore the artifact alone cannot distinguish a shape failure from a nonfinite failure. R5-I adds a protected-source reconciliation; it does not rewrite the artifact's evidence content.

## 5. Current `S6_I5B_RETURNS` failure

The frozen harness line 4714 checks:

```python
tuple(rollout.event_returns_result.returns.shape) == (T + 1, E, 1)
and bool(torch.isfinite(rollout.event_returns_result.returns).all())
```

For R5-H, `T=2`, `E=2`, so the harness expected `(3,2,1)` from the returned I5b result object.

## 6. Combined-predicate evidence gap

The check conflates two predicates and persists neither actual value before `require()`. The later `evidence["s6"]` block would have stored only shape, but it is constructed after the failed assertion and was never reached.

This violates the required observability order:

```text
inspect actual object
-> build bounded evidence
-> persist evidence
-> adjudicate shape
-> adjudicate finite status
```

## 7. I5b source audit

`compute_event_gae_returns_v2()` derives `T,E` from `rewards[T,E,1]`, validates `value_preds[T+1,E,1]`, and creates:

```text
advantages = zeros_like(rewards)                    [T,E,1]
returns = advantages + arithmetic_value_preds[:-1] [T,E,1]
```

It then explicitly checks all `returns` entries finite before constructing `EventGAEReturnComputationV2`, and stores a detached, cloned, contiguous tensor (`assignment_event_gae_returns.py:407-438`). A nonfinite result raises `EventGAEReturnsError` before a result DTO can be returned.

The pure result is therefore source-authoritatively:

```text
shape:         [T,E,1]
dtype:         torch.float32
device:        rollout critic-buffer device
requires_grad: false
contiguous:    true
finite:        all entries
scale:         unnormalized return/critic-target scale
```

## 8. `event_returns_result` source audit

`EventGAEReturnComputationV2` currently contains exactly:

```text
schema_version
returns
advantages
deltas
bootstrap_values
trace_continue_masks
arithmetic_value_preds
```

`EventOnPolicyCriticBufferEPV2.compute_event_returns()` returns that exact DTO. I6 assigns it to local `event_returns`, emits it to the existing observer, and then places the same DTO object into `EventDormantLearnedRolloutResultV2.event_returns_result` without another clone (`assignment_event_learned_route.py:594-649`).

The DTO contains enough live tensor data to derive bounded shape/finite evidence, but it does not contain precomputed bounded metadata, expected shape, independent verdicts, buffer final-slot semantics, or durable evidence. R5-H did not use the existing observer point to persist those facts.

## 9. Critic-buffer returns source audit

Installed `OnPolicyCriticBufferEP` allocates:

```text
self.returns = zeros([T+1,E,1], float32, device)
```

The repo-local event subclass requires GAE and commits only:

```python
self.value_preds[-1].copy_(next_value)
self.returns[:-1].copy_(result.returns)
```

It never calls installed `compute_returns()`. Its `after_update()` delegates to installed rollover—which copies only share observations, critic RNN state, masks, and bad masks—then clears I5a event fields and the once guard. Neither method writes `returns[T]`.

## 10. Exact object identity/copy map

| Object | Producer/owner | Shape | Identity/copy relation | Consumer and lifetime |
|---|---|---:|---|---|
| A. `critic_buffer.returns` | installed buffer allocation; event buffer owns mutation | `[T+1,E,1]` | independent mutable storage | rollout storage; only `[:-1]` enters advantage/training |
| B. `EventGAEReturnComputationV2.returns` | I5b pure computation | `[T,E,1]` | detached contiguous clone of temporary D | audit/result lifetime; no buffer alias |
| C. `rollout.event_returns_result.returns` | I6 composition result | `[T,E,1]` | exact same DTO/tensor object as B | returned bounded rollout result |
| D. local `returns` | `advantages + arithmetic_value_preds[:-1]` | `[T,E,1]` | new ephemeral tensor, then cloned into B | validated then discarded after function return |
| E. training target slice | `critic_buffer.returns[:-1]` | `[T,E,1]` | view of A; content copied from B | reshaped/selected into `return_batch` for critic |

The feed-forward generator reshapes E to `[T*E,1]` and advanced-indexes minibatches; recurrent generators likewise derive batches only from `returns[:-1]`. `VCritic` consumes the generated `return_batch`, not B/C and not A's final slot.

## 11. Exact shape contract for frozen `T=2,E=2`

| Object | General shape | R5-H shape |
|---|---:|---:|
| event result `returns` | `[T,E,1]` | `[2,2,1]` |
| critic-buffer `returns` storage | `[T+1,E,1]` | `[3,2,1]` |
| critic training slice `returns[:-1]` | `[T,E,1]` | `[2,2,1]` |
| flattened critic target | `[T*E,1]` | `[4,1]` |
| route advantages | `[T,E,1]` | `[2,2,1]` |
| result GAE advantages/deltas/bootstrap/trace | `[T,E,1]` | `[2,2,1]` |
| `value_preds` storage | `[T+1,E,1]` | `[3,2,1]` |
| rewards / reasons / timeout value/mask | `[T,E,1]` | `[2,2,1]` |
| masks / bad_masks | `[T+1,E,1]` | `[3,2,1]` |
| ordinary final `next_value` | `[E,1]` | `[2,1]` |
| full-E evaluated timeout values | `[E,1]` | `[2,1]` |

## 12. Training-slice contract

The authoritative critic target is `critic_buffer.returns[:-1]`, not the full buffer and not a separate reconstruction. All installed EP critic generators exclude the final slot. For R5-H it is `[2,2,1]`; a feed-forward critic would receive minibatches derived from `[4,1]`.

The event result `returns` and buffer training slice must be exactly equal in value at commit, but must not alias. The current source enforces this through a result clone followed by `copy_()` into buffer storage.

## 13. Final-slot semantics

`critic_buffer.returns[T]` is an inherited storage slot, not the event result's final element. In the event-GAE path:

```text
explicitly written by event compute: no
bootstrap holder:                 no
critic training target:           no
advantage input:                  no
rollover source/destination:       no
initialized value:                zero at buffer construction
event semantic invariant:         none beyond storage shape/dtype/device
```

It is not `next_value`; `next_value` is explicitly written to `value_preds[T]`. It is not safe to relabel `returns[T]` as a computed return or bootstrap target.

## 14. Final-slot write trace

All relevant writes are:

1. installed buffer constructor zero-initializes the entire `[T+1,E,1]` returns tensor;
2. event compute writes only `returns[0:T]` by `self.returns[:-1].copy_(result.returns)`;
3. event `after_update()` does not write or clear returns;
4. installed GAE branches also write only `returns[step]`, not `returns[-1]`;
5. installed non-GAE branches write `returns[-1]=next_value`, but the event buffer rejects `use_gae=False` and the I6 route excludes installed `compute_returns()`.

Thus the event final slot may legally remain untouched. In a pristine first rollout it remains the finite zero initializer, but source does not define a learner-facing finite/zero invariant for that unused slot.

## 15. Critic training target trace

```text
I5b unnormalized result.returns [T,E,1]
-> copy into critic_buffer.returns[:-1]
-> feed-forward / naive recurrent / recurrent generator
-> return_batch [batch,1]
-> VCritic.update()
-> VCritic.cal_value_loss()
```

ValueNorm OFF compares `return_batch` directly with critic output. ValueNorm ON first updates normalizer statistics from unnormalized `return_batch`, then normalizes `return_batch` for value loss. No R5-H optimizer/update occurred because its critic trainer was a recorder.

## 16. Advantage computation trace

I5b's internal GAE `advantages` is `[T,E,1]`. I6 independently derives stock-compatible actor advantages before trainers:

```text
ValueNorm OFF:
  critic_buffer.returns[:-1] - critic_buffer.value_preds[:-1]

ValueNorm ON:
  critic_buffer.returns[:-1]
  - value_normalizer.denormalize(critic_buffer.value_preds[:-1])
```

It clones the result and requires `[T,E,1]` and all finite. R5-H reached and passed both the internal I6 validation and the external harness advantage check.

This rules out a nonfinite critic training slice at that point under the exact protected source. It does not prove anything about unused `critic_buffer.returns[T]`, and the artifact still lacks independently persisted return metadata.

## 17. ValueNorm OFF semantics

- critic-native `value_preds` and timeout values are used directly;
- delta, GAE, result returns, buffer training targets, and advantages remain in that native/unnormalized scale;
- no ValueNorm state exists or is updated;
- TIME_LIMIT still uses the I5a timeout value and stops trace.

## 18. ValueNorm ON semantics

- I5b concatenates all native rollout values and only mask-selected timeout values;
- one current installed ValueNorm snapshot denormalizes them under inference mode;
- I5b verifies the normalizer state/mode did not change and calls no `update()`;
- delta/GAE/returns are computed and stored unnormalized;
- I6 derives advantages with the same current normalizer's denormalized `value_preds[:-1]`;
- only a later real critic training call would update statistics from `return_batch` and normalize targets for loss.

R5-H used ValueNorm ON but recorder-only trainers. It performed no normalizer update, optimizer, or backward operation.

## 19. Exact TIME_LIMIT return path

```text
pre-reset terminal critic observation
-> EventTerminalLearnerRecordV2 (truncated=true, bootstrap present)
-> exact terminal correlation
-> identity-selected exactly-one timeout critic call
-> full-E timeout_bootstrap_value_preds[t] + mask[t]
-> I5a insert at transition t
-> masks[t+1]=0; bad_masks[t+1]=0 for compatibility only
-> I5b reason=TIME_LIMIT selects timeout value[t]
-> bootstrap continues for delta
-> trace_continue=0
-> return[t] stored in returns[:-1]
```

Returned post-autoreset `value_preds[t+1]` is ignored for TIME_LIMIT. `bad_masks` is not I5b authority.

## 20. Reason trichotomy

| Reason | Bootstrap | Trace | Returned-current role |
|---|---|---|---|
| `NONE` | `value_preds[t+1] * masks[t+1]` | continues while mask is one | normal current next value |
| `TIME_LIMIT` | authoritative pre-reset timeout critic value | stops | post-reset value ignored |
| `ALL_TASKS_COMPLETED` | zero | stops | ignored |
| `NO_FEASIBLE_TASKS_REMAIN` | zero | stops | ignored |

Termination priority and frozen timeout-call/input contracts are unchanged.

## 21. Predicate authority classification

| Predicate | Object actually checked | Classification | Decision |
|---|---|---|---|
| current full shape `(T+1,E,1)` | result DTO C | **E — unsupported / needs revision** (origin: C, harness assumption) | expected result shape must be `(T,E,1)` |
| result all finite | result DTO C | **A — source-authoritative; D at harness because redundant** | retain separately for observability |
| buffer full storage shape `[T+1,E,1]` | A | **A + B — source and frozen-design authoritative** | retain as structural check |
| training slice shape `[T,E,1]` | A `[:-1]` / B | **A — source-authoritative** | mandatory |
| training slice all finite | A `[:-1]` / B | **A — source-authoritative** | mandatory |
| final slot shape `[E,1]` | A `[T]` | **A — structural source-authoritative** | record separately |
| final slot all finite | A `[T]` | **E — no event-return semantic authority; D only** | diagnostic, not I5b PASS authority |

No frozen design states that `EventGAEReturnComputationV2.returns` has buffer-storage shape. B2-D and I5b use `[T+1,E,1]` for buffer storage, while I5b explicitly commits the returned computation into `returns[:-1]`.

## 22. Main reconciliation decision

The source-proven contract is Option 4:

```text
event result DTO returns:
  [T,E,1], all finite, detached clone

critic-buffer storage:
  [T+1,E,1]

critic training target:
  critic_buffer.returns[:-1] == result.returns

final buffer slot:
  storage-only, not event-written, not trained, no I5b finite invariant
```

Primary R5-I decision:

```text
HARNESS RETURNS ORACLE REVISION REQUIRED
```

Because the protected producer guarantees a successful DTO is finite and deterministically `[T,E,1]`, R5-H's combined predicate failed at its shape subpredicate under the exact current source. This is a harness DTO/buffer conflation, not an I5b implementation-defect candidate and not a ValueNorm/GAE diagnosis.

## 23. Full-buffer, training-slice, and final-slot finite decisions

- Full event result: all finite is mandatory, but its full extent is `[T,E,1]`.
- Buffer training slice: all finite is mandatory and must exactly equal the result values without aliasing.
- Buffer full storage: `[T+1,E,1]` is mandatory structurally; all-finite is not an I5b semantic predicate because its last slot is unused.
- Final slot: record shape and nonfinite counts for localization, but do not fail `S6_I5B_RETURNS` solely on its value under the current source contract.

## 24. I5b result DTO sufficiency audit

The current DTO is sufficient as an in-process source for result returns, internal advantages, deltas, bootstrap values, trace masks, and arithmetic values. It is insufficient as durable evidence because it carries full tensors rather than bounded summaries and says nothing about buffer storage, final slot, expected shapes, equality/no-alias, or independent verdicts.

No production DTO change is needed for the next observability slice. A test-only observer can derive bounded evidence from the actual returned DTO plus the exact buffer at the existing `I5b_compute_event_returns` observer point.

## 25. Future bounded returns DTO design

Proposed harness-local immutable DTO: `PD2S6I5bReturnsEvidenceV1`.

Exact v1 field set:

```text
schema_version
capture_status
source_boundary
event_gae_schema_version
event_buffer_schema_version
T
E
C
valuenorm_enabled
producer_failure_code
producer_failure_stage

result_expected_shape
result_actual_shape
result_shape_pass
result_dtype
result_device
result_numel
result_contiguous
result_requires_grad
result_all_finite
result_nan_count
result_posinf_count
result_neginf_count
result_first_nonfinite_flat_index
result_first_nonfinite_t
result_first_nonfinite_env
result_first_nonfinite_component
result_first_nonfinite_kind

buffer_commit_performed
buffer_storage_expected_shape
buffer_storage_actual_shape
buffer_storage_shape_pass
buffer_storage_dtype
buffer_storage_device
buffer_storage_numel

training_slice_start
training_slice_end_exclusive
training_slice_expected_shape
training_slice_actual_shape
training_slice_shape_pass
training_slice_numel
training_slice_all_finite
training_slice_nan_count
training_slice_posinf_count
training_slice_neginf_count
training_slice_first_nonfinite_flat_index
training_slice_first_nonfinite_t
training_slice_first_nonfinite_env
training_slice_first_nonfinite_component
training_slice_first_nonfinite_kind
training_slice_matches_result_exact
training_slice_no_alias_result

final_slot_index
final_slot_expected_shape
final_slot_actual_shape
final_slot_shape_pass
final_slot_semantics
final_slot_written_by_event_compute
final_slot_training_consumed
final_slot_all_finite
final_slot_nan_count
final_slot_posinf_count
final_slot_neginf_count
final_slot_all_zero

advantages_expected_shape
advantages_actual_shape
advantages_shape_pass
advantages_all_finite
advantages_nan_count
advantages_posinf_count
advantages_neginf_count
advantages_training_shape_match

value_preds_storage_shape
value_preds_training_slice_shape
value_preds_final_slot_shape
value_preds_all_finite
arithmetic_value_preds_shape
arithmetic_value_preds_all_finite

event_slots_complete
timeout_identity_schema_version
timeout_call_identity_pass
timeout_call_count
```

All fields are bounded primitives, tuples, strings, booleans, integers, or null. No tensor, buffer, rollout, DTO reference, environment object, or model object may enter durable evidence. `C` is fixed to one for this contract.

`capture_status` is one of `RETURNED_RESULT` or `TYPED_EVENT_GAE_FAILURE`. If I5b raises `EventGAEReturnsError`, a future test-only catch may inspect its existing ephemeral `failure_code`, `stage`, and tensor-valued `actual` only long enough to build bounded counts. It must not recompute returns.

## 26. Bounded nonfinite-location design

For result and training tensors, persist counts for NaN, +Inf, and -Inf independently. If any exists, persist only the first row-major flat index and its `(t,env,component)` coordinate plus kind. Null all location fields when finite.

For the final slot, `t=final_slot_index` and only `(env,component)` is searched. Counts remain diagnostic and do not become final-slot PASS authority.

`finite_min`, `finite_max`, and `finite_mean` are deferred from v1: they do not distinguish the observed contract failure and must not become authority.

## 27. Failure-boundary refinement

Keep the frozen top-level class and boundary:

```text
classification: PD2-STOP-TERMINAL-TRANSPORT-FAIL
first_boundary: S6_I5B_RETURNS
```

Add a bounded `failure_detail` inside evidence, not an eleventh STOP class:

```text
S6_I5B_RETURNS_RESULT_SHAPE
S6_I5B_RETURNS_RESULT_NONFINITE
S6_I5B_RETURNS_BUFFER_STORAGE_SHAPE
S6_I5B_RETURNS_TRAINING_SLICE_SHAPE
S6_I5B_RETURNS_TRAINING_SLICE_NONFINITE
S6_I5B_RETURNS_RESULT_BUFFER_MISMATCH
```

Final-slot nonfiniteness is recorded as `S6_I5B_RETURNS_FINAL_SLOT_DIAGNOSTIC`, not a fail-closed detail under the current contract.

If multiple predicates fail, persist all verdicts first and select the first detail by the ordered list above. No information is lost to a combined predicate.

## 28. Evidence-before-assertion ordering

Future test-only ordering:

```text
compute_event_returns exactly once
-> existing I6 observer: I5b_compute_event_returns
-> inspect the actual returned result and exact buffer storage
-> build PD2S6I5bReturnsEvidenceV1
-> durably persist i5b_returns_evidence_captured
-> adjudicate result shape [T,E,1]
-> adjudicate result finite
-> adjudicate buffer storage shape [T+1,E,1]
-> adjudicate training slice shape/finite/equality/no-alias
-> record final-slot diagnostic without making it I5b authority
-> continue advantage/trainer/rollover/Snapshot B checks
```

The observer point is before actor trainer, critic trainer, and `after_update()`. It adds zero actor/critic forwards, zero return computations, zero ValueNorm updates, zero optimizer calls, and zero backward calls.

If a typed I5b failure occurs before the observer, the test-only harness catch must persist bounded typed-failure evidence from the exact exception payload before mapping it to `S6_I5B_RETURNS`.

## 29. Pure synthetic test matrix for a future R5-J

| Case | Input | Expected adjudication |
|---|---|---|
| RA | result `[T,E,1]`, finite; storage `[T+1,E,1]`; exact slice | PASS |
| RB | wrong result shape, all finite | result shape FAIL; finite PASS recorded |
| RC | correct shape with NaN | shape PASS; result finite FAIL; NaN count/location exact |
| RD | correct shape with +Inf | result finite FAIL; +Inf evidence exact |
| RE | correct shape with -Inf | result finite FAIL; -Inf evidence exact |
| RF | wrong shape plus nonfinite | both verdicts persisted; shape selected as first detail |
| RG | training slice finite, final slot nonfinite | I5b returns PASS; final-slot diagnostic records anomaly |
| RH | training slice nonfinite, final slot finite | training-slice finite FAIL |
| RI | storage/result/training/final shapes valid | PASS |
| RJ | result finite but buffer training slice differs | exact-match FAIL |
| RK | result aliases buffer training storage | no-alias FAIL |
| RL | ValueNorm OFF | native-scale result/training evidence PASS; zero updates |
| RM | ValueNorm ON | unnormalized result/training evidence PASS; stable normalizer; zero updates |
| RN | typed `returns_nonfinite` failure payload | bounded counts persisted before STOP; no recompute |
| RO | evidence builder invocation | zero extra forwards/compute_returns/optimizer/backward |

RG is not permission to mutate a formal buffer. It establishes only that the unused final slot is not an I5b learner-target predicate under current source.

## 30. Frozen non-returns contracts

R5-I does not reopen:

- S5 real continuation evidence;
- Gate A/B or S1;
- S2 installed VCritic or S3 actor evidence;
- S4 physical P2 -> Ak -> controller authority;
- timeout-call identity, exactly-one timeout call, or exact timeout input;
- terminal historical/current separation or runtime ACK semantics;
- P2 sole authority, proposal/effective separation, or default-off public route.

## 31. No-runtime and no-implementation statement

```text
formal supervisor / worker:        0 / 0
AppLauncher / SimulationApp:       0 / 0
Isaac / CUDA:                      0 / 0
real HARL / VCritic / actor:       0 / 0 / 0
environment construct/reset/step: 0 / 0 / 0
optimizer / backward:              0 / 0
training/playback/evaluation:      0 / 0 / 0
formal retry:                      0
harness implementation:           NONE
I5a/I5b/I6 implementation:         NONE
production/installed HARL changes: NONE
commit:                            NONE
```

No Python test, synthetic execution, or runtime command was needed. All conclusions come from static source/call-path inspection and protected hashes.

## 32. Protected integrity

The pre-documentation protected set contains 22 rows: the reviewed formal harness; terminal learner transport; I5b GAE, critic-buffer, and I6 route sources; wrapper, environment, and DirectMARLEnv; installed HARL EP buffer, ValueNorm, VCritic, HA runner, and base runner; R5-C, R5-D, R5-D-TR, R5-D-TR2, R5-E, R5-F, R5-G, R5-H; and the pre-R5-I `TASK_PROGRESS.md`.

Key identities before documentation:

```text
formal harness:
  593fad7a980d584954e7a55cecb4a91234ad16e7dc4064c96c75f59e9bcccd34
I5b GAE:
  7d9f154571ee43a1918d4f33f888c8b180c7c8731e8a474fdf31e32ba1923379
event critic buffer:
  682e924fb2c9196818b9ef537ecda8eee46408d6828b4e380718786597adc29f
I6 route:
  b883ee48dfe0a15cc01ddf01b0bd1914a17e0627e6cc145c214f8b369b4d371b
installed EP buffer:
  0a288f3888908b98157a0848744d7eebec655159d5e89d9c85436a2e30b9a46f
installed ValueNorm:
  a35471b136567bde0b7fc7be34a7873efa617bdabf9a9074517ff0e3ef3fb8b0
installed VCritic:
  ae66390702efb55099d151c11f28ae533f25ef6d62697949445abd2979708bf3
R5-H report:
  a5549e16392ba3bac99d89bf93c37436aa915e902d04ee0e269465a0306d7353
pre-R5-I TASK_PROGRESS:
  80859d25bbfd315d8e1ed9556b4f7c3981f19439d3eb78f723572cbf6e0e61d5
```

The exact pre-update handoff is archived as `TASK_PROGRESS_ARCHIVE_BEFORE_PD2_R5I_HANDOFF_20260831.md` with the same SHA-256. Post-write verification must leave every non-documentation protected row exact.

## 33. Final classification

```text
classification:
  PHASE-B2-V2-PD2-R5I-I5B-RETURNS-CONTRACT-AND-OBSERVABILITY-DESIGN-PASS-AWAITING-GPT-REVIEW

primary decision:
  HARNESS RETURNS ORACLE REVISION REQUIRED

source-proven event result shape:
  [T,E,1] = [2,2,1]

source-proven buffer storage shape:
  [T+1,E,1] = [3,2,1]

source-proven critic target:
  critic_buffer.returns[:-1]

I5b implementation defect:
  NOT ESTABLISHED

I6 composition defect:
  NOT ESTABLISHED

R5-H / B2-V2:
  FROZEN STOP / STOPPED-INCOMPLETE

next implementation:
  NOT AUTHORIZED

B2-R / training / commit:
  NOT AUTHORIZED / NOT AUTHORIZED / NONE
```

## 34. Recommended next step

Stop for GPT independent design review.

Only after review PASS and a new explicit user authorization may a candidate `B2-V2-PD2-R5-J` modify the test-only harness to implement the bounded evidence/oracle revision with pure/static tests. R5-J implementation, any formal R5-K reentry, learner repair, runtime, B2-R, and training are not authorized by R5-I.
