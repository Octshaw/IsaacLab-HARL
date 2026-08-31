# Phase B2-V2-PD2-R5-F — Integral-Horizon Timing Fixture and S1 Boundary Attribution Reconciliation Design

Date: 2026-08-29

Classification: `PHASE-B2-V2-PD2-R5F-INTEGRAL-HORIZON-AND-S1-BOUNDARY-DESIGN-PASS-AWAITING-GPT-REVIEW`

Implementation: `NOT STARTED`

Formal runtime: `NOT RUN`

Isaac / HARL / CUDA: `NOT RUN`

Production changes: `NONE`

Harness changes: `NONE`

Commit: `NONE`

## 1. Starting authority

Committed starting checkpoint:

```text
HEAD: 14993dee344bade0230d2eb97b5f22171331f44a
```

Authoritative phase state entering this design slice:

```text
B2-D:                         REVIEW PASS / FROZEN
B2-I0 through B2-I6:          REVIEW PASS / CLOSED
B2-V1:                        GPT REVIEW PASS / CLOSED
B2-V2:                        STOPPED / INCOMPLETE
R5-B historical stop:         PD2-STOP-TERMINAL-TRANSPORT-FAIL / S6_TIME_LIMIT
R5-C:                         REVIEW PASS / FROZEN
R5-D:                         REVIEW PASS / CLOSED
R5-E:                         ONE FORMAL RUN COMPLETED / STOP REVIEW CONFIRMED
runtime/policy/learner ready: BLOCKED
public route:                 DORMANT / BLOCKED
B2-R:                         NOT AUTHORIZED
training:                     NOT AUTHORIZED
```

This slice reopens exactly two design questions:

1. the test-only integral-horizon timing fixture contract;
2. precise S1 boundary attribution around `gym.make(...)`.

All R5-D non-timing contracts remain frozen.

## 2. Scope and method

This was a design-only, source-audit-only, documentation-only slice. The audit read the reviewed reports, current harness, production scale-contract source, scan environment, and `DirectMARLEnv` timing/order source. One pure arithmetic check used only Python standard-library `math`, `json`, and `sys` under the exact project interpreter. It did not import Torch, Isaac, Gym, HARL, or the production package.

No AppLauncher, Isaac environment, CUDA operation, `gym.make`, reset, step, actor, critic, optimizer, backward, training, playback, or evaluation was run.

## 3. R5-E reviewed result

The single R5-E formal execution remains stopped. Its persisted primary artifact is authoritative and remains unchanged:

```text
classification: PD2-STOP-STARTUP-EQUIVALENCE-MISMATCH
first_boundary: S0R
```

The run durably completed S0 and S0R. The following S1 environment-construction call raised:

```text
AssignmentEventProfileSchemaV2ContractError
failure_code: nonintegral_episode_horizon
stage: scale_validation
expected: integral episode_time_limit / control_step
actual: 2.5
```

No repair or retry occurred.

## 4. Historical artifact versus independently located exception site

Two statements must coexist without rewriting history:

```text
Historical persisted artifact boundary:
  S0R

Independent traceback/source attribution:
  subsequent S1 gym.make environment-construction path
```

The artifact reported `S0R` because the worker's mutable `active_stage` was still `S0R` when the exception escaped. The harness did not durably enter S1 or record a finer operation boundary before `gym.make(...)`.

This is an attribution-precision gap, not evidence that S0R's extension-identity predicate failed.

## 5. Source files audited

- `scripts/environments/test_assignment_phase_b2_v2_pd2_production_startup_path_real_interface_smoke.py`
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_event_profile_schema_contract_v2.py`
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py`
- `source/isaaclab/isaaclab/envs/direct_marl_env.py`
- `AgentRead/20260829/PHASE_B2_V2_PD2_R5E_ONE_CONTROLLED_FORMAL_REENTRY_REPORT.md`
- `AgentRead/20260829/PHASE_B2_V2_PD2_R5D_TEST_ONLY_S5_S6_FIXTURE_EVIDENCE_AND_S2_FINGERPRINT_IMPLEMENTATION_REPORT.md`
- `AgentRead/20260829/PHASE_B2_V2_PD2_R5D_TR_S6_EXACT_TIMEOUT_CRITIC_INPUT_CORRELATION_REPORT.md`
- `AgentRead/20260829/PHASE_B2_V2_PD2_R5D_TR2_TIMEOUT_CRITIC_INVOCATION_IDENTITY_REPORT.md`
- `AgentRead/20260828/PHASE_B2_V2_PD2_R5C_S5_S6_TIMING_FIXTURE_AND_EVIDENCE_ORDERING_CONTRACT_DESIGN.md`
- `AgentRead/20260828/PHASE_B2_V2_PD2_R5B_CONTROLLED_FORMAL_REENTRY_REPORT.md`
- `AgentRead/20260827/PHASE_B2_V2_PD1_PRODUCTION_STARTUP_PATH_VALIDATION_DESIGN.md`
- `AgentRead/TASK_PROGRESS.md`

