# Phase B2-V2-PD2-R5-B Controlled Formal Re-entry Report

Date: 2026-08-28

Classification: `PD2-STOP-TERMINAL-TRANSPORT-FAIL`

Handoff state: `PHASE-B2-V2-PD2-R5B-CONTROLLED-FORMAL-REENTRY-STOPPED-AT-S6-TIME-LIMIT-AWAITING-GPT-REVIEW`

## 1. Outcome

The one authorized formal PD2 re-entry was executed exactly once. It passed the production startup path, live extension identity, canonical environment/reset interface, installed VCritic forward, real HAPPO actor proposal sampling, and the first physical event step. It then stopped at the first failed predicate:

```text
first boundary: S6_TIME_LIMIT
classification: PD2-STOP-TERMINAL-TRANSPORT-FAIL
exact error: second transition did not terminate all rows
```

The second `route.collect_step()` returned a HARL six-tuple, but its done matrix did not satisfy the harness requirement that every row terminate at that point. The harness stopped before S5 assertions, terminal sidecar/ACK/buffer/GAE assertions, and Snapshot B.

No retry was performed. No repair was attempted.

```text
formal supervisor executions: 1
formal workers:               1
AppLauncher lifetimes:        1
retry:                        0
repair:                       0
```

The worker shut down safely under the reviewed D4-O contract:

```text
shutdown class:     EXTERNAL_CLEAN_TERMINATION
safe shutdown:      true
timeout / kill:     false / false
main survivor:      false
known-child survivor: 0
supervisor cleanup: PASS
postrun integrity:  NO_OBSERVED_STATE_CHANGE
```

This is not a B2-V2 PASS. B2-V2 remains stopped/incomplete.

## 2. Starting checkpoint and authority

```text
branch: main
HEAD:   14993dee344bade0230d2eb97b5f22171331f44a

B2-D:              REVIEW PASS / FROZEN
B2-I0 through I6:  REVIEW PASS / CLOSED
B2-V1:             GPT REVIEW PASS / CLOSED
B2-V2:             STOPPED / INCOMPLETE
B2-V2-PD2-R5-A:    GPT REVIEW PASS / CLOSED
B2-V2-PD2-R5-B:    ONLY AUTHORIZED RUNTIME SLICE
B2-R:              NOT AUTHORIZED
training:          NOT AUTHORIZED
commit:            NONE
```

Authoritative inputs reconciled before execution:

- `AgentRead/TASK_PROGRESS.md`;
- `AgentRead/202608/20260828/PHASE_B2_V2_PD2_R5A_CACHE_BACKED_S0R_PREDICATE_IMPLEMENTATION_AND_STATIC_VERIFICATION_REPORT.md`;
- `AgentRead/202608/20260828/PHASE_B2_V2_PD2_R4_CACHE_BACKED_S0R_AUTHORITY_PREDICATE_REFINEMENT_DESIGN.md`;
- R3 and R2 reports under `AgentRead/202608/20260828/`;
- PD1, D4-CI, and D4-O under `AgentRead/202608/20260827/`;
- the frozen formal harness and official headless `.kit`.

## 3. Scope and changes

Executed only the authorized frozen test harness:

```text
scripts/environments/
  test_assignment_phase_b2_v2_pd2_production_startup_path_real_interface_smoke.py
```

Documentation created/updated:

- this report;
- top-level `AgentRead/TASK_PROGRESS.md`.

```text
harness modification:            NONE
production modification:         NONE
installed HARL modification:     NONE
DirectMARLEnv modification:      NONE
official .kit modification:      NONE
manifest/Junction/cache mutation:NONE
driver/package/environment change:NONE
public route activation:         NONE
optimizer/backward:              0 / 0
training/playback/evaluation:    NOT RUN
checkpoint load/save:            0 / 0
commit:                          NONE
```

## 4. Exact interpreter and frozen hashes

