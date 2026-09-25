# TASK_PROGRESS

## Current status

```text
classification:
  PHASE-A1A-IMPLEMENTATION-COMPLETE-AWAITING-GPT-REVIEW

authoritative design:
  AUTHORITATIVE-DESIGN-APPROVED

latest authorization:
  A1A-IMPLEMENTATION-AUTHORIZED

authorized slice:
  A1a pure registry / resolved identity only

A1a:
  complete

A1b/A1c:
  not started
  not authorized

A2–A6:
  not started
  not authorized

Phase B0/B/C/D/E:
  not entered

runtime behavior changed:
  no

Isaac/AppLauncher:
  not run

training/playback/evaluation:
  not run

checkpoint I/O:
  none

installed HARL:
  unchanged

commit:
  none
```

The 2026-07-27 direct A1a instruction superseded the older plan footer that
recorded implementation authorization as `none`. No broader phase authority was
inferred.

## Repository baseline

```text
starting HEAD:
  dca976001d8c53a9cfb424b468fa58d9fca367f6

current/ending HEAD:
  dca976001d8c53a9cfb424b468fa58d9fca367f6

active interpreter:
  C:\isaacenvs\isaac45_harl\python.exe
```

The starting worktree contained only five previously known AgentRead Markdown
states: one modified top-level handoff plus the targeted plan, summary, and two
archives. No unknown code/config/test change was present; the index was empty.

## Completed in A1a

Added the pure production contract:

- `assignment_profile_contract.py`

It defines:

- `AssignmentProfileName`;
- `AssignmentRuntimeRoute`;
- `AssignmentCheckpointFamily`;
- `AssignmentProfileSupport`;
- `AssignmentRuntimeReadiness`;
- `AssignmentProfileResolutionOrigin`;
- frozen slot `TrainingSemanticContract`;
- frozen slot `EventGatedTargetSemantics`;
- frozen slot `ResolvedExistingAssignmentProfile`;
- frozen slot `ResolvedEventGatedAssignmentProfile`;
- `ResolvedAssignmentProfile` union;
- normalization, explicit-origin resolution, immutable-registry validation,
  existing-route validation, canonical serialization, and module-identity
  validation.

Added the pure/static regression:

- `scripts/environments/test_assignment_profile_contract.py`

Added the implementation report and exact pre-update archive:

- `AgentRead/202607/20260727/PHASE_A1A_PURE_PROFILE_REGISTRY_RESOLVED_IDENTITY_IMPLEMENTATION_REPORT.md`
- `AgentRead/202607/20260727/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE_A1A_IMPLEMENTATION_20260727.md`

The archive and pre-update TASK have the same Git blob:

```text
01287dc66194e515d721ac2c080f5f19484e288c
```

## Five-profile registry

Registry order:

```text
legacy
lifecycle_ablation
lifecycle_contract_c
diagnostics_hidden_state
event_gated_local_mrta
```

Resolved matrix:

| Profile | Route | Checkpoint compatibility | Training | Playback | Readiness |
|---|---|---|---|---|---|
| legacy | existing legacy HARL | v2 where current native conditions hold | allowed | normal | existing-ready |
| lifecycle_ablation | existing ablation HARL | non-native explicit-ablation v2 evaluation target | existing-blocked | explicit-ablation | existing-ready |
| lifecycle_contract_c | existing Contract C HARL | native v2 | allowed | normal | existing-ready |
| diagnostics_hidden_state | existing diagnostics HARL | none | existing-blocked | diagnostics-only/no native checkpoint playback | existing-ready |
| event_gated_local_mrta | Phase-A interface-only | v3 identity only | Phase-A-blocked | blocked | interface-only |

The four existing route IDs are newly centralized A1a labels for current
branches, not pre-existing runtime constants or runtime wiring evidence.

## Discriminated identity boundary

Only `ResolvedExistingAssignmentProfile` exposes current runtime booleans and
`to_legacy_wrapper_mapping()`.

