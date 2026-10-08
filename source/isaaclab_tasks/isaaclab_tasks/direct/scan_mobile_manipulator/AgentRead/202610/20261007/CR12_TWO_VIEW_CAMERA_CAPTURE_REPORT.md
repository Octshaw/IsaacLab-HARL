# CR12 双视点连续按需相机采集报告

执行日期：2026-10-07，Asia/Shanghai（UTC+08:00）。状态：**TWO_VIEW_CAPTURE_INTEGRATION_PASS，等待 GPT/用户审阅**。本报告不自行授予 GPT REVIEW PASS。

## 1. 结论与范围

本轮完成了一个 App 内的两段连续 scanner pose 执行，以及同一 Camera/product 的两次按需采集。唯一主运行 `attempt_01`：**1324 个受控物理步 / 11.033333909 秒**，两点各实际稳定到位、取得本次新 RGBA、独立确认 OFF、保存；最后统一释放资源。构造14.469秒、所属进程树50.672秒，目标Python/Conda均自然exit0，全部所属进程退出，无超时、强杀或runtime重试。App预算 **1/3**，成功后未使用剩余额度。

新增能力是跨请求控制连续性、请求结果隔离和设备资源复用。整个序列只创建一次场景/机器人，reset与授权初态joint-state写入各一次；两个目标预先冻结；第二段从第一段关闭及保存后的实际状态出发，保留上一条真正提交的q_cmd，返回冻结的初始scanner位姿。没有中间reset、teleport、状态回写、相机独立位移或资源重建。两点分别取得source frame **571 / 902**；OFF各 **30 render / 30 quiet / 在途0**。

用户已确认此前单视点采集 **GPT REVIEW PASS**；visual、基本驱动、formal pose、大幅demo既有接受范围保持。本轮没有重跑旧验收。Phase B保持 **COMPLETE / GPT REVIEW PASS / CLOSED**；没有改变MRTA owner/completed、claim/release/reassign，也没有把普通采集失败定义为永久failed-pair。

本文路径缩写均从仓库根 `E:\Project\IsaacLab_HARL` 起算：

- `T = source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator`。
- `E = scripts/environments`，`Q = source/isaaclab_tasks/test`。
- `L = logs/scan_assignment/20261007_cr12_two_view_capture`，`A = L/attempt_01`。
- Python：`C:\isaacenvs\isaac45_harl\python.exe`；Conda：`D:\miniconda3\Scripts\conda.exe`。
- 当次HEAD：`24ecbad7dd1bdcd006399b64bfb757a86b71aeec`。既有dirty worktree和已暂存历史ZIP删除保持；本轮没有Git写操作。

## 2. 实现变化与旧默认保护

| 本轮新增/修改 | 关键符号与行号 | 内容 |
|---|---|---|
| 新增 [run_cr12_two_view_capture.py](../../../../../../../../scripts/environments/run_cr12_two_view_capture.py) | `main:5` | 显式选择两点runner和整体结果标签，复用原startup/cleanup |
| 新增 [_cr12_two_view_capture.py](../../../../../../../../scripts/environments/_cr12_two_view_capture.py) | `TwoViewSequence:40`、`handoff_goal_2:120`、`run_two_capture:172`、`resource_continuity:308` | 固定两目标顺序、独立SingleViewRequest、交接门槛、结果冻结/保存、最终统一检查和释放 |
| 新增 [_cr12_pose_continuation.py](../../../../../../../../scripts/environments/_cr12_pose_continuation.py) | `FrozenPoseSegment:16`、`TwoViewPoseContinuation:47`、`queue_goal_2:106`、`activate_pending:127` | 小型显式continuation；目标一次冻结，保留控制对象/命令/信任锚，重置局部参考与稳定窗口 |
| 修改 [run_cr12_pose_target.py](../../../../../../../../scripts/environments/run_cr12_pose_target.py) | `_pose_ticks:185`，激活345、yield536 | 可选`continuation=None`；同一generator推进两请求，全局step/render连续 |
| 修改 [run_cr12_single_view_capture.py](../../../../../../../../scripts/environments/run_cr12_single_view_capture.py) | `initialize_capture_run:267`、`execute_capture_request:311`、`finalize_capture_scene:529`、`run_capture:557`、`main:578` | 抽取准备、单请求推进、最终native/释放；旧默认仍一个`formal_goal_1`后结束 |
| 修改 [_cr12_camera_capture.py](../../../../../../../../scripts/environments/_cr12_camera_capture.py) | `prepare:100`、`begin_capture:264`、`_after_camera_update:307`、`_observe_event:360`、`observe_close:419`、`release:474` | 默认`max_requests=1`；两点入口显式2。请求OFF与最终release分离；局部接收槽重置，全局source历史和失败保持 |
| 新增Q下三个测试文件 | `test_cr12_pose_continuation.py`、`test_cr12_two_view_capture.py`、`test_cr12_two_view_integration.py` | 坐标/交接、序列门槛/不可变性、共享真实逻辑的CPU整合 |
| 修改Q下后端测试 | `test_cr12_camera_capture.py` | 两请求、旧/重复事件、OFF后异常新输出、资源生命周期 |
| 新增L/repro辅助项 | `supervise_cr12_two_view_capture.py`、`test_supervisor_cpu.py`、`prepare_private_user_config.py`、`check_two_view_local_path.py` | 本任务有界监督、fresh private、名义CPU路径核对；不被生产代码import |

