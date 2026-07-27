# Phase 10A — Event-Gated Local MRTA 与 HAPPO/HARL 接口兼容性审计

## 0. 审计范围、证据边界与仓库状态

审计日期：2026-07-24
审计基线：

```text
HEAD:
  e3febe417c5323e28ceb9e256ba71dcd44f3c457

latest commits:
  e3febe41 docs(assignment): validate multi-condition late-training regression
  9d31b15f add deterministic baseline and cyclic pose-slot profiles
  167bafaa docs(assignment): validate 100k best-final attribution comparison

installed HARL:
  harl==1.0.0
  C:\isaacenvs\isaac45_harl\Lib\site-packages\harl

Python:
  C:\isaacenvs\isaac45_harl\python.exe
```

本报告以当前 HEAD 的代码和当前 Conda 环境内实际 import 到的 HARL
实现为准。历史 Phase 9G 报告只用于理解既有契约；当报告与当前代码
不一致时，以当前代码为准。

本阶段只进行了：

- 代码和 AgentRead 文档阅读；
- Git、Python/HARL 路径和静态调用链检查；
- 不构造 Isaac 环境的纯张量级行为核对；
- 本审计报告和 `TASK_PROGRESS.md` 的文档更新。

本阶段没有：

- 修改 environment、wrapper、resolver、reward、buffer、trainer、runner、
  playback、checkpoint 或 YAML 的运行行为；
- 启动 AppLauncher、Isaac Sim、训练、playback 或 evaluation；
- 加载或修改 checkpoint 权重；
- 修改 installed HARL；
- stage 或 commit。

文中行号对应上述 HEAD 和当前安装的 HARL 1.0.0；后续代码变更后行号可能漂移。

---

## 1. Executive summary

### 1.1 最终分类

```text
RUNNER-CHANGES-REQUIRED
```

目标方法与现有系统不存在根本架构冲突，但不能只改环境或 action mask。
要完整实现锁定的训练语义，至少需要 repo-local 的：

1. event/lifecycle/cost/local-set 接口；
2. local action mask 与 staged atomic transfer resolver；
3. actor buffer 的 `decision_valid_mask`；
4. runner 的 decision-valid subset sampling；
5. HAPPO actor loss、entropy、advantage normalization 和 sequential factor
   的 decision-valid 处理；
6. 新 profile/checkpoint semantic contract；
7. 结构化正确性日志。

### 1.2 当前已经可复用的结构

- 固定物理 step rollout 和标准 GAE；
- EP centralized critic 的全物理步更新骨架；
- 全局固定 task 顺序、全局 task ID 和 `Discrete(N+1)` 动作；
- historical `available_actions` 在 actor buffer 中保存并在 PPO 更新时重放；
- proposal 与 effective assignment 的实际数据流分离；
- controller 只消费 effective assignment；
- HAPPO sequential factor 的 `[T,E,1]` 形状足以支持同一时刻不同 agent
  拥有不同 decision-valid 状态；
- 严格 checkpoint manifest/fingerprint 基础设施；
- default-off 的 legacy profile 边界。

### 1.3 最高风险发现

1. **当前 EP critic 不是明确的 team-reward reducer。** Wrapper 输出
   `[E,M,1]` 的“共享项 + 个体项”混合 reward，但 installed HARL EP
   runner 只写入 `rewards[:, 0]`。因此 GAE、return、ValueNorm 和三个
   actor 的共享 advantage 实际都由 `robot_0` reward 驱动。

2. **当前 HAPPO factor 会被非决策样本污染。** Actor 更新后，runner
   对全部 rollout 样本计算 `new/old` ratio 并乘入 factor；active mask
   不屏蔽该 ratio。只在最终 policy loss 外乘 `decision_valid_mask`
   不能修复这个问题。

3. **严格 event 顺序不能只在 wrapper post-step 实现。** Isaac
   `DirectMARLEnv` 在 `_get_dones()` 和 `_get_rewards()` 后、返回 wrapper
   之前自动 reset done env。Wrapper 随后读到的 `post_step_problem` 已可能
   是 reset 后状态，终止帧的 completion/failure/release facts 会丢失。

4. **当前 executing action mask 有两个 raw action、一个真实语义。**
   Contract C 对执行中的机器人同时允许 current task 和 noop，而 resolver
   把两者都解释为 CONTINUE。不能简单用
   `available_actions.sum(-1) > 1` 推导 decision-valid。

5. **zero/singleton valid sample 需要显式处理。** 当前 policy/entropy
   reduction 对 mask sum 没有零分母保护；当前 `torch_nanstd` 默认
   `unbiased=True`，只有一个有效 advantage 时会产生 NaN。

6. **checkpoint 当前未冻结新方法的核心语义。** 即使 observation/action
   维度不变，v2 manifest 也无法识别 event tick、local set、component、
   decision masking 和 non-decision factor identity 的差异。

### 1.4 核心判断

| 分类 | 判断 |
|---|---|
| 已由当前代码支持 | 固定 step、global IDs、global fixed-width actor rows、historical action mask replay、proposal/effective 分离、effective→controller、标准 GAE/ValueNorm 骨架 |
| 可局部修改支持 | event DTO、local set/Top-K、cost/path-valid 接口、local mask、failure/task state、atomic component resolver、日志、config/checkpoint schema |
| 需要较深 runner/trainer 修改 | 仅 valid row 采样、DVM buffer、actor/entropy reduction、valid-only advantage stats、zero-valid skip、sequential factor ratio=1 |
| 当前证据不足 | 真正的 navigation/alignment 预计时间来源、执行层终端姿态失败/robot fail-recover 接口、最终训练稳定性与性能 |

---

## 2. 当前 environment → HAPPO 完整数据流

### 2.1 启动和类注册

```text
scripts/reinforcement_learning/harl/train.py
  -> import installed HARL RUNNER_REGISTRY
  -> register_assignment_harl_runner(...)
  -> RUNNER_REGISTRY["happo"] = AssignmentOnPolicyHARunner
  -> runner.run()

AssignmentOnPolicyHARunner
  -> repo-local AssignmentIsaacLabEnv
  -> repo-local AssignmentHarlWrapper
  -> installed HAPPO actors
  -> installed OnPolicyActorBuffer per actor
  -> installed VCritic
  -> installed OnPolicyCriticBufferEP
  -> installed ValueNorm
```

关键位置：

- `scripts/reinforcement_learning/harl/train.py:168-177,195-197,270,278`
- `assignment_harl_training.py:251-319,383-565,740-748`
- `assignment_lifecycle_training_contract.py:150-218`

当前 `lifecycle_contract_c` 的正式训练 guard 限定：

- algorithm = HAPPO；
- state type = EP；
- `share_param=False`；
- feed-forward actor；
- state-dict checkpoint。

### 2.2 一个物理 step 的实际调用链

```text
installed OnPolicyBaseRunner.run
  1. collect(step)
     - 对每个 agent 调 actor.get_actions
     - 使用 actor_buffer.obs[t] 与 available_actions[t]
     - 得到 raw proposal action 与 rollout log-prob
     - centralized critic 对 shared_obs[t] 估值

  2. AssignmentIsaacLabEnv.step(actions)
     -> AssignmentHarlWrapper.step(actions)
        a. 重新读取 pre_step_problem
        b. 重新生成 pre_step_available_actions
        c. raw action 解码为 assignment_proposal
        d. resolver.resolve_pre_step(proposal)
        e. 得到 effective_assignment
        f. effective_assignment -> 9D controller action
        g. raw DirectMARLEnv.step
        h. 读取 post_step_problem
        i. reward stack/shaping
        j. resolver.observe_post_step(completion/budget release/reset)
        k. 生成下一状态 obs/shared_obs/available_actions

  3. AssignmentIsaacLabEnv
     - 扁平化少量 scalar log
     - 丢弃原 structured info，返回空 infos

  4. installed OnPolicyBaseRunner.insert
     - actor buffer 写入步骤 1 的 raw action/log-prob
     - EP critic buffer 写入 share_obs[:,0] 与 rewards[:,0]

  5. rollout 完成后
     - compute_returns/GAE
     - OnPolicyHARunner.train 按 agent 顺序更新 actor/factor
     - VCritic.train
```

关键位置：

- installed `harl/runners/on_policy_base_runner.py:189-314,334-398,400-542`
- `assignment_harl_training.py:311-319,350-365,598-605`
- `assignment_harl_wrapper.py:396-495`
- `assignment_controller.py:39-111`

