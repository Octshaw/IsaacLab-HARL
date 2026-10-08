# CR12 有界OBB精化与大幅关节往返实施报告

执行日期：2026-10-04，Asia/Shanghai（UTC+08:00）。
仓库：`E:\Project\IsaacLab_HARL`；HEAD：`24ecbad7dd1bdcd006399b64bfb757a86b71aeec`。
`T` 表示 `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator`；
`L` 表示 `logs/scan_assignment/20261004_cr12_obb_joint_sweep`，以下相对仓库路径使用这两个缩写。

## 1. 本轮结果

**已实现显式OBB精化模式和独立joint-space往返入口；唯一主运行取得 `MANUAL_JOINT_SWEEP_RUNTIME_PASS`。** 冻结profile为 `j3_visible_roundtrip_v1`、joint_3正向 **20°**，模式 `aabb_then_obb_margin_v1`。

| 关键交付 | 实际结果 |
|---|---|
| 完整往返 | 2520受控physics steps，21.000001095s；外摆、保持、返回、保持全部完成 |
| joint_3实际最大转角 | **+20.797719409°**，step1073，t=8.941667133s |
| scanner实际最大离起点距离 | **0.252206252m（25.22cm）**，step1068，t=8.900000464s |
| 两个保持窗 | 各121个连续post-step样本，跨度各1.000000052s |
| 物理/状态守卫 | clock、joint、contact、geometry、frame、render_clock各2520 PASS |
| GUI/marker | 实际D3D12，native1440×900；9 prototypes/9 instances，2521次更新，`visual_errors=[]` |
| 播放速度 | 21.000001s仿真 / **56.797s墙钟 = 0.369738×**；实际慢于目标1× |
| 退出与预算 | App构造17.359s，全树82.125s；Conda/目标进程自然exit0，全部所属进程退出，无超时/强杀；App **1/3**，受控 **1/2**，无重试 |

幅度来自native关节状态和实际link_6位姿×T_ES，独立CSV复算一致。没有用命令角度、FK端点、marker或累计路程代替实测。

**人工观感仍为 `PENDING_USER_REVIEW`。** marker可见性已有用户正面反馈，但本次大幅运动的连续性、连杆随动、明显穿插和保持观感仍需用户查看。第9节提供一条自动准备private配置的人工命令；本轮没有执行该人工命令或启动第二个App。

原basic drive/formal pose的GPT REVIEW PASS、既有manual/private运行记录和Phase B **COMPLETE / GPT REVIEW PASS / CLOSED**保持。本轮没有写新的GPT REVIEW PASS，也不扩展为IK、全空间、视觉资产或扫描验收。

## 2. 原阻断与几何输入

[上一轮报告](../20261003/CR12_MANUAL_LARGE_JOINT_SWEEP_REPORT.md)的 `PREFLIGHT_BLOCKED` 保持：旧世界AABB规则下，+20°/+15°各201点中分别95/60点被拒绝，首次角度10.6°/10.575°。当时没有App，本次是新授权检查模式及新运行，不回写旧结论。

原首个pair为：

- `/World/CR12/link_4/collisions/link_4_collision/mesh`；
- `/World/CR12/link_6/collisions/scanner_collision/mesh`。

名义仅q3变化、q4/q5/q6为零时，二者相对位姿恒定；世界AABB投影却会随共同旋转重叠。这是精化检查的动机，不是提前删除pair的依据。本轮仍对所有原禁止pair统一检查，每次用新姿态，不缓存永久安全结论。

唯一资产仍为 `T/assets/rokeaCR12/derived/fixed_lift0_v1/usd/cr12_fixed_lift0.usd` 及既有引用层。输入读取既有派生URDF的mass/COM/完整惯量和10份collision OBJ；没有重新导入、修改资产、读取visual重拟合惯量。

10个shape分别保留。以下OBJ位于 `T/assets/rokeaCR12/model/`，scale均为 **(0.001,0.001,0.001)**：

