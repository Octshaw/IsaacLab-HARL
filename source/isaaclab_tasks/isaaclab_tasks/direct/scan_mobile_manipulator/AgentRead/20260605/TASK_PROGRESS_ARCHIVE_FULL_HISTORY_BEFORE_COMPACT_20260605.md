# TASK_PROGRESS

This file tracks implementation progress for the high-level viewpoint assignment path.

## Current status

Status: Assignment-based RL Phase 4 assignment-mode play/eval smoke complete

Current phase: Phase 4 only; waiting for the next instruction before long training or formal comparison

## Current assignment RL Phase 4 play/eval smoke summary

This session implemented only `Assignment-based RL Phase 4: assignment-mode play/eval smoke`.

Phase 4 goal:
- Add a bounded assignment checkpoint play/eval path.
- Restore an assignment-mode HARL Categorical actor checkpoint.
- Run deterministic scalar Discrete actions through `available_actions[:, agent_id, :]`.
- Reuse `AssignmentHarlWrapper` so actions decode to assignment ids, call `viewpoint_assignment_to_actions()`, and step the
  unchanged underlying 9D scan env.
- Keep the existing continuous `scripts/reinforcement_learning/harl/play.py` path unchanged.

Files created:
- `scripts/reinforcement_learning/harl/play_assignment.py`

Files modified:
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md`

External package modifications:
- None. No files under `C:\isaacenvs\isaac45_harl\Lib\site-packages` were modified.

Play/eval assignment mode path:
- `play_assignment.py` is a dedicated assignment-only bounded smoke script.
- It accepts `--assignment_rl` for explicitness, but the script runs assignment mode by design even if that flag is
  omitted.
- It constructs the normal scan task from Hydra config and wraps it with `make_assignment_harl_env()`.
- It creates HARL actors from the assignment-facing `Discrete(num_viewpoints + 1)` action spaces.
- It loads actor state dicts from `--dir` using the naming convention
  `actor_agent_<robot_id>.pt`.
- It calls `actor.act(..., available_actions[:, agent_id, :], deterministic=True)`.
- It stores scalar Discrete ids in a `[num_envs, num_agents, 1]` action tensor from `make_harl_action_tensor()`.
- It calls `AssignmentHarlWrapper.step(actions)`, which decodes actions to assignments, calls
  `viewpoint_assignment_to_actions()`, and steps the underlying scan env with a 9D action dict.

Checkpoint restore:
- Passed using the Phase 3B checkpoint directory:
  `E:\Project\IsaacLab_HARL\results\isaaclab\Isaac-Scan-Mobile-Manipulator-Direct-v0\happo\codex_assignment_rl_smoke\seed-00001-2026-06-05-21-56-55\models`
- Restored:
  - `actor_agent_robot_0.pt`
  - `actor_agent_robot_1.pt`
  - `actor_agent_robot_2.pt`
- All restored actors printed `action_type=Discrete distribution_head=Categorical`.

Available actions:
- Reset returned `available_actions.shape=(1, 3, 13)` on `cuda:0`.
- The play loop passes each agent slice `available_actions[:, agent_id, :]` into deterministic actor inference.
- `available_actions` is asserted non-`None` on reset and after every step.

Assignment diagnostics output:
- The bounded smoke printed step diagnostics including:
  - `assignment`
  - `noop_count`
  - `duplicate_count`
  - `valid_action_count`
  - `coverage_ratio`
  - `new_viewpoints`
  - `mean_reward`
- Example first step:
  - `assignment=[[8, 5, 5]]`
  - `noop_count=[0.0]`
  - `duplicate_count=[1.0]`
  - `valid_action_count=[3.0]`
  - `coverage_ratio=0.000000`
  - `new_viewpoints=0.000000`
  - `mean_reward=-0.009778`

Validation commands run:
- `D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python -c "import sys; print(sys.executable)"`
  - Passed; printed `C:\isaacenvs\isaac45_harl\python.exe`.
- `D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts\reinforcement_learning\harl\play_assignment.py`
  - Passed before and after adding the CUDA warm-up.
- `D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python scripts\environments\test_assignment_rl_interface.py`
  - Passed; printed `[OK] assignment_rl_interface self-check passed`.
- `D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python scripts\environments\test_assignment_harl_discrete_shape.py`
  - Passed; printed `[OK] assignment HARL Discrete shape smoke passed`.
- `D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python scripts\environments\test_assignment_harl_wrapper_smoke.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --num_envs 1 --max_steps 2 --headless`
  - Passed with exit code 0.
- First attempt:
  `D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python scripts\reinforcement_learning\harl\play_assignment.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --algorithm happo --assignment_rl --num_envs 1 --dir E:\Project\IsaacLab_HARL\results\isaaclab\Isaac-Scan-Mobile-Manipulator-Direct-v0\happo\codex_assignment_rl_smoke\seed-00001-2026-06-05-21-56-55\models --headless --max_steps 32`
  - Failed after successful actor restore/reset with `CUBLAS_STATUS_NOT_INITIALIZED` on the first policy MLP forward.
  - This matched the known HARL train startup issue; `play_assignment.py` was updated with the same small CUDA warm-up
    before `AppLauncher`.
- Retry with the same 32-step command:
  - Passed with exit code 0.
  - Completed `[OK] assignment play smoke completed max_steps=32`.

Known runtime notes:
- Isaac/Kit printed normal non-fatal startup warnings, including OmniHub inaccessible, unsupported Intel GPU, and old-Gym
  dependency warnings from HARL's dependency chain.
- The 16-step Phase 3B checkpoint is intentionally weak; Phase 4 only verifies restore/inference/controller wiring, not
  policy quality or coverage improvement.

Code intentionally not modified in this phase:
- No installed HARL package changes.
- No scan env reward changes.
- No scan env underlying 9D action-space changes.
- No `assignment_controller.py` control-logic changes.
- No baseline solver changes.
- No duplicate sequential mask.
- No arbitrary/variable viewpoint-count support.
- No old 9D continuous checkpoint was loaded in assignment mode.
- No long training, GUI run, or formal performance comparison was run.

Not completed in this phase:
- No integration of assignment mode into the existing continuous `play.py`.
- No formal eval script with aggregate metrics.
- No long assignment training.
- No comparison against random/nearest/greedy baselines.

Suggested next step:
- Wait for explicit instruction before continuing. The next narrow step could either run a longer but still bounded
  assignment training smoke, or add a formal assignment eval script that aggregates the same diagnostics and compares the
  assignment checkpoint against random/nearest/greedy without changing rewards or controller logic.

## Current assignment RL Phase 3B tiny training smoke summary

This session implemented only `Assignment-based RL Phase 3B: integrate repo-local assignment wrapper into HARL tiny
training smoke`.

Phase 3B goal:
- Add an explicit project-local `--assignment_rl` mode to `scripts/reinforcement_learning/harl/train.py`.
- Keep the default no-flag HARL path on the original 9D continuous scan action space.
- In assignment mode, use HARL Discrete/Categorical actor output, pass real `available_actions`, decode scalar ids in a
  repo-local wrapper/facade, call `viewpoint_assignment_to_actions()`, and step the unchanged scan env with its 9D action
  dict.
- Run only a bounded 16-step headless HAPPO smoke, not long training.

Files created:
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_training.py`

