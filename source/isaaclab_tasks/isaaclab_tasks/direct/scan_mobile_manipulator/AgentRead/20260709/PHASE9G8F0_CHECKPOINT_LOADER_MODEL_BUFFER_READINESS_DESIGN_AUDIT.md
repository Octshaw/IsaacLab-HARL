# Phase 9G-8F-0 Checkpoint / Loader / Model-Buffer Readiness Design Audit

Date: 2026-07-09

Classification:

```text
DESIGN-READY
```

Scope: documentation and static inspection only. No checkpoint, model, loader, buffer, optimizer, training, or runtime behavior was implemented or exercised.

## 1. Executive Classification

Phase 9G-8F-0 is:

```text
DESIGN-READY
```

Static inspection located:

- every project model-construction boundary used by assignment HAPPO;
- every current HARL save boundary inherited by the project runner;
- five user-facing RL load entry points;
- all actor, critic, buffer, optimizer, and value-normalizer constructors;
- current `models/`, `best_model/`, optional checkpoint, and final-save behavior;
- the exact limits of current weight restoration;
- the metadata owner, canonicalization rules, fingerprint rules, compatibility categories, unversioned legacy fallback, and follow-on phase split.

No unresolved question blocks Phase 9G-8F-1 after this report is reviewed and accepted.

The attachment referenced the Phase 9G-8E-R report under `20260708/`. The accepted file is under the current-date archive:

```text
AgentRead/20260709/
PHASE9G8E_R_FEED_FORWARD_SUPPORT_FREEZE_AND_RECURRENT_GUARDRAIL_CLOSURE_REPORT.md
```

## 2. Current Lifecycle / HARL Readiness State

Accepted lifecycle contract:

| contract | frozen value |
|---|---|
| Profile | `lifecycle_contract_c` |
| Actor schema | `lifecycle_v1_actor_3n` |
| Actor dimension | `100 + 3M + 19N`; `M=3,N=50 -> 1059` |
| Shared schema | `lifecycle_v1_shared_option_a_budget2m` |
| Shared dimension | `M*(100+3M+19N)+2M`; `M=3,N=50 -> 3183` |
| Action space | `Discrete(N+1)`; `N=50 -> 51` |
| Raw noop | `N` |
| Decoded noop | `-1` |
| Sequence contract | `lifecycle_feed_forward_v1` |
| Recurrent flags | both false |
| Generator | `feed_forward_generator_actor` |
| HARL state type | Current assignment entry resolves to `EP` |
| Parameter sharing | Current HAPPO YAML resolves `share_param=False` |
| Official first algorithm | HAPPO |

Implemented and validated before this audit:

```text
lifecycle actor observation
Option A shared observation
lifecycle Contract C available-actions
atomic actor/shared/mask snapshot generation
feed-forward historical-mask replay
feed-forward recurrent guard
legacy observation/mask isolation
```

Still absent:

```text
persisted checkpoint contract manifest
canonical JSON and SHA-256
shared loader validator
safe lifecycle restore
synthetic actor/critic/buffer forward-backward readiness
versioned save/load smoke
validated training continuation
exact training resume
```

Resolver-enabled training remains prohibited.

## 3. Model-Construction Audit

### 3.1 Construction Chain

```text
scripts/reinforcement_learning/harl/train.py
-> resolved Hydra agent_cfg and env_cfg
-> lifecycle sequence validator
-> AssignmentOnPolicyHARunner
-> AssignmentIsaacLabEnv
-> AssignmentHarlWrapper
-> wrapper observation/action spaces
-> HAPPO actors
-> actor buffers
-> VCritic
-> EP critic buffer
-> ValueNorm
-> inherited restore when model_dir is non-null
```

The task registry exposes only `harl_happo_cfg_entry_point`. `AssignmentOnPolicyHARunner` lists HAPPO, HATRPO, and HAA2C as allowed classes, but task-local HATRPO/HAA2C YAML entry points are not registered. The first official lifecycle checkpoint contract is therefore HAPPO-only. Adding official HATRPO/HAA2C checkpoint support requires a separate registered-config and compatibility review.

### 3.2 Component Table

