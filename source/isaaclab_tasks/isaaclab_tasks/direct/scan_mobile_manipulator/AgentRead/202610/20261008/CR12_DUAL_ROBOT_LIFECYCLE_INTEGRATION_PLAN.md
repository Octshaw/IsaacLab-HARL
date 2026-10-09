# CR12 固定双机器人 lifecycle 接入评估与最小实施方案

日期：2026-10-08，Asia/Shanghai（UTC+08:00）。状态：**DESIGN ONLY / 源码与离线布局计算完成 / 等待 GPT、用户审阅；双机未实施、未运行。**

## 1. 当前基线与结论

本轮只读确认：仓库 `E:\Project\IsaacLab_HARL`，分支 `main`，HEAD **`a8c618a32da65747827f1cb3f722fac24df2aec8`**，最近提交 `feat(cr12): establish single-robot scan execution and lifecycle integration`，提交时间 `2026-10-08 16:30:33 +0800`。开始时 `git status --short` 为空；本轮读取的实现已存在，未发现相关未提交代码差异。该 HEAD 是本次设计基线，不使用历史报告中的旧 HEAD。用户确认单机 execution-to-lifecycle 已 **GPT REVIEW PASS**、已手动 commit，且不再补人工观看单机动作；旧报告当时的待审、FAIL、旧 HEAD 原文保留。

**推荐一个私有 E1/M2/N4 Host：一个 App/stage/SimulationContext，两个明确的 Articulation 对象、两个独立控制和 Camera/product 上下文，一个真实 domain/Store/resolver/claim/P2/producer/authority/facade。** 两台沿 Y 轴相距 **2.0 m**，同朝向、同固定底盘/lift0/v1。四任务统一编号，每台只领取本区两个目标；每个物理子步共同推进，每个 Host transition 只 finalize 一次全域事实。复用当前组件并局部拆分初始化，不复制两个单机 Host，也不改核心 authority。

本轮实际算得：原小幅名义路径的跨机完整扫掠包络，在双方各 2 mm 碰撞余量后分隔 **1.135999908 m**；整个名义每轴 ±5° 信任盒的保守跨机分隔 **0.270116059 m**，超过本方案额外布局裕量 0.25 m。这支持布局选择，**不是双机实际运动、连续接触安全或双相机运行 PASS**。

主要实施工作是：单次 scene 初始化的拆分；每机器人独立执行槽与无任务保持；adapter 的多 binding/同事务多结果；相机与 contact 的实例归属；四任务全局终态。当前源码没有要求把该范围扩为通用多机框架。首轮不验证同任务竞争、跨机转交、负载均衡、异构性、任意规模策略或 checkpoint；不重新开启 Phase B。Phase B 保持 **COMPLETE / GPT REVIEW PASS / CLOSED**，公共 event gate 保持。

### 1.1 本文证据类别与路径

| 标记 | 含义 |
|---|---|
| 用户确认 | 最新审阅/commit/停止单机人工观看决定 |
| 源码确认 | 当前文件、契约、已安装 API 的静态读取得到；不代表实例运行通过 |
| 单机证据 | 已接受单机原始结果，只作复用与预算依据，本轮未重跑 |
| 离线计算 | 当前 URDF/mesh/纯 CPU FK 与包络计算；无 App、IK 求解或动力学 |
| 拟实施 | 本报告推荐的接口/文件/流程，当前未创建 |
| 待双机运行 | 第二实例重定位、native 映射、实际并行/接触/产品隔离等 |

下文路径相对仓库根：`T=source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/`；`E=scripts/environments/`；`Q=source/isaaclab_tasks/test/`；`L=logs/scan_assignment/20261008_cr12_dual_robot_plan/`。行号均指上述 HEAD 对应当前源文件；USD 不伪造文本行号。唯一前置主报告为 [单机 execution-to-lifecycle 实施报告](CR12_EXECUTION_LIFECYCLE_INTEGRATION_REPORT.md)，必要契约背景见 [已审单机接入方案](../20261007/CR12_EXECUTION_LIFECYCLE_INTEGRATION_PLAN.md)。

## 2. 实体、路径、任务与维度

### 2.1 固定实例方案

复用资产 `T/assets/rokeaCR12/derived/fixed_lift0_v1/cr12_fixed_lift0.urdf` 及其已生成的 `usd/cr12_fixed_lift0.usd`。后者仍是后续场景直接引用的 v1 来源；本轮不重新导入、不改资产或物理参数。这里不是用户早前已删除的旧 USD。

| 项目 | robot0 | robot1 |
|---|---|---|
| domain 身份 | env_id=0, robot_id=0 | env_id=0, robot_id=1 |
| 拟定 agent 名 | `cr12_0` | `cr12_1` |
| 实例根 / cfg.prim_path | `/World/CR12_0` | `/World/CR12_1` |
| 预期 agv LINK world 位置，m | `(0,0,0.053)` | `(0,2,0.053)` |
| root WXYZ | `(1,0,0,0)` | `(1,0,0,0)` |
| camera prim | `/World/CR12_0/link_6/SingleViewCamera` | `/World/CR12_1/link_6/SingleViewCamera` |
| 非物理 fixture | `/World/CameraInterfaceFixture_R0` | `/World/CameraInterfaceFixture_R1` |
| render product 请求名 | `CR12_R0_Capture` | `CR12_R1_Capture` |
| Camera 对象名 | `cr12_r0_camera` | `cr12_r1_camera` |
| 独立观察订阅标签 | `cr12.r0.independent_completion` | `cr12.r1.independent_completion` |
| 本区任务、请求额度 | task0、task1；2 次 | task2、task3；2 次 |

上表实例根不同于 ArticulationRootAPI 所在 prim；旧单机读回为 `/World/CR12/root_joint`，双机对应候选各为本实例 `/root_joint`，首次运行须逐实例确认。实例放置Xform、root joint API与agv LINK不能混为同一frame。

产品预期前缀为 `/Render/OmniverseKit/HydraTextures/`，但实际身份必须取创建返回的 `product.path`，并核对 Camera relationship。不得依赖自动添加数字后缀或创建顺序。逻辑预定路径已被占用时 SETUP 拒绝；两个实际 product、Hydra handle、各组annotator、Camera 对象须互异，每台内部跨请求保持原对象。

选择**两个明确 Articulation 对象**，各自 `num_instances=1`，每台继续使用现有单实例控制张量。`_cr12_scan_executor.py:174–217`、`_cr12_pose_control.py:283–298` 的 `[0]` 是该对象内的 articulation batch 维度，不是 domain robot_id；原 Jacobian `(1,6,6,6)` 检查保留每台一份。不会将所有 `[0]` 改为 robot 索引。每台按本 root 下真实 body/joint 名与 prim 路径建映射，映射不可依赖对象创建顺序。

预期每台 7 个 rigid body、6 个 revolute joint、1 个 world fixed joint、10 个 collision；全局至少两份相应实例而非把 14 体塞入原单台 schema。地面/灯光共享，fixture 无 physics schema。实际数量与路径仍在首次运行逐台读回。