Files modified:
- `scripts/reinforcement_learning/harl/train.py`
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_wrapper.py`
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md`

External package modifications:
- None. No files under `C:\isaacenvs\isaac45_harl\Lib\site-packages` were modified.

Assignment mode train route:
- `train.py --assignment_rl` calls `register_assignment_harl_runner(RUNNER_REGISTRY, args["algo"])`.
- The registry entry for HA algorithms (`happo`, `hatrpo`, `haa2c`) is replaced at runtime with the repo-local
  `AssignmentOnPolicyHARunner`.
- `env_args["assignment_rl"] = True` selects `AssignmentIsaacLabEnv`, which constructs the normal scan env and wraps it
  with `AssignmentHarlWrapper`.
- The underlying scan env still receives only the original 9D per-agent action dict.
- `--assignment_rl` prints a checkpoint compatibility warning because old 9D continuous checkpoints are not compatible
  with Discrete/Categorical assignment policies.

Discrete action shape handling:
- The repo-local runner subclass copies the installed HARL base-runner initialization only where necessary.
- The installed `.shape[0]` max-action-width assumption is replaced with
  `get_harl_scalar_action_dim(action_space)`, so `Discrete(num_viewpoints + 1)` uses scalar storage width `1`.
- Actor buffers still use HARL's existing `OnPolicyActorBuffer`, whose Discrete path allocates scalar actions and
  `available_actions` buffers.

Available actions:
- `AssignmentIsaacLabEnv.reset()` and `step()` assert `available_actions` is not `None`.
- Assignment smoke printed `available_actions.shape=(2, 3, 13)` for `num_envs=2`, `num_agents=3`,
  `num_viewpoints=12`, and no-op id `12`.
- `AssignmentOnPolicyHARunner.collect()` confirms that each actor receives
  `available_actions[:, agent_id, :]` through HARL's existing policy call.

Tiny HAPPO smoke result:
- Passed with exit code 0.
- HARL-facing action spaces printed as `{0: Discrete(13), 1: Discrete(13), 2: Discrete(13)}`.
- Actor summaries printed `action_type=Discrete distribution_head=Categorical` for all three agents.
- The wrapper/facade route decoded actions, called the assignment controller, stepped the underlying scan env, logged
  assignment diagnostics, completed `episodes 1/1 total num timesteps 16/16`, and saved the final model.

Validation commands run:
- `D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python -c "import sys; print(sys.executable)"`
  - Passed; printed `C:\isaacenvs\isaac45_harl\python.exe`.
- `D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python -m py_compile source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\assignment_harl_wrapper.py`
  - Passed.
- `D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python -m py_compile source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\assignment_harl_training.py`
  - Passed.
- `D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts\reinforcement_learning\harl\train.py`
  - Passed.
- `D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python scripts\environments\test_assignment_rl_interface.py`
  - Passed; printed `[OK] assignment_rl_interface self-check passed`.
- `D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python scripts\environments\test_assignment_harl_discrete_shape.py`
  - Passed; printed `[OK] assignment HARL Discrete shape smoke passed`.
- `D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python scripts\environments\test_assignment_harl_wrapper_smoke.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --num_envs 1 --max_steps 2 --headless`
  - Passed with exit code 0.
- `D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python scripts\reinforcement_learning\harl\train.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --algorithm happo --assignment_rl --num_envs 2 --num_env_steps 16 --save_interval 1 --log_interval 1 --exp_name codex_assignment_rl_smoke --headless "agent.train.episode_length=8"`
  - Passed with exit code 0; completed 16/16 timesteps and final save.

Known runtime notes:
- Isaac/Kit printed normal non-fatal startup warnings, including OmniHub inaccessible, unsupported Intel GPU, and old-Gym
  dependency warnings from HARL's dependency chain.
- The smoke created a short assignment checkpoint under
  `./results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/codex_assignment_rl_smoke/.../models`.

Code intentionally not modified in this phase:
- No installed HARL package changes.
- No `scripts/reinforcement_learning/harl/play.py` changes.
- No scan env reward changes.
- No scan env underlying 9D action-space changes.
- No `assignment_controller.py` control-logic changes.
- No baseline solver changes.
- No duplicate sequential mask.
- No arbitrary/variable viewpoint-count support.

Not completed in this phase:
- No Phase 4 play/eval integration.
- No long training.
- No formal performance evaluation.
- No old 9D checkpoint loading in assignment mode.

Suggested next step:
- Wait for explicit Phase 4 instruction. The next narrow step should add a similarly explicit assignment mode for play/eval
  or a dedicated assignment training entry route, while keeping 9D checkpoints and assignment checkpoints separated.

## Current assignment RL Phase 3A wrapper smoke summary

This session implemented only `Assignment-based RL Phase 3A: repo-local assignment-aware wrapper/env shim smoke`.

Phase 3A goal:
- Add a repo-local assignment-aware wrapper/shim around the normal `Isaac-Scan-Mobile-Manipulator-Direct-v0` env.
- Expose HARL-facing per-agent `Discrete(num_viewpoints + 1)` action spaces while leaving the underlying scan env 9D
  action contract unchanged.
