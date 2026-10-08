# CR12 visual 覆盖预初始化集成与有界运行收尾报告

执行日期：2026-10-07，Asia/Shanghai（UTC+08:00）。结果：**VISUAL_PREINIT_INTEGRATION_PASS；等待 GPT/用户审阅，外观 PENDING_USER_REVIEW。**

## 1. 本轮结论与范围

本轮完成的是显示覆盖的**接入生命周期**：robot reference 已存在、根约束校准已完成且尚未建立 native physics views 时，应用一次十个 collision Mesh 的 visibility 意见；同一物理生命周期内完成初始化、固定 120 步保持和两份独立 native 参数快照；最终 native 读回之后才暂停、截图，随后正常关闭与自然退出。**首次主 App 全部通过，无运行失败、无重试，App 1/2，不追加运行。**

| 完成条件 | 实际结果 |
|---|---|
| 预初始化显示接入 | 一次 apply；十个 collision leaf invisible、十份正确 visual 可见；四阶段只读核对层与机器人 composition 不变，无运行期 revoke/reapply |
| apply 前后 composed 物理配置 | 紧邻比较 75 个 prim，完全相同；中间只写十项 visibility |
| native 参数 | setup、独立 initial、独立 final 共三次真实读取；两比较快照 raw/checked 逐值相等，各参数最大差 0；均符合既有独立期望 |
| 有界兼容性保持 | 初始化 2 步另计；受控 120 步、1.000000052154s；六类 guard 各 120 PASS，60 次正常 render |
| 修正后新图 | scanner 全头/支架图与车体图各一张，1280×720，各 15 次 UI updates；无暂停后 native getter 或新增物理步 |
| 正常退出 | 完整工作事实与关闭请求已保存；目标、Conda 均 exit0，全部所属进程结束，无超时/强制终止/native fault；全树 31.109s |
| 文件保护 | 原 URDF、20 个 OBJ、v1 七文件共 28 项未变；真实 user.config 的内容、大小、mtime 不变 |
| 用户外观确认 | 待用户审阅本次新图；无需强制再运行 App |

已接受的上轮结论保持：正确源 visual 没有丢失，可见 guide collision 遮住车体及 scanner 部分结构；精确 render visibility 覆盖是合适方向。本轮没有重新做 20 份完整三角形审计，也没有重算惯性、重新导入或修复源 OBJ。

这是一条新的集成顺序，**不是单变量根因隔离实验**。本次通过不能证明上轮 live layer 操作必然导致访问异常，旧四图、原 native FAIL、监督缺失记录及旧报告都保持原状。通过范围是当前 fixed-base/lift0/v1、baseline、explicit-on 的 120 步兼容性和退出路径，不是新的正式 pose/关节运动资格。

Phase B COMPLETE / GPT REVIEW PASS / CLOSED、basic drive、formal pose 既有接受结果保持；大幅 joint_3 demo 的数值与人工接受仅限该 demo，marker 正面反馈保持。本轮不自行授予新 GPT REVIEW PASS，未接扫描相机、构件、双视点、MRTA、训练或实体设备。

## 2. 实际修改与默认保护

下文仓库根为 `E:/Project/IsaacLab_HARL`，**T** 为 `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator`，**L** 为 `logs/scan_assignment/20261007_cr12_visual_preinit`。HEAD 保持 `24ecbad7dd1bdcd006399b64bfb757a86b71aeec`。

唯一机器人入口资产是 [cr12_fixed_lift0.usd](../../../assets/rokeaCR12/derived/fixed_lift0_v1/usd/cr12_fixed_lift0.usd) 及其现有引用层。沿用派生 URDF 中已接受的惯性数值和既有配置，未从本次实际读回生成期望。

