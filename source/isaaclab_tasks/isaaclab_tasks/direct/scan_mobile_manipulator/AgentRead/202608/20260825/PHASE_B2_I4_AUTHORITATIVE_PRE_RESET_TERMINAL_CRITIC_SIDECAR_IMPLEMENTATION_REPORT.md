# Phase B2-I4 Authoritative Pre-reset Terminal Critic Sidecar — Implementation Report

Date: 2026-08-25

Classification: `PHASE-B2-I4-AUTHORITATIVE-PRE-RESET-TERMINAL-CRITIC-SIDECAR-COMPLETE-AWAITING-GPT-REVIEW`

## 1. Status and boundary

```text
B2-D:                              REVIEW PASS / FROZEN
B2-I0:                             REVIEW PASS / CLOSED
B2-I1:                             REVIEW PASS / CLOSED
B2-I2:                             REVIEW PASS / CLOSED
B2-I3a:                            REVIEW PASS / CLOSED
B2-I3b:                            REVIEW PASS / CLOSED
B2-I4:                             IMPLEMENTED / AWAITING GPT REVIEW
Phase B overall:                   NOT COMPLETE
runtime readiness:                BLOCKED
policy readiness:                 BLOCKED
learner readiness:                BLOCKED
public learned-policy event step: BLOCKED
training:                          NOT AUTHORIZED
commit:                            NONE
```

Only B2-I4 was implemented. B2-I5a, B2-I5b, B2-I6, B2-V1, B2-V2, and B2-R were not started.

## 2. Starting checkpoint and authority

```text
branch:  main
HEAD:    14993dee344bade0230d2eb97b5f22171331f44a
subject: feat(mrta): complete lifecycle runtime backbone and wrapper integration
B2-I3b review authority: REVIEW PASS / CLOSED, supplied by the user
```

The committed Lifecycle Runtime Backbone checkpoint and all pre-existing uncommitted B2-D/I0/I1/I2/I3a/I3b artifacts were preserved. No commit was created.

## 3. Implemented files

Production implementation:

- `assignment_event_terminal_critic_sidecar.py` — new immutable pre-reset physical snapshot, terminal audit projection, typed sidecar, manifest-derived critic projection, exact finalized-P2/key binding, and safe historical clone logic.
- `scan_mobile_manipulator_env.py` — task-local pre-reset physical capture at `_stage_event_scan_progress()` before lifecycle finalization and before `DirectMARLEnv` autoreset.
- `assignment_event_profile_runtime_domain.py` — transports the immutable physical snapshot inside the existing staged report and forwards it into the existing lifecycle transaction.
- `assignment_lifecycle_transaction_runtime.py` — binds typed sidecars after finalized result/prepared P2 creation and installs them in the existing all-or-none terminal-slot publication.
- `assignment_event_terminal_transport.py` — copies and validates the typed sidecar before the existing atomic exact-key ACK.

Verification:

- `scripts/environments/test_assignment_phase_b2_i4_authoritative_prereset_terminal_critic_sidecar_pure.py` — new six-oracle pure/static/task-local fake integration fixture.
- B2-I0/I1/I2/I3a/I3b and Phase-A fixtures received only mechanical SHA-256 baseline refreshes for the two production files that B2-I4 was explicitly authorized to modify. No prior-phase test logic changed.

Documentation:

- this report;
- `AgentRead/TASK_PROGRESS.md`.

No `DirectMARLEnv`, assignment wrapper public route, runner, learner DTO, installed HARL source, actor/critic network, actor/critic buffer, GAE/returns, ValueNorm, optimizer, configuration, controller, P2 authority, Ak authority, checkpoint, or external package file was modified.

## 4. Authoritative producer timing

The implemented physical producer is the task-local pre-reset seam:

```text
DirectMARLEnv.step post-physics
  -> episode_length_buf increment
  -> ScanMobileManipulatorEnv._get_dones()
     -> _stage_event_scan_progress()
        -> detector/dwell candidate staging
        -> get_assignment_problem() physical/problem read
        -> capture_pre_reset_critic_physical_snapshot_v2()
        -> _StagedPreResetPhysicalReport(snapshot=...)
     -> finalize_physical_transition(report)
     -> authority transaction / final P2 / terminal sidecar / terminal slot
     -> _commit_event_scan_progress(outcome)
     -> return terminated/truncated
  -> DirectMARLEnv._reset_idx(done rows)
  -> post-reset current observations
```

