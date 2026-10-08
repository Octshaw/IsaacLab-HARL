# CR12 manual-only 大幅关节往返观察报告

执行日期：2026-10-03（Asia/Shanghai，UTC+08:00）。仓库：`E:\Project\IsaacLab_HARL`；HEAD：`24ecbad7dd1bdcd006399b64bfb757a86b71aeec`。

本文以 `T = source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator`、`L = logs/scan_assignment/20261003_cr12_manual_joint_sweep` 表示仓库内路径。

## 1. 结论与停止位置

**本轮结果：`PREFLIGHT_BLOCKED`。+20°、+15°均未通过原几何守卫；未选定角度、未冻结可执行 profile，App 0/3、受控运动 0/2。大幅往返未实施、未运行、未完成。**

用户希望通过 joint-space 参考直接指定 `joint_3` 明显运动，避免再次由 DiffIK 将 scanner pose 目标分配成难以观察的小动作。本轮按此方向完成当前模型的运动学、路径和六轴负载复算，发现两候选均在约10.6°时触发非相邻形状世界 AABB 重叠。负载估计和名义位移满足候选要求，但不能抵消几何阻断。

附件明确要求：“若两个候选都不适合，说明具体路径/负载阻断，不要继续生成一个达不到用户可视要求的‘小动作成功’。”因此停在首次 App 之前；没有换轴、换方向、减成≤10°，也没有修改保护来运行。这是具体离线阻断结果，不是 runtime 失败。

**用户最新反馈：marker可见性已有用户正面反馈，但机械臂运动幅度仍不足，运动连续性/穿插等人工判断尚未完成。** 旧约32mm/3° scanner-pose 动作不足以完成本次观察。本轮没有新的人工运动结果，不将该反馈扩大为全部视觉资产通过。

原基本 joint drive、formal 单目标 scanner pose 的 **GPT REVIEW PASS** 保持；既有 manual pose/private 配置运行记录保持；Phase B **COMPLETE / GPT REVIEW PASS / CLOSED** 保持。本轮不产生新的 IK、全空间、扫描或实体安全通过结论。

## 2. 输入与源码依据

唯一后续运行候选资产仍是 `T/assets/rokeaCR12/derived/fixed_lift0_v1/usd/cr12_fixed_lift0.usd` 及既有引用层。本轮没有加载 USD runtime、导入、重导出或重算惯性。

离线输入为当前 `T/assets/rokeaCR12/derived/fixed_lift0_v1/cr12_fixed_lift0.urdf` 的已接受质量、COM、完整惯量，以及它引用的10份 collision OBJ；不读取全部 visual mesh 重新做资产审计。另取已接受 external-forces 运行 `logs/scan_assignment/20260930_cr12_external_forces/attempt_02/result.json` 的 `usd_readback.colliders` 作为实际 USD 读回边界的历史来源。

| 直接来源 | 关键符号/位置 | 本次用途与边界 |
|---|---|---|
| 派生 URDF，L179–225 | 六个 revolute joints；`joint_3` 在 L195–201 | 当前名称、父子、轴、硬限位；没有当成当前物理状态 |
| `scripts/environments/_cr12_pose_control.py`，L22–23、L177–184、L331–380 | `JOINT_NAMES/JOINT_LIMITS`、`T_ES`、`KinematicModel` | 只调用名称映射、FK、矩阵变换；未调用 DiffIK/Jacobian 求解/command integrator |
| `scripts/environments/_cr12_asset_math.py`，L248起 | `geometry_body_bounds` | 对实际 collision 顶点施加 scale/origin 后求 body-local enclosure；没有调用惯性生成流程 |
| `scripts/environments/_cr12_runtime_support.py`，L286–315 | `_check_geometry` | 原世界 AABB、2mm 扩张、非相邻 pair 和 ground 规则原样复用 |
| 同上，L266、347、411、430、565起 | frame/contact、提交读回、场景与初始化 | 只读确认可复用边界，本轮未执行这些 runtime 分支 |
| `source/isaaclab_assets/isaaclab_assets/robots/rokea_cr12.py`，L19–29、L60–80 | baseline、初态、`ImplicitActuatorCfg` | 只读源码；未导入 Isaac 配置模块 |

当前10份 collision bounds 与历史 USD 读回逐一按 body/bounds 唯一匹配，最大坐标差 **5.64032234×10⁻⁸m**；两种边界来源分别复算均得相同失败计数和首次 pair。派生 URDF 内容哈希与已接受记录一致。另定向核对既有20个源码/测试/v1文件与前一任务留存快照一致；这不是全仓库或全资产哈希审计。未跟踪资产和既有 dirty worktree 均保留。

