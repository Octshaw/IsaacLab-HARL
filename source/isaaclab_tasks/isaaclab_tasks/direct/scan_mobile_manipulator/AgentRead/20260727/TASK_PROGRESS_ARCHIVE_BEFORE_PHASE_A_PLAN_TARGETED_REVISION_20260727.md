# TASK_PROGRESS

## Current status

```text
classification:
  PHASE-A-PLAN-READY-FOR-GPT-REVIEW

authoritative design:
  AUTHORITATIVE-DESIGN-APPROVED

authorized technical phase:
  Phase A only

current activity:
  PHASE-A-IMPLEMENTATION-PLAN-DESIGN

plan design status:
  complete -- awaiting GPT/user review

Phase A implementation:
  not started

implementation authorization:
  none -- wait for GPT/user approval of this plan

Phase B0/B/C/D/E:
  not entered

runtime behavior changed:
  no

training/playback/evaluation/checkpoint load:
  none

commit:
  none
```

The approved method authority remains
`AgentRead/20260727/Lifecycle_Aware_Event_Gated_Local_MRTA_Design_Authoritative_V2_1_20260727.md`.
That file was not modified in this planning pass.

## Repository baseline

```text
current HEAD:
  dca976001d8c53a9cfb424b468fa58d9fca367f6

V2.1 verification baseline:
  e3febe417c5323e28ceb9e256ba71dcd44f3c457

[CURRENT-CODE-DELTA-SINCE-V2.1]:
  HEAD changed only through AgentRead Markdown approval/review records.
  No Phase A-relevant Python, YAML, JSON, runtime, training, or checkpoint
  implementation delta was found.
```

The active interpreter and imported HARL remain:

```text
C:\isaacenvs\isaac45_harl\python.exe
C:\isaacenvs\isaac45_harl\lib\site-packages\harl\__init__.py
```

Installed HARL was inspected read-only and was not modified.

## Completed in this pass

Created the review-ready Phase A implementation plan:

- `AgentRead/20260727/PHASE_A_PURE_INTERFACE_IDENTITY_DIAGNOSTICS_IMPLEMENTATION_PLAN.md`

Archived the exact pre-update top-level progress file:

- `AgentRead/20260727/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE_A_PLAN_DESIGN_20260727.md`

The plan defines, without implementing:

- one resolved-profile authority and direct old-route bypass;
- immutable transition facts/result schemas with generation, token, and authority checks;
- typed event, cost, local-set, DVM, proposal, component, rejection, and diagnostics contracts;
- scenario parse/apply propagation;
- separate checkpoint v2/v3 semantic dispatch;
- team-reward semantic configuration only;
- A1–A6 commit-style implementation slices;
- profile-specific default-off identity evidence;
- pure/static tests and deferred runtime evidence.

## Frozen planning decisions

- `assignment_lifecycle_profile` remains the sole configuration selector; no
  redundant event-gate boolean is planned.
- Existing four profiles retain their exact downstream supported/blocked routes
  for absent-default or already-valid resolved-config cohorts. Explicit scenario
  propagation is an intentional A1 correction to the current ignored-profile gap,
  not claimed as current byte identity.
- `event_gated_local_mrta` is the planned fifth profile. During Phase A it must
  fail closed before environment, runner, actor, checkpoint-load, or playback
  execution. Prelaunch-visible declarations fail before AppLauncher; Hydra-only
  declarations can fail only after AppLauncher but before other side effects.
- Existing checkpoint contract v2 remains unchanged. Event-gated semantics use a
  distinct `assignment_checkpoint_contract_v3` family and shared semantic
  dispatcher.
- Phase A defines interfaces and diagnostics only. It does not connect the
  pre-reset lifecycle hook, local set, Top-K, DVM, component resolver, HAPPO
  changes, or runtime reward.
- The proposed guarantee is frozen metadata, no public writable tensor alias,
  and supported-path mutation detection plus an external consume ledger. It does
  not overclaim absolute PyTorch storage immutability.
