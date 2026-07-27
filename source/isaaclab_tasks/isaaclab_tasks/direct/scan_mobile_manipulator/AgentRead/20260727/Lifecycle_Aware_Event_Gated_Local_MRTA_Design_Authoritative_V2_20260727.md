# Lifecycle-Aware Event-Gated Local MRTA

> Authoritative Design V2 candidate: method semantics, HAPPO contract, and phased implementation route

```text
document_status:
  AUTHORITATIVE-DESIGN-CANDIDATE

supersedes:
  Lifecycle_Aware_Event_Gated_Local_MRTA_Design_Backup_20260724.md

review_basis:
  PHASE10A_EVENT_GATED_LOCAL_MRTA_DESIGN_BACKUP_REVIEW.md

interface_audit_basis:
  PHASE10A_EVENT_GATED_LOCAL_MRTA_HAPPO_INTERFACE_AUDIT.md

verified_against_head:
  e3febe417c5323e28ceb9e256ba71dcd44f3c457

last_reviewed_date:
  2026-07-27

implementation_authorization:
  none -- documentation gate only

next_technical_phase:
  Phase A only, after GPT/user approval
```

原始
[`Lifecycle_Aware_Event_Gated_Local_MRTA_Design_Backup_20260724.md`](../20260724/Lifecycle_Aware_Event_Gated_Local_MRTA_Design_Backup_20260724.md)
保持不变，作为历史讨论快照。本文在 targeted GPT re-review 和用户确认前仍是
`AUTHORITATIVE-DESIGN-CANDIDATE`，不是代码实现授权。

最新实施状态始终以
[`TASK_PROGRESS.md`](../TASK_PROGRESS.md)
为准。若本文中的 `[CURRENT-CODE]` 描述与当前 HEAD 冲突，以当前代码为准。

---

## 0. Authority、证据与状态标签

### 0.1 必读材料

使用本文进行恢复或实现设计前，必须同时阅读：

1. [`AGENTS.md`](../AGENTS.md)；
2. 最新 [`TASK_PROGRESS.md`](../TASK_PROGRESS.md)；
3. [Phase 10A HAPPO/HARL 接口审计](../20260724/PHASE10A_EVENT_GATED_LOCAL_MRTA_HAPPO_INTERFACE_AUDIT.md)；
4. [设计备忘录独立审核](../20260724/PHASE10A_EVENT_GATED_LOCAL_MRTA_DESIGN_BACKUP_REVIEW.md)；
5. 当前 HEAD 中本文列出的 environment、wrapper、resolver、training 和 checkpoint 入口。

### 0.2 证据优先级

```text
当前 HEAD 的实际代码
>
当前安装环境实际 import 的 HARL
>
Phase 10A HAPPO/HARL 接口审计
>
设计备忘录独立审核报告
>
最新 TASK_PROGRESS.md
>
本文 supersede 的原始设计备忘录
>
更早历史报告
```

已经由用户和 Phase 10A 后续审阅明确冻结的目标方法不因当前尚未实现而删除；
它们统一标记为 `[FROZEN-TARGET-NOT-IMPLEMENTED]`。

### 0.3 状态标签

| 标签 | 含义 |
|---|---|
| `[CURRENT-CODE]` | 当前 HEAD 已实际实现并经代码确认 |
| `[FROZEN-TARGET-NOT-IMPLEMENTED]` | 方法或工程契约已冻结，但当前代码尚未实现 |
| `[NUMERIC-TBD]` | 接口和行为语义已确定，具体数值等待实验或消融 |
| `[IMPLEMENTATION-EVIDENCE-TBD]` | 目标接口已定义，但真实 estimator、execution signal 或代码证据尚不存在 |
| `[DEFERRED-SECOND-WORK]` | 后续 variable-cardinality 独立工作 |

`RESOLVED` 在本文末尾 finding matrix 中只表示文档问题已被 V2 修正，不表示代码已实现、
数值已确定、实验已完成或 V2 已获最终批准。

---

## 1. Executive contract

**Status:** `[FROZEN-TARGET-NOT-IMPLEMENTED]`

核心方法是：

> 固定物理 control step 持续执行，由 lifecycle event 或
> `NEEDS_ASSIGNMENT` opportunity 触发同步的局部 assignment tick。

第一篇使用：

```text
global fixed-dimensional observation
+
local action mask
+
agent-specific decision-valid mask
```

policy 产生 global-task-ID proposal；resolver 只校验 proposal、构造完整 transfer
component 并原子提交 effective assignment；controller 只消费 effective assignment。

固定步 critic、GAE 和 ValueNorm 保留。actor 只从真实 decision-valid 样本学习。
nondecision row 对 HAPPO sequential factor 的概率比严格为 1。

该目标与当前系统结构兼容，但仍需要明确、可控的 runner/trainer/buffer、lifecycle、
resolver、reward 和 checkpoint 修改：

```text
Phase 10A classification:
  RUNNER-CHANGES-REQUIRED
```

不存在已知 architectural blocker。

---

## 2. 研究范围与论文边界

### 2.1 第一篇工作

**Status:** `[FROZEN-TARGET-NOT-IMPLEMENTED]`

第一篇的核心贡献是：

```text
Lifecycle-aware Dynamic Multi-Robot Task Allocation
```

研究任务持续 ownership、执行阶段、完成、终端 pair failure、forced release、
robot availability、局部重分配、冲突仲裁、受约束 preemption、proposal/effective
一致性和 decision-valid HAPPO 学习。

允许：

- 在多个固定机器人数量 `M` 和固定任务/视点数量 `N` 下分别训练和评估；
- 每个固定 `(M,N)` 使用自己的 observation/action shape 和 checkpoint；
- 分析 lifecycle 方法随固定规模变化的趋势。

不宣称：

- 一个 checkpoint 支持任意 `M`；
- 一个 checkpoint 支持任意 `N`；
- 对未见规模进行 zero-shot 泛化；
- 当前 MLP/HAPPO 是 variable-cardinality policy。

### 2.2 后续第二篇工作

**Status:** `[DEFERRED-SECOND-WORK]`

后续独立工作才研究：

- variable-cardinality robot/task representation；
- parameter sharing；
- permutation consistency/equivariance；
- Transformer、Set Encoder、GNN 等候选结构；
- 同一 checkpoint 跨不同 `(M,N)`；
- cardinality interpolation 与 extrapolation。

这些模型尚未选型，不是 Phase A–E 的当前依赖，也不能作为第一篇已经具备的能力。

### 2.3 非研究贡献

**Status:** `[FROZEN-TARGET-NOT-IMPLEMENTED]`

第一篇不把以下内容作为论文贡献：

- viewpoint generation；
- coverage view planning；
- next-best-view；
- ROI / information gain；
- path-planning algorithm；
- local-avoidance algorithm；
- navigation controller design；
- reconstruction-quality optimization。

MRTA 只消费 execution layer 提供的：

- nominal path validity；
- expected navigation cost；
- expected terminal alignment cost；
- completion、release、terminal pair failure；
- robot unavailable/recovered；
- 其他明确 lifecycle result。

普通 execution progress 可用于控制、reward 或诊断，但不是 assignment event。

---

## 3. 当前代码能力快照

**Status:** `[CURRENT-CODE]`

