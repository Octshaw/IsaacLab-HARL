# CR12 单目标 scanner pose：实现、有限真实验证与人工查看交接

日期：2026-09-30（Asia/Shanghai）。结论：**正式单目标数值验证 PASS；等待 GPT/用户审阅和人工可视化反馈。**

## 1. 执行摘要

在当前 **fixed-base / lift0 / v1、baseline PD、external-forces-every-iteration=on、dt=1/120、TGS 8/2、GUI/D3D12/cuda:0** 固定构型下，CR12通过实际六轴关节执行器，完成了预定单目标scanner完整pose的有限闭环到位验证。

只运行 **attempt_01、1个App**，无运行失败、无修复重试。首次Jacobian校核唯一匹配 **COM**；按审阅公式转换到link_6原点和实际root系后执行。第 **600** 个受控步、`5.000000260770321 s` 发出 `POSE_REACHED`：最终位置误差 **0.069558789 mm**、姿态误差 **0.004687157°**。第480–600步含两端 **121个连续样本** 满足原2mm/0.25°/0.01rad/s判据，跨度 `1.0000000521540642 s`。上限仍为960步/8秒，成功后提前正常结束，没有将600步改成新预算。

全部600步的clock、joint、contact、actual geometry、root/frame、render clock检查通过；1200次提交前中点/终点碰撞sanity检查通过。App构造24.343秒，所属进程树总计63.484秒；目标Python和Conda均自然exit0，未超时、未强制终止，全部所属进程已退出。

这不是全工作空间IK、任意视点可达、通用避障、构件避障、扫描完成、相机接入、实体机器人或visual资产验收。**POSE_REACHED != SCAN_COMPLETE**。基本joint drive既有GPT REVIEW PASS保持；Phase B保持COMPLETE / GPT REVIEW PASS / CLOSED。本轮未重跑旧5° joint_2/720步验收。

## 2. 实际文件变化与旧入口等价性

| 文件（相对仓库） | 实际变化/关键定位 |
|---|---|
| [scripts/environments/_cr12_runtime_support.py](../../../../../../../../scripts/environments/_cr12_runtime_support.py) | 新增共享支持；Recorder:39、状态/guard工具；create_fixed_cr12_scene:430、initialize_fixed_cr12_state:565 |
| [scripts/environments/run_cr12_joint_drive.py](../../../../../../../../scripts/environments/run_cr12_joint_drive.py) | 仅机械抽取和共享调用替换，旧轨迹、旧诊断、旧720步成功条件保留 |
| [scripts/environments/_cr12_pose_control.py](../../../../../../../../scripts/environments/_cr12_pose_control.py) | 新增纯CPU坐标/FK/校核/准入；FrozenPoseTarget:154、resolve_mapping:189、select_jacobian_adapter:207、adapt_jacobian:224、KinematicModel:237、CommandIntegrator:317、PoseMonitor:393 |
| [scripts/environments/run_cr12_pose_target.py](../../../../../../../../scripts/environments/run_cr12_pose_target.py) | 新增正式入口；parse_args:28、PoseTrace:60、native state/J快照98/113行；_run_pose:169、main:408 |
| [scripts/environments/_cr12_pose_visuals.py](../../../../../../../../scripts/environments/_cr12_pose_visuals.py) | 新增懒加载显示辅助层；set_spectator_view:76、PoseDebugVisuals:96；不创建扫描相机或推进物理 |
| [source/isaaclab_tasks/test/test_cr12_pose_control.py](../../../../../../../../source/isaaclab_tasks/test/test_cr12_pose_control.py) | 新增31项针对性CPU测试 |
| `logs/scan_assignment/20260930_cr12_pose_target/repro/supervise_cr12_pose.py` | 本任务一次性监督器，复用既有Windows Job/实时排空/同次Kit日志方法；正式入口不依赖此目录 |
| 文档 | 新增本报告，小范围更新TASK_PROGRESS、REPORT_INDEX；旧设计/历史报告保留 |

共享抽取以本轮开始时旧driver原文作AST对照：**21个迁移定义、8个保留定义内容相同**；将两个共享函数展开回旧`_run_drive`后，原122条执行语句顺序/AST等价。唯一白名单差异是记录字符串callsite改成真实`create_fixed_cr12_scene`名称。旧StateConsistencyTrace插入位置仍位于场景构造与一次初始化之间。未把pose逻辑塞入共享层，未复制整份driver。

