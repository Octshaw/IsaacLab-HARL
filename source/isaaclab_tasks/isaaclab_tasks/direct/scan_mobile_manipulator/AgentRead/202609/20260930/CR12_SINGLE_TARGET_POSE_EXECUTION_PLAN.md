# CR12 单目标 scanner pose 执行：实施设计与最小接入方案

日期：2026-09-30（Asia/Shanghai）。状态：**设计完成，等待 GPT/用户审阅；尚未实施、尚未进行 pose 执行仿真验证。**

## 1. 推荐方案与已接受前提

推荐以实际刚体 **link_6** 为控制末端 E，把 world scanner 完整目标换算成 E 的 root-frame 目标；复用本地 **DifferentialIKController、absolute pose、DLS λ=0.01**。增加一个很小的、受约束的位置命令积分层，产生连续的六轴 position/velocity targets，交给现有 ImplicitActuator/PhysX。4 秒平滑 task-space 参考之后保持最终 pose 闭环，总受控时间最多 8 秒；以真实 scanner pose 连续稳定 1 秒判到位。

本轮只读取源码、配置、已有资产记录并做 CPU FK/几何 Jacobian/单次线性代数预测；没有调用 IK controller、迭代求解 IK、启动 Isaac/CUDA 或生成实现文件。下文所有新阈值、控制环和有限运行安排都是**待审方案**，不是已通过结果。

**用户已确认**：固定底盘、lift0、v1、baseline PD、TGS 8/2、显式 external-forces-every-iteration=on 下，原 5°轨迹完成 720/720 步、6 秒运动/保持验收，已获 **GPT REVIEW PASS**。只接受这一构型的基本驱动；不重新调查 false、PD、solver 时序或 Windows。历史报告形成时的待审/FAIL 标签不回写。Phase B 保持 COMPLETE / GPT REVIEW PASS / CLOSED。

| 保留项 | 本轮采用的明确值或边界 |
|---|---|
| 派生资产 | [fixed_lift0_v1/usd/cr12_fixed_lift0.usd](../../../assets/rokeaCR12/derived/fixed_lift0_v1/usd/cr12_fixed_lift0.usd)，不改 USD、URDF、惯量或碰撞 |
| 刚体/活动轴 | agv、link_1…link_6；仅 joint_1…joint_6；不控制底盘或升降 |
| K / D | K=(200,4000,2000,200,1000,150)，D=(20,550,166,12,37,7) |
| effort / velocity | effort=(20,60,30,10,10,5)，velocity_limit_sim=0.2 rad/s |
| 物理 | dt=1/120 s、render_interval=2、TGS 8/2、重力 (0,0,−9.81)；原接触、自碰撞、摩擦、armature 等保持 |
| 外力设置 | 新 pose 入口必须显式 on；复用现有 pre-init/session 设置及读回，不提升旧入口 inherit 默认 |
| 初始化/执行 | 复用原 reset 与一次初始关节状态写入；任务执行只能设置关节目标，不 teleport、逐步写状态或单独移动 scanner |
| 场景 | 原单机器人、地面、灯光；不加构件、相机、双视点、MRTA 或训练 |

依据：[已接受的外力单因素报告](CR12_EXTERNAL_FORCES_SINGLE_FACTOR_REPORT.md)、[机器人配置 rokea_cr12.py](../../../../../../../../source/isaaclab_assets/isaaclab_assets/robots/rokea_cr12.py) 的 `make_cr12_cfg`（19–80 行）、[run_cr12_joint_drive.py](../../../../../../../../scripts/environments/run_cr12_joint_drive.py) 的 `_run_drive`（673–827 行）。配置接受不等于本轮重新检验。

源码定位基线：HEAD `24ecbad7dd1bdcd006399b64bfb757a86b71aeec`；仓库 VERSION=2.1.0；`source/isaaclab/config/extension.toml:5` 扩展包版本 0.36.23。版本字段各有用途，以下 API 以当前本地文件为准。

## 2. W/R/E/S 与固定安装变换

统一 `T_AB = B frame 在 A frame 中的位姿`，使用列向量、米、弧度、四元数 WXYZ。scanner +X forward、+Z up；这不是 camera optical 约定，本轮不创建 camera frame。

| 记号 | 实际对象与来源 |
|---|---|
| W | 独立场景 world |
| R | articulation 实际根刚体 **agv 的 actor/link frame**；运行时 root_link_pos_w / root_link_quat_w |
| E | **link_6 的 actor/link frame**；从 body_names 解析，读取 body_link_pos_w / body_link_quat_w |
| tool / S | E 下纯 Xform：`/World/CR12/link_6/tool`、`/World/CR12/link_6/tool/scanner`，不在 articulation body/Jacobian 列表 |
| C | link_6 COM，仅用于核对 native Jacobian 的线速度参考点；不是 E/S/R |
| joint frame | 描述关节安装与轴向，不能替代末端或根刚体 frame |
| base_link / root_joint | 前者为 agv 下纯 frame，后者为固定 world joint prim；都不是此处 R |