## 6. Frozen configuration and semantic objective

The reviewed real-interface configuration remains:

```text
sim.dt:                       1 / 60 seconds
decimation:                   6
physical control step:        0.1 seconds
desired terminal transition:  2
required max episode length:  3
```

The semantic objective is unchanged: the first physical transition is nonterminal and the second physical transition is a TIME_LIMIT transition. This slice does not shorten or lengthen the semantic horizon.

## 7. Production scale-contract audit

The production event-profile scale contract computes:

```python
control_step = sim_dt * decimation
horizon_ratio = time_limit / control_step
horizon = round(horizon_ratio)
```

It rejects the configuration unless:

```python
math.isclose(horizon_ratio, horizon, rel_tol=0.0, abs_tol=1.0e-9)
```

On success it publishes `episode_horizon_steps = horizon`.

Important facts:

- the production rounded horizon uses Python `round`;
- relative tolerance is exactly zero;
- absolute tolerance is exactly `1e-9`;
- the contract is invoked inside the event-profile scan-environment constructor;
- therefore an invalid timing fixture can raise before `gym.make(...)` returns.

No production tolerance or scale-contract behavior is reopened.

## 8. DirectMARLEnv horizon audit

`DirectMARLEnv` computes:

```python
step_dt = cfg.sim.dt * cfg.decimation
max_episode_length = math.ceil(cfg.episode_length_s / step_dt)
```

For the required max episode length of 3, the runtime ratio must satisfy:

```text
2 < episode_length_s / step_dt <= 3
```

The fixture must therefore satisfy both the production near-integral predicate and the `ceil == 3` predicate. Passing only one is insufficient.

## 9. Lifecycle TIME_LIMIT ordering audit

In `DirectMARLEnv.step()`, `episode_length_buf` increments before `_get_dones()`.

The event-profile lifecycle timeout path evaluates:

```python
episode_length_buf >= max_episode_length - 1
```

For `max_episode_length == 3`:

```text
transition 1: episode_length_buf == 1 -> 1 >= 2 -> False
transition 2: episode_length_buf == 2 -> 2 >= 2 -> True
```

Thus a constructed environment with authoritative `max_episode_length == 3` preserves the reviewed two-transition fixture semantics.

## 10. Three-contract intersection

The accepted fixture must simultaneously satisfy:

```text
Production scale contract:
  ratio is within 1e-9 of integer horizon 3

DirectMARLEnv horizon:
  2 < ratio <= 3
  ceil(ratio) == 3

Lifecycle transition timing:
  max_episode_length == 3
  transition 1 nonterminal
  transition 2 TIME_LIMIT
```

The ratio need not be bitwise-equal to binary floating-point `3.0`. It must satisfy the exact production tolerance and runtime ceil predicates.

## 11. Candidate A — strict midpoint

Reviewed R5-D fixture:

```python
episode_length_s = control_step * 2.5
```

Exact observed arithmetic:

```text
episode_length_s:      0.25
horizon ratio:         2.5
round(ratio):          2
integrality error:     0.5
production isclose:    False
ceil(ratio):           3
```

Python rounds the exact tie `2.5` to the even integer 2. Candidate A passes the ceil bucket but fails the frozen production integral-horizon contract. It is rejected.

## 12. Candidate B — control-step multiplication

Candidate:

```python
episode_length_s = control_step * 3
```

With the frozen configuration, binary operation ordering yields:

```text
episode_length_s:      0.30000000000000004
horizon ratio:         3.0000000000000004
round(ratio):          3
integrality error:     4.440892098500626e-16
production isclose:    True
ceil(ratio):           4
```

