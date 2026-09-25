# Phase B2-V2-D4-O SimulationApp Shutdown Observability Contract Report

Date: 2026-08-27

Classification: `PHASE-B2-V2-D4O-SIMULATIONAPP-SHUTDOWN-OBSERVABILITY-CONTRACT-COMPLETE-AWAITING-GPT-REVIEW`

## 1. Outcome

D4-O established a repeatable process-level shutdown evidence mode without changing `SimulationApp`, fast-shutdown settings, AppLauncher, framework code, or production:

```text
T0 minimal/no-op:
  NOOP_PASS + EXTERNAL_CLEAN_TERMINATION 3/3

T1 minimal/CUDA body:
  CUDA_PASS + EXTERNAL_CLEAN_TERMINATION 3/3

T2 expected diagnostic failure artifact:
  EXPECTED_TEST_FAILURE + EXTERNAL_CLEAN_TERMINATION 2/2

O6 SimulationApp_close_returned:
  0/8

timeout / supervisor kill / main survivor / known-child survivor:
  0 / 0 / 0 / 0

supervisor cleanup:
  PASS 8/8
```

The pure shutdown classifier also passed 12/12 synthetic cases, including timeout, survivor, missing-result/checkpoint, cleanup/hash failure, unexpected non-zero exit, and authorized expected-failure non-zero exit branches.

Evidence supports the proposed domain:

```text
shutdown_result in {
  IN_PROCESS_CLOSE_RETURN,
  EXTERNAL_CLEAN_TERMINATION,
  UNSAFE_OR_INCONCLUSIVE_TERMINATION
}

safe_shutdown = shutdown_result in {
  IN_PROCESS_CLOSE_RETURN,
  EXTERNAL_CLEAN_TERMINATION
}
```

O6 is retained as exact in-process return evidence but removed from the proposed universal clean-shutdown requirement. No O6 was fabricated.

## 2. Starting checkpoint and frozen state

```text
branch:        main
HEAD:          14993dee344bade0230d2eb97b5f22171331f44a
git describe:  v2.0.0-53-g14993dee-dirty

B2-D:          REVIEW PASS / FROZEN
B2-I0-I6:      REVIEW PASS / CLOSED
B2-V1:         GPT REVIEW PASS / CLOSED
B2-V2:         STOPPED / INCOMPLETE
B2-V2-D1:      GPT REVIEW PASS / CLOSED
B2-V2-D2:      GPT REVIEW PASS / CLOSED
B2-V2-D3 core: GPT REVIEW PASS / FROZEN
B2-V2-D3:      STOPPED / INCOMPLETE
B2-V2-D4:      STOPPED / INCOMPLETE under old shutdown contract
B2-R:          NOT AUTHORIZED
training:      NOT AUTHORIZED
commit:        NONE
```

Frozen upstream results remain unchanged:

```text
D1: APP_LAUNCHER_CUDA_CONTEXT_INTERACTION
D2: APPLAUNCHER_TORCH_CUDA_FIRST_USE_ORDER_SENSITIVE_BEHAVIOR
D3: APPLAUNCHER_EXPERIENCE_SUFFICIENT_BOUNDARY
D4 static normalized experience diff: RETAINED
D4 R1-R8 runtime evidence: NONE
```

## 3. D4 STOP history and reason for contract review

Old D4 required every B0 repeat to persist S0-S15, where S15 meant Python regained control after `SimulationApp.close()`. Its first worker completed CUDA through Linear, persisted S13/S14, entered close, exited code 0 with no timeout or survivor, but did not persist S15. D4 therefore correctly stopped under its authorized contract.

GPT review retained that STOP and identified the narrower incompatibility: S15-only observability was too strong for the observed standalone fast-shutdown lifecycle. D4-O evaluates a new contract; it does not reinterpret the old execution under rules created later.

## 4. Scope and files

Added test-only script:

- `scripts/environments/test_assignment_phase_b2_v2_d4o_simulationapp_shutdown_observability.py`

Documentation:

- this report;
- updated `AgentRead/TASK_PROGRESS.md`.

