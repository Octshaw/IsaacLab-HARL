# Phase 9G-8I-3-0R: Controlled Initial-Condition Variation Interface And Contract Design

Date: 2026-07-21

## 1. Classification

~~~text
INITIAL-CONDITION-CONTRACT-DESIGN-READY
~~~

Preferred-axis support classification:

~~~text
POSE-PERMUTATION-SUPPORTED-WITH-RUNTIME-VALIDATION
~~~

The current source supports a narrow, deterministic variation contract: keep
the ordered robot identities and every identity-bound capability unchanged, and
permute only the three existing complete base start-pose slots. The source has
no hardcoded controller or actor dependency on the current robot-to-slot
mapping. The task is a tensor/task-space proxy with diagnostic-only collision
checks, however, so static inspection cannot certify every heterogeneous
robot/slot trajectory. A later bounded runtime identity phase remains required.

No implementation or runtime execution is part of this phase.

## 2. Starting Repository Preflight

~~~text
HEAD:
  167bafaac84f7f8f527af40ed786e4834a7db704

git log -1 --oneline:
  167bafaa docs(assignment): validate 100k best-final attribution comparison
~~~

The only starting worktree changes were the accepted Phase 9G-8I-3-0
documentation chain:

~~~text
M  AgentRead/TASK_PROGRESS.md
?? AgentRead/20260721/
   PHASE9G8I30_BEST_FINAL_ROBUSTNESS_AND_LATE_TRAINING_REGRESSION_DIAGNOSIS_DESIGN.md
?? AgentRead/20260721/
   TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G8I30_ROBUSTNESS_DIAGNOSIS_DESIGN_20260721.md
~~~

`git diff --name-status` contained only the tracked `TASK_PROGRESS.md` change;
the two expected new files were untracked. `git diff --check` passed with only
the repository's LF-to-CRLF warning. No production, test, YAML, result,
checkpoint, or unrelated documentation change was present. No interrupted
9G-8I-3-0R output existed after the power loss.

## 3. Accepted Blocker

Phase 9G-8I-3-0 remains accepted unchanged:

~~~text
classification:
  NOT READY

seed classification:
  SEED-INEFFECTIVE

selection alignment:
  SELECTION-PARTIALLY-ALIGNED

checkpoint history:
  ONLY-BEST-AND-FINAL-AVAILABLE
~~~

Changing `--seed` reseeds runtime RNGs but does not change the active fixed
robot poses, persisted ordered N=50 viewpoint set, deterministic reset, masked
categorical mode action, resolver state, or controller state. This report does
not revive seed 2/3 and does not provide playback commands.

## 4. Authorities And Source Boundaries Inspected

Read completely:

~~~text
AgentRead/AGENTS.md
AgentRead/TASK_PROGRESS.md
AgentRead/20260721/
  PHASE9G8I30_BEST_FINAL_ROBUSTNESS_AND_LATE_TRAINING_REGRESSION_DIAGNOSIS_DESIGN.md
AgentRead/20260720/
  PHASE9G8I21_SEQUENTIAL_BEST_FINAL_BOUNDED_ATTRIBUTION_PLAYBACK_EXECUTION_AND_COMPARISON.md
AgentRead/20260720/
  PHASE9G8I20_BEST_VS_FINAL_PROPOSAL_EFFECTIVE_ATTRIBUTION_COMPARISON_DESIGN.md
~~~

Inspected statically:

~~~text
scripts/reinforcement_learning/harl/play_assignment.py
scripts/reinforcement_learning/harl/train.py

scenario_config.py
robot_config.py
capability_config.py
viewpoint_csv.py
scan_mobile_manipulator_env.py
static_feasibility.py
assignment_controller.py
assignment_rl_interface.py
assignment_harl_wrapper.py
assignment_playback_attribution_diagnostics.py
assignment_checkpoint_contract.py
assignment_checkpoint_load.py
assignment_checkpoint_save.py

configs/scenarios/algorithm_proxy_component_mesh.yaml
configs/robots/robots_real_proxy.yaml
configs/robots/robots_three_proxy.yaml
configs/capabilities/mobile_scanner_profiles.yaml
configs/viewpoints/component_mesh_jittered_n50.csv
Model/aircraft_skin_with_frame.obj
~~~

