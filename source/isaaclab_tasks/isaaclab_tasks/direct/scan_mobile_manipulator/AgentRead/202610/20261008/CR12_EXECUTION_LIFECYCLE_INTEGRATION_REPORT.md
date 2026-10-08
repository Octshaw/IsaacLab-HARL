# CR12 execution-to-lifecycle 最小接入实施与有界验证报告

日期：2026-10-08（Asia/Shanghai，UTC+08:00）。状态：**CR12_EXECUTION_LIFECYCLE_INTEGRATION_PASS，等待 GPT/用户审阅**。本报告不自行赋予 GPT REVIEW PASS。

路径简写：仓库为 E:/Project/IsaacLab_HARL；T 为 source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator；E 为 scripts/environments；Q 为 source/isaaclab_tasks/test；L 为 logs/scan_assignment/20261008_cr12_lifecycle_integration。以下源码行号对应本次冻结工作区。HEAD 为 24ecbad7dd1bdcd006399b64bfb757a86b71aeec，包含既有未提交修改；没有以 HEAD 覆盖工作区。

## 1. 结论、授权与实际范围

用户已审阅[接入方案](../20261007/CR12_EXECUTION_LIFECYCLE_INTEGRATION_PLAN.md)，本轮明确授权私有 E=1/M=1/N=2 Host 的实施、CPU 检查和两个有界真实 case。现已完成真实 resolver → claim → Store/P2 → 非阻塞 CR12 执行 → typed report → producer/transaction/authority → receipt/退役 → terminal/rebuild/facade ACK。

| 结果 | normal / attempt_01 | cancel_then_reclaim / attempt_02 |
|---|---|---|
| 最终分类 | **NORMAL_CASE_PASS** | **CANCEL_THEN_RECLAIM_CASE_PASS** |
| 真实 claim / 请求 | 2 / 2 | 3 / 3 |
| 完成 C / 取消释放 R | 2 / 0 | 2 / 1 |
| 本次真实 RGBA / PNG | 2 / 2 | 2 / 2；取消请求无 PNG |
| Host transition / continuation | 112 / 110 | 167 / 164 |
| 受控 physics / 正常 render | 1344 / 672 | 2004 / 1002 |
| 受控物理时间 | 11.200000584 秒 | 16.700000871 秒 |
| 初始化 physics / 全部 physics | 2 / 1346 | 2 / 2006 |
| App 构造 / 全所属进程墙钟 | 22.656 / 84.875 秒 | 14.328 / 126.734 秒 |
| 旧 episode 完成数 / terminal transport / ACK | 2 / 1 行 / 完成 | 2 / 1 行 / 完成 |
| Conda、目标 Python 退出码 | 0、0，自然退出 | 0、0，自然退出 |
| 超时、强杀、原生故障匹配、监督器错误 | 均无 | 均无 |

两次运行使用同一冻结代码，没有运行后修补再借用旧结果。**App 共 2/3，共享局部运行重试使用 0/1；未创建 attempt_03，成功后停止运行。** 正常链全部通过、全树退出后，才启动取消 case。

本次结论限于 fixed-base/lift0/v1 的局部两个冻结任务、虚拟 RGBA 相机及一次稳定 WAITING_DATA 主动取消。Phase B 保持 **COMPLETE / GPT REVIEW PASS / CLOSED**；basic/formal/visual、已接受双点 demo 及历史 FAIL/待审记录均保留。公共 event gate 未开放，未接学习器或多机器人。

## 2. 从固定 demo 到真实 authority 驱动的改动

### 2.1 文件、符号和职责