```text
interpreter: C:\isaacenvs\isaac45_harl\python.exe
Python:      3.10.20
HEAD:        14993dee344bade0230d2eb97b5f22171331f44a

formal harness SHA-256:
  e54d31e8b2c613fdb91d7ae0c7a71f43bd00cedf2810375fc35039eeb46cf486

official apps/isaaclab.python.headless.kit SHA-256:
  475bb23c5941fbaaf0186991bf6e5445a267b1e0fd8bbab333cc78dc2e1bc795

R5-A report SHA-256:
  d98c1d3567654dc3ade38808526f83b0db5f4761b567ab986134b2a28406d2d1
R4 report SHA-256:
  30f9233c35d43d22e7bc50e11b61371e1d7be376a0f64c5ad75072665e211ce1
R3 report SHA-256:
  787ea307068a8223031ecdf64ab37e9a351a87461c35cf8a6a166215f788e136
R2 report SHA-256:
  843b392ab0ed81330c89c39c007d524bc1f4cb27eb8df7ba4d47a6a97ad74390
PD1 design SHA-256:
  242b782e92634d746a45b93f814b6e14286e6f46f0b85f953483924c4570fd5e
D4-CI report SHA-256:
  ced5867e7eefdf7618a89861122562a83cc62a488ac77a0a4d0fa67109e32209
D4-O report SHA-256:
  eda1524388d6eff6858a52c7b2815956d8e008c69958452ac2e76ef441b86e70
```

## 5. Preflight

Preflight used no worker, AppLauncher, SimulationApp, Isaac, CUDA runtime forward, HARL forward, environment, or MRTA call.

| Gate | Result |
|---|---|
| exact interpreter | PASS |
| committed HEAD | PASS |
| harness/report/official `.kit` hashes | PASS |
| `py_compile` | PASS |
| frozen static integrity | PASS |
| 45 protected source/report hashes | 45/45 exact |
| shared-state fingerprint | 103/103 exact |
| shared-state SHA-256 | `ebdfb41e35d85b55eb7d86acf2ab78b33229ca0bec30623d1c88ec297deb846f` |
| primary Win32 Junction oracle | 43/43 PASS |
| independent PowerShell oracle | 43/43 PASS |
| dual mapping equality | PASS |
| critical static manifests | PASS |
| startup environment (`LIVESTREAM`, `ENABLE_CAMERAS`, `XR`) | unset / PASS |
| R5-A predicate synthetic matrix | 21/21 PASS |
| R5-A real cache targets | 2/2 exact A/B captures |
| `git diff --check` | PASS; existing line-ending warnings only |

The two R5-A read-only target captures remained exact:

```text
omni.warp.core:
  446 files / 156,115,208 bytes
  path-set: 183bb2674fa2cd2a34dc15b7c59f79d685453afc4b6458c19bff86daab4c7f77
  content:  905ace881e97336901df25692a22bc3fbbfb1e7466c16daec7aaa231a443b8bb

usdrt.scenegraph:
  536 files / 31,105,760 bytes
  path-set: 8e2047e45e5c2af50785c80c9110dde1ed96289980a561416c936d56c97b3db8
  content:  785e278f675786a53b3160b02aeb0abb47c432f3342b6b4e2153e7b753391a43
```

Preflight artifacts:

```text
C:\Users\33506\AppData\Local\Temp\b2_v2_pd2_r5b_preflight_r2a_20260828.json
  SHA-256 f17c90d5e3ccbc18f94b9b874672325bdf158a1e5f3259800f5709770dba6dcf

C:\Users\33506\AppData\Local\Temp\b2_v2_pd2_r5b_preflight_r5a_20260828.json
  SHA-256 2c860761d8f24d72e15330f90c0a14db5351c079a189dadb8820e5a838e7e675
```

## 6. Formal command and artifact identity

One command was issued once:

```powershell
C:\isaacenvs\isaac45_harl\python.exe -u \
  scripts\environments\test_assignment_phase_b2_v2_pd2_production_startup_path_real_interface_smoke.py \
  --json-output C:\Users\33506\AppData\Local\Temp\b2_v2_pd2_r5b_formal_20260828.json
```

Durable supervisor artifacts:

```text
C:\Users\33506\AppData\Local\Temp\b2_v2_pd2_r5b_formal_20260828.json
  length:  915,595 bytes
  SHA-256: dea6e4ba2a55185a051ff77dc749090d328e65f8690434a3abeaf6c402d107db

C:\Users\33506\AppData\Local\Temp\b2_v2_pd2_r5b_formal_20260828_stdout_stderr.txt
  length:  915,597 bytes
  SHA-256: 22b92a34055e49309c484aea99a03264ec77eaaf53d80ebd37550be94697438f
```

The supervisor JSON embeds the complete parsed worker primary result and all 57 checkpoint events. The worker's internal `primary_result.json`, `checkpoints.json`, and temporary directory were supervisor-lifetime artifacts and were deleted by the frozen harness after evidence extraction. They were not recreated or copied because harness modification was forbidden.

