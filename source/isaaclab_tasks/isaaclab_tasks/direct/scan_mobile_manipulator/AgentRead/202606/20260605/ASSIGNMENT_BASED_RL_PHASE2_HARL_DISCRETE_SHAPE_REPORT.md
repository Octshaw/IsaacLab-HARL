# Assignment-Based RL Phase 2 HARL Discrete Shape Report

Date: 2026-06-05

Scope: Phase 2 investigation and minimal repo-local integration preparation only. This phase does not run training, does
not modify scan env reward, does not change the scan env's underlying 9D action space, and does not modify
`assignment_controller.py`.

## 1. Phase 2 Result

HARL core supports Discrete action spaces well enough for assignment RL:

- `gymnasium.spaces.Discrete(num_viewpoints + 1)` can be constructed per agent.
- HARL `StochasticPolicy -> ACTLayer` creates a `Categorical` head for Discrete spaces.
- HARL sampled Discrete actions are scalar ids with shape `[num_envs, 1]`, not one-hot vectors.
- `OnPolicyActorBuffer` allocates `actions` as `[episode_length, num_envs, 1]` and `available_actions` as
  `[episode_length + 1, num_envs, num_viewpoints + 1]`.
- `available_actions` masks are applied inside `Categorical.forward()` by setting unavailable logits to a large negative
  value.

The current installed HARL IsaacLab integration does not support Discrete end to end:

- The installed IsaacLab wrapper converts all action spaces to Box and returns `available_actions=None`.
- The installed on-policy runner computes max action width with `.shape[0]`, which fails for standard Discrete spaces.
- The installed HARL IsaacLabEnv wrapper returns `[None] * n_threads` for reset/step masks, so Categorical actors would
  not receive assignment masks.
- The project `play.py` also allocates action tensors via `.shape[0]` and passes `available_actions=None`.

No installed `site-packages` files were modified in this phase.

## 2. Files Checked

Installed HARL files checked:

- `C:\isaacenvs\isaac45_harl\Lib\site-packages\harl\envs\env_wrappers.py`
  - `IsaacLabWrapper.reset()`
  - `IsaacLabWrapper.step()`
  - `IsaacLabWrapper.action_space`
  - `ShareDummyVecEnv.reset()/step_wait()`
  - `ShareSubprocVecEnv.reset()/step_wait()`
- `C:\isaacenvs\isaac45_harl\Lib\site-packages\harl\envs\isaaclab\Isaac_lab_env.py`
  - `IsaacLabEnv.__init__()`
  - `IsaacLabEnv.reset()`
  - `IsaacLabEnv.step()`
- `C:\isaacenvs\isaac45_harl\Lib\site-packages\harl\runners\on_policy_base_runner.py`
  - `OnPolicyBaseRunner.__init__()`
  - `OnPolicyBaseRunner.warmup()`
  - `OnPolicyBaseRunner.collect()`
  - `OnPolicyBaseRunner.insert()`
  - `OnPolicyBaseRunner.eval()`
  - `OnPolicyBaseRunner.render()`
- `C:\isaacenvs\isaac45_harl\Lib\site-packages\harl\common\buffers\on_policy_actor_buffer.py`
  - `OnPolicyActorBuffer.__init__()`
  - `OnPolicyActorBuffer.insert()`
  - actor mini-batch generators
- `C:\isaacenvs\isaac45_harl\Lib\site-packages\harl\utils\envs_tools.py`
  - `get_shape_from_act_space()`
  - `make_train_env()`
  - `make_eval_env()`
- `C:\isaacenvs\isaac45_harl\Lib\site-packages\harl\models\base\act.py`
  - `ACTLayer.__init__()`
  - `ACTLayer.forward()`
  - `ACTLayer.evaluate_actions()`
- `C:\isaacenvs\isaac45_harl\Lib\site-packages\harl\models\base\distributions.py`
  - `Categorical.forward()`
  - `FixedCategorical.log_probs()`
- `C:\isaacenvs\isaac45_harl\Lib\site-packages\harl\models\policy_models\stochastic_policy.py`
  - `StochasticPolicy.__init__()`
  - `StochasticPolicy.forward()`

