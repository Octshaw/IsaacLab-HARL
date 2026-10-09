# CR12 固定双机器人 lifecycle 接入实施与有限运行报告

执行日期：2026-10-08，Asia/Shanghai（UTC+08:00）。状态：**实现及针对性 CPU 检查完成；真实运行在 App 构造期发生原生窗口故障，双机运行未验证；已停止，等待 GPT/用户审阅。**

## 1. 结论与授权边界

本轮按用户新授权实施已审的 E=1 / M=2 / N=4 私有执行接入。新增双机入口，扩展原 Host、运行准备、执行器、相机及 adapter，保留一个真实 domain/Store/resolver/claim/P2/producer/authority/facade。没有另建第二套 Host、控制算法或 lifecycle authority。

唯一实际 App 为 `attempt_01 / dual_normal_staggered`。**总体为 `CR12_DUAL_ROBOT_LIFECYCLE_INTEGRATION_FAIL`，原因是启动基础设施失败，不是策略任务失败或四任务完成率为零。** 该进程在 `AppLauncher → SimulationApp.__init__` 内创建 `120×0` 窗口，D3D12 swapchain 初始化失败，随后以 `0xC0000005` 退出。没有 `app_ready`；未进入 `run_dual`，没有双机器人场景、项目 reset/受控 step、claim、RGBA 或 terminal。

本轮使用 App **1/2**、受控运行 **0**。第二 App 只授权明确局部实现错误的修复，用户明确规定窗口故障/原生访问异常应停止。因此**没有 attempt_02，不进行运行修复或盲重试**。所有本次所属进程已退出，无超时、无强杀；异常退出不等于正常关闭通过。

| 验收层 | 本轮真实结果 | CPU/源码能够支持的范围 |
|---|---|---|
| SETUP_AND_MAPPING | NOT_REACHED | 双实例顺序、独立 root/native/anchor 映射检查、共同 reset/forward 接线 |
| BUSINESS_EXECUTION | NOT_REACHED | 真实 authority 配合 fake 物理/事件的四请求、C、receipt、退役 |
| PARALLEL_AND_PRODUCT_ISOLATION | NOT_REACHED | 唯一共同步进、混合阶段与产品隔离的 CPU 行为；没有真实隔离片段 |
| TERMINAL_AND_SHUTDOWN | terminal NOT_REACHED；process exit FAIL | CPU 真实 schema/sidecar/rebuild/ACK；监督确认进程树退出 |

这不是 `COVERAGE_INCOMPLETE`：该分类适用于真实四任务业务完成、仅并行/隔离覆盖不足。本次没有业务完成事实。原始 `result.json` 停在 `status=RUNNING, failures=[]`，是 native 异常来不及执行 Python 收尾；不得据此视为成功或仍有进程在运行。最终进程结果以监督记录为准，原始文件未改写。

基线保持 `main / a8c618a32da65747827f1cb3f722fac24df2aec8`（`feat(cr12): establish single-robot scan execution and lifecycle integration`）。开始时存在上轮设计报告及 TASK_PROGRESS/REPORT_INDEX 变更，均保留。单机已获 GPT REVIEW PASS，用户决定不再补人工观看；Phase B **COMPLETE / GPT REVIEW PASS / CLOSED**。本报告不自行赋予新 GPT REVIEW PASS。

路径缩写均以仓库 `E:\Project\IsaacLab_HARL` 为根：`T=source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/`，`E=scripts/environments/`，`Q=source/isaaclab_tasks/test/`，`L=logs/scan_assignment/20261008_cr12_dual_lifecycle_integration/`。前置设计为[双机接入方案](CR12_DUAL_ROBOT_LIFECYCLE_INTEGRATION_PLAN.md)，已接受 M1 为[单机实施报告](CR12_EXECUTION_LIFECYCLE_INTEGRATION_REPORT.md)，两份历史正文均未回写。

## 2. 实际实现与旧默认保护

以下是当前源码及 CPU 事实，**不是双机 runtime PASS**。路径后的数字为本轮最终源码关键行。