`rokea_cr12.py`、Windows/helper、pre-App CUDA、external-force helper、PD/solver/惯量/资产未修改。仅对本次v1目录7个文件作运行前后只读摘要比较，**7/7内容一致**；未做全仓库哈希库存、资产导入或重新导出。

## 3. 实际frame和Jacobian校核

约定 `T_AB = B frame在A frame中的位姿`，列向量、米、WXYZ。W为world；R为实际agv actor/link；E为link_6 actor/link；S为其下scanner纯Xform，+X forward/+Z up。本轮没有camera optical frame。

实际body names：`agv, link_1, link_2, link_3, link_4, link_5, link_6`；joint names：`joint_1…joint_6`。tool/scanner不属于刚体列表。`T_Etool=I`；`T_ES` 零平移、`Rz(+135°)`，WXYZ为
`(0.3826834323650898,0,0,0.9238795325112867)`。入口从场景读取固定frame并校核，不独立移动scanner。

~~~text
T_WE_target = T_WS_target · inverse(T_ES)
T_RE_target = inverse(T_WR) · T_WE_target
T_WS_actual = T_WE_actual · T_ES
~~~

实际末端姿态来自`body_link_pos_w/body_link_quat_w`，验收不用q_cmd FK、reference或USD authored world pose；q/dq使用native PhysX getter的独立clone。

| 运动前实际读回 | 结果 |
|---|---|
| fixed base、实例/刚体/轴数 | true；1 / 7 / 6 |
| E body index / Jacobian row | link_6=6；fixed-base row=5 |
| 六轴列索引 | 按joint_1…6解析为[0,1,2,3,4,5]，无root DOF |
| native J | **(1,6,6,6)、torch.float32、cuda:0**；E切片(1,6,6)，立即clone |
| actor候选最大误差 | linear **0.11853274297714211 m/rad**；angular **2.980232238769531e−7** |
| COM候选最大误差 | linear **4.315905810514664e−7 m/rad**；angular **2.980232238769531e−7** |
| 预定义容差 | linear 1e−4 m/rad、angular 1e−4；**只有COM匹配** |
| 校核前/后clock | 同为step=2、time=0.01666666753590107s |
| 额外刷新/物理步 | 0；没有为了更新J偷偷step |

解析模型从当前派生URDF读取六轴安装/轴向，用本次实际q/root建立几何J_E/J_C；实际link poses同次读回并参与frame和末端控制。初态rank3未被误判为故障。整个运行冻结adapter为`com`：

~~~text
r_W = R_WE · c_E
Jv_E_W = Jv_C_W + skew(r_W) · Jw_W
J_E_R = diag(R_RW, R_RW) · J_E_W
~~~

linear/angular顺序为[vx,vy,vz,wx,wy,wz]；两块都旋转到实际R系，没有再次应用scanner的135°安装旋转。此参考点结论限当前安装版本和当前模型，不推广所有native后端。

## 4. 实际冻结目标与执行链

目标只由本次初始化实测S构造一次：
`delta_p_W=(+0.0106981457149994,0,−0.000155046722254002) m`；
`R_target=Ry_world(+1°) R_WS0`（世界Y左乘）。

| pose | position，m | quaternion，WXYZ |
|---|---|---|
| 本次实测T_WS0 | (0.104999989271164, −0.149999842047691, 2.887999057769775) | (0.382683440451755, 2.903724264e−8, 6.713141502e−9, 0.923879529161680) |
| 冻结T_WS_target | (0.115698134986163, −0.149999842047691, 2.887844011047521) | (0.382668868980368, 0.008062296543587, 0.003339507340628, 0.923844350406740) |
| 最终实测T_WS_actual | (0.115679316222668, −0.150004059076309, 2.887910842895508) | (0.382643873362153, 0.008034825557049, 0.003326075881031, 0.923854991314065) |

初始实际R位置`(4.656613e−9,5.820766e−11,0.05300015211105347)`，WXYZ约`(1,−1.030614e−10,1.036531e−9,6.352974e−12)`。目标转换使用实际R，不将根朝向写死为identity。

实际controller为本地`DifferentialIKControllerCfg(command_type="pose",use_relative_mode=False,ik_method="dls",ik_params={"lambda_val":0.01})`，N=1、cuda:0、完整6D误差，姿态为最短轴角。