| 文件 / 符号 | 本轮变化 | 保留行为 |
|---|---|---|
| [inspect_cr12_visual_geometry.py](../../../../../../../../scripts/environments/inspect_cr12_visual_geometry.py)：`_run_check:345`、`native_view_validity:92`、`read_native_snapshot:121`、`run_hold:183`、`render_corrected:255` | 预初始化回调、真实 view 检查、独立快照、固定 120 步、暂停后只做 viewport/时钟读取；移除本路径 live revoke/reapply；完整 scanner 取景 | 原 Windows/private/pre-App CUDA、既有场景与物理参数；无扫描 sensor 或动作目标 |
| [_cr12_visual_geometry.py](../../../../../../../../scripts/environments/_cr12_visual_geometry.py)：`inspect_preinit_mapping:162`、`CollisionVisualOverride:286` | metadata-only 来源/安装/schema 核对；显式 pre-init apply 一次、seal 后禁止撤销/重用，只读 `verify_stable` | 原十个 collision leaf、独立正确 visual；只写 visibility，不写 purpose/active/physics |
| [_cr12_runtime_support.py](../../../../../../../../scripts/environments/_cr12_runtime_support.py)：`create_fixed_cr12_scene:430` | 两个 keyword-only、默认 None 回调：`pre_physics` 在 :534；`before_native_read` 在 :557 | 无回调时全部原语句和顺序保持；`_read_physics:168` 未修改 |
| [test_cr12_visual_geometry.py](../../../../../../../../source/isaaclab_tasks/test/test_cr12_visual_geometry.py)、[test_cr12_visual_entry.py](../../../../../../../../source/isaaclab_tasks/test/test_cr12_visual_entry.py) | 精确身份/显示/生命周期、无效 view 拒读、独立快照、调用顺序/失败传播、暂停后无 native 等针对性测试 | fake backend 不冒充 native 验证 |
| [test_cr12_runtime_support_hooks.py](../../../../../../../../source/isaaclab_tasks/test/test_cr12_runtime_support_hooks.py)（新增） | 最小默认顺序及两个 hook 的成功/失败回归 | 不扩展全仓库测试 |
| L/repro/supervise_cr12_visual_preinit.py（新增） | 沿用已有 owned-process、实时排空、desktop/private 检查；独立本轮预算、严格完成/退出合取 | 180/360 秒上限，只管理所属进程，不复用旧 attempt |
| L/repro/prepare_private_user_config.py、test_supervisor_cpu.py（新增） | 已接受 private helper 的逐字副本；本轮监督器 CPU 检查 | 每 App 新 private，仅允许窗口三项 0–3 处差异 |

shared support 的两个回调确有必要：显示意见必须进入函数内部首次 reset 之前；该函数返回前已经有一次既有 `_read_physics`，所以初次 view 有效性检查也必须放在该读取紧前，不能等函数返回再检查。未复制场景构造代码，未把 visual 逻辑固化为全局默认。

默认保护已进行两种核对：删除新增两个 if 块和签名参数后，整个模块 AST 与修改前相同；直接按字节去除这 232 bytes 新增文本即可恢复原文件 SHA256 `ee63d013c2e6955009465927ad990decbd9a78272453e2e731176d50290c3963`。新文件 SHA256 为 `7fb130319a194ee4449f5b3019dd184b8d3a8387d6ab1eb485deef46e549271c`。原 formal/manual/joint-sweep 调用不传两个回调，默认行为不变。

未修改 Windows helper、安装包、驱动、真实 user.config、原资产、collision 几何/approximation/enabled/offset、mass/COM/inertia、PD/effort/solver/dt/gravity、root/scanner 定义、AABB/OBB 算法/默认或允许 pair。没有更改旧运动控制/判据或重跑 720/960/2520 步。

## 3. 为什么是真正的 pre-init，以及实际顺序

### 3.1 当前本地接口依据

以下安装路径前缀 **I** 为 `C:/isaacenvs/isaac45_harl/Lib/site-packages/isaacsim`，依据当前 Isaac Sim 4.5 安装源码；仓库 Isaac Lab 源码中的行号也按本轮当前文件核对。

- `source/isaaclab/isaaclab/assets/asset_base.py:68,77,93`：构造时标未初始化、spawn reference、注册 PLAY/STOP 回调；PLAY 的 `_initialize_callback:251` 才执行初始化。
- `source/isaaclab/isaaclab/assets/articulation/articulation.py:1147,1176`：`_initialize_impl` 创建 native articulation view；`:1300` 附近 STOP 使初始化状态失效并清空 root view。
- `I/exts/isaacsim.core.api/isaacsim/core/api/simulation_context/simulation_context.py:1296`：初始 stage/PhysicsContext 配置；`:598` 的首次 reset 经 `:861 play` 触发 PLAY。构造函数不是完整物理初始化的同义词。
- `I/exts/isaacsim.core.simulation_manager/isaacsim/core/simulation_manager/impl/simulation_manager.py:107`：warm-start 的 native load/start/update/fetch；`:122` 创建 Tensor SimulationView；`:116` 的 STOP invalidate/清空。SimulationContext 的 `physics_sim_view:344` 返回管理器当前 view。
- `I/extsPhysics/omni.physics.tensors/omni/physics/tensors/impl/api.py:122` 的 `SimulationView.is_valid` 是属性；`:444 SimulationView.check()`、`:2766 ArticulationView.check()` 是方法。
- `I/extsPhysics/omni.physx.tests/omni/physxtests/tests/PhysxSimulationInterface.py:103–124` 的本地测试明确 detach 后 `get_attached_stage()==0`。本轮联合其他状态判断，不只依赖该数值。
- pause/commit 沿用已确认的 `omni.timeline-1.0.11` 主线程接口；pause 不等于 STOP。STOP 会让 view 失效，所有应用层 native 读取必须提前完成。