| shape → body | collision OBJ | body-local origin xyz，m / rpy，rad |
|---|---|---|
| agv_collision → agv | scanner_sys_agv_collision.obj | (0,0,0) / 0 |
| elevate_collision → agv | scanner_sys_elevate_collision.obj | (0,0,0.314) / 0 |
| base_link_collision → agv | cr12_base_collision.obj | (0.105,0,1.062) / 0 |
| link_1_collision → link_1 | cr12_link1_collision.obj | 0 / 0 |
| link_2_collision → link_2 | cr12_link2_collision.obj | 0 / 0 |
| link_3_collision → link_3 | cr12_link3_collision.obj | 0 / 0 |
| link_4_collision → link_4 | cr12_link4_collision.obj | 0 / 0 |
| link_5_collision → link_5 | cr12_link5_collision.obj | 0 / 0 |
| link_6_collision → link_6 | cr12_link6_collision.obj | 0 / 0 |
| scanner_collision → link_6 | scanner_sys_scanner_collision.obj | 0 / (0,0,2.356194490192345) |

来源为派生URDF collision段L10/22/34/54/74/94/114/134/154/167。`geometry_body_bounds` 对真实collision顶点先scale、再origin旋转和平移，形成**body-LINK坐标系、米**的局部enclosure；固定组合并已体现在这些origin中。OBB只加body位姿，**不再施加scanner的135°或mesh的0.001缩放**。scanner坐标架T_ES用于测量/显示，与collision已施加的origin不能混算。

每个shape有唯一prim路径和body绑定。离线逐一对照已接受USD读回，最大bounds差 **5.64032234e−8m**；运行时读取本次USD collision点及convexHull设置，逐一核对原源边界，入口再按路径/body/bounds进行1e−6m、rtol=0检查。10个均匹配，没有遗漏scanner。包围盒覆盖这些collision mesh输入及其凸包；不是读取PhysX cooked vertices或对visual外观作验收。

## 3. 新判据：世界AABB粗筛后寻找充分分离证据

`_cr12_collision_refinement.py`使用float64。对body-local bounds构造：

`c_local=(b_min+b_max)/2`，`e=(b_max-b_min)/2`；
`c_world=R_WB c_local+p_WB`；三根OBB轴为R_WB三列。

每个原局部盒B附加**世界轴立方体** `C=[−m,m]³`，`m=0.002m`，检查包络为 `B⊕C`。对单位世界方向n：

`r_box(n)=Σ e_i |n·u_i|`；
`r_margin(n)=m(|n_x|+|n_y|+|n_z|)`；
`gap(n)=|n·(c_B−c_A)|−r_box,A−r_box,B−2m||n||₁`。

双方各有2mm余量，没有只加一次pair margin，也没有把OBB局部半长各加2mm冒充世界扩张。软件余量没有改动物理contact_offset。

固定数值规则在首次路径检查前确定：

- **可靠分离严格要求gap > 1e−6m**。该1µm容差约为当前最大源/USD bounds差的17.7倍；不是负容差，不缩小盒。
- 刚体旋转正交/行列式误差容差1e−6；齐次末行容差1e−12，有限值、正半长、单位、shape/body/transform映射均检查。不静默修复scale/shear或重新正交化。
- 候选方向为A三轴、B三轴及9个叉积；有效轴归一化。叉积范数≤1e−8只跳过该不可靠方向，不能因此放行。
- 世界扩张AABB已有可靠间隔时计入 `aabb_separated`；否则进入精化。有充分投影分离证据时计入 `obb_separated`；未找到则 `OVERLAP_OR_UNRESOLVED` 并拒绝。非法输入为 `INVALID_GEOMETRY` 并拒绝。
- 15方向对带世界余量的包络只提供**充分分离证据**，不是完整zonotope/mesh相交算法。未解不等于证明真实碰撞，`contact_proven=false` 保留。
- 原10 shapes共45组合，保持同body/相邻body的13例外，余32禁止pair全部遍历；没有新增link4/scanner例外。
- ground继续用未扩张移动臂enclosure `min_z < −1e−6m` 拒绝；agv正常地面支撑例外不变。

精化记录包含pair、粗筛gap、轴来源/世界方向、双方余量投影、gap和输入有效性。gap是某一方向的投影分离量，**不是mesh最近距离、物理穿透深度或接触测量**。

## 4. 实现落点与旧行为保护

