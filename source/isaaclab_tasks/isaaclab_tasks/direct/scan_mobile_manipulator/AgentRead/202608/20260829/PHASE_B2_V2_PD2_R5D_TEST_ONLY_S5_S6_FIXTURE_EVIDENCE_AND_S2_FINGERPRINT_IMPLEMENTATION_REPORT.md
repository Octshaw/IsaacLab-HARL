# Phase B2-V2-PD2-R5-D Test-Only S5/S6 Fixture Evidence and S2 Fingerprint Implementation Report

Date: 2026-08-29 (Asia/Shanghai)

Classification: `PHASE-B2-V2-PD2-R5D-TEST-ONLY-S5S6-EVIDENCE-AND-S2-FINGERPRINT-IMPLEMENTATION-PASS-AWAITING-GPT-REVIEW`

## 1. Starting authority

Starting committed HEAD:

```text
14993dee344bade0230d2eb97b5f22171331f44a
```

Authoritative inputs were:

- `AgentRead/TASK_PROGRESS.md`;
- frozen R5-C design `AgentRead/202608/20260828/PHASE_B2_V2_PD2_R5C_S5_S6_TIMING_FIXTURE_AND_EVIDENCE_ORDERING_CONTRACT_DESIGN.md`;
- historical R5-B formal report and the frozen R5-A/R4/R3/R2/PD1 chain;
- the existing test-only PD2 harness.

The report is under `AgentRead/202608/20260829/` because `AgentRead/AGENTS.md` requires every newly created report to use the current local date. Existing 20260828 authoritative artifacts were not relocated or modified.

## 2. R5-C GPT review closure

R5-C is `GPT REVIEW PASS / FROZEN`. Its SHA-256 remained:

```text
ce4f4d8399cf465e981dd4fb67f37ba81ed991271530df802d09be8448a1ceac
```

R5-D implements the frozen contract. It does not revise the timing authority, PRETERMINAL/POST-RETURN separation, S5/S6 adjudication order, S2 algorithm, or formal STOP taxonomy.

## 3. Authorized implementation scope

The sole code mutation was the existing test-only formal harness:

```text
scripts/environments/
test_assignment_phase_b2_v2_pd2_production_startup_path_real_interface_smoke.py
```

Documentation mutations are this report and `AgentRead/TASK_PROGRESS.md`.

Production source, DirectMARLEnv, I0-I6, wrapper/training, installed HARL, official Kit, Junction/cache/package state, and public route were not modified. No optional helper was added.

## 4. Files modified or added

```text
MODIFIED  scripts/environments/test_assignment_phase_b2_v2_pd2_production_startup_path_real_interface_smoke.py
MODIFIED  source/.../AgentRead/TASK_PROGRESS.md
ADDED     source/.../AgentRead/202608/20260829/PHASE_B2_V2_PD2_R5D_TEST_ONLY_S5_S6_FIXTURE_EVIDENCE_AND_S2_FINGERPRINT_IMPLEMENTATION_REPORT.md
```

The repository was already intentionally dirty with reviewed B2 artifacts. Those unrelated changes were preserved.

## 5. Timing fixture implementation

The harness now derives one immutable `PD2TimeoutFixtureV1` from:

```text
desired terminal transition: 2
required max episode length:  3
strict ratio bucket:          2 < raw_ratio < 3
fixture ratio:                2.5
control_step:                 float(cfg.sim.dt) * int(cfg.decimation)
episode_length_s:             control_step * 2.5
```

The DTO records the control step, duration, raw ratio, ceil, and both strict-bucket margins. No epsilon, `nextafter`, hard-coded duration, third physical transition, or DirectMARLEnv change is used.

The retained historical comparison verifies that multiplier `3` produces duration `0.30000000000000004`, raw ratio `3.0000000000000004`, and `ceil == 4` for the audited production-like arithmetic.

## 6. Early timing gate implementation

Before reset, model forward, or physical stepping, the harness now requires:

```text
control_step > 0 and finite
2 < raw_ratio < 3
ceil(raw_ratio) == 3
raw.max_episode_length == 3
```

Failure preserves:

```text
classification: PD2-STOP-PHYSICAL-STEP-FAIL
boundary:       S1_TIMING_FIXTURE_CONTRACT
```

The timing checkpoint is durably emitted immediately after environment construction and before wrapper reset or HARL component construction. R5-D did not execute this runtime path.