这些文件只读，未修改 installed packages。没有按 Python 对象非 None 或旧 tensor shape 推定 native 有效。

### 3.2 实际调用与落盘阶段

```text
App / SimulationContext / external-forces explicit-on
→ 地面、灯光、robot reference
→ 既有 USD 检查、root anchor 校准、固定 frame 读取
→ pre_physics：身份检查 → composed before → apply 一次 → composed after → seal
→ contacts 构造、原首次 reset / PLAY / native views 建立（初始化 2 步）
→ before_native_read 有效性检查 → 既有 setup 参数读取
→ 既有一次零位 joint-state 初始化（不额外物理步）
→ 独立 initial native 读取、copy、保存
→ 120 步保持 + 60 次正常 render + 原基础 guards
→ 独立 final native 读取、copy、保存与比较
→ pause + commit
→ scanner / agv 两图（共 30 次 UI update）
→ 只读层检查、文件保护与完整工作事实保存
→ before_exit 仅 USD 外力读回 / contact 摘要仅已有 Python 数据
→ sim.stop → 关闭请求保存 → app.close → 外层自然退出确认
```

pre-hook 实际观察：robot_initialized=false、simulation_view_present=false、robot_view_present=false、physics_initialized=false、physics_running=false、timeline_playing=false、timeline_stopped=true、attached_stage_id=0。因此不是仅把 apply 移到名字叫 reset 的函数之前；在该位置 reference 已存在且首次 attach/view 创建尚未发生。

composed 两快照之间只有 `override.apply`，既有 anchor 校准在之前，contact 构造、drive/native 初始化在之后。snapshot 比较不跨这些合法 setup 写入。

本轮关键阶段落盘顺序为：

`overlay_applied_preinit → native_initial_saved → holding_completed → native_final_saved → timeline_paused → screenshots_completed → work_completed`

这里真实 `_read_physics` 共 **3 次**：保留的 setup 读取、初态写入之后的独立 initial、保持之后的独立 final。用于前后比较并独立持久保存 raw/checked 的是 **2 份**；顶层 `physx_raw_readback` 最后指向 final，不称为三份独立 raw 档案。setup、initial、final 三个读取前的 initialized/present/is_valid/simulation check/articulation check 均实际为 true，未触发 NOT_EXPOSED 分支；接口不可用的情况下代码会显式记录 NOT_EXPOSED，已知 false 则 NATIVE_VIEW_INVALID 并拒绝参数 getter，不 reset 或重建 view 补验。

## 4. 显示意见与三层物理比较

### 4.1 十项显示意见、一次应用与稳定性

实际匿名层为 `anon:000002915C29B370:cr12_collision_render_visibility.usda`，未保存为 USD 文件。层内只有祖先 over 与以下十个 Mesh 的 `visibility=invisible`：

```text
/World/CR12/agv/collisions/{agv_collision,elevate_collision,base_link_collision}/mesh
/World/CR12/link_1/collisions/link_1_collision/mesh
/World/CR12/link_2/collisions/link_2_collision/mesh
/World/CR12/link_3/collisions/link_3_collision/mesh
/World/CR12/link_4/collisions/link_4_collision/mesh
/World/CR12/link_5/collisions/link_5_collision/mesh
/World/CR12/link_6/collisions/{link_6_collision,scanner_collision}/mesh
```

花括号表示实际三个/两个独立路径，完整十路径逐项保存在 `render_override.properties`。purpose、active、变换、真实 collision 未修改；十份正确 visual 有效可见。恢复原 edit target，不调用 Stage.Save。

`inspect_preinit_mapping` 从派生 URDF 元数据核对 20 个独立表示、唯一 Mesh、body owner、scale/origin、schema、points 属性来源层及内部路径；points 必须来自该 v1 的 `configuration/cr12_fixed_lift0_base.usd`。本轮不读取 OBJ 顶点/重做全三角对应，`comparison.status=NOT_REPEATED_PREVIOUS_ACCEPTED_AUDIT`，不把 metadata PASS 包装成新的几何审计。