| 文件 / 关键接口 | 实际修改与用途 |
|---|---|
| `E/run_cr12_dual_lifecycle_integration.py:14,37,68` | 新正式入口；`instance_specs`、`next_proposals`、`run_dual` 固定双实例、四任务、72 tick 错峰；复用原 capture main，不引入另一套启动器 |
| `E/_cr12_runtime_support.py:629,728,783,798,844` | `create_fixed_cr12_world` / `spawn_fixed_cr12_instance` / `prepare_fixed_cr12_contacts` / `reset_fixed_cr12_world` / `read_fixed_cr12_instance`；world 与单实例分离，旧 `create_fixed_cr12_scene:867` 包装原单机顺序 |
| `E/run_cr12_single_view_capture.py:313,356,240,664` | 双实例 spec 校验、实例准备、共同 Fabric 发布；最终 native 验证与释放分开；旧单机包装及默认参数保留 |
| `E/_cr12_scan_executor.py:135,331,348,394,525` | 显式 `allow_unbound_hold=False` 旧默认；双机启用 `enter_idle_hold`，沿原 DLS/积分器/q_cmd 反馈保持，旧请求 deadline 停止 |
| `E/_cr12_capture_runner.py:21,110,180` | 增加 robot/root/product 身份、阶段变化与实际 joint/scanner 位移摘要；沿用单请求 FSM 和最新边界验证 |
| `E/_cr12_camera_mount.py`、`E/_cr12_camera_capture.py:104,233,242,681` | 可选 fixture/product/Camera/observer 命名、`render_evidence`、完整请求归属、`verify_camera_isolation`；旧默认名保持 |
| `E/_cr12_lifecycle_host.py:47,149,234,270,308,331,433` | 同一个 Host 的 `RobotExecutionContext`、双实例 reset、批绑定、整批交付后逐槽退役、无绑定保持、共同终态、唯一物理循环 |
| `T/assignment_cr12_execution_adapter.py:176,278,374,476,513` | 仅 `single_m1n2` 与 `dual_m2n4` 两个 profile；plural binding/report/ACK、两份 pending/custody、逐槽退役；旧 M1 单数接口包装同一逻辑 |

新增四个可复用测试：`Q/test_cr12_dual_runtime_support.py`、`test_cr12_dual_camera_capture.py`、`test_cr12_dual_execution_adapter.py`、`test_cr12_dual_lifecycle_integration.py`；小范围调整已有 `test_cr12_runtime_support_hooks.py`。一次性监督/private helper 与其测试在 `L/repro/`，生产代码不导入这些文件。

`_cr12_visual_geometry.py` 无需修改：复用原 root 定向 pre-init apply/seal。没有修改机器人 USD/引用层、PD/solver/光学配置、Windows helper、installed packages、domain/facade/claim/transaction 核心或公共 event gate。没有训练、checkpoint、策略网络、共享任务竞争/跨机器人转交。

### 2.1 独立预期、共同初始化及任务冻结

唯一资产仍为 `T/assets/rokeaCR12/derived/fixed_lift0_v1/usd/cr12_fixed_lift0.usd` 及原引用层；计划在同一个 stage 中 reference 两次，不复制或重导出资产。

| 身份 | 固定配置期望 | 本次实际读回 |
|---|---|---|
| robot0 | `/World/CR12_0`；agv world `(0,0,.053)` m、WXYZ `(1,0,0,0)` | NOT_REACHED |
| robot1 | `/World/CR12_1`；agv world `(0,2,.053)` m、WXYZ `(1,0,0,0)` | NOT_REACHED |
| 每台物理结构 | 7 rigid body、6 活动关节、1 world fixed joint、10 collision；Articulation 本地 batch[0] | NOT_REACHED |
| 每台相机 | 本 root `/link_6/SingleViewCamera`；fixture `/World/CameraInterfaceFixture_Rr`；请求 product `CR12_Rr_Capture`、Camera `cr12_r{r}_camera`（r=0 时 `cr12_r0_camera`）、独立 observer | NOT_CREATED |

源码先建立共享 sim/ground/light，再准备两套 robot/camera/fixture/OFF product/visual/contact，全部完成后各自 seal，随后只一次 global reset。每台合法初态 q/dq 写入一次；两台全部完成后共同一次 `sim.forward`，验证 native 数组、clock 和 App update 计数未变。预期共享初始化 **2 physics ticks**，不是逐台各 2 步；CPU fake 驱动验证该顺序，真实值本次未取得。

