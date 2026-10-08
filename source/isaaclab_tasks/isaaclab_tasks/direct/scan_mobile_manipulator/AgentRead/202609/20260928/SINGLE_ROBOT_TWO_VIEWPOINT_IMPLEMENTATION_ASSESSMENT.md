# 单机器人双视点扫描执行环境：静态实施评估

日期：2026-09-28，Asia/Shanghai。状态：**静态实施评估完成；等待GPT/用户审阅；尚未实施、尚未进行仿真验证。**

实际仓库为 `E:\Project\IsaacLab_HARL`。下文 `T/`＝`source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/`；`L/`＝`source/isaaclab/isaaclab/`；`I/`＝`C:/isaacenvs/isaac45_harl/Lib/site-packages/isaacsim/`。带行号的源码索引是本次文本读取位置；未解析的USD不虚构prim或行号。

## 1. 执行摘要与推荐最小方案

**推荐：以当前能定位并解析的CR12 URDF为结构基线，准备固定AGV、保持升降高度、六轴机械臂关节驱动的独立场景；运动模块采用完整pose的DLS差分IK与受限关节目标，并补充有限场景的路径/碰撞检查；相机采用独占render product的真实渲染开关。上层顺序提交两个视点，单视点模块逐tick推进。** 不接HAPPO、奖励、mask、checkpoint或MRTA authority。

现在不能直接认定“已有USD可以直接加载”：在用户新目录中实际找到的是 `T/assets/rokeaCR12/rokea_cr12_7DOF.urdf` 和21个OBJ；在本次限定范围内**未定位到新机器人USD**，已询问准确路径。旧 `ScanRobot.usd.back` 不能代替这次新资产。若补充USD并能核对结构/依赖，可改用已准备的USD直接加载，避免重复转换；本次不要求两条加载路线都实现，也未执行转换。

主要实施前提是：确认资产入口与惯性处理、明确scanner到camera的固定安装变换、选定同一固定基座下可达且有安全转移路径的两个完整pose。URDF已具备关节树和collision引用，超出了旧代理外观资产；但八个link的惯性参数违反物理惯量必要约束，且没有可确认的相机或PD drive配置。这些属于新执行环境的准备问题，不是Phase B缺陷。

最小目标严格保持用户流程：相机OFF → 运动至视点1 → 实测到位并保持 → 开启本次采集 → 等待本次实际数据 → 关闭采集并确认OFF → 从实际结束状态运动至视点2 → 同样采集与关闭 → 结束。正常等待不报失败；几何到位、驻留、缓存或虚构回执都不能代替采集成功。

**本轮已确定且不再询问的要求**：全部决策智能体都可独立扫描；不设置辅助定位角色；独立入口/验证场景、可复用运动与相机模块；取得本次实际数据即采集成功，无深度比例、分割、点云、重建或精度门槛；采集按任务启停；Phase B保持 **COMPLETE / GPT REVIEW PASS / CLOSED**；不开展视点生成、Transformer/可变规模实现或大规模论文实验。

证据标记：**U**＝用户本轮已确认；**S**＝当前文件/源码直接确认；**P**＝实施建议/静态推断；**V**＝需要后续运行验证；**Q**＝需要用户补充且影响具体路线。U“用户提供了可驱动模型”与S“本次读到了关节树、限位、collision引用”分别成立，不能据此把V“运行可用”标为通过。

## 2. 当前资产和本地源码事实

### 2.1 资产入口、依赖和USD限制

| 对象 | 实际位置/检查结果 | 证据等级与含义 |
|---|---|---|
| 推荐机器人 | [rokea_cr12_7DOF.urdf](../../../assets/rokeaCR12/rokea_cr12_7DOF.urdf)，XML robot名`rokea_cr12`，注释xMateCR12 | S：当前新目录唯一可解析完整关节树候选；推荐依据结构，不根据actor槽位或文件时间推断 |
| 机器人mesh | `T/assets/rokeaCR12/model/`：AGV、elevate、cr12_base/link1..6、scanner各visual/collision，加`object_convex_collision.obj` | S：21个OBJ；URDF的20条mesh引用全部在当前机器存在 |
| 路径与材质 | 20条mesh引用均为本机绝对`E:\Project\IsaacLab_HARL\...`路径；scale均`0.001 0.001 0.001` | S：当前可解析依赖，可移植性不足；21个OBJ未发现`mtllib`行，未见其声明的外部MTL/贴图依赖；不等于验证了最终材质 |
| 额外collision文件 | `model/object_convex_collision.obj` | S：不被此URDF引用；不能凭名称认定已经作为构件碰撞体使用，其坐标/用途待核对 |
| 用户新USD | 在新目录、任务assets/Model、`source/isaaclab_assets`及根assets的有限检查中未定位 | Q：准确路径待补充；root/articulation prim、关节drive、units、up-axis、引用依赖与URDF版本差异全部UNKNOWN |
| 旧USD备份 | `T/assets/scene/robots/robot_visual/ScanRobot.usd.back` | S：历史文件存在；不拿它证明本次CR12的身份、结构或可用性，本次未解析其内容 |
| 现有构件 | `T/Model/aircraft_skin_with_frame.obj`；`component_mesh.py`可读取OBJ及变换后bounds | S：原任务按mm→m可视化；旧bbox/footprint逻辑没有给新物理场景建立碰撞体 |