本节只描述 HEAD
`e3febe417c5323e28ceb9e256ba71dcd44f3c457`
和当前 import 的 HARL，不描述目标已经实现。

| Topic | Current code | Frozen target | Owning phase |
|---|---|---|---|
| actor sampling | installed runner 每个 physical step 调用所有 actor | policy sampling 只发生在 DVM=true row；其他 row 使用 forced placeholder | C |
| cost | scanner-to-viewpoint Euclidean distance prototype | expected navigation + alignment time | A/B |
| switch | resolver-enabled Contract C 拒绝 executing switch；resolver-disabled legacy 是 proposal pass-through，没有持久 ownership switch 语义 | 受 pair/component gate 约束的 switch | B |
| resolver | per-robot immediate mutation；无 transfer component | staged atomic components | B |
| proposal/effective | resolver-enabled wrapper 保留 sampled proposal，并把 effective assignment 交给 controller；诊断可同时读取两者 | proposal 永不被 effective 覆盖，component 结果另存 | A/B/C |
| action mask | current physical/Contract-C prototype mask 保留 noop；无 event-local Top-K、path-valid 或 DVM 联合契约 | global-ID local mask + independently derived DVM | B/C |
| task state | env 输出只实例化 unassigned/completed proxy；robot status 全 IDLE placeholder | full task/robot lifecycle 与 `TEAM_INFEASIBLE` | B0 |
| DVM | 不存在 | agent-specific DVM | A/C |
| team reward | env reward 是 shared+individual；wrapper 输出 `[E,M,1]`；EP buffer 只取 `rewards[:,0]` | wrapper-final mean team scalar，component penalty 后 broadcast | D |
| pre-reset facts | authoritative transition DTO 不存在 | immutable、generation-bound、consume-once DTO | A/B0 |
| checkpoint | v2 manifest 可描述 legacy 与 current Contract C，但不含 event-gated/DVM/reward/component 新语义 | 保留 v2 parser + distinct event-gated semantic version | A |
| config propagation | lifecycle profile 可 parse/validate，但 current apply path 未完整传播这些字段 | 单一 resolved profile 贯通 runtime/manifest/playback | A |
| playback | current path 每步逐 actor inference；诊断脚本有 coverage-only pre-reset monkey-patch，但不是 lifecycle authority | DVM-aware inference + authoritative transition DTO | A/B0/C |
| proper time limit | HARL/YAML machinery 已存在，但 assignment facade 返回 empty infos，使 effective bad mask 恒为 1 | explicit terminated/truncated/bad-transition contract | D |

关键证据：

- `scan_mobile_manipulator_env.py:1695-1720`：
  Euclidean cost、task unassigned/completed、robot IDLE placeholder；
- `scan_mobile_manipulator_env.py:2930-3020`：
  candidate/dwell coverage completion、shared+individual reward、all-covered/timeout done；
- `assignment_harl_wrapper.py:396-495`：
  proposal → resolver → effective → controller，并分别保存 proposal/effective；
- `assignment_lifecycle_observation.py:659-742`：
  current Contract C executing current 与 noop 都可用；
- `assignment_lifecycle_resolver.py:676-802`：
  resolver-enabled Contract C 中 current/noop 均 continue、switch rejected、claim 直接 mutation；
- `assignment_harl_training.py:315-319,598-605`：
  facade 丢弃 infos，repo-local collect 仍调用 installed runner；
- installed `on_policy_base_runner.py:334-370,506-514`：
  all-actor sampling，EP critic 插入 `rewards[:,0]`；
- installed `on_policy_ha_runner.py:17-24,116-127`：
  `[T,E,1]` factor 无条件乘 raw ratio；
- installed `happo.py:76-99,118-155`：
  active-mask reduction、minibatch optimizer step、active-only advantage normalization；
- `direct_marl_env.py:389-405`：
  done env 在 `step()` 返回 wrapper 前确定执行 `_reset_idx()`；
- `assignment_checkpoint_contract.py:39`：
  current manifest version 为 `assignment_checkpoint_contract_v2`。

`assignment_state.py` 虽定义通用 assigned/in-progress/failed/unreachable/timeout 和
moving/scanning/blocked 等常量，但 current environment assignment problem 并未填充本文
目标 lifecycle。current resolver 还有一套独立的 Contract C prototype pair/robot state；
两者都不能被写成目标 lifecycle 已实现。

---

## 4. 固定物理步、事件和唯一 strict order

**Status:** `[FROZEN-TARGET-NOT-IMPLEMENTED]`

### 4.1 Canonical strict order

系统只允许以下一个目标顺序：

```text
physical execution result
→ authoritative pre-reset transition facts
→ robot/task lifecycle state update
→ completion/release/failed-pair/availability writes
→ termination determination
→ same-step lifecycle event collection
→ local-set construction and overlap merge
→ assignment-tick cost/path-valid refresh
→ per-robot Top-K construction
→ global observation + local action mask + DVM snapshot
→ one proposal per local decision-valid robot
→ transfer-component validation
→ staged atomic effective-assignment commit
→ next physical control step
```

先更新事实，再让 policy 决策。不能使用旧 ownership、旧 failed-pair 或 reset 后状态生成
本 tick 的 observation、mask、DVM 或 proposal。

### 4.2 固定步边界

- physics、collision、controller、execution progress、reward 和 lifecycle observation
  每个固定 physical control step 更新；
- assignment tick 是两个相邻 physical control step 之间的同步逻辑边界；
- assignment tick 不是新的 asynchronous environment step；
- 本方法不是完整 SMDP 重构；
- 固定步 rollout、discount 和 GAE 时间轴保持；
- 普通 `NAVIGATING` progress 不触发 proposal；
- 普通 `ALIGNING` progress 不触发 proposal；
- 非局部且正常执行的机器人不重新决策。

### 4.3 Event taxonomy

能触发或合并进 assignment tick 的 lifecycle event 至少包括：

- task completed；
- structural terminal pair failure；
- forced release；
- robot unavailable；
- robot recovered；
- ownership materially changed；
- task/robot feasibility materially changed；
- persistent `NEEDS_ASSIGNMENT` robot 的 scheduled assignment opportunity。

`NEEDS_ASSIGNMENT` retry tick 是 scheduled assignment opportunity，不必伪装成新的
physical lifecycle event；它仍必须按配置 cadence 触发同一套 cost/mask/DVM snapshot。

### 4.4 Terminal rule

terminal environment 只记录 authoritative facts、termination/truncation 和 reason：

```text
terminal transition:
  decision_valid_mask[:] = 0
  no new proposal
  no new transfer-component commit
```

---

## 5. Task 与 Robot lifecycle

### 5.1 目标 task states

**Status:** `[FROZEN-TARGET-NOT-IMPLEMENTED]`

| State | 语义 |
|---|---|
| `AVAILABLE` | 未完成、可被合法机器人 claim |
| `CLAIMED` | ownership 已原子建立，尚未进入稳定导航执行 |
| `NAVIGATING` | owner 正在导航至 task 的扫描区域 |
| `ALIGNING` | owner 正在做终端姿态/可达性调整 |
| `COMPLETED` | alignment success，本 episode 永久终态 |
| `TEAM_INFEASIBLE` | 所有机器人对该 task 都已有 structural terminal failed pair，本 episode 永久终态 |

