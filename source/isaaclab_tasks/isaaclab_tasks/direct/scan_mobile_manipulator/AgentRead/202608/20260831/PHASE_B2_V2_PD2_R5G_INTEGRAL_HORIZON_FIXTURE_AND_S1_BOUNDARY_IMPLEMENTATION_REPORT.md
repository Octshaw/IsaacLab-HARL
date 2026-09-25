# Phase B2-V2-PD2-R5-G Integral-Horizon Fixture and S1 Boundary Implementation Report

## 1. Starting authority

```text
starting HEAD: 14993dee344bade0230d2eb97b5f22171331f44a
B2-D:          REVIEW PASS / FROZEN
B2-I0..I6:     REVIEW PASS / CLOSED
B2-V1:         GPT REVIEW PASS / CLOSED
B2-V2:         STOPPED / INCOMPLETE
R5-F:          GPT REVIEW PASS / FROZEN
```

R5-F is the frozen design authority for this implementation. Its selected Candidate C, Gate A, Gate B, and S1 boundary sequence were implemented only in the test-only PD2 harness. The historical R5-E result remains unchanged.

## 2. Classification

```text
classification:
  PHASE-B2-V2-PD2-R5G-INTEGRAL-HORIZON-AND-S1-BOUNDARY-IMPLEMENTATION-PASS-AWAITING-GPT-REVIEW

R5-G:             IMPLEMENTATION PASS / AWAITING GPT REVIEW
B2-V2:            STOPPED / INCOMPLETE
formal runtime:   NOT RUN / NOT AUTHORIZED
R5-H:             NOT AUTHORIZED
B2-R:             NOT AUTHORIZED
commit:           NONE
```

## 3. Scope and authorization boundary

This slice implemented and verified the R5-F contract offline. It did not run the formal supervisor or worker and did not initialize AppLauncher, SimulationApp, Isaac, CUDA, a real HARL actor/VCritic, an environment, reset, or step.

No production repair, environment change, DirectMARLEnv change, I0-I6 change, installed HARL change, Kit/cache mutation, training, playback, evaluation, checkpoint operation, or public-route activation was authorized or performed.

## 4. Files modified or created

Test-only implementation:

- `scripts/environments/test_assignment_phase_b2_v2_pd2_production_startup_path_real_interface_smoke.py`

Documentation:

- `AgentRead/202608/20260831/PHASE_B2_V2_PD2_R5G_INTEGRAL_HORIZON_FIXTURE_AND_S1_BOUNDARY_IMPLEMENTATION_REPORT.md`
- `AgentRead/202608/20260831/TASK_PROGRESS_ARCHIVE_BEFORE_PD2_R5G_HANDOFF_20260831.md`
- `AgentRead/TASK_PROGRESS.md`

Production changes: `NONE`.

Installed HARL changes: `NONE`.

## 5. Old midpoint retirement

The old current-authority fixture `control_step * 2.5` was removed from the formal harness path. It remains only as an explicitly named negative historical regression:

```text
MIDPOINT_2P5
episode length:             0.25
raw ratio:                  2.5
ceil:                       3
production round:           2
production integrality:     FAIL
expected:                   REJECT
```

No current runtime path uses the midpoint, `nextafter`, epsilon subtraction, a magic offset, or a hardcoded `0.299999...` value.

## 6. Candidate C implementation

The formal harness config path now builds the episode time from an integer simulation-tick horizon:

```python
semantic_horizon_steps = 3
simulation_tick_count = control_decimation * semantic_horizon_steps
physical_control_step_seconds = sim_dt_seconds * control_decimation
candidate_episode_length_seconds = sim_dt_seconds * simulation_tick_count
```

Frozen arithmetic was reproduced exactly:

```text
sim_dt_seconds:                    0.016666666666666666
control_decimation:                6
semantic_horizon_steps:            3
simulation_tick_count:             18
physical_control_step_seconds:     0.1
candidate_episode_length_seconds:  0.3
raw_horizon_ratio:                 2.9999999999999996
production_rounded_horizon:        3
integrality_error_abs:             4.440892098500626e-16
production_abs_tol:                1e-09
production integrality:            PASS
ceil_horizon:                      3
```