`_cr12_single_view_capture.py`、`_cr12_camera_mount.py`、`_cr12_pose_control.py`、`_cr12_runtime_support.py`、Windows helper、资产和installed packages未修改。生产入口不import AgentRead/logs脚本，不读取旧attempt结果充当当前状态。辅助监督器只核对本轮最多三个独立App及当前小范围代码preflight，不需要旧单点历史运行才能启动新入口。

默认保护：将continuation专门化为None后，整个旧pose模块AST等价；原standalone与原单点继续保持分支均保留。直接受影响的旧单点入口、单点整合与pose子集均通过CPU检查。没有以此宣称旧入口又做了一次runtime验收。后端新增全局事件分类增强duplicate/迟到事件处理；未降低旧fresh/OFF要求，旧默认仍最多一次请求。

## 3. 保持的配置与初始化

唯一机器人：`T/assets/rokeaCR12/derived/fixed_lift0_v1/usd/cr12_fixed_lift0.usd`及现有引用层，fixed-base/lift0/v1、baseline PD；原关节effort/限位、TGS8/2、dt=1/120s、render_interval=2、gravity=(0,0,−9.81)、external-forces-every-iteration显式on。GPU pipeline/GPU dynamics实际启用，关节张量cuda:0。仍用原 **AABB**：非相邻体pair与运动臂对地面、每侧2mm余量；没有推广manual OBB或实现通用避障。

保留`virtual_camera_mount_v1`：camera prim `/World/CR12/link_6/SingleViewCamera`，product `/Render/OmniverseKit/HydraTextures/CR12SingleViewCapture`。名字保留SingleView不代表换设备。T_ES为既有scanner固定旋转；T_SC平移`(0.168921722410,−0.129429244995,0.192403900145)m`、旋转identity。world风格+X forward/+Z up经原WORLD_TO_USD_AXES转成USD −Z forward/+Y up。pinhole RGBA uint8 640×480、HFOV60°、aperture36×27mm、焦距31.176914536mm、clipping0.01–10m；fx=fy=554.256258px，cx=320、cy=240，无畸变/景深。虚拟安装不是厂家参数或实体标定。

原非物理四色fixture在准备阶段放置一次、全程固定。没有改光心/光轴/分辨率、移动或改色以制造图像差异，也没有加入真实构件。

pre-init visual一次apply/seal，reapply/revoke均0；初始化后与最终检查一致。首次reset内部推进 **2步/0.016666667536秒**，另计，hidden settle0；授权初态q=dq=0只写一次，root-state写入0。

Camera OFF时，一次非渲染`sim.forward`发布授权初态的Fabric：native q/dq/body-link三组数组、native clock `[2,0.016666667536]`、App update计数5均未变，额外physics/App update均0。发布前camera/native组合偏差0.124558mm/0.000579188rad是已接受初始化过程中的暂态；发布后1.279416e−7m/1.019521e−7rad通过，随后才冻结目标。未把publication放入每个goal；普通render内部既有forward不属于新的初始化。

## 4. 冻结目标、连续控制与交接

profile：`two_view_local_return_v1`。首次运动前，取本次实际native link_6组合T_ES得到scanner初态T_WS0。goal1为原目标偏移`(0.0106981457149994,0,−0.000155046722254002)m`，姿态世界Y左乘+1°；goal2精确等于T_WS0。完整实测冻结值如下，单位米、world坐标、WXYZ；不以名义URDF姿态代替运行初态。

| 目标 | world position / m | quaternion WXYZ |
|---|---|---|
| goal_1 | 0.11569813498616334, -0.14999984204769135, 2.8878440110475214 | 0.3826688689803681, 0.008062296543587387, 0.003339507340627997, 0.9238443504067398 |
| goal_2 | 0.10499998927116394, -0.14999984204769135, 2.8879990577697754 | 0.38268344045175545, 2.9037242642047637e-8, 6.71314150164411e-9, 0.9238795291616796 |

两点距离 **0.010699269191185055m**，姿态差 **1°**。第二点检验真实闭环返回初始scanner位姿，不要求关节回零；结束最大轴角仍约0.53245°。

