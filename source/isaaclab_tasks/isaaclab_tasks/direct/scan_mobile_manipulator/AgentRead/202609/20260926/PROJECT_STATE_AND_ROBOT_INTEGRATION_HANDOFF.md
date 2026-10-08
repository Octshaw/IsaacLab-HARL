# 项目现状与目标机器人接入交接

日期：2026-09-26（Asia/Shanghai）。仓库：`E:\Project\IsaacLab_HARL`。
本次范围：源码、配置、资产引用及保留文档的静态梳理；未运行、未重新验证 Phase B，未实施下一阶段。

## 1. 当前状态摘要（新窗口先读）

**Phase B 保持 COMPLETE / GPT REVIEW PASS / CLOSED；目标机器人执行与扫描设备接入尚未完成。** 已关闭的是给定视点集合上的、固定规模的 lifecycle-aware dynamic MRTA 学习/runtime/优化状态续训骨干。它运行于真实 Isaac/HARL 进程，机器人运动仍采用任务空间代理。`real Isaac runtime` 不代表实体机器人已连接，也不代表目标机器人关节和传感器已经接通。

- 已具备：proposal 与 effective assignment 分离、环境拥有的 claim/complete/release 等 lifecycle authority、P2 发布与步进准入、事件决策/DVM、pre-reset terminal transport、真实 actor/critic/Adam/ValueNorm 更新、重复更新及完整优化状态保存/跨进程继续更新的验收证据。失败/释放语义存在，但当前 event 环境的实际故障 reporters 尚未接入，见第 4 节。
- 当前执行：离散任务分配转换成每机器人 9D 归一化增量；直接更新底盘位置/yaw、扫描头位置/四元数张量，臂展球面裁剪；USD marker/OBJ 跟随显示。没有当前任务中的真实关节驱动、底盘动力学、IK 或扫描仪采集链。
- 当前扫描完成：位置、姿态、球形臂展、bbox 量程、方向/FOV 条件连续满足驻留步数，再由当前 owner 限定归属。没有点云、图像、跟踪仪测量或设备完成回执参与。
- 目标模型：发现 `ScanRobot.obj/.mtl`、一个二进制 `ScanRobot.usd.back`、proxy/capability YAML；OBJ 是外观，USD 备份内部结构和目标设备对应关系 UNKNOWN。不能据三个 actor 槽位认定最终有三台实物，也不能从旧构型设想确定当前设备方案。
- 当前入口：已验证的 callable 是 `execute_real_isaac_single_transaction_v1 → execute_full_learner_transaction_v1`。公共 train/play 对 event profile 仍有显式阻断；通用 `runner.run/train/restore` 不等价于已验证 event 路径。
- 建议先讨论：确认目标设备/角色、资产对应、坐标变换和执行/扫描反馈契约，然后选一台目标机器人、一个视点作为仿真接入最小单元。可并行整理显式 event 系统入口。无需先连接全部实体硬件，也不自动开始论文实验。

四个工程提交和已批准清理已完成。旧 raw artifacts 与 smoke checkpoint 的获准删除不构成回归，不恢复、不重建、不检查旧目录库存。下一阶段均为候选，等待用户/GPT讨论与后续授权。

## 2. 证据口径与阅读起点

本文标记：**S**＝当前源码/配置/文件直接确认；**R**＝保留运行记录确认（本次只读，未重跑）；**H**＝仅历史设计/报告陈述；**I**＝合理推断或建议，未验证；**U**＝仓库无法确认，需要用户资料。实现存在不等于已验证，文件存在不等于已加载，通信代码存在也不等于硬件在线。

先读适用的 [AGENTS.md](../../AGENTS.md) 和 [TASK_PROGRESS.md](../../TASK_PROGRESS.md)，再按现有链接读取：

- [20260925 implementation summary](../20260925/PHASE_B_IMPLEMENTATION_CHANGE_SUMMARY.md)：当前生产模块与历史提交范围；其中“pending/uncommitted”是提交前文字。
- [20260924 readiness audit](../20260924/PHASE_B_FINAL_CLOSURE_READINESS_AUDIT.md)：源码/证据边界；其待做的最后 smoke 已由后续报告和用户验收关闭。
- [20260924 final closure report](../20260924/PHASE_B_FINAL_CLOSURE_REPORT.md)：真实 A-save/fresh-B-load/B-update 证据；其 AWAITING-GPT-REVIEW 是历史标签，当前接受状态以用户说明和 TASK_PROGRESS 为准。
- [20260925 最新已完成清理报告](../20260925/PHASE_B_LOCAL_ARTIFACT_CLEANUP_EXECUTION_SINGLE_ABSENCE_REPORT.md)：删除结果、保留证据和已接受的不可重放边界。

本次另直接读取少量明确保留的 compact JSON：[final_result](../20260924/phase_b_final_closure_artifacts/final_result.json)、[effective_config](../20260924/phase_b_final_closure_artifacts/effective_config.json)、[A update](../20260924/phase_b_final_closure_artifacts/process_a/update_result.json)、[B update](../20260924/phase_b_final_closure_artifacts/process_b/update_result.json)、[跨进程状态相等](../20260924/phase_b_final_closure_artifacts/cross_process_state_equality.json)、[B continuity](../20260924/phase_b_final_closure_artifacts/process_b/continuity_result.json)。未读取 checkpoint tensor，未重建已删数据，未重算历史全量 ledgers。

