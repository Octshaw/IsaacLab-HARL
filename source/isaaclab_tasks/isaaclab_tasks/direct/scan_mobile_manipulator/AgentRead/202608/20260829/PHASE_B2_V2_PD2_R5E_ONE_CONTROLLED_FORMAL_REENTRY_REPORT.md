# Phase B2-V2-PD2-R5-E — One Controlled Formal Reentry Report

Date: 2026-08-29

Formal classification: `PD2-STOP-STARTUP-EQUIVALENCE-MISMATCH`

Handoff classification: `PHASE-B2-V2-PD2-R5E-STOP-STARTUP-EQUIVALENCE-MISMATCH-AT-S0R-AWAITING-GPT-REVIEW`

## 1. Starting authority

Committed checkpoint HEAD remained `14993dee344bade0230d2eb97b5f22171331f44a`. B2-D remained reviewed/frozen; B2-I0 through B2-I6 and B2-V1 remained reviewed/closed; B2-V2 remained `STOPPED / INCOMPLETE`. R5-B remained the immutable historical formal STOP at `S6_TIME_LIMIT`; R5-C and the final R5-D/R5-D-TR/R5-D-TR2 test-only contract were the reviewed authority for this one reentry.

R5-E authorized exactly one real formal supervisor, one child worker, one AppLauncher lifetime, and no retry or repair-and-rerun. It did not authorize production, I0-I6, DirectMARLEnv, installed HARL, Kit/cache, public-route, optimizer, backward, training, playback, evaluation, checkpoint, or commit changes.

## 2. Scope and one-run discipline

The reviewed harness was used without modification:

```text
scripts/environments/test_assignment_phase_b2_v2_pd2_production_startup_path_real_interface_smoke.py
SHA-256: 96c220b895b5410d1aca37bfde4f97f09c5e79da785a2b8377642a4c3de9c6d5
```

Formal execution ledger:

```text
formal supervisor attempts:       1
formal child workers:             1
AppLauncher lifetimes:            1
formal retries:                   0
repair-and-rerun:                 0
second formal run:                0
```

The first formal failure was retained. No command capable of starting another formal worker was issued afterward.

## 3. Preflight

The exact interpreter was `C:\isaacenvs\isaac45_harl\python.exe`.

Before formal launch, and without AppLauncher/CUDA runtime:

```text
py_compile:                        PASS / EXIT 0
--static-only:                     PASS / PD2_STATIC_PREFLIGHT_PASS
protected frozen set:             53/53 EXACT
git diff --check:                 PASS / EXIT 0
--r5d-only:                       PASS
R5-D synthetic matrix:            A-AL 38/38 PASS
CUDA initialized before/after:    0 / 0
worker/formal execution count:    0 / 0
formal artifact pre-existed:      false
preflight ready:                  true
```

The preflight did not predict the subsequently observed real constructor-time scale-contract mismatch.

## 4. Formal command and persisted evidence

The supervisor invoked the reviewed harness once with a 300-second bound and one unique JSON output path:

```text
C:\isaacenvs\isaac45_harl\python.exe -u
  scripts/environments/test_assignment_phase_b2_v2_pd2_production_startup_path_real_interface_smoke.py
  --timeout-seconds 300
  --json-output C:\Users\33506\AppData\Local\Temp\b2_v2_pd2_r5e_formal_20260829.json
```

Outer supervisor observation:

```text
started:                           2026-08-29T15:18:16.7568801+08:00
ended:                             2026-08-29T15:23:20.3822982+08:00
outer elapsed:                     303.6254181 s
supervisor exit:                   1
artifact exists:                  true
artifact bytes:                   904764
artifact SHA-256:                 73bce8e0392fa4069c8d0f98d519980bfba64a8675ffe0caeeffabf3834ba382
captured supervisor stdout bytes: 889538
captured supervisor stdout SHA:   f26899c05c869011697d2f147445e6e1467aaa836247334b3ce8e59419910d07
```