This preserves the reviewed intended timeline: transition 1 nonterminal, transition 2 TIME_LIMIT. That timeline is offline contract evidence only; it was not rerun against Isaac in R5-G.

## 7. Timing DTO and schema

The retired `PD2TimeoutFixtureV1` was replaced by immutable, slotted, bounded `PD2IntegralHorizonFixtureV1`. It contains:

- source inputs: sim dt, decimation, semantic horizon;
- derived tick, control-step, episode-time, ratio, round, error, tolerance slack, ceil, and bucket margins;
- desired terminal transition and required max episode length;
- the exact production tolerance constants.

The postconstruction side uses immutable, slotted `PD2S1PostconstructionTimingEvidenceV1`; it copies only bounded primitive evidence from the completed environment and production scale mapping.

## 8. Gate A implementation

`build_pd2_integral_horizon_fixture_v1(...)` builds Candidate C. `adjudicate_pd2_s1_preconstruction_timing_v1(...)` validates it before `gym.make(...)`.

Gate A checks all frozen predicates, plus self-consistency of every stored derivation. Failure mapping is unchanged at the top level:

```text
classification: PD2-STOP-PHYSICAL-STEP-FAIL
boundary:       S1_PRECONSTRUCTION_TIMING_CONTRACT
```

A Gate A failure cannot proceed to constructor, reset, model forward, or physical step.

## 9. Gate A source-faithful production mirror

The test-only mirror uses exactly:

```python
rounded_horizon = round(raw_horizon_ratio)
math.isclose(raw_horizon_ratio, rounded_horizon, rel_tol=0.0, abs_tol=1.0e-9)
```

It does not introduce a second tolerance or alter `episode_length_s` after adjudication.

## 10. S1_ENTER implementation

After the reviewed S0R gate returns successfully and before `run_real_smoke(...)` performs S1 imports/operations, the harness durably publishes:

```text
active_stage:    S1
active_boundary: S1_ENTER
checkpoint:      s1_entered
```

## 11. Environment-construction attribution

Only after Gate A PASS, immediately before `gym.make(...)`, the harness publishes:

```text
active_boundary: S1_ENVIRONMENT_CONSTRUCTION
checkpoint:      environment_construction_entered
```

Only a successful constructor return records `environment_construction_returned`. An untyped constructor exception now remains `PD2-STOP-STARTUP-EQUIVALENCE-MISMATCH` but receives first boundary `S1_ENVIRONMENT_CONSTRUCTION`; it cannot fall back to S0R.

The exception record preserves the exact exception type, message, traceback, and bounded production fields `failure_code`, `stage`, `expected`, and `actual` when present.

## 12. Gate B implementation

After constructor return and before reset, the harness builds bounded postconstruction evidence from:

- `raw.max_episode_length`;
- `raw.max_episode_length_s`;
- `raw.step_dt`;
- the configured dt, decimation, episode length, agent/task order, and scene spacing;
- `raw._event_terminal_critic_scale_contract_v2`.

`adjudicate_pd2_s1_postconstruction_timing_v1(...)` validates this evidence without mutating the raw environment, config, or scale mapping. Failure mapping is:

```text
classification: PD2-STOP-PHYSICAL-STEP-FAIL
boundary:       S1_POSTCONSTRUCTION_TIMING_CONTRACT
```

Only Gate B PASS records `postconstruction_timing_contract_pass` and permits reset.

## 13. Gate B float-comparison source audit

| Field | Source origin | Copied or recomputed | R5-G comparison rule |
|---|---|---|---|
| `raw.max_episode_length_s` | `DirectMARLEnv.max_episode_length_s` returns `self.cfg.episode_length_s` | direct config return | exact equality with configured Candidate C |
| `raw.step_dt` | `DirectMARLEnv.step_dt` returns `self.cfg.sim.dt * self.cfg.decimation` | recomputed with the same expression | exact equality with `cfg.sim.dt * cfg.decimation` |
| `raw.max_episode_length` | `ceil(max_episode_length_s / (sim.dt * decimation))` | recomputed | exact integer `3` |
| scale `sim_dt_seconds` | scan env passes `float(self.cfg.sim.dt)`; scale builder validates/retains it | converted then copied | exact equality with the converted config value |
| scale `control_decimation` | scan env passes `int(self.cfg.decimation)` | converted then copied | exact integer equality |
| scale `physical_control_step_seconds` | scale builder computes `sim_dt * decimation` | recomputed | exact equality with `raw.step_dt` because both use the same operation and operands |
| scale `episode_time_limit_seconds` | scan env passes `float(self.cfg.episode_length_s)`; scale builder retains it | converted then copied | exact equality with Candidate C configured time |
| scale `episode_horizon_steps` | scale builder uses `round(time_limit / control_step)` after production `isclose` | recomputed | exact integer `3`; integrality uses production `isclose` |
| scale M/N/order/spacing | scan env canonical fields passed into scale builder | validated and retained | exact fixed-cardinality/order/value equality |