| 文件（相对仓库） | 本轮改动及关键符号 |
|---|---|
| `scripts/environments/_cr12_collision_refinement.py` | 新增纯CPU模块；`box_from_bounds:64`、`pair_separation:92`、`GeometryGuard:165`、`GeometrySummary:244`、`load_accepted_inputs:278` |
| `scripts/environments/_cr12_manual_joint_sweep.py` | 新增固定profile、解析quintic参考、actual统计/两窗/失败粘性、假时钟可测的节流；`SweepProfile:40`、`SweepPlan:142`、`SweepMonitor:209`、`RealtimePacer:347` |
| `scripts/environments/run_cr12_manual_joint_sweep.py` | 新增独立CLI和实际joint-space执行；`validate_private_path:33`、`parse_args:55`、`finish_sweep_sample:120`、`_run_sweep:138`、`main:344` |
| `scripts/environments/_cr12_runtime_support.py` | 仅`initialize_fixed_cr12_state:565`增加keyword `geometry_check=None`；None仍选原`_check_geometry`，新入口显式传精化回调 |
| `source/isaaclab_tasks/test/test_cr12_collision_refinement.py` | 新增几何风险测试，含当前collision bounds回归和旧默认检查 |
| `source/isaaclab_tasks/test/test_cr12_manual_joint_sweep.py` | 新增轨迹、命名、保持、真实幅度、失败和pacing测试 |
| `source/isaaclab_tasks/test/test_cr12_manual_joint_entry.py` | 新增private/CLI边界、受影响接线和失败CSV保留检查 |
| `L/repro/`三个Python | 离线筛查、复制已接受0–3项private helper、最小适配的owned-process监督器 |

旧`_check_geometry`函数不动，旧formal/basic/manual入口默认行为、轨迹、判据及旧5°限制均不动。新入口没有把20°范围提升为旧入口默认。共享支持层未加入轨迹或pose控制。

新入口复用既有scene/initialization、native状态读取、frame/contact/clock及提交buffer检查；只调用现有pose模块的名称/FK/固定坐标数学，没有DiffIK、Jacobian求解或pose command integrator。生产模块不依赖任何日志目录脚本；private/监督复用只在本任务repro中。

三处策略保持一致：离线完整路径使用新GeometryGuard；运行初始化以实测q_start/root重新检查201点；每次提交前对actual q→量化后q_ref的中点/终点检查；每个post-step使用**实际物理body/link位姿**检查。运行时没有拿参考FK替代actual几何。

## 5. 两候选的完整离线准入与冻结

当前源collision bounds及历史USD读回bounds分别筛查两候选各201点，含两端；每条路径都检查全部32禁止pair。旧AABB对照原样保留。

| 指标（当前源bounds） | +20° | +15° |
|---|---:|---:|
| 采样数 / 所有形状组合 | 201 / 9045 | 201 / 9045 |
| 原例外 / 禁止pair检查 | 2613 / 6432 | 2613 / 6432 |
| AABB可靠分离 | 6337 | 6372 |
| 进入OBB精化且分离 | **95** | **60** |
| 未解 / ground / invalid | **0 / 0 / 0** | **0 / 0 / 0** |
| 旧AABB仍拒绝的采样数 | 95 | 60 |
| 最小所选可靠分离gap | 0.000248625783m | 0.000248625783m |
| 代表pair最小OBB gap | 0.062679350944m | 0.062907222514m |
| scanner名义位移 | 0.230257484m | 0.173077731m |
| 六轴负载估计最高占限值 | joint_3：65.70% | joint_3：51.56% |
| 新判据准入 | PASS | PASS |

负载输入的派生URDF哈希与旧结果一致；按旧模型核对的采样负载逐字段与旧记录一致（1e−12范围）。20°六轴重力+惯性估计峰值为 `(0.013436,19.834859,19.709958,2.310199,4.829613,0.750234)N·m`，对照 `(20,60,30,10,10,5)`，均低于80%。没有重算资产惯量；这些仍是名义采样估计，不是实际动态上界或厂家额定能力证明。

因此首次App前优先冻结 **20°**，没有运行中换成15°。当前运行初态再次201点通过，未另选构型。源名义q3轴为link_2→link_3的+Y；FK scanner起点约(0.105,−0.15,2.888)m，20°端点约(0.331759,−0.15,2.848016)m。这些名义值与第8节实测结果分别记录。

