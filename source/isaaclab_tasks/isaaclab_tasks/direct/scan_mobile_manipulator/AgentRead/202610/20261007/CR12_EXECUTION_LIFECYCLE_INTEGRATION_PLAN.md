# CR12 扫描执行层与现有 lifecycle authority 接入方案

- 日期：2026-10-07（本机 Asia/Shanghai，UTC+08:00）。
- 类型：**源码/契约分析与实施方案；未实施、未运行集成。**
- 仓库：`E:/Project/IsaacLab_HARL`；HEAD：`24ecbad7dd1bdcd006399b64bfb757a86b71aeec`。以下行号来自本轮工作区，包含已有未提交的 CR12 实现。
- 记号：`T=source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator`；`E=scripts/environments`；`Q=source/isaaclab_tasks/test`。
- 证据标签：**[用户确认]** 最新审阅结论；**[已有运行]** 已接受报告记录；**[源码]** 本轮静态核对；**[建议]** 待审实现；**[待运行]** 未由源码或先前独立运行证明。

## 1. 两条当前调用链与结论

**当前 event MRTA 链 [源码]：** 调用者在 OPEN window 捕获 `EventProposalDecisionSnapshot` → `EventProposalAdapter.resolve` 处理 proposal → facade/O1 经 production claim port 提交合法 claim → coordinator 更新唯一 Store 并发布 P2 effective assignment → O1 从 admitted P2 反演 assignment → 默认 `assignment_to_env_actions` 生成旧 9D proxy 动作 → `ScanMobileManipulatorEnv.step` 更新 proxy pose，几何+dwell 形成 `raw_new_candidate` → reset 前 domain 构造 `ExecutionTransitionInput` → producer 创建 immutable facts → authority transaction 消费并发布 result/P2 → env 复制权威 coverage。故障/释放/不可用/恢复信号在当前 domain 输入构造中仍为 false。公共 event 入口仍关闭；这是当前私有 composition 的真实源码链，不能称公共入口已经开放。

**当前 CR12 链 [源码；正常双点另有已有运行]：** `run_cr12_two_view_capture.main` → 共享单点 `main(capture_runner=run_two_capture)` → `initialize_capture_run` 一次创建 scene/robot/Camera/product → `TwoViewSequence` 固定提交两目标，`TwoViewPoseContinuation` 保留跨两段控制状态 → `execute_capture_request` 内部循环 `next(_pose_ticks)` → DLS/积分器下发关节目标，自行 physics step/render → `OwnedCameraCapture` 同事件复制新 RGBA → `SingleViewRequest` 记录 acquired/save/OFF 并终态 → 下一固定目标 → `finalize_capture_scene` 统一释放，main 自然退出。异常通常上抛至 runner/main 关闭整个 App。**没有向 MRTA producer/authority 提交成果。**

**推荐一个方案 [建议]：** 新增一个私有 `E=1/M=1/N=2` integration host，真实复用既有 domain、Store、resolver、claim、P2、producer、transaction、facade；以确定性 proposal 驱动一台真实 CR12。Host 拥有唯一 scene/physics/render 时钟，窄 adapter 将 admitted assignment 绑定为长请求，并将采集/关闭事实提交现有 authority。保留现有任务权威语义，新增的执行阶段、数据交付和 claim 绑定使用明确的 report 扩展，不能硬塞进原布尔字段。

不用旧 proxy 环境并行驱动 CR12：它会引入两套 pose 与几何完成来源。也不另建 owner/completed 字典、直接写 P2，或把固定双点 runner 当作 authority。首版不接 HARL/RL、网络、reward、checkpoint 或公共 gate；不证明多机器人冲突仲裁、动态调度性能或任意视点可达性。

| 结论 | 证据等级与范围 |
|---|---|
| 独立单机双视点正常最小闭环已经完成 | [用户确认] `TWO_VIEW_CAPTURE_INTEGRATION GPT REVIEW PASS`；Phase B 保持 COMPLETE / GPT REVIEW PASS / CLOSED |
| 同 App/scene/robot，两段真实 pose、同 Camera/product 两次 fresh+OFF、连续控制、自然退出 | [已有运行] [双视点主报告](CR12_TWO_VIEW_CAMERA_CAPTURE_REPORT.md)：1324 physics ticks、两份采集，各 OFF 30 render/30 quiet；本轮未重跑 |
| 当前 MRTA 仍使用 proxy 运动与几何+dwell 候选；CR12 到独立结果为止 | [源码] 见下表及第 2 节 |
| E1/M1/N2 可以组合真实 authority | [源码] 动态维度契约允许；[待运行] 新 CR12 host 的集成尚不存在 |
| 取消恢复、无数据请求再次复用、迟到反馈与真实 authority 的组合 | [待运行] 不能由双点正常 PASS 代验；本轮只设计 |

### 1.1 关键源码证据索引

链接指向真实文件，行号为当前工作区定位；不是历史 PASS 标题的替代品。

| 标识 | 路径、关键符号/行号 | 直接支持的事实 |
|---|---|---|
| S1 | [facade](../../../assignment_event_runtime_facade.py)：`capture_proposal_decision:557`、`step_resolved_proposals:609`、`resolve_and_step_proposals:719`、`reset:739`、`step_without_new_claim:754`、compose `782` | proposal、claim、continuation、terminal 接入表面 |
| S2 | [O1 synchronous runtime](../../../assignment_event_profile_synchronous_runtime.py)：`_derive_control_assignment_from_admitted_publication:139`、ctor `250`、claim `393`、reset `421`、step `446–477` | 先 admission/P2，再 action_builder，再一次 environment.step；异常 poison |
| S3 | [runtime domain](../../../assignment_event_profile_runtime_domain.py)：spec `216–255`、`_StagedPreResetPhysicalReport:333`、environment port `689`、finalize `1324`、`_build_transition_input:1484–1564` | 真实 domain 持有 Store/producer/coordinator；当前 staged report 与固定 false 信号 |
| S4 | [proposal adapter](../../../assignment_event_proposal_adapter.py)：`resolve:484`；[initial claim](../../../assignment_initial_claim_runtime.py)：`InitialClaimDeriver.derive_candidate:647`、artifact `782–807`、P2 `350–441` | proposal 不是有效分配；claim 与 P2 provenance/版本 |
| S5 | [authority runtime](../../../assignment_lifecycle_authority_runtime.py)：clock `116/175/219/281`、`ExecutionTransitionInput:548`、`EnvironmentExecutionFactsProducer.build_facts:603` | generation 与 producer-owned token、真实输入字段 |
| S6 | [transaction runtime](../../../assignment_lifecycle_transaction_runtime.py)：Store `791`、authority `1513/1539`、transaction `4148`、claim `4547/4591`、terminal `4933` | 唯一状态决策/事务、C/R/U/F 优先级、consume/发布/poison |
| S7 | [transition contract](../../../assignment_lifecycle_transition_contract.py)：枚举 `83–108`、facts `552`、ledger `1398/1467`、result `1998`；[terminal transport](../../../assignment_event_terminal_transport.py)：`_copy_and_validate_terminal_history:403–592` | 身份、消费一次、terminal 必须先合法 auto-reset 再 transport/ACK |
| S8 | [MRTA env](../../../scan_mobile_manipulator_env.py)：cfg `117–153`、proxy `2934–2985`、stage/commit `3100–3146`、dones/reset `3230–3320`；[旧控制桥](../../../assignment_controller.py)：`assignment_to_env_actions:39` | proxy、dwell、authority 前后 bookkeeping 与 reset |
| S9 | [DirectMARLEnv](../../../../../../../../source/isaaclab/isaaclab/envs/direct_marl_env.py)：`step:361–405` | decimation 子步；先 dones/finalization 再 reset、再返回 observation |
| S10 | [双点入口](../../../../../../../../scripts/environments/run_cr12_two_view_capture.py)：`main:5`；[双点 runner](../../../../../../../../scripts/environments/_cr12_two_view_capture.py)：`TwoViewSequence:40`、`run_two_capture:172`；[continuation](../../../../../../../../scripts/environments/_cr12_pose_continuation.py)：`47/106/127` | 固定 demo 顺序、一次 goal1→2 交接，不是长期 assignment executor |
| S11 | [共享相机入口](../../../../../../../../scripts/environments/run_cr12_single_view_capture.py)：`initialize_capture_run:267`、`execute_capture_request:311`、`finalize_capture_scene:529`、`main:578`；[pose tick](../../../../../../../../scripts/environments/run_cr12_pose_target.py)：`_pose_ticks:185`、命令 `364–385`、step `391`、render `449` | 当前 blocking loop、唯一控制器、真正驱动/读回及异常出口 |
| S12 | [请求 FSM](../../../../../../../../scripts/environments/_cr12_single_view_capture.py)：`SingleViewRequest:39`、`accept_frame:155`、`observe_close:201`、`cancel:230`；[Camera backend](../../../../../../../../scripts/environments/_cr12_camera_capture.py)：`prepare:100`、`begin_capture:264`、callback `307`、OFF `419`、release `474` | acquired/saved/OFF 分离，但 demo 保存和复用限制仍存在 |
| S13 | [policy evidence](../../../assignment_event_policy_evidence.py)：physical `357–472`、episode progress `605`、workload `618`；[scale contract](../../../assignment_event_profile_schema_contract_v2.py)：`build_event_policy_scale_contract_v2:397`、维度 `617–655`；[pre-reset critic](../../../assignment_event_terminal_critic_sidecar.py)：`capture_pre_reset_critic_physical_snapshot_v2:169` | 实际输入、动态 M/N、pre-reset sidecar |
| S14 | [wrapper](../../../assignment_harl_wrapper.py)：event 初始化 `220/329–388`、普通 step gate `641`、私有 proposal `758–807`、旧 budget `1874/1922`、diagnostics `2171`；[profile gate](../../../assignment_profile_contract.py)：`1222–1250` | 旧 budget 不在 exact-event 分支运行；公共 event 保持 fail-closed |