### 2.2 冻结的四个目标

以下是本轮从当前 URDF 计算的**名义** scanner world 位姿，米、WXYZ；目标仍指 scanner frame，Camera 通过已接受的固定虚拟安装变换随机器人运动。不是四个已运行可达点。

| task | 执行范围 | 位置 `(x,y,z)`，m | WXYZ |
|---|---|---|---|
| 0 | robot0 外移小目标 | `(0.115698145715,-0.150000000000,2.887844953278)` | `(0.382668860953,0.008062267537,0.003339500557,0.923844354010)` |
| 1 | robot0 返回初始 scanner | `(0.105000000000,-0.150000000000,2.888000000000)` | `(0.382683432365,0,0,0.923879532511)` |
| 2 | robot1 外移小目标 | `(0.115698145715,1.850000000000,2.887844953278)` | 同 task0 |
| 3 | robot1 返回初始 scanner | `(0.105000000000,1.850000000000,2.888000000000)` | 同 task1 |

首次初始化后，分别从每台**实际 scanner world 状态**冻结两个目标：外移沿当前 formal 位移定义，并在 world-Y 左乘 +1°；返回目标是本台初始实际 scanner 位姿。依据 `_cr12_pose_control.py:205–211` 的 `FrozenPoseTarget`；模型 `KinematicModel._chain/forward:366–379` 已从传入的 root world 变换起算，不能再加一次 robot 平移或 env_origin。此处同朝向纯平移保持原位移/旋转语义，不额外引入面对面布局。

四个 world pose 形成一份只读全局任务表；认领/释放/更换 owner 不重算任务位置。每次 reference 的起点取接单时本台实际状态，task1/3 不从理想 task0/2 终点跳回；同台 `q_cmd` 和信任锚连续。cost 根据每台当前实际 scanner 到**同一份**全局表的距离计算，不能只填本区两个距离。名义初始 cost 为：

```text
[[[0.010699269191, 0, 2.000028618386, 2],
  [2.000028618386, 2, 0.010699269191, 0]]]
```

本次已检查的执行范围 allowlist 为 bool `[1,2,4]`：

```text
[[[true,  true,  false, false],
  [false, false, true,  true ]]]
```

它限制首版执行准入，**不表示全部未允许跨区 pair 已被证明物理不可达**；也不能把跨区 proposal 被此 mask 拒绝称为真实竞争仲裁通过。owner、completed、completion_count 仍由一份 authority 唯一维护。

### 2.3 契约张量与编码

依据 `T/assignment_lifecycle_transition_contract.py:486–505` 和 `assignment_event_proposal_adapter.py:134–164,500–533`：

| 内容 | E1/M2/N4 shape / dtype | 维度含义 |
|---|---|---|
| assignment、raw/decoded proposal | `[1,2] / int64` | environment、robot |
| feasible、C/F/R、failed pairs | `[1,2,4] / bool` | environment、robot、全局 task |
| U/Rc | `[1,2] / bool` | environment、robot |
| cost | `[1,2,4] / float32`（契约也接受 float64） | 所有 robot-task pair |
| task state、owner；coverage | `[1,4] / int64`；`[1,4] / bool` | 一份四任务状态 |
| robot state、completion_count | `[1,2] / int64` | 两台 attribution |
| episode/transition/consume token | `[1] / int64` | 共同 environment generation |
| done/time-limit/bad-transition | `[1] / bool` | environment 终态 |

这里 task 数为 4，所以 raw NO_CLAIM 为 **4**，decode 后为 **−1**，不能沿用单机的 2。已有 EXECUTING 机器人在 proposal 路径须填自己的当前 task，不可 raw4 代替 continuation：`assignment_event_proposal_adapter.py:568–579` 会拒绝 `ILLEGAL_EXECUTING_NOOP`。例如 r0 新 task1、r1 继续 task2，raw=`[[1,2]]`，新 claim request=`[[1,-1]]`；r0 无本区任务、r1 新 task3，raw=`[[4,3]]`。都没有新 claim 时调用现有 `step_without_new_claim`。

## 3. 本轮实际布局计算及限制

### 3.1 输入与方法

离线脚本 `L/repro/check_dual_layout.py` 只读当前派生 URDF/mesh，使用标准库、NumPy 及可独立工作的 `_cr12_asset_math`、`_cr12_pose_control` 和原 `_check_geometry` 纯计算部分；没有 import 任务包、torch、Kit、Isaac、控制器或 IK。十份 body-local collision AABB 与既有单机 `attempt_01/result.json` 中 `usd_readback.colliders` 作定向比对，最大分量差 **5.64032234e−8 m**。这是当前源几何与旧读回相符，不是本轮解析了 USD composition。

名义 witness 关节增量 `(0,1,-1.5,0,1.5,0)°`，4 s quintic `q(u)=witness*(10u³−15u⁴+6u⁵)`，`u=0..1` 取 201 点；返回为同路径反向，共 201 个独立构型。原 self/ground AABB guard 全部通过，运动 arm 最低 Z 为 **1.239999229 m**。端点 FK 与 formal 目标相差 **4.45e−16 m / 0 rad**。途中 scanner 与实际 task-space 插值 reference 的最大名义偏差 **3.8761963e−5 m（0.038762 mm）**，因此不将这条 joint witness 路径等同实际 DLS/执行器轨迹。

每个 shape 用完整路径世界角点 union 形成独立扫掠 AABB，再检查 10×10=**100** 个跨机组合，覆盖任意相对进度；不是仅比较两台同一 u 的状态。额外用各祖先关节的保守半径 `L_j = 后续链段平移长度之和 + body-local角点最大半径`，通过逐轴 telescoping 得到角点位移上界：

```text
位移 ≤ Σ_j 2 sin(|δq_j|/2) L_j
最近样点 δq_j ≤ |witness_j| × 1.875 / (2×200)
```

据此扩张逐 shape union，给出名义采样间隙的连续外包络；再从名义 `q0=(0,0,0,0,0,0)` 按每轴 ±5° 用同一界扩张，给出整个原信任盒的保守外包络。这里是各状态相对中心的5°，不是说盒内两任意状态只相差5°。没有扩大原 5° 控制范围。该界对**名义刚体 FK 与原角点 bounds**成立，不覆盖错误 native 映射、错误 root anchor、真实动力学偏离、PhysX cooked 几何差异；self/ground 本轮仍只是 201 构型原守卫检查，不升级为全信任盒的 self/ground 连续证明。

### 3.2 包络与间距

robot0 世界 AABB 数值如下，单位 m；robot1 相同范围的 Y 分量加 2.0：

| 几何范围 | min `(x,y,z)` | max `(x,y,z)` |
|---|---|---|
| agv 固定组合并包络 | `(-0.527,-0.430000031,0.000000061)` | `(0.527,0.430000061,1.245006058)` |
| 运动 arm 名义采样 union | `(0.006799217,-0.203724045,1.239999229)` | `(0.406973039,0.283491730,3.273247126)` |
| 全部形状、连续名义路径保守 union | `(-0.527,-0.430000031,0.000000061)` | `(0.527,0.430000061,3.273672910)` |
| 全部形状、整个 ±5° 盒保守 union | `(-0.634336344,-0.889336344,0.000000061)` | `(1.091534278,0.836547598,3.974739847)` |