首次App前，以当前派生URDF/原10 collision AABB检查正反向各51个witness样本及36个邻域扰动，共 **138** 个样本通过。名义witness `(0,1,−1.5,0,1.5,0)°`达goal1，反向到q0；witness与笛卡尔插值最大偏差38.761963μm、最低arm z1.239999229m。这只支持局部名义可行性，实际DLS路径仍逐步在线守卫；未将witness直接当命令，也未增加Jacobian rank gate。

每段沿原4秒五次平移/最短旋转插值；DLS λ=.01、COM Jacobian adapter、2/s命令积分保持。当前native Jacobian首次检查：COM linear误差4.3159058e−7、actor候选0.118532743，唯一匹配COM，无额外校准物理步。实际每tick下发一对position/velocity target，一次physics step。全局提交核对1324、命令中点/端点检查2648；只有一个generator/controller/integrator。

交接同时要求goal1稳定到位、fresh snapshot冻结、OFF确认、PNG及metadata保存成功、无未解决失败。保存不推进physics：第一次约16ms、第二次15ms，各前后native clock相同且product=false。第一段结束后交接前后：

- 全局受控step **662**；native step **664**、time **5.533333621919155s**；累计render **331**。
- actual q/dq/scanner逐值相同；交接自身0physics、0新product完成帧；product持续OFF。
- goal2参考起点为实际`p=(0.11571165919303894,−0.15000304579734802,2.887899875640869)m`、`q_WXYZ=(0.3826444777609372,0.008062879158090397,0.0033375260652276427,0.9238544552788094)`，不同于goal1理想目标。
- controller ID2269425001680、integrator ID2269424753424，绑定1次，交接generation662；保留初态零向量±5°信任锚。activation确认actual/clock/q_cmd均未改。
- global663/local1才执行goal2第一步，不重复消费global662；只重置轨迹局部时间、PoseMonitor稳定窗、单请求预算/接收槽/close统计。global render继续原奇偶相位。

紧凑交接快照（角度rad、速度rad/s；下发值与实际值分别保存）：

| 关节 | actual q | actual dq | 上次q_cmd | 上次dq_cmd |
|---|---:|---:|---:|---:|
| joint_1 | -0.0003849762 | 0.0002429495 | -0.0005610672 | 0.0002058595 |
| joint_2 | -0.0009127596 | -0.0015049248 | -0.0020168938 | -0.0015108101 |
| joint_3 | 0.0173331853 | 0.0034147073 | 0.0147262095 | 0.0033622608 |
| joint_4 | 0.0029997497 | 0.0006680417 | 0.0028927044 | 0.0006065704 |
| joint_5 | 0.0010327132 | -0.0018467375 | -0.0012860353 | -0.0018494669 |
| joint_6 | -0.0025622111 | -0.0009167579 | -0.0023088984 | -0.0009173993 |

q_cmd−actual q最大绝对差 **0.002606975846rad**，原承载补偿连续保留，没有将q_cmd重新设成actual q或0。目标、参考起点、控制连续性与设备身份分别保存在`two_view_profile`、`views[*].trajectory_start`、`handoff`、`resource_continuity`。

## 5. 同一设备的两次采集及结果隔离

`OwnedCameraCapture` prepare/initialize一次，底层同一Camera/product/Hydra/annotators/独立observer。再次begin先确认上一请求OFF_CONFIRMED、未release、无sticky error、ID合法；只清本请求接收槽与OFF计数，保留真实source frame/time、已处理事件历史和全局计数。每次记录新ON source rational基线、buffer/source帧基线、product计数基线后resume并开启Hydra updates。

接收沿用真实product NEW_FRAME → installed Camera原super更新 → event SWH与同份ReferenceTime匹配 → post-super clone及独立readonly数组。两请求路径要求source严格晚于本次ON；不会从resume后的旧current_frame取数据换ID。metadata沿用的通用文字“at/after ON”不是精确阈值定义；本轮代码和实测比较均为严格大于。

OFF先设并读回Hydra `updates_enabled=False`，Camera.pause解除当前数据接收回调；同一个独立完成observer继续观察。每次重置关闭计数，至少30正常render机会且最后至少6次连续静默，本次各实际30/30。关闭不靠停止写盘、暂停timeline或销毁product。两个运动段新增unique product完成帧均0，交接新增0。

