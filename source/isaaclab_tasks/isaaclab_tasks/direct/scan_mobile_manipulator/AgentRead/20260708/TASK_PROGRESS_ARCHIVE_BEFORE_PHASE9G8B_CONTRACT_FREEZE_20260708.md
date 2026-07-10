# TASK_PROGRESS

Compact handoff for the assignment-based scan-mobile-manipulator work.

## Current Status

Phase 9G-8A is complete.

Classification:

```text
DOCUMENTATION-ONLY DESIGN AUDIT COMPLETE
```

Phase 9G-7 was completed and manually committed by the user with:

```text
feat(assignment): add default-off lifecycle resolver
```

Phase 9G-8A inspected the committed default-off lifecycle resolver and the current HARL-facing observation, mask, action, rollout-buffer, playback, training, and checkpoint boundaries. It produced an implementation-ready design for lifecycle-aware observations, lifecycle-aware masks, schema/version guards, and checkpoint migration.

Report:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260708/PHASE9G8A_LIFECYCLE_AWARE_OBSERVATION_TRAINING_READINESS_DESIGN_AUDIT.md
```

TASK_PROGRESS archive created before this update:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260708/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G8A_LIFECYCLE_OBSERVATION_DESIGN_AUDIT_20260708.md
```

No Python source files were modified in Phase 9G-8A.

No training was run.

No short training smoke was run.

No playback or comparison-method evaluation was run.

No commit was made.

## Main Findings

Current actor observation:

```text
obs[agent_id]: [E, 100 + 3M + 16N]

For M=3, N=50:
  obs[agent_id]: [E, 909]
```

It includes physical task availability, feasibility, coverage, cost, previous assignment, and legacy dynamic assignment diagnostics. It does not include resolver active target, execution latch, task ownership, or same-robot failed/released pair memory.

Current critic/shared observation:

```text
shared_flat: [E, M * actor_dim]
share_obs:   [E, M, M * actor_dim]

For M=3, N=50:
  share_obs: [E, 3, 2727]
```

The critic currently receives a repeated common flattened concatenation of actor observations. Because actor observations do not include resolver lifecycle state, the critic does not observe it either.

Current available-action mask:

```text
available_actions: [E, M, N + 1]
raw target ids:     0 .. N-1
raw noop id:        N
resolver noop:      -1
```

The mask currently reflects physical availability/coverage plus optional legacy wrapper guardrails. It does not reflect lifecycle resolver active target, ownership, or failed/released pair state. Noop is always available.

Current checkpoint boundary:

```text
actor input dim:      env.observation_space[agent_id]
critic input dim:     env.share_observation_space[0]
actor buffer shape:   actor observation space
critic buffer shape:  shared observation space
action dim:           N + 1
```

Observation-shape changes will structurally invalidate old actor and critic checkpoints unless schema guards and explicit compatibility policy are added.

## Hidden-State Inventory Result

Behavior-driving actor-required state:

```text
robot idle/executing state, represented by active target
active_target_id
task ownership state: unowned / self-owned / teammate-owned
same-robot failed/released pair memory
current task availability/feasibility/coverage, already present
```

Mask-required state:

```text
physical availability/coverage
active target for executing robots
teammate-owned tasks
same-robot failed/released pairs
noop action under Contract C
```

Critic-only optional state:

```text
full teammate failed-pair matrix
global attempt ages
last failure/release reasons
resolver step or normalized lifecycle counters
```

Diagnostics-only state:

```text
active-target infeasibility streaks
stranded failed-pair streaks
proposal/effective explanation rows
event history beyond persistent pair/ownership/active state
```

Attempt age is not actor-required in the first migration because the current resolver does not use `attempt_age` or `attempt_start_step` to interpret proposals. Budget release results must instead become visible through same-robot failed/released pair state.

## Selected Minimum Observation Design

Selected actor lifecycle add-on:

```text
per task, for the acting robot:
  self_active_target[j]
  task_owned_by_self[j]
  task_owned_by_teammate[j]
  self_pair_failed_or_released[j]
```

Shape:

```text
actor lifecycle add-on: [E, 4N]

For N=50:
  +200 actor dims
```

Lifecycle actor observation:

```text
lifecycle_actor_dim = 100 + 3M + 20N

For M=3, N=50:
  lifecycle_actor_dim = 1109
```

Selected shared/critic design:

```text
share_obs remains common flattened concatenation of all lifecycle actor observations
lifecycle_shared_dim = M * lifecycle_actor_dim

For M=3, N=50:
  lifecycle_shared_dim = 3327
```

No separate critic-only lifecycle block is required for the minimum safe migration because the current shared convention can expose all actor-required lifecycle state for all robots through concatenation.

## Selected Encodings

Active target:

```text
per-task self_active_target[j] binary
```

This is preferred over raw normalized target id, separate one-hot id, gathered active embedding, or future attention/query tokens for the first MLP/HAPPO migration.

Task ownership:

```text
task_owned_by_self[j]
task_owned_by_teammate[j]
unowned = both bits 0
```

No actor-visible raw owner id or owner one-hot is required.

Failed pair:

```text
self_pair_failed_or_released[j]
```

Teammate failed-pair state is not actor-required. Exposing self failed/released pair state does not solve the stranded-task retry-policy limitation.

