# Phase B2-V2-PD2-R5-D-TR2 — Timeout-Critic Invocation Identity Report

Date: 2026-08-29

Classification: `PHASE-B2-V2-PD2-R5D-TR2-TIMEOUT-CALL-IDENTITY-PASS-AWAITING-GPT-REVIEW`

## 1. Starting authority

Committed checkpoint HEAD remains `14993dee344bade0230d2eb97b5f22171331f44a`. B2-D and B2-I0 through B2-I6 remain reviewed/frozen or closed; B2-V1 remains closed; B2-V2 remains `STOPPED / INCOMPLETE`. R5-C, R5-D, and R5-D-TR were read as immutable historical authority.

This slice authorized only a targeted test-only harness revision plus documentation. Formal PD2 runtime, R5-E, B2-R, production changes, and training remained unauthorized.

## 2. GPT review issue R5D-S6-CALLIDENTITY-02

GPT accepted the exact S6 `torch.equal` input oracle but found that the harness still discovered the timeout invocation by searching all recorded inputs for exactly one equal tensor. This conflated invocation identity with input equality.

`R5D-S6-CALLIDENTITY-02` is now `CLOSED` at the static/pure test-only implementation level.

## 3. Why value equality cannot identify role

If current `V(t)` and timeout bootstrap both receive `X`, two equal matches are valid and a unique-value search falsely fails. Conversely, if current receives expected `X` but the designated timeout call incorrectly receives `Y`, a search can falsely select the earlier current call and pass.

Tensor values, digest, shape, dtype, and device therefore cannot establish timeout-call role. They are examined only after an independently designated invocation exists.

## 4. Source audit of critic call ordering

The frozen I6 source establishes the following deterministic order without a production role tag:

1. `EventDormantLearnedPolicyRouteV2.collect_step()` unconditionally calls current `self.critic.get_values(...)` before actor collection and physical execution (`assignment_event_learned_route.py:474-485`).
2. After the physical result and terminal-info attachment, it calls `EventTerminalLearnerCollectorV2.consume_before_optimizer_update(...)` (`assignment_event_learned_route.py:521-539`).
3. The collector calls `evaluate_event_timeout_bootstrap_values_v2(...)` exactly once and publishes the resulting batch through `I5a_critic_buffer_insert` (`assignment_event_critic_buffer.py:491-500`; route line 540).
4. The timeout evaluator executes `critic.get_values(...)` exactly once when `timeout_input.env_indices` is nonempty, then sets `critic_batch_calls = 1` (`assignment_event_terminal_learner_transport.py:1147-1155,1195-1203`).

No other critic call occurs inside `collect_step()`. `finish_rollout()` has a later ordinary next-value call, but it occurs after S6 timeout-input adjudication and is outside the second-collect cursor.

## 5. Second collect critic-call timeline

The harness records a cursor immediately before the second `collect_step()`:

```text
critic_call_start_before_second = K

second collect:
  relative 0 / global K:     current V(t)
  relative 1 / global K + 1: TIME_LIMIT bootstrap critic

critic_call_end_after_second = K + 2
```

The canonical first nonterminal collect implies `K == 1`, but the oracle does not hard-code that absolute value. It captures `K` from the recorder so earlier bounded instrumentation cannot silently shift global indices.

## 6. Designated timeout invocation rule

`identify_pd2_s6_timeout_critic_call_v1(...)` accepts only bounded cursor/count evidence. It requires:

```text
one current critic call per second collect
one I5a_critic_buffer_insert event in the second-collect event slice
event_batch.critic_batch_calls == 1
end - start == current_count + timeout_count == 2
```

Only then is the timeout invocation designated as relative index `1`, global index `K + 1`. The helper does not import Torch or inspect input tensors, shapes, dtypes, devices, digests, or values.

## 7. Invocation cursor/index implementation

The test-only harness captures both critic and route-event cursors before the second collect and their ends after it. `CriticRecorder` retains bounded `global_call_index`, runtime class, shape, stride, dtype, device, and digest metadata per call, plus a private ephemeral input clone.