| 文件及关键符号/行号 | 本次实现与旧默认保护 |
|---|---|
| E/run_cr12_lifecycle_integration.py：configure_parser:15、validate_case_prerequisite:20、run_integration:55 | 新私有 composition 与确定性 proposal driver；只选真实 P2 中 AVAILABLE 的任务。cancel 必须引用本主题已自然退出的 normal PASS。实际入口在 App 前检查前置条件。 |
| E/_cr12_lifecycle_host.py：CR12IntegrationHost:47、reset:98、assignment_problem:142、step:246 | 新真实 domain Host，统一 D=12 时钟；实际 CR12 base/scanner、两个冻结目标、当前任务状态和规模契约进入现有生产链。只作一次场景物理初始化。 |
| E/_cr12_scan_executor.py：Cr12PoseControlSession:132、submit_goal:319、prepare_tick:364、submit_prepared:412、observe_physics:433、finish_tick:495 | 从已接受实现抽取同一 DLS、积分器及守卫；方法内部不 step/render。旧 E/run_cr12_pose_target.py 的 _pose_ticks:89 驱动这些阶段，保留旧默认参数、顺序和停止行为。 |
| E/_cr12_capture_runner.py：CaptureRequestRunner:20、before_tick:86、observe_tick:104、boundary:165 | 新单请求推进器；请求/成果锁存、真实取消命令、块尾保持和交接复核。两个任务序列不写进控制器。 |
| T/assignment_cr12_execution_adapter.py：ExecutionBinding:48、RawCaptureCustody:71、bind_effective_assignment:224、record_pending:272、build_report:293 | 新纯任务边界模块，不 import Isaac。绑定真实 claim provenance，保留 birth artifact、长期请求身份和不可变数据；不维护第二套 owner/completed。 |
| 同 adapter：_validate_report:316、ack_authority_delivery:369、retire_request:399 | producer 前核对来源、当期 prestate/generation、数据与块末条件。只确认该 domain 实际提交的 outcome；重复 ack 返回原 receipt；receipt 前不能退役。 |
| T/assignment_event_profile_runtime_domain.py：环境入口 finalize_execution_transition:698、内部入口:1333、原 producer 提交段:1427–1458 | 新 typed execution 分支与旧 physical 分支共用原合法 finalize 管道；未修改 authority 决策、claim 准入或 consume ledger。 |
| T/assignment_event_policy_evidence.py:362/468；T/assignment_event_terminal_critic_sidecar.py:174/182 | 新 Host 显式来源透传；旧 ScanMobileManipulatorEnv 默认来源不变。 |
| E/_cr12_camera_capture.py：prepare:103、begin_capture:276、peek_retained_snapshot:424、eligible_to_retire:451、retire_request:485、observe_close:537 | 显式 integration 预算 2/3 请求；只读 Python 快照、健康无数据资格检查、真实 receipt 后退役。旧默认 1/2 请求行为保留，不清 sticky。 |
| E/_cr12_single_view_capture.py：accept_frame:160、retain_custody:191、record_artifact:235 | integration 显式 raw-held-with-custody；旧入口继续 artifact-required。已取得数据不因 PNG 或关闭失败而被改成未采集。 |
| E/run_cr12_single_view_capture.py：parse_args:22、prepare_scene:119、initialize_capture_run:270、main:582 | 增加显式可选 parser、App 前校验、相机预算/集成模式钩子；原启动、visual/Fabric、初始化、收尾链复用。旧调用不传新参数时默认不变。 |

新增三个生产 CPU 测试文件：Q/test_cr12_scan_executor.py、Q/test_cr12_lifecycle_execution_adapter.py、Q/test_cr12_lifecycle_host.py。调整五个受抽取影响的原测试：test_cr12_pose_continuation.py、test_cr12_manual_visual.py、test_cr12_pose_control.py、test_cr12_camera_capture.py、test_cr12_single_view_capture.py；未删除语义断言。旧 single_view_entry/integration 仅运行针对性回归。

运行监督与 fresh-private 准备脚本只放 L/repro；生产实现/测试未放入 AgentRead。新增 _cr12_capture_runner.py 是已授权的少量文件组织调整，不建立通用启动框架。

### 2.2 真实权威、长期 binding 和消费一次

入口复用 _EventProfileLifecycleRuntimeDomain、_EventProfileLifecycleDomainSpec、EventProfileSynchronousRuntimeCoordinator 和 _compose_event_assignment_runtime_facade 及其真实 ports。运行中使用规范包名导入；CPU 规范化加载仅为隔离 Isaac 包初始化，不替换生产 authority/contract 类型。

每次新请求必须先经 decision snapshot、resolver、production claim 和 P2 发布，action_builder 才能绑定并提交 pose goal。长期 binding 包含 run/domain、env/episode、robot/task、真实 claim token、birth artifact 及来源版本；按 selected_env_ids 映射。没有新 claim 的 transition 调用 step_without_new_claim，兼容 physical P2 的 assignment_artifact=None；不会把内部 −1 当成当前有效 assignment，也不重复 ON。