## 2. 当前状态写入者与真实缺口

| 状态/时钟 | 当前所有者和写入点 | 接入后的边界 [建议] |
|---|---|---|
| task state、owner、robot lifecycle、failed-pair、完成归属 | production claim deriver/coordinator；lifecycle authority derive + Store swap；episode rebuild（S4/S6） | 原 authority 保持唯一真值；adapter 只提交事实 |
| event coverage | env stage 不写；finalize 成功后 `_commit_event_scan_progress` 复制 authority coverage（S8:3132–3146） | Host 仅保留权威投影；不把 camera 回调直接 OR 进 coverage |
| legacy coverage/owner | 非 event env `3148–3201` 直接 dwell completion；旧 resolver claim/complete/release 自行维护旧分支状态 | 首版 Host 不实例化该分支，不能同时开两套完成来源 |
| 实际 CR12 q/dq/scanner pose、q_cmd | Articulation/native 真实读回；DLS+CommandIntegrator 产生目标；初始化/reset 可写初态 | 任务中只下发执行器目标，保持原守卫；无 teleport/代理 pose 回写 |
| execution stage、请求 deadline、acquired | `SingleViewRequest` + runner；不是任务 owner | 新单请求推进器维护，不复制 authority 状态机 |
| Camera/product、数据快照、sticky errors、OFF | `OwnedCameraCapture`；真实 readonly RGBA 不在 FSM.frame 中，后者仅 metadata | 一份设备资源，明确数据持有者，按请求 retire；不清资源错误伪装恢复 |
| physics/render | 旧 MRTA 由 DirectMARLEnv；独立 CR12 由 `_pose_ticks` | 新 Host 唯一推进；执行器不得自行 step/render |
| episode/transition/consume token | `LifecycleGenerationClock` / producer / ledger | 使用本次有效上下文，不让 Camera 或 adapter 自增代替 |

旧链 `_pre_physics_step` 一次 env step 更新 9D proxy base/scanner 张量；`_apply_action` 只更新 debug USD。把 CR12 画在旁边不会替换运动。event 分支仍由位置/姿态、reach、bbox range、FOV+dwell 产生完成候选，而非 Camera acquisition。

本轮未找到名为 `AssignmentManager` 的当前生产类；相关旧代码实际是 `AssignmentLifecycleResolver` 与 wrapper。旧 wrapper 的 cost/步长预算、attempt age、coverage gain、no-global-gain 不能描述成现 event authority 已实现的卡滞判断：event 初始化提前 return，旧 resolver 设为 None，关闭这些 guardrail/reward/cooldown 路径（S14）。

## 3. 唯一推荐的接入位置与最小接口

### 3.1 composition 与真实调用点

[建议] 新 `run_cr12_lifecycle_integration.py` 只负责已接受 Windows/private/D3D12/CUDA 启动准备、构造单 scene 和私有 integration composition、有限循环及收尾。保留 canonical module identity 检查；不修改 `require_assignment_profile_runtime_ready`、普通 wrapper.step 或 train/play。

Host 实现同步 `reset()`、`step(actions)`。O1 当前只要求这两个 callable，不要求实例属于 DirectMARLEnv。因此可真实复用 S1–S7，不需创建旧 proxy env。`action_builder(environment, effective_assignment)` 是现有替换点（S2:465），只绑定/继续请求，不能在其中跑完整运动循环。

构造伪代码（**Host、binding/report 方法拟新增；domain/facade 调用为现有符号**）：

```python
profile = resolve_assignment_profile(
    "event_gated_local_mrta", AssignmentProfileResolutionOrigin.FORMAL_ENTRYPOINT)
domain = _EventProfileLifecycleRuntimeDomain(
    _EventProfileLifecycleDomainSpec(
        profile, device=device, env_ids=int64([0]), num_robots=1, num_tasks=2))
host = ProposedCR12IntegrationHost(domain, one_scene, frozen_two_tasks)
runtime = EventProfileSynchronousRuntimeCoordinator(
    environment=host, current_read_port=domain.current_read_port,
    production_claim_port=domain.production_claim_port,
    physical_step_admission_port=domain.physical_step_admission_port,
    standalone_reset_admission_port=domain.standalone_reset_admission_port,
    terminal_consumer_port=domain.terminal_consumer_port,
    fence_read_port=domain.interstep_fence_read_port)
facade = _compose_event_assignment_runtime_facade(
    resolved_assignment_profile=profile, runtime_domain=domain,
    synchronous_runtime=runtime)
facade.reset()
decision = facade.capture_proposal_decision(
    feasible_mask=limited_two_task_mask, cost_matrix=cost_from_actual_scanner)
facade.resolve_and_step_proposals(
    raw_action_ids=int64([[0]]), decoded_proposal=int64([[0]]),
    decision=decision, action_builder=host.bind_effective_assignment)
# 后续 OPEN window 内，无新 claim 的周期：
facade.step_without_new_claim(action_builder=host.bind_effective_assignment)
```

任务 0 完成后在下一 OPEN window 捕获新 decision、proposal task 1。proposal 顺序可确定；effective assignment、claim 是否成立、completed 和 owner 必须来自真实组件。`raw_action_ids=N` 才是原 action 的 NO_CLAIM 编码；resolver 内部为 −1，不混用。持有中重复同 task 是 CONTINUE_EXISTING；不能通过换 proposal 直接抢占活动请求。

### 3.2 执行模块的最小拆分

[建议，方法均未实现] `E/_cr12_scan_executor.py` 提供两个窄对象：

