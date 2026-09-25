# Phase 10A — Event-Gated Local MRTA Design Backup 独立技术审核

- 审核日期：2026-07-27
- 被审核文档：`Lifecycle_Aware_Event_Gated_Local_MRTA_Design_Backup_20260724.md`
- 当前代码基线：`e3febe417c5323e28ceb9e256ba71dcd44f3c457`
- 审核性质：文档与当前仓库事实一致性审核
- 最终分类：`REVISION-REQUIRED`
- Findings：21 项（`CRITICAL 1 / HIGH 9 / MEDIUM 10 / LOW 1`）
- 原备忘录是否修改：否
- 运行行为是否修改：否
- Isaac Sim / training / playback / evaluation / checkpoint load：均未执行
- Commit：无

---

## 1. Executive summary

该备忘录是一份有价值的短摘要，已经抓住 Phase 10A 的主方向：

- 固定物理 step 与 event-gated assignment tick；
- global fixed-width observation 与 global task ID；
- proposal / effective assignment 分离；
- lifecycle failure、failed pair 与 `TEAM_INFEASIBLE`；
- actor 使用 `decision_valid_mask`，critic 保留固定步 GAE；
- HAPPO nondecision ratio identity；
- Phase A / B0 / B / C / D / E 的总体实施顺序；
- 第一篇固定 cardinality 与后续 variable-cardinality 工作的基本隔离。

但它目前不能作为唯一、权威、可直接执行的长期恢复文档。审核发现一个会直接改变方法目标的
`CRITICAL` 错误，以及多项会导致错误实现的 `HIGH` 缺口：

1. §4 将已冻结的
   `navigation_cost + alignment_cost`
   改成了
   `navigation_cost + lambda_align * alignment_cost`；
2. 没有完整冻结 event/non-event 边界和 canonical strict order；
3. local-set 的 seed、owner closure、第二层 owner lock 和 global-ID 规则不自足；
4. 没有明确解决 executing current/noop 的同义动作，也没有冻结 semantic-singleton
   `decision_valid_mask=0`；
5. resolver fallback、完整 component、staging 与 atomic accept/reject 规则不完整；
6. pair-level preemption gate、component objective 和 transfer penalty 的层次没有分开；
7. pre-reset auto-reset 事实被弱化为“可能”，DTO 字段和 terminal DVM 规则不完整；
8. default-off 没有写出“直接旁路旧 runner/trainer 路径”及 RNG、v2、side-effect identity；
9. 当前实现、冻结目标、数值待定和后续工作使用同一种现在时，且“已冻结”来源与
   Phase 10A / `TASK_PROGRESS.md` 仍存在 provenance 冲突；
10. baseline 公平性边界缺失。

因此：

```text
REVISION-REQUIRED
```

不是 `BLOCKED-BY-INCONSISTENT-CONTRACTS`：现有代码结构与目标方法没有发现新的架构冲突，
上述问题可以通过文档修订和已经规划的 repo-local Phase A–D 改造解决。

仓库层面的下一实施阶段仍然是 Phase A，但不建议把当前备忘录直接作为 Phase A 的实现授权或
唯一规格。建议先生成修订版、同步其 contract provenance，并做一次针对性 GPT 复核；通过后再
进入 Phase A。无需重新讨论已经锁定的整体方法原则。

---

## 2. 审核范围、方法与证据优先级

### 2.1 证据优先级

本审核使用：

```text
当前 HEAD 的实际代码
>
当前安装环境实际 import 的 HARL 实现
>
Phase 10A 接口审计
>
当前 TASK_PROGRESS.md
>
被审核备忘录
>
更早的历史报告
```

目标设计本身按本次审核指令中已经冻结的 A–S 契约核对；审核者没有重新设计该方法，也没有将
建议方案写成当前实现。

### 2.2 已核对的当前代码入口

仓库代码：

- `scan_mobile_manipulator_env.py`
- `assignment_harl_wrapper.py`
- `assignment_lifecycle_observation.py`
- `assignment_lifecycle_resolver.py`
- `assignment_lifecycle_resolver_runtime.py`
- `assignment_harl_training.py`
- `assignment_checkpoint_contract.py`
- `assignment_lifecycle_training_contract.py`
- `scenario_config.py`
- `play_assignment.py`
- assignment playback diagnostics 与 logger 路径

当前环境实际 import 的 HARL：

- `C:\isaacenvs\isaac45_harl\Lib\site-packages\harl\runners\on_policy_base_runner.py`
- `C:\isaacenvs\isaac45_harl\Lib\site-packages\harl\runners\on_policy_ha_runner.py`
- `C:\isaacenvs\isaac45_harl\Lib\site-packages\harl\algorithms\actors\happo.py`
- `C:\isaacenvs\isaac45_harl\Lib\site-packages\harl\common\buffers\on_policy_actor_buffer.py`
- `C:\isaacenvs\isaac45_harl\Lib\site-packages\harl\common\buffers\on_policy_critic_buffer_ep.py`
- `C:\isaacenvs\isaac45_harl\Lib\site-packages\harl\common\valuenorm.py`

文档：

- 被审核备忘录；
- `PHASE10A_EVENT_GATED_LOCAL_MRTA_HAPPO_INTERFACE_AUDIT.md`；
- 当前 `TASK_PROGRESS.md`；
- Phase 9G lifecycle resolver、observation/mask、proposal/effective、
  checkpoint 与训练验证报告。

### 2.3 静态边界

本次只做代码阅读、import 路径确认和静态调用链审核。没有：