`apply(before_first_physics_initialization=True)` 之后调用 `seal_before_physics_initialization()`。同一 helper 永不 reapply，seal 后禁止 revoke；没有 context-manager、析构或 finally 隐式撤销。preinit、after_initialization、after_final_native、after_screenshots 四个阶段只读 `verify_stable` 均为同一层、同一摘要、apply_count=1、10 invisible/10 visible。运行不更改 robot reference/层栈，允许机器人之外的正常 Kit/Hydra 活动。

### 4.2 三种比较分别成立

| 比较 | 数据来源 / 结果 | 限制 |
|---|---|---|
| apply 前后 composed | 紧邻的 75 prim 快照相等，摘要 `725ce962381dab434cfb1bc4c68502c27e0755a006108481bab18cd256236a3d`；含 physics/schema/active、collision points/拓扑/xform、关系、drive 等 | 属性/几何摘要是 USD 证据，不是 native cooked hull 读取 |
| native 对独立期望 | 沿用 `_read_physics`，按 body/joint 名称映射对既有派生 URDF 七体惯性与 baseline 配置比较；initial/final 均通过 | 未重算惯性；均匀盒近似仍不是厂家真实参数 |
| 同生命周期 initial / final | 两份新 native 读取立即 host copy、deepcopy 并写盘，initial witness 后续不变；raw/checked 逐值相等，各参数最大差 0 | q/dq/world pose 不属于静态参数，另由 guard 监测，不要求逐值等于初态 |

`_read_physics:178` 的 `.detach().cpu().numpy().astype(float64, copy=True)` 完成必要 CPU 传输同步与独立复制，随后转换为 list；入口立即 deepcopy 两份 raw/checked 快照，避免后续 getter 复用缓冲区。完整惯量读回继续按**质心处、body/link 轴表达的 3×3 矩阵**解释，不重复按 COM 主轴四元数旋转。

以下为初始与最终共同的 native 数值摘要（为阅读取位，完整非对称浮点末位和 COM quaternion 保存在两份 raw 中）。质量 kg，COM m，惯量 kg·m²；惯量列顺序为 Ixx/Iyy/Izz/Ixy/Ixz/Iyz。

| body | mass（initial=final） | COM body xyz（initial=final） | 完整惯量的六个分量摘要（initial=final） |
|---|---:|---|---|
| agv | 63.440750122 | (0.009847510,0.000603783,0.610060751) | (11.110952377,12.797722816,8.173584938,−0.002458908,−0.196418345,−0.019800413) |
| link_1 | 3.440749407 | (−0.000008324,0.003624203,0.283859074) | (0.040731404,0.040002394,0.022845590,0,0,0) |
| link_2 | 5.024380684 | (−0.000023014,0.191745415,0.369056314) | (0.379516244,0.379773527,0.028452044,0,0,0) |
| link_3 | 2.439584732 | (−0.000072464,0.021512238,0.064993307) | (0.021837734,0.020865714,0.010365227,0,0,0) |
| link_4 | 2.439584732 | (0.000037994,−0.009180899,−0.141903639) | (0.035520706,0.034323316,0.006663129,0,0,0) |
| link_5 | 2.422757864 | (−0.000008404,0.011287979,−0.024584511) | (0.011912175,0.011024733,0.005939185,0,0,0) |
| link_6 | 3.652558804 | (0.060712673,0.060718220,0.118532829) | (0.097615875,0.097627044,0.056319557,−0.009122879,−0.016382311,−0.016366545) |

总质量均为 **82.8603663444519 kg**，body 顺序 agv/link_1…6，joint 顺序 joint_1…6，indices 分别 0…6 / 0…5，fixed-base=true、单实例；初态与最终相同。六轴 stiffness 为 (200,4000,2000,200,1000,150)，damping=(20,550,166,12,37,7)，max_force=(20,60,30,10,10,5)，max_velocity 每轴 0.20000000298023224 rad/s，friction/armature 全零。joint_2 position limits 为 ±2.9670996666 rad，其他五轴为 ±3.0542998314 rad，均与独立期望相符且前后不变。

使用原容差：mass rtol=1e−5/atol=1e−6；COM xyz 对期望 atol=1e−5、前后 COM xyz+xyzw 同样绝对 1e−5；完整惯量 rtol=1e−4/atol=1e−6；限位/drive/effort/velocity rtol=1e−4/atol=1e−6；friction/armature atol=1e−6。本轮各字段实际最大差均为 **0**，不是依赖放宽容差通过。