读取的前置报告为 [private 配置单因素报告](CR12_PRIVATE_USER_CONFIG_SINGLE_FACTOR_REPORT.md)、[正式 pose 实施报告](../../202609/20260930/CR12_SINGLE_TARGET_POSE_EXECUTION_IMPLEMENTATION_REPORT.md)、[基本驱动计划](../../202609/20260929/CR12_DERIVED_ASSET_AND_JOINT_DRIVE_PLAN.md)及[实施报告](../../202609/20260929/CR12_DERIVED_ASSET_AND_JOINT_DRIVE_IMPLEMENTATION_REPORT.md)。这些是已接受边界和输入来源，没有重跑其验收。

## 3. 两个候选的具体离线结果

### 3.1 名称、方向、坐标与硬限位

`joint_3` 是 `link_2 → link_3` 的 revolute 关节，局部轴 `(0,1,0)`，origin `(0,0,0.76)m`。按名称 `JOINT_NAMES.index("joint_3")` 定位，不以未知原生数组的第三项代替名称映射。模型构造核对六轴名称、父子、origin/rpy/axis。

采用已接受名义初态：六轴零位，root 平移 `(0,0,0.053)m`、旋转 I；不是本轮实测初态。`T_ES` 零平移、绕局部 Z 旋转135°，scanner 原点与 link_6 原点重合，坐标架方向不同。

此初态中 joint_3 世界轴为 +Y、轴原点 `(0.105,0,2.225)m`；scanner 起点 **`(0.105,-0.150,2.888)m`**。绕轴半径为 `0.54+0.123=0.663m`，正向运动使 scanner 向世界 +X、−Z 移动。

| 指标 | joint_3 +20° | joint_3 +15° |
|---|---:|---:|
| FK scanner 终点 (m) | (0.331759355, −0.150, 2.848016208) | (0.276597027, −0.150, 2.865408823) |
| 名义最大离起点距离 (m) | **0.230257484** | **0.173077731** |
| scanner 姿态旋转量 | 20° | 15° |
| 全路径/全轴最小硬限位裕量 (rad) | 2.705234150 | 2.792500612 |
| 再扣命令0.02rad保护后的裕量 | 2.685234150 | 2.772500612 |
| 8s quintic 峰值速度 (rad/s) | 0.081812309 | 0.061359232 |
| 峰值加速度 (rad/s²) | 0.031489572 | 0.023617179 |
| 由峰值速度得到的每1/120s参考变化上界 (rad) | 0.000681769 | 0.000511327 |

硬限位为 joint_2 ±2.9671rad，其余五轴 ±3.0543rad，与当前 URDF 对照一致。其他五轴名义零位，joint_3 单调正向，因此最小裕量出现在外摆端点。以上只是参考路径/FK结果，**不是 native q 或真实 scanner excursion**。

### 3.2 原几何守卫：两候选均被阻断

每条往程线段均采 **201点，含两端**：20°步距0.1°；15°步距0.075°。以当前 collision 顶点形成的 enclosure 和历史 USD enclosure 各跑一遍原 `_check_geometry`；ground 和 pair 规则不变。返回参考访问相同构型逆序，因此名义上遇到相同阻断；不能据此声称真实返回路径与往程相同。

| 指标 | +20° | +15° |
|---|---:|---:|
| 失败采样数/总数 | **95/201** | **60/201** |
| 首个失败，采样从0计 | 106，**10.600°** | 141，**10.575°** |
| 最后一个通过采样角度 | 10.500° | 10.500° |
| 最低机械臂原始 enclosure Z (m) | 1.239999229 | 1.239999229 |
| 所有受检 pair/采样最小带符号轴向间隔 (m) | −0.0574370874 | −0.0271589753 |
| 起点/终点 | 起点通过，终点失败 | 起点通过，终点失败 |

带符号轴向间隔定义为，对每个经2mm扩张的 pair 取各轴分离量的最大值，再对所有 pair/采样取最小值；负数表示三轴投影重叠，**不是 mesh 最短距离或物理穿透深度**。最低 Z 不包含正常地面支撑的 agv；原 ground 判据是 arm 原始 enclosure 不低于 −1e−6m。

两候选首个失败均为：