- 构造 Isaac 环境；
- 启动 AppLauncher / Isaac Sim；
- 启动训练、playback 或 evaluation；
- 加载或修改 checkpoint；
- 修改 installed HARL；
- 修改 environment、wrapper、resolver、reward、buffer、trainer、runner、YAML 或测试；
- 修改被审核备忘录；
- stage 或 commit。

审核开始时，被审核备忘录的 SHA-256 为：

```text
A9DD70253EC78575C14394B4F566505A5C85F0BFD0440D76E2F44403E55A42FC
```

---

## 3. 总体判断

| 用途 | 判断 | 原因 |
|---|---|---|
| 简短方法方向摘要 | 有条件可用 | 主方向和阶段路线大体正确 |
| Phase 10A 的速查卡 | 有条件可用 | 需要同时打开 Phase 10A 报告核查细节 |
| 唯一实现规格 | 不可用 | cost、event order、DVM、component、pre-reset、default-off 等契约不完整 |
| 唯一长期恢复文档 | 不可用 | 当前/目标语态、证据来源、HEAD/status、恢复入口不足 |
| 直接交给新 Codex/GPT 窗口 | 不建议 | 容易把冻结目标误读成当前实现，并遗漏关键禁止项 |
| 生成修订版后再用 | 建议 | 现有结构可保留，主要需要精确补契约和 provenance |

---

## 4. 与 Phase 10A 一致、应保留的内容

以下内容技术方向正确，不应在修订中被重新设计：

1. **研究边界基本正确。**
   §1 正确把第一篇限制为 lifecycle-aware dynamic MRTA，允许对不同固定 `(M,N)`
   分别训练和评估，不声称单 checkpoint 任意 cardinality；viewpoint generation、
   NBV、planner、local avoidance 和 reconstruction model 不属于当前贡献。

2. **固定物理步骨架正确。**
   §2 和 §6 保留固定 step execution、rollout 和标准 GAE，而不是把环境重构成异步
   event-only step。

3. **proposal/effective 主链正确。**
   §2 明确 policy proposal 先进入 resolver，PPO 保存 proposal，controller 消费
   effective assignment；§10 禁止 effective 覆盖 proposal。

4. **resolver 的禁止项正确。**
   不搜索最优 matching、不枚举 proposal subset、不替 rejected robot 生成第二候选。

5. **failed-pair 主方向正确。**
   终端 alignment failure 才写 episode-permanent failed pair；导航内部恢复、短暂阻塞和
   avoidance 不自动升级为永久 pair failure。

6. **`TEAM_INFEASIBLE` 和指标方向正确。**
   全队 pair failure 后移出候选，raw completion 分母不删除 infeasible task，并补充
   team-infeasible 与 feasible-task completion 指标。

7. **reward 主原则正确。**
   accepted proposal 不额外奖励；第一版 rejection 是统一小额 penalty；每个 rejected
   component 只扣一次；新 profile 才使用 mean-reduced team scalar broadcast，
   legacy 保持旧行为。

8. **HAPPO 主原则正确。**
   critic 使用固定物理步；actor loss、entropy 和 advantage statistics 使用 DVM；
   rejected proposal 仍是有效 actor action；nondecision sequential ratio 为 1；
   zero-valid 不能用 zero-loss optimizer step 冒充 skip。

9. **pre-reset 的方向正确。**
   备忘录已经意识到 reset 后状态不能解释上一 episode，并要求 immutable、带 generation、
   consume-once 的事实载体。

10. **阶段依赖总体正确。**
    Phase A → B0 → B → C → D → E 的主顺序正确；尤其没有把 terminal failure、
    `NEEDS_ASSIGNMENT` 和 `TEAM_INFEASIBLE` 全部错误推迟到 Phase D。

11. **installed HARL 边界正确。**
    §10 明确禁止直接修改 installed HARL，符合 Phase 10A 的 repo-local
    subclass/shim/registry 路线。

---

## 5. 与当前代码事实一致的内容

### 5.1 当前真实数据流

当前 wrapper 的实际顺序是：

```text
HARL all-agent actions
→ decode proposal
→ current lifecycle resolver
→ effective assignment
→ controller/env actions
→ DirectMARLEnv.step
→ wrapper post-step diagnostics/snapshot
```

证据：

- `assignment_harl_wrapper.py:396-415`：
  proposal 经 resolver 得到 effective，再转换成 controller action；
- `assignment_harl_wrapper.py:440-449`：
  `last_assignment_proposal` 和 `last_effective_assignment` 独立保存；
- `assignment_harl_wrapper.py:2445-2481`：
  lifecycle payload 同时记录 proposal、effective、accepted/rejected reason；
- current actor buffer 仍直接保存 HARL 采样 action，因此没有被 effective assignment 覆盖。

备忘录 §2、§8 对这部分的摘要是准确的。

### 5.2 当前 reward 事实

备忘录 §8 正确写出 EP critic 当前读取 `rewards[:,0]`，但 §5 尚未完整解释其前置事实：

- `scan_mobile_manipulator_env.py:2985-2996`：
  每个机器人 reward 是 shared global/time 项与 own/duplicate/reach/action-rate 个体项组合；
- `assignment_harl_wrapper.py:2199-2254`：
  wrapper 还加入 per-robot 和 broadcast shaping；
- `assignment_harl_wrapper.py:2422-2423`：
  对外 shape 为 `[E,M,1]`；
- installed `on_policy_base_runner.py:506-514`：
  EP critic buffer 插入 `rewards[:,0]`，不是显式 reducer。

