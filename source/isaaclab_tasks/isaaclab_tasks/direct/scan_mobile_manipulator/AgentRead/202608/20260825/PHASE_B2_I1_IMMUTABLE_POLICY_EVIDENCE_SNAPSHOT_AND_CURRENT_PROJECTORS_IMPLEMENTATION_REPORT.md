# Phase B2-I1 Immutable Policy Evidence Snapshot and Current Projectors — Implementation Report

Date: 2026-08-25

Classification: `PHASE-B2-I1-IMMUTABLE-POLICY-EVIDENCE-SNAPSHOT-AND-CURRENT-PROJECTORS-COMPLETE-AWAITING-GPT-REVIEW`

## 1. Status and boundary

```text
B2-D:                              REVIEW PASS / FROZEN
B2-I0:                             REVIEW PASS / CLOSED
B2-I1:                             IMPLEMENTED / AWAITING GPT REVIEW
Phase B overall:                   NOT COMPLETE
runtime readiness:                BLOCKED
policy readiness:                 BLOCKED
learner readiness:                BLOCKED
public learned-policy event step: BLOCKED
training:                          NOT AUTHORIZED
commit:                            NONE
```

Only B2-I1 was implemented. B2-I2 legality, DVM, row kinds, forced actions, decision bundle, policy sampling, and learner work were not started.

## 2. Starting checkpoint

```text
branch: main
HEAD: 14993dee344bade0230d2eb97b5f22171331f44a
subject: feat(mrta): complete lifecycle runtime backbone and wrapper integration
B2-I0 review authority: REVIEW PASS / CLOSED, supplied by the user
```

The pre-existing B2-D and B2-I0 working-tree artifacts were preserved. No commit was created.

## 3. Changed files

Implementation:

- `assignment_event_policy_evidence.py` — new task-local pure Torch current evidence/projector module.

Verification:

- `scripts/environments/test_assignment_phase_b2_i1_immutable_policy_evidence_current_projectors_pure.py` — new 14-oracle synthetic fixture.

Documentation:

- this report;
- `AgentRead/TASK_PROGRESS.md`.

No existing runtime facade, wrapper, P2 writer, lifecycle transaction, DirectMARLEnv, environment, runner, buffer, GAE, controller, configuration, checkpoint, or installed HARL file was modified.

## 4. EventPolicyEvidenceSnapshot schema

The factory-only frozen snapshot holds:

```text
event_policy_evidence_snapshot_v2 schema/profile identity
EventPolicyEvidenceIdentityV2
exact source _EventRuntimeCurrentPublication reference
exact source _ClaimWindowIdentity reference
detached EventPolicyPhysicalProblemEvidenceV2
cloned P2 task_state [E,N]
cloned P2 robot_state [E,M]
cloned P2 ownership [E,N]
derived current_owned_task_id [E,M]
cloned P2 cumulative_failed_pairs [E,M,N]
cloned P2 completion_count [E,M]
actor_obs [E,M,O_v2]
semantic_share_obs [E,S_critic_v2]
runner_share_obs [E,M,S_critic_v2]
actor/critic block-layout and offset descriptors
immutable scale, normalization, source, and provenance metadata
```

All public tensor properties return detached contiguous clones. The snapshot clones the already-detached physical DTO again, so neither environment problem tensors nor a caller-held DTO can mutate sealed evidence.

A separate I1 projector descriptor marks actor/current-critic projection implemented while leaving the frozen I0 descriptor and runtime/readiness gates unchanged.

## 5. Capture authority and lifetime

The canonical capture consumes one already-read bundle:

```text
one exact current P2 publication
+ one exact idle OPEN fence view
+ one detached physical/problem evidence DTO
+ one frozen v2 scale contract
-> one sealed EventPolicyEvidenceSnapshot
```

The OPEN view must be exact, phase `OPEN`, contain an exact opaque window, and have no active step/reset admission. P2 and OPEN must carry the same opaque runtime-domain identity. Window serial/counters are never retained or used.

Each P2 tensor is cloned into a local value once. One common semantic block map then produces both actor and critic tensors. There is no actor-P2 read followed by a critic-P2 reread. The physical capture reads every required problem mapping key once before detaching it.