failure 与 release 是 authoritative transition/event，不要求都成为长期驻留 task state。

目标执行链为：

```text
AVAILABLE
→ CLAIMED
→ NAVIGATING
→ ALIGNING
→ COMPLETED
```

- task 不是连续 scan-progress allocation 模型；
- robot 先导航到扫描区域，再做 terminal alignment；
- alignment success 立即完成 task；
- `ALIGNING` 默认不可主动 preempt；
- `NAVIGATING` 只允许通过严格 pair gate 与完整 component 被 preempt。

### 5.2 目标 robot states/events

**Status:** `[FROZEN-TARGET-NOT-IMPLEMENTED]`

| State/event | 语义 |
|---|---|
| `EXECUTING` | 持有合法 current task，处于 navigation/alignment execution |
| `NEEDS_ASSIGNMENT` | 当前无合法 assignment，并在下一 scheduled opportunity 参与决策 |
| `WAITING_FOR_TASK` | 当前只有 forced idle/noop，没有真实策略选择 |
| `UNAVAILABLE` | 不得 claim/switch，不能进入 decision-valid local set |
| `RECOVERED_EVENT` | transient event；恢复后转入 `NEEDS_ASSIGNMENT` 或合法 `EXECUTING`，不是长期驻留状态 |

### 5.3 当前 completion proxy

**Status:** `[CURRENT-CODE]`

当前 `scan_mobile_manipulator_env.py:2930-2983` 的 position/orientation/workspace/range/FOV
candidate + dwell + covered 更新只是 prototype completion signal。当前代码尚未实现本文目标
authoritative terminal-alignment lifecycle，不能把 coverage proxy 当作该 lifecycle 的证据。

---

## 6. Local set、Top-K 与 observation

**Status:** `[FROZEN-TARGET-NOT-IMPLEMENTED]`

### 6.1 Local-set algorithm

每个 assignment tick 按以下顺序构造：

1. seeds：

   ```text
   lifecycle event robots
   ∪ NEEDS_ASSIGNMENT robots
   ```

2. 每个 seed 独立生成固定小 Top-K；
3. Top-K 只按 nominal robot-task cost 排序；
4. Top-K 前过滤：

   - `COMPLETED` task；
   - `TEAM_INFEASIBLE` task；
   - episode-permanent failed pair；
   - nominal path invalid pair；
   - task globally invalid 或明确不可执行状态；

5. Top-K 生成时不直接排除被其他 robot 占有的 task；
6. event-updated baseline 中仍合法的 current task 即使不在 Top-K，也必须加入该 robot
   candidate，作为 `CONTINUE`；
7. seed Top-K 中 occupied task 的 current owner 加入 local robot set；
8. 新加入的 owner 也生成自己的 Top-K；
9. 第一版只做这一轮 owner expansion；
10. 不递归加入新 owner Top-K 中第二层 occupied task 的 owner；
11. 第二层 candidate 若属于集合外 owner，本 tick 对 preemption mask 掉；
12. 多个 local set 有 robot/task overlap 时合并；
13. 合并后重新计算 cost、Top-K、action mask 和 DVM，但不得因重算重新开启第二轮
    owner expansion；
14. 始终使用 global task ID；
15. 不做 local task renumbering；
16. 不做 local observation repacking。

### 6.2 Observation strategy

第一篇固定使用：

```text
global fixed-dimensional observation
+
local action mask
```

actor/critic 仍看到固定 `(M,N)` 的 global robot/task state。locality、failed pair、
ownership、phase、Top-K、path validity 和 preemption eligibility 由 action mask 与
DVM 限制，不改变 task ID。

### 6.3 Capacity 与 overflow

- `top_k_tasks_per_robot`：`[NUMERIC-TBD]`
- `local_robot_cap`：`[NUMERIC-TBD]`
- `local_task_cap`：`[NUMERIC-TBD]`

cap overflow 不得静默截断 owner closure 或 transfer component。第一版必须：

- fail closed；或
- 进入“不允许新增 preemption、只允许安全 continue/unowned claim”的显式安全模式。

具体选择在 Phase A 定义 typed result/reason，在 Phase B 实现和测试；任何 fallback 都必须
记录 diagnostics。

---

## 7. Nominal cost contract

### 7.1 冻结公式

**Status:** `[FROZEN-TARGET-NOT-IMPLEMENTED]`

```text
nominal_cost[e,i,j]
=
navigation_cost[e,i,j]
+
alignment_cost[e,i,j]
```

不存在 objective-level `lambda_align`。若原始数据单位不同，estimator/interface 必须先转成
共同 expected-time 单位，再相加。

接口：

```text
navigation_cost:   [E,M,N] float, expected remaining time
alignment_cost:    [E,M,N] float, pair-specific expected time
nominal_path_valid:[E,M,N] bool
cost_generation:   transition/tick identity
```

要求：

- current owner 使用当前时刻的 remaining expected cost；
- 每个 assignment tick 开始时刷新；
- `alignment_cost` 保持 pair-specific matrix；
- 第一版可把 robot-specific `alignment_time_constant[i]` 广播到 N；
- no-path 用 `nominal_path_valid=false`；
- 禁止以任意大有限数代替 invalid path；
- Top-K 不加入 switching/transfer penalty；
- pair gate 使用 nominal remaining cost；
- transfer penalty 只进入完整 component objective。

### 7.2 当前 fallback 与证据缺口

**Status:** `[CURRENT-CODE]`

当前 `get_assignment_problem()` 只有 scanner-to-viewpoint Euclidean distance。它是明确的
prototype fallback，不满足 expected navigation/alignment time contract。

**Status:** `[IMPLEMENTATION-EVIDENCE-TBD]`

真实 navigation-time estimator、alignment-time estimator 和 authoritative
remaining-time source 当前不存在。Phase A 可先冻结 typed interface；Phase B0/B 再接
execution evidence。不能把 prototype distance 写成真实预计时间实验结果。

---

## 8. Action semantics 与 decision-valid mask

**Status:** `[FROZEN-TARGET-NOT-IMPLEMENTED]`

### 8.1 Executing robot

```text
current global task ID = CONTINUE
another legal global task ID = SWITCH
noop = masked
```

current task ID 是新 profile 下唯一 CONTINUE 表示。current 与 noop 不得同时表达 CONTINUE。

### 8.2 Idle / NEEDS_ASSIGNMENT robot

```text
global task ID = CLAIM
raw noop ID = N
noop = IDLE / remain waiting
```

action dimension 可保持 `N+1`，task action 始终使用 global task ID。

### 8.3 DVM definition

raw mask count 不等于 semantic legal action count。DVM 由以下条件共同决定：

- 本 step 是否有 assignment tick；
- robot 是否属于合并后的 local set；
- robot 是否 available；
- 是否存在至少两个 semantic legal actions；
- environment 是否 nonterminal；
- snapshot/generation 是否有效。

等价规则：

```text
DVM[e,i] =
    tick_eligible
    and local_set_member
    and robot_available
    and semantic_legal_action_count >= 2
    and not terminal
```

只有一个 semantic legal action：

```text
DVM = 0
```

被 resolver 拒绝的真实 proposal：

```text
DVM = 1
```

因为 rejection 是 policy action 的结果，不能从 actor training 删除。