| 项目 | goal1 / capture1 | goal2 / capture2 |
|---|---:|---:|
| attempt_id | attempt_01 | attempt_01 |
| ON局部 / 全局step | 600 / 600 | 600 / 1262 |
| product通知/unique基线 | 0 / 0 | 1 / 1 |
| buffer/source帧基线 | 0 | 571 |
| ON SyntheticData source-time | 19/1（570/30） | 901/30 |
| 接受source frame / ReferenceTime frame | 571 / 571 | 902 / 902 |
| 接受source-time | 571/30 > 19 | 902/30 > 901/30 |
| 接收局部 / 全局 / native step | 602 / 602 / 604 | 602 / 1264 / 1266 |
| 接收simulation/rendering_time / s | 5.033333595842123 | 10.550000550225377 |
| DATA_RECEIVED发布 | 1 | 1 |
| OFF正常render / 最后quiet / 在途 | 30 / 30 / 0 | 30 / 30 / 0 |
| acquired / saved / confirmed_off | true / true / true | true / true / true |

source rational是SyntheticData时间域，不与simulation秒/墙钟直接比较；不用帧号恰好+1作为新帧要求。接收metadata的scanner/native dq来自该次正常render前的native post-step，camera Fabric读回在render后；支持采集窗口中实际保持，不声称精确曝光时刻位姿或实体同步。

三次（初始化后/交接/最终释放前）设备身份如下，来自仍被持有的真实对象；是进程内Python对象ID，不冒充跨进程/native指针。结合创建/初始化次数和无重建路径提供连续性证据。Hydra对象是本地Replicator `scripts/utils/viewport_manager.py` 中stored `hydra_texture`，不是按路径重新查到的临时wrapper。

| 资源 | 对象ID | 比较 |
|---|---:|---|
| Camera | 2269451307232 | 三次相同 |
| render product | 2269451315104 | 三次相同 |
| Hydra texture handle | 2269399841392 | 三次相同 |
| 独立 product observer | 2269282027696 | 三次相同 |
| RGBA annotator | 2269428096624 | 三次相同 |
| ReferenceTime annotator | 2269428096576 | 三次相同 |

scene/sim/robot/native simulation view/articulation view五项身份亦三次相同。计数：prepare、product/camera/observer create、initialize各 **1**；begin、request resume、request pause、OFF请求、OFF确认各 **2**；release调用及有效完成各 **1**。数据接收订阅按原pause/resume分别建立，subscription ID不同且上一条先解除；持续不变的是独立observer，不会叠加observer。

全App product通知=unique completion=2、Camera更新2；GUI全局事件667。duplicate/late/旧帧拒收/确认OFF后异常新输出均0；errors与close_evidence_errors为空。**2是实测结果，不是强制事件总数只能为2**。重复同source通知拒收并单列；相同frame冲突source-time、确认OFF后新的完成帧均形成sticky错误，禁止下一请求。

第一份真实snapshot、原终态request对象、冻结view结果保留到第二次结束；六类证据（RGBA数组、snapshot metadata、request summary、view result、PNG、metadata文件）前后SHA256全部相等。第二份独立`view_02`，未清空/覆盖第一份。两张PNG可以同像素；图像差异和hash不同不作为fresh条件。

## 6. 唯一真实运行、时间轴与物理结果

### 6.1 命令、模式与预算

cwd `E:\Project\IsaacLab_HARL`。本次实际调用（历史命令，请勿再次使用已有attempt目录）：

```powershell
& 'D:\miniconda3\Scripts\conda.exe' run --no-capture-output -p 'C:\isaacenvs\isaac45_harl' python -X utf8 -u 'logs/scan_assignment/20261007_cr12_two_view_capture/repro/supervise_cr12_two_view_capture.py' --attempt-dir 'E:\Project\IsaacLab_HARL\logs\scan_assignment\20261007_cr12_two_view_capture\attempt_01'
```

监督器生成新private后实际启动的子命令：

```powershell
& 'D:\miniconda3\Scripts\conda.exe' run --no-capture-output -p 'C:\isaacenvs\isaac45_harl' python -u 'scripts/environments/run_cr12_two_view_capture.py' --usd-path 'E:\Project\IsaacLab_HARL\source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\assets\rokeaCR12\derived\fixed_lift0_v1\usd\cr12_fixed_lift0.usd' --output-dir 'E:\Project\IsaacLab_HARL\logs\scan_assignment\20261007_cr12_two_view_capture\attempt_01' --device cuda:0 --external-forces-every-iteration on --enable_cameras --info '--kit_args=--/app/userConfigPath=E:/Project/IsaacLab_HARL/logs/scan_assignment/20261007_cr12_two_view_capture/attempt_01/private_config/user.config.json'
```

子环境继承父进程并覆盖PYTHONUTF8=1、HEADLESS=0、ENABLE_CAMERAS=1、LIVESTREAM=0、XR=0。实际Python UTF8 mode1；既有pre-App CUDA helper完成后才AppLauncher，最终kit_args追加D3D12 token，`apps/isaaclab.python.rendering.kit`、GUI、camera enabled、cuda:0。Kit实际Graphics API **D3D12**，NVIDIA driver610.60，native窗口1440×900，renderer请求1280×720。composed_window_settings未导出，仍UNKNOWN，不用请求值替代该字段。