`ResolvedEventGatedAssignmentProfile` has only shared identity plus
`event_gated_target_semantics`; it has no event-enable boolean, old lifecycle
booleans, or legacy mapping method. The existing-only validator rejects it with
`AssignmentProfileRouteError`.

The existing mappings match current wrapper key/value/insertion order, including
`training_allowed` and ablation's sole trailing `training_blocked_reason`.

The event profile remains:

```text
runtime_route: event_gated_phase_a_interface_only_v1
checkpoint_family: assignment_checkpoint_contract_v3
training_support: phase_a_blocked
playback_support: blocked
runtime_readiness: interface_only
```

No event runtime behavior is enabled.

## Canonical module identity

Sole production module key:

```text
isaaclab_tasks.direct.scan_mobile_manipulator.assignment_profile_contract
```

The source checks the key before declaring enums, dataclasses, or custom
exceptions. Wrong-key execution raises built-in `ImportError` with expected
key, actual key, and source purpose. Production contains no bare fallback or
`sys.modules` alias.

Pure child evidence confirms:

- sole target-source key is canonical;
- producer class/enum/exception is the consumer object;
- strict `isinstance()` succeeds;
- wrong-key execution fails before public types exist.

This does not claim A1c formal-entrypoint-to-wrapper same-object wiring.

## Verification

Final results:

```text
python -m py_compile <new contract> <new test>
  exit 0

python scripts/environments/test_assignment_profile_contract.py --json
  exit 0
  11/11 passed

python scripts/environments/test_assignment_initial_condition_contract.py --json
  exit 0
  9/9 passed
```

The A1a suite dynamically AST-compares the current wrapper/observation mapping
without importing the wrapper. Training/checkpoint identities were also traced
by static code review; the suite holds independent exact semantic goldens.

Side-effect evidence confirms unchanged RNG, environment, cwd, `sys.path`,
logger state, temporary/source directory snapshots, and no forbidden
runtime/checkpoint imports.

One intermediate A1a test run found a test-only forbidden-prefix false positive;
the harness was corrected, followed by clean final passes.

## Boundary confirmation

Not modified:

- scenario/config/YAML/JSON;
- assignment wrapper, training contract, runner, buffer, trainer, resolver,
  observation, reward, environment, or logger;
- train/play/evaluation entrypoints;
- checkpoint modules;
- package `__init__.py`;
- installed HARL.

Not run:

- Isaac Lab or AppLauncher;
- environment construction;
- training;
- playback;
- formal evaluation;
- checkpoint load/save/read/write.

No commit was created.

## Residual review risks

1. Review should accept or rename the four new centralized existing-route
   semantic labels before A1c.
2. The explicit-ablation checkpoint value is a non-native v2 evaluation
   compatibility target, not a new manifest/save family.
3. No production consumer is wired; scenario authority and same-object evidence
   remain A1b/A1c work.
4. Event checkpoint v3 is identity only; no v3 manifest/dispatcher exists.

No A1a architectural blocker remains.

## Detailed handoff

- `AgentRead/202607/20260727/PHASE_A1A_PURE_PROFILE_REGISTRY_RESOLVED_IDENTITY_IMPLEMENTATION_REPORT.md`
- `AgentRead/202607/20260727/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE_A1A_IMPLEMENTATION_20260727.md`
- `AgentRead/202607/20260727/PHASE_A_PURE_INTERFACE_IDENTITY_DIAGNOSTICS_IMPLEMENTATION_PLAN.md`
- `AgentRead/202607/20260727/PHASE_A_IMPLEMENTATION_PLAN_TARGETED_REVISION_SUMMARY.md`
- `AgentRead/202607/20260727/Lifecycle_Aware_Event_Gated_Local_MRTA_Design_Authoritative_V2_1_20260727.md`

## Next step

Review A1a only. Do not enter A1b, A1c, A2–A6, or Phase B0/B/C/D/E without new
explicit authorization.
