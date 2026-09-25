# Phase B2-V2-PD2-R5-H One Controlled Formal Reentry Report

Date: 2026-08-31

## Classification

```text
handoff classification:
  PHASE-B2-V2-PD2-R5H-STOP-S6-I5B-RETURNS-AWAITING-GPT-REVIEW
artifact classification:
  PD2-STOP-TERMINAL-TRANSPORT-FAIL
first failing boundary:
  S6_I5B_RETURNS
R5-H:
  STOPPED / FROZEN / AWAITING GPT REVIEW
B2-V2:
  STOPPED / INCOMPLETE
runtime / policy / learner readiness:
  BLOCKED / BLOCKED / BLOCKED
public learned-policy event route:
  DORMANT / BLOCKED
B2-R:
  NOT AUTHORIZED
training:
  NOT AUTHORIZED / NOT RUN
commit:
  NONE
```

This report freezes the one user-authorized R5-H formal reentry. It does not diagnose or repair the failure and does not authorize a retry.

## Starting authority

```text
starting HEAD:       14993dee344bade0230d2eb97b5f22171331f44a
B2-D:                GPT REVIEW PASS / FROZEN
B2-I0 through B2-I6: GPT REVIEW PASS / CLOSED
B2-V1:               GPT REVIEW PASS / CLOSED
B2-V2-PD2-R5-G:      GPT REVIEW PASS / CLOSED
reviewed harness:
  593fad7a980d584954e7a55cecb4a91234ad16e7dc4064c96c75f59e9bcccd34
```

Historical results remain immutable:

- R5-B remains `PD2-STOP-TERMINAL-TRANSPORT-FAIL / S6_TIME_LIMIT`, with S0-S4 retained and S5 not adjudicated in that run.
- R5-E remains `PD2-STOP-STARTUP-EQUIVALENCE-MISMATCH / S0R`; its independent later failure site was the S1 `gym.make(...)` construction path.
- R5-E shutdown remains unsafe/inconclusive. R5-H does not rewrite either artifact.

## Authorized scope and attempt ledger

Exactly one bounded formal attempt was performed using the reviewed test-only harness.

```text
supervisor attempts:          1
formal child workers:         1
AppLauncher lifetimes:        1
formal attempts:              1
retries / repairs:            0 / 0
second formal run:            0
optimizer / backward observed:0 / 0
training/playback/evaluation: NOT RUN
```

No production, HARL, DirectMARLEnv, environment, wrapper, lifecycle, Kit, cache, or harness modification was authorized or performed. No public route was activated.

## Offline preflight

The checks below ran before the formal worker and did not start AppLauncher or initialize CUDA:

```text
artifact target absent:                    PASS
HEAD and harness SHA exact:                PASS
py_compile:                                PASS
--static-only:                             PD2_STATIC_PREFLIGHT_PASS
protected source observations:             56 / 56 exact
STOP taxonomy:                             exact
--r5g-only:                                PASS, 22 / 22
R5-D regression within --r5g-only:         PASS, 38 / 38
--r5d-only:                                PASS, 38 / 38
CUDA initialized before/after offline run: 0 / 0
git diff --check:                           PASS / exit 0
formal worker / AppLauncher in preflight:  0 / 0
```

## Formal command and frozen artifact

Exact interpreter and command:

```text
C:\isaacenvs\isaac45_harl\python.exe

C:\isaacenvs\isaac45_harl\python.exe E:\Project\IsaacLab_HARL\scripts\environments\test_assignment_phase_b2_v2_pd2_production_startup_path_real_interface_smoke.py --json-output C:\Users\33506\AppData\Local\Temp\b2_v2_pd2_r5h_formal_20260831.json --timeout-seconds 300
```

Frozen artifact:

```text
path: C:\Users\33506\AppData\Local\Temp\b2_v2_pd2_r5h_formal_20260831.json
bytes: 959373
SHA-256: 21693caea34957fa72156d45d47ba6fe01f570898ade35e5069bceeb74a849ec
```

Process and output evidence:

```text
outer supervisor / worker exit:  1 / 0
outer / artifact elapsed seconds:118.007 / 115.703
timed out / supervisor kill:     false / false
worker alive after wait:         false
known child survivors:           0
supervisor stdout bytes:         959375
supervisor stdout SHA-256:        2bd23fe061c155f24c12480bf437251359f9898344b05ac1e108cf54320ef9b3
supervisor stderr bytes:         0
supervisor stderr SHA-256:        e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
worker combined output lines:     84
worker combined output SHA-256:   23b0ef9cb808bd72ea7268c59d08736cbf4d47e6c623284f653267522cf1533c
```

