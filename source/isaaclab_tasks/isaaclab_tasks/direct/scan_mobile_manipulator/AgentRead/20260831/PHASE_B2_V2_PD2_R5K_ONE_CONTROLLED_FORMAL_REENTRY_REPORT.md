# Phase B2-V2-PD2-R5-K One Controlled Formal Reentry Report

## 1. Classification

```text
classification:
  PHASE-B2-V2-PD2-R5K-ONE-CONTROLLED-FORMAL-REENTRY-PASS-AWAITING-GPT-REVIEW

formal reentry:
  PASS

formal supervisor attempts:
  1

formal workers:
  1

AppLauncher lifetimes:
  1

retry:
  0

repair:
  0

B2-V2:
  INCOMPLETE / AWAITING GPT CLOSURE

B2-R:
  NOT AUTHORIZED

training:
  NOT AUTHORIZED

commit:
  NONE
```

This is the R5-K slice classification. The frozen harness retained its existing raw success label:

```text
PHASE-B2-V2-PD2-R2-CURRENT-PRODUCTION-STARTUP-REAL-INTERFACE-VALIDATION-PASS-AWAITING-GPT-REVIEW
```

The R5-K classification above is the authorized phase-level interpretation of that one successful formal artifact. The harness was not renamed or modified.

## 2. Authoritative starting point

- Starting HEAD: `14993dee344bade0230d2eb97b5f22171331f44a`
- R5-J: GPT REVIEW PASS / CLOSED.
- Reviewed harness SHA-256: `28b98443c0e0612101738c9b32742416fe00ccb6cc0d391f174d59d816bee8e3`.
- B2-V2 before R5-K: STOPPED / INCOMPLETE.
- Historical R5-H first failure: `PD2-STOP-TERMINAL-TRANSPORT-FAIL` at `S6_I5B_RETURNS`.
- Historical last durable R5-H checkpoint: `S5`.
- R5-I frozen returns contract:
  - event result: `[T,E,1]`;
  - critic-buffer storage: `[T+1,E,1]`;
  - learner training slice: `returns[:-1]`, exactly `[T,E,1]`;
  - training slice exactly equals the event result and does not alias it;
  - the final `[E,1]` slot is diagnostic/storage-only and is not a learner target.

The current evidence does not reopen or revise the frozen P2/Ak/B1, proposal/effective-assignment, continuation, terminal/current separation, or learner semantics.

## 3. Authorized scope and execution boundary

R5-K authorized one controlled formal reentry only:

```text
one supervisor
-> one worker
-> one AppLauncher / SimulationApp lifetime
-> one bounded current-production startup/interface validation
-> stop
```

The run used the dormant learned-policy composition and bounded two-transition evidence path. It did not authorize a public route, a rollout, training, playback, evaluation, checkpoint work, repair, retry, or B2-R.

## 4. Files created or updated

Created documentation:

- `AgentRead/20260831/PHASE_B2_V2_PD2_R5K_ONE_CONTROLLED_FORMAL_REENTRY_REPORT.md`
- `AgentRead/20260831/TASK_PROGRESS_ARCHIVE_BEFORE_PD2_R5K_FORMAL_REENTRY_20260831.md`

Updated documentation:

- `AgentRead/TASK_PROGRESS.md`

Production changes: **NONE**.

Harness changes: **NONE**.

Installed HARL changes: **NONE**.

Kit, extension, registry, cache, driver, package, and environment changes: **NONE**.

The TASK_PROGRESS archive preserves the pre-R5-K text. Its byte hash differs from the source TASK_PROGRESS hash because `apply_patch` normalized Markdown line endings; it is a content snapshot, not a claimed byte-for-byte copy.

## 5. Exact interpreter and device evidence

- Interpreter: `C:\isaacenvs\isaac45_harl\python.exe`
- Python: `3.10.20`
- Device: `cuda:0`
- GPU: `NVIDIA GeForce RTX 4060 Ti`
- Driver: `537.58`
- Reported GPU memory before: total `8188 MiB`, used `1391 MiB`, free `6571 MiB`.
- Reported GPU memory after: total `8188 MiB`, used `1390 MiB`, free `6572 MiB`.