参考轨迹4秒：`u=min(t/4,1)`、`h=10u³−15u⁴+6u⁵`，位置按h平移，姿态`Ry_world(h×1°)R_WS0`，等价于本目标最短测地线。没有使用小角直接跳到目标的helper。每tick读取t_k实际状态，计算t_(k+1)参考，提交后仅step一次，在相同t_(k+1)评价。

~~~text
delta_q_ik = q_IK − q_actual
q_proposal = q_cmd_previous + (dt × 2.0) · delta_q_ik
dq_cmd = (真正提交的float32 q_proposal − 上次提交值) / dt
~~~

全部准入通过后，成对set target、`write_data_to_sim`，精确核对提交buffer后才commit积分状态。速度也转换为float32实际提交。未逐tick重置积分状态、直接下发raw q_IK、增加力矩/重力补偿或改PD。

已审限制全部保持：硬限位margin .02rad、raw delta .035rad、command/actual差 .035rad、命令步差 .00125rad、命令速度 .15rad/s、5°信任范围、实际速度 .25rad/s、actuator速度 .2rad/s。无clamp、目标变更或在线调参。

## 5. 实际命令、环境和过程预算

工作目录`E:\Project\IsaacLab_HARL`；解释器`C:\isaacenvs\isaac45_harl\python.exe`，UTF8 mode=1；HEAD `24ecbad7dd1bdcd006399b64bfb757a86b71aeec`，保留已有dirty worktree及既有暂存删除。
experience为`E:\Project\IsaacLab_HARL\apps\isaaclab.python.kit`。
同次Kit日志实际Graphics API=**D3D12/DX12**；GPU管线/TGS/cuda:0读回通过，不另做Windows或CUDA基准试验。

实际外层命令：

~~~powershell
Set-Location 'E:\Project\IsaacLab_HARL'
& 'D:\miniconda3\Scripts\conda.exe' run -p 'C:\isaacenvs\isaac45_harl' python -u logs/scan_assignment/20260930_cr12_pose_target/repro/supervise_cr12_pose.py --attempt-dir logs/scan_assignment/20260930_cr12_pose_target/attempt_01
~~~

监督器实际子命令如下；合并子进程环境`PYTHONUTF8=1`、`HEADLESS/ENABLE_CAMERAS/LIVESTREAM/XR=0`，未写持久设置：

~~~powershell
& 'D:\miniconda3\Scripts\conda.exe' run --no-capture-output -p 'C:\isaacenvs\isaac45_harl' python -u scripts/environments/run_cr12_pose_target.py --usd-path 'E:\Project\IsaacLab_HARL\source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\assets\rokeaCR12\derived\fixed_lift0_v1\usd\cr12_fixed_lift0.usd' --output-dir 'E:\Project\IsaacLab_HARL\logs\scan_assignment\20260930_cr12_pose_target\attempt_01' --device cuda:0 --physics_steps 960 --external-forces-every-iteration on --info
~~~

baseline是入口唯一允许的PD profile；正式运行`visual_debug_pose=false`、view=overall，spectator设置成功，visual_errors=[]。使用已接受Windows helper和pre-App CUDA准备，保留原顺序。

| 过程 | 实际记录 |
|---|---|
| 本地开始/结束 | 2026-09-30 16:11:52.233 → 16:12:55.715，+08:00 |
| App构造/全树上限 | 180s / 360s（350s预留清理）；实际24.343s / 63.484s |
| 初始化 | reset一次隐含2物理步、0.016666667536s；一次joint state初始化；root state写入0次 |
| 受控阶段 | 600步、5.000000260770321s；初始化2步不计入960 |
| 受控render | 300次；render_interval=2，render未推进物理 |
| 外力读回 | before为false/unauthed；after_apply、after_first_reset、before_motion、before_exit均true且matches_expected |
| 设置证据边界 | composed USD/schema session读回及调用时序，不伪称直接读取native solver内部flag |
| 进程 | 目标PID7468、Conda PID6060；exit均0；全部owned descendants退出，无超时/强制终止 |
| 正式结果 | entry POSE_REACHED、无内部/次级失败；supervisor validation_pass=true、process_exit_pass=true |

