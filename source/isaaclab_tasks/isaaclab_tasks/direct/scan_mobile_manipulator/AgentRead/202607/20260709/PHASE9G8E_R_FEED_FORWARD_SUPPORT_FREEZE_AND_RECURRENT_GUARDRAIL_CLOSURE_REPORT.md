# Phase 9G-8E-R Feed-Forward Support Freeze And Recurrent Guardrail Closure

Date: 2026-07-09

## Classification

```text
PASS
```

Phase 9G-8E is closed as `PASS` for the official `lifecycle_contract_c_v1` support matrix.

## Support Decision

The first official resolver-enabled lifecycle policy sequence contract is:

```text
policy_sequence_contract_version: lifecycle_feed_forward_v1
policy_sequence_mode: feed_forward
model.use_recurrent_policy: false
model.use_naive_recurrent_policy: false
supported generator: feed_forward_generator_actor
```

Officially unsupported in lifecycle contract version 1:

```text
naive_recurrent_generator_actor
recurrent_generator_actor
GRU/LSTM lifecycle training
```

The naive recurrent historical-mask boundary passed Phase 9G-8E testing. It is intentionally outside the first official lifecycle support matrix; it is not classified as broken.

Profile support:

| profile | sequence contract | normal training status |
|---|---|---|
| `legacy` | Existing legacy HARL configuration | Unchanged by the new guard |
| `lifecycle_ablation` | No training sequence contract | Not enabled for normal training |
| `lifecycle_contract_c` | Feed-forward only | Still prohibited pending Phase 9G-8F |
| `diagnostics_hidden_state` | Diagnostics only | Prohibited |

## Source Boundaries Inspected

Project:

```text
assignment_harl_training.py
assignment_harl_wrapper.py
assignment_lifecycle_training_contract.py
scenario_config.py
scan_mobile_manipulator_env.py
scripts/reinforcement_learning/harl/train.py
agents/harl_happo_cfg.yaml
scan_mobile_manipulator/__init__.py
```

Installed HARL, read-only:

```text
harl/runners/on_policy_base_runner.py
harl/common/buffers/on_policy_actor_buffer.py
harl/algorithms/actors/on_policy_base.py
harl/algorithms/actors/happo.py
harl/algorithms/actors/haa2c.py
harl/algorithms/actors/hatrpo.py
harl/models/policy_models/stochastic_policy.py
harl/models/base/rnn.py
harl/utils/trans_tools.py
```

The task-local HAPPO YAML is the registered HARL config entry point. Its sequence fields are:

```text
model.use_recurrent_policy
model.use_naive_recurrent_policy
model.data_chunk_length
model.recurrent_n
```

Hydra resolves that YAML and any overrides before `train.py:main(...)` invokes the new guard. Scenario/profile application resolves `env_cfg.assignment_lifecycle_profile` before the same call.

## Installed Generator-Selection Audit

`HAPPO.train`, `HAA2C.train`, and `HATRPO.train` use the same precedence:

```text
if self.use_recurrent_policy:
    recurrent_generator_actor(..., self.data_chunk_length)
elif self.use_naive_recurrent_policy:
    naive_recurrent_generator_actor(...)
else:
    feed_forward_generator_actor(...)
```

| resolved mode | installed flags | selected actor generator | lifecycle_contract_c_v1 |
|---|---|---|---|
| Feed-forward | both false | `feed_forward_generator_actor` | Supported |
| Naive recurrent | recurrent false, naive true | `naive_recurrent_generator_actor` | Unsupported by official profile |
| Chunked recurrent | recurrent true, regardless of naive flag | `recurrent_generator_actor` | Unsupported and known incompatible |
| Contradictory | both true | `recurrent_generator_actor` due first-branch priority | Hard error before runner |

`model.data_chunk_length` is passed only to `recurrent_generator_actor`; it does not select a generator. `model.recurrent_n` controls GRU layer/state shape when either recurrent flag is enabled; it does not select a generator.

With both official lifecycle flags false, `StochasticPolicy` does not construct/use its recurrent layer and actor training can reach only `feed_forward_generator_actor`.

## Known Installed Dependency Incompatibility

The pinned installed chunked generator performs:

```text
OnPolicyActorBuffer.recurrent_generator_actor(...)
  -> _sa_cast(torch_tensor)
  -> torch_tensor.transpose(1, 0, 2)
```

PyTorch `Tensor.transpose` accepts two dimensions, so the branch raises before yielding a batch.

Classification:

```text
known installed-dependency incompatibility
outside lifecycle_contract_c_v1 feed-forward support
not a lifecycle observation defect
not a lifecycle mask defect
not a resolver defect
not a checkpoint defect
```

The installed package was not patched or shadowed. A future recurrent-support phase would require an explicitly versioned HARL fork or adapter.

Read-only SHA-256 evidence:

```text
on_policy_actor_buffer.py  A7352B59D8FA28B96E28E3021DDEAA9F8DA5944C686651B1C04B0EC26C96F8CC
trans_tools.py             12FA0F758B5F7153DEE63D1358AC789E112E3ADE8F492DE8F4EE7E8054B0A81A
happo.py                   DD44FE7842160AA215B2D220726F6DD5E70B251C1A2E9C50CFEB6BD00535CF96
haa2c.py                   63AE6DC048BC3EDA0D7D1434AA1930426A0BD674BB61E67AB51D21B07D2911F6
hatrpo.py                  BD2083E7F54DBEB42C9861C402CAB890024370E34D767560860547F139E77129
```

## Guard Implementation And Timing

Shared project-local implementation:

```text
assignment_lifecycle_training_contract.py
  validate_assignment_lifecycle_policy_sequence(...)
  resolve_installed_harl_actor_buffer_generator(...)
  policy_sequence_contract_for_profile(...)
```