```text
D4 original harness changes:    NONE
D3/D2/D1/V2 harness changes:   NONE
production modifications:       NONE
AppLauncher changes:            NONE
SimulationApp/framework changes:NONE
production .kit changes:        NONE
installed HARL changes:         NONE
Torch/CUDA/driver changes:      NONE
fast_shutdown override:         NONE
monkeypatch/atexit workaround:  NONE
```

## 5. Installed SimulationApp source audit

Audited source:

```text
C:\isaacenvs\isaac45_harl\Lib\site-packages\isaacsim\exts\
  isaacsim.simulation_app\isaacsim\simulation_app\simulation_app.py

SHA-256:
  7d9ac4310913d776c17abe9f8cd0041b3d4d62cfcf6cd1a7d0548e85c2dd5b69
```

Source-supported facts:

- `DEFAULT_LAUNCHER_CONFIG` sets `fast_shutdown=True` at line 79;
- its parameter documentation at line 109 describes `True` as exiting the process immediately and `False` as shutting down each extension;
- construction passes the resolved value to `/app/fastShutdown` at line 321;
- `close()` begins at line 561;
- the shutdown path prints/logs `Simulation App Shutting Down`, calls `self._app.shutdown()`, and then `self._framework.unload_all_plugins()` at lines 588 and 616-617.

All eight workers recorded the actual `simulation_app.config["fast_shutdown"]` as `true`. D4-O did not supply or mutate that key.

The source supports immediate-process-exit intent for the active default. It does not provide a Python-level guarantee about whether control returns after plugin unload in every configuration. D4-O therefore uses runtime checkpoints for that fact: O6 was absent in 8/8 actual runs.

## 6. Candidate shutdown evidence contract

### Mode A — `IN_PROCESS_CLOSE_RETURN`

Required joint evidence:

```text
valid primary diagnostic result
O4 primary_result_persisted
O5 immediately_before_SimulationApp_close
O6 SimulationApp_close_returned
normal exit or exact authorized expected-failure exit
no timeout or supervisor kill
main worker dead
no known pre-close descendant survivor
supervisor cleanup PASS
protected files unchanged
```

O6 means exactly that `SimulationApp.close()` returned to Python. No other signal substitutes for O6.

### Mode B — `EXTERNAL_CLEAN_TERMINATION`

Required joint evidence:

```text
valid primary diagnostic result
O4 primary_result_persisted
O5 immediately_before_SimulationApp_close
O6 absent — no close-return claim
normal exit or exact authorized expected-failure exit
no timeout or supervisor kill
main worker dead
no known pre-close descendant survivor
supervisor cleanup PASS
protected files unchanged
```

The shutdown stdout marker is supporting evidence only. Exit code 0 alone is insufficient.

### Mode C — `UNSAFE_OR_INCONCLUSIVE_TERMINATION`

Any of these is sufficient:

- timeout or supervisor kill;
- main worker or known child survives;
- missing/corrupt primary result;
- O4 or O5 missing;
- unexpected non-zero exit;
- supervisor cleanup failure;
- protected hash change;
- ambiguous process state.

An exact authorized expected diagnostic failure artifact may use its explicitly defined non-zero exit without becoming unsafe automatically. It still must satisfy every other clean-evidence condition.

## 7. Diagnostic result is orthogonal

The contract stores these as separate fields:

```text
diagnostic_result
shutdown_result
```

Actual observations include both:

```text
CUDA_PASS + EXTERNAL_CLEAN_TERMINATION
EXPECTED_TEST_FAILURE + EXTERNAL_CLEAN_TERMINATION
```

Thus diagnostic failure is not shutdown failure, and clean shutdown is not a CUDA pass claim.

## 8. Crash-safe persistence and ownership

Checkpoint and primary-result files are external to the worker's post-close control flow. Every write uses:

```text
temporary sibling file
-> flush
-> os.fsync
-> os.replace
```

Worker responsibility ends after it persists O4, captures the known pre-close process tree, persists O5, and calls `SimulationApp.close()`. O6 is written only if close truly returns.

Supervisor responsibility includes timeout enforcement, process-exit observation, known-child survivor checks, result/checkpoint parsing, stdout/stderr capture, and temporary-directory deletion. Cleanup never depends on worker code after close.

## 9. Synthetic unsafe-classifier oracle

Pure metadata classification used no Isaac process. All 12 cases passed:

| Case | Expected and observed |
|---|---|
| in-process O6 | `IN_PROCESS_CLOSE_RETURN` |
| external clean, no O6 | `EXTERNAL_CLEAN_TERMINATION` |
| timeout + supervisor kill | `UNSAFE_OR_INCONCLUSIVE_TERMINATION` |
| surviving main worker | `UNSAFE_OR_INCONCLUSIVE_TERMINATION` |
| surviving known child | `UNSAFE_OR_INCONCLUSIVE_TERMINATION` |
| missing O4 | `UNSAFE_OR_INCONCLUSIVE_TERMINATION` |
| missing O5 | `UNSAFE_OR_INCONCLUSIVE_TERMINATION` |
| corrupt/missing result | `UNSAFE_OR_INCONCLUSIVE_TERMINATION` |
| supervisor cleanup failure | `UNSAFE_OR_INCONCLUSIVE_TERMINATION` |
| protected hash change | `UNSAFE_OR_INCONCLUSIVE_TERMINATION` |
| unexpected exit code 7 | `UNSAFE_OR_INCONCLUSIVE_TERMINATION` |
| authorized expected-failure exit code 10 | `EXTERNAL_CLEAN_TERMINATION` |

No actual healthy SimulationApp was killed to test unsafe classification.

## 10. T0 — minimal SimulationApp normal close

Definition:

```text
fresh process
direct SimulationApp({"headless": True})
no AppLauncher
no custom experience
no Torch import/CUDA body
no MRTA/HARL/I0-I6
no-op diagnostic
O4 -> O5 -> close -> O6 only if returned
```

Results:

| Repeat | Checkpoints | Diagnostic | Exit | Timeout/kill | Main/known-child survivors | Marker | Cleanup | Shutdown class | Elapsed |
|---:|---|---|---:|---|---|---|---|---|---:|
| 1 | O0-O5; O6 absent | `NOOP_PASS` | 0 | false/false | 0/0 | yes | PASS | `EXTERNAL_CLEAN_TERMINATION` | 13.171 s |
| 2 | O0-O5; O6 absent | `NOOP_PASS` | 0 | false/false | 0/0 | yes | PASS | `EXTERNAL_CLEAN_TERMINATION` | 13.125 s |
| 3 | O0-O5; O6 absent | `NOOP_PASS` | 0 | false/false | 0/0 | yes | PASS | `EXTERNAL_CLEAN_TERMINATION` | 13.171 s |

Decision:

```text
EXTERNAL_CLEAN_TERMINATION 3/3
IN_PROCESS_CLOSE_RETURN    0/3
UNSAFE/INCONCLUSIVE        0/3
```

This provides stable evidence that the current standalone minimal fast-shutdown path commonly terminates the worker before an O6 Python checkpoint.

## 11. T1 — minimal SimulationApp with CUDA body

T1 ran only after T0 established one stable clean mode. It used no pre-startup CUDA initialization.

Unified body:

```text
cuda:0 / float32 / 8x8 / seed 260826
allocation -> x + 1 -> synchronize
matmul -> synchronize
Linear(8,8) -> synchronize
```

Results:

| Repeat | Checkpoints | Diagnostic | Exit | Timeout/kill | Main/known-child survivors | Marker | Cleanup | Shutdown class | Elapsed |
|---:|---|---|---:|---|---|---|---|---|---:|
| 1 | O0-O5; O6 absent | `CUDA_PASS` | 0 | false/false | 0/0 | yes | PASS | `EXTERNAL_CLEAN_TERMINATION` | 17.359 s |
| 2 | O0-O5; O6 absent | `CUDA_PASS` | 0 | false/false | 0/0 | yes | PASS | `EXTERNAL_CLEAN_TERMINATION` | 17.125 s |
| 3 | O0-O5; O6 absent | `CUDA_PASS` | 0 | false/false | 0/0 | yes | PASS | `EXTERNAL_CLEAN_TERMINATION` | 17.250 s |

Each CUDA body recorded:

```text
basic finite/sum:   true / 128.0
matmul finite/sum:  true / 16128.0
Linear shape/finite:[2,8] / true
Torch:              2.5.1+cu121
CUDA build:         12.1
```

Decision:

```text
CUDA_PASS                     3/3
EXTERNAL_CLEAN_TERMINATION    3/3
IN_PROCESS_CLOSE_RETURN       0/3
UNSAFE/INCONCLUSIVE           0/3
```

