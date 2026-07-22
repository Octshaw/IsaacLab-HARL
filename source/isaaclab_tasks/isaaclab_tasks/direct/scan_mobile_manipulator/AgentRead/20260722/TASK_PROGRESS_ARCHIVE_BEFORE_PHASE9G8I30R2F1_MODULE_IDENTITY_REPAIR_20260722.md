# TASK_PROGRESS

## Current Status

Phase 9G-8I-3-0R-2F completed the documentation-only design for repairing the
explicit-profile runtime module-identity boundary.

Classification:

~~~text
MODULE-IDENTITY-REPAIR-DESIGN-READY
~~~

Starting committed baseline remains:

~~~text
167bafaac84f7f8f527af40ed786e4834a7db704
167bafaa docs(assignment): validate 100k best-final attribution comparison
~~~

The accepted uncommitted Phase 9G-8I-3-0 through 3-0R-2 chain and all runtime
evidence remain preserved.

## Latest Design Decision

The accepted R-2 default-off runtime result remains valid. Explicit A failed
because the same source file was loaded under two module names:

~~~text
producer:
  assignment_initial_condition

consumer:
  isaaclab_tasks.direct.scan_mobile_manipulator.assignment_initial_condition
~~~

That produced distinct `InitialConditionRequest` class identities and caused
the strict environment `isinstance` check to reject the request.

The design selects this single canonical runtime module:

~~~text
isaaclab_tasks.direct.scan_mobile_manipulator.assignment_initial_condition
~~~

The package-qualified import is unsafe at the existing pre-AppLauncher line
because importing `isaaclab_tasks` recursively enters Isaac task/runtime
modules. The minimal repair therefore freezes:

~~~text
before AppLauncher:
  import-free CLI vocabulary and early usage validation only
  no request/type/factory import

after simulation_app and existing import isaaclab_tasks:
  all request/type/factory/manifest imports from the canonical package module
  canonical CLI revalidation before environment construction
~~~

The environment's package-relative import and strict `isinstance` check remain
unchanged. No `sys.modules` alias, duck typing, class copy, or package bootstrap
redesign is allowed.

## Frozen Implementation Boundary

The next implementation may modify only:

~~~text
scripts/reinforcement_learning/harl/play_assignment.py
scripts/environments/test_assignment_initial_condition_contract.py
~~~

It must add a real canonical producer/consumer class-identity regression and a
static AST import regression. It must preserve default-off behavior, A/B/C
mappings, schemas, fingerprints, manifests, checkpoint behavior, and all
environment semantics.

No change is allowed in `assignment_initial_condition.py`,
`scan_mobile_manipulator_env.py`, `train.py`, YAML/data, attribution collector,
wrapper, checkpoint, reward, resolver, mask, controller, installed HARL, or
Conda files.

## Current Non-Actions

Phase 9G-8I-3-0R-2F changed documentation only. It did not implement the repair,
modify source/tests/YAML, relax type checks, launch AppLauncher/Isaac Sim,
construct an environment, retry A, run B/C, train, use a new seed, run GUI/video,
continue 300k steps, modify installed packages, or commit.

## Next Step

After review and explicit acceptance only:

~~~text
Phase 9G-8I-3-0R-2F-1:
Initial-Condition Runtime Module-Identity Boundary Repair
And Import-Boundary Regression
~~~

F-1 is source/test-only. Runtime retry remains a later separately reviewed
Phase 9G-8I-3-0R-2R boundary.

## Detailed Reports / Archives

- `AgentRead/20260721/PHASE9G8I30R2F_INITIAL_CONDITION_RUNTIME_MODULE_IDENTITY_BOUNDARY_REPAIR_DESIGN.md`
- `AgentRead/20260721/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G8I30R2F_MODULE_IDENTITY_REPAIR_DESIGN_20260721.md`
- `AgentRead/20260721/PHASE9G8I30R2_CONTROLLED_INITIAL_CONDITION_RUNTIME_IDENTITY_VALIDATION.md`
- `AgentRead/20260721/PHASE9G8I30R1_CONTROLLED_INITIAL_CONDITION_INTERFACE_IMPLEMENTATION_AND_REGRESSION.md`
- `AgentRead/20260721/PHASE9G8I30R_CONTROLLED_INITIAL_CONDITION_VARIATION_INTERFACE_AND_CONTRACT_DESIGN.md`
- `AgentRead/20260721/PHASE9G8I30_BEST_FINAL_ROBUSTNESS_AND_LATE_TRAINING_REGRESSION_DIAGNOSIS_DESIGN.md`