这些记录支持 G1–G10 PASS；A actor steps=(5,5,5)、critic/VN=10/10，保存后新进程 B 严格恢复，再按 B 自己的计划执行 (5,5,10)、critic/VN=10/10；Adam 继续至 (10,10,15)/20，progression 从 completed1/next2 到 completed2/next3，B 的 10 次 VN recurrence 相等。固定条件为 rollout T=2、E=2、M=3、N=12，环境 horizon=30秒/300步。**最终 A/B 各只采集两步，正常 horizon 的结论来自此前验收及 readiness audit 的历史证据梳理；不能把最终 smoke 写成另一轮完整 horizon 验证。**

本文源码简写 `T/`＝`source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/`，`R/`＝仓库根。行号针对本次 HEAD；第 7 节提供关键文件链接。

## 3. 实际调用链与模块表

```text
builtin fixed12 或外部固定N CSV（含扫描头目标位置/姿态）
  → env.get_assignment_problem：proxy物理状态、几何可行性、欧氏代价
  + 当前环境生命周期 Store / P2 / inter-step window
  → event evidence / policy decision：合法任务、forced continuation、DVM
  → actor proposal（保留原动作和行为logprob）
  → EventProposalAdapter / claim authority → 最终 effective assignment / P2
  → P2准入 → viewpoint_assignment_to_actions → 9D proxy增量
  → env._pre_physics_step / _integrate_high_level_actions → 张量运动
  → 几何scan candidate + dwell → pre-reset物理报告
  → owner限定的ExecutionTransitionInput/Facts → lifecycle authority / P2
  → complete/eligible decision reopening；终止历史与reset后当前状态分开
  → 下一次collect_step；rollout满后 reviewed event learner → S0–S10
```

| 模块/能力 | 实际文件与符号 | 输入/输出 | 当前实现方式 | 已有证据 | 缺口 |
|---|---|---|---|---|---|
| 视点输入 | `T/viewpoint_csv.py:56 load_fixed_viewpoint_csv`；`env.py:1150 _prepare_viewpoint_cfg`（此表 env.py 指完整环境文件） | CSV/内置七元pose → 固定N pose、连续ID | 严格 world/meter/WXYZ 扫描头位姿；没有在线视点生成 | S；final R 使用内置12点 | 目标设备坐标/标定关系 U；外部N50不等同已验收fixture |
| 环境与机器人状态 | `T/scan_mobile_manipulator_env.py:1473 __init__`、`:1815 get_assignment_problem` | cfg → base/scanner张量、覆盖、mask、cost | task-space proxy；legacy problem内的task/robot status只是简化占位 | S；该环境用于 R | lifecycle真值必须来自P2，不能拿legacy status替代 |
| 事件观测/决策 | `assignment_event_policy_evidence.py:_project_common_blocks`；`assignment_event_policy_decision.py:569`附近 | 同代P2/物理状态 → actor/critic输入、legal actions、DVM | NEEDS_ASSIGNMENT且有合法任务才采样；EXECUTING强制续当前任务；无合法任务强制no-op | S、已接受R | 当前固定规模；不是Transformer/可变规模实现 |
| proposal/resolver/P2 | `assignment_event_proposal_adapter.py:EventProposalAdapter`；`assignment_event_runtime_facade.py:609 step_resolved_proposals`；`assignment_initial_claim_runtime.py:647 derive_candidate` | proposal → 零或一次claim batch → 最终P2 | 原proposal/logprob用于学习；effective assignment用于控制；唯一owner与版本准入 | S、已接受R | 外部执行器必须消费权威分配，不能自行改owner |
| 执行桥 | `assignment_event_profile_synchronous_runtime.py`；`assignment_controller.py:39 viewpoint_assignment_to_actions` | P2 assignment [E,M] → 按agent名9D动作 | 位置差/欧拉角差、步长缩放与clamp | S；现有R经过该桥 | 没有目标设备action backend |
| 运动与显示 | `env.py:2934 _pre_physics_step`、`:2949 _integrate_high_level_actions`、`:2980 _apply_action` | 9D → proxy状态 → 可视Xform | 直接加增量；扫描头与底盘独立张量；臂展球裁剪；无simulator侧机器人actuation | S、proxy环境R | 无关节目标/力矩、底盘驱动、FK/IK或碰撞约束 |
| 扫描/完成 | `env.py:3065 _compute_scan_candidate`、`:3100`附近覆盖更新；`assignment_event_profile_runtime_domain.py:1484 _build_transition_input` | 几何+dwell → [E,M,N]完成候选 → owner限定完成 | 模拟谓词、连续步数、当前任务owner限定 | S；正常horizon完成/reopen由已接受历史R支持 | 无实际扫描数据/质量验收/设备回执 |
| 生命周期反馈 | `assignment_lifecycle_authority_runtime.py:ExecutionTransitionInput/EnvironmentExecutionFactsProducer`；`assignment_lifecycle_transition_contract.py:ExecutionTransitionFacts`；`assignment_lifecycle_transaction_runtime.py:LifecycleAuthorityTransactionCoordinator` | pre-reset事实 → complete/release/failed pairs/robot状态/P2 | 带env/episode/transition身份、consume-once与owner校验 | S、已接受R；故障源边界见下文 | 当前event故障/强制释放/不可用/恢复输入为false；设备异步反馈尚无适配 |
| terminal/reset | `env.py` pre-reset report；`R/source/isaaclab/isaaclab/envs/direct_marl_env.py:389`附近 | 终止前状态 → 历史terminal transport；随后reset当前状态 | 不以reset后状态重建历史；timeout bootstrap与true terminal区分 | S、已接受R | 外部执行反馈未来必须保留此时序边界 |
| event学习更新 | `assignment_event_training_real_isaac_adapter.py:1001` → `assignment_event_training_full_transaction.py:996` | rollout、既有learner、冻结计划 → actor/critic/VN更新、rollover、S10 | 真实PPO/HAPPO factor、active AND DVM、event returns，保留优化器 | S、直接保留R | 日常可配置event入口未整合；不代表策略收敛/质量 |
| 优化状态续训 | `assignment_optimization_checkpoint.py:512/652/805` save/validate/load；progression tracker | clean边界完整状态 ↔ checkpoint | 模型/Adam/VN/config/progression/LR，严格验证、失败回滚/poison | S、直接保留R | 不含仿真/RNG轨迹恢复；已删旧tensor不可加载 |