| component | class / constructor | dimensions and source | profile behavior | device / dtype | count |
|---|---|---|---|---|---:|
| Actor observation space | `AssignmentHarlWrapper._make_observation_space()` | Wrapper-generated flat actor dimension | 909 legacy; 1059 lifecycle | Gym Box float32 | one space per agent |
| Shared space | `AssignmentHarlWrapper._make_share_observation_space()` | Actor concat, plus lifecycle `2M` budget block | 2727 legacy; 3183 lifecycle | Gym Box float32 | same EP space per agent |
| Action space | `make_assignment_discrete_action_spaces()` | `Discrete(N+1)` | Same in legacy/lifecycle | scalar id; HARL storage float32 | one per agent |
| Actor algorithm | `ALGO_REGISTRY["happo"]` / `HAPPO` | Actor space and action space | Input/head shape profile-dependent | runner device; parameters float32 | 3 independent actors |
| Actor network | `StochasticPolicy` | MLP input 909 or 1059; Categorical output 51 | No RNN in lifecycle v1 | runner device; float32 | one per actor |
| Actor optimizer | `torch.optim.Adam` in `OnPolicyBase` | Actor parameters; YAML `lr`, `opti_eps`, `weight_decay` | Same class, different input-layer shape | runner device | one per independent actor |
| Actor buffer | `OnPolicyActorBuffer` | Observation/action spaces and train/model args | Observation width profile-dependent | project runner passes runner device; float32 | one per agent |
| Critic | `VCritic` / `VNet` | shared observation space | Input 2727 or 3183 | runner device; float32 | one centralized critic |
| Critic optimizer | `torch.optim.Adam` in `VCritic` | Critic parameters | Input layer profile-dependent | runner device | one |
| EP critic buffer | `OnPolicyCriticBufferEP` | shared space and train/model/algo args | Width 2727 or 3183 | runner device; float32 | one |
| FP critic buffer | `OnPolicyCriticBufferFP` | adds agent dimension | Constructed only if `state_type=FP` | NumPy float32 in installed HARL | not used by official profile |
| Value normalizer | `ValueNorm(1)` | scalar return normalization | Enabled by current YAML | runner device | one |

### 3.3 Exact Dimensions

Legacy:

```text
actor:  100 + 3M + 16N = 909
shared: M * (100 + 3M + 16N) = 2727
action: N + 1 = 51
```

Lifecycle Contract C:

```text
actor:  100 + 3M + 19N = 1059
shared: M * (100 + 3M + 19N) + 2M = 3183
action: N + 1 = 51
```

For current `M=3`, the raw environment actor block is 96:

```text
base position 3
yaw sin/cos 2
scanner position 3
scanner quaternion 4
coverage ratio 1
capability 4
nearest viewpoint slots 64
other scanners 6
previous action 9
```

Lifecycle wrapper extension:

```text
task rows: N * 17
noop context: 5
previous assignment one-hot: N + 1
dynamic scalars: 7
covered vector: N
```

### 3.4 Actor Sharing And File Inventory

Current YAML:

```text
algo.share_param = False
```

Therefore:

```text
three independent HAPPO actor wrappers
three independent StochasticPolicy instances
three independent Adam actor optimizers
```

Current save names use `cfg.possible_agents`:

```text
actor_agent_robot_0.pt
actor_agent_robot_1.pt
actor_agent_robot_2.pt
critic_agent.pt
value_normalizer.pt
```

Manual loaders also accept numeric fallback actor names:

```text
actor_agent_0.pt
actor_agent_1.pt
actor_agent_2.pt
```

The versioned lifecycle manifest must freeze the exact actor inventory and canonical names. Numeric fallback is legacy-only.

If `share_param=True`, HARL stores the same actor object under multiple list entries and current save code writes duplicate actor files. Lifecycle v1 must hard-require `share_param=False`; shape compatibility must not silently reinterpret shared versus independent policies.

### 3.5 Effective Critic Hidden Sizes

Current project code assigns:

```text
self.hidden_sizes_critic = algo_args["model"]["hidden_sizes"]
```

It does not consume YAML `model.hidden_sizes_critic`. Thus the effective current actor and critic hidden sizes are both:

```text
[256, 256]
```

The YAML value `[512, 256]` is currently unused. The manifest must record effective constructed values, not merely raw YAML. Changing the runner to consume `hidden_sizes_critic` would change critic structure and is outside Phase 9G-8F.

## 4. Checkpoint-Save Audit

### 4.1 Save Callers

| save kind | caller | destination | trigger | overwrite behavior |
|---|---|---|---|---|
| Regular | `OnPolicyBaseRunner.run()` | run root `models/` | every `eval_interval`, even when evaluation is disabled | overwrites fixed names |
| Best | `OnPolicyBaseRunner.run()` | run root `best_model/` | logger `total_reward > best_avg_reward` | overwrites fixed names |
| Optional snapshot | `OnPolicyBaseRunner.run()` | `models/checkpoints/episode_<n>/` | `save_checkpoints` and interval | new episode directory |
| Final | project `train.py` | run root `models/` | after `runner.run()` returns | overwrites fixed names |

`init_dir()` creates:

```text
run_root/
  logs/
  models/
```

`best_model/` is created lazily. No loader automatically selects `models/`, `best_model/`, or latest checkpoint; users pass a directory explicitly.

### 4.2 Saved Files

Default `save_entire_model=False`:

```text
actor_agent_<robot_name>.pt       StochasticPolicy.state_dict
critic_agent.pt                   VNet.state_dict
value_normalizer.pt               ValueNorm.state_dict, when enabled
```

Optional `save_entire_model=True`:

```text
actor_agent_<robot_name>_full.pt  pickled StochasticPolicy object
critic_agent_full.pt              pickled VNet object
value_normalizer_full.pt          pickled ValueNorm object
```

Official lifecycle checkpoints must prohibit `save_entire_model=True`. Lifecycle v1 uses state dictionaries only.

The installed full-model restore replaces `self.actor[...].actor` and `self.critic.critic` after their optimizers were constructed. The existing optimizers can therefore remain bound to the pre-replacement parameter objects. This is an additional reason that `_full.pt` restoration is outside every lifecycle v1 load and continuation path.

### 4.3 Save Properties

Current saves are not atomic:

- `torch.save()` writes directly to final file names;
- a crash can leave partial files;
- `models/` and `best_model/` are overwritten in place;
- the critic and value normalizer are saved once per actor loop, repeatedly overwriting the same files;
- there is no completion marker, file digest, checkpoint generation, or cross-file consistency check.

The future project-level metadata/save integration must live at runner level outside the actor loop.

### 4.4 Current State Inventory

| state | currently saved? | currently loaded by runner? | implication |
|---|---:|---:|---|
| Actor weights | Yes | Yes | Weight restoration possible |
| Critic weights | Yes | Yes outside render | Training weight continuation possible |
| Actor optimizer | No | No | Exact resume impossible |
| Critic optimizer | No | No | Exact resume impossible |
| Value normalizer | Yes when enabled | Yes outside render | Required for meaningful continuation |
| LR scheduler object | No object exists | No | LR decay is procedural |
| Episode/update count | No | No | Schedule/log position resets |
| `best_avg_reward` | No | No | Best-model selection resets |
| Algorithm dynamic state | No additional HAPPO state saved | No | Static config only |
| RNG states | No | No | Exact stochastic continuation impossible |
| Environment state | No | No | Episode restarts |
| Resolver/budget state | No | No | Episode lifecycle restarts |
| Rollout buffers | No | No | Rollout restarts |
| Hydra/HARL config at run root | HARL `save_config()` skips `env=="isaaclab"` | No | No colocated reliable config contract |
| Scenario file copy | No | No | Source path may be machine-specific |

Current HARL `restore()` is not true resume.

## 5. Complete Load / Restore Entry-Point Audit

Five user-facing load paths were identified.

| # | entry point | load implementation | accepted path | loaded objects | current checks | future disposition |
|---:|---|---|---|---|---|---|
| 1 | `scripts/reinforcement_learning/harl/train.py --dir` | `AssignmentOnPolicyHARunner.__init__ -> inherited restore()` | any supplied directory | all actors, critic, ValueNorm | state-dict load only; exceptions printed and swallowed | Override/route through shared validator before any load |
| 2 | `scripts/reinforcement_learning/harl/play.py --dir` | generic HARL runner inherited `restore()` | any supplied directory | actors; full runner decides critic by render mode | no project validation | For assignment task, hard-route to supported project loader or hard reject |
| 3 | `scripts/reinforcement_learning/harl/play_assignment.py --dir` | local `_load_assignment_actors()` | explicit directory | actors only | file candidates and PyTorch shape errors | Replace duplicated checks with shared validator |
| 4 | `scripts/environments/evaluate_assignment_rl_playback_diagnostics.py --dir` | local `_load_assignment_actors()` | explicit directory; labels `models`/`best_model` by basename | actors only | file candidates and PyTorch shape errors | Replace duplicated checks with shared validator |
| 5 | `scripts/environments/evaluate_assignment_methods.py --assignment_checkpoint_dir` | local `_load_assignment_actors()` | explicit directory | actors only | file candidates and PyTorch shape errors | Keep validator-ready; main currently rejects assignment RL |

Underlying implementation families:

```text
one inherited HARL restore implementation
three duplicated project actor-only torch.load implementations
```

Current direct manual loads use:

```text
torch.load(..., map_location="cpu", weights_only=True)
```

Installed HARL runner restore uses `torch.load` without `weights_only=True`, catches broad exceptions, prints errors, and continues. That behavior is unacceptable for lifecycle checkpoints.

No current path:

- validates a manifest or fingerprint;
- validates field ordering when dimensions match;
- distinguishes structural/evaluation/continuation compatibility;
- validates lifecycle mask, budget, guardrail, resolver, or sequence contracts;
- verifies all expected actor files before the first actor load;
- automatically discovers the latest run.

## 6. Compatibility Definitions

### A. Structural Load Compatibility

Question:

```text
Can the complete expected state-dict key/shape inventory load into
the constructed actor/critic/value-normalizer objects?
```

Required comparisons:

```text
actor count and parameter sharing
actor observation dimensions by agent
shared dimension
action dimension and Categorical head
effective hidden sizes
feature-normalization layers
recurrent-layer presence
recurrent_n when recurrent
critic architecture and state type
state-dict key sets and tensor shapes
```

Structural compatibility alone never authorizes evaluation or continuation.