There is no separate `scan_mobile_manipulator_env_cfg.py`; the active
`ScanMobileManipulatorEnvCfg` is defined in
`scan_mobile_manipulator_env.py`. There is no separate checkpoint fingerprint
module; canonical checkpoint JSON and SHA-256 are owned by
`assignment_checkpoint_contract.py`.

## 5. Current Source-Of-Truth Trace

The current source resolves one playback decision state in this order:

1. `play_assignment.py` preloads the scenario and installs its values as parser
   defaults.
2. Hydra constructs `env_cfg` and `agent_cfg`.
3. `play_assignment.main` writes `num_envs` and seed, then calls
   `apply_scenario_config_to_env_cfg`.
4. `make_assignment_harl_env` constructs the scan environment and wrapper.
5. Before `DirectMARLEnv.__init__`, `ScanMobileManipulatorEnv.__init__` runs
   project-local config preparation in this order: visualization, robot config,
   component mesh/proxy, diagnostics, and fixed viewpoint config.
6. `_prepare_robot_config_cfg` loads enabled robots in YAML order. It creates
   `possible_agents`, action/observation/state-space mappings, converts each
   seven-value WXYZ pose to `[x,y,z,yaw]`, and applies capability profiles in
   the same enabled-robot order.
7. `DirectMARLEnv` and the task tensors are constructed. The wrapper obtains
   its fixed agent order from `possible_agents`.
8. `_reset_idx` broadcasts `base_start_poses[:,0:3]` and
   `base_start_poses[:,3]`, derives scanner position as base position plus the
   identity-bound scanner offset, and resets scanner quaternion to
   `[1,0,0,0]`.

`scenario_config.py` does not currently own an initial-condition profile.
Its post-Hydra application does own the robot, capability, component, and
viewpoint paths. A new selector therefore must be applied after this scenario
application, not as a lower-level override that the scenario can replace.

## 6. Same-Task Invariant Contract

Every Condition A/B/C run must pass all of the following. A failed invariant is
a hard contract error, not a new condition.

| Area | Frozen invariant |
| --- | --- |
| Task | `Isaac-Scan-Mobile-Manipulator-Direct-v0` |
| Scenario | `algorithm_proxy_component_mesh`, same scenario semantics and file identity |
| Component | Same OBJ, transform/alignment, proxy type, center, and half extents |
| Viewpoints | Same CSV bytes, N=50, ids `0..49`, row order, poses, frame, units, and WXYZ convention |
| Robots | M=3 and ordered identities `[robot_0,robot_1,robot_2]` |
| Actor mapping | `robot_i` remains bound to `actor_robot_i`; no actor/network reorder |
| Capabilities | Same profile per robot, scanner offset, reach/range/FOV/tolerances, and motion scales |
| Visual/proxy identity | Same robot model/visual metadata and common task-space proxy geometry |
| Policy contract | `lifecycle_contract_c`, HAPPO, EP, feed-forward, `share_param=false`, deterministic mode |
| Interface | Actor/shared/action widths `1059/3183/51`, raw noop `50`, decoded noop `-1` |
| Behavior | Same reward, mask, resolver, Contract C, ownership/arbitration, budget/cooldown, controller, completion logic, and episode length |
| Execution | One explicit profile, one environment, fixed for the process and every reset; no sampling |

Current immutable file anchors at the inspected HEAD are:

| Identity | Repository-relative path | SHA-256 |
| --- | --- | --- |
| Scenario | `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/scenarios/algorithm_proxy_component_mesh.yaml` | `3256398cda4de7caee3b1e1d6de74018623a5d36888a86eeabe0a94392affdfd` |
| Robot config | `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/robots/robots_real_proxy.yaml` | `31f6be04615bdab58f06dd51fdc7185a608231b1f0c784aeff37647e4c9f5837` |
| Capability config | `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/capabilities/mobile_scanner_profiles.yaml` | `a340f18094c117066e4f5a9e2ee0d5656bc98d54a91c4071d93808abe6e6bf29` |
| Viewpoint CSV | `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/viewpoints/component_mesh_jittered_n50.csv` | `f18ee898395e872037e93ff80659e6d480dc89b92460aee8da42bcbb7e2351eb` |
| Component OBJ | `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/Model/aircraft_skin_with_frame.obj` | `9e779f2cfddbb2e9a60691217d2abb7bb780ecb2f5661c666397c55bf6119dc7` |