## 4. 视点、控制、反馈与近似的详细边界

### 4.1 当前实际输入与坐标

默认 `ScanMobileManipulatorEnvCfg` 的 `robot_config_path=None`、`viewpoint_csv_path=None`，因此 final closure 构造使用 legacy 三个 proxy 与内置 `viewpoint_poses` 12点；**默认仍读取 capability profile YAML**，不能笼统说“不读取配置文件”。算法 YAML 默认 train rollout T=1000、E=20、linear LR=false；final closure 则明确改成 T=2、E=2、linear LR=true、优化/LR计划total_updates=12（环境episode horizon仍为30秒/300步）。受控运行配置与仓库默认配置分开理解。

外部视点通过 `scenario_config.py` 的 load/apply，或配置 `viewpoint_csv_path`，进入 `_prepare_viewpoint_cfg → load_fixed_viewpoint_csv`。例如 [algorithm_proxy_component_mesh.yaml](../../../configs/scenarios/algorithm_proxy_component_mesh.yaml) 指向 `configs/viewpoints/component_mesh_jittered_n50.csv`、`robots_real_proxy.yaml` 和 capability YAML；它是独立的 algorithm visual debug 场景，**不是 final closure 的输入**。已有CSV还包括sample6、real_component_bbox_sample（场景声明24点）、synthetic smoke N50/N100/N200。离线生成入口为 `scripts/environments/generate_synthetic_viewpoints.py`、`generate_bbox_viewpoint_csv.py`、`generate_mesh_viewpoint_csv.py` 及 `configs/scenarios/generate_*.yaml`，只是给定集合的准备工具；本次未执行，视点生成不作为本阶段研究贡献。

测试fixture另有两类：`scripts/environments/test_viewpoint_csv_loader.py` 默认用sample6 CSV走同一loader；`test_assignment_event_gated_mrta_contract.py` 的nominal/local request fixture直接构造张量/契约字段，不能当作外部视点或设备入口。final closure则直接使用cfg内置fixed12。不存在“所有测试都读取外部CSV”的统一入口。

CSV格式 `scanner_pose_world_quat_wxyz_v1` 明确：米、world、`qw,qx,qy,qz`、scanner +X forward/+Z up、四元数表示扫描头坐标系在world中的姿态；ID必须从0连续且按行排列。位置和姿态都被消费：控制器同时用目标位置及姿态差，scan predicate同时用位置/四元数误差与方向，event观测也包含task quaternion，绝非仅位置分配。

环境内部 `viewpoint_pos_local`、`base_pos`、`scanner_pos` 是每个克隆场景的公共局部坐标；显示和部分几何计算给机器人与视点都加 `scene.env_origins`。CSV的“world”在此按单场景模板使用，再做环境平移复制。底盘初始四元数仅取yaw；扫描头初始化为 `base_pos + scanner_start_offsets`，未按base yaw旋转offset，scanner quaternion初始为identity；后续与底盘独立积分并做球面限制。**没有 world→真实底盘→机械臂法兰/TCP→扫描头的完整标定/FK链**；真实设备轴向、手眼变换、单位/时间戳与外部视点世界系的配准均 U，不能以可视OBJ偏移替代标定。

### 4.2 实际运动、阶段与完成

`viewpoint_assignment_to_actions` 把分配的任务索引映射到目标pose；无效、已覆盖或不可行目标输出0。9维为 `[base_dx, base_dy, base_dyaw, ee_dx, ee_dy, ee_dz, ee_droll, ee_dpitch, ee_dyaw]`，底盘XY朝视点移动、yaw朝视点，扫描头位置和姿态同时跟随。这些是每控制步归一化增量，不是设备速度、关节目标或力矩。默认控制间隔约0.1秒；不同最大步长是proxy速度差异，不能直接当实物额定速度。

`_integrate_high_level_actions` 直接改变状态；`_apply_action` 只同步debug可视化。`NAVIGATING/ALIGNING` 存在于枚举及active集合，claim写入 `CLAIMED`；当前控制器没有按“导航完成→对准完成→启动扫描”分阶段驱动设备。状态名称不构成导航栈或扫描触发器已实现的证据。