This is lifecycle-control evidence, not renewed experience isolation or B2-V2 evidence.

## 12. T2 — expected diagnostic failure with clean shutdown

T2 ran only after T0 and T1 were stable. It persisted an authorized synthetic Python diagnostic failure artifact and did not create a CUDA failure.

| Repeat | Checkpoints | Diagnostic | Exit | Timeout/kill | Main/known-child survivors | Marker | Cleanup | Shutdown class | Elapsed |
|---:|---|---|---:|---|---|---|---|---|---:|
| 1 | O0-O5; O6 absent | `EXPECTED_TEST_FAILURE` | 0 | false/false | 0/0 | yes | PASS | `EXTERNAL_CLEAN_TERMINATION` | 13.922 s |
| 2 | O0-O5; O6 absent | `EXPECTED_TEST_FAILURE` | 0 | false/false | 0/0 | yes | PASS | `EXTERNAL_CLEAN_TERMINATION` | 14.219 s |

Decision: diagnostic-result and shutdown-result orthogonality is directly verified 2/2.

## 13. Process-tree and marker evidence

At O5 each worker used `psutil 5.9.8` to persist a recursive pre-close descendant snapshot including PID, create time, and process name. The supervisor compared PID and create time after worker termination and waited up to five seconds for known descendants to disappear.

Observed pre-close known-child counts:

```text
T0: 6, 6, 6
T1: 0, 0, 0
T2: 6, 4
```

T0/T2 children were `nvngx_update.exe` and `conhost.exe` instances. Known surviving children after each worker: `0/8` runs.

Limitation: this proves no survivor among descendants known at O5. It cannot prove absence of a descendant created only after O5. The report therefore does not claim universal OS process-tree completeness.

`Simulation App Shutting Down` appeared in 8/8 captured outputs. It is recorded as supporting evidence only and is not required by the classifier.

## 14. Final contract decision

Evidence supports this proposed D4-O contract pending GPT review:

```text
shutdown_result ∈ {
  IN_PROCESS_CLOSE_RETURN,
  EXTERNAL_CLEAN_TERMINATION,
  UNSAFE_OR_INCONCLUSIVE_TERMINATION
}

safe_shutdown = shutdown_result in {
  IN_PROCESS_CLOSE_RETURN,
  EXTERNAL_CLEAN_TERMINATION
}

O6 universal requirement:
  REMOVED FROM PROPOSED CONTRACT

O6 meaning:
  retained exclusively as in-process close-return evidence

stdout marker:
  supporting only

diagnostic_result:
  orthogonal to shutdown_result
```

The active SimulationApp behavior remains unchanged.

## 15. D3 G4 non-reinterpretation

D3 G4 remains `UNSAFE / INCONCLUSIVE` because it timed out, required supervisor termination, and lacked a structured CUDA result. Allowing clean termination without O6 does not waive timeout, kill, result, survivor, cleanup, or protected-state requirements.

```text
D3 G4 reinterpreted: NO
```

## 16. No retroactive D4 pass

Old D4 remains stopped under its old S15-only contract. Its single repeat is not counted toward any future baseline.

```text
old D4 retroactively passed: NO
future D4 retry baseline:     must restart at B0 repeat 1
```

## 17. Protected hashes and cleanup

The formal run protected the D4 36-file set: I0-I6/runtime/lifecycle/env/wrapper/training, DirectMARLEnv, installed HARL actor/critic/buffers/runners/ValueNorm, V2/D1/D2/D3/D4 harnesses, AppLauncher, three experience files, and installed SimulationApp source.

```text
protected before/after: 36/36 unchanged
```

Every worker's checkpoint, primary-result, and temporary directory was supervisor-owned and removed after evidence extraction:

```text
supervisor cleanup: 8/8 PASS
temporary directories remaining: 0
```

## 18. Runtime inventory

```text
interpreter:          C:\isaacenvs\isaac45_harl\python.exe
Python:               3.10.20
platform:             Windows-10-10.0.26100-SP0
Torch:                2.5.1+cu121
Torch CUDA build:     12.1
GPU:                  NVIDIA GeForce RTX 4060 Ti
driver:               537.58
VRAM:                 8188 MiB
Isaac Sim:            4.5.0.0
isaaclab metadata:    0.36.23
isaaclab-tasks:       0.10.31
HARL:                 1.0.0
psutil:               5.9.8
CUDA environment:     none present
timeout:              180 seconds
```