搜索包含ignored/untracked文件，采用资产范围内的`rg --files -uuu`及定向目录读取。有限扩大搜索只发现无关钢琴/球体USD，不据此无限扩大到日志、历史产物或整台电脑。

已核对离线解释器为 `C:\isaacenvs\isaac45_harl\python.exe`；同解释器 `importlib.util.find_spec('pxr')` 返回None。没有通过Kit启动、添加sys.path/PYTHONPATH或安装包绕过。即使随后提供二进制USD，本次环境也未确认现成独立pxr解析能力；文本USDA可按文本检查，二进制属性应继续标UNKNOWN，不能靠字符串片段或文件名补全。

**加载路线建议（P）**：当前以URDF为可审查输入，在惯性处理和配置审阅后，未来经授权一次性生成独立派生USD，再通过`ArticulationCfg + UsdFileCfg`加载；保留原始文件。`UrdfFileCfg`本身会调用Kit/URDF converter并生成USD，不是本轮可运行的离线解析器。若用户补充了结构/依赖可核对的现成驱动USD，则优先直接加载该资产，此分支会替代转换步骤。两者不是并行开发任务。

### 2.2 URDF关节树、坐标、驱动与惯性

```text
world --joint_agv(fixed)--> agv
      --joint_0(prismatic Z)--> elevate
      --joint_base(fixed)--> base_link
      --joint_1..6(revolute)--> link_1..6
      --joint_tool(fixed identity)--> tool
      --joint_scanner(fixed yaw 135 deg)--> scanner
```

S：12 links、11 joints，七个活动关节是“一轴升降+六轴机械臂”，不是七轴机械臂加移动底盘。没有轮子/底盘平面运动自由度，也没有camera/sensor/optical-frame元素。

| 项目 | URDF来源 | 读到的值 |
|---|---|---|
| world→agv | 184–188行 | fixed，xyz=(0,0,0.053)，rpy=0 |
| joint_0 | 189–195行 | prismatic，+Z，origin z=0.314；位置[0,0.5]、速度0.05、effort300 |
| elevate→base_link | 196–200行 | fixed，xyz=(0.105,0,0.748)，rpy=0 |
| joint_1 | 202–208行 | Z；位置±3.0543、速度2.094395、effort300、damping0.7 |
| joint_2 | 210–216行 | Y；位置±2.9671、速度2.094395、effort300、damping0.7 |
| joint_3 | 218–224行 | Y；位置±3.0543、速度3.1415926、effort300、damping0.7 |
| joint_4 | 226–232行 | Z；位置±3.0543、速度4.084070、effort300、damping0.7 |
| joint_5 | 234–240行 | Y；位置±3.0543、速度4.1887901、effort300、damping0.7 |
| joint_6 | 242–248行 | Z；位置±3.0543、速度4.1887901、effort300、damping0.7 |
| link_6→tool | 251–257行 | fixed identity；tool无geometry/inertial |
| tool→scanner | 259–283行 | scanner有visual/collision/inertial；固定零平移、rpy=(0,0,2.356194490192345) |

数值按URDF/SI解释为米、弧度及对应速度/力或力矩；OBJ缩放支持mm→m解释，但尚未与设备尺寸资料核对。URDF没有USD stage的`metersPerUnit/upAxis`字段，Z方向的建模意图可由升降轴和安装位移看到，未来生成/加载stage时仍须明确米制/Z-up。scanner的135°只是模型安装角，不是光学轴校准。

**驱动层次（S/V）**：存在关节类型、轴、限位、effort上限、六轴damping；未发现transmission、actuator或PD stiffness/gain定义。标准URDF结构可用于建立articulation，但不等于已具备Isaac驱动配置。需后续明确每组关节的position drive、stiffness/damping、effort/velocity限制并做短运行确认；不照搬UR10的数值。

**惯性问题（S）**：10个惯性矩阵的基础对称正定检查通过；其中`base_link、link_1..6、scanner`共八个违反物理惯量必要三角约束。例如base/link1：`Izz=1.120163944 > Ixx+Iyy=0.034265761`；link2：`Iyy=1.747453457 > Ixx+Izz=0.149295248`。来源分别在58/78/98/118/138/158/178/275行附近。正定不能代替物理有效性。AGV/elevate对角均为1，其真实性也未经设备资料确认。

后续物理驱动前应选择可靠质量/惯量来源：提供修正参数，或明确接受由可信几何/质量产生的仿真近似并在派生资产中记录。不能靠调大PD掩盖，也不能假定importer必然忽略或正确修复原值。本地`UrdfConverter._get_urdf_import_config`未显式选择`import_inertia_tensor`；具体导入结果需要明确配置和检查。本次未修改原URDF、质量、惯性、mesh或USD。

