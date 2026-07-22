# Phase 9G-8I-3-0R-2F-1: Initial-Condition Module-Identity Repair And Import-Boundary Regression

Phase lineage date: 2026-07-21
Implementation completed: 2026-07-22

## 1. Classification

~~~text
RUNTIME-IDENTITY-RETRY-READY
~~~

The frozen two-file repair is complete. Playback now obtains every
initial-condition request-producing runtime symbol from the canonical package
module after SimulationApp startup and task-package registration. The
environment's package-relative consumer import and strict `isinstance`
boundary remain unchanged.

All required pure/static regressions pass. This classification authorizes only
a separately reviewed bounded runtime identity retry. No runtime retry occurred
in this phase.

## 2. Starting Repository State

~~~text
HEAD:
  167bafaac84f7f8f527af40ed786e4834a7db704

git log -1 --oneline:
  167bafaa docs(assignment): validate 100k best-final attribution comparison
~~~

The preflight worktree contained only the accepted uncommitted Phase
9G-8I-3-0 through R-2F chain:

~~~text
M  scripts/reinforcement_learning/harl/play_assignment.py
M  scripts/reinforcement_learning/harl/train.py
M  AgentRead/TASK_PROGRESS.md
M  scan_mobile_manipulator_env.py

?? scripts/environments/test_assignment_initial_condition_contract.py
?? assignment_initial_condition.py
?? accepted 20260721 reports and TASK_PROGRESS archives
~~~

`git diff --check` passed at preflight with line-ending warnings only. No
unrelated production, test, YAML/data, result, checkpoint, configuration, or
documentation change was present. The accepted R-2 runtime evidence was not
cleaned, moved, renamed, overwritten, or reused.

## 3. Accepted R-2 Authority

The accepted R-2 result remains:

~~~text
classification: RUNTIME-IDENTITY-FAIL

no-selector:
  exit 0
  300 decisions
  900 robot rows
  exact historical rows and segment bytes
  exact normalized-summary semantics

explicit A:
  failed before environment construction and checkpoint loading
  duplicate producer/consumer class identities

B/C:
  not run
~~~

The repair does not rerun or reinterpret the accepted no-selector evidence.

## 4. Files Inspected

Read or inspected for the repair:

~~~text
AgentRead/AGENTS.md
AgentRead/TASK_PROGRESS.md
AgentRead/20260721/PHASE9G8I30R2F_..._DESIGN.md
AgentRead/20260721/PHASE9G8I30R2_..._VALIDATION.md

scripts/reinforcement_learning/harl/play_assignment.py
scripts/reinforcement_learning/harl/train.py
scripts/environments/test_assignment_initial_condition_contract.py

assignment_initial_condition.py
scan_mobile_manipulator_env.py
assignment_playback_attribution_diagnostics.py
checkpoint, lifecycle observation, and lifecycle mask regression boundaries
~~~

## 5. Files Changed In F-1

Production/test changes were confined exactly to:

~~~text
scripts/reinforcement_learning/harl/play_assignment.py
scripts/environments/test_assignment_initial_condition_contract.py
~~~

Documentation created/updated:

~~~text
AgentRead/20260722/
  PHASE9G8I30R2F1_INITIAL_CONDITION_MODULE_IDENTITY_REPAIR_AND_IMPORT_BOUNDARY_REGRESSION.md
  TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G8I30R2F1_MODULE_IDENTITY_REPAIR_20260722.md

AgentRead/TASK_PROGRESS.md
~~~

No other production or test file was changed by this phase.

## 6. Playback Import Repair

### 6.1 Removed Defective Producer Import

Removed from the pre-AppLauncher production path:

~~~python
from assignment_initial_condition import (...)
~~~

`play_assignment.py` now has no top-level `from assignment_initial_condition`
or plain `import assignment_initial_condition` statement.

### 6.2 Import-Free Prelaunch Layer

Before AppLauncher, playback defines only this immutable CLI vocabulary:

~~~text
baseline_identity
pose_cycle_forward
pose_cycle_reverse
~~~

The local `_validate_initial_condition_prelaunch_cli` helper:

~~~text
accepts None immediately
rejects an unknown profile
requires attribution logging for an explicit profile
requires an output path for an explicit profile
rejects an existing non-directory
rejects an existing nonempty directory
~~~

It does not import or construct a request/dataclass, define pose mappings,
resolve condition schemas, hash a condition, or write a manifest. The tuple is
used only by argparse choices and this early usage check.

### 6.3 Canonical Post-AppLauncher Import

The target import now occurs after both:

~~~python
app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app
...
import isaaclab_tasks
~~~

The exact module is:

~~~text
isaaclab_tasks.direct.scan_mobile_manipulator.assignment_initial_condition
~~~

Imported symbols are exactly:

~~~text
INITIAL_CONDITION_MANIFEST_FILENAME
INITIAL_CONDITION_PROFILE_CHOICES
InitialConditionRunProvenance
build_initial_condition_manifest
make_initial_condition_request
make_playback_policy_interface_contract
validate_initial_condition_output_files
validate_initial_condition_playback_cli
validate_initial_condition_runtime_interface
write_initial_condition_manifest_atomic
~~~

No unused request class was imported merely for testing.

### 6.4 Canonical Vocabulary Revalidation

After the canonical import, playback requires exact ordered equality between
the local CLI tuple and canonical `INITIAL_CONDITION_PROFILE_CHOICES`. Drift
raises a clear startup `RuntimeError` before request or wrapper construction.

The canonical `validate_initial_condition_playback_cli` is then run using the
resolved CLI values before `_attach_initial_condition_request` can create a
request and before `make_assignment_harl_env` can construct the wrapper.

### 6.5 Request Construction

The explicit-profile request remains constructed only by the canonical
`make_initial_condition_request` factory, using the canonical policy-interface
factory. The resulting object is attached through the existing frozen
environment configuration handoff.

When the selector is `None`, `_attach_initial_condition_request` still returns
immediately. No request is constructed or attached.

## 7. Module-Identity Evidence

The new clean child-process regression loaded
`assignment_initial_condition.py` under only this key:

~~~text
isaaclab_tasks.direct.scan_mobile_manipulator.assignment_initial_condition
~~~

It created a real `baseline_identity` request through the production policy and
request factories. Recorded evidence:

~~~text
ProducerClass is ConsumerClass:
  True

request.__class__ is ConsumerClass:
  True

isinstance(request, ConsumerClass):
  True

request.__class__.__module__:
  isaaclab_tasks.direct.scan_mobile_manipulator.assignment_initial_condition

request.profile_id:
  baseline_identity

canonical sys.modules key present:
  True

conflicting top-level assignment_initial_condition key present:
  False
~~~

The child did not import AppLauncher, Isaac Lab, the environment, HARL, or a
checkpoint. Its one canonical `sys.modules` registration is ordinary isolated
module loading for the regression, not a production alias.

## 8. AST And Consumer Boundary Evidence

The AST regression proves:

~~~text
exactly one package-qualified playback target import
canonical import after simulation_app assignment
canonical import after import isaaclab_tasks
canonical validation after canonical import
canonical validation before request and wrapper construction
prelaunch usage validation before AppLauncher construction
argparse uses the local import-free tuple
local and canonical tuples are exactly equal and ordered
no top-level target import in playback
no production sys.modules access/alias in playback
~~~

Static inspection of `scan_mobile_manipulator_env.py` proves that it retains:

~~~python
from .assignment_initial_condition import InitialConditionRequest
...
isinstance(request, InitialConditionRequest)
~~~

The consumer was not modified and the type boundary was not relaxed.

## 9. Default-Off And Semantic Isolation

Preserved default-off contract:

~~~text
CLI default remains None
prelaunch None validation returns immediately
request attachment returns before factory construction
environment profile/request None branch remains immediate
no condition resolution, hashing, fingerprint, diagnostic line, or manifest
historical attribution path remains three artifacts
~~~

