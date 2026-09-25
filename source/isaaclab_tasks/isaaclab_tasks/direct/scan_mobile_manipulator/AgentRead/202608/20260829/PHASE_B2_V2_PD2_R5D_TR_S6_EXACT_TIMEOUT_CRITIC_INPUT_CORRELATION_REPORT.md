# Phase B2-V2-PD2-R5-D-TR — S6 Exact Timeout-Critic Input Correlation Report

Date: 2026-08-29

Classification: `PHASE-B2-V2-PD2-R5D-TR-S6-EXACT-TIMEOUT-CRITIC-CORRELATION-PASS-AWAITING-GPT-REVIEW`

## 1. Starting authority

The committed checkpoint remains `14993dee344bade0230d2eb97b5f22171331f44a`. B2-D and B2-I0 through B2-I6 remain reviewed/frozen or closed; B2-V1 remains closed; B2-V2 remains `STOPPED / INCOMPLETE`. The authoritative R5-C design and reviewed R5-D implementation were read before this targeted revision.

This slice was authorized only to correct the test-only S6 timeout-critic input oracle. It did not authorize formal PD2 runtime, R5-E, B2-R, production repair, or training.

## 2. GPT R5-D targeted review issue

GPT accepted the R5-D timing fixture, S5 preterminal authority/DTO, post-return separation, S5-before-S6 ordering, S2 first-input fingerprint, and A-Y matrix. It found one targeted defect: S6 correlated the TIME_LIMIT critic call to the authoritative pre-reset input by SHA-256 equality alone.

Digest equality is bounded supporting evidence, but it is not the frozen exact input oracle.

## 3. R5D-S6-EXACTINPUT-01

`R5D-S6-EXACTINPUT-01` is `CLOSED` at the static/pure test-only implementation level.

The harness now requires ephemeral, in-process exact equality between the expected authoritative timeout critic tensor and the actual tensor passed into the recorded VCritic seam. It also retains separate expected and observed bounded SHA-256 evidence.

This closure is not real S6 runtime evidence.

## 4. What remained frozen

The following were not changed: R5-C; the timeout fixture; S5 DTO, authority, and adjudicator; S5/S6 order; post-return diagnostic separation; S2 fingerprint algorithm and capture ordering; R5-B historical STOP; I0-I6; lifecycle/P2/Ak authority; DirectMARLEnv; environment, wrapper, runtime facade, production training/entrypoints; installed HARL; official Kit; junction/cache state.

## 5. Files modified

- `scripts/environments/test_assignment_phase_b2_v2_pd2_production_startup_path_real_interface_smoke.py` — authorized test-only change.
- `AgentRead/202608/20260829/PHASE_B2_V2_PD2_R5D_TR_S6_EXACT_TIMEOUT_CRITIC_INPUT_CORRELATION_REPORT.md` — this report.
- `AgentRead/TASK_PROGRESS.md` — status handoff only.

Production changes: `NONE`. Installed HARL changes: `NONE`.

## 6. Previous digest-only implementation

The previous S6 path derived `pre_fp` from the stacked authoritative terminal sidecars and selected a critic call using only `call["obs_sha256"] == pre_fp`. It retained useful bounded evidence, but no longer proved that the actual input tensor was exactly equal in shape, dtype, and values.

No upstream semantic defect was implied by this test-oracle gap.

## 7. Restored exact S6 oracle

The new frozen/slotted `PD2S6TimeoutCriticInputCorrelationV1` contains only bounded metadata, digests, and equality results. `compare_pd2_s6_timeout_critic_input_exact_v1(...)` performs the ephemeral exact comparison; `adjudicate_pd2_s6_timeout_critic_input_correlation_v1(...)` fails closed unless every exact predicate passes.

The runtime S6 adjudication constructs a bounded correlation DTO for each successfully recorded critic call, requires exactly one exact match, and adjudicates that match before buffer/return claims.

## 8. Expected timeout input authority

The expected tensor remains:

```text
terminal_historical_payload
-> each environment-owned optional_sidecar.bootstrap_critic_obs
-> torch.stack(..., dim=0)
-> pre_obs
```

It is the authoritative pre-reset timeout bootstrap critic input. It is not reconstructed from post-autoreset current state.

## 9. Observed timeout input authority

`CriticRecorder.get_values(obs, rnn, masks)` now captures `obs.detach().clone()` into a private ephemeral list immediately before the sole wrapped `self.wrapped.get_values(...)` invocation. The comparison reads that private captured argument by index.

The observed authority is therefore the actual argument at the VCritic call seam, not a later reconstruction and not the stored digest.

## 10. Exact equality implementation

The exact oracle requires:

- exact shape;
- exact dtype;
- exact device;
- exact `numel`;
- `torch.equal(expected_cpu, observed_cpu)` after read-only, dtype-preserving CPU copies.

There is no `allclose`, tolerance, epsilon, rounding, normalization, or dtype conversion used to establish equality. Dtype and shape must match even where a value-only library comparison could otherwise appear equal.

## 11. Bounded digest retention

Expected and observed SHA-256 values are independently calculated from dtype-preserving, contiguous CPU raw bytes with `PD2_TORCH_CPU_CONTIGUOUS_RAW_BYTES_SHA256_V1`. The bounded DTO also records shape, dtype, device, numel, and byte count.

The adjudicator requires exact tensor equality independently; a stale or injected equal digest cannot rescue an exact mismatch. Digest equality is supporting integrity evidence only.

## 12. No-full-tensor durable persistence