原十份 collision 几何/approximation/enabled/contact/rest offset 和 root/scanner 关系未改；本轮没有读取 native cooked hull 顶点，继续标 **NOT_READ**，不宣称完整形状或任意轨迹的连续碰撞安全。

## 5. 120 步保持与完整新图

运行使用 dt=1/120、render_interval=2、TGS8/2、baseline、重力 (0,0,−9.81)、cuda:0、external-forces explicit-on。既有 root 上抬 0.053m 与 anchor 校准在 apply 前完成；external-forces 的 after_apply/after_first_reset/before_render/before_exit 四次 composed 读回 true，无 native flag getter，保留该证据层级。

初始化 reset 一次，实际 **2 physics steps**，一次 joint-state 写入、零 root-state 写入；此后只下发原 baseline 的六轴零位置/零速度目标，循环不写 joint/root state，不设 kinematic、不改变重力。

| 运行数字 | 实际值 |
|---|---:|
| 受控保持 | 120 步，1.000000052154s |
| 起止 SimulationContext clock | (2,0.01666666753590107) → (122,1.0166667196899652) |
| 正常运行 render | 60 次，每两步一次，每次核对不多走 physics |
| clock / joint / contact / geometry / frame / render_clock | 各 120 PASS |
| 最大 |q| | 0.0022924216464161873 rad（约 0.13135°） |
| 最大实际 |dq| | 0.036533817648887634 rad/s |
| 禁止 contact 最大力 | 0 N |
| arm collision 包围最低 z | 1.2399987642922665 m |
| 运行 joint-state / root-state 写入 | 0 / 0 |

joint guard 只保留 finite、原硬限位 ±1e−3 rad 数值容差、actual speed≤0.25 rad/s；使用既有 contact≤0.1N、原 AABB 与 root/frame/clock 保护。不套用旧轨迹 t=2/t=5 进展窗或末秒精度门槛，不把 PD 保持的非零小偏差误判成质量/惯量变化，也不把这 1 秒扩成新的控制验收。

最终 native 读取并保存后才 `pause(); commit()`。暂停下 SimulationContext clock 固定为 (122,1.0166667196899652)，timeline time 固定为 1.0500000000000012；两个计时来源分别不增，不要求彼此数值相同。截图循环没有 robot/Tensor getter、reset、physics step 或层切换。

本轮只保存两张 corrected 原 PNG，没有重拍上轮 A/B。使用既有 `/OmniverseKit_Persp`、既有 viewport render product，没有新增 camera/sensor/render-product 采集链。每图 15 次更新（12 次预热+3 次完成等待），总计 30；均低于每图 60 次上限，PNG 完整/IEND 与文件 hash 已核对。

### 完整 scanner 修正图

eye=(1.03,−0.98,3.58)，target=(0.23,−0.03,3.08)，world 米制。取景参考完整 scanner 包围范围、已记录 optics，保守八角投影预估最少约 16.55% 整幅边缘余量；真实图片已查看，头部、支架和开放空间均在画面内，顶部不再裁切。机械臂其他部位无需全部进入此近景。

![本轮完整scanner修正图](../../../../../../../../logs/scan_assignment/20261007_cr12_visual_preinit/attempt_01/scanner_corrected.png)

1280×720，224511 bytes。与上轮 scanner 视角不同，且本轮经过 120 步保持，**不能称为与旧图逐像素同条件 A/B**。未裁剪或修图，未更改材质/robot/visual。

### 车体修正图

eye=(1.75,−2.2,1.35)，target=(0,0,0.53)，车体分层、底座与上部波纹结构可见。

![本轮车体修正图](../../../../../../../../logs/scan_assignment/20261007_cr12_visual_preinit/attempt_01/agv_corrected.png)

1280×720，615267 bytes。用户可直接查看两张图片；两处外观判断仍为 **PENDING_USER_REVIEW**。GUI 图片不是扫描相机采集，更不代表重建或测量精度。

## 6. 实际命令、CPU 验证、保护与退出

### 6.1 运行前检查与实际执行命令

解释器实核：`C:/isaacenvs/isaac45_harl/python.exe`，Python 3.10.20，运行 UTF8=1。全部命令 cwd 为 `E:/Project/IsaacLab_HARL`。

主要 CPU 命令如下，均 exit0；helper **31/31**、entry **19/19**、shared hook **6/6**、supervisor **11/11**，合计 67 项。源码变化后完成对应最小检查，未重跑 source 全三角、OBB/sweep/formal/Windows/Phase B 套件。