所以当前不是“明确的 shared team reward contract”；memo 将 mean+broadcast 限定为
“新 profile”是正确方向，但仍需更精确地标为未实现设计。

### 5.3 当前 actor / buffer / HAPPO 事实

- installed `on_policy_base_runner.py:334-370` 每个物理 step 循环所有 actor，
  为每个 actor 采样 action 和 log-prob；
- repo-local `assignment_harl_training.py:598-605` 只检查 mask 后调用
  `super().collect(step)`，没有 event-gated collect；
- installed actor buffer 有 obs、RNN state、available actions、action、
  log-prob、masks、active masks 和训练期 factor，没有 DVM；
- installed HAPPO `happo.py:76-99` 用 active mask 做 policy reduction，
  每个 minibatch执行 backward/optimizer step；
- `happo.py:118-155` 只对全 inactive actor 做早退，并使用 active mask
  normalization；
- installed `on_policy_ha_runner.py:17-24,116-127` 的 factor 为 `[T,E,1]`，
  当前无条件乘每个 actor 的 raw new/old ratio。

备忘录 §8 对“必须修改 runner/buffer/HAPPO/factor”的判断正确。

### 5.4 当前 mask / resolver 事实

- `assignment_lifecycle_observation.py:659-697` 无条件开放 noop；
- `assignment_lifecycle_observation.py:717-742` 对 executing robot 只开放 current task；
- 所以当前 executing robot 同时有 current 和 noop 两个 raw action；
- `assignment_lifecycle_resolver.py:712-746` 把两者都解释为 CONTINUE；
- `assignment_lifecycle_resolver.py:747-765` 拒绝所有 switch；
- `_start_claim` 在 `assignment_lifecycle_resolver.py:767-802` 直接更新 ownership，
  当前没有 staged transfer component。

备忘录 §8 对“current/noop 同义、resolver 无 switch/component”的当前事实是准确的。

### 5.5 当前 environment / lifecycle / cost 事实

- `scan_mobile_manipulator_env.py:1695-1703` 当前 `cost_matrix` 是 scanner-to-viewpoint
  Euclidean distance；
- `scan_mobile_manipulator_env.py:1704-1720` task 只有 unassigned/completed，
  robot status 每次全部是 IDLE placeholder；
- `scan_mobile_manipulator_env.py:2930-2983` completion 仍由 candidate/dwell/covered
  proxy 更新；
- `scan_mobile_manipulator_env.py:3012-3020` termination 只有 all-covered 与 timeout。

因此 memo §3–§4 描述的是目标状态，不是当前已实现能力。

### 5.6 当前 auto-reset 事实

`DirectMARLEnv.step` 当前确定会在返回前 reset done env：

- `direct_marl_env.py:389-396` 先求 done/reward，再对 reset ids 调 `_reset_idx`；
- `direct_marl_env.py:403-405` reset 后重新生成 observation；
- wrapper 在 `assignment_harl_wrapper.py:417-420` 的 `env.step` 返回之后才读取
  `post_step_problem`。

因此 memo §7 的“可能自动 reset”不够准确；这是当前确定存在的时序风险。

### 5.7 当前 checkpoint/config 事实

- `assignment_checkpoint_contract.py:39` 当前 manifest 为
  `assignment_checkpoint_contract_v2`；
- v2 已绑定当前 profile/schema/mask/resolver/policy-sequence 等 Contract C 字段，
  但没有 event-gated local-set、DVM、factor identity、team reducer、
  component objective 等新语义；
- `scenario_config.py:1146-1173` 能验证 lifecycle profile metadata；
- `scenario_config.py:479-495` 的 `apply_scenario_config_to_env_cfg` 只传播
  `ENV_CFG_SCENARIO_ATTRS`，当前 Phase 10A 已指出 lifecycle propagation gap。

memo §9–§10 正确要求新 semantic fingerprint 和禁止新 profile 静默加载旧 v2，
但 default-off 的精确旁路契约仍缺失。

---

## 6. 容易被误解为“已经实现”的表述

下列表述使用现在时，但当前代码只实现了 Phase 9G Contract C prototype 或更早行为：

| Memo 位置 | 表述 | 当前事实 |
|---|---|---|
| 20–23 | event 触发局部 tick、Top-K、owner expansion | 当前没有 event-gated collect/local-set/Top-K |
| 24–27 | executing 可 SWITCH、resolver 做 component/cost | current resolver 拒绝所有 switch，没有 component |
| 32–38 | 完整 lifecycle 与 TEAM_INFEASIBLE | 当前 env task 仅 unassigned/completed，robot status 是 IDLE placeholder |
| 42–49 | expected-time cost 和 component comparison | 当前只有 Euclidean distance，无 pair-specific time/path-valid interface |
| 53–56 | component-once rejection 与 mean team reward | 尚未实现；当前 EP critic 读取 robot 0 |
| 62–67 | DVM valid-only HAPPO update | 当前 buffer/runner/HAPPO 无 DVM |
| 71 | immutable pre-reset facts | 当前尚无 authoritative pre-reset transition DTO/hook |

修订版应给全文增加统一状态标签：

```text
[CURRENT-CODE]
[FROZEN-TARGET-NOT-IMPLEMENTED]
[NUMERIC-TBD]
[IMPLEMENTATION-EVIDENCE-TBD]
[DEFERRED-SECOND-WORK]
```

---

## 7. A–S 覆盖结论

