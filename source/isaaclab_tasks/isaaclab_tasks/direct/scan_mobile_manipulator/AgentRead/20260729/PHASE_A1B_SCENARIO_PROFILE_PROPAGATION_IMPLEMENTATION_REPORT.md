# Phase A1b Scenario Profile Propagation Implementation Report

## 1. Classification

```text
classification:
  PHASE-A1B-IMPLEMENTATION-COMPLETE-AWAITING-GPT-REVIEW

A1a:
  complete
  report-reviewed

A1b:
  complete

A1c:
  not started
  not authorized

A2–A6:
  not started
  not authorized

Phase B0/B/C/D/E:
  not entered

commit:
  none
```

This package implements only scenario-side primitive profile parsing,
declaration provenance/conflict validation, conditional profile-string
application, and current existing-profile primitive prerequisite preflight.

## 2. Authorization and scope

The direct instruction authorized A1b after A1a review `PASS`. The implementation
did not enter A1c, A2–A6, or later phases.

Authorized production change:

- `scenario_config.py`

Authorized pure-test change:

- `scripts/environments/test_assignment_profile_contract.py`

Authorized documentation changes:

- this report;
- the exact pre-A1b `TASK_PROGRESS.md` archive;
- the current `TASK_PROGRESS.md` handoff.

No wrapper, environment, resolver, reward, runner, trainer, buffer, checkpoint,
entrypoint, YAML, JSON, or package bootstrap file was modified.

## 3. Starting repository state

```text
starting HEAD:
  dca976001d8c53a9cfb424b468fa58d9fca367f6

git log -3 --oneline:
  dca97600 docs(assignment): approve event-gated local MRTA design for Phase A
  e3febe41 docs(assignment): validate multi-condition late-training regression
  9d31b15f - add deterministic baseline and cyclic pose-slot profiles - preserve robot identities, capabilities, actors, and checkpoint compatibility - add strict condition contracts, fingerprints, and runtime manifests - keep historical no-selector playback behavior unchanged - guard condition profiles from training use - fix canonical runtime request module identity - add pure and import-boundary regressions - validate A compatibility and deterministic B/C runtime behavior

active interpreter:
  C:\isaacenvs\isaac45_harl\python.exe
```

The initial status contained only the known Phase A planning/A1a work and the
modified A1a handoff. There was no unknown code, configuration, or test change.
The index was empty.

Starting checks:

| Command | Result |
|---|---|
| `git rev-parse HEAD` | exit 0; expected HEAD |
| `git log -3 --oneline` | exit 0 |
| `git status --short --untracked-files=all` | exit 0; known cohort only |
| `git diff --name-status` | exit 0; pre-existing `TASK_PROGRESS.md` modification only |
| `git diff --check` | exit 0 |
| `git diff --cached --name-status` | exit 0; empty |
| conda interpreter probe | exit 0; expected interpreter |

## 4. Files changed

Implementation/test:

- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scenario_config.py`
- `scripts/environments/test_assignment_profile_contract.py`

Documentation:

- `AgentRead/20260729/PHASE_A1B_SCENARIO_PROFILE_PROPAGATION_IMPLEMENTATION_REPORT.md`
- `AgentRead/20260729/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE_A1B_IMPLEMENTATION_20260729.md`
- `AgentRead/TASK_PROGRESS.md`

The A1a contract was not modified.

## 5. Primitive vocabulary

`scenario_config.py` now has one ordered immutable primitive vocabulary:

```text
legacy
lifecycle_ablation
lifecycle_contract_c
diagnostics_hidden_state
event_gated_local_mrta
```

It is an exact tuple, has no duplicate, and is ordered-equal to
`AssignmentProfileName` in the package-safe pure test harness.

The scenario normalizer:

- accepts only an exact built-in `str`;
- strips leading/trailing whitespace;
- rejects empty values;
- rejects case variants;
- rejects aliases/fuzzy matches;
- rejects non-string values, `str` enum members, and other `str` subclasses;
- never defaults an explicit invalid declaration to `legacy`.

Stable error context includes the error prefix, source, raw value, normalized
value, and the ordered allowed tuple.

The scenario module does not import or reference:

- `assignment_profile_contract`;
- `AssignmentProfileName`;
- any `Resolved*AssignmentProfile` type.

It declares no enum, dataclass, or custom exception identity and uses no
`sys.modules` alias.

## 6. Declaration sources and conflict handling

The pure declaration resolver distinguishes:

```text
ABSENT
TOP_LEVEL
NESTED
TOP_LEVEL_AND_NESTED
```

Its immutable result is:

```text
(canonical_profile_or_none, provenance_label, source_records)
```

Each source record is:

```text
(source_path, raw_string, canonical_string)
```

Implemented matrix:

| Top-level | Nested | Result |
|---|---|---|
| absent | absent | no explicit profile; `ABSENT` |
| valid A | absent | A; `TOP_LEVEL` |
| absent | valid A | A; `NESTED` |
| valid A | valid A | A; both source records retained |
| valid A | valid B | stable source-aware conflict error |
| invalid | absent | fail-fast |
| absent | invalid | fail-fast |
| invalid | valid | invalid source fails; no overwrite |
| valid | invalid | invalid source fails; no overwrite |
| empty/whitespace | any | fail-fast |

Explicit `null` is a present invalid declaration, not absence. Resolution is
read-only and deterministic. The previous nested-silently-overwrites-top-level
behavior is removed.

## 7. Conditional env_cfg propagation

`smoke_defaults_from_config()` resolves the two declaration sources once and
adds a canonical profile default only when a declaration is explicit.

`apply_scenario_config_to_env_cfg()` preflights an explicit profile before any
environment-config mutation, then writes only:

```text
env_cfg.assignment_lifecycle_profile = canonical_builtin_string
```

It does not write provenance, enum, registry object, resolved dataclass,
runtime route, or checkpoint family.

When profile declaration/argument state is absent:

- no profile `setattr` occurs;
- no profile instance field is created;
- a class/default `legacy` remains untouched;
- a nonempty old scenario still applies its existing unrelated fields exactly;
- repeated application remains deterministic.

Both Mapping and `argparse.Namespace` apply paths are covered.

The event profile is accepted and applied only as a primitive string. A1b does
not construct an event runner, enable a resolver/DVM, create checkpoint state,
or claim runtime readiness.

## 8. Existing-profile prerequisite preflight

The pure preflight reads scenario/argument primitives without modifying or
filling them. It first reuses the existing scenario primitive validators, then
checks the profile combination.

| Profile | A1b preflight |
|---|---|
| `legacy` | raw resolver effective bool must be false |
| `lifecycle_ablation` | raw resolver, cooldown, redirect guardrail, and failed-pair memory must be false |
| `lifecycle_contract_c` | cooldown true; trigger `budget` or `budget_and_streak`; duration positive; cooldown action mask false; redirect false; failed-pair memory false |
| `diagnostics_hidden_state` | raw resolver effective bool must be true |
| `event_gated_local_mrta` | no Contract C/runtime prerequisite reuse in A1b |

### Contract C resolver clarification

The instruction's “resolver enabled” wording was checked against current code
rather than interpreted as a new raw flag requirement.

Current `AssignmentHarlWrapper`:

1. does not inspect `assignment_lifecycle_resolver_enabled` in the Contract C
   branch;
2. returns profile mapping `resolver_enabled=True`;
3. builds resolver config from that profile-derived effective value.

Current controlled Contract C tests also start with the raw resolver flag false
or omit it. Therefore A1b preserves existing semantics: Contract C's effective
resolver is profile-derived true, while the raw flag may be false, true, or
absent. Requiring raw true here would reject currently accepted train/play
configuration and would be an unauthorized validation tightening.

This interpretation does not make A1b the final production authority. A1c and
the current wrapper must still validate post-bootstrap state.

### Primitive-validation boundary

The scenario validators are deliberately stricter than some wrapper coercions
for noncanonical input (for example explicit non-boolean values). The parity
claim is profile-combination parity after scenario primitive validation, not
byte-for-byte parity with every wrapper `bool()`/`int()` coercion.

The preflight reads scenario/args, not a post-Hydra/directly-mutated `env_cfg`.
It also propagates only the profile string, not the raw resolver flag. Those
authority/wiring concerns remain A1c work.

## 9. Default-off identity evidence

Parent and clean-child tests prove the profile-absent cohort:

- empty and representative nonempty profile-absent scenarios do not create an
  `assignment_lifecycle_profile` instance field;
- primitive state changes only for pre-existing explicitly supplied fields;
- the class/default `legacy` remains unchanged;
- RNG state is unchanged;
- environment variables are unchanged;
- cwd and `sys.path` are unchanged;
- logger names/root handlers are unchanged;
- temporary/source directory snapshots are unchanged;
- no Isaac/AppLauncher/HARL/torch/NumPy/checkpoint/assignment-profile-contract
  module is imported by the scenario clean-child path;
- no stdout/stderr is emitted.

This is a D0 absent-declaration identity claim. It is not a claim that explicit
profile scenarios retain previous output identity.

## 10. Canonical import boundary

The test statically verifies:

- exactly one five-profile tuple literal;
- shared normalization use by declaration resolution, prerequisite validation,
  and argument validation;
- metadata validation routes through the source-aware declaration resolver;
- no contract module/type reference or import;
- no contract relative-to-bare fallback;
- no `sys.modules` access;
- no scenario-owned enum/dataclass/custom-exception identity.

A1a canonical module identity and its wrong-key guard remain unchanged and pass
all A1a regressions.

## 11. Tests and command results

Final authorized commands:

```text
python -m py_compile scenario_config.py test_assignment_profile_contract.py
  exit 0