`_check_instance_composition:368`、`_check_dual_preinit:405`、`_check_native_instance:442` 逐实例核对 body/joint targets、world anchor、resetXformStack、碰撞过滤及明确 native view 路径。world anchor 只在本次场景 pre-init 中按本台 body/frame 校准。独立 expected root 来自上述固定 spec，不从 actual 倒推出期望；CPU 反例验证 robot1 误在原点仍会拒绝。创建顺序 `[1,0]` 与本地 body/joint 顺序改变均按身份/名称映射；spec 要求唯一 exact-int `{0,1}`。

Host 在两台 setup/native/camera 与跨机初态检查之后，才冻结本次实际 scanner 四目标：每台第一点为 initial scanner + `(0.0106981457149994,0,-0.000155046722254002)` m、`Ry_world(+1°) × R_initial`，第二点为本台 initial scanner。全局 task0/1 属于 robot0，task2/3 属于 robot1；world/m/WXYZ/scanner frame 保持，FK 不重复加 root 平移。表只读，新 reference 从实际接单状态开始。**本次没有冻结到任何 runtime 目标，不把名义坐标或 CPU fake 值列成实测。**

allowlist 固定 `[1,2,4]` 的 `[[[1,1,0,0],[0,0,1,1]]]`；8 个 cost 均按各自 actual scanner 到同一四目标欧氏距离计算。它是本区准入限制，不代表跨区不可达。raw proposal `[1,2] int64`，NO_CLAIM=4；EXECUTING 列保持有效 task continuation。

### 2.2 共同推进、保持与碰撞守卫

`Host.step:433` 每块 12 子步，全部 `prepare` → 两台同刻 actual 到本次量化 q_cmd 的联合 midpoint/endpoint 几何检查 → 全部 `submit` → **一次** `sim.step(render=False)` → 两台 native/self/ground/frame/contact/actual cross guard → 缓存两份 context → cadence 到期 **一次** render → 两台 finish/FSM/OFF。第二台 submit 失败后不 step，也不回写状态伪装撤回；真实一步已经发生时，parent 计数先于后续 guard 更新，即使 guard 抛出也保留该步事实。

每台持有独立 controller、integrator、q_cmd、初始信任锚、reference、runner、capture context 与数据槽。初始无绑定保持目标只冻结一次；退役后保持上次合法最终目标。actual 仅作反馈，不逐 tick 追随重设目标，不每步写 joint/root state。新 claim 重建本请求 reference/稳定窗/预算，不重置 q_cmd/controller/integrator；终态 FSM 不再累积旧 deadline，剩余块尾继续真实保持与 OFF 守卫。保持不创建假 claim，不手写 P2 状态。

原 DLS λ=.01、2/s 积分器、4 秒 reference、5° 信任域、baseline PD/effort、TGS8/2、gravity、外力逐迭代开关、GPU physics/cuda:0、dt=1/120/render_interval=2、原 AABB 容差均保留。

新增 `check_cross_geometry:465` 覆盖全部 10×10 shape 组合。每次先算当时整机包络；可靠分离时记录一次 coarse +100 logical coverage、0 fine；否则逐 pair，不能跨机器人套用同 body/相邻例外，包含 agv-agv/同名 link。`_make_contacts:522` / `_check_contacts:546` 保留每台7个单body sensor，加入对方全部7 body 完整路径，核对 native body/filter/矩阵维度/时间新鲜度，保留本台 agv-ground 支撑例外与0.1N阈值。没有碰撞豁免或间距调整。这些是有界离散守卫，不是连续时间避障规划；**本次真实最小间隔、接触力和 guard 次数均未取得**，旧离线0.270116059 m不是本次证据。

### 2.3 单批 authority、相机隔离与共同 terminal

adapter 仍每次调用维护一个 observed/admitted/report/committed 链，binding/pending/custody/delivery 按 robot 分槽。身份包括 run/domain/episode/robot/task/claim，初始两个 claim 可以共享 token。另台新 claim 或 `artifact=None` 的物理 publication 不破坏本台有效 birth，但缺失 provenance 不能仅凭 owner 相同重建。CPU 使用真实 production authority 测试两 C 同一事务、单 C 另一台继续、共享 receipt 的逐效果匹配、重复 ACK 幂等返回，以及重复 report/退役拒绝。