Artifact-internal elapsed time was `301.812 s`. The child worker's bounded stdout/stderr contained 74 lines with SHA-256 `3941d68b469fd131dbfa05697aaf421f710d51a81994f7bdfa36100839b26c70`.

## 5. Stage matrix

| Stage | New R5-E real-runtime result | Durable evidence |
|---|---|---|
| O0 | PASS | one worker started; PID 11316 |
| S0 | PASS | CUDA availability, `cuda:0` selection, one tiny Linear forward/synchronize, AppLauncher return, and startup config validation completed |
| S0R | PASS as a predicate stage | complete extension snapshots A/B were equal; all critical runtime identity rows passed; `runtime_extension_identity_pass` persisted |
| S1 | STOP during `gym.make(...)` | installed HARL seed checkpoint persisted, then derived environment construction raised the scale-contract error before `environment_constructed` |
| reset | NOT REACHED | reset count 0 |
| S2 current VCritic | NOT REACHED | no Snapshot A/current critic artifact |
| S3 actor | NOT REACHED | no actor call |
| S4 first physical step | NOT REACHED | environment step count 0 |
| S5 continuation | NOT ADJUDICATED | no S5 artifact |
| S6 terminal transport | NOT ADJUDICATED | no S6 or timeout-call artifact |
| Snapshot B | NOT REACHED | absent |

The artifact's authoritative `first_boundary` and `active_stage` are both `S0R`. That field is retained exactly. Source/traceback evidence narrows the actual exception site to the following S1 environment-construction call, after the durable S0R PASS and `installed_harl_seed_complete` checkpoint. Therefore this report does not reinterpret the result as a failed extension-identity predicate.

## 6. First formal failure

```text
classification:
  PD2-STOP-STARTUP-EQUIVALENCE-MISMATCH

first_boundary:
  S0R

exception type:
  AssignmentEventProfileSchemaV2ContractError

exception:
  episode horizon must be an integral number of physical control steps;
  failure_code='nonintegral_episode_horizon';
  stage='scale_validation';
  expected='integral episode_time_limit / control_step';
  actual=2.5;
  contract_version='assignment_event_profile_schema_contract_v2'
```

The traceback is:

```text
formal harness run_real_smoke -> gym.make
-> ScanMobileManipulatorEnv.__init__
-> build_event_policy_scale_contract_v2
-> fail-closed nonintegral_episode_horizon
```

This first failure remains primary. The later timeout/kill and shutdown classification do not replace it.

## 7. Test-fixture/production-contract boundary

Static source inspection after the one run establishes only the immediate interface conflict:

```text
reviewed test-only harness:
  PD2_TIMEOUT_FIXTURE_RATIO = 2.5
  episode_length_s = control_step * 2.5
  required ceil-style max_episode_length = 3

frozen production scale contract:
  horizon_ratio = episode_time_limit / control_step
  horizon must be integral within abs_tol 1e-9
```

Thus the reviewed R5-D strict-interior `2.5` fixture is rejected by the production event-profile scale contract before the formal environment object is completed. This is sufficient evidence for a test-fixture/production-contract boundary mismatch. It is not authorization to change either side and is not evidence that the production contract, DirectMARLEnv, lifecycle runtime, HARL, critic, or actor is defective.

## 8. S0/S0R evidence

The unique run newly confirmed:

```text
tiny CUDA allocation/Linear/sync:  PASS
AppLauncher returned:              PASS
resolved experience:               apps/isaaclab.python.headless.kit
experience SHA-256:                475bb23c5941fbaaf0186991bf6e5445a267b1e0fd8bbab333cc78dc2e1bc795
extension Snapshot A count/SHA:    67 / 0f12ff19f4044ec0293a23da1d190759102114e345b063671815a204f3335405
extension Snapshot B count/SHA:    67 / 0f12ff19f4044ec0293a23da1d190759102114e345b063671815a204f3335405
complete extension set stable:     true
critical runtime identity:         PASS
```

