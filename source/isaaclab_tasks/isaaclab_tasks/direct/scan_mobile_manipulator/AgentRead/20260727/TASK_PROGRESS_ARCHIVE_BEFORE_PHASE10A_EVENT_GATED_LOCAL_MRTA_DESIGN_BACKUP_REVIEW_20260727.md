# TASK_PROGRESS

## Current status

Phase 10A event-gated local MRTA 与现有 HAPPO/HARL 训练接口兼容性审计已完成。

```text
audit classification:
  RUNNER-CHANGES-REQUIRED

repository baseline:
  e3febe417c5323e28ceb9e256ba71dcd44f3c457

runtime behavior changed:
  no

training/playback/evaluation launched:
  no

commit:
  none
```

Phase 9G-8 已由当前 HEAD 的文档 commit 关闭，本审计没有重开其训练或评估结论。

## Latest completed phase

完成了 environment、assignment wrapper、lifecycle resolver、observation/action
mask、reward、repo-local training facade、installed HARL runner/HAPPO/buffer/critic、
GAE、ValueNorm、checkpoint、config、logger 和 playback 的静态调用链审计。

核心结论：

- 当前 base reward 是 shared + individual 组合；wrapper 输出 `[E,M,1]`，
  但 EP critic 实际只写入 `rewards[:,0]`。
- 当前每个物理 step 对所有 actor、所有 rollout thread 采样 action/log-prob。
- PPO actor buffer 当前保存 proposal，effective assignment 没有覆盖 proposal；
  controller 只消费 effective。
- global fixed-width observation、global task ID、historical action-mask replay、
  固定物理 step GAE 和 centralized critic 骨架可复用。
- `decision_valid_mask` 必须进入 repo-local actor buffer、runner collect/insert、
  HAPPO loss/entropy/advantage normalization 和 sequential factor。
- 非决策 HAPPO ratio 必须为 1；只在最终 policy loss 外乘 mask 不足。
- zero-valid actor 必须跳过 optimizer；single-valid advantage 需要 finite fallback。
- 当前 DirectMARLEnv 在 wrapper 读取 post-step problem 前自动 reset done env，
  所以 terminal facts 需要 pre-reset hook。
- 当前 resolver 只有 continue/idle claim/conflict，禁止 switch；没有 local-set、
  Top-K、preemption 或 staged atomic transfer component。
- 最终分类不是 architectural blocker，而是明确且可控的 runner/trainer/buffer
  与 lifecycle/resolver 改造。

## Active architecture / implementation path

推荐路径：

1. Phase A：default-off profile/config、typed event/cost/local-set/component
   contract、checkpoint identity 和 diagnostics，不改变行为。
2. Phase B0：pre-reset facts、terminal pair failure、release、
   `NEEDS_ASSIGNMENT`、availability 和 TEAM_INFEASIBLE state transition。
3. Phase B：event-gated local Top-K/mask、DVM sidecar、atomic component resolver；
   只做 deterministic smoke。
4. Phase C：repo-local buffer/runner/HAPPO valid-only update 与 factor identity。
5. Phase D：explicit team reward、component rejection penalty、termination reason。
6. Phase E：完成全部 gate 后才设计并执行训练/消融。

不得直接修改 installed
`C:\isaacenvs\isaac45_harl\Lib\site-packages\harl`；使用 repo-local
subclass/shim/registry。

## Changed files

Documentation only:

- Added
  `AgentRead/20260724/PHASE10A_EVENT_GATED_LOCAL_MRTA_HAPPO_INTERFACE_AUDIT.md`
- Added
  `AgentRead/20260724/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE10A_EVENT_GATED_LOCAL_MRTA_HAPPO_INTERFACE_AUDIT_20260724.md`
- Updated `AgentRead/TASK_PROGRESS.md`

No source, test, YAML/data, result, checkpoint, installed HARL, Conda environment,
training, simulation, controller, reward, buffer, trainer or runner behavior changed.

## Latest verification

Read-only/static checks:

```text
git rev-parse HEAD
git log -3 --oneline
git status --short --untracked-files=all
git diff --name-status
git diff --check

D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl \
  python -c "import sys; print(sys.executable)"

D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl \
  python -c "import harl; print(harl.__file__)"
```

Interpreter and HARL import paths matched `C:\isaacenvs\isaac45_harl`.
Pure tensor-level inspection confirmed unique-action sampling still occurs,
zero-mask reductions are unsafe, and current unbiased nan-std is NaN for one
valid sample.

No AppLauncher, Isaac Sim, environment construction, training, playback,
evaluation or checkpoint load was run.

## Known issues / blockers

- EP team reward contract is not explicit; current learner uses robot 0 reward.
- Terminal pre-reset facts need an authoritative environment hook.
- Real navigation/alignment estimated-time sources are not present.
- Scenario YAML lifecycle profile is parsed but not propagated by the current
  `apply_scenario_config_to_env_cfg` path.
- Assignment facade returns empty infos, so proper-time-limit `bad_masks` are
  effectively always 1.
- Checkpoint v2 does not fingerprint event/DVM/component/factor/reward semantics.

These are implementation prerequisites, not architectural blockers.

## Do not do

- Do not start training, playback or formal evaluation from this audit alone.
- Do not modify or load old checkpoints under a new event-gated semantic profile.
- Do not edit installed HARL; add repo-local subclasses/shims.
- Do not use `active_masks` as `decision_valid_mask`.
- Do not write effective assignment into PPO action storage.
- Do not put all failure/TEAM_INFEASIBLE state work after local-set Phase B.
- Do not commit unless the user explicitly requests it.

## Next step

After user/GPT review, implement **Phase A only**:

- freeze one high-level default-off profile;
- freeze explicit EP team reward reducer/broadcast semantics;
- define typed event/fact/cost/local-set/DVM/component interfaces;
- add versioned checkpoint semantic fields with v2 backward parsing;
- add structured correctness diagnostics;
- prove feature-off identity before Phase B0.

A broad method redesign is not needed. Before implementation, only a narrow
interface decision is recommended for team reward reduction, singleton advantage
normalization, and the terminal pre-reset fact hook.

## Detailed reports / archives

- `AgentRead/20260724/PHASE10A_EVENT_GATED_LOCAL_MRTA_HAPPO_INTERFACE_AUDIT.md`
- `AgentRead/20260724/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE10A_EVENT_GATED_LOCAL_MRTA_HAPPO_INTERFACE_AUDIT_20260724.md`
- `AgentRead/20260722/PHASE9G8I320_MULTI_CONDITION_BEST_FINAL_EVIDENCE_SYNTHESIS_AND_COMMIT_READINESS_REVIEW.md`
- `AgentRead/20260722/PHASE9G8I31_PAIRED_BEST_FINAL_MULTI_CONDITION_ROBUSTNESS_COMPARISON_EXECUTION.md`
- `AgentRead/20260722/PHASE9G8I310_PAIRED_BEST_FINAL_MULTI_CONDITION_ROBUSTNESS_COMPARISON_DESIGN.md`