每个 Host transition 都用当期 admitted P2/prestate/generation。只有长任务身份保留初始 claim；producer 的 consume token 每次由真实管道产生。最终任务状态、ownership、完成归属、failed-pair 均来自 P2/result。普通取消产生 R，不产生永久 F。本轮没有非预期 F/U/Rc；旧 proxy 环境、9D 动作和几何+dwell 完成链未构造/调用。

交付顺序已实现为：最新资格复核 → 冻结 pending/custody → typed report → 原 producer/transaction → 验证并 ack 真实 receipt → Camera 局部槽位退役 → adapter 退役 → 下一合法 OPEN。ack 后先记录 receipt，再做第二次边界复核和本地退役；若此后失败，保留已提交事实和数据，由既有 poison 阻止继续，不重发 C/R。该故障路径有真实 authority CPU 证据，本轮未作实际故障注入。

## 3. 唯一时钟、连续控制与块末重新确认

唯一资产为 T/assets/rokeaCR12/derived/fixed_lift0_v1/usd/cr12_fixed_lift0.usd 及既有引用。保持 baseline、dt=1/120、render_interval=2、TGS 8/2、gravity=(0,0,−9.81)、external-forces-every-iteration 显式 on、原 AABB 与保护阈值。没有修改资产、惯性、PD、effort、margin 或 solver。

两个目标在首次初始化后由实际 scanner world 位姿 T_WS0 一次冻结：

- task0：位置加 (0.0106981457149994, 0, −0.000155046722254002) m，姿态左乘世界 Y 轴 +1°。
- task1：精确使用冻结的 T_WS0。
- world / 米 / WXYZ / scanner frame；E1 不重复加 env_origin。相机通过原 T_ES/T_SC 和 virtual_camera_mount_v1 挂在 link_6，不独立移动相机。task0 重认领仍用相同矩阵。

每个 Host.step 在 O1 admission 内执行 12 次 prepare → 成对 q/dq target write/readback/commit → 一次 physics → actual/守卫 → 偶数全局步一次 render → finish/poll，再一次 finalize。executor 自身无 physics/render；没有外部再次 next 旧 generator 的双时钟。authority transition 的 0.1 秒、physics tick、render opportunity、SyntheticData 来源时间及墙钟分开记录。

保留 absolute DLS λ=.01、COM Jacobian 适配、2/s 积分、4 秒 reference、pose≤960 ticks，以及 2 mm / .25° / native |dq|≤.01 rad/s 连续 121 点、跨度≥1秒的到位要求。新 claim 仅刷新局部 reference/稳定窗/请求时钟；controller、CommandIntegrator、q_cmd_previous、初始 5° 信任锚和全局时钟连续。normal 两次积分器 generation 为 0/672，cancel 三次为 0/660/1332，进程内 controller/integrator identity 各自相同。

请求终态后不再累加终态 FSM tick。成功请求都有 10 个剩余块尾 physics ticks，保持原反馈控制、OFF 和独立观察器；块末与 receipt 后再次确认最新状态。取消请求恰在块末终态，没有额外尾步。没有复用终态旧 healthy=true 快照提交 C/R。CPU 覆盖尾步保持丢失、块末资源恶化、receipt 后退役失败和 poison，验证不能继续发新请求。

初始化每 App 仅 1 次 sim.reset、1 次 joint-state 初态写入、0 次 root-state 写入、原 2 physics ticks；hidden settle=0、Jacobian extra steps=0。Camera 初始化 OFF、visual pre-init apply/seal 和非渲染 Fabric forward 沿已接受链。任务期间通过真实 actuator 目标运动，无 teleport/每步回写状态。

## 4. 实际 authority 与采集时间线

下表 step 为**本 App 受控全局 physics step**，不包含初始化 2 步；“claim 边界”是该步完成后的接单边界，第一次任务 physics 晚于 claim。token 数值仅记录本次读数，不作为实现中的固定常量。

| case / 请求 | task / claim token | claim 边界 | ON | 数据/取消 | 首次 OFF / FSM 终态 | receipt + retire | facts token / receipt ID / transition |
|---|---|---:|---:|---:|---:|---:|---|
| normal / 01 | 0 / 0 | 0 | 600 | DATA 602 | 662 | 672 | 55 / 56 / 55 |
| normal / 02 | 1 / 1 | 672 | 1272 | DATA 1274 | 1334 | 1344 | 111 / 112 / 111 |
| cancel / 01 | 0 / 0 | 0 | 600 | CANCEL 600 | 660 | 660 | 54 / 55 / 54 |
| cancel / 02 | 0 / 1 | 660 | 1260 | DATA 1262 | 1322 | 1332 | 110 / 111 / 110 |
| cancel / 03 | 1 / 2 | 1332 | 1932 | DATA 1934 | 1994 | 2004 | 166 / 167 / 166 |