### 2.3 当前时序与目标严格顺序的关系

对于未终止 env，当前“post-step facts 在下一次 actor collect 前进入 snapshot”
的跨步结构可以复用：

```text
physical step t result
  -> wrapper post-step lifecycle update
  -> next obs/mask
  -> runner collect proposal for step t+1
  -> resolver pre-step atomic decision
  -> physical step t+1
```

但它尚不满足目标契约，原因是：

- 没有 lifecycle event collector；
- 没有 `NEEDS_ASSIGNMENT`；
- 没有 local-set/one-round owner expansion/overlap merge；
- 没有 tick-time cost refresh 和 Top-K；
- 没有 `decision_valid_mask`；
- resolver 不是 transfer-component resolver；
- terminal frame facts 可能被 DirectMARLEnv auto-reset 覆盖；
- wrapper 在 actor 已经按上一份 mask 采样后又重建 pre-step mask，
  当前没有强断言两份 mask 属于同一 snapshot generation。

Isaac 的真实 auto-reset 顺序位于：

- `source/isaaclab/isaaclab/envs/direct_marl_env.py:361-415`

其中 `_get_dones()` 在 389 行，`_get_rewards()` 在 391 行，自动 reset 在
393-396 行，obs 重新生成在 403-405 行。因此，未来必须在 environment
内部或一个 pre-reset transition hook 中暴露终止帧 facts，不能只依赖
wrapper 在 `_env.step()` 返回后重新读取 problem。相同边界还会使 wrapper
终止步 reward shaping 所用的 `post_step_problem["viewpoints_covered"]`
可能来自 reset 后 episode；base env reward 是 reset 前计算的，但 wrapper
的 post-step adjustment 需要单独防止这种跨 episode 混读。

---

## 3. A — Reward 语义审计

### 3.1 当前 reward 不是完全共享 reward

`scan_mobile_manipulator_env.py::_get_rewards`
（`2985-3010`）为每个 agent 返回一个 `[E]` tensor：

```text
robot_i reward =
    shared global coverage gain
  + individual own coverage gain_i
  - individual duplicate scan penalty_i
  - individual reach violation penalty_i
  - individual action-rate penalty_i
  - shared time penalty
```

所以当前语义是：

```text
共享项 + 每机器人个体项的组合
```

不是完全共享 team reward，也不是完全独立 reward。

### 3.2 Wrapper 是否复制或变换 reward

`AssignmentHarlWrapper._stack_rewards`
（`assignment_harl_wrapper.py:2422-2423`）按 agent 顺序直接 stack：

```text
[E] per agent -> [E,M,1]
```

它不复制、不平均 base reward。

`_compute_assignment_reward_decomposition`
（`2199-2258`）再加入：

- per-robot repeated-assignment penalty；
- broadcast 到所有机器人的 global no-progress penalty；
- per-robot selected path-cost penalty。

最终仍是 `[E,M,1]`，机器人列通常不保证相等。

### 3.3 Actor 和 centralized critic 实际接收什么

Actor 不直接接收 reward。当前 EP 路径先生成单一
`advantages [T,E,1]`，随后同一份 advantage clone 传给三个独立 actor。

Centralized critic 的关键实际行为在 installed
`harl/runners/on_policy_base_runner.py:506-514`：

```python
self.critic_buffer.insert(
    share_obs[:, 0],
    ...,
    rewards[:, 0],
    ...
)
```

因此：

- critic 只接收 `robot_0` reward；
- GAE/return 只基于 `robot_0` reward；
- 三个 actor 的 EP advantage 都基于该同一 return；
- 这不是明确的 team mean/sum reducer。

只有当 wrapper 的 M 列 reward 完全相同时，它才偶然等价于 shared team reward。

### 3.4 ValueNorm 使用什么

标准 GAE 在 critic buffer 中先用 reward 和 denormalized value 计算 return。
ValueNorm 的统计更新发生在
`harl/algorithms/critics/v_critic.py:90-95`：

```text
value_normalizer.update(return_batch)
normalize(return_batch)
```

所以 ValueNorm 跟踪的是 EP critic return；在当前代码中，该 return 最终来自
`rewards[:,0]`，并覆盖全部有效物理 step，而不是只覆盖 assignment decision。

### 3.5 rejection penalty 的接口可行性

Tensor shape 层面，wrapper 可以对某个机器人写入 `[E,M,1]` 的独立 penalty。
但在当前 EP runner 下：

- 对 `robot_0` 的 penalty 会进入 critic/actor target；
- 对 `robot_1/2` 的独立 penalty 会被 EP critic 静默忽略。

因此在进入训练前必须冻结一个明确 reward contract。若保持本项目当前的
EP/shared-advantage 方向，建议：

```text
rejected_component_count[e]
  -> 每个 rejected component 只计一次
  -> team_penalty[e] = -scale * rejected_component_count[e]
  -> broadcast 为 [E,M,1] 的相同值
```

不能按 component 内 rejected robot 数量重复相加，否则 component size 越大
惩罚被重复计算。

另一可行路径是在 repo-local runner 中明确配置并记录 team reducer
（例如 mean/sum/authoritative team scalar），再把单一 team reward 写入 EP
critic buffer。若目标是每机器人真正不同的 return/credit，则需要 FP 或
per-agent critic-return 管线，超出当前锁定的 EP 方案。

### 3.6 Reward 审计结论

```text
当前环境输出:
  shared + individual combination

当前 EP learner 实际目标:
  robot_0 reward stream

目标方法进入训练前必须解决:
  explicit team reward reduction/broadcast contract
```

---

## 4. B — 当前 actor 调用时序

### 4.1 所有 actor 是否每 step 被调用

是。

Installed `OnPolicyBaseRunner.collect`
（`on_policy_base_runner.py:334-370`）每个物理 step 执行：

```python
for agent_id in range(self.num_agents):
    actor[agent_id].get_actions(...)
```

每个 actor 又一次性处理全部 E 个 rollout thread。因此当前每个物理 step：

- 强制调用全部 actor；
- 为每个 robot/env row 采样 action；
- 为每个 row 计算 rollout log-prob。

Repo-local `AssignmentOnPolicyHARunner.collect`
（`assignment_harl_training.py:598-605`）只检查 action-mask buffer 后调用
`super().collect(step)`，没有 assignment decision gate。

### 4.2 当前 mask 的语义

- `masks`：RNN reset/episode boundary；
- `active_masks`：HARL 的 alive/dead mask；
- `available_actions`：Categorical support mask；
- 当前没有 agent mask 或 `decision_valid_mask`。

`active_masks` 在 installed runner
`on_policy_base_runner.py:446-466` 由 dones 构造，并在整个 env done 时重新置 1。
它不参与 collect，也不表示“该 agent 此时是否做 assignment 决策”。

### 4.3 唯一合法动作是否仍采样

是。

调用链：

```text
OnPolicyBase.get_actions
  -> StochasticPolicy.forward
  -> ACTLayer.forward
  -> Categorical
```

`harl/models/base/distributions.py:51-55` 只把 unavailable logits 设为
`-1e10`；`harl/models/base/act.py:44-82` 即使只剩一个合法 action，仍构造
分布、sample/mode 并计算 log-prob。纯张量核对显示该情况通常得到
log-prob 0、entropy -0，但仍发生 policy forward 和 buffer 写入。

### 4.4 Proposal 是否被替换

Actor raw action 在进入 wrapper 后解码为 proposal。Resolver 另产 effective，
controller 只消费 effective。Runner 在 step 后仍把 collect 得到的原 raw
action 写入 actor buffer。

所以当前：

```text
actor buffer action = proposal raw action
effective assignment 不会覆盖 PPO action
rejected proposal 仍留在 actor buffer
```

### 4.5 “仅 decision-valid robot 真正采样”所需位置

至少需要修改：

1. `AssignmentHarlWrapper`/facade：暴露当前 state-aligned
   `[E,M,1] decision_valid_mask` 和 forced action；
2. repo-local `AssignmentOnPolicyHARunner.warmup/collect/insert`：
   只对 DVM=true rows 调 `get_actions`；
3. repo-local actor buffer：按 snapshot 对齐保存 DVM；
4. resolver 调用边界：明确 nondecision placeholder 不是一个新的策略 proposal；
5. playback：enabled profile 下镜像相同 gating。

推荐 nondecision row：