Candidate B passes the production integral-horizon contract but produces `max_episode_length == 4`. It violates the lifecycle timing objective and is rejected.

## 13. Candidate C — integer simulation-tick derivation

Accepted design candidate:

```python
semantic_horizon_steps = 3
simulation_tick_count = int(cfg.decimation) * semantic_horizon_steps
episode_length_s = float(cfg.sim.dt) * simulation_tick_count
```

Under the frozen configuration:

```text
simulation_tick_count: 18
episode_length_s:       0.3
horizon ratio:          2.9999999999999996
round(ratio):           3
integrality error:      4.440892098500626e-16
production isclose:     True
ceil(ratio):            3
```

Candidate C lies inside the three-contract intersection and is selected for a future separately authorized test-only harness implementation.

## 14. Exact arithmetic matrix

The following values were obtained from the exact project interpreter using only standard-library arithmetic:

```text
Python:      3.10.20
interpreter: C:\isaacenvs\isaac45_harl\python.exe
dt:          0.016666666666666666 (0x1.1111111111111p-6)
control step:0.1                  (0x1.999999999999ap-4)
```

| Candidate | Episode length | Ratio | `round` | `abs(ratio-round)` | Production | `ceil` | Result |
|---|---:|---:|---:|---:|---|---:|---|
| A: midpoint | 0.25 | 2.5 | 2 | 0.5 | FAIL | 3 | REJECT |
| B: `control_step * 3` | 0.30000000000000004 | 3.0000000000000004 | 3 | 4.440892098500626e-16 | PASS | 4 | REJECT |
| C: `dt * (decimation * 3)` | 0.3 | 2.9999999999999996 | 3 | 4.440892098500626e-16 | PASS | 3 | ACCEPT |

Candidate C margins:

```text
ratio - lower bound 2: 0.9999999999999996
upper bound 3 - ratio: 4.440892098500626e-16
production tolerance slack:
  1.0e-9 - 4.440892098500626e-16 > 0
```

## 15. Production-tolerance compatibility

For Candidate C:

```text
abs(2.9999999999999996 - 3) = 4.440892098500626e-16
4.440892098500626e-16 <= 1.0e-9
```

Therefore the production contract resolves the horizon to 3 without modifying its tolerance, rounding rule, or implementation.

## 16. Ceil compatibility

For Candidate C:

```text
2 < 2.9999999999999996 <= 3
ceil(2.9999999999999996) == 3
```

Therefore `DirectMARLEnv.max_episode_length` remains 3 without modifying `DirectMARLEnv`.

## 17. Lifecycle compatibility

Candidate C preserves the required lifecycle observations:

```text
first physical transition:  nonterminal
second physical transition: TIME_LIMIT
```

This follows from the audited increment-before-done order and the event-profile `>= max_episode_length - 1` predicate, not from a new lifecycle rule.

## 18. Semantic justification

Candidate C is not an epsilon workaround. It represents the same semantic three-control-step horizon as exactly 18 configured simulation ticks:

```text
6 simulation ticks / control step * 3 control steps = 18 simulation ticks
```

Only floating-point operation ordering changes. The design is derived from configuration values and the required semantic horizon; it does not hardcode `0.3` as a magic timeout.

This acceptance is intentionally bounded to the frozen `sim.dt`, decimation, and horizon configuration. A future preconstruction gate must reject any configuration that does not independently satisfy every predicate.

## 19. Rejected alternatives

The following are explicitly rejected:

- subtracting an arbitrary epsilon from `3 * control_step`;
- using `math.nextafter` to push the value below 3;
- hardcoding `0.3`, `0.299999`, or another decimal literal;
- changing the production `1e-9` tolerance;
- changing production `round` or `DirectMARLEnv.ceil` behavior;
- changing lifecycle TIME_LIMIT semantics;
- moving the expected terminal event to a third physical transition;
- changing production, HARL, I0-I6, or lifecycle code to accommodate the fixture.

`Decimal` or `Fraction` may explain arithmetic in design review but must not conceal the actual float passed to the existing environment configuration.

## 20. Gate A — preconstruction timing contract

A future separately authorized harness implementation must execute Gate A before `gym.make(...)`. Gate A is a fail-closed test-only mirror of the relevant production and runtime predicates.