所有五次到位均重新取得 121 点、1.000000052 秒稳定证据；每个成功请求局部 pose/capture/close=600/2/60，共662步，另记10步块尾；取消为600/0/60，共660步。没有预先把1344或2004步写成成功门槛；实际完成后提前结束。

normal：第一次 C 后 P2 store58、task=[COMPLETED,AVAILABLE]、completion=[1]；下一 OPEN 才生产 task1 claim。第二次 C 后旧 P2 store115、task=[COMPLETED,COMPLETED]、completion=[2]。

cancel：第一次 ON 的真实 enable 读回后，before_tick 在首次后续正常 render 前发生产取消命令；没有暂停渲染、更改 cadence 或丢弃帧。直到 R，后端 retained raw/fresh/acquired 均无成果，本 product 事件为0、in-flight=0，OFF 30次观察。真实 R 后 store57、task=[AVAILABLE,AVAILABLE]、owner=[−1,−1]、completion=[0]、failed-pair 全false。随后新 claim1 的 birth source store57、commit store58；goal/capture ID 更新，attempt_id 仍 attempt_02。task0 C 后 store114、completion=[1]，task1 C 后 store171、completion=[2]。重认领未漂移目标、未复用旧稳定窗。

每条请求 metadata 留存对应 birth 版本、完整 goal/capture/attempt 身份、authority receipt、块末最新资格和 retired_after_receipt=true。没有已获得数据却报无数据的竞争情况；如果竞争发生，实现保留成果并结束该预期取消 case，而不会删除数据以获取 PASS。

## 5. 数据持有、fresh、按需 OFF 与资源复用

业务 C 使用显式 raw-held-with-custody：独立 RGBA 和来源 metadata 被真正 custodian 持有，最终两个 bytes-backed readonly 数组在退役与逻辑 rebuild 后仍有效。保存失败与采集失败分开；PNG 失败但 raw 存在不反写 acquired。完整 case 的 artifact_delivery_pass 仍独立要求两张真实 PNG。本次业务、文件交付均通过，没有实际注入 PNG 失败。

| case / 成功请求 | ON source time | 实际 frame / source time | 本请求 source frame baseline | OFF 首次 / 块末 quiet机会 |
|---|---|---|---:|---|
| normal / 01 | 609/30 | 610 / 610/30 | 0 | 30 / 35 |
| normal / 02 | 945/30 | 946 / 946/30 | 610 | 30 / 35 |
| cancel / 02 | 883/30 | 884 / 884/30 | 0 | 30 / 35 |
| cancel / 03 | 1219/30 | 1220 / 1220/30 | 884 | 30 / 35 |

四张均为同 product NEW_FRAME 与 Camera ReferenceTime 同帧、post-super clone 的 640×480 uint8 RGBA，source 严格晚于本次 ON。取消请求 ON/OFF 同为553/30，没有新帧，OFF 30/30 quiet。所有关闭观测 updates_enabled=false、独立 observer active、in-flight=0；成功后的额外5次正常 render 属于块尾持续确认，不是额外物理步或隐藏采集。

专属 Hydra updates 的实际关闭及 Camera pause/resume 控制采集，独立 observer 持续观察；没有改为常开筛帧、停写盘或每次销毁重建。每个 App 中 camera/product/Hydra/两个 annotator/独立 observer 六项 Python object identity 保持，prepare/create/initialize 各1；normal begin/OFF/retire各2，cancel各3，最终有效release各1。接收订阅按请求 resume 会更换，独立 observer 不换；这些是**各 App 内**对象连续性，不声称跨 App 的 native handle 相同。

SyntheticData source time 与 native simulation/rendering_time 是不同时间域，frame号不是physics步数。receive-context 是正常 render 前缓存的实际 scanner/link 状态，**不是精确曝光姿态**。本轮没有重复、迟到、非零 in-flight 或确认 OFF 后新输出；有关防护仅有 CPU 证据。没有增加图像质量、深度比例、分割、点云或重建门槛。

可直接查看原始数据，无需再运行：

