# CR12 单视点到位后的按需相机采集：实施与有限真实验证

日期：2026-10-07，Asia/Shanghai（UTC+08:00）。状态：**SINGLE_VIEW_CAPTURE_INTEGRATION_PASS；等待 GPT/用户审阅**。本轮使用 **2/3 App**，其中第一个初始化读回失败、第二个完成闭环；不继续使用剩余额度。

本文路径缩写均以仓库 `E:\Project\IsaacLab_HARL` 为根：`T=source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator`，`L=logs/scan_assignment/20261007_cr12_single_view_capture`，`E=scripts/environments`，`Q=source/isaaclab_tasks/test`。环境为 `C:\isaacenvs\isaac45_harl`，Conda 为 `D:\miniconda3\Scripts\conda.exe`。本轮读取的 HEAD 为 `24ecbad7dd1bdcd006399b64bfb757a86b71aeec`；已有 dirty worktree 和暂存删除保持，不执行 Git 写操作。

## 1. 结论与范围

用户已确认 2026-10-07 的 scanner_corrected.png、agv_corrected.png 外观无问题，VISUAL_PREINIT_INTEGRATION 已获 GPT REVIEW PASS。**显示修复分支收口**；旧报告的当时待审/FAIL 标签不回写。本轮按新授权实现一个正式小目标到位后的专属相机采集，没有另起外观调查或旧 pose 资格复验。

App02 的真实顺序为：初始化专属 product OFF → 实际执行原正式小目标 → 第 600 步稳定到位 → ON → 第 602 步取得真实 RGBA → OFF → 再保持/渲染 60 步确认关闭 → 保存 → 释放本模块资源 → stop → close 请求 → 所属进程自然退出。

| 层次 | 本轮真实结果 |
|---|---|
| 场景/虚拟安装/显示集成 | 同一 fixed-base/lift0/v1，pre-init apply 1 次、seal，运行期 revoke/reapply 均 0 |
| 正式 pose | 600 步、受控 5.000000261 秒；121 个连续稳定样本、跨度 1.000000052 秒 |
| 运动时采集关闭 | 600 个 post-step OFF 检查，专属 product 完成事件 0 |
| 本次新帧 | 同一专属 product 的 SWH event frame 与 Camera ReferenceTime frame 都为 **558**，真实 buffer 更新后复制 |
| 独立数据/保存 | 一帧 640×480、RGBA、uint8；原始 PNG 86,551 bytes，保存成功 |
| OFF 确认 | 实际 updates_enabled=false，独立观察器持续工作；30 次正常 render 机会、30 次连续静默、在途事件 0 |
| 保持/物理/native | 六类 guard 各 662 PASS；native 参数首末逐值相同，挂载 332 次独立读回通过 |
| 完成/退出 | acquired/saved/confirmed_off 均 true，SUCCEEDED_OFF；工作完成记录齐全，Conda/目标 exit 0、全部所属自然退出 |

总受控 **662 步 / 5.516666954 秒**，初始化另计 2 步；App 构造 13.875 秒、全树 35.203 秒。没有超时、强杀或记录到的原生故障。CPU 针对性检查最终 **107/107** 通过；合成事件测试与上述真实运行分开计。

这证明当前 Windows GUI/D3D12/cuda:0、固定机器人、小目标与虚拟相机的一次闭环；不证明任意目标、第二视点、重复使用同一个 Camera 对象、非零在途排空、多机调度、精确曝光位姿、真实光学标定或真实构件避障。depth/pointcloud、结构光模型、双视点和 MRTA 接入均未实施。Phase B **COMPLETE / GPT REVIEW PASS / CLOSED**、basic/formal 及已接受 demo 的原结论保持。

## 2. 实际文件变化与旧默认保护

| 文件/关键符号 | 本轮变化 |
|---|---|
| [E/run_cr12_single_view_capture.py](../../../../../../../../scripts/environments/run_cr12_single_view_capture.py):22/114/222/263/516 | 新独立入口；固定原 formal 配置、唯一场景时钟、pre-init 相机/fixture/覆盖、初始化 publication、分阶段有界推进、证据与收尾 |
| [E/_cr12_camera_mount.py](../../../../../../../../scripts/environments/_cr12_camera_mount.py):23/66/104/127/184/200/236 | 新不可变 virtual_camera_mount_v1；只读 scanner bounds；光轴/光学换算、无物理 prim、独立实际相机位姿读回 |
| [E/_cr12_camera_capture.py](../../../../../../../../scripts/environments/_cr12_camera_capture.py):50/77/98/193/214/236/273/294/311/344/376 | 新独占 Camera/product 后端；post-super 同帧快照、Hydra ON/OFF、独立事件观察、所有权限定的释放及无损 PNG 保存 |
| [E/_cr12_single_view_capture.py](../../../../../../../../scripts/environments/_cr12_single_view_capture.py):39/97/103/155/189/201/239 | 新纯 CPU 单请求状态机；分离 acquired、artifact_saved、off_confirmed，保持检查及独立阶段预算 |
| [E/run_cr12_pose_target.py](../../../../../../../../scripts/environments/run_cr12_pose_target.py):185，`_pose_ticks` / `_run_pose` | 仅必要 generator 抽取；旧 `_run_pose` 消费默认 generator，新入口显式采用 `continue_after_arrival=True`、已有 scene/initial 与 before_render 回调 |
| Q/test_cr12_camera_mount.py、test_cr12_camera_capture.py、test_cr12_single_view_capture.py、test_cr12_single_view_entry.py、test_cr12_single_view_integration.py | 新针对性 CPU 测试；安装、状态、事件/快照、启停、预算、异常与入口整合 |
| Q/test_cr12_manual_visual.py | 只把原 AST 测试定位从 `_run_pose` 转向 `_pose_ticks`，补旧薄包装/默认参数断言；不改 marker 测试期望或旧动作 |
| L/repro/supervise_cr12_single_view_capture.py、test_supervisor_cpu.py | 本任务监督及测试；fresh private、相机参数传递、Windows Job 全树预算、完成/退出联合判定；无自动重试 |
| L/repro/prepare_private_user_config.py | 复用已接受 private helper，内容 SHA256 为 `9209c28d707ebab79db9de87fcf111b116b2f107ccd0240303467ac918ffb82d` |
| 本文、AgentRead/TASK_PROGRESS.md、AgentRead/REPORT_INDEX.md | 一份新主报告、小范围当前状态与主题导航更新 |

