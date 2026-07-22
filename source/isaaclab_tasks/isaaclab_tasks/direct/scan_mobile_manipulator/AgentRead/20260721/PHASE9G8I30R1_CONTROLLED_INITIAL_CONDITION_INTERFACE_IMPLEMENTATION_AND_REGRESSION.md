# Phase 9G-8I-3-0R-1: Controlled Initial-Condition Interface Implementation And Regression

Date: 2026-07-21

## 1. Classification

~~~text
RUNTIME-IDENTITY-VALIDATION-READY
~~~

The frozen Phase 9G-8I-3-0R interface is implemented within its approved file
map. All new pure/fake/static tests and the relevant existing no-Isaac
regressions pass. Runtime pose identity, reset state, and B/C behavioral safety
remain intentionally deferred to Phase 9G-8I-3-0R-2.

## 2. Starting State

~~~text
HEAD:
  167bafaac84f7f8f527af40ed786e4834a7db704

git log -1 --oneline:
  167bafaa docs(assignment): validate 100k best-final attribution comparison
~~~

The user explicitly retained the uncommitted Phase 9G-8I-3-0 and
9G-8I-3-0R documentation chain. Starting changes were limited to:

~~~text
M  AgentRead/TASK_PROGRESS.md
?? AgentRead/20260721/PHASE9G8I30_..._DESIGN.md
?? AgentRead/20260721/PHASE9G8I30R_..._DESIGN.md
?? their two required TASK_PROGRESS archives
~~~

No unrelated production, test, YAML, result, checkpoint, or documentation
change existed. `git diff --check` passed with only Git's LF-to-CRLF warning.

## 3. Files Inspected

Read completely:

~~~text
AgentRead/AGENTS.md
AgentRead/TASK_PROGRESS.md
AgentRead/20260721/PHASE9G8I30_BEST_FINAL_ROBUSTNESS_AND_LATE_TRAINING_REGRESSION_DIAGNOSIS_DESIGN.md
AgentRead/20260721/PHASE9G8I30R_CONTROLLED_INITIAL_CONDITION_VARIATION_INTERFACE_AND_CONTRACT_DESIGN.md
~~~

Inspected statically:

~~~text
scripts/reinforcement_learning/harl/play_assignment.py
scripts/reinforcement_learning/harl/train.py
scan_mobile_manipulator_env.py
robot_config.py
scenario_config.py
capability_config.py
viewpoint_csv.py
component_mesh.py
assignment_harl_wrapper.py
assignment_playback_attribution_diagnostics.py
assignment_checkpoint_contract.py
assignment_checkpoint_load.py
assignment_checkpoint_save.py
relevant scripts/environments pure tests
the frozen scenario/robot/capability/viewpoint/component source files
~~~

## 4. Files Created And Modified

Created production/test files:

~~~text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/
  assignment_initial_condition.py

scripts/environments/
  test_assignment_initial_condition_contract.py
~~~

Modified production entry/boundary files:

~~~text
scripts/reinforcement_learning/harl/play_assignment.py
scripts/reinforcement_learning/harl/train.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/
  scan_mobile_manipulator_env.py
~~~

Created documentation:

~~~text
AgentRead/20260721/
  PHASE9G8I30R1_CONTROLLED_INITIAL_CONDITION_INTERFACE_IMPLEMENTATION_AND_REGRESSION.md
  TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G8I30R1_INITIAL_CONDITION_IMPLEMENTATION_20260721.md
~~~

Updated `AgentRead/TASK_PROGRESS.md` after creating its archive.

## 5. Pure Contract Module

Selected location:

~~~text
assignment_initial_condition.py
~~~

It imports no Isaac Lab, HARL, torch, AppLauncher, or simulation package. It
uses only standard Python and existing pure project loaders/helpers.

Implemented immutable types include:

~~~text
InitialConditionProfile
InitialConditionRequest
ResolvedFileReference
PolicyInterfaceContract
CapabilityBinding
ResolvedRobotIdentity
ResolvedComponentIdentity
ResolvedInitialConditionConfig
PoseSlot
ResolvedRobotPose
InitialConditionContract
InitialConditionResolutionResult
InitialConditionRunProvenance
InitialConditionManifest
~~~

Project-owned exception classes distinguish profile, contract, usage, and
manifest failures.

## 6. Profiles And Pose Conversion

The immutable registry contains exactly:

| Condition | Profile | Ordered mapping |
| --- | --- | --- |
| A | `baseline_identity` | `robot_0->S0, robot_1->S1, robot_2->S2` |
| B | `pose_cycle_forward` | `robot_0->S1, robot_1->S2, robot_2->S0` |
| C | `pose_cycle_reverse` | `robot_0->S2, robot_1->S0, robot_2->S1` |

No aliases, arbitrary mappings, external coordinate files, sampling, or random
profile selection were added.

The pure conversion normalizes source WXYZ quaternions and computes yaw with
the same formula formerly local to the environment. The environment helper now
delegates to that pure conversion while retaining its prior `ValueError`
boundary. Each slot keeps both:

~~~text
[x,y,z,qw,qx,qy,qz]
[x,y,z,yaw]
~~~

Position and orientation move atomically as one slot. Scanner offsets remain
identity-bound and are not part of a pose slot.

## 7. Strict Resolution

The explicit path verifies the five repository-relative paths, declared
hashes, actual hashes, and frozen v1 hashes. It reloads the existing pure robot,
capability, viewpoint, and component sources and compares them with the fully
resolved environment configuration.

Validated state includes:

~~~text
task/scenario name/type/path/hash
component path/hash, transform/alignment, bounds, and proxy semantics
viewpoint path/hash/format, ids 0..49, row order, and all poses
robot/capability paths and hashes
ordered robot ids and all source/reset poses
agent-id and action/observation/state key order
model, capability profile, complete capability values, scanner offsets
speed/cost and visual metadata identity
M=3, N=50
lifecycle Contract C policy/interface dimensions and sequence mode
~~~

Malformed shape, zero quaternion, NaN/Inf, unknown/non-bijective mappings,
identity changes, and file/config drift fail with field-specific errors. No
sorting, repair, clamping, fallback, or baseline substitution occurs.

## 8. Schema And Fingerprint

Implemented schema ids:

~~~text
assignment_initial_condition_contract_v1
assignment_initial_condition_manifest_v1
robot_config_wxyz_to_xyzyaw_v1
~~~

The condition fingerprint is SHA-256 over compact canonical JSON with sorted
object keys, preserved ordered lists, ASCII escaping, UTF-8 encoding, and
`allow_nan=False`.

Fingerprint identity includes profile/mapping, task and file identities,
baseline/resolved poses, component/viewpoint/robot/capability identity, M/N,
the policy interface, and conversion contract. Human description and all run
provenance are excluded.

Tests prove:

~~~text
A != B != C
repeat(profile) is stable
same profile best == final
timestamp/seed/output/repository-commit provenance does not change identity
fingerprinted semantic changes do change identity
~~~

The checkpoint canonicalizer and checkpoint fingerprint inputs were not used
or modified.

## 9. Manifest And Atomic Publication

The manifest structure is exactly:

~~~text
manifest_schema_version
condition_contract
condition_fingerprint
run_provenance
~~~

Run provenance supports repository commit, selected CLI field, profile, absolute
diagnostic source paths, seed, deterministic mode, checkpoint child/kind/
generation/fingerprint, load purpose, legacy fallback, attribution schema, and
timestamp.

The writer serializes a complete finite JSON temporary sibling, flushes and
`fsync`s it, then uses an atomic no-clobber hard-link publication. An existing
destination fails; it is never overwritten. The temporary sibling is removed.
Collision and pre-existing partial-destination tests pass.

## 10. Playback CLI And Output Contract

`play_assignment.py` adds only:

~~~text
--assignment_initial_condition_profile
~~~

Its default is `None`; argparse choices are the exact A/B/C ids. Validation is
executed before `AppLauncher`. Explicit selection requires both attribution
logging and an output directory, and that directory must be absent/empty.

After Hydra and scenario application, playback creates one immutable request
and attaches it to `env_cfg`; it never writes pose arrays directly. After the
wrapper is built it validates ordered agents and the `1059/3183/51` lifecycle
interface. It prints one explicit-profile line with profile, fingerprint, and
ordered mapping.

After successful attribution finalization, playback verifies the original
three files, builds provenance from the validated checkpoint-load result,
writes `assignment_initial_condition_manifest.json`, and verifies the exact
four-file directory. The attribution collector and its three schemas remain
unchanged.

## 11. Environment Application Hook

The hook order is:

~~~text
robot config
component mesh/proxy
diagnostics
viewpoints
controlled initial-condition validation/application
DirectMARLEnv.__init__
~~~