`active_masks` 表示 agent/episode 存活边界；DVM 表示是否做出真实 assignment choice。
两者必须独立存储、独立断言，不能复用。

### 8.4 Nondecision storage

为保留固定 rollout tensor shape，DVM=false row 可以写入 deterministic forced
continue/idle placeholder，但：

- 不调用 policy 进行 proposal sampling；
- placeholder 不是有效 policy proposal；
- 不进入 actor loss、entropy、advantage statistics；
- sequential ratio 必须为 1；
- effective assignment 仍不回写 action buffer。

---

## 9. Assignment-tick retry 与 fallback

**Status:** `[FROZEN-TARGET-NOT-IMPLEMENTED]`

- 每个 robot 每个 assignment tick 最多提出一次 proposal；
- 同 tick 不采样第二、第三候选；
- rejection 后只在下一 eligible assignment tick 重算 cost、Top-K、mask 和 DVM；
- 正常执行且不受局部 event 影响的 robot 不参与 retry。

### 9.1 Rejected executing SWITCH

```text
fallback = event-updated baseline/current task
```

只要 baseline current task 仍合法，robot 保持 `EXECUTING`，不进入
`NEEDS_ASSIGNMENT`。如果 forced lifecycle fact 已先 release current task，则 baseline
已经无 current assignment，按 idle/unassigned fallback 处理。

### 9.2 Rejected idle/unassigned CLAIM

```text
fallback = NOOP
state = NEEDS_ASSIGNMENT
```

下一 scheduled assignment opportunity 再决策。

### 9.3 Forced idle

只有 noop 或唯一 forced action时：

- `DVM=0`；
- robot 进入 `WAITING_FOR_TASK`；
- 不在每个 physical step 重复 policy-sample noop；
- ownership、candidate、availability、retry schedule 或 lifecycle 状态变化后才重新激活。

`assignment_retry_cadence` 的数值是 `[NUMERIC-TBD]`；它是 scheduled opportunity
参数，不是新的 lifecycle event type。

---

## 10. Proposal、effective assignment 与 controller

### 10.1 当前可复用主链

**Status:** `[CURRENT-CODE]`

在 resolver-enabled Contract C 路径中，当前 wrapper 已有：

```text
decoded assignment proposal
→ lifecycle resolver
→ effective assignment
→ controller/env action
```

并在 `assignment_harl_wrapper.py:440-442,2445-2481` 分开记录 proposal 与 effective。

### 10.2 冻结数据契约

**Status:** `[FROZEN-TARGET-NOT-IMPLEMENTED]`

唯一数据流：

```text
policy proposal
→ resolver
→ effective assignment
→ controller
```

- PPO action buffer 在 decision-valid row 保存 proposal；
- proposal log-prob 必须对应 proposal action；
- nondecision row 仅保存 DVM=false forced placeholder；
- effective assignment 不得覆盖 proposal/placeholder action storage；
- rejected proposal 仍用于 actor learning；
- controller 只消费 effective assignment；
- logger/diagnostics 同时保留 proposal、effective、accepted 和 rejection reason。

`effective_assignment`、`proposal_accepted`、`rejection_reason` 和 component detail
主要属于 diagnostics/info/logger；DVM 和 proposal action/log-prob 属于核心训练 contract。

---

## 11. Resolver responsibility 与禁止项

**Status:** `[FROZEN-TARGET-NOT-IMPLEMENTED]`

Resolver 负责：

- hard constraints；
- task ownership uniqueness；
- deterministic conflict arbitration；
- preemption eligibility；
- transfer-component closure；
- component objective；
- staged atomic commit。

Resolver 禁止：

- 搜索最优 matching；
- 枚举 proposal subset；
- 为 rejected robot 生成第二候选；
- 自动选择 policy 未提出的 task；
- 在失败 component 中提升 runner-up contender；
- 顺序 mutation 导致半提交；
- 用 effective assignment 回写 PPO action buffer。

Resolver 是 proposal validator/committer，不是隐藏 optimizer。

---

## 12. Transfer component 与 atomic commit

**Status:** `[FROZEN-TARGET-NOT-IMPLEMENTED]`

每个 tick：

1. 应用 forced lifecycle facts：

   - completion；
   - forced failure/release；
   - robot unavailable/recovered；
   - `TEAM_INFEASIBLE` update；

2. 形成 event-updated baseline `a0`；
3. 校验 proposal hard constraints；
4. 对同 task competition 做 deterministic arbitration；
5. 用 baseline ownership edge 与 proposal edge 构造 transfer graph；
6. 分解 connected components；
7. 每个 component 全量验证，不 mutation；
8. 生成 staged assignment/ownership；
9. component 整体接受或整体拒绝；
10. 接受后一次性 commit effective assignment 与 ownership。

完整 component 必须满足：

- 所有 proposed pair 合法；
- ownership 唯一；
- task phase 允许 preemption；
- 每条 active preemption edge 通过 pair gate；
- 被 preempt owner 在同一 component 有合法新去向；
- transfer chain/cycle 闭合；
- 不抢占集合外 owner；
- assigned-count 与 component-cost 条件通过。

任一关键条件失败：

```text
reject entire component
```

同一 component 不能半提交。多个真正不相交 component 可独立 accept/reject；每个 component
仍是 atomic unit。完整、合法且满足 objective 的 component 可以覆盖 current owner 的
`CONTINUE` proposal。

---

## 13. Pair gate、component objective 与 transfer counting

### 13.1 Pair-level preemption eligibility

**Status:** `[FROZEN-TARGET-NOT-IMPLEMENTED]`

仅对 active ownership preemption 检查：

```text
owner_remaining_cost - new_robot_cost > pair_abs_threshold
```

且：

```text
new_robot_cost
<
(1 - pair_rel_threshold) * owner_remaining_cost
```

absolute 与 relative gate 必须同时通过。pair gate 只说明一条 preemption edge 有资格，
不是 component 最终接受条件。

`pair_abs_threshold`、`pair_rel_threshold` 均为 `[NUMERIC-TBD]`。

### 13.2 Component baseline

```text
a0 = event-updated baseline assignment
```

`a0` 必须在 completion、forced release/failure、availability 和 team-infeasible facts
应用后形成。forced lifecycle release 不是 active proposal 导致的 assigned-count decrease。

### 13.3 Assigned unfinished task count

在每个 component 内先比较：

```text
assigned_count(a_proposal)
vs
assigned_count(a0)
```

只统计未完成 task。

#### Count 增加

只有以下全部通过才接受：

- hard constraints；
- pair gates；
- component closure；
- ownership uniqueness；
- atomic staging。

count 增加不能绕过 preemption gate。

#### Count 相同

```text
J0 =
sum of nominal remaining cost under a0
```

```text
Jp =
sum of nominal remaining cost under staged proposal
+
transfer_penalty * N_owner_changes
```

同时要求：

```text
J0 - Jp > component_abs_threshold
```

```text
Jp < (1 - component_rel_threshold) * J0
```

`component_abs_threshold`、`component_rel_threshold`、`transfer_penalty`
均为 `[NUMERIC-TBD]`。

#### Count 减少

active proposal 拒绝。forced lifecycle release 已在 `a0` 中处理，不算 proposal 主动减少。

### 13.4 Transfer counting