The validator reads, without mutation:

```text
env_args["config"].assignment_lifecycle_profile
algo_args["model"]["use_recurrent_policy"]
algo_args["model"]["use_naive_recurrent_policy"]
```

Both flags must be actual resolved booleans. Missing or string-like values hard-fail as ambiguous.

Primary guard timing:

```text
Hydra config merge
-> command-line/Hydra overrides
-> assignment episode-length override
-> scenario config applied to env_cfg
-> env_args assembled
-> validate_assignment_lifecycle_policy_sequence(...)
-> RUNNER_REGISTRY[algo](...)
```

Defense-in-depth timing:

```text
AssignmentOnPolicyHARunner.__init__
-> read assignment_rl
-> same shared validator
-> seed/device/log directory
-> environment
-> actor
-> actor buffer
-> critic
-> restore
```

Thus invalid lifecycle recurrent settings cannot construct an environment, actor, rollout buffer, checkpoint restore path, or training loop. The validator does not silently rewrite config.

Error guidance includes:

```text
lifecycle_contract_c_v1 supports feed-forward policies only.

Set:
  use_recurrent_policy = False
  use_naive_recurrent_policy = False

No installed HARL package modification is required.
```

## Valid / Invalid Configuration Matrix

| profile | recurrent | naive recurrent | result |
|---|---:|---:|---|
| `lifecycle_contract_c` | false | false | Valid sequence contract; training remains blocked by Phase 9G-8F gate |
| `lifecycle_contract_c` | true | false | Hard error before runner |
| `lifecycle_contract_c` | false | true | Hard error before runner; naive is unsupported, not broken |
| `lifecycle_contract_c` | true | true | Contradictory hard error before runner |
| `lifecycle_contract_c` | non-boolean/missing | any | Ambiguous resolved-config hard error |
| `legacy` | any existing legacy combination | any existing legacy combination | New lifecycle guard does not reject |
| `lifecycle_ablation` | any | any | Profile remains non-training |
| `diagnostics_hidden_state` | any | any | Profile remains diagnostics-only |

## Historical-Mask Contract

The supported path retains:

```text
sampling available_actions[t]
==
actor_buffer available_actions[t]
==
feed_forward_generator available_actions_batch
==
evaluate_actions available_actions_batch
```

Synthetic masks encode distinct time/environment sample identities. Feed-forward minibatch shuffling preserves the observation/mask association. HAPPO receives the exact generated historical mask in `evaluate_actions`; the existing lightweight HAA2C and HATRPO checks also pass.

No PPO update regenerates a historical mask from current resolver state.

## In-Memory Manifest Update

`AssignmentHarlWrapper.assignment_observation_schema_manifest` now includes:

```text
policy_sequence_contract_version
policy_sequence_mode
use_recurrent_policy
use_naive_recurrent_policy
supported_actor_buffer_generator
unsupported_actor_buffer_generators
```

Official lifecycle values are:

```text
lifecycle_feed_forward_v1
feed_forward
false
false
feed_forward_generator_actor
[naive_recurrent_generator_actor, recurrent_generator_actor]
```

These are in-memory contract metadata only. Checkpoint persistence, canonical JSON, SHA-256 fingerprinting, and compatibility loading remain Phase 9G-8F work.

## Tests And Results

Interpreter:

```text
C:\isaacenvs\isaac45_harl\python.exe
```

Results:

| validation | result |
|---|---|
| `py_compile` for changed/new Python files | PASS |
| Phase 9G-8C pure snapshot/builders | PASS, 11/11 |
| Phase 9G-8D observation integration | PASS, 6/6 |
| Revised Phase 9G-8E mask/HARL replay | PASS, 11/11 |
| Phase 9G-8E-R feed-forward guard | PASS, 9/9 |
| `git diff --check` | PASS; line-ending warnings only |

The 9G-8E-R suite verifies:

```text
valid feed-forward resolution
chunked recurrent early rejection
naive recurrent early rejection
contradictory flag rejection
ambiguous non-boolean rejection
legacy non-regression
manifest sequence contract
ablation/diagnostics training prohibition
train-entry guard ordering before runner construction
```

The revised 9G-8E suite retains a diagnostic assertion that installed `_sa_cast` contains and exhibits the known incompatible transpose call. It no longer treats an explicitly unsupported branch as a supported-path failure.

No Isaac Sim/AppLauncher, training, short training smoke, playback, evaluation, checkpoint loading, or video recording ran.

## Phase 9G-8E Closure Decision

```text
PASS
```

Closure rationale:

```text
Lifecycle Contract C version 1 officially supports feed-forward
policies only.

All supported lifecycle observation, shared observation, available-action
mask, rollout-buffer historical-mask, generator, and evaluate_actions
paths pass.

The installed HARL chunked recurrent generator remains a documented,
guarded, unsupported dependency branch and cannot be entered by the
official lifecycle profile.
```

Recurrent support itself is not classified as passed.

## Remaining Blockers And Next Boundary

Resolver-enabled training remains prohibited. Unimplemented Phase 9G-8F readiness work:

```text
checkpoint manifest persistence
canonical JSON and SHA-256 fingerprint
all-loader compatibility validation
actor/critic/buffer forward-backward readiness
checkpoint save/load validation
```

Next possible phase:

```text
Phase 9G-8F:
Checkpoint / Loader / Buffer / Forward-Backward Readiness
```

No Phase 9G-8F implementation was started.

## Non-Modification Confirmation

```text
installed HARL: not modified
Conda environment: not modified
project YAML runtime defaults: not modified
checkpoint loaders/fingerprints: not implemented
resolver/Contract C/budget behavior: unchanged
training/playback/evaluation/Isaac Sim: not run
commit: not made
```