Embedded worker stdout/stderr evidence:

```text
line count: 84
SHA-256:   1b850bd7e34b6cb2a206cc9115671425aeaef7066f8a3f02eee7513dd0fe2d56
```

## 7. Stage matrix

| Stage | Result | Durable evidence |
|---|---|---|
| PRELAUNCH | PASS | exact static/source/shared/Junction/manifest/startup gates |
| S0 | PASS | production CUDA warm-up and exact AppLauncher startup config |
| S0R | PASS | stable 67-extension set and all critical runtime identities exact |
| S1 | PASS | real environment, canonical reset, I1/I2 shapes/identity/device/finiteness |
| S2 | PASS | first installed VCritic CUDA forward finite under inference mode |
| S3 | PASS | DVM-only real actor sampling, finite proposal logprobs, mask-valid actions |
| S4 | PASS | first nonterminal physical event step; final P2 -> Ak -> controller exact |
| S5 | NOT ADJUDICATED | second `collect_step()` returned, but S6 done assertion is ordered before S5 assertions |
| S6 | **STOP** | second transition did not terminate all rows at `S6_TIME_LIMIT` |
| Snapshot B | NOT REACHED | no A/B equality claim |
| D4-O | PASS | `EXTERNAL_CLEAN_TERMINATION` |
| POSTRUN | PASS | protected files and bounded shared state unchanged |

First-boundary discipline was preserved. Later S5/S6/Snapshot-B requirements are not inferred from earlier evidence.

## 8. S0 — production startup prefix

```text
device:                    cuda:0
headless:                  true
experience override:       empty
resolved experience:       E:\Project\IsaacLab_HARL\apps\isaaclab.python.headless.kit
resolved experience hash:  475bb23c5941fbaaf0186991bf6e5445a267b1e0fd8bbab333cc78dc2e1bc795
livestream/cameras/xr:      0 / false / false

warm-up:
  no pre-warm-up seed
  zeros [1,1]
  Linear(1,1) forward once
  float32 / cuda:0
  synchronize once
  matmul count 0
  retry count 0
```

The production startup prefix returned normally and AppLauncher was constructed exactly once.

## 9. S0R — live runtime extension identity

```text
complete extension set A: 67 entries
complete extension set B: 67 entries
set A/B SHA-256:
  0f12ff19f4044ec0293a23da1d190759102114e345b063671815a204f3335405
stable: true

critical rows: all PASS
runtime_extension_identity_pass checkpoint: PRESENT
```

Both cache-backed rows passed the frozen R5-A three-layer predicate at live S0R:

```text
usdrt.scenegraph-7.5.1: L1/L2/L3 PASS
omni.warp.core-1.5.0:  L1/L2/L3 PASS
```

This is the first live extension-manager verification of the R5-A cache-backed predicate. Historical R2 remains stopped under its historical predicate and is not retroactively reclassified.

## 10. S1 — environment, reset, I1, and I2

```text
environment: Isaac-Scan-Mobile-Manipulator-Direct-v0
type:        ScanMobileManipulatorEnv
profile:     event_gated_local_mrta
E/M/N/T:     2 / 3 / 12 / 2
device:      cuda:0

actor observation:    [2,3,421]
runner share obs:      [2,3,418]
available actions:     [2,3,13]
DVM policy rows:       6
episode generations:  [0,0]
transition generations:[-1,-1]
P2 publication identity: exact current object
public wrapper route: DORMANT / BLOCKED AS EXPECTED
```

The public fence rejected `wrapper.step()` without changing `common_step_counter`.

## 11. S2 — installed VCritic current V(t)

The first installed `harl.algorithms.critics.v_critic.VCritic` CUDA forward passed:

```text
input shape/stride: [2,418] / [418,1]
contiguous:         true
dtype/device:       torch.float32 / cuda:0
finite:             true
requires_grad:      false
RNN state shape:    [2,1,256]
mask shape:         [2,1]
hidden sizes:       [256,256]
output shape:       [2,1]
output finite:      true
grad enabled:       false
values:             [[1.1743873357772827], [1.1743873357772827]]
actor forward attempts before the first VCritic invocation: 0 by frozen critic-first route order
CUDA/cuBLAS exception: NONE
```

The durable S2 checkpoint itself is emitted after the complete first `collect_step()` returns, so the zero-before-S2 statement is an invocation-order fact, not a checkpoint-time actor-call counter.