| 拟新增接口 | 从何处抽取 | 有限工作及所有权 |
|---|---|---|
| `Cr12PoseControlSession.submit_goal(binding, target, latest_actual_boundary)` | pose + continuation | 持有唯一 controller/integrator/q_cmd/初始信任锚；新目标从真正接单时最新 actual 起步，只重建局部 reference/monitor |
| `prepare_tick(boundary)` | S11:364 前的求解/命令守卫 | DLS、积分 propose、参考和命令中点/端点检查；不 step |
| `submit_prepared(token)` | S11:364–385 | 成对 joint position/velocity target → write → 实际下发缓冲核对 → integrator commit |
| `observe_physics(before, after)`、`finish_tick(rendered)` | S11:404–536 | native/contact/几何/frame 守卫、同刻 render context、稳定窗、实际样本 |
| `CaptureRequestRunner.before_tick(now, command)`、`observe_tick(tick, now)` | S11:311–497 的 while 内容 | 单次预算/cancel/ON/OFF 准入、一次 poll/close observation；不内循环，不拥有 physics/render |
| `pending_result()`、`ack_authority_delivery(receipt)` | 新反馈边界 | immutable 结果与独立数据引用；真实 transaction 返回成功才标交付 |

旧 `_pose_ticks` 和单点 while 可成为这些原顺序接口的兼容包装；不复制第二套 DLS。`TwoViewSequence/TwoViewPoseContinuation` 留作已接受 demo，不扩成 MRTA owner。新执行上下文支持 authority 确认期间 IDLE_HOLD，不能把旧“恰好在前段最后 tick 立即切换”的限制原样套用。

### 3.3 最小 report 扩展，不改核心 lifecycle 字段含义

现 `_StagedPreResetPhysicalReport` 只含 device、coverage_before_transition、raw_new_candidate、physical_truncated、time_limit_reached、可选 pre_reset_critic_physical_snapshot。建议在 domain 增加明确类型 `_StagedPreResetExecutionReport` 与专用 `finalize_execution_transition(report)`；由同一内部 finalize 管道处理，默认原 report 路径不变。

新 report 携带：admitted P2 的来源、绑定对象/commit artifact、只读阶段/数据/OFF/健康结果，和明确的 C/F/R/U/Rc 请求信号；提交前验证 binding、真实当前 prestate、形状、episode、来源及一次交付状态。其元数据不是第二个 task state。继续使用原 producer 与 transaction，不直接构造假的 LifecycleTransitionResult。

原 `ExecutionTransitionInput` 的完整字段（S5:548–572）：`device; env_id; episode_generation; transition_generation; physical_terminated; physical_truncated; time_limit_reached; bad_transition; completion_signals; terminal_pair_failure_signals; forced_release_signals; robot_unavailable_signals; robot_recovered_signals; coverage_before_transition; task_state_before_transition; robot_state_before_transition; ownership_before_transition`。**没有** claim token、pose error、采集阶段、acquired、saved、OFF 或 payload 字段。长绑定和阶段信息必须留在明确扩展中验证，不能把 received 等同现有 C。

## 4. 身份、字段、时间域与提交确认

### 4.1 三类身份

| 类别 | 真实现有字段 | 使用规则 / 拟新增部分 |
|---|---|---|
| 长时占有来源 | claim artifact `token/source_store_version/committed_store_version`、selected env、episode/transition、requested/effective task | artifact token 每次新 claim 分配；同 robot/task 再 claim 也不同。**拟新增** binding=(run_instance_id, domain_identity, env_id, episode_generation, robot_id, task_id, claim_token)，保留 birth artifact |
| 每步权威身份 | P2 `publication_identity/store_version/env_id/episode_generation/transition_generation`；facts `consume_once_token`；result `facts_consume_token/authority_receipt_id` | P2/Store 每周期正常推进，不是新长请求。提交使用当期 transition context；不能冻结初次 claim 的 transition |
| 设备采集身份 | `goal_id/attempt_id/capture_id/render_product_path`，`rendering_frame/rendering_time`，rational source time、ON baseline | Camera attempt_id 当前是同资源序列/运行目录身份，第二次要求相同；**不能直接改用每 claim token**。新 execution binding 单列，goal_id/capture_id 唯一关联本次占有/ON |

run_instance_id 是拟新增的进程/回调隔离标识；domain identity 为进程内已有 opaque identity。reset 后即使局部 goal 名称重用，也必须同时匹配 run/domain、episode 和 claim token，不能只看 task_id。P2 后续 physical publication 不必再包含初次 claim artifact，adapter 保留经原 publication 验证的 artifact，且逐周期验证 owner/episode/新 claim。

### 4.2 输入输出映射

| 字段/内容 | 生产者 → 消费者 | 身份与时间域 | 更新/消费时机 |
|---|---|---|---|
| effective assignment `[E,M]` | O1 从 admitted P2 反演 → adapter | admitted publication + Store/clock | 每 host step；同占有只 continue |
| 目标 `T_WS*`、task ID | 冻结两任务表 → pose session | 长 binding；米、WXYZ、scanner +X forward/+Z up | 新 claim 接受一次，不按 transition 重建 |
| q/dq、实际 scanner/base pose、误差/稳定窗 | 本次 native/FK/守卫 → executor/evidence | global physics tick、同刻 physics time；local request tick 分开 | 每 physics tick；不得用 command/目标冒充 actual |
| acquired、fresh metadata、独立数据引用 | Camera callback/请求校验 → pending result/结果持有者 | capture/product/source event + binding | fresh 校验且数据实际持有后一次锁存；以后关闭/保存失败不清除 |
| artifact_saved/error | 文件保存方 → 本地交付诊断 | 当前 binding/data identity，wall time | 另行记录，不直接决定 MRTA completion |
| off_confirmed、quiet/inflight/updates_enabled | Camera 独立 observer → executor | product、OFF request、render机会/source time | 达到真实 OFF 证据后锁存，不能靠 release/destroy 代替 |
| C/F/R/U/Rc | typed execution report → domain/producer | 当期 transition + 当前合法 binding/prestate | 每 host transition 形成一次全域 facts，未终结周期可以全 false |
| 更新 task/robot/owner、coverage、计数 | authority → Store/P2/Host 投影 | consume token + authority receipt | transaction 成功后更新；adapter 无写权限 |
| pending/delivered、payload custody | adapter/结果接收者 | 稳定 binding + result receipt | 一份不可变 pending；transaction 成功返回才 delivered；与 terminal slot ACK 分开 |

CSV 契约见 [viewpoint_csv.py](../../../viewpoint_csv.py):15–43、89–105：ID 顺序 0…N−1、米、world scanner、WXYZ、单位 quaternion；旧 env 在 `1560–1562/3068–3069` 存 local 模板再加 env_origins。首版 E1 冻结一次世界 `T_WS*`，不二次加 origin。控制目标仍 `T_WE*=T_WS*·inverse(T_ES)`，Camera 安装 `T_SC` 单独沿现有虚拟约定；不把 scanner pose 当 Camera 光心或重复做相机轴系转换。

### 4.3 continue、去重与迟到结果

adapter 必须持有**由真实 claim artifact 建立的来源绑定**，不是自行分配 owner：在 action_builder 读取本次 admitted/current P2，遇新 production claim 才建请求；后续按相同绑定 continue。每次 authority outcome/episode rebuild 都使已释放或旧 episode binding 失效。若漏过 publication、无法证明 claim 来源，拒绝接单，不凭 task 相同猜测连续占有。实际读取链为 `current_read_port.read_current().provenance[domain_row].assignment_artifact`（S3:739；S4:329/411）；artifact 的 `selected_env_ids` 要另查行，`effective_task_by_robot=-1` 只表示本批无新增 claim，不能替代当前 assignment。O1 此时已进入 STEP_IN_FLIGHT，正常 claim/reset 不能插入。physical P2 的 `assignment_artifact=None` 是正常情况（S6:3542/3569），不能据此取消。新 report 接口也要核对该绑定，不能只检查当前 owner——释放后又由同一 robot 认领会通过单纯 owner 比较。

例 1：env0/episode0/robot0/task0 的 claim token=0，经 transition k、k+1…持有；Store/P2 版本不断变，pose session/goal/capture 不重建。最终第 n 个 transition 收到已持有数据+OFF+保持结果，仅提交一次 C。成功 result 的 facts_consume_token/authority_receipt_id 写入交付标记；之后重复终态仅返回原凭据，不再构造 C。这里 token 数字为示例，实际由现 coordinator 分配。