| 审核项 | 结论 | 主要 finding |
|---|---|---|
| A 研究范围 | 基本一致，边界不完全自足 | DR-11 |
| B 事件决策 | 核心方向正确，缺关键否定契约 | DR-02 |
| C lifecycle | 目标方向正确，taxonomy/当前事实不足 | DR-12 |
| D local set | 过度压缩，不能独立恢复算法 | DR-03 |
| E cost | 存在公式错误与接口缺口 | DR-01、DR-06 |
| F action/DVM | 主映射正确，semantic alias 未冻结 | DR-04 |
| G proposal/effective/resolver | 主链正确，fallback/atomicity 不完整 | DR-05 |
| H component/preemption | pair gate 与 component objective 未分层 | DR-06 |
| I failed pair/termination | 核心正确，taxonomy 与继续条件不完整 | DR-13 |
| J rejection reward | 主原则正确，reason taxonomy 不足 | DR-14 |
| K team reward | 新 profile 方向正确，当前/目标和运算顺序不足 | DR-15 |
| L HAPPO DVM | 主原则正确，训练边界不完整 | DR-16 |
| M zero/singleton | 主分支正确，统计和 skip identity 不完整 | DR-17 |
| N pre-reset | 方向正确，当前事实和 DTO 不完整 | DR-07 |
| O strict order | 未集中冻结 canonical order | DR-02 |
| P checkpoint/default-off | feature-on 禁令正确，feature-off identity 不完整 | DR-08 |
| Q Phase A–E | 总体依赖正确，阶段 bullet 有遗漏 | DR-18 |
| R baseline fairness | 缺失 | DR-10 |
| S 参数/消融 | 未写死数值正确，但分类和清单不完整 | DR-19 |

---

## 8. 逐条 findings

### DR-01 — CRITICAL — Cost 公式引入未授权的 `lambda_align`

- 文档位置：§4，第 42 行。
- 原问题：
  `c_ij = navigation_cost_ij + lambda_align * alignment_cost_ij`
  偏离已冻结的共同预计时间契约
  `navigation_cost[i,j] + alignment_cost[i,j]`。
  额外权重会改变 Top-K、pair eligibility、component objective 和最终 assignment，
  因而会改变方法和论文结论。
- 证据：
  Phase 10A 报告 `1204-1224` 明确要求两项为 estimated-time、pair-specific 直接和；
  current env `1695-1697` 仍只是 Euclidean prototype，并不能为该权重提供实现依据。
- 建议修订：

  ```text
  nominal_cost[i,j] =
      navigation_cost[i,j] + alignment_cost[i,j]
  ```

  两项先在 estimator/interface 内换算到统一时间单位。第一版可用
  `alignment_time_constant[i]` 广播为 `[M,N]`；不要在 objective 中另加
  `lambda_align`。若未来研究加权目标，必须明确降级为新的未冻结消融，不得混入当前方法。

### DR-02 — HIGH — Event/non-event 边界和 strict order 不完整

- 文档位置：§2、§7、§9。
- 原问题：
  备忘录没有明确写出正常 `NAVIGATING/ALIGNING` progress 不触发 proposal，
  assignment tick 不是异步 env step 或 SMDP 重构，非局部正常机器人不重新决策；
  也没有在一处冻结唯一 canonical order。
- 代码证据：
  current installed runner 仍在 `on_policy_base_runner.py:334-370`
  每物理 step 采样所有 actor，所以这里必须明确标成目标行为，而不能依赖读者推断。
- 建议修订：

  ```text
  execution result
  → authoritative pre-reset facts
  → lifecycle state update
  → completion/release/failed-pair/availability write
  → termination determination
  → same-step event collection
  → local-set construction/overlap merge
  → tick-time cost refresh
  → per-robot Top-K
  → global obs/local action mask/DVM snapshot
  → one proposal per local decision-valid robot
  → component validation
  → atomic effective commit
  → next physical step
  ```

  terminal 分支只记录 facts，`DVM=0`，不得对 reset 后状态采样 proposal。

### DR-03 — HIGH — Local-set / owner expansion 规则不足以独立恢复

- 文档位置：§2，第 21–23 行。
- 原问题：
  缺少 seed 的精确定义、occupied task 的处理、第一层 owner 的 Top-K、第二层 owner lock、
  overlap merge 后重算范围和 global-ID no-repacking。
- 证据：
  Phase 10A 报告 `1170-1183` 已确认当前没有 local-set builder；因此备忘录不能依赖现有代码
  补足算法。
- 建议修订：

  1. seeds = event robots ∪ `NEEDS_ASSIGNMENT` robots；
  2. 每个 local robot 按 nominal pair cost 生成自己的小 Top-K；
  3. Top-K 阶段不能直接排除已占有任务；
  4. current task 无条件 union 为 CONTINUE；
  5. Top-K 中 occupied task 的 owner 加入 local robot set；
  6. 新加入 owner 也生成自己的 Top-K；
  7. 只做这一轮 owner expansion；
  8. 第二层候选的集合外 owner 不再加入，其任务本 tick 不可抢占；
  9. 重叠集合合并后重新计算 cost/candidates；
  10. 始终输出 global task ID，不进行 local observation/task repacking。

### DR-04 — HIGH — Semantic legal action 与 DVM 的定义不完整

- 文档位置：§2 第 24 行；§6 第 63–65 行；§8 第 79 行。
- 原问题：
  memo 识别 current/noop 是同一 CONTINUE 语义，却没有冻结新 profile 的修正。
  如果用 raw available-action count 推断 DVM，executing robot 可能因 current+noop 两个编码
  被误判为有真实选择。
- 代码证据：
  `assignment_lifecycle_observation.py:659-697` 总是开放 noop；
  `717-742` 还开放 executing current；
  `assignment_lifecycle_resolver.py:712-746` 把两者都解释为 CONTINUE。