`PD2S6TimeoutCriticInvocationIdentityV1` durably records the second-collect range, total call count, current and timeout relative/global indices, event count, expected/observed timeout counts, source-order contract, and verdict. It contains no tensor or runtime object.

## 8. Exact timeout call count

Timeout count is proven independently from input equality using the timeout evaluation batch's frozen `critic_batch_calls` field. The identity helper requires exactly one timeout call and exactly two total calls in the second-collect slice.

`matching_input_count` is not used and no longer exists in the S6 role-selection path.

## 9. Exact input oracle after identity

After identity PASS, S6 retrieves only:

```text
critic.observed_input(timeout_invocation_identity.timeout_call_global_index)
```

It compares that actual invocation argument with the authoritative pre-reset sidecar stack. Exact shape, dtype, device, numel, and `torch.equal` values remain mandatory. Correlation cannot run without a resolved exact-once identity DTO.

## 10. Bounded digest retention

The combined correlation DTO records the invocation range/index/count fields plus independent expected and observed SHA-256 values using `PD2_TORCH_CPU_CONTIGUOUS_RAW_BYTES_SHA256_V1`. Digest equality remains supporting integrity evidence only and cannot designate a role or rescue an exact mismatch.

No full tensor, whole critic, receipt, environment, or event batch is durably persisted.

## 11. No earlier-call rescue rule

The S6 implementation makes one `observed_input(...)` lookup using only the designated global timeout index. It does not iterate through calls, construct equality candidates, choose first/last matches, or fall back after a mismatch.

Thus a matching current call cannot rescue a mismatching timeout call, while duplicate current/timeout values do not create ambiguity.

## 12. CriticRecorder metadata changes

The test-only recorder adds bounded `global_call_index` and `critic_runtime_class` to every invocation record. It continues to retain a private ephemeral clone of the actual `obs` argument for later exact comparison.

The recorder does not mutate `obs`, RNN state, masks, call order, wrapped critic semantics, or return values.

## 13. No critic-forward changes

The recorder still has one wrapped `get_values` call site. Cursor capture, role identification, metadata construction, input retrieval, exact comparison, and hashing invoke no critic.

Pure case AF records the source-contract two calls—one current and one timeout—then proves comparison adds `0` calls. Timeout forward count remains exactly `1`.

## 14. STOP mapping

Invocation cursor/count/event failures stop after durable S5 PASS as:

```text
classification: PD2-STOP-TERMINAL-TRANSPORT-FAIL
boundary:       S6_TIMEOUT_CRITIC_CALL_IDENTITY
```

After identity PASS, designated-input metadata/value/digest failures retain:

```text
classification: PD2-STOP-TERMINAL-TRANSPORT-FAIL
boundary:       S6_TIMEOUT_CRITIC
```

S2 fingerprint mapping remains frozen and separate. An S6 failure never rolls back the already persisted S5 verdict.

## 15. Static guards

The static contract now proves:

- identity DTO and correlation DTO have exact bounded fields;
- identity helper contains no tensor/value/digest selection;
- cursor and fixed relative role are required;
- timeout count has an independent exact-one predicate;
- frozen I6 current call precedes collector timeout evaluation;
- frozen evaluator contains one timeout forward and records `calls = 1`;
- invocation identity occurs before exact correlation in S6;
- value-based scan/match-list/index selection is absent;
- only the designated invocation is retrieved, with no fallback;
- `torch.equal`, no-approximation, bounded digest, and no-extra-forward guards remain;
- R5-D-TR historical report is now protected with prior authoritative reports.

Static contract review: `PASS`.

## 16. A-AF regression results

The complete prior matrix remains `32/32 PASS`. A-Y remain `25/25 PASS`; Z-AF remain `7/7 PASS`. Timing, S5 authority/order, post-return separation, S2 fingerprint, exact-input mismatch/dtype/shape/no-mutation, digest-rescue prevention, and no-extra-forward semantics remain intact.

## 17. AG/AH results