### B. Evaluation / Ablation Compatibility

Normal evaluation requires:

```text
valid native manifest and fingerprint
structural compatibility
matching evaluation-semantic contract
matching complete contract fingerprint
```

Explicit ablation evaluation may differ only through a named, validator-owned whitelist. The first approved cross-contract case is:

```text
lifecycle_contract_c checkpoint
-> lifecycle_ablation evaluation
```

It requires matching actor/shared/action/model structure and an explicit ablation request. It is not continuation-compatible and must be recorded in output metadata.

### C. Training-Continuation / Resume Compatibility

Validated weight continuation requires:

```text
exact complete contract fingerprint
all independent actor files
critic file
required ValueNorm file
matching training-state classification
no full-model pickle mode
fresh environment and buffers
explicit acknowledgement that optimizers/counters/RNG reset
```

Exact training resume additionally requires optimizer, scheduler/counter, RNG, environment, resolver, and rollout state. Current HARL does not save those states.

Frozen decision:

```text
validated weight continuation: future supported target
exact training resume: unsupported
```

## 7. Ordered Checkpoint Manifest Design

### 7.1 Ownership

One project-local manifest builder owns the contract. It combines:

```text
wrapper observation/action manifest
resolved lifecycle profile
resolved sequence contract
effective constructed model configuration
HARL state type and algorithm
training contract fields
```

Scripts must not hand-author manifests.

### 7.2 Top-Level Schema

Recommended format:

```text
manifest_format_version: assignment_checkpoint_contract_v1

identity
scale
actor_schema
shared_schema
action_contract
lifecycle_behavior_contract
policy_sequence_contract
model_structure
training_contract
```

Identity:

```text
profile_name
training_time_profile
algorithm_name
harl_state_type
harl_shared_observation_mode
serialization_mode = state_dict
```

Scale:

```text
M
N
num_agents
ordered_agent_names
```

Actor schema:

```text
actor_schema_version
actor_dimension
actor_dimension_by_agent
actor_ordered_feature_manifest
actor_task_row_field_order
actor_tail_field_order
```

Ordered actor blocks:

```text
raw_env_observation
per_task_rows
noop_context
previous_assignment_one_hot
dynamic_scalars
covered_vector
```

Every block/field entry records:

```text
name
source
shape
dtype
normalization
snapshot_timing
padding_semantics
```

Shared schema:

```text
shared_schema_version
shared_dimension
shared_construction_mode
shared_ordered_blocks
critic_budget_schema_version
```

Lifecycle shared block order remains:

```text
actor_obs_robot_0
actor_obs_robot_1
actor_obs_robot_2
budget_progress_robot_0
budget_step_fraction_robot_0
budget_progress_robot_1
budget_step_fraction_robot_1
budget_progress_robot_2
budget_step_fraction_robot_2
```

Action contract:

```text
action_space_type = Discrete
action_dimension
target_action_min = 0
target_action_max = N - 1
noop_raw_id = N
noop_decoded_value = -1
```

Lifecycle behavior:

```text
snapshot_contract_version = lifecycle_decision_snapshot_v1
resolver_contract_version = assignment_lifecycle_resolver_contract_c_v1
mask_contract_version = lifecycle_contract_c_mask_v1
budget_release_contract_version = budget_release_v1
legacy_guardrail_profile = lifecycle_no_legacy_guardrails_v1
ownership_contract_version = exclusive_owner_active_equivalence_v1
arbitration_contract_version = lowest_cost_then_robot_id_v1
```

Policy sequence:

```text
policy_sequence_contract_version = lifecycle_feed_forward_v1
policy_sequence_mode = feed_forward
use_recurrent_policy = false
use_naive_recurrent_policy = false
supported_actor_buffer_generator = feed_forward_generator_actor
```

### 7.3 Model-Structure Fields

| field | include in fingerprint? | reason |
|---|---:|---|
| Effective actor hidden sizes | Yes | Structural shape |
| Effective critic hidden sizes | Yes | Structural shape |
| Activation function | Yes | Changes loaded-model forward semantics |
| Feature normalization enabled | Yes | Changes modules and semantics |
| Actor/critic class identifiers | Yes | Structural and semantic identity |
| Action distribution class | Yes | Policy semantics |
| Recurrent flags | Yes | Structure and generator contract |
| `recurrent_n` | Yes | RNN/buffer contract even though lifecycle flags are false |
| `share_param` | Yes | Actor identity and file inventory |
| Number and ordered names of actor networks | Yes | File-to-agent mapping |
| Critic architecture and EP/FP mode | Yes | Structure and shared-state semantics |
| Initialization method and action gain | Yes | Strict training provenance and reproducibility |
| `data_chunk_length` | No for lifecycle v1 fingerprint | Feed-forward guard makes it behaviorally inactive; retain only as non-fingerprinted run provenance |
| Raw unused `hidden_sizes_critic` YAML value | No | Current runner does not consume it |

