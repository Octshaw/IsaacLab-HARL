# CR12 派生资产生成与基本关节驱动实施报告

执行日期：2026-09-29，Asia/Shanghai（UTC+08:00）。状态：**实施已完成；派生资产检查通过；完整关节运动与保持验收未通过；等待 GPT/用户审阅。**

本文的 `T/` 指仓库内 `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/`；`E/` 指 `logs/scan_assignment/20260929_cr12_joint_drive/`。工作目录为 `E:\Project\IsaacLab_HARL`，HEAD 为 `24ecbad7dd1bdcd006399b64bfb757a86b71aeec`。这些缩写只用于正文定位，下面实际执行命令不依赖缩写。

## 1. 结论与授权边界

用户已审阅并批准[参数与基本驱动计划](CR12_DERIVED_ASSET_AND_JOINT_DRIVE_PLAN.md)，本轮实际生成独立派生 URDF/USD，实现独立 GUI 关节入口，执行一次 USD 导入和两次驱动进程。旧计划中的“待授权”保留为当时记录，本轮采用用户最新授权。

| 层次 | 实际结果 | 结论边界 |
|---|---|---|
| CPU 实现与资产生成 | 最终 14/14 针对性测试通过；新文件语法检查通过；派生 URDF 检查通过 | 不等于运行驱动通过 |
| USD 导入、保存与读回 | attempt_01 通过；7 刚体、6 活动关节、唯一固定根、10 个独立 convex hull 输入、无缺失依赖 | 原质量加均匀盒惯量是已批准的调试近似，不是厂家动力学真值 |
| 最终 PhysX 参数、初态与监测 | attempt_03 通过动作前检查；GPU pipeline/GPU dynamics/TGS、cuda:0 关节张量、名称映射、质量属性和驱动上限得到实际读回 | 固定底盘、升降 q0=0 的这一构型；没有升降主动控制 |
| 实际驱动 | attempt_03 执行 **600/720 步**，受控时间 **5.000000260770321 秒**；joint_2 最后为 **5.297537409°** | 是真实执行器运动；完整 6 秒验收 **FAIL** |
| 失败条件 | 在数学参考 t=5 秒，joint_5/6 的速度绝对值为 **0.023184916 / 0.025973620 rad/s**，超过末秒保持上限 **0.01 rad/s** | 未完成最后 1 秒，不报告运动与保持成功 |
| 进程退出 | 三次目标 Python/Conda 都自然 exit 0，全部所属进程退出，无超时/强制终止；三次实际 D3D12 | 内部失败记录优先；两次驱动不因 exit 0 改成通过 |

首次驱动在动作前因惯量读回发生重复主轴旋转而停止，已依据保存的原始矩阵及本地 API 说明修正，并用掉唯一一次驱动重试。第二次驱动的保持速度失败后，**没有再次调参或启动进程**。预算使用为 USD **1/2**、驱动 **2/2**、总 App **3/4**；总数未达 4 不允许突破驱动的 2 次上限。PD 调试与代码修复共享该次重试，因此本轮不再有 PD 复测额度。

Phase B 保持 **COMPLETE / GPT REVIEW PASS / CLOSED**。已接受 Windows 启动代码、原始 URDF/mesh、MRTA/lifecycle/学习代码、依赖和共享配置均未修改；未运行训练、checkpoint、旧 viewer 或历史验收，未执行 Git 写操作。本报告不自行赋予 GPT REVIEW PASS。

## 2. 实际实现与产物

| 新增文件 | 接口与用途 |
|---|---|
| `scripts/environments/prepare_cr12_fixed_asset.py` | `main:428` 分离 `--stage urdf/usd`；`_import_usd:335` App 后调用薄 converter；`inspect_usd_stage:54` 验证组合 USD；`_finish_imported_stage:227` 落实纯 frame、非实例化及逐源碰撞形状 |
| `scripts/environments/_cr12_asset_math.py` | CPU float64 均匀盒、旋转和平行轴合并；`generate_urdf:449` 独占输出、原文件保护；`validate_derived:438` 返回实际 XML 读回；`checked_physx_body_inertia:135` 明确最终惯量坐标解释；含轨迹及名称映射纯逻辑 |
| `source/isaaclab_assets/isaaclab_assets/robots/rokea_cr12.py` | `make_cr12_cfg:32`，显式 USD 路径、固定构型、六轴批准 PD/限制；不自动转换、不额外固定根、不覆盖质量 |
| `scripts/environments/run_cr12_joint_drive.py` | `_run_drive:447` 独立场景与有界序列；`_read_physics:205` 参数读回；`_calibrate_root_anchor:164` 初始化校准现有固定根；接触、实际状态与计数守卫；没有 Gym/RL/MRTA 封装 |
| `source/isaaclab_tasks/test/test_cr12_asset_math.py` | 直接运行的 CPU unittest；不通过任务包顶层导入 Isaac；原资产只读，生成类测试只使用临时 fixture |
| `E/repro/supervise_cr12.py` | 本任务一次性 Windows Job 监督器；实时排空输出、独立计时、所属进程退出和当次 Kit 后端证据；正式入口不依赖它或历史 AgentRead 脚本 |