The v1 profile set must bind these hashes. A content change requires a reviewed
new condition-contract version; it must not be silently accepted under v1.

## 7. Candidate Variation Axes

| Candidate | Same task | Deterministic | Source-backed | Decision |
| --- | --- | --- | --- | --- |
| Change seed | Yes | No meaningful state change | Yes | Rejected as seed-ineffective |
| Permute current complete pose slots | Yes | Yes | Yes | Selected |
| Use `robots_three_proxy.yaml` | Changes coordinates and has no active component-mesh selection boundary | Yes | File exists | Rejected for v1 |
| Invent new coordinates | Potentially | Yes | No current validity rule | Deferred |
| Change viewpoints/component | No | Yes | Yes | Prohibited |
| Stochastic actions/noise | No controlled initial-state isolation | No | Not requested | Prohibited |

Selected axis:

~~~text
Permute the three existing complete robot base start-pose slots among the fixed
robot identities. Do not reorder identities, actors, robot records, capability
records, scanner offsets, or any task data.
~~~

## 8. Full-Pose Slot Semantics

The robot YAML stores a source pose as:

~~~text
[x, y, z, qw, qx, qy, qz]
~~~

The current reset does not consume a seven-value pose directly. It normalizes
the quaternion, converts it to yaw, and stores exactly:

~~~text
[x, y, z, yaw]
~~~

Therefore one v1 full-pose slot is an atomic structured value containing both:

~~~text
source_pose_world_wxyz: [x,y,z,qw,qx,qy,qz]
reset_pose_world_xyzyaw: [x,y,z,yaw]
~~~

The source pose is provenance; the reset-effective four-tuple is behavioral.
Both representations and the conversion-contract id are recorded. A profile
must move the whole slot. It may not mix position from one slot with yaw from
another.

Current baseline slots:

| Slot | Source robot | Source WXYZ pose | Reset-effective pose |
| --- | --- | --- | --- |
| `S0` | `robot_0` | `[-4,-2,0,1,0,0,0]` | `[-4,-2,0,0]` |
| `S1` | `robot_1` | `[0,3.5,0,0.70710678,0,0,-0.70710678]` | `[0,3.5,0,-1.5707963267948966]` |
| `S2` | `robot_2` | `[4,-2,0,0,0,0,1]` | `[4,-2,0,3.141592653589793]` |

Scanner state is not a slot field. For the robot assigned a slot, current reset
continues to compute:

~~~text
scanner_position = assigned base xyz + that robot identity's scanner offset
scanner_quaternion = [1,0,0,0]
~~~

The offset is added in world coordinates by current source and is not rotated by
base yaw. This report preserves that behavior and does not introduce a new
scanner-pose convention.

## 9. Frozen Conditions

| Condition | Profile id | `robot_0` | `robot_1` | `robot_2` |
| --- | --- | --- | --- | --- |
| A | `baseline_identity` | `S0` | `S1` | `S2` |
| B | `pose_cycle_forward` | `S1` | `S2` | `S0` |
| C | `pose_cycle_reverse` | `S2` | `S0` | `S1` |

These are the only v1 profiles. They preserve the exact slot multiset and all
pairwise/component-relative slot geometry. They change which heterogeneous
identity/capability begins at each validated spatial slot.

## 10. Pose-Permutation Support Audit

### 10.1 Robot Geometry And Collision Boundary

All three active records use `model_type=task_space_proxy`. The accepted
scenario uses `robot_visual_mode=debug_marker`; no robot articulation or
collision body is spawned. The base marker dimensions are common, the optional
OBJ visual path/scale is common, and inter-robot and component-obstacle checks
are diagnostics-only. The common diagnostic robot footprint radius is 0.35 m
with 0.15 m margin.

The slot separations are approximately 6.8007 m, 6.8007 m, and 8.0 m. A
permutation preserves them exactly, so it cannot create a new base-base overlap
at reset under the current common-radius diagnostic.

Static inspection cannot prove physical safety for a future real articulation,
nor can the present proxy environment prove collision freedom. That is why the
support classification includes runtime validation.