- 建议修订：

  - executing noop 在新 profile 下必须 mask；
  - current task ID 是唯一 CONTINUE 编码；
  - 其他合法 global task ID 才是 SWITCH；
  - idle/`NEEDS_ASSIGNMENT` 的 task ID 是 CLAIM，noop 是 IDLE；
  - action dimension 可保持 `N+1`；
  - DVM 根据 semantic legal choices 与 lifecycle tick eligibility 计算；
  - 只有一个 semantic action 时 `DVM=0`；
  - rejected proposal 的 DVM 仍为 1；
  - `active_masks` 与 DVM 必须独立。

### DR-05 — HIGH — Resolver fallback、component closure 和 atomicity 不完整

- 文档位置：§2 第 25–29 行；§4 第 44–49 行。
- 原问题：
  “rejection 后保持 `NEEDS_ASSIGNMENT`”被写成无条件规则，但执行中机器人被拒绝 switch 时
  应回到 event-updated baseline/current task；只有 idle/unassigned fallback 才保持
  `NEEDS_ASSIGNMENT`/noop。文档还缺少被抢占 owner 的同 component 新去向、CONTINUE
  可被完整改善 component 覆盖、staging 和全接收/全拒绝。
- 代码证据：
  current resolver `676-765` 直接回退 current 并拒绝 switch；
  `_start_claim` `767-802` 直接 mutation，尚无 component staging。
- 建议修订：

  - failure/release 已使机器人无 assignment 时，rejection fallback 为
    `NEEDS_ASSIGNMENT`/noop；
  - 正在执行且 baseline task 仍合法时，rejected SWITCH fallback 为 baseline/current，
    不强制转成 `NEEDS_ASSIGNMENT`；
  - 不允许同 tick 第二次采样；
  - 每个被抢占 owner 必须在同一 component 有合法新去向；
  - 完整合法且明显改善的 component 可覆盖 owner 的 CONTINUE；
  - 任何 member 不完整/不合法/收益不足时 component 整体拒绝；
  - 所有 ownership/state mutation 先 staging，验证成功后一次性 commit。

### DR-06 — HIGH — Pair gate、component objective 与 transfer penalty 未分层

- 文档位置：§4、§11。
- 原问题：
  “assigned count 增加时硬约束通过即可接受”没有明确仍需所有 preemption pair
  eligibility；`N_transfer` 被定义，但 transfer penalty 没有进入明确公式，也没有写明
  不参与 Top-K。
- 证据：
  Phase 10A 报告 §13–§14 将 nominal pair cost、preemption eligibility 和 full component
  comparison 分为不同接口；当前代码尚无这些层次，不能依赖实现纠正歧义。
- 建议修订：

  1. Top-K 只按 nominal pair cost 排序；
  2. 每个 active-owner preemption 先过 pair absolute + relative eligibility；
  3. 完整 component 再比较 event-updated baseline 与 full proposal；
  4. assigned count 增加只在 hard constraints、pair gates 和 closure 全通过后接受；
  5. assigned count 相同时，用含
     `transfer_penalty * N_owner_changes`
     的 component cost 做 absolute + relative improvement；
  6. active proposal 减少 assigned count 时拒绝；
  7. unowned claim = 0 transfer；
  8. forced failure release 后 claim = 0 active-preemption transfer；
  9. bilateral swap = 2 owner changes。

### DR-07 — HIGH — Pre-reset 当前事实和 DTO 契约不完整

- 文档位置：§7。
- 原问题：
  “DirectMARLEnv 可能……自动 reset”与当前代码事实不符；当前 done env 确实在返回 wrapper
  前 reset。memo 也没有列全 authoritative DTO 字段、consume-once assertion 和 terminal
  DVM 规则。
- 代码证据：
  `direct_marl_env.py:389-405` 在 step return 前 `_reset_idx` 并重建 obs；
  wrapper `417-420` 返回后才读 post problem。
  当前 lifecycle decision snapshot 不是 authoritative pre-reset transition DTO。
- 建议修订：

  DTO 至少包含：

  - episode generation；
  - transition generation；
  - terminated / truncated；
  - termination reason；
  - completion / release / failure facts；
  - coverage / task / ownership before reset；
  - availability/recovery facts；
  - consume-once token。

  明确 Phase A 只定义 DTO 与断言，Phase B0 才接 environment pre-reset hook；
  terminal env 本 transition 的 DVM 必须为 0。

### DR-08 — HIGH — Default-off identity 没有冻结 direct bypass

- 文档位置：§9、§10、§12。
- 原问题：
  “每 phase 证明 default-off identity”太抽象。没有写出 feature-off 必须直接旁路旧实现，
  不能使用“新 trainer + DVM 全 1”模拟 legacy；也没有列 RNG、minibatch、factor、returns、
  v2 manifest 和文件副作用的 identity。
- 代码证据：
  repo-local runner `assignment_harl_training.py:598-605` 当前直接调用 installed collect；
  checkpoint v2 在 `assignment_checkpoint_contract.py:39`；
  v2 manifest 当前不含 event/DVM/factor/team-reducer/component 新语义。
- 建议修订：

  - feature-off 直接 dispatch 当前 legacy runner/trainer/resolver 路径；
  - 保持 obs/shared/action/mask、action/log-prob、factor、GAE/return、RNG path、
    logging/file side effect 和 checkpoint v2 精确不变；
  - old v2 仅在同一 feature-off profile 下继续可用；
  - feature-on 使用新 semantic contract/fingerprint；
  - 即使 shape 不变，v2 在 event-gated normal playback/evaluation/continuation 下也必须拒绝；
  - installed HARL 只读，修改放在 repo-local subclass/shim/registry。