原每侧余量为 **0.002 m**，双方共 0.004 m；新增 **0.25 m 布局裕量**用于选择间距，不修改现有接触阈值或碰撞体。Y 信任盒总宽 **1.725883941 m**：

```text
最小候选间距 = 1.725883941 + 0.004 + 0.25 = 1.979883941 m
向上取 0.1 m 整数格 → 2.0 m
名义路径裸间隙 = 2.0 − 0.860000092 = 1.139999908 m
名义路径余量后间隙 = 1.135999908 m
完整 ±5° 盒余量后间隙 = 2.0 − 1.725883941 − 0.004 = 0.270116059 m
```

X 方向按同算法亦需取整到 2.0 m（信任盒宽 1.725870622 m）；本设计选择 Y，无需旋转机器人且保留当前局部运动语义。间距不是为了视觉美观。后续仍逐实际物理步检查跨机几何、root/frame 和 contact；任一违反则 fail-stop，不能借离线宽裕布局跳过实际检查。

### 3.3 USD 引用与固定 root

`source/isaaclab_assets/isaaclab_assets/robots/rokea_cr12.py:33,64` 的 `make_cr12_cfg` 已接受 `prim_path`，但默认初始位置固定 `(0,0,.053)`。后续可在返回的场景 cfg 上设置本实例 `init_state.pos/rot`，保留函数原默认；`source/isaaclab/isaaclab/assets/asset_base.py:77–82` 将其传入 spawner，`sim/spawners/from_files/from_files.py:185–225` 用该平移/姿态创建引用。

`E/_cr12_runtime_support.py:_calibrate_root_anchor:127–165` 已验证“一端 world、另一端本 agv”，以 **本 body 的 USD world 矩阵 × body-side joint frame** 推算 world 端 localPos/localRot，仅写 scene layer，并以 1e−6 核对。它可逐实例复用，但必须传正确本实例 info，且在首次 reset 前；不能两次复用 robot0 路径或把第二台约束到原点。不保存到源 USD，也不在任务运动中回写 root/关节状态。

本轮 stdlib 检查 top USD 与 `configuration/*_base.usd / *_physics.usd / *_sensor.usd` 均为 `PXR-USDC`；指定解释器 `find_spec('pxr')` 为 None，未启动 Kit 或污染导入路径。故**第二引用的 absolute relationship、resetXformStack、具体 composition 重定位为 UNKNOWN**。首次授权 App 在 physics 初始化前必须核对：两个 subtree 的 rigid body/world transform；每个 joint 的 body targets 是否全在本 root；world side 空 target；每台唯一 articulation root/world anchor；无跨 root body 引用、意外 resetXformStack 位移丢失及隐藏 collision group/filter。任何失败在 reset 前拒绝，不自动修资产。初始化后再核对 native root/body/joint path、实际 agv 位置和固定 frame。

## 4. 单实例假设与拟改文件

所有下列改动均为**下一轮建议，尚未实施**。只支持明确的旧 M1/N2 与新 M2/N4 两个私有 profile，不顺手推广任意规模。

| 位置/符号（E/T 见第1节） | 当前单机假设与双机影响 | 最小拟改法 | 旧默认保护 |
|---|---|---|---|
| E `_cr12_runtime_support.py:create_fixed_cr12_scene:430–566` | 内建 SimulationContext、固定 root、ground、contacts、`sim.reset:549`；调用两次会重建/重置共享 scene | 拆 shared-world 建立、单实例 pre-init spawn、一次 global reset 后逐实例 readback；原函数组合这些阶段 | 单机原函数签名/默认次序保留 |
| 同文件 `_calibrate_root_anchor:127`、`initialize_fixed_cr12_state:569–614` | anchor 可复用；初态期望 root 仍硬编码 `ROOT_TRANSLATION:596` | 显式传实例 root pose/路径；合法初态每实例写一次 | 默认原 root/位置；不改 v1 |
| 同文件 `_check_geometry:286–315`、`_make_contacts:328–344` | self 邻接例外只适合本机；contacts 仅本机非相邻体/ground | 保留 self；增跨机 100 shape 检查；contact 加对方完整 body filters | 原单机 filter 和 AABB 模式不变 |
| E `run_cr12_single_view_capture.py:prepare_scene:119–188`、`refresh_initial_camera_publication:229–267` | 一套 resources/recorder、硬编码 root、每次调用一次 sim.forward | 抽出实例前置与发布前后快照阶段；双机所有初态写完后只 global forward 一次，再各 verify | 原入口用单实例 wrapper，旧调用仍一次 |
| E `_cr12_scan_executor.py:135–244,319,364–495` | 单对象内部 batch `[0]` 正确；必须先 submit_goal 才 prepare；spectator 单视角 | 保留局部张量与 controller.num_envs=1；每实例 context；增加无绑定初始/末次状态反馈保持，统一 Host clock；双机只设一次共同 spectator | 原 pose/捕获默认行为与阈值不变；不要求人工观看 |
| E `_cr12_pose_control.py:283–298,331–443` | 7体/6轴映射、单对象 batch；初始5°信任锚 | 原函数逐实例传其 root/native 映射，通常无需改算法 | 不将 robot_id 写入本地 batch维，不改reference/IK/信任域 |
| E `_cr12_capture_runner.py:20–185` | 单 runner 与绑定；日志需明确机器人；退役后不能继续调用原请求 | 每实例一 runner，新增日志 robot/root/product 身份；Host 在无runner时继续 session 保持与camera OFF检查 | 原请求FSM/总预算/采集成功条件不变 |
| E `_cr12_camera_mount.py:create_camera_and_fixture:127–175` | camera 已由本 link_6 推导；fixture:144 固定路径冲突 | 增 keyword `fixture_path` | 默认 `/World/CameraInterfaceFixture`；安装/光学参数不变 |
| E `_cr12_camera_capture.py:103–174` | 固定 product/Camera/observer 名；可变请求字段已是实例级 | 可选实例命名参数；创建后路径/关系/资源身份互异检查 | 原三个名称默认不变；每产品额度2，不设全局4次共享buffer |
| E `_cr12_visual_geometry.py:162–264,294–299,372–389` | 已支持 root，但单台十项 schema不可混成二十项 | 逐实例 mapping/apply/seal；创建全部机器人相机后再 seal；无需改几何规则 | 原十项覆盖与默认不自动推广；运行期不撤销 |
| E `_cr12_lifecycle_host.py:47–76,98–215,246–345` | domain M1/N2、单 session/runner/绑定、单计数、无 idle、结果只有 cr12 | 显式固定实例 specs/contexts、四任务、共同子步循环、两套保持、一次report/delivery、全局terminal | 默认原 normal/cancel profile；不复制第二套 Store/Host |
| T `assignment_cr12_execution_adapter.py:168–181,224–263,293–402` | 限E1/M1/N2/robot0、单binding/pending/delivery；continuation要求当前artifact==birth | 同一类加入固定M2/N4模式及两槽；plural bind/report/ACK，保留全域一次 publication/transaction | 单数M1接口包装同一内部逻辑；保留 exact type检查与receipt来源约束 |
| E `run_cr12_lifecycle_integration.py:22–139` | normal/cancel前置、单任务顺序、期待2成果/单资源、任意无可领任务报错 | 保留现入口；新双机入口复用 Host/初始化/收尾，只放固定proposal调度与M2验收 | 不把新case塞入旧取消前置或重跑单机normal |
| T domain/facade/claim/terminal 核心 | 已有按M/N张量的真实事务；名字中的M1 batch是契约阶段名 | 复用，不改 authority、claim authority、consume ledger 或 public gate | Phase B 与已有契约保持 |