Project files checked:

- `scripts\reinforcement_learning\harl\train.py`
- `scripts\reinforcement_learning\harl\play.py`
- `source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\assignment_rl_interface.py`
- `scripts\environments\test_assignment_rl_interface.py`

## 3. Key Findings

### Action Space Read And Conversion

`IsaacLabWrapper.action_space` currently rebuilds every underlying IsaacLab action space as:

```python
gymnasium.spaces.Box(v.low.flatten()[-1], v.high.flatten()[-1], (v.shape[-1],))
```

This loses any Discrete semantics. An assignment wrapper must expose `Discrete(num_viewpoints + 1)` at the HARL-facing
boundary while keeping the scan env's underlying 9D action dict unchanged.

`Isaac_lab_env.py` hardcodes the installed `IsaacLabWrapper` / `IsaacLabAdversarialWrapper` selection. A repo-local
assignment wrapper cannot be selected by the installed `IsaacLabEnv` without either:

- a repo-local replacement/shim for the HARL IsaacLabEnv entry path, or
- a minimal patch/monkeypatch that makes the installed path choose the repo-local wrapper.

### Actor Policy Creation

HARL actor core is ready for Discrete:

- `StochasticPolicy` creates `ACTLayer(action_space, ...)`.
- `ACTLayer.__init__()` branches on `action_space.__class__.__name__ == "Discrete"`.
- For Discrete, `ACTLayer` creates `Categorical(inputs_dim, action_space.n, ...)`.
- For Box, it creates `DiagGaussian(..., action_space.shape[0], ...)`.

The Phase 2 smoke verified that `Discrete(13)` creates a `Categorical` head and masked logits force the sampled scalar
action id to the only available category.

### Action Buffer Creation

`OnPolicyActorBuffer.__init__()` already uses `get_shape_from_act_space(act_space)`.

For Discrete:

- `get_shape_from_act_space(Discrete)` returns `1`.
- `actions` shape becomes `[episode_length, n_rollout_threads, 1]`.
- `available_actions` is allocated with width `act_space.n`.

This is the correct storage contract for assignment RL.

### Available Actions Buffer

HARL actor buffer allocates `available_actions` only for Discrete spaces. The current installed IsaacLabEnv prevents that
from being useful because reset/step return `[None] * n_threads`.

The assignment path should return:

```text
available_actions: torch.Tensor  # [num_envs, num_agents, num_viewpoints + 1]
```

Then the runner already slices per actor:

```python
available_actions[:, agent_id]
```

### Runner Action Tensor Allocation

`OnPolicyBaseRunner.__init__()` still uses:

```python
if val.shape[0] > self.max_action_space:
    self.max_action_space = val.shape[0]
```

This fails for standard Gymnasium Discrete because `Discrete.shape == ()`, so `shape[0]` raises `IndexError`.

The replacement logic should use the scalar action storage dim:

```python
get_shape_from_act_space(space)  # Discrete -> 1
```

The rest of `collect()` can stack scalar Discrete actions as `[num_envs, num_agents, 1]`.

### Wrapper Step Action Slicing

Installed `IsaacLabWrapper.step()` does:

```python
actions = {
    self._agent_map_inv[i]: actions[i][:, : self.action_space[i].shape[0]]
    for i in range(self.unwrapped.num_agents)
}
```

This is Box-only and directly forwards raw policy actions to the env. Assignment RL must instead:

1. receive scalar Discrete ids in HARL layout after `IsaacLabEnv.step()` permutation,
2. decode them to assignment `[num_envs, num_agents]`,
3. call `viewpoint_assignment_to_actions(env, assignment)`,
4. forward the resulting 9D action dict to the scan env.

This decoding belongs in a repo-local assignment wrapper in Phase 3, not in the scan env.

### Play Path

Project `scripts\reinforcement_learning\harl\play.py` currently:

- computes `max_action_space` using `obs_space.shape[0]` over `runner.env.action_space`,
- preallocates `actions` as `[num_envs, num_agents, max_action_space]`,
- calls `get_actions(..., None, True)`,
- directly calls `runner.env.step(actions)`.

