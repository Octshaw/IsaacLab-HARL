# TASK_PROGRESS

## Current status

Phase 10A Authoritative V2.1 targeted 文档修订已完成。

```text
V2.1 targeted revision:
  complete

classification:
  TARGETED-REVISION-COMPLETE-AWAITING-USER-APPROVAL

document status:
  AUTHORITATIVE-DESIGN-CANDIDATE-V2.1

original findings:
  DR-01–DR-21 remain resolved

targeted residual findings:
  TR-01–TR-03 resolved

unresolved CRITICAL/HIGH:
  0

V2 and original 20260724 memo:
  unchanged
  superseded for design recovery

enter Phase A:
  no -- wait for explicit user approval

runtime behavior changed:
  no

training/playback/evaluation/checkpoint load:
  none

commit:
  none
```

V2.1 只修正三个 residual contracts：

- raw `ExecutionTransitionFacts` 与 derived `LifecycleTransitionResult` 分层；
- event-gated default-off 按 resolved pre-event-gated profile 精确分派；
- `RESOLVER_COMMIT_DIAGNOSTIC` 不自触发下一 assignment tick。

原始 20260724 memo 与 V2 均未修改。V2.1 无需再次 broad review，但在用户确认前仍不是
实现授权。`[NUMERIC-TBD]` 与 `[IMPLEMENTATION-EVIDENCE-TBD]` 继续是受控后续工作，
不是 unresolved review finding。

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

创建了 Phase 10A 之后、Phase A 之前的 V2.1 authoritative design candidate：

- 继承 DR-01～DR-21 的 21/21 resolved 状态；
- TR-01～TR-03 targeted residual findings 3/3 resolved；
- 将 raw execution facts 与 lifecycle-derived result 拆成两个权威对象；
- default-off 保留 resolved legacy、Contract C 或其他既有 profile 的精确路径；
- resolver commit event 仅为 diagnostic，不独立进入 trigger set；
- candidate 尚需用户显式批准。

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
- 当前 DirectMARLEnv 在 wrapper 读取 post-step problem 前自动 reset done env；Phase B0
  需要 pre-reset `ExecutionTransitionFacts` hook 和唯一 lifecycle authority/result。
- 当前 resolver 只有 continue/idle claim/conflict，禁止 switch；没有 local-set、
  Top-K、preemption 或 staged atomic transfer component。
- 最终分类不是 architectural blocker，而是明确且可控的 runner/trainer/buffer
  与 lifecycle/resolver 改造。

## Active architecture / implementation path

推荐路径：

1. Phase A：resolved-profile dispatcher、两个 transition object schema、typed
   event/cost/local-set/component contract、checkpoint identity 和 diagnostics，
   不改变行为。
2. Phase B0：pre-reset raw-facts hook、lifecycle authority/result、terminal pair
   failure、release、`NEEDS_ASSIGNMENT`、availability、`TEAM_INFEASIBLE` 和
   termination reason。
3. Phase B：trigger-source filtering、event-gated local Top-K/mask、DVM sidecar、
   atomic component resolver；只做 deterministic smoke。
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
- Added
  `AgentRead/20260724/PHASE10A_EVENT_GATED_LOCAL_MRTA_DESIGN_BACKUP_REVIEW.md`
- Added
  `AgentRead/20260727/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE10A_EVENT_GATED_LOCAL_MRTA_DESIGN_BACKUP_REVIEW_20260727.md`
- Added
  `AgentRead/20260727/Lifecycle_Aware_Event_Gated_Local_MRTA_Design_Authoritative_V2_20260727.md`
- Added
  `AgentRead/20260727/PHASE10A_AUTHORITATIVE_V2_REVISION_SUMMARY.md`
- Added
  `AgentRead/20260727/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE10A_AUTHORITATIVE_V2_REVISION_20260727.md`
- Added
  `AgentRead/20260727/Lifecycle_Aware_Event_Gated_Local_MRTA_Design_Authoritative_V2_1_20260727.md`
- Added
  `AgentRead/20260727/PHASE10A_AUTHORITATIVE_V2_1_TARGETED_REVISION_SUMMARY.md`
- Added
  `AgentRead/20260727/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE10A_AUTHORITATIVE_V2_1_TARGETED_REVISION_20260727.md`
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
git diff --cached --name-status

D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl \
  python -c "import sys; print(sys.executable)"

D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl \
  python -c "import harl; print(harl.__file__)"
