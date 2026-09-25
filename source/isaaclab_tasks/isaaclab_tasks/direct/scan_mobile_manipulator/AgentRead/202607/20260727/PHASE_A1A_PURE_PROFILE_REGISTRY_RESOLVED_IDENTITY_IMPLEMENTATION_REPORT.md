# Phase A1a Pure Profile Registry / Resolved Identity Implementation Report

## 1. Classification

```text
classification:
  PHASE-A1A-IMPLEMENTATION-COMPLETE-AWAITING-GPT-REVIEW

authorized implementation:
  A1a pure registry / resolved identity only

A1b/A1c:
  not entered

A2–A6:
  not entered

Phase B0/B/C/D/E:
  not entered

runtime behavior changed:
  no

commit:
  none
```

No A1a blocker was found. The result is a pure, repo-local identity module plus
a pure/static regression suite. No production consumer imports the new module
in this slice.

## 2. Authorization and scope

The direct authorization is the 2026-07-27 user instruction classified
`A1A-IMPLEMENTATION-AUTHORIZED`. It supersedes the older plan footer that still
recorded A1a authorization as `none`; the plan itself was not edited.

Implemented:

- five-profile vocabulary and normalization;
- origin-independent immutable profile registry;
- explicit-origin resolved-profile construction;
- existing/event discriminated resolved subtypes;
- exact current four-profile legacy wrapper mappings;
- event-gated interface-only target identity;
- canonical module-name guard and typed error hierarchy;
- deterministic primitive serialization and pure validators;
- pure/static tests.

Not implemented:

- scenario/profile propagation;
- formal-entrypoint or wrapper-fallback wiring;
- any production wrapper/runner consumer;
- event/lifecycle/MRTA DTOs from A1b/A1c or A2 onward;
- checkpoint v3 manifest or dispatcher;
- runtime event gate, DVM, resolver, reward, trainer, or logger behavior.

## 3. Starting repository state

Starting HEAD:

```text
dca976001d8c53a9cfb424b468fa58d9fca367f6
```

Starting log:

```text
dca97600 docs(assignment): approve event-gated local MRTA design for Phase A
e3febe41 docs(assignment): validate multi-condition late-training regression
9d31b15f - add deterministic baseline and cyclic pose-slot profiles ...
```

The starting worktree contained only the five previously known AgentRead
Markdown states:

- modified `AgentRead/TASK_PROGRESS.md`;
- untracked targeted-revision summary;
- untracked targeted-revised Phase A plan;
- two untracked pre-plan/pre-revision TASK archives.

No unknown Python, YAML, JSON, test, runtime, or installed-package change was
present. The starting index was empty and `git diff --check` passed.

Interpreter verification returned:

```text
C:\isaacenvs\isaac45_harl\python.exe
```

## 4. Files changed

A1a code:

- added `assignment_profile_contract.py`;
- added `scripts/environments/test_assignment_profile_contract.py`.

A1a documentation:

- added this implementation report;
- added
  `TASK_PROGRESS_ARCHIVE_BEFORE_PHASE_A1A_IMPLEMENTATION_20260727.md`;
- updated top-level `AgentRead/TASK_PROGRESS.md`.

No file outside the authorized list was modified by A1a.

The new archive is byte-for-byte equal to the pre-A1a top-level handoff:

```text
pre-update TASK_PROGRESS git blob:
  01287dc66194e515d721ac2c080f5f19484e288c

A1a archive git blob:
  01287dc66194e515d721ac2c080f5f19484e288c
```

## 5. Implemented contract

Public enums:

- `AssignmentProfileName`;
- `AssignmentRuntimeRoute`;
- `AssignmentCheckpointFamily`;
- `AssignmentProfileSupport`;
- `AssignmentRuntimeReadiness`;
- `AssignmentProfileResolutionOrigin`.

Frozen slot dataclasses:

- `TrainingSemanticContract`;
- `EventGatedTargetSemantics`;
- `ResolvedExistingAssignmentProfile`;
- `ResolvedEventGatedAssignmentProfile`.

Union:

```python
ResolvedAssignmentProfile = (
    ResolvedExistingAssignmentProfile
    | ResolvedEventGatedAssignmentProfile
)
```

Public functions:

- `normalize_assignment_profile_name()`;
- `resolve_assignment_profile()`;
- `get_assignment_profile_registry()`;
- `validate_assignment_profile_registry()`;
- `validate_existing_assignment_profile()`;
- `resolved_assignment_profile_to_mapping()`;
- `validate_canonical_module_identity()`.

All resolution requires an explicit canonical
`AssignmentProfileResolutionOrigin`. The registry view deliberately excludes
the call-specific origin instead of inventing a registry/default origin.