- Return real `available_actions` with shape `[num_envs, num_agents, num_viewpoints + 1]` on reset and step.
- Decode scalar discrete ids into `assignment: torch.long [num_envs, num_agents]`.
- Reuse the existing `viewpoint_assignment_to_actions()` controller through `assignment_to_env_actions()`.
- Validate only reset/step/decode/controller wiring with a short bounded headless smoke; do not run HAPPO training.

Files created:
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_wrapper.py`
- `scripts/environments/test_assignment_harl_wrapper_smoke.py`

Files modified:
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md`

Wrapper reset path:
- `make_assignment_harl_env(task, cfg=...)` constructs the normal IsaacLab scan env with `gymnasium.make(...)`.
- `AssignmentHarlWrapper.reset()` calls the underlying env reset, builds HARL-style shared observations by concatenating
  per-agent observations, and returns `obs, shared_obs, available_actions`.
- `available_actions` comes from `env.unwrapped.get_assignment_problem()["available_mask"]` plus an always-on no-op
  column via `make_assignment_action_mask()`.

Wrapper step path:
- Accepts scalar discrete action tensors in either `[num_envs, num_agents, 1]` or `[num_agents, num_envs, 1]` layout.
- Calls `AssignmentHarlAdapter.decode_actions()` / `decode_discrete_assignment()` to produce
  `assignment: torch.long [num_envs, num_agents]`.
- Calls `assignment_to_env_actions(env.unwrapped, assignment)`, which reuses the existing
  `viewpoint_assignment_to_actions()` controller and returns the unchanged 9D action dict.
- Steps the underlying scan env with the 9D dict, then returns next `obs, shared_obs, rewards, dones, info,
  available_actions`.
- Stores diagnostic tensors on the wrapper: last assignment, controller action dict, duplicate count, no-op count,
  valid-action count, and selected-available mask.

Phase 3A smoke coverage:
- Reset succeeds.
- HARL-facing action spaces are `Discrete(num_viewpoints + 1)`.
- `available_actions` is not `None`.
- `available_actions.shape == [num_envs, num_agents, num_viewpoints + 1]`.
- Manual actions use `robot_0 -> 0`, `robot_1 -> 1`, `robot_2 -> no-op`.
- No-op id `num_viewpoints` decodes to `-1`.
- Controller output is a per-agent 9D action dict with values in `[-1, 1]`.
- Underlying `env.step()` executes for two headless steps.
- Step returns a refreshed `available_actions` tensor with the same expected shape.

External package modifications:
- None. No files under `C:\isaacenvs\isaac45_harl\Lib\site-packages` were modified.

Code intentionally not modified in this phase:
- No installed HARL package changes.
- No HARL runner changes.
- No `scripts/reinforcement_learning/harl/train.py` changes.
- No `scripts/reinforcement_learning/harl/play.py` changes.
- No scan env reward changes.
- No scan env underlying 9D action-space changes.
- No `assignment_controller.py` control-logic changes.

Validation commands run:
- `D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python -c "import sys; print(sys.executable)"`
  - Passed; printed `C:\isaacenvs\isaac45_harl\python.exe`.
- `D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python -m py_compile source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\assignment_harl_wrapper.py`
  - Passed.
- `D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts\environments\test_assignment_harl_wrapper_smoke.py`
  - Passed.
- `D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python scripts\environments\test_assignment_rl_interface.py`
  - Passed; printed `[OK] assignment_rl_interface self-check passed`.
- `D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python scripts\environments\test_assignment_harl_discrete_shape.py`
  - Passed; printed `[OK] assignment HARL Discrete shape smoke passed`.
- `D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python scripts\environments\test_assignment_harl_wrapper_smoke.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --num_envs 1 --max_steps 2 --headless`
  - Passed with exit code 0. Isaac/Kit printed normal startup warnings and GPU/system information; no smoke assertion failed.

Test results:
- Phase 1 utility test still passes.
- Phase 2 Discrete shape smoke still passes.
- Phase 3A wrapper smoke confirms the repo-local reset/decode/controller/env-step path works for a bounded headless run.

Not completed in this phase:
- No Phase 3B integration with HARL `train.py` or `play.py`.
- No HAPPO training.
- No full assignment-aware runner flow.
- No duplicate sequential mask.
- No arbitrary/variable viewpoint-count support.
- No old 9D checkpoint test in assignment mode.

Suggested next step:
- Wait for explicit Phase 3B instruction. The next narrow step should be selecting this repo-local assignment wrapper from
  project-controlled HARL entry code and passing real `available_actions` into policy calls, while preserving the scan
  env's 9D controller boundary.

## Current assignment RL Phase 2 HARL Discrete shape summary

This session implemented only `Assignment-based RL Phase 2: HARL Discrete action shape support investigation and minimal
integration preparation`.

Phase 2 goal:
- Re-check HARL Discrete action support in actor, buffer, runner, wrapper, and play paths.
- Add repo-local shape/adapter helpers if useful.
- Verify HARL core can construct Categorical policy and Discrete available-action buffers without running training.
- Keep scan env reward, scan env underlying 9D action space, and `assignment_controller.py` control logic unchanged.

Report created:
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260604/ASSIGNMENT_BASED_RL_PHASE2_HARL_DISCRETE_SHAPE_REPORT.md`

Files created:
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_adapter.py`
- `scripts/environments/test_assignment_harl_discrete_shape.py`
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260604/ASSIGNMENT_BASED_RL_PHASE2_HARL_DISCRETE_SHAPE_REPORT.md`

Files modified:
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md`

HARL files and key functions checked:
- `C:\isaacenvs\isaac45_harl\Lib\site-packages\harl\envs\env_wrappers.py`
  - `IsaacLabWrapper.reset()`, `IsaacLabWrapper.step()`, `IsaacLabWrapper.action_space`,
    `ShareDummyVecEnv.reset()/step_wait()`, `ShareSubprocVecEnv.reset()/step_wait()`.
- `C:\isaacenvs\isaac45_harl\Lib\site-packages\harl\envs\isaaclab\Isaac_lab_env.py`
  - `IsaacLabEnv.__init__()`, `IsaacLabEnv.reset()`, `IsaacLabEnv.step()`.
- `C:\isaacenvs\isaac45_harl\Lib\site-packages\harl\runners\on_policy_base_runner.py`
  - `OnPolicyBaseRunner.__init__()`, `warmup()`, `collect()`, `insert()`, `eval()`, `render()`.