例 2：token=0 取消，OFF/保持确认后在当前 transition 提交 R；authority 释放。下一 OPEN 中重新 proposal task0，production claim 发 token=1。旧 token0 frame/result 迟到，即使 env/robot/task 相同，也只封存到旧结果，不能改为 token1 或套上新 transition 提交。episode reset 后还需拒绝旧 episode；旧数据不能因隔离而被静默删除。

消费边界：`TransitionConsumeLedger.consume` 拒绝重复 generation/token、同 generation 换 token、旧/未来 generation；producer build 失败可能已经消耗自身 token 号，不以连续编号推定成功。只有完整 transaction 返回才可标 delivered。纯 transaction receipt 前拒绝可保留同 pending report/context，但异常若逃出 O1 action_builder/Host.step，现 O1 会 poison；receipt 后异常同样 poison。**不在 facade 异常后 catch 并自动继续，不给旧结果换身份重发。** 预期业务取消/超时应成为可正常提交的结构化事实；意外错误 fail-closed 并保留数据/阶段。


## 5. 成果、保存、关闭、任务完成与机器人可用性

### 5.1 推荐语义及现有 authority 限制

[建议，待审] **正常 C 的提交条件为：本次数据已真实取得且被有效持有/交付，OFF 已独立确认，实际保持/设备状态允许继续。** acquired 在取得数据时立即锁存；等待关闭只推迟权威完成提交，不反写成“未采集”。artifact_saved 是另一个结果，不增加图像质量、重建或精度门槛。结果接收者需持有独立 readonly RGBA 或明确数据交付凭据；“没写 PNG”可以，“数据已经丢了但 metadata 说收到过”不作为正常交付。

当前 authority 完成会清 owner，并按是否有可领取任务把 robot 转 NEEDS_ASSIGNMENT 或 WAITING_FOR_TASK；它没有“task completed 但 robot 正常排空中”的独立 busy 字段。先 C 后继续关闭会过早允许下一请求；故建议正常关闭期间保留原占有，不新增一个假 task state。

记 `C=completion_signals`，`F=terminal_pair_failure_signals`，`R=forced_release_signals`，`U=robot_unavailable_signals`，`Rc=robot_recovered_signals`。S6:1575–1755 明确：

- C/F/R 必须对应 pre-transition 的 active owner；C 与 F 同 pair 不可同时为 true。
- completion 优先于 release；U 可与 C 同时存在，任务仍完成，机器人为 UNAVAILABLE。
- U 只接收可用→不可用边沿，重复报 U 会拒绝；Rc 仅从已有 UNAVAILABLE 且无 owner 状态恢复，不能无条件每周期报健康。
- F 累积到 failed-pair；M=1 时一次 F 可能使该任务 TEAM_INFEASIBLE。普通相机超时/文件失败/主动取消不具有这个永久含义。
- 当前报告和 input 没有阶段/进展字段；任务 CLAIMED 不会仅因本地 MOVING/WAITING_DATA 自动变 NAVIGATING/ALIGNING。首版保持权威状态含义，执行阶段只在新诊断里表达。

### 5.2 逐阶段映射表

以下 lifecycle 映射均为待审建议，不是已实现的运行结果。`0` 表示没有新增 C/F/R/U/Rc，不表示没有任务进展。

| 执行阶段/事实 | authority 输入建议 | 任务/机器人结果 | 下一运动 | 新表达或必要条件 |
|---|---|---|---|---|
| MOVING_OFF | 0 | 保持当前 CLAIMED/active owner、EXECUTING | 不接受别的请求 | actual error、dq、参考进度与 deadline；到位不报 C |
| ARRIVED_HOLD_OFF | 0 | 保持占有 | 否 | 原 121 样本/≥1 秒稳定证据；一次 ON 准入 |
| WAITING_DATA | 0 | 保持占有 | 否 | 本 product 的 ON baseline、真实等待/阶段超时；静止不是卡滞 |
| DATA_RECEIVED / CAPTURE_CLOSING | 0，先锁存 acquired | 保持占有直到 OFF/保持确认 | 否 | immutable payload custody + frame identity + 独立 OFF 进展 |
| SUCCEEDED_OFF，数据有效持有，保持/设备健康 | C 一次；F/R/U/Rc=false | COMPLETED，owner=-1；有剩余任务则 NEEDS_ASSIGNMENT | 仅下一 OPEN window 且接单守卫通过 | received 与 authority delivery 各有独立凭据 |
| 已采到，仍正常等待 OFF | 暂不 C；正常等待不是 U | 保持 active owner/EXECUTING | 否 | acquired=true，off_confirmed=false |
| 已采到，OFF deadline 耗尽/关闭故障 | 若有效边界还能合法提交，C+U 可表达“成果完成、设备不可用”；否则保留成果后 fail-stop | 可合法提交时 COMPLETED + UNAVAILABLE；不能承诺 terminal 正常 reset/ACK | 否 | 现有字段不能表达资源故障详情，需新结果 metadata；见第 6.2 节 terminal/reset 限制 |
| 保存 PNG/metadata 失败，但数据仍被接收方持有、OFF+保持健康 | MRTA 可 C，artifact_saved=false 另记 | 数据成果不被文件错误抹除 | 下个合法请求可；本地证据保存验收可另判失败 | integration 显式 raw-held 交付模式；旧 demo 保存必需默认不变 |
| 没采到，取消/采集 timeout，OFF+保持确认且资源健康 | R 一次，F=false | AVAILABLE、owner=-1；可 NEEDS_ASSIGNMENT | 经 authority 再 claim 后才可 | no-data retire/reuse 尚缺；FAILED_OFF 本身不足以证明可复用 |
| 没采到，设备 sticky 或 OFF 未确认，STOP_UNCONFIRMED | 可安全提交时 U；U 已自动释放 owned active pair，不需重复 R | UNAVAILABLE，任务不虚报完成 | 否 | native 无效则不强行构造事务或继续 step；全局退出 |
| 资源经后续明确修复且安全关闭/保持，无占有 | Rc 一次 | 由 authority 重新判 NEEDS_ASSIGNMENT/WAITING | 下一合法 claim | 首版不实现 sticky 自动恢复或一般硬件重建 |

**采到后物理失败的保留边界：** callback 可能已有 raw copy，但 runner 尚未 poll/accept 就在 post-render guard 抛异常。S11:481–486 的 finally 仅保存已接受的局部 snapshot，不能说当前所有 raw 必然保留。建议 backend 增加 `peek_retained_snapshot()`，只返回已存在 Python snapshot/验证阶段，不新增 native getter、不清 sticky。将“raw copy 存在”“fresh/身份校验通过”“请求 acquired 已确认”分别封存；不能把未完成必要校验的 raw 强称成功，也不能删掉已经确认的 acquired。

## 6. 唯一时钟、长请求与 terminal/reset

### 6.1 当前时间单位与推荐选择

[源码] 旧 env：dt=1/60，decimation=6，故 authority finalized transition 对应一次 env.step=0.1 秒，不是一次 sim.step。dwell 每 env transition 增长。CR12：physics dt=1/120，render 每 2 tick；motion/capture/close 预算以 physics tick 为主。`assignment_event_contract.py:1305–1349` 的 assignment_retry_cadence 是 unresolved parameter，未发现已接通的独立 cadence timer；不能编造“当前固定每几步 policy 决策”。

[建议] 新 Host 明确 **dt=1/120、control_decimation=12、render_interval=2**，保留 0.1 秒 authority 边界。O1 允许一步 Host 内多个物理子步，scale contract 能表示此设置；原 env/CR12 默认不变。这个选择减少每 physics tick 构造/消费事务的额外工作；policy proposal 只在合法事件/OPEN 边界提交，不等于 10 Hz 必须运行策略，更不等于 120 Hz policy。