Normalization accepts only the canonical enum identity or an exact `str`,
strips surrounding whitespace, and rejects empty, unknown, case-folded, or
alias values. It does not read scenario, Hydra, argparse, environment config,
or the call stack.

## 6. Five-profile registry

The immutable registry order is:

1. `legacy`;
2. `lifecycle_ablation`;
3. `lifecycle_contract_c`;
4. `diagnostics_hidden_state`;
5. `event_gated_local_mrta`.

| Profile | Runtime route | Checkpoint compatibility identity | Training | Playback | Readiness |
|---|---|---|---|---|---|
| `legacy` | `existing_legacy_assignment_harl_v1` | v2, where current native conditions are met | allowed | normal | existing-ready |
| `lifecycle_ablation` | `existing_lifecycle_ablation_assignment_harl_v1` | named explicit-ablation v2 evaluation target | existing-blocked | explicit-ablation | existing-ready |
| `lifecycle_contract_c` | `existing_lifecycle_contract_c_assignment_harl_v1` | native v2 | allowed | normal | existing-ready |
| `diagnostics_hidden_state` | `existing_diagnostics_hidden_state_assignment_harl_v1` | none | existing-blocked | diagnostics-only route; no native checkpoint playback | existing-ready |
| `event_gated_local_mrta` | `event_gated_phase_a_interface_only_v1` | v3 identity only | Phase-A-blocked | blocked | interface-only |

The first four route strings are newly centralized A1a semantic labels for the
current wrapper branches. They are not claimed to be pre-existing runtime
constants or runtime wiring evidence.

`assignment_checkpoint_contract_v2_explicit_ablation_evaluation` denotes a
non-native named v2 evaluation compatibility target. It does not define a new
manifest format, native ablation save family, loader, or checkpoint artifact.
The support fields carry the training/playback restriction.

All matches are explicit. Unknown and event profiles cannot fall through to the
current training-contract helper's diagnostics catch-all.

## 7. Discriminated resolved-profile family

Both subtypes share the frozen identity fields and exact contract version
`assignment_resolved_profile_v1`.

Only `ResolvedExistingAssignmentProfile` contains current runtime booleans,
schema/mask/budget/guardrail values, policy-sequence identity, and
`to_legacy_wrapper_mapping()`.

`ResolvedEventGatedAssignmentProfile` contains only the shared identity plus
`event_gated_target_semantics`. It has no:

- `event_gate_enabled`;
- `resolver_enabled`;
- `lifecycle_observation_enabled`;
- `lifecycle_mask_enabled`;
- `to_legacy_wrapper_mapping()`.

The existing-only validator performs a strict canonical subtype check and
raises `AssignmentProfileRouteError` for the event subtype. Constructors also
reject subtype/profile discriminant mismatches and any value drift from the
exhaustive registry.

Support values are split by validation into disjoint training and playback
subsets, preventing cross-field values such as `training_support=normal`.

## 8. Canonical module identity boundary

Sole production module key:

```text
isaaclab_tasks.direct.scan_mobile_manipulator.assignment_profile_contract
```

The source performs its `__name__` check before any enum, dataclass, or custom
exception declaration. A wrong-key execution raises built-in `ImportError`
containing:

- expected module key;
- actual module key;
- source purpose.

The module-local `CanonicalModuleIdentityError` is declared only after this
guard, because declaring it earlier would itself create a second exception
identity.

Production source contains no:

- bare self-import;
- relative-to-bare fallback;
- `sys.modules` access or alias;
- package `__init__.py` modification.

The clean-child test registers the source under the canonical key exactly once.
Its wrong-key reproduction creates a non-registered module object and confirms
failure before any public identity-bearing type is created.

This is pure canonical-module-cache identity evidence only. It is not A1c
evidence for formal-entrypoint-to-wrapper same-object wiring.

## 9. Existing-profile identity evidence

Pure/static AST evidence dynamically reads:

- `assignment_harl_wrapper.py`;
- `assignment_lifecycle_observation.py`.

It verifies, for all four existing profiles:

- exact mapping keys;
- exact values;
- exact insertion order;
- `training_allowed`;
- ablation's sole trailing `training_blocked_reason`.

The wrapper is not imported.

Manual static code review also traced:

- policy-sequence values in
  `assignment_lifecycle_training_contract.py`;
- Contract C HAPPO/EP/non-shared/feed-forward/state-dict guards;
- legacy runtime-config-selected semantics;
- native/non-training profile handling in assignment training/checkpoint code.

The test has independent exact goldens for all existing nested training
semantic fields and corruption guards. It does not claim to AST-extract the
entire training/checkpoint implementation.

Legacy algorithm, state, sharing, recurrence, serialization, and whole-model
save fields remain unbound (`None`) where current configuration selects them.
Ablation and diagnostics remain non-training identities. Only Contract C is
frozen to the current HAPPO/EP/feed-forward/state-dict contract.