旧入口 CLI 继续拒绝 scan cameras；默认 formal/manual 的控制、目标、时序、到位判据和停止行为保持。抽取后的默认分支在消除 generator suspension/返回副本、代入默认参数后，与原完整模块 AST 等价，证据见 `L/repro/pose_default_ast_equivalence.json`；这不是旧入口额外 runtime 通过声明。本轮没有启动旧 formal/manual/sweep App。

保留 absolute-pose DLS λ=.01、原 COM Jacobian adapter、2/s command integrator、实际 position/velocity joint targets 与全部原守卫。只在初始化写一次 joint state；运行期没有 teleport、回写机器人状态或 camera world pose。到位后沿用原 integrator 状态及最终目标继续反馈；旧 8 秒 timeout 仅约束未到位运动，新采集/关闭各有独立预算。

生产模块不 import AgentRead/logs 的一次性脚本。未改 `_cr12_pose_control.py`、`_cr12_runtime_support.py`、`_cr12_visual_geometry.py`、Windows helper、机器人配置、资产、安装包或物理参数。必要旧入口抽取与本轮 repair 差异保存在 `L/repro/*.patch`，没有复制整套源码或资产。

## 3. 本地 API、安装与光学参数

### 3.1 本地来源及实际接线

本地 `I=C:/isaacenvs/isaac45_harl/Lib/site-packages/isaacsim`；Isaac Sim 4.5，Camera 扩展 0.2.9，Replicator `1.11.35+106.5.0.wx64.r.cp310`，Hydra texture `1.4.0+d02c707b.wx64.r.cp310`，SyntheticData `0.6.10+d02c707b.wx64.r.cp310`。使用实际安装文件定向核对，未使用新版本网页 API 替代、未修改 installed packages。

| 本地源文件/位置 | 使用语义 |
|---|---|
| I/exts/isaacsim.sensors.camera/isaacsim/sensors/camera/camera.py:50/176/311/360/372 | world→USD 轴矩阵；绑定已有 render_product_path；频率设 -1 接收每个完成事件；同份 get_current_frame(clone=True)；initialize 的初始零 buffer 不算数据 |
| 同文件:429/436/450/462 | PLAY 自动 resume；pause/resume 只管理 Camera 回调。窄子类先调用原 `_data_acquisition_callback`，原 graph/update 完成后才检查事件并克隆快照，不依赖回调注册先后猜测 |
| 同文件:508/1070/1118/1155/1453 | world-style 实际位姿、focal/aperture 单位接口及内参读回 |
| I/extscache/omni.replicator.core-1.11.35+106.5.0.wx64.r.cp310/omni/replicator/core/scripts/create.py:1526 | `rep.create.render_product(..., force_new=True)`；保留专属 handle，创建后立即 OFF；Camera 绑定其路径，检查未另建第二 product |
| 同扩展 scripts/viewport_manager.py:75、annotators.py:800/841 | 只销毁本模块拥有的 product、detach 自己的 annotators；不删全局 Render 分支 |
| I/extscache/omni.kit.hydra_texture-1.4.0+d02c707b.wx64.r.cp310/omni/hydratexture/_hydra_texture.pyi:293/300 | `updates_enabled` 的真实 getter/setter；实际限制该 product 渲染调度，不是停止写盘 |
| I/extscache/omni.syntheticdata-0.6.10+d02c707b.wx64.r.cp310/omni/syntheticdata/scripts/sensors.py:24/89 | NEW_FRAME 的 product/rational-time 解析与真实 `swh_frame_number`；与 Camera ReferenceTime 联合核验 |
| I/exts/isaacsim.core.utils/isaacsim/core/utils/xforms.py:84/169 | Camera 的 world pose 经此优先读取 Fabric parent world/local；独立于 native link×安装矩阵 |
| source/isaaclab/isaaclab/sim/simulation_context.py:502/591/710 | `forward()` 更新运动学并发布 Fabric；普通 render 也先 forward；初始化局部修复不 render、不 step、不 app.update |

真实专属 Camera 为 `/World/CR12/link_6/SingleViewCamera`，唯一 product 为 `/Render/OmniverseKit/HydraTextures/CR12SingleViewCapture`。`--enable_cameras` 与子进程 `ENABLE_CAMERAS=1` 正确传递，实际 experience 为 `E:\Project\IsaacLab_HARL\apps\isaaclab.python.rendering.kit`。已接受 Windows/pre-App CUDA 准备顺序保持；实际日志为 D3D12，不将旧无相机 experience 的结果移植过来。

### 3.2 冻结的 virtual_camera_mount_v1

W=world；E=实际 link_6 link frame；S=既有 scanner frame；C=world-style camera（+X forward、+Z up）。继续使用 `T_ES=Rz(135°)`、零平移；目标仍是 S 的目标。