**拟新增唯一生产入口**：`E/run_cr12_dual_lifecycle_integration.py`，职责是固定 `dual_normal_staggered` proposal、上述 instance specs、四任务验收与共享资源收尾。不是新 GUI 启动框架；复用现有 Windows/private/UTF8/pre-App CUDA/监督链及相机入口启动模板。固定 specs 可定义在该入口并传现 Host，不需要另造场景配置文件或资产。`E/_cr12_lifecycle_host.py` 内拟有独立 `RobotExecutionContext`，持有本台 session/runner/binding/recorder/receive_context/contacts/visual/camera；global sim/domain/clock/failure 状态由 Host 持有。实例 recorder 必须分开结果槽与输出子目录，不能两台覆写 `resources['camera']` 或同一个 `last_request`。

拟新增针对性测试 `Q/test_cr12_dual_lifecycle_integration.py`，可在现有 adapter/camera CPU 测试内追加局部用例；不用新测试框架。本轮未创建这些实现/测试文件。未来回撤只移除新增入口/测试及本补丁的明确 hunks；不得 `reset/restore` 用户整体工作区、资产或现有提交。文中拟新增 API 不是当前可执行命令。

## 5. 一次初始化与跨机碰撞监测

### 5.1 初始化顺序

1. 一次 App 启动，保留已审 Windows/private/D3D12/cuda:0 和外力逐迭代设置；一次 SimulationContext、共享 ground/light。创建两个明确 root/Articulation，分别 inspect、本 root world anchor 校准。
2. 首次 physics 初始化前，完成两台 camera prim/fixture、各backend `prepare()`创建专属product并立即OFF、各自十项 visual apply、contact sensors；所有 compose 完成后各自 seal。不能先 seal robot0 再在其 subtree 增 Camera。root/reference异常此时停止。
3. **只调用一次 `sim.reset()`** 建立 native views（既有单机初始化观测为共同2物理步，未来检查不因M2变4）。逐台检查真实prim/name映射、7/6/10 schema、参数/关节/根约束与独立contacts。
4. 各台合法 q/dq 初态写一次、targets、各自 `robot.reset()` 清局部buffer；后者不同于 scene reset，不推进全局clock。旧 helper `initialize_fixed_cr12_state:584–588` 即此用途。各backend此时仅执行 `initialize_off()`，不重复prepare/product创建，保持已接受的pre-init prepare→共同reset→initialize_off顺序。
5. 两台初态均完成后，按 `refresh_initial_camera_publication` 拆出的共同阶段 **global `sim.forward()` 一次**，逐台核对前后 native状态、clock、Camera/Fabric光学关系。该 forward 不应额外物理步；不能每台做一次独立刷新后错用不同基线。
6. 每台初始化 controller/integrator/Jacobian/frame/trust anchor，从实际scanner冻结全局四目标；进入共同OPEN。未分配时也有合法保持，不能造假goal来绕过准备检查。

本地 `articulation.py:1150–1188` 在每个 cfg prim 下解析 articulation root并创建 view；两对象明确路径避免多匹配/错误batch。初次运行须确认两个native view所有body属于各自root且互异。首次参数/readback失败不可通过第二次reset或teleport修补。

### 5.2 自碰撞、跨机与 contacts

每台保留 `_check_geometry` 原 self/ground 规则、每侧2mm余量和 arm-ground 检查；agv-ground支撑是允许接触。跨机用**所有**十对十shape角点world AABB，加原余量，逐pair直接分离；相同 link 名、相同 body 索引、agv-agv 都不免检。100 pair 可按整机包络分离粗筛，但需记录覆盖100的逻辑，不把本机相邻体例外移到跨机。首版不增加 OBB、不缩碰撞体、不设置互不碰撞组、不修改 PhysX 碰撞启用状态。

当前 `_make_contacts` 是每台7个单body sensor，每个过滤本机非相邻 body，非agv另含ground；**当前未监听另一台**。`_check_contacts:347–389` 读 `force_matrix_w` 而非仅net force，并核对路径、filters、shape `(1,1,filter_count,3)`、时间戳，原力阈值0.1N。拟增加 `extra_filter_paths`，每个本体sensor均加入对方全部7个body路径；每台7个、共14个单body view。对方full path作为归属键，避免同名link覆盖。

本地 `source/isaaclab/isaaclab/sensors/contact_sensor/contact_sensor.py:49–57,251–281,313–343` 支持 one-to-many filtered contact；多个body要独立sensor。未来读回每个sensor实际body、全部filter映射、pair力矩阵维度与fresh时间；验证没有跨机过滤/碰撞组掩盖接触。pair force是body聚合，不能据其0证明全部shape路径连续安全，故与实际shape/frame守卫共同使用。

起始状态在一次reset/初态发布后检查；拟下发目标q经本台原准入及跨机联合命令几何检查；每次实际物理步后检查两台actual包络、root/frame、contacts。未来检查轨迹的参考必须是实际控制器提交的两份q_cmd，不以本文witness代替。碰撞/无进展/超期按现有失败类别结束；共享native失效不继续另一个robot。layout与guards是此固定场景的有界执行保护，不宣称主动避障规划器或任意障碍安全。

## 6. 唯一时钟与混合阶段

保留 `dt=1/120 s`、D=12、`render_interval=2`。一个Host transition对应共同12子步、0.1 s，最多6次全局render，最后一次真实authority事务；不因两台变24子步或12次render。

每子步拟执行：

```text
读取两台同一global边界actual
→ 两套session.prepare（active或IDLE_HOLD），先验证全部命令及跨机预测关系
→ 分别submit各自joint position/velocity targets（此处不step）
→ sim.step(render=False)恰一次
→ 两台actual/native/frame/self/ground及全局cross/contact检查
→ 为各Camera缓存该台实际render context
→ cadence到期时sim.render恰一次
→ 各session.finish、Camera事件/runner FSM/OFF观察各推进一次
```

如果后一个submit异常，即使先一个已写target也不再step；全局fail-stop并保留已发生事实，不通过回写状态“撤回”命令。两套session使用共同global step/clock，连无任务时期也更新自己的index、actual缓存与guard；不能一台等待数据时阻塞循环。并行指真实仿真时间上执行区间重叠，不要求Python多线程或宣称GPU内部并发。