## 6. 固定控制时序与保护

profile `j3_visible_roundtrip_v1`，`MANUAL_JOINT_VISUAL_ONLY=true`；q_out仅在实际q_start的joint_3上加20°，其他五轴position target保持q_start、velocity target=0。每段8s使用 `h=10u³−15u⁴+6u⁵`，解析速度 `(30u²−60u³+30u⁴)(q_b−q_a)/8`。

| 阶段 | 仿真时间 | 执行内容 |
|---|---|---|
| START_HOLD | 0–1s | 初态保持 |
| OUTBOUND | 1–9s | 8s平滑外摆 |
| OUTBOUND_HOLD | 9–11s | 保持；10…11s验收 |
| RETURN | 11–19s | 8s平滑返回 |
| RETURN_HOLD | 19–21s | 保持；20…21s验收 |

一次初始化joint-state写入，root/scanner运行期状态写入为0。每tick：同刻actual→下一参考→float32位置/速度成对提交→write_data_to_sim并核对buffer→唯一physics step→更新native q/dq及实际link位姿→各守卫、marker、必要render→墙钟节流。初始化reset包含2个physics steps，受控2520步另计；没有额外settle或Jacobian刷新步。

固定baseline K=(200,4000,2000,200,1000,150)，D=(20,550,166,12,37,7)，effort=(20,60,30,10,10,5)N·m，actuator速度上限.2rad/s；dt=1/120、render_interval=2、TGS8/2、GPU设置、重力(0,0,−9.81)、fixed-base/lift0/v1及external-forces显式on保持。

manual保护：命令硬限位margin .02rad；Δq/tick≤.00125rad；command速度≤.15rad/s、actual≤.25rad/s；同刻六轴reference误差≤1°；q3相对起点在[−1°,21°]、其他五轴相对起点偏差≤1°；actual硬限位数值容差沿旧1e−3rad。保持窗逐样本native |dq|≤.01rad/s，禁止contact>0.1N停止；root≤1e−4m/rad，fixed frame≤1e−5m/rad。finite、ground和时钟守卫继续有效。

quintic名义峰值速度.081812309rad/s、加速度.031489572rad/s²。实际最大提交位置步增 **.000681772828rad**，不是通过clamp或额外状态写回形成。

## 7. CPU检查、局部修正与实际运行命令

CPU检查：

- 几何 **20/20**：8角点覆盖与独立投影、非零中心/旋转/重排、AABB重叠而OBB分离、必须用cross轴的用例、包含/接触/近边界拒绝、世界L1余量、swap/零margin刚体不变性、非法输入/缺shape/错body、原pair/ground/旧默认。
- trajectory/monitor/pacer **26/26**：名称、单位、2520步、解析速度、往返连续、两窗121点、严格actual>10°/>.10m、返回净位移不替代峰值、失败粘性、假clock。
- entry **13/13**：固定CLI/private转发与拒绝、无运行时调角接口、唯一step及无IK/状态写回接线、失败CSV和首因保留。
- supervisor **110/110断言**：0–3项private适配最小回归、固定CLI、完整完成事实+退出、预算/重试拒绝、四桶geometry覆盖；Job/输出排空/desktop逻辑与已接受版本一致。
- 新/修改Python均语法检查通过。没有重跑旧formal/joint-drive App、全仓测试或Phase B。

CPU阶段修正了一个入口路径拒绝分支（期望目录不存在时改为规范的路径不匹配拒绝），以及两个新测试自身问题（tuple限位索引、AST白名单）。只读审查又加固了统计保存异常不能覆盖原始失败、不能跳过失败CSV行，并用两个针对测试确认。**这些都发生在首App之前，不是runtime重试；没有调整几何公式、margin/tolerance或动作参数。**

实际测试命令均在仓库根执行；轨迹测试使用已核对的同一环境Python直达，其余优先Conda：