These are bounded R5-E real-runtime observations. They do not establish pre-R8 equivalence or a cuBLAS root cause/repair.

## 9. Environment, critic, actor, and physical-step evidence

Isaac logged base scene creation and simulation setup inside `gym.make`, but the derived constructor then raised before the harness could assign the returned environment and persist `environment_constructed`. Authoritative counters therefore remain:

```text
formal environment constructed:    false
environment reset:                 0
environment step:                  0
current VCritic forward:            NOT REACHED
actor forward:                      NOT REACHED
physical learned-policy step:       NOT REACHED
terminal transport/I4/I5a/I5b:      NOT REACHED
```

No new R5-E claim is made for I1/I2, VCritic, actor, P2 -> Ak -> controller, S5, S6, TIME_LIMIT, ACK, buffer insertion, GAE, or rollover.

## 10. Historical evidence remains separate

Historical R5-B remains exactly:

```text
classification:                    PD2-STOP-TERMINAL-TRANSPORT-FAIL
first boundary:                    S6_TIME_LIMIT
S0/S0R/S1/S2/S3/S4:               historical real PASS
S5:                                not adjudicated
terminal I4/I5a/I5b:              not reached
shutdown/postrun:                  safe / pass
```

The new R5-E STOP neither erases nor retroactively modifies those historical observations. Conversely, historical R5-B PASS evidence cannot be substituted for missing R5-E stages.

## 11. Test-only synthetic evidence remains separate

R5-D-TR2 preflight retained A-AL `38/38 PASS` with zero CUDA initialization. That evidence validates only the reviewed test-only timing/evidence/timeout-call oracle implementation. It is not real S5/S6 or terminal learner evidence.

## 12. Shutdown and supervisor cleanup

After the primary result was persisted, the worker emitted `O5: immediately_before_SimulationApp_close` but did not return within the 300-second supervisor bound:

```text
worker close invoked:               true
supporting close-return marker:     absent
timed out:                          true
supervisor process-tree kill used:  true
worker alive after wait:            false
known child survivors:              0
supervisor cleanup:                 PASS
temporary directory remaining:      false
shutdown class:                     UNSAFE_OR_INCONCLUSIVE_TERMINATION
safe shutdown:                      false
```

The supervisor's kill was bounded cleanup after the already-persisted primary error. It is a secondary shutdown result and does not override the first formal classification. No environment or SimulationApp process was left alive according to the bounded process-tree evidence.

## 13. Postrun integrity

```text
postrun class:                      NO_OBSERVED_STATE_CHANGE
postrun eligible:                   true
observed shared-state changes:      0
shared-state before SHA-256:        ebdfb41e35d85b55eb7d86acf2ab78b33229ca0bec30623d1c88ec297deb846f
shared-state after SHA-256:         ebdfb41e35d85b55eb7d86acf2ab78b33229ca0bec30623d1c88ec297deb846f
protected frozen rows:              53/53 exact
formal aggregate protected entries:54/54 unchanged, including the reviewed harness
harness SHA-256 after run:          96c220b895b5410d1aca37bfde4f97f09c5e79da785a2b8377642a4c3de9c6d5
```

Supporting GPU observations:

```text
GPU / driver:                       NVIDIA GeForce RTX 4060 Ti / 537.58
VRAM total:                         8188 MiB
before used/free:                   1642 / 6320 MiB
after used/free:                    1619 / 6343 MiB
temperature before/after:           22 C / 25 C
```

These memory readings are not used for causal inference.

## 14. No mutation and no training

```text
production changes:                 NONE
I0-I6 changes:                      NONE
DirectMARLEnv changes:              NONE
installed HARL changes:             NONE
Kit/Junction/cache changes:         NONE
formal harness changes:             NONE
optimizer calls:                    0
backward calls:                     0
training/playback/evaluation:       NOT RUN
checkpoint load/save:               NOT RUN
public route activation:            0
B2-R:                               NOT AUTHORIZED
commit/stage:                        NONE / NONE
```