### DR-09 — HIGH — 当前/目标语态和 contract provenance 存在冲突

- 文档位置：元数据第 5–8 行；§2–§8；§12 第 110 行。
- 原问题：
  正文用现在时陈述尚未实现的 Top-K、switch/component、team reward、DVM 和 pre-reset hook。
  第 110 行又称 team reducer、singleton fallback、pre-reset facts 已冻结，但 Phase 10A
  报告 `1898-1902` 与当前 `TASK_PROGRESS.md:143-145` 仍记录“实现前窄范围接口确认”。
  按本审核的证据优先级，这是仓库内 provenance 不一致。
- 建议修订：

  - 使用状态标签区分 current、frozen target、numeric TBD、implementation evidence TBD、
    deferred work；
  - 为三项冻结决策记录决定来源、日期和 supersedes 关系；
  - 同步 `TASK_PROGRESS.md` 后再将 memo 标记为 reviewed authoritative；
  - 在版本元数据中记录 `verified_against_head` 和 review report。

### DR-10 — HIGH — Baseline 公平性边界缺失

- 文档位置：§1、§11。
- 原问题：
  只写“baseline adapter 细节待定”是必要但不充分；没有冻结哪些基础条件所有方法共享，
  也没有冻结哪些本文机制不能无条件赠予 baseline。
- 实现风险：
  当前 wrapper `404-414` 统一把 proposal 送入 resolver。未来若直接复用该入口，
  baseline 可能无意获得本文完整 transfer resolver，或因缺少最小 ownership safety
  被不公平削弱。
- 建议修订：

  所有方法共享：

  - scenario、robots、task set；
  - 底层控制；
  - success/failure detection；
  - path-valid/cost interface；
  - termination；
  - 最低 ownership uniqueness/safety。

  不无条件共享：

  - 本文完整 lifecycle observation；
  - event-gated Top-K；
  - transfer-component resolver；
  - DVM actor update；
  - 完整 failed-pair-aware mask；
  - 本文受约束 preemption。

  具体 baseline 和 adapter 只在 baseline inventory 与文献审计后冻结。

### DR-11 — MEDIUM — 第一篇/第二篇和 execution progress 边界仍不完全自足

- 文档位置：§1、§10。
- 原问题：
  fixed-cardinality 限定正确，但没有明写 variable-cardinality 是后续独立工作；
  “第一篇完成前不要扩展到 variable-cardinality Transformer”可能被读成 Transformer
  已选型。execution “progress”也可能被读成普通 progress 触发 tick。
- 建议修订：
  第二篇才研究 variable-cardinality/generalization；Transformer、Set Encoder、GNN
  都只是未来候选，当前未选型。planner、controller、avoidance 和 viewpoint generation
  均非当前贡献。普通执行 progress 只用于控制/诊断，不构成 lifecycle assignment event。

### DR-12 — MEDIUM — Lifecycle taxonomy、alignment success 和当前 proxy 未区分

- 文档位置：§3。
- 原问题：
  主链正确，但没有把 `TEAM_INFEASIBLE` 明确作为 task terminal state 纳入 taxonomy，
  没有补齐 robot wait/release/`NEEDS_ASSIGNMENT`/unavailable/recovered，
  也没有明写 alignment success 才完成。
- 代码证据：
  current env `1704-1720` 只有 unassigned/completed 与 IDLE placeholder；
  completion 仍由 `2930-2983` candidate+dwell proxy 产生。
- 建议修订：
  用 target-state 与 robot-state 两张表；明确“到达 → ALIGNING → alignment success →
  COMPLETED”，当前 coverage/dwell 仅为 prototype execution signal，不是目标 authoritative
  lifecycle 已实现的证据。

### DR-13 — MEDIUM — Failed-pair / termination taxonomy 仍缺 `TIME_LIMIT`

- 文档位置：§3、§5、§10。
- 原问题：
  没有明写 `TEAM_INFEASIBLE` 同时从 action mask 移除；单个 task infeasible 后继续条件只可
  推断；termination reason 缺 `TIME_LIMIT`。
- 代码证据：
  current `_get_dones` `3012-3020` 只有 all-covered/timeout，没有 team-infeasible reason。
- 建议修订：
  明列：

  - `ALL_TASKS_COMPLETED`；
  - `NO_FEASIBLE_TASKS_REMAIN`；
  - `TIME_LIMIT`；
  - 单个 task infeasible 且仍有可执行 task 时 episode 继续；
  - infeasible task 从 candidate 与 action mask 移除；
  - feasible completion 是附加指标，不替代全任务分母 raw completion。

### DR-14 — MEDIUM — Rejection penalty 的 reason taxonomy 不完整

- 文档位置：§5、§11。
- 原问题：
  “策略原因”没有可执行分类。缺少 hard-invalid 应由 mask 阻止、snapshot 后系统状态失效
  不惩罚策略、第一版不使用连续拒绝递增 penalty。
- 代码证据：
  当前 reward 路径没有 component rejection penalty；现有 resolver reason 包含多类系统和
  proposal 原因，未来不能全部等价处罚。
- 建议修订：
  定义 penalized / non-penalized rejection reason 表；每个 policy-caused rejected component
  扣一次、不得按 member 数放大；accepted 无 bonus；scale 留待 ablation；第一版不做
  progressive penalty。