未修改包导出或已有入口。启动顺序仍为参数解析 → 已接受 Windows helper → 窄复用 `view_scan_assignment._prepare_cuda_before_app` → AppLauncher → Isaac/机器人配置。没有调用 viewer.main，也没有导入依赖其全局 torch 的诊断函数。

最终资产版本为 `cr12_fixed_lift0_visual_box_v1`，实际路径：

```text
T/assets/rokeaCR12/derived/fixed_lift0_v1/
  cr12_fixed_lift0.urdf
  usd/cr12_fixed_lift0.usd
  usd/configuration/cr12_fixed_lift0_base.usd
  usd/configuration/cr12_fixed_lift0_physics.usd
  usd/configuration/cr12_fixed_lift0_sensor.usd
  usd/config.yaml
  usd/.asset_hash
```

后三个 configuration 层及 config/hash 为转换器生成的本次派生资源；`sensor.usd` 的名称不代表创建了扫描相机。机器人内实际未发现 Camera prim。原文件 `T/assets/rokeaCR12/rokea_cr12_7DOF.urdf` 和 `model/` 未覆盖、复制或恢复；已删除的旧 USD 未恢复。本轮没有第二个资产版本：重试仅修正参数读取，两个驱动均加载同一已检查资产，驱动期间没有保存或修改它。

派生 URDF 保留 20 条 `../../model/<原文件名>.obj` 引用，逐条相对于 URDF 所在目录解析；没有依赖当前工作目录。仅对原 URDF 与这 20 个引用 mesh 进行输入保护核对，最终 **21/21 未变**；没有全仓库库存/哈希审计。

## 3. 质量、装配、USD 与 PhysX 三层核验

### 3.1 参数落实

按原质量、visual 顶点的单次 `0.001` 缩放计算均匀实心盒：`c=(min+max)/2`，`I=(m/12)diag(dy²+dz²,dx²+dz²,dx²+dy²)`。原 10 个有质量 link 全部使用这一自洽 COM/惯量近似。collision 不另计质量，也未替换为质量盒。

基础组 `agv/elevate/base_link → agv` 的组内平移分别为 `(0,0,0)`、`(0,0,0.314)`、`(0.105,0,1.062)`；末端组 `link_6/tool/scanner → link_6` 的 scanner 安装为 `Rz(135°)`。先旋转/平移每个成员，再关于合并 COM 计算完整平行轴张量，保留交叉项。去掉无质量 world、内部 fixed joints、升降 DOF 和被合并物理子体；joint_1 重接 agv，origin 为 `(0.105,0,1.062)`。其余关节轴、几何和原位置/速度/effort 资料保留。

下表是派生 URDF 实际读回的 COM 与完整惯量，单位 m、kg·m²；六分量顺序为 **Ixx,Ixy,Ixz,Iyy,Iyz,Izz**，均关于该 COM、以保留 link 的坐标轴表达。

| 刚体 | COM | 完整惯量六分量（展示值） |
|---|---|---|
| agv | (0.009847510,0.000603783,0.610060757) | (11.110953937,-0.002458907,-0.196418282,12.797724006,-0.019800414,8.173585187) |
| link_1 | (-0.000008324,0.003624203,0.283859081) | (0.040731403,0,0,0.040002395,0,0.022845592) |
| link_2 | (-0.000023014,0.191745411,0.369056328) | (0.379516244,0,0,0.379773521,0,0.028452047) |
| link_3 | (-0.000072464,0.0215122375,0.064993309) | (0.021837733,0,0,0.020865714,0,0.010365227) |
| link_4 | (0.000037994,-0.009180899,-0.141903635) | (0.035520707,0,0,0.034323317,0,0.006663129) |
| link_5 | (-0.000008404,0.011287979,-0.0245845105) | (0.011912175,0,0,0.011024733,0,0.005939185) |
| link_6 | (0.060712673,0.060718218,0.118532826) | (0.097615839,-0.009122867,-0.016382307,0.097627014,-0.016366536,0.056319555) |

计算和写入使用 float64 原输入，没有把本表舍入小数当成精确输入。七体张量均满足正定及主惯量三角必要条件；这只是模型的数学一致性。