Full expected and observed tensors exist only ephemerally in the worker/test process. The private observed-input list is never inserted into `evidence`, checkpoints, JSON, reports, or a buffer. Durable S6 evidence contains only the bounded DTO fields and verdict.

No environment object or full environment state is persisted.

## 13. Exact-once timeout critic preservation

The recorder still contains exactly one wrapped `get_values` call site. Capturing the argument and comparing it do not invoke the critic. S6 compares already-recorded inputs and requires exactly one matching call.

Pure case AF proves: fake critic calls `1`, wrapped-forward attempts `1`, exact comparisons `1`, second critic calls `0`.

## 14. STOP mapping

Missing/non-tensor comparison inputs, comparison failures, malformed correlation DTOs, exact metadata/value mismatches, non-unique matches, or bounded fingerprint inconsistency fail as:

```text
classification: PD2-STOP-TERMINAL-TRANSPORT-FAIL
boundary:       S6_TIMEOUT_CRITIC
```

The S2 first-current-input fingerprint retains its separate `PD2-STOP-VCritic-CUDA-FAIL / S2_CRITIC_INPUT_EVIDENCE` mapping.

## 15. Static guards

`r5d_static_contract_review()` now verifies:

- exact bounded DTO field set;
- explicit `torch.equal` authority;
- absence of approximate-comparison tokens;
- expected/observed digest retention;
- exact-value predicate cannot be bypassed by digest equality;
- actual argument capture precedes the one wrapped forward call;
- expected input comes from terminal sidecars;
- no full observed tensor enters durable evidence;
- no additional critic call site;
- R5-D historical report hash is protected alongside R5-C and earlier reports.

Static contract review: `PASS`.

## 16. Existing A-Y regression results

The original R5-D pure/static cases A-Y remain unchanged in meaning and pass `25/25`. This preserves timing, S5 authority/ordering, post-return separation, S2 fingerprint behavior, forced-row/proposal/P2-Ak checks, and mutation guards.

## 17. Z/AA targeted cases

- Z: exact cloned tensor — `PASS`; exact value and bounded digest both match.
- AA: one value changed — `PASS` by failing closed at `S6_TIMEOUT_CRITIC`; exact value and digest do not match.

## 18. AB-AF targeted cases

- AB: injected stale equal digests with an exact mismatch cannot rescue adjudication — `PASS`.
- AC: dtype mismatch fails closed — `PASS`.
- AD: shape mismatch fails closed — `PASS`.
- AE: comparison/fingerprinting preserves values, dtype, shape, `requires_grad`, and tensor version — `PASS`.
- AF: exact-once fake critic and one comparison, with no second forward — `PASS`.

Combined pure matrix: `32/32 PASS`.

## 19. No-runtime counters

```text
formal supervisor:                 0
worker:                            0
AppLauncher:                       0
SimulationApp:                     0
Isaac:                             0
CUDA initialization before/after: 0 / 0
HARL real:                         0
VCritic real:                      0
actor real:                        0
environment construct/reset/step: 0 / 0 / 0
physical step:                     0
optimizer/backward/training:       0 / 0 / 0
playback/evaluation:               0 / 0
```

Only `py_compile`, `--static-only`, and `--r5d-only` pure CPU checks ran.

## 20. Protected integrity

The protected source/report set, excluding the explicitly authorized harness mutation, is `52/52 EXACT`. It includes production, DirectMARLEnv, scan environment, wrapper, I0-I6, runtime facade, installed HARL actor/critic/buffers/runner/ValueNorm, official Kit, and PD1/R2/R3/R4/R5-A/R5-B/R5-C/R5-D reports.

No protected mismatch was observed.

## 21. Harness pre/post SHA

```text
pre-TR harness SHA-256:
38e903064285cf6dd21ae3ef8418936e766c609d0c2f072d2d0f51cbfcff9115

post-TR harness SHA-256:
436ae4ea5db6264ed644eeb43defd12790d0e0af24078de3f2eea01eb2a35401
```

## 22. git diff --check

`git diff --check`: `PASS / EXIT 0`. PowerShell reported only existing LF-to-CRLF working-copy warnings; there were no whitespace errors.

Verification matrix:

```text
py_compile:    PASS / EXIT 0
--static-only: PASS / EXIT 0
--r5d-only:    PASS / EXIT 0
A-Y:           25/25 PASS
Z-AA:          2/2 PASS
AB-AF:         5/5 PASS
total:         32/32 PASS
```

## 23. Final classification

```text
classification:
  PHASE-B2-V2-PD2-R5D-TR-S6-EXACT-TIMEOUT-CRITIC-CORRELATION-PASS-AWAITING-GPT-REVIEW

R5D-S6-EXACTINPUT-01:
  CLOSED

B2-V2:
  STOPPED / INCOMPLETE

R5-E:
  NOT AUTHORIZED

B2-R:
  NOT AUTHORIZED

runtime/policy/learner readiness:
  BLOCKED

public route:
  DORMANT / BLOCKED

training:
  NOT AUTHORIZED / NOT RUN

commit:
  NONE
```

R5-D-TR PASS means only that the test-only formal harness again expresses the frozen exact S6 input-correlation semantics while retaining bounded evidence. It does not establish real S5/S6, terminal transport, Snapshot B, or B2-V2 PASS.

## 24. Recommended next step

Stop and wait for GPT independent implementation review. Only after GPT review PASS and separate explicit user authorization may B2-V2-PD2-R5-E be considered as one controlled formal reentry with one worker, one AppLauncher lifetime, and no retry.

Do not run R5-E, B2-R, Isaac/HARL runtime, training, playback, evaluation, or commit under this authorization.
