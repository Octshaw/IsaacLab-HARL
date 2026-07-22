# Phase 9G-8I-3-0R-2F: Initial-Condition Runtime Module-Identity Boundary Repair Design

Date: 2026-07-21

## 1. Classification

~~~text
MODULE-IDENTITY-REPAIR-DESIGN-READY
~~~

The R-2 root cause is confirmed and a two-file repair is available. The
runtime request producer and consumer will use exactly one package-qualified
module object. The strict `isinstance` boundary remains unchanged. No source or
test implementation is part of this phase.

## 2. Starting Repository Preflight

~~~text
HEAD:
  167bafaac84f7f8f527af40ed786e4834a7db704

git log -1 --oneline:
  167bafaa docs(assignment): validate 100k best-final attribution comparison
~~~

The worktree contains only the accepted uncommitted Phase 9G-8I-3-0, 3-0R,
3-0R-1, and 3-0R-2 chain:

~~~text
M  scripts/reinforcement_learning/harl/play_assignment.py
M  scripts/reinforcement_learning/harl/train.py
M  scan_mobile_manipulator_env.py
M  AgentRead/TASK_PROGRESS.md

?? assignment_initial_condition.py
?? test_assignment_initial_condition_contract.py
?? accepted 20260721 reports and TASK_PROGRESS archives
~~~

`git diff --check` passed with line-ending warnings only. There was no
unrelated production, test, YAML, data, result, checkpoint, or documentation
change. The accepted R-2 no-selector output and both R-2 console logs remain
preserved outside Git.

## 3. Accepted R-2 Evidence

Phase 9G-8I-3-0R-2 remains accepted as:

~~~text
RUNTIME-IDENTITY-FAIL
~~~

The default-off no-selector run passed 300 decisions and 900 rows. Its rows and
segments are byte-identical to the accepted historical best run, and its
summary is identical after output-path normalization. That result remains the
default-off runtime authority.

Explicit `baseline_identity` failed before environment construction and before
checkpoint loading:

~~~text
InitialConditionContractError:
explicit assignment_initial_condition_profile requires a project-owned
InitialConditionRequest
~~~

No retry and no B/C execution occurred. The failure is not related to pose
values, checkpoint contents, resolver, mask, controller, GPU, or numerical
health.

## 4. Files And Import Boundaries Inspected

Read completely:

~~~text
AgentRead/AGENTS.md
AgentRead/TASK_PROGRESS.md
AgentRead/20260721/PHASE9G8I30R_..._DESIGN.md
AgentRead/20260721/PHASE9G8I30R1_..._IMPLEMENTATION_AND_REGRESSION.md
AgentRead/20260721/PHASE9G8I30R2_..._RUNTIME_IDENTITY_VALIDATION.md
~~~

Inspected statically:

~~~text
scripts/reinforcement_learning/harl/play_assignment.py
scripts/reinforcement_learning/harl/train.py
scripts/environments/test_assignment_initial_condition_contract.py

assignment_initial_condition.py
scan_mobile_manipulator_env.py
scenario_config.py
assignment_playback_attribution_diagnostics.py

isaaclab_tasks/__init__.py
isaaclab_tasks/utils/__init__.py
isaaclab_tasks/utils/importer.py
isaaclab_tasks/utils/parse_cfg.py
isaaclab_tasks/direct/__init__.py
isaaclab_tasks/direct/scan_mobile_manipulator/__init__.py
isaaclab/app/__init__.py
isaaclab/app/app_launcher.py
~~~

Repository-wide searches covered every Python import of
`assignment_initial_condition`, every `sys.path` mutation in the playback
entry, and every relevant `sys.modules` reference or alias mechanism.

## 5. Exact Duplicate-Identity Proof

Current producer import in `play_assignment.py`:

~~~python
from assignment_initial_condition import make_initial_condition_request
~~~

Current consumer import in `scan_mobile_manipulator_env.py`:

~~~python
from .assignment_initial_condition import InitialConditionRequest
~~~