只读取 `T/assets/rokeaCR12/model/scanner_sys_scanner_visual.obj` 的必要顶点和派生 URDF scanner visual origin。0.001 缩放仅施加一次，通过已有 T_ES 还原到 S 后：

- S bounds min = (−0.148955841060, −0.296358489990, −0.000000183110) m；max = (0.148921722410, 0.037500000000, 0.384807983400) m。
- `p_SC=(x_max+.020,y_center,z_center)=(0.168921722410,−0.129429244995,0.192403900145)` m，`R_SC=I`。
- `T_EC=T_ES×T_SC`，平移为 (−0.027925398586,0.210965992226,0.192403900145) m，旋转 Rz135°。
- USD 光学 frame 为 −Z forward/+Y up，局部旋转仅右乘一次本地官方 world→USD 矩阵 `[[0,0,−1],[−1,0,0],[0,1,0]]`；WXYZ 排列相同不代表光轴相同。

这是用户授权的**虚拟光心/外参**，不是 CAD 识别出的真实镜头、厂家参数或手眼标定。首次 App 前已固定；运行中不调整光心、光轴或 clipping。Camera 是 E 的子节点，local matrix 读回通过、resetXformStack=false，无 Mass/RigidBody/Collision/Joint，不增加机器人负载。

| 光学项 | 冻结值/实际读回 |
|---|---|
| projection / output | pinhole / 640×480 RGBA uint8 |
| 水平 FOV | 60°，无畸变/噪声模型；fStop=0，无 DOF |
| clipping | 0.01 / 10 m；实际 0.009999999776 / 10 |
| horizontal/vertical aperture | 0.036 / 0.027 m；USD raw 0.36 / 0.27（tenths of stage unit，米制场景） |
| focal length | 0.03117691453624 m；USD raw 0.3117691453624；API 读回 0.0311769157648 m |
| 内参 | 预期 fx=fy=554.256258422 px、cx=320、cy=240；实际 fx=fy=554.25628662 px |

相机/小测试板在首次 physics/native 初始化前创建。fixture 位于独立 `/World/CameraInterfaceFixture`，约 0.2×0.2 m、非对称四色、无物理 schema；以名义最终 camera pose 的前方 0.5 m 一次布置，世界位置 (−0.262364631332,0.414519382819,3.086877272253) m，不随 actual camera 移动。它是成像接口 fixture，不是真实构件，也不作为采集成功门槛。

### 3.3 实际随动核验

初态修复后及每次普通 render 后读取 `Camera.get_world_pose(camera_axes='world')`，Fabric lineage 中实际 `/World/CR12/link_6` 带 world transform，再与独立 native link pose×T_EC 比较。App02 共 **332 次**，最大位置误差 **2.503791933e−7 m**、角误差 **2.513350101e−7 rad**；原比较容差 1e−4 m / 1e−4 rad 未改变。保留初态、运动中 120/240/360/480 步、到位及接收边界样本，运行期 camera world pose writes=0。

这里确认当前读取/渲染边界的实际父子随动，未声称 renderer 精确曝光 pose。接收时实测 C 位置 (0.091095507145,0.060959756374,3.080772161484) m；实测 S 位置 (0.115681238472,−0.150004073977,2.887910604477) m。完整矩阵及时间语义在 capture metadata 中。

## 4. 初始化、运动、采集与关闭的真实时序

### 4.1 初始化与唯一时钟

顺序为 App → SimulationContext / explicit external-forces on → 原机器人 reference/anchor/setup → camera/fixture → 已接受 visual pre-init 一次 apply/seal → 专属 product 立即 OFF → 首次 reset/native views → 原零关节初始化 → Camera.initialize/pause/OFF → 一次无步进 Fabric publication → 正式运动。

App02 reset 1 次，physics clock 从 (0,0) 到 (2,0.016666667536 s)，单列初始化 2 步，无 hidden settle；joint state writes=1、root state writes=0。Camera prepare 前后 physics=(0,0)、App update count=2→2；Camera initialize 前后 physics=(2,0.016666667536)、App updates=5→5。初始化专属 product event=0；零 buffer 从未作为结果。

controlled 阶段仅主循环 `sim.step(render=False)`，每两步调用原 `sim.render()`；相机回调不调用 step/render/orchestrator/pause-play 长循环。主循环 App update count=5→336，恰为 331 次 controlled render。stop/close 内部框架收尾不并入受控步，也不作为 OFF 排空证据。

### 4.2 同一正式小目标与保持

相对本次初始化实测 S：world 平移 (0.0106981457149994,0,−0.000155046722254002) m，姿态绕 world Y 左乘 +1°；4 秒 reference，position≤2 mm、orientation≤0.25°、native |dq|≤0.01 rad/s，连续 121 个 post-step 样本、至少 1 秒。

App02 在第 480–600 步形成稳定窗口；第 600 步到位位置误差 **0.069558789 mm**、姿态误差 **0.004687157°**，当刻 max|dq|=0.003844582 rad/s。ON 窗口 2 个 post-step 样本，最大位置误差 0.069042420 mm、角误差 0.004625586°、max|dq|=0.003835491 rad/s；原容差内，没有重新稳定等待或第二次 capture。关闭保持后第 662 步末误差 0.057567534 mm / 0.003034632°。

六类 clock/joint/contact/geometry/frame/render_clock guard 各覆盖 662 步；实际目标下发检查 662 次、现有 actual→proposal 的几何 sanity 1324 次；禁止接触最大力 0，root 位移/转角漂移 0，native 生命周期有效。原 AABB 几何模式保持，并未借用大幅 demo 的 OBB 模式或添加真实构件。