~~~powershell
& 'D:\miniconda3\Scripts\conda.exe' run -p 'C:\isaacenvs\isaac45_harl' python -B source/isaaclab_tasks/test/test_cr12_collision_refinement.py
& 'C:\isaacenvs\isaac45_harl\python.exe' -X utf8 source/isaaclab_tasks/test/test_cr12_manual_joint_sweep.py
& 'D:\miniconda3\Scripts\conda.exe' run -p 'C:\isaacenvs\isaac45_harl' python -B -m unittest discover -s source/isaaclab_tasks/test -p test_cr12_manual_joint_entry.py
& 'D:\miniconda3\Scripts\conda.exe' run -p 'C:\isaacenvs\isaac45_harl' python -B logs/scan_assignment/20261004_cr12_obb_joint_sweep/repro/check_obb_sweep_feasibility.py --output logs/scan_assignment/20261004_cr12_obb_joint_sweep/repro/offline_feasibility.json
~~~

以上均exit0；离线输出文件已存在，工具拒绝覆盖。监督器断言为一次性inline CPU检查，摘要保留于repro，未另建长期测试框架。显式py_compile产生的__pycache__为编译缓存。

实际主运行外层命令（历史记录，attempt_01不可重复覆盖）：

~~~powershell
& 'D:\miniconda3\Scripts\conda.exe' run --no-capture-output -p 'C:\isaacenvs\isaac45_harl' python -u logs/scan_assignment/20261004_cr12_obb_joint_sweep/repro/supervise_cr12_obb_joint_sweep.py --attempt-dir 'E:\Project\IsaacLab_HARL\logs\scan_assignment\20261004_cr12_obb_joint_sweep\attempt_01'
~~~

监督器实际生成的目标命令：

~~~powershell
& 'D:\miniconda3\Scripts\conda.exe' run --no-capture-output -p 'C:\isaacenvs\isaac45_harl' python -u scripts/environments/run_cr12_manual_joint_sweep.py --usd-path 'E:\Project\IsaacLab_HARL\source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\assets\rokeaCR12\derived\fixed_lift0_v1\usd\cr12_fixed_lift0.usd' --output-dir 'E:\Project\IsaacLab_HARL\logs\scan_assignment\20261004_cr12_obb_joint_sweep\attempt_01' --device cuda:0 --profile j3_visible_roundtrip_v1 --geometry_mode aabb_then_obb_margin_v1 --view arm-oblique --external-forces-every-iteration on --info '--kit_args=--/app/userConfigPath=E:/Project/IsaacLab_HARL/logs/scan_assignment/20261004_cr12_obb_joint_sweep/attempt_01/private_config/user.config.json'
~~~

解释器实际为 `C:\isaacenvs\isaac45_harl\python.exe`，Python3.10.20、UTF8=1。父进程合并继承环境，只对子进程设PYTHONUTF8=1及HEADLESS/ENABLE_CAMERAS/LIVESTREAM/XR=0；保留已接受Windows helper/pre-App CUDA顺序，helper补入D3D12参数。experience为 `E:\Project\IsaacLab_HARL\apps\isaaclab.python.kit`。实际后端由同次Kit log的DX12/D3D12确认，不只看参数。

## 8. 唯一主运行的完整结果

运行时间 **2026-10-04 11:33:24.241 → 11:34:46.363 +08:00**；Kit原文时间约03:33…03:34，与本机相差8小时。App构造17.359s，全部所属进程82.125s退出，低于180s/360s上限。Conda PID2076、目标PID4992退出码均0。无timeout、强制终止、failure/secondary failure或原生故障证据。

退出前保存了完整工作事实、simulation_stop_returned和app_close_requested；没有 `app_close_returned` 事件，**不声称Python的app.close调用已返回**。自然退出结论来自进程句柄和全所属进程清空。exit0没有覆盖内部失败。

### 8.1 六轴与两个保持窗

下表“最大实际转角”指相对独立保存的q_start的最大绝对变化，非command：

| 轴 | 最大实际转角° | 最大native速度rad/s | 最大同刻跟踪误差° |
|---|---:|---:|---:|
| joint_1 | 0.062380 | 0.006303 | 0.062380 |
| joint_2 | 0.439822 | 0.005080 | 0.439822 |
| joint_3 | **20.797719** | **0.084622** | **0.798191** |
| joint_4 | 0.549449 | 0.009226 | 0.549449 |
| joint_5 | 0.284956 | 0.036534 | 0.284956 |
| joint_6 | 0.306891 | 0.023519 | 0.306891 |

