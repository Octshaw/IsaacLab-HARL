# Phase 9G-8F-4 Actor / Critic / Buffer Forward-Backward Readiness Report

Date: 2026-07-09

## Classification

```text
PASS
```

The real installed HARL feed-forward HAPPO actor, centralized VCritic, actor buffer, EP critic buffer, ValueNorm, minibatch generators, backward paths, and Adam optimizer paths passed with synthetic CPU data for both the accepted lifecycle and legacy dimensions.

No assignment environment, AppLauncher, checkpoint, rollout loop, playback, evaluation, or formal training was used.

## Files

Created:

```text
scripts/environments/test_assignment_actor_critic_buffer_forward_backward_readiness.py
AgentRead/20260709/PHASE9G8F4_ACTOR_CRITIC_BUFFER_FORWARD_BACKWARD_READINESS_REPORT.md
AgentRead/20260709/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G8F4_FORWARD_BACKWARD_READINESS_20260709.md
```

Modified:

```text
AgentRead/TASK_PROGRESS.md
```

Inspected read-only:

```text
assignment_harl_training.py
assignment_harl_wrapper.py
assignment_lifecycle_training_contract.py
assignment_checkpoint_save.py
assignment_checkpoint_load.py
agents/harl_happo_cfg.yaml

C:\isaacenvs\isaac45_harl\Lib\site-packages\harl\
  algorithms\actors\happo.py
  algorithms\actors\on_policy_base.py
  algorithms\critics\v_critic.py
  models\policy_models\stochastic_policy.py
  models\base\act.py
  models\base\distributions.py
  models\value_function_models\v_net.py
  common\buffers\on_policy_actor_buffer.py
  common\buffers\on_policy_critic_buffer_ep.py
  common\valuenorm.py
```

No installed HARL or Conda file was modified.

## Installed HARL Classes Exercised

```text
harl.algorithms.actors.happo.HAPPO
harl.models.policy_models.stochastic_policy.StochasticPolicy
harl.models.base.act.ACTLayer
harl.models.base.distributions.Categorical / FixedCategorical
harl.algorithms.critics.v_critic.VCritic
harl.models.value_function_models.v_net.VNet
harl.common.buffers.on_policy_actor_buffer.OnPolicyActorBuffer
harl.common.buffers.on_policy_critic_buffer_ep.OnPolicyCriticBufferEP
harl.common.valuenorm.ValueNorm
```

The test calls the real installed:

```text
HAPPO.get_actions
HAPPO.evaluate_actions
HAPPO.update
VCritic.get_values
VCritic.update
OnPolicyActorBuffer.insert
OnPolicyActorBuffer.feed_forward_generator_actor
OnPolicyActorBuffer.after_update
OnPolicyCriticBufferEP.insert
OnPolicyCriticBufferEP.compute_returns
OnPolicyCriticBufferEP.feed_forward_generator_critic
OnPolicyCriticBufferEP.after_update
```

No simplified project-local PPO or critic loss substitutes were used.

## Environment And Toolchain

```text
Python:
  C:\isaacenvs\isaac45_harl\python.exe

PyTorch:
  2.5.1+cu121

Execution device:
  CPU only

Synthetic rollout:
  T = 4
  R = 2
  M = 3
  feed-forward batch population = 8 samples
  actor minibatches = 2
  critic minibatches = 2
```

The installed Gym package emitted its existing maintenance warning. It did not affect the tests.

## Effective Configuration

The test reads the current project `harl_happo_cfg.yaml` and verifies the resolved values used by the assignment runner.

| field | effective value |
|---|---|
| Algorithm | HAPPO |
| State type | EP |
| Parameter sharing | false |
| Actor count | 3 |
| Policy sequence | feed-forward |
| `use_recurrent_policy` | false |
| `use_naive_recurrent_policy` | false |
| Hidden sizes | `[256, 256]` |
| Activation | `relu` |
| Feature normalization | true |
| Initialization | `orthogonal_` |
| Action gain | `0.01` |
| Actor learning rate | `0.0005` |
| Critic learning rate | `0.0005` |
| Optimizer epsilon | `0.00001` |
| Weight decay | `0` |
| PPO clip | `0.2` |
| Entropy coefficient | `0.01` |
| Maximum gradient norm | `10.0` |
| PPO epochs in normal config | `5` |
| Actor minibatches | `2` |
| Critic epochs in normal config | `5` |
| Critic minibatches | `2` |
| Gamma | `0.99` |
| GAE lambda | `0.95` |
| ValueNorm | enabled |
| Proper time limits | enabled |
| `recurrent_n` placeholder | `1` |