当前 `_cr12_scan_executor.py:364` 在没有goal时拒绝prepare；因此初始等待不是简单 `runner=None; continue`。拟增加明确的**无绑定反馈保持**：在实际初态目标保持、每步写正常执行器targets、继续guard；不创建假claim、假request或completion。请求已退役时延续上一合法保持q_cmd，停止该请求deadline但保持控制/设备守卫；不能清零q_cmd或每步回写joint state。不同机器人controller/integrator/reference/到位窗口/deadline/原始信任锚/pending/custody完全独立。同台跨任务保留controller、integrator、q_cmd、global计数和初始信任锚；每次新claim建立新的请求身份、reference、到位窗口、deadline和pending，旧custody独立留存。

| 混合状态 | 本台处理 | 另一台/全局行为 |
|---|---|---|
| A MOVING，B WAITING_DATA/CLOSING | A照常运动，B原目标反馈保持与相机FSM | 共同step/render，无阻塞等待 |
| A请求终态待块末，B仍执行 | A继续最新保持/OFF/资源检查，保留pending | 块末重新审资格后聚合；不提前单独提交A |
| A退役后等待下一OPEN，B继续 | A无绑定IDLE_HOLD，不复用已退役runner | 下一OPEN可仅给A新claim，B保留原binding |
| A两个局部任务完毕，B还有任务 | A OFF、资源保留、反馈保持，无假UNAVAILABLE | 全局episode未结束，B继续 |

authority 的 `eligible_work`（`assignment_lifecycle_transaction_runtime.py:1723–1737`）按 AVAILABLE/owner/failed_pairs判断，**不包含本方案物理allowlist**。所以A无本区任务时P2仍可能 NEEDS_ASSIGNMENT，不能硬写 WAITING_FOR_TASK。Host的IDLE_HOLD是物理执行状态，与P2状态分离；合法NO_CLAIM由resolver处理。没有新请求不代表相机或机器人损坏。

## 7. 同批 claim、多结果与 receipt 退役

### 7.1 一份 adapter 与两份 binding

保留一个 `Cr12ExecutionAdapter`。现有 `_observed/_admitted/_report/_committed/_last_ack` 仍为每全域调用一份；binding/pending/custody/局部delivery按robot_id两槽。domain `assignment_event_profile_runtime_domain.py:698,1333,1427–1458` 的typed report、一次producer与事务路径保持；不以新类型绕过其exact-type来源检查。

拟新增plural入口 `bind_effective_assignments(assignment)`、`build_report(boundaries_by_robot=...)`、`ack_authority_deliveries(outcome)`；旧单数M1入口包装同一内部逻辑。`record_pending(binding,...)` 和退役必须通过真实binding中的robot_id定位，不从最近活动robot猜测。idle返回独立OFF/保持/健康证据，无active binding，不借旧request ID。

初始 raw `[[0,2]]` 一次真实claim batch可产生两份binding。源码 `assignment_lifecycle_transaction_runtime.py:4547–4556` 每claim request分配token，`assignment_initial_claim_runtime.py:864,909–925` 把它及按robot列的requested/effective张量放入整个artifact；**同一个token可覆盖两台**。唯一request键包含 `(run_instance, domain, episode, robot_id, task_id, claim_token)`，并保留birth artifact与publication来源，不能只用token作全局唯一键。

当前adapter `:240–242` 要求current artifact就是本binding的birth artifact，在另一台新claim时会误拒。拟按本批artifact的对应env行/robot列核对：非负为本台新claim；−1表示本批未给本台新claim，可以保留原binding，但必须核对episode、owner、task、连续publication链及原birth来源。物理publication正常会将 `assignment_artifact=None`（transaction runtime:3542–3566），不能因此遗失已验证binding，也不能跳过未观察的publication靠相同owner重建来源。

facade `assignment_event_runtime_facade.py:633–636,675–685` 本已提交整个requested batch且要求一次Store/P2版本变化。这里代码名“M1 batch”不是只允许一个机器人，不需要修改这一真实authority接口。

### 7.2 块末一次事务

同一物理块末先读取两台最新boundary。对每个pending验证owner、claim来源、当前prestate、product OFF、最新保持/设备健康。C另外要求本次raw有效持有；健康无数据取消R要求最新无数据检查，不要求也不伪造raw custody。数据采集成功、PNG保存、关闭成功分别记录。PNG写盘失败不否认已取得数据；已取得数据而关闭失败也不回写成未采集，但不具备正常C提交/下一动作资格。

两台同块完成task0/2时，C只在 `[0,0,0]` 与 `[0,1,2]` 为true；一台完成另一台继续时另一台C/R/U均false并保留binding/ownership。普通业务取消可R，不自动F或永久failed-pair。把完整C/R/U等合成**一个typed report**，由同一producer创建facts，一次transaction处理全域同一prestate/generation；不能两次finalize。

固定顺序：

```text
全部终态资格块末复核
→ 单report / 单producer / 单authority transaction
→ 验证并保存真实outcome、receipt及所有robot-task提交效果
→ 逐pending确认其对应效果（允许共享receipt_id/facts token/generation）
→ 各Camera/request/executor/adapter槽退役
→ 下一OPEN才接新请求
```

批ACK先核对全部效果并保全全量history，再清各槽；第一台ACK不可清全域pending而吞掉第二台。adapter旧 `:369–402` 的单槽清理必须改为此顺序。若事务整体已成功、某台退役失败，保留全部authority效果及raw/metadata，不抹掉另一台成果、不重发整批C/R。经既有 `report_post_authority_bookkeeping_failure` 和O1路径 poison共享domain并停止；不承诺另一台在此情况下继续运行。

## 8. 双Camera产品隔离与按需ON/fresh/OFF

每台复用当前虚拟 `T_SC`、640×480 RGBA、pinhole参数、专属product以及按任务启停；fixture仅跟随本实例初始化关系创建一次，运行中不改测试板颜色、镜头或光轴。图像相同与否不作隔离/fresh依据，不升级扫描成功门槛。

### 8.1 静态已确认与最小调整

安装API来源（本轮只读源码，未import）：`P=C:/isaacenvs/isaac45_harl/Lib/site-packages/isaacsim`；Camera为 `P/exts/isaacsim.sensors.camera/isaacsim/sensors/camera/camera.py:379–389,436–480`；Replicator根 `R=P/extscache/omni.replicator.core-1.11.35+106.5.0.wx64.r.cp310/omni/replicator/core`，其 `scripts/create.py:1526–1591`、`scripts/utils/viewport_manager.py:75–96,260–271`、`scripts/annotators.py:1295–1357` 支持产品创建/销毁和独立Annotator实例的判断。Replicator版本来自实际安装目录标识；本轮没有另核Camera扩展package.version。Isaac Sim4.5运行环境来自已接受单机记录，不因找到接口就宣称双产品已通过。