```powershell
& 'D:\miniconda3\Scripts\conda.exe' run -p 'C:\isaacenvs\isaac45_harl' python -B source/isaaclab_tasks/test/test_cr12_visual_geometry.py
& 'D:\miniconda3\Scripts\conda.exe' run -p 'C:\isaacenvs\isaac45_harl' python source/isaaclab_tasks/test/test_cr12_visual_entry.py
& 'D:\miniconda3\Scripts\conda.exe' run -p 'C:\isaacenvs\isaac45_harl' python source/isaaclab_tasks/test/test_cr12_runtime_support_hooks.py
& 'D:\miniconda3\Scripts\conda.exe' run --no-capture-output -p 'C:\isaacenvs\isaac45_harl' python -X utf8 -B 'logs/scan_assignment/20261007_cr12_visual_preinit/repro/test_supervisor_cpu.py'
```

修改的三个实现、三个对应测试及 repro Python 均完成 `python -m py_compile`；它可能更新相应 `__pycache__`，不更改资产。fake 事件测试覆盖真实编排、默认调用顺序、初始数据独立复制、无效 view 拒读、先 native 后 pause、暂停后禁 getter、保持/截图失败不得完成、主异常与次级关闭异常区分。监督器 CPU 测试执行了真实完成判定调用点的成功/失败两分支，避免重现上轮少传参数。

本轮唯一真实 GUI 主验证命令：

```powershell
& 'D:\miniconda3\Scripts\conda.exe' run --no-capture-output -p 'C:\isaacenvs\isaac45_harl' python -X utf8 -u 'logs/scan_assignment/20261007_cr12_visual_preinit/repro/supervise_cr12_visual_preinit.py' --attempt-dir 'E:\Project\IsaacLab_HARL\logs\scan_assignment\20261007_cr12_visual_preinit\attempt_01'
```

其实际目标进程命令如下（父监督合并继承环境，并设置 PYTHONUTF8=1、HEADLESS/ENABLE_CAMERAS/LIVESTREAM/XR=0）：

```powershell
& 'D:\miniconda3\Scripts\conda.exe' run --no-capture-output -p 'C:\isaacenvs\isaac45_harl' python -u 'scripts/environments/inspect_cr12_visual_geometry.py' --usd-path 'E:\Project\IsaacLab_HARL\source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\assets\rokeaCR12\derived\fixed_lift0_v1\usd\cr12_fixed_lift0.usd' --output-dir 'E:\Project\IsaacLab_HARL\logs\scan_assignment\20261007_cr12_visual_preinit\attempt_01' --device cuda:0 --external-forces-every-iteration on --info '--kit_args=--/app/userConfigPath=E:/Project/IsaacLab_HARL/logs/scan_assignment/20261007_cr12_visual_preinit/attempt_01/private_config/user.config.json'
```

这两条是同一次已发生运行的外层与子命令，不应重新使用 attempt_01。最终 Kit 参数由既有 Windows helper 保留 private 并追加 `--/app/vulkan=false`，experience=`apps/isaaclab.python.kit`；实际 D3D12 另由 Kit 日志确认。未修改既有 pre-App CUDA 顺序。

### 6.2 本轮运行事实

| 项目 | attempt_01 |
|---|---|
| 本地开始 / 结束 | 2026-10-07 10:04:15.602 → 10:04:46.703，UTC+08 |
| App 构造 / 所属树耗时 | 18.281s / 31.109s，分别低于 180s / 360s |
| 目标 / Conda | PID32972 / PID21016，均 exit0 |
| 实际图形与尺寸 | D3D12；native window 1440×900，viewport 1280×720 |
| 完成 / 收尾 | completed_physics_steps=120；work_completed、diagnostics_complete、simulation_stop_returned、app_close_requested 均 true |
| 错误 / 超时 | 主失败、次级失败、native fault、supervisor errors 均空；无 timeout、无 termination |
| 进程树 | 所属全部退出、remaining=[]，实时输出完整排空 |
| 本轮预算 | App1/2，受控一次120步，2/2新图；没有 attempt_02、没有修复重试 |

console :7251 是 work_completed、:7253 是 app_close_begin（failures=0）；Kit :6953 为正常 ShuttingDown。**没有 app_close_returned 事件**，所以报告不声称 Python 已记录该函数返回；完整内部工作、关闭请求、正常 shutdown 与目标/Conda 自然 exit0/全树退出共同支持本次退出通过。不能单凭 exit0 或 PNG 存在作结论。