The accepted R-2 no-selector runtime identity remains the runtime authority;
no redundant runtime replay was run here.

Unchanged semantics include:

~~~text
A/B/C mappings and pose coordinates
WXYZ-to-XYZYaw conversion
condition contract and manifest schemas
canonical JSON and condition SHA-256
manifest writer and explicit four-file output contract
checkpoint manifest/load/save compatibility
training hard guard
environment pose application and reset order
robot identities, actor mapping, capabilities, scanner offsets
M/N and 1059/3183/51 interfaces
reward, resolver, Contract C, ownership/arbitration
mask, cooldown/budget, controller, completion
~~~

## 10. Verification Results

Pinned interpreter:

~~~text
C:\isaacenvs\isaac45_harl\python.exe
~~~

### 10.1 Syntax

~~~powershell
D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/reinforcement_learning/harl/play_assignment.py scripts/environments/test_assignment_initial_condition_contract.py
~~~

Result: PASS.

### 10.2 Initial-Condition Contract And Identity

~~~powershell
D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python scripts/environments/test_assignment_initial_condition_contract.py --json
~~~

Result: PASS 9/9 groups. The JSON output contains the explicit identity,
canonical-key, top-level-key, AST-order, consumer-import, and strict-type-check
evidence listed above.

### 10.3 Playback Attribution

~~~powershell
D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python scripts/environments/test_assignment_playback_attribution_diagnostics.py --json
~~~

Result: PASS 16/16.

### 10.4 Checkpoint Contract

~~~powershell
D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python scripts/environments/test_assignment_checkpoint_contract_core.py
~~~

Result: PASS 28/28.

### 10.5 Lifecycle Regressions

~~~powershell
D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python scripts/environments/test_assignment_lifecycle_observation_integration.py

D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python scripts/environments/test_assignment_lifecycle_mask_and_harl_replay.py
~~~

Results:

~~~text
lifecycle observation integration:  PASS 6/6
lifecycle mask / HARL replay:        PASS 11/11
~~~

The latter emitted only the installed Gym deprecation notice; all tests passed.

### 10.6 Static Isolation

`git diff --check` passed with line-ending warnings only. Repository searches
show:

~~~text
play_assignment.py:
  canonical package import present
  top-level target import absent
  sys.modules alias absent

scan_mobile_manipulator_env.py:
  package-relative consumer import preserved
  strict isinstance preserved

train.py:
  accepted pre-existing top-level training guard import remains unchanged

standalone pure test:
  accepted top-level pure import remains for its isolated test process
  child identity group registers only the canonical target key
~~~

No forbidden source path was edited in F-1.

## 11. Runtime-Deferred Items

This phase deliberately does not prove runtime explicit A after the repair. It
does not validate A pose/scanner/reset identity, A/no-selector equivalence, B/C
repeatability, or behavioral distinctness. Those checks remain confined to a
separately reviewed runtime retry.

## 12. Explicit Non-Actions

~~~text
No AppLauncher or Isaac Sim launch.
No environment construction or reset/step.
No playback retry and no A/B/C execution.
No final-checkpoint or best/final comparison.
No checkpoint loading or continuation.
No training, new seed, stochastic action, GUI/video, or 300k continuation.
No YAML/data, profile, mapping, pose, schema, fingerprint, or manifest change.
No checkpoint semantic change.
No environment consumer change and no isinstance relaxation.
No production sys.modules alias.
No installed HARL or Conda modification.
No commit.
~~~

## 13. Next Recommendation

Recommend only:

~~~text
Phase 9G-8I-3-0R-2R:
Controlled Initial-Condition Runtime Identity Validation Retry
~~~

That future phase must preserve all prior R-2 evidence, use new output/log
paths, reuse the accepted no-selector result, validate explicit A before B,
and validate B before C. It must remain separately reviewed and was not
started automatically.