- `E/_cr12_camera_capture.py:121–158` 的 `_request/_snapshot/_errors`、frame去重表与计数都是实例字段；回调 `:80–96` 通过本Camera的owner引用，不存在现成的共享请求buffer。新实例化循环须factory绑定各自receive_context，不能复用一份dict或捕获循环最后一个context。
- `:162–174` 已 `force_new=True` 创建产品、立即OFF并显式传入Camera；`frequency=-1` 保持。仅把固定name参数化；本机安装Replicator具名创建会强制force_new，但实际会自动找next-free-path，故必须核对返回路径、Camera关系、实际handle，不以名字字符串证明唯一。
- Camera已有product的initialize分支仅设置该product分辨率/Camera关系，不另创建产品；rgb与ReferenceTime annotator attach本产品。每台分别readback，避免两Camera误绑同产品。
- `:85–89` 在super更新前过滤本product，独立observer `:389–392` 再过滤；去重 `:371–405` 是每backend。两product同一次render收到相同frame/time是合法的，不引入全局frame唯一约束。fresh身份至少包含product、binding/capture、真实source frame/time及本次ON基线；每台复制本product实际buffer，不用“全局最近帧”。
- 实际采集开关仍是本 `HydraTexture.updates_enabled` 属性写入/读回 + 本Camera pause/resume；不只停写盘、不暂停整个timeline、不常开筛帧。独立observer仍观测产品事件，guard每台ON/OFF状态及请求来源。
- `:537–552` 每次实际全局render给每台最多一次 `render_opportunity=True`；其他检查False。多个product/viewport事件不可累计多次quiet opportunity。A OFF时B事件可以增加A见到的global事件数，却不应增加A的own-product计数或改变quiet基线。
- `:451–514,596–624` 逐实例custody/receipt退役及release；只detach/销毁本产品和本订阅。不删除全局 `/Render`，不STOP。提前无任务者保持资源OFF到全局收尾，之后各release一次，最后唯一App close。

本地Camera `camera.py:285–286,467` 的回调会同步evaluate共享 `/Render/PostProcess/SDGPipeline`；静态接口可用不保证底层双产品调度顺序或GPU开销。应采样每台prepare/initialize/begin/OFF/release计数、真实resource identity、订阅归属和交接数组不变性。日志/PNG路径分 `robot_0/task_0/<claim>/...` 等，并在metadata同时记录run/env/robot/task/claim/product；不要只依赖文件名。

### 8.2 双机专门证据

首case需明确记录一个区间：A产品OFF读回且本产品无新增采集事件，B产品ON且实际接收本次fresh数据，两者使用相同global render索引；这证明没有靠关闭B/暂停timeline确认A。每产品的ON帧来源各自合法，同source frame号不判冲突。A pause/retire后B的identity与接收须不受影响。若首case缺少该实际区间，报告“相机隔离覆盖不足”，不能用两张不同图片或源码检查替代。

## 9. 全局terminal、逻辑rebuild与失败范围

`assignment_lifecycle_transaction_runtime.py:1739–1755` 按环境全部任务决定终态。四任务完成时旧episode保留coverage `[true,true,true,true]`、真实更新owner/任务状态与两台completion_count **`[2,2]`**；owner退役后的实际值遵循authority，完成归属保存在receipt/history，不能人为要求completed仍有owner。任一台完成自己的两任务不使Host finished。

共同逻辑rebuild前，两台均须OFF、无未交付请求、所有已确认请求成功退役且无残留runner/局部请求槽、actual保持和资源健康。旧terminal artifact/sidecar先封存；再以 `[1,4]` AVAILABLE/owner−1、`[1,2]` NEEDS_ASSIGNMENT统一开启新episode，保留两台actual/q/dq/q_cmd与唯一global clock、不做物理reset、不重建Camera/控制器、不再写joint state。刷新episode观测基线；旧结果/数组/receipt仍可读。合法rebuild和五元组返回后，facade复制历史并ACK，terminal pending slots为0；E1只有**一条environment历史行**，不是两条robot终态。

`assignment_event_profile_schema_contract_v2.py:742–755` 静态公式代入M2/N4：actor=`5MN+24M+14N+1`=**145**，critic=`5MN+23M+14N+1`=**143**。本轮仅公式/源码核对，未来需实际builder/sidecar CPU检查；不沿用M1/N2的62常量、不创建网络或宣称可变规模policy。Host五元组保留观测、按两agent key的零reward占位（明确无learner）、terminated/truncated及info；两个agent的done均来自同一个authority环境终态 `[1] bool`。`assignment_event_terminal_transport.py:367–400,438–504,576–591` 会OR agent done，因此尤其不能把单台局部完成直接当done。

| 失败层级 | 最小处理与边界 |
|---|---|
| 健康、无数据、已关闭/保持的请求级取消 | 可形成结构化R，另一台正常continuation；不天然销毁另一相机。首runtime不注入取消，CPU覆盖 |
| 已取得数据但关闭/退役失败 | 保留acquired/custody及任何已提交receipt；禁止本台接新任务；按现O1失败范围全局停止，不能改写成果 |
| 某机器人确认不能继续接单 | 真正健康/可用性变化才形成契约U；普通无本区任务不是U。首版不实现sticky恢复/移动中制动 |
| camera资源/native getter/physics/render基础设施异常 | 首个正常case fail-stop，保存实际阶段及两台状态；不伪造C/R来凑完整事务 |
| 事务后本地bookkeeping异常 | `assignment_event_profile_synchronous_runtime.py:470–473`→domain`:1261–1273` poison整个共享domain；保留所有提交效果，不重复提交、不承诺局部进程容错 |

## 10. 下一轮实施顺序与一个正常并行case

以下均为**待审计划，未执行，也不是额外运行授权**。

### 10.1 连续实施步骤

1. **固定实例与共同初始化**：拆分原scene/helper；参数化root/fixture/product、独立context/contacts/visual、无绑定保持；离线确认旧M1默认与映射/clock逻辑。无须为各模块单开App。
2. **双槽adapter与Host**：保持production authority，加入批binding/完整facts/多效果receipt、mixed idle与全局terminal/143维sidecar；用真实authority的小型CPU反例核对。完成新入口的确定性proposal和结果汇总。
3. **一次有界双机正常运行**：在同一App做pre-init/readback、真实并行四任务、产品隔离、terminal/rebuild/ACK及自然退出；成功即停止。只在明确局部实现错误且另有剩余额度时允许一次局部修复重试，不因未知native故障反复开App。

### 10.2 推荐 `dual_normal_staggered`（拟新增case名）

首次合法OPEN提交raw `[[0,2]]`，两台同时由真实claim进入各自小目标。robot0完成task0且receipt退役后，在最早合法OPEN提交task1。robot1提交task3必须同时满足：自身task2已完成且receipt退役；**robot0第二goal已开始至少6个Host transition（72 physics ticks、0.6 s）**。等待只影响proposal时机，robot1 OFF/反馈保持，scene和robot0继续推进。不改速度、到位标准、frequency、曝光，不丢帧或暂停simulation。