### 3.2 三层实际比较

USD 从保存、reload、重新打开的组合 stage 读取；由 diagonalInertia/principalAxes 重建完整 body-axis 张量。PhysX 列来自最终 attempt_03 执行器应用后的读回。误差列为与实际派生 URDF 的逐分量最大绝对差，比较包含完整 3×3 的交叉项。

| body | 质量 URDF / USD / PhysX，kg | COM 误差 USD / PhysX，m | 惯量误差 USD / PhysX，kg·m² |
|---|---|---|---|
| agv | 63.440749380 / 63.440750122 / 63.440750122 | 5.946159e-9 / 5.946159e-9 | 1.700943e-6 / 1.559712e-6 |
| link_1 | 3.440749380 / 3.440749407 / 3.440749407 | 6.884247e-9 / 6.884247e-9 | 1.035705e-9 / 1.706327e-9 |
| link_2 | 5.024380503 / 5.024380684 / 5.024380684 | 1.377003e-8 / 1.377003e-8 | 6.723429e-9 / 6.723429e-9 |
| link_3 | 2.439584706 / 2.439584732 / 2.439584732 | 2.005562e-9 / 2.005562e-9 | 5.038275e-10 / 5.038275e-10 |
| link_4 | 2.439584706 / 2.439584732 / 2.439584732 | 3.839722e-9 / 3.839722e-9 | 1.075186e-9 / 1.075186e-9 |
| link_5 | 2.422757896 / 2.422757864 / 2.422757864 | 7.949610e-10 / 7.949610e-10 | 2.674232e-10 / 2.674232e-10 |
| link_6 | 3.652558753 / 3.652558804 / 3.652558804 | 2.509302e-9 / 2.509302e-9 | 1.889061e-8 / 3.588607e-8 |

总质量：URDF **82.860365324 kg**，USD/PhysX 均为 **82.8603663444519 kg**。全部满足质量 `rtol=1e-5, atol=1e-6`、COM `atol=1e-5 m`、惯量 `rtol=1e-4, atol=1e-6`；组合容差并非只看绝对底线。未修改期望值或放宽容差。

### 3.3 导入结构、碰撞和引用

本地 UrdfConverter 调用 `super()._get_urdf_import_config()` 后显式设置 `set_import_inertia_tensor(True)`、`set_up_vector(0,0,1)`；其余为批准的 fix_base=True、root_link_name=agv、merge_fixed_joints=False、density=0、distance_scale=1、collision_from_visuals=False、convex_hull、self_collision=True、force position drive。无质量回退或 runtime 质量覆盖。

实际 USD 默认根为 `/cr12_fixed_lift0_visual_box_v1`；七体为其直接子节点 `agv,link_1…link_6`，六关节位于 `joints/joint_1…joint_6`。**唯一 FixedJoint 和 ArticulationRootAPI 均在 `root_joint`**，世界侧 body0 为空，body1 绑定 agv。加载到场景后前缀为 `/World/CR12`。PhysX 的 body/joint 顺序这次恰为批准顺序、映射索引分别 0…6/0…5，但代码按名称建立映射，没有假定数组顺序。

本地 importer 2.3.10 实际生成了 14 个 instanceable visual/collision 引用以及 7 个 MeshMergeCollision 容器。安装包 `docs/CHANGELOG.md:8,121,127` 和 PhysxSchema `schema.usda:1198` 可解释此行为：多个源 mesh 会作为一个合并凸包。准备入口只在新派生 root layer 中去实例化，解除这 7 个合并碰撞 API，并给 **10 份原 collision Mesh** 各自启用 convexHull；几何点、安装变换和质量未改。这是落实已批准的逐源凸包表示，没有将组合外包体当成原形状。

实际形状数：agv=3、link_1…5 各 1、link_6=2。所有 collider 启用，contact_offset=0.002 m、rest_offset=0；self collision=true，六对相邻 joint collisionEnabled=false，未发现额外屏蔽非相邻对象的 collision group/filtered-pair。十个 USD 碰撞 mesh 的实际点经变换所得 bounds 与源 OBJ 单次缩放及装配后的 bounds 逐一匹配，最大误差 **5.640322e-8 m**。

stage 为 metersPerUnit=1、Z-up。依赖解析得到上述 4 个 USD 层，全部在本版本目录；额外外部 asset 列表为空、unresolved 为空。读回文件保留的是**解析后的绝对层路径**，不把它冒充 authored reference 全部为相对路径的证明；未进行跨机器移动/可移植性试验。没有为补充这项报告细节再次启动 App。