The current assignment runner assigns:

```text
hidden_sizes_critic = algo_args["model"]["hidden_sizes"]
```

Therefore the effective critic structure remains `[256, 256]`. The YAML field `hidden_sizes_critic: [512, 256]` remains unused and was not adopted by this test.

## Dimensions

| profile | actor observation | shared observation | action | raw noop |
|---|---:|---:|---:|---:|
| `lifecycle_contract_c` | 1059 | 3183 | 51 | 50 |
| `legacy` | 909 | 2727 | 51 | 50 |

The constructed first actor and critic linear layers were asserted to consume the corresponding actor/shared widths.

## Synthetic Data Contract

Actor observations and shared observations carry an integer sample identity in feature zero. Remaining features are deterministic finite float32 values.

Historical available-action masks:

```text
shape: [sample, 51]
noop id 50: always enabled
idle-style rows: target choices plus noop
executing-style rows: one target plus noop
all-zero rows: prohibited
```

Actions include target and noop actions and are validated against the mask attached to the same historical sample.

The rollout includes:

```text
distinct time/environment identities
different masks across time
one terminal-style recurrent mask
one inactive actor mask
one bad-mask truncation-style critic sample
finite rewards, predictions, returns, factors, and advantages
```

No resolver state was reconstructed and no lifecycle mask was regenerated during minibatch generation.

## Actor Forward And Masked Categorical

Lifecycle and legacy actor forward paths passed.

Verified:

```text
actions: [B,1]
action log probabilities: [B,1]
feed-forward RNN placeholder returned as [B,1,256]
sampled actions are enabled by available_actions
evaluate_actions accepts the historical [B,51] mask
log probabilities and entropy are finite
noop has nonzero probability
masked actions have probability <= 1e-12
```

The categorical exclusion is the installed HARL behavior:

```text
logits[available_actions == 0] = -1e10
```

## Critic Forward

The real centralized `VCritic.get_values` path passed for both shared dimensions.

Verified:

```text
values: [B,1]
feed-forward RNN placeholder: [B,1,256]
all values finite
critic input layer matches declared shared dimension
```

## Actor Buffer

The real actor buffer passed:

```text
obs:               [T+1,R,actor_dim]
rnn_states:        [T+1,R,1,256]
actions:           [T,R,1]
action_log_probs:  [T,R,1]
masks:             [T+1,R,1]
active_masks:      [T+1,R,1]
available_actions: [T+1,R,51]
factor:            [T,R,1]
```

Evidence:

```text
insert stores actions/log-probs at t
insert stores next obs/rnn/masks/available-actions at t+1
step wraps after T insertions
after_update copies final observation and available-actions to index zero
```

## EP Critic Buffer

The real EP critic buffer passed:

```text
share_obs:         [T+1,R,shared_dim]
rnn_states_critic: [T+1,R,1,256]
value_preds:       [T+1,R,1]
returns:           [T+1,R,1]
rewards:           [T,R,1]
masks:             [T+1,R,1]
bad_masks:         [T+1,R,1]
```

`compute_returns` ran with current GAE, proper-time-limit, and ValueNorm settings. Returns and derived advantages remained finite. The installed EP buffer does not contain an `active_masks` tensor.

`after_update` copied the final shared state to index zero.

## Feed-Forward Generator Alignment

Actor minibatch shuffling preserved exact correspondence among:

```text
observation sample identity
RNN placeholder
action
mask
active mask
old action log probability
advantage
historical available-actions
HAPPO factor
```

Critic minibatch shuffling preserved exact correspondence among:

```text
shared-observation sample identity
RNN placeholder
value prediction
return
mask
```

Every one of the eight rollout samples appeared exactly once per direct generator pass. Historical available-actions were read from the actor buffer; they were not regenerated from current state.

## Actor Loss, Backward, And Optimizer

One real `HAPPO.update` was run for each profile.

| metric | lifecycle | legacy |
|---|---:|---:|
| Actor scalar parameters | 353401 | 314701 |
| Parameter tensors with gradients | 12 | 12 |
| Policy loss | -0.2138750 | -0.2138750 |
| Entropy | 0.7945057 | 0.7944770 |
| Pre-clip gradient norm | 2.0024540 | 1.9752408 |
| Post-clip gradient norm | 2.0024538 | 1.9752408 |
| Parameter changed | yes | yes |
| Updated parameters finite | yes | yes |
| Adam state created | yes | yes |

Importance ratios were finite. Gradient shapes matched parameter shapes, all inspected gradients were finite, and masked probabilities remained excluded when the same historical minibatch was evaluated after the update.

