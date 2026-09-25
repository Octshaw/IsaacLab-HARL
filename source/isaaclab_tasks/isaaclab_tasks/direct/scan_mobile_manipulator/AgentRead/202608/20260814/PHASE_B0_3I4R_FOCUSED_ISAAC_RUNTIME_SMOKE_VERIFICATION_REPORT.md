# Phase B0-3I4-R Focused Isaac Runtime Smoke Verification Report

## Classification

```text
PHASE-B0-3I4R-FOCUSED-ISAAC-RUNTIME-SMOKE-VERIFIED-AWAITING-GPT-REVIEW
```

Date: 2026-08-14

Base phase:

```text
Phase B0-3I4
PHASE-B0-3I4-IMPLEMENTATION-CONDITIONAL-PASS
```

This focused revision closes only the missing bounded Isaac runtime evidence
from B0-3I4. It does not authorize or implement a new lifecycle feature.

## Outcome

The focused runtime smoke passed.

Evidence was obtained from three independent headless processes:

```text
R0-A  minimal AppLauncher baseline                    passed
R0-B  existing/default environment reset + one step  passed
R0-C  event domain + environment construction        passed
R0-D  event initial reset + first physical step      passed
R0-E  event three-step generation continuity         passed
```

The event path constructed a real Isaac environment with two vector rows,
performed a real reset, and performed three real neutral physics steps. Each
step returned the DirectMARLEnv five-element tuple and finalized one lifecycle
transition for every row.

No production defect or external Isaac baseline failure was found. Therefore
neither B0-3I4-R STOP classification applies.

## Authorized scope

The only new executable artifact is a diagnostic runner:

```text
scripts/environments/test_assignment_phase_b0_3i4_runtime_smoke.py
```

Production implementation files were read and hashed but not modified in this
revision. The runner does not enable the event route through wrapper/HARL and
does not change profile readiness.

No training, playback, evaluation, checkpoint operation, GUI run, wrapper
rollout, or policy action selection occurred. No commit was made.

## Diagnosis of the earlier opaque smoke attempts

The prior optional B0-3I4 smoke combined launcher, event terminal/autoreset/R3,
acknowledgement, another event step, a second legacy environment, and shutdown
inside one process. It had no flushed phase markers. The two bounded attempts
therefore timed out without an auditable last completed boundary.

The focused runner exposed one concrete reporting behavior in this Isaac Sim
installation:

```text
SimulationApp.close() is invoked at S13;
the worker process then exits with code 0 without returning to Python code
placed after close().
```

This explains why a direct runner cannot reliably emit S14 or its final result
after `close()`. It does not indicate a production lifecycle defect.

The diagnostic runner uses a small supervisor/worker arrangement:

```text
worker:
  emits every S0-S13 marker with flush=True
  submits its phase result before invoking close()

supervisor:
  streams worker stdout/stderr without buffering
  observes exact worker PID termination and exit code
  emits S14 and the final JSON result
```

This change makes shutdown observable without altering Isaac, environment, or
lifecycle production code. It also prevents a shutdown exit from masking an
earlier worker failure.

The old monolithic timeout location is not retrospectively claimed. The new
staged evidence replaces that unauditable attempt for the authorized minimum
runtime gate.

## Diagnostic runner contract

The runner has three isolated modes:

```text
--mode app
--mode legacy
--mode event
```

Each invocation creates a fresh worker process and a fresh `SimulationApp`.
Markers include stage, PID, monotonic elapsed time, and phase evidence. The
event mode additionally records episode and transition generations.

The exact stage vocabulary is:

```text
S0   diagnostic script entered
S1   before AppLauncher construction
S2   AppLauncher construction returned
S3   before environment/runtime imports
S4   before configuration or event-domain construction
S5   event domain constructed
S6   before environment construction
S7   environment constructed
S8   before reset
S9   observations/current lifecycle publication obtained
S10  before neutral physical step
S11  physical step returned
S12  selected smoke mode complete
S13  before SimulationApp shutdown
S14  supervisor observed worker exit after shutdown
```

The commands use the required interpreter and unbuffered transport:

```text
D:\miniconda3\Scripts\conda.exe run --no-capture-output \
  -p C:\isaacenvs\isaac45_harl python -u \
  scripts/environments/test_assignment_phase_b0_3i4_runtime_smoke.py ...
```

Interpreter evidence:

```text
C:\isaacenvs\isaac45_harl\python.exe
```

## R0-A — AppLauncher baseline

Command mode:

```text
--mode app --json
```

Observed boundary:

```text
worker PID:             20820
S2 elapsed:             5.406 seconds
S13 reached:            yes
S14 child exit code:    0
shutdown observed:      true
result:                 passed
```

The process used `cuda:0` and loaded
`apps/isaaclab.python.headless.kit`. Isaac reported the RTX 4060 Ti as active.

Warnings about the inaccessible OmniHub, deprecated dynamic control, missing
optional rendering-modes config, and the unsupported Intel integrated GPU did
not prevent AppLauncher construction or clean process exit.

R0-A passed, so environment diagnosis was permitted to continue.

## R0-B — Existing/default environment baseline

Command mode:

```text
--mode legacy --num-envs 2 --json
```

Observed boundary:

```text
worker PID:             24256
environment rows:       2
S9 reset returned:      14.390 seconds
S11 step returned:      15.703 seconds
step tuple length:      5
S14 child exit code:    0
shutdown observed:      true
result:                 passed
```

The environment returned observations for `robot_0`, `robot_1`, and
`robot_2`. One zero-action physical step completed. This establishes that the
base Isaac environment route was available before event-specific evidence was
considered.