- `/World/CR12/link_4/collisions/link_4_collision/mesh`
- `/World/CR12/link_6/collisions/scanner_collision/mesh`

原检查跳过同 body 和相邻 body；link_4、link_6 相隔两个 body 索引，不属于例外。两边各扩张0.002m后，三轴交集宽度同时严格大于0即失败。当前 source bounds 的具体数值：

| q3角度 | X重叠 (m) | Y重叠 (m) | Z重叠 (m) | 判断 |
|---|---:|---:|---:|---|
| 0° | 约0.099414 | 约0.143041 | **−0.063806202** | Z仍分离，通过 |
| 10.575° | 0.085349143 | 0.143041126 | **0.000208423** | 15°路径首失败 |
| 10.600° | 约0.085312 | 0.143041126 | **0.000360773** | 20°路径首失败 |
| 15° | 0.078612976 | 0.143041126 | **0.027158975** | 终点失败 |
| 20° | 约0.070468 | 0.143041126 | **0.057437087** | 终点失败 |

例如10.6°时，扩张后的 link4 Z范围为 `[2.409898269376,2.822693731582]m`，scanner 为 `[2.822332958135,3.263808110239]m`，因此 Z交集约0.361mm，X/Y也重叠。

**解释与限制：** q3是二者共同上游，q4/q5/q6保持零位时，`inv(T_W_link4) × T_W_link6` 全程保持旋转 I、平移 `(0,-0.15,0.123)m`；两候选各201点的矩阵最大变化 **8.88×10⁻¹⁶**。因此，在这条名义路径中二者相对几何没有变化，新增重叠有明确的世界轴对齐投影保守性解释。原异常本身也标记 `contact_proven=false`。

这说明不能把本结果写成“已发生 PhysX 接触/机器人真实穿模”。但原守卫确实会拒绝这条参考路径，本轮没有权限将这类失败改为通过或直接豁免该 pair。离散201点也不是连续碰撞证明；未以实际姿态、跟踪误差或真实初态执行任何检查。

### 3.3 六轴负载复算

只读取已接受派生 mass/COM/full inertia；这些仍是首版仿真近似，不是厂家真值。未重新拟合或生成质量属性。重力补偿矩按每轴下游刚体累加：

`τ_g,j = Σ a_j · [(p_COM − o_j) × m(0,0,+9.81)]`。

仅q3运动时，令 `r3 = p_COM−o3`、轴为 `a3`：

`a_COM = α(a3×r3) + ω²[a3×(a3×r3)]`；
转动惯性扳手为 `I_W a3 α + (a3×I_W a3)ω²`，平动力再以各轴力臂投影。所有下游刚体贡献累加到其上游关节，包含joint_1/2及腕部保持负载，非只检查joint_3。

`h(u)=10u³−15u⁴+6u⁵`，`max h′=1.875`、`max |h″|=10/√3`，8s运动得到上表速度/加速度。每个名义构型使用 `|τ_g|+|Cα|α_max+|Cω²|ω_max²`，再对201点取每轴峰值。它是给定刚体参考模型的**采样估计包络**，不是完整逆动力学验证或连续严格上界；不含真实PD跟踪、接触、求解器或控制瞬态。分项峰值不必发生在同一点，故合计峰值不一定等于两个独立分项峰值之和。

**+20°，单位 N·m：**

| 轴 | 重力绝对峰值 | 惯性项估计峰值 | 同点合计后峰值 | 当前effort限值 | 占比 | 剩余裕量 |
|---|---:|---:|---:|---:|---:|---:|
| joint_1 | 0.000000 | 0.013436 | 0.013436 | 20 | 0.067% | 19.986564 |
| joint_2 | 19.600222 | 0.236752 | 19.834859 | 60 | 33.058% | 40.165141 |
| joint_3 | 19.601357 | 0.108602 | 19.709958 | 30 | **65.700%** | 10.290042 |
| joint_4 | 2.296882 | 0.013317 | 2.310199 | 10 | 23.102% | 7.689801 |
| joint_5 | 4.804222 | 0.025391 | 4.829613 | 10 | 48.296% | 5.170387 |
| joint_6 | 0.744110 | 0.006125 | 0.750234 | 5 | 15.005% | 4.249766 |

**+15°，单位 N·m：**