一次 host.step 的拟定顺序：

1. O1 打开本次 admission，固定 admitted P2；action_builder 验证/创建/继续 binding，不运动、不 render。
2. 12 个子步逐次执行：所有 executor prepare → 所有 executor submit joint targets → scene **一次** physics step → 全部 actual/native/geometry 守卫 → 缓存同刻 render context → 若全局 cadence 到期则 **一次** render → 全部 finish_tick 与 capture FSM/poll/OFF observation。
3. 子步发生采集/OFF终态就锁存真实时刻与结果；剩余子步用同一 pose session 安全 IDLE_HOLD、保持相机 OFF，不再调用已终态 FSM.observe_tick（当前该方法拒绝终态继续计数）。
4. 块末用真实 pre-reset physical snapshot、当前 P2 prestate、锁存结果构造一次 typed report → producer → transaction → Store/P2；记录成功交付 receipt。
5. Host 正常返回，O1 才打开 Wnext；下一 proposal/claim 或 continuation 才能发生。本 Ak 内不能第二次 claim，也不能把同一个物理样本再 consume。

600 physics tick 的 motion 是 5 秒、约 50 个 Host transition，不是 600 次 policy decision。OFF 最低 30 次真实 render 机会在当前 cadence 下通常需 60 physics tick，约 5 个 Host transition；有在途事件则继续到安静窗口或 deadline。总扫描跨多少周期取决于真实到位/新帧/OFF；沿用 phase budget，不用 alive/tick 递增刷新“任务进展”。

source event time/render frame、receive wall time、physics tick/sim time、Host transition/generation 是四种相关但不同的记录。Camera source 必须按当前 backend 检查；双点模式要求 source time 严格大于 ON，render frame 严格大于 baseline（S12:307–329）。块末提交时间不能覆盖原采集时间，现有 source/pose 证据也不等于已标定的精确曝光姿态。

render lag 以逐步 poll 和已有 stage physics/wall deadline 有界等待；不写一个 while 阻塞整个 scene。若原生 render 调用本身卡死，外层所属进程墙钟监督结束的是基础设施失败，不能伪装成可恢复业务超时。native/guard 硬错误立刻停止，不为补足 12 子步而继续物理或伪造样本。

### 6.2 结果与 reset 顺序——复用 facade 的实际要求

[源码] DirectMARLEnv 在 dones/finalization 后、返回 observation 前 auto-reset。facade terminal transport 的真实限制更严格（S7:496–504、576–591）：返回精确五元组，done 行匹配已封存 terminal artifact；当前 P2 必须已经是 `result=None` 的新 episode，generation 为 `(old_episode+1, same_terminal_transition)`，reason NONE、done=false。因此新 Host 不能 terminal 后简单 break，再谎称已完成 facade copy/ACK。

[建议] 正常任务末尾先确认 OFF+保持，再在该 Host 块末：

```text
锁存旧 episode 的 frame/payload、真实物理 snapshot、执行结果
→ environment admission finalization 校验
→ producer / authority / Store / P2 / terminal artifact（旧 episode）
→ 保存 result receipt 和旧数据；作废旧请求/回调 binding
→ validate_reset_entry_for_active_call
→ environment_port.episode_rebuild(AVAILABLE, NEEDS_ASSIGNMENT, owner=-1)
→ 初始化明确安全的新 episode 上下文，commit_physical_reset_complete
→ 返回旧 done + 新 episode observation
→ O1 开 Wnext → facade 复制旧 terminal 历史 → batch ACK
→ 本次验证结束，不为新 episode 再 claim/运动
→ 最后统一 release、stop/close、核对进程自然退出
```

拟新增 Host 的本次 terminal reset 可采用**安全最终姿态上的逻辑 episode rebuild**：机器人已 OFF+稳定，保留 actual q/q_cmd/scene clock，刷新 episode/request 身份与观测基线；不必重新播放初态或再次建 Camera。这是明确待实现的 Host reset 语义，不等同已有 `ScanMobileManipulatorEnv._reset_idx`，也不声称支持后续无限 episode。初次 reset 仍调用已接受初始化；如未来必须回初始 q，只能作为另行明确的 reset 行为与计数，不能夹在任务两点之间。

保留标准 pre-reset critic sidecar：`capture_pre_reset_critic_physical_snapshot_v2` 接真实 assignment problem、episode_progress_steps 和 scale；M1/N2 在现有公式下得到 critic schema 宽度 62。只是按已有动态 schema 构造数据，不建/改网络。不能用旧 pure fixture 的 snapshot=None 兼容口绕开 terminal 契约。

**不能掩盖的限制：** episode rebuild 强制 task AVAILABLE、robot NEEDS_ASSIGNMENT、owner=-1（S6:3722–3752）。若最后一任务 C+U、OFF 未确认，不能虚报 healthy reset 来完成 facade。仅在有效边界可提交时保留 C+U/terminal artifact 后 fail-closed；正常 reset/ACK 验证失败，旧成果仍保留。首版不新增 terminal-without-reset 协议。若 native 已无效，连这个提交也不能保证；保留已取得数据及基础设施错误，禁止追加物理凑 OFF。

同理，时间限前要预留实际 close/hold 预算：不再接受新请求，完成安全收尾后才在合法块末提交 TIME_LIMIT。达到硬上限仍不安全则 fail-stop，不在 terminal 之后额外无 admission 地推进以补证据。

## 7. 进展、失败、取消与复用范围

### 7.1 进展及调度输入来源

| 项目 | 当前可取得的真实事实 | 首版用途 [建议]；不作何种推定 |
|---|---|---|
| 运动进展 | actual position/orientation error、变化、native dq、有效 reference/guard、局部步数 | 诊断及既有 pose deadline；不因 error 非单调或某步 q 不变直接释放 |
| 到位稳定 | 121 样本、跨度≥1秒；到位后位置≤2mm、角≤0.25°、max abs dq≤0.01 rad/s（S12:27–35/123–138） | 原接受边界继续；保持丢失是明确故障，不增新感知质量门槛 |
| 等数据 | phase、ON boundary、新 product event/frame、fresh 验证、阶段剩余 budget | 允许正常等待；仅 deadline/明确异常触发本次失败 |
| 关闭 | updates=false、独立 observer、opportunity/quiet/inflight、close deadline | 禁止新动作直到 OFF；有事件不刷成“运动进展” |
| 设备/物理健康 | view validity、resource sticky/close errors、guard status | 决定可否继续/是否 U 或基础设施终止；alive 不代表健康 |
| robot lifecycle/task status | 唯一 P2 | EXECUTING/UNAVAILABLE/NEEDS_ASSIGNMENT 等来自 authority；不拿 legacy “robot IDLE”覆盖 |
| cost | 旧 env `1824–1826` 为 scanner→task 欧氏距离 | 保留几何排名定义，换 actual scanner；不是路径时长、能耗或碰撞安全 |
| feasibility | [static_feasibility.py](../../../static_feasibility.py):44–91、env `3470–3517` 的 bbox range/起始base垂向reach/FOV及人工 mask | 首版只允许已接受局部两任务，明确受限 mask 来源；旧 proxy 近似不能认证任意外部视点 |
| workload/progress/observation | S13:605/618：episode steps/horizon；P2 completion attribution count/N | 两者不是执行阶段耗时。用实际 base/scanner、冻结目标、能力参数、cost/mask + P2 构造 v2 evidence；不改旧90/96D proxy observation或网络 |

viewpoint 两目标沿已接受局部集合冻结，不运行视点生成；第一点从已接受初态，第二点从真实结束状态建立 reference，保持原 5° 信任锚与命令/实际路径守卫。已验证的两个方向不自动证明逆序或任意重新规划。异常候选只在第一点稳定保持处取消再认领同点，不新加未经核对路径。