若robot0第二goal开始时robot1仍执行task2，raw应为 `[[1,2]]`；若robot0已完成本区而robot1准备task3，则用 `[[4,3]]`。实际raw依据当前P2/绑定构造，不把这些例子硬写成不看状态的脚本。

预期第一对执行有明显物理时间重叠；第二对错峰提供 A采集/关闭时B仍MOVING，以及 A完成后OFF/IDLE而B ON/fresh 的机会。**不预设同tick到位或保证上述阶段自动出现**：运行须记录各请求MOVING/WAITING_DATA/CLOSING/retire区间、实际joint/scanner变化与global步索引，计算真实重叠，并定位至少一个混合阶段和A OFF/B fresh区间。同步双C的事务分支必做CPU检查，runtime是否发生如实记录。若正常四任务完成但关键隔离区间未出现，结果分“业务完成/隔离覆盖不足”；先审阅实际时序，再决定是否另行授权一个调整OPEN错峰的最小正常case，不自动扩大矩阵。

成功依据同时包括：两真实articulation持续存在且映射正确；执行器targets导致actual运动、无teleport；四份本次fresh RGBA；每台两次ON/OFF及一次资源生命周期；实际并行/混合区间；跨机实际守卫/contact覆盖；一次每transition的authority提交；四任务两台计数、143维pre-reset sidecar、统一rebuild与facade ACK；完成记录和监督器全树自然exit0。GUI里出现两台或EXITCODE=0单独均不足。基础设施失败单列，不记录成策略零分/完成率0。

不提供假称已存在的新入口命令；下一轮实现后再从实际argparse/监督器支持生成完整命令。本轮App数为 **0**，不会请求用户额外观看单机或双机demo来替代这些证据。

### 10.3 未来CPU反例（未运行）

| 验证落点 | 具体输入/变化 | 预期 |
|---|---|---|
| instance/context映射 | 创建顺序 `[1,0]`，本地body/joint名称排序变化 | 按root/name还原robot映射；每对象batch `[0]` 不变，结果不串槽 |
| root/FK/anchor | root1 Y=2；错误注入root0 body target或resetXformStack丢位移 | 正确目标Y+2；错误路径/anchor在pre-init拒绝；不重复加origin |
| cross guard | r0/link_6与r1/link_6的bounds重叠，含agv-agv | 必检查并拒绝，不能套用同名/相邻豁免；分离布局覆盖100pair |
| 同batch身份 | raw`[[0,2]]`，两个binding共享token | robot/task不同仍合法；错robot/episode/旧claim成果拒绝 |
| 混合新claim | r0完成后raw`[[1,2]]`，artifact本批仅r0新claim | r1原birth/custody保持，raw4用于EXECUTING必须拒绝 |
| facts聚合 | 同块C(0,0)+C(1,2)；另例仅C(0,0)、r1继续 | 各一次producer/transaction/receipt；后例保留r1绑定/owner |
| receipt退役 | 同receipt含两效果；分别注入第一/第二台退役失败 | ACK不清错槽；已提交全部成果保全、不重发，全domain poison |
| Camera归属 | 两product各source frame700；错product帧；交换创建顺序 | 正确两帧都可fresh，错归属不读buffer，闭包/context不串 |
| OFF与事件计数 | A OFF/B ON，单render多个viewport/product事件 | A quiet机会最多1；B正常接收，A own-product无新增；A pause/release不操作B |
| 初始/末期idle | A未claim或两局部任务完毕，B MOVING/WAITING | A保持q_cmd/actual检查、共同clock继续，不伪造goal/U/done |
| 全局terminal/rebuild | 只完成2/4；完成4/4但一台非OFF/有pending；最后全健康 | 前两例不得正常rebuild；最终一行旧history、计数[2,2]、两台状态/clock连续、ACK清空 |
| schema/旧默认 | 实际builder M2/N4与旧M1/N2；旧单数adapter/helper接口 | actor145/critic143；旧M1默认62 critic与原路径/phase顺序保持，不启动网络或旧App |

这些测试应使用现有Q组织和真实production authority（仅CPU），不另造一套假Store作为真实性证据；Camera/clock边界可用可控替身做逻辑反例，但不能据其宣称双产品runtime通过。只跑改动相关新增及必要旧默认用例，不把全部182项或Phase B资格验证作为前置。

## 11. 资源、计数与未来运行预算

已有单机证据只读来源：`logs/scan_assignment/20261008_cr12_lifecycle_integration/attempt_01/`（normal）、`attempt_02/`（cancel）。

| 既有测量 | normal | cancel |
|---|---:|---:|
| Host transitions | 112 | 167 |
| 受控global physics / render | 1344 / 672 | 2004 / 1002 |
| 初始化physics，另计 | 2 | 2 |
| App构造墙钟 | 22.656 s | 14.328 s |
| controlled_step_begin→work_completed | 54.343 s | 104.813 s |
| 监督器全树墙钟 | 84.875 s | 126.734 s |

中间阶段墙钟含authority与收尾读取，不是纯GPU/physics benchmark。旧Kit日志 `kit_20261008_154452.log:3323–3341`、`kit_20261008_154644.log:3448–3466` 记录 RTX4060Ti、D3D12、驱动610.60、Kit表7949MB；早期FB快照分别8188MiB total/1134 used/6816 free及8188/1147/6803（对应`:2885–2889`、`:2909–2913`）。这是当时整卡初始化读数，WDDM逐进程显存 unavailable，**不是单机峰值，更不能推定双产品峰值**。两份640×480 RGBA仅2,457,600 bytes，不能代替RTX/PhysX显存预算。双articulation/14contact view/两组RGB与ReferenceTime（共4个Annotator对象）的CPU、GPU时间与显存峰值待首轮测量；不预先降分辨率、关相机、换设备/后端或串行化。

推荐下一轮预算：

| 项目 | 建议上限与计数语义 |
|---|---|
| App模式 | 保持GUI、D3D12、fresh task-private config、cuda:0、相机启用；不加headless/人工观看case |
| 请求 | 全局4、每台2；无request内部重试；每台原对象prepare/initialize各1，begin/OFF各2，最终release1 |
| 每请求phase | 原pose960、capture600、close240，总1800受控ticks；capture墙钟60s、close30s，保持 `_cr12_single_view_capture.py:11–16` |
| Host horizon | **420 transitions / 42 s simulation**；新请求须保留原1800+12块尾额度，不临近截止强行接单 |
| global physics/render | **5040 / 2520**受控上限；共享初始化2步另计，physical总计目标上限5042；不能算成10080实际scene steps |
| 每机器人检查/保持 | 每台最多5040受控ticks（含idle），合计最多10080次本机检查；cross检查每globaltick一次 |
| 每product | ON期间实际事件独立记录；每台最多2520个global render机会，OFF只计属于关闭观察窗口的机会；全局render不翻倍 |
| authority | 每transition一次，共至多420；claim批次另记，不误当physics子步或逐机器人事务 |
| 初始化/退出 | 一次scene reset，逐实例初态写入，单次共同Fabric发布；两台健康检查/release后唯一App关闭 |
| App次数 | 主运行1；仅明确局部实施错误最多修复重试1，合计最多2；首轮成功即停止 |
| 全树墙钟 | 每App **480 s**（含启动、运行、退出），其中App构造上限180s；保留现owned-process监督与失败分类 |