Required evidence payload:

```text
desired_terminal_transition
required_max_episode_length
sim_dt_seconds
control_decimation
semantic_horizon_steps
simulation_tick_count
physical_control_step_seconds
candidate_episode_length_seconds
raw_horizon_ratio
production_rounded_horizon
integrality_error_abs
production_rel_tol = 0.0
production_abs_tol = 1.0e-9
integrality_tolerance_slack
ceil_horizon
lower_bucket_margin = ratio - 2
upper_bucket_margin = 3 - ratio
```

Gate A passes only if all are true:

```text
dt, control step, and episode length are finite and positive
semantic_horizon_steps == 3
simulation_tick_count == decimation * semantic_horizon_steps
production math.isclose predicate passes exactly
production_rounded_horizon == 3
2 < raw_horizon_ratio <= 3
ceil(raw_horizon_ratio) == 3
```

No value may be repaired after a failed predicate.

Future static guards should bind this test-only mirror to the reviewed production source logic so drift cannot silently turn the mirror into a second authority.

## 21. S1 environment-construction boundary

Immediately before `gym.make(...)`, a future harness must durably publish:

```text
active_stage:    S1
active_boundary: S1_ENVIRONMENT_CONSTRUCTION
checkpoint:      environment_construction_entered
```

The environment-construction boundary begins before the call and ends only after the call returns a completed environment object. Any constructor exception belongs to `S1_ENVIRONMENT_CONSTRUCTION`, with its exact exception type, message, traceback, and production failure fields preserved.

It must not fall back to the previously completed S0R stage.

## 22. Gate B — postconstruction timing contract

If and only if `gym.make(...)` returns, a future harness must inspect the completed raw environment before reset. Gate B must verify at least:

```text
raw.max_episode_length == 3
raw.max_episode_length_s == cfg.episode_length_s
raw.step_dt == cfg.sim.dt * cfg.decimation
recomputed actual ratio satisfies 2 < ratio <= 3
ceil(actual ratio) == 3
```

The event-profile scale mapping must exist and agree with the constructed configuration:

```text
contract version is the expected reviewed version
M/N/order/scene spacing match the canonical configuration
sim_dt_seconds matches cfg.sim.dt
control_decimation matches cfg.decimation
physical_control_step_seconds matches raw.step_dt
episode_time_limit_seconds matches candidate episode length
episode_horizon_steps == 3
```

Gate B is evidence validation, not a repair point. A mismatch must stop before reset.

## 23. S1 sub-boundary and durable-checkpoint sequence

The required future sequence is:

| Order | Active stage | Active boundary | Durable checkpoint/action |
|---:|---|---|---|
| 1 | S1 | `S1_ENTER` | emit `s1_entered` |
| 2 | S1 | `S1_PRECONSTRUCTION_TIMING_CONTRACT` | evaluate Gate A; emit `preconstruction_timing_contract_pass` only on PASS |
| 3 | S1 | `S1_ENVIRONMENT_CONSTRUCTION` | emit `environment_construction_entered`; call `gym.make(...)` |
| 4 | S1 | `S1_ENVIRONMENT_CONSTRUCTION` | after return, emit `environment_construction_returned` |
| 5 | S1 | `S1_POSTCONSTRUCTION_TIMING_CONTRACT` | evaluate Gate B; emit `postconstruction_timing_contract_pass` only on PASS |
| 6 | S1 | `S1_RESET` | emit `reset_entered`; perform canonical reset |
| 7 | S1 | `S1_I1_I2` | continue existing reviewed I1/I2 adjudication |

Constructor and reset failures therefore cannot share a boundary. The last durable PASS and the active failing operation are independently recoverable.

## 24. Existing stop taxonomy mapping

No eleventh top-level stop class is introduced.

| Failure site | Existing classification | Precise boundary |
|---|---|---|
| Gate A | `PD2-STOP-PHYSICAL-STEP-FAIL` | `S1_PRECONSTRUCTION_TIMING_CONTRACT` |
| `gym.make` constructor | `PD2-STOP-STARTUP-EQUIVALENCE-MISMATCH` | `S1_ENVIRONMENT_CONSTRUCTION` |
| Gate B | `PD2-STOP-PHYSICAL-STEP-FAIL` | `S1_POSTCONSTRUCTION_TIMING_CONTRACT` |
| reset | `PD2-STOP-STARTUP-EQUIVALENCE-MISMATCH` | `S1_RESET` |