- `C:\isaacenvs\isaac45_harl\Lib\site-packages\harl\common\buffers\on_policy_actor_buffer.py`
  - `OnPolicyActorBuffer.__init__()`, `insert()`, actor mini-batch generators.
- `C:\isaacenvs\isaac45_harl\Lib\site-packages\harl\utils\envs_tools.py`
  - `get_shape_from_act_space()`, `make_train_env()`, `make_eval_env()`.
- `C:\isaacenvs\isaac45_harl\Lib\site-packages\harl\models\base\act.py`
  - `ACTLayer.__init__()`, `forward()`, `evaluate_actions()`.
- `C:\isaacenvs\isaac45_harl\Lib\site-packages\harl\models\base\distributions.py`
  - `Categorical.forward()`, `FixedCategorical.log_probs()`.
- `C:\isaacenvs\isaac45_harl\Lib\site-packages\harl\models\policy_models\stochastic_policy.py`
  - `StochasticPolicy.__init__()`, `forward()`.
- Project paths checked:
  - `scripts/reinforcement_learning/harl/train.py`
  - `scripts/reinforcement_learning/harl/play.py`
  - `assignment_rl_interface.py`
  - `scripts/environments/test_assignment_rl_interface.py`

Discrete action shape findings:
- HARL core supports Discrete:
  - `ACTLayer` creates `Categorical` for `gymnasium.spaces.Discrete`.
  - `Categorical.forward()` applies `available_actions == 0` masks.
  - `OnPolicyActorBuffer` allocates `available_actions` for Discrete spaces.
  - `get_shape_from_act_space(Discrete)` returns scalar action storage width `1`.
- Current installed HARL IsaacLab integration remains blocked:
  - `IsaacLabWrapper.action_space` converts all spaces to `Box(...)`, losing Discrete semantics.
  - `IsaacLabWrapper.step()` slices by `self.action_space[i].shape[0]` and forwards raw actions directly to env.
  - `Isaac_lab_env.py` hardcodes installed wrapper selection and returns `[None] * n_threads` for masks.
  - `OnPolicyBaseRunner.__init__()` computes max action width using `val.shape[0]`, which fails for standard Discrete.
  - `play.py` uses `.shape[0]` for action tensor allocation and passes `available_actions=None`.

Repo-local adapter implemented:
- `assignment_harl_adapter.py` provides:
  - `make_assignment_discrete_action_space(num_viewpoints)`
  - `make_assignment_discrete_action_spaces(num_agents, num_viewpoints, agent_ids=None)`
  - `get_harl_scalar_action_dim(action_space)`
  - `get_harl_available_action_dim(action_space)`
  - `get_max_harl_scalar_action_dim(action_spaces)`
  - `make_harl_action_tensor(num_envs, action_spaces, device=None, dtype=torch.float32)`
  - `AssignmentHarlAdapter`
- The adapter intentionally does not call `env.step()`. It is only a Phase 2 shape/mask/decode preparation helper for a
  future assignment-aware wrapper.

External package modifications:
- None. No files under `C:\isaacenvs\isaac45_harl\Lib\site-packages\harl` were modified.

Validation commands run:
- `D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python -c "import sys; print(sys.executable)"`
  - Passed; printed `C:\isaacenvs\isaac45_harl\python.exe`.
- `D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python -m py_compile source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\assignment_harl_adapter.py`
  - Passed.
- `D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts\environments\test_assignment_harl_discrete_shape.py`
  - Passed after fixing the test loader to register the file-loaded module in `sys.modules`.
- `D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python scripts\environments\test_assignment_rl_interface.py`
  - Passed; printed `[OK] assignment_rl_interface self-check passed`.
- `D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python scripts\environments\test_assignment_harl_discrete_shape.py`
  - Passed; printed `[OK] assignment HARL Discrete shape smoke passed`.

Test results:
- Phase 1 utility test still passes.
- Phase 2 smoke confirms:
  - per-agent `Discrete(num_viewpoints + 1)` action spaces can be constructed,
  - HARL scalar action dim for Discrete is `1`,
  - adapter action tensor shape is `[num_envs, num_agents, 1]`,
  - `available_actions` shape is `[num_envs, num_agents, num_viewpoints + 1]`,
  - HARL `StochasticPolicy` creates `Categorical`, not `DiagGaussian`,
  - masked Categorical sampling respects the available-action mask,
  - `OnPolicyActorBuffer` allocates scalar actions and Discrete `available_actions`,
  - current `.shape[0]` on `Discrete` is a real runner/play blocker.
- The Phase 2 smoke printed a non-fatal old-Gym dependency warning from HARL's dependency chain; exit code remained 0.

Execution note:
- Initial Phase 2 smoke failed because the file-based test loader did not insert the loaded adapter module into
  `sys.modules`, which `dataclasses.dataclass` expects. The loader was fixed and the smoke passed.
- The `.pyc` files generated by `py_compile`/test runs for the assignment utility/adapter scripts were removed after
  validation.

Not completed in this phase:
- No Phase 3 assignment-aware HARL wrapper.
- No project `train.py` or `play.py` integration change.
- No installed HARL package patch.
- No training run.
- No long simulation or GUI.
- No duplicate sequential mask.
- No arbitrary viewpoint-count support.

Suggested next step:
- Start Phase 3 only after explicit instruction: add a repo-local assignment-aware IsaacLab wrapper/env shim that exposes
  Discrete action spaces and returns real `available_actions`, then decode scalar HARL actions through
  `assignment_rl_interface.py` before passing 9D actions to the unchanged scan env.

## Current assignment RL Phase 1 utility summary

This session implemented only `ASSIGNMENT_BASED_RL_INTERFACE_DESIGN.md` Phase 1: shared assignment RL utilities.

Phase 1 goal:
- Add a small reusable tensor interface for assignment-based RL masks, discrete action decode, duplicate-count metrics,
  and a single controller entry point.
- Keep HARL runner, installed `site-packages`, `train.py`, `play.py`, scan env reward/action space, and
  `assignment_controller.py` control logic unchanged.
- Do not run training or long GUI simulation.

Files created:
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_rl_interface.py`
- `scripts/environments/test_assignment_rl_interface.py`

Files modified:
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md`