完成要求：扫描头位置误差、四元数角误差、目标到base的臂展距离、扫描头到bbox表面的量程、扫描头forward与目标forward的FOV方向条件同时满足，连续满足 `dwell_steps`（当前默认1）后形成候选。没有射线遮挡/实际表面采样、真实传感器采集帧/数据回执、点云密度或设备测量质量判据。构件OBJ只是可视化，扫描仍针对bbox几何代理。

### 4.3 反馈来源、身份与未接通信号

当前 event 路径在 autoreset 前封存几何完成候选、覆盖状态和timeout等报告；`_build_transition_input` 用 active task 和当前owner匹配筛选完成。Facts绑定 env_id、episode_generation、transition_generation、consume-once token；authority校验C/F/R只能作用于当前合法owner。episode 30秒超时是环境 time-limit，**不是单次设备执行超时**。

当前生产适配器 `assignment_event_profile_runtime_domain.py:1530–1558` 将 `terminal_pair_failure_signals`、`forced_release_signals`、`robot_unavailable_signals`、`robot_recovered_signals` 默认构造为false。所以可以确认 lifecycle 有失败/释放/failed-pair排除语义，不能确认真实卡滞、设备故障、失联恢复已驱动它们。测试注入或纯contract证据也不能替代真实reporter。

旧 wrapper/cooldown 路径另有 `_budget_expected_and_limit_steps`：以 `ceil(欧氏距离/max_base_xy_step)` 估算步数，再乘multiplier加slack，结合重复未进展/streak形成预算失败proxy；旧 `assignment_lifecycle.py` 还有诊断性的 `budget_failure_proxy`。event wrapper初始化禁用这些legacy guardrails且legacy resolver为None（`assignment_harl_wrapper.py:326–388`）。它们与已验收event环境的实际输入要分开；不能直接声称旧预算逻辑已经成为event真实故障源。

完成张量绑定robot/task，authority绑定本次环境transition；但未发现面向异步设备的command ID/attempt UUID、反馈时间戳及迟到回执处理协议。`dwell_counter[E,M,N]` 根据每步几何候选连续累加/清零，并在episode reset清零，未按每次claim单独建立设备attempt。它不能自动证明外部异步回执属于本次执行。未来适配至少需要：权威分配及目标pose→可取消/暂停的执行命令；实测base/TCP/scanner状态和身份/时序；进展、到达、扫描完成/失败、不可用/恢复等反馈；再由环境拥有的producer转换成同代facts，让既有authority发布P2，不能在设备回调中直接改owner。这是 I/后续接口建议，并非已实现。

### 4.4 代价、可行性与工作负载

| 项目 | 当前公式/模块 | 性质与限制 |
|---|---|---|
| 路径/排序代价 | `env.get_assignment_problem:1826`，`norm(scanner_pos - viewpoint_pos)`；event evidence按env_spacing归一化 | S：三维欧氏距离，未做导航路径、绕障、时间或能耗规划；代价不能代替可行性 |
| 静态可行性 | `static_feasibility.py:25 generate_static_geometric_feasibility` | S：视点到bbox表面距离在量程内；视点高度相对base起点不超arm_reach；目标朝向面向bbox并满足FOV。明确不调用IK、碰撞、关节限位或真实articulation |
| 固定fixture例外 | `env._build_static_feasibility` 与 `_apply_fixed_12_manual_feasibility_override` | S：内置12点另屏蔽robot_2/viewpoint5；是固定fixture控制可行性例外，不能推广为目标机器人的运动学知识 |
| 实际执行约束 | `env._integrate_high_level_actions` | S：扫描头距base超过arm_reach则裁到球面；不是多关节可达域或碰撞安全保证 |
| workload | `assignment_event_policy_evidence.py:618` | S：每机器人P2完成归属数/N；不是未来待执行队列、负载、预计服务时长或剩余工作量 |
| 障碍/冲突 | `component_obstacle_footprint.py`、`env._mesh_footprint_obstacle_fields`、`solvers/conflict_aware_solver.py` | S：可选OBJ二维footprint、线段穿越诊断、欧氏距离+固定惩罚；另有selected-target top-k组合基线。未产生物理碰撞/避障轨迹，当前event几何cost仍取原cost_matrix |
| robot权重 | `robot_config.py` 的speed_weight/cost_weight | S：配置/诊断/初始条件元数据中可见；当前运动缩放由capability步长决定，cost仍为原欧氏距离，未见这些权重参与上述公式 |

nearest按机器人顺序选择可用最短距离，greedy用逆距离评分并排重；不是全局路径规划或完整调度最优解。本次不新增路径、IK或避障算法。

## 5. 目标机器人接入程度：四层分别说明