- executing：直接填 current global task ID，语义为 forced CONTINUE；
- idle/non-seed：填 raw noop `N`；
- rollout log-prob 填 0；
- feed-forward RNN state保持不变；
- diagnostics 使用显式 `NO_PROPOSAL`/`decision_valid=false`，避免把 forced
  placeholder 计入 claim/continue proposal 统计。

当前 lifecycle contract 已限定 feed-forward，这使按 row subset forward
可控。若以后开放 recurrent actor，必须另行定义非决策期间 hidden-state
是否推进，不能沿用本次结论。

---

## 5. C — Rollout buffer 字段和 shape

记：

```text
T = episode_length
E = n_rollout_threads
M = num_agents
O_i = actor i observation dimension
S = shared observation dimension
A = N + 1
R = recurrent_n
H = actor hidden size
Hc = critic hidden size
```

### 5.1 当前 per-actor buffer

Installed `OnPolicyActorBuffer`
（`harl/common/buffers/on_policy_actor_buffer.py:10-185`）每个 actor 一份：

| 字段 | Shape | 当前语义 |
|---|---:|---|
| `obs` | `[T+1,E,O_i]` | actor observation |
| `rnn_states` | `[T+1,E,R,H]` | actor recurrent state |
| `available_actions` | `[T+1,E,A]` | historical Categorical support |
| `actions` | `[T,E,1]` | raw proposal action |
| `action_log_probs` | `[T,E,1]` | rollout proposal log-prob |
| `masks` | `[T+1,E,1]` | RNN/episode reset |
| `active_masks` | `[T+1,E,1]` | alive/dead |
| `factor` | `None`，训练时 `[T,E,1]` | HAPPO sequential correction |

Actor buffer 不保存 reward、shared observation、value prediction 或 return。

### 5.2 当前 EP critic buffer

Installed `OnPolicyCriticBufferEP`
（`harl/common/buffers/on_policy_critic_buffer_ep.py:9-252`）：

| 字段 | Shape |
|---|---:|
| `share_obs` | `[T+1,E,S]` |
| `rnn_states_critic` | `[T+1,E,R,Hc]` |
| `value_preds` | `[T+1,E,1]` |
| `returns` | `[T+1,E,1]` |
| `rewards` | `[T,E,1]` |
| `masks` | `[T+1,E,1]` |
| `bad_masks` | `[T+1,E,1]` |

Critic buffer 不保存 action、available actions、active mask 或 factor。

### 5.3 Frozen Phase 9G-8 profile 的实例维度

对 `M=3, N=50, lifecycle_contract_c`：

```text
O_i = 1059
S   = 3183
A   = 51
raw noop = 50
decoded noop = -1
```

公式位于 `assignment_lifecycle_observation.py:745-762`：

```text
legacy actor = 100 + 3M + 16N
lifecycle actor = legacy actor + 3N
shared option A = M * lifecycle actor + 2M
```

### 5.4 新字段的推荐归属

| 候选字段 | 是否进入核心 PPO buffer | 推荐位置与 shape | 理由 |
|---|---|---|---|
| `decision_valid_mask` | **是** | 每 actor `[T+1,E,1]`，训练用 `[:-1]` | actor loss、entropy、adv stats、factor 都需要 |
| `proposal_action` | 不新增副本 | 现有 `actions [T,E,1]` | 当前 actions 已是 raw proposal，应以断言冻结语义 |
| `effective_assignment` | 否 | wrapper payload/logger，step 级 `[E,M]` | 不参与 PPO ratio，进入核心 buffer会诱发误覆盖 |
| `proposal_accepted` | 否 | wrapper payload/logger，`[E,M]` | 诊断和论文分析 |
| `rejection_reason` | 否 | wrapper payload/logger，`[E,M]` + component id | string/enum 诊断，不参与 actor gradient |

建议 DVM 与 observation/available-actions 一样使用 state alignment：

```text
reset/warmup:
  decision_valid_masks[0] = current state DVM

after env step t:
  insert next state DVM at [t+1]

actor sample at t:
  use decision_valid_masks[t]

training:
  use decision_valid_masks[:-1]

after_update:
  copy [-1] -> [0]
```

这能避免把 post-step 的 decision validity 错配给刚执行的 action。

### 5.5 Rollout buffer serialization

当前 checkpoint 不序列化 rollout buffer。`AssignmentTrainingStateManifest`
明确记录 `rollout_buffer_state_available=False`，也不保存 optimizer、RNG、
environment/resolver state。因此新增 DVM 没有旧 buffer 文件迁移问题，但必须：

- 更新 runtime buffer schema/readiness test；
- 在 checkpoint semantic contract 中冻结 DVM/trainer/factor 语义；
- 不把 fresh-rollout continuation 误称为 exact resume。

---

## 6. D — Actor loss、entropy、importance ratio

### 6.1 当前实现位置

Installed `harl/algorithms/actors/happo.py`：

- `55-69`：重新 evaluate action，计算 importance weight；
- `70-84`：PPO clipped surrogate 与 policy reduction；
- `88-99`：zero_grad/backward/optimizer step；
- `103-155`：advantage normalization、minibatch/epoch loop、日志平均。

Installed `harl/models/base/act.py:143-155`：

- Categorical entropy；
- 若传 active mask，则除以 `active_masks.sum()`。

### 6.2 DVM 应在哪里乘入

DVM 必须同时约束：

1. policy surrogate；
2. entropy reduction；
3. actor advantage normalization sample set；
4. actor ratio diagnostics；
5. HAPPO sequential factor 更新；
6. optimizer 是否执行。

推荐：

```text
loss_mask = decision_valid_mask * active_mask
```

但两个 mask 必须保持独立字段和独立日志。`active_mask` 仍表示 agent alive；
`decision_valid_mask` 表示该 alive agent 当前是否拥有真实 assignment choice。

### 6.3 有效样本归一化

Policy 和 entropy 都应按有效样本数归一化：

```text
valid_count = loss_mask.sum()
loss = masked_sum / valid_count
```

不能按 minibatch 总样本数、固定 `ppo_epoch * actor_num_mini_batch` 或
active sample 数归一化。

更稳妥的 feed-forward 实现是先选出 DVM=true flat indices，再动态组成
valid-only minibatch。若保留全样本 minibatch，则每个 minibatch 都必须：

- 检查 `valid_count > 0`；
- zero-valid minibatch 不 forward/backward/step；
- 日志除以真实 processed update 数。

### 6.4 zero-valid actor

若某 actor 在整个 rollout 中没有有效决策：

- 跳过该 actor 的 old-prob evaluation；
- 跳过 advantage normalization；
- 跳过所有 optimizer 操作；
- actor 参数和 optimizer state 均不改变；
- factor 全部保持原值；
- 记录 `actor_update_skipped_zero_valid=1`。

不能执行“零 loss 的 optimizer step”。Adam 的 momentum/weight decay 仍可能
改变参数或 optimizer state，所以这不等价于安全 skip。

### 6.5 当前 NaN/除零风险

当前实现有以下风险：

- policy reduction 除以 `active_masks.sum()`，无 zero guard；
- entropy reduction同样无 zero guard；
- `torch_nanstd(..., unbiased=True)` 在一个有效样本时分母为 0；
- 当前日志固定除以配置的更新次数，即使未来跳过 minibatch 也会失真。

建议冻结 singleton contract：

```text
K = valid advantage sample count
K = 0: skip actor update
K = 1: 不做中心化/标准化，使用 finite raw advantage
K >= 2: 仅在 valid samples 上沿用既定 mean/std 规则
```

### 6.6 为什么不能复用 active mask

典型合法状态：

```text
robot alive and executing normally:
  active_mask = 1
  decision_valid_mask = 0
```

若把两者混用：

- 正常执行机器人会被错误标为 dead；
- episode/RNN boundary 语义被污染；
- advantage stats 与 HAPPO factor 无法表达 agent-specific decision；
- 未来真正的 robot failure 与“本 step 不需要重新分配”无法区分。

因此必须新增独立 DVM。

---

## 7. E — Advantage、GAE 与 ValueNorm

### 7.1 当前 GAE

Installed runner 在
`on_policy_base_runner.py:520-542` 计算 bootstrap value，然后调用
`OnPolicyCriticBufferEP.compute_returns`。

当前配置启用：

```text
use_gae = true
use_valuenorm = true
use_proper_time_limits = true
```

GAE + ValueNorm 路径位于
`on_policy_critic_buffer_ep.py:105-127`：