App关闭前entry状态仍为`WORK_COMPLETED_PENDING_NATURAL_EXIT`，原始文件不回改；随后监督器取得的实际退出结果与其合并才形成正式PASS。未记录`app_close_returned`，因此只确认**所属进程自然退出**，不声称Python的`app.close()`已返回。

## 6. 误差趋势、关节运动和稳定窗口

下表误差均为实际scanner相对**冻结最终目标**；每步reference误差另存CSV，供发散判据使用。

| step | 受控时间，s | 位置误差，mm | 姿态误差，° | max实际abs(dq)，rad/s |
|---:|---:|---:|---:|---:|
| 1 | 0.008333334 | 10.688783 | 0.987651 | 0.033820711 |
| 120 | 1.000000052 | 9.872580 | 0.917733 | 0.000318245 |
| 240 | 2.000000104 | 7.229657 | 0.678488 | 0.003051474 |
| 360 | 3.000000156 | 2.826163 | 0.270366 | 0.004787351 |
| 480 | 4.000000209 | 0.413939 | 0.042224 | 0.004341098 |
| 600 | 5.000000261 | 0.069559 | 0.004687 | 0.003844582 |

第480–600步稳定窗口的位置误差最大 **0.413939mm**、姿态误差最大 **0.042223849°**、六轴速度最大 **0.004366657rad/s**。121/121全部符合既定阈值，实际跨度1.000000052s。未将reference在4秒结束当成功，也未用“已经很接近”替代完整稳定窗口。

| joint | 实际角度范围，°（含初态） | 全程max abs(dq)，rad/s |
|---|---:|---:|
| 1 | −0.032134 ～ +0.017389 | 0.006303389 |
| 2 | −0.005350 ～ +0.119774 | 0.005158069 |
| 3 | 0 ～ +0.885354 | 0.012359147 |
| 4 | −0.031194 ～ +0.149669 | 0.009351360 |
| 5 | 0 ～ +0.246730 | 0.036258463 |
| 6 | −0.118177 ～ +0.024983 | 0.023519406 |

实际多关节分配不同于离线FK见证构型是允许的；成功依据真实scanner pose，不要求复现预设q。

最大raw DLS update **0.002345477rad**（上限.035），最大相邻提交位置变化 **3.909133375e−5rad**（上限.00125），最大提交速度 **0.004690960rad/s**（上限.15）。CSV事后核对的最大“提交命令−post-step实际q”差为0.002577045rad；该值不是提交前读数，提交前差准入由入口实际执行通过。

最终实际提交：

~~~text
q_cmd rad =
(-0.000651566777, -0.001194335637, 0.012875299901,
  0.002539722249, -0.000284127134, -0.001809876529)

dq_cmd rad/s =
( 0.000132315326, -0.001655817032, 0.003784149885,
  0.000761272386, -0.002002530964, -0.001001455821)
~~~

600次提交buffer核对全部通过；CSV离线再计算float32位置命令差分速度，600/600与实际提交dq_cmd精确一致。无运行期机器人状态写回或scanner独立移动。最终误差数值不构成实体/工业精度承诺。

## 7. 碰撞、异常、失败与重试边界

| 检查/事件 | 实际结果 |
|---|---|
| clock、joint、contact、geometry、frame、render_clock | 各600/600 PASS，CSV每行对应guard均PASS |
| contact传感器 | 7个body各600次更新，原禁止pair过滤保持；禁止接触最大力0N |
| actual-state AABB | 600次PASS；臂最低collision enclosure z=1.239998764m |
| root/frame | root最大漂移0m/0rad；各固定frame最终误差0，全程frame守卫600次通过 |
| pre-command collision sanity guard | actual q→本次q_proposal的midpoint/endpoint共1200次通过 |
| NaN/Inf、硬限位、命令拒绝 | 未出现 |
| DIVERGENCE / NO_PROGRESS / TIMEOUT | 均未出现；没有换目标、放宽阈值或增加预算 |
| App/修复重试 | 主运行1次、修复0次；第2次App未使用 |
| native/CUDA故障 | 同次console/Kit定向检索未发现；未替换环境/驱动 |

pre-command guard只是两个采样点的碰撞sanity检查，不是连续轨迹碰撞证明或完整collision-free planning。实际状态仍逐步检查几何/contact；本轮无构件，不能宣称构件避障。