纯 Xform：`agv/elevate` 相对 agv 为 `(0,0,0.314)`；`agv/base_link` 为 `(0.105,0,1.062)`；`link_6/tool` 单位变换，其 `scanner` 子节点为 Rz135°。均不带 RigidBody/Mass/Joint，没有 camera prim、额外 DOF 或重复 scanner 质量。

## 4. 场景、驱动与监测的实际设置

场景仅一台 CR12、本地 `physicsUtils.add_ground_plane` 产生的 z=0 地面、DomeLight 和 GUI viewport；不使用远程地面资源、不加入构件/扫描相机。device=cuda:0、dt=1/120 s、render_interval=2、gravity=(0,0,-9.81)、TGS、articulation position/velocity iterations=8/2。最终实际物理上下文读回 GPU pipeline=true、GPU dynamics=true、solver=TGS，关节状态张量实际在 cuda:0。

| 轴 | K，Nm/rad | D，Nm·s/rad | effort_limit_sim，Nm | velocity_limit_sim，rad/s |
|---|---:|---:|---:|---:|
| joint_1 | 200 | 20 | 20 | 0.2 |
| joint_2 | 4000 | 550 | 60 | 0.2 |
| joint_3 | 2000 | 166 | 30 | 0.2 |
| joint_4 | 200 | 12 | 10 | 0.2 |
| joint_5 | 1000 | 37 | 10 | 0.2 |
| joint_6 | 150 | 7 | 5 | 0.2 |

PhysX K/D/max force 与表值一致，max velocity 为 float32 的 `0.20000000298023224`。原硬限位 joint_2 ±2.9671 rad，其余 ±3.0543 rad；实际读回分别 ±2.9670996666、±3.0542998314。K/D/limits 使用批准的 1e-4 相对容差和 1e-6 零值底线。USD 旋转 PD 是 converter 写入的“每度”表示，运行 Tensor/ImplicitActuator 使用 rad 单位，不再二次换算。原 URDF effort=300、较高速度与 damping=0.7 保留为原资料，没有把它们混作最终调试限制。

原生 friction 和 armature 最终均读回六个 0，没有人工追加摩擦/转子惯量、重力补偿或质量补丁。**两次驱动之间 PD、effort、velocity、重力、求解器和目标完全相同；本轮没有 PD 调参。**

agv 初始世界 link pose 为 `(0,0,0.053)`、单位四元数，六轴初始 q/dq 实际均为 0。spawn 后现有 root_joint 世界侧 anchor 仍为 z=0；在首次物理初始化前，仅场景层将其校准至 **0.05299999937415123 m**，与 body-side joint frame 一致。没有第二个约束、没有保存到派生 USD，运行期没有回写 root/anchor。一次 `sim.reset()` 的初始化时钟从 0 变到 **2 步 / 0.01666666753590107 秒**，单独记录；其后仅一次初始化 joint-state 写入，零次 root-state 写入，无额外 settle。受控计数基线建立在全部初始化读回之后。

序列实现为 0–1 秒零位保持，1–3 秒 joint_2 从 0 到 5° 五次平滑轨迹，3–6 秒保持；其余关节目标为零。位置和解析速度同时提交。每步以明确的区间终点 `t_after` 采样目标，步进后实测与同一 `q_ref(t_after)` 比较。循环只下发执行器 target，没有每步写机器人状态、teleport 或独立移动 scanner。

每 tick 顺序：targets → write_data_to_sim → sim.step(render=False) → 实际 clock 核验 → robot.update → 七个 ContactSensor 强制刷新 → 实测 q/dq 判据 → 几何/固定关系。每两个 tick 单独 render 并核验无额外 physics 推进。当前 sim 实例设置 `_disable_app_control_on_stop_handle=True`，避免本地 `simulation_context.py:724–743` 默认 STOP 回调进入无限等待恢复；没有修改框架。外层 Job watchdog 仍独立生效。

接触为七个单 body 传感器：agv 及 link_1…5 各 5 个禁止 filter，link_6 为 6 个，共 36 个有向过滤项。明确核对 native sensor_paths/filter_paths、对象数量、`[1,1,M,3]` 数据形状、时间戳和每步刷新。禁止非相邻 body 接触及活动臂—地面接触，允许同一聚合体内部、相邻安装对和 agv—地面支撑；法向向量范数单步超过 0.1 N 即停止，未用净合力抵消或空过滤器冒充无碰撞。

几何守卫使用**实际 PhysX link frame 位姿**，将实际 USD 碰撞 mesh 的 body-local AABB 转到世界，并加入 contact offset，检查非相邻重叠与活动臂穿地。这是保守守卫，不是主动避障；AABB 来源是导入后的凸包输入点，**未逐顶点读回 PhysX cooked hull**。实际接触检测提供另一路证据，不能据此认证任意运动或构件避障。

