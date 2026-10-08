# CR12 扫描前视觉几何一致性检查、显示修复与有界渲染报告

执行日期：2026-10-04，Asia/Shanghai（UTC+08:00）。本报告状态：**局部差异已定位、显示 helper 已实现、四张渲染对照已取得；整体运行验收 FAIL，等待 GPT/用户审阅。**

## 1. 结论、范围与接受边界

源 visual 并未被均匀盒惯性或碰撞近似替换。本轮对照原 OBJ、派生 URDF 与真实加载的 USD，20 份 visual/collision 表示均找到独立对应，米制 body/link 坐标下的点与三角形几何匹配。当前 viewport 同时显示了正确 visual 和 purpose=guide 的 collision 几何；**仅隐藏已确认独立 collision 的十个 Mesh 后，车体层次与末端支架的开放结构重新可见**。这支持用户所见两处“封闭/填充”观感的一个明确原因，不等于所有外观差异已被唯一解释。

采用用户允许的 **B 路线：精确 collision-only Mesh 的 render visibility 覆盖**。新增小型显式 helper，在匿名 session 子层写十个 `visibility=invisible`；不修改目的用途、不新增替代 visual、不修改或保存原 USD，不关闭真实碰撞。旧入口默认不接入该 helper。

**不能交付整体 PASS**：第一个 App 因 timeline 暂停 API 的即时状态检查失败，随后监督器收尾又出现本轮参数遗漏；局部修正后，第二个 App 成功保存四幅同视角原图，但在撤销/重应用覆盖后的 native `get_masses` 读回发生访问异常，目标进程退出码 `0xC0000005`。最终 native 物理不变性、完整完成记录与正常关闭均未通过。已用 **2/2 App**，按本轮停止条件不再运行或修改实现；不提供宣称已通过的新人工运行命令。

| 判定项 | 本次结果及证据边界 |
|---|---|
| visual 来源与差异定位 | 源 OBJ→派生→USD 的 20 项几何映射通过；guide collision 同时可见及两处遮挡变化有属性与图片支持 |
| 修复实施与加载 | 显式 helper 已实现，首次实际应用及十项有效 visibility 已记录；完整生命周期验证未通过 |
| 原资产/配置保护 | 28 份原输入与 v1 文件、15 份既有代码未变；真实 user.config 字节/大小/mtime 未变；最终 native 参数前后相等 **未完成** |
| 同视角渲染 | 四张 1280×720 原 PNG 已保存，同组视角/光学/分辨率一致；整次运行仍 FAIL |
| 用户外观确认 | **PENDING_USER_REVIEW**；scanner 顶部在近景中有裁切，不能作为整套头部外观验收 |
| 扫描相机与采集 | **NOT_IMPLEMENTED / NOT_VALIDATED**；viewport 截图不是扫描数据 |

用户本轮已确认：大幅 joint_3 demo 完整外摆、保持、返回、保持，动作平稳、未见明显异常；结合此前数值审阅，该 demo 已获人工接受。此反馈只适用于该 demo，不推广六轴、全工作空间或全部碰撞情形。marker“显示比较明显”的反馈保持。Phase B COMPLETE / GPT REVIEW PASS / CLOSED、basic drive 与 formal pose 既有接受结果不变；OBB 精化仍需显式选择，不自动推广旧入口。历史报告不回写。

## 2. 路径、方法和真实来源

本报告定义仓库根为 `E:/Project/IsaacLab_HARL`，任务目录 **T** 为 `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator`，资产目录 **A** 为 `T/assets/rokeaCR12`，本次证据 **L** 为 `logs/scan_assignment/20261004_cr12_visual_geometry`。HEAD 为 `24ecbad7dd1bdcd006399b64bfb757a86b71aeec`。

实际读取：

- 原 URDF：[rokea_cr12_7DOF.urdf](../../../assets/rokeaCR12/rokea_cr12_7DOF.urdf)，及其 `model/` 内 20 个引用 OBJ。
- 派生 URDF：[cr12_fixed_lift0.urdf](../../../assets/rokeaCR12/derived/fixed_lift0_v1/cr12_fixed_lift0.urdf)。
- 现有 USD：[cr12_fixed_lift0.usd](../../../assets/rokeaCR12/derived/fixed_lift0_v1/usd/cr12_fixed_lift0.usd)，以及其 `configuration/` 下 base/physics/sensor 三个现有 USD 层；v1 共七个既有文件保持只读。
- `scripts/environments/prepare_cr12_fixed_asset.py` 的导入与后处理；当前 runtime support、资产数学模块、场景配置、Windows/private 启动支持。
- 适用 `AgentRead/AGENTS.md`、当前交接/索引及用户指定的 OBB、formal pose 报告相关段落；未重读或重验历史 Phase B。

独立 harl Python 中 `find_spec("pxr")` 不可用，四个 USD 为 USDC。因此先用标准库/NumPy 核对 URDF/OBJ，再在本次获准的 App 内读取真实 composition；未安装依赖、改 PYTHONPATH 或绕过 Kit 导入要求。对照基准是**用户确认正常的源 OBJ**，没有原 CAD，不宣称 CAD 完全一致。