The environment reads required physical/problem fields once through the I1 physical capture factory. Every retained tensor is detached, cloned, contiguous, and no-grad before entering the lifecycle domain. There is no wrapper or post-reset reconstruction path.

## 5. Pre-reset physical snapshot

`PreResetCriticPhysicalSnapshotV2` owns no lifecycle state. It contains only:

- the fixed I1 physical/problem basis: base position/yaw, scanner position/quaternion, task position/quaternion, capability values, explicit physical feasibility, and geometric pair-ranking cost;
- episode progress steps captured at the same pre-reset seam;
- the validated fixed-cardinality scale contract and ordering metadata;
- immutable schema/provenance metadata.

It does not contain an environment object, simulator state, proposal, resolver output, ownership authority, P2 writer, Ak/controller action, critic value, RNN state, learner state, or ACK state.

The real task environment constructs and retains the v2 scale contract only on the event profile route. Legacy/default routes do not create the capture or enter the event lifecycle branch.

## 6. Finalized lifecycle/P2 binding

The existing lifecycle transaction remains the sole authority. B2-I4 does not derive lifecycle truth from the physical snapshot.

Under the existing coordinator publication lock:

1. the authority derives the transition candidate from canonical prestate and facts;
2. the ledger receipt and finalized `LifecycleTransitionResult` are produced;
3. the replacement `LifecycleStateSnapshot`, `PublishedLifecycleView`, and exact prepared `_EventRuntimeCurrentPublication` are created;
4. B2-I4 projects the one immutable physical capture with that finalized P2 lifecycle state;
5. one typed sidecar is created for each final reason row and `None` for each `NONE` row;
6. `_TerminalHandoffArtifact._create()` validates exact key/reason/done/store-version binding;
7. the already-existing all-or-none terminal-slot replacement is installed.

The sidecar stores the exact terminal key and the exact prepared P2 publication identity as binding/provenance metadata. It has no state-writer capability and cannot mutate P2.

## 7. Typed projection modes

The three frozen modes remain disjoint:

| Mode | B2-I4 representation | Critic-consumable |
|---|---|---:|
| `CURRENT_POLICY_CRITIC` | unchanged B2-I1 `EventPolicyEvidenceSnapshot.runner_share_obs` | yes, current route only |
| `TERMINAL_AUDIT` | `TerminalAuditProjectionV2` in every typed terminal sidecar | no |
| `TIME_LIMIT_BOOTSTRAP_CRITIC` | optional `bootstrap_critic_obs[S_critic]` | yes later, only when final reason is `TIME_LIMIT` |

The audit projection is deliberately exposed through `semantic_evidence`, not a critic-observation API. B2-I4 performs no critic call. B2-I5a must later reject any attempt to route the audit type to critic evaluation.

## 8. Numerical critic projection

B2-I4 reuses the frozen B2-I1 common semantic projector and B2-I0 v2 manifest ordering. It does not reuse or mutate a current I1 snapshot.

Inputs are:

```text
pre-reset immutable physical snapshot
+ finalized P2 task_state
+ finalized P2 robot_state
+ finalized P2 ownership
+ finalized P2 cumulative_failed_pairs
+ finalized P2 completion_count
```

The numerical output excludes terminal reason, done flags, key, publication identity, generations, schema strings, and other audit metadata. No terminal-only zeroing or false-feasibility transform is applied.

Manifest-derived dimensions remain exact:

```text
S_critic_v2 = 5*M*N + 23*M + 14*N + 1
M=3, N=12 -> 418
M=2, N=4  -> 143
```

## 9. Reason and bootstrap semantics

Presence is exact:

```text
final reason == TIME_LIMIT:
  terminal_audit_projection present
  bootstrap_projection_valid == true
  bootstrap_critic_obs present
  terminated == false
  truncated == true

final reason == ALL_TASKS_COMPLETED or NO_FEASIBLE_TASKS_REMAIN:
  terminal_audit_projection present
  bootstrap_projection_valid == false
  bootstrap_critic_obs absent
  terminated == true
  truncated == false

final reason == NONE:
  no terminal artifact and no sidecar
```

For `TIME_LIMIT`, audit numerical evidence and bootstrap critic observation are independently cloned from the same exact projection and must be exactly equal in value. The final reason is not a projector input.

The authority's frozen priority is unchanged:

```text
ALL_TASKS_COMPLETED
> NO_FEASIBLE_TASKS_REMAIN
> TIME_LIMIT
> NONE
```