Implemented utility behavior:
- `make_assignment_action_mask(problem, include_noop=True)` uses `problem["available_mask"]`, preserves device, returns
  `torch.float32`, and appends an always-available no-op column when requested.
- `decode_discrete_assignment(...)` supports scalar discrete action layouts `[num_envs, num_agents, 1]` and
  `[num_agents, num_envs, 1]`, decodes `num_viewpoints` to `-1`, returns `torch.long` shaped
  `[num_envs, num_agents]`, and raises on invalid ids in strict mode.
- `assignment_to_env_actions(env, assignment)` directly calls the existing
  `viewpoint_assignment_to_actions(env, assignment)` controller through a lazy import.
- `compute_assignment_duplicate_count(assignment)` returns per-env duplicate counts while ignoring `-1` no-op entries.

Validation commands run:
- `D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python -c "import sys; print(sys.executable)"`
  - Passed; printed `C:\isaacenvs\isaac45_harl\python.exe`.
- `D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python -m py_compile source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\assignment_rl_interface.py`
  - Passed.
- `D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts\environments\test_assignment_rl_interface.py`
  - Passed.
- `D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python scripts\environments\test_assignment_rl_interface.py`
  - Passed; printed `[OK] assignment_rl_interface self-check passed`.
- `D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python scripts\environments\evaluate_scan_assignment.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --solver greedy --num_envs 2 --num_episodes_per_env 1 --max_steps_per_episode 20 --headless`
  - Passed with exit code 0. Isaac/Kit printed startup warnings and GPU/system information, but no regression failure.

Test coverage added:
- Mask shape is correct.
- No-op column is always 1.
- `available_mask` is preserved and concatenated correctly.
- `env_agent_action` layout decodes correctly.
- `agent_env_action` layout decodes correctly.
- No-op action id decodes to `-1`.
- Decoded assignments use `torch.long`.
- Duplicate count ignores `-1`.
- Invalid action ids raise in strict mode.

Execution note:
- Initial sandboxed conda/read attempts hit `windows sandbox: spawn setup refresh`; required validation commands were rerun
  non-sandboxed after approval.
- The `.pyc` files generated by `py_compile` for the new utility/test script were removed after validation.
- Existing unrelated worktree changes were present before this phase, including `train.py`, `play.py`, assets, and earlier
  environment scripts. This phase did not modify those files except for the new self-check script and progress note.

Not completed in this phase:
- No Phase 2 HARL IsaacLab wrapper changes.
- No HARL runner changes.
- No `train.py` or `play.py` changes.
- No scan env reward, scan env action space, or assignment controller control-logic changes.
- No assignment RL training run.

Suggested next step:
- Wait for explicit Phase 2 instruction, then integrate the utility into an assignment-aware HARL wrapper/action-mask path
  while keeping the underlying scan env action contract at 9D.

## Current assignment-based RL design task summary

This session created a technical design for changing HARL from direct 9D continuous actions to assignment-based
viewpoint-id actions while reusing the existing `viewpoint_assignment_to_actions(env, assignment)` controller.

New design document:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260604/ASSIGNMENT_BASED_RL_INTERFACE_DESIGN.md
```

Key conclusions:
- HARL core supports Discrete/Categorical policies and action masks, but the current HARL IsaacLab wrapper/runner path is
  still Box-oriented and does not support Discrete end to end without changes.
- The minimum viable route is to keep the scan env's underlying 9D action contract, expose
  `Discrete(num_viewpoints + 1)` only to HARL, decode `num_viewpoints` as no-op `-1`, and call the existing assignment
  controller before `env.step`.
- `available_actions` should be shaped `[num_envs, num_agents, num_viewpoints + 1]`, using
  `get_assignment_problem()["available_mask"]` plus an always-available no-op column.
- Static masks should include feasible, uncovered, and no-op conditions. Same-step duplicate avoidance should be deferred
  or implemented with sequential sampling, not naive post-processing that changes the action after HARL records its
  log-probability.
- Future arbitrary viewpoint counts are limited by fixed HARL actor output size, fixed replay-buffer mask shape,
  vectorized env batching, and checkpoint compatibility.

Files created in this session:
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260604/ASSIGNMENT_BASED_RL_INTERFACE_DESIGN.md`

Files modified in this session:
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md`

Python source/config/reward changes:
- None.

Commands run in this session:
- `rg --files source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead`
- `rg -n "^" source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/AGENTS.md`
- `rg -n "^" source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md`
- `rg -n "^" source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/RL_ASSIGNMENT_PIPELINE_DIAGNOSTIC_REPORT.md`
- `rg -n "^" source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260604/RL_ASSIGNMENT_PIPELINE_DIAGNOSTIC_REPORT.md`
- Several targeted `rg -n -C ...` inspections of `scan_mobile_manipulator_env.py`, `assignment_controller.py`,
  `evaluate_scan_assignment.py`, HARL `train.py`/`play.py`, HARL installed wrapper/runner/model/buffer files, and Isaac
  Lab space utilities.

Command attempts that did not complete:
- `Get-Content -Raw ...` for the requested markdown files failed before process spawn with
  `windows sandbox: spawn setup refresh`; `rg` was used instead for read-only inspection.
- `git status --short` failed before process spawn with the same Windows sandbox error.

Commands not run:
- No Python compile checks were run because no Python files were changed.
- No HARL training, play, simulation, baseline evaluator, or reward/config verification commands were run because this
  task was design-only.

Path note:
- The user requested `AgentRead/RL_ASSIGNMENT_PIPELINE_DIAGNOSTIC_REPORT.md`. In the current filesystem, that root-level
  file was not found by `rg`; the same-named report under `AgentRead/20260604/` was read and used.

Suggested next step:
- Implement Phase 1 from the design document: add a small shared assignment RL interface utility for mask creation,
  no-op decode, and assignment validation, then verify it with a lightweight syntax/import check before changing HARL
  training or play.

## Current video finalization follow-up summary

The short video smoke:

```powershell
.\isaaclab.bat -p scripts\reinforcement_learning\harl\train.py --video --video_length 32 --video_interval 1 --num_envs 1 --task "Isaac-Scan-Mobile-Manipulator-Direct-v0" --seed 1 --save_interval 1 --log_interval 1 --exp_name "video_smoke" --num_env_steps 32 --algorithm happo --headless "agent.train.episode_length=32"
```

produced 31 zero-second videos and ended with:

```text
TypeError: OnPolicyBaseRunner.save() missing 1 required positional argument: 'directory'
```

Root cause:
- `--video_interval 1` makes Gymnasium `RecordVideo` start a new recording every environment step. Its
  `start_recording()` method stops any active recording first, so each file only receives about one frame.
- `scripts/reinforcement_learning/harl/train.py` called `runner.save()` without the required on-policy `directory`
  argument, causing an exception before normal shutdown.
- HARL's installed IsaacLabEnv `close()` does not call down into the hidden Gymnasium `RecordVideo` wrapper, so an
  active final recording can remain un-finalized unless the wrapper stops during training.

Implemented changes:
- `train.py` now calls `runner.save(save_dir)` for the final save.
- `train.py` now uses `try/finally` so `runner.close()` is reached after training/save.
- `train.py` now walks the nested HARL/Gym wrapper chain and calls `stop_recording()` on any active RecordVideo wrapper
  before runner shutdown.
- README now recommends a video smoke with `--video_interval 64` instead of `1`, producing one short video.

## Files changed in current video finalization follow-up

- `scripts/reinforcement_learning/harl/train.py`
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/README.md`
- `TASK_PROGRESS.md`