### 2.1 visual / collision / frame 映射

所有 OBJ 原 `scale=(0.001,0.001,0.001)`，各自原 visual/collision origin 为零；固定链变换由派生 URDF 合并到相应 body 表示，比较时 scale 与合并 origin 各应用一次。20 项原链与派生变换最大矩阵差为 0。

以下实际 Mesh 均位于 `/World/CR12` 下；`visuals/<名称>/mesh` 与 `collisions/<名称>/mesh` 是独立 prim，身份还经资源来源、几何和 schema 核对，不凭名字判断。

| 部位 | 原 visual / collision（均在 A/model） | 派生 body 中安装关系 | 实际 Mesh 相对 /World/CR12 路径 | as-loaded 显示与确认结果 |
|---|---|---|---|---|
| agv 车体 | scanner_sys_agv_visual.obj / scanner_sys_agv_collision.obj | agv，平移/旋转零 | agv/visuals/agv_visual/mesh；agv/collisions/agv_collision/mesh | visual inherited/default，collision inherited/guide；独立且几何不同，后者遮住车体层次 |
| elevate | scanner_sys_elevate_visual.obj / scanner_sys_elevate_collision.obj | agv，平移 (0,0,0.314)m | agv/visuals/elevate_visual/mesh；agv/collisions/elevate_collision/mesh | 独立；collision 极简，bounds 相近不表示结构相同 |
| base_link | cr12_base_visual.obj / cr12_base_collision.obj | agv，平移 (0.105,0,1.062)m | agv/visuals/base_link_visual/mesh；agv/collisions/base_link_collision/mesh | 源两文件几何/字节相同，实际仍为两个独立 prim |
| link_1…link_5 | cr12_link1…5_visual.obj / 对应 collision.obj | 各同名 body，零 origin | link_N/visuals/link_N_visual/mesh；link_N/collisions/link_N_collision/mesh | 源每对文件相同，实际独立；同样存在 default/guide 双表示 |
| link_6 | cr12_link6_visual.obj / cr12_link6_collision.obj | link_6，零 origin | link_6/visuals/link_6_visual/mesh；link_6/collisions/link_6_collision/mesh | 两文件相同，两个 prim，不隐藏 link_6 父节点 |
| scanner | scanner_sys_scanner_visual.obj / scanner_sys_scanner_collision.obj | link_6，平移零、Rz=135° | link_6/visuals/scanner_visual/mesh；link_6/collisions/scanner_collision/mesh | 独立且几何明显不同；collision 遮挡支架开放结构 |
| tool/scanner frame | 原 tool 无 mesh | tool 为固定 frame；scanner 安装关系保留 | link_6/tool/scanner 为 Xform | Mesh 是上述 link_6 下的另一条分支，不把 frame 当作 Mesh，不重复旋转 135° |

十份 visual 的有效 visibility 都是 `inherited`、purpose 都是 `default`；十份 collision 是 `inherited`、purpose `guide`，guide 来自相应上级表示。未发现另外的无来源机器人 Mesh 或惯性包络 render prim。原 agv OBJ 有 12 个 group、scanner 有 4 个 group；导入实际得到每份源一个 Mesh，共 20 个。本轮解析支持同源分组聚合，但不把 group 数直接当作实际 prim 数。

所有 Mesh 点属性的有效来源均为：

`A/derived/fixed_lift0_v1/usd/configuration/cr12_fixed_lift0_base.usd`

属性路径为 `/meshes/<原OBJ文件名去掉.obj>/mesh.points`。base 层中的 `/visuals/<body>`、`/colliders/<body>` 再引用这些 mesh，root/physics 层完成 composition 与物理意见。完整 property stack 与祖先显示状态在 `attempt_02/result.json → visual_mapping.meshes`；本报告给 prim/property，不为二进制 USD 编造行号。

`prepare_cr12_fixed_asset.py:377` 明确 `collision_from_visuals=False`，碰撞采用既有 `convex_hull`。其 `_finish_imported_stage:227` 对碰撞 deinstance/属性进行既有后处理，没有复制 collision 去覆盖 visual，也没有将质量/惯量盒写成 render Mesh。本轮未改变这一代码或重新导入。

### 2.2 几何核对与结构解释

`_cr12_visual_source.py:102 load_visual_sources` 读取派生 URDF 中的 body origin 与所引用的源 OBJ；原 URDF 固定链与派生 origin 的一致性由 `L/repro/check_visual_source_mapping.py` 核对。`:197 compare_mesh` 在米制 body/link 坐标中，以 1e−6 m 容差对应点位置，比较三角形几何多重集和绕序，同时检查 bounds。支持点重排/同坐标拆点，不仅比较数组顺序或 bounds；这是针对当前模型的核对，不是通用 CAD 修复工具。