## 7. S5 DTO implementation

The harness-local frozen/slotted `PD2S5PreterminalEvidenceV1` implements exactly the 24 R5-C fields:

- transition identity and canonical source/admitted P2 serial/store versions;
- episode/transition generations and OPEN-window serial;
- bounded `[E,M]` admitted effective, expected-controller, and actual controller-time assignments;
- continuation, policy, forced, forced-noop, and claim-mutated row masks;
- continuation expected tasks;
- original proposal IDs, logprob finite mask, and proposal-present mask;
- immutable actor call records and resolution interpretations.

Tensor evidence is normalized into bounded immutable tuples. The DTO contains no whole environment, Store, resolver, lifecycle object, live P2 pointer, or tensor alias.

Static guards prove that it contains no `post_return_*`, `post_autoreset_*`, `terminal_*`, `next_episode_*`, `current_p2`, `current_assignment`, or `current_generation` field.

## 8. S5 authority-chain implementation

The builder binds only the retained transition-2 receipt and the controller-time recorder:

```text
decision bundle / evidence identity
-> exact source P2 + OPEN window + generations
-> resolution
-> zero-or-one claim artifact
-> final post-claim admitted P2
-> admitted effective Ak assignment
-> controller-time assignment copy
```

It verifies exact object identity for the bundle/envelope/source publication chain, canonical serials for durable evidence, and full assignment equality:

```text
reprojection(admitted P2)
== admitted_effective_assignment
== controller_assignments[1]
```

No proposal value is promoted to effective/controller authority. P2 remains sole lifecycle/ownership authority and physical authority remains final P2 -> Ak -> controller.

## 9. Continuation, claim, and forced-row implementation

Continuation is derived only from `second.decision_bundle.forced_continuation_mask`. For each continuation row, the builder/adjudicator requires:

```text
forced action == precontrol current owned task
             == admitted effective assignment
             == controller-time assignment
```

Claim-mutated rows are derived only from the immutable claim artifact's selected environments and `requested_task_by_robot >= 0`; a zero-artifact result yields the all-false mask. Claim mutation and continuation must not overlap.

Actor call records must equal the compact policy-decision row indices per robot. Forced rows may not be sampled, may not carry a genuine proposal, and preserve the frozen invalid-action/logprob sentinels. Genuine policy rows retain finite original behavior logprobs and in-range original proposal IDs. Continuation interpretations must be `CONTINUE_EXISTING`.

## 10. S5/S6 adjudication order implementation

The external harness order is now:

```text
second collect_step returns
-> build immutable PRETERMINAL S5 DTO
-> adjudicate S5
-> persist continuation_second_step_pass
-> optionally capture POST-RETURN diagnostic
-> assert S6 done/reason
-> inspect terminal sidecar/ACK/current separation/I5a/I5b
```

Static AST evidence records exactly two `collect_step()` calls and places the S5 checkpoint before both `S6_TIME_LIMIT` assertions. If S5 fails, the pure flow leaves S6 `NOT ADJUDICATED`. If S5 passes and S6 fails, the persisted S5 verdict remains unchanged.

This is external evidence ordering only. Frozen I6 internal atomic terminal transport was not changed.

## 11. Post-return diagnostic implementation

The separate frozen/slotted optional `PD2PostReturnStateDiagnosticV1` has only the frozen fields:

- `post_return_current_*` publication/store/generation evidence;
- `post_return_next_bundle_*` identity/generation evidence;
- immutable `terminal_status_proven=False` and `autoreset_status_proven=False` capture-time flags.

It is built only after S5 PASS. Capture failure is recorded but cannot fail or rewrite S5. Only later successful S6 evidence may interpret the unchanged DTO as post-autoreset state; the DTO itself is never renamed or mutated.

## 12. S5 independence implementation

`build_pd2_s5_preterminal_evidence_v1()` has static guards forbidding access to `current_publication`, `next_decision_bundle`, terminal history, live domain reads, wrapper current P2, and POST-RETURN/POST-AUTORESET names.

Pure cases prove S5 PASS with absent post-return diagnostics, later changed/cleared state, and a later S6 failure. A post-return state matching a bad controller value cannot rescue a PRETERMINAL P2/Ak/controller mismatch.

## 13. S2 fingerprint implementation