源`C:\isaacenvs\isaac45_harl\Lib\site-packages\omni\data\Kit\Isaac-Sim\4.5\user.config.json`只读；private准备仅宽/高/maximized三项语义差异（−1/−1/true→1440/900/false）。运行后源byte/hash/mtime保持、语义差0；Kit写回private新增一项console-source布尔，语义差1，窗口目标保持。未修改真实source、Conda持久变量或共享设置。

每goal仍pose≤960steps/8s、capture≤600/5s且wall≤60s、close≤240/2s且wall≤30s，总≤1800/15s；序列≤3600/30s。每App构造≤180wall、owned tree≤360wall（work350+cleanup10）。本次构造14.469秒，全树50.672秒，未触及预算。

### 6.2 共用时间轴

受控step不含初始化2步；native step恒为受控step+2。墙钟为监督器收到事件时相对启动的耗时，不是曝光时间。

| 事件 | goal局部step | 全局受控step | native物理时间/s | 墙钟耗时/s |
|---|---:|---:|---:|---:|
| App ready | — | — | — | 17.578 |
| goal1提交，两个target已冻结 | 0 | 0 | 0.016666668 | 19.016 |
| goal1稳定到位 / ON1 | 600 | 600 | 5.016666928 | 32.281 / 32.297 |
| fresh1 / OFF1请求 | 602 | 602 | 5.033333596 | 32.406 / 32.422 |
| OFF1确认 | 662 | 662 | 5.533333622 | 33.625 |
| 保存1完成 / 交接完成 | 662 | 662 | 5.533333622 | 33.703 / 33.766 |
| goal2提交/激活，无额外step | 0 | 662 | 5.533333622 | 33.781 |
| goal2稳定到位 / ON2 | 600 | 1262 | 10.533333883 | 46.734 / 46.750 |
| fresh2 / OFF2请求 | 602 | 1264 | 10.550000550 | 46.859 / 46.875 |
| OFF2确认 / 保存2完成 | 662 | 1324 | 11.050000576 | 48.141 / 48.250 |
| 最终native/释放后sequence完成 | — | 1324 | 11.050000576 | 48.359 |
| work_completed / stop返回 / close开始 | — | 1324 | 不再取native | 48.438 / 48.547 / 48.594 |
| 全部所属进程自然退出 | — | — | — | 50.672 |

两goal之间没有遗漏的保持step。各goal本地pose600+capture2+close60=**662**，共1324；这是实测结果，逻辑没有硬编码662×2。CPU整合使用不同两段步数验证时间基准。各段121连续样本/1.000000052秒稳定窗（local480–600；第二段global1142–1262），原2mm/0.25°/native速度≤0.01rad/s条件未改。

| 测量 | goal1 | goal2 |
|---|---:|---:|
| 到位位置误差/mm | 0.069558789 | 0.046870631 |
| 到位姿态误差/° | 0.004687158 | 0.005032539 |
| ON保持样本 | 2 | 2 |
| ON保持最大位置误差/mm | 0.069042420 | 0.046275601 |
| ON保持最大姿态误差/° | 0.004625586 | 0.004970533 |
| ON保持最大native速度/rad/s | 0.003835491 | 0.000693197 |
| 关闭结束位置误差/mm | 0.057567534 | 0.017970244 |
| 关闭结束姿态误差/° | 0.003034632 | 0.001589697 |
| 关闭结束最大native速度/rad/s | 0.003414707 | 0.000567253 |
| 本段正常render / 后步六guard（各） | 331 / 662 | 331 / 662 |

六类clock/joint/contact/geometry/frame/render_clock守卫全局各**1324**，未接受post-step0；禁止接触最大0N、root位移/转角最大0、arm collision最低1.239998764m，实际最大轴偏离初态0.993672142°，原5°信任域保持。camera mount663次检查，最大2.503792e−7m/3.058966e−7rad；最终native view有效、native参数逐值不变、visual seal通过。只证明当前局部路径/场景的守卫通过，不是任意障碍主动规划或真实构件安全认证。

`views[*].pose_summary`计数为本地差值，运动极值仍为App起点以来累计量；goal2累计极值不能当其专属窗口极值。落盘trace是选样摘要，非1324行完整回放；完整守卫计数来自实际循环累计，无逐帧raw dump。

### 6.3 资源结束、退出与警告

goal2保存后，冻结/核对两个结果，在有效生命周期内复核native/挂载/visual/参数，再最终release。`camera_backend_final.release.complete=true`、errors空、release_effective_count=1，`resource_release_before_stop=true`。只释放自有product/连接、保留camera prim，不删除全局Render、不live撤销visual；随后stop返回、调用close，不调用失效native getter。