### 4.3 分阶段预算与关键边界

下表“受控步”不含初始化 2 步，“native simulation time”包含初始化；不把这两个计数混用。

| 阶段 | 实际受控步 / render | 实际受控仿真时长 | 授权上限 |
|---|---:|---:|---|
| pose / MOVING_OFF | 600 / 300 | 5.000000261 s | 960 / 8 s |
| ON 等本次数据 | 2 / 1 | 0.016666668 s；墙钟 0.141 s | 600 / 5 s，墙钟 60 s |
| OFF 排空/保持 | 60 / 30 | 0.500000026 s；墙钟 1.344 s | 240 / 2 s，墙钟 30 s |
| 合计 | **662 / 331** | **5.516666954 s** | 1800 / 15 s |

| 状态/边界 | 受控步 | native step / simulation time | 关键事实 |
|---|---:|---|---|
| MOVING_OFF | 0→600 | 2→602 | 每步实际 Hydra OFF；产品完成事件始终 0 |
| ARRIVED_HOLD_OFF / CAPTURE_STARTING / WAITING_DATA | 600 | 602 / 5.016666928306 s | 先建立接收状态、清本次结果槽、读真实 frame/event 基线，再 resume/ON 并读回 true |
| DATA_RECEIVED | 602 | 604 / 5.033333595842 s | 一次独立真实 RGBA 快照，DATA_RECEIVED count=1 |
| CAPTURE_CLOSING | 602 | 604 / 5.033333595842 s | 先 product false/读回，再 Camera.pause；独立 product observer 保留 |
| SUCCEEDED_OFF | 662 | 664 / 5.533333621919 s | 30 render 排空观察完成，随后保存成功；没有第二 goal |

本次 ID 为 `formal_goal_1 / attempt_02 / capture_1`。ON 实际墙钟 11:23:34.741789+08，回调接收 11:23:34.868306+08，OFF 请求 11:23:34.889811+08，OFF 确认 11:23:36.196947+08，PNG 保存 11:23:36.223943+08。

### 4.4 新帧同源与时间边界

`_cr12_camera_capture.py:77` 的项目子类先运行 installed Camera 原回调；原回调过滤 product、同步 graph、把 RGBA 与 ReferenceTime 写入同份 current_frame。随后 post-super 才克隆该 frame，并在项目端再次复制冻结数组和 metadata；后续事件不能覆盖结果槽。验证 event 的真实 SWH frame 等于 buffer 的 ReferenceTime frame，而不是把本地计数贴到旧数组。

实际 ON 基线：product event count=0、buffer frame=0、SyntheticData rational source time=**557/30**。接收事件来自本 product；**event SWH=Camera rendering_frame=558**，source time=**558/30=18.6**，严格晚于本次 ON。Camera update count=1、product event count=1、旧帧丢弃/帧拒绝=0，完整 RGBA 维度/dtype 可访问，数据只发布一次。初始化零 buffer、错误 product、旧 capture、不同步 event/buffer 均不能通过；相同像素的新帧允许通过。

**18.6 是 SyntheticData source 时间域，不是物理仿真时间。** Camera `rendering_time=5.033333595842123`，与该接收 tick 的 native simulation time 相等；回调 wall time 是 UNIX epoch 秒，FSM 的 `wall_time` 字段是 monotonic deadline 时钟，保存时间又单独记录。没有把这些字段互相替换。metadata 明确使用 receive-time cached native state、post-render camera readback 及 ON 窗口保持范围；没有可靠曝光 pose，未编造精确帧级曝光位姿。

### 4.5 OFF、失败语义与收尾

真正的 OFF 由 Hydra product `updates_enabled=False` 并实际读回完成；Camera.pause 仅停数据回调。独立全局 NEW_FRAME 观察器仍按 product 过滤，继续 30 个普通 render 机会：global events 累计 335、专属产品仍只有 1 个、OFF 后 in-flight=0、连续 quiet=30。不是凭 Camera 缓存不变、停止写盘、停止 timeline 或关闭窗口推断停止。

关闭结论仅为“已禁止本 product 新调度，且本次有界观察未再出现输出”；不宣称未来永远没有事件或实体断电。可识别的 OFF 前在途事件会记录身份、重新累计 quiet；OFF 后新 source 事件拒绝。**本次没有非零在途事件，这条分支只有 CPU 覆盖。**

状态机分别保留 acquired / artifact_saved / off_confirmed。数据成功而关闭失败时保留快照和 acquired=true，整体不能 SUCCEEDED_OFF；保存失败不能改称未出帧。正常等待在独立预算内保持 WAITING_DATA；API/超时失败进入有界关闭；物理/native/保持失效不再追加物理步来凑关闭，禁用/释放资源并报告 STOP_UNCONFIRMED。失败/cancel/保存/关闭超时均经 CPU 检查，本次 runtime 未注入这些故障。

App02 以 setup 首次 native 参数读回为基准，在 OFF 确认后进行第二次独立 native 读回并比较，完成 external flag 末次读回和 visual seal 检查，再 release 自己的 subscriptions/annotators/product，保留 camera prim，随后 stop/close。`camera_release.complete=true`、errors=[]、resource_release_before_stop=true；`camera_backend.release=null` 是释放前摘要，不能当作最终释放状态。stop 返回和 close 请求有阶段事件；**未观察 app.close 的 Python 返回事件，正常退出依据是目标/Conda exit 0 和全部所属进程自然退出。** stop 后没有 native getter 补验。

## 5. 原始相机输出