当前 authority 没有独立 pose-stall 输入，也没有据这些细节自动重规划的逻辑。首版把阶段 deadline/健康结果映射到已有 C/R/U；阶段信息入 typed report/诊断。不能为避免 release 无条件刷新 progress，不能把旧 wrapper cost budget 拿来衡量 Camera 关闭阶段。

### 7.2 当前异常传播与所需最小复用改动

当前 `SingleViewRequest.cancel` 真实存在，但生产 runner 未接线，定向找到的调用在 `Q/test_cr12_single_view_capture.py:187`。generator close/异常没有受控减速和停止确认；不再 yield、保留最后 target、设速度零都不等于已停止。异常沿 `execute_capture_request → run_two_capture → main`，通常最终释放自有设备并关闭整个 App；不能把它描述成“只结束一个机器人请求、其余继续”。

`OwnedCameraCapture.prepare` 仅允许 max_requests 1/2，begin 要求前次有 snapshot+OFF、同 attempt_id 且新 goal/capture ID；无数据超时即便 OFF 成功也不能重开。首次 ON 前 request_off 后，_off 非空而 _request=None 也会阻止之后 begin。_errors 是资源级 sticky，_close_errors 会否决 OFF，不能 new 一个 FSM 就清除。

[建议] integration 显式允许**有限** request budget（正常2、异常候选3），新增 `retire_request`：核对 OFF、保持、健康、旧结果有效移交或明确无数据失败；保留历史与资源错误，仅退役请求局部槽。旧默认1/2及“前次成功数据”约束保持；新的 no-data retire 是单独测试/运行范围，不能直接把 max_requests 改成无限或抹去 sticky。保存要求增加显式 delivery mode：demo 默认 artifact-required；integration 为 raw-held-with-custody，绝非无条件 skip。

| 原因 | 当前实际行为 | 建议 facts / 是否复用 / 停止层级 |
|---|---|---|
| 健康 Camera 的采集 deadline | 请求失败、bounded close 后 runner 整体失败；无数据槽不能直接复用 | OFF+保持+retire 成功才 R，F=false；可再由 authority claim。首版 runtime 不同时注入此项 |
| 主动 WAITING_DATA 取消 | FSM 方法存在；实际 runner 未接 | 保持控制→真实 OFF→确认→R；资源健康才复用；作为唯一异常候选 |
| MOVING 取消 | 无制动接口；关 generator 无停止证据 | 需 STOPPING_OFF，用当前有效状态构造有界减速参考，继续成对目标/守卫，确认 dq和漂移后才 release/接单；首版不承诺可恢复此阶段，按不可继续接单/有序全局终止处理 |
| CLOSING 取消 | 无外部控制入口 | 记录原因并继续已有关闭，不重 ON/重复 OFF；已经 acquired 不清除，若成果/关闭/保持满足则 C 优先，不强行改 R |
| 路径/命令准入失败、到位保持丢失 | 原 guard 抛异常退出 | 禁止执行被拒命令；尚未动且已安全可有 R 的后续分支，首版默认 fail-stop/U（仅有效提交时），不自动永久 F，不自动换路 |
| PNG/metadata 保存错误 | acquired 可仍 true，demo终态失败并退出 | raw仍持有且OFF健康则业务可 C；本地保存失败单列。若raw丢失，保留 acquisition历史但不能声称交付成功 |
| OFF 未确认 / close sticky | STOP_UNCONFIRMED，退出；release不能算OFF | 禁止新请求；有成果可 C+U，无成果U（只在安全合法边界）；不自动重建相机恢复 |
| Camera resource sticky，但物理仍有效 | 现实现上抛 App | 不清sticky；本轮最小host只有一机器人，无继续业务价值，U后终止/保留证据；多机隔离后置 |
| native view无效/硬物理异常 | native getter禁用、停止追加physics并退出 | 不为提交正常块/OFF而继续；基础设施故障，不能虚构 C/F 或强行延迟退出 |
| App启动/私有配置/初始化失败 | 未形成可执行场景即失败 | 基础设施失败，不记任务完成率0/策略零分，不生成虚构authority任务失败 |

### 7.3 owner 被撤销、取消与数据的次序

推荐正常取消命令先发给当前 binding，在原占有下完成安全 OFF/保持，再通过 R 交由 authority 释放。adapter 不自行改 owner。若其他合法权威流程先撤销 owner，新 P2 一经观察即停止旧请求继续生产有效业务结果，旧数据封存，旧 callback 不再提交 C/R（现有 pair active-owner guard 会拒绝）；设备仍须独立执行可行的收尾。若物理/采集未安全，adapter 也不能因为 P2 出现新 assignment 就动；有效边界可提交 robot U 边沿，否则全局 fail-stop。

moving cancellation 的减速须沿用现有关节、速度、命令步增和信任域守卫；减速曲线、所需加速度约束及实际 dq/位姿漂移的连续停止确认须另行设计审定。当前 CommandIntegrator（E/_cr12_pose_control.py:430–470）没有现成通用加速度限制；这是一项额外控制能力，不把停止计数当证据。最小下一轮只实现/实测稳定等待数据阶段的取消恢复，moving 的完整可恢复停止后置，入口明确拒绝未支持的恢复承诺。native失效时的全局退出是错误处置，不报告物理已经安全停止。



## 8. 下一轮拟改文件与旧行为保护

全部是**实施方案，文件/接口本轮未创建或修改**；新文件名在审阅后落实。按一套 Host+adapter 方案列出，不作全仓启动重构。

| 拟改/新增路径 | 符号/工作内容 | 必要性及旧默认保护 |
|---|---|---|
| 新 `E/run_cr12_lifecycle_integration.py` | 私有 E1/M1/N2 composition、确定性 proposal、有限执行/退出 | 单独显式入口；复用已接受启动/private helper，不改 train/play/viewer/public gate |
| 新 `E/_cr12_lifecycle_host.py` | `CR12IntegrationHost.reset/step/bind_effective_assignment`、唯一12子步调度、实际 assignment problem、pre-reset sidecar/合法 rebuild | 一个 App/scene/clock；无旧 proxy env；正常 terminal 五元组与 ACK 兼容 |
| 新 `T/assignment_cr12_execution_adapter.py` | `ExecutionBinding`、immutable pending execution result、来源验证、continue/cancel/fact映射/交付确认 | 纯任务边界，不 import Isaac；binding 是 authority 来源引用，不写 Store/owner/completed |
| 新 `E/_cr12_scan_executor.py` | 第3节 pose session 与单次 capture runner | 真正非阻塞推进，保留唯一 DLS/integrator/q_cmd；新目标从接单时 actual 开始 |
| `E/run_cr12_pose_target.py:_pose_ticks` | 抽取 prepare/submit/observe/finish，保留旧 generator 包装 | 原 joint 命令、guard、步/render 顺序、默认参数不变 |
| `E/run_cr12_single_view_capture.py:execute_capture_request/initialize_capture_run` | 旧 while 包装新 runner；仅显式 integration 模式接健康 no-data retire/结果持有 | 原单点/双点默认保存门槛、请求数和停止行为保持；不把 integration 控制混入 TwoViewSequence |
| `E/_cr12_single_view_capture.py:SingleViewRequest` | 显式 data delivery/custody 结果，取消接线需要的状态接口 | artifact-required 为旧默认；acquired/saved/off 分离；不改感知成功阈值 |
| `E/_cr12_camera_capture.py:prepare/begin_capture` | 显式有限 request budget、`retire_request`、`peek_retained_snapshot` | 健康/no-data 安全复用新分支；保留 sticky、严格 fresh/独立 OFF，不 reinitialize Camera/product |
| `T/assignment_event_profile_runtime_domain.py` | 新 typed report、environment port 的 `finalize_execution_transition`、同管道 validation/build input | 原 staged report 默认仍为 proxy；新分支明确 F/R/U/Rc 接线，不改 C/F/R/U authority 优先级 |
| `T/assignment_event_policy_evidence.py` 与 `assignment_event_terminal_critic_sidecar.py` | physical capture 增加/透传显式 producer 来源 | 当前 `463` 硬编码 ScanMobileManipulatorEnv；保留旧默认，避免新 Host 假借旧来源；不改 critic schema/网络 |
| 新 `Q/test_cr12_lifecycle_execution_adapter.py`；已有 CR12 相关测试局部补充 | 第9节 CPU 反例及新推进/兼容边界 | 不重跑 Phase B qualification，不建新测试框架；旧基础测试只在相关抽取触及后按需回归 |