### 10.2 Identity-Bound Capabilities

The profile loader applies capability values in enabled-robot order, separate
from `base_start_poses`. The selected design changes only the latter. Initial
scanner offset norms remain within each identity's arm reach:

| Robot | Scanner offset | Offset norm | Arm reach |
| --- | --- | ---: | ---: |
| `robot_0` | `[0.7,0,0.85]` | about 1.101 | 2.0 |
| `robot_1` | `[0.9,0,1.05]` | about 1.383 | 3.0 |
| `robot_2` | `[0.6,0,0.75]` | about 0.960 | 1.6 |

All slots have base z=0, so permutation does not invalidate these initial
workspace distances.

### 10.3 Feasibility, Controller, And Actor Mapping

`generate_static_geometric_feasibility` consumes identity-ordered capability
tensors and only the base z component of `base_start_poses`; it does not consume
base x/y/yaw. Because all three slots have z=0, the v1 permutation does not by
itself change the static feasibility mask. Dynamic cost, relative observations,
base/scanner state, and controller trajectory do change with the assigned slot.

The controller uses `env.agent_index`, identity-ordered motion-scale tensors,
and the current base/scanner state. It has no slot-specific `robot_0/1/2`
branch. `AssignmentHarlWrapper` obtains agent order from `possible_agents`, and
checkpoint loading binds actors to `wrapper.agents` in that same order. No
source-backed identity/slot hardcoding blocks the permutation.

### 10.4 Support Decision

~~~text
POSE-PERMUTATION-SUPPORTED-WITH-RUNTIME-VALIDATION
~~~

The profile can be implemented without changing task semantics. Later runtime
validation must still check reset diagnostics, no immediate invalid state,
finite observations, deterministic repeatability, and behavioral usefulness of
B/C.

## 11. Interface Architecture Comparison

| Option | Scope and ownership | Override/default risk | Provenance | Decision |
| --- | --- | --- | --- | --- |
| A. Dedicated playback CLI plus code-owned profiles | One explicit v1 profile; pure project module owns mapping/schema | Lowest; applied after scenario and default is absent | Direct, versioned, easy to validate | Selected |
| B. Scenario-level profiles | Mixes condition experiment definitions into general scenario YAML and training defaults | Scenario application can overwrite or broaden behavior | Adequate but coupled to scenario evolution | Rejected for v1 |
| C. External profile file | Most extensible | Adds arbitrary paths, parser surface, file drift, and a second configuration authority | Requires another file identity and stronger trust rules | Deferred |

Selected user-facing interface:

~~~text
--assignment_initial_condition_profile baseline_identity
--assignment_initial_condition_profile pose_cycle_forward
--assignment_initial_condition_profile pose_cycle_reverse
~~~

The parser default is `None`, not an implicit string profile. The three mapping
definitions and v1 same-task hash anchors live in a new pure project module,
not YAML. No new configuration file is required.

The first interface is playback/evaluation-only. It requires attribution
logging and an attribution output directory so every explicit condition has a
persistent manifest. Training receives no selector; a low-level Hydra attempt
to set the env field must hard-fail before runner construction.

## 12. Configuration Application Order

The frozen implementation order is:

~~~text
parse profile choice (default None; unknown value rejected before AppLauncher)
-> load parser scenario defaults
-> Hydra resolves env_cfg and agent_cfg
-> play_assignment.main applies num_envs/seed
-> apply_scenario_config_to_env_cfg
-> attach one playback-owned initial-condition request to env_cfg
-> make_assignment_harl_env begins project env construction
-> _prepare_robot_config_cfg resolves ordered robots, baseline poses, and capabilities
-> component/proxy/viewpoint preparation resolves same-task data
-> new pure initial-condition resolver validates the complete resolved config
-> resolver replaces only cfg.base_start_poses with the selected slot permutation
-> resolver freezes condition contract/fingerprint diagnostics on cfg
-> DirectMARLEnv.__init__, scene/tensors/static feasibility
-> AssignmentHarlWrapper construction and dimension assertions
-> normal checkpoint compatibility/load boundary
-> reset uses the selected fixed poses
~~~