下面直接引用本次相机的原始 RGBA PNG，没有裁剪、修图、叠字或 viewport 截图替代：

![CR12 本次专属相机原始 RGBA 帧](../../../../../../../../logs/scan_assignment/20261007_cr12_single_view_capture/attempt_02/camera_rgba.png)

图中可见一次布置的红/黄/绿/蓝非对称测试板。本轮人工工具查看确认文件可解码，构图现象单独披露；不使用颜色、非黑比例、图案占比或识别结果作为成功门槛，也不将本次图像替代用户对最终成像用途的审阅。

- 文件：`L/attempt_02/camera_rgba.png`，640×480，4 通道，86,551 bytes。
- SHA256：`c08d7b96f25de702480e7876e21bb936b09c88cfaeb50e9535505cfde4cd5b46`，保存记录与落盘文件复核一致。
- [capture metadata](../../../../../../../../logs/scan_assignment/20261007_cr12_single_view_capture/attempt_02/capture_metadata.json) 包含三个 ID、camera/product、virtual T_SC、内参、source frame/time、接收/保存时间、实测 pose 与语义、ON/数据/OFF 边界、保存状态。
- acquired=true、saved=true、confirmed_off=true；artifact_error=null。没有视频、逐帧图像或全部机器人 tensor dump；紧凑 phase/pose 样本在同次 result.json 中。

## 6. 两次 App、局部失败及修复

| 同次记录（+08:00） | App 构造 / 全树 | 实际结果 |
|---|---:|---|
| attempt_01，11:11:22.011 → 11:11:44.546 | 14.000 / 22.531 s | 初始化 camera/native 位姿比较 FAIL；0 受控步、初始化 2 步，未开启采集；目标 PID 32608/Conda 均自然 exit 0，不因此写任务成功 |
| attempt_02，11:23:03.210 → 11:23:38.419 | 13.875 / 35.203 s | 初始化修复后完整 662 步闭环 PASS；目标 PID 25408、Conda PID 18188 均自然 exit 0，全树已退出 |

两次均使用 fresh private、UTF8、GUI/D3D12/cuda:0、rendering.kit、相机能力开启；监督器各自 App≤180 秒、工作≤350 秒、全部所属树≤360 秒。无 timeout/termination/native_fault_evidence/supervisor_errors。任务总预算使用 App2/3，真正进入受控运动的 App1；成功后没有补跑第 3 次。

### 6.1 App01 失败事实

`result.json` 原记录 phase=`physics_initialize`、type=`ValueError`、category=`runtime_exception`，message：

```text
Camera actual mount mismatch: 0.00012455800111410833 m, 0.0005791877710578032 rad
```

偏差为 0.124558 mm / 0.0331850°，超过原挂载比较容差。此时 native q/dq 为零，Camera 初始化完成但专属 product OFF，product event=0、camera update=0，controlled_step_attempted=false。没有故意执行额外运动、没有 PNG、没有 capture 成功。原 result/supervisor 未改写；仅 exit0 不足以覆盖内部 FAIL。

### 6.2 源码定位及最小修复

`_cr12_runtime_support.py:585–594` 在 reset 后设置授权初始零状态；`articulation_data.py:456–469` 的 link 读取会更新 native kinematics，但不发布 Fabric。installed Camera world pose 经 Fabric-aware xforms 读取，而 Camera.initialize 的 backend/view/annotator 初始化不替它发布新零状态。已有 `SimulationContext.forward():502–508` 提供无 physics/render/App update 的运动学/Fabric 发布，普通 render 也采用此路径。

仅新入口 `refresh_initial_camera_publication` 在 Camera OFF 状态调用一次 `sim.forward()`。之前读取并记录 local USD mount、Camera/Fabric 与 native 比较；之后要求 native q/dq/link 三份独立数组完全相等、physics step/time 和 App update 计数相等，再按**同一原容差**比较相机。没有改变 T_SC、135°、目标、PD、solver、初态、guard 或下发参考；没有额外 render 预热或提前打开采集。

App02 的直接前后对照：before Camera 偏差与 App01 两数完全相同；forward 后降至 **1.279416006e−7 m / 1.019520576e−7 rad**。native q/dq/link 全 array_equal，clock 仍 (2,0.016666667536)、App updates 5→5，extra physics=0、extra App update=0；local mount 符合 T_EC/光轴，reset stack=false。这支持并解决了本次初始化 publication/read-phase 缺口；不据此解释其他历史 native/图形故障。

监督器仅为这份 App01 既有记录增加窄归类：绑定原 result 与 supervisor 两 SHA、精确异常字典、0 受控/OFF/无采集/有效 native/自然退出等事实，要求显式 snapshot_copy 修复说明；不把任意 ValueError、后续失配或真实物理异常放行。原失败不改为 PASS。修复后的集成/监督/入口测试先通过，再启动新进程 App02；补丁见辅助表。

### 6.3 日志和配置限制

App02 Kit 副本 `kit_20261007_112306.log:2688/3632` 记录 DX12/D3D12，:3340 记录 native 1440×900，:5132/6959 记录 CUDA ordinal 0，驱动 610.60；torch 2.5.1+cu121。Kit 时间为 03:23，与同次监督本地 11:23+08 对应。pre-App CUDA 准备完成并同步，实际 native tensors/Jacobian 为 cuda:0；没有另加旧 CUDA benchmark。

保留非致命警告：Camera 包装转换后的 xformOp:transform 缺失提示（:6963）、DLSS 输入尺寸调整（:6977）、host-copy 性能提示（:6978）、释放阶段 removePath/接口已释放提示（:6985/:7001）。本次独立 local mount/Fabric 随动、frame/OFF、资源释放和退出证据通过；不能写“零警告”，也未为了清警告再运行或修改安装包。