| 对象/能力 | 目标是什么 | 当前实现 | 当前是否接到主链 | 证据位置 | 后续缺口/用户待确认 |
|---|---|---|---|---|---|
| A：设备身份/数量/角色 | 用户最终设备及扫描、辅助定位等职责 | 默认robot_0/1/2与三个actor槽位；YAML可配置enabled顺序 | 接入的是逻辑槽位，不是实物身份 | S：`env.possible_agents/_prepare_robot_config_cfg`；`robot_config.py` | U：最终数量、型号、谁扫描/谁只辅助定位；不得从旧三机器人设想推定 |
| A：机器人外观资产 | 可核对尺寸/外形的目标模型 | `assets/scene/robots/robot_visual/ScanRobot.obj`及`.mtl`；各槽可共用同一OBJ | 仅可选显示；不是执行模型 | S：`env.add_robot_obj_visual:2363`、`UsdGeom.Mesh`；`robots_real_proxy.yaml` | U：是否对应目标设备、CAD来源、精度；OBJ不定义可用关节/执行器 |
| A：USD/URDF/关节/执行器 | 目标可驱动的仿真构型 | `ScanRobot.usd.back`存在；只读文件头为PXR-USDC二进制。任务资产/配置检索未发现已引用目标URDF/ArticulationCfg链 | USD备份未发现主链引用；当前env明确不spawn真实articulation | S：备份文件头、`env:152–157/2157`；内部内容U | 未通过USD静态语义工具解析，内部joint、actuator、单位均UNKNOWN；不为查看资产启动Isaac |
| A：robots_real_proxy配置 | 将设备构型绑定场景 | 全部model_type=task_space_proxy；visual_usd_path仅metadata；三条robot_0/1/2_visual.usd路径当前不存在 | proxy/capability可接；这些USD路径不用于spawn | S：[robots_real_proxy.yaml](../../../configs/robots/robots_real_proxy.yaml)、`robot_config.py` | 已存在配置名“real”不代表真实资产已加载；缺失可选metadata路径不升级为Phase-B阻断 |
| B：底盘/机械臂/扫描头控制 | 用实际运动学、驱动和状态完成目标pose | XY/yaw底盘proxy、独立6D扫描头proxy、球形arm_reach | proxy接主链；目标关节/底盘执行器未接 | S：controller及env积分；R仅确认proxy执行链 | 目标底盘/飞行平台类型、joint/link、限位、执行接口、反馈读取；当前无飞行控制链 |
| B：异构性 | 表达不同机器人实际能力 | mobile_scanner_a/b/c的臂展、量程/FOV、容差、最大步长不同 | 参数确实影响动作、mask、完成及观测 | S：[capability YAML](../../../configs/capabilities/mobile_scanner_profiles.yaml)及env | 目前是同类proxy的能力参数差异；无不同真实运动学/实际传感器模型证据 |
| C：扫描任务闭环 | 把scanner目标pose转换为运动并确认扫描有效 | 消费位置与姿态，几何+dwell完成；构件bbox代替真实表面 | 已接proxy闭环；真实扫描闭环未接 | S：viewpoint CSV/controller/scan candidate；R为proxy完成 | U：TCP/scanner外参、到达容差、启动/停止扫描、有效数据/质量完成条件 |
| C：跟踪仪/辅助定位角色 | 支持目标设备定位但未必承担扫描 | 当前每个enabled slot都按同类scanner任务代理处理 | 未发现专用跟踪仪观测、只定位不扫描的角色分支 | S：统一动作/controller及capability配置 | U：是否有辅助设备、是否需独立agent或仅提供状态；不强制假定构型 |
| D：实体接口与连接证据 | 状态读取、命令发送、确认与故障处理 | 本次任务源码、scripts及source文本检索未发现目标设备驱动、ROS通信、serial/socket或厂商SDK接入链 | 未确认接入；用户明确真实机器人尚未接入 | S：检索范围内未发现；U：仓库外驱动/设备运行情况 | 获取现有协议/驱动资料；不自动选ROS2或某SDK，不连接设备 |
| D：暂停/取消/失联 | 处理命令生命周期和设备不可用 | lifecycle有forced_release/unavailable/recovered事实槽位；当前生产reporter为false | 语义接口存在；设备控制入口未发现 | S：`runtime_domain._build_transition_input` | 需要设备级取消确认、暂停恢复及失联定义；不能把no-op或逻辑release当设备已停止 |

资产静态检查局限：未加载二进制USD、未打开Isaac验证关节/碰撞/材质；没有据文件名推断它的机器人型号或可驱动性。`robots_real_proxy.yaml` 中mesh scale=0.001是显示参数；三个槽共用mesh也不能证明三个目标设备相同。默认cfg允许mesh/debug USD创建；headless条件限制可视刷新，不应写成“headless完全不创建USD”。外部 `algorithm_proxy_component_mesh.yaml` 当前明确选robot_visual_mode=debug_marker，故该场景也不能据mesh路径存在便认定加载机器人OBJ；只有选择mesh模式且路径可用才创建对应外观。[保留资产说明](../../../assets/scene/README.md)也将OBJ定位为显示、USD路径定位为未来metadata。

角色关键词的有限文档检索未定位到可作为最终设备依据的构型资料。即便另有较早的三机器人、飞行平台或跟踪仪设计，也只能先作为H类意图，待用户确认后才能形成当前设备需求；本报告不替用户确定构型。

## 6. 当前入口、运行模式和复用位置