运行前集成审查修正了字段名匹配、失败步CSV保留首次异常、App关闭前记录失败仍尝试关闭、visual异常独立记录、监督器不能让exit0/缺证据覆盖内部FAIL等局部问题。全部在首次App前完成；没有失败运行被抹掉，运行后也没有修改控制代码来改变原日志结论。

## 8. CPU、静态及运行后核对

指定Conda解释器上完成：

- 7个新增/修改Python文件`py_compile`通过（正式6个源码/测试文件和一次性监督器）。
- **31/31**控制CPU测试通过，最终门槛运行2.216s。覆盖安装变换、非identity root、q/−q、世界Y左乘、1°小角轨迹、名称乱序、COM符号/唯一匹配、finite、限位/margin/步幅、float32差分速度、拒绝不累计、121样本、no-progress/timeout、两点碰撞sanity、内部失败不可覆盖和失败步CSV。
- 共享抽取AST等价、stdlib-only导入、**6/6**针对性guard/Recorder/旧纯逻辑回归通过；未重跑旧仿真或资产套件。
- 监督器**11项**纯CPU完成条件检查通过：内部失败、缺字段、CSV/guard缺步、缺关闭/on读回、时间不一致及native故障不能PASS。
- visual helper CPU数学/AST检查通过：轴与连线端点、预设、输入不变、无step/render/状态写入；marker运行路径未测。
- 运行后只读核对600行CSV步序、guard、位置/四元数误差、量化命令差分和最后121样本；与result一致。v1七文件内容未变，既有Git index状态未变。

合成CPU测试只证明逻辑；实际pose PASS来自唯一真实GUI/CUDA/PhysX运行及真实退出证据。未运行全仓pytest、Phase B或旧checkpoint操作。

## 9. 用户人工可视化命令

以下为**用户手动命令，Codex本轮未执行**。同一入口、v1、baseline、explicit on、正式10.7mm+1°目标与最多8秒/960步，只开启debug marker/wrist视角。创建带时间戳的新manual目录，不覆盖attempt_01。环境变量仅作用当前PowerShell及其子进程，不写持久配置。

~~~powershell
Set-Location 'E:\Project\IsaacLab_HARL'
$env:PYTHONUTF8 = '1'
$env:HEADLESS = '0'
$env:ENABLE_CAMERAS = '0'
$env:LIVESTREAM = '0'
$env:XR = '0'
$cr12ManualDay = Get-Date -Format 'yyyyMMdd'
$cr12ManualStamp = Get-Date -Format 'yyyyMMdd_HHmmss_fff'
$cr12ManualRelative = 'logs/scan_assignment/' + $cr12ManualDay + '_cr12_pose_target/manual_' + $cr12ManualStamp
$cr12ManualOutput = Join-Path (Get-Location) $cr12ManualRelative
& 'D:\miniconda3\Scripts\conda.exe' run --no-capture-output -p 'C:\isaacenvs\isaac45_harl' python -u scripts/environments/run_cr12_pose_target.py --usd-path 'E:\Project\IsaacLab_HARL\source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\assets\rokeaCR12\derived\fixed_lift0_v1\usd\cr12_fixed_lift0.usd' --output-dir $cr12ManualOutput --device cuda:0 --physics_steps 960 --pd-profile baseline --external-forces-every-iteration on --visual-debug-pose --view-preset wrist --info
~~~

整体视角仅将`--view-preset wrist`改成`overall`，不要改目标/参数。直接人工命令不经过本轮自动监督器，因此不生成supervisor_result或复制Kit日志；入口仍有960步/8秒数值预算、正常关闭、result/CSV。自动试验的180/360秒Windows Job墙钟监督只覆盖正式attempt，不能声称该人工命令也具备外层监督。

图例：实际scanner为**较长较粗RGB三轴（12cm）**；冻结目标为**较短浅色RGB三轴（8cm）**；原点间黄色连线。按实际pose与固定target更新，不用虚构FK“已到位”。独立`/CR12PoseDebug`下marker不带RigidBody/Collision/Mass/Joint，不参与碰撞、不创建扫描相机，不改变dt/render_interval/步计数/成功条件，只用现有GUI perspective spectator。

正式运行marker关闭，overall spectator设置已实际成功；**marker显示路径只有源码/CPU检查，尚未运行确认**。显示异常单列visual_errors并停用显示，不更改数值判据；visual_errors非空时不能算显示正常。成功/失败后自动退出，不为了观察额外驻留step。