- `LifecycleTransitionResult.updated_ownership` is the event-updated,
  resolver-precommit baseline `a0`.

## Current implementation facts retained

- Current physical-step collection samples all actors and has no
  `decision_valid_mask`.
- Current EP critic input uses robot-0 reward from the wrapper's `[E,M,1]`
  reward tensor.
- Current HAPPO sequential factor uses the unmasked new/old probability ratio.
- Current DirectMARLEnv auto-reset occurs before the assignment wrapper can
  inspect terminal pre-reset state.
- Current resolver supports the existing continue/idle/claim/conflict contract;
  it does not implement switch, local Top-K, preemption, or atomic transfer
  components.
- Scenario lifecycle profile parsing exists, but the present scenario apply path
  does not propagate it to the environment configuration.
- Existing checkpoint v2 does not fingerprint the new event/DVM/factor/reward/
  component/transition semantics.

These are implementation prerequisites for later phases, not architectural
blockers and not work authorized by this pass.

## Review focus

GPT/user review should concentrate on:

1. whether the single resolved-profile identity and fail-closed event profile
   eliminate all duplicate dispatch authority;
2. whether the exact event/rejection enums, transition shapes, generation rules,
   consume-once ledger, and `updated_failed_pairs` field are sufficient;
3. whether v2 preservation, metadata-free legacy fallback, and the split between
   v3 interface descriptor and checkpoint-ready manifest are correct;
4. whether terminal no-opportunity masks, historical forced placeholders, and
   typed diagnostic ownership are unambiguous;
5. whether A1a/A1b/A1c, A3-schema→A4, A4a/A4b, and A5 closeout keep B0/B/C/D/E
   behavior out of Phase A.

## Latest verification

Read-only/static commands:

```text
git rev-parse HEAD
git log -3 --oneline
git status --short --untracked-files=all
git diff --name-status
git diff --check
git diff --cached --name-status
git hash-object <archive>
git rev-parse HEAD:<pre-update TASK_PROGRESS path>
```

Results:

- HEAD is `dca976001d8c53a9cfb424b468fa58d9fca367f6`;
- exactly three authorized Markdown files differ; no non-Markdown file differs;
- index is empty and `git diff --check` passes;
- archive Git blob equals the pre-update HEAD `TASK_PROGRESS.md` blob
  `e6ba38d8dbf5c8d067020121354adc50b9331cde`;
- archive SHA-256 is
  `423E1EB24D79F3BB9A947293840E3B4265C86480AD7A91CE9A936EAF7ECF8A5B`;
- Authoritative V2.1 has no diff;
- the plan's relative V2.1 link resolves.

The interpreter/import-path checks resolved to the paths recorded above. No test
entrypoint, Isaac environment, AppLauncher, training, playback, evaluation,
checkpoint I/O, package operation, or installed-HARL edit was performed.

## Do not do

- Do not implement A1/A2/A3/A4/A5/A6 without new explicit authorization.
- Do not enter B0/B/C/D/E.
- Do not run Isaac, training, playback, evaluation, or checkpoint I/O from this
  plan alone.
- Do not modify installed HARL or commit.

## Detailed reports / archives

- `AgentRead/20260727/PHASE_A_PURE_INTERFACE_IDENTITY_DIAGNOSTICS_IMPLEMENTATION_PLAN.md`
- `AgentRead/20260727/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE_A_PLAN_DESIGN_20260727.md`
- `AgentRead/20260727/Lifecycle_Aware_Event_Gated_Local_MRTA_Design_Authoritative_V2_1_20260727.md`

## Next step

Review
`AgentRead/20260727/PHASE_A_PURE_INTERFACE_IDENTITY_DIAGNOSTICS_IMPLEMENTATION_PLAN.md`.
Do not begin Phase A source implementation until GPT/user approval explicitly
grants implementation authority.