Source facts audited:

- `source/isaaclab/isaaclab/envs/direct_marl_env.py`: `step_dt`, `max_episode_length_s`, and `max_episode_length` properties;
- `assignment_event_profile_schema_contract_v2.py`: scale builder multiplication, ratio, `round`, and `math.isclose(rel_tol=0.0, abs_tol=1.0e-9)`;
- `scan_mobile_manipulator_env.py`: direct mapping from config and canonical M/N/order/spacing into the production scale contract.

No comparison is stricter than the audited production value path. Recomputed horizon integrality follows production semantic tolerance rather than bytewise ratio identity.

## 14. S1_RESET attribution

After Gate B PASS and immediately before the canonical admitted reset:

```text
active_boundary: S1_RESET
checkpoint:      reset_entered
```

An untyped reset exception is therefore attributed to `S1_RESET` with the existing startup classification.

## 15. S1_I1_I2 attribution

After reset returns, before the existing reviewed I1/I2 checks:

```text
active_boundary: S1_I1_I2
checkpoint:      reset_returned_i1_i2_entered
```

No I1/I2 semantics were changed.

## 16. Timing synthetic migration

Existing R5-D timing-specific cases A-D were migrated:

- A now treats Candidate C as the positive authoritative fixture;
- B retains the intended two-transition timeline;
- C retains `control_step * 3` only as a negative ceil regression;
- D validates Gate B fail-closed behavior for an actual max length of four.

Existing non-timing cases E-AL were not renumbered or semantically changed.

## 17. Historical Candidate A/B regressions

Both rejected candidates remain visible as named negative cases:

```text
Candidate A midpoint:       ratio 2.5, production integrality FAIL
Candidate B step times 3:   episode 0.30000000000000004,
                            ratio 3.0000000000000004,
                            production integrality PASS, ceil 4, REJECT
```

## 18. Candidate C positive regression

`CANDIDATE_C_INTEGER_SIM_TICKS_18` asserts exact episode `0.3`, ratio `2.9999999999999996`, round `3`, production integrality PASS, and ceil `3`.

## 19. Gate A pure cases

GA1-GA7 all passed:

- Candidate C PASS;
- midpoint integrality rejection;
- control-step-times-three ceil rejection;
- semantic horizon mismatch rejection;
- lower/upper bucket rejection;
- resolved production horizon mismatch rejection.

## 20. Gate B pure cases

GB1-GB7 all passed using synthetic bounded DTOs, not a real environment:

- canonical PASS;
- max episode length, step dt, scale horizon, contract version, episode time, and actual ceil mismatches all fail closed at the exact Gate B boundary.

## 21. Boundary-attribution cases

BA1-BA5 all passed:

- Gate A failure -> `S1_PRECONSTRUCTION_TIMING_CONTRACT`;
- constructor failure -> `S1_ENVIRONMENT_CONSTRUCTION`;
- Gate B failure -> `S1_POSTCONSTRUCTION_TIMING_CONTRACT`;
- reset failure -> `S1_RESET`;
- prior S0R PASS cannot recapture a subsequent constructor failure.

## 22. Non-timing R5-D regression

The complete existing R5-D/R5-D-TR/R5-D-TR2 A-AL matrix remains `38/38 PASS`. The existing S2/S5/S6 identity, exact-input, proposal/logprob, P2/Ak, historical/current, and no-training assertions remain active.

## 23. Static guards

Static review proves:

- Candidate C uses the reviewed multiplication order;
- no midpoint current authority or float fudge is present in the formal path;
- Gate A PASS and constructor boundary publication precede `gym.make`;
- Gate B occurs after constructor return and before reset;
- reset occurs only after Gate B PASS;
- worker fallback uses `active_boundary`, not the earlier S0R stage;
- the formal STOP taxonomy remains the exact frozen ten classes;
- R5-E and R5-F historical/frozen reports are hash protected.

## 24. CLI and verification commands

The prior CLI remains intact and `--r5g-only` was added for timing/boundary-specific offline verification.

Commands run with the exact interpreter:

```text
C:\isaacenvs\isaac45_harl\python.exe -m py_compile \
  scripts/environments/test_assignment_phase_b2_v2_pd2_production_startup_path_real_interface_smoke.py

C:\isaacenvs\isaac45_harl\python.exe \
  scripts/environments/test_assignment_phase_b2_v2_pd2_production_startup_path_real_interface_smoke.py --static-only

C:\isaacenvs\isaac45_harl\python.exe \
  scripts/environments/test_assignment_phase_b2_v2_pd2_production_startup_path_real_interface_smoke.py --r5g-only

C:\isaacenvs\isaac45_harl\python.exe \
  scripts/environments/test_assignment_phase_b2_v2_pd2_production_startup_path_real_interface_smoke.py --r5d-only
```

Results:

```text
py_compile:       PASS
--static-only:    PD2_STATIC_PREFLIGHT_PASS
--r5g-only:       R5G PASS; 22/22 R5-G cases; 38/38 R5-D regression
--r5d-only:       PASS; CUDA initialized before/after = 0/0
failed cases:     NONE
git diff --check: PASS / EXIT 0
```

## 25. No-runtime counters

```text
formal supervisor:     0
worker:                0
AppLauncher:           0
SimulationApp:         0
Isaac:                 0
gym.make:              0
CUDA:                  0
real HARL/VCritic:     0 / 0
real actor:            0
environment construct:0
reset/step:            0 / 0
optimizer/backward:    0 / 0
training:              0
playback/evaluation:   NOT RUN / NOT RUN
```

CPU Torch was imported only by the existing `--r5d-only` synthetic suite. `torch.cuda.is_initialized()` was false before and after.

## 26. Protected integrity and hashes

```text
pre-R5G harness SHA-256:
  96c220b895b5410d1aca37bfde4f97f09c5e79da785a2b8377642a4c3de9c6d5

post-R5G harness SHA-256:
  593fad7a980d584954e7a55cecb4a91234ad16e7dc4064c96c75f59e9bcccd34

protected source/report observations: 56
protected mismatches:                 0
historical R5-E report SHA-256:
  21fc419942c63c278af6ee1a89706c4404d4a57abf4b77772155062ebcb8287c
frozen R5-F report SHA-256:
  4683245527f5294c14c4995bb618687de4daf3d9dd3c3b0305291138ab04d6ef
```

The harness is the only code file intentionally changed. Production, DirectMARLEnv, scan environment, wrapper, runtime facade, I0-I6, installed HARL, official Kit, and historical protected reports matched their frozen hashes.

## 27. Historical and readiness non-claims

R5-E remains historically:

```text
classification: PD2-STOP-STARTUP-EQUIVALENCE-MISMATCH
first_boundary: S0R
independent later exception site: S1 gym.make path
```

R5-G does not rewrite that artifact and does not establish constructor, reset, VCritic, actor, physical step, S5/S6, Snapshot B, safe shutdown, or B2-V2 runtime PASS.

Runtime, policy, and learner readiness remain BLOCKED. The public learned-policy route remains DORMANT / BLOCKED. Training remains NOT AUTHORIZED.

## 28. Final classification

```text
PHASE-B2-V2-PD2-R5G-INTEGRAL-HORIZON-AND-S1-BOUNDARY-IMPLEMENTATION-PASS-AWAITING-GPT-REVIEW
```

This classification means only that the R5-F test-only timing/boundary design is implemented and passes offline pure/static verification.

## 29. Recommended next decision

Stop and wait for GPT independent implementation review.

Only after that review and a new explicit user authorization may the project consider B2-V2-PD2-R5-H: one controlled formal reentry with the new reviewed harness identity. R5-H, B2-R, training, playback, evaluation, public-route activation, and commit are not authorized by this report.