Variable `M` and `N`:

```text
current first migration remains fixed-shape MLP compatible
future variable N should use padded task slots plus task_valid and action masks
future variable M requires a broader model/schema migration
```

## Selected Mask Migration

Selected option:

```text
Option B: lifecycle observation plus lifecycle-aware masks
```

Resolver remains the final safety boundary.

Executing robot mask semantics:

```text
available raw actions = current active target id and noop raw id N
all other target ids masked out
```

Noop/continue semantics:

```text
idle + noop       -> remain idle
executing + noop  -> continue active target
```

Noop must remain available in both states.

Ownership mask semantics:

```text
teammate-owned task targets are masked for idle robots
self-owned current active target remains available for the executing owner
resolver owner rejection remains required for safety
```

Failed-pair mask semantics:

```text
same-robot failed/released pairs are masked for idle robots
resolver pair rejection remains required for safety
```

Option C, explicit continue/hold action redesign, is deferred because it changes action semantics and checkpoint/action compatibility.

## Selected Schema and Checkpoint Policy

Default legacy mode remains:

```text
assignment_lifecycle_resolver_enabled = False
assignment_lifecycle_observation_enabled = False
assignment_lifecycle_mask_enabled = False
assignment_observation_schema_version = "legacy_v1"
```

Lifecycle training mode requires:

```text
assignment_lifecycle_resolver_enabled = True
assignment_lifecycle_observation_enabled = True
assignment_lifecycle_mask_enabled = True
assignment_observation_schema_version = "lifecycle_v1"
```

Selected checkpoint policy:

```text
dual legacy/lifecycle model mode
```

Compatibility decision:

```text
legacy checkpoint + resolver off + legacy_v1:
  supported

legacy checkpoint + resolver on:
  unsupported by default; diagnostics-only explicit hidden-state override may be allowed later

new lifecycle checkpoint + resolver off:
  supported only with lifecycle_v1 observation shape

new lifecycle checkpoint + resolver on:
  supported after lifecycle observation, mask, guard, and training-smoke gates pass
```

Zero-filled old-checkpoint adapters are rejected for resolver-enabled runs because zero lifecycle features can falsely imply idle, unowned, and unfailed state.

Required future checkpoint metadata:

```text
assignment_observation_schema_version
assignment_lifecycle_resolver_enabled
assignment_lifecycle_observation_enabled
assignment_lifecycle_mask_enabled
num_robots
num_tasks
actor_observation_dim
shared_observation_dim
action_dim
noop_action_id
lifecycle schema/contract version
```

## Training-Readiness Gate

Resolver-enabled training remains prohibited until:

```text
lifecycle_v1 observation schema is implemented
actor observation exposes all actor-required lifecycle state
shared observation exposes required centralized lifecycle state
lifecycle-aware mask semantics are implemented
observation and mask shape smokes pass
checkpoint/schema guards pass
rollout-buffer and model construction pass
actor/critic forward-backward smoke passes
resolver-disabled legacy identity passes
resolver-enabled observation/mask consistency passes
short resolver-enabled training and checkpoint save/load smoke passes
```

Long formal training, performance comparison, and hyperparameter tuning remain user-run activities.

## Recommended Next Phases

Phase 9G-8B:

```text
lifecycle observation schema config and pure tensor builder
no HARL observation integration yet
no mask redesign yet
no training
```

Phase 9G-8C:

```text
actor/shared observation integration
schema metadata and checkpoint guards
disabled legacy identity and lifecycle shape smokes
no training
```

Phase 9G-8D:

```text
lifecycle-aware available-action mask integration
noop/current-target execution mask semantics
ownership and failed-pair masks
resolver remains final safety boundary
no training
```

Phase 9G-8E:

```text
disabled legacy identity validation
enabled observation/mask runtime validation
schema/output isolation
passive logger coexistence
no training
```

Phase 9G-8F:

```text
very short resolver-enabled training/checkpoint smoke
rollout/model construction validation
invalid checkpoint combination validation
not a performance run
```

Phase 9G-8G:

```text
commit-readiness review
```

## Validation Results

Phase 9G-8A validation commands:

```powershell
git status --short --untracked-files=all
git diff --check
```

Result:

```text
git status --short --untracked-files=all:
  documentation-only changes:
    M  AgentRead/TASK_PROGRESS.md
    ?? AgentRead/20260708/PHASE9G8A_LIFECYCLE_AWARE_OBSERVATION_TRAINING_READINESS_DESIGN_AUDIT.md
    ?? AgentRead/20260708/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G8A_LIFECYCLE_OBSERVATION_DESIGN_AUDIT_20260708.md

git diff --check:
  passed
  warning only: TASK_PROGRESS.md LF will be replaced by CRLF the next time Git touches it
```

Expected changed files are documentation only:

```text
new Phase 9G-8A design audit report
new TASK_PROGRESS archive
updated TASK_PROGRESS.md
```

No `py_compile` was required because no Python helper script or Python source file was added.

## Exact Next Action

Wait for the Phase 9G-8B implementation instruction.

Do not implement observations or masks until Phase 9G-8B or later is explicitly requested.

Do not run training, short training smoke, playback, or comparison-method evaluation.

Do not commit unless explicitly asked.