| 轴 | 重力绝对峰值 | 惯性项估计峰值 | 同点合计后峰值 | 当前effort限值 | 占比 | 剩余裕量 |
|---|---:|---:|---:|---:|---:|---:|
| joint_1 | 0.000000 | 0.009981 | 0.009981 | 20 | 0.050% | 19.990019 |
| joint_2 | 15.386019 | 0.176651 | 15.561657 | 60 | 25.936% | 44.438343 |
| joint_3 | 15.387154 | 0.081451 | 15.468605 | 30 | **51.562%** | 14.531395 |
| joint_4 | 1.738134 | 0.009974 | 1.748108 | 10 | 17.481% | 8.251892 |
| joint_5 | 4.189835 | 0.018893 | 4.208729 | 10 | 42.087% | 5.791271 |
| joint_6 | 0.563095 | 0.004565 | 0.567660 | 5 | 11.353% | 4.432340 |

两者均低于建议80%限值；20°最紧的是joint_3，距离80%限值24N·m还有4.290042N·m。这里比较的是配置 `effort_limit_sim=(20,60,30,10,10,5)`，不是URDF中旧的300N·m字段。**负载不是此次停止原因，也不是实际保持能力已获验证。**

## 4. 尚未落地的固定执行契约

以下是本轮授权要求的记录，**不是已实现/已冻结/已运行的 profile**。原先拟定名称 `j3_visible_roundtrip_v1` 和 `MANUAL_JOINT_VISUAL_ONLY=true` 未进入生产入口。

| 阶段 | 仿真时间 | 要求 |
|---|---|---|
| START_HOLD | 0–1s | q_start保持 |
| OUTBOUND | 1–9s | 8s quintic；q3正向外摆 |
| OUTBOUND_HOLD | 9–11s | 末1秒10…11s保持检查 |
| RETURN | 11–19s | 同参考路径反向8s |
| RETURN_HOLD | 19–21s | 末1秒20…21s保持检查 |

正常预算21s、2520受控physics steps，初始化另计；没有提前终止的“外摆成功”。baseline ImplicitActuator、PD、effort、velocity_limit_sim=.2、dt=1/120、render_interval=2、TGS8/2、external-forces显式on、fixed/lift0/v1均须保持。

实际实现仍须按名称索引，除q3外五轴position保持q_start/velocity=0；quintic位置与解析速度成对按实际提交dtype记录、读回buffer、每tick一次physics。初始化后禁止写joint/root状态、teleport或独立移动scanner。本轮未执行以上运动流程，也没有用FK替代actual。

manual专属保护仍为：命令硬限位margin .02rad，Δq/tick≤.00125rad，命令速度≤.15rad/s、actual速度≤.25rad/s；六轴actual相对同刻reference误差≤1°，q3相对起点范围[−1°,选定角+1°]，其余五轴偏差≤1°。两保持窗口各需≥121个连续含端点post-step样本、跨度约1s、误差≤1°且native |dq|≤.01rad/s。原contact .1N、几何/ground、root1e−4m/rad、fixed frame1e−5m/rad和clock/render检查不变；旧pose 5°信任域及旧joint-drive 5°/720步规则均未修改。

近实时方案仍应只在physics/必要render完成后按monotonic期限sleep，控制时间用simulation time；不追加step/render/update、不跳步或改dt。由于无新入口，本轮没有假clock/新轨迹测试，也没有实际墙钟播放比例。

marker设计未改：RGB轴/球/品红连线与尺寸、固定arm-oblique复用。未来外摆参考frame应固定表示q_out的FK端点，actual来自真实link_6×T_ES，回程品红线增长是预期；这些行为本轮没有新runtime证据。

## 5. 本轮实际改动与CPU检查

未创建拟议的生产入口 `scripts/environments/run_cr12_manual_joint_sweep.py`、控制模块 `_cr12_manual_joint_sweep.py` 或可复用测试 `source/isaaclab_tasks/test/test_cr12_manual_joint_sweep.py`；未改任何旧driver、formal/manual pose、marker、Windows helper、机器人配置或资产。

只保留两个任务局部辅助脚本及紧凑输出，均在 `L/repro/`：

1. `check_joint_sweep_feasibility.py`：只读URDF/collision/historical readback，直接复用原几何守卫，计算两候选与六轴负载；保存 `offline_feasibility.json`。未保存402点逐步raw dump，只保留汇总、首次/终点和关键包围盒。
2. `prepare_private_user_config.py`：从前一任务工具作必要幂等适配；`patched_tree / validate_allowed_changes` 允许真实源三个值到1440/900/false产生 **0–3项**差异，不再要求原值必须−1/−1/true。其余语义不变、严格JSON类型、拒绝覆盖输出、source只读。尚未接入新入口/监督器，未用真实source生成private；`supervise_cr12_manual_joint_sweep.py` 未创建。