Training contract must also fingerprint behavior-driving optimization fields:

```text
optimizer class
actor/critic learning rates
optimizer epsilon and weight decay
PPO epochs/minibatches
clip/value/entropy coefficients
gradient clipping
gamma/GAE lambda
ValueNorm enabled
proper-time-limit behavior
episode length and rollout threads where continuation semantics require them
```

## 8. Training-State Metadata Design

A separate per-checkpoint file is required:

```text
assignment_training_state_manifest.json
```

It is not the immutable contract manifest. It describes the actual saved artifact set:

```text
training_state_format_version
contract_fingerprint
checkpoint_kind
checkpoint_generation
episode_or_update_index, when known
actor_file inventory
critic_file
value_normalizer_file
optimizer availability
counter availability
RNG availability
environment/buffer availability
continuation_classification
relative file names, sizes, and SHA-256 digests
```

State classification:

| state | exact resume | validated weight continuation | evaluation | current availability |
|---|---|---|---|---|
| Actor weights | Required | Required | Required | Available |
| Critic weights | Required | Required | Irrelevant for actor-only evaluation | Available |
| ValueNorm | Required when enabled | Required | Usually irrelevant | Available |
| Actor optimizer | Required | May reset explicitly | Irrelevant | Unavailable |
| Critic optimizer | Required | May reset explicitly | Irrelevant | Unavailable |
| LR schedule/current episode | Required if decay enabled | Reset/explicit | Irrelevant | Unavailable |
| `best_avg_reward` | Required for identical save behavior | Optional reset | Irrelevant | Unavailable |
| Entropy/PPO hyperparameters | Required as contract | Required as contract | Irrelevant | Config only |
| Algorithm dynamic state | Required if introduced | Required if behavior-driving | Irrelevant | No separate HAPPO state found |
| Torch/NumPy/Python/CUDA RNG | Required | May reset explicitly | Irrelevant | Unavailable |
| Environment/resolver state | Required | Fresh reset | Irrelevant | Unavailable |
| Rollout buffer | Required for mid-rollout resume | Fresh warmup | Irrelevant | Unavailable |

No future report may call current restoration exact resume.

## 9. Canonical JSON Rules

Canonical contract bytes:

```text
encoding: UTF-8
serialization: JSON
object keys: lexicographically sorted
ordered feature/block/agent lists: preserve list order
separators: "," and ":"
whitespace: none
ensure_ascii: true
allow_nan: false
boolean/null: JSON true/false/null
canonical bytes: no BOM and no trailing newline
```

The human-readable file may end with one LF, but verification must parse and recanonicalize before hashing.

Number rules:

- integer contract fields are JSON integers;
- floating contract values must be finite;
- float-valued hyperparameters are normalized to schema-defined canonical decimal strings before serialization;
- `-0`, NaN, and infinities are forbidden;
- list order is never sorted.

Path rules:

- fingerprinted content contains only normalized relative artifact roles/names;
- no absolute paths;
- no drive letters, hostnames, usernames, run-directory names, timestamps, or device names;
- path separators in metadata are `/`;
- paths containing `..`, absolute roots, or escaping the selected checkpoint directory are rejected.

## 10. SHA-256 Fingerprint Design

Selected design:

```text
one complete immutable contract fingerprint
+
explicit field-category comparisons for structural inspection
and approved ablation decisions
```

Separate structural/semantic/resume fingerprints were rejected for v1 because they multiply metadata and disagreement states. One complete fingerprint is easier to bind to every saved checkpoint.

Definition:

```text
sha256(canonical_contract_manifest_bytes)
```

Storage:

```text
assignment_contract_manifest.json
assignment_contract_fingerprint.txt
```

Fingerprint file:

```text
64 lowercase hexadecimal characters
single trailing LF allowed
```

Verification:

1. Parse manifest as trusted JSON data.
2. Validate schema/version and reject duplicate/unknown critical fields.
3. Canonicalize.
4. Recompute SHA-256.
5. Constant-time compare to stored lowercase fingerprint.
6. Hard-error on mismatch.

The fingerprint is generated metadata. CLI/config cannot supply an override fingerprint.

## 11. Metadata Placement And Discovery

Required layout:

```text
run_root/
  assignment_contract_manifest.json
  assignment_contract_fingerprint.txt
  models/
    assignment_contract_manifest.json
    assignment_contract_fingerprint.txt
    assignment_training_state_manifest.json
  best_model/
    assignment_contract_manifest.json
    assignment_contract_fingerprint.txt
    assignment_training_state_manifest.json
  models/checkpoints/episode_<n>/
    assignment_contract_manifest.json
    assignment_contract_fingerprint.txt
    assignment_training_state_manifest.json
```

Rules:

- Run-root contract is authoritative for the run.
- Every child checkpoint directory contains an identical self-contained copy so it can be moved to Linux independently.
- Child and run-root fingerprints/manifests must agree when both are present.
- A manual copied directory is supported only when it contains its own complete metadata pair.
- Parent fallback is allowed only for recognized repository-created relationships: `models/`, `best_model/`, or `models/checkpoints/episode_<n>/`.
- Never walk arbitrary ancestors looking for metadata.
- Manifest without fingerprint: hard error.
- Fingerprint without manifest: hard error.
- Local/root disagreement: hard error.
- Training-state manifest is checkpoint-local and must bind the contract fingerprint.

Save completion:

- write model artifacts to same-directory temporary files;
- replace individual files atomically where supported;
- compute file digests;
- write contract copies;
- write `assignment_training_state_manifest.json` last as the checkpoint completion marker;
- loader rejects incomplete inventories.

## 12. Unversioned Legacy Checkpoint Policy

Old metadata-free checkpoints are supported only as:

```text
explicit profile = legacy
resolver disabled
legacy observation
legacy mask
state_dict actor files only
legacy playback/evaluation
```

Required structural fallback:

1. Construct the exact requested legacy model.
2. Require explicit legacy mode and trusted local directory.
3. Load state dictionaries with `weights_only=True` on CPU.
4. Compare exact state-dict key sets and tensor shapes.
5. Confirm actor input layer is compatible with 909.
6. Confirm Categorical action head output is 51.
7. If critic requested, confirm critic input is 2727.
8. Confirm current known legacy `N=50`, noop raw id 50, decoded noop -1.

Prohibited:

```text
lifecycle observation/resolver/mask
training continuation
full-model pickle
silent padding/truncation
strict=False partial load
fabricated native manifest
```

An optional migration utility is deferred to a separate future phase. It must never relabel inferred legacy metadata as a native lifecycle checkpoint.

## 13. Shared Validator Decision Procedure

One project-level validator must execute before actor, critic, optimizer, or ValueNorm state loading.

Inputs:

```text
purpose
current resolved manifest
selected checkpoint directory
optional explicit ablation name
expected model/file inventory
```

Pseudocode:

```text
resolve selected directory without arbitrary parent traversal
discover local metadata pair
discover only recognized run-root pair

if exactly one of manifest/fingerprint exists:
    hard error: incomplete metadata pair

if native metadata exists:
    parse JSON
    validate manifest version and schema
    canonicalize and verify SHA-256
    if local and run-root copies exist:
        require byte-equivalent canonical manifests and equal fingerprints
    validate training-state manifest and expected relative file inventory
else:
    if purpose is legacy evaluation and current profile is explicit legacy:
        enter unversioned legacy fallback
    elif purpose is structural inspection:
        allow read-only weights-only shape inspection
    else:
        hard error: metadata required

construct compatibility result:
    structural = compare model inventory, dimensions, keys, shapes
    evaluation = compare semantic fields or named ablation whitelist
    continuation = require exact complete fingerprint and required training artifacts

if purpose == structural inspection:
    return report; do not load into live model

if purpose == normal evaluation:
    require structural and exact native evaluation contract

if purpose == explicit ablation evaluation:
    require structural and named approved field-difference set

if purpose == training continuation:
    require exact fingerprint
    require actor + critic + ValueNorm inventory
    require explicit approximate-continuation acknowledgement
    reject exact-resume claim

only now:
    deserialize expected state_dict files with weights_only=True
    recheck key/shape maps
    strict load actors, critic, ValueNorm
```

Error messages must name:

```text
purpose
checkpoint directory
manifest/fingerprint version
first mismatching field and expected/actual values
whether mismatch is structural, semantic, or continuation state
allowed corrective profile/purpose, when one exists
```

## 14. Forward / Backward Readiness Design

Use real installed HARL classes with synthetic Gym spaces and CPU tensors. Do not construct an environment.

Lifecycle case:

```text
B actor observations: [B,1059]
B shared observations: [B,3183]
available_actions: [B,51], at least noop available
actions: [B,1], valid target/noop ids
rnn_states: [B,1,256] placeholder
masks: [B,1]
active_masks: [B,1]
```

Required checks:

1. Construct three independent HAPPO actors and one VCritic.
2. Verify no RNN module is constructed.
3. `get_actions()` respects available-actions.
4. `evaluate_actions()` reuses the supplied historical mask.
5. Critic returns `[B,1]`.
6. Build actor and critic losses through real HAPPO/VCritic update APIs.
7. Run backward.
8. Assert required gradients exist and are finite.
9. Run one optimizer step.
10. Assert selected actor and critic parameters changed finitely.
11. Assert unavailable action probability is effectively zero.

Legacy case repeats with:

```text
actor [B,909]
shared [B,2727]
available_actions [B,51]
```

No policy-performance claim follows from this smoke.

## 15. Buffer Readiness Design

Use real:

```text
OnPolicyActorBuffer
OnPolicyCriticBufferEP
```