块末最新保持/OFF/健康边界与全部 C/F/R/U/Rc 一起形成一个 typed report、一个 producer、一个 transaction。`_deliver:270` 先验证并保全整批 receipt/history，再逐 pending 确认和退役；退役异常按既有事务后 bookkeeping poison 停止，不能重发整批或回滚已完成 C。正常 C 需要真实 fresh raw custody + OFF + 最新健康保持；PNG 保存独立，保存失败不能抹掉 acquired/C。

两 Camera 的 product 实际路径取创建返回值并读关系，逻辑资源预存在即拒绝。独立 Hydra、RGBA/ReferenceTime annotator、observer、factory context 与 buffer；每台 request limit=2。`render_evidence:233` 与 Host `_record_isolation:411` 记录同一 global render 前后：A OFF 且 own-product 计数不增、observer 仍活跃；B 前 ON，在本次 render 的本请求中收到实际 fresh 元数据，可立即 OFF。不同 product 同 frame 合法；产品身份不能用 frame 全局去重替代。OFF 仍要求本 Hydra updates=false/Camera pause/独立观察≥30正常render与原 quiet 条件；其他产品事件不增加本台机会次数。

入口只安排 proposal：首次 `[[0,2]]`；robot0 task0 receipt/退役后最早 OPEN 接 task1；robot1 task2 退役且 task1实际开始后≥72共同ticks，再最早 OPEN 接task3。无新增 claim 时 `step_without_new_claim`，不直接写 effective。parallel 统计要求同 tick 两台 actual joint 变化；相位 interval 和有序 OFF/fresh 片段独立记录，不能以四图代替。

四任务总体 terminal 才允许 logical rebuild；各槽须已退役、无 pending、两台 OFF/保持/健康。旧 coverage=[true×4]、completion_count=[2,2] 与最后一 transition 增量 completed_tasks 分开。使用当前 builder 的 actor145/critic143；一个 environment sidecar/history/ACK。rebuild 保留两台 q/dq/q_cmd/scanner 和共同 clock，不物理 reset 或重建 product。入口先完成**两台全部最终 native 参数读回**，才逐台 release；资源生命周期预期各 prepare/initialize/release=1、begin/OFF/retire=2。真实首末 mass/COM/完整惯量/drive、四 custody、终态及上述计数本次都 **NOT_REACHED**。

## 3. 针对性 CPU 与静态检查

全部在 `C:\isaacenvs\isaac45_harl\python.exe`，通过 `D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl` 执行；root/adapter/监督组另带 `--no-capture-output`，runtime/hooks/camera组没有该参数。没有重跑旧182项套件、全仓测试或 Phase B。修改 Python 与本任务 repro 已 py_compile；`git diff --check` 无差异错误（仅现有 LF/CRLF 提示）。

| 测试文件（Q/，最后一项在L/repro） | 已执行最终结果 | 检查性质/限制 |
|---|---:|---|
| `test_cr12_scan_executor.py`、`test_cr12_lifecycle_host.py`、`test_cr12_dual_lifecycle_integration.py` | 15+5+8=28 PASS | 27行为测试+1纯AST；dual 使用真实 authority，物理/事件为fake |
| `test_cr12_lifecycle_execution_adapter.py`、`test_cr12_dual_execution_adapter.py` | 21+21=42 PASS | 真实 production lifecycle/事务与反例，fake物理 |
| `test_cr12_runtime_support_hooks.py`、`test_cr12_dual_runtime_support.py` | 6+20=26 PASS | 19普通fake API/几何行为、5 AST摘取函数后执行、1纯AST、1签名；不能等同 PhysX 接入验证 |
| `test_cr12_dual_camera_capture.py` | 19 PASS | 17正常导入/fake API行为+2 AST摘取语句后执行；反序创建新增用例通过 |
| `test_cr12_camera_capture.py`、`test_cr12_single_view_integration.py`、`test_cr12_single_view_entry.py`、`test_cr12_camera_mount.py` | 41+17+13+6=77 PASS | 旧相机与入口直接受影响回归；事件/Camera/native为fake，含源码检查 |
| `test_supervisor_cpu.py` | 10 PASS | 9合成/纯函数行为+1 argv行为兼AST旧监督结构比较；没有启动App |

