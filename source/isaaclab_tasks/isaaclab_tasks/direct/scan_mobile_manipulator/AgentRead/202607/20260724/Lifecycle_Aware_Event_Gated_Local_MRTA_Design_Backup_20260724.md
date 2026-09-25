# Lifecycle-aware Event-Gated Local MRTA

## 方法设计、训练语义与实施路线备忘录

- 整理日期：2026-07-24
- 状态：概念设计已基本冻结；Phase 10A 审计完成；下一步为 Phase A
- 审计分类：`RUNNER-CHANGES-REQUIRED`
- 用途：长期备份、窗口迁移、Codex 交接、论文方法复盘

> 核心方案：固定物理 step 执行 + 生命周期事件触发的局部 assignment tick。Proposal 进入 PPO buffer，effective assignment 进入控制器；critic 使用全部固定步，actor 只使用 decision-valid 样本。

## 1. 研究边界

第一篇研究 lifecycle-aware dynamic MRTA：任务持续占有、冲突仲裁、失败释放、重新分配、策略与执行一致性。允许针对不同固定机器人数量和视点规模分别训练评估；不宣称同一 checkpoint 支持任意 M/N，也不将固定维度 MLP 描述为 variable-cardinality policy。

不研究视点生成、NBV、信息增益、路径规划器/局部避障算法、重建质量模型。底层执行层仅向 MRTA 提供路径有效性、预计代价、进展和最终结果。

## 2. 已锁定的运行语义

1. 物理仿真、控制、reward 和 lifecycle 每个 control step 更新。
2. completion、failure/release、robot unavailable/recovered 或 `NEEDS_ASSIGNMENT` 触发局部 assignment tick。
3. 每机器人生成自己的固定小 Top-K；current task 强制保留。
4. 一轮 owner 扩展，重叠集合合并后重算候选，不递归扩张。
5. 执行机器人：current task = CONTINUE；其他合法 task = SWITCH。空闲机器人：task = CLAIM；noop = IDLE。
6. 每机器人每个 tick 最多一个 proposal；rejection 后保持 `NEEDS_ASSIGNMENT`，下一 tick 重试。
7. Policy 输出全局 task ID；resolver 只做合法性、冲突、component 完整性、代价改善和原子 commit。
8. Resolver 不搜索最优 matching，不搜索 proposal 子集，不发明第二候选。
9. Proposal 保存到 PPO buffer；effective assignment 只交给控制器。

## 3. 生命周期和失败

任务主链：`AVAILABLE -> CLAIMED -> NAVIGATING -> ALIGNING -> COMPLETED`。

- `ALIGNING` 默认不可主动抢占；`NAVIGATING` 可受约束抢占。
- `ALIGNMENT_FAILED(i,j)` 是结构性终端失败：写入 episode-permanent `failed_pair[i,j]`，释放任务并触发局部重分配。
- 导航内部重规划、短暂阻塞和局部避障不属于论文贡献，导航失败不能自动写成永久 failed-pair。
- 所有机器人对任务 j 都 terminal failed 后，task j = `TEAM_INFEASIBLE`，从候选中移除。
- 当所有任务均为 `COMPLETED` 或 `TEAM_INFEASIBLE` 时结束 episode；区分 `ALL_TASKS_COMPLETED` 和 `NO_FEASIBLE_TASKS_REMAIN`。

## 4. Cost 和 transfer

`c_ij(t) = navigation_cost_ij(t) + lambda_align * alignment_cost_ij(t)`，优先统一为预计时间。当前 owner 使用实时剩余代价；每次 assignment tick 刷新 cost。无路径使用显式 bool mask。

Transfer component 比较 event-updated baseline 和完整 proposal assignment：

- 分配任务数量增加：硬约束通过即可接受；
- 数量相同：要求绝对和相对 cost improvement 同时通过；
- 数量减少：主动 proposal 拒绝；
- `N_transfer` 只统计未完成任务 owner 实际变化；claim unowned task 不计 transfer。