### DR-15 — MEDIUM — Team reward 的当前/目标和运算顺序不够精确

- 文档位置：§5、§8。
- 原问题：
  “原始 per-agent reward”不清楚是 env base reward 还是 wrapper final reward；
  mean 与 component penalty 的先后也不明确，可能使 penalty 被 `1/M` 稀释或按机器人重复。
- 代码证据：
  env reward 是 shared+individual；wrapper 再 shaping 并输出 `[E,M,1]`；
  EP critic 当前只取 robot 0。
- 建议修订为 current/target 两栏，并冻结公式，例如：

  ```text
  base_team[e] = mean_i(wrapper_final_reward[e,i])
  team[e] = base_team[e]
            - rejection_scale * policy_rejected_component_count[e]
  learner_reward[e,i] = team[e]  # broadcast
  ```

  per-agent decomposition 仅供诊断。该公式只属于新 profile，legacy 直接旁路；明确尚未实现。

### DR-16 — MEDIUM — HAPPO valid-only 边界没有写全

- 文档位置：§6、§10。
- 原问题：
  核心方向正确，但没有明写 DVM 不进入 GAE、return 或 ValueNorm；
  policy/entropy denominator、zero-valid minibatch、processed-update logging 和 same-step
  per-agent DVM/factor shape 也不完整。
- 代码证据：
  installed critic buffer `compute_returns` 使用全部 fixed-step rewards；
  installed HAPPO 只按 active mask reduction；factor 当前 `[T,E,1]` 并乘 raw ratio。
- 建议修订：

  - GAE、return、critic、ValueNorm 保持全部有效物理 step；
  - actor mask = `active_mask * DVM`，policy 与 entropy 除以真实有效样本数；
  - minibatch 无有效 row 时不 forward/backward/step；
  - actor rollout 全无有效 sample 时整个 actor update skip；
  - 同一 step 不同 agent 可有不同 DVM；
  - 每 actor buffer 保存自己的 `[T+1,E,1]` DVM；
  - factor 仍为 `[T,E,1]`，不新增 agent 维；
  - 只 mask 最终 loss 不足；
  - factor 优先用 `torch.where(DVM, raw_ratio, 1)`，避免 `0 * NaN`。

### DR-17 — MEDIUM — Zero/singleton 统计细节和 `K` 术语冲突

- 文档位置：§6 第 66 行；§11 第 106 行。
- 原问题：
  §6 的 `K` 表示 actor rollout valid sample count，§11 的 `K` 表示 Top-K，
  容易混淆；“population-stat”没有显式写 `unbiased=False`；K=0 只写 optimizer skip，
  没有冻结参数、optimizer state 和 factor identity。
- 代码证据：
  installed `torch_nanstd` 默认 unbiased behavior 对 singleton 有 NaN 风险；
  current HAPPO 每 minibatch optimizer step。
- 建议修订：

  ```text
  n_valid_actor_samples == 0:
      skip actor train/evaluate/backward/optimizer
      parameters, optimizer state, factor unchanged

  n_valid_actor_samples == 1:
      use finite raw advantage

  n_valid_actor_samples >= 2:
      valid-only mean/std, unbiased=False
      nonfinite or too-small std -> raw advantage
  ```

  Top-K 参数统一写成 `top_k_tasks_per_robot`。

### DR-18 — MEDIUM — Phase A–E 主顺序正确，但阶段 bullet 仍有遗漏

- 文档位置：§9。
- 原问题：
  依赖顺序通过，但 B0 未显式列 lifecycle transition 与 termination-reason data model；
  C 未显式列 zero/singleton 与 valid-count-safe minibatch；D 的 proper-time-limit/bad-mask
  只在主 memo 中不够突出。
- 建议修订：
  保持 A→B0→B→C→D→E，不移动 failure/TI 到 D；补全：

  - A：typed DTO/event/cost/local-set/DVM/component + semantic checkpoint + diagnostics；
  - B0：pre-reset hook、state transition、terminal facts、termination reason data model；
  - B：local-set/Top-K/mask/DVM sidecar/atomic resolver，deterministic smoke only；
  - C：buffer/runner/HAPPO、zero/singleton/factor identity；
  - D：explicit team reward、rejection、formal termination、proper-time-limit/bad-mask；
  - E：全部 gate 后训练与消融。

### DR-19 — MEDIUM — 参数与消融清单混合了数值、接口和证据问题

- 文档位置：§11。
- 原问题：
  未区分 local robot/task caps、pair/component 两组 abs/relative threshold，
  缺 alignment constant 与 event retry cadence；“真实 estimator”和 baseline adapter
  不是普通数值参数。local cap 数值可待定，但 overflow semantics 不能待定到运行时静默截断。
- 建议修订：
  使用表格列：

  - semantic contract；
  - config key；
  - numeric status；
  - implementation evidence status；
  - owning phase；
  - test/ablation。

  至少分别列出：
  `top_k_tasks_per_robot`、`local_robot_cap`、`local_task_cap`、
  `pair_abs/rel_threshold`、`component_abs/rel_threshold`、
  `transfer_penalty`、`rejection_penalty_scale`、
  `alignment_time_constant`、`event_retry_cadence`。
  cap overflow 必须 fail-closed 或显式 fallback，不能破坏 owner closure/atomicity。

### DR-20 — MEDIUM — 快速恢复与 provenance 不足

- 文档位置：元数据、§8、§12。
- 原问题：
  没有列精确的 `AGENTS.md`、Phase 10A、`TASK_PROGRESS.md`、关键代码入口、
  installed HARL read-only 路径、evidence priority、review HEAD、git status 检查和 review
  状态。当前 memo 本身仍是 untracked 文件，不能称为由 HEAD 可恢复的仓库权威资料。