| 入口 | 状态 | 用途与边界 |
|---|---|---|
| `assignment_event_training_real_isaac_adapter.execute_real_isaac_single_transaction_v1` → `assignment_event_training_full_transaction.execute_full_learner_transaction_v1` | **有保留运行证据** | 已完成rollout的reviewed event更新；调用者仍需组装环境、learner、collection、progression及退出流程 |
| `scripts/environments/test_assignment_phase_b_final_closure.py:226 construct / :301 learner_run` | **历史入口，有保留运行证据** | 受控A/B一次更新、保存、恢复；固定fixture/输出/source freeze，作为来源参考保留，不继续堆叠下一阶段产品功能 |
| `assignment_optimization_checkpoint.py` save/validate/load；`assignment_harl_training.py:799/847/874`完整状态API/LR helper | **模块有保留运行证据；runner集成仅源码定位** | final event evidence直接调用checkpoint module；caller必须消费保存的next/total/LR，不能只恢复权重 |
| `scripts/reinforcement_learning/harl/train.py`；runner `.train/.restore` | **仅源码定位，未验证为等价event入口** | train调generic runner.run，runner.train仍super().train；restore是显式确认的weights-only continuation，可恢复模型与适用ValueNorm，但不恢复完整Adam/训练进度/LR续训状态 |
| `scripts/reinforcement_learning/harl/play_assignment.py` | **仅源码定位，未验证** | 有assignment checkpoint playback实现；event profile在AppLauncher前被preflight阻断 |
| `scripts/environments/view_scan_assignment.py:77 main`；`evaluate_scan_assignment.py` | **历史基础接口，仅源码定位，未验证** | baseline solver→controller→env的viewer/evaluation；viewer不具备scenario-config CLI，不能把它当新的event训练/目标机器人demo入口 |
| `__init__.py`注册 `Isaac-Scan-Mobile-Manipulator-Direct-v0`；`ScanMobileManipulatorEnvCfg`；`scenario_config.py` load/apply；robot/capability YAML | **仅源码定位；默认cfg构造有保留R** | 环境和场景配置模块可复用；各外部场景/资产配置不因默认fixture通过而自动获得运行验证 |
| 日常可配置event训练/完整恢复/演示一体入口 | **尚未发现现成入口** | 公共event gate仍存在；需要后续明确授权下整理，不能称已解封或作为新的Phase-B失败 |

公共阻断的当前源码证据：`scenario_config.py:353 preflight_assignment_lifecycle_profile_runtime_primitive` 在约385行拒绝 `event_gated_local_mrta`；train约100行和play约177行调用。`assignment_profile_contract.py`的registry仍保留interface-only/PHASE_A_BLOCKED/BLOCKED标签，private route descriptor为 `private_test_only_dormant`。这些是入口发布范围，不推翻已经接受的callable backbone结果。

下一阶段应复用环境cfg、scenario/robot/capability解析、环境拥有的domain/Store、P2准入、`_compose_event_assignment_harl_wrapper`、`EventDormantLearnedPolicyRouteV2`、event schema/critic buffer、reviewed adapter/transaction、optimization checkpoint/progression，以及既有HARL HAPPO/VCritic/ValueNorm构造。历史final harness可用于理解组合顺序；不能继承其冻结authority、旧输出路径或整目录inventory作为新系统的启动条件。需要产品级入口时，应新建清晰的组合层并明确profile授权，勿绕过现有gate。

本次不提供猜测性启动命令。[final closure report](../20260924/PHASE_B_FINAL_CLOSURE_REPORT.md) 已保留当时实际运行的preflight/`--run`命令及证据；这些是历史记录，不是清理后的现成恢复方案，也不在本次执行。

## 7. 关键源码索引（按下一步用途读取）

| 用途 | 文件与关键符号 |
|---|---|
| 场景、proxy、反馈替换边界 | [scan_mobile_manipulator_env.py](../../../scan_mobile_manipulator_env.py)：`ScanMobileManipulatorEnvCfg`、`_prepare_robot_config_cfg`、`_prepare_viewpoint_cfg`、`_setup_scene`、`get_assignment_problem`、`_integrate_high_level_actions`、`_compute_scan_candidate`、pre-reset report |
| 目标pose到当前控制 | [assignment_controller.py](../../../assignment_controller.py)：`viewpoint_assignment_to_actions` |
| 输入与构型 | [viewpoint_csv.py](../../../viewpoint_csv.py)：`VIEWPOINT_CSV_CONVENTIONS/load_fixed_viewpoint_csv`；[robot_config.py](../../../robot_config.py)：`RobotSpec/load_robot_config`；[scenario_config.py](../../../scenario_config.py)：load/apply/preflight；[capability_config.py](../../../capability_config.py) |
| 当前几何近似 | [static_feasibility.py](../../../static_feasibility.py)：`generate_static_geometric_feasibility`；[component_obstacle_footprint.py](../../../component_obstacle_footprint.py)：二维footprint诊断 |
| P2到控制及反馈入口 | [assignment_event_runtime_facade.py](../../../assignment_event_runtime_facade.py)：`step_resolved_proposals`；[assignment_event_profile_synchronous_runtime.py](../../../assignment_event_profile_synchronous_runtime.py)：P2步进准入；[assignment_event_profile_runtime_domain.py](../../../assignment_event_profile_runtime_domain.py)：`_build_transition_input` |
| 生命周期所有权 | [assignment_initial_claim_runtime.py](../../../assignment_initial_claim_runtime.py)：`InitialClaimDeriver`；[assignment_lifecycle_authority_runtime.py](../../../assignment_lifecycle_authority_runtime.py)：`ExecutionTransitionInput/EnvironmentExecutionFactsProducer`；[assignment_lifecycle_transition_contract.py](../../../assignment_lifecycle_transition_contract.py)：`ExecutionTransitionFacts`；[assignment_lifecycle_transaction_runtime.py](../../../assignment_lifecycle_transaction_runtime.py)：`LifecycleAuthorityTransactionCoordinator` |
| event采集与输入 | [assignment_event_learned_route.py](../../../assignment_event_learned_route.py)：`EventDormantLearnedPolicyRouteV2.collect_step`；[assignment_event_policy_evidence.py](../../../assignment_event_policy_evidence.py)：`_project_common_blocks`；[assignment_harl_wrapper.py](../../../assignment_harl_wrapper.py)：`_compose_event_assignment_harl_wrapper` |
| event更新与续训 | [assignment_event_training_real_isaac_adapter.py](../../../assignment_event_training_real_isaac_adapter.py)、[assignment_event_training_full_transaction.py](../../../assignment_event_training_full_transaction.py)：本文指定的两个execute入口；[assignment_optimization_checkpoint.py](../../../assignment_optimization_checkpoint.py)：save/validate/load及progression；[assignment_harl_training.py](../../../assignment_harl_training.py)：runner API与非等价边界 |
| 算法配置 | [agents/harl_happo_cfg.yaml](../../../agents/harl_happo_cfg.yaml)：默认算法超参数；受控已验收值另见第2节effective_config |