**Status:** `[FROZEN-TARGET-NOT-IMPLEMENTED]`

```text
claim unowned task:
  0 transfers

forced failure release followed by claim:
  0 active-preemption transfers

unfinished task changes owner:
  1 transfer

bilateral swap of two owned tasks:
  2 transfers
```

`N_owner_changes` 只统计未完成 task 的主动 ownership change。

---

## 14. Conflict arbitration

**Status:** `[FROZEN-TARGET-NOT-IMPLEMENTED]`

occupied task 多 contender 的确定性顺序：

1. non-preemptible stage 的 current owner 优先；
2. 只保留满足 hard constraints 与 pair gate 的 contender；
3. 比较 contender 的 improvement；
4. 再比较更低的新 nominal cost；
5. 最后按 deterministic robot-ID tie-break。

unowned task 没有 owner improvement 可比较；在 hard-legal contenders 中按更低 nominal cost、
再按 deterministic robot ID 仲裁。

仲裁后必须重新检查 transfer-component closure。若 winner 所在 component 失败，
本 tick 不提升 loser、不重建 proposal subset、不生成第二候选。

Loser fallback：

- executing loser 回 event-updated baseline/current；
- idle loser 回 noop/`NEEDS_ASSIGNMENT`；
- 不自动分配其他 task。

---

## 15. Failed pair 与 `TEAM_INFEASIBLE`

### 15.1 Structural terminal failure

**Status:** `[FROZEN-TARGET-NOT-IMPLEMENTED]`

```text
ALIGNMENT_FAILED(i,j)
→ failed_pair[i,j] = true
→ episode 内永久禁止
→ release task
→ robot NEEDS_ASSIGNMENT
→ trigger local reassignment
```

结构性终端失败例如：

- IK infeasible；
- joint limit；
- terminal self-collision；
- terminal component collision；
- 其他稳定 robot-task capability mismatch。

### 15.2 非 permanent failed pair

以下不自动写入 permanent failed pair：

- temporary navigation obstruction；
- temporary inter-robot collision；
- controller stall；
- planner internal replan；
- temporary robot failure；
- transient path block。

execution layer 内部处理这些情况；超过内部预算后只向 MRTA 上报执行失败或 forced release。
只有 authoritative structural terminal alignment failure 才永久禁止 pair。

### 15.3 `TEAM_INFEASIBLE`

**Status:** `[FROZEN-TARGET-NOT-IMPLEMENTED]`

```text
if for all robots i:
    failed_pair[i,j] = true
then:
    task_state[j] = TEAM_INFEASIBLE
```

随后：

- 从 Top-K 移除；
- 从 action mask 移除；
- 不再分配；
- 记录 team-infeasible metric。

单个 task `TEAM_INFEASIBLE` 时，只要仍有其他可执行 task，episode 继续。
某一时刻所有 robot 的 `nominal_path_valid=false` 不能自动等价于
`TEAM_INFEASIBLE`，因为 path invalid 可能是 transient；该终态只由 episode-permanent
structural failed pairs 推导。

---

## 16. Episode termination 与指标

**Status:** `[FROZEN-TARGET-NOT-IMPLEMENTED]`

termination reason 和优先级：

```text
if all tasks == COMPLETED:
    ALL_TASKS_COMPLETED

elif all tasks in {COMPLETED, TEAM_INFEASIBLE}:
    NO_FEASIBLE_TASKS_REMAIN

elif time limit:
    TIME_LIMIT
```

指标：

```text
raw_completion_rate
=
completed / total_tasks
```

```text
team_infeasible_rate
=
team_infeasible / total_tasks
```

```text
feasible_task_completion_rate
=
completed / (total_tasks - team_infeasible)
```

- raw completion 分母始终包含全部原始 task；
- feasible completion 只是辅助指标；
- 不能用删除 infeasible task 后的 100% 替代 raw completion；
- `NO_FEASIBLE_TASKS_REMAIN` 不等于完整成功；
- feasible denominator 为 0 时，指标必须报告 undefined/invalid flag，不能除零或伪报 100%。

---

## 17. Rejection reward

**Status:** `[FROZEN-TARGET-NOT-IMPLEMENTED]`

第一版：

- accepted proposal 不额外奖励；
- policy-caused rejection 使用统一小额 penalty；
- 每个 rejected component 只计一次；
- 不按 component robot 数放大；
- 不使用连续拒绝递增 penalty；
- `rejection_penalty_scale` 为 `[NUMERIC-TBD]`。

### 17.1 Penalized policy outcomes

例如：

- contention loss；
- insufficient pair improvement；
- incomplete transfer chain；
- component cost insufficient；
- individually legal actions 形成 policy-caused invalid coordination。

### 17.2 Not penalized

例如：

- proposal snapshot 后 system facts 改变；
- implementation synchronization error；
- environment/system invalidation；
- terminal transition；
- 其他非 policy 可控状态变化。

hard-invalid action 原则上必须被 action mask 阻止。如果仍出现，应先 fail-fast 或标为
implementation anomaly，并记录 mask/snapshot/generation 诊断；不得静默当作普通 learning
signal。

resolver 必须输出 canonical component-level rejection record，至少包含稳定 component/
rejection identity、reason、policy-caused/penalty-eligible 标志和 member robots/tasks。
reward 只能对唯一 penalty-eligible component record 计一次，不能直接累加 per-robot
rejection flags。

---

## 18. Team reward contract

### 18.1 当前事实

**Status:** `[CURRENT-CODE]`

- env base reward 是 shared global/time 项与 per-agent own/duplicate/reach/action-rate 项组合；
- wrapper 加入 assignment shaping 后输出 `[E,M,1]`；
- installed HARL EP critic buffer 实际插入 `rewards[:,0]`；
- 当前没有明确的 team reward reducer。

### 18.2 新 event-gated profile

**Status:** `[FROZEN-TARGET-NOT-IMPLEMENTED]`

先对不含新 component-rejection penalty 的 wrapper final per-agent reward 求 mean：

```text
base_team_reward[e]
=
mean_i(wrapper_final_reward[e,i])
```

再按 rejected component 数扣一次：

```text
team_reward[e]
=
base_team_reward[e]
-
rejection_penalty_scale
*
policy_rejected_component_count[e]
```

最后 broadcast：

```text
learner_reward[e,i]
=
team_reward[e]
```

因此：

- rejection penalty 在 mean reduction 后扣除；
- 不被 agent mean 稀释；
- 不因 broadcast 按 robot 数重复放大；
- raw per-agent reward decomposition 只用于 diagnostics；
- legacy/default-off profile 直接保持 current behavior；
- 本契约尚未实现。

---

## 19. HAPPO decision-valid contract

**Status:** `[FROZEN-TARGET-NOT-IMPLEMENTED]`

- 固定 physical-step rollout 保留；
- standard GAE 保留；
- critic 使用全部有效 physical step；
- ValueNorm 使用全部 critic return；
- DVM 不进入：

  - GAE；
  - return；
  - critic loss；
  - ValueNorm；

- actor policy loss、entropy 和 advantage statistics 只用 DVM=true；
- rejected proposal 仍是 valid actor sample；
- PPO action buffer 保存 proposal，不保存 effective replacement。

每个 actor buffer 新增：

```text
decision_valid_mask: [T+1,E,1]
```