```text
delta_t =
  reward_t
  + gamma * denorm(V_{t+1}) * mask_{t+1}
  - denorm(V_t)

gae_t =
  delta_t
  + gamma * lambda * mask_{t+1} * gae_{t+1}

return_t = gae_t + denorm(V_t)
```

### 7.2 当前 advantage normalization

`OnPolicyHARunner.train`
（`on_policy_ha_runner.py:26-34`）先得到一个 EP
`advantages [T,E,1]`。

每个 actor 的 `HAPPO.train`
（`happo.py:121-126`）再分别基于该 actor 的 `active_masks` 计算 mean/std。

因此当前 EP 语义是：

- raw advantage 对所有 actor 相同；
- normalization 在每个 actor 内独立执行；
- 不是所有 actor 联合 normalization；
- 当前只排除 inactive 样本，不排除 nondecision 样本。

FP 分支才在 runner 层跨 agent 联合 normalization，但当前 lifecycle
training contract 不允许 FP。

### 7.3 推荐修改

保持标准 GAE 完全不变，只改变每个 actor 的 normalization sample set：

```text
valid = decision_valid_mask[:-1] == 1
assert valid <= active
mean/std 只从 valid advantage 收集
invalid advantage 不参与 actor stats 或 actor loss
```

Critic 仍使用全部物理 step：

- reward；
- return；
- value loss；
- ValueNorm update；
- timeout/termination mask。

DVM 不应乘入 GAE、critic return 或 ValueNorm。

### 7.4 当前 proper-time-limit 缺口

`AssignmentIsaacLabEnv.step`
（`assignment_harl_training.py:315-319,333-334`）把 wrapper 原 info 替换为
空 dict。Installed runner 在
`on_policy_base_runner.py:468-490` 查找 `bad_transition`，因此 assignment
路径的 `bad_masks` 实际总为 1。

所以尽管 YAML 配置 `use_proper_time_limits=True`，当前 timeout 与 true
termination 不能通过 bad mask 正确区分。新方法引入
`ALL_TASKS_COMPLETED`/`NO_FEASIBLE_TASKS_REMAIN` 后，这个现存缺口必须在
进入训练前修复；它与 DVM 是两个独立契约。

---

## 8. F — HAPPO sequential correction factor

### 8.1 当前 agent 顺序和 factor

Installed `OnPolicyHARunner.train`
（`harl/runners/on_policy_ha_runner.py:12-132`）：

1. 初始化：

   ```text
   factor = ones([T,E,1])
   ```

2. 使用 fixed order 或 `torch.randperm(M)`；
3. 当前 agent 更新前，把累计 factor clone 到该 actor buffer；
4. 用当前、更新前 actor 参数对全部 rollout action 重新 evaluate，得到
   `old_actions_logprob`；
5. 调 `HAPPO.train`；
6. 再对全部 rollout action evaluate，得到 `new_actions_logprob`；
7. 更新：

   ```text
   factor *= aggregate(exp(new - old))
   ```

8. 下一 actor 使用更新后的累计 factor。

需要区分两类 ratio：

- HAPPO actor 内部 PPO ratio：当前 policy vs rollout 时保存的 log-prob；
- sequential factor ratio：同一 actor 本轮 optimizer 更新后 vs 更新前。

### 8.2 active mask 是否影响 factor

否。

Runner 虽把 active mask 传给 `evaluate_actions`，但它只影响返回后被丢弃的
entropy scalar，不影响 action log-prob。`factor` 更新本身没有乘 active
mask，也没有 decision mask。

### 8.3 正确的 nondecision identity

对当前 agent：

```text
raw_ratio = aggregate(exp(new_logprob - old_logprob))
d = actor_buffer[agent_id].decision_valid_masks[:-1]
effective_ratio = where(d == 1, raw_ratio, ones_like(raw_ratio))
factor = factor * effective_ratio
```

语义等价于用户锁定公式：

```text
d * ratio + (1 - d) * 1
```

实现时优先使用 `torch.where`，因为若 raw ratio 中出现 NaN，
`0 * NaN` 仍是 NaN。

更严格的实现是：

- 只对该 actor 的 DVM=true flat indices 做 pre/post `evaluate_actions`；
- 先创建全 1 的 `[T,E,1] effective_ratio`；
- 把 valid raw ratio scatter 回对应位置。

### 8.4 只在最终 actor loss 乘 mask 为什么不足

Actor 由共享网络参数处理该 actor 的所有 observation。即使 optimizer
只由 valid samples 驱动，更新后网络在 nondecision observation 上的
log-prob 也可能改变。

若 runner 仍把这些 nondecision ratio 乘入 factor，后续 agent 在相同
`(t,e)` 的 surrogate 会被一个“前一 agent 当时并未做决策”的概率变化
错误重权。这违反 event-gated causal semantics。

### 8.5 同 step 不同 agent 的 DVM

现有 factor shape `[T,E,1]` 足够。每个 actor buffer 保存自己的
`[T,E,1]` DVM；agent 按顺序更新时，用当前 agent 的 mask 选择是否改变
累计 factor。

因此不需要给 factor 新增 agent 维，也不是架构阻塞。

### 8.6 必须修改哪些层

| 层 | 必要修改 |
|---|---|
| Buffer | 保存/生成每 actor DVM |
| Runner collect/insert | 对齐 DVM，valid row sampling，forced row 填充 |
| HAPPO actor trainer | valid-only advantage/loss/entropy、zero-valid skip |
| Runner train | factor 的 nondecision ratio=1 |
| Logger | valid count、skip count、factor identity error |

只改 trainer 或只改最终 loss 都不完整。

---

## 9. G — Action mask 与 decision-valid 的关系

### 9.1 当前生成与消费路径

Legacy/base：

- `assignment_rl_interface.py:11-37`
- `problem["available_mask"]` 加一个永远可用的 noop；
- shape `[E,M,N+1]`。

Lifecycle Contract C：

- `assignment_lifecycle_observation.py:659-742`
- base target：

  ```text
  task_valid
  & available
  & feasible
  & uncovered
  ```

- idle robot 再排除 teammate owner 和 self failed/released pair；
- executing robot 只保留 current active target；
- noop 始终为 1。

消费：

- wrapper 返回 mask；
- runner warmup/insert 写 per-actor historical mask；
- collect 与 PPO evaluate 都使用对应 state 的 historical mask。

这条 historical replay 路径当前是正确且可复用的。

### 9.2 锁定条件的当前支持情况

| 约束 | 当前状态 |
|---|---|
| 全局 task validity | snapshot 有字段，但 wrapper 当前硬编码 all-ones |
| completed/unavailable | 有 covered/available filter |
| failed-pair | 只有 budget failed/released pair；不是终端姿态失败 |
| nominal path validity | 无独立 bool mask |
| local Top-K | 无 |
| current task 强制保留 | 有 |
| ownership | idle 排除 teammate-owned |
| preemption eligibility | 无；所有 switch/preemption 禁止 |
| noop | 对所有机器人永远合法 |
| robot unavailable/recovery | 无 |
| TEAM_INFEASIBLE | 无 |

Wrapper snapshot 位置：

- `assignment_harl_wrapper.py:959-988`

### 9.3 当前+noop 的语义别名

执行中的机器人当前合法 raw support 为：

```text
{current_task_id, raw_noop=N}
```

Resolver 在
`assignment_lifecycle_resolver.py:712-746` 把两者都解释为 CONTINUE。

所以 raw action count=2，但 semantic decision count=1。目标新模式下建议：

- executing noop mask 为 0；
- current task ID 唯一表示 CONTINUE；
- 其他合法 task ID 表示 SWITCH；
- noop 只用于 idle/`NEEDS_ASSIGNMENT` 的 IDLE。

Action dimension 仍可保持 `N+1`，default-off profile 保留旧 mask 精确不变。

### 9.4 DVM 的推荐定义

```text
decision_valid =
    robot active/available
  & current assignment tick
  & robot in merged local set
  & semantic_legal_action_count >= 2
  & environment not terminal
```

被 resolver 拒绝的 proposal 仍满足上述条件，所以必须保持
`decision_valid=1` 并参加 actor 训练。

### 9.5 Action mask 和 DVM 可能不一致

两者表达不同问题：

- action mask：若策略需要决策，哪些 action 合法；
- DVM：该 state 是否真的让策略做决策和承担 policy gradient。

合法状态包括：

```text
available_actions 有唯一 forced action
decision_valid = 0
```

错误状态包括：

```text
decision_valid = 1
但只有一个 semantic legal action
```