The one formal run used the reviewed harness at:

```text
scripts/environments/
test_assignment_phase_b2_v2_pd2_production_startup_path_real_interface_smoke.py
```

## 6. Preflight matrix

Each required harness preflight was executed exactly once in this R5-K slice. No failed preflight was rerun.

| Gate | Result | Runtime counters |
|---|---|---|
| exact interpreter identity | PASS | expected interpreter exact |
| `py_compile` to a temp `.pyc` | PASS | no import/runtime execution |
| `--static-only` | PASS | worker `false` |
| `--r5d-only` | PASS | worker/AppLauncher/Isaac/CUDA runtime `0` |
| `--r5g-only` | PASS | worker/AppLauncher/Isaac/CUDA runtime `0` |
| `--r5j-only` | PASS | worker/AppLauncher/Isaac/CUDA runtime `0` |
| `git diff --check` | PASS, exit `0` | only existing LF/CRLF warnings |
| 59 frozen source/report hashes | PASS | zero mismatch |
| reviewed harness hash | PASS | exact reviewed SHA |
| R5-J report hash | PASS | exact frozen SHA |

R5-J pure/static evidence again confirmed the frozen result/storage/training-slice schema without initializing CUDA runtime.

## 7. Formal invocation and artifact identity

The sole formal supervisor invocation was equivalent to:

```powershell
C:\isaacenvs\isaac45_harl\python.exe -u `
  scripts\environments\test_assignment_phase_b2_v2_pd2_production_startup_path_real_interface_smoke.py `
  --json-output C:\Users\33506\AppData\Local\Temp\b2_v2_pd2_r5k_formal_20260831.json `
  --timeout-seconds 300
