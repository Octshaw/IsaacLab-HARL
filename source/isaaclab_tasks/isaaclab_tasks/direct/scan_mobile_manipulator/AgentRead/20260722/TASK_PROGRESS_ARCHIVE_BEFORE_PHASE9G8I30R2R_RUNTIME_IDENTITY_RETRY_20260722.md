# TASK_PROGRESS

## Current Status

Phase 9G-8I-3-0R-2F-1 implemented the canonical initial-condition runtime
module-identity repair and completed the import-boundary regressions.

Classification:

~~~text
RUNTIME-IDENTITY-RETRY-READY
~~~

Starting committed baseline remains:

~~~text
167bafaac84f7f8f527af40ed786e4834a7db704
167bafaa docs(assignment): validate 100k best-final attribution comparison
~~~

The accepted uncommitted Phase 9G-8I-3-0 through R-2F-1 chain and all prior R-2
runtime evidence remain preserved. No commit was made.

## Latest Completed Phase

Playback no longer imports the request producer under the defective top-level
module identity. Before AppLauncher it now retains only an import-free CLI
profile tuple and early usage checks. After SimulationApp startup and the
existing `import isaaclab_tasks`, all initial-condition runtime symbols come
from:

~~~text
isaaclab_tasks.direct.scan_mobile_manipulator.assignment_initial_condition
~~~

The local profile tuple is checked for exact ordered equality with the
canonical registry, and canonical CLI validation runs before request or wrapper
construction. Explicit requests are created only through the canonical factory.

The clean child-process regression proves:

~~~text
ProducerClass is ConsumerClass:            True
request.__class__ is ConsumerClass:         True
isinstance(request, ConsumerClass):         True
canonical sys.modules key present:          True
conflicting top-level target key present:   False
~~~

AST guards prove the canonical import occurs after `simulation_app` and task
package registration, while the environment retains its package-relative
consumer import and strict `isinstance` check.

## Latest Verification

~~~text
py_compile:                                  PASS
initial-condition contract/identity:         PASS 9/9
playback attribution diagnostics:            PASS 16/16
checkpoint contract core:                    PASS 28/28
lifecycle observation integration:           PASS 6/6
lifecycle mask / HARL replay:                 PASS 11/11
git diff --check:                             PASS, line-ending warnings only
~~~

Tests used `C:\isaacenvs\isaac45_harl\python.exe` and did not import or launch
AppLauncher/Isaac Sim.

## Changed Files

Phase F-1 production/test changes were confined to:

~~~text
scripts/reinforcement_learning/harl/play_assignment.py
scripts/environments/test_assignment_initial_condition_contract.py
~~~

The report, archive, and this handoff are the only F-1 documentation changes.
`assignment_initial_condition.py`, `scan_mobile_manipulator_env.py`, `train.py`,
YAML/data, attribution, wrapper, checkpoint, reward, resolver, mask, controller,
installed HARL, and Conda files were not modified by F-1.

## Current Non-Actions

No AppLauncher, Isaac Sim, environment construction, playback retry, A/B/C run,
checkpoint load, training, new seed, stochastic action, GUI/video, best/final
comparison, or 300k continuation occurred. No type check was relaxed, no
production `sys.modules` alias was added, and no commit was made.

The accepted R-2 no-selector run remains the default-off runtime authority. F-1
does not claim explicit-profile runtime success; it proves the repaired import
boundary statically and in an isolated pure child process.

## Next Step

After review and explicit acceptance only:

~~~text
Phase 9G-8I-3-0R-2R:
Controlled Initial-Condition Runtime Identity Validation Retry
~~~

R-2R must preserve all earlier evidence, use new output/log paths, reuse the
accepted no-selector result, run and validate explicit A first, and only then
proceed sequentially to repeated B and C runs. Do not start it automatically.

## Detailed Reports / Archives

- `AgentRead/20260722/PHASE9G8I30R2F1_INITIAL_CONDITION_MODULE_IDENTITY_REPAIR_AND_IMPORT_BOUNDARY_REGRESSION.md`
- `AgentRead/20260722/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G8I30R2F1_MODULE_IDENTITY_REPAIR_20260722.md`
- `AgentRead/20260721/PHASE9G8I30R2F_INITIAL_CONDITION_RUNTIME_MODULE_IDENTITY_BOUNDARY_REPAIR_DESIGN.md`
- `AgentRead/20260721/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G8I30R2F_MODULE_IDENTITY_REPAIR_DESIGN_20260721.md`
- `AgentRead/20260721/PHASE9G8I30R2_CONTROLLED_INITIAL_CONDITION_RUNTIME_IDENTITY_VALIDATION.md`
- `AgentRead/20260721/PHASE9G8I30R1_CONTROLLED_INITIAL_CONDITION_INTERFACE_IMPLEMENTATION_AND_REGRESSION.md`
- `AgentRead/20260721/PHASE9G8I30R_CONTROLLED_INITIAL_CONDITION_VARIATION_INTERFACE_AND_CONTRACT_DESIGN.md`
- `AgentRead/20260721/PHASE9G8I30_BEST_FINAL_ROBUSTNESS_AND_LATE_TRAINING_REGRESSION_DIAGNOSIS_DESIGN.md`