### 9.6 推荐断言

至少增加：

- shape/device/dtype/binary/finite；
- 每行至少一个合法 raw action；
- DVM 是 binary，且 `DVM <= active/available robot mask`；
- `DVM=1` 必须属于 tick/local set 且至少有两个不同 semantic choices；
- `DVM=0` 必须有唯一 forced semantic action；
- nonlocal executing 的 forced action 等于 current global task ID；
- idle nondecision 的 forced action等于 raw noop；
- current task 始终保留，即使不在 Top-K；
- target mask 是 `TopK ∪ current` 的子集；
- failed-pair/path-invalid/TEAM_INFEASIBLE task 不可选；
- 集合外 owner 的任务不可抢占；
- sampled proposal 必须在 historical available-actions 中合法；
- obs/shared/mask/DVM 使用相同 snapshot/tick generation；
- wrapper pre-step 重建 mask 必须与 runner sample 时的 mask 完全一致；
- ownership 唯一；
- component commit 全接受或全拒绝；
- terminal env 的 DVM 全 0。

---

## 10. H — Proposal 与 effective assignment 分离

### 10.1 当前代码已经保证的部分

`assignment_harl_wrapper.py:401-449`：

```text
discrete_actions
  -> assignment_proposal
  -> resolver
  -> effective_assignment
  -> controller action
```

保存变量：

```text
last_assignment_proposal
last_effective_assignment
last_assignment = effective_assignment  # 旧的模糊别名
```

Resolver pre-result：

- `assignment_lifecycle_resolver.py:115-129`
- 含 effective、accepted、rejection reason、continue/claim/switch 诊断。

Runner buffer：

- installed `on_policy_base_runner.py:493-504`
- 写入 collect 产生的原 raw `actions/action_log_probs`；
- 没有从 wrapper 读取 effective 覆盖 action。

Controller：

- `assignment_controller.py:39-111`
- 只接 effective assignment。

所以当前核心 PPO action 语义正确：

```text
PPO buffer = proposal
controller = effective
rejected proposal 不被覆盖
```

### 10.2 当前不足

- `last_assignment` 命名模糊，实际是 effective；
- structured lifecycle payload 没有进入训练 logger；
- `AssignmentIsaacLabEnv.step` 返回空 infos；
- 当前 TensorBoard scalar path 会把 tensor mean-collapse，不能保留 per-robot、
  per-component 正确性；
- proposal/effective 同时记录主要存在于 resolver optional trace 和 playback
  attribution collector，不等于训练日志已经支持。

未来必须继续禁止：

- 用 effective 回写 `actor_buffer.actions`；
- 用 acceptance 反向定义 DVM；
- 因 rejected proposal 选择第二候选；
- resolver 自动生成策略未提出的任务。

---

## 11. Global observation + local action mask 兼容性

### 11.1 结构兼容

当前 lifecycle actor observation 对所有 N 个 task 按全局固定顺序拼接，
action 也直接输出 global task ID。Shared observation 由全部 actor
observation 加 centralized budget block 构造。

关键位置：

- `assignment_harl_wrapper.py:900-946,2267-2409`
- `assignment_lifecycle_observation.py:619-656,745-762`

因此第一篇工作所需：

```text
global fixed-dimensional observation
+ local action mask
+ global task IDs
```

在结构上兼容，不需要局部 task 重编号或 repack。

### 11.2 是否需要改变 observation dimension

若：

- local membership；
- Top-K；
- failed-pair；
- path validity；
- ownership/preemption；
- decision-valid

全部仅作为 mask/sidecar，actor/shared dimension 可以保持不变。

但当前 actor observation 没有明确表示：

- robot availability/failure/recovery；
- `NEEDS_ASSIGNMENT`；
- task phase/TEAM_INFEASIBLE；
- pair-specific navigation/alignment decomposition。

若方法要求策略显式看到这些全局状态，就必须新增 feature，actor/shared
dimension 和 checkpoint fingerprint 都改变。

即使 dimension 不变，mask、event、decision 和 resolver semantics 已改变，
也必须升级 profile/schema/fingerprint，不能因 state_dict shape 相同而视为
checkpoint 兼容。

---

## 12. Event update → Top-K → policy → resolver 顺序兼容性

### 12.1 推荐运行边界

目标顺序可映射为相邻两个固定物理 step 之间的一次 assignment boundary：

```text
physical execution result
  -> pre-reset transition facts
  -> robot/task lifecycle transition
  -> completion/release/failed-pair/availability facts
  -> termination state and reason
  -> collect same-step lifecycle events
  -> seed local robots
  -> one-round owner expansion
  -> merge overlapping local sets
  -> recompute navigation/alignment/path-valid
  -> recompute Top-K after merge
  -> global obs + local mask + DVM snapshot
  -> runner samples only DVM=true rows
  -> resolver validates/stages transfer components
  -> atomic effective/ownership commit
  -> next fixed physical step
```

若 env 已终止，则仍记录 facts/events/termination reason，但不再采样或提交新
assignment，DVM 全 0。

### 12.2 必要接口

需要 immutable tick snapshot，至少包含：

- `tick_id`/snapshot generation；
- event batch；
- robot/task authoritative lifecycle state；
- owner/current assignment；
- failed-pair；
- robot availability；
- `navigation_cost[E,M,N]`；
- `alignment_cost[E,M,N]`；
- `nominal_path_valid[E,M,N]`；
- merged local robot/task sets；
- Top-K global task IDs/mask；
- final available-actions；
- `decision_valid_mask`；
- forced action。

Wrapper、runner 和 resolver 必须使用同一 generation，不能在 actor sample
之后无检查地重建不同 mask。

### 12.3 Local-set builder 当前缺失

当前代码没有：

- event/`NEEDS_ASSIGNMENT` seed；
- per-robot Top-K；
- 一轮 owner expansion；
- overlap merge；
- merge 后候选重算；
- 集合外 owner preemption lock；
- current task union。

建议新建纯数据模块，将该逻辑从 wrapper 和 resolver 中分离，输出 global-ID
mask，不重新编号 task。

---

## 13. Cost 接口审计

`scan_mobile_manipulator_env.py:get_assignment_problem`
（`1686-1758`）当前：

```text
cost_matrix = Euclidean norm(scanner_pos - viewpoint_pos)
```

它只用于 baseline/resolver arbitration，不影响 dynamics。当前还存在：

- static geometric `feasible_mask`；
- `available_mask = feasible & uncovered`；
- obstacle footprint 只做 diagnostics，不改变 cost/mask；
- `task_status` 只有 unassigned/completed；
- `robot_status` 每次全部写成 IDLE placeholder。

当前未满足：

- `navigation_cost + alignment_cost` 的 pair-specific time contract；
- current owner 的 remaining navigation time；
- 每 tick 显式 refresh contract；
- pair-specific alignment matrix；
- nominal path valid bool mask；
- no-path 不使用大有限数的约束。

推荐 environment/execution layer 暴露：

```text
navigation_cost: [E,M,N] float, estimated time
alignment_cost: [E,M,N] float, pair-specific matrix
nominal_path_valid: [E,M,N] bool
cost_generation/timestamp
```

第一版可以用每机器人 alignment 常数广播到 N 列，但接口本身必须保持
pair-specific。现有 Euclidean distance 可作为明确标注的 prototype fallback，
不能宣称已满足预计时间语义。

真实 navigation/alignment estimator 的来源在当前仓库中证据不足，需要后续
execution-interface work，但不阻塞先建立 typed/default-off 接口。

---

## 14. Resolver 与 transfer component 改动范围

### 14.1 当前 resolver 行为

`AssignmentLifecycleResolver.resolve_pre_step`
（`assignment_lifecycle_resolver.py:213-415`）：

- disabled：proposal 原样 pass-through；
- enabled：逐 env、逐 robot 立即处理；
- idle noop：接受；
- covered/owned/failed/unavailable target：拒绝；
- 同一未占有 target 的同步 claim：按最低 finite cost，robot ID tie-break；
- winner 立即写 active target/owner；
- executing current 或 noop：CONTINUE；
- executing 的任何其他 target：`switch_disabled`。

`_start_claim`（`767-802`）直接 mutation resolver state。

`observe_post_step`（`417-496`）只处理：

- newly covered completion；
- budget failure/release；
- done reset。

不存在：

- transfer graph/component；
- owner closure；
- switch/preemption；
- component before/after cost；
- component threshold；
- staged all-or-none commit；
- terminal posture failed-pair；
- TEAM_INFEASIBLE。