## 5. Reward 和指标

- accepted proposal 不额外奖励；
- 策略原因的 rejection 使用统一小额 penalty；
- 每个 rejected component 只计一次；
- 新 profile 的 team reward：对原始 per-agent reward 取 mean，形成 team scalar，再 broadcast；legacy profile 保持旧行为。

主要指标：raw completion ratio（分母为全部任务）、team-infeasible ratio、feasible-task completion ratio、termination reason、decision/rejection/transfer/idle 指标。

## 6. HAPPO 训练语义

- 固定步 rollout 和标准 GAE 保留；critic 使用全部有效物理 step。
- 新增 agent-specific `decision_valid_mask`。
- Actor loss、entropy、advantage statistics 只使用 DVM=1 样本。
- Rejected proposal 仍是有效 actor action。
- K=0：跳过 actor optimizer；K=1：使用 raw finite advantage；K>=2：valid-only population-stat normalization；std 太小时退回 raw advantage。
- HAPPO sequential factor 对 nondecision 样本必须严格使用 ratio=1：`where(DVM, raw_ratio, 1)`。

## 7. Pre-reset facts

DirectMARLEnv 可能在 wrapper post-step 读取前自动 reset done env。终止帧 facts 必须由 environment 在 reset 前生成 immutable snapshot，携带 transition/episode generation，并由 wrapper 一次性消费。禁止使用 reset 后状态解释上一 episode 的 completion、failure、coverage 或 termination。

## 8. Phase 10A 审计结论

可复用：global fixed observation、global task ID、historical action mask、proposal/effective 分离、controller effective path、固定步 GAE、EP critic 骨架。

必须修改：repo-local buffer、runner、actor loss/entropy、valid-only advantage、zero-valid skip、HAPPO factor、local set/Top-K、staged atomic resolver、pre-reset facts、checkpoint semantic identity。

关键现状：EP critic 只读取 `rewards[:,0]`；executing current/noop 是同一 CONTINUE 语义；assignment facade 丢弃 proper-time-limit infos；current resolver 不支持 switch/transfer component。

## 9. 实施阶段

- Phase A：default-off profile/config、typed contracts、checkpoint identity、diagnostics；不改变行为。
- Phase B0：pre-reset facts、terminal pair failure、release、NEEDS_ASSIGNMENT、availability、TEAM_INFEASIBLE state。
- Phase B：event-gated Top-K/mask、DVM sidecar、atomic transfer resolver；deterministic smoke only。
- Phase C：repo-local buffer/runner/HAPPO valid-only update、factor identity。
- Phase D：team reward、rejection penalty、termination、proper time limit、指标。
- Phase E：多 seed、多实例、扰动与消融训练。

## 10. 明确禁止

- 不要每个物理 step 让所有 actor 重新采样。
- 不要把 active mask 当 DVM。
- 不要用 effective 覆盖 PPO proposal。
- 不要只 mask 最终 loss 而忽略 advantage/entropy/factor。
- 不要 zero-loss optimizer step 代替 zero-valid skip。
- 不要让 resolver 成为隐藏优化器或自动第二选择器。
- 不要把短暂导航失败写成 failed-pair。
- 不要从 raw coverage 分母删除 TEAM_INFEASIBLE。
- 不要修改 installed HARL。
- 不要让新 profile 静默加载旧 v2 checkpoint。
- 第一篇完成前不要扩展到 variable-cardinality Transformer。

## 11. 仍需实验确定

K、局部集合硬上限、pair/component thresholds、transfer penalty、rejection penalty 数值、真实 navigation/alignment time estimator、baseline adapter 细节。

## 12. 快速恢复

当前下一步只有 Phase A。实现前已经冻结：team reward mean reduction + broadcast；K=0/1 advantage fallback；authoritative immutable pre-reset facts。每个 phase 必须证明 default-off identity，并把新 semantic 写入 checkpoint fingerprint。