With no profile and no request, the hook returns immediately before config
copying, hashing, source loading, fingerprinting, or mutation.

For explicit use it snapshots protected identity fields, builds immutable
resolved input, applies only `cfg.base_start_poses`, then asserts every protected
field is byte/value-equivalent. The validated immutable result/diagnostics are
exposed through the environment for playback. Repeated resets continue to use
the same fixed `self.base_start_poses`; existing scanner reset remains:

~~~text
scanner_pos = assigned base xyz + same robot identity's scanner offset
~~~

No scanner pose is written by the condition profile.

## 12. Training Guard

`train.py` imports one pure validator. Its first Hydra-main action rejects any
non-`None` initial-condition profile or request before assignment runner
registration, runner construction, environment construction, restore, or
training-loop entry. The training parser does not expose the playback CLI.
Normal no-selector training remains accepted.

## 13. Default-Off Compatibility Proof

For a historical playback command without the new selector:

1. argparse resolves the field to `None`.
2. playback's request helper returns without touching `env_cfg`.
3. the environment sees profile/request both `None` and returns immediately.
4. robot-config `base_start_poses` remain unchanged.
5. no condition file hash, contract, fingerprint, or diagnostic is built.
6. no condition startup line is printed.
7. the manifest writer branch is unreachable.
8. the attribution collector still owns exactly its historical three files.
9. checkpoint construction/loading is unchanged.

The existing attribution suite passed all 16 cases after integration.

## 14. Identity And Checkpoint Compatibility Proof

The resolver output contains only replacement base poses. Ordered robot ids,
agent-id mapping, capability profile/value, scanner offset, visual metadata,
and fake actor mapping remain identical in tests. Wrapper lifecycle observation
tests preserve legacy identity and the lifecycle `1059/3183/51` dimensions.

The following are unchanged by diff:

~~~text
assignment_harl_wrapper.py
assignment_checkpoint_contract.py
assignment_checkpoint_load.py
assignment_checkpoint_save.py
assignment_playback_attribution_diagnostics.py
~~~

The existing checkpoint contract suite passed 28/28 tests. Condition SHA-256 is
additional evaluation provenance only and is absent from checkpoint manifests,
compatibility decisions, and actor loading.

## 15. Test And Validation Results

~~~text
new initial-condition pure/fake/static suite:
  PASS 8/8 groups

existing playback attribution diagnostics:
  PASS 16/16 cases

existing checkpoint contract core:
  PASS 28/28 tests

existing lifecycle observation integration:
  PASS 6/6 tests

existing lifecycle mask/HARL historical replay:
  PASS 11/11 tests

existing viewpoint CSV loader smoke:
  PASS

scenario + robot pure load:
  PASS (algorithm_proxy_component_mesh, 3 ordered robots)

py_compile, all five new/modified Python files:
  PASS

git diff --check:
  PASS (line-ending warning only)
~~~

Static searches confine new ownership to the frozen production/test files.
There is no YAML/data, reward, resolver, mask, controller, attribution-collector,
checkpoint-module, installed HARL, or Conda diff.

## 16. Runtime-Deferred Items And Limitations

This phase proves only pure/static readiness. It does not prove that B/C produce
finite initial observations, avoid immediate diagnostic collision/invalid
state, or yield useful/different deterministic trajectories. It also does not
claim physical safety for future articulated robots.

The current profile set is fixed M=3/N=50 and bound to the five frozen file
hashes. Any task file, robot set, condition coordinate, or policy-interface
change requires a reviewed new contract version.

## 17. Explicit Non-Actions

~~~text
No AppLauncher or Isaac Sim was launched.
No assignment environment was constructed/reset/stepped.
No playback or evaluation was run.
No checkpoint tensor was loaded.
No new seed was executed.
No training or continuation was run.
No GUI/video operation ran.
No YAML/data, reward, resolver, mask, controller, or checkpoint semantic changed.
No installed HARL or Conda file was modified.
No result/checkpoint directory was created.
No commit was made.
~~~

## 18. Recommendation

Accept Phase 9G-8I-3-0R-1 as:

~~~text
RUNTIME-IDENTITY-VALIDATION-READY
~~~

The only next recommended phase is:

~~~text
Phase 9G-8I-3-0R-2:
Controlled Initial-Condition Runtime Identity Validation
~~~

Do not begin it automatically. Runtime validation must remain bounded and
reviewed; this phase authorizes no best/final comparison, new seed, training,
GUI/video, or 300k continuation.