Evidence limitation retained explicitly: the frozen `CriticRecorder` persists shape, stride, layout, dtype, device, finiteness, RNN/mask shapes, values, and grad mode, but it does not persist a bounded hash of this current critic input or a direct runtime class-name field. The class and hidden sizes above are source/construction facts; no current-input hash is invented. This omission did not cause the observed runtime STOP, whose first failed predicate was later at S6.

## 12. S3 — real actor sampling

```text
actor forward calls after first collect: [1,1,1]
sampled policy rows:                     6/6
forced rows at reset:                    0
deterministic:                           false
all sampled actions mask-valid:          true
all original proposal logprobs finite:   true
inference mode:                          true
```

Original proposal IDs:

```text
env 0: [10,4,9]
env 1: [3,9,4]
```

Original proposal logprobs remained attached to the stochastic proposals. No resolver winner or effective assignment was substituted as a policy action.

## 13. S4 — first physical event step

```text
HARL result arity:      6
transition:             nonterminal
claim artifact:         present
source store version:   1
post-claim version:     2
admitted version:       2

controller assignment:
  [[10,4,9], [3,9,4]]
expected final P2/Ak:
  [[10,4,9], [3,9,4]]

P2 sole authority:      true
proposal controller authority: false
physical route:         final P2 -> Ak -> controller
```

This provides real actor-forward and first physical learned-route evidence, but not full B2-V2 readiness evidence.

## 14. S5/S6 first failure

The second `route.collect_step()` returned. The first assertion after that return is the S6 TIME_LIMIT assertion:

```python
len(second.harl_step_result) == 6
and bool(second.harl_step_result[3].all())
```

It failed with:

```text
PD2Stop: second transition did not terminate all rows;
first_boundary='S6_TIME_LIMIT';
classification='PD2-STOP-TERMINAL-TRANSPORT-FAIL'
```

Because the S6 done assertion precedes all S5 checks in the frozen harness, the following are not adjudicated:

- second controller assignment equality;
- lifecycle continuation equality;
- forced-row bypass on the second decision;
- absence of repeated claim for existing owners.

The following S6 requirements were not reached:

- exact termination-reason matrix;
- authoritative pre-reset terminal critic sidecar;
- historical/current separation;
- exact runtime ACK lifetime;
- timeout critic exact-once evaluation;
- I5a buffer transport;
- TIME_LIMIT bootstrap fields;
- I5b returns/GAE;
- recorder-only trainer seams;
- event buffer rollover.

## 15. Source-supported timing explanation

The observed S6 result is explained by the frozen harness timing fixture and current DirectMARLEnv arithmetic:

```text
harness constant:
  EPISODE_HORIZON_CONTROL_STEPS = 3

harness assignment:
  cfg.episode_length_s = cfg.sim.dt * cfg.decimation * 3

runtime values:
  cfg.sim.dt = 1/60
  cfg.decimation = 6
  control step = 0.1
  episode_length_s = 0.30000000000000004

DirectMARLEnv:
  max_episode_length = ceil(episode_length_s / control_step)
                     = ceil(3.0000000000000004)
                     = 4

environment timeout predicate:
  episode_length_buf >= max_episode_length - 1
  episode_length_buf >= 3
```

DirectMARLEnv increments `episode_length_buf` before `_get_dones()`. Consequently, the first and second transitions test buffer values 1 and 2; TIME_LIMIT is expected only on the third transition under these exact values. The frozen harness instead requires all rows done immediately after transition two.

This is evidence of a current formal-harness timing/expectation mismatch at S6. It does not establish a frozen I0-I6, lifecycle, P2/Ak, HARL, VCritic, actor, or production environment semantic defect. No constant, horizon, dtype, environment, or harness code was changed in this slice.

## 16. Snapshot and no-training boundary

Snapshot A was captured before route reset:

```text
combined SHA-256:
  a86619feca21131a0a29bfcb4f5b8d628320625aeecdb2db7f24cf41f50a6c79
gradients all none: true
```

Snapshot B was not reached. Therefore this run does not claim Snapshot A/B equality, buffer rollover, or full end-of-rollout mutation proof.

No optimizer or backward call occurred. Training, playback, evaluation, checkpoint load/save, stock runner execution, and public route activation were not run.

## 17. Shutdown evidence