## 5. 实际命令、进程及重试

解释器核对为 `C:\isaacenvs\isaac45_harl\python.exe`，实际 UTF8 mode=1。三个 App 进程都使用 `apps/isaaclab.python.kit`、GUI/cuda:0、enable_cameras=false、livestream=0、XR=false；首轮及重试均省略 kit_args，由原 Windows helper 添加 `--/app/vulkan=false`，实际后端由各自 Kit 日志确认 **D3D12**。日志中的 GPU 为 RTX 4060 Ti（7949 MB），驱动 610.60，torch 为 2.5.1+cu121。没有使用 `isaacsim.exe` 或另一个环境代验。

以下命令均已实际执行，工作目录统一为 `E:\Project\IsaacLab_HARL`。CPU 生成仅 0.828 秒，外层 Conda 命令耗时约 3.20 秒，无 torch/Isaac/pxr/omni 模块导入。

```powershell
& D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python scripts/environments/prepare_cr12_fixed_asset.py --stage urdf --urdf-path source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assets/rokeaCR12/derived/fixed_lift0_v1/cr12_fixed_lift0.urdf --output-dir logs/scan_assignment/20260929_cr12_joint_drive/cpu_prepare

& D:\miniconda3\Scripts\conda.exe run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u logs/scan_assignment/20260929_cr12_joint_drive/repro/supervise_cr12.py --mode usd --attempt-dir logs/scan_assignment/20260929_cr12_joint_drive/attempt_01 --urdf-path source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assets/rokeaCR12/derived/fixed_lift0_v1/cr12_fixed_lift0.urdf

& D:\miniconda3\Scripts\conda.exe run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u logs/scan_assignment/20260929_cr12_joint_drive/repro/supervise_cr12.py --mode drive --attempt-dir logs/scan_assignment/20260929_cr12_joint_drive/attempt_02 --usd-path source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assets/rokeaCR12/derived/fixed_lift0_v1/usd/cr12_fixed_lift0.usd

& D:\miniconda3\Scripts\conda.exe run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u logs/scan_assignment/20260929_cr12_joint_drive/repro/supervise_cr12.py --mode drive --attempt-dir logs/scan_assignment/20260929_cr12_joint_drive/attempt_03 --usd-path source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assets/rokeaCR12/derived/fixed_lift0_v1/usd/cr12_fixed_lift0.usd
```

监督器实际创建的三个目标子进程命令如下。继承父进程环境，仅在子进程环境副本中明确 GUI/camera/livestream/XR 开关；没有改持久环境变量。

```powershell
D:\miniconda3\Scripts\conda.exe run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/prepare_cr12_fixed_asset.py --stage usd --urdf-path E:\Project\IsaacLab_HARL\source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\assets\rokeaCR12\derived\fixed_lift0_v1\cr12_fixed_lift0.urdf --output-dir E:\Project\IsaacLab_HARL\logs\scan_assignment\20260929_cr12_joint_drive\attempt_01 --device cuda:0 --info
D:\miniconda3\Scripts\conda.exe run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/run_cr12_joint_drive.py --usd-path E:\Project\IsaacLab_HARL\source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\assets\rokeaCR12\derived\fixed_lift0_v1\usd\cr12_fixed_lift0.usd --physics_steps 720 --output-dir E:\Project\IsaacLab_HARL\logs\scan_assignment\20260929_cr12_joint_drive\attempt_02 --device cuda:0 --info
D:\miniconda3\Scripts\conda.exe run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/run_cr12_joint_drive.py --usd-path E:\Project\IsaacLab_HARL\source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\assets\rokeaCR12\derived\fixed_lift0_v1\usd\cr12_fixed_lift0.usd --physics_steps 720 --output-dir E:\Project\IsaacLab_HARL\logs\scan_assignment\20260929_cr12_joint_drive\attempt_03 --device cuda:0 --info
```

| 尝试 | 监督器起止（UTC+08:00） | Python / Conda PID | App构造 / 全进程树秒 | 工作结果 | 目标 / Conda / 监督命令退出 |
|---|---|---|---|---|---|
| 01 USD | 12:58:02.218 → 12:58:49.454 | 16532 / 36544 | 31.297 / 47.234 | 导入、保存、读回通过；无关节动作 | 0 / 0 / 0 |
| 02 drive | 12:59:32.664 → 13:00:12.076 | 21472 / 29488 | 24.500 / 39.421 | 惯量读回误判，0受控步，FAIL | 0 / 0 / 1 |
| 03 drive | 13:03:26.821 → 13:04:18.245 | 3836 / 21816 | 23.813 / 51.422 | 600受控步，保持速度超限，FAIL | 0 / 0 / 1 |

