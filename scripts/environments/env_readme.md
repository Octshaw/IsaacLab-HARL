# scripts/environments baseline evaluation notes

This directory contains lightweight environment scripts for the scan mobile manipulator task. The main baseline
comparison entry point is:

```powershell
D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python scripts\environments\evaluate_scan_assignment.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --solver greedy --num_envs 2 --num_episodes_per_env 1 --max_steps_per_episode 50 --headless
```

## Scope

`evaluate_scan_assignment.py` evaluates only the high-level assignment baselines:

- `random`
- `nearest`
- `greedy`

It does not load RL checkpoints, HARL policies, or HAPPO training code. Each step follows the assignment path:

```python
problem = env.unwrapped.get_assignment_problem()
assignment = solver.solve(problem)
actions = viewpoint_assignment_to_actions(env.unwrapped, assignment)
obs, rewards, terminated, truncated, info = env.step(actions)
```

## Episode Count Semantics

Use `--num_episodes_per_env` for new experiments. In a vectorized environment, the target number of episode records is:

```text
target_episode_records = num_envs * num_episodes_per_env
```

The old `--num_episodes` option is kept only for compatibility and means total episode records, not episodes per
parallel environment. Prefer `--num_episodes_per_env` in scripts and experiment tables.

## Metrics

The evaluator writes per-episode records and prints a summary. The CSV fields include:

- `assignment_duplicate_count`: duplicate viewpoint choices inside one assignment step.
- `scan_duplicate_count`: actual repeated scans of already covered viewpoints reported by the environment.
- `steps_to_50_coverage`: first step reaching coverage ratio >= 0.5, or `-1` if not reached.
- `steps_to_80_coverage`: first step reaching coverage ratio >= 0.8, or `-1` if not reached.
- `coverage_auc`: mean coverage ratio over the episode.
- `mean_action_norm`: mean per-agent action L2 norm.
- `mean_action_delta`: mean per-agent action change after the first step.
- `robot_i_coverage_gain`: cumulative coverage gain attributed to robot `i`.

The summary keeps threshold reach rates separate from reached-only step means so missing thresholds are not averaged as
ordinary `-1` step values.

## CSV Example

```powershell
D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python scripts\environments\evaluate_scan_assignment.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --solver greedy --num_envs 2 --num_episodes_per_env 1 --max_steps_per_episode 50 --save_csv logs\scan_assignment\greedy_eval.csv --headless
```

The script creates parent directories for `--save_csv` automatically.

## Verification

Use small headless checks for this evaluator. Avoid full training or long simulation runs unless explicitly needed.

```powershell
D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts\environments\evaluate_scan_assignment.py
```

Then run one short smoke test per solver with `--num_envs 2 --num_episodes_per_env 1 --max_steps_per_episode 50
--headless`.