The retained P2/window references serve binding and stale validation only. The snapshot is not a state writer, second lifecycle store, ownership table, scheduler, or clock.

## 6. Physical/problem sources

`EventPolicyPhysicalProblemEvidenceV2` captures base position/yaw, scanner pose, task pose, arm/scanner capabilities, explicit `feasible_mask`, Euclidean `cost_matrix`, episode progress, and fixed agent/task order.

`problem["robot_status"]` and `problem["task_status"]` are recorded as excluded legacy placeholders and are not lifecycle sources.

Geometric cost remains finite nonnegative scanner-to-viewpoint Euclidean ranking distance. It is not path cost, time, nominal travel cost, or feasibility. Nonfinite cost fails closed as malformed evidence; it never infers or mutates feasibility. A false feasibility value and finite cost remain distinct numerical signals.

Local/top-k, path-valid, nominal path-cost/time, and retry producers remain external seams. No fake values or geometric-cost fallback were added.

## 7. P2-derived fields and current-only boundary

Only current `LifecycleStateSnapshot` supplies robot/task lifecycle, availability, ownership, inverse owned task, cumulative failed pairs, and completion attribution.

Owned-task derivation maps zero tasks to none index `N`, one task to its global ID, and rejects more than one with `multiple_owned_tasks`. It never selects the first or lowest ID.

I1 requires `terminated=false`, `truncated=false`, and `termination_reason=NONE`. Terminal publications and non-publication historical objects are rejected. No terminal audit, pre-reset capture, sidecar, post-reset reconstruction, or TIME_LIMIT bootstrap mode exists in I1.

## 8. Actor manifest mapping

| Order | Block | Per-row width |
|---:|---|---:|
| 1 | actor robot identity one-hot | `M` |
| 2 | global robot physical state | `16*M` |
| 3 | robot lifecycle plus availability | `5*M` |
| 4 | task pose | `7*N` |
| 5 | task lifecycle | `6*N` |
| 6 | task ownership including unowned | `N*(M+1)` |
| 7 | current robot-owned task including none | `M*(N+1)` |
| 8 | failed-pair state | `M*N` |
| 9 | explicit physical feasibility | `M*N` |
| 10 | geometric ranking cost | `M*N` |
| 11 | robot workload | `M` |
| 12 | physical episode progress | `1` |

Offsets derive from I0 manifest order and actual semantic shapes. Raw nearest-eight/96D observations are not consumed and task IDs are never repacked.

```text
O_v2 = 5*M*N + 24*M + 14*N + 1
M=3,N=12 -> 421
M=2,N=4  -> 145
```

## 9. Centralized critic mapping

The critic uses the same once-built global semantic blocks, excluding actor-row identity. It is stored once as `[E,S]` and copied at the HARL transport boundary to `[E,M,S]`.

```text
S_critic_v2 = 5*M*N + 23*M + 14*N + 1
M=3,N=12 -> 418
M=2,N=4  -> 143
```

It is not actor concatenation. Termination reason and identity metadata are absent from numerical blocks. Only `CURRENT_POLICY_CRITIC` is implemented.

## 10. Normalization/scaling

| Feature | Rule |
|---|---|
| positions and capability lengths | divide by `scene_env_spacing` |
| base yaw | `sin`, then `cos` |
| quaternions | finite unit `wxyz`, deterministic nonnegative leading sign |
| lifecycle/ownership/failed/feasibility | canonical 0/1 float |
| geometric ranking cost | divide by `scene_env_spacing` |
| workload | P2 completion count divided by fixed `N` |
| episode progress | steps divided by fixed horizon, clamped to `[0,1]` |

Outputs are deterministic contiguous `float32` on the source device. No running statistics, learned normalization, mean/std, or empirical tuning exists.

## 11. Identity exclusion and stale validation

The reused I0 identity binds exact P2 publication identity, episode generations, transition generations, OPEN opaque identity, and fixed M/N. These are metadata only.

A two-snapshot oracle supplies identical semantic state with different valid P2/window/generation identities and obtains bitwise-equal actor/critic tensors. `validate_current()` rejects a different P2 reference, wrong episode, wrong transition, and wrong OPEN identity without rebinding.