## 10. Event-profile interface-only identity

The event profile exactly resolves to:

```text
profile_contract_version: assignment_resolved_profile_v1
profile_name: event_gated_local_mrta
runtime_route: event_gated_phase_a_interface_only_v1
checkpoint_family: assignment_checkpoint_contract_v3
training_support: phase_a_blocked
playback_support: blocked
runtime_readiness: interface_only
```

Its target semantics exactly identify the authorized global actor/shared
schemas, global-ID local mask, authoritative lifecycle release contract,
decision-valid feed-forward policy route, and HAPPO/EP/non-shared/
non-recurrent/state-dict training target.

These are deterministic interface identity fields only. No event runtime,
checkpoint v3 implementation, or actor update is enabled.

## 11. Tests and command results

Final authorized compile:

```text
D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python -m py_compile source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_profile_contract.py scripts/environments/test_assignment_profile_contract.py

exit code: 0
```

Final A1a pure suite:

```text
D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python scripts/environments/test_assignment_profile_contract.py --json

exit code: 0
tests: 11/11 passed
```

Coverage includes vocabulary, exact registry matrix, deep immutability,
fresh/equal resolution, subtype discrimination, current wrapper AST mapping,
existing/event training semantics, corruption guards, deterministic primitive
serialization, module/type identity, wrong-key rejection, and side effects.

One intermediate pure-suite invocation exited 1 because the test's forbidden
module prefix initially counted the canonical `isaaclab_tasks...` module
itself. The harness filter was corrected; no production-contract behavior was
changed for that false positive. Subsequent runs passed.

The historical regression was statically confirmed pure before execution:

```text
D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python scripts/environments/test_assignment_initial_condition_contract.py --json

exit code: 0
tests: 9/9 passed
runtime boundary: pure/fake/static; no Isaac Lab or AppLauncher import
```

No training, playback, formal evaluation, checkpoint, or environment test was
run.

Final repository checks:

```text
git rev-parse HEAD
  exit 0; dca976001d8c53a9cfb424b468fa58d9fca367f6

git status --short --untracked-files=all
  exit 0; only four pre-existing untracked plan/archive files plus the
  authorized A1a module, test, report, archive, and modified TASK_PROGRESS

git diff --name-status
  exit 0; only tracked TASK_PROGRESS.md is modified

git diff --check
  exit 0

git diff --cached --name-status
  exit 0; empty
```

Git emitted the repository's non-failing Windows autocrlf notice for the
tracked TASK file; no whitespace error was reported.

## 12. Side-effect audit

The clean child uses `-I -B` and snapshots import/resolve behavior. Final
evidence:

```text
random state unchanged: true
environment unchanged: true
cwd unchanged: true
sys.path unchanged: true
logger state unchanged: true
temporary cwd and contract source tree unchanged: true
forbidden runtime/checkpoint modules absent: true
stdout/stderr empty: true
sole target-source module key: canonical key only
```

The source AST contains no Isaac/AppLauncher/HARL/torch/NumPy/checkpoint,
filesystem, RNG, or logging dependency and no filesystem mutation call.

## 13. Deferred A1b/A1c work

Deferred and not authorized:

- A1b primitive pre-AppLauncher declaration/normalization;
- A1c formal authority, wrapper fallback, conflict validation, and real
  propagation;
- production imports of this module;
- formal entrypoint/wrapper same-object identity proof;
- pre-AppLauncher rejection behavior;
- default-off production equivalence.

No part of A2–A6 or Phase B0/B/C/D/E was started.

## 14. Risks and blockers

Blockers:

```text
none within A1a
```

Residual review risks:

1. The four existing route IDs are new centralized semantic labels and should
   be accepted or renamed by review before A1c wiring.
2. The explicit-ablation checkpoint value must continue to be treated as a
   non-native v2 evaluation compatibility target, never as a new manifest/save
   family.
3. Registry identity is not yet consumed by scenario, entrypoint, wrapper,
   runner, playback, or checkpoint code.
4. Canonical cache identity is proven only in the pure harness; production
   same-object wiring remains an A1c obligation.
5. Event v3 identity is a target descriptor only; A4 must implement and
   validate the separate checkpoint contract before any use.

## 15. Final classification

```text
classification:
  PHASE-A1A-IMPLEMENTATION-COMPLETE-AWAITING-GPT-REVIEW

evidence:
  pure/static A1a evidence complete

runtime evidence:
  none claimed or required for A1a

deferred evidence:
  A1b/A1c propagation and production identity wiring

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

A1a:
  stopped for GPT/user review

A1b/A1c:
  not entered

A2–A6:
  not entered

Phase B0/B/C/D/E:
  not entered
```