They resolve the same source file under different module keys:

~~~text
producer module key:
  assignment_initial_condition

consumer module key:
  isaaclab_tasks.direct.scan_mobile_manipulator.assignment_initial_condition
~~~

Consequently the current identities are:

~~~text
producer InitialConditionRequest.__module__:
  assignment_initial_condition

consumer InitialConditionRequest.__module__:
  isaaclab_tasks.direct.scan_mobile_manipulator.assignment_initial_condition

ProducerClass is ConsumerClass:
  False

request.__class__ is ConsumerClass:
  False

isinstance(request, ConsumerClass):
  False
~~~

Python caches by module name, not by resolved file path. Loading one file under
two names creates two module objects, runs its class declarations twice, and
therefore creates distinct dataclass identities. The R-2 exception is the
expected result of that exact condition.

No project source currently creates an alias between these names. The only
assignment initial-condition imports are the playback top-level producer, the
training top-level usage guard, the standalone pure test, and the environment's
package-relative consumer.

## 6. Import Bootstrap Audit

`play_assignment.py` adds both of these paths:

~~~text
source/isaaclab_tasks
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator
~~~

The second path is why top-level imports such as
`assignment_initial_condition` succeed. The first makes the
`isaaclab_tasks...` package available after simulator startup.

### 6.1 Playback Import Classification

| Import | Current category | Timing and use |
| --- | --- | --- |
| `argparse`, `datetime`, `math`, `pathlib`, `subprocess`, `sys`, `typing` | Standard library | Before AppLauncher |
| `torch` | Third-party/runtime | Before AppLauncher; CUDA warm start |
| `scenario_config` | Task-local top-level through scan source path | Before AppLauncher; scenario defaults and validation |
| `assignment_playback_attribution_diagnostics` | Task-local top-level through scan source path | Before AppLauncher; attribution CLI and later collector |
| `assignment_initial_condition` | Task-local top-level through scan source path | Before AppLauncher; defective request producer |
| `isaaclab.app.AppLauncher` | Isaac runtime | Parser setup and simulator launch |
| HARL actor/model imports | HARL runtime | After simulator launch |
| `isaaclab.envs` | Isaac runtime | After simulator launch |
| `isaaclab_tasks` | Package-qualified task registration | After simulator launch |
| assignment adapter/checkpoint/wrapper | Package-qualified project runtime | After task registration |

The scenario helper mutates resolved configuration but does not pass one of its
classes into an environment `isinstance` boundary. The attribution helper is
owned and consumed by the playback script. Neither currently crosses a
producer/consumer class-identity boundary. They do not need to be redesigned in
this narrow repair.

The scan-task source path remains necessary for those pre-launch pure imports
and for current lightweight script conventions. Removing it would broaden the
repair and is rejected.

### 6.2 Why A Same-Location Package Import Is Unsafe

The exact package-qualified initial-condition import is not safe at the
current pre-AppLauncher line:

1. Importing `isaaclab_tasks...` executes `isaaclab_tasks/__init__.py`.
2. That imports `isaaclab_tasks.utils`, whose `__init__.py` imports
   `parse_cfg.py`.
3. `parse_cfg.py` imports `isaaclab.envs`.
4. Task package discovery recursively imports direct task packages, including
   the scan environment.
5. Those runtime imports require the Isaac/Omniverse application ordering.

`AppLauncher._create_app` explicitly initializes `SimulationApp` before
extensions and runtime modules are loaded. Therefore merely replacing the
existing pre-launch top-level import with a package-qualified import is not the
safe repair.

### 6.3 Safe Canonical Import Point

The existing playback order already provides a safe point:

~~~text
app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app
...
import isaaclab_tasks
~~~

`import isaaclab_tasks` registers the scan package, whose environment imports
`.assignment_initial_condition` under the canonical package key. An explicit
package-qualified producer import immediately after this line retrieves the
same existing module object. It does not execute a second copy.

## 7. Canonical Module Decision

Frozen canonical name:

~~~text
isaaclab_tasks.direct.scan_mobile_manipulator.assignment_initial_condition
~~~

Required post-repair identities:

~~~text
producer InitialConditionRequest.__module__:
  isaaclab_tasks.direct.scan_mobile_manipulator.assignment_initial_condition

consumer InitialConditionRequest.__module__:
  isaaclab_tasks.direct.scan_mobile_manipulator.assignment_initial_condition

request.__class__.__module__:
  isaaclab_tasks.direct.scan_mobile_manipulator.assignment_initial_condition

ProducerClass is ConsumerClass:
  True

request.__class__ is ConsumerClass:
  True

isinstance(request, ConsumerClass):
  True
~~~

The playback production process must not import the target file under the
top-level key `assignment_initial_condition`.

## 8. Selected Minimal Repair

Select Option A, with import relocation required by the verified AppLauncher
bootstrap boundary.

### 8.1 Pre-AppLauncher CLI Layer

Remove the current top-level `assignment_initial_condition` import entirely.
Keep only import-free CLI metadata and a narrow pre-launch usage check local to
`play_assignment.py`:

~~~text
profile vocabulary:
  baseline_identity
  pose_cycle_forward
  pose_cycle_reverse

pre-launch checks:
  selector None returns immediately
  unknown profile remains an argparse choices error
  explicit profile requires attribution logging
  explicit profile requires an output directory
  existing non-directory fails
  an existing output directory containing any file fails
~~~

This layer must not define, copy, import, construct, or inspect
`InitialConditionRequest` or any condition-contract dataclass. It owns no pose
mapping, schema, fingerprint, or manifest behavior.

The local CLI tuple is an early parser vocabulary only. After simulator launch,
it must be checked against canonical `INITIAL_CONDITION_PROFILE_CHOICES`; any
drift is a startup error before wrapper/environment construction.

### 8.2 Post-AppLauncher Canonical Layer

Immediately after the existing `import isaaclab_tasks`, import all current
initial-condition runtime symbols from:

~~~python
from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_initial_condition import (...)
~~~

This includes `InitialConditionRequest`, `make_initial_condition_request`, the
policy-interface factory, runtime validator, manifest/provenance functions,
canonical CLI validator, filename, and profile choices used by playback.

Before `make_assignment_harl_env`:

1. Assert the pre-launch profile tuple equals the canonical tuple.
2. Re-run the canonical CLI validator using the resolved command values.
3. Construct the request only through the canonical factory.

The canonical revalidation preserves one semantic owner. The pre-launch helper
exists only to retain the accepted early-failure behavior without importing the
Isaac task package too early.

### 8.3 Unchanged Consumer

Keep the environment import exactly package-relative:

~~~python
from .assignment_initial_condition import InitialConditionRequest
~~~

Keep the strict check exactly:

~~~python
isinstance(request, InitialConditionRequest)
~~~

No `scan_mobile_manipulator_env.py` change is permitted by this repair.

## 9. Rejected Alternatives

| Option | Decision | Reason |
| --- | --- | --- |
| A. Package-qualified playback import | Selected | Aligns producer with the package-relative consumer; relocation handles startup ordering |
| B. Top-level import everywhere | Rejected | Breaks package ownership, requires an environment change, and preserves duplicate-import risk |
| C. Remove or weaken `isinstance` | Rejected | Hides the import defect and accepts foreign lookalike objects |
| D. `sys.modules` alias | Rejected | Order-dependent masking rather than a canonical import repair |
| Remove all task-local `sys.path` setup | Rejected | Unrelated bootstrap redesign with unnecessary risk |
| Modify package `__init__.py` for lightweight import | Rejected | Broad package-wide semantic and startup change |
| Copy/redefine `InitialConditionRequest` | Rejected | Creates another type owner and violates the contract |

No alias, duck typing, protocol substitution, deserialization conversion, or
mapping reconstruction is allowed.

## 10. Strict Type-Boundary Proof Contract

The central future regression must prove:

~~~python
ProducerClass is ConsumerClass
request.__class__ is ConsumerClass
isinstance(request, ConsumerClass)
~~~

It must also prove:

~~~text
canonical key exists in sys.modules
top-level assignment_initial_condition is not used by the playback handoff
request.profile_id is the selected profile
~~~

The strict check should pass because import identity is correct, not because the
check was relaxed.

## 11. Real Import-Boundary Regression Design

Extend the existing
`scripts/environments/test_assignment_initial_condition_contract.py` with one
focused group.

Normal import of the full `isaaclab_tasks` package is intentionally unsafe in a
no-AppLauncher test. Use the bounded alternative authorized by the phase:

1. Start a clean child Python process so the existing top-level pure-test
   import cannot contaminate the result.
2. Load the pure source file under the exact canonical module name with
   `importlib.util.spec_from_file_location`; direct pure dependency fallbacks
   remain available through `SCAN_TASK_SOURCE`.
3. Register only the canonical target key, never a top-level alias.
4. Obtain the producer factory and producer class from that canonical module.
5. Resolve the consumer reference through the same canonical module key.
6. Create a real `baseline_identity` request using the production factory and
   frozen policy-interface factory.
7. Assert class identity with `is`, strict `isinstance`, canonical
   `__module__`, expected profile, and absence of a conflicting top-level target
   module key.

This child process does not import `isaaclab_tasks/__init__.py`, AppLauncher,
Isaac Sim, HARL, torch, or the environment. It tests the pure canonical class
identity. The static production-import regression below proves that both real
runtime boundaries select that same canonical key.

No `sys.modules` alias is introduced in production. The test uses the ordinary
module-cache entry for the one canonical module it loads.

## 12. Static Production-Import Regression

Use Python AST inspection rather than a full-file text snapshot.

For `play_assignment.py`, require:

~~~text
one ImportFrom whose module is exactly:
  isaaclab_tasks.direct.scan_mobile_manipulator.assignment_initial_condition

that import occurs after:
  simulation_app = app_launcher.app
  import isaaclab_tasks

no ImportFrom with module:
  assignment_initial_condition

no plain import:
  assignment_initial_condition
~~~

For `scan_mobile_manipulator_env.py`, require the existing relative
`ImportFrom(level=1, module='assignment_initial_condition')` and imported
`InitialConditionRequest` symbol.

Also require:

~~~text
pre-launch CLI validation call precedes AppLauncher construction
canonical CLI validation follows canonical import and precedes wrapper creation
local parser choices equal canonical profile choices
no assignment target sys.modules alias code exists in playback
~~~

These checks focus on the production producer/consumer boundary. Standalone
pure tests may continue importing the module top-level in their isolated test
process; they do not produce a runtime request for the package environment.

## 13. Default-Off Preservation

Freeze the following regressions:

~~~text
CLI default remains None
pre-launch selector-None branch returns immediately
_attach_initial_condition_request returns before request construction
environment profile/request-None branch returns immediately
no-selector performs no condition resolution or hashing
no-selector writes no condition manifest
historical attribution output remains exactly three files
~~~

The existing 16/16 playback-attribution suite must remain unchanged and pass.
No second no-selector runtime is required in the implementation phase; the
accepted R-2 exact historical identity result remains authoritative.

## 14. Condition And Checkpoint Isolation

The repair changes import identity only. It must not change:

~~~text
A/B/C mappings or pose coordinates
WXYZ-to-XYZYaw conversion
condition contract or manifest schema
condition fingerprint payload/canonicalization
manifest writer or four-file explicit-output contract
checkpoint manifest, fingerprint, compatibility, or load purpose
training hard guard
environment application/reset order
robot identity, capabilities, scanner offsets, actor mapping
observation/shared/action dimensions
reward, resolver, mask, Contract C, budget, cooldown, controller, completion
~~~

Any need to alter these semantics blocks implementation and requires a new
design review.

## 15. Frozen Implementation File Map

Future Phase 9G-8I-3-0R-2F-1 may modify only:

~~~text
scripts/reinforcement_learning/harl/play_assignment.py
scripts/environments/test_assignment_initial_condition_contract.py
~~~

No change is needed in `assignment_initial_condition.py`. The package-relative
consumer is already canonical, so `scan_mobile_manipulator_env.py` must remain
unchanged.

Explicitly unchanged:

~~~text
train.py
scenario_config.py and all YAML/data
assignment_initial_condition.py
scan_mobile_manipulator_env.py
assignment_playback_attribution_diagnostics.py
assignment_harl_wrapper.py
all checkpoint modules
reward/resolver/mask/controller modules
installed HARL and Conda files
~~~

The training top-level import is a pre-launch hard-guard helper only. Training
does not create or pass an `InitialConditionRequest`; any selected profile or
request is rejected before runner/environment construction. It therefore is
not part of the failing producer/consumer handoff and remains out of scope. Any
future training support for conditions would require a new canonical-import
audit.

## 16. Future Regression Commands And Evidence

Phase 9G-8I-3-0R-2F-1 must run with the pinned environment:

~~~powershell
D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/reinforcement_learning/harl/play_assignment.py scripts/environments/test_assignment_initial_condition_contract.py

D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python scripts/environments/test_assignment_initial_condition_contract.py --json

D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python scripts/environments/test_assignment_playback_attribution_diagnostics.py --json

D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python scripts/environments/test_assignment_checkpoint_contract_core.py

D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python scripts/environments/test_assignment_lifecycle_observation_integration.py

D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python scripts/environments/test_assignment_lifecycle_mask_and_harl_replay.py
~~~

Required results:

~~~text
new canonical import-boundary group: PASS
initial-condition suite: 9/9 groups or updated equivalent
playback attribution diagnostics: 16/16
checkpoint contract core: 28/28
lifecycle observation integration: 6/6
lifecycle mask/HARL replay: 11/11
ProducerClass is ConsumerClass: True
request.__class__ is ConsumerClass: True
strict isinstance: True
canonical module key: present
conflicting top-level production target: absent
playback top-level target import: absent
git diff --check: PASS
forbidden paths: unchanged
~~~

No AppLauncher or runtime retry is allowed in F-1.

## 17. Future Runtime Retry Boundary

Only after F-1 implementation and regression review may a separate design or
execution authorization create:

~~~text
Phase 9G-8I-3-0R-2R:
Controlled Initial-Condition Runtime Identity Validation Retry
~~~

The retry must use new output and console-log paths. It must preserve all R-2
evidence and must not delete, overwrite, rename, or reuse the failed A path.

Preferred future order:

1. Reuse the accepted R-2 no-selector output rather than rerunning it.
2. Run explicit A first.
3. Validate its manifest, pose/scanner/reset identity, and exact behavioral
   equivalence with accepted R-2 no-selector output.
4. Only after A passes, run B twice and validate repeatability.
5. Only after B passes, run C twice and validate repeatability.

This report freezes no retry path or command and executes none.

## 18. Explicit Non-Actions

~~~text
No production source or test was modified.
No YAML/data or import repair implementation was modified.
No isinstance check was relaxed.
No sys.modules alias was added.
No profile, mapping, pose, schema, fingerprint, manifest, or checkpoint changed.
No AppLauncher or Isaac Sim process was launched.
No environment was constructed.
No playback retry or A/B/C execution occurred.
No final checkpoint or best/final comparison ran.
No training, new seed, GUI/video, or 300k continuation ran.
No installed HARL or Conda file was modified.
No commit was made.
~~~

## 19. Final Recommendation

Accept this phase as:

~~~text
MODULE-IDENTITY-REPAIR-DESIGN-READY
~~~

The only next recommended phase is:

~~~text
Phase 9G-8I-3-0R-2F-1:
Initial-Condition Runtime Module-Identity Boundary Repair
And Import-Boundary Regression
~~~

Do not begin runtime retry automatically after implementation. F-1 must remain
source/test-only and receive review before any AppLauncher execution.