Only this report, the required pre-R5-E TASK_PROGRESS archive, and the concise TASK_PROGRESS update are documentation changes in this slice.

## 15. Frozen lifecycle and policy boundaries

No result in this run reopens the frozen authority chain:

- current P2 remains sole lifecycle/ownership truth;
- actor action remains a proposal and proposal logprob remains tied to that original proposal;
- M1/B1 remains the only ownership mutation transaction;
- physical control remains final P2 -> Ak -> controller;
- continuation is not a repeated claim;
- terminal historical data remains separate from current post-autoreset state;
- runtime ACK remains distinct from learner consumption/buffer insertion;
- the event-profile public route remains dormant/default-off.

## 16. Historical shared-state limitations retained

```text
cache provenance:                   PARTIALLY_ATTRIBUTED
baseline restoration:              NOT_PROVABLY_RESTORABLE
pre-R8 runtime equivalence:         NOT_ESTABLISHED
future diagnostic contamination:   HIGH
```

The exact R5-E pre/post fingerprint proves no newly observed change during this bounded run. It does not reconstruct a pre-R8 baseline or clear the historical limitations.

## 17. Claims and non-claims

This R5-E run establishes only:

- exact one-supervisor/one-worker/one-AppLauncher execution discipline;
- S0 and the S0R runtime extension-identity predicate completed in the current shared state;
- the first formal STOP was the recorded `PD2-STOP-STARTUP-EQUIVALENCE-MISMATCH` at artifact boundary `S0R`;
- the concrete exception arose during `gym.make` because the test-only `2.5` timing fixture violates the production integral-horizon scale contract;
- no reset, critic, actor, physical step, terminal learner path, optimizer, or backward occurred;
- the worker was terminated by bounded supervisor cleanup with no observed survivors or shared/protected-state changes.

It does not establish B2-V2 PASS, real S5/S6, runtime/policy/learner readiness, public-route readiness, training readiness, a production defect, a lifecycle defect, a cuBLAS root cause, or a safe shutdown.

## 18. Recommended next decision

Stop for GPT independent formal review. The next candidate, only if separately authorized, is a test-only design/reconciliation slice for the contradiction between the reviewed strict-interior `2.5` timeout fixture and the frozen production integral-horizon contract. It should also decide whether the harness must set a more precise active boundary before `gym.make`, while preserving the existing formal first-failure record.

Do not repair or rerun R5-E under this authorization. Do not change production episode semantics, DirectMARLEnv, lifecycle termination, I0-I6, HARL, Kit/cache, or the public route. Any future executable reentry requires a new reviewed harness identity and separate explicit authorization.

## 19. Final state

```text
formal classification:
  PD2-STOP-STARTUP-EQUIVALENCE-MISMATCH

handoff classification:
  PHASE-B2-V2-PD2-R5E-STOP-STARTUP-EQUIVALENCE-MISMATCH-AT-S0R-AWAITING-GPT-REVIEW

first boundary:
  S0R (artifact authority; exception occurred during subsequent S1 gym.make)

last durable positive runtime evidence:
  S0R runtime_extension_identity_pass
  S1 installed_harl_seed_complete

formal execution:
  EXACTLY ONE SUPERVISOR / ONE WORKER / ONE APPLAUNCHER LIFETIME

retry / repair-and-rerun:
  0 / 0

shutdown / postrun:
  UNSAFE_OR_INCONCLUSIVE_TERMINATION / NO_OBSERVED_STATE_CHANGE

B2-V2:
  STOPPED / INCOMPLETE

runtime / policy / learner readiness:
  BLOCKED / BLOCKED / BLOCKED

public route:
  DORMANT / BLOCKED

B2-R:
  NOT AUTHORIZED

training:
  NOT AUTHORIZED / NOT RUN

commit:
  NONE
```

Stop here for GPT/user review.