训练使用：

```text
decision_valid_mask[:-1]
```

在 timestep `t`，action/log-prob 与 `decision_valid_mask[t]` 对齐；insert 同时写入下一
state 的 mask。历史 available-action mask 继续保存，不能用 current mask 重新解释旧 action。

同一 physical step 不同 agent 可以有不同 DVM。actor loss/entropy 的有效 mask 是：

```text
actor_valid = active_mask * decision_valid_mask
```

但两个字段仍保持独立，分别用于 episode/alive 与 decision semantics。

policy loss 与 entropy 都必须按有效样本数归一化：

```text
masked_mean(x) = sum(actor_valid * x) / sum(actor_valid)
```

该除法只允许在 `sum(actor_valid) > 0` 时执行；分母为 0 的 actor/minibatch 按
§20 完整跳过，不产生 zero-loss optimizer step。

---

## 20. Zero-valid 与 singleton advantage

**Status:** `[FROZEN-TARGET-NOT-IMPLEMENTED]`

禁止再用单独的 `K` 表示 valid sample count；统一使用：

```text
n_valid_actor_samples
```

### 20.1 `n_valid_actor_samples == 0`

- 不执行 actor train；
- 不 evaluate pre/post ratio；
- 不 backward；
- 不 `optimizer.step()`；
- actor parameters 不变化；
- optimizer state 不变化；
- sequential factor 不变化；
- 记录 skipped actor update。

zero loss + optimizer step 不等价于 skip。

### 20.2 `n_valid_actor_samples == 1`

- 不做 mean/std normalization；
- 使用 finite raw advantage；
- raw advantage 非 finite 时 fail-fast。

### 20.3 `n_valid_actor_samples >= 2`

- 只在该 actor rollout 的 valid sample set 计算 mean/std；
- 使用 `unbiased=False`；
- std 非 finite 或低于 epsilon 时回退 finite raw advantage；
- 不在每个 minibatch 单独重算统计。

### 20.4 Empty minibatch

minibatch 没有 valid sample 时：

- 不 forward；
- 不 backward；
- 不 optimizer step；
- logger 按真实 processed updates 归一化，不使用固定 minibatch 数除法。

---

## 21. HAPPO sequential factor

**Status:** `[FROZEN-TARGET-NOT-IMPLEMENTED]`

每个已更新 actor 的 raw new/old action-probability ratio 先变换为：

```python
effective_ratio = torch.where(
    decision_valid_mask,
    raw_ratio,
    torch.ones_like(raw_ratio),
)
```

再更新：

```python
factor *= effective_ratio
```

- nondecision ratio 必须严格为 1；
- 禁止用 `DVM * ratio + (1-DVM) * 1`，因为 `0 * NaN` 仍可能产生 NaN；
- 只在最终 actor loss 外乘 DVM 不足；
- factor shape 保持 `[T,E,1]`；
- 不新增 agent 维；
- 每个 actor 用自己的 DVM 更新共同 sequential factor；
- zero-valid actor 完全跳过，factor 不变。

---

## 22. Authoritative pre-reset transition facts

### 22.1 当前事实

**Status:** `[CURRENT-CODE]`

`DirectMARLEnv` 确定会在 `env.step()` 返回 wrapper 前 reset done environment。
`direct_marl_env.py:389-405` 先求 done/reward，再 `_reset_idx()`，最后构造 reset 后 obs；
wrapper 在返回后才读取 post-step assignment problem。它不能从该 reset 后状态反推上一
episode。

`evaluate_assignment_rl_playback_diagnostics.py:725-756` 的 diagnostics-only
coverage capture 会临时替换 `_reset_idx()`，只能证明 playback 有一个局部观测补丁；
它不提供 lifecycle typed DTO、generation match 或 consume-once authority，不能作为
训练接口的 pre-reset 事实源。

### 22.2 目标 DTO

**Status:** `[FROZEN-TARGET-NOT-IMPLEMENTED]`

终止帧事实必须在 `_reset_idx()` 前由 environment 生成 immutable transition DTO：

```text
episode_generation
transition_generation
env_id

terminated
truncated
termination_reason
bad_transition

newly_completed_tasks
released_tasks
terminal_failed_pairs
team_infeasible_tasks

robot_unavailable_events
robot_recovered_events

coverage_before_reset
task_state_before_reset
ownership_before_reset

consume_once_token
```

规则：

- snapshot immutable；
- 每份 snapshot 只能消费一次；
- generation 与 wrapper 当前 transition 必须精确匹配；
- stale、duplicate 或 future generation fail-fast；
- terminal transition DVM 全 0；
- wrapper 不得用 reset 后 `get_assignment_problem()` 解释上一 transition；
- Phase A 只定义 DTO version、shape、authority 和 assertions；
- Phase B0 实现 environment pre-reset hook 与 lifecycle transition。

---

## 23. Default-off direct bypass

**Status:** `[FROZEN-TARGET-NOT-IMPLEMENTED]`

最严格的 feature-off 契约：

```text
feature off
→ direct dispatch to current legacy runner/trainer/resolver path
```

禁止：

```text
new event-gated path
+ DVM all ones
```

模拟 legacy。

Feature-off 必须与当前 HEAD 保持：

- observation；
- shared observation；
- action dimension；
- action mask；
- sampled action；
- rollout log-prob；
- effective assignment；
- reward；
- GAE/return；
- ValueNorm input；
- HAPPO factor；
- RNG path；
- minibatch order；
- logger output；
- file side effects；
- checkpoint v2；
- playback behavior。

Feature-on：

- 使用新的高层 profile；
- 使用新的 semantic contract/fingerprint；
- 即使 tensor shape 相同，也不得把 legacy v2 当作正常 event-gated checkpoint；
- semantic mismatch fail-fast；
- installed HARL 保持只读；
- 使用 repo-local subclass/shim/registry。

---

## 24. Checkpoint semantic contract

**Status:** `[FROZEN-TARGET-NOT-IMPLEMENTED]`

event-gated profile 的新 manifest/fingerprint 必须绑定：

- event taxonomy/order；
- assignment-tick semantics；
- local-set seed/owner expansion/merge；
- Top-K/current retention；
- cost/path-valid contract；
- action semantic/noop rule；
- DVM definition；
- valid-only sampling/loss/entropy/advantage normalization；
- zero/singleton handling；
- nondecision factor identity；
- team reward reducer；
- rejection penalty unit；
- component closure/objective；
- transfer counting；
- failed-pair semantics；
- `TEAM_INFEASIBLE`；
- termination reasons；
- pre-reset fact version。

版本策略：

- 保留 current v2 parser，对 legacy 与 current `lifecycle_contract_c` 继续按原
  semantic 解析；
- event-gated profile 使用 distinct next-version manifest；
- Phase A 的目标标识为 `assignment_checkpoint_contract_v3`；
- parser 不得单向改成只支持 v3；
- feature-off v2 在同一 legacy semantics 下继续可用；
- feature-on 对 v2 semantic mismatch 必须 fail-fast；
- 未经具名、窄范围、明确授权的 ablation，不允许跨 semantic load。

rollout buffer 不作为跨 run continuation 的隐式兼容保证。即使 observation/action dimension
不变，DVM、reward、factor 或 component semantic 变化也构成 checkpoint incompatibility。