不需要更改 `assignment_lifecycle_transaction_runtime` 的 authority 决策、consume ledger、claim 规则或公共 gate。若实现发现必须改变这些已接受语义，应停止该扩展、明确报告缺口再审，而不是在 adapter 内绕过。Camera no-data retire 与有效数据持有是本轮真正提出的新执行能力，不能标成现有接口直接可用。

## 9. 下一轮最小实施与有限验证计划（本轮一律不执行）

推荐下一轮在一份明确授权内连续完成以下三步；先通过前置才继续，不为用完预算运行。

### 9.1 CPU 与结构接线

完成真实 host/adapter/nonblocking 抽取及显式 branch，以少量测试核对以下对外行为：

| 反例/检查 | 必须观察的结果 |
|---|---|
| 同 claim 多周期 continue、重复终态 | 请求/ON 各一次；completion attribution 只增一次；重复结果不再创建新 consume token 送 authority |
| 同 task/token0 release 后 token1 | 新 goal/capture identity；旧 frame/result 不改变新 P2；使用真实 production claim/transaction fixture |
| 旧 episode、非 owner、claim 来源丢失 | 在 typed report/facts 前拒绝；pending data 保留；不把 stale 事实 rebase |
| OFF 未确认、新 assignment 到达 | 无新动作/ON； acquired 不清；终止不冒充 healthy reset |
| no-data cancel/timeout OFF 后 retire | 健康才允许复用；resource sticky 保留；未开始请求关闭与有数据关闭分别处理 |
| raw-held 与 artifact-required | 真实持有者缺失则不正常交付；PNG失败不抹 acquired；旧 demo 默认保持 |
| 12子步唯一 clock、终态在子步发生 | 每块一个 admitted assignment/一次 finalize；剩余子步只保持；每 robot不自行step；terminal按真实facade复制/ACK |
| 抽取兼容性 | 成对target/提交读回、guard、render cadence、稳定判据及旧入口默认一致；不构造“和代码逐句一样”的空测试 |

这是新接入边界的必要测试，不是 Phase B 重验。测试使用现有规范化加载/契约 fixture；不为反射 import 整个任务包启动 Isaac。实现前核对授权解释器；本轮未运行 pytest、compile 或 import。

### 9.2 正常真实链

入口拟为 `E/run_cr12_lifecycle_integration.py` 的 `normal` case；配置固定一 scene、一 CR12、两个已接受局部 scanner 目标、v1/fixed base/lift0、baseline PD、dt1/120、TGS8/2、external-forces-every-iteration=on、原 guard/visual pre-init、同虚拟 RGBA Camera/product、GUI/D3D12/private/cuda:0。初始化、guard、camera按接受范围复用，不重做 Windows 或资产资格验收。

实际运行必须证明：

1. 第一次 proposal 经 resolver→production claim→P2 后才出现关节驱动；连续多个 Host transition 无重复 submit/ON。
2. 两次 acquisition 各有本次 ON 后的 source frame/data、OFF 独立确认；C 只在当期合法 facts 中一次提交，result receipt、P2 completion count 与 task attribution一致。
3. task0完成后下一 OPEN 才接受task1，从接单瞬间 actual/q_cmd 接续；Camera/product/controller/integrator 仍为同一实例。
4. 旧 proxy动作/dwell源未调用；owner/completed 只有真实 authority 写入。检查最终 task/count、旧 terminal sidecar、合法 rebuild、facade copy/ACK。
5. 最终资源一次有效释放，内部完成记录与自然进程退出同时成立；仅 exit0 或两个PNG不足以证明链通过。

### 9.3 唯一异常候选：稳定等待数据时主动取消

在 task0 已到位、`capture_started` 成为 WAITING_DATA 之后、**第一次可能产新帧的正常 render 之前**，由 case driver 对当前 binding 发一次 cancel。注入在新非阻塞请求命令边界，实际调用 OFF 并按正常 cadence 继续保持/观察；不是修改 raw frame、丢弃帧冒充硬件坏，也不制造 native 崩溃、碰撞或删除资产。

预期流程：claim token0 → ON → 主动 cancel → acquired=false（需确认此时确无有效帧）→ OFF+保持+健康 retire → typed R → authority AVAILABLE/owner=-1 → 下一 OPEN 再 proposal task0 → 新 claim token1、新 goal/capture ID → 同 Camera/product 真实新帧+OFF→C → task1完整成功→terminal/ACK。取消与数据事件若发生意外竞争，必须保留实际 acquired 并按第5节处理；**不能丢掉已获数据来满足预设“无数据取消”**，该 no-data 场景未按计划命中就不能报告此候选 PASS。

场景通过仅指：这一次主动取消被安全关闭、无虚报 C/永久 F，真实 authority 一次 release，随后新请求成功，正常 terminal 与自然退出。预期取消本身不是整个 App 失败；未知 guard/native错误、OFF失败、资源sticky、强杀、未取得后续数据、身份不符都属场景失败，不能套 expected-failure 掩盖。旧 token 迟到/重复结果主要在 CPU 反例检验，不额外制造 runtime 迟到队列。

### 9.4 预算与时间核算

现 FSM 源常量（S12:10–16）：POSE≤960、CAPTURE≤600、CLOSE≤240、TOTAL≤1800 physics tick/请求；capture墙钟60秒、close30秒。沿用这些界限。新 idle块尾保持最多额外11 tick/请求，属于 Host 持稳，不扩展已终态请求的1800预算。episode与最大physics按Host边界统一：

| 未来 case | E/M/N、最多请求 | 建议 episode/horizon | 受控 physics / Host render 上限 | App与墙钟上限 |
|---|---|---|---|---|
| normal | 1/1/2，2次合法claim/capture | 32秒 / 320 Host transitions | 3840 physics、1920 正常render；两请求1800×2+块尾<24=3624内，剩余216为有限调度/安全收口余量 | 1 App，所属进程树总300秒，含启动/关闭 |
| cancel_then_reclaim | 1/1/2，3次请求（一次无数据取消+两次成果） | 48秒 / 480 transitions | 5760 physics、2880正常render；1800×3+块尾<36=5436内，余324 | normal通过后1 App，总420秒 |
| 唯一可选局部修复重试 | 重试失败的同一case，不另加场景 | 保持该case预算 | 不放宽phase/guard/episode阈值 | 总App≤3，共享一次重试；300或420秒同case上限，不自动用满 |

初始化接受实现有 reset warm-start 的约2个physics tick，需单独读时钟核对；建议不增加隐藏settle，初始physics预算2个，故总可报告physics上限为3842/5762。terminal采用第6节逻辑rebuild不额外物理推进。Host主动render上限如表；Kit初始化内部update/render单列实际计数与300/420秒全树硬界，不能把UI update谎称受控physics/render，也不能为相机预热额外开采集。若实现沿用的初始化确需改变物理数或显式render预算，先披露来源并重新审定，不静默超额。

旧运行1324tick/全树50.672秒只作估算依据：若相同子阶段仍每请求662tick，D12向上补齐为672×2=1344tick（并非已测结果）。以最大3624/5436tick相对1324的比例作粗略工作量估计约139/208秒，再给CPU事务/同步、启动和收尾余量，建议300/420秒，**不是照搬360秒，也不是性能预测**。达到阶段/全局界限就停止，不扩到多seed/训练。申请重试前必须是明确局部问题且不涉及新authority语义/native重复崩溃；未满足条件不使用第三App。