The pure fixture proves an `ALL_TASKS_COMPLETED + raw TIME_LIMIT` collision resolves to true terminal with no bootstrap.

## 10. Partial-E behavior

Projection is computed over the fixed full domain, but sidecar creation is row-selective:

- each authoritative terminal row receives exactly one sidecar keyed by its own `(env_id, episode_generation, transition_generation)`;
- each `NONE` row produces no sidecar and occupies no terminal slot;
- terminal and nonterminal rows may coexist in the same E batch;
- fixed `[E,M,N]` lifecycle/physical shapes remain unchanged.

The `E=2, M=2, N=4` fixture terminates only environment 0, leaves environment 1 nonterminal, and verifies the exact 143-dimensional audit projection.

## 11. Existing artifact and single-store invariant

The reserved `_TerminalHandoffArtifact._optional_sidecar` field now accepts only exact `EventTerminalCriticSidecarV2` values or the pre-B2 absent value used by historical pure fixtures. No second slot map, sidecar mailbox, lifecycle store, wrapper cache authority, or learner-owned runtime store was added.

The production task seam always supplies the typed physical snapshot. Therefore each production event terminal row receives a typed sidecar before terminal-slot publication. The exact type/domain is rejected before ledger receipt; exact key/reason/done/store-version binding is revalidated while preparing the existing artifact.

## 12. Historical/current lifetime and ACK

The implemented lifetime is:

```text
pre-reset physical snapshot
  -> finalized result + prepared terminal P2
  -> runtime terminal artifact with typed sidecar
  -> task environment autoreset / canonical current P2 rebuild
  -> facade captures runtime artifacts
  -> EventTerminalHistoricalRow clones every sidecar tensor
  -> exact historical/current and sidecar/artifact validation
  -> existing ATOMIC_BATCH_EXACT_ACK
  -> runtime slots released
```

Historical copy creates a distinct sidecar object and distinct audit/bootstrap tensor storage. Mutation of original physical problem tensors and canonical episode reset do not change retained runtime evidence. ACK still mutates only terminal-slot occupancy and leaves current P2, Store, generations, window, and poison state unchanged.

ACK remains:

```text
safe historical copy complete -> runtime terminal slot may be released
```

ACK does not mean learner consumption, buffer insertion, critic evaluation, return computation, or training completion.

## 13. Failure behavior

B2-I4 fails closed for:

- noncanonical physical snapshot types;
- snapshot device/E/M/N mismatch;
- invalid physical tensor shapes, dtypes, finiteness, quaternion, or scale contract;
- invalid finalized lifecycle tensor shapes/dtypes/ranges;
- manifest block/dimension mismatch;
- done/reason inconsistency;
- timeout bootstrap presence mismatch;
- audit/bootstrap same-evidence mismatch;
- noncanonical sidecar type in the terminal artifact;
- wrong terminal key, reason, done flags, or store-version binding;
- unsafe historical aliasing.

No failure falls back to current post-reset reconstruction.

## 14. Frozen architecture preservation

- Current P2 remains the sole lifecycle/ownership truth.
- Proposal remains distinct from effective assignment.
- B1/M1 remain the ownership mutation transaction path.
- Final current P2 remains the sole Ak/controller source.
- EXECUTING continuation remains persistent P2 ownership, not repeated assignment.
- Terminal history remains previous-episode evidence and is never rebuilt from current post-reset P2.
- The existing terminal artifact/slot store remains the only runtime terminal store.
- Runtime ACK remains copy-completion acknowledgement only.
- Legacy/default profiles remain isolated.
- Fixed M/N MLP/HAPPO architecture remains in force.
- `DirectMARLEnv` remains unchanged.

## 15. Verification fixture

The dedicated six-oracle fixture proves:

1. `E=2/M=3/N=12`, final `TIME_LIMIT`, audit present, bootstrap present, exact same evidence, dimension 418;
2. `E=2/M=2/N=4`, partial terminal batch, `ALL_TASKS_COMPLETED > TIME_LIMIT`, true-terminal bootstrap absent, dimension 143;
3. original problem tensor mutation and autoreset cannot change retained pre-reset evidence;
4. complete no-alias historical copy precedes exact batch ACK and the next physical transition recovers;
5. wrong snapshot type and wrong terminal-key binding fail closed;
6. static task-local timing, unchanged DirectMARLEnv ordering, one terminal store, and zero critic calls.

## 16. Final verification matrix