**碰撞资产（S）**：`cr12_base`和`cr12_link1..6`七组collision/visual文件逐对SHA256相同，不能认为collision命名表示已经简化或凸分解。collision几何引用存在与PhysX cooking、collider启用、自碰撞过滤、稳定接触均是不同层次。实际运行可用性仍V。

### 2.3 本地版本与可复用入口

仓库`VERSION`为2.1.0；`source/isaaclab/config/extension.toml:4`和安装metadata为isaaclab扩展0.36.23，editable安装指向本仓库`source/isaaclab`；Isaac Sim及sensor/robot_motion安装metadata为4.5.0.0。相机扩展配置版本0.2.9。`_isaac_sim`目录未发现，实际安装源码位于上述I/，没有将此当作runtime缺陷。

| 能力 | 本地源码/符号 | 已确认与边界 |
|---|---|---|
| 独立场景范式 | `scripts/tutorials/01_assets/run_articulation.py`、`add_new_robot.py` | Articulation/SimulationContext循环，无需RL环境；本次只阅读，不执行其AppLauncher |
| 资产与执行器配置 | `L/sim/spawners/from_files/from_files_cfg.py:71/111`；`L/assets/articulation/articulation_cfg.py:54`；`L/actuators/actuator_pd.py:34` | UsdFileCfg/UrdfFileCfg、ArticulationCfg.actuators、ImplicitActuatorCfg；URDF导入是未来有副作用的步骤 |
| 完整pose DiffIK | `scripts/tutorials/05_controllers/run_diff_ik.py:99/162`；`L/controllers/differential_ik.py:98/148/227` | absolute pose + DLS输出q+Δq；不自动处理轨迹、限位、碰撞或完成 |
| 实测与驱动 | `L/assets/articulation/articulation.py:173/882` | set_joint_position_target写命令缓存，write_data_to_sim交给PhysX，后续physics step才产生运动 |
| 帧变换 | `L/utils/math.py:750/785/820/1429` | combine/subtract_frame_transforms、compute_pose_error、camera frame convention转换 |
| Jacobian坐标 | `L/envs/mdp/actions/task_space_actions.py:69/143`；`scripts/tutorials/05_controllers/run_osc.py:319` | body/joint索引规则和world→root Jacobian旋转；不能默认base_link=root |
| 接触与场景查询 | `L/sensors/contact_sensor/contact_sensor.py:49/251/320`；`L/sim/schemas/schemas.py:464`；`I/extsPhysics/omni.physx/omni/physx/bindings/_physx.pyi:2067/2218` | contact报告激活、单body对多object过滤；overlap_box/sweep_box接口；不是已完成CR12碰撞后端 |
| 本地高级运动模块 | `I/exts/isaacsim.robot_motion.motion_generation/isaacsim/robot_motion/motion_generation/lula/` | kinematics.py:202/221有FK/IK；trajectory_generator.py:53/73有轨迹；path_planners.py:33/55有RRT。三者职责不同，当前未发现CR12 descriptor/规划配置 |

OSC需要质量矩阵/力矩控制，RMPFlow/Lula需要目标模型descriptor及映射；当前首先解决位置执行小场景，故不将它们作为默认新增复杂度。本地Lula IK明确不提供USD障碍避碰（kinematics.py:292附近）；RRT才是另一个规划层，预配示例主要为Franka。示例存在不等于CR12运行可用。

## 3. 视点、运动控制与碰撞方案

### 3.1 完整pose与坐标关系

S：当前[viewpoint_csv.py](../../../viewpoint_csv.py):15/35–43定义`scanner_pose_world_quat_wxyz_v1`：米制world中的scanner完整pose，WXYZ、+X前/+Z上。它不是法兰目标，也不能未经安装变换直接当相机光学pose。原任务对克隆env做origin平移；独立单场景需要显式声明同一个场景world和构件放置变换。

P：输入使用`goal_id + target_pose + target_frame/convention`。兼容已有CSV时，保留scanner语义并显式变换；人工给两个camera目标时也显式标camera的轴约定，不让控制器猜测。只选现有集合子集或后续人工指定，不生成视点，不给出“已验证可达”的数值目标。

令`T_AB`表示B在A中的位姿，W为场景world、R为实际articulation root、E为有可靠Jacobian的末端刚体、S为CSV语义scanner frame、C为camera frame：

```text
scanner目标：T_WE* = T_WS* · inverse(T_ES)
camera目标： T_WE* = T_WC* · inverse(T_EC)
IK输入：    T_RE* = inverse(T_WR) · T_WE*
实测scanner：T_WS = T_WE_measured · T_ES
实测camera： T_WC = T_WE_measured · T_EC
```