## Verification commands run in current video finalization follow-up

- `D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts\reinforcement_learning\harl\train.py`
- `D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python scripts\reinforcement_learning\harl\train.py --video --video_length 16 --video_interval 64 --num_envs 1 --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --seed 1 --save_interval 1 --log_interval 1 --exp_name codex_video_smoke --num_env_steps 32 --algorithm happo --headless "agent.train.episode_length=32"`
- `D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python -c "from moviepy.video.io.VideoFileClip import VideoFileClip; ..."`
- `D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python scripts\reinforcement_learning\harl\train.py --video --video_length 32 --video_interval 64 --num_envs 1 --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --seed 1 --save_interval 1 --log_interval 1 --exp_name codex_video_finalize --num_env_steps 32 --algorithm happo --headless "agent.train.episode_length=32"`
- `D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python -c "from moviepy.video.io.VideoFileClip import VideoFileClip; ..."`

## Test results in current video finalization follow-up

- Passed `py_compile` for `scripts/reinforcement_learning/harl/train.py`.
- The `codex_video_smoke` command exited with code 0, saved the final HARL model, and generated
  `videos/train/rl-video-step-0.mp4` with duration `0.57` seconds at `30` fps.
- The `codex_video_finalize` command exited with code 0, saved the final HARL model, and generated
  `videos/train/rl-video-step-0.mp4` with duration `1.07` seconds at `30` fps and about `32` frames.

## Known issues in current video finalization follow-up

- A direct non-conda `.\isaaclab.bat` smoke from Codex's shell selected `C:\Users\33506\AppData\Local\Microsoft\WindowsApps\python.exe`, so Codex verification used the project-required `conda run -p C:\isaacenvs\isaac45_harl python ...` form.
- Isaac/Kit emitted the usual non-fatal startup warnings during video smoke tests.
- A MoviePy duration check initially failed because conda could not encode a non-ASCII approximation symbol in GBK
  output; the ASCII-only retry passed.

## Unfinished tasks from current video finalization follow-up

- No unfinished work remains for HARL training video finalization.

## Suggested next step

Use `--video_interval` larger than `--video_length` for video smoke tests. For long training, use a large interval such
as `50000` and inspect later interval videos rather than setting the interval to `1`.

## Current video follow-up summary

The HARL training command with `--headless --video` produced a static-looking recording:

```powershell
.\isaaclab.bat -p scripts\reinforcement_learning\harl\train.py --video --video_length 500 --video_interval 50000 --num_envs 4 --task "Isaac-Scan-Mobile-Manipulator-Direct-v0" --seed 1 --save_interval 500 --log_interval 1 --exp_name "scan_happo" --num_env_steps 10000000 --algorithm happo --headless
```

Root cause:
- The scan environment is still a high-level task-space skeleton. It updates tensor buffers such as `base_pos` and
  `scanner_pos`, not real PhysX robot articulations.
- The visible robots are USD debug markers. `_update_usd_debug_visuals()` only ran when `self.sim.has_gui()` was true,
  so camera-enabled headless video did not mirror the high-level tensor state into the USD markers.
- The first training video is also recorded at environment step 0 because HARL's installed IsaacLab wrapper uses
  `step_trigger=lambda step: step % video_interval == 0`. That first recording is early/untrained behavior.

Implemented changes:
- `scan_mobile_manipulator_env.py` now updates USD debug markers when GUI is active or when the simulation render mode
  supports camera/offscreen rendering, so `--headless --video` recordings can show high-level marker movement.
- README now documents that camera-enabled headless video syncs debug markers, while pure headless training skips marker
  sync for overhead.
- README now documents that the first `--video` training recording happens at step 0 and later recordings are controlled
  by `--video_interval`.

## Files changed in current video follow-up

- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py`
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/README.md`
- `TASK_PROGRESS.md`

## Verification commands run in current video follow-up

- `D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python -c "import sys; print(sys.executable)"`
- `D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python -m py_compile source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\scan_mobile_manipulator_env.py`
- `D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts\reinforcement_learning\harl\train.py`

## Test results in current video follow-up

- Passed interpreter check; executable was `C:\isaacenvs\isaac45_harl\python.exe`.
- Passed `py_compile` for `scan_mobile_manipulator_env.py`.
- Passed `py_compile` for `scripts\reinforcement_learning\harl\train.py`.

## Known issues in current video follow-up

- No short video smoke was run, because validating actual pixels would require launching Isaac/Kit with camera rendering.
- The recorded objects are still debug markers, not real robot articulation motion. Real robot motion still requires
  replacing the high-level tensor skeleton with articulation/IK/base control.

## Unfinished tasks from current video follow-up

- Optional: run a very short `--headless --video --video_length 32` HARL smoke and visually inspect the generated mp4.
- Optional: add video support to `scripts/reinforcement_learning/harl/play.py` for cleaner trained-policy recording.

## Suggested next step

Re-run the training command and inspect a video after the initial step-0 recording, or run a short video smoke first with
small `--video_length` and `--num_env_steps`.

## Task phases

### Phase 1: Add assignment problem interface