### 14.2 支持 transfer component 所需算法范围

Resolver 需要从“逐 robot 立即写”改为：

1. 对当前 local decision proposals 全量校验，但不 mutation；
2. 构造 `robot -> proposed task -> current owner` transfer graph；
3. 形成 connected transfer components；
4. 校验 component 完整性、one-round owner closure、pair/path/mask legality、
   ownership uniqueness、preemption eligibility；
5. 用本 tick freshly recomputed pair cost 计算：

   ```text
   local_cost_before
   local_cost_after
   improvement
   ```

6. improvement 达到 config threshold 才接受；
7. 对每个 component staging；
8. 原子提交全部 effective assignment/ownership/pair state；
9. 失败 component 全拒绝并保留旧 effective/ownership；
10. 输出一个 component-level canonical rejection reason。

完整、合法、改善充分的 component 可以覆盖 current-owner 的 CONTINUE。
若 component 不完整、不合法或改善不足，current owner 保持原 assignment。

### 14.3 必须维持的禁止项

Resolver 不得：

- 搜索最优 matching；
- 枚举 proposal 子集；
- 为 rejected robot 生成第二候选；
- 自动分配策略没有提出的 task；
- 以 per-robot 局部 mutation 产生半提交；
- 用 effective 覆盖 proposal buffer。

该改动在文件范围上主要集中于 resolver/local-set 模块，但算法实质较大；
它是可控的项目内改动，不是 HAPPO 架构阻塞。

---

## 15. Failure、TEAM_INFEASIBLE 与 termination

### 15.1 当前状态模型缺口

`assignment_state.py:10-42` 有一般 task/robot 常量，但没有：

- `NEEDS_ASSIGNMENT`；
- `TEAM_INFEASIBLE`；
- robot recovered event；
- `ALL_TASKS_COMPLETED`；
- `NO_FEASIBLE_TASKS_REMAIN`。

当前 `get_assignment_problem` 的 task/robot status 只是 derived placeholder，
不是 authoritative lifecycle state。

Resolver 的 pair state 只有 budget failure/release，不能代表执行层终端姿态失败。

### 15.2 推荐 authority

必须冻结单一 transition authority：

```text
execution result
  -> TERMINAL_PAIR_FAILURE(i,j)
  -> failed_pair[i,j] = true for rest of episode
  -> release task ownership
  -> robot = NEEDS_ASSIGNMENT
  -> local event seed
  -> if all robots failed for task j:
       task_j = TEAM_INFEASIBLE
```

Termination：

```text
if all tasks == COMPLETED:
  ALL_TASKS_COMPLETED

elif all tasks in {COMPLETED, TEAM_INFEASIBLE}:
  NO_FEASIBLE_TASKS_REMAIN

else:
  continue episode
```

### 15.3 Phase 依赖

这些 state/fact 接口不能全部推迟到原建议 Phase D，因为：

- failure/release/`NEEDS_ASSIGNMENT` 是 Phase B local-set seed；
- robot unavailable/recovery 也是 Phase B event；
- TEAM_INFEASIBLE 决定 action mask；
- termination 检查决定 terminal step 是否允许下一次 assignment。

应在 A/B0 先建立 typed/default-off facts 与 pre-reset snapshot；D 再启用正式
reward penalty、termination policy 和统计。

---

## 16. I — Checkpoint、配置与 playback 兼容性

### 16.1 当前 checkpoint contract

当前代码权威版本：

```text
assignment_checkpoint_contract_v2
```

位置：

- `assignment_checkpoint_contract.py:39`
- `AssignmentCheckpointContractManifest:517-560`

Manifest 当前冻结：

- identity/profile/state type/serialization；
- M/N/agent order；
- actor/shared schema 和 dimension；
- Discrete action contract；
- lifecycle snapshot/resolver/mask/budget/ownership/arbitration version；
- feed-forward policy sequence；
- actor/critic model structure；
- training hyperparameter contract。

Normal evaluation 比较 `_EVALUATION_PATHS`
（`225-251`）；validated weight continuation 比较完整 contract
（`1311-1325`）。

Fine-tuning 和 exact resume 当前明确不支持
（`1209-1229`）。无 metadata checkpoint 只允许显式
legacy+resolver-disabled evaluation fallback（`1458-1496`）。

### 16.2 当前 manifest 未覆盖的新语义

即使 dimension 不变，v2 未冻结：

- event taxonomy/order；
- assignment tick；
- local-set/one-round owner expansion/overlap merge；
- Top-K/current retention；
- navigation/alignment/path-valid contract；
- preemption/component/threshold；
- terminal failed-pair/TEAM_INFEASIBLE/termination reason；
- DVM definition；
- valid-only sampling/loss/entropy/adv normalization；
- zero-valid/singleton handling；
- HAPPO nondecision ratio identity；
- explicit team reward reduction；
- component-level rejection penalty。

这是语义 checkpoint 的高风险缺口。

### 16.3 推荐版本策略

Feature off：

- 保持当前 profile、v2 manifest/fingerprint、obs/shared/action、控制流和文件
  副作用不变；
- 旧 v2 checkpoint 在同一 feature-off profile 下继续可用；
- 不要令 `DVM=1` 后走新 trainer 来模拟 old path；必须直接旁路到 installed
  old path，避免 RNG/minibatch/statistics 漂移。

Feature on：

- 使用一个新的高层 profile，而不是散落 low-level bool；
- 建议新增可分派解析的 v3，而不是把 parser 单向改成只认 v3；
- v2 checkpoint 对 event-gated normal evaluation/validated continuation 必须
  因 semantic mismatch 拒绝；
- 除非以后明确批准具名、窄范围 ablation，不得静默跨语义加载。

### 16.4 Observation/shared/action dimension

- 保持 global observation 现有 feature：dimension 可不变；
- 增加 availability/task-phase features：actor/shared dimension 改变；
- 保持 global ID + noop：action dimension 仍为 `N+1`；
- executing noop 从 mask 中移除不改变 action dimension，但改变 mask/action
  semantic contract，仍需 fingerprint。

### 16.5 Scenario/config 缺口

`scan_mobile_manipulator_env.py:307-312` 当前默认：

```text
assignment_lifecycle_profile = "legacy"
assignment_cooldown_enabled = false
```

这是良好的 default-off 基础。

但 `scenario_config.py` 有一个当前代码 plumbing gap：

- `ASSIGNMENT_LIFECYCLE_SCENARIO_ATTRS` 定义 profile（`49-51`）；
- config parser 读取 top-level/nested profile（`252-255`）；
- `apply_scenario_config_to_env_cfg` 只循环
  `ENV_CFG_SCENARIO_ATTRS`（`479-492`）；
- lifecycle attrs 未包含在该 tuple 中。

所以通过 scenario YAML 解析出的 lifecycle profile 当前不会由这个 apply
函数落到 env cfg。Hydra 直接 override 是另一条路径，不能据此认为 scenario
plumbing 已完整。

推荐新建独立 event-gated scenario YAML，不修改已有 Phase 9G-8 YAML，并在
Phase A 加：

- nested block parse；
- flatten/apply；
- type/range/cross-field validation；
- enabled mode 所有关键值显式；
- invalid combinations fail-fast。

### 16.6 Playback

`scripts/reinforcement_learning/harl/play_assignment.py:670-706` 当前仍每个物理
step 对所有 actor 调 `act` 和 `evaluate_actions`。

当前 playback attribution collector 已能断言：

- raw action decode == proposal；
- controller assignment == effective。

它是可复用先例，但 enabled event-gated playback 必须镜像：

- same tick/DVM；
- valid-only actor call；
- forced nondecision action；
- component/tick diagnostics；
- strict checkpoint profile。

Feature off 必须保留当前 playback 行为和输出。

---

## 17. J — 日志与诊断建议

### 17.1 当前训练日志缺口

Wrapper 已有 proposal/effective payload，但：

- `_augment_info` 未加入完整 lifecycle resolution；
- `AssignmentIsaacLabEnv.step` 向 HARL 返回空 infos；
- `_flatten_numeric_log` 会把 tensor/array mean-collapse；
- installed Isaac logger 只接受 scalar；
- training logger 当前无法追踪 per-robot/component proposal/effective/rejection；
- resolver full JSONL/CSV 默认关闭，开启后逐步同步写，不适合高吞吐训练全量使用。