真实 source `C:\isaacenvs\isaac45_harl\Lib\site-packages\omni\data\Kit\Isaac-Sim\4.5\user.config.json` 的内容/大小/mtime/hash 均未变。每次副本只按已接受规则初始化 width=1440、height=900、maximized=false，退出时 Kit 在 private 另写入一项 console source bool；该写回单列，未反写 source。实际 composed window settings 导出字段仍 UNKNOWN，native 窗口尺寸依据同次 Kit 日志。报告没有附完整个人配置。

## 7. CPU 检查、真实命令及可选复现

### 7.1 针对性 CPU 检查

先核对解释器，实际为 `C:\isaacenvs\isaac45_harl\python.exe`、Python 3.10.20。改动 Python 的 py_compile 通过；CPU import/fake 检查不启动 Kit/Isaac/CUDA。最终按不同测试计 **107**，早期失败调整后的重跑不累计成更多用例：

| 检查 | 最终通过数 | 主要覆盖 |
|---|---:|---|
| test_cr12_camera_mount.py | 6 | 缩放/T_ES/T_SC、非 identity root、q/−q、光轴、fixture 固定及光学换算 |
| test_cr12_camera_capture.py | 19 | 零/旧/错误 product、同源 frame、相同像素、快照不变、真 OFF、在途/新事件、释放、PNG |
| test_cr12_single_view_capture.py | 27 | 到位门槛、分阶段预算、正常等待、超时、取消、关闭幂等/失败粘性、保存/采集/关闭分离 |
| test_cr12_single_view_entry.py | 13 | camera/private/GUI CLI，pre-init 一次覆盖，clock/native 收尾与旧默认 |
| test_cr12_single_view_integration.py | 17 | fake 主循环成功/异常/实际失败 tick 计数；其中 7 项覆盖 initialization publication 不改 native/clock/OFF/local mount/原容差 |
| L/repro/test_supervisor_cpu.py | 13 | enable_cameras/env/参数传递、预算、完成+退出联合判定、精确首失败归类及拒绝变体 |
| 原 PoseControlTests 受影响子集 | 8 | 正式目标/reference、121/960时序、guard/clock非有限、Recorder失败粘性、CSV失败步 |
| 原 ManualEntryBoundaryTests | 4 | 薄包装/默认 false、marker懒加载、旧分类及异常分离 |

工作目录均为仓库根。新增各测试的实际命令形式（每个文件分别执行）为：

```powershell
& 'D:\miniconda3\Scripts\conda.exe' run -p 'C:\isaacenvs\isaac45_harl' python -B source/isaaclab_tasks/test/test_cr12_camera_mount.py
& 'D:\miniconda3\Scripts\conda.exe' run -p 'C:\isaacenvs\isaac45_harl' python -B source/isaaclab_tasks/test/test_cr12_camera_capture.py
& 'D:\miniconda3\Scripts\conda.exe' run -p 'C:\isaacenvs\isaac45_harl' python source/isaaclab_tasks/test/test_cr12_single_view_capture.py
& 'D:\miniconda3\Scripts\conda.exe' run -p 'C:\isaacenvs\isaac45_harl' python -B source/isaaclab_tasks/test/test_cr12_single_view_entry.py
& 'D:\miniconda3\Scripts\conda.exe' run -p 'C:\isaacenvs\isaac45_harl' python -B source/isaaclab_tasks/test/test_cr12_single_view_integration.py
& 'D:\miniconda3\Scripts\conda.exe' run -p 'C:\isaacenvs\isaac45_harl' python -B logs/scan_assignment/20261007_cr12_single_view_capture/repro/test_supervisor_cpu.py
```

两组受影响旧测试的实际命令仅覆盖上述 8+4 项：

```powershell
& 'D:\miniconda3\Scripts\conda.exe' run -p 'C:\isaacenvs\isaac45_harl' python source/isaaclab_tasks/test/test_cr12_pose_control.py PoseControlTests.test_target_uses_world_y_left_multiply_and_freezes_input PoseControlTests.test_small_angle_geodesic_endpoints_and_four_second_hold PoseControlTests.test_arrival_requires_final_reference_and_121_inclusive_samples PoseControlTests.test_timeout_at_960_unless_full_success_window PoseControlTests.test_guard_failure_latches_and_success_cannot_overwrite_it PoseControlTests.test_clock_and_nonfinite_post_state_failure_preserves_sample PoseControlTests.test_recorder_internal_failure_survives_completed_work_and_recording_errors PoseControlTests.test_pose_csv_preserves_named_values_and_partial_failing_step
& 'D:\miniconda3\Scripts\conda.exe' run -p 'C:\isaacenvs\isaac45_harl' python source/isaaclab_tasks/test/test_cr12_manual_visual.py ManualEntryBoundaryTests
```

早期 CPU 整合还校正了失败 tick 计数归属、保存/关闭失败的独立结果、metadata 字段和监督判定；均在相应 App 前完成检查，没有运行中热改。未运行全仓、Phase B、旧 visual/sweep 完整矩阵或训练测试。

### 7.2 两次实际 App 的完整外层命令

以下为本轮已执行命令，cwd=`E:\Project\IsaacLab_HARL`。第一次命令对应原修复前代码，不能把它改说成修复后通过。