q3实际超过命令20°，但仍在批准[−1°,21°]内，最大reference误差0.798191°<1°；其余五轴目标保持不变，实际存在有限保持偏差，不能写成五轴完全不动。没有以formal pose精度标准宣称这些误差通过正式定位。

| 保持窗 | 样本step | 连续数 / span | 全轴最大误差° | 全轴最大native速度绝对值，rad/s |
|---|---|---|---:|---:|
| 外摆末秒 | 1200…1320 | 121 / 1.000000052s | 0.797002 | 1.2979708e−5 |
| 返回末秒 | 2400…2520 | 121 / 1.000000052s | 0.126995 | 1.5118674e−7 |

实测scanner起点 `(0.104999989,−0.149999842,2.887999058)m`；
外摆保持结束step1320的位置 `(0.352977127,−0.149788797,2.842217445)m`；
返回结束step2520为 `(0.107825123,−0.149999946,2.887995481)m`，q3仍约 **+0.123200°**。返回净位移 **2.825136mm**，并非精确回零；它不替代最大离起点 **252.206252mm**。

独立按CSV实际q/actual_p复算峰值、发生step/time和2520行连续性均一致。其他五轴每行command保持起点、dq_command=0，位置/速度成对提交和buffer核对各2520次。

### 8.2 几何与其他物理守卫

| 运行检查位置 | checks | 全组合 / 原例外 / 禁pair | AABB分离 | OBB精化且分离 |
|---|---:|---|---:|---:|
| 初始化actual | 1 | 45 / 13 / 32 | 32 | 0 |
| 实际初态完整路径 | 201 | 9045 / 2613 / 6432 | 6337 | 95 |
| 提交前中点/终点 | 5040 | 226800 / 65520 / 161280 | 158910 | 2370 |
| post-step实际body位姿 | 2520 | 113400 / 32760 / 80640 | **79420** | **1220** |

四处均failed/invalid/unresolved/ground failures=0、输入有效；没有只看首个pair就放行。实际q4/q5/q6偏差后仍重新计算，未使用名义共转结论缓存。

最小“所选分离证据gap”分别为：实态初始路径 **0.000248619888m**、提交前 **0.000097634078m**、actual **0.000028556793m**。该统计混合了粗筛选定世界轴与精化选定轴，不是最小物理间距。

actual的最小代表OBB gap为 **0.062328293264m**，仍是link4/scanner pair；轴来源B2，世界方向 **(0.366847187046,0.000348186541,0.930281151116)**。同记录原AABB gap **−0.067196795567m**，双方世界余量投影 **0.005189906099m**；15方向均有效。名义路径对应记录12方向有效、3近平行cross跳过。这个差异由本次actual姿态参与精化，未把实际姿态强改成理想共转。

七个contact sensor各2520次强制更新，原禁配对和移动臂对ground过滤目标保留，最大禁止接触读值 **0N**。actual未扩张臂enclosure最低z **1.239998763731m**。六类guard各2520 PASS；root最大平移/旋转漂移均0。四个fixed frame最终误差均(0,0)，全程2520次检查未超过阈值；最终零误差本身不单独证明全程误差全零。

### 8.3 节流、窗口与marker

实际render1260次、pacer调用2520次；节流只允许sleep，没有新增physics/render/app.update或改dt。全程工作已慢于截止时刻，累计sleep=0；因此 **0.369738×是本机实际表现，不是1×已实现性能保证**。用户会看到约57秒的受控序列，而非几秒快速播完。

真实source窗口三值为−1/−1/true，本次准备差异3项到1440/900/false；helper也支持未来0–3项实际差异，不要求永远恰好3项。source准备前/运行前/运行后的size=114100、mtime及SHA256相同，语义diff0。Kit实际加载当次private，native窗口1440×900，实际D3D12。

private由84107字节变为114104字节，hash和mtime改变，但语义diff0，属于Kit格式写回；不把输出hash变化说成source污染，也不把写回后的文件当作原输入。

marker设计、尺寸、颜色、球和品红线不变；实际9 prototypes/9 instances、visible=true、无物理schema，更新2521次。arm-oblique固定视角覆盖初态与外摆参考，不跟随末端。actual为实测scanner，固定浅色坐标架/黄球为**外摆FK参考端点**；回程品红线重新变长是正常图例，不移动参考点制造贴合。