- 建议修订：
  添加：

  - `verified_against_head`、`last_reviewed_date`、review report；
  - 必读路径；
  - authority order；
  - environment/wrapper/resolver/training/checkpoint 入口；
  - installed HARL 只读位置；
  - 新窗口先执行 `git status` / `git rev-parse HEAD`；
  - “下一步 Phase A”是带日期的快照，始终以最新 `TASK_PROGRESS.md` 为准。

### DR-21 — LOW — 标题层级和术语需要统一

- 文档位置：标题及全文。
- 原问题：
  第 3 行副标题使用 `##`，与正式章节同级；`failed_pair` / `failed-pair` /
  `terminal failed`、`TEAM_INFEASIBLE` / `team-infeasible` 混用；§6 与 §11 重用 `K`。
- 建议修订：
  将副标题改为普通说明或 blockquote；增加短 glossary；enum/state 使用代码样式；
  统一 proposal、effective assignment、ownership、release、failed pair、
  `TEAM_INFEASIBLE` 等术语。

---

## 9. 是否适合作为长期恢复文档

### 9.1 当前版本

不适合作为唯一长期恢复文档，原因不是篇幅短，而是：

- 有一个方法目标公式错误；
- 多个关键契约只能从 Phase 10A 报告或用户指令补全；
- 当前代码事实与目标设计没有逐段标签；
- 缺少 authority/provenance/HEAD/status；
- “已冻结”的来源与当前高优先级文档未完全同步。

### 9.2 修订后的预期定位

建议保留其“短备忘录”定位，不必复制整份 Phase 10A 报告。修订版应做到：

1. 自足地冻结会改变行为的算法规则；
2. 用状态标签区分 current/target/TBD/deferred；
3. 对复杂实现细节链接 Phase 10A 和代码入口；
4. 给出版本、HEAD、review 和最新 `TASK_PROGRESS.md` 路由；
5. 明确它是设计权威摘要，不是实验结果或 current implementation claim。

---

## 10. 是否适合直接交给新的 Codex/GPT 窗口

当前不建议单独交付。若必须使用，应同时提供：

1. 相关 `AGENTS.md`；
2. 最新 `TASK_PROGRESS.md`；
3. `PHASE10A_EVENT_GATED_LOCAL_MRTA_HAPPO_INTERFACE_AUDIT.md`；
4. 本审核报告；
5. 当前 `git rev-parse HEAD` 与 `git status --short --untracked-files=all`；
6. 明确指示“当前代码优先于 memo；memo 尚未修订，不授权实现”。

修订版通过再次复核后，才适合成为新窗口的入口文档。

---

## 11. 推荐修订范围

建议修改原文件，但不在本次第一轮审核中修改。推荐按以下章节生成修订版：

1. 元数据与状态图例；
2. §1 第一篇/第二篇与 execution interface 边界；
3. §2 event/non-event、local-set 和 canonical strict order；
4. §3 lifecycle/failed-pair/termination taxonomy；
5. §4 nominal cost、pair gate、component objective、transfer counting；
6. §5 current reward facts、新 profile team formula、rejection taxonomy；
7. §6 semantic action/DVM、GAE/ValueNorm boundary、zero/singleton、factor；
8. §7 authoritative pre-reset DTO；
9. §8 current-code evidence table；
10. §9 default-off direct bypass 与完整 Phase A–E gate；
11. 新增 baseline fairness boundary；
12. §11 参数/证据/消融表；
13. §12 recovery paths、HEAD、authority 和 review provenance；
14. glossary 与术语统一。

修订后建议进行一次窄范围 GPT 再审核，重点检查：

- cost equation；
- event order 与 terminal branch；
- semantic singleton DVM；
- resolver fallback / component atomicity；
- transfer objective；
- pre-reset DTO；
- default-off direct bypass；
- team reward 运算顺序；
- baseline fairness matrix；
- parameter table。

---

## 12. 推荐下一步与 Phase A 决策

### 12.1 是否建议立即进入 Phase A

```text
NO — 不以当前未修订 memo 作为权威规格直接进入 Phase A。
```

这不是对 Phase 10A 技术路线的否定。仓库的推荐实现阶段仍是 Phase A，且没有发现新的
architectural blocker。进入顺序应为：

```text
生成 memo 修订版
→ 同步 contract provenance / TASK_PROGRESS
→ 针对性 GPT 复核
→ 用户确认
→ Phase A only
```

### 12.2 是否需要重新讨论方法

不需要 broad method redesign。只需修正文档错误、补全已冻结规则，并把 team reward、
singleton 和 pre-reset authority 的决定来源在仓库文档中同步一致。

---

## 13. 最终分类

```text
REVISION-REQUIRED
```

```text
finding total:
  21

severity distribution:
  CRITICAL: 1
  HIGH:     9
  MEDIUM:   10
  LOW:      1
  NOTE:     0

modify original memo:
  yes, in a later explicitly authorized revision turn

original memo modified in this review:
  no

recommended sections:
  metadata/status labels
  research and second-work boundary
  event order and local set
  lifecycle and termination
  cost and component objective
  action/DVM and resolver fallback
  reward and HAPPO
  pre-reset DTO
  checkpoint/default-off
  baseline fairness
  parameters/ablation
  recovery/provenance

GPT re-review:
  yes

enter Phase A now:
  no, first revise and re-review the memo

repository implementation route after review:
  Phase A remains the next technical phase
```