```powershell
& 'D:\miniconda3\Scripts\conda.exe' run --no-capture-output -p 'C:\isaacenvs\isaac45_harl' python -X utf8 -u 'logs/scan_assignment/20261007_cr12_single_view_capture/repro/supervise_cr12_single_view_capture.py' --attempt-dir 'E:\Project\IsaacLab_HARL\logs\scan_assignment\20261007_cr12_single_view_capture\attempt_01'

& 'D:\miniconda3\Scripts\conda.exe' run --no-capture-output -p 'C:\isaacenvs\isaac45_harl' python -X utf8 -u 'logs/scan_assignment/20261007_cr12_single_view_capture/repro/supervise_cr12_single_view_capture.py' --attempt-dir 'E:\Project\IsaacLab_HARL\logs\scan_assignment\20261007_cr12_single_view_capture\attempt_02' --repair-kind snapshot_copy --repair-reason 'Publish authorized initial zero native state to Fabric once while capture stays OFF; assert native arrays and clocks unchanged before original camera mount tolerance check'
```

监督器为目标 Python 在启动前合并父环境与 `PYTHONUTF8=1, HEADLESS=0, ENABLE_CAMERAS=1, LIVESTREAM=0, XR=0`。App02 实际子命令如下；App01 仅输出/private 路径为 attempt_01。此子命令用于说明真实启动链，人工复现应使用下面带监督的命令。

```powershell
D:\miniconda3\Scripts\conda.exe run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/run_cr12_single_view_capture.py --usd-path E:\Project\IsaacLab_HARL\source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\assets\rokeaCR12\derived\fixed_lift0_v1\usd\cr12_fixed_lift0.usd --output-dir E:\Project\IsaacLab_HARL\logs\scan_assignment\20261007_cr12_single_view_capture\attempt_02 --device cuda:0 --external-forces-every-iteration on --enable_cameras --info --kit_args=--/app/userConfigPath=E:/Project/IsaacLab_HARL/logs/scan_assignment/20261007_cr12_single_view_capture/attempt_02/private_config/user.config.json
```

已接受 Windows helper 在 AppLauncher 前追加缺省 `--/app/vulkan=false`；最终 Kit argv/实际 backend 都有同次证据。不是只凭命令写了 false 就认为 D3D12 生效。

### 7.3 用户可选的单次有界复现命令（本轮未执行）

可以直接查看第 5 节已取得的 PNG，无需再开 App。若用户希望自行再看同一个小目标/采集闭环，在 PowerShell 执行以下一组命令；每次自动新建输出目录和 fresh private，最大 1800 受控步，App≤180秒/全树≤360秒，不保持窗口无限等待，也不覆盖 attempt_01/02。

```powershell
Set-Location -LiteralPath 'E:\Project\IsaacLab_HARL'
$cr12CaptureDir = Join-Path 'E:\Project\IsaacLab_HARL\logs\scan_assignment\20261007_cr12_single_view_capture' ('manual_' + (Get-Date -Format 'yyyyMMdd_HHmmss_fff'))
& 'D:\miniconda3\Scripts\conda.exe' run --no-capture-output -p 'C:\isaacenvs\isaac45_harl' python -X utf8 -u 'logs/scan_assignment/20261007_cr12_single_view_capture/repro/supervise_cr12_single_view_capture.py' --manual-check --attempt-dir $cr12CaptureDir
```

这条命令使用同一实现、相机配置和监督约束；manual-check 只标记用户显式的一次运行，不是 agent 自动新增 App 的授权。监督会校验当前七个直接代码输入和已有 CPU preflight，代码变化后应先复核/更新相应检查，不能禁用校验继续运行。唯一输出目录已存在时拒绝，不删除或覆盖旧结果。

## 8. 复用接口、未验证项与停止边界

本轮独立入口提交且只提交 `formal_goal_1`。单请求状态机和采集后端不内置两个视点序列：`SingleViewRequest.start_motion/observe_tick/capture_starting/accept_frame/request_close/observe_close` 由 scene 主循环逐步驱动；`OwnedCameraCapture.prepare/initialize_off/begin_capture/poll_snapshot/request_off/observe_close/release` 负责一个专属产品。模块每 tick 有限工作，不拥有 physics 时钟、不另开长阻塞采集循环。

未来接第二视点必须由外层顺序驱动器在上一请求数据结果与 OFF 已确认后，从实际结束状态提交下一目标。本轮尚未证明同 Camera/product 的第二次启停、跨请求基线重置或多机共同步进，不自动承诺现有对象无修改即可循环复用。保持反馈与后续碰撞运动参考仍必须使用实际下发/跟踪参考；不以实现通用规划器作为本轮完成前提。

后续 MRTA 边界仍为 effective assignment → 单视点执行 → feedback → 现有生命周期 authority；当前模块不改 owner/completed，不复制 claim/release/reassign，也不把普通采集失败自动定义为永久 failed-pair。

待后续明确授权的能力：双视点连续状态传递及重复请求；真实构件/路径的碰撞安全；需要时的 depth/pointcloud；真实安装和光学参数/设备接口。非零在途、实际异常/取消/保存失败的 runtime 分支本轮未注入，当前只有针对性 CPU 证据；headless/Linux/其他资产未代验。没有图像质量任务、训练、checkpoint、历史重建或清理。

**本轮已完成实现与有限真实闭环验证，停止并等待 GPT/用户审阅。** 没有需用户补充才能解释本次结果的阻断问题；下一阶段方向和新运行授权不由本次 PASS 自动产生。

## 9. 操作及文档交付

