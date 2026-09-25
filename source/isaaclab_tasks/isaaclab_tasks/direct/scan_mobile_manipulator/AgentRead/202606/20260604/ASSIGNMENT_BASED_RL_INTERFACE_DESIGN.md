# Assignment-Based RL Interface Design

Date: 2026-06-04

Scope: design only. This document does not modify Python source, training config, environment config, or reward.

## 1. Current Conclusion

The diagnostic report shows that current HARL training/play does not use the assignment controller. The current RL path is:

```text
HARL actor -> 9D continuous action -> HARL IsaacLab wrapper -> ScanMobileManipulatorEnv.step()
```

The baseline path is:

```text
random/nearest/greedy solver -> assignment -> viewpoint_assignment_to_actions(env, assignment) -> 9D action -> env.step()
```

The design target is to make assignment-based RL use the same second path:

```text
HARL categorical policy -> viewpoint id or no-op -> assignment tensor -> viewpoint_assignment_to_actions -> env.step()
```

The recommended minimum implementation should keep the underlying scan environment's 9D controller action contract intact and add an HARL-facing assignment interface above it.

## 2. Evidence From Current Code

- `scan_mobile_manipulator_env.py` currently exposes `action_spaces = {"robot_0": 9, "robot_1": 9, "robot_2": 9}`. This becomes a Box action space, so HARL builds 9D Gaussian actors.
- `get_assignment_problem()` already returns `feasible_mask` and `available_mask` with shape `[num_envs, num_agents, num_viewpoints]`.
- `viewpoint_assignment_to_actions(env, assignment)` already accepts `torch.long` assignment with shape `[num_envs, num_agents]`; `-1` means no-op; invalid, covered, or infeasible targets become zero 9D actions.
- `evaluate_scan_assignment.py` already runs `problem -> solver -> assignment -> viewpoint_assignment_to_actions -> env.step`.
- `play.py` currently calls `get_actions(..., None, True)` and then `runner.env.step(actions)` with raw policy actions.
- Current `harl.envs.env_wrappers.IsaacLabWrapper` returns `available_actions=None`, converts all IsaacLab multi-agent action spaces to Box, and slices actions using `.shape[0]`.
- HARL core supports Discrete action policies through `ACTLayer -> Categorical`, and `Categorical.forward()` applies `available_actions == 0` masking. However, the current IsaacLab wrapper and runner path are still Box-oriented.

## 3. Does Current HARL / IsaacLab Wrapper Support Discrete?

Answer: HARL core supports Discrete, but the current HARL IsaacLab integration does not support Discrete end to end for this task without changes.

Details:

- HARL core:
  - `ACTLayer` branches on `action_space.__class__.__name__ == "Discrete"` and creates a Categorical distribution.
  - `OnPolicyActorBuffer` allocates `available_actions` only for Discrete spaces.
  - `get_shape_from_act_space(Discrete)` returns action shape `1`.
  - `Categorical.forward()` masks logits by setting unavailable entries to a very negative value.
- Isaac Lab core:
  - `DirectMARLEnvCfg.action_spaces` can represent Discrete spaces. Isaac Lab's `spec_to_gym_space()` maps a single-value set like `{13}` to `gym.spaces.Discrete(13)`.
  - `sample_space(Discrete)` returns `torch.int64` tensors shaped `[num_envs, 1]`.
- Current HARL IsaacLab wrapper and runner:
  - The wrapper converts `self.unwrapped.action_spaces` to `gymnasium.spaces.Box(...)` by reading `.low`, `.high`, and `.shape`.
  - `OnPolicyBaseRunner.__init__` computes `max_action_space` using `val.shape[0]`, which is unsafe for standard Discrete spaces because their shape is scalar/empty.
  - `IsaacLabWrapper.step()` slices by `self.action_space[i].shape[0]` and passes the result directly into the underlying env. That is correct for 9D Box, but not for assignment ids that must be decoded before env.step.

Therefore, implementation must modify the HARL IsaacLab interface and runner shape handling, or provide an equivalent repo-local assignment wrapper that presents Discrete spaces and decodes before the underlying scan env receives actions.

## 4. Multi-Agent Discrete Action Space Feasibility

Using one `Discrete(num_viewpoints + 1)` action space per agent is feasible for the current fixed-size task.

For the current scan task:

```text
num_agents = 3
num_viewpoints = 12
action_dim_per_agent = 13
actions 0..11 = viewpoint ids
action 12 = no-op
```

All agents can share the same action space size. Heterogeneous robot capability should be represented through action masks, not through different action dimensions. This keeps parameter sharing valid when enabled and avoids HARL heterogeneous action padding complexity.

The output from HARL Categorical should be treated as one scalar action per agent, not a 13D one-hot vector.

## 5. Fixed `num_viewpoints` Action Space Definition

Recommended for the minimum implementation:

- Keep `ScanMobileManipulatorEnvCfg.action_spaces` as the existing 9D Box-style action contract.
- Add an HARL-facing assignment mode in the IsaacLab wrapper that advertises:

```python
gymnasium.spaces.Discrete(env.unwrapped.num_viewpoints + 1)
```

for each robot agent.

This preserves the underlying environment/controller contract:

```text
HARL-facing Discrete action -> wrapper decode -> controller 9D action -> scan env 9D action
```

Alternative if building a dedicated assignment env variant later:

```python
action_spaces = {
    "robot_0": {num_viewpoints + 1},
    "robot_1": {num_viewpoints + 1},
    "robot_2": {num_viewpoints + 1},
}
```

or explicit `gymnasium.spaces.Discrete(num_viewpoints + 1)`.

That alternative would require the scan env itself to accept discrete ids in `_pre_physics_step()` or to wrap the env before DirectMARLEnv receives actions. It is more invasive and is not the recommended MVP.

## 6. Limitation With Arbitrary Viewpoint Counts

HARL's current policy and buffer interfaces require a fixed action dimension.

If `num_viewpoints` changes across runs, env instances, or episodes:

- The actor output layer size changes, so checkpoints cannot load across different `num_viewpoints` without architecture mismatch.
- `available_actions` buffer shape is fixed at runner creation.
- Vectorized environments need the same action dimension for every env in the batch.
- HARL Categorical is not a pointer network and cannot naturally choose among a variable-length set.
- Current scan observations expose only nearest viewpoint slots and do not include all viewpoint ids as a variable-length set.

Future variable-size support should use one of these designs:

- Fixed maximum number of viewpoints, pad unused ids, and mask padded ids.
- Separate policies/checkpoints for each fixed viewpoint count.
- A custom set/pointer policy outside the current HARL Categorical interface.

For the next implementation, use the fixed `num_viewpoints = len(cfg.viewpoint_poses)` route.

## 7. `available_actions` / Action Mask Interface

HARL expects `available_actions` as a float/bool-like mask where `1` means selectable and `0` means masked.

Recommended shape:

```python
available_actions: torch.Tensor  # shape [num_envs, num_agents, num_viewpoints + 1]
```

Construction:

```python
problem = env.unwrapped.get_assignment_problem()
view_mask = problem["available_mask"].to(dtype=torch.float32)
noop_mask = torch.ones(problem["num_envs"], problem["num_agents"], 1, device=view_mask.device)
available_actions = torch.cat([view_mask, noop_mask], dim=-1)
```

Wrapper returns:

- On reset: `(obs, shared_obs, available_actions)`
- On step: `(obs, shared_obs, rewards, dones, info, available_actions)`

Policy calls must pass the relevant per-agent slice:

```python
available_actions[:, agent_id, :]  # shape [num_envs, num_viewpoints + 1]
```

The no-op column must always be available to avoid all-zero masks when a robot has no feasible uncovered viewpoint.

## 8. Mask Conditions

The assignment action mask should include these conditions:

- In range: represented structurally by the Discrete size. Valid policy ids are `0..num_viewpoints`; no extra mask entry is needed for out-of-range ids.
- Uncovered: viewpoint action `j` is available only when `viewpoints_covered[:, j] == False`.
- Feasible: viewpoint action `j` is available only when `feasible_mask[:, agent, j] == True`.
- No-op: action id `num_viewpoints` should always be available.
- Duplicate avoidance: do not include as a static per-agent mask in the MVP.

Reason for duplicate avoidance decision:

Same-step duplicate avoidance depends on other agents' sampled actions. A static mask computed before all agents act cannot know which viewpoint another agent will choose. Post-processing duplicates after sampling would make the environment execute a different action than the action/log-prob stored by HARL, which weakens on-policy correctness.