## 19. Commands and verification

```powershell
C:\isaacenvs\isaac45_harl\python.exe -m py_compile \
  scripts\environments\test_assignment_phase_b2_v2_d4o_simulationapp_shutdown_observability.py

C:\isaacenvs\isaac45_harl\python.exe -u \
  scripts\environments\test_assignment_phase_b2_v2_d4o_simulationapp_shutdown_observability.py \
  --synthetic-only --json-output <temporary-synthetic-result>

C:\isaacenvs\isaac45_harl\python.exe -u \
  scripts\environments\test_assignment_phase_b2_v2_d4o_simulationapp_shutdown_observability.py \
  --timeout-seconds 180 --json-output <temporary-formal-result>

git diff --check
```

```text
py_compile:                 PASS
synthetic classifier:      PASS 12/12
fresh actual workers:      8
timeouts/kills/survivors:  0/0/0
supervisor cleanup:        PASS 8/8
protected hashes:          PASS 36/36
git diff --check:          PASS (existing line-ending warnings only)
```

## 20. Execution accounting

```text
minimal SimulationApp workers: 8
custom experience:              0
AppLauncher:                    0
MRTA environment:               0
environment reset/step:         0 / 0
HARL:                           0
I0-I6:                          0
optimizer/backward:             0 / 0
training/playback/evaluation:   NOT RUN
checkpoint model operations:    NONE
public route activation:        NONE
original B2-V2:                 NOT RERUN
commit:                         NONE
```

## 21. Causal non-claims

D4-O does not prove:

- that every SimulationApp configuration exits before close returns;
- complete observation of descendants created after O5;
- that exit code 0 alone is clean evidence;
- any new CUDA experience/settings/extension boundary;
- any result for D4 R1-R8;
- that D3 G4 was clean;
- a cuBLAS root cause or repair;
- any MRTA/HARL/I0-I6 defect or readiness state.

## 22. Recommended next action

Stop for GPT independent review. If the proposed contract passes review, the next possible slice is:

```text
B2-V2-D4-R
Restarted Headless Experience Narrow Isolation
Under Reviewed Shutdown Contract
```

Status: `NOT AUTHORIZED`.

Any future D4-R must restart B0 at repeat 1 and must not reuse old D4 evidence as part of its required repeat count. D4-O itself does not authorize D4, R1-R8, G4, original B2-V2, B2-R, repair, warm-up, or training.

## 23. Final classification

```text
classification:
  PHASE-B2-V2-D4O-SIMULATIONAPP-SHUTDOWN-OBSERVABILITY-CONTRACT-COMPLETE-AWAITING-GPT-REVIEW

B2-V2-D4-O:
  COMPLETE / AWAITING GPT REVIEW

shutdown modes:
  IN_PROCESS_CLOSE_RETURN
  EXTERNAL_CLEAN_TERMINATION
  UNSAFE_OR_INCONCLUSIVE_TERMINATION

T0 minimal normal:
  EXTERNAL_CLEAN_TERMINATION 3/3

T1 minimal CUDA:
  CUDA_PASS + EXTERNAL_CLEAN_TERMINATION 3/3

T2 expected diagnostic failure:
  EXPECTED_TEST_FAILURE + EXTERNAL_CLEAN_TERMINATION 2/2

in-process close return:
  0/8

synthetic unsafe classifier:
  PASS 12/12

S15/O6 universal requirement:
  REMOVED FROM PROPOSED CONTRACT

actual SimulationApp behavior:
  UNMODIFIED

old D4:
  STILL STOPPED / NOT RETROACTIVELY PASSED

D3 G4:
  STILL INCONCLUSIVE / UNSAFE

production/framework/HARL:
  UNCHANGED

original B2-V2:
  NOT RERUN / STOPPED / INCOMPLETE

B2-R:
  NOT AUTHORIZED

runtime/policy/learner readiness:
  BLOCKED

training:
  NOT AUTHORIZED

commit:
  NONE
```

Stop here for GPT/user review.