Goal:
- Add `get_assignment_problem()` to `ScanMobileManipulatorEnv`.

Expected files:
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py`

Status:
- Complete

Verification:
- Passed interpreter check.
- Passed `py_compile` for `scan_mobile_manipulator_env.py`.
- Passed headless shape/device smoke test with `num_envs=2`.

Notes:
- Added `get_assignment_problem()` only; existing 9D continuous action path was not changed.
- Returned assignment tensors stay on `env.device`.

---

### Phase 2: Add viewpoint assignment controller

Goal:
- Add `assignment_controller.py`.
- Implement `viewpoint_assignment_to_actions(env, assignment)`.

Expected files:
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_controller.py`

Status:
- Complete

Verification:
- Passed interpreter check.
- Passed `py_compile` for `assignment_controller.py`.
- Passed headless shape/device smoke test with `num_envs=2`.

Notes:
- Invalid, covered, infeasible, or out-of-range assignments should produce zero actions.
- Added `viewpoint_assignment_to_actions(env, assignment)` only; no solver code was started.
- Returned action tensors match the existing DirectMARLEnv action dict format and stay on `env.device`.

---

### Phase 3: Add baseline solvers

Goal:
- Add random, nearest, and greedy assignment solvers.

Expected files:
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/solvers/__init__.py`
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/solvers/base_solver.py`
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/solvers/random_solver.py`
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/solvers/nearest_solver.py`
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/solvers/greedy_solver.py`

Status:
- Complete

Verification:
- Passed interpreter check.
- Passed Phase 2 `py_compile` and headless controller smoke check before starting Phase 3.
- Passed `py_compile` for all solver files.
- Passed headless shape/device smoke test with `num_envs=2`.

Notes:
- Keep all tensor operations on the same device.
- Added random, nearest, and greedy solvers only; no evaluation script was started.
- Solvers return `torch.long` assignments on the same device as `available_mask`.
- Solvers avoid duplicate viewpoint assignment within each environment when possible.

---

### Phase 4: Add headless evaluation script

Goal:
- Add `evaluate_scan_assignment.py`.

Expected files:
- `scripts/environments/evaluate_scan_assignment.py`

Status:
- Complete

Verification:
- Passed interpreter check.
- Passed Phase 3 `py_compile` and headless solver smoke check before starting Phase 4.
- Passed `py_compile` for `evaluate_scan_assignment.py`.
- Passed headless shape/device evaluation smoke test with `num_envs=2`, `num_episodes=2`, and `max_steps_per_episode=1`.

Notes:
- Should support random, nearest, and greedy solvers.
- Should support CSV output.
- Added headless evaluation script only; no GUI viewer was started.
- The script validates assignment/action shapes, dtypes, devices, ranges, and available-mask consistency during evaluation.
- The script supports summary metrics and optional per-episode CSV output.

---

### Phase 5: Add GUI viewer

Goal:
- Add `view_scan_assignment.py`.

Expected files:
- `scripts/environments/view_scan_assignment.py`

Status:
- Complete

Verification:
- Passed interpreter check.
- Passed Phase 4 `py_compile` and headless evaluation smoke check before starting Phase 5.
- Passed `py_compile` for `view_scan_assignment.py`.
- Passed headless viewer shape/device smoke test with `num_envs=1` and `max_steps=2`.

Notes:
- Should not break existing viewer scripts.
- Added a standalone viewer script only; no further phase was started.
- The viewer supports random, nearest, and greedy solvers.
- The viewer validates assignment/action shapes, dtypes, devices, and action ranges before stepping.
- The viewer prints `step`, `coverage_ratio`, and `assignment` at a configurable interval.

---

## Latest session summary

The baseline evaluator in `scripts/environments/evaluate_scan_assignment.py` was refined for clearer vectorized-episode
semantics and more useful baseline comparison metrics.

Implemented changes:
- Added `--num_episodes_per_env` and kept deprecated `--num_episodes` as total-record compatibility mode.
- Split duplicate metrics into `assignment_duplicate_count` and `scan_duplicate_count`.
- Added `steps_to_50_coverage`, `steps_to_80_coverage`, and normalized `coverage_auc`.
- Added optional action metrics `mean_action_norm` and `mean_action_delta`.
- Renamed per-robot CSV fields to `robot_i_coverage_gain`.
- Added Python, NumPy, and PyTorch seed setup.
- Made done tensor conversion robust to scalar bools, lists, and tensors.
- Added `scripts/environments/env_readme.md` with usage, metric, CSV, and verification notes.

## Files changed in latest session

- `scripts/environments/evaluate_scan_assignment.py`
- `scripts/environments/env_readme.md`
- `TASK_PROGRESS.md`

## Verification commands run in latest session

- `D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python -c "import sys; print(sys.executable)"`
- `D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts\environments\evaluate_scan_assignment.py`
- `D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python scripts\environments\evaluate_scan_assignment.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --solver random --num_envs 2 --num_episodes_per_env 1 --max_steps_per_episode 50 --headless`
- `D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python scripts\environments\evaluate_scan_assignment.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --solver nearest --num_envs 2 --num_episodes_per_env 1 --max_steps_per_episode 50 --headless`
- `D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python scripts\environments\evaluate_scan_assignment.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --solver greedy --num_envs 2 --num_episodes_per_env 1 --max_steps_per_episode 50 --headless`
- `D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python scripts\environments\evaluate_scan_assignment.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --solver greedy --num_envs 2 --num_episodes_per_env 1 --max_steps_per_episode 50 --save_csv logs/scan_assignment/greedy_eval.csv --headless`
- `Get-Content logs\scan_assignment\greedy_eval.csv -TotalCount 5`
- `(Import-Csv logs\scan_assignment\greedy_eval.csv).Count`

## Test results in latest session

- Passed interpreter check; executable was `C:\isaacenvs\isaac45_harl\python.exe`.
- Passed `py_compile` for `scripts/environments/evaluate_scan_assignment.py`.
- Passed random, nearest, and greedy headless smoke checks with exit code 0.
- Passed CSV output check. The generated file contained 2 records for `--num_envs 2 --num_episodes_per_env 1` and the
  new fields `assignment_duplicate_count`, `scan_duplicate_count`, `steps_to_50_coverage`,
  `steps_to_80_coverage`, `coverage_auc`, `mean_action_norm`, `mean_action_delta`, and
  `robot_i_coverage_gain`.

## Known issues from latest session

- Isaac Lab emitted non-fatal startup/shutdown warnings during the smoke tests, including OmniHub inaccessible,
  unsupported Intel GPU, and inability to save `user.config.json` while another Kit process held the lock. All smoke
  checks exited with code 0.
- The command-capture output mostly showed Isaac/Kit stderr warnings; the CSV check was used to verify the evaluator
  records and field names directly.

## Unfinished tasks

- No unfinished work remains for the requested evaluator refinement.

## Suggested next step

Use the CSV command in `scripts/environments/env_readme.md` to generate per-solver tables for longer baseline
comparisons, increasing `--num_episodes_per_env` as needed.

## Current follow-up summary

The HAPPO training command was reported to finish without an obvious saved model/result file:

```powershell
.\isaaclab.bat -p scripts\reinforcement_learning\harl\train.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --algorithm happo --num_envs 2 --num_env_steps 100000 --save_interval 1 --log_interval 1 --headless
```

To make saving explicit and discoverable, `scripts/reinforcement_learning/harl/train.py` now:
- Prints `runner.run_dir` and `runner.save_dir` immediately after runner creation, when those attributes exist.
- Calls `runner.save()` after `runner.run()` completes, before `runner.close()`.
- Prints the final saved model directory after the explicit final save.

`README.md` now documents the printed save-path messages in the HARL smoke section.

## Files changed in current follow-up

- `scripts/reinforcement_learning/harl/train.py`
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/README.md`
- `TASK_PROGRESS.md`