Private helper **67/67 CPU检查通过**：0/1/2/3差异、幂等、类型错误、额外字段变化拒绝、duplicate/NaN拒绝、合成文件字节复制/hash/BOM、source bytes/hash/mtime不变、拒覆盖、无效输入不创建output/parent。结果在 `cpu_checks.txt`。仅合成fixture，fixture由该测试自行清理；没有读写真实个人配置。新helper语法检查通过。离线脚本语法检查及一次CPU执行退出0；**退出0表示复算程序完成，JSON结论仍是PREFLIGHT_BLOCKED**。

工作目录均为 `E:\Project\IsaacLab_HARL`，实际解释器已先核对为 `C:\isaacenvs\isaac45_harl\python.exe`，Python3.10.20、UTF8=1。离线文件实际执行命令：

```powershell
& 'D:\miniconda3\Scripts\conda.exe' run -p 'C:\isaacenvs\isaac45_harl' python -B -m py_compile logs/scan_assignment/20261003_cr12_manual_joint_sweep/repro/check_joint_sweep_feasibility.py

& 'D:\miniconda3\Scripts\conda.exe' run -p 'C:\isaacenvs\isaac45_harl' python -B logs/scan_assignment/20261003_cr12_manual_joint_sweep/repro/check_joint_sweep_feasibility.py --output logs/scan_assignment/20261003_cr12_manual_joint_sweep/repro/offline_feasibility.json
```

这是已执行的CPU命令记录，不是GUI命令；输出文件现已存在，脚本会拒绝覆盖。Explicit `py_compile` 会生成 `repro/__pycache__/check_joint_sweep_feasibility.cpython-310.pyc`，即使带 `-B`；这是编译缓存，不是额外实现或报告。Helper检查用一次性inline CPU断言与合成fixture，未保存第二套长期测试框架。另有独立inline FK/201点复算及公式审查，结果一致，没有额外App。

## 6. 运行、真实幅度与人工交付状态

| 独立交付项 | 本轮状态 |
|---|---|
| 运行/实际物理、contact、actual-AABB、frame/root/clock | **NOT_RUN**；仅名义路径几何阻断 |
| 完整往返/外摆和返回保持 | **NOT_RUN / 未完成** |
| 六轴实际最大角度、速度、跟踪误差 | **NOT_RUN**，无native样本 |
| joint_3实际最大转角/正向转角、发生step/time | **NOT_RUN** |
| scanner实际最大离起点距离、发生step/time | **NOT_RUN** |
| 外摆/返回端点实际状态、121点保持窗口 | **NOT_RUN** |
| 受控仿真时长/对应墙钟/播放比例 | **未产生受控循环**；不填“21秒已完成” |
| 新marker/窗口状态 | **NOT_RUN**；旧marker有用户正面反馈 |
| 新private加载与真实source App前后保护 | **NOT_RUN / 不适用**；无App，无真实private准备 |
| 新运动人工观感 | **PENDING_USER_REVIEW**，当前尚无可观察的大幅运行 |
| App次数 / 进入受控次数 / runtime重试 | **0/3 / 0/2 / 0** |

没有native GPU/CUDA错误、启动失败、运行退出码或超时可供本轮判断；因为没有启动进程。未创建 `attempt_01`、joint/scanner CSV、Kit日志或虚构完成回执；未以headless/CPU simulation代验，也未运行旧formal/joint-drive/Phase B。

**本轮不提供、也不推荐人工GUI执行命令。** 用户要求只有runtime完成、实际>10°且>0.10m并且marker可运行后才推荐；这三个前提均未取得本轮证据，新入口也不存在。旧private报告中的小动作命令不能当成本轮大幅观察入口。

未来幅度仍必须由native q和实际物理link_6×T_ES相对实际起点取最大excursion；不能用本报告0.2303/0.1731m的FK、command、marker、累计路程或往返最终净位移代替。当前不标记 `VISIBLE_AMPLITUDE_NOT_MET`（没有实际运行可测），更不标记 `MANUAL_JOINT_SWEEP_RUNTIME_PASS`。

## 7. 下一步的具体审阅点

建议先审阅**保守世界AABB守卫是否需要有界精化**这一点。已有证据已把问题定位到具体pair、具体角度和投影方式，无需重查Windows启动、改PD或引入通用规划器。