URDF提供world/agv/elevate/base_link和link_6/tool/scanner固定关系；**没有提供scanner模型原点到实际/拟建相机光心的外参或光学参数**。需明确`T_ES/T_EC`，不能自动以零偏移替代。仿真第一版可以使用明确配置、经审阅的固定相机安装约定，不宣称真实标定。相机prim作为末端子节点随机器人运动，禁止每tick独立set相机world pose追赶目标。

导入的`merge_fixed_joints`默认True，tool/scanner可能并非独立rigid body；应基于实际导入层级选择E（如link_6）并保留固定工具变换。只控制E的Jacobian时先将目标换成E，可避免遗漏TCP平移导致的Jacobian偏置。目标、实测pose、Jacobian必须统一到R；根可能是world/agv对应body而不是机械臂base_link。

相机轴约定也必须显式转换：IsaacLab CameraCfg支持world（+X前/+Z上）、ROS（+Z前/−Y上）、OpenGL（−Z前/+Y上）；IsaacSim Camera使用`camera_axes="world"/"ros"/"usd"`。建议适配器统一对外用world-style camera pose，通过本地转换函数到USD光学约定。相同WXYZ顺序不代表光轴相同，URDF scanner yaw135°也不消除这一差异。

### 3.2 固定底盘、六轴控制及到位

P：第一版保持URDF的固定AGV；在选定升降高度下hold/lock `joint_0`，只对`joint_1..6`做IK与执行。`fix_base=True`只固定根，**不锁内部升降轴**；需给升降明确保持策略并读取实际漂移。两个pose必须在同一安装位置和升降高度下均可达，且两点间能形成受限安全路径。当前没有证据说明必须移动底盘。

若六轴方案不足，先排查目标frame/安装偏置、局部IK初值/奇异性、joint限位及碰撞；DLS不收敛不能直接等于全局不可达。若是高度范围不足，最小扩大是纳入已有prismatic升降轴及对应单位/速度限制；若确实需要AGV平面移动，现有URDF缺少该自由度和控制模型，会增加底盘模型、控制、定位、路径/碰撞工作，不属于本次最小默认路线。固定底盘完成不代表移动操作已完成。

控制流程建议：实测q/末端pose/Jacobian → absolute pose DLS → 受限q目标/渐进参考 → `set_joint_position_target` → `write_data_to_sim` → 主循环physics step → 更新真实状态。外层必须限制joint position、每步速度/加速度及命令跃变；`soft_joint_pos_limit_factor`只是软范围数据，不会自动替controller限幅。升降与旋转关节应分别使用m/rad单位。

本地教程每150步重置joint state再切换目标（run_diff_ik.py:144–159）；**双点执行不能照搬此部分**。`write_joint_state_to_sim/write_root_pose_to_sim`只允许初始化/明确reset。视点2从视点1采集关闭后的实测q、速度和姿态开始，不把起点改写成理想目标q。

到位由实测E/相机pose相对目标的位置误差、旋转角误差，以及小速度/短稳定窗口判断；阈值作为显式配置在后续有限运行中选定。到位仅开启采集的前提，稳定驻留不是扫描成功。采集期间保持关节目标并持续核对实测pose；越界进入本次尝试失败/中止分支，不能拿早前到位时刻解释晚到数据。

### 3.3 最小场景的碰撞处理

P：单机、固定构件、地面，优先选择构件同一开放侧的两个近邻完整pose，避免第一版绕背面/穿孔。构件可用现有OBJ显示，**另建立同变换下覆盖实际几何的保守静态box/少量简单collider**；包络应由该mesh变换后的bounds得到，不能沿用与模型无关的旧hard-coded bbox。保守体可能误拒绝狭窄空间，第一版接受范围收窄，不以此声称真实表面规划能力。现有`component_mesh.py:124/219`可复用读取/计算bounds的逻辑，旧visual创建函数本身不产生碰撞。

机器人使用经核对的collision mesh及明确PhysX近似设置；碰撞名称相同不证明其凸性。首次派生/加载时检查cooking、scale、world固定、非相邻link自碰撞和过滤；不能默认URDF importer `self_collision=False` 就满足需求，也不能一律打开相邻link接触导致安装处假报警。

| 阶段 | 最小检查与行为 | 限制 |
|---|---|---|
| 起始状态 | 先静态/几何检查root、升降、各joint范围；未来初始化后检查实际姿态和禁止pair重叠/接触；相机保持OFF | 初始非法则不提交视点；不能靠步进把深度穿透“弹出来”作为正常初始化 |
| 目标状态 | 得到候选末端和joint解后检查全部robot link/scanner与构件、非允许self pair、地面的关系 | 只检查TCP终点不够；local IK解还不是轨迹 |
| 转移全过程 | 检查实际起点到目标及必要via waypoint的完整候选路径；控制每个next target前检查短段保守扫掠包络，并计入跟踪误差/制动余量；执行时检查实际几何和接触 | 单一固定姿态的box sweep不覆盖旋转关节完整扫掠；稀疏采样不能包装成连续无碰撞保证 |
| 碰撞/无路/无进展 | 停止推进新目标，相机OFF，按有界减速/保持策略结束当前尝试，记录collision/path_blocked/motion_timeout/no_progress等原因 | 报失败不代表设备已经瞬时静止；未确认安全停止时禁止第二目标 |
| 允许接触 | 明确只允许底座正常支撑/安装接触及经核对的相邻固定结构pair；扫描头/机械臂碰构件、非相邻自碰撞、臂碰地面为禁止 | 应按body-pair过滤，不能用机器人总接触力阈值把所有地面接触都判失败 |