Official lifecycle v1 does not test FP as a supported mode.

Lifecycle actor-buffer shapes:

```text
obs:               [T+1,R,1059]
rnn_states:        [T+1,R,1,256]
available_actions: [T+1,R,51]
actions:           [T,R,1]
action_log_probs:  [T,R,1]
masks:             [T+1,R,1]
active_masks:      [T+1,R,1]
```

Lifecycle EP critic-buffer shapes:

```text
share_obs:         [T+1,R,3183]
rnn_states_critic: [T+1,R,1,256]
value_preds:       [T+1,R,1]
returns:           [T+1,R,1]
rewards:           [T,R,1]
masks:             [T+1,R,1]
bad_masks:         [T+1,R,1]
```

Tests:

```text
warmup index 0
insert at step+1 for obs/share_obs/masks/available-actions
action/log-prob at step
after_update last-to-zero copy
feed-forward minibatch shuffling
observation/action/mask sample identity
share_obs/value/return identity
GAE returns finite
active_masks and bad_masks preserved
no current resolver-state mask regeneration
```

## 16. Checkpoint Save / Load Smoke Design

Use a temporary directory and no environment.

Valid path:

1. Construct lifecycle actors/critic/ValueNorm.
2. Produce deterministic actor logits/actions and critic outputs.
3. Save state dictionaries to temporary names.
4. Generate native contract manifest and fingerprint.
5. Generate training-state manifest with relative file inventory/digests.
6. Reconstruct identical models.
7. Validate before state loading.
8. Strict-load.
9. Compare actor logits/actions and critic outputs exactly or at tight deterministic tolerance.
10. Verify ValueNorm equality.
11. Exercise explicit validated weight continuation and confirm optimizer reset is reported.

Invalid cases:

| mismatch | required result |
|---|---|
| Legacy checkpoint -> lifecycle | Hard error |
| Lifecycle -> legacy | Hard error except separately approved structural inspection |
| M or N | Hard error |
| Action dimension/noop | Hard error |
| Actor feature order with same dimension | Hard error |
| Shared block order with same dimension | Hard error |
| Mask/budget/guardrail/sequence contract | Hard error |
| Resolver-disabled named ablation | Explicit ablation evaluation only |
| Fingerprint corruption | Hard error |
| Missing/malformed manifest | Hard error except legacy fallback |
| Partial file inventory | Hard error |
| Full-model pickle | Hard error for lifecycle |

## 17. Terminology Freeze

| term | precise meaning |
|---|---|
| Weight load | Load one or more network state dictionaries |
| Evaluation restore | Validated actor weight load for inference under an allowed evaluation contract |
| Validated weight continuation | Load actors, critic, and ValueNorm under exact contract; initialize fresh optimizers/counters/RNG/env/buffers |
| Exact training resume | Restore all behaviorally relevant training and runtime state and continue identically |

Current `--dir` behavior is weight restoration, not exact resume. Future lifecycle reporting and CLI validation must use these terms.

## 18. Robustness / Security Boundaries

Required ordering:

```text
resolve constrained metadata path
-> parse trusted JSON metadata
-> verify schema and fingerprint
-> validate contract and inventory
-> construct expected model
-> weights-only deserialize expected state files
-> strict state-dict load
```

Safeguards:

- reject path traversal and metadata outside recognized checkpoint/run roots;
- never search arbitrary parent directories;
- reject child/run-root disagreement;
- reject stale child copies via fingerprint and training-state binding;
- reject partial checkpoint directories;
- reject unknown extra actor identities;
- prohibit lifecycle full-model pickle files;
- use `weights_only=True` for state dictionaries;
- do not call installed HARL restore directly for lifecycle checkpoints;
- do not swallow load exceptions;
- require exact key sets and shapes.

Limitation: unversioned structural inspection necessarily deserializes a state dictionary before its tensor shapes are known. It must be explicit legacy/structural mode, CPU-only, `weights_only=True`, and restricted to expected local files.

## 19. Legal / Illegal Compatibility Matrix

| combination | classification |
|---|---|
| Unversioned legacy + explicit legacy evaluation | Legacy evaluation fallback |
| Unversioned legacy + legacy training continuation | Hard error |
| Legacy + lifecycle evaluation | Hard error |
| Legacy + lifecycle training | Hard error |
| Matching native lifecycle + lifecycle evaluation | Normal evaluation |
| Matching native lifecycle + validated weight continuation | Normal training continuation |
| Matching lifecycle + exact resume request | Hard error; exact resume unsupported |
| Lifecycle checkpoint + resolver-disabled named ablation | Explicit ablation evaluation only |
| Lifecycle + different mask contract | Hard error |
| Lifecycle + different budget contract | Hard error |
| Lifecycle + different guardrail profile | Hard error |
| Lifecycle + recurrent flags enabled | Hard error |
| Lifecycle + different actor feature order | Hard error |
| Lifecycle + different shared block order | Hard error |
| Lifecycle + different M | Hard error |
| Lifecycle + different N | Hard error |
| Lifecycle + different noop id | Hard error |
| Metadata missing | Legacy fallback only when explicit; otherwise hard error |
| Malformed/unsupported manifest | Hard error |
| Fingerprint mismatch | Hard error |
| Manifest only or fingerprint only | Hard error |
| `models/` manifest differs from run root | Hard error |
| `best_model/` manifest differs from run root | Hard error |
| Checkpoint-child manifest differs from run root | Hard error |
| Metadata-free checkpoint structural inspection | Structural inspection only |
| Generic HARL `play.py` with assignment lifecycle checkpoint | Hard error until routed through project validator |