- normal：[task0 PNG](../../../../../../../../logs/scan_assignment/20261008_cr12_lifecycle_integration/attempt_01/request_01/camera_rgba.png)、[metadata](../../../../../../../../logs/scan_assignment/20261008_cr12_lifecycle_integration/attempt_01/request_01/capture_metadata.json)；[task1 PNG](../../../../../../../../logs/scan_assignment/20261008_cr12_lifecycle_integration/attempt_01/request_02/camera_rgba.png)、[metadata](../../../../../../../../logs/scan_assignment/20261008_cr12_lifecycle_integration/attempt_01/request_02/capture_metadata.json)。
- cancel：[取消请求 metadata，无图片](../../../../../../../../logs/scan_assignment/20261008_cr12_lifecycle_integration/attempt_02/request_01/capture_metadata.json)；[重认领 task0 PNG](../../../../../../../../logs/scan_assignment/20261008_cr12_lifecycle_integration/attempt_02/request_02/camera_rgba.png)、[metadata](../../../../../../../../logs/scan_assignment/20261008_cr12_lifecycle_integration/attempt_02/request_02/capture_metadata.json)；[task1 PNG](../../../../../../../../logs/scan_assignment/20261008_cr12_lifecycle_integration/attempt_02/request_03/camera_rgba.png)、[metadata](../../../../../../../../logs/scan_assignment/20261008_cr12_lifecycle_integration/attempt_02/request_03/capture_metadata.json)。

## 6. Terminal、逻辑 rebuild、sidecar 与正常收尾

最后一次 C 的旧 episode result 在 reset 前封存，保留 coverage=[true,true]、completion_count=[2]、updated_task_state=[4,4]、owner=[−1,−1]、failed-pair=[[false,false]]、terminated=true/truncated=false。历史字段 completed_tasks=[false,true] 表示**最后一个 transition 新完成 task1**，不是整个 episode 只完成一个任务；累计事实取 coverage/completion_count。

| 旧 → 新 P2 | normal | cancel |
|---|---|---|
| episode generation | 0 → 1 | 0 → 1 |
| transition generation | 111 → 111 | 166 → 166 |
| store version | 115 → 116 | 171 → 172 |
| result present | true → false | true → false |
| reason | ALL_TASKS_COMPLETED(1) → NONE(0) | 同左 |
| 当前任务 / 归属 / 完成数 | AVAILABLE×2 / owner −1×2 / 0 | 同左 |
| rebuild前后native clock | 同为1346 / 11.216667252秒 | 同为2006 / 16.716667539秒 |

receipt 确认并退役后，Host 校验 OFF/保持/健康，走合法 episode_rebuild 和 commit_physical_reset_complete，实际建立新 episode context。actual q/dq/q_cmd/scanner 和时钟逐值不变，没有回零、新 Camera.initialize 或额外 physics。五元组正常返回后 O1 开 Wnext，facade 复制一行旧历史并 batch ACK；pending terminal slots=0。随后 case结束，不为新 episode 再 claim。该 Host 专属逻辑 reset 不等同旧 proxy 物理 reset，也不证明无限 episode 重用。

pre-reset sidecar 通过现有 capture_pre_reset_critic_physical_snapshot_v2 与 builder，用实际 assignment problem、episode_progress_steps、scale生成；critic dimension 与 audit semantic evidence 都为62。来源显式为 CR12IntegrationHost.assignment_problem guarded actual state。ALL_TASKS_COMPLETED 分支 bootstrap_critic_obs=None、bootstrap_projection_valid=false 符合原契约，**实际 audit projection 存在**，没有用零向量或 snapshot=None过关。未创建网络、运行 critic 或改变原 reward；五元组的零 reward 仅为明确未用于学习的接口占位。

assignment problem 的位置/姿态来自 actual CR12 与冻结任务；cost 为 actual scanner 到目标的欧氏距离；feasibility 仅声明已接受的两任务局部范围。arm_reach 为 URDF 平移链长与 scanner offset 的几何上界，不是全模型可达性证明；workload沿现有完成归属/N定义。

六类 guard（clock/joint/contact/geometry/frame/render_clock）每受控步全部通过：normal各1344，cancel各2004。最大禁止contact、root translation/rotation均0；首末 native 参数一致，结束前 native articulation/simulation view 有效。相机资源 release完成且errors=[]，发生在 STOP 前；STOP返回、App close请求后两进程及所有所属后代自然退出。原物理守卫与固定非物理fixture支持本次场景结论，不证明任意构件路径避障。