最终派生 writer [prepare_cr12_fixed_asset.py](../../../../../../../../scripts/environments/prepare_cr12_fixed_asset.py) 的 `_finish_imported_stage`（287–298 行）明确创建零平移 tool，以及 tool 下零平移、+135° Z 旋转 scanner；`inspect_usd_stage`（199–216 行）检查纯 frame 的局部姿态及无 RigidBody/Mass。已接受运行 [attempt_02/result.json](../../../../../../../../logs/scan_assignment/20260930_cr12_external_forces/attempt_02/result.json) 的 `usd_readback.frame_paths`（435 行附近）和初始 link poses 支持实际路径。不是只依据旧原 URDF 推断。

`T_Etool=I`；`T_ES=[Rz(+135°), (0,0,0)]`，其 WXYZ quaternion 为
`(0.382683432365, 0, 0, 0.923879532511)`。因此 S 与 E 原点相同，坐标轴不同；逆变换是 Rz(−135°)。

```text
T_WE* = T_WS* · inverse(T_ES)       用户 scanner 目标 → 控制刚体目标
T_RE* = inverse(T_WR) · T_WE*       换成 controller 使用的实际 root 系
T_RE  = inverse(T_WR) · T_WE        当前控制刚体 pose
T_WS  = T_WE · T_ES                实际 scanner pose，供到位判断
```

`T_WS*` 由本轮固定目标规则产生；`T_ES` 来自最终派生 frame；`T_WR/T_WE` 来自运行时实际刚体运动学读回。到位不用 USD 静态 authored transform、q_des 的 FK 或旧 CSV proxy 位置代替。保持已有固定 frame 检查，但不要把读取固定局部 frame 误认为实际动态 E pose。

本地 [math.py](../../../../../../../../source/isaaclab/isaaclab/utils/math.py) 的 `combine_frame_transforms`（750–781 行）与 `subtract_frame_transforms`（785–816 行）可复用。[articulation_data.py](../../../../../../../../source/isaaclab/isaaclab/assets/articulation/articulation_data.py) 的 root_link pose（626–651 行）、body_link pose（830–854 行）说明 actor/link 姿态；完整 root/body state 的速度字段可能采用 COM，不能把整个 state 都解释为 link-origin twist。到位速度本轮直接用 native joint dq。

## 3. Jacobian：预期映射、参考点与首次读回

### 3.1 由本地源码及已保存运行确认的映射

已接受 result 的 `physx_readback.body_order` 为 `agv,link_1,…,link_6`，`physx_readback.joint_order` 为 `joint_1,…,joint_6`（1455、1473 行），`is_fixed_base=true`。每次仍按 native body_names/joint_names 解析并断言数量、唯一性和集合，再形成六轴列索引，不能把旧数组顺序当成永久保证。

| 项目 | 当前 v1 推导 | 下轮读回要求 |
|---|---|---|
| articulation body index | agv=0；link_6=6 | 实际按名称解析 E |
| fixed-base Jacobian body row | `body_index−1`，因此 E row=5 | fixed-base 为真；没有 root body row |
| joint columns | 当前预期 [0,1,2,3,4,5]，按 joint_1…6 顺序 | 显式选择六列，无 floating-root +6 偏移 |
| raw tensor | 预期 **(1,6,6,6)**：环境、非根刚体、空间分量、DOF | 本轮未实际调用 get_jacobians；首次运行断言 |
| E tensor | 预期 **(1,6,6)** | 克隆切片，再按名称列映射/转换 |
| 空间顺序 | `[vx,vy,vz,wx,wy,wz]` | 与解析几何 J 的两块分别校核 |
| 表达坐标 | native 文档为 world-space link velocities | 目标在 R 时，两块都旋转至 R |
| root DOF / scanner row | fixed base 无 root 6DOF；纯 scanner 无单独 row | 不虚构 scanner body index |

fixed-base 索引依据：[task_space_actions.py](../../../../../../../../source/isaaclab/isaaclab/envs/mdp/actions/task_space_actions.py) 70–77 行；native names 来源：[articulation.py](../../../../../../../../source/isaaclab/isaaclab/assets/articulation/articulation.py) 115–147 行。

安装版文件 `C:/isaacenvs/isaac45_harl/Lib/site-packages/isaacsim/extsPhysics/omni.physics.tensors/omni/physics/tensors/impl/api.py`：
`get_jacobians` 第 1765 行说明 world-space，第 1783–1794 行实际建立并重复使用 4D float32 buffer。第 1772 行的 3D 描述和部分 shape 文档不能替代实际断言；必须 clone 后转换，避免后来读回复用 buffer 改写快照。

### 3.2 仍需运行校核的线速度参考点