日志存在预App模块加载提示、RTX TLAS warning以及 `/CR12PoseDebug.proto7_mesh_id0` 未populated的Hydra warning，另有扩展/deprecation等启动warning；未修改这些系统问题。其与本轮实际marker读回、持续更新及自然退出并列记录，不写“无warning”或代替人眼判断。

## 9. 人工查看命令（本次未执行）

以下为**一条完整PowerShell操作块**，在本机使用已验证的新joint-sweep入口。它自动创建新manual目录、复制真实source到新private、只处理三个窗口setting，再启动固定20°/精化模式/arm-oblique/默认墙钟节流：

~~~powershell
Set-Location -LiteralPath 'E:\Project\IsaacLab_HARL'
$cr12ManualDir = Join-Path 'logs/scan_assignment/20261004_cr12_obb_joint_sweep' ('manual_' + (Get-Date -Format 'yyyyMMdd_HHmmss_fff'))
& 'D:\miniconda3\Scripts\conda.exe' run --no-capture-output -p 'C:\isaacenvs\isaac45_harl' python -X utf8 -u 'logs/scan_assignment/20261004_cr12_obb_joint_sweep/repro/supervise_cr12_obb_joint_sweep.py' --manual-check --attempt-dir $cr12ManualDir
Write-Host "Exit code: $LASTEXITCODE; output: $cr12ManualDir"
~~~

此命令与自动主运行使用**相同private准备、owned-process Job、180s App/360s全树上限和完整结果检查**。区别是显式 `--manual-check`、新时间戳目录及 `USER_MANUAL` 标记；每次仅一个App、不自动重试。它不继续消耗已结束的Codex自动尝试序列，也不授权Codex自行调用。没有另开不受监督的启动路线。

`-X utf8`在解释器创建时生效；子进程环境由监督器合并，不改持久变量。若private准备、源保护或冻结源码检查失败，入口不会启动，也不回退真实source；后续若修改实现，应重新评估检查，而非绕过冻结校验。

观察重点：q3是否明显正向外摆并平滑返回；下游连杆是否正确随动；有无跳变、明显穿插、穿地；两端保持是否抖动；marker是否对应真实机械臂。旧marker已有正面反馈，本轮仍请用户确认大幅运动观感。Codex不能代用户宣布“动作自然、没有视觉穿插”。

## 10. 范围、文档及停止条件

已完成本轮授权的精化、离线准入、独立joint-space实现、一次真实GUI验证和人工命令交接。运行后33个本轮冻结输入与运行前一致。新增本文，并小范围更新TASK_PROGRESS/REPORT_INDEX；旧AABB阻断及历史失败报告原样保留。

交付检查：本文21个相对文件链接均存在，4个PowerShell命令块仅做语法解析、未重新执行；表格分隔符已修正。交接与导航仅更新本轮状态、当前边界和报告链接，Phase B关闭状态保留；定向差异检查通过。当天报告目录仅新增本文，没有Python、JSON或日志混放。

未修改原始/派生URDF、USD、mesh、惯量、collision，未更改PD/effort/solver/dt/重力/摩擦/armature；未修改旧入口默认、真实user.config、共享配置、驱动、installed packages；无Git写操作或历史清理。既有dirty worktree和暂存历史ZIP删除保留。

这不是任意路径、任意关节或连续时间无碰撞证明；本轮证据限固定v1、fixed/lift0、20°、当前速度/时序、已列离散检查和实际接触监测。没有新增IK能力、相机、构件、双视点、MRTA或训练。源OBJ用户确认正常，仿真“封闭/填充”显示差异仍未修复；几何守卫通过不能代替visual一致性审查。

**停止，等待GPT/用户审阅与大幅动作人工反馈。** 不用剩余App预算追加运行，不将OBB自动推广到旧入口，不扩大角度或换轴，不自动进入后续扫描实现。

## 11. 辅助证据对应表

`logs/`下材料及部分实现仍为本机未提交产物，受现有忽略/未跟踪状态影响，不能承诺新checkout自动具有；未制作ZIP、ledger或全仓hash清单。主报告给出完整数字和命令，下面只列核验入口。