The current robot-config preparation occurs at the beginning of
`ScanMobileManipulatorEnv.__init__`. Thus the exact source-compatible
application point is after all project-local config preparation and immediately
before `DirectMARLEnv.__init__`. The Python object constructor has entered, but
no DirectMARLEnv state, scene, task tensor, static feasibility tensor, or reset
has been constructed. This is the earliest unambiguous point that satisfies
both the scenario-order and robot-config-order constraints without duplicating
runtime state ownership.

No profile operation may occur after tensor construction or reset.

## 13. Default Compatibility Contract

| Input | Behavior |
| --- | --- |
| No selector | Execute the current path exactly; do not mutate `base_start_poses`, build a condition manifest, or change the three-file attribution contract |
| Explicit `baseline_identity` | Validate and apply the identity mapping; reset-effective state must equal the current baseline exactly; write the fourth condition manifest |
| Explicit forward/reverse | Apply the frozen bijection uniformly for the entire process and every reset |
| Unknown profile | Argparse hard error; no fallback |
| Malformed profile/source/hash | Contract validation hard error before `DirectMARLEnv` construction/reset |
| Profile without attribution output | Startup hard error in v1 |
| Any profile in training | Startup hard error before runner/environment construction |

The no-selector branch must return before any new resolver/fingerprint work. It
must not append metadata to observations, masks, checkpoints, or historical
three-file outputs.

## 14. Robot Identity And Actor Mapping Guarantees

The implementation must snapshot and assert the protected identity fields
before applying a profile:

~~~text
possible_agents
action_spaces / observation_spaces / state_spaces key order
robot_config agent_id_by_name
capability_profile_by_robot
scanner_start_offsets
arm/range/FOV/tolerance/motion-scale tensors
robot visual/model metadata
~~~

After profile resolution, only `cfg.base_start_poses` may differ. The required
invariants are:

~~~text
possible_agents == [robot_0,robot_1,robot_2]
wrapper.agents == [robot_0,robot_1,robot_2]
env.agent_index == {robot_0:0, robot_1:1, robot_2:2}
actor checkpoint identities == [robot_0,robot_1,robot_2]
~~~

`robot_config_diagnostics.initial_pose_world_by_robot` remains source-config
provenance and must not be rewritten to imply that capabilities moved. A
separate initial-condition diagnostic block records the resolved mapping and
poses.

## 15. Frozen Initial-Condition Schema

Condition schema id:

~~~text
assignment_initial_condition_contract_v1
~~~

Persistent manifest schema id:

~~~text
assignment_initial_condition_manifest_v1
~~~

The manifest has three top-level logical blocks:

~~~text
manifest_schema_version
condition_contract
condition_fingerprint
run_provenance
~~~

`condition_contract` contains:

| Field | Required semantics |
| --- | --- |
| `schema_version` | `assignment_initial_condition_contract_v1` |
| `profile_id` | One frozen A/B/C id |
| `profile_description` | Human-readable, not used to decide mapping |
| `task_id` | Exact task id |
| `scenario_identity` | Stable repository-relative path, name/type, file SHA-256 |
| `ordered_robot_ids` | Exact ordered list |
| `baseline_slot_ids` | `[S0,S1,S2]` |
| `baseline_slot_full_poses` | Ordered slot records with source WXYZ and reset-effective XYZYaw |
| `robot_to_slot_mapping` | Ordered records, one per ordered robot |
| `resolved_robot_full_poses` | Ordered robot records with slot, source WXYZ, and reset-effective XYZYaw |
| `component_identity` | Stable path/hash plus resolved mesh transform/alignment and proxy semantics |
| `viewpoint_identity` | Stable CSV path/hash, format/frame/units, N, ordered ids, and ordered-pose digest |
| `robot_configuration_identity` | Robot/capability paths and hashes, ordered identity/profile bindings, scanner offsets |
| `policy_interface_contract` | Lifecycle profile, HAPPO/EP/feed-forward/share mode, deterministic mode, dimensions, noop ids |
| `M`, `N` | 3 and 50 |
| `reset_pose_conversion_contract` | `robot_config_wxyz_to_xyzyaw_v1` |