**局部IK不足的最小补充**：第一版也需要一个有界的候选路径/碰撞检查层，不只是DLS+collider。建议限制在已选开放侧走廊，采用少量经检查的via姿态/关节waypoint；在独立运动学表示中取得候选joint序列并检查整段，运行中再检查实际状态和下一小段。不能把活动机器人teleport到候选q做检查。所需FK/几何变换及关节映射属于后续执行支撑实现，目前CR12检查后端尚不存在。

若有限waypoint走廊无法建立、保守包络无法接受或缺少可信候选路径检查，就返回`path_unavailable`，不能仅启用collider后强行推进。需要自动寻找路径时，最小升级是为本地Lula补CR12 descriptor/collision模型后复用其RRT和轨迹模块，而非研发新规划算法；这会增加明确的准备步骤，需要审阅后选择，不预设本轮必须覆盖任意障碍场景。

本地支撑来源：`ContactSensorCfg`、`activate_contact_sensors`及`force_matrix_w`可以实现接触监控，但filtered contacts仅支持单sensor body对多个对象，需要按body配置；阈值不能证明“无穿透”，净力还可能相互抵消。`PhysxSceneQuery.overlap_box`/`sweep_box_all`可做候选保守形状查询，命中需按允许pair分类；它们是原语，不是完整关节路径检查器。`overlap_box`四元数为XYZW（_physx.pyi:2074），须与应用WXYZ显式转换。scene query默认未开启；CCD也有独立配置（`L/sim/simulation_cfg.py:86/284`），必须检查其对选定articulation/collider的实际效果，不能把CCD设为True当作防穿模证明。

未来只验收所选双点和所选场景的有限路径：记录禁止pair接触/几何穿透检查及状态，不能从一次执行推广为任意目标安全。未完成上述路径检查时，允许验证静止相机/单关节调试，但不应宣称双点无穿模闭环已通过。

## 4. 相机按任务采集方案

### 4.1 采用的本地API与真正开关

P：使用IsaacSim 4.5 `isaacsim.sensors.camera.Camera`连接**专属**render product，作为独立场景的采集后端；相机可一直存在，按任务关闭/开启该product的Hydra渲染。简单数据通道建议先用RGB/RGBA一帧，不建立深度/点云质量门槛。该选择只降低接口复杂度，不改变“取得本次实际数据即成功”。

相机源码根 `C/ = I/exts/isaacsim.sensors.camera/isaacsim/sensors/camera/`；Replicator源码根 `R/ = I/extscache/omni.replicator.core-1.11.35+106.5.0.wx64.r.cp310/omni/replicator/core/scripts/`；Hydra声明根 `H/ = I/extscache/omni.kit.hydra_texture-1.4.0+d02c707b.wx64.r.cp310/omni/hydratexture/`。

| API | 本地证据 | 能证明什么/不能证明什么 |
|---|---|---|
| `rep.create.render_product(..., force_new=True)` | `R/create.py:1526` | 可取得独占product handle与hydra_texture；不能共享GUI viewport或别的sensor product |
| `rp.hydra_texture.updates_enabled=False/True` | `H/_hydra_texture.pyi:229/293` | 声明明确禁用时不调用相关HydraEngine渲染；是实际采集渲染开关。旧set_updates_enabled已deprecated，优先property |
| `Camera(render_product_path=...)` / initialize | `C/camera.py:176/372` | 绑定已有product，attach RGB/ReferenceTime、注册事件、创建初始零buffer；initialize不等于获得数据 |
| pause/resume | `C/camera.py:436/450` | 仅移除/注册NEW_FRAME回调；单独pause不足以满足停采集 |
| NEW_FRAME回调 | `C/camera.py:462` | 先匹配product，再同步graph求值，读取ReferenceTime、RGBA及rendering_time到同一current_frame |
| `get_current_frame(clone=True)` | `C/camera.py:360` | 复制同份frame字典；独立get_rgba与另一次frame读取不能擅自拼成同帧证据 |
| Camera.frame / update_period | `L/sensors/camera/camera.py:509–527`；`L/sensors/sensor_base.py:197–204` | IsaacLab frame在buffer读取时自增；update_period控制缓存更新。它们不能证明fresh，也不能代替渲染开关 |
| 主循环render | `L/sim/simulation_context.py:530/561` step/render | 主循环统一推进physics和必要render；不在每个执行器中运行长阻塞采集循环 |