| 结论/检查 | 文件位置 | 关键字段/符号 | 限制 |
|---|---|---|---|
| 精化公式与输入 | [collision模块](../../../../../../../../scripts/environments/_cr12_collision_refinement.py) | `pair_separation`、`GeometryGuard`、`load_accepted_inputs` | 充分分离，不是完整mesh求交 |
| 固定轨迹/统计/节流 | [sweep模块](../../../../../../../../scripts/environments/_cr12_manual_joint_sweep.py) | `PROFILE`、`SweepMonitor`、`RealtimePacer` | manual固定profile |
| 实际接线 | [运行入口](../../../../../../../../scripts/environments/run_cr12_manual_joint_sweep.py)；[共享支持](../../../../../../../../scripts/environments/_cr12_runtime_support.py) | `_run_sweep`；`initialize_fixed_cr12_state` | 旧默认未提升 |
| CPU测试 | [几何](../../../../../../../../source/isaaclab_tasks/test/test_cr12_collision_refinement.py)、[轨迹](../../../../../../../../source/isaaclab_tasks/test/test_cr12_manual_joint_sweep.py)、[入口](../../../../../../../../source/isaaclab_tasks/test/test_cr12_manual_joint_entry.py) | 20/26/13项 | 不替代真实运行 |
| 全路径准入 | [offline_feasibility.json](../../../../../../../../logs/scan_assignment/20261004_cr12_obb_joint_sweep/repro/offline_feasibility.json)、[复算工具](../../../../../../../../logs/scan_assignment/20261004_cr12_obb_joint_sweep/repro/check_obb_sweep_feasibility.py) | `candidates`、selected20、两个来源 | 离线名义路径 |
| 监督准备 | [supervisor](../../../../../../../../logs/scan_assignment/20261004_cr12_obb_joint_sweep/repro/supervise_cr12_obb_joint_sweep.py)、[private helper](../../../../../../../../logs/scan_assignment/20261004_cr12_obb_joint_sweep/repro/prepare_private_user_config.py)、[CPU摘要](../../../../../../../../logs/scan_assignment/20261004_cr12_obb_joint_sweep/repro/supervisor_cpu_checks.txt) | `build_command/completion/assess_history`、110断言 | 局部复现工具，不被生产模块import |
| 实际启动命令 | [command.json](../../../../../../../../logs/scan_assignment/20261004_cr12_obb_joint_sweep/attempt_01/command.json) | argv/cwd/env overrides/time | 当次自动运行 |
| 实际结果 | [result.json](../../../../../../../../logs/scan_assignment/20261004_cr12_obb_joint_sweep/attempt_01/result.json) | geometry_summary、monitor_summary、sweep_summary、pacing | 内部完成，须结合退出 |
| native/实际位姿CSV | [joint_scanner_trace.csv](../../../../../../../../logs/scan_assignment/20261004_cr12_obb_joint_sweep/attempt_01/joint_scanner_trace.csv) | 2520行q/dq/actual_p、command、guard | 一份必要轨迹，无逐pair矩阵dump |
| 配置保护/退出 | [config_runtime_summary.json](../../../../../../../../logs/scan_assignment/20261004_cr12_obb_joint_sweep/attempt_01/config_runtime_summary.json)、[supervisor_result.json](../../../../../../../../logs/scan_assignment/20261004_cr12_obb_joint_sweep/attempt_01/supervisor_result.json) | source unchanged/private diff0、layers、exits/budget | 不是仅看exit0 |
| 同次日志 | [console.log](../../../../../../../../logs/scan_assignment/20261004_cr12_obb_joint_sweep/attempt_01/console.log)、[Kit log](../../../../../../../../logs/scan_assignment/20261004_cr12_obb_joint_sweep/attempt_01/kit_20261004_113327.log) | Kit L2682/3460 D3D12、L3343窗口、L6938 marker warning | 保留warning，不作视觉代验 |
| 已接受启动前置 | [private单因素报告](../20261003/CR12_PRIVATE_USER_CONFIG_SINGLE_FACTOR_REPORT.md) | private/窗口/监督基础 | 旧运行不计本次预算 |