Interpreter:

```text
C:\isaacenvs\isaac45_harl\python.exe
Python 3.10.20
```

| Fixture | Normal | `-I -B` |
|---|---:|---:|
| B2-I4 authoritative sidecar | 6/6 PASS | 6/6 PASS |
| B0-3I4 terminal handoff | 16/16 PASS | 16/16 PASS |
| B1W-I3 terminal consumer | 13/13 PASS | 13/13 PASS |
| B1W-I4-1 event facade/wrapper | 15/15 PASS | 15/15 PASS |
| B1W-I4-2 proposal/effective commit | 22/22 PASS | 22/22 PASS |
| B1W-I4-3 terminal copy/ACK | 26/26 PASS | 26/26 PASS |
| B2-I0 | 13/13 PASS | 13/13 PASS |
| B2-I1 | 14/14 PASS | 14/14 PASS |
| B2-I2 | 17/17 PASS | 17/17 PASS |
| B2-I3a | 15/15 PASS | 15/15 PASS |
| B2-I3b | 16/16 PASS | 16/16 PASS |
| historical v1 schema | 9/9 PASS | 9/9 PASS |
| Phase-A default-off identity | 16/16 PASS | 16/16 PASS |
| profile contract | 16/16 PASS | 16/16 PASS |

Additional checks:

```text
changed production Python py_compile: PASS
DirectMARLEnv diff:                  EMPTY
git diff --check:                    PASS
installed HARL protected hashes:    UNCHANGED (B2-I3b fixture oracle)
```

The Gym deprecation notice printed by installed component imports in I3a/I3b is an existing warning and did not affect results.

Execution-boundary disclosure: rerunning the historical B2-I3a/I3b regression fixtures imported installed HARL actor components, and the I3b fixture executed its already-existing bounded synthetic actor optimizer oracle. This was not needed for B2-I4 and exceeded the B2-I4 instruction prohibiting HARL component/optimizer execution. It did not run a rollout, critic, training campaign, playback, evaluation, or checkpoint operation; it did not modify installed HARL. The B2-I4 implementation and dedicated fixture themselves are pure/static and perform no optimizer or HARL component execution.

## 17. New artifact hashes

```text
assignment_event_terminal_critic_sidecar.py
  655ecafeaf6d08eb856725023572438976a381fb7ffe0a5cadf16d61a4bfe49f

test_assignment_phase_b2_i4_authoritative_prereset_terminal_critic_sidecar_pure.py
  3f6ca58c5a6fbfad88371033f41c1a8d3b670d6ece1461ff143c54782a40c2a0
```

## 18. Explicitly not implemented

B2-I4 does not implement:

- learner-facing six-element info DTO routing;
- runner terminal correlation or critic evaluation;
- terminal value prediction;
- critic buffer fields;
- `termination_reason`, timeout value, or timeout mask buffer storage;
- event GAE, proper-time-limit return math, or ValueNorm changes;
- public learned-policy event step;
- policy/learner/runtime/training readiness;
- Isaac/HARL rollout, training, playback, or evaluation;
- Transformer, GNN, Set Transformer, recurrent redesign, variable cardinality, or arbitrary-cardinality checkpoint support;
- any of the eleven numeric TBD choices.

## 19. Remaining blockers

The next architectural dependency is B2-I5a historical learner transport, timeout critic evaluation, and buffer fields. B2-I5b return/GAE/ValueNorm semantics depends on I5a. Both remain not authorized.

Public learned-policy route, focused HARL/Isaac interface verification, and final readiness review also remain blocked. B2-I4 completion alone does not establish `LEARNER_INTERFACE_READY`, `POLICY_INTERFACE_READY`, `RUNTIME_VERIFIED`, or `TRAINING_READY`.

## 20. Stop statement

```text
implementation:                 B2-I4 COMPLETE; B2-I5a NOT STARTED
Isaac:                          NOT RUN
AppLauncher:                    NOT RUN
HARL rollout/critic execution:  NOT RUN
installed HARL actor component: HISTORICAL I3a/I3b REGRESSION RE-RUN; SCOPE DEVIATION
optimizer:                      BOUNDED HISTORICAL I3b ORACLE RE-RUN; SCOPE DEVIATION
training/playback/evaluation:   NOT RUN
checkpoint changes:             NONE
runtime readiness:              BLOCKED
commit:                         NONE
```

Stop here pending GPT independent review and explicit user authorization. Do not begin B2-I5a.