以上按不重复测试方法计总数202：**197项包含CPU行为断言（其中8项AST摘取真实函数/语句后执行、1项argv行为兼AST比较），另有4项纯AST/source结构检查、1项签名检查。** 四项纯结构检查位于 executor:314、dual_runtime_support:295、camera_capture:336、single_view_entry:154；签名项在 runtime_support_hooks:120。不把AST/源码比较冒充完整动态集成，不把fake帧或合成完成记录冒充真实RGBA/运行。

关键 CPU 覆盖对应如下：

| 用户要求 | 已运行用例定位与结论 |
|---|---|
| 反序创建、错root、局部名称映射、world anchor、一次reset/forward | dual_runtime:54–144、272–295；dual_camera:231、257、355、358；拒绝robot1在原点、跨root映射或4初始化步 |
| 跨机100pair无self例外、对方完整filter/维度/fresh | dual_runtime:155–246；粗筛/细筛量分别核对，含agv-agv与时间/映射反例 |
| 不追actual的固定保持、跨请求控制连续、后submit失败不step | dual_integration:196、254、266；真实session方法与fake场景，q_cmd/积分器保持 |
| token共享、continuation、来源丢失、EXECUTING raw4、idle不报U | dual_adapter:143–205、319–342；真实resolver的非法NO_CLAIM是拒绝该proposal，不擅自改变合法旧effective |
| 同步两C单事务、单C继续、共享receipt、重复ACK/退役失败 | dual_adapter:153–188、245–307、342–373；dual_integration:215整批C及两份custody保留、poison不rebuild |
| 终态块尾仍守卫、较早成功不能覆盖后来恶化 | dual_integration:204 在fake第665tick失败，真实计数保留665，无C交付、两份pending custody仍在 |
| 同frame双product、旧身份拒绝、buffer/factory不串台、OFF机会去重 | dual_camera:73–175、257；旧 camera/单机集成回归；A释放不影响B |
| 本区两任务不触发环境done、143sidecar与一行ACK、custody经rebuild保留 | dual_integration:168、226；dual_adapter:207、235、373；fake全case经真实authority形成一条environment历史 |
| 业务/覆盖不足/异常退出分类 | dual_integration:240、dual_camera:396；监督合成正例/反例，coverage不足与native均禁止重试 |

CPU 开发阶段曾出现 fake fixture 的资源接口、计数/非刚体姿态插值问题；已在首 App 前分别补正产品resolver fixture、真实步先记录、采用原 `FrozenPoseSegment`。源码审查删除一处不存在的重复 spectator 导入，实际 spectator 设置沿共享 sim；修正 spec 不应强求创建顺序。最后相应测试重新通过后才冻结输入。没有把这些纯 CPU 问题计作 App 重试，也没有 runtime 失败后的补丁。

最后 root 回归实际命令：

```powershell
& 'D:\miniconda3\Scripts\conda.exe' run --no-capture-output -p 'C:\isaacenvs\isaac45_harl' python -m pytest -q source/isaaclab_tasks/test/test_cr12_scan_executor.py source/isaaclab_tasks/test/test_cr12_lifecycle_host.py source/isaaclab_tasks/test/test_cr12_dual_lifecycle_integration.py
```

结果 `28 passed in 15.79s`、exit0。其余实际定向命令如下；`$file`表示表中各文件分别执行，没有为报告再运行一遍：

```powershell
# adapter两文件，以及 L/repro/test_supervisor_cpu.py（分别执行）
& 'D:\miniconda3\Scripts\conda.exe' run --no-capture-output -p 'C:\isaacenvs\isaac45_harl' python -B $file
# runtime/hooks两文件，以及camera组五文件（分别执行）
& 'D:\miniconda3\Scripts\conda.exe' run -p 'C:\isaacenvs\isaac45_harl' python -B $file
```

表中Q/与L/展开规则见第1节；所有所列最终结果exit0。runtime missing-peer用例局部修正后额外执行一次指定用例并通过，不重复加总；camera早期13/18项通过轮次也不加总。各修改文件通过 `python -m py_compile <对应文件>`。运行前 `L/repro/preflight.json` 定向记录23个直接相关代码/测试/监督输入、已通过检查及冻结case，不是全仓库/全资产库存。