## Verification commands attempted in current follow-up

- `D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts\reinforcement_learning\harl\train.py`

## Verification result in current follow-up

- The verification command could not be executed because the shell tool failed before spawning the process with
  `windows sandbox: spawn setup refresh`.

## Suggested verification for next run

```powershell
D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts\reinforcement_learning\harl\train.py
.\isaaclab.bat -p scripts\reinforcement_learning\harl\train.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --algorithm happo --num_envs 2 --num_env_steps 16 --save_interval 1 --log_interval 1 --headless "agent.train.episode_length=8"
```

---

## Previous session summary

The HARL/HAPPO training path was debugged after the default GPU command failed with
`CUBLAS_STATUS_NOT_INITIALIZED` during the first policy MLP forward pass.

Two fixes were added:
- `scan_mobile_manipulator_env.py` now publishes top-level `info["log"]` metrics through `self.extras["log"]`, which is
  required by `harl.envs.isaaclab.IsaacLabEnv.step()`.
- `scripts/reinforcement_learning/harl/train.py` now performs a tiny PyTorch CUDA Linear warm-up before launching Isaac
  Kit/AppLauncher. This initializes cuBLAS before Kit takes over the CUDA context and prevents the first HARL policy
  forward pass from failing.

The README HARL smoke section was updated to document the 512-step default smoke, the 16-step minimal smoke with
`"agent.train.episode_length=8"`, and the CUDA warm-up behavior.

All five planned assignment phases remain complete. No Phase 6 is defined or started.

## Files changed in last session

- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/README.md`
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py`
- `scripts/reinforcement_learning/harl/train.py`
- `TASK_PROGRESS.md`

## Verification commands run in last session

- `D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python -c "import sys; print(sys.executable)"`
- `D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python -m py_compile source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\scan_mobile_manipulator_env.py`
- `D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts\reinforcement_learning\harl\train.py`
- `nvidia-smi`
- `D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python scripts\reinforcement_learning\harl\train.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --algorithm happo --num_envs 2 --num_env_steps 16 --save_interval 1 --log_interval 1 --exp_name codex_smoke --headless "agent.train.episode_length=8" "agent.logger.log_dir=C:/Users/33506/AppData/Local/Temp/harl_smoke"`

## Test results

- Passed interpreter check; executable was `C:\isaacenvs\isaac45_harl\python.exe`.
- Passed `py_compile` for `scan_mobile_manipulator_env.py`.
- Passed `py_compile` for `scripts/reinforcement_learning/harl/train.py`.
- `nvidia-smi` showed no residual Isaac/Kit/Python GPU process before the final smoke check.
- Passed the minimal HAPPO GPU smoke test. The run completed `episodes 1/1 total num timesteps 16/16`, printed
  `coverage_ratio`, `new_viewpoints`, `duplicate_scans`, `reach_violation`, and `mean_reward`, and exited with code 0.

## Known issues

- Isaac Lab emitted non-fatal startup/shutdown warnings during the smoke test, including OmniHub inaccessible, unsupported Intel GPU, and inability to save `user.config.json` while another Kit process held the lock. The smoke test still passed.
- Importing `isaaclab_tasks` directly outside Isaac's AppLauncher can fail on `omni.kit`; use AppLauncher/Isaac Lab script entry points for runtime imports.
- For env-internal terminations, DirectMARLEnv resets completed envs before returning from `step()`. The evaluation script preserves success and reward from returned tensors, and tracks coverage conservatively using running max coverage.
- The viewer was smoke-tested in headless mode for shape/device correctness. The new camera-light branch only runs in GUI mode, so manual GUI visual confirmation is still recommended.
- The mobile-base assignment feasibility is intentionally broader than the original static arm-reach check. It is now suitable for assigning targets that require base motion.
- `agent.device.cuda=False` is not currently a safe workaround by itself for this HARL Isaac wrapper: the environment
  tensors remain on CUDA, while HARL actor/critic buffers move to CPU, causing a CPU/CUDA tensor mismatch during return
  computation. Use the default GPU policy path with the new CUDA warm-up instead.
- The 512-step default HAPPO smoke was not re-run after the warm-up patch because the 16-step smoke exercises the same
  HARL collect/compute/log path with much less runtime.

## Next recommended step

All planned phases in this task are complete.

Suggested HAPPO smoke/training command:

```powershell
.\isaaclab.bat -p scripts\reinforcement_learning\harl\train.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --algorithm happo --num_envs 2 --num_env_steps 512 --save_interval 1 --log_interval 1 --headless
```

Suggested manual GUI check, if visual confirmation is desired:

```powershell
D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python scripts/environments/view_scan_assignment.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --solver greedy --num_envs 1 --step_rate 2
```