```text
worker diagnostic result:     PD2-STOP-TERMINAL-TRANSPORT-FAIL
worker process exit code:     0
outer supervisor CLI exit:    1 (diagnostic classification)
O4 primary result persisted:  yes
O5 immediately before close:  yes
O6 close-return checkpoint:   absent
environment.close():          RETURNED
SimulationApp close invoked:  yes
timeout / supervisor kill:    false / false
main worker alive after wait: false
known children before close:  0
known survivors:              0
supervisor cleanup:           PASS
temporary directory remaining:false
shutdown marker observed:     false (supporting only; not required)
shutdown result:              EXTERNAL_CLEAN_TERMINATION
safe shutdown:                true
```

Diagnostic STOP and shutdown safety remain orthogonal under D4-O.

## 18. Postrun integrity

```text
protected formal set: 46/46 unchanged
  (45 frozen source/report rows plus the formal harness)

shared state before:
  103 rows
  ebdfb41e35d85b55eb7d86acf2ab78b33229ca0bec30623d1c88ec297deb846f

shared state after:
  103 rows
  ebdfb41e35d85b55eb7d86acf2ab78b33229ca0bec30623d1c88ec297deb846f

postrun class: NO_OBSERVED_STATE_CHANGE
changes:       0
```

GPU observations were supporting only:

```text
GPU/driver: NVIDIA GeForce RTX 4060 Ti / 537.58
VRAM total: 8188 MiB
before used/free: 1502 / 6460 MiB
after used/free:  1380 / 6582 MiB
temperature:      25 C before and after
```

Memory values are not used as a causal claim.

## 19. Claims and non-claims

This run establishes:

- the reviewed production CUDA warm-up and exact headless AppLauncher path execute once;
- the R5-A cache-backed predicate passes live S0R for both reviewed cache rows;
- canonical real Isaac reset/I1/I2 passes at E=2/M=3/N=12/cuda:0;
- installed VCritic current V(t) passes on real I1 input;
- real HAPPO actor forward is reached and passes the first DVM sampling contract;
- the first learned-policy physical event step passes P2 -> Ak -> controller authority checks;
- the earliest formal STOP is S6 TIME_LIMIT expectation after the second transition;
- shutdown and postrun shared/protected integrity are safe and exact.

This run does not establish:

- S5 continuation/forced-row semantics on the second transition;
- terminal I4/I5a/I5b, ACK, TIME_LIMIT bootstrap, returns, or GAE;
- Snapshot A/B equality;
- full B2-V2 PASS;
- public route readiness;
- runtime, policy, learner, or training readiness;
- a need to change DirectMARLEnv or frozen lifecycle contracts;
- a cuBLAS root cause, general repair, or pre-R8 equivalence;
- training performance or checkpoint compatibility.

## 20. Recommended next decision

Stop for GPT independent review.

The next candidate should be a separately authorized, test-only design/audit slice for the S6 formal-fixture timing contract. It should decide how the bounded two-slot rollout and intended terminal control step are represented without changing DirectMARLEnv, production episode semantics, frozen lifecycle termination priority, or learner contracts.

That review should also resolve the frozen-harness evidence limitations before any new formal run:

- no separately persisted bounded S2 current-input fingerprint;
- worker primary/checkpoint files survive only as embedded supervisor JSON after mandated cleanup;
- Snapshot B and all terminal transport evidence remain absent because this run stopped at the first S6 predicate.

No retry, harness repair, production change, B2-R entry, public activation, or training is authorized by this recommendation.

## 21. Final status

```text
classification:
  PD2-STOP-TERMINAL-TRANSPORT-FAIL

handoff state:
  PHASE-B2-V2-PD2-R5B-CONTROLLED-FORMAL-REENTRY-STOPPED-AT-S6-TIME-LIMIT-AWAITING-GPT-REVIEW

first boundary:
  S6_TIME_LIMIT

formal execution:
  EXACTLY ONE SUPERVISOR / ONE WORKER / ONE APPLAUNCHER LIFETIME

S0 / S0R / S1 / S2 / S3 / S4:
  PASS

S5:
  NOT ADJUDICATED

S6:
  STOP AT TIME_LIMIT DONE-MATRIX ASSERTION

Snapshot B:
  NOT REACHED

D4-O / postrun:
  SAFE / PASS

B2-V2:
  STOPPED / INCOMPLETE

production / HARL / harness changes:
  NONE / NONE / NONE

optimizer / backward:
  0 / 0

training/playback/evaluation:
  NOT RUN

runtime/policy/learner readiness:
  BLOCKED

public route:
  DORMANT / BLOCKED

B2-R:
  NOT AUTHORIZED

commit:
  NONE
```

Stop here for GPT/user review.
