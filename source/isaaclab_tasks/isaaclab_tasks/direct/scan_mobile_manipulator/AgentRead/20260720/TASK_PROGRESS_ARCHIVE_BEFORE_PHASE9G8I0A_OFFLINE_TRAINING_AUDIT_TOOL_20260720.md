# TASK_PROGRESS

## Current Status

Phase 9G-8I-0 completed the documentation-only design and static preflight for one fresh 100k-configured-step `lifecycle_contract_c` training run.

Classification: `CONTROLLED-TRAINING-READY`.

The Phase 9G-8H attribution implementation and evidence are committed at baseline `7875612117fbf617aa5f740ebca6dfbd0280485b` (`feat(assignment): add validated playback attribution diagnostics`). The pre-design worktree was clean.

## Frozen Manual Experiment

```text
HAPPO / EP / feed-forward / share_param=false
fresh start; no --dir or checkpoint load
num_envs=1
M=3, N=50
episode_length=300
num_env_steps=100000
save_interval=20 rollouts
log_interval=1 rollout
seed=1
```

Installed HARL will execute 333 complete rollouts, collect 99,900 environment transitions and 299,700 robot decisions, and run 333 update cycles. The 100-transition remainder is not collected because the runner floors to complete rollouts.

The unique experiment parent was absent during preflight. The exact foreground PowerShell command, checkpoint-v2 expectations, 63-tag TensorBoard inventory, trend-review plan, and later best/final attribution comparison are frozen in the Phase 9G-8I-0 report.

## Boundaries

This experiment changes only the configured duration and approved save/log cadence. It does not change resolver behavior, Contract C, observations, masks, rewards, controller/environment behavior, policy architecture, YAML defaults, or checkpoint behavior.

No source, test, YAML, training, playback, checkpoint load, AppLauncher, Isaac Sim, evaluation, GUI, environment construction, or commit occurred in Phase 9G-8I-0.

No automatic retry or 300k extension is authorized. Checkpoint and TensorBoard review must precede any separately authorized best/final attribution playback.

## Next Step

After review, the next possible phase is:

```text
Phase 9G-8I-1:
User-Executed Fresh 100k Controlled Training
```

The user runs the frozen command manually from the repository root in a foreground PowerShell process with no short external timeout. Codex must not launch the long run.

## Detailed Report / Archive

- `AgentRead/20260720/PHASE9G8I0_POLICY_NOOP_LOAD_IMBALANCE_CONTROLLED_TRAINING_DESIGN_AND_PREFLIGHT.md`
- `AgentRead/20260720/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G8I0_CONTROLLED_TRAINING_DESIGN_20260720.md`