| 部位 | USD visual 顶点/三角形 | USD collision 顶点/三角形 |
|---|---:|---:|
| agv | 47,601 / 99,298 | 234 / 464 |
| elevate | 2,018 / 4,124 | 10 / 16 |
| base_link | 5,354 / 4,994 | 5,354 / 4,994 |
| link_1 | 1,571 / 2,000 | 1,571 / 2,000 |
| link_2 | 2,656 / 4,000 | 2,656 / 4,000 |
| link_3 | 1,494 / 2,000 | 1,494 / 2,000 |
| link_4 | 1,619 / 1,998 | 1,619 / 1,998 |
| link_5 | 2,053 / 3,000 | 2,053 / 3,000 |
| link_6 | 919 / 800 | 919 / 800 |
| scanner | 70,480 / 57,532 | 451 / 898 |

20 项源→USD 三角形位置及绕序均匹配，最大点差 `5.8953585815451314e−8 m`，最大 bounds 差 `5.640322342514992e−8 m`；读到 `subdivisionScheme=none`、`orientation=rightHanded`、无 holeIndices。源 scanner visual 为 70,498 顶点，USD 少 18 个，但双方唯一位置均 28,795、全部三角形几何/绕序匹配，不能据顶点数量变化判损坏。这里不验收 CAD 材质、法线/着色一致性或逐像素一致性。

车体 visual 的 body-local bounds 约为 [−0.527,−0.430000031,−0.052999939] 至 [0.527,0.430000061,1.132]m；collision 顶部为 1.1875m，超过 visual 55.5mm，且只有 464 个三角形。elevate collision 仅 16 个三角形。scanner 两种表示 bounds 几乎相同，却分别为 57,532 和 898 个三角形；近似外包形会遮住支架中的空隙。**边界相同不能代表凹陷/开放结构相同**，本轮用全三角形核对与实际前后图片共同判断。

## 3. 原画面显示了什么与唯一主要修复

### 3.1 实际显示设置

第二次 App 的 `display_settings_as_loaded` 读到：