Mappings and poses are ordered lists, not JSON objects whose key sorting could
erase semantic order. All repository paths used by the fingerprint are
normalized repository-relative POSIX strings. Resolved absolute paths may be
recorded only as non-fingerprinted provenance.

## 16. Condition Fingerprint Semantics

The condition fingerprint is:

~~~text
sha256(canonical_json(condition_contract_identity_payload))
~~~

Canonical JSON requirements:

~~~text
UTF-8
object keys sorted
separators=(",", ":")
ASCII escaping enabled
NaN/Inf forbidden
ordered lists preserved exactly
one trailing LF in the stored manifest, but not in fingerprint input
~~~

The identity payload includes all semantic `condition_contract` fields except
the human description. It includes the profile id, mapping, source/effective
poses, exact task-file hashes, ordered robot/capability bindings, M/N, and
frozen policy-interface contract.

Excluded from the condition fingerprint:

~~~text
repository commit
resolved absolute paths
created/resolved timestamp
output directory
command seed
checkpoint directory, child, kind, generation, or artifact hashes
assignment checkpoint contract fingerprint
attribution output paths
~~~

These exclusions ensure:

~~~text
Condition A best == Condition A final fingerprint
Condition B best == Condition B final fingerprint
Condition A != Condition B != Condition C fingerprint
~~~

The existing `canonical_manifest_bytes` cannot be reused directly because it
only accepts and semantically validates `AssignmentCheckpointContractManifest`.
The new pure module should reuse its proven canonical JSON recipe, not its
checkpoint-specific validator. It owns a separate
`canonical_initial_condition_bytes` and SHA-256 function. No checkpoint module
is modified.

## 17. Checkpoint Compatibility Separation

Current checkpoint manifests bind ordered agent names, M/N,
actor/shared/action schemas, lifecycle behavior, sequence mode, model structure,
and training contract. They do not bind robot start poses, scenario paths,
component files, or viewpoint files.

Pose permutation therefore changes environment state while leaving structural
normal-evaluation compatibility unchanged:

~~~text
actor/shared/action dimensions:
  unchanged at 1059/3183/51

ordered actor identities:
  unchanged

assignment checkpoint fingerprint:
  unchanged

condition fingerprint:
  varies with A/B/C
~~~

The condition profile must not be added to
`AssignmentCheckpointContractManifest`, and no checkpoint loader branch or
compatibility purpose changes. The existing `normal_evaluation` actor-only load
remains authoritative. Checkpoint identity is recorded only in run provenance.

## 18. Manifest And Output Contract

Selected location:

~~~text
inside the attribution output directory, next to the existing three artifacts
~~~

Filename:

~~~text
assignment_initial_condition_manifest.json
~~~

Historical Phase 9G-8H/8I output directories remain valid schema-v1
three-artifact outputs. The attribution CSV, summary JSON, and segment CSV
schemas do not change.

Successful explicit-profile outputs contain exactly four files:

~~~text
assignment_proposal_effective_rows.csv
assignment_proposal_effective_summary.json
assignment_target_segments.csv
assignment_initial_condition_manifest.json
~~~

The playback entry, not the existing attribution collector, owns the fourth
file. It writes the manifest atomically only after collector finalization has
successfully written the original three files. A manifest collision or write
failure is a hard failure. The collector's existing summary `artifact_paths`
block remains a three-artifact attribution-schema field.

`run_provenance` records at least:

~~~text
repository_commit
selection CLI field and selected profile id
resolved absolute source paths for diagnostics
command seed
deterministic actor mode
checkpoint directory/child
checkpoint kind and generation
assignment checkpoint contract fingerprint
checkpoint load purpose and legacy_fallback flag
attribution schema version
created timestamp
~~~

None of those checkpoint fields affect `condition_fingerprint`.

One concise startup line is printed after resolved config/wrapper validation and
before reset, containing profile id, condition fingerprint, and ordered
robot-to-slot mapping. Exact prose is not part of the contract.

## 19. Strict Validation Rules

The v1 implementation hard-fails on any of the following:

1. Profile is absent from the exact A/B/C registry.
2. Explicit profile is used without attribution logging/output.
3. Task, scenario name/type/path/hash, component path/hash/semantics, robot
   config hash, capability hash, or viewpoint hash differs from the v1 scope.