Gate A/B failures remain test-only physical-timeline fixture failures under the frozen R5-C/R5-D taxonomy. A constructor exception remains a startup-equivalence mismatch. Exact exception metadata is retained; it is not flattened into the classification string.

## 25. Historical preservation rule

R5-F must not edit or regenerate the R5-E report or formal artifact. Future evidence may say:

```text
Historical R5-E persisted boundary: S0R
Independent R5-E exception site:    S1 gym.make construction path
Future corrected attribution:       S1_ENVIRONMENT_CONSTRUCTION
```

It may not claim that the historical artifact originally recorded the corrected boundary.

Historical R5-B remains `PD2-STOP-TERMINAL-TRANSPORT-FAIL / S6_TIME_LIMIT`; its real S0-S4 evidence is neither erased nor counted as new R5-F evidence.

## 26. Shutdown remains a secondary issue

R5-E shutdown remains `UNSAFE_OR_INCONCLUSIVE_TERMINATION`. That observation is retained but is outside the two reopened R5-F design questions. It does not change the primary startup mismatch, and R5-F does not design or authorize a shutdown repair.

If a later authorized run constructs an environment successfully but again fails to close within bounds, shutdown must be reviewed as a separate boundary.

## 27. Frozen non-timing contracts

The following remain frozen and are not redesigned here:

- S2 current-critic fingerprint and installed VCritic invocation identity;
- S5 continuation DTO and sole-authority rules;
- historical/current post-return separation;
- S6 timeout critic role selection;
- exact-once timeout-critic invocation evidence;
- exact `torch.equal` tensor correlation and digest rules;
- I5a/I5b terminal transport, TIME_LIMIT bootstrap, GAE, ValueNorm, and rollover rules;
- proposal versus effective assignment semantics;
- P2 sole authority and P2 -> Ak -> controller;
- default-off public route.

R5-D A-AL `38/38 PASS` remains static/synthetic evidence only.

## 28. Protected integrity

Before documentation edits, a 46-file protected set was hashed. It covered the reviewed harness, environment, `DirectMARLEnv`, scale contract, wrapper, runtime facade, proposal adapter, lifecycle/I0-I6 modules, installed HARL actor/critic/buffers/runners/ValueNorm, relevant Kit/AppLauncher sources, and authoritative design/verification reports.

```text
protected files: 46
missing:         0
combined SHA-256:
  976b90be0b0e479d7c2cac42d70146a2fd323c5f27d1bb82cd3c9c9deb796e4b
reviewed harness SHA-256:
  96c220b895b5410d1aca37bfde4f97f09c5e79da785a2b8377642a4c3de9c6d5
```

The post-documentation audit reproduced the same 46-file count, zero missing files, combined SHA-256, and harness SHA-256 exactly. Result: `46/46 UNCHANGED`.

`git diff --check` and whitespace checks for both newly added Markdown files passed with exit code 0. The emitted Git messages were line-ending conversion warnings only, not whitespace errors.

## 29. Decision and next authorized boundary

Design result:

```text
timing candidate:
  ACCEPT Candidate C for future test-only implementation

derivation:
  episode_length_s = float(cfg.sim.dt) *
                     (int(cfg.decimation) * 3)

Gate A:
  DESIGNED / NOT IMPLEMENTED

Gate B:
  DESIGNED / NOT IMPLEMENTED

S1 active-boundary attribution:
  DESIGNED / NOT IMPLEMENTED

formal runtime:
  NOT RUN
```

The next possible slice is `B2-V2-PD2-R5-G`, only after GPT review and explicit user authorization. Its maximum proposed scope is test-only harness implementation plus pure/static verification. R5-G must not infer permission for formal runtime reentry.

Current gates remain:

```text
B2-V2:                         STOPPED / INCOMPLETE
runtime readiness:             BLOCKED
policy readiness:              BLOCKED
learner readiness:             BLOCKED
public learned-policy route:   DORMANT / BLOCKED
B2-R:                          NOT AUTHORIZED
training/playback/evaluation:  NOT AUTHORIZED
commit:                        NONE
```

Stop here and await GPT independent review.