---

## 25. Scenario、playback、logger 与 correctness diagnostics

### 25.1 当前事实

**Status:** `[CURRENT-CODE]`

- `scenario_config.py` 能验证 lifecycle metadata，但 Phase 10A 已确认 current apply path
  尚未完整传播目标 profile；
- playback 当前逐 actor inference，没有 DVM subset 路径；
- wrapper 能记录 proposal/effective 与部分 rejection/event diagnostics；
- assignment training facade 返回 empty infos，proper-time-limit fact 没有进入 HARL bad mask。

### 25.2 目标

**Status:** `[FROZEN-TARGET-NOT-IMPLEMENTED]`

Phase A 必须定义单一高层 default-off profile，并使 scenario parse、apply、runtime manifest、
checkpoint 和 playback 使用同一 resolved identity。

训练正确性必须至少记录：

- assignment tick count；
- per-robot decision count；
- DVM sample count；
- skipped actor/minibatch update count；
- claim/continue/switch proposal count；
- accepted/rejected component count；
- rejection reason；
- component size；
- ownership transfer count；
- local cost before/after；
- `NEEDS_ASSIGNMENT` / `WAITING_FOR_TASK` duration；
- idle-with-available-task；
- failed-pair count；
- `TEAM_INFEASIBLE` count；
- termination reason；
- proposal/effective mismatch；
- nondecision factor-identity assertion；
- team reward reducer/broadcast equality；
- pre-reset generation/consume-once assertion。

论文分析可在 Phase D/E 增加分阶段等待时间、local-set size 分布、pair/component margin 和
baseline fairness 指标；这些不能替代训练正确性日志。

---

## 26. Baseline fairness boundary

### 26.1 所有方法共享

**Status:** `[FROZEN-TARGET-NOT-IMPLEMENTED]`

- 同一 scenario；
- 同一 robot model；
- 同一 task set；
- 同一 low-level control；
- 同一 success/failure detection；
- 同一 path-valid/cost input；
- 同一 episode termination；
- 最低 ownership uniqueness 与 safety constraints；
- 相同 evaluation budget 和 metrics。

### 26.2 不无条件共享

以下是本文方法机制，不能默认赠予所有 baseline：

- 完整 lifecycle observation；
- event-gated local Top-K；
- transfer-component resolver；
- DVM actor update；
- 完整 failed-pair-aware mask；
- 受约束 preemption；
- 本文 component objective。

### 26.3 Adapter evidence

**Status:** `[IMPLEMENTATION-EVIDENCE-TBD]`

具体 baseline adapter 只能在完成以下工作后冻结：

- baseline inventory；
- literature/method audit；
- 每个 baseline 原始 decision mechanism 审核。

本文不预先宣称所有 baseline 使用相同 event gating 或本文 resolver。

---

## 27. 参数、证据与消融边界

接口语义已冻结不等于数值已确定。`[NUMERIC-TBD]` 不阻碍 Phase A 建立 typed interface，
但当前文档不写推荐数值。

| Contract / parameter | Status | Owning phase | Validation |
|---|---|---|---|
| `top_k_tasks_per_robot` | `[NUMERIC-TBD]` | B/E | ablation |
| `local_robot_cap` | `[NUMERIC-TBD]` | A/B | overflow test |
| `local_task_cap` | `[NUMERIC-TBD]` | A/B | overflow test |
| `pair_abs_threshold` | `[NUMERIC-TBD]` | B/E | ablation |
| `pair_rel_threshold` | `[NUMERIC-TBD]` | B/E | ablation |
| `component_abs_threshold` | `[NUMERIC-TBD]` | B/E | ablation |
| `component_rel_threshold` | `[NUMERIC-TBD]` | B/E | ablation |
| `transfer_penalty` | `[NUMERIC-TBD]` | B/E | ablation |
| `rejection_penalty_scale` | `[NUMERIC-TBD]` | D/E | ablation |
| `alignment_time_constant` | `[NUMERIC-TBD]` | A/B/E | estimator validation + ablation |
| `assignment_retry_cadence` | `[NUMERIC-TBD]` | A/B | deterministic retry test |
| real navigation estimator | `[IMPLEMENTATION-EVIDENCE-TBD]` | B0/B | interface validation |
| real alignment estimator | `[IMPLEMENTATION-EVIDENCE-TBD]` | B0/B | interface validation |
| baseline adapters | `[IMPLEMENTATION-EVIDENCE-TBD]` | after inventory | fairness review |

cap overflow behavior不是 numeric TBD：它已冻结为不能静默破坏 closure/atomicity，
必须 fail-closed 或进入禁用额外 preemption 的显式安全模式。

---

## 28. Phase A–E implementation route

路线与 Phase 10A 保持一致。

### Phase A — Pure interface / identity / diagnostics

**Status:** `[FROZEN-TARGET-NOT-IMPLEMENTED]`

- 新高层 default-off profile；
- typed event/fact/cost/local-set/DVM/component DTO；
- generation identity；
- scenario parse/apply；
- checkpoint v2/v3 dispatcher；
- structured diagnostics；
- team reward contract config/assertions；
- 不改变 runtime behavior；
- 证明 feature-off identity。

### Phase B0 — Pre-reset facts / lifecycle transition

**Status:** `[FROZEN-TARGET-NOT-IMPLEMENTED]`

- pre-reset environment hook；
- terminal pair failure；
- release；
- `NEEDS_ASSIGNMENT`；
- unavailable/recovery；
- `TEAM_INFEASIBLE`；
- termination-reason data model；
- consume-once transition facts。

### Phase B — Event-gated local MRTA / resolver

**Status:** `[FROZEN-TARGET-NOT-IMPLEMENTED]`

- event seeds；
- local set；
- owner expansion；
- overlap merge；
- Top-K；
- path-valid；
- local action mask；
- DVM sidecar；
- staged atomic component resolver；
- deterministic smoke only；
- 不训练。

### Phase C — Repo-local HAPPO update

**Status:** `[FROZEN-TARGET-NOT-IMPLEMENTED]`

- buffer DVM；
- valid-only collect/policy sampling；
- actor loss/entropy；
- valid-only rollout advantage statistics；
- zero/singleton handling；
- nondecision factor identity；
- exact skip semantics；
- synthetic tests；
- installed HARL 不修改。

### Phase D — Reward / formal termination / metrics

**Status:** `[FROZEN-TARGET-NOT-IMPLEMENTED]`

- explicit team mean reducer；
- component rejection penalty；
- formal termination；
- proper-time-limit / bad-mask；
- metrics and diagnostics。

### Phase E — Training / ablation

**Status:** `[FROZEN-TARGET-NOT-IMPLEMENTED]`

只有 A–D gate 全部通过后才允许：

- tiny smoke；
- training；
- playback attribution；
- ablation；
- multi-seed evaluation。

本文不授权任何 Phase A 代码修改，更不授权 Phase E。

---

## 29. Required implementation verification gates

**Status:** `[FROZEN-TARGET-NOT-IMPLEMENTED]`

后续至少需要：

- feature-off 与当前 HEAD 的 observation/mask/action/log-prob/effective/reward/
  GAE/return/factor/RNG/side-effect identity；