python scripts/environments/test_assignment_profile_contract.py --json
  exit 0
  A1a: 11/11 passed
  A1b: 5/5 passed
  combined: 16/16 passed

python scripts/environments/test_assignment_initial_condition_contract.py --json
  exit 0
  9/9 passed

git status --short --untracked-files=all
  exit 0
  known Phase A/A1a cohort plus authorized A1b files only

git diff --name-status
  exit 0
  tracked modifications: TASK_PROGRESS.md and scenario_config.py

git diff --check
  exit 0

git diff --cached --name-status
  exit 0
  empty index
```

The historical regression was run only after its pure boundary was confirmed
by the A1a AST test.

No AppLauncher, Isaac environment, HARL actor, training, playback, formal
evaluation, or checkpoint I/O test was run.

## 12. Intentional behavior correction

```text
intentional behavior correction:
  explicit scenario lifecycle profile is now propagated

top/nested conflict correction:
  conflicting declarations now fail instead of nested silently winning

default-off identity:
  absent declaration remains unchanged

runtime assignment behavior:
  not activated or tested

production resolved-object wiring:
  not implemented
```

The explicit-profile correction is not described as byte identity for all old
scenarios.

## 13. Deferred A1c work

A1c still owns:

- canonical `ResolvedAssignmentProfile` creation in production entrypoints;
- same-object/same-class consumer propagation;
- formal-entrypoint versus direct-wrapper-fallback authority;
- production readiness guards;
- event profile fail-closed ordering before current wrapper/runtime consumers;
- runner/wrapper/checkpoint/playback consumer wiring;
- manual-apply entrypoints that do not use the shared scenario apply helper;
- post-bootstrap mismatch validation;
- end-to-end diagnostics raw-resolver propagation guarantees.

No part of that work was started.

## 14. Risks and blockers

No A1b blocker remains.

Residual review risks:

1. Review should explicitly accept the code-derived Contract C raw/effective
   resolver distinction above.
2. The event string can now reach `env_cfg`, but the current wrapper has no event
   runtime branch. A1c must install a pre-runtime readiness guard before anyone
   executes that profile.
3. A1b's preflight is not final authority for callers that mutate `env_cfg`
   after validation.
4. Diagnostics needs a caller to propagate its raw resolver flag separately;
   A1b intentionally propagates profile string only.
5. Scenario primitive validation is stricter than wrapper coercion for some
   noncanonical raw types.

Independent read-only reviews found no declaration/apply or prerequisite
semantic blocker after the final corrections.

## 15. Final classification

```text
classification:
  PHASE-A1B-IMPLEMENTATION-COMPLETE-AWAITING-GPT-REVIEW

scenario parse/apply behavior changed:
  yes -- explicit profile propagation and conflict correction

absent/default profile identity:
  preserved

runtime assignment behavior changed:
  no

Isaac/AppLauncher:
  not run

training/playback/formal evaluation:
  not run

checkpoint I/O:
  none

installed HARL:
  unchanged

commit:
  none

A1b:
  stopped for GPT/user review

A1c:
  not entered

A2–A6:
  not entered

Phase B0/B/C/D/E:
  not entered
```