目标result保留`WORK_COMPLETED_PENDING_PROCESS_EXIT`，自身无法在退出后更新；外层`supervisor_result.json`综合完成事件、文件、业务/物理/设备与退出证据得出最终PASS。未观察`app_close_returned`，不编造；自然退出依据Conda/target各0、owned Job为空、remaining_owned_pids=[]、console drain完成。开始12:19:48.418+08，结束12:20:39.103+08；target PID28388、Conda PID12572，failure/secondary/native-fault/supervisor-error均空。

Kit仍有camera xform op、DLSS低输入分辨率、host-copy性能、关闭时removePath/已释放hydratexture等警告；无[Error]/[Fatal]。不宣称零warning，也无证据将它们归为本次物理/native失败。PNG仍640×480 RGBA，DLSS内部输入提示不等同输出尺寸变化。

## 7. 图像、保存事实及不可变性

可直接查看两张原始图，无需再启动App：

| 请求 | 原始PNG | metadata | 大小 | PNG SHA256 |
|---|---|---|---:|---|
| goal1/capture1 | [view_01/camera_rgba.png](../../../../../../../../logs/scan_assignment/20261007_cr12_two_view_capture/attempt_01/view_01/camera_rgba.png) | [capture_metadata.json](../../../../../../../../logs/scan_assignment/20261007_cr12_two_view_capture/attempt_01/view_01/capture_metadata.json) | 86551B | `c08d7b96f25de702480e7876e21bb936b09c88cfaeb50e9535505cfde4cd5b46` |
| goal2/capture2 | [view_02/camera_rgba.png](../../../../../../../../logs/scan_assignment/20261007_cr12_two_view_capture/attempt_01/view_02/camera_rgba.png) | [capture_metadata.json](../../../../../../../../logs/scan_assignment/20261007_cr12_two_view_capture/attempt_01/view_02/capture_metadata.json) | 85062B | `451ce9a6d31230ffad6787157f36fb19aaf29f6b30cb9f510caf5cf26bc8db22` |

两文件独立读回hash与记录一致；已静态打开两张PNG，均显示现有四色fixture。外观便于查看，成功仍指对应目标位置实际开启并获得本次数据；没有深度比例、分割、点云、重建或精度门槛。

第一份RGBA hash `a5788fd56198c1cd149be77445675cb28236cc03d6901b12d1949168817dba23`，metadata文件hash `9c2da9036fcb3136645726c162f762233336f7a9c2613e31c6652690843f619b`，第二次完成前后不变。其余snapshot metadata/request/result摘要保存在`first_view_immutability`，六类比较全true。metadata包含各自ON基线、source frame/time、接收真实pose语义、OFF及保存；不能跨请求贴新ID复用旧数据。

## 8. CPU检查、局部问题与失败范围

最终 **114个不同的针对性unittest用例通过**，重复执行不重复计数。另有修改Python的py_compile、解释器核对、名义路径138样本及默认AST核对，均通过。未例行重跑旧107项、全仓/Phase B/visual/sweep验收。

| 测试 | 用例 |
|---|---:|
| Q/test_cr12_camera_capture.py（共享后端完整文件） | 32 |
| Q/test_cr12_pose_continuation.py | 15 |
| 旧PoseExtractionTests4 + manual默认marker边界1 + 原控制3 | 8 |
| Q/test_cr12_single_view_integration.py | 17 |
| Q/test_cr12_single_view_entry.py | 13 |
| Q/test_cr12_two_view_capture.py | 10 |
| Q/test_cr12_two_view_integration.py | 7 |
| L/repro/test_supervisor_cpu.py | 12 |

覆盖一次冻结、非identity root/WXYZ/q与−q/世界Y左乘、actual起点/连续q_cmd、全局step/render与局部预算、原5°锚、唯一控制器、OFF/save门槛、终态冻结、每次独立close30、一次prepare/init/release、pause/resume重订阅、旧buffer/迟到/重复通知拒收、同像素不同源接受、第一失败第二未开始、第一成功第二失败、文件不覆盖、资源身份替换拒绝、异常与exit0不洗掉失败。整合使用实际请求/相机后端/continuation逻辑与fake physics/events，是CPU证据。

实施期发现未归一化测试四元数造成continuation测试失败，修正fixture后通过；运行前审查修正列表形式q_cmd序列化、目录创建/记录失败使当前请求残留RUNNING的终态问题，针对性CPU通过。补丁导出曾遇Windows命令长度限制，改用本地文本差分写补丁；未影响运行。这些均在首App前，不是runtime失败或新App。**attempt_01一次成功，无runtime修复/重试。**

CPU检查命令如下，cwd均为仓库根。多数测试使用-B；pose专属/旧pose子集通过同一解释器直接python执行，不启动App：