## 4. 唯一 App 的实际命令、阶段与故障

工作目录 `E:\Project\IsaacLab_HARL`。实际父命令（历史记录，**不要在现有attempt目录重跑**）：

```powershell
$env:PYTHONUTF8='1'
& 'D:\miniconda3\Scripts\conda.exe' run --no-capture-output -p 'C:\isaacenvs\isaac45_harl' python -u logs/scan_assignment/20261008_cr12_dual_lifecycle_integration/repro/supervise_cr12_dual_lifecycle_integration.py --attempt-dir logs/scan_assignment/20261008_cr12_dual_lifecycle_integration/attempt_01 --integration-case dual_normal_staggered
```

监督器使用继承环境，仅进程内覆盖 `PYTHONUTF8=1, HEADLESS=0, ENABLE_CAMERAS=1, LIVESTREAM=0, XR=0`，在 owned Windows Job 中实际执行：

```powershell
D:\miniconda3\Scripts\conda.exe run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/run_cr12_dual_lifecycle_integration.py --usd-path E:\Project\IsaacLab_HARL\source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\assets\rokeaCR12\derived\fixed_lift0_v1\usd\cr12_fixed_lift0.usd --output-dir E:\Project\IsaacLab_HARL\logs\scan_assignment\20261008_cr12_dual_lifecycle_integration\attempt_01 --device cuda:0 --external-forces-every-iteration on --enable_cameras --info --integration-case dual_normal_staggered --kit_args=--/app/userConfigPath=E:/Project/IsaacLab_HARL/logs/scan_assignment/20261008_cr12_dual_lifecycle_integration/attempt_01/private_config/user.config.json
```

现有 Windows helper 在 `AppLauncher` 前追加 `--/app/vulkan=false`，保留原 private kit_args；最终 Kit argv、实际加载配置与 D3D12 均有同次日志证据。experience 是 `E:\Project\IsaacLab_HARL\apps\isaaclab.python.rendering.kit`。本轮没有切换 headless/Vulkan/CPU，没有修改公共配置或 Windows helper。

| 时刻/相对进程树起点 | 实际事件 |
|---|---|
| 18:08:50.456 +08:00 / 0s | 监督启动；Conda PID26900，目标Python PID15904 |
| +1.484s | `process_started`；实际Python为指定harl环境，UTF8=1 |
| +1.828s | `startup_prepared` 与 `pre_app_cuda_begin` |
| +3.140s | `pre_app_cuda_ready`，cuda:0 / torch2.5.1+cu121 / synchronized=true；随后 `app_constructor_begin` |
| Kit原文10:08:55 / App约1.585s | `Created window: width=120,height=0`（console:3356） |
| Kit原文10:08:56 / App约2.924s | `Invalid desc parameters`；`createSwapchain failed. Width:120,height:0,Format:9`；graphics environment失败（console:3924–3926） |
| 同次console:3932及后续栈 | `Windows fatal exception: access violation`；viewport window构造栈，调用仍在SimulationApp/AppLauncher构造 |
| 18:09:13.781 +08:00 / +23.328s | 目标exit3221225477=`0xC0000005`，Conda exit4294967295=`0xFFFFFFFF`；全部所属进程退出、无remaining PID |

Kit文本未显式标时区，原文比同次监督的本地时间少8小时；此处保留两者，不改写日志。Kit日志 `kit_20261008_180853.log:2688,3398` 实际 DX12/D3D12，驱动610.60。异常模块/偏移没有本次Windows事件证据，保持 UNKNOWN，不将Python栈文件称为故障DLL，也不与旧Vulkan故障强作同因。

pre-App CUDA准备沿原 `E/view_scan_assignment.py:51`：cuda:0 上16×16张量乘法并同步，实际返回。该helper没有结果数值回读比较；本轮没有另做 post-App CUDA验收，更没有 PhysX GPU步进。App构造未返回，因此不宣称完整GUI/CUDA/viewer链通过。

### 4.1 private 配置实际证据