`AssignmentIsaacLabLogger` 对 `Total_Reward` 使用 exact whitelist；新增 diagnostics
必须继续与 reward accumulator 解耦，不能改变 best-model 选择。

### 17.2 训练正确性必须记录

建议 invariant + episode aggregate，不能只存总体均值：

- assignment tick count / tick id；
- per-robot/per-actor decision-valid sample count；
- zero-valid actor update skipped count；
- semantic legal action count / unique-action row count；
- sampled proposal 与 buffer action identity；
- proposal/effective pair；
- accepted/rejected 与 canonical reason；
- component id、all-accept/all-reject；
- ownership uniqueness/atomic-transfer violation count；
- mask/DVM/snapshot-generation mismatch count；
- nondecision factor effective-ratio 与 1 的 max error/count；
- terminal-step decision count，目标必须为 0；
- explicit team reward reducer/broadcast equality；
- termination reason count；
- failed-pair/team-infeasible count。

### 17.3 论文分析日志

- per-robot decision count；
- CLAIM/CONTINUE/SWITCH/IDLE proposal count；
- accepted/rejected count和 reason 分布；
- transfer component size；
- ownership transfer count；
- local cost before/after/delta；
- `NEEDS_ASSIGNMENT` duration；
- idle-with-available-task；
- failed-pair count；
- team-infeasible task count；
- termination reason distribution；
- per-robot productive completion/load balance。

### 17.4 可后置的附加日志

- 全 action probability vector；
- counterfactual candidate score；
- 每 tick 完整 cost matrix；
- 每机器人完整 Top-K trace；
- owner-expansion graph；
- 全 pose/motion/event dump；
- visualization/video。

高容量明细应进入可选 JSONL/CSV artifact；TensorBoard 只保留低基数 aggregate。

---

## 18. 风险清单

| ID | 风险 | 等级 | 影响 | 缓解 |
|---|---|---:|---|---|
| R1 | EP critic 只取 `rewards[:,0]` | Critical | rejection/team reward 语义错误 | 明确 team scalar/reducer 并写 contract/assert |
| R2 | nondecision raw ratio 污染 HAPPO factor | Critical | 后续 actor surrogate 因无决策状态被错误重权 | valid-only pre/post eval 或 `where(DVM,ratio,1)` |
| R3 | DirectMARLEnv auto-reset 覆盖 terminal facts | Critical | failure/termination/event 顺序不可靠 | environment pre-reset fact snapshot/hook |
| R4 | executing current/noop 是语义别名 | High | DVM 被错误置 1 | 新 profile 移除 executing noop；按 semantic count |
| R5 | zero/singleton valid sample NaN | High | actor 参数/optimizer 污染 | K=0 skip；K=1 finite fallback；valid-count guard |
| R6 | resolver 逐项 mutation | High | transfer component 半提交 | validate/stage/component-level atomic commit |
| R7 | v2 manifest 不冻结新语义 | High | shape 相同旧模型被错误接受 | 新 profile + v3 dispatcher + strict mismatch |
| R8 | structured info 被 facade 丢弃 | High | 无法证明训练正确性 | typed sidecar/aggregate logger，不做 mean-collapse |
| R9 | `bad_masks` 恒 1 | High | timeout 与 termination return 语义混淆 | 恢复 `bad_transition`/typed termination info |
| R10 | mask snapshot 在 sample 后被重建 | High | action 与 historical support 不一致 | immutable generation + equality assertion |
| R11 | 真实 time cost 来源不存在 | Medium | Top-K/component improvement 不符合论文语义 | typed cost interface；prototype fallback 明示 |
| R12 | failure/availability execution interface 不存在 | Medium | lifecycle event 只能模拟 | 先 DTO/hook，后接 execution layer |
| R13 | scenario profile 解析但未 apply | Medium | YAML 请求与运行 profile 不一致 | 修 config propagation + startup echo/assert |
| R14 | full resolver trace 写入开销 | Medium | training throughput/IO 抖动 | aggregate counters + sampled detailed traces |
| R15 | default-off 走新代码路径 | High | Phase 9G-8 RNG/行为漂移 | feature-off 直接旁路 current implementation |

---

## 19. 推荐实施阶段与依赖修正

### Phase A — 纯接口、身份与诊断

内容：

- 新高层 profile/config，默认关闭；
- event/fact/cost/local-set/decision/component typed DTO；
- snapshot/tick generation；
- checkpoint v2/v3 dispatcher 设计；
- proposal/effective/decision/component 结构化诊断；
- team reward reducer contract 的显式配置与断言；
- 不改变训练、resolver 或 controller 行为。

测试：

- default-off 深比较；
- config parse/apply；
- unknown/invalid combination fail-fast；
- feature-off v2 checkpoint 正常接受；
- feature-on 对 v2 semantic mismatch；
- 新字段 fingerprint 变化；
- no new diagnostics file when off。

### Phase B0 — Pre-reset facts 与 lifecycle transition

这是对原 A-E 拆分的必要补充。

内容：

- execution result/pre-reset fact surface；
- terminal pair failure；
- release；
- `NEEDS_ASSIGNMENT`；
- robot unavailable/recovery；
- task `TEAM_INFEASIBLE` state；
- termination reason data model；
- 全部先置于 default-off gate。

测试：

- fact update 先于 decision snapshot；
- failed pair episode-persistent；
- failure→release→NEEDS_ASSIGNMENT；
- all-pairs-failed→TEAM_INFEASIBLE；
- terminal frame snapshot 不被 auto-reset 覆盖。

### Phase B — Local action mask、assignment tick 与 atomic resolver

内容：

- event seed；
- one-round owner expansion；
- overlap merge 后重新算候选；
- tick-time navigation/alignment/path-valid；
- per-robot Top-K + current retention；
- global-ID local mask；
- DVM sidecar，但尚不用于训练；
- staged transfer component；
- deterministic controller/effective smoke。

测试：

- one robot event；
- multi-robot same tick；
- overlapping sets merge；
- no second-layer recursion；
- outside owner不可抢占；
- current task retained；
- component all accept/all reject；
- cost threshold；
- ownership uniqueness/atomicity；
- feature-off resolver identity。

本阶段只做 deterministic smoke，不训练。

### Phase C — Buffer 与 decision-valid HAPPO update

内容：

- repo-local actor buffer DVM；
- valid-only collect；
- proposal action identity；
- actor loss/entropy/adv normalization；
- K=0/K=1 handling；
- nondecision factor ratio=1；
- actor update/factor diagnostics；
- critic/GAE/ValueNorm 保持全物理 step。

测试：

- synthetic tensor/spy runner tests；
- one-valid/multi-valid/different-agent DVM；
- unique legal action不更新；
- rejected proposal仍更新；
- effective不覆盖 buffer；
- factor invalid位置严格 1；
- zero-valid optimizer state不变；
- DVM变化不改变 GAE/critic/ValueNorm input；
- default-off action/logprob/params/factor/returns 精确一致。

### Phase D — Reward 与正式 termination 语义

内容：

- component-level rejection penalty；
- explicit team reward reducer/broadcast；
- 正式启用 TEAM_INFEASIBLE termination；
- `ALL_TASKS_COMPLETED`/`NO_FEASIBLE_TASKS_REMAIN`；
- proper time-limit/bad-mask 修复；
- 论文指标和 termination aggregates。

测试：

- 每 rejected component 只扣一次；
- reward M 列符合已冻结 team contract；
- 非 robot_0 rejection 不被丢失；
- 还有其他可行 task 时不终止；
- 全 complete 与无可行任务两种 reason；
- terminal step DVM=0；
- Total_Reward whitelist/best selection 不被诊断字段改变。

### Phase E — 训练与消融

本次只设计，不执行。

进入条件：

- A-D pure/static/deterministic tests 通过；
- default-off identity 通过；
- checkpoint mismatch 通过；
- reward contract 和 singleton advantage contract 已冻结；
- 先 tiny controlled smoke，再训练；
- 训练后再做 attribution playback 与消融。

### 19.1 对用户原 A-E 拆分的判断

总体顺序合理，但有一个依赖错误：

```text
failure/team-infeasible/termination 的全部状态语义不能都留到 D
```

Failure/release/availability/`NEEDS_ASSIGNMENT` 是 B 的 local-set 输入；
task terminal state 又是 B 的 action mask 输入。应把 typed state transition
和 pre-reset facts 前移到 A/B0，D 只负责正式启用 termination policy、
reward penalty 和最终指标。