4. Viewpoint count is not 50, ids are not exactly `0..49` in order, or pose
   order/values differ.
5. Ordered robot ids are not exactly `[robot_0,robot_1,robot_2]` or M is not 3.
6. Mapping is incomplete, non-bijective, references an unknown slot, duplicates
   a slot, or contains an extra robot/slot.
7. Source pose shape is not 7, reset pose shape is not 4, a quaternion is zero,
   or any numeric value is nonfinite.
8. The resolved source-pose multiset or reset-effective-pose multiset differs
   from the baseline slot multiset.
9. Any protected identity/capability/visual/config field changes while applying
   the mapping.
10. Resolved environment `base_start_poses` differs from the expected mapping,
    or scanner offsets/capabilities differ from their identity-bound baseline.
11. Lifecycle profile, HAPPO/EP/feed-forward/share mode, deterministic action
    mode, dimensions, action width, or noop ids differ.
12. A profile is requested from `train.py` or another unsupported usage mode.
13. Canonical manifest/fingerprint verification fails or the manifest path
    collides.

Validation never clamps, repairs, sorts, substitutes, or falls back to
baseline.

## 20. Reproducibility Contract

For one profile, the following must be fixed:

~~~text
same implementation repository commit
same profile id and condition fingerprint
same scenario and all bound file hashes
same checkpoint when reproducing one trajectory
same command seed
same deterministic masked Categorical.mode() path
same device/execution boundary used by the accepted comparison
~~~

They must resolve to the same base/scanner initial state, first
observation/mask/lifecycle snapshot, first actions, and deterministic trajectory
subject to the already accepted device determinism boundary. Reset always
reuses the fixed resolved `base_start_poses`; the profile cannot change between
episodes and no per-environment or per-reset sampling exists.

Paired best/final runs are valid only when their condition fingerprints are
exactly equal. Profile id or directory naming alone is insufficient.

## 21. Future Implementation File Map

Phase 9G-8I-3-0R-1 is frozen to this narrow change set:

| File | Allowed future change |
| --- | --- |
| New `assignment_initial_condition.py` | Pure profile registry, immutable request/result/schema types, pose/mapping/hash validation, canonical JSON/SHA-256, manifest builder, atomic writer, usage guard |
| `play_assignment.py` | Add the dedicated choices-based CLI, enforce attribution output, attach request after scenario application, log validated resolution, write manifest after collector finalization |
| `scan_mobile_manipulator_env.py` | Add default-`None` config handoff/diagnostics fields and one pre-`DirectMARLEnv` preparation hook that replaces only `cfg.base_start_poses` |
| `train.py` | Add an early project-local hard guard against any selected initial-condition profile |
| New `scripts/environments/test_assignment_initial_condition_contract.py` | Pure/fake/default-identity/mapping/fingerprint/output/training-guard regressions |

No new YAML/config file is needed. `scenario_config.py` intentionally does not
gain a profile field. The following remain unmodified:

~~~text
assignment_harl_wrapper.py
assignment_playback_attribution_diagnostics.py
assignment_checkpoint_contract.py
assignment_checkpoint_load.py
assignment_checkpoint_save.py
all reward/resolver/controller/mask modules
installed HARL and Conda files
~~~

If implementation proves that the profile cannot be applied through the frozen
single `base_start_poses` hook, it must stop for review rather than expand this
file map silently.

## 22. Future Regression Plan

### 22.1 Pure Contract Tests

~~~text
no selector leaves the legacy cfg path untouched
baseline_identity resolves exact current source/effective poses
forward and reverse resolve the exact frozen mappings
all profiles preserve both pose multisets
A/B/C fingerprints are stable and pairwise distinct
best/final checkpoint provenance leaves a condition fingerprint unchanged
repository/output/timestamp/seed provenance leaves it unchanged
unknown profile, duplicate slot, missing robot, extra robot, bad hash,
bad shape, zero quaternion, and nonfinite pose all fail
canonical manifest JSON rejects NaN/Inf and round-trips exactly
~~~

### 22.2 Identity And Isolation Tests