The actual first `CriticRecorder.get_values()` input is captured before the wrapped VCritic call using:

```text
PD2_TORCH_CPU_CONTIGUOUS_RAW_BYTES_SHA256_V1
```

The helper:

1. reads shape, stride, dtype, device, contiguity, finiteness, requires-grad, numel, RNN shape, and mask shape;
2. detaches without modifying the source;
3. performs the diagnostic CPU copy while preserving dtype;
4. makes the CPU view C-contiguous;
5. hashes `numpy().tobytes(order="C")` with SHA-256;
6. records byte count, CPU byte order, capture index, and runtime class `module.qualname`;
7. persists `first_real_vcritic_input_captured` before invoking the installed critic.

Only bounded metadata and the digest enter S2 evidence; the full critic input is not persisted. Existing S6 exact-input matching now uses a bounded raw-byte digest rather than retaining the full input tensor.

## 14. Single-VCritic-call guard

`CriticRecorder` has one syntactic `self.wrapped.get_values(...)` call site. The first-input fingerprint and observer execute before that call. A dedicated `wrapped_forward_attempts` counter distinguishes evidence-capture failure from a VCritic forward attempt.

Pure case M uses a recorder-only CPU fake and proves:

```text
fingerprint observer calls: 1
wrapped critic calls:       1
recorder forward attempts:  1
```

No dummy critic replaces the installed VCritic in the formal path.

## 15. STOP mapping preservation

The formal taxonomy remains exactly ten classes. R5-D adds no formal STOP class.

```text
timing fixture failure                    -> PD2-STOP-PHYSICAL-STEP-FAIL / S1_TIMING_FIXTURE_CONTRACT
required PRETERMINAL evidence unavailable -> PD2-STOP-PHYSICAL-STEP-FAIL / S5_PRETERMINAL_EVIDENCE_UNAVAILABLE
P2/Ak/controller or continuation failure  -> PD2-STOP-PHYSICAL-STEP-FAIL / precise S5_*
forced row sampled                        -> PD2-STOP-ACTOR-FORWARD-FAIL / S5_FORCED_ROW_BYPASS
S6 done/reason failure after S5 PASS       -> PD2-STOP-TERMINAL-TRANSPORT-FAIL / S6_TIME_LIMIT
S2 capture/persistence failure             -> PD2-STOP-VCritic-CUDA-FAIL / S2_CRITIC_INPUT_EVIDENCE
```

## 16. Static guard results

Command:

```text
C:\isaacenvs\isaac45_harl\python.exe
  scripts/environments/test_assignment_phase_b2_v2_pd2_production_startup_path_real_interface_smoke.py
  --static-only
```

Result: `PD2_STATIC_PREFLIGHT_PASS`, exit `0`.

R5-D static guards all passed:

```text
exact two collect_step calls                         PASS
S5 checkpoint before S6 assertions                  PASS
S5 DTO exact fields / forbidden fields absent       PASS
S5 builder no POST-RETURN dependency                 PASS
POST-RETURN DTO exact and temporally qualified       PASS
no timing boundary hack                              PASS
fingerprint before sole wrapped VCritic call         PASS
formal STOP taxonomy exact ten                       PASS
R5-C and official Kit frozen hashes protected        PASS
```

`py_compile` also passed with the exact required interpreter.

## 17. Synthetic matrix A-U

`--r5d-only` ran pure/static and CPU Torch helpers only. Cases A-U all passed:

| Case | Evidence | Result |
|---|---|---|
| A | midpoint ratio strict interior, ceil 3 | PASS |
| B | transition 1 nonterminal, transition 2 TIME_LIMIT timeline | PASS |
| C | historical multiplier-3 ratio exceeds 3, ceil 4 | PASS |
| D | actual max-length mismatch stops at early timing boundary | PASS |
| E | S5 adjudication/checkpoint precedes S6 | PASS |
| F | S5 continuation failure leaves S6 not adjudicated | PASS |
| G | S5 PASS plus done/reason failure stops at S6_TIME_LIMIT | PASS |
| H | S5 plus terminal predicate enters terminal evidence | PASS |
| I | identical tensor gives identical digest | PASS |
| J | one-value change changes digest | PASS |
| K | source tensor shape/stride/dtype/value unchanged | PASS |
| L | runtime-class evidence deterministic | PASS |
| M | one recorder invocation equals one wrapped call | PASS |
| N | later changed state cannot alter valid PRETERMINAL S5 | PASS |
| O | controller mismatch cannot be rescued by later state | PASS |
| P | later timeout clearing cannot alter continuation proof | PASS |
| Q | S5 builder has no POST-RETURN dependency | PASS |
| R | exact S5 passes without optional diagnostic | PASS |
| S | pre-S6 diagnostic names remain `post_return_*` | PASS |
| T | S6 failure does not mutate/rollback S5 PASS | PASS |
| U | S5/S6 PASS preserves historical/current separation | PASS |