MVP policy:

- Mask unavailable, covered, and infeasible viewpoints.
- Allow duplicate same-step selections.
- Log `assignment_duplicate_count`.
- Let the current controller move both robots if duplicates occur.

Advanced duplicate avoidance:

- Implement sequential action sampling inside HARL collection/play.
- After agent `i` chooses viewpoint `j`, set `available_actions[:, later_agents, j] = 0` before sampling later agents.
- Store the actual masks used for each agent in the actor buffer.
- Keep no-op exempt from duplicate masking.

## 9. Decode HARL Discrete Output To Assignment

Expected HARL action tensor after collection:

```python
actions  # shape [num_envs, num_agents, 1]
```

Inside the current HARL IsaacLab path, `IsaacLabEnv.step()` permutes this before calling `IsaacLabWrapper.step()`, so the wrapper may receive:

```python
actions  # shape [num_agents, num_envs, 1]
```

Recommended wrapper decode:

```python
raw_ids = torch.stack(
    [actions[agent_index, :, 0] for agent_index in range(num_agents)],
    dim=1,
).to(device=env.unwrapped.device, dtype=torch.long)

noop_id = env.unwrapped.num_viewpoints
assignment = torch.where(raw_ids == noop_id, torch.full_like(raw_ids, -1), raw_ids)
```

The decoded result must be:

```python
assignment: torch.LongTensor  # shape [num_envs, num_agents]
```

Validation:

```python
assert assignment.dtype == torch.long
assert assignment.shape == (env.num_envs, env.unwrapped.num_agents_cfg)
assert torch.all((assignment == -1) | ((assignment >= 0) & (assignment < env.unwrapped.num_viewpoints)))
```

Out-of-range ids should be impossible when the HARL-facing action space is `Discrete(num_viewpoints + 1)`. If they appear due to a wrapper bug, fail fast in debug mode and convert to no-op only in a defensive release path.

## 10. No-Op Handling

Use `num_viewpoints` as the HARL-visible no-op action id.

Decode:

```text
0..num_viewpoints-1 -> viewpoint id
num_viewpoints -> -1
```

The controller already treats `-1` as invalid/out-of-range and returns exact zero 9D action for that robot. This should be preserved.

Why not expose `-1` directly to HARL:

- `Discrete(n)` cannot emit negative ids.
- Keeping no-op as the final category gives a clean mask column and stable checkpoint shape.

## 11. Reusing `viewpoint_assignment_to_actions`

The assignment RL wrapper should call the existing controller directly:

```python
from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_controller import (
    viewpoint_assignment_to_actions,
)

continuous_actions = viewpoint_assignment_to_actions(env.unwrapped, assignment)
obs, reward, terminated, truncated, info = env.step(continuous_actions)
```

Do not duplicate controller math in HARL code. The controller is the single bridge from assignment ids to 9D continuous actions.

The wrapper should add diagnostic info without changing reward:

```python
info["assignment_rl"] = {
    "raw_action_ids": raw_ids.detach(),
    "assignment": assignment.detach(),
    "available_actions": available_actions.detach(),
}
```

Keep diagnostics lightweight; avoid CPU copies during training except for logging aggregates.

## 12. Required Future Code Changes By Area

`scripts/reinforcement_learning/harl/train.py`:

- Add an explicit flag such as `--assignment_rl`.
- Pass this mode through `env_args` so the HARL IsaacLab env/wrapper exposes assignment action spaces.
- Print whether assignment RL is enabled, `num_viewpoints`, `action_dim`, and no-op id.
- Use a new experiment name for assignment policies because 9D checkpoints are incompatible with Discrete actors.

`scripts/reinforcement_learning/harl/play.py`:

- Add `--assignment_rl`.
- Make action tensor allocation robust for Discrete spaces using HARL's `get_shape_from_act_space()` or equivalent.
- Pass `available_actions[:, agent_id, :]` into `get_actions()` instead of `None`.
- Decode through the same wrapper path as training.
- Add a bounded max-step option for smoke playback if not already present.

HARL runner / IsaacLab wrapper:

- Stop assuming action spaces have `.shape[0]`; use `get_shape_from_act_space()`.
- Preserve Discrete spaces instead of converting all IsaacLab multi-agent action spaces to Box.
- In assignment mode, expose `Discrete(num_viewpoints + 1)` to HARL while keeping the underlying scan env's 9D action space untouched.
- Return `available_actions` on reset and step.
- Decode `[num_agents, num_envs, 1]` discrete actions into `[num_envs, num_agents]` assignment.
- Call `viewpoint_assignment_to_actions()` before stepping the underlying env.

Scan env:

- No MVP change required if the HARL wrapper handles assignment decode.
- Optional future helper: add `get_assignment_action_mask(include_noop=True)` as a thin wrapper around `get_assignment_problem()`.
- Do not change reward for the MVP.
- Do not replace `_pre_physics_step()` with discrete handling unless creating a separate assignment env variant.

Baseline evaluator:

- Already uses the correct assignment-controller-env path.
- Optionally import shared mask/decode validation utilities so RL and baselines agree on mask semantics.
- Keep random/nearest/greedy solvers returning `assignment: torch.long [num_envs, num_agents]`.
- Continue logging duplicate assignment count so RL can be compared fairly.

## 13. Ensuring One Controller-Env Path

Create a small shared interface module, for example:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_rl_interface.py
```

Suggested functions:

```python
def make_assignment_action_mask(problem: dict, include_noop: bool = True) -> torch.Tensor:
    ...

def decode_discrete_assignment(actions: torch.Tensor, num_viewpoints: int, layout: str) -> torch.LongTensor:
    ...

def assignment_to_env_actions(env, assignment: torch.Tensor) -> dict[str, torch.Tensor]:
    return viewpoint_assignment_to_actions(env, assignment)