## 12. Single-capture and no-alias proof

The fixture proves:

- every required physical problem key is read exactly once;
- actor and critic common slices are bitwise equal;
- exact source P2/OPEN objects are retained;
- source problem mutation after physical capture has no effect;
- caller-held physical DTO mutation after sealing has no effect;
- fixture mutation of source P2 backing after sealing has no effect;
- mutation of returned actor/runner tensors has no effect;
- runner share transport is contiguous copied storage, not a writable expand alias.

## 13. Verification matrix

Interpreter:

```text
C:\isaacenvs\isaac45_harl\python.exe
Python 3.10.20
```

| Suite | normal | `-I -B` |
|---|---:|---:|
| B2-I1 evidence/current projectors | `14/14 PASS` | `14/14 PASS` |
| B2-I0 no-tick reconciliation | `13/13 PASS` | `13/13 PASS` |
| historical v1 schema | `9/9 PASS` | `9/9 PASS` |
| Phase-A default-off identity | `16/16 PASS` | `16/16 PASS` |
| profile contract | `16/16 PASS` | `16/16 PASS` |

`py_compile` for the new module and fixture: `2/2 PASS`. Final hygiene includes protected hashes, `git diff --check`, untracked whitespace inspection, and removal of temporary bytecode output.

## 14. Protected hashes

The I1 fixture checks 11 protected files, including the frozen I0 module and all v1/profile/wrapper/training/facade/proposal/P2/environment anchors. Representative hashes:

```text
assignment_event_profile_schema_contract_v2.py
  9fb64e62f1fff8b2ad9eafd8137f8d71b8912464e4c859e2b8b395421c37f955
assignment_event_runtime_facade.py
  036082d8df61514aa3f3c424ae6559fa678536097b66bfd5bd6f632ca3479478
assignment_harl_wrapper.py
  f238536c8a4bed53da984e4f2d81150f7b634915e49b601d86eb407fae9fa2ae
scan_mobile_manipulator_env.py
  c19b5de8f73d22fbc8b4c1f6b38dbfc4804d28b6e37b002cdfc4e20d5ecc9c99
```

New artifact hashes after final source verification:

```text
assignment_event_policy_evidence.py
  7563835ca94eb08baab463a349aa8d27a056da12477e3ded8827b512dd86f83a
test_assignment_phase_b2_i1_immutable_policy_evidence_current_projectors_pure.py
  103d9f84bebad8b2deec34b15719f592351a3e405588875556c6a50883525295
```

## 15. Runtime/readiness non-claims

The projector is deliberately not wired into public wrapper reset/step. The pure consumer API is available for a later separately authorized private composition step. Public policy stepping and readiness remain blocked.

No Isaac, AppLauncher, HARL rollout, actor sampling, optimizer, training, playback, evaluation, or checkpoint operation was run. Installed HARL was not modified.

## 16. Remaining blockers

No B2-I1 STOP condition was encountered. Remaining blockers include B2-I2; B2-I3a/I3b collection and HAPPO math; B2-I4 terminal sidecar; B2-I5a/I5b learner/TIME_LIMIT semantics; B2-I6 dormant public route; and later verification/readiness gates.

```text
next proposed slice: B2-I2 — Lifecycle legality, DVM, row plan, proposal ledger
status: NOT AUTHORIZED
```

## 17. Final classification

```text
classification:
  PHASE-B2-I1-IMMUTABLE-POLICY-EVIDENCE-SNAPSHOT-AND-CURRENT-PROJECTORS-COMPLETE-AWAITING-GPT-REVIEW
B2-D:
  REVIEW PASS / FROZEN
B2-I0:
  REVIEW PASS / CLOSED
B2-I1:
  IMPLEMENTED / AWAITING GPT REVIEW
tests:
  PASS
Isaac:
  NOT RUN
HARL runtime:
  NOT RUN
training/playback/evaluation:
  NOT RUN
runtime readiness:
  BLOCKED
policy readiness:
  BLOCKED
learner readiness:
  BLOCKED
training:
  NOT AUTHORIZED
commit:
  NONE
```

Stop here pending GPT independent review and explicit user authorization. Do not begin B2-I2.