以上是关键修改候选位置，不是本次实现授权。若仅做目标仿真执行接入，应优先隔离执行/传感器适配，保留proposal/P2/authority/terminal/学习更新契约；无需重写已关闭的学习器。

## 8. 下一步候选路线与推荐顺序（未授权实施）

### 路线1：确认目标构型、坐标及执行/扫描契约——建议先做

解决“模型是否匹配设备、谁承担扫描、目标pose究竟属于哪个frame、什么代表任务完成”这组基础缺口。现在先做的理由：这些答案决定是补关节模型、执行控制、扫描回执还是辅助定位；直接换mesh或先选通信框架都不能解决它们。

复用：RobotSpec/capability、现有CSV约定、场景cfg、P2和ExecutionTransitionInput。需要用户设备清单、模型/关节资料、frame/标定图、扫描完成定义。最小交付：一份确定的slot→设备/角色→资产→base/TCP/scanner frame映射及单机器人单视点输入/输出示例，明确哪些参数仍是proxy；在另行授权后，可进一步静态解析目标USD/URDF。可观察完成条件：同一个真实目标pose能无歧义解释其单位、姿态、坐标变换和负责设备，执行成功/失败有明确反馈定义。

不改变Phase-B语义；仅确认/补充外部契约。资产资料整理与路线3入口设计可并行。此步不要求实体在线。

### 路线2：最小目标仿真执行与扫描反馈闭环，按需要准备实体适配

依赖路线1确定的构型和frame。解决当前“9D直接积分+几何驻留”与目标执行之间的落差。复用现有分配、P2准入、生命周期facts及目标集合；根据目标设备选用实际需要的底盘/关节控制、必要的IK/路径支撑或已有控制器，不扩成新规划研究方向。

最小交付：后续授权下，让一台已确认模型执行一个视点，读取真实仿真状态，清楚区分到达与扫描完成；若传感器暂未建模，反馈模拟必须标注。命令与回执关联同一次执行，失败/取消按既有authority释放。可观察完成条件：模型状态到达约定pose，指定扫描完成输入驱动对应任务完成；受控失败回报能对应同一robot/task/attempt而不误完成新任务。只需围绕该单元的有限检查，不设计大型qualification阶段或全量回归矩阵。

目标是保留Phase-B ownership/P2/DVM/terminal语义；改变执行动力学和完成来源必须明确记录，不能宣称旧proxy运行证据自动覆盖新backend。设备协议/取消/失联资料可并行整理；只有用户需要且另外授权时才连接实体，不预选ROS2或厂商SDK。

### 路线3：把已验证event骨干整理成可配置系统入口

解决“生产callable已验收、日常entry仍分散且public gate阻断”的使用缺口。复用第6–7节生产模块，显式组织collection→reviewed transaction→progression/LR→checkpoint→fresh restore与退出；将场景和执行backend配置清晰传入。历史qualification脚本仅作来源参考。

最小交付：先形成可审查的入口/配置设计；获后续授权后实现一个有界、可重复调用、正确消费完整优化进度的入口及简洁使用说明。可观察完成条件：入口确实调用指定event coordinator，保存/恢复后从保存的next update/LR继续，选择的场景与backend清楚可见；现有public gate的调整必须单独明确授权。不能把generic weights-only restore包装成完整event恢复。

原则上不改已关闭Phase-B核心语义，可与路线1并行；目标设备演示依赖路线2，proxy上的算法实验可在其假设、输入及实验范围被用户接受后另行授权，不必等待全部实体部署。本轮既不启动论文实验，也不批准新的规模/多seed训练。

**推荐顺序：先路线1；路线3的入口设计可并行；路线2以路线1结果选定最小backend，再决定实体接口和算法实验各自的时间。** 主线保持给定视点集合上的lifecycle-aware dynamic MRTA；视点生成不是本阶段贡献，不开始Transformer/variable-cardinality实现。

### 最多五项待用户补充