时间以监督器明确带 +08:00 的记录为准，Kit 正文保留其原始 04/05 时显示。三次分别对应 `kit_20260929_125807.log`、`kit_20260929_125937.log`、`kit_20260929_130331.log`，已各保留一份当次副本。监督器在启动前确认桌面可用，先将 suspended Conda 归入独占 Job 再恢复；App 180 秒、全树 360 秒，预留收尾时间。三次均自然退出、无超时、无 kill，且前一次全部退出后才开启下一次。app.close 前完成/失败事实均已 flush；native close 没有返回 Python，不能仅依赖 `app_close_returned`，也没有修改 telemetry/关闭设置缩短等待。

### 5.1 首次失败与本地修正

attempt_02 的质量、COM、完整原生矩阵已在检查前保存。原实现按 API 中含糊的 “center of mass local frame” 将它再做 `R_com I_raw R_comᵀ`，导致 agv 最大误差约 **0.192909 kg·m²**，触发动作前停止。这次失败原件保留，仍为 FAILED。

本地 `omni.physics.tensors/impl/api.py:2152` 对 ArticulationView 描述较短；同文件 RigidBodyView 的 `:3160,3327` 明确返回/设置 **object frame** 中的完整矩阵，core articulation wrapper 也直接 reshape/返回它。安装包未提供可审查的 native 实现，未声称查明其内部算法。本次原始矩阵的非零交叉项及两种独立校验提供了进一步证据：

- 七体 raw 直接与批准 body-axis 张量比较全部在原容差内；agv/link_6 最大误差为 **1.559712e-6 / 3.588607e-8**。
- `R_comᵀ I_raw R_com` 与保存的 USD diagonalInertia 对应，agv/link_6 最大差为 **1.507504e-6 / 2.950178e-8**；COM quaternion 与 USD 主轴旋转也一致。
- 错误地再旋转一次，agv/link_6 反而产生 **0.192909 / 0.0268252** 的误差。

最终固定解释为：原生 3×3 **关于 COM、以 link/object 轴表达**；直接比较 body 张量，并额外用逆旋转交叉检查 USD 主惯量。没有在多个解释中运行时择优，没有把观测值写回期望，没有质量覆盖或新平行轴项。新增非单位主轴的独立手算 regression，最终 14/14 CPU 测试通过，再进入唯一一次重试。旧计划中关于 Tensor 返回值必须再乘 COM 主轴旋转的假设由本次证据纠正，旧报告不回写。

## 6. 最后一次真实运动数据与失败边界

实际初态六轴位置和速度均为 0；以下“最后”是 **t=5 秒停止样本**，不是计划 t=6 秒终点。全过程最大值由原累计的前 599 个样本加上保存的第 600 个 q/dq 离线合并，后者未增大任一最大值；没有补造丢失的逐 tick 数据或改写原 JSON。

| 轴 | 起点° / 最后位置° | 600样本最大位置误差° | 最后速度 rad/s | 600样本最大绝对速度 rad/s |
|---|---:|---:|---:|---:|
| joint_1 | 0 / 0.006714367 | 0.030597893 | 0.005991803482 | 0.007379265036 |
| joint_2 | 0 / 5.297537409 | 0.329173151 | -0.001313207904 | 0.087915927172 |
| joint_3 | 0 / 0.303719596 | 0.338239025 | -0.002486783545 | 0.010190325789 |
| joint_4 | 0 / 0.130164956 | 0.156460517 | 0.006123690866 | 0.010972766206 |
| joint_5 | 0 / 0.167138491 | 0.177328880 | **-0.023184916005** | 0.025670422241 |
| joint_6 | 0 / -0.086883168 | 0.104028130 | **-0.025973619893** | 0.030289942399 |

已观测 600 样本的位置误差均≤0.5°、速度绝对值均≤0.25 rad/s，未记录硬限位/非有限状态失败。t=1 秒 joint_2 为 **0.047046773°**，t=2 秒 **2.624886948°**，相对 ramp 起点约 **2.577840175°**，无进展检查通过；t=3 秒为 **5.321145104°**。第 600 步 joint_2 超过 4.5°只证明当时实际位移，不替代完整保持验收。

末秒速度判据从数学参考 t=5 秒开始执行，joint_5/6 在首个该时刻样本即超限，按规则立刻结束。因此：