CPU完成后再实现/核对CLI；未来入口拟支持 `--integration-case normal|cancel_then_reclaim` 并使用现有 device/camera/private/output 参数风格。**当前该入口和case选项不存在，故此报告不给伪称现成可运行的启动命令。** 下一轮实施报告必须把已核对的完整命令、工作目录、解释器、private来源、预算和实际退出写全；解释器固定 `C:/isaacenvs/isaac45_harl/python.exe`，优先 `D:/miniconda3/Scripts/conda.exe run -p C:/isaacenvs/isaac45_harl python ...`。

### 9.5 最小证据

每次未来运行仅保留：两份实际采集成果（异常case取消请求无虚构PNG）、各请求简短metadata、claim/binding与finalized result的关键身份、ON/fresh/OFF/数据持有凭据、阶段/总physics-render计数、终止/ACK摘要、原生完成和所属进程退出结果。正常continuation可聚合计数，不逐步dump tensor；保留必要的首尾/交接样本即可。

文档放 AgentRead 月/日；未来日志/JSON/数据证据按 `logs/scan_assignment/YYYYMMDD_cr12_lifecycle_integration/attempt_XX/`，由主报告关联。本轮没有这些运行产物，不制造空attempt、JSON或ZIP。启动/基础设施失败与任务业务结果分列，不记策略失败率或虚构零分。

## 10. 待审决策、未决事项与实施顺序

下一轮只需集中审阅以下三点，不再确认机器人角色、采集质量或相机通道：

| 待审事项 | 推荐决定 |
|---|---|
| 正常 authority 完成时点与文件保存 | acquired立即封存；raw实际持有/交付 + OFF + 保持确认后提交C；PNG保存独立。C+U只用于能合法提交的不可用成果分支，不承诺安全terminal auto-reset |
| 接入边界与时钟 | 私有E1/M1/N2 Host + 真实domain/facade，dt1/120、D12、render2；typed report扩展与显式backend，public gate不变；安全终态采用实际末姿态上的逻辑episode rebuild |
| 下一轮实现/运行范围 | 可在一轮授权中先正常接入、再唯一WAITING_DATA取消/无数据retire/同task新claim候选；moving可恢复制动、sticky恢复、多机、任意路径后置；预算按第9节 |

真实实施缺口是：非阻塞抽取/连续实际控制、claim来源绑定和结果确认、typed执行report接线、数据有效持有与healthy no-data retire、真实Host pre-reset/terminal/rebuild。无需重新提供被删除旧USD、重新证明资产/IK/visual、做实体标定或新增视点生成。

只需后续运行确认：D12 authority开销是否在墙钟内；真实fresh/OFF跨Host边界的时序；取消位置确未采到数据；同Camera三次请求健康复用；原控制/guard保持；正常terminal后逻辑rebuild和facade ACK。局部工程事项包括 evidence producer来源、数据 custody接口，以及旧累计pose极值不是每段专属极值、metadata“at/after ON”与双点严格大于检查的文字差异；后两项仅在相关实现触及时修正，不重开相机验收。

建议顺序：审阅本方案 → 最小接口/CPU反例与旧默认保护 → 正常真实authority单机双任务 → 唯一稳定取消恢复候选 → 另行决定多机器人和MRTA研究接入。单机通过仍不证明多机仲裁/重分配能力，不自动解封训练或public入口。

## 11. 本轮操作、限制与辅助证据

本轮实际执行：读取用户任务、适用 `AgentRead/AGENTS.md`、当前 TASK_PROGRESS/REPORT_INDEX、双视点报告及必要单点背景；定向 `rg` / PowerShell 读取上述源码、接口测试定义和配置；只读 HEAD、相关工作区/index状态；文本整理字段、调用链与步数预算。历史记忆仅用于 pre-reset/authority 导航，关键结论重新核对当前源码。没有为了离线检查启动 Python、import 任务包或创建分析脚本。

局部不存在的候选路径（如 `scripts/tests`、假定的个别模块名）已改用定向符号定位，不安装依赖或扩大到全盘。没有全仓资产/哈希/历史链接审计，没有恢复旧USD/checkpoint/raw evidence。旧未提交启动文件、CR12实现与未跟踪报告保留；原index中的历史cleanup ZIP删除未碰。HEAD和index写操作均无。

辅助证据表（本轮无新辅助文件）：

| 结论 | 实际文件位置 | 定位与限制 |
|---|---|---|
| 已接受双点运行范围 | [双点主报告](CR12_TWO_VIEW_CAMERA_CAPTURE_REPORT.md) | 同scene/product、1324步、各fresh/OFF、数据保持/退出；本轮未重跑 |
| acquired/saved/OFF历史边界 | [单点主报告](CR12_SINGLE_VIEW_CAMERA_CAPTURE_REPORT.md) | 独立正常运行及原失败保留；不证明authority恢复 |
| authority当前输入/消费/终止 | 第1.1节 S1–S9 链接 | 当前源码事实，不能冒充新Host运行PASS |
| Camera无数据复用及sticky限制 | 第1.1节 S11/S12 | begin/observe_close/FSM实际分支；第5、7节给出缺口 |
| 请求cancel与double-view接口测试 | [单点FSM测试](../../../../../../../../source/isaaclab_tasks/test/test_cr12_single_view_capture.py)、[双点测试](../../../../../../../../source/isaaclab_tasks/test/test_cr12_two_view_capture.py)、[Camera测试](../../../../../../../../source/isaaclab_tasks/test/test_cr12_camera_capture.py) | 仅定向读取；测试定义/名称不等于本轮运行，也不等于真实恢复已接线 |
| continuation/claim/terminal 直接契约测试 | [I4-2 proposal/commit](../../../../../../../../scripts/environments/test_assignment_phase_b1w_i4_2_proposal_effective_commit_pure.py)、[B1 initial claim](../../../../../../../../scripts/environments/test_assignment_phase_b1_initial_claim_transaction_pure.py)、[I4-3 terminal handoff](../../../../../../../../scripts/environments/test_assignment_phase_b1w_i4_3_terminal_wrapper_handoff_pure.py) | 本轮只读：I4-2:486/640/655 continuation与stale；B1:431/585 stale/replay；I4-3:277/380/388历史/当前分离、public gate与旧None兼容；未运行历史验收 |
| 当前交付规则/导航 | [AGENTS](../../AGENTS.md)、[TASK_PROGRESS](../../TASK_PROGRESS.md)、[REPORT_INDEX](../../REPORT_INDEX.md) | Markdown主报告自足、历史接受范围和本轮停止边界 |

## 12. 文档变更与停止

1. 新增本报告 `AgentRead/202610/20261007/CR12_EXECUTION_LIFECYCLE_INTEGRATION_PLAN.md`。
2. 小范围更新 `AgentRead/TASK_PROGRESS.md`：记录双点已获用户/GPT审阅、独立最小闭环完成、本轮接入分析与未实施状态、报告链接；历史待审/FAIL段落保留当时表述。
3. 小范围更新 `AgentRead/REPORT_INDEX.md`：扫描执行主题关联新方案；Phase B主题仅加接入分析关联，不重写已关闭结论。

本轮仅文档修改；未实施 adapter/Host/恢复接口，未改生产代码、测试、配置、资产、authority或学习器。未启动 Isaac/CUDA/GUI/渲染/仿真，未执行测试、训练、推理、checkpoint、Git写操作或历史清理。

文档核对结果：本报告38个相对链接均能定位；Markdown代码围栏成对。TASK_PROGRESS的3处局部块与REPORT_INDEX的5处局部块逐字符合预期修改，未发生整篇重写；TASK_PROGRESS的Git空白检查通过。只读复核HEAD仍为上述提交，index仍仅保留原有cleanup ZIP删除。此处是文档核对结果，不是实现或运行PASS。

**CR12 扫描执行层与 lifecycle authority 接入分析及最小实施方案已完成，等待 GPT/用户审阅；尚未实施、尚未进行集成运行验证。返回报告后停止。**