```

Formal artifacts:

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `b2_v2_pd2_r5k_formal_20260831.json` | 1,003,916 | `9cec63231b92c9491b0ec29f73ec0be20de67c93be55fb3269dd5cf50694bae6` |
| supervisor stdout | 1,003,918 | `155cec83e0a7903e7918fb5c5b9317522255ddde4f7b84a03faf592f5d3f4eec` |
| supervisor stderr | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |

The worker-combined stdout/stderr embedded by the supervisor contained 73 lines with SHA-256 `694be280cae65d0b7c5d763238988d1f1a787912de835e61efe19df3dae3a19f`.

## 8. One-attempt proof

- Supervisor process exit code: `0`.
- Formal worker count: `1`.
- Formal AppLauncher lifetime count: `1`.
- Timeout: `false`.
- Supervisor kill used: `false`.
- Worker alive after wait: `false`.
- Worker primary result valid: `true`.
- Temporary worker directory remaining: `false`.
- Supervisor cleanup: PASS.
- Retry count: `0`.
- Repair count: `0`.
- Second formal run: **NOT RUN**.

Elapsed supervisor time was approximately `168.453 s`.

## 9. Formal stage matrix

| Stage | Durable result | Key evidence |
|---|---|---|
| S0 | PASS | Torch CUDA warmup completed before AppLauncher; one `Linear(1,1)` forward, one synchronize, no retry |
| S0R | PASS | complete extension set stable; all critical runtime identity rows passed |
| S1 | PASS | real `E=2/M=3/N=12`, environment construction/reset, I1/I2 shapes and horizon contracts passed |
| S2 | PASS | installed real VCritic current `V(t)` forward passed on `[2,418]` CUDA input |
| S3 | PASS | real DVM-only actor forward passed for all 3 agent rows |
| S4 | PASS | first physical event step passed; `final P2 -> Ak -> controller` preserved |
| S5 | PASS | second-step forced continuation passed with zero actor resampling |
| S6 capture | PASS | `i5b_returns_evidence_captured` durably emitted at the existing I5b boundary |
| S6 adjudication | PASS | `time_limit_terminal_transport_returns_pass` durably emitted |
| SNAPSHOT_B | PASS | parameter/optimizer/ValueNorm snapshot exact match; gradients all `None` |
| O4/O5 | PASS | primary result persisted and pre-close marker persisted |
| shutdown | PASS | external clean termination, no supervisor intervention, no known survivor |

No earlier stage failed. Therefore the formal first boundary is `PASS`; there is no R5-K failure detail.

## 10. S1 real reset/interface evidence

- Environment: `Isaac-Scan-Mobile-Manipulator-Direct-v0`.
- Environment type: `ScanMobileManipulatorEnv`.
- Profile: `event_gated_local_mrta`.
- `E=2`, `M=3`, `N=12`, `T=2`.
- Actor observation shape: `[2,3,421]`.
- Shared/critic observation shape: `[2,3,418]`.
- Available-actions shape: `[2,3,13]`.
- DVM rows: `6`.
- Episode horizon: `3` steps, exactly matching the reviewed semantic horizon contract.
- Initial episode generations: `[0,0]`.
- Initial transition generations: `[-1,-1]`.

## 11. S2 installed VCritic evidence

The first real current-value forward reached and passed the boundary that originally blocked B2-V2:

- runtime class: `harl.algorithms.critics.v_critic.VCritic`;
- input shape: `[2,418]`;
- stride: `[418,1]`;
- dtype: `torch.float32`;
- device: `cuda:0`;
- contiguous: `true`;
- finite: `true`;
- requires grad: `false`;
- output shape: `[2,1]`;
- output finite: `true`;
- grad enabled: `false`.

This run did not reproduce the historical VCritic/cuBLAS failure. The evidence is limited to the current reviewed startup path; it does not establish a cuBLAS root cause, necessity claim, general fix, or pre-R8 behavior.

## 12. S3 actor proposal evidence

- Exactly one forward call per installed actor: `[1,1,1]`.
- Each actor saw batch size `2` and valid env rows `[0,1]`.
- Actor observation shape: `[2,421]` per actor.
- Available-action shape: `[2,13]` per actor.
- Original proposals and finite original proposal log-probabilities were retained.
- No forced row was treated as a stochastic policy decision at S3.
- The proposal remained a proposal and was not controller authority.

## 13. S4/S5 proposal, authority, and continuation evidence

S4 established:

- first physical event step returned normally;
- claim artifact present;
- controller assignment exactly matched final current P2;
- P2 was sole ownership/effective-assignment authority;
- physical route was `final P2 -> Ak -> controller`;
- actor proposal was not controller authority.

S5 established the frozen continuation semantics:

- all 6 rows were `FORCED_CONTINUATION_ROW`;
- all 6 policy-decision rows were false;
- actor batch sizes were zero for all 3 actors;
- proposal-present mask was false for all rows;
- original proposal IDs were `-1` for all rows;
- interpretations were `CONTINUE_EXISTING` for all rows;
- no row performed a new claim mutation;
- controller assignments exactly continued the current P2 task assignments.

Thus `EXECUTING` continuation was not converted into repeated stochastic task selection.

## 14. S6 terminal transport and TIME_LIMIT evidence

The bounded run reached the real terminal/autoreset transport path:

- old episode generations: `[0,0]`;
- new episode generations: `[1,1]`;
- terminal slots before ACK: `2`;
- terminal slots after safe historical copy and ACK: `0`;
- termination reason encoded TIME_LIMIT for both environments;
- timeout bootstrap: `true`;
- pre-reset critic fingerprint: `c120c16dd20e4c7138e841ba72f2b0f863bef25c09f313864c50650bf8c0d23a`;
- post-reset current fingerprint: `df1bc7ba60579082acd37b2dc69ecdd54cbc5f99c8d9547beaf54db1fdf39a23`;
- the two fingerprints were distinct and retained their pre-reset/post-reset roles;
- stock HARL `compute_returns` calls: `0`.

The timeout critic call identity and exact-input correlation both passed:

- second collect call order: current `V(t)` then timeout bootstrap;
- exactly one timeout critic call;
- expected and observed shape: `[2,418]`;
- expected and observed device: `cuda:0`;
- expected and observed dtype: `torch.float32`;
- expected and observed byte count: `3344`;
- expected and observed SHA-256: `c120c16dd20e4c7138e841ba72f2b0f863bef25c09f313864c50650bf8c0d23a`;
- exact tensor comparison executed and passed.

## 15. I5b returns contract adjudication

The source-faithful I5b observer returned:

```text
classification:
  S6_I5B_RETURNS_SOURCE_FAITHFUL_PASS