预算约为单机实测全树84.9–126.7s的宽裕上界，同时覆盖双机状态/contact/RTX增加及四请求；不假定耗时不变或精确翻倍。480s也不保证在所有phase耗尽时还能跑满5040步：先达到任何有效边界即失败并收尾，不无限等候、不制造健康终态。初始化比既有2步更多或clock异常应说明失败，不默默提高预算。

未来只保留四张实际采集PNG、每请求小型metadata、关键phase/共同step摘要、两个产品identity/OFF计数、最终authority/terminal和监督器退出结果及必要Kit日志；不逐physics步写庞大raw dump。基础设施失败、采集结果、保存结果、OFF、authority提交、退出分别记录。

## 12. 真正共享任务的边界与审阅决定

本布局在原固定底盘、名义初态每轴±5°信任域内，scanner位置相对各自初态的保守位移半径为 **0.410458435 m**；两初态相距2m，球间仍有 **1.179083130 m** 分隔。因此此名义局部域没有相同位置候选，更不用说相同完整pose。该结论限定当前刚体FK与5°盒，不推断整个CR12工作空间不可达。运行实际初态仍需核对；首版共享任务状态记 **NOT_ESTABLISHED**，不阻断本区四任务并行接入。

后续跨机器人转交必须另选共享布局/起始构型及必要运动能力，先建立两台从各自合法状态均能执行的**同一global task_id、同一冻结scanner world pose**；前owner关闭/收尾、authority释放后新owner真实claim，旧回调/成果不能改写新attempt。复制两套局部任务、认领时重定位目标、给不同pose起同名都不成立。本轮不重叠摆放、不关闭碰撞、不放宽5°、不加底盘运动、不做大规模IK/布局优化。

**需GPT/用户审阅的只有下一轮方案与运行额度**：是否采用本报告推荐的“2m同朝向布局、E1/M2/N4局部allowlist、一个共享Host/双显式Articulation、一个错峰正常case、主1+局部修复最多1、每App480s”整套最小范围。当前没有必须另向用户索取才能完成本设计的信息；原角色、扫描成功、独立Host方向和停止单机人工观看已确定，不重问。

首次运行待确认项不是本轮批准已获得的事实：第二USD引用/anchor/physics映射、双Camera product隔离与显存、共同clock/并行时序、四任务terminal/ACK。实现时可局部处理的是命名参数、两槽日志/结果、old-default wrappers；共享任务、真实构件规划、一般故障恢复、策略/训练/可变规模及实体标定均后置。

## 13. 本次实际操作、文档与停止边界

已读取适用 `AgentRead/AGENTS.md`、TASK_PROGRESS、REPORT_INDEX、单机实施报告及本任务直接相关源码/契约/安装API；只读记录branch/HEAD/status，定向读取已有两次单机JSON/Kit日志用于成本和边界，不做历史全量审计。核对指定解释器为 `C:\isaacenvs\isaac45_harl\python.exe`，进行标准库文本/AST/JSON/二进制头/模块查找与纯CPU数学；部分局部路径/字段读取不匹配后调整只读方法，没有因此启用runtime或改依赖。

实际离线计算命令（工作目录为仓库根）如下，仅复现数学，不创建App入口：

```powershell
& 'D:\miniconda3\Scripts\conda.exe' run -p 'C:\isaacenvs\isaac45_harl' python -B logs/scan_assignment/20261008_cr12_dual_robot_plan/repro/check_dual_layout.py | Set-Content -LiteralPath 'logs/scan_assignment/20261008_cr12_dual_robot_plan/repro/offline_layout.json' -Encoding utf8
```

检查产物只有一个只读计算脚本和一份紧凑包络摘要，没有逐样本dump。之后仅修正脚本中Y轴选择的说明注释，计算未变、未重复运行。标准库AST与JSON关键margin核对完成；**未运行未来CPU反例、旧182项测试或任何单/双机App**。当前pxr离线不可用，因此USD组合关系限制已在第3.3节明确保留。

文档变更为本主报告、`AgentRead/TASK_PROGRESS.md` 当前状态小范围更新、`AgentRead/REPORT_INDEX.md` 扫描主题导航；更新用户已审单机/新HEAD/停止人工观看及双机设计状态，保留历史报告和Phase B CLOSED。新增文档链接、范围差异与空白检查随交付核对，不扫描旧全目录链接/哈希。离线辅助文件放L/repro，**AgentRead本轮没有新增Python**。L受既有Git忽略规则影响，仅本机可取；主报告已包含关键方法、数值与限制，不暗示新checkout自动带日志。

未修改生产、测试、资产、运行配置、installed packages或Windows配置；未启动Isaac/Kit/CUDA/渲染/仿真/训练；未创建双机入口/场景/相机、attempt_01、runtime_result、截图或ZIP；无Git add/commit/push/reset等写操作，无历史移动/删除/恢复。文档交付后停止，等待GPT/用户审阅，不自动进入实施或消耗未来运行预算。

## 14. 辅助证据对应表

以下链接相对本报告；logs为本机已有/新增辅助证据，未加入Git。源码证据以正文给定实际路径、符号及行号为准。

| 证据 | 用途与边界 |
|---|---|
| [本轮离线计算脚本](../../../../../../../../logs/scan_assignment/20261008_cr12_dual_robot_plan/repro/check_dual_layout.py) | 只读URDF/mesh和已留单机bounds，NumPy FK/包络，含公式；不运行App/IK |
| [本轮布局摘要](../../../../../../../../logs/scan_assignment/20261008_cr12_dual_robot_plan/repro/offline_layout.json) | 四目标、两轴候选、十shape摘要、201构型guard与100跨pair界；非runtime PASS |
| [既有normal结果](../../../../../../../../logs/scan_assignment/20261008_cr12_lifecycle_integration/attempt_01/result.json)、[监督结果](../../../../../../../../logs/scan_assignment/20261008_cr12_lifecycle_integration/attempt_01/supervisor_result.json) | 既有单机bounds/成本/自然退出；不代替双机验证 |
| [既有cancel监督结果](../../../../../../../../logs/scan_assignment/20261008_cr12_lifecycle_integration/attempt_02/supervisor_result.json) | 第二个已有成本样本；本轮未复跑取消 |
| [既有normal Kit日志](../../../../../../../../logs/scan_assignment/20261008_cr12_lifecycle_integration/attempt_01/kit_20261008_154452.log)、[cancel Kit日志](../../../../../../../../logs/scan_assignment/20261008_cr12_lifecycle_integration/attempt_02/kit_20261008_154644.log) | 第11节GPU/后端/早期显存字段来源；不是双产品峰值 |
| [已接受单机主报告](CR12_EXECUTION_LIFECYCLE_INTEGRATION_REPORT.md) | 完整旧配置、原始日志/PNG入口及原结论；当时待审状态不回写 |