源 `C:\isaacenvs\isaac45_harl\Lib\site-packages\omni\data\Kit\Isaac-Sim\4.5\user.config.json` 只读，原窗口字段为 `width=-1,height=-1,maximized=true`。本次独占新副本只将三个值变为 `1440,900,false`，语义差异恰好3项，其余相等。运行前后 source 的字节/mtime/hash及语义均不变；private 也没有运行写回。加载日志明确指向本次private，最终CLI还请求window1440×900、renderer1280×720。

这些证据只证明**配置隔离和参数转发成功**，不能证明实际窗口尺寸生效。真实native窗口120×0与请求不同；composed window settings未导出，UNKNOWN。本次没有通过修改更多字段、共享配置、驱动或依赖追查根因。现有private方法曾获接受的历史结果不被回写，但它不能保证本次窗口成功。

### 4.2 预算、资源与未进入的工作

构造预算180s、全树480s（监督预留最后10s收尾、工作470s），本次全树23.328s、未超时。Job已分配、bytes输出排空完成、supervisor_errors=[]、termination_requested=false；退出是崩溃后的全树退出，不是 `SimulationApp.close()` 正常返回。

| 计数 | 预期正常case上限/要求 | 实际 |
|---|---|---|
| App | 主1+仅局部修复1 | 1；原生故障后停止，0修复 |
| 项目shared sim/reset/初始化 | 1 sim / 1 reset / 2 ticks | 未构造项目sim，初始化NOT_REACHED |
| Host/global physics/render | 420 / 5040 / 2520 | 0 / 0 / 0；不推算Kit内部update/渲染次数 |
| 每台本地检查/请求 | ≤5040 / 2 | 0 / 0 |
| 请求预算 | pose960、capture600、close240，总1800；wall60/30s；新请求余量1812 | 未进入 |
| claim/receipt/C/F/R/U/Rc | 实际真实authority决定 | 未创建domain/Host，均无运行事实 |
| 四张原始RGBA/metadata/raw custody/OFF | 每请求独立真实数据与关闭 | 0份，未创建扫描Camera/product；无可交付双机原图 |
| 同时实际运动、mixed phase、有序A OFF/B fresh | 至少一段/片段 | NOT_REACHED，无global render索引可报告 |
| 首末native、参数不变、terminal/rebuild/ACK/release | 两台真实独立快照与共同终态 | NOT_REACHED，不以CPU结果代填 |

显存证据仅为整卡离散读数：18:08:12运行前1420MiB；本次console:2918–2921启动期1590MiB；18:09:46退出后1588MiB，总显存8188MiB。观察到的三样本最大1590MiB**不是进程峰值、不是torch allocated/reserved，也不是双机稳态显存需求**。本次没有取得这些峰值，不能从此断言有/无未来OOM；日志显示的故障是窗口/swapchain/访问异常。

## 5. 收尾、交付与下一步

已经保留全部实现、针对性测试、唯一失败attempt与同次console/Kit/监督退出证据。原设计离线布局和旧单机attempt均未覆盖。收尾只读核对：23份冻结输入与首App前一致，attempt_02不存在，主报告17个新增链接均有效，index无暂存变更。没有产生双机PNG、视频、ZIP、全仓hash/新ledger或重复日志群。`L/`受现有Git忽略规则影响，是本机辅助证据，不暗示新checkout自带；AgentRead本轮仅新增本主Markdown和必要导航更新。

本轮修改清单：第2节8个既有生产文件+1个新入口、1个既有测试+4个新测试；新增本报告，小范围更新 `AgentRead/TASK_PROGRESS.md`、`REPORT_INDEX.md`；本地辅助为 `L/repro/` 与 `L/attempt_01/`。`_cr12_visual_geometry.py`、Windows helper、authority核心和机器人资产未改。未执行 Git add/commit/push/reset/restore/checkout/clean/stash 等写操作；没有安装/升级/改系统配置或连接设备。

下一步仅审阅本次代码、CPU覆盖与启动失败。若继续，需要**另行明确授权本次GUI窗口构造故障的定向诊断及运行预算**；重点是已加载private且请求尺寸正确时，实际native窗口为何成为120×0。当前证据不足以判定唯一根因，也不支持改双机布局、降分辨率、串行相机、放宽碰撞/到位/fresh/OFF或更换驱动。先恢复同一真实启动链，再在新授权下回到同一个已冻结双机case；不能拼接不同attempt补成PASS。