- **720 步/6 秒未完成**；实际受控增量为 600 步、5.000000260770321 秒，初始化的 2 步不混入其中。
- 七个接触传感器各完成 **600 次**强制新读回；映射/形状/刷新检查有效，所记录禁止 pair 最大法向力均为 **0 N**。这不是空 filter 或净合力抵消结论。
- 第 600 步先做接触刷新，再做速度判据并抛出；其后的几何/frame检查未执行。**几何、root/frame 汇总只覆盖初始化及前 599 受控步**。这些样本未触发 AABB/穿地守卫，活动臂碰撞包围盒最低 z 为 **1.2399987636 m**；agv link 最大漂移为 **0 m / 0 rad**，四个纯装配 frame 的最大相对误差均为 0。没有将它们扩写成完整循环无碰撞通过。
- `render_calls=299`，第 600 步失败后未继续渲染/凑步。原结果中的 `last_second_maximum_*` 全零是**尚未完成一次成功累计的初始化值**，不能读作末秒速度/误差为零，更不能读作保持通过。
- 没有在速度超限后放宽阈值、继续 settle、关重力/碰撞、增加摩擦/armature，或用每步状态写入压住运动。

当前能确认 joint_5/6 在保持判据开始处速度未满足要求；没有完整轨迹/力矩测量支持饱和、数值噪声或特定耦合根因结论。本轮按简洁记录要求没有逐 tick 原始张量 dump。后续若需解释保持行为，应针对这一失败做有限诊断，而不是将当前数据写成全工作空间控制成功。

## 7. 验证、日志限制与未执行事项

已执行的主要 CPU 检查命令：

```powershell
& D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python -c "import sys; print(sys.executable); print(sys.flags.utf8_mode)"
& D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/_cr12_asset_math.py scripts/environments/prepare_cr12_fixed_asset.py scripts/environments/run_cr12_joint_drive.py source/isaaclab_assets/isaaclab_assets/robots/rokea_cr12.py source/isaaclab_tasks/test/test_cr12_asset_math.py logs/scan_assignment/20260929_cr12_joint_drive/repro/supervise_cr12.py
& D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/_cr12_asset_math.py scripts/environments/run_cr12_joint_drive.py source/isaaclab_tasks/test/test_cr12_asset_math.py
& D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python -B source/isaaclab_tasks/test/test_cr12_asset_math.py
```

首次完整套件 13/13、4.689 秒；读回修复后的最终套件 **14/14、4.620 秒、exit 0**。覆盖独立批准质量/张量、旋转平行轴、源保护/拒绝覆盖、派生结构/引用、实际几何点变换、轨迹端点/速度/采样时刻、名称/四元数、额外物理步/NaN 时间、t=2 无进展、末秒速度和非有限状态。另以纯 CPU 内存检查确认失败数据 NaN/Inf 能记录为明确字符串，且导入纯检查入口不加载 runtime；保存的七体 raw/主轴也做了离线交叉核对。

早期 CPU 测试曾发现人工录入的 link_3 源 hash 多一个字符，已在正式生成前按只读实测修正；原模型没有变化。序列化检查还避免了失败前统计初值 infinity 掩盖主异常的问题。这些都在首个 App 前完成；实际唯一运行修复是第 5.1 节的惯量读回解释，修改只发生在两次运行完全退出之间。

三个当次 console/Kit 未发现 GPU/CUDA device-lost、访问异常、OOM 或 PhysX 错误，但**存在警告**：omni.kit_app 提前加载、HDF5 build/runtime 版本提示、RTX TLAS limit `valid true, within:false`、跳过 Intel 集显及部分旧扩展路径/OmniHub 提示。没有观察到随后的原生崩溃，也没有据此归因本次保持速度失败；未修改已接受启动逻辑、软件包、驱动、共享 user.toml、experience 或缓存来处理这些警告。

本轮未实现/未代验：末端 IK、移动底盘或主动升降、构件避障/通用规划、扫描相机按需采集、双视点连续循环、MRTA 适配、奖励/mask/训练器、实体精度及实机额定能力。没有训练、推理、checkpoint 读写、旧 viewer/Phase B 复验、实体连接或历史资产清理。没有 Git add/commit/push/reset/restore 等写操作；既有 dirty worktree 和已暂存 ZIP 删除保持原样。

## 8. 交接状态与下一步

当前阻断是**完整保持验收失败**，不是原资产路径、USD 导入、GPU 后端或已关闭 Phase B 的缺口。实施文件和检查通过的 v1 资产可供审阅，但不能将该版本标为完整基本驱动 PASS。

下一步先审阅本报告、首次读回修正及 t=5 秒 joint_5/6 速度失败。若同意继续，应**重新明确授权**有限的保持行为诊断/局部 PD 复测及新预算；本轮不预先调参、不生成第二版本、不启动第三次驱动。已有 effort/velocity、目标、重力、碰撞、solver 和判据保持；没有证据要求重算质量或更换依赖。