若另行授权，可针对该pair核对定向包围盒/实际collision形状分离，研究让保守粗筛重叠进入更精确的几何检查，同时保留原contact offset、禁止pair、真实contact、ground及其他守卫。**本轮尚未完成该精化，也未证明应采取哪种实现。** 不能简单删除link4/scanner pair：真实跟踪误差和其他构型会改变相对位姿，当前名义共转不等于永久允许接触。

在审阅并决定处理方式之前，不继续实现/运行joint sweep，不用15°重试规避相同阻断，不降低可视幅度要求。后续如重新获得可运行路径，还需在实际初始化q_start/root后、第一条运动命令前复核；不适用则SETUP失败，不能在线另选目标。

源OBJ用户确认正常、仿真显示封闭/填充差异仍待查；本轮不修mesh、visibility、purpose、collision表示或材质。相机、双视点、构件和MRTA接入未开展。**交付后停止，等待GPT/用户审阅；本报告不自动授权守卫修改或下一次App。**

## 8. 文档、范围与辅助证据对应表

新增本文；小范围更新 `AgentRead/TASK_PROGRESS.md`、`AgentRead/REPORT_INDEX.md`，记录本轮阻断、0App、最新marker反馈及下一步。没有重写历史报告或新建大幅交接归档；原已接受状态和历史FAIL保持。

收尾核对本文12个相对链接与两处新报告导航均可达；新增报告无行尾空白，TASK_PROGRESS定向 `git diff --check` 无差错（仅已有LF/CRLF提示）。Git索引仍只有进入本轮前已存在的历史ZIP删除，未作Git写操作。

本轮未改生产代码/测试/资产/惯量/PD/solver/dt/effort、真实user.config、驱动、依赖或共享设置；未启动Isaac/CUDA/仿真/训练，未执行Git写操作或历史清理。既有staged删除和untracked文件保留。源配置在本轮没有被任务写入；没有把旧任务hash检查当作本轮App前后证据。

`logs/` 下4个证据/辅助源文件与编译缓存受现有忽略规则影响，**仅本机可取，不随新checkout自动出现**；未生成ZIP、ledger、重复日志包或全仓库清单。正文已给关键数字及结论，核验算法/原始字段时再读取下列最小材料。

| 结论/检查项 | 文件位置 | 关键字段或定位 | 用途 |
|---|---|---|---|
| 两候选、首个pair、负载与包围盒 | [offline_feasibility.json](../../../../../../../../logs/scan_assignment/20261003_cr12_manual_joint_sweep/repro/offline_feasibility.json) | `status=PREFLIGHT_BLOCKED`、`selected_angle_deg=null`、`candidates` | 当前CPU结果，不是runtime结果 |
| 复算算法 | [check_joint_sweep_feasibility.py](../../../../../../../../logs/scan_assignment/20261003_cr12_manual_joint_sweep/repro/check_joint_sweep_feasibility.py) | `inputs:35`、`geometry_path:99`、`load_estimate:135` | 只读输入、201点和六轴估计复现 |
| 原几何判据 | [_cr12_runtime_support.py](../../../../../../../../scripts/environments/_cr12_runtime_support.py) | `_check_geometry:286–315` | 原规则未变；`contact_proven=false` |
| 当前运动学/安装 | [_cr12_pose_control.py](../../../../../../../../scripts/environments/_cr12_pose_control.py)；[派生URDF](../../../assets/rokeaCR12/derived/fixed_lift0_v1/cr12_fixed_lift0.urdf) | `T_ES:177`、`KinematicModel:331`；URDF `joint_3:195` | 名义FK、关节与质量输入 |
| 已接受USD collision读回 | [历史result.json](../../../../../../../../logs/scan_assignment/20260930_cr12_external_forces/attempt_02/result.json) | `usd_readback.colliders` | 历史运行输入，未被本轮重跑 |
| 幂等private准备适配 | [prepare_private_user_config.py](../../../../../../../../logs/scan_assignment/20261003_cr12_manual_joint_sweep/repro/prepare_private_user_config.py) | `patched_tree:101`、`validate_allowed_changes:113`、`prepare:131` | 0–3项语义改动，尚未接入runtime |
| helper CPU检查 | [cpu_checks.txt](../../../../../../../../logs/scan_assignment/20261003_cr12_manual_joint_sweep/repro/cpu_checks.txt) | `passed:67`、scope、helper hash | 合成fixture通过，不代表真实private启动 |