Assignment play will need the same scalar action dim helper and must pass `available_actions[:, agent_id, :]`.

## 4. Repo-Local Adapter Added

Added:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_adapter.py
```

It provides:

- `make_assignment_discrete_action_space(num_viewpoints)`
- `make_assignment_discrete_action_spaces(num_agents, num_viewpoints, agent_ids=None)`
- `get_harl_scalar_action_dim(action_space)`
- `get_harl_available_action_dim(action_space)`
- `get_max_harl_scalar_action_dim(action_spaces)`
- `make_harl_action_tensor(num_envs, action_spaces, device=None, dtype=torch.float32)`
- `AssignmentHarlAdapter`

This adapter intentionally does not call `env.step()`. It is a Phase 2 preparation layer for Phase 3's assignment-aware
wrapper.

## 5. Smoke Test Added

Added:

```text
scripts/environments/test_assignment_harl_discrete_shape.py
```

The smoke verifies:

- `Discrete(num_viewpoints + 1)` is constructed per agent.
- HARL scalar action width for Discrete is `1`.
- action tensor allocation is `[num_envs, num_agents, 1]`.
- assignment `available_actions` shape is `[num_envs, num_agents, num_viewpoints + 1]`.
- HARL `StochasticPolicy` creates a `Categorical` head for Discrete.
- a one-available-action mask forces sampled action id `3`.
- `OnPolicyActorBuffer` allocates scalar actions and Discrete `available_actions`.
- current `.shape[0]` usage on `Discrete` is a real blocker.

## 6. Minimal Implementation Recommendation

For Phase 3, prefer a repo-local path:

1. Add a repo-local assignment-aware IsaacLab wrapper that uses `AssignmentHarlAdapter`.
2. Add a repo-local HARL env shim that constructs the normal Isaac scan env but wraps it with the assignment wrapper when
   `assignment_rl=True`.
3. Add a repo-local runner shim or project entry-script route so the runner uses the repo-local env shim and scalar action
   dim helper.
4. Keep the scan env action space and reward unchanged.
5. Decode only inside the assignment wrapper before the underlying scan env receives 9D actions.

If the next phase insists on using the installed `OnPolicyBaseRunner` and installed `IsaacLabEnv` unchanged, the integration
is blocked because those installed files hardcode both the Box wrapper and `.shape[0]` Discrete-incompatible logic.

At this point, modifying installed HARL is not required. A repo-local shim/copy is more reviewable and can be selected from
the project scripts.

## 7. Verification

Commands run:

```powershell
D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python -c "import sys; print(sys.executable)"
D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python -m py_compile source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\assignment_harl_adapter.py
D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts\environments\test_assignment_harl_discrete_shape.py
D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python scripts\environments\test_assignment_rl_interface.py
D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python scripts\environments\test_assignment_harl_discrete_shape.py
```

Results:

- Interpreter check passed: `C:\isaacenvs\isaac45_harl\python.exe`.
- `py_compile` passed for the new adapter.
- `py_compile` passed for the new smoke script.
- Phase 1 utility self-check passed.
- Phase 2 Discrete shape smoke passed.
- The Phase 2 smoke printed a non-fatal dependency warning that the old `gym` package is unmaintained. The script exited
  with code 0.

## 8. Not Done

- No training was run.
- No long simulation or GUI was launched.
- No scan env reward change.
- No scan env underlying 9D action space change.
- No assignment controller control-logic change.
- No installed `site-packages` modification.
- No complete assignment-aware wrapper integration.
- No duplicate sequential mask implementation.
- No variable viewpoint-count support.

## 9. Next Step

Phase 3 should add an assignment-aware HARL wrapper/env shim that reuses:

- `assignment_rl_interface.py` for mask/decode/controller entry,
- `assignment_harl_adapter.py` for Discrete action spaces and scalar action dimensions.

The first Phase 3 validation should still avoid full training: instantiate the assignment wrapper, call reset, verify
`available_actions`, sample/construct scalar Discrete actions, decode to assignment, convert to 9D actions, and perform at
most a tiny headless bounded smoke only after the wrapper shape path is proven.