```powershell
$Conda = 'D:\miniconda3\Scripts\conda.exe'
$EnvPrefix = 'C:\isaacenvs\isaac45_harl'
$Q = 'source/isaaclab_tasks/test'
$Repro = 'logs/scan_assignment/20261007_cr12_two_view_capture/repro'
& $Conda run -p $EnvPrefix python -B "$Q/test_cr12_camera_capture.py"
& $Conda run -p $EnvPrefix python "$Q/test_cr12_pose_continuation.py"
& $Conda run -p $EnvPrefix python "$Q/test_cr12_single_view_capture.py" PoseExtractionTests
& $Conda run -p $EnvPrefix python "$Q/test_cr12_manual_visual.py" ManualEntryBoundaryTests.test_visual_false_does_not_import_or_construct_marker_runtime
& $Conda run -p $EnvPrefix python "$Q/test_cr12_pose_control.py" PoseControlTests.test_trust_region_native_velocity_and_fixed_dt PoseControlTests.test_submission_mismatch_does_not_commit PoseControlTests.test_arrival_requires_final_reference_and_121_inclusive_samples
& $Conda run -p $EnvPrefix python -B "$Q/test_cr12_single_view_integration.py"
& $Conda run -p $EnvPrefix python -B "$Q/test_cr12_single_view_entry.py"
& $Conda run -p $EnvPrefix python -B "$Q/test_cr12_two_view_capture.py"
& $Conda run -p $EnvPrefix python -B "$Q/test_cr12_two_view_integration.py"
& $Conda run --no-capture-output -p $EnvPrefix python -X utf8 -B "$Repro/test_supervisor_cpu.py"
& $Conda run -p $EnvPrefix python "$Repro/check_two_view_local_path.py"
```

py_compile按负责文件分批执行，覆盖第2节六个生产文件、四个测试文件与repro四个Python文件；`repro/preflight.json`记录CPU通过及10项直接启动代码hash，只用于本任务有界监督，不是全仓hash或新资格审计体系。

失败处理保持：acquired、saved、off_confirmed分开；保存失败保留acquired但阻止下一goal；关闭未确认不得继续运动；物理/native失效不追加physics凑OFF，必要时STOP_UNCONFIRMED并结束。第一成功不会因第二失败回滚；未开始goal保留NOT_STARTED/BLOCKED。禁止内部重开ON重试或跳过失败。本次两请求成功，非零在途、取消、保存失败、关闭异常/恢复、GPU/native失败分支 **CPU_ONLY / NOT_INJECTED**，不随正常PASS宣称全部恢复能力已验证。

## 9. 人工复现、范围与交接

可以直接查看第7节两张图。若用户日后自行复现下面命令，将单独启动一个有界GUI App；本轮未执行这条人工命令。它每次生成新目录、新private，使用相同入口/物理/两目标/camera模式和owned-process监督，不需要新demo或checkpoint：

```powershell
Set-Location -LiteralPath 'E:\Project\IsaacLab_HARL'
$runName = 'manual_' + (Get-Date -Format 'yyyyMMdd_HHmmss_ffffff')
$attemptPath = Join-Path 'E:\Project\IsaacLab_HARL\logs\scan_assignment\20261007_cr12_two_view_capture' $runName
& 'D:\miniconda3\Scripts\conda.exe' run --no-capture-output -p 'C:\isaacenvs\isaac45_harl' python -X utf8 -u 'logs/scan_assignment/20261007_cr12_two_view_capture/repro/supervise_cr12_two_view_capture.py' --manual-check --attempt-dir $attemptPath
```

监督器在prepare/Popen前校验source保持、fresh private、mode、UTF8及本任务代码preflight；目录存在即拒绝、不覆盖。未来若修改相关代码，应重新做相应CPU检查并更新本任务preflight，不能为了绕过校验直接改hash。`--manual-check`显式人工运行不会自动循环/重试，不是本轮自动追加授权。

结论限于固定底盘/lift0/v1、本局部两目标、同一virtual RGBA设备与fixture。未完成任意路径/真实构件避障、第三点/长期重复、多机、depth/pointcloud、真实结构光/实体标定/曝光同步、异常恢复runtime、多seed、MRTA适配、RL训练/策略推理/checkpoint。保留逐tick generator/单请求边界便于后续复用；未接effective assignment→执行反馈→生命周期，未放开公共event gate。

没有改资产、PD/solver、阈值、installed packages、驱动、真实user.config/持久环境；运行前后8项直接资产/源输入hash保持。只读Git核对，无add/commit/push/tag/reset/restore/checkout/clean/stash。没有删除/恢复历史产物，没有ZIP、全仓库存或逐帧图像转储。

文档新增本主报告，小范围更新`AgentRead/TASK_PROGRESS.md`与`REPORT_INDEX.md`：记录单视点已审通过、本轮双点运行待审及下一阶段边界，不重写旧报告。实现/测试在E/Q，repro/数据在L；AgentRead本轮只新增Markdown。