实际日志仍有 DLSS 最小输入尺寸、SyntheticData host copy 性能、关闭时 removePath/interface/menu warning；两个 console 未出现 [Error]/[Fatal]，监督 native fault匹配为空。不能把这些有界通过推广为所有驱动/运行情形均无问题。

## 7. 检查、运行输入与预算

### 7.1 CPU 与修改前基线

共 **182 个不同 CPU 测试用例通过**；17项 AST/源码抽取对照另计，修改Python均 py_compile通过。CPU 使用真实 production claim/producer/transaction/facade，物理和相机事件为明确 fake，不替代本节真实 App证据。

| 检查 | 通过数 |
|---|---:|
| 非阻塞 pose session / 原 continuation | 15 / 15 |
| 原 manual入口边界 / recorder与CSV | 4 / 2 |
| Camera backend / 单请求FSM | 41 / 35 |
| 新真实authority adapter | 21 |
| 原 single-view entry / integration | 13 / 17 |
| 完整新Host（真实authority + fake物理/事件） | 5 |
| 本轮监督器（含两个完整CPU Host结果契约） | 14 |

覆盖 continuation/P2 artifact=None、旧claim/episode/nonowner拒绝、STEP_IN_FLIGHT拒绝新proposal、once/重复ack、真实数据保管、PNG独立性、3请求预算、sticky/无数据退役、块尾保持恶化、receipt前后失败及poison、terminal/rebuild/ACK、C+U不能healthy reset、cancel/fresh竞争与normal前置。

CPU阶段修正了抽取后的测试定位、fake pipe接口、误在poison后重新读取P2的fixture断言、真实receipt失败留存顺序、metadata落盘标记及监督器实际字段匹配。均在首App前结束；不是运行重试。未删除原检查或把失败样本标成预期取消。源码AST对照验证DLS、paired write/readback/commit、poststep guards等沿原实现。

[本轮preflight](../../../../../../../../logs/scan_assignment/20261008_cr12_lifecycle_integration/repro/preflight.json)仅冻结17份直接相关输入，包含检查命令/计数和参数，未建立全仓库存。两次 App前验证，运行后再次确认17份内容无变化。[pose抽取证据](../../../../../../../../logs/scan_assignment/20261008_cr12_lifecycle_integration/repro/pose_session_extraction_checks.json)、[camera/监督器CPU证据](../../../../../../../../logs/scan_assignment/20261008_cr12_lifecycle_integration/repro/camera_supervisor_cpu_checks.json)及repro内四份局部patch基于**本轮开始前的dirty工作区文本**，不以HEAD覆盖既有实现。

### 7.2 实际运行来源与时间

Python为 C:/isaacenvs/isaac45_harl/python.exe，Conda为 D:/miniconda3/Scripts/conda.exe。仓库 VERSION=2.1.0，isaaclab扩展metadata=0.36.23；实际Kit为Isaac Sim4.5，torch=2.5.1+cu121，pre-App CUDA实际cuda:0且同步完成。GUI/camera-enabled isaaclab.python.rendering.kit、日志D3D12、驱动610.60；未改Windows启动helper或已接受初始化顺序。

监督器用项目Python的 -X utf8 启动；子进程继承环境并只覆盖本次 PYTHONUTF8=1、HEADLESS=0、ENABLE_CAMERAS=1、LIVESTREAM=0、XR=0。每App独立private副本，仅窗口width/height/maximized允许0–3项变更；真实source配置首尾不变。实际Kit参数与加载路径确认private和D3D12，未修改Conda持久变量/共享配置。

| App | 本地起止（UTC+08:00） | 原始结果及日志 |
|---|---|---|
| attempt_01 normal | 15:44:49.218 → 15:46:14.096 | [result](../../../../../../../../logs/scan_assignment/20261008_cr12_lifecycle_integration/attempt_01/result.json)、[supervisor](../../../../../../../../logs/scan_assignment/20261008_cr12_lifecycle_integration/attempt_01/supervisor_result.json)、[console](../../../../../../../../logs/scan_assignment/20261008_cr12_lifecycle_integration/attempt_01/console.log)、[Kit](../../../../../../../../logs/scan_assignment/20261008_cr12_lifecycle_integration/attempt_01/kit_20261008_154452.log) |
| attempt_02 cancel | 15:46:40.839 → 15:48:47.560 | [result](../../../../../../../../logs/scan_assignment/20261008_cr12_lifecycle_integration/attempt_02/result.json)、[supervisor](../../../../../../../../logs/scan_assignment/20261008_cr12_lifecycle_integration/attempt_02/supervisor_result.json)、[console](../../../../../../../../logs/scan_assignment/20261008_cr12_lifecycle_integration/attempt_02/console.log)、[Kit](../../../../../../../../logs/scan_assignment/20261008_cr12_lifecycle_integration/attempt_02/kit_20261008_154644.log) |