人工请看：

1. 实际scanner坐标架是否平滑向target移动，朝向是否沿规定世界Y方向变化。
2. 各link随动是否连续，有无突然跳关节、明显自穿插或穿地。
3. 接近目标后是否有明显持续抖动；长轴和连线仅辅助观察。
4. 幅度约10.7mm+1°，仍可能很难肉眼分辨，不扩大正式目标。更大manual-only动作需新授权。

人工观察只是sanity反馈，不能替代POSE_REACHED、contact和guard。本轮未替用户多开App，也未为截图补跑。

## 10. visual待办、结论边界和交接

**源OBJ由用户确认正常；仿真显示几何存在差异，原因待查。** 既有“封闭/填充观感”未调查/修复，不能归因本轮pose controller或均匀盒惯量。显示marker不改变机器人visual/collision资产，也不构成visual验收。在加入构件/相机和正式扫描视点前，仍须解决显示一致性事项。

本轮交付为已实现入口/辅助层、CPU验证、唯一真实pose结果、人工查看命令和本报告。结论严格限定当前构型与这一个小目标；相机、双视点、MRTA接入、训练、实体机器人均未实施。未修改Phase B、依赖/驱动/共享配置，未执行Git写操作或历史清理。

[TASK_PROGRESS](../../TASK_PROGRESS.md)和[REPORT_INDEX](../../REPORT_INDEX.md)同步基本驱动GPT REVIEW PASS、本轮pose数值PASS待审、visual debug人工反馈及未实施边界。下一步是审阅和按需人工观察，不自动进入调参、大幅动作、视觉修复、相机、双视点或MRTA。

## 11. 辅助证据对应表

证据主要在现有忽略规则下的`logs/`，目前是**本机文件**，不保证新checkout自动包含。未生成ZIP、重复日志包或全仓哈希清单。源码位置见第2节。

| 结论/检查项 | 文件 | 关键字段/定位 | 用途 |
|---|---|---|---|
| frame/J/目标/数值 | [result.json](../../../../../../../../logs/scan_assignment/20260930_cr12_pose_target/attempt_01/result.json) | jacobian_check、frozen_poses、pose_summary、initialization、external_forces_setup | 初次COM唯一匹配及实际完成；退出前状态需与监督合读 |
| 实际命令 | [command.json](../../../../../../../../logs/scan_assignment/20260930_cr12_pose_target/attempt_01/command.json) | cwd、argv、child_environment_overrides | 启动和环境来源 |
| 退出/后端 | [supervisor_result.json](../../../../../../../../logs/scan_assignment/20260930_cr12_pose_target/attempt_01/supervisor_result.json) | validation_pass、exit、owned退出、kit_log | 内部完成加自然退出；同次D3D12 |
| 连续采样 | [pose_joint_trace.csv](../../../../../../../../logs/scan_assignment/20260930_cr12_pose_target/attempt_01/pose_joint_trace.csv) | step1…600，480…600稳定窗口 | actual/ref/target、q/dq、提交命令、每步guard |
| 同次原始日志 | [console.log](../../../../../../../../logs/scan_assignment/20260930_cr12_pose_target/attempt_01/console.log)、[Kit日志](../../../../../../../../logs/scan_assignment/20260930_cr12_pose_target/attempt_01/kit_20260930_161156.log) | RUNTIME_CHECK；Graphics API（Kit2682/3572行） | 同次启动/事件；Kit08:xx对应本地16:xx |
| 监督/代码差异 | [supervise_cr12_pose.py](../../../../../../../../logs/scan_assignment/20260930_cr12_pose_target/repro/supervise_cr12_pose.py)、[本轮源码patch](../../../../../../../../logs/scan_assignment/20260930_cr12_pose_target/repro/shared_extraction.patch) | owned Job、180/360秒、完成/重试限制；共享抽取及新增pose代码 | 复现/审查；正式入口不依赖logs |
| 已审设计 | [单目标实施方案](CR12_SINGLE_TARGET_POSE_EXECUTION_PLAN.md) | 固定目标/参数/判据 | 历史设计保留，本轮依其实施 |

**本轮实现与有限真实验证已完成，正式数值PASS；等待GPT/用户审阅及人工可视化反馈。停止，不自动进入下一阶段。**