双机真实初始化、碰撞/native/参数、并行运动、四次按需采集、相机隔离、共同terminal及正常关闭均待验证；共享任务竞争/跨机器人转交仍 **NOT_ESTABLISHED**。真实构件、depth/pointcloud、实体设备、一般故障恢复、学习策略和可变规模checkpoint均未建立。本轮结束不自动授权这些工作。

**实施及授权内检查已完成；唯一GUI尝试发生原生启动故障并按约停止。双机运行尚未验证，等待GPT/用户审阅。**

## 6. 辅助证据对应表

| 结论/检查项 | 文件位置 | 关键字段或定位 | 用途/限制 |
|---|---|---|---|
| 总体失败、预算、全树退出 | [supervisor_result.json](../../../../../../../../logs/scan_assignment/20261008_cr12_dual_lifecycle_integration/attempt_01/supervisor_result.json) | classification、stage_events、exit code、budget_after、remaining_owned_pids | 本次最终进程事实；false完成项是未通过，不全部代表执行后业务失败 |
| 120×0及访问异常 | [console.log](../../../../../../../../logs/scan_assignment/20261008_cr12_dual_lifecycle_integration/attempt_01/console.log) | 3356、3924–3950；2918–2921整卡显存样本 | 同次日志，不能代推窗口唯一根因 |
| 实际D3D12 | [同次Kit日志](../../../../../../../../logs/scan_assignment/20261008_cr12_dual_lifecycle_integration/attempt_01/kit_20261008_180853.log) | 2688、3398；3913附近故障 | 保留副本，原生来源路径在监督记录 |
| 未进入场景、CUDA准备返回 | [result.json](../../../../../../../../logs/scan_assignment/20261008_cr12_dual_lifecycle_integration/attempt_01/result.json) | pre_app_cuda、phase_order、completed_physics_steps=0、status=RUNNING | 原始中断快照，不是完成记录 |
| 实际完整命令 | [command.json](../../../../../../../../logs/scan_assignment/20261008_cr12_dual_lifecycle_integration/attempt_01/command.json) | cwd、argv、child_environment_overrides、预算 | 只对attempt_01历史有效 |
| private仅3项、source不变 | [prepare摘要](../../../../../../../../logs/scan_assignment/20261008_cr12_dual_lifecycle_integration/attempt_01/source_private_config_summary.json)、[运行前后摘要](../../../../../../../../logs/scan_assignment/20261008_cr12_dual_lifecycle_integration/attempt_01/config_runtime_summary.json) | diff_count=3、all_other_values_equal；source/private diff=0 | 配置隔离成功，不等于窗口生效 |
| 首App前输入冻结 | [preflight.json](../../../../../../../../logs/scan_assignment/20261008_cr12_dual_lifecycle_integration/repro/preflight.json) | 23直接输入、checks、fixedcase、GPU前样本 | 定向代码及检查摘要；不是全仓审计 |
| 双机真实authority CPU链 | [集成测试](../../../../../../../../source/isaaclab_tasks/test/test_cr12_dual_lifecycle_integration.py)、[adapter测试](../../../../../../../../source/isaaclab_tasks/test/test_cr12_dual_execution_adapter.py) | 第3节用例定位 | fake物理/事件，不能生成真实运行PASS |
| 映射/接触/相机CPU检查 | [runtime测试](../../../../../../../../source/isaaclab_tasks/test/test_cr12_dual_runtime_support.py)、[camera测试](../../../../../../../../source/isaaclab_tasks/test/test_cr12_dual_camera_capture.py) | 反序、root、contact、frame/product、OFF | 明确区分行为/AST摘取范围 |
| 本轮监督与复制规则 | [监督器](../../../../../../../../logs/scan_assignment/20261008_cr12_dual_lifecycle_integration/repro/supervise_cr12_dual_lifecycle_integration.py)、[private helper](../../../../../../../../logs/scan_assignment/20261008_cr12_dual_lifecycle_integration/repro/prepare_private_user_config.py)、[监督CPU测试](../../../../../../../../logs/scan_assignment/20261008_cr12_dual_lifecycle_integration/repro/test_supervisor_cpu.py) | main、assess_history、completion_checks、owned Job/drain | 一次性本地复现辅助，不是生产依赖，不授权第二次App |