Kit正文为07:xx UTC；监督起止明确+08:00，两个时间源未混用。完整cwd/argv/Windows引号在各自[normal command](../../../../../../../../logs/scan_assignment/20261008_cr12_lifecycle_integration/attempt_01/command.json)、[cancel command](../../../../../../../../logs/scan_assignment/20261008_cr12_lifecycle_integration/attempt_02/command.json)。实际入口为 E/run_cr12_lifecycle_integration.py，参数含唯一USD、cuda:0、--external-forces-every-iteration on、--enable_cameras、--info、--integration-case 和 fresh --kit_args userConfigPath；cancel另传本轮normal supervisor_result。

本轮真实调用的监督器为 L/repro/supervise_cr12_lifecycle_integration.py，已实现 --attempt-dir、--integration-case、--normal-result 及明确局部修复参数。**这些命令记录是已完成证据，已有目录禁止重用；本任务不再提供或执行新的App。** 用户直接查看上述四张原图和报告即可。

每次owned Windows Job全树监督：App≤180秒包含在normal300/cancel420秒内，输出按bytes排空，超时只作用于本次所属进程，不按进程名处理无关进程。单请求保留960/600/240及总1800tick，capture/close wall60/30秒；新请求要求剩余预算至少完整请求加块尾。实际两case远低于320/480 transition、3840/5760受控physics、1920/2880render上限。无超时、强杀或局部运行修复，不补跑第三App。

## 8. 未覆盖范围与下一步边界

本轮已运行证明正常C、一次稳定WAITING_DATA主动取消R、同机器人同任务新claim、安全复用和正常terminal。没有实际注入 MOVING取消、自然卡滞、相机超时、sticky恢复、关闭故障、C+U、跨机器人重新分配或不安全reset；相关拒绝/保留/poison分支只有CPU或源码证据，不能标runtime PASS。Host对无安全边界/native错误立即fail-stop，不追加physics来凑完整事务或OFF统计；这也不构成运动中物理制动能力。

仍未实施/验证真实构件碰撞场景、通用规划、depth/pointcloud、真实结构光或曝光/安装标定、实体设备、多机仲裁、可变规模策略和策略性能。保持原局部feasibility/AABB范围。已采到但关闭失败时必须保留acquired并阻止新运动，不能自动reset成健康；当前两个成功case没有触及此分支。

下一步是GPT/用户审阅本轮实现、两条真实时间线、receipt/retire与terminal边界，再决定后续范围。当前没有必须追加询问才能解释本轮结果的问题，也没有本轮未处理的运行失败。**审阅结束前不自动增加case/机器人/任务规模，不解封公共event入口，不开始训练或checkpoint操作。**

## 9. 交付、保留与停止

本轮交付本主报告；小范围更新 AgentRead/TASK_PROGRESS.md 与 REPORT_INDEX.md，标明设计已审阅、本轮真实结果及等待审阅。原设计、旧报告和历史FAIL不改写；既有checkpoint/raw清理边界不变，没有恢复历史数据或生成ZIP、全仓hash及逐tick tensor档案。

实现/测试变更见第2节，辅助材料只在L的两个实际attempt和repro。原USD/URDF及引用、物理配置、Windows helper和真实user.config未修改。每App八项既有资产/关联输入内容保护通过；源码冻结复核通过。Git仅只读查询HEAD/状态/diff；既有暂存ZIP删除仍原样存在，没有add/commit/push/tag/reset/restore/checkout/clean/stash操作。

**本轮实施与限定真实验证已完成：CR12_EXECUTION_LIFECYCLE_INTEGRATION_PASS；等待GPT/用户审阅。已停止，不自行写GPT REVIEW PASS，不继续运行或扩展实施。**