~~~text
possible_agents and agent_id_by_name unchanged
capability profiles/scanner offsets/reach/range/FOV/tolerances/scales unchanged
wrapper agent order and actor-to-robot mapping unchanged in a fake boundary
M/N and 1059/3183/51 interfaces unchanged
assignment checkpoint manifest/fingerprint unchanged across A/B/C
training usage hard-fails; legacy no-selector training is unaffected
reward/resolver/mask/controller modules have no diff
~~~

### 22.3 Output Tests

~~~text
legacy no-selector collector still emits exactly the existing three artifacts
explicit profile successful fake output emits exactly those three plus manifest
attribution row/summary/segment schemas and values are unchanged
manifest contains required condition and run-provenance fields
checkpoint kind/generation is separate from the fingerprint payload
manifest is atomically written after collector finalization
collision/partial-output cases fail without overwrite
~~~

Phase 9G-8I-3-0R-1 runs only pure/fake/static tests. It does not launch Isaac
Sim.

## 23. Future Runtime-Validation Plan

After R-1 review, recommend a separate bounded phase:

~~~text
Phase 9G-8I-3-0R-2:
Controlled Initial-Condition Runtime Identity Validation
~~~

Use one already accepted actor checkpoint and seed 1 only. Do not compare best
versus final yet. The phase should:

1. Run explicit Condition A and compare its resolved state, first
   observation/mask/lifecycle snapshot, first actions, and three attribution
   artifacts with the accepted no-selector baseline, accounting only for path
   fields and the intentional fourth manifest.
2. Run B twice and C twice, sequentially, to verify stable fingerprints,
   reset poses, and deterministic outputs.
3. Assert same task/component/viewpoint/capability/interface/checkpoint contract
   on every run.
4. Assert no immediate proxy overlap/invalid-state diagnostic and no nonfinite
   observation/action/runtime value.
5. Confirm B and C differ from A in initial actor observation and/or trajectory.
   If a resolved-different profile produces an identical trajectory, retain the
   result and classify it behaviorally ineffective.
6. Stop on first failure with no automatic retry or invented replacement
   condition.

Only after R-2 passes may a new design authorize paired best/final A/B/C
robustness execution.

## 24. Alternative-Axis Boundary

No alternative axis is selected because pose permutation is source-supported.
If R-1 exposes a structural contradiction or R-2 finds B/C unsafe, the only
acceptable next design axis is another explicit deterministic set of robot base
poses derived from a reviewed component-clearance and robot-spacing rule. It
must preserve identities/capabilities/component/viewpoints and receive a new
contract version. No coordinates, profile, or retry may be generated
automatically.

Viewpoint reorder, component movement, capability changes, initial coverage,
noise, stochastic action selection, and unused seeds remain prohibited as
substitutes.

## 25. Explicit Non-Goals And Non-Actions

~~~text
No production source behavior was modified.
No test or YAML file was modified.
No new configuration file was created.
No attribution output or checkpoint behavior was modified.
No reward, observation, mask, resolver, Contract C, ownership, arbitration,
budget, cooldown, completion, or controller behavior was modified.
No checkpoint was loaded or deserialized.
No AppLauncher or Isaac Sim process was launched.
No assignment environment was constructed.
No playback or evaluation was run.
No new seed was run.
No training or 300k continuation was run.
No GUI or video operation was run.
No result or checkpoint directory was created or modified.
No installed HARL or Conda file was modified.
No commit was made.
~~~

## 26. Documentation Validation

~~~text
git diff --check:
  PASS (line-ending warning only)

git status --short --untracked-files=all:
  only the accepted Phase 9G-8I-3-0 documentation chain,
  this Phase 9G-8I-3-0R report/archive,
  and AgentRead/TASK_PROGRESS.md

unexpected changed paths:
  none
~~~

No Python compilation or test is required because this phase changes
documentation only.

## 27. Final Recommendation

Accept Phase 9G-8I-3-0R as:

~~~text
INITIAL-CONDITION-CONTRACT-DESIGN-READY
~~~

The only next recommended phase is:

~~~text
Phase 9G-8I-3-0R-1:
Controlled Initial-Condition Variation Interface Implementation And Regression
~~~

Do not start it automatically. It may implement only the frozen interface,
strict validation, condition fingerprint/manifest, default compatibility, and
pure/fake/static regressions. It may not run playback, evaluation, training,
GUI/video, a new seed, or 300k continuation.