本地Replicator示例`I/exts/isaacsim.replicator.examples/isaacsim/replicator/examples/tests/test_sdg_useful_snippets_timeline_based.py:80–127`展示product OFF→需要时ON→step_async→读取→OFF的范式，本次未执行。`rep.orchestrator.step/step_async`会涉及timeline暂停，不能未经协调嵌入运动loop；默认建议由独立场景的统一step/render调度产生事件，保持hold控制及deadline推进。

### 4.2 初始化、开启、fresh确认和关闭

1. **初始化OFF**：在实际末端挂载frame下建立camera prim，设置一次固定外参/光学参数。创建独占product后，在任何显式render、sim.step或app.update之前立即置`updates_enabled=False`；Camera绑定它，initialize后pause，并再次重申/读取OFF。该initialize函数体没有显式render，但底层create/attach是否会产生首帧仍V，不能仅据Python函数体宣称初始绝无采集。
2. **预热与运动**：GPU/场景预热保持扫描product OFF，初始化零数组不进入结果。若相机graph本身需要首次出帧，留在首次到位后的ON窗口等待。运动时维持OFF；GUI可继续显示，不通过关闭整个GUI冒充关闭该相机。
3. **开启本次任务**：实测到位、驱动保持后，为当前goal建立独立`capture_id`，记录开窗之前的product/frame/reference基线，清空本次结果。先建立本次接收状态/resume，再将独占product设ON。不能在机器人途中连续采集后只选择到位帧。
4. **等待本次实际数据**：保持机器人、继续主循环步进/渲染。只接受本次ON之后**匹配本product的真实完成事件**，在Camera对该帧完成更新的同一接收边界复制整份current_frame；goal_id/capture_id、product、实际frame/reference、实际相机pose及数据绑定在一起。需要明确事件回调次序/适配器封装，避免观察器先运行而拿到旧buffer。
5. **fresh不是像素变化**：数组存在、零buffer、用户计数递增、单独ReferenceTime或Camera.frame都不够。ReferenceTime来自共享dispatcher，必须与product事件及对应数据结合；相同像素允许成功。若渲染时sim time不变，不能要求rendering_time严格增加，需采用经运行核实的新product完成事件/帧身份。频率节流也不能让新事件搭配旧current_frame；最小单次采集应避免非必要节流并核对同帧关联。
6. **关闭并确认**：拿到本次实际数据后，先关`hydra_texture.updates_enabled`，再pause回调，保持机器人。保留独立product事件观察器，确认关闭状态、排空/区分在途帧，并在约定有界检查窗口确认不再产生新采集；不能只看pause后冻结的current_frame。关停异常或超时则阻止下一运动，返回明确失败停止状态。OFF确认后才发布正常完成并允许下一goal。
7. **第二次采集**：从此时实际机器人状态开始，使用新的goal/capture身份、开启基线及fresh数据；旧回执、第一次图像或关闭时在途帧不能用于第二次成功。

S：`Camera._timeline_timer_callback_fn`（camera.py:429）在PLAY自动resume；因此reset/play之后必须重申OFF，不能只在构造时pause一次。自动resume回调与Hydra rendering开关是两个维度。

| 当前状态/事件 | 结果处理 |
|---|---|
| 尚无fresh事件或数据未就绪，未到deadline | `WAITING_DATA`，继续主循环，不立即判失败 |
| 正确capture窗口内实际返回所选数据 | 记录`data_received`；关闭并确认OFF后报告该视点成功 |
| capture API异常、身份不一致、约定数据等待超时 | 结束本次尝试并关闭相机；报告具体失败，不无限等待 |
| 数据已收到但关闭失败 | 分开记录`data_received=true`与`shutdown_failed`；不虚称没有采集，但整体执行不释放给下一目标 |
| 写盘失败 | 另记持久化结果；不把“停止写盘”当OFF，也不把写盘成功当实际采集证据 |

“数据实际返回”的接口检查只验证所选通道存在、buffer已由当前帧产生且可访问；不增加内容质量阈值。deadline用明确的仿真时间/渲染tick和必要wall-clock watchdog，防止渲染停滞时永不超时；无进展、正常GPU延迟和显式异常分开处理。

V：开启后product事件/ReferenceTime/数据严格同帧，首帧初始化行为，OFF之后在途帧排空和停止新帧，timeline边界，实际挂载随动、相机位置与数据时刻对应，都必须后续短仿真确认。**本轮仅找到源码支持，不能宣称相机启停或fresh保证已经PASS。**

## 5. 独立环境结构与后续复用边界

P：以下是拟新增位置，**本次均未创建实现文件**：