failed_details:
  []

primary_failure_detail:
  null
```

Exact contract evidence:

| Layer | Expected | Actual | Result |
|---|---|---|---|
| event producer result | `[2,2,1]` | `[2,2,1]` | PASS |
| critic-buffer storage | `[3,2,1]` | `[3,2,1]` | PASS |
| learner training slice `returns[:-1]` | `[2,2,1]` | `[2,2,1]` | PASS |
| final storage slot | `[2,1]` | `[2,1]` | diagnostic-only PASS |
| advantages | `[2,2,1]` | `[2,2,1]` | PASS |

Additional exact properties:

- result finite: `true`;
- training slice finite: `true`;
- training slice exactly equals result: `true`;
- training slice does not alias result: `true`;
- buffer commit performed: `true`;
- all event slots complete: `true`;
- final slot written by event compute: `false`;
- final slot consumed by learner: `false`;
- final slot all finite and zero: `true`;
- ValueNorm enabled: `true`;
- producer failure code/stage: `null`.

This is the first durable formal evidence that crosses the historical R5-H blocker at `S6_I5B_RETURNS`. It does not erase or rewrite the R5-H STOP artifact; that artifact remains authoritative historical evidence for its own run.

## 16. Learner boundary and no-training proof

- critic trainer recorder calls: `1`;
- actor trainer recorder calls: `1`;
- buffer rollover: `true`;
- actor optimizer steps: `0`;
- critic optimizer steps: `0`;
- backward calls: `0`;
- ValueNorm updates: `0`;
- stock HAPPO train calls: `0`;
- runner run calls: `0`;
- checkpoint load/save: `0/0`;
- training/playback/evaluation: `0/0/0`.

Snapshot B exactly matched Snapshot A for actor, critic, optimizer, and ValueNorm state, and all gradients remained `None`.

## 17. Shutdown, shared state, and protected integrity

Shutdown classification:

```text
EXTERNAL_CLEAN_TERMINATION
safe_shutdown: true
```

The environment close returned, O4/O5 were durable, the process ended without supervisor kill, no known child survived, and the temporary supervisor directory was removed.

Shared-state post-run classification:

```text
NO_OBSERVED_STATE_CHANGE
eligible: true
```

- Shared-state SHA before/after: `ebdfb41e35d85b55eb7d86acf2ab78b33229ca0bec30623d1c88ec297deb846f`.
- Counts before/after: linkroot `45`, cacheroot `50`, metadata `8`, total `103`, junction pairs `43`.
- Harness-internal protected before/after map: exact match.
- External post-run rehash of 59 frozen source/report files: zero mismatch.
- Reviewed harness post-run SHA: exact.
- R5-J report post-run SHA: exact.

## 18. Readiness and non-claims

This R5-K PASS is formal real-interface evidence, not automatic phase closure.

```text
B2-V2:
  INCOMPLETE / AWAITING GPT CLOSURE

runtime readiness:
  BLOCKED / AWAITING GPT DECISION

policy readiness:
  BLOCKED / AWAITING GPT DECISION

learner readiness:
  BLOCKED / AWAITING GPT DECISION

public learned-policy route:
  DORMANT / BLOCKED

B2-R:
  NOT AUTHORIZED

training/playback/evaluation:
  NOT AUTHORIZED / NOT RUN
```

No claim is made about training convergence, policy quality, arbitrary rollouts, public-route readiness, variable cardinality, or checkpoint compatibility.

## 19. Recommended next decision

Stop for GPT formal review of the sole R5-K artifact and this report. GPT/user may decide whether the evidence closes B2-V2 and changes any readiness gate. Do not rerun R5-K, do not repair the already-passing harness, do not activate the public route, and do not enter B2-R or training without separate authorization.