**本轮实施与有限验证完成，等待 GPT/用户审阅；已经停止，不自动增加视点或进入真实构件、MRTA、异常恢复实验、训练、Git提交或历史清理。**

## 10. 辅助证据对应表

`logs/`受现有忽略规则影响，以下运行证据与repro当前仅本机可取，未随Git提交；新checkout不会自动包含。需要外部审阅时可另行提供最小材料，本轮不生成复制包。

| 结论/检查项 | 文件位置 | 关键字段或定位 | 用途及限制 |
|---|---|---|---|
| 两点控制/采集/handoff/生命周期 | [A/result.json](../../../../../../../../logs/scan_assignment/20261007_cr12_two_view_capture/attempt_01/result.json) | `views`；4865/6032阶段计数、8408 handoff、10253不可变性、11040生命周期、11131身份 | 实际循环累计；退出待外层 |
| 退出、Graphics API、窗口/预算 | [A/supervisor_result.json](../../../../../../../../logs/scan_assignment/20261007_cr12_two_view_capture/attempt_01/supervisor_result.json) | 46–58退出、574–582两PASS/构造、637耗时、750故障、761分类 | 完成加自然退出，不只exit0 |
| 完整子命令与子环境 | [A/command.json](../../../../../../../../logs/scan_assignment/20261007_cr12_two_view_capture/attempt_01/command.json) | argv/cwd/child_environment_overrides | 实际命令 |
| 共用时间轴与警告 | [A/console.log](../../../../../../../../logs/scan_assignment/20261007_cr12_two_view_capture/attempt_01/console.log)；[保留的Kit日志](../../../../../../../../logs/scan_assignment/20261007_cr12_two_view_capture/attempt_01/kit_20261007_121951.log) | console7007–7062；Kit3515 D3D12 | Kit原本机路径见app.kit_log_file，必要副本在A |
| 两次数据与source/OFF | 第7节两PNG及metadata | metadata6 source、397 OFF、555 ON基线 | 两份独立帧，非精确曝光pose |
| source/private隔离 | [config_runtime_summary.json](../../../../../../../../logs/scan_assignment/20261007_cr12_two_view_capture/attempt_01/config_runtime_summary.json)；[source_private_config_summary.json](../../../../../../../../logs/scan_assignment/20261007_cr12_two_view_capture/attempt_01/source_private_config_summary.json) | source_unchanged、semantic diff | 不复制个人配置全文到报告 |
| 首App前局部检查 | [two_view_local_path.json](../../../../../../../../logs/scan_assignment/20261007_cr12_two_view_capture/repro/two_view_local_path.json)；[检查脚本](../../../../../../../../logs/scan_assignment/20261007_cr12_two_view_capture/repro/check_two_view_local_path.py) | 138样本、目标/witness | CPU名义路径 |
| 旧pose默认保持 | [默认AST核对](../../../../../../../../logs/scan_assignment/20261007_cr12_two_view_capture/repro/pose_continuation_default_checks.json)；[pose补丁](../../../../../../../../logs/scan_assignment/20261007_cr12_two_view_capture/repro/pose_continuation.patch) | old_default_module_ast_equal、23 tests | 静态/CPU保护 |
| 共享抽取与后端 | [共享抽取补丁](../../../../../../../../logs/scan_assignment/20261007_cr12_two_view_capture/repro/shared_capture_request_extraction.patch)；[顺序请求补丁](../../../../../../../../logs/scan_assignment/20261007_cr12_two_view_capture/repro/camera_backend_sequential_requests.patch) | 本轮修改前后差异 | 保留用户既有工作 |
| 新核心CPU测试 | [continuation](../../../../../../../../source/isaaclab_tasks/test/test_cr12_pose_continuation.py)；[sequence](../../../../../../../../source/isaaclab_tasks/test/test_cr12_two_view_capture.py)；[integration](../../../../../../../../source/isaaclab_tasks/test/test_cr12_two_view_integration.py) | 15/10/7 | synthetic/fake不冒充GPU |
| 有界人工入口 | [supervisor](../../../../../../../../logs/scan_assignment/20261007_cr12_two_view_capture/repro/supervise_cr12_two_view_capture.py)；[private helper](../../../../../../../../logs/scan_assignment/20261007_cr12_two_view_capture/repro/prepare_private_user_config.py)；[监督CPU](../../../../../../../../logs/scan_assignment/20261007_cr12_two_view_capture/repro/test_supervisor_cpu.py)；[preflight](../../../../../../../../logs/scan_assignment/20261007_cr12_two_view_capture/repro/preflight.json) | owned tree/drain，最多3自动App，无自动重试 | 本任务repro，生产代码不依赖 |