| 层次/拟路径 | 职责与复用来源 |
|---|---|
| `scripts/environments/run_single_robot_two_viewpoint_scan.py` | 独立入口、主simulation step/render调度、固定顺序驱动器；仅在goal1完整成功并OFF后提交goal2，失败则终止序列 |
| `T/scan_execution/contracts.py`、`single_viewpoint_executor.py` | goal/result/中间状态；submit、tick、cancel；组合运动和采集。单视点模块不知道“总共两个视点”，不拥有simulation循环 |
| `T/scan_execution/motion.py`、`collision_guard.py` | 实测pose、IK、限位/轨迹跟踪、有限路径/碰撞校验和停止；复用DiffIK/Articulation及明确选定的几何/运动学后端 |
| `T/scan_execution/camera_capture.py` | 独占product、任务ON/OFF、fresh-frame关联、超时及关闭确认；不把writer当采集控制器 |
| `T/scan_execution/scene.py`、`device_cfg.py` | 场景与设备、实际root/body/joint映射、末端挂载、构件/地面碰撞、传感器注册；借鉴独立articulation/contact/camera示例 |
| `T/configs/scan_execution/cr12_two_viewpoints.yaml` | 两个完整目标pose及frame、robot/base/lift初态、构件变换、相机外参/内参、容差、超时、joint限制；序列留在配置/驱动器，不写死在controller |

推荐状态机：

```text
IDLE_OFF → PLANNING_OFF → MOVING_OFF → ARRIVED_HOLD_OFF
  → CAPTURE_STARTING → WAITING_DATA → CAPTURE_CLOSING → SUCCEEDED_OFF
任何失败/取消 → STOPPING_AND_CLOSING → FAILED_OFF / STOP_UNCONFIRMED
```

tick应有有限工作量，scene拥有唯一physics/render时钟。planning也应分步或有界提交，不能让一个robot长阻塞等待相机或无限IK，阻止未来其他robot共同step。结果至少关联goal_id/attempt_id、阶段、原因、实测结束状态，以及有数据时的capture_id/product/frame；不需要全步raw dump。

未来MRTA只需：`effective assignment → submit(goal) → tick反馈 → 环境的ExecutionTransitionInput/Facts → 现有lifecycle authority`。执行模块不改owner/completed，不复制claim/release/reassign；普通camera timeout只是一次执行失败原因，是否重试、release或永久failed-pair由以后适配契约及现有authority决定。不能直接把任意采集异常置永久failed-pair。本次不实现这一适配，不改reward、统计、mask、学习器或公共event gate。

## 6. 推荐实施顺序与未来最小验收

所有步骤均需后续另行授权；本轮只提出方案。

| 步骤 | 新增内容/依赖 | 最小未来验证 |
|---|---|---|
| 1. 明确并加载一个可用设备 | 定位USD或确定URDF派生路线；处理惯性来源、joint drive、fixed root/升降保持、末端/camera frame；建立地面与保守构件碰撞 | 单独启动一场景，检查实际body/joint名称、scale、惯性/drive、初态合法；给有限关节目标，实测由执行器运动；相机保持OFF |
| 2. 单视点运动和按需采集 | 明确一个完整pose与安装变换；受限运动及路径/碰撞检查；独占product/fresh-frame封装 | 从合法初态运动并实测到位→ON→正常等待→一份本次数据→OFF；未收到数据且未到deadline时保持WAITING_DATA，等待超时或关闭失败时返回明确停止结果，不将到位当成功 |
| 3. 两视点连续循环 | 顺序驱动器与第二个完整pose；实际结束状态作为起点；失败后不提交第二点 | 一次完整OFF→move1→capture1→OFF→move2→capture2→OFF；核对两次数据身份、过程碰撞和关闭区间，退出后有简洁结果 |

未来双点验收保留少量可观察事实：

- 运动期间下发joint/actuator目标，实际joint/body状态变化；无goal间teleport、代理张量运动或独立移动相机。
- 每次ON之前实测camera/scanner完整pose满足约定到位条件，采集中保持；每次实际取得对应capture的新数据。
- 两次采集间扫描product处于OFF，独立事件观察支持其停止新采集；不能只凭writer停写或Camera.pause判定。
- 未收到本次数据不报告成功；WAITING_DATA、异常和timeout区分；停止/关闭未确认时不继续第二目标。
- 对初态、终态及转移段执行了相应碰撞检查，实际执行未通过构件穿模完成；允许支撑接触与禁止pair分开。
- 视点2由视点1真实结束状态连续执行；记录两个goal各自的结果，失败不伪造第二份数据。

仅建议保留两次实际采集数据及一份简洁执行记录：目标/实测pose、goal/capture/frame关联、ON/OFF边界、碰撞/错误摘要与结果。无需大量逐步raw dump、新qualification编号或历史审计体系。相机数据持久化格式属于实施小项，不升级扫描成功定义。

## 7. 缺口分类与少量待补资料