1. 最终设备清单、型号/数量及职责：谁执行扫描，谁仅提供定位/跟踪，哪些平台可以移动？三个actor槽位是否需要重新对应？
2. 哪些USD/URDF/CAD对应哪些设备；可提供的joint/link、限位、执行器参数、尺寸单位及已有可用仿真/控制模型是什么？
3. 外部视点与真实场景world如何配准；base、法兰/TCP、scanner/跟踪仪之间的标定变换、轴向/四元数约定，以及一个代表性目标pose是什么？
4. 执行与扫描的现有软件接口/协议是什么：命令、实测状态、到达与有效扫描数据回执、暂停/取消/失联如何表达？是否有仓库外驱动/SDK文档或样例？
5. 下一步优先交付是目标仿真执行演示、可配置event研究入口，还是实体单机接口准备；可接受保留哪些proxy假设，扫描完成需要满足什么业务/数据质量条件？

## 9. 清理后状态、Git与本次变更边界

本次起始只读Git快照：branch=`main`；HEAD=`5e62cd58d631946aa5d68a64c27c8132ae5aef84`。已完成的四个工程提交：

| 提交 | 内容 |
|---|---|
| `c107a6c892eb90ff643d549d928c555ec9f9be5b` | AgentRead月/日归档迁移 |
| `5e7367ce28f0dfc3d4de86fa90d751284f1159c3` | Phase-B生产训练骨干 |
| `947f9261864945ab120a7958f3cc08b38b37e44a` | 测试/helper及compact证据 |
| `5e62cd58d631946aa5d68a64c27c8132ae5aef84` | Phase-B关闭文档 |

起始index无暂存差异。TASK_PROGRESS已修改；20260925清理审计/执行报告、归档及其记录目录/ZIP起初为已有untracked内容。clean worktree不是此次交接前提。

**收尾发现并发外部Git变化**：2026-09-26 12:56:48 +08:00只读复核时，branch仍为main，HEAD已变为 `24ecbad7dd1bdcd006399b64bfb757a86b71aeec`，新增提交题为 `chore(mrta): finalize Phase B cleanup records and project handoff`。与起始HEAD相比只涉及20260925清理记录和TASK_PROGRESS，没有生产/测试/harness/配置/资产实现变更。原清理资料已进入该提交；此时index另有 `AgentRead/202609/20260925/phase_b_local_artifact_cleanup_execution.zip` 的暂存删除，TASK_PROGRESS为未暂存修改，本文为untracked。该ZIP与此前清理报告中的已缺失 `phase_b_git_closeout_artifacts.zip` 不是同一文件。本次及协作子任务均未执行Git写或删除；外部操作者/意图未确认，不推断、不撤销。本文记录时间点快照，不声称整个工作区HEAD/index未变或后续始终不变。

低优先级管理差异：实际存在annotated tag `lifecycle-mrta-phase-b-complete`，tag对象=`990d8689e23cf4da24fd7eda36201584cbec877c`，剥离后指向旧提交 `b71d85a32f51be6ada324f870813a56bb45dd396`，不指向当前HEAD；TASK_PROGRESS仍有“optional/not created”历史表述。仅记录，不修复、不移动tag，也不以标签名判断代码版本或阻断机器人接入讨论。

清理结论引用最新已完成报告，未重新执行inventory或旧存在性检查：实际删除50,638文件/12,122,922,342逻辑字节；唯一原先已缺失的`phase_b_git_closeout_artifacts.zip`未重建、不计删除；9个旧smoke checkpoint tensor payload已获准删除，旧checkpoint不可再load。报告保留了核心compact证据，部分历史raw/detail链接故意不可用；UNKNOWN旧实验数据保留，不继续清理。保留历史STOP及AWAITING标签，不因失效细节链接重新开启历史STOP或Phase B。

本次仅新增本文，并在TASK_PROGRESS追加完成句及本文链接；不重写/压缩原handoff，因此无需再建立逐字节archive。未修改生产/测试/harness/资产/配置/installed HARL；未运行测试、项目import、Isaac、CUDA、训练/评估、checkpoint load/save；未连接硬件或发送命令；未删除/移动/压缩数据；未执行Git add/commit/push/tag/reset/restore/checkout/clean/stash。文档检查仅限本文引用/正文、TASK_PROGRESS差异和只读Git状态；新文档本地引用可解析，TASK_PROGRESS scoped diff whitespace检查通过，未对历史报告失效链接做全量审计。

## 10. 新GPT / Codex窗口最小阅读清单

先读 [AGENTS.md](../../AGENTS.md)、[TASK_PROGRESS.md](../../TASK_PROGRESS.md)、**本文**，再读第2节的四份报告：implementation summary、readiness audit、final closure report、最新single-absence清理执行报告。不要从全部历史R系列重新开始，不要运行旧产物存在性校验。

讨论机器人接入时，追加第7节前五行的源码及`robots_real_proxy.yaml`、`mobile_scanner_profiles.yaml`；讨论系统入口时，追加event learned route、real adapter/full transaction、optimization checkpoint及当前public preflight。需要核对验收数字时，只按第2节读取明确保留的compact JSON，不尝试加载旧checkpoint。

当前交接结论：**已完成项目现状与机器人接入交接，等待用户/GPT讨论下一步。Phase B COMPLETE / GPT REVIEW PASS / CLOSED保持不变。后续路线均未授权实施。**