```

2026-07-27 V2 revision closeout：

- V2 和 revision summary 的 finding matrix 均为 21/21 `RESOLVED`，
  无 unresolved CRITICAL/HIGH documentation finding；
- V2、summary 和 TASK_PROGRESS 的相对 Markdown links 均可解析；
- 原始 memo SHA256 仍为
  `A9DD70253EC78575C14394B4F566505A5C85F0BFD0440D76E2F44403E55A42FC`；
- HEAD 仍为 `e3febe417c5323e28ceb9e256ba71dcd44f3c457`；
- `git diff --check` exit 0，`git diff --cached --name-status` 为空；
- worktree 中没有 AgentRead 外的本轮修改。

2026-07-27 V2.1 targeted revision closeout：

- V2.1 与 targeted summary 的 TR matrix 均为 3/3 `RESOLVED`；
- V2.1 的 DR-01～DR-21 rows 与 V2 逐行一致，仍为 21/21 `RESOLVED`；
- V2.1、targeted summary 和 TASK_PROGRESS 的相对 Markdown links 均可解析；
- backup、V2 和原 V2 summary SHA256 分别保持
  `A9DD70253EC78575C14394B4F566505A5C85F0BFD0440D76E2F44403E55A42FC`、
  `39F6C9F4857135E790DC897A2820FD83AA03CBA1CEAF93FC6824F7326899D517` 和
  `E55DDDE44B4D1CFA8FA1B84FA09606F209BDA048286CB7314CDA14530BE9D517`；
- V2.1 前 TASK_PROGRESS archive SHA256 为
  `26EA9180AE7EF3FF531A2E0C679D108A9343A16BC2FEC372C7073A1038B61827`；
- HEAD 未变，`git diff --check` exit 0，staged files 为空；
- worktree 没有 AgentRead 外的变化。

Interpreter and HARL import paths matched `C:\isaacenvs\isaac45_harl`.
Pure tensor-level inspection confirmed unique-action sampling still occurs,
zero-mask reductions are unsafe, and current unbiased nan-std is NaN for one
valid sample.

No AppLauncher, Isaac Sim, environment construction, training, playback,
evaluation or checkpoint load was run.

## Known issues / blockers

- V2.1 contracts are candidate-frozen and require explicit user approval before Phase A.
- Explicit team reward remains unimplemented; current EP learner uses robot 0 reward.
- `ExecutionTransitionFacts` / `LifecycleTransitionResult` and the pre-reset hook remain
  unimplemented.
- Real navigation/alignment estimated-time sources are not present.
- Scenario YAML lifecycle profile is parsed but not propagated by the current
  `apply_scenario_config_to_env_cfg` path.
- Assignment facade returns empty infos, so proper-time-limit `bad_masks` are
  effectively always 1.
- Checkpoint v2 does not fingerprint event/DVM/component/factor/reward semantics.

These are implementation prerequisites, not architectural blockers.

## Do not do

- Do not start training, playback or formal evaluation from this audit alone.
- Do not treat the V2.1 candidate as implementation authorization before user approval.
- Do not modify or load old checkpoints under a new event-gated semantic profile.
- Do not edit installed HARL; add repo-local subclasses/shims.
- Do not use `active_masks` as `decision_valid_mask`.
- Do not write effective assignment into PPO action storage.
- Do not put all failure/TEAM_INFEASIBLE state work after local-set Phase B.
- Do not commit unless the user explicitly requests it.

## Next step

Wait for explicit user approval. No further broad review is required for V2.1.

After explicit user approval, implement **Phase A only**:

- freeze the event-gated gate and resolved-profile dispatcher;
- define/version `ExecutionTransitionFacts` and `LifecycleTransitionResult`;
- freeze generation、consume-once、authority and event-source provenance;
- freeze explicit EP team reward reducer/broadcast semantics;
- define typed event/fact/cost/local-set/DVM/component interfaces;
- add versioned checkpoint semantic fields with v2 backward parsing;
- add structured correctness diagnostics;
- prove feature-off identity separately for supported pre-event-gated profiles before Phase B0.

The team reward reducer、singleton fallback、two-layer transition authority、
profile-aware default-off dispatcher and resolver-commit trigger suppression are frozen
as candidate contracts in V2.1. They still require user approval and later implementation
evidence.

## Detailed reports / archives

- `AgentRead/20260727/Lifecycle_Aware_Event_Gated_Local_MRTA_Design_Authoritative_V2_1_20260727.md`
- `AgentRead/20260727/PHASE10A_AUTHORITATIVE_V2_1_TARGETED_REVISION_SUMMARY.md`
- `AgentRead/20260727/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE10A_AUTHORITATIVE_V2_1_TARGETED_REVISION_20260727.md`
- `AgentRead/20260727/Lifecycle_Aware_Event_Gated_Local_MRTA_Design_Authoritative_V2_20260727.md`
- `AgentRead/20260727/PHASE10A_AUTHORITATIVE_V2_REVISION_SUMMARY.md`
- `AgentRead/20260727/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE10A_AUTHORITATIVE_V2_REVISION_20260727.md`
- `AgentRead/20260724/PHASE10A_EVENT_GATED_LOCAL_MRTA_DESIGN_BACKUP_REVIEW.md`
- `AgentRead/20260727/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE10A_EVENT_GATED_LOCAL_MRTA_DESIGN_BACKUP_REVIEW_20260727.md`
- `AgentRead/20260724/PHASE10A_EVENT_GATED_LOCAL_MRTA_HAPPO_INTERFACE_AUDIT.md`
- `AgentRead/20260724/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE10A_EVENT_GATED_LOCAL_MRTA_HAPPO_INTERFACE_AUDIT_20260724.md`
- `AgentRead/20260722/PHASE9G8I320_MULTI_CONDITION_BEST_FINAL_EVIDENCE_SYNTHESIS_AND_COMMIT_READINESS_REVIEW.md`
- `AgentRead/20260722/PHASE9G8I31_PAIRED_BEST_FINAL_MULTI_CONDITION_ROBUSTNESS_COMPARISON_EXECUTION.md`
- `AgentRead/20260722/PHASE9G8I310_PAIRED_BEST_FINAL_MULTI_CONDITION_ROBUSTNESS_COMPARISON_DESIGN.md`