| 类别 | 事项 | 处理方式 |
|---|---|---|
| 影响加载路线，Q | 新机器人USD准确路径及它是否对应当前URDF；本次未定位，不能确认版本/drive/inertia差异 | 已异步询问；回答前以URDF条件方案完成评估，不认定USD已不存在于用户全部存储，也不扫描全盘 |
| 物理实施前需决定，Q | 八个URDF惯量不合物理必要条件；现成USD是否已修正未知 | 提供可靠参数，或明确批准仿真近似/重算策略；保留原始模型，本次不自动修复 |
| 目标/相机配置需落实，Q或实施设计 | 模型scanner frame、目标语义frame和拟建camera光心/光轴之间外参 | 提供安装资料，或审阅第一版明确的仿真安装约定；不再询问机器人角色或扫描成功定义 |
| 后续短运行，V | 导入root/body合并、PD与升降保持、惯性/collision cooking、两pose可达及完整路径、实际到位 | 有限单场景检查，不能以静态XML宣称通过 |
| 后续短运行，V | 独占product启动/关闭、在途帧、同product同帧数据、timeline自动resume | 验证真正OFF和fresh；无法确认时不声称满足双点闭环 |
| 实施小项 | 绝对mesh路径可移植性、非标准visual color写法、材质显示、输出格式、具体阈值/超时、导入后prim名 | 在批准的派生配置/适配中局部处理，原始资产本轮不变；不是重新开Phase B的理由 |
| 可后置 | 移动底盘/升降协同、任意障碍规划、多机避碰、实体SDK、深度/点云后处理、MRTA适配 | 不纳入本次最小场景；不新增研究方向或训练计划 |

真正需要用户补充/选择的集中问题只有：**USD准确入口；惯性采用可靠原值还是经批准的仿真近似；camera安装外参资料或可接受的第一版仿真定义。** 两个具体pose可以随后从现有集合或人工给定，并按固定基座与碰撞范围挑选；本次不要求先给所有最终实验目标才能完成评估。

## 8. 本次实际只读检查与限制

1. 读取适用[AgentRead/AGENTS.md](../../AGENTS.md)、当前[TASK_PROGRESS](../../TASK_PROGRESS.md)和最新[20260926项目交接](../20260926/PROJECT_STATE_AND_ROBOT_INTEGRATION_HANDOFF.md)。根及相关祖先未发现额外AGENTS。旧报告中的辅助角色、扫描质量待定、仅旧外观资产等表述不覆盖本轮新决定/新文件；未从历史R系列重启阅读或验收。
2. 只读Git：main，起始HEAD=`24ecbad7dd1bdcd006399b64bfb757a86b71aeec`；已有暂存删除`20260925/phase_b_local_artifact_cleanup_execution.zip`、未暂存TASK_PROGRESS、untracked 20260926报告及新`assets/rokeaCR12/`。保留原状，未用clean worktree作为前提。起始index SHA256=`3563d58e2f15d225a032c35e59afd0b60b907772de45b4309be4b901aeb9f67d`。
3. 资产范围定向目录/扩展名查找包含ignored文件；标准库XML解析、mesh路径存在性、OBJ顶点/面及mtllib轻量读取、七组visual/collision内容对比、惯性基础数学检查。没有导入机器人或项目模块，没有建场景、碰撞cooking或动力学验证。
4. Python通过 `D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python ...`，先核对sys.executable；离线检查只用标准库。首次多行`-c`被conda包装器拒绝，未执行解析；改为单行编码传入同一标准库解析后完成，未创建解析脚本/证据树。pxr不可独立发现，未启动Kit、安装依赖或污染导入路径。
5. 读取本地framework、installed camera/Replicator/Hydra/PhysX/URDF importer/motion源码及metadata，不调用这些runtime API。URDF importer扩展实际在`I/extscache/isaacsim.asset.importer.urdf-2.3.10+106.4.0.wx64.r.cp310/`，最初按exts路径未找到后定向定位到extscache；没有为路径查找错误停止整个评估。
6. 只对本次文档做正文、引用和scoped diff检查。没有旧checkpoint load/save、历史目录存在性/全量哈希/链接审计、旧数据恢复、UNKNOWN清理、压缩或移动。

因此本报告是**静态实施依据**，不是asset运行资格证明：未验证实际加载、驱动稳定、IK收敛、两点可达、路径无碰撞、camera启停或实际采集。用户“模型可驱动”的确认予以记录，当前新USD缺定位和URDF问题也如实保留，二者不互相覆盖。

## 9. 文档变更与下一步

本次只新增本文，并在TASK_PROGRESS小范围追加本次评估状态/报告链接。未重写历史handoff，故无需压缩归档；20260926报告保持原样。未新增或修改实现文件、测试/harness、运行配置、机器人资产或installed packages；未启动Isaac/GUI/headless/physics/render/camera；未训练、评估、连接设备或发送命令；未执行Git写操作。

建议审阅顺序：先确认第1节最小路线及第7节三个资料/选择项，再决定步骤1的具体资产与控制配置范围和有限运行授权。后续运动执行与采集模块须可复用，但此时无需引入MRTA或RL封装。Phase B保持 **COMPLETE / GPT REVIEW PASS / CLOSED**，既有清理边界保持。

**静态实施评估已完成，等待 GPT/用户审阅；尚未实施、尚未进行仿真验证。** 返回报告后停止，不自动进入环境实现、仿真、训练或Git提交。