Kit `kit_20261007_100419.log:2682,3484` 记录 DX12/D3D12；native 窗口见 console :3382 / Kit :3342。Kit 时间字段使用 UTC，例如 02:04:20 对应本地 10:04:20。`composed_window_settings` 未由入口导出，仍 UNKNOWN，不用 native 尺寸反填这个缺失字段。

本轮没有 runtime 失败或热修改。准备期一次只读文件保护命令最初未区分原 URDF 的绝对 mesh 路径，导致 Get-FileHash/JSON 解析报错；修正为绝对路径直接使用后，28 项核对成功，无文件变更、不占 App。此为取证方法修正，不是机器人或运行修复。

### 6.3 配置、资产与既有 worktree

真实 source 为 `C:/isaacenvs/isaac45_harl/Lib/site-packages/omni/data/Kit/Isaac-Sim/4.5/user.config.json`，114100 bytes，mtime_ns=`1790759017622695800`，SHA256=`9b3b72015f7e8ca7a74ad179a81329bc3f00966862dd0ce8f831831a12dea625`，准备前、Popen 前及退出后均不变，语义差 0。fresh private 实际三项差异 −1/−1/true→1440/900/false；helper 允许以后 source 已符合要求时仅 0–3 项差异。运行后 private 84107→114104 bytes，Kit 格式重写、语义差 0，三项窗口值保持；没有写真实 source 或共享配置。

本轮只保护必要范围：入口对原 URDF/20 OBJ/v1 七文件的 28 项 before/after 内容比较通过；运行后 10:07:19+08 外层只读再次核对这 28 项与五个当前执行代码输入，全部未变。五代码项只用于防止本次运行前后热改，不复制旧 53 项冻结体系；未新增全仓库 manifest、ZIP、视频、逐帧 dump 或重复汇总包。

原 worktree 的 view/train/play、AgentRead 既有修改及未跟踪文件保留；index 仍只有原先的 Phase B ZIP 删除，本轮未增删暂存，未执行 Git 写操作或清理。旧四张图片及失败 result 不改写、不删除、不恢复旧资产。

## 7. 人工静态查看命令与后续接入约定

可直接查看上方两张新 PNG，不必再启动。若要人工 GUI 查看，下面是一条当前已实现的 PowerShell 调用流程：每次生成独占新目录、fresh private，使用同一 pre-init/120 步/两图/关闭路径和 180/360 秒监督；暂停后每个视图在最多 60 次更新范围内短暂停留。没有动作目标、20°往返或 live 撤销开关。

```powershell
Set-Location 'E:\Project\IsaacLab_HARL'
$cr12VisualAttempt = Join-Path (Get-Location) ('logs\scan_assignment\20261007_cr12_visual_preinit\manual_' + (Get-Date -Format 'yyyyMMdd_HHmmss'))
& 'D:\miniconda3\Scripts\conda.exe' run --no-capture-output -p 'C:\isaacenvs\isaac45_harl' python -X utf8 -u 'logs/scan_assignment/20261007_cr12_visual_preinit/repro/supervise_cr12_visual_preinit.py' --manual-check --attempt-dir $cr12VisualAttempt
```

目录格式必须 `manual_YYYYMMDD_HHMMSS`；命令会自动创建 private，勿手工复用 attempt_01/private。同秒重用或已有输出会拒绝覆盖。监督器核对当前五份代码的已检查版本，源码发生后续变化时不会静默沿用旧通过记录。

本轮自动验证使用相同路径但未加 `--manual-check`；人工分支额外的有界静态停留只做源码/CPU 检查，**没有为此再启动一 App**，不能写成用户已经完成外观确认。人工命令不会解封新运行范围或自动接 sensor。

后续扫描场景的显式接入约定是：

```text
机器人 reference 存在、原 anchor/setup 已到安全位置且 native views 未建立
→ 校验独立 visual/collision
→ 相邻 composed before / helper.apply 一次 / composed after
→ seal，首次物理初始化
→ 整个运行期间保留同一匿名意见，仅只读核对
→ 所有需要的 native 读取在 pause/stop/detach 之前完成
→ 关闭场景；匿名意见随场景销毁结束
```

本次证据足以支持下一轮在**同一资产与初始化路径**中显式复用该约定，旧 formal/manual/sweep 默认不自动启用。helper 使用 `before_first_physics_initialization=True` 是调用方已经验证时序后的显式承诺，不能代替实际 view/timeline/attach 检查。无需改模型、碰撞或重新导入。

