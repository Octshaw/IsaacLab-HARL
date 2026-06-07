# TASK_PROGRESS

This file tracks implementation progress for the high-level viewpoint assignment path.

## Current status

Status: Assignment-based RL interface design complete

Current phase: Design only; no Python source, training config, environment config, or reward changes made

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