The reviewed artifact retained a worker combined-output line count and hash, not an exact worker-output byte count. No byte count is inferred.

## Formal stage matrix

| Boundary | Result | Durable evidence |
|---|---:|---|
| Prelaunch | PASS | manifest, junction, source and shared-state predicates passed |
| S0 | PASS | labels 0-18 persisted |
| S0R | PASS | runtime extension identity passed; complete sets stable |
| S1_ENTER | PASS | `s1_entered`, sequence 47 |
| Gate A | REAL PASS | preconstruction timing contract, sequence 50 |
| Environment construction | REAL PASS | `ScanMobileManipulatorEnv`, sequence 52 |
| Gate B | REAL PASS | postconstruction timing/scale contract, sequence 54 |
| Reset / I1 / I2 | REAL PASS | observation/action shapes, sequence 60 |
| S2 | REAL PASS | installed VCritic current V(t), sequence 62 |
| S3 | REAL PASS | installed HAPPO actor proposal forward, sequence 63 |
| S4 | REAL PASS | first nonterminal physical event step, sequence 64 |
| S5 | REAL PASS | forced continuation second step, sequence 65 |
| S6 | STOP | first failure at `S6_I5B_RETURNS`; no S6 PASS checkpoint |
| Snapshot B | NOT REACHED | no end-to-end parameter mutation comparison |

The last durable PASS is `S5 / continuation_second_step_pass` at sequence 65.

## Gate A, Gate B, and reset

Gate A crossed the reviewed timing fixture:

```text
sim dt / decimation:     0.016666666666666666 / 6
semantic steps / ticks:  3 / 18
episode / control step:  0.3 / 0.1
raw ratio / round / ceil:2.9999999999999996 / 3 / 3
integrality error:       4.440892098500626e-16
absolute / relative tol: 1e-9 / 0
```

Gate B confirmed `max_episode_length=3`, `max_episode_length_s=0.3`, `step_dt=0.1`, scale contract `event_policy_scale_contract_v2`, M/N `3/12`, agents `robot_0..2`, tasks `0..11`, and scene spacing `12.0`.

Real constructor PASS crosses the independent later construction site observed after the historical R5-E artifact. It does not rewrite R5-E or establish a general root cause.

Reset/I1/I2 produced:

```text
E / M / N:                 2 / 3 / 12
device:                    cuda:0
actor observation:         [2, 3, 421]
shared critic observation: [2, 3, 418]
available actions:         [2, 3, 13]
DVM rows:                  6
```

## Real critic, actor, and physical route

S2 invoked installed `harl.algorithms.critics.v_critic.VCritic` on the real I1 input:

```text
input shape / stride:   [2,418] / [418,1]
dtype / device:         torch.float32 / cuda:0
contiguous / finite:    true / true
requires_grad:          false
bytes / elements:       3344 / 836
RNN / mask:             [2,1,256] / [2,1]
input SHA-256:           df1bc7ba60579082acd37b2dc69ecdd54cbc5f99c8d9547beaf54db1fdf39a23
output shape / finite:  [2,1] / true
```

This crosses the original current-VCritic cuBLAS blocker in this single run. It does not prove a resolved cause or that warmup is generally necessary or sufficient.

S3 made one real actor call for each robot over valid environment indices `[0,1]`. Proposals and logprobs were finite. Initial proposal IDs were `[10,4,9]` and `[3,9,4]`.

S4 returned the six-item HARL step interface and one nonterminal physical step. The claim artifact was present, P2 remained sole authority, and controller assignments exactly matched final P2 (`[10,4,9]` and `[3,9,4]`) through `final P2 -> Ak -> controller`. The actor proposal was not controller authority.

## S5 retained real evidence

```text
continuation / forced rows: 6 / 6
policy decision rows:       0
second-step actor calls:    0
proposal present:           false for all rows
original proposal IDs:      -1 for all rows
claim mutation:             false for all rows
interpretation:             CONTINUE_EXISTING for all rows
controller assignment:      exact continuation from P2
```

Assignments remained `[10,4,9]` and `[3,9,4]`. This is not a repeated B1 claim and does not reopen frozen P2/Ak authority.

## S6 partial progress and first failure

The artifact durably retained the timeout critic call-identity DTO:

```text
schema:                       PD2_S6_TIMEOUT_CRITIC_INVOCATION_IDENTITY_V1
call identity pass:           true
second collect start/end:     1 / 3
second collect calls:         2
current V(t) relative/global: 0 / 1
timeout relative/global:      1 / 2
timeout event count:          1
expected/observed timeout:    1 / 1
source order:                 current V(t) then timeout bootstrap
```

Before the failing `require`, source-order audit shows returned checks for: second transition all-done; termination reasons `NONE`/`TIME_LIMIT`; terminal historical sidecars; one pre-ACK observation; empty post-ACK pending slots; historical/current separation; episode-generation advance; the correlation adjudicator; current/post-reset and timeout-bootstrap buffer fields; `finish_rollout()`; and the advantages shape/finite predicate.

These are control-flow predicates returned before failure. They were not assembled into a durable S6 summary/checkpoint, so they are not full S6 PASS or independently durable exact-correlation evidence.

The exact failing check at harness line 4714 was:

```python
tuple(rollout.event_returns_result.returns.shape) == (T + 1, E, 1)
and bool(torch.isfinite(rollout.event_returns_result.returns).all())
```

```text
exception: PD2Stop
message: event returns invalid; first_boundary='S6_I5B_RETURNS'; classification='PD2-STOP-TERMINAL-TRANSPORT-FAIL'
```

The artifact did not separately persist the actual returns shape or finiteness. It proves only that the combined predicate failed; it cannot distinguish shape failure from non-finite values. No diagnosis or repair claim is made.

Therefore S6 terminal transport is not closed; I5b returns are not PASS; full ValueNorm semantics and rollover are not adjudicated; Snapshot B and the final no-training counter bundle were not reached. No retry is permitted in this slice.

## Shutdown and postrun integrity

```text
environment_close / close invoked: RETURNED / true
O4 / O5:                          persisted at sequences 66 / 67
O6 marker/claim:                  absent
supporting shutdown marker:       false
shutdown classification:          EXTERNAL_CLEAN_TERMINATION
safe_shutdown:                    true
worker alive / survivors:         false / 0
timeout / supervisor kill:        false / false
temporary directory remaining:   false
supervisor cleanup:               PASS
```

Artifact reason: `O4/O5 persisted, no O6 claim, process terminated without supervisor intervention, no known survivor`. This applies only to R5-H and does not reinterpret R5-E.

```text
postrun class:              NO_OBSERVED_STATE_CHANGE
eligible / changes:         true / []
reason:                     all bounded rows and protected sources exact
protected set:              57 (56 expected sources plus harness)
protected hashes unchanged: true
harness SHA after run:      593fad7a980d584954e7a55cecb4a91234ad16e7dc4064c96c75f59e9bcccd34
HEAD after run:             14993dee344bade0230d2eb97b5f22171331f44a
```

Shared-state digests before/after both equal `ebdfb41e35d85b55eb7d86acf2ab78b33229ca0bec30623d1c88ec297deb846f`, with 45 linkroot rows, 50 cacheroot rows, 8 metadata rows, 103 total rows, and 43 junction pairs. Cache provenance remains partially attributed; the baseline is not proven restorable; pre-R8 equivalence is not established; contamination risk remains high.

Read-only `nvidia-smi` observations changed from `8188/1089/6873 MiB, 7 processes` to `8188/1122/6840 MiB, 11 processes` on an RTX 4060 Ti, driver 537.58. These are evidence only, not a causal diagnosis.

## Files and non-mutations

Created documentation:

- `AgentRead/202608/20260831/PHASE_B2_V2_PD2_R5H_ONE_CONTROLLED_FORMAL_REENTRY_REPORT.md`
- `AgentRead/202608/20260831/TASK_PROGRESS_ARCHIVE_BEFORE_PD2_R5H_FORMAL_REENTRY_20260831.md`

Updated documentation:

- `AgentRead/TASK_PROGRESS.md`

```text
production changes:           NONE
test harness changes:         NONE
installed HARL changes:       NONE
Kit/cache edits:              NONE
optimizer/backward observed:  0 / 0
training/playback/evaluation: NOT RUN
checkpoint changes:           NONE
commit:                       NONE
```

## Recommended next decision

Freeze R5-H at `PD2-STOP-TERMINAL-TRANSPORT-FAIL / S6_I5B_RETURNS` and submit this report, the unique artifact, and the handoff for GPT independent review.

Do not diagnose, repair, rerun R5-H, retry B2-V2, activate the public route, enter B2-R, or begin training without a new explicit authorization.