Rejection penalty 留在 D 是合理的，因为“只扣一次”的单位依赖 B 已冻结的
component identity。

Default-off equivalence 必须是每个 phase 的 gate，不是只在 E 前验证一次。

---

## 20. 后续测试矩阵

| 测试 | 最小层级 | 关键断言 |
|---|---|---|
| default-off 与当前 HEAD 一致 | pure + deterministic smoke | obs/mask/action/logprob/effective/reward/factor/side effect 一致 |
| 一个 robot decision-valid | synthetic runner | 只 forward 对应 row；其他 forced |
| 多机器人同 tick decision-valid | synthetic runner/resolver | agent-specific DVM 与 component 正确 |
| 唯一合法动作 | mask/trainer unit | DVM=0，无 optimizer step |
| rejected proposal 保留 | runner/resolver unit | buffer raw action=proposal，DVM=1 |
| effective 不覆盖 buffer | runner integration | buffer action与 sampled raw相等 |
| nondecision factor ratio=1 | HAPPO unit | invalid位置 exact ones |
| zero-valid actor | HAPPO unit | params/optimizer/factor unchanged |
| singleton valid advantage | HAPPO unit | finite，无 NaN，采用冻结 fallback |
| component 全接受或全拒绝 | resolver unit | ownership/state 无半提交 |
| owner CONTINUE 被合法 component 覆盖 | resolver unit | only complete/improving component can override |
| overlapping event sets | local-set unit | union + recompute，no second recursion |
| current 不在 Top-K | mask unit | current仍作为 CONTINUE |
| invalid nominal path | cost/mask unit | bool mask禁止，无大有限数 fallback |
| failed pair permanent | lifecycle unit | episode内永久禁止 |
| team-infeasible | lifecycle/env unit | 从候选移除；其他任务仍执行 |
| termination reason | env unit | 两类 reason 严格区分 |
| terminal pre-reset facts | env integration | reset前 facts/event 可见 |
| proper-time-limit | buffer integration | timeout bad_mask=0，true terminal=1 |
| checkpoint mismatch | contract unit | v2→new profile拒绝；semantic field变更指纹变化 |
| playback parity | playback unit/smoke | enabled mirror tick/DVM；off保持 HEAD |
| logger correctness | logger unit | per-robot不被 mean-collapse；不影响 Total_Reward |

本阶段没有运行这些测试；它们是后续实施 gate。

---

## 21. 精确预期修改文件清单

以下是推荐实施清单，不是本阶段已修改内容。

### 21.1 Environment / lifecycle / resolver

| 文件 | 预期职责 |
|---|---|
| `scan_mobile_manipulator_env.py` | pre-reset execution facts、authoritative availability/failure/task terminal state、termination reason、cost source |
| `assignment_state.py` | `NEEDS_ASSIGNMENT`、`TEAM_INFEASIBLE`、event/termination typed constants |
| `assignment_lifecycle_observation.py` | 新 profile global features/local mask、executing noop规则、path/local/preemption filters、DVM断言 |
| `assignment_lifecycle_resolver.py` | component graph、合法性/改善判断、staging、atomic transfer、failure/release semantics |
| `assignment_lifecycle_resolver_runtime.py` | tick/event/component/cost/ownership payload 与 aggregate |
| `assignment_harl_wrapper.py` | immutable tick snapshot、global obs/local mask/DVM、forced action、proposal/effective sidecar、reward contract |
| `assignment_controller.py` | 预计无需改变职责；继续只消费 effective，补接口断言即可 |

建议新增：

| 新文件 | 预期职责 |
|---|---|
| `assignment_event_gated_contract.py` | event/fact/tick/cost/decision/component dataclass 与 version strings |
| `assignment_local_mrta.py` | seed、one-round owner expansion、overlap merge、Top-K、current retention |

### 21.2 HARL training

| 文件 | 预期职责 |
|---|---|
| `assignment_harl_training.py` | facade DVM sidecar、warmup/insert/collect/train 路由、structured aggregates、explicit EP team reward |
| `assignment_lifecycle_training_contract.py` | 新 profile、feed-forward/DVM/factor/zero-valid startup guard |
| `scripts/reinforcement_learning/harl/train.py` | 新 profile/config wiring 与 startup validation |
| `agents/harl_happo_cfg.yaml` | default-off 高层配置入口；不要把语义身份拆成无版本 bool |

建议新增：

| 新文件 | 预期职责 |
|---|---|
| `assignment_happo_event_gated.py` | repo-local actor-buffer subclass、HAPPO valid-only trainer、factor helper |

不要直接修改：

```text
C:\isaacenvs\isaac45_harl\Lib\site-packages\harl
```

现有 repo-local runner/registry 已足以接入 subclass/shim。

### 21.3 Config/checkpoint/playback/logging

| 文件 | 预期职责 |
|---|---|
| `scenario_config.py` | 新 MRTA block parse/validate/apply，并修 lifecycle profile漏传 |
| 新 event-gated scenario YAML | 所有 enabled 参数显式，既有 Phase 9G YAML 不变 |
| `assignment_checkpoint_contract.py` | v2/v3 分派、新 semantic contract、strict mismatch |
| `assignment_checkpoint_save.py` | 从真实 runtime 捕获新 profile/DVM/factor/reward/event contract |
| `assignment_checkpoint_load.py` | v2/v3 strict load 与明确拒绝旧语义 |
| `scripts/reinforcement_learning/harl/play_assignment.py` | enabled tick/DVM actor gating 与 strict profile |
| `assignment_playback_attribution_diagnostics.py` | tick/DVM/component/cost/termination fields |
| `assignment_lifecycle_diagnostics.py` | 低开销 aggregate 与可选高容量 trace |

### 21.4 建议新增/扩展测试

```text
scripts/environments/test_assignment_event_gated_contract.py
scripts/environments/test_assignment_local_set_topk.py
scripts/environments/test_assignment_transfer_component_resolver.py
scripts/environments/test_assignment_decision_valid_buffer.py
scripts/environments/test_assignment_decision_valid_happo.py
scripts/environments/test_assignment_team_reward_contract.py
scripts/environments/test_assignment_team_infeasible_termination.py
scripts/environments/test_assignment_event_gated_checkpoint_contract.py
scripts/environments/test_assignment_event_gated_default_off_identity.py
```

并扩展现有 lifecycle mask、resolver、checkpoint save/load、ValueNorm 和 playback
attribution tests。

---

## 22. 结论与下一步

### 22.1 最终结论

```text
RUNNER-CHANGES-REQUIRED
```

原因：

- 现有 global observation/global ID/historical mask/proposal buffer/critic GAE
  骨架兼容；
- local MRTA 和 atomic component resolver 可在项目内扩展；
- 但锁定的 actor sampling、valid-only loss/entropy/advantage 和
  HAPPO nondecision factor identity 无法仅靠环境/action mask 达成；
- 必须明确修改 repo-local runner、trainer 和 buffer。

### 22.2 推荐下一实施阶段

```text
Phase A:
  pure interface + profile/config + checkpoint identity + diagnostics

随后:
  Phase B0 pre-reset facts/lifecycle transition
```

Phase A 必须保持 default-off 行为、RNG path、checkpoint v2 和文件副作用不变。

### 22.3 最大技术风险

```text
第一:
  HAPPO sequential factor 在 nondecision 样本上的 ratio identity

第二:
  EP critic 当前只使用 robot_0 reward，而不是显式 team reward

第三:
  DirectMARLEnv auto-reset 前后终止 facts 的时序
```

### 22.4 是否建议实现前再做方法讨论

不建议重新讨论或重设计本次已经锁定的 MRTA 方法原则。

建议在实现前只做一次窄范围接口确认，冻结三个工程契约：

1. EP team reward 的 reducer/broadcast 定义；
2. 单个有效 advantage 样本的 finite normalization fallback；
3. terminal pre-reset facts 的 authority/hook 位置。

此外，真实 navigation/alignment 预计时间来源可以先以 typed interface 和
明确 prototype fallback 推进，不必阻塞 Phase A。

---

## 23. 本阶段验证与边界确认

已完成的安全检查：

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

另进行了不构造环境的纯张量级核对：

- unique Categorical support 仍会返回 action/log-prob；
- zero mask denominator 会产生非有限值；
- current `torch_nanstd(unbiased=True)` 在单有效样本时产生 NaN。

没有进行训练、playback、evaluation、checkpoint load、Isaac environment
construction 或任何运行行为修改。