R0-B passed, so event-profile construction and stepping were permitted.

## R0-C — Event domain and environment construction

Command mode:

```text
--mode event --num-envs 2 --steps 3 --json
```

The canonical event profile was resolved once with formal-entrypoint origin
and passed as the same object to the domain and environment.

Before environment construction, the retained domain published:

```text
episode_generation:     [-1, -1]
transition_generation:  [-1, -1]
result:                 None
terminated:             [false, false]
truncated:              [false, false]
```

Observed construction boundary:

```text
worker PID:             28840
device:                 cuda:0
S5 domain constructed:  13.578 seconds
S7 environment built:   yes
```

No raw producer, clock, store, ledger, or authority capability was read by the
smoke. Lifecycle state was observed only through `current_read_port`.

## R0-D — Initial reset and first transition

After the real environment reset, the current publication was:

```text
episode_generation:     [0, 0]
transition_generation:  [-1, -1]
result:                 None
```

The first neutral physical step returned at 15.781 seconds with:

```text
tuple length:            5
episode_generation:     [0, 0]
transition_generation:  [0, 0]
finalized result:        present
lifecycle event count:  0
terminated:             [false, false]
truncated:              [false, false]
```

The next physical step was admitted, which is also runtime evidence that the
coordinator was not poisoned and no terminal acknowledgement gate was pending.

## R0-E — Bounded continuity

Three neutral steps produced this exact sequence:

```text
step 0: episode [0, 0], transition [0, 0], events 0
step 1: episode [0, 0], transition [1, 1], events 0
step 2: episode [0, 0], transition [2, 2], events 0
```

Every step returned the five-element environment tuple and a finalized result.
No step terminated or truncated either row. No episode rebuild occurred during
the continuity interval.

Shutdown evidence:

```text
S12 elapsed:            16.687 seconds
S13 elapsed:            17.156 seconds
S14 supervisor elapsed: 18.469 seconds
child exit code:         0
shutdown observed:       true
```

No matching smoke or Isaac child process remained after the run.

## Terminal-path boundary

This focused runtime verification deliberately used nonterminal neutral steps.
The optional forced-terminal runtime branch was not required for the minimum
B0-3I4-R gate and was not exercised.

Terminal slot, synchronous exact-key acknowledgement, R3 blocking, reset
coexistence, and publication atomicity remain covered by the unchanged I4 pure
suite at 16/16. This report does not upgrade that pure evidence into a claim of
real-Isaac terminal transition execution.

## Regression verification

All required pure/static suites passed after the smoke:

```text
I4 terminal handoff pure                  16/16 passed
I4 environment integration static         12/12 passed
I3 staged pre-reset adapter                16/16 passed
I2 runtime domain capabilities             12/12 passed
I1 episode rebuild transaction             12/12 passed
B0-2 lifecycle authority transaction       18/18 passed
B0-1A execution facts producer              9/9 passed
B0-1B generation clock                     12/12 passed
lifecycle transition contract              12/12 passed
assignment profile contract                16/16 passed
event-profile schema                         9/9 passed
Phase-A default-off identity               16/16 passed
profile production wiring                  10/10 passed
event-gated MRTA contract                  13/13 passed
```

Additional checks:

```text
diagnostic runner py_compile   passed
git diff --check               passed (existing line-ending warnings only)
leftover smoke/Isaac process   none
```

## Production byte identity

The three production files involved in B0-3I4 retained the exact hashes
recorded before this focused revision:

```text
scan_mobile_manipulator_env.py
030EFB1BE030C6F1BB22BB2DCF5918D0235305CB5D543D01569C1066836501D5

assignment_event_profile_runtime_domain.py
8491398D03A16FA34AB0C7E5E62B858D81308FFFFADC959D5B59F8B71AA2DC7A

assignment_lifecycle_transaction_runtime.py
F77BA9B713E4AB394B389EDFF16D19B992D944C5851CAD232B4DBCA42088D803
```

The final diagnostic runner hash before documentation closeout is:

```text
267811C211643834C00C43F2AAB29D5C2FEF2751AA43EA1D2BDE0EDF351293F0
```

## Changed files in B0-3I4-R

```text
scripts/environments/test_assignment_phase_b0_3i4_runtime_smoke.py
AgentRead/202608/20260814/PHASE_B0_3I4R_FOCUSED_ISAAC_RUNTIME_SMOKE_VERIFICATION_REPORT.md
AgentRead/TASK_PROGRESS.md
```

All other dirty or untracked workspace files predate this focused revision and
were preserved. No TASK_PROGRESS archive was created because the existing
handoff remained within the AGENTS.md size target and required only a focused
in-place update.

## Boundaries preserved

This verification does not:

```text
flip event-profile runtime readiness
route event profile through wrapper or HARL
add wrapper/HARL terminal transport or acknowledgement
add assignment, claim, transfer, or ordinary phase progression
add Phase B/C/D/E behavior
add a terminal sidecar
change frozen Phase-A or B0 contracts
claim a real-Isaac terminal transition smoke
authorize training, playback, or evaluation
create a commit
```

## Final handoff

The prior opaque timeout is replaced by auditable, stage-local evidence. The
minimal AppLauncher baseline, existing environment baseline, event domain and
environment construction, initial episode rebuild, three authoritative
nonterminal transitions, generation continuity, and shutdown all passed.

The focused classification at the top of this report therefore applies. The
next action is GPT/user review. Runtime readiness, wrapper/HARL transport,
training, playback, evaluation, and later lifecycle phases remain unauthorized.