| 设置 | 实际值 | 可下结论 |
|---|---|---|
| /persistent/physics/visualizationDisplayColliders | 0 | 该 collider debug 模式未开启 |
| /persistent/physics/visualizationDisplayColliderNormals | false | 该法线 debug 未开启 |
| /persistent/physics/visualizationCollisionMesh | null | 未取得明确 true/false，不能写成 false |
| /defaults/persistent/physics/visualizationCollisionMesh | null | 默认路径同样 UNKNOWN |
| /persistent/app/hydra/displayPurpose/guide | true | 当前 viewport 允许 guide 几何显示 |
| 同 namespace 下 proxy / render | true / true | 对应显示目的允许 |
| /persistent/ext/hydra/displayPurpose/* | null | 不能用另一 namespace 的配置推定运行值 |

未触发“仅关闭 debug overlay”分支，没有 `debug_disabled` 图片，也没有修改这些设置。已有 collision Mesh 的 guide 可见性与 B 路线前后对照足以支持本次局部结论；并未证明某个未知 native debug 开关的唯一状态。尤其不能由 GUI 推定此前扫描相机图像也被 debug overlay 污染。

### 3.2 helper 的精确范围

新增 [`_cr12_visual_geometry.py`](../../../../../../../../scripts/environments/_cr12_visual_geometry.py)：

- `:41 inspect_visual_mapping` 记录引用/spec、body 变换、独立 visual/collision、几何匹配、schema、visibility 继承。
- `:129 select_collision_leaves` 只接受已匹配且有独立可见 visual 的十份 collision 表示；拒绝共用 prim、未知来源、隐藏 visual 或物理后代。
- `:177 CollisionVisualOverride` / `:186 apply` 在新的匿名 session 子层，用 `Usd.EditContext` 写精确 Mesh 的 `visibility=invisible`，恢复原 edit target。仅允许无物理 schema 的 face/material GeomSubset 子节点。
- `:214 verify` 核对有效 visibility 和层内属性白名单；只有祖先 over 与十项 visibility，不含新增 typed prim、physics/drive/xform/active/purpose 意见。
- `:240 revoke` 仅在 session 子层列表仍符合本 helper 创建时状态时撤销自己的层，避免覆盖外部修改。

确切覆盖路径是：

```text
/World/CR12/agv/collisions/agv_collision/mesh
/World/CR12/agv/collisions/elevate_collision/mesh
/World/CR12/agv/collisions/base_link_collision/mesh
/World/CR12/link_1/collisions/link_1_collision/mesh
/World/CR12/link_2/collisions/link_2_collision/mesh
/World/CR12/link_3/collisions/link_3_collision/mesh
/World/CR12/link_4/collisions/link_4_collision/mesh
/World/CR12/link_5/collisions/link_5_collision/mesh
/World/CR12/link_6/collisions/link_6_collision/mesh
/World/CR12/link_6/collisions/scanner_collision/mesh
```

未 hide root/link，未 active=false，未 collisionEnabled=false，未删 schema 或 Mesh，未改 collision approximation/contact offset。首次应用后十份 collision 有效 invisible、十份正确 visual 继续 inherited/default，保留原目的用途。没有复制源 visual 叠在错误模型上；也没有新增纯 visual 实体或参考对象。

持久交付是显式 helper 源码，**没有导出新 USD 覆盖资产**；本次匿名意见随进程结束失效。未调用全 stage Save，v1 原文件不变。撤销/重应用逻辑有 CPU 检查，第二次 App 控制流也经过该段，但完整 native 复核失败，不能把当前 live 场景应用时序宣称可安全复用。

## 4. 同视角真实渲染对照

以下均为 `attempt_02` 原始 PNG，不裁剪、不修图。每张 1280×720、15 次 UI update（12 次预热及 3 次截图完成等待），四张合计 60 次；每个视图低于授权 60 轮上限。两张 as-loaded 先完成，随后一次应用十 Mesh visibility 覆盖，再完成两张 corrected；没有混入 debug 开关、材料替换、姿态或灯光变化。

| 部位 | 原画面：visual + 可见 guide collision | corrected：仅十个 collision leaf invisible |
|---|---|---|
| 车体 | ![车体原画面](../../../../../../../../logs/scan_assignment/20261004_cr12_visual_geometry/attempt_02/agv_as_loaded.png) | ![车体修正显示](../../../../../../../../logs/scan_assignment/20261004_cr12_visual_geometry/attempt_02/agv_corrected.png) |
| 末端 | ![末端原画面](../../../../../../../../logs/scan_assignment/20261004_cr12_visual_geometry/attempt_02/scanner_as_loaded.png) | ![末端修正显示](../../../../../../../../logs/scan_assignment/20261004_cr12_visual_geometry/attempt_02/scanner_corrected.png) |

车体原画面的大块封闭表面遮住下部层次与升降细节；corrected 显示车体分层/缝隙和上部波纹结构。末端原画面的粗大实心外形，在 corrected 中呈现窄支架及其开放空间。**scanner 近景顶部有裁切**，本组只能支持支架遮挡差异，不能验收整个头部、全部开口或所有角度。用户尚未对本次两处图片作新确认。

使用现有 spectator `/OmniverseKit_Persp` 和既有 viewport render product `/Render/OmniverseKit/HydraTextures/omni_kit_widget_viewport_ViewportTexture_0`；未新建 camera sensor 或 render product。视角 world 米制：

| 视图 | eye | target |
|---|---|---|
| agv | (1.75,−2.2,1.35) | (0,0,0.53) |
| scanner | (0.60,−0.70,3.08) | (0.105,−0.15,2.89) |

每组真实读回的 world camera matrix、focal length、aperture、clipping、projection 与分辨率相等。整体 manual 视图分支未进入，不冒充第三个已验证视角。

固定画面采用主线程 `timeline.pause(); timeline.commit()`，不关重力、不设置 kinematic、不每步写状态。初始化 reset 实际产生 2 physics steps；一次初始化 joint-state 写入、零 root-state 写入，额外受控保持/动作 **0 步**。截图时 SimulationContext clock 固定为 (2,0.01666666753590107)，timeline time 固定 0.05；这是两个不同计时来源，不把数值不同说成物理推进。每次 `app.update` 前后检查 clock 与 native q/dq/link pose 不变。记录支持截图期间无物理推进，未保存每次原始张量供独立离线重算。

本地 API 依据（版本和来源均来自安装源码）：

- `omni.kit.viewport.utility-1.0.18+d02c707b/.../utility/__init__.py:471 capture_viewport_to_file`，捕获既有 viewport LdrColor。
- `omni.kit.widget.viewport-107.0.7+d02c707b/.../capture.py:25,142`，异步结果/写盘；本入口不无限 wait，最多 60 UI updates，并确认完整 PNG/IEND。
- `omni.timeline-1.0.11+d02c707b.wx64.r.cp310/docs/FRAME_INTEGRITY.md:70` 及 `omni/timeline/tests/tests.py:298`，pause 为排队状态、主线程 commit 生效；不能在 pause 后立即未 commit 就要求状态已变。
- `omni.kit.viewport.menubar.display-107.0.3+d02c707b/.../display_menu_container.py:198` 的 app/hydra purpose 设置；`omni.kit.viewport.actions-107.0.0+d02c707b/.../visibility.py:143,184` 的 session visibility 用法。
- `isaacsim/exts/isaacsim.core.utils/isaacsim/core/utils/viewports.py:26 set_camera_view` 使用已有 spectator；`isaacsim/extsPhysics/omni.physx.ui/.../physxDebugView.py:482` 区分 debug 显示设置。

扩展路径位于 `C:/isaacenvs/isaac45_harl/Lib/site-packages/isaacsim/extscache/`，除条目明确列出的 `exts/`、`extsPhysics/`。本轮未改 installed packages。

## 5. 物理保护证据：哪些成立，哪些未完成

| 层级 | 实际证据 | 不能据此声称 |
|---|---|---|
| 文件保护 | 运行前冻结、崩溃后只读复核：原 URDF+20 OBJ+v1 七文件共 28 份内容全未变；15 份既有代码未变 | 文件没改不等于运行中所有 native 状态复核通过 |
| 初始化 USD/native | 保存 7 body、6 活动轴、唯一 root fixed joint、10 collision、tool/scanner frame 与初次 mass/COM/inertia/drive 等读回 | 这些初态数据不是覆盖之后的 native 参数比较 |
| 显示意见 | 首次匿名层白名单及有效 visibility 已保存；十个属性，不含物理/几何/变换意见，没有新增物理 schema | render-only 意图不能代替 native 生命周期验证 |
| 截图期间 | 60 次 update 周围的 clock/native q/dq/link pose 检查未报错，四张截图及各自 clock 已保存 | 没有覆盖撤销/重应用之后，也不是每步张量独立离线复算 |
| 撤销/重应用后的 composed 属性 | 异常栈抵达入口 :254，之前 :252–253 的 `physical_snapshot` 相等检查未抛错；只能作为控制流推断 | 对应最终字段未落盘，不能写成完整持久化 PASS |
| 最终 native 参数 | 第一项 `get_masses` 发生访问异常，后续 COM/inertia/drive 比较未完成 | **native 物理不变性未验证，整体未通过** |
| native 碰撞形状 | 未读取 cooked convex hull 顶点；collider mesh/approximation/enabled 的证据来自 composed USD | 不能宣称重新验证 native hull 形状或完整碰撞安全 |

`physical_snapshot:156` 比较 robot 子树的 schema、active、physics/physx/drive 属性、关系、xform、points/face topology 等摘要，排除显示意见。它不覆盖所有仿真全局 native 内部状态。原 contact/rest offset、pair 规则、AABB/OBB、PD/effort、solver/dt/gravity 没有修改。

场景继续使用既有 setup：root 在地面上抬 0.053m，既有 helper 在匿名场景层对齐 root fixed anchor；这是接受的初始化，**不是本次 render helper 的物理改动**。dt=1/120、TGS8/2、重力 (0,0,−9.81)、baseline PD、fixed-base/lift0/v1 均继承。external-forces 显式 on 在 after_apply / after_first_reset / before_render 三次 composed 读回 true；无 native scene flag getter，退出前读回未到达。

真实 source 配置为 `C:/isaacenvs/isaac45_harl/Lib/site-packages/omni/data/Kit/Isaac-Sim/4.5/user.config.json`：114100 bytes，SHA256 `9b3b72015f7e8ca7a74ad179a81329bc3f00966862dd0ce8f831831a12dea625`，mtime_ns `1790759017622695800`，前后不变。每次创建新 private，实际只改 width/height/maximized 三项（−1/−1/true→1440/900/false）。第二次 Kit 重写 private 格式，语义差异 0，source 不受影响；监督 L0 隔离为 true，最终整体仍 FAIL。

崩溃后仅做文件/证据检查，`post_run_static_checks.json` 在 23:22:23+08 记录最终冻结的 53 项未变（28 资产、15 旧代码、3 新实现、3 新测试、4 repro 输入）。这个小范围冻结用于本轮保护，不是全仓库或历史库存审计。四张 PNG 字节数/hash 与运行记录一致，未重写失败 result 或原日志。

## 6. 实际启动、失败、修正与预算

解释器核对为 `C:/isaacenvs/isaac45_harl/python.exe`，Python 3.10.20，UTF8=1。两次 cwd 均为 `E:/Project/IsaacLab_HARL`；Conda 父监督保留已有环境，并为目标进程明确 UTF8，GUI/D3D12/cuda:0、headless/cameras/livestream/XR=0。experience 为 `apps/isaaclab.python.kit`。沿用已有 Windows helper、pre-App CUDA 与独立 CR12 setup；没有重排初始化。

以下是**已发生的历史命令，不是新的运行授权或当前推荐人工命令**。监督器实际子命令、argv、环境白名单与 cwd 完整保留在各 `command.json`；其共同目标入口为 `scripts/environments/inspect_cr12_visual_geometry.py`，参数包含 `--usd-path A/derived/fixed_lift0_v1/usd/cr12_fixed_lift0.usd --device cuda:0 --external-forces-every-iteration on --info`，独立 output/private 路径，并由已接受 helper 形成 `--/app/vulkan=false`。实际 backend 以日志为准。

```powershell
& 'D:\miniconda3\Scripts\conda.exe' run --no-capture-output -p 'C:\isaacenvs\isaac45_harl' python -X utf8 -u 'logs/scan_assignment/20261004_cr12_visual_geometry/repro/supervise_cr12_visual_geometry.py' --attempt-dir 'E:\Project\IsaacLab_HARL\logs\scan_assignment\20261004_cr12_visual_geometry\attempt_01'

& 'D:\miniconda3\Scripts\conda.exe' run --no-capture-output -p 'C:\isaacenvs\isaac45_harl' python -X utf8 -u 'logs/scan_assignment/20261004_cr12_visual_geometry/repro/supervise_cr12_visual_geometry.py' --attempt-dir 'E:\Project\IsaacLab_HARL\logs\scan_assignment\20261004_cr12_visual_geometry\attempt_02' --repair-kind api_call --repair-reason 'Apply queued timeline pause with main-thread commit without a physics update; fix supervisor completion argument and preserve first-attempt missing-exit evidence honestly.'
```

| 项目 | attempt_01 | attempt_02 |
|---|---|---|
| 本地开始 | 23:02:03.374+08 | 23:17:18.925+08 |
| App 构造耗时 | 14.641s | 14.234s |
| 初始化 / 额外保持 | 2 / 0 physics steps | 2 / 0 physics steps |
| 图片 | 0 | 4，均完整保存 |
| 停止点 | physics_initialize：pause 后状态尚未提交 | 完成四图后，入口 :254 native 参数读回 |
| 主失败 | `render_pause: Timeline did not pause` | Windows access violation，`get_masses` |
| 监督收尾 | `completion(entry,result)` 少 attempt 参数而 TypeError，原 final 未生成 | supervisor_result 正常保存，明确 FAIL |
| 目标/Conda 退出码 | **UNKNOWN / UNKNOWN**，不能由外层 exit1 补齐 | 3221225477（0xC0000005） / 4294967295（0xFFFFFFFF） |
| 外层命令退出码 | 1 | 1 |
| 整个所属树 | 已退出；最终精确耗时/termination flag 未留存 | 38.391s；无 timeout、无 supervisor terminate，remaining=[] |
| 完整验收 | FAIL | **VISUAL_GEOMETRY_RENDER_FAIL** |

第一轮日志有 App shutdown，后续只读进程检查确认所属进程已退出，没有 console/Kit native fault 命中。23:02:03 启动至 23:02:29 已复制收尾日志，未达监督时限，但不能将缺失的监督终态补成“自然 exit0”。新增单独 `attempt_01/supervisor_recovery.json`，保留原六份产物 hash、TypeError、23:08:02 的进程/source 再核对；退出码/termination 仍 UNKNOWN，PASS 字段仍 false。原 console/result/配置记录未修改。第二轮只对这一精确、零受控步的 API 失败允许预算内重试，不把 UNKNOWN 当成功。

两次之间的局部修正：pause 后采用主线程 commit、不增加物理 update；修正监督 `completion(entry,result,attempt)` 实参；解析允许同源多 Mesh 聚合与非物理 GeomSubset；先完成相关 CPU 检查，新冻结保存在 `preflight_repair_01.json`，不覆盖第一版 `preflight.json`。没有修改物理控制、资产或 Windows 启动实现。

第二轮真实 D3D12 见 `kit_20261004_231722.log:2682,3513`；native 窗口 1440×900 见 `console.log:3382`。日志文件头为 UTC 时间，例如 15:17:23 对应本地 23:17:23。`console.log:7239,7240,7244,7245` 依次记录四次 capture；随后 `:7246` 报 Windows fatal exception；栈 `:7285` 指向：

```text
isaacsim/extsPhysics/omni.physics.tensors/omni/physics/tensors/impl/api.py:2092 get_masses
scripts/environments/_cr12_runtime_support.py:184 _read_physics
scripts/environments/inspect_cr12_visual_geometry.py:254 _run_check
```

这次故障在 App/GUI/场景/截图之后，**不是历史 120×0 swapchain 构造失败**。当前实际是 D3D12，不回到 Vulkan、驱动、DPI 或 solver 排错。可能涉及 native view 与运行中 layer composition 的生命周期，但**根因未证实**；仅有堆栈不能断言是哪次层操作使句柄失效。

最终 `result.json` 保留最后 checkpoint：`status=RUNNING, work_completed=false, diagnostics_complete=false, app_close_requested=false`，`failures=[]` 只是 native 异常未走 Python 捕获写回，绝非成功。最终 `physical_invariance/render_comparison/visual_check/asset_protection` 均未生成；正常 close 完成也没有证据。监督器的 GUI 层 false 含正常退出门槛，不意味着没有出现窗口；四图/1440×900/D3D12 是独立阳性证据。

日志还含启动前 omni.kit_app 导入提示、扩展/OmniHub/Intel adapter 跳过与 TLAS 提示；不隐去，也无证据把它们归为这次 native 异常根因。只保留既有日志，没有新建大规模诊断包。

实际预算：App **2/2**，总截图 **4/6**，受控保持 **0/120 每 App**，无 motion target、无 IK/2520 步旧 demo；各 App 构造低于 180s。第二轮所属树 38.391s 低于 360s，第一轮未触发等待时限但终态字段部分丢失。原生故障后**没有第三次 App、没有继续修实现、没有 headless 替代**。

## 7. 新增代码、针对性 CPU 检查与文件清单

| 新增位置 | 用途 / 关键符号 | 最终检查 |
|---|---|---|
| scripts/environments/_cr12_visual_source.py | read_obj:71、load_visual_sources:102、compare_mesh:197；米制源几何核对 | 配套 8/8 CPU 测试 |
| scripts/environments/_cr12_visual_geometry.py | inspect_visual_mapping、physical_snapshot、CollisionVisualOverride | 配套 20/20 CPU 测试 |
| scripts/environments/inspect_cr12_visual_geometry.py | parse_args:24、png_complete:53、commit_pause:82、_run_check:94、main:288；独立有界入口 | 配套 9/9 CPU 测试；runtime 总体 FAIL |
| source/isaaclab_tasks/test/test_cr12_visual_source.py | 点/面重排、源单位/变换、拓扑差异 | 8/8 |
| source/isaaclab_tasks/test/test_cr12_visual_geometry.py | 身份/叶节点/继承/白名单/撤销/非物理 subset | 20/20 |
| source/isaaclab_tasks/test/test_cr12_visual_entry.py | PNG完整性、参数/预算、pause commit 等 | 9/9 |
| L/repro/check_visual_source_mapping.py | 原 URDF 与派生源映射；不加载 Isaac | 20 项、最大变换差 0 |
| L/repro/prepare_private_user_config.py | 既有已接受 helper 的任务本地副本 | 真实 source 只读，每次新 private |
| L/repro/supervise_cr12_visual_geometry.py | 沿用 owned-process/private 支持，换成本轮完成判定和精确失败恢复 | 本轮初次 42 项、可选 debug 图片 4 项、局部恢复/调用点 25 项 CPU 断言通过；首轮收尾遗漏仍作为真实失败保留 |

最终针对性测试 **37/37**，仅本轮新增测试；未重跑完整 OBB/sweep、六轴、Phase B 或全仓库测试。新增/局部修正文件 `py_compile` 通过。CPU 原几何检查和实际 App 源→USD 检查分开，不以 CPU 假对象测试替代真实 USD/runtime。

实际使用的主要 CPU 命令（cwd 为仓库根）：

```powershell
& 'D:\miniconda3\Scripts\conda.exe' run -p 'C:\isaacenvs\isaac45_harl' python source/isaaclab_tasks/test/test_cr12_visual_source.py
& 'D:\miniconda3\Scripts\conda.exe' run -p 'C:\isaacenvs\isaac45_harl' python source/isaaclab_tasks/test/test_cr12_visual_geometry.py
& 'D:\miniconda3\Scripts\conda.exe' run -p 'C:\isaacenvs\isaac45_harl' python source/isaaclab_tasks/test/test_cr12_visual_entry.py
```

补充源映射输出为 `L/repro/source_geometry_check.json`，任务局部 preflight 记录冻结输入与 CPU 修正检查；一次性监督断言不另建大型测试框架。新增 Python 都在 scripts/test/repro 各自位置，**AgentRead 本轮只新增本 Markdown，另小范围更新 TASK_PROGRESS/REPORT_INDEX**。

既有 dirty worktree 保留，包括既有 view/train/play 与 AgentRead 修改、未跟踪历史 CR12 文件/资产，以及 index 中原有 Phase B ZIP 删除；本轮没有 Git add/commit/push/reset/restore/checkout/clean/stash 或删除历史产物。没有改原正式入口、runtime support、Windows helper、guard/pair 或模型文件。

## 8. 后续如何显式使用，以及当前缺口

**预期 visual 来源**：继续直接使用现有 v1 的原 visual 表示，它们已经保留源 OBJ 的几何和安装关系；不需恢复/重导入整机、修改惯性或要求用户重导出 CAD。显示修复仅排除独立 collision 的 render visibility。

将来的扫描场景可以显式调用 `load_visual_sources → inspect_visual_mapping → CollisionVisualOverride.apply`，记录应用对象并在合适生命周期撤销；旧入口默认仍不变。但本次**没有证明当前“native views 已建立后反复插拔匿名层”的完整运行安全性**，不能直接照搬本检查入口到扫描主线。

建议后续单独审阅一个小范围候选：在 stage/机器人 reference 已存在、首次 reset/native physics views 建立之前一次性应用 render 意见，运行期间不重组该层；撤销安排在未初始化的 stage 或受控销毁阶段。需同时证明原物理配置未变、native 参数读回/退出正常。此为针对堆栈的实施方向，尚未实施或验证，也不代表已证实 layer 重组是唯一根因。不能仅删除失败的 native getter 或放松通过条件来获得 PASS。

当前未发现源 visual 丢失或必须改资产物理结构的证据；**阻断相机接入的是显示修复的完整运行集成验证尚未完成**，以及用户对两处外观（含完整 scanner 取景）的确认。无需扩大动作、换轴、改 marker 或重新开始动力学验证。

本轮不满足“修复与 GUI 路径已经实际通过”的前提，因此不交付新的可直接人工运行命令；保留失败入口和记录供审阅，等待下一轮明确范围。后续关闭这一局部缺口后，研究主线下一步仍是**单视点到位后按需开启相机→实际取得本次新数据→关闭相机**，随后才是双视点和 MRTA。本轮未接 sensor、未采扫描数据、未加构件。viewport 图片、几何到位和延时均不能代替采集；不增加质量门槛。采集成功与随后关闭失败分开记，未确认关闭不能开始下一段运动。

撤销本轮显示功能不需要还原 v1：保持旧入口或不调用 helper 即不应用 render 意见；匿名层不持久存在。源码保留/删除应只针对本轮新增文件、另行按需要处理，**不能用仓库 reset/clean 撤销用户既有工作**。本轮没有执行清理。

## 9. 辅助证据对应表与归档

| 结论/检查项 | 文件位置 | 关键字段或定位 | 用途与限制 |
|---|---|---|---|
| 原源→派生 | [source_geometry_check.json](../../../../../../../../logs/scan_assignment/20261004_cr12_visual_geometry/repro/source_geometry_check.json) | source_derived_mappings、visual_collision_pairs | CPU 来源/坐标证据，不是 runtime PASS |
| 真实 USD 映射、初态、四图元数据 | [attempt_02/result.json](../../../../../../../../logs/scan_assignment/20261004_cr12_visual_geometry/attempt_02/result.json) | visual_mapping、render_override、display_corrected、screenshots、paused_state | 最后 checkpoint，RUNNING/未完成；最终验收字段缺失 |
| 第一轮失败 | [attempt_01/console.log](../../../../../../../../logs/scan_assignment/20261004_cr12_visual_geometry/attempt_01/console.log)、[result.json](../../../../../../../../logs/scan_assignment/20261004_cr12_visual_geometry/attempt_01/result.json) | render_pause / physics_initialize | 保留真实 API 失败 |
| 第一轮监督缺失恢复 | [supervisor_recovery.json](../../../../../../../../logs/scan_assignment/20261004_cr12_visual_geometry/attempt_01/supervisor_recovery.json) | 原六产物保护、UNKNOWN exits、process/source 检查 | 独立补充，不冒充原 final，不改旧证据 |
| 第二轮原生命令与监督结果 | [command.json](../../../../../../../../logs/scan_assignment/20261004_cr12_visual_geometry/attempt_02/command.json)、[supervisor_result.json](../../../../../../../../logs/scan_assignment/20261004_cr12_visual_geometry/attempt_02/supervisor_result.json) | child argv、38.391s、exit、FAIL、budget_after | 主失败与预算依据 |
| 第二轮 native 异常 | [console.log](../../../../../../../../logs/scan_assignment/20261004_cr12_visual_geometry/attempt_02/console.log) | 7246、7285及其后调用栈 | get_masses 访问异常，不能证明唯一底层根因 |
| 实际 D3D12 | [kit_20261004_231722.log](../../../../../../../../logs/scan_assignment/20261004_cr12_visual_geometry/attempt_02/kit_20261004_231722.log) | 2682、3513；UTC时间 | 原 Kit 路径来自 app_ready；仅保留本轮副本 |
| private/source 保护 | [source_private_config_summary.json](../../../../../../../../logs/scan_assignment/20261004_cr12_visual_geometry/attempt_02/source_private_config_summary.json)、[config_runtime_summary.json](../../../../../../../../logs/scan_assignment/20261004_cr12_visual_geometry/attempt_02/config_runtime_summary.json) | hash/mtime/三项语义差异与实际加载 | source 不变，不能代替正常退出 |
| 最终只读保护复核 | [post_run_static_checks.json](../../../../../../../../logs/scan_assignment/20261004_cr12_visual_geometry/post_run_static_checks.json) | 53项未变、28资产、4PNG、remaining_apps=0 | 崩溃后文件证据，不是 native 补验 |
| 初始/局部修正输入冻结 | [preflight.json](../../../../../../../../logs/scan_assignment/20261004_cr12_visual_geometry/repro/preflight.json)、[preflight_repair_01.json](../../../../../../../../logs/scan_assignment/20261004_cr12_visual_geometry/repro/preflight_repair_01.json) | 本轮窄范围输入与修正检查 | 保留两版，不构成历史库存审计 |
| 先前接受范围 | [OBB与往返报告](CR12_OBB_REFINEMENT_AND_LARGE_JOINT_SWEEP_REPORT.md)、[formal pose报告](../../202609/20260930/CR12_SINGLE_TARGET_POSE_EXECUTION_IMPLEMENTATION_REPORT.md) | 当前资产/支持与 frame 结构 | 原报告保持历史口径；最新人工反馈见本报告第1节 |

日志与 PNG 位于本机 `logs/`，受现有忽略规则影响，未 Git 提交；新的 checkout 不自动包含这些证据。未生成 ZIP、全场景 dump、视频或重复日志包。

文档变更仅为本主报告、小范围 [TASK_PROGRESS.md](../../TASK_PROGRESS.md) 与 [REPORT_INDEX.md](../../REPORT_INDEX.md)。本报告 26 个本地链接及交接/索引中本轮 6 处导航目标均存在；PowerShell 命令块只做语法解析，未重执行；交接修改与本轮开始时文本对照，仅涉及最新状态/资产边界/对应导航，未重写历史。只读 index 核对仍只有本轮之前的 Phase B ZIP 删除，未新增暂存。旧报告和既有清理边界不变。**本轮停止，等待 GPT/用户审阅；没有自动接相机、追加 runtime、实施双视点/MRTA、提交或清理。**