## 18. Additional negative cases V-Y

| Case | Evidence | Result |
|---|---|---|
| V | continuation and claim-mutated overlap | expected S5 failure PASS |
| W | continuation row inserted into actor valid indices | expected STOP_ACTOR/S5_FORCED_ROW_BYPASS PASS |
| X | proposal substituted as controller without admitted-P2 authority | expected S5_P2_AK failure PASS |
| Y | forbidden POST-RETURN/terminal field in S5 schema | static rejection PASS |

All 25 A-Y cases passed.

## 19. No-runtime counters

```text
formal supervisor / worker:     0 / 0
AppLauncher / SimulationApp:    0 / 0
Isaac / CUDA initialization:    0 / 0
HARL / VCritic / actor:         0 / 0 / 0
environment construct/reset:    0 / 0
physical environment step:      0
optimizer / backward:           0 / 0
training/playback/evaluation:   0 / 0 / 0
checkpoint load/save:           0 / 0
public route activation:        0
```

CPU Torch was used only for the authorized bounded fingerprint and S5 synthetic cases. `torch.cuda.is_initialized()` was false before and after.

## 20. Protected integrity

The frozen hash set covers DirectMARLEnv, scan environment, wrapper/training, lifecycle/runtime facade and I0-I6 modules, proposal adapter, official Kit, installed HARL actor/critic/buffers/runner/ValueNorm, prior diagnostics, and authoritative PD1/R2/R3/R4/R5-A/R5-B/R5-C reports.

Post-implementation static preflight reported `51/51` exact frozen source/report hashes, including PD1, R2, R3, R4, R5-A, R5-B, and R5-C. The authorized harness is intentionally outside its own immutable source map. R5-C and official Kit remained exact at:

```text
R5-C:        ce4f4d8399cf465e981dd4fb67f37ba81ed991271530df802d09be8448a1ceac
official Kit:475bb23c5941fbaaf0186991bf6e5445a267b1e0fd8bbab333cc78dc2e1bc795
```

No protected source was in the R5-D mutation set, and no protected hash changed.

## 21. Git and syntax integrity

```text
starting HEAD:    14993dee344bade0230d2eb97b5f22171331f44a
commit:           NONE
py_compile:       PASS / EXIT 0
--static-only:    PASS / EXIT 0
--r5d-only:       PASS / EXIT 0
git diff --check: PASS / EXIT 0
```

The final test-only harness SHA-256 is `38e903064285cf6dd21ae3ef8418936e766c609d0c2f072d2d0f51cbfcff9115`; it is test evidence, not a production identity.

## 22. Final classification

```text
classification:
  PHASE-B2-V2-PD2-R5D-TEST-ONLY-S5S6-EVIDENCE-AND-S2-FINGERPRINT-IMPLEMENTATION-PASS-AWAITING-GPT-REVIEW

R5-D implementation:          COMPLETE
R5-D static/synthetic:        PASS
B2-V2:                        STOPPED / INCOMPLETE
historical R5-B STOP:         RETAINED
formal PD2 runtime:           NOT RUN
R5-E:                         NOT AUTHORIZED
runtime/policy/learner ready: BLOCKED
public route:                 DORMANT / BLOCKED
B2-R:                         NOT AUTHORIZED
training:                     NOT AUTHORIZED / NOT RUN
production changes:           NONE
installed HARL changes:       NONE
commit:                       NONE
```

This result is not B2-V2 PASS, does not retroactively adjudicate R5-B S5, and supplies no real S5/S6/TIME_LIMIT evidence.

## 23. Recommended next step

Stop and obtain GPT independent review of R5-D. Do not run formal PD2 or R5-E, do not start AppLauncher/Isaac/CUDA/HARL, do not activate the public route, do not enter B2-R, do not train, and do not commit without separate authorization.