## Critic Loss, Backward, And Optimizer

One real `VCritic.update` was run for each profile.

| metric | lifecycle | legacy |
|---|---:|---:|
| Critic scalar parameters | 888543 | 770895 |
| Parameter tensors with gradients | 12 | 12 |
| Value loss | 0.4639370 | 0.5888529 |
| Pre-clip gradient norm | 10.6641884 | 12.8111763 |
| Post-clip gradient norm | 10.0002203 | 10.0000655 |
| Parameter changed | yes | yes |
| Updated parameters finite | yes | yes |
| Adam state created | yes | yes |

The small float32 excess above `10.0` in the recomputed post-clip norm is numerical accumulation tolerance. Installed `clip_grad_norm_` ran with `max_grad_norm=10.0`; all gradients and parameters remained finite.

## Actor Independence

The official three-actor contract passed:

```text
three distinct HAPPO wrappers
three distinct StochasticPolicy objects
three distinct Adam optimizers
distinct parameter storage
each optimizer bound to its current actor parameters
actor 0 changed after its update
actor 1 remained bitwise unchanged
actor 2 remained bitwise unchanged
```

## ValueNorm

ValueNorm was passed to the real critic update. Its debiasing state changed through `VCritic.cal_value_loss -> ValueNorm.update`, and its resulting mean/variance remained finite.

No ValueNorm update was fabricated outside the installed critic path.

## Legacy Regression

The legacy profile passed the same essential chain:

```text
909-wide actor construction and forward
2727-wide centralized critic construction and forward
51-wide historical action mask
actor and EP critic buffer insertion
actor and critic feed-forward generator alignment
masked HAPPO loss/backward/Adam step
VCritic loss/backward/Adam step
finite gradients and parameters
independent actor isolation
ValueNorm update
```

No lifecycle observation fields were required by legacy synthetic inputs.

## Negative Tests

Project-local readiness assertions rejected:

```text
actor widths 1058 and 1060
shared widths 3182 and 3184
available-actions widths 50 and 52
all-zero available-action rows
an action disabled by its historical mask
NaN actor observation
NaN shared observation
NaN advantage
NaN return
wrong actor count
share_param=true
FP state type
chunked recurrent lifecycle
naive recurrent lifecycle
```

The installed actor and critic were also called with incorrect observation widths and failed in their normalization/input boundary as expected.

## Test Results

New Phase 9G-8F-4 suite:

```text
PASS 15/15
```

Required regressions:

| suite | result |
|---|---|
| Phase 9G-8F-1 contract core | PASS, 27/27 |
| Phase 9G-8F-2 save integration | PASS, 15/15 |
| Phase 9G-8F-3 all-loader integration | PASS, 15/15 |
| Phase 9G-8E mask/HARL replay | PASS, 11/11 |
| Phase 9G-8E-R feed-forward guard | PASS, 9/9 |

Total:

```text
PASS 92/92
```

Validation:

```text
py_compile: PASS
git diff --check: PASS
```

## Known Limitations

- This is a synthetic CPU readiness validation, not an environment rollout or policy-performance result.
- The test runs one direct real `HAPPO.update` and one direct real `VCritic.update` per profile, not the full multi-epoch training loop.
- Lifecycle recurrent, FP critic, `share_param=true`, HATRPO, and HAA2C remain outside the official support matrix.
- The installed chunked recurrent generator incompatibility remains documented and unchanged.
- Checkpoint output equivalence and post-load continuation are deferred to Phase 9G-8F-5.
- Exact resume and fine-tuning remain unsupported.
- Resolver-enabled training remains prohibited pending the remaining readiness phases.

## Non-Modification Confirmation

```text
installed HARL: not modified
Conda environment: not modified
actor/critic architecture: not modified
hidden sizes: not modified
observation/shared/action contracts: not modified
available-action semantics: not modified
resolver and Contract C: not modified
checkpoint save/load behavior: not modified
checkpoint saved or loaded: no
assignment environment constructed: no
AppLauncher / Isaac Sim: not launched
environment rollout: not run
training loop: not run
playback/evaluation: not run
commit: not made
```

## Next Phase Boundary

```text
Phase 9G-8F-5:
Checkpoint Save / Load / Continuation Smoke
```

No Phase 9G-8F-5 work was started.

## Final Decision

```text
PASS
```

The accepted lifecycle and legacy assignment dimensions complete the real installed feed-forward HAPPO actor, centralized EP critic, historical-mask buffer, loss, backward, gradient-clipping, ValueNorm, and optimizer paths with finite synthetic CPU data.