- one decision-valid robot + other nondecision robots；
- multiple decision-valid robots in one step；
- singleton semantic action gives DVM=0；
- rejected proposal remains in proposal action buffer；
- effective assignment never overwrites PPO action；
- nondecision factor ratio exactly 1；
- zero-valid actor and minibatch exact skip；
- singleton finite raw advantage；
- component whole accept/whole reject；
- overlap merge and one-round owner expansion；
- cap overflow fail-closed/safe-mode；
- `TEAM_INFEASIBLE` continuation and termination；
- pre-reset consume-once and generation mismatch failure；
- old v2 semantic mismatch rejection in feature-on profile；
- legacy v2 acceptance in unchanged feature-off profile。

本轮没有执行这些测试；它们属于后续实现 gate。

---

## 30. Quick recovery checklist

1. 阅读 [`AGENTS.md`](../AGENTS.md)；
2. 阅读最新 [`TASK_PROGRESS.md`](../TASK_PROGRESS.md)；
3. 阅读 [Phase 10A HAPPO/HARL audit](../20260724/PHASE10A_EVENT_GATED_LOCAL_MRTA_HAPPO_INTERFACE_AUDIT.md)；
4. 阅读本文 V2；
5. targeted V2 review 生成后必须阅读；当前 candidate 尚无该 review 文件，以最新
   `TASK_PROGRESS.md` 提供的路径为准，不使用虚构链接；
6. 执行：

   ```text
   git rev-parse HEAD
   git status --short --untracked-files=all
   ```

7. 确认
   `C:\isaacenvs\isaac45_harl\Lib\site-packages\harl`
   只读；
8. 确认最新 technical next step 是否仍为 Phase A；
9. 未经用户确认，不得训练、修改 resolver runtime behavior，或把 old checkpoint
   加载到新 profile。

本文中的 “next technical phase” 是 2026-07-27 快照；后续始终以最新
`TASK_PROGRESS.md` 为准。

---

## 31. Glossary

| Term | Frozen meaning |
|---|---|
| proposal | policy 在一个真实 assignment decision 上提出的 global task ID |
| effective assignment | resolver 校验、仲裁并原子提交后交给 controller 的 assignment |
| current task | event-updated baseline 中 robot 仍合法持有的未完成 task |
| ownership | task 到唯一 current owner 的映射 |
| claim | idle/`NEEDS_ASSIGNMENT` robot 对 unowned task 的 proposal |
| continue | executing robot 选择 current global task ID |
| switch | executing robot 选择另一个合法 global task ID |
| preemption | active owned task 经 pair/component gates 改变 owner |
| release | forced lifecycle fact 解除 current ownership |
| failed pair | `failed_pair[i,j]`；本 episode 内 robot-task structural terminal incompatibility |
| `TEAM_INFEASIBLE` | 所有 robot 对该 task 均为 failed pair 的 task terminal state |
| assignment tick | lifecycle/opportunity 触发的同步 high-level decision boundary |
| physical control step | 固定 physics/control/reward/rollout 时间步 |
| decision-valid mask / DVM | agent-specific real-assignment-choice indicator |
| transfer component | baseline/proposal ownership graph 的 connected atomic validation unit |
| event-updated baseline | forced lifecycle facts 应用后的 baseline assignment `a0` |
| nominal pair cost | expected navigation time + expected alignment time |
| Top-K | 每个 local robot 的 nominal-cost task candidate set |
| `n_valid_actor_samples` | 一个 actor rollout 中 DVM=true 的 sample 数；不得简称为 Top-K 的 K |

全文统一使用 `failed pair`、`TEAM_INFEASIBLE`、proposal、effective assignment；
不以 `terminal failed` 或小写 team-infeasible 代替正式 state/field。

---

## 32. Review finding resolution matrix

`RESOLVED` 只表示本文已修正文档契约，不代表代码实现、数值冻结、实验验证或 GPT/user
最终批准。

| Finding | Severity | V2 section | Resolution |
|---|---|---|---|
| DR-01 | CRITICAL | Nominal cost contract | RESOLVED |
| DR-02 | HIGH | 固定物理步、事件和唯一 strict order | RESOLVED |
| DR-03 | HIGH | Local set、Top-K 与 observation | RESOLVED |
| DR-04 | HIGH | Action semantics 与 decision-valid mask | RESOLVED |
| DR-05 | HIGH | Assignment-tick retry；Resolver；Transfer component | RESOLVED |
| DR-06 | HIGH | Pair gate、component objective 与 transfer counting | RESOLVED |
| DR-07 | HIGH | Authoritative pre-reset transition facts | RESOLVED |
| DR-08 | HIGH | Default-off direct bypass；Checkpoint semantic contract | RESOLVED |
| DR-09 | HIGH | Metadata；状态标签；当前代码能力快照 | RESOLVED |
| DR-10 | HIGH | Baseline fairness boundary | RESOLVED |
| DR-11 | MEDIUM | 研究范围与论文边界 | RESOLVED |
| DR-12 | MEDIUM | Task 与 Robot lifecycle | RESOLVED |
| DR-13 | MEDIUM | Failed pair；Episode termination 与指标 | RESOLVED |
| DR-14 | MEDIUM | Rejection reward | RESOLVED |
| DR-15 | MEDIUM | Team reward contract | RESOLVED |
| DR-16 | MEDIUM | HAPPO decision-valid contract | RESOLVED |
| DR-17 | MEDIUM | Zero-valid 与 singleton advantage | RESOLVED |
| DR-18 | MEDIUM | Phase A–E implementation route | RESOLVED |
| DR-19 | MEDIUM | 参数、证据与消融边界 | RESOLVED |
| DR-20 | MEDIUM | Authority、证据与 Quick recovery checklist | RESOLVED |
| DR-21 | LOW | 标题层级与 Glossary | RESOLVED |

```text
resolution count:
  RESOLVED:           21
  PARTIALLY-RESOLVED: 0
  NOT-APPLICABLE:     0

unresolved CRITICAL/HIGH documentation findings:
  0
```

`[NUMERIC-TBD]` 和 `[IMPLEMENTATION-EVIDENCE-TBD]` 是被明确管理的后续参数/证据工作，
不是未解决的 review finding。

---

## 33. Candidate approval gate

```text
revision classification:
  REVISION-COMPLETE-AWAITING-GPT-REVIEW

document status:
  AUTHORITATIVE-DESIGN-CANDIDATE

implementation authorization:
  none

enter Phase A:
  no -- wait for targeted GPT re-review and user confirmation

overall Phase 10A classification:
  RUNNER-CHANGES-REQUIRED

architecture route:
  Phase A → Phase B0 → Phase B → Phase C → Phase D → Phase E
```

targeted GPT review 应重点核对：

- nominal cost 无 `lambda_align`；
- canonical event order 与 terminal branch；
- semantic singleton DVM；
- rejected SWITCH/CLAIM fallback；
- transfer closure、pair gate 与 component objective；
- team reward mean-then-penalty order；
- zero/singleton/factor identity；
- pre-reset DTO；
- feature-off direct bypass；
- checkpoint v2/v3 dispatch；
- baseline fairness；
- 21 finding resolution matrix。

在 targeted review 和用户确认前，不进入 Phase A，不运行训练、playback/evaluation，
不加载 checkpoint，不修改 installed HARL，不 commit。