本地 Python 文档没有充分说明 Isaac tensor 的线性块最终位于 actor 原点还是 COM；后端为编译模块，定向查找未发现能证明转换细节的源码。[上游 PhysX dense Jacobian 文档](https://nvidia-omniverse.github.io/PhysX/physx/5.3.0/docs/Articulations.html#jacobian) 采用 COM，并给上述六分量顺序；这**不能单独证明当前 Isaac wrapper 是否已经转换**。不将该项伪装成静态确认。

下轮第一次运动前，在原初始化完成、实际 q/link pose 已读取的同一物理时刻，读取并克隆 J；用派生 joint origins/axes 与当前实际 q/root/link pose 构造解析 J_E 和 J_C：
`Jv_i = a_i × (p_point−p_joint_i)`，`Jw_i=a_i`。分别比较六列的线性/角块，候选绝对容差为 `1e−4 m/rad` / `1e−4`。**唯一匹配**才选定预先定义的 adapter 并冻结本次选择；双匹配、均不匹配、维度/有限值错误或陈旧数据均报 `SETUP_JACOBIAN_SEMANTICS`，不发运动命令。不靠哪种结果“更容易到位”选语义。

已保存 E 的 COM 偏置约 `c_E=(0.060712673,0.060718220,0.118532829) m`。零位 joint_6 对 E 原点的线性列为零，对 COM 则约 `(−0.060718220,+0.060712673,0)`，可明显区分。比较必须使用实际 q，而不是假定 q 始终精确为零。

若读回为 COM Jacobian，令 `r_W=R_WE c_E=p_C−p_E`，则：

```text
Jv_E^W = Jv_C^W + skew(r_W) · Jw^W     # 正号
J_E^R  = diag(R_RW, R_RW) · J_E^W       # R_RW = transpose(R_WR)
```

若原本就是 E 原点则跳过点平移。这里仅改变表达基及线速度参考点，不给 fixed root 加运动项，也不再因 scanner 的 +135° yaw 把 root/world angular block 旋转一次。scanner 零平移使 E/S 原点一致；安装旋转已在目标换算中处理。

[run_osc.py](../../../../../../../../scripts/tutorials/05_controllers/run_osc.py) 315–323 行可参考 clone 及两个 block 的 root 旋转，225–228 行提示 reset 后 J 可能尚未刷新，所以上述校核同时检查 freshness。若首次数据未刷新，停止并按局部读取/API 实现问题处理，不自行添加未计数 step。[run_diff_ik.py](../../../../../../../../scripts/tutorials/05_controllers/run_diff_ik.py) 162–171 行只转换 pose，不能照搬为任意 root 朝向方案；144–158 行周期 reset/state write 不适用连续执行。

## 4. 一个已定数值的 scanner 功能目标

### 4.1 来源及确定规则

使用已接受 explicit-on `attempt_02/result.json → initial_body_link_poses`（1868 行起，link_6 在 2025 行附近），复合最终 `T_ES` 得到以下保存初态。不是本轮新仿真测量。

| pose | position，m | quaternion，WXYZ |
|---|---|---|
| 保存的 `T_WR0` | (0.000000004657, 0.000000000058, 0.053000152111) | (1, −1.030614e−10, 1.036531e−9, 6.352974e−12) |
| 保存的 `T_WS0` | (0.104999989271, −0.149999842048, 2.887999057770) | (0.382683440452, 2.903724e−8, 6.713142e−9, 0.923879529162) |

**下一轮固定算法**：完成原初始化和 guard 后，只采样一次实际 `T_WS0`，立刻生成并冻结目标：

```text
Δp_W = (+0.0106981457149994, 0, −0.000155046722254002) m
p_WS* = p_WS0 + Δp_W
R_WS* = Ry_world(+1.0 degree) · R_WS0
```

旋转是**绕世界 Y 左乘**，不是绕 scanner 局部 Y 右乘。平移模长 10.699269 mm，姿态变化 1°；相同平移在初始 scanner 系约为 (−7.564731,−7.564732,−0.155046) mm。上述 offset 本轮定死，运行中不随当前姿态重新定目标、不随机换点。

若采用保存初态，则具体数值为：

| 目标 | position，m | quaternion，WXYZ |
|---|---|---|
| `T_WS*` | **(0.115698134986, −0.149999842048, 2.887844011048)** | **(0.382668868980, 0.008062296544, 0.003339507341, 0.923844350407)** |
| `T_WE*=T_WS* inv(T_ES)` | 同上 | **(0.999961922808, 0.000000004833, 0.008726564893, −0.000000008795)** |

下一轮以本次实测初态构造的值为 authority，并记录它与以上候选的区别；不同时强制旧绝对值和新测相对值。`T_RE*` 再用同次实测 `T_WR` 左乘逆变换；不直接减配置中的 0.053 而忽略实际 root 旋转。此点仅为功能测试，未成为构件扫描视点。

### 4.2 离线数学支持与限度

读取[当前派生 URDF](../../../assets/rokeaCR12/derived/fixed_lift0_v1/cr12_fixed_lift0.urdf) 的六关节段（179–226 行），与最终 USD inspector（`prepare_cr12_fixed_asset.py:122–148`）一致：安装平移依次为
`(.105,0,1.062),(0,0,.35),(0,0,.76),(0,0,.54),(0,−.15,0),(0,0,.123)`，轴向 `Z,Y,Y,Z,Y,Z`，零位安装 RPY 为零。使用标准齐次 FK 与几何 J，名义零位 FK 与保存初态矩阵最大元素差约 1.0942e−6；计算按实际初始 E 姿态对齐，保留数值误差说明。

零位、world 近似 identity root 下，E 原点的 J（列为 joint_1…6，前三行 m/rad）为：

```text
[ .150  1.423  .663  .150  .123  0 ]
[ 0     0      0     0     0     0 ]
[ 0     0      0     0     0     0 ]
[ 0     0      0     0     0     0 ]
[ 0     1      1     0     1     0 ]
[ 1     0      0     1     0     1 ]
```

秩为 **3**，不满秩是当前构型事实，不能直接当成 API 配置错误。原始奇异值约 `(2.237013,1.732051,0.721388,0,0,0)`；线性和角度单位混合，不能解释成通用无量纲条件数门槛。

给定一个**离线 FK 见证构型** `q_deg=(0,+1,−1.5,0,+1.5,0)`，可得到上面的非零平移与世界 Y +1°变化；与实际初态对齐后，目标位置差约 6.6e−10 m。该构型的 J 为 rank 6，最小原始奇异值约 0.006440；离原硬限位最近仍约 169°。它说明附近存在一个几何构型，不是下轮规定必须走的关节轨迹或实际可达证据。

只对同一目标做一次 `Jᵀ(JJᵀ+0.01²I)⁻¹e` 线性预测，没有调用 controller、迭代求解或控制机器人：

| joint | 单次线性预测 Δq，度 |
|---|---:|
| joint_1 | −0.007104083 |
| joint_2 | +0.235762493 |
| joint_3 | +0.343737364 |
| joint_4 | −0.007104083 |
| joint_5 | +0.420456351 |
| joint_6 | +0.014206746 |

该预测经 FK 后距目标约 **0.102459 mm / 0.000181495°**。这里只说明局部任务误差主要落在可运动方向，小量二阶偏差不大；不能把这组数直接下发替代本轮要验证的完整 pose 链。下轮预期运动为亚度至约 1.5°量级，允许负载补偿造成不同分配；不把“必须复现见证 q”当成功条件。

用已保存 `usd_readback.colliders`（441 行起）的 10 个局部碰撞包围盒，对见证路径 `q(s)=s q_witness` 做 101 个离线采样，每侧加原 0.002 m offset：禁止非相邻包围盒重叠数为 0，运动臂最低 z 约 1.239999 m，最小盒分离裕量约 14.888 mm。这**不是**实际 Cartesian+DLS 路径，也不是连续碰撞证明或 cooked hull 实测；仅支持此小目标适合作为第一项功能尝试。

## 5. DiffIK 与连续执行器参考

### 5.1 复用的 controller

拟配置：

```text
DifferentialIKControllerCfg(
    command_type="pose",
    use_relative_mode=False,
    ik_method="dls",
    ik_params={"lambda_val": 0.01},
)
```

N=1；下一轮使用已接受的 cuda:0 执行模式。输入是 R 系 E 的完整 absolute pose `[x,y,z,qw,qx,qy,qz]`。每 tick 提供当前实际 `T_RE`、统一到 E 原点/R 系的 `J_E^R`、按名称排列的实际 q。误差 `e=[p*−p; axis_angle(q* inv(q))]`，位置和轴角均在 R 表达，角度为弧度、采用最短旋转。

源码：[differential_ik_cfg.py](../../../../../../../../source/isaaclab/isaaclab/controllers/differential_ik_cfg.py) 21–70 行；[differential_ik.py](../../../../../../../../source/isaaclab/isaaclab/controllers/differential_ik.py) 76–84、144–174、227–236 行；`math.compute_pose_error:852–866`、`axis_angle_from_quat:646–674`。

```text
Δq_IK = Jᵀ (J Jᵀ + λ² I)⁻¹ e
q_IK  = q_actual + Δq_IK
```

**compute 返回绝对 q_IK**，不是速度，也不是独立的 Δq。λ=0.01 是本地默认，不是 CR12 优化结果。DLS 分支没有 k_val、dt、速度输出、限位、碰撞、轨迹或迭代到收敛功能；`reset()` 是空操作，不能依靠它清除旧目标。set_command 不代做完整有限值/归一化检查。6D 米与弧度直接拼接，本轮不另加权重、伪逆选型或自适应 damping。

### 5.2 推荐最小位置命令积分层

旧关节 drive 通过不代表 scanner pose 已达到本轮精度。已接受 result 的最终 actual q，与原 `(0,5°,0,0,0,0)` 命令做 CPU FK 比较，scanner 差约 **11.6278 mm / 0.77306°**。这只是静态负载下位置偏差的证据，不重开 PD 调试。

每 tick 直接提交 `q_actual+Δq_IK`，在任务误差趋零时会把弹簧的位置偏置也趋零，无法一般性保留承载重力需要的 position-command offset。因此推荐复用 DLS 方向，外加以下**新参考层**，不改变原 PD，也不增加力矩补偿：

```text
初始化一次：q_cmd_previous = q_actual_initial

Δq_IK      = controller.compute(...) − q_actual
α          = dt × 2.0 /s = 1/60
q_proposal = q_cmd_previous + α × Δq_IK
准入全部通过后：
    将 q_proposal 转为实际提交的 dtype，复核所有约束
    dq_cmd = (q_proposal − q_cmd_previous) / dt
    成对设置 joint position target、joint velocity target
    write_data_to_sim()
    保存本次实际提交的 q_proposal 作为 q_cmd_previous
    sim.step() 一次；robot.update(dt)
    读取 post-step actual pose/q/dq，进行 guard 与到位判断
```

增益 2.0/s 是首版固定候选，不做扫描。它保留任务误差消失时的负载位置偏置，dq_cmd 自然趋零；属于**新增外环、尚未证明稳定和精度**。q_cmd_previous 不能每 tick 被实测 q 重置，也不能把被拒绝的 proposal 累加进去。dq_cmd 按最终实际量化/提交的位置差分算，不能把原始 DLS Δq 除 dt 冒充速度。

两类 setters 只写 buffer，实际提交见 `articulation.py:173–200、882–928`。[actuator_pd.py](../../../../../../../../source/isaaclab/isaaclab/actuators/actuator_pd.py) 的 `ImplicitActuator.compute:115–140` 保留传入目标；其中 effort 公式只是近似记录，真实 PD 仍由 PhysX 执行。下轮继续核对提交的两个 buffer 与本 tick 命令一致。

## 6. 轨迹和命令准入

### 6.1 4 秒 task-space 参考

从初始化实测 `T_WS0` 到一次冻结的 `T_WS*`，取 `u=clip(t/4,0,1)`、`h=10u³−15u⁴+6u⁵`：

```text
p_ref = p_0 + h (p*−p_0)
R_ref = Exp(h Log(R* R_0ᵀ)) R_0
```

本目标等价于 `Ry_world(h × 1°) R_0`。位置与旋转进度共享端点速度/加速度为零的 quintic；每 1/120 s 更新一次。第 k 次控制根据 t_k 实测状态求解 t_(k+1) 的 reference，step 后在 t_(k+1) 比较；不混用未来参考与旧采样时间。不线性插 Euler。

本地 `quat_slerp:1648–1673` 非 batch 且负 dot 时修改 q2；`interpolate_rotations:1713–1715` 对小于 0.05 rad 直接重复目标，本例 1°会失去平滑。建议用现有 quaternion/axis-angle 基元实现上述等价 geodesic，规范符号、clone 输入、显式处理零角。不要直接复制该小角快捷路径。

4 秒后 reference 固定为最终 scanner 目标，继续同一反馈与积分层，直到稳定成功或总预算耗尽；不锁住某个中间 q，不在 q_cmd 尚变化时强行改成 velocity_target=0。

### 6.2 首版固定准入值

以下全部是待审的功能测试保护值；超限即 FAIL，**不 clamp 输出、不更改目标、不延长轨迹**。

| 检查 | 拟采用值/行为 |
|---|---|
| 状态/目标/输出有限 | q、dq、J、pose、q_IK、q_proposal、dq_cmd 全部 finite；目标四元数非零、norm 误差≤1e−3 后规范化，异常输入拒绝 |
| 原硬限位 | joint_2 为 ±2.9671 rad，其余 ±3.0543 rad；下轮与已有读回一致。q_IK 与提交命令各留 **0.02 rad** margin；不改模型 |
| 原实际限位守卫 | actual q 不超过原硬限位加原 1e−3 rad 数值容差 |
| 原始 DLS 更新 | max abs(q_IK−q_actual) ≤ **0.035 rad** |
| 累计命令与实际差 | max abs(q_proposal−q_actual) ≤ **0.035 rad**，防止位置积分累积 |
| 相邻提交命令变化 | max abs(q_proposal−q_cmd_previous) ≤ **0.00125 rad/tick** |
| 命令速度 | max abs(dq_cmd) ≤ **0.15 rad/s**；在 α 与原始更新共同限制下通常更小（≤0.07 rad/s） |
| 本次小目标信任范围 | actual q、q_IK、q_proposal 均距初始化 actual q 每轴≤**5°**；不是重设硬限位或规定见证路径 |
| 原实际速度 guard | 保留 max abs(dq_actual)≤**0.25 rad/s**；actuator 0.2 rad/s 限制不改 |
| Jacobian | 首帧语义校核通过，后续 shape/finite/索引固定；rank<6 本身不拒绝，DLS 异常或输出违规才失败 |

soft_joint_pos_limit_factor 当前为 1.0；soft limits 是软件参考范围，不等于 IK 自动约束。上述 margin/步长由执行层负责，PhysX 硬限位只是最后物理约束，不能代替命令检查。限位拒绝、计算失败或未收敛不转化为“夹到另一 pose 后成功”。

## 7. 实际到位、碰撞和有限失败

### 7.1 成功定义

只在 t≥4 秒后，以 post-step `T_WS=T_WE T_ES` 相对冻结的最终目标判断：

- position 欧氏误差 **≤0.002 m（2 mm）**；
- 最短姿态误差 **≤0.25°（0.004363323 rad）**，四元数 q/−q 等价；
- native 六关节 max abs(dq) **≤0.01 rad/s**；
- 当前 sample 的 finite、原硬限位、contact/AABB、root/frame 和 clock 全通过；
- 上述条件连续保持 **1.0 秒**，120 Hz **至少 121 个含两端的连续 post-step 样本**，实际时钟跨度≥1.0−1e−6 s。中间不满足即清零稳定窗口，不重置总预算。

成功最早约 t=5 秒。末端姿态来自实际运动；不能仅用 q tracking、目标 FK 或 reference 结束来判成功。2 mm/0.25°是本次功能目标的待验证阈值，不是实体测量精度承诺，也不用 0.12 mm 测量指标。

**到位 ≠ 扫描完成**。本轮后续若成功只记录 `POSE_REACHED`，不存在相机数据或扫描成功回执。

### 7.2 最小碰撞边界

复用原 `_check_contacts`（409–448 行）、`_check_geometry`（348–376 行）及 `_check_frames`（328–344 行）：

- ground 对底座支撑、同一固定组合及原相邻关节例外保持；禁止 pair contact force>0.1 N 即失败；不新加忽略对。
- 按实际 link pose 变换原碰撞包围盒，保留原 0.002 m offset；禁止非相邻包围盒重叠、臂包围盒穿过 ground。AABB 重叠是保守拒绝，不等于证实 hull 接触。
- root 漂移≤1e−4 m / 1e−4 rad；纯固定 frame 漂移≤1e−5 m / 1e−5 rad。各项每个 post-step 检查，失败步也留证。

新增很小的**提交前预测 guard**：对实际 q 到本次真正 q_proposal 的关节线段中点/终点做 CPU FK，以相同盒与例外规则拒绝明显自碰/穿地；采用将实际提交的参考，不能检查离线见证轨迹却执行另一条轨迹。它不是连续 swept-volume 碰撞保证；真正状态仍靠每步 actual/contact 守卫。预测触发即停止，不求绕路。首个场景没有构件，不能由此声称具备构件避障。

物理 collider、contact 检测、保守几何拒绝与主动规划是不同能力。本轮建议不引入完整规划器。局部路线不能完成时按失败收口；若后续需要通用绕障、碰撞可行路径或更大工作空间，另行审阅。

### 7.3 预算及故障分类

| 项目 | 待审的明确预算/条件 |
|---|---|
| 受控物理预算 | **最多 8.0 s / 960 physics steps**，4 s reference + 至多4 s最终反馈/稳定；原初始化步骤单列计数 |
| 时钟 | 每 tick 只允许一次受控 step、dt=1/120；root/frame/physics/clock 异常立即失败 |
| 发散 | 相对当前 task reference 的位置误差>30 mm 或姿态误差>5°连续12步即 FAIL；非有限立即 FAIL |
| 无进展 | t≥4 s 后，ρ=max(position_error/2mm, angle_error/0.25°)；每满1 s窗口，若当前ρ>1且较窗口起点下降不足10%，报 NO_PROGRESS。已在 pose 容差内等待 dq/稳定时间时不套此规则 |
| 到期 | 8 s 未形成完整稳定窗口即 TIMEOUT；不能自动加时或放宽判据 |
| App 墙钟 | 保留启动最多180 s、所属进程树总计最多360 s；成功/失败均有关闭与进程退出记录 |
| 下轮建议次数 | 1次主运行；仅明确局部实现错误允许审阅授权范围内最多1次修复重试；不是本轮运行授权 |

SETUP（shape、名称、frame、J 参考点/刷新）、COMMAND_REJECTED（finite、limits、jump、累积差）、PHYSICS/GUARD、DIVERGENCE、NO_PROGRESS、TIMEOUT、INFRASTRUCTURE 分开记录。诊断“本地 DLS/当前外环未到位”不等于证明几何目标全局不可达。

frame/index/名称映射、controller API、轨迹离散/时间戳错误属于可局部修正实现；目标确实不可达、需改模型/PD/solver、需规划则结束并返回审阅。禁止接触、native/GPU 故障、正常无进展/超时或效果不佳不自动触发重跑、换目标或调参。故障后不再提交新运动，执行有界停止/关闭；不把停止仿真描述成实体机器人已安全制动或可开始下一任务。

## 8. 下一轮最小代码接入位置

以下是拟新增/修改清单，**本轮没有创建这些实现文件**。不用 legacy proxy env、RL wrapper 或完整 scan executor。

| 拟文件/符号 | 范围与复用 |
|---|---|
| 新增 `scripts/environments/run_cr12_pose_target.py` | 单目标入口、固定 baseline/on、目标冻结、120 Hz主循环、预算、结果与关闭；App后创建现有 DiffIK |
| 新增 `scripts/environments/_cr12_pose_control.py` | W/R/E/S math、解析 Jacobian 点校核、轨迹、受限位置参考积分、准入与连续到位窗口；按单 tick 推进，不做长阻塞 executor |
| 新增 `scripts/environments/_cr12_runtime_support.py` | 只抽取现有 CR12 场景/初始化、通用 Recorder 和状态/几何/contact/frame/clock/提交读回工具 |
| 修改 `scripts/environments/run_cr12_joint_drive.py` | 改共享 imports/调用；保留旧5°轨迹、原诊断窗口与720步成功条件；不塞入 pose 逻辑 |
| 新增 `source/isaaclab_tasks/test/test_cr12_pose_control.py` | 有意义的纯 CPU 数学/状态机/拒绝行为检查，见下节 |
| 下一轮日志目录内一次性 `repro/` 监督器 | 复用已有 owned Job、实时排空、180/360秒机制；将720步旧工作标志改为本次 pose完成/≤960步。旧监督器不改 |

共享抽取具体边界：`DriveCheckError/check_clock`、`_pose_matrix/_rotation_error/_calibrate_root_anchor/_read_physics`、`_body_poses/_frame_locals/_check_frames/_check_geometry`、`_make_contacts/_check_contacts/_contact_summary`、`_assert_active/_clock/_joint_state/_capture_submitted_targets`。`_usd_world_matrix/_flatten_paths` 等只随直接依赖机械迁移。场景构造（原673–781行）和一次初始状态准备（798–827行）分别抽成 `create_fixed_cr12_scene`、`initialize_fixed_cr12_state`，维持当前先后关系，避免把旧 state probe 的插入位置改变。

`check_joint_sample` 含旧 t=2/t=5 到位窗口、`_sync_diagnostics` 和旧720步流程仍留旧入口；新循环可复用其基础有限值/硬限位思路，不能沿用旧成功分类。新姿态报告不依赖重跑旧关节试验；针对抽取只做导入/静态调用序与必要 CPU 回归。

直接复用且不计划改动：[rokea_cr12.py](../../../../../../../../source/isaaclab_assets/isaaclab_assets/robots/rokea_cr12.py)、[_windows_runtime_startup.py](../../../../../../../../scripts/environments/_windows_runtime_startup.py) 的启动参数准备、[view_scan_assignment.py](../../../../../../../../scripts/environments/view_scan_assignment.py) 的 `_prepare_cuda_before_app`、[_cr12_external_forces.py](../../../../../../../../scripts/environments/_cr12_external_forces.py) 的 pre-init/readback、现有 v1 资产。保持既有 UTF8/D3D12/experience/相机关闭/pre-App CUDA 顺序；不做另一个 Windows 启动框架或无关 CUDA 基准。

新入口只需要一个已定目标及上述少量固定参数，不需要新的 profile 文件、scheduler 或 MRTA authority。未来可复用单 tick pose 执行与场景 helper；本轮不提前实现 assignment/owner/completed、相机、双视点或策略反馈。

## 9. 审阅后建议的最小实施/验证顺序

| 顺序 | 新增工作与依赖 | 最小验证/产物 |
|---|---|---|
| 1. 纯数学与局部共享层 | 上节有限抽取；目标/变换、controller adapter、积分参考和 guard | CPU测试覆盖 q/−q、非identity root（如90°）、COM修正符号、名称乱序映射、错误shape/NaN、拒绝不累计、不clamp、量化后差分速度、轨迹端点和121样本计时；不启动 App |
| 2. 同一新入口首次读回 | 原场景初始化/on/baseline；实际 body/joint、pose和 J 校核；一次冻结目标 | 不额外加入诊断 step；读回不合格在运动前 FAIL。不能跳过设置/参考点问题开始控制 |
| 3. 一次有限 pose 执行 | 只有步骤2合格才开始4秒参考与最终反馈；GUI/D3D12/cuda:0，num_envs=1，无相机 | 最多960受控步；记录实际到位窗口、全部 guard、完成标志、自然退出或超时处理；用户当前没有授权执行 |
| 4. 结果审阅 | 一份 Markdown 主报告，失败如实分类 | 不因exit0宣称成功，不将基础设施错误当pose成功/扫描失败；下一阶段仍另行授权 |

现有入口 `run_cr12_pose_target.py` 尚不存在，故本报告不提供伪装成现成可执行的命令。下一轮实现后应使用已验证的 Conda 父进程/UTF8准备、现有 AppLauncher 参数及显式 on，新增 pose入口自己的960步上限；不要把旧 drive 的720步参数或 PD profile 直接透传成新语义。原初始化隐含的2个 physics steps单列，960只计本轮受控循环；任何新出现未解释的步数差都失败。

最小日志：一个结果JSON（输入目标、固定frame、实际名称/J shape/点适配、参数、总步数、到位/失败原因和退出）、一个紧凑CSV（每步 clock、实际/ref/target pose误差、q/dq、提交位置/速度、关键guard）、一份 console/监督结束记录。初始 Jacobian 及失败样本保存一次即可，不做全量 tensor/raw dump、ZIP或新的 gate/ledger。源码与测试放源码/测试目录，临时监督器在日志 `repro/`，**AgentRead 只放主报告**。监督复用来源：[已有 supervise_cr12_external.py](../../../../../../../../logs/scan_assignment/20260930_cr12_external_forces/repro/supervise_cr12_external.py)，不在本轮运行或复制。

## 10. 未决事项、证据等级与本轮交付

**人工显示边界**：**源OBJ由用户确认正常；仿真显示几何存在差异，原因待查。** 用户已看过整体比例，5°运动不足以确认微小关节运动、穿插和保持细节。本轮未调查、未改 visual/collision 显示，不归因源OBJ，也不归因均匀盒惯量。它不阻断此小目标设计，但列为**加入构件/相机和正式扫描视点前必须解决的资产显示一致性事项**；未宣称 visual 已验收。

| 证据级别 | 当前结论 |
|---|---|
| 用户接受/既有运行 | explicit-on固定构型基本关节运动与保持 GPT REVIEW PASS；保存的body/joint/初态/碰撞包围盒可作设计依据 |
| 当前源码直接确认 | 最终纯frame零平移/+135°；DiffIK配置/公式/返回值；fixed-base索引规则；隐式执行器位置/速度目标链 |
| 本轮 CPU数学 | 目标offset与换算、FK见证、rank3、单次线性预测、离线见证路径AABB采样 |
| 设计建议 | 4秒参考、λ=.01、2/s命令积分、准入值、2mm/.25°/.01rad/s稳定1秒、8秒/960步和局部代码范围 |
| 必须真实运行验证 | native J shape/参考点及freshness、新外环收敛/静载精度、实际路径contact/AABB、提交速度一致、实际scanner到位与有界退出 |
| 本轮未做 | 实现/测试代码、资产修改/导入、IK controller调用或迭代求解、Isaac/CUDA/GUI/headless/仿真、视觉调查、相机/MRTA/训练、Git写操作/清理 |

真正待审的是**新控制参考层及固定阈值/预算是否按本方案进入实施**。不需要重新选择机器人、底盘/lift、扫描成功条件或目标来源。Jacobian 点语义属于有明确停止规则的首次运行校核，不要求用户凭经验回答；若首次校核失败，停止修正本地 adapter 后再按授权预算决定是否重试。若到位失败需要变更外环增益、PD、目标或物理前提，另行提交证据与方案，不在实现轮自行放宽。

本轮实际检查：读取适用 AGENTS、当前 TASK_PROGRESS/REPORT_INDEX；定向读取上述三个相关历史报告的必要部分及 accepted result；阅读本地 controllers/math/articulation/native tensor API、CR12生成frame与drive源码；核对项目解释器路径，使用已有 NumPy/标准库做有限CPU计算；只读核对HEAD/相关工作区/索引；检查本次新增文档链接与局部差异。公开 PhysX 文档仅用于区分上游语义与本地wrapper未确认项。未导出环境变量，未扫描历史全目录、重验Windows或恢复旧产物。局部监督器文件名搜索更正后继续，未生成新的证据目录。

文档变更仅三项：

1. 本报告 `CR12_SINGLE_TARGET_POSE_EXECUTION_PLAN.md`。
2. [TASK_PROGRESS.md](../../TASK_PROGRESS.md)：同步新收到的基本drive审阅通过、当前设计、视觉待办与未实施边界；不重写历史。
3. [REPORT_INDEX.md](../../REPORT_INDEX.md)：资产/基本drive主题更新接受状态；单机执行主题指向本报告并保留[双视点原评估](../20260928/SINGLE_ROBOT_TWO_VIEWPOINT_IMPLEMENTATION_ASSESSMENT.md)。

**单目标 scanner pose 实施设计已完成，等待 GPT/用户审阅；尚未实施、尚未进行 pose 执行仿真验证。报告交付后停止。**