```

Use this module in:

- HARL assignment wrapper.
- `play.py` diagnostics, if needed.
- Baseline evaluator validation, if useful.

This gives all policies the same final path:

```text
assignment tensor -> viewpoint_assignment_to_actions -> env.step
```

Random, nearest, and greedy still choose assignments with solvers. RL chooses assignments with a categorical policy. The downstream controller and env path are identical.

## 14. Minimal Viable Implementation

MVP goal: run a small fixed-12-viewpoint assignment RL smoke test.

MVP constraints:

- Fixed `num_viewpoints`.
- Per-agent `Discrete(num_viewpoints + 1)`.
- No-op id is `num_viewpoints`.
- Hard mask for feasible and uncovered viewpoints plus no-op.
- No hard duplicate avoidance during training.
- No reward change.
- No scan env action-space change.
- No variable-size viewpoint research.
- No long training.

Expected successful smoke:

- HARL actor output is Categorical with 13 logits per agent, not Gaussian 9D.
- `available_actions` is not `None` and has shape `[num_envs, 3, 13]`.
- Decoded assignment has shape `[num_envs, 3]`, dtype `torch.long`.
- Controller output action dict has 3 keys and each action tensor has shape `[num_envs, 9]`.
- Training command completes a tiny run and saves a model.
- Baseline evaluator remains unchanged and still passes.

## 15. Verification Commands For MVP

Use the project conda environment:

```powershell
D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python -c "import sys; print(sys.executable)"
```

Syntax checks for changed repo files:

```powershell
D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts\reinforcement_learning\harl\train.py
D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts\reinforcement_learning\harl\play.py
D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python -m py_compile source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\assignment_rl_interface.py
```

If HARL installed package files are modified, also run targeted `py_compile` on those exact files.

Baseline regression smoke:

```powershell
D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python scripts\environments\evaluate_scan_assignment.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --solver greedy --num_envs 2 --num_episodes_per_env 1 --max_steps_per_episode 20 --headless
```

Assignment RL smoke:

```powershell
D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python scripts\reinforcement_learning\harl\train.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --algorithm happo --assignment_rl --num_envs 2 --num_env_steps 16 --save_interval 1 --log_interval 1 --exp_name codex_assignment_rl_smoke --headless "agent.train.episode_length=8"
```

Assignment RL play smoke after a model exists:

```powershell
D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python scripts\reinforcement_learning\harl\play.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --algorithm happo --assignment_rl --num_envs 1 --dir <assignment_model_dir> --headless --num_env_steps 32
```

Do not use old 9D continuous checkpoints with assignment mode.

## 16. Risk Points

- Action space shape: current runner uses `.shape[0]`; Discrete needs `get_shape_from_act_space()`.
- Wrapper action-space conversion: current wrapper converts all action spaces to Box, losing Discrete semantics.
- Mask format: HARL expects `[num_envs, num_agents, action_dim]` at env level and `[num_envs, action_dim]` per actor.
- Mask all-zero failure: no-op must always be available.
- Device mismatch: masks and assignments should stay on `env.device` or the runner device consistently.
- Dtype mismatch: HARL may store actions as float in buffers; wrapper decode must cast to `torch.long`.
- Parallel env shape: train path may pass `[num_envs, num_agents, 1]`, while wrapper internals may see `[num_agents, num_envs, 1]`.
- Save/load incompatibility: 9D Gaussian actor checkpoints cannot load into 13-way Categorical actors.
- Play path: current `play.py` allocates action tensors using `.shape[0]` and passes `available_actions=None`.
- Duplicate selections: independent agents can select the same viewpoint in the same step unless sequential masking is implemented.
- Heterogeneous robot capability: feasibility mask must be per-agent, not global.
- Stale mask: mask must be recomputed after reset and after every env step.
- Controller validity: current controller zeroes covered/infeasible/no-op assignments; this is useful safety but can hide mask bugs unless diagnostics log invalid counts.
- Baseline comparability: random/nearest/greedy avoid duplicates; MVP RL may not. Report duplicate metrics when comparing.
- Installed HARL package edits: if implementation changes `C:\isaacenvs\isaac45_harl\Lib\site-packages\harl`, those edits are outside the repo and harder to review. Prefer repo-local shims where practical, but runner shape assumptions may still require a HARL patch.

## 17. Phased Implementation Plan

Phase 1: Shared assignment RL utilities.

- Add `assignment_rl_interface.py`.
- Implement mask creation, no-op convention, decode validation, and optional duplicate metrics.
- Verify with `py_compile` and a small headless script or evaluator import.

Phase 2: HARL Discrete shape support.

- Patch runner/play allocation paths to use `get_shape_from_act_space()`.
- Ensure Discrete buffers allocate `available_actions`.
- Verify with `py_compile` and runner initialization smoke if possible.

Phase 3: Assignment-aware IsaacLab wrapper mode.

- Add `assignment_rl` mode.
- Expose per-agent `Discrete(num_viewpoints + 1)`.
- Return `available_actions` from reset/step.
- Decode policy actions to assignment.
- Call `viewpoint_assignment_to_actions()`.
- Verify with a tiny HAPPO run of 16 steps.

Phase 4: Play/eval path.

- Add `--assignment_rl` to play.
- Pass masks into deterministic policy actions.
- Add max-step bounded play smoke.
- Verify with a model saved by Phase 3.

Phase 5: Baseline alignment and comparison.

- Reuse shared mask/validation utilities in the baseline evaluator if helpful.
- Run random/nearest/greedy smoke after wrapper changes.
- Add an assignment-RL comparison command only after Phase 3 and Phase 4 pass.

Phase 6: Optional duplicate avoidance.

- If duplicate selections materially hurt learning, add sequential mask updates during collection/play.
- Store the actual per-agent masks used for sampling.
- Keep no-op always available.
- Verify on a tiny run before any long training.

Each phase should update `TASK_PROGRESS.md` before moving on.

## 18. Recommended Route

Recommended:

- Keep scan env's underlying 9D action contract.
- Add HARL-facing assignment mode that exposes `Discrete(num_viewpoints + 1)`.
- Use `num_viewpoints` as no-op and decode to `-1`.
- Generate `available_actions` from `get_assignment_problem()["available_mask"]` plus no-op.
- Reuse `viewpoint_assignment_to_actions()` as the only assignment-to-9D bridge.
- Start with fixed 12 viewpoints and no hard duplicate avoidance.
- Treat old 9D checkpoints as incompatible with assignment mode.

## 19. Not Recommended

Not recommended:

- Do not train assignment RL by outputting 9D continuous actions and rounding part of the vector into ids.
- Do not change reward before the assignment interface is proven.
- Do not change scan env `action_spaces` to Discrete in the MVP if that breaks baseline/controller users.
- Do not implement variable-number viewpoint support before the fixed-size assignment smoke passes.
- Do not silently post-process duplicate RL assignments during training unless the stored action/log-prob semantics are also made consistent.
- Do not compare assignment RL with baselines without logging mask validity, no-op count, duplicate count, and controller action norms.