可撤销的含义是旧入口不调用 helper 即保持原显示，新场景结束后匿名意见消失；本轮不展示 live views 存在时撤销。未初始化 stage/CPU 可用 revoke，sealed 本对象不允许再用。不要通过 reset/clean 撤销本轮而覆盖用户既有 worktree。

下一研究步骤仍为单视点到位后按需相机采集，需另行授权：开启→实际取得属于本次的数据→关闭，不以 pose reached、viewport PNG 或等待时间代替采集；不增加点云覆盖/重建质量门槛。采集成功与随后关闭失败分别记，未确认关闭不能进入下一段运动。camera 挂载/启停/新帧关联、构件、双视点和 MRTA 都未实施或代验。

## 8. 辅助证据与文档变更

| 结论 | 文件位置 | 关键字段 / 行号 | 证据边界 |
|---|---|---|---|
| pre-init、初末参数、120步与截图 | [attempt_01/result.json](../../../../../../../../logs/scan_assignment/20261007_cr12_visual_preinit/attempt_01/result.json) | preinit_timing、visual_preinit、native_snapshots、holding_check、physical_invariance、phase_order、screenshots | 内部完整事实；退出要结合监督结果 |
| 自然退出与整体判定 | [supervisor_result.json](../../../../../../../../logs/scan_assignment/20261007_cr12_visual_preinit/attempt_01/supervisor_result.json) | visual_preinit_runtime_pass、双exit0、budget_after、layer_checks | 全树31.109s、App1/2；无close_returned推定 |
| 实际命令 / 实时事件 | [command.json](../../../../../../../../logs/scan_assignment/20261007_cr12_visual_preinit/attempt_01/command.json)、[console.log](../../../../../../../../logs/scan_assignment/20261007_cr12_visual_preinit/attempt_01/console.log) | argv/env白名单；7248/7249两图、7251完成、7253关闭请求 | 没有复制完整环境变量或无关凭据 |
| D3D12 / 正常shutdown | [kit_20261007_100419.log](../../../../../../../../logs/scan_assignment/20261007_cr12_visual_preinit/attempt_01/kit_20261007_100419.log) | 2682、3484、6953 | 同次 app_ready 指向的本机 Kit 日志副本 |
| private 与 source 保护 | [source_private_config_summary.json](../../../../../../../../logs/scan_assignment/20261007_cr12_visual_preinit/attempt_01/source_private_config_summary.json)、[config_runtime_summary.json](../../../../../../../../logs/scan_assignment/20261007_cr12_visual_preinit/attempt_01/config_runtime_summary.json) | 0–3差异规则、本次3、source_unchanged、语义diff0 | private格式变更不混为source改变 |
| 五代码输入 / CPU通过前提 | [repro/preflight.json](../../../../../../../../logs/scan_assignment/20261007_cr12_visual_preinit/repro/preflight.json) | task/checks/code_sha256；attempt内记录准备完成事实 | 窄范围运行前检查，不是旧库存审计 |
| 人工与自动共同监督 | [supervise_cr12_visual_preinit.py](../../../../../../../../logs/scan_assignment/20261007_cr12_visual_preinit/repro/supervise_cr12_visual_preinit.py)、[test_supervisor_cpu.py](../../../../../../../../logs/scan_assignment/20261007_cr12_visual_preinit/repro/test_supervisor_cpu.py) | completion、budget_for_attempt、prepare_attempt | main与失败调用点经过CPU测试 |
| 上轮定位与失败 | [CR12_VISUAL_GEOMETRY_CONSISTENCY_REPORT.md](../20261004/CR12_VISUAL_GEOMETRY_CONSISTENCY_REPORT.md) | 原四图/源映射/native FAIL | 历史结论保留；本轮不证明其唯一根因 |

本次仅新增本主报告，并小范围更新 [TASK_PROGRESS.md](../../TASK_PROGRESS.md)、[REPORT_INDEX.md](../../REPORT_INDEX.md)。主报告22个本地链接与交接/索引相关6处链接均存在，4个PowerShell块只做语法解析、未重新执行；交接变更与本轮开始文本对照，仅涉及最新状态、当前边界与导航。Python/JSON/图片留在源码、test、logs 对应用途目录；`logs/` 受既有忽略规则影响、仅本机可取，未提交，不暗示新 checkout 自动拥有运行证据。

**本轮实施与有界验证已完成，等待 GPT/用户审阅和两处外观确认；已停止，不自动接相机、增加可视化分支、运行第二个 App、提交或清理。**