- AG: current `X`, designated timeout `X`, expected `X` — identity selects relative index 1, timeout count is one, exact comparison passes despite duplicate values: `PASS`.
- AH: current `X`, designated timeout `Y`, expected `X` — identity selects `Y`; exact comparison fails at `S6_TIMEOUT_CRITIC`; earlier `X` cannot rescue: `PASS`.

## 18. AI-AL results

- AI: designated timeout invocation missing — identity fails before comparison: `PASS`.
- AJ: unexpected extra second-collect critic call — total-count/order contract fails closed: `PASS`.
- AK: current and timeout calls share values and digest — role remains relative index 1: `PASS`.
- AL: non-timeout input is arbitrary and designated timeout exactly matches expected — `PASS`.

Combined pure matrix: `38/38 PASS`.

## 19. No-runtime counters

```text
formal supervisor / worker:        0 / 0
AppLauncher / SimulationApp:       0 / 0
Isaac / CUDA initialization:       0 / 0
HARL real / VCritic real / actor:  0 / 0 / 0
environment construct/reset/step:  0 / 0 / 0
physical step:                     0
optimizer / backward / training:   0 / 0 / 0
playback / evaluation:             0 / 0
torch.cuda.is_initialized before:  false
torch.cuda.is_initialized after:   false
```

Only exact-interpreter compilation and pure CPU/static paths ran.

## 20. Protected integrity

The protected source/report set, excluding the explicitly authorized harness mutation, is `53/53 EXACT`. It includes production, DirectMARLEnv, scan environment, wrapper, I0-I6, runtime facade, installed HARL actor/critic/buffers/runner/ValueNorm, official Kit, and PD1/R2/R3/R4/R5-A/R5-B/R5-C/R5-D/R5-D-TR reports.

R5-C, R5-D, and R5-D-TR reports are unchanged.

## 21. Harness pre/post SHA

```text
pre-TR2 harness SHA-256:
436ae4ea5db6264ed644eeb43defd12790d0e0af24078de3f2eea01eb2a35401

post-TR2 harness SHA-256:
96c220b895b5410d1aca37bfde4f97f09c5e79da785a2b8377642a4c3de9c6d5
```

## 22. git diff --check

`git diff --check`: `PASS / EXIT 0`. Only existing PowerShell LF-to-CRLF working-copy warnings were printed; there were no whitespace errors.

Verification matrix:

```text
py_compile:    PASS / EXIT 0
--static-only: PASS / EXIT 0
--r5d-only:    PASS / EXIT 0
A-AF:          32/32 PASS
AG-AH:         2/2 PASS
AI-AL:         4/4 PASS
total:         38/38 PASS
```

## 23. Final classification

```text
classification:
  PHASE-B2-V2-PD2-R5D-TR2-TIMEOUT-CALL-IDENTITY-PASS-AWAITING-GPT-REVIEW

R5D-S6-EXACTINPUT-01:
  CLOSED

R5D-S6-CALLIDENTITY-02:
  CLOSED

timeout critic role:
  IDENTITY-BASED / FROZEN CANDIDATE

timeout call count:
  EXACTLY ONE / FROZEN CANDIDATE

timeout input:
  EXACT torch.equal / FROZEN

digest:
  BOUNDED SUPPORTING EVIDENCE / FROZEN

B2-V2:
  STOPPED / INCOMPLETE

R5-E / B2-R:
  NOT AUTHORIZED / NOT AUTHORIZED

runtime/policy/learner readiness:
  BLOCKED

public route:
  DORMANT / BLOCKED

training:
  NOT AUTHORIZED / NOT RUN

commit:
  NONE
```

R5-D-TR2 PASS means only that the test-only formal harness can distinguish which invocation is the timeout call from whether that call's input equals the expected timeout observation. It does not establish real timeout-call identity, real S5/S6, terminal transport, Snapshot B, or B2-V2 PASS.

## 24. Recommended next step

Stop and wait for GPT independent implementation review. Only after GPT review PASS and separate explicit user authorization may B2-V2-PD2-R5-E be considered as one controlled formal reentry with one worker, one AppLauncher lifetime, and no retry.

Do not run R5-E, B2-R, AppLauncher/Isaac/HARL runtime, training, playback, evaluation, or commit under this authorization.