## 20. Recommended Phase 9G-8F Implementation Split

### Phase 9G-8F-1: Manifest / Canonical JSON / Fingerprint / Compatibility Core

| item | boundary |
|---|---|
| Allowed files | New project-local metadata/compatibility module and pure tests |
| Forbidden | Runner/load/save integration, model changes, environment |
| Tests | Manifest schema, canonical bytes, fingerprint, category decisions, matrices |
| Checkpoint files | No real model checkpoint; JSON fixtures/temp metadata only |
| Forward/backward | No |
| Environment/Isaac Sim | No |
| Training | No |

### Phase 9G-8F-2: Checkpoint Save Metadata Integration

| item | boundary |
|---|---|
| Allowed files | Project assignment runner/save integration, metadata module/tests |
| Forbidden | Loader integration, model architecture, resolver behavior |
| Tests | Run-root/child placement, atomic metadata, inventory, disagreement/partial cases |
| Checkpoint files | Temporary synthetic state-dict artifacts allowed |
| Forward/backward | No |
| Environment/Isaac Sim | No |
| Training | No |

### Phase 9G-8F-3: All-Loader Compatibility Integration

| item | boundary |
|---|---|
| Allowed files | Assignment runner restore plus five audited entry points and shared loader module/tests |
| Forbidden | Architecture/resolver changes, runtime evaluation |
| Tests | Validator-before-load spies, valid/invalid matrix, legacy fallback |
| Checkpoint files | Temporary state-dict fixtures may be loaded |
| Forward/backward | No |
| Environment/Isaac Sim | No |
| Training/playback/evaluation | No |

### Phase 9G-8F-4: Actor / Critic / Buffer Forward-Backward Readiness

| item | boundary |
|---|---|
| Allowed files | Project-local synthetic readiness tests; minimal project model-construction helper only if required |
| Forbidden | Environment, checkpoint loader changes, resolver changes |
| Tests | Real HARL actor/critic/buffer, legacy/lifecycle, gradients and one optimizer step |
| Checkpoint files | No |
| Forward/backward | Yes, synthetic CPU |
| Environment/Isaac Sim | No |
| Training | No rollout/training loop |

### Phase 9G-8F-5: Checkpoint Save / Load / Continuation Smoke

| item | boundary |
|---|---|
| Allowed files | Temporary checkpoint smoke tests and narrowly required save/load fixes |
| Forbidden | Environment training, performance evaluation, exact-resume claims |
| Tests | Output equality, ValueNorm, file integrity, invalid matrix, validated weight continuation |
| Checkpoint files | Yes, temporary test directories only |
| Forward/backward | Only if needed to prove post-load continuation |
| Environment/Isaac Sim | No |
| Training | No environment training |

### Phase 9G-8F-6: Phase 9G-8F Readiness Review

| item | boundary |
|---|---|
| Allowed files | Review report and TASK_PROGRESS |
| Forbidden | New behavior unless separately scoped defect correction |
| Tests | Review prior evidence; no new broad run |
| Checkpoint files | No new artifacts |
| Forward/backward | No |
| Environment/Isaac Sim | No |
| Training | No |

## 21. Remaining Unresolved Questions

No blocking design question remains.

Explicitly deferred:

- exact training resume;
- official HATRPO/HAA2C task configs and checkpoint support;
- use of YAML `hidden_sizes_critic`;
- recurrent lifecycle policy support;
- migration of old checkpoints into native manifests;
- cryptographic signatures or untrusted remote checkpoint support;
- environment/resolver state serialization;
- performance or long-training validation.

## 22. Final Frozen Recommendation

```text
DESIGN-READY
```

Freeze Phase 9G-8F around:

```text
one project-owned immutable ordered contract manifest
one SHA-256 over canonical manifest bytes
one checkpoint-local training-state/inventory manifest
one shared validator before every load
state_dict-only lifecycle checkpoints
five audited load entry points
HAPPO + EP + three independent feed-forward actors
normal matching evaluation
named explicit ablation evaluation
validated weight continuation
exact training resume unsupported
unversioned legacy evaluation fallback only
synthetic real-HARL model/buffer readiness without an environment
```

Phase 9G-8F-1 may begin only after this design is reviewed and accepted.