实际操作包括：读取适用 AGENTS、当前交接/主题导航和用户指定的三份必要前置；定向本地 Camera/Replicator/Hydra/SyntheticData/Fabric 源码核对；scanner 必要 bounds/挂载解析；实现及 CPU 检查；两次受监督 GUI/CUDA/physics/render/camera App；读取同次日志/JSON/PNG；小范围文档更新及新增链接核对。没有全资产重新审计、全仓哈希/历史链接审计或外部设备操作。

运行末次验证 v1 七个派生文件和所读源 scanner OBJ 共八项内容不变；真实 source 配置不变。没有改机器人质量/惯量/collider/PD/effort/solver/dt/重力，未改 installed packages、驱动、持久环境变量或共享配置；没有 Git add/commit/push/reset/checkout 等写操作。既有暂存的历史 ZIP 删除保持原状，不归因于本轮。

文档只新增本文，小范围更新 TASK_PROGRESS 最新状态、资产边界与报告入口，以及 REPORT_INDEX 扫描主题；历史报告不改写，没有大幅压缩重写，故未制造全量交接备份。生产 Python 在 E、可复用测试在 Q、监督/证据在 L；**AgentRead 本轮仅新增 Markdown 主报告**。

`logs/` 受现有忽略规则影响：PNG、JSON、console/Kit、副本和 repro 当前仅在本机工作区可取，并非新 checkout 自动拥有。报告直接相对引用原始 PNG，不复制成额外展示版，不生成完整 ZIP。外部转交如有需要，另行提供与审阅有关的最小材料。

### 辅助证据对应表

| 结论/检查项 | 文件位置 | 关键字段/定位 | 用途及限制 |
|---|---|---|---|
| App02 分层完成与全树退出 | [supervisor_result.json](../../../../../../../../logs/scan_assignment/20261007_cr12_single_view_capture/attempt_02/supervisor_result.json) | runtime/process pass、stage_events、双 exit0、预算2/3、elapsed_seconds=35.203 | 完成记录与自然退出联合依据 |
| native、pose、mount、OFF/阶段 | [result.json](../../../../../../../../logs/scan_assignment/20261007_cr12_single_view_capture/attempt_02/result.json) | initial_fabric_publication、camera_mount_checks、arrival、stage_counts、off_confirmation、camera_release | 同次实际值；status 工作完成字段不单独代表进程已退出 |
| 原始数据与时间语义 | [camera_rgba.png](../../../../../../../../logs/scan_assignment/20261007_cr12_single_view_capture/attempt_02/camera_rgba.png)、[capture_metadata.json](../../../../../../../../logs/scan_assignment/20261007_cr12_single_view_capture/attempt_02/capture_metadata.json) | frame558、source557/30→558/30、rendering_time、receive pose、artifact | 数据不是 viewport；无精确曝光 pose 声明 |
| 实际启动/后端/警告 | [command.json](../../../../../../../../logs/scan_assignment/20261007_cr12_single_view_capture/attempt_02/command.json)、[console.log](../../../../../../../../logs/scan_assignment/20261007_cr12_single_view_capture/attempt_02/console.log)、[Kit 副本](../../../../../../../../logs/scan_assignment/20261007_cr12_single_view_capture/attempt_02/kit_20261007_112306.log) | Kit:5/6/2688/3340/3632/6963–7001 | 原生 Kit 本机源路径在 result.app；副本保留同次实际记录 |
| 配置隔离 | [config_runtime_summary.json](../../../../../../../../logs/scan_assignment/20261007_cr12_single_view_capture/attempt_02/config_runtime_summary.json) | source_unchanged=true、private_semantic_diff_count=1 | 区分 source 未改与 private 正常写回，不附完整配置 |
| 首 App 失败保留 | [App01 result](../../../../../../../../logs/scan_assignment/20261007_cr12_single_view_capture/attempt_01/result.json)、[App01 supervisor](../../../../../../../../logs/scan_assignment/20261007_cr12_single_view_capture/attempt_01/supervisor_result.json) | physics_initialize ValueError、0受控、双exit0但FAIL | 旧失败原样，不能由 App02 覆盖 |
| 旧默认抽取保护 | [pose_generator_extraction.patch](../../../../../../../../logs/scan_assignment/20261007_cr12_single_view_capture/repro/pose_generator_extraction.patch)、[AST/CPU 摘要](../../../../../../../../logs/scan_assignment/20261007_cr12_single_view_capture/repro/pose_default_ast_equivalence.json) | default_path_ast_equal、8+4 CPU | 不宣称旧入口新 runtime 资格 |
| 初始化局部修复 | [initial_fabric_publication_repair.patch](../../../../../../../../logs/scan_assignment/20261007_cr12_single_view_capture/repro/initial_fabric_publication_repair.patch)、[监督修复差异](../../../../../../../../logs/scan_assignment/20261007_cr12_single_view_capture/repro/initial_snapshot_supervision_repair.patch) | 原失败代码哈希核对、单次 forward、窄历史归类 | 不改原失败 JSON，不普遍放行 ValueError |
| 本轮监督与准备 | [supervise_cr12_single_view_capture.py](../../../../../../../../logs/scan_assignment/20261007_cr12_single_view_capture/repro/supervise_cr12_single_view_capture.py)、[preflight.json](../../../../../../../../logs/scan_assignment/20261007_cr12_single_view_capture/repro/preflight.json) | 单次 App、完整预算、fresh private、camera/env转发、七个直接输入 | 一次性运行证据工具；生产代码不依赖该目录 |
| 当前交接入口 | [TASK_PROGRESS.md](../../TASK_PROGRESS.md)、[REPORT_INDEX.md](../../REPORT_INDEX.md) | 最新扫描采集状态与停止边界 | 历史结论保留，本次等待审阅 |