只有基本关节驱动与保持结果通过并经审阅后，才讨论末端执行、单视点采集、双视点和 MRTA。原扫描成功条件仍为到位后按需开启相机并实际取得本次数据，未被本轮扩展或改变。

文档变更仅新增本文，并小范围更新 [TASK_PROGRESS.md](../../TASK_PROGRESS.md) 与 [REPORT_INDEX.md](../../REPORT_INDEX.md) 的当前资产状态/主题链接；没有重写旧参数计划、Windows 报告或 Phase B 历史。AgentRead 本次只新增 Markdown，Python/JSON/log/patch 按用途放在源码和 `logs/`；未生成 ZIP 或重复证据包。

## 辅助证据对应表

`logs/` 证据受现有忽略规则影响，**当前保存在本机工作区，不保证随新 checkout 提供**。主报告已包含关键数字、完整命令与失败边界；以下文件用于复核。本轮只保留每次 console、同次 Kit 副本、紧凑结果/监督事件与一份新代码差异，没有逐步张量 archive。

| 结论/检查项 | 文件位置 | 关键字段/定位 | 用途与限制 |
|---|---|---|---|
| CPU 生成/实际 XML 参数 | [urdf_check.json](../../../../../../../../logs/scan_assignment/20260929_cr12_joint_drive/cpu_prepare/urdf_check.json)、[派生URDF](../../../assets/rokeaCR12/derived/fixed_lift0_v1/cr12_fixed_lift0.urdf) | bodies/candidates/joints/geometries/source_hashes | 7体6轴、模型参数、20引用和原输入保护 |
| 保存的 USD 与导入结果 | [派生USD](../../../assets/rokeaCR12/derived/fixed_lift0_v1/usd/cr12_fixed_lift0.usd)、[USD读回](../../../../../../../../logs/scan_assignment/20260929_cr12_joint_drive/attempt_01/usd_readback.json) | roots/bodies/joints/colliders/source_collision_bounds/dependencies | 实际组装、惯量、逐源碰撞与依赖；不是关节动作结果 |
| 导入执行/实际后端/退出 | [attempt_01](../../../../../../../../logs/scan_assignment/20260929_cr12_joint_drive/attempt_01/) | command.json、console.log:5627–5989、Kit Graphics API、supervisor_result.json | 独立导入一次，PASS |
| 首次驱动失败原件 | [attempt_02](../../../../../../../../logs/scan_assignment/20260929_cr12_joint_drive/attempt_02/) | result.json 的 physx_raw_readback/failures；console:7276 | 0受控步；原 key inertia_com_local 的命名不能代替坐标证据 |
| 最终驱动及严格失败 | [attempt_03/result.json](../../../../../../../../logs/scan_assignment/20260929_cr12_joint_drive/attempt_03/result.json)、[当次目录](../../../../../../../../logs/scan_assignment/20260929_cr12_joint_drive/attempt_03/) | physx_readback、initialization、drive_summary、contact_summary、failures、supervisor_result | 600步实际状态；599步几何/frame边界；内部FAIL即使exit0 |
| 实现与回归 | [准备入口](../../../../../../../../scripts/environments/prepare_cr12_fixed_asset.py)、[CPU模块](../../../../../../../../scripts/environments/_cr12_asset_math.py)、[驱动入口](../../../../../../../../scripts/environments/run_cr12_joint_drive.py)、[配置](../../../../../../../../source/isaaclab_assets/isaaclab_assets/robots/rokea_cr12.py)、[测试](../../../../../../../../source/isaaclab_tasks/test/test_cr12_asset_math.py) | 本文第2/5.1/6节符号及行号 | 当前代码与严格检查；未依赖某日AgentRead脚本 |
| 本次新代码完整差异 | [implementation.patch](../../../../../../../../logs/scan_assignment/20260929_cr12_joint_drive/attempt_03/implementation.patch) | 仅4个新正式模块/入口、1测试和1监督脚本 | 从空文件到当前内容的可审阅差异；无Git写入 |
| 所属进程监督 | [supervise_cr12.py](../../../../../../../../logs/scan_assignment/20260929_cr12_joint_drive/repro/supervise_cr12.py) | WindowsJob、阶段watchdog、same-run Kit、内部完成与退出合判 | 一次性本任务repro；不构成新通用启动框架 |

**本轮实施及授权内运行已收口，完整关节运动与保持验证未通过，等待 GPT/用户审阅；不自动进入后续调参、IK、相机、双视点、训练、Git 提交或清理。**
