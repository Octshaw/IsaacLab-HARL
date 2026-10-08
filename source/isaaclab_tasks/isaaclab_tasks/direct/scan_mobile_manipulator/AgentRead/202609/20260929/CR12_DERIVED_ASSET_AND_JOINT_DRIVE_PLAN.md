# CR12 派生资产参数与基本关节驱动实施方案

日期：2026-09-29，Asia/Shanghai（UTC+08:00）。状态：**离线参数计算与实施方案已完成，等待GPT/用户审阅；尚未生成资产、尚未运行关节驱动。**

仓库：`E:\Project\IsaacLab_HARL`。本文 `T/`＝`source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/`，`L/`＝`source/isaaclab/isaaclab/`，`R`＝`T/assets/rokeaCR12/rokea_cr12_7DOF.urdf`，`M/`＝同目录 `model/`。数值单位统一为 **m、kg、rad、s、kg·m²**；惯量六分量顺序统一为 **(Ixx,Ixy,Ixz,Iyy,Iyz,Izz)**。小数位用于复算，不代表实物辨识精度。

## 1. 一个推荐方案与审阅边界

推荐采用**原质量暂用 + 每个有质量link的visual包围盒均匀实体近似 + CPU预合并固定组**，生成独立派生URDF，再经本地Isaac Sim 4.5导入USD。原URDF和mesh保持不变。首版把底盘固定在世界，将升降冻结于 **q0=0 m**；仅控制 `joint_1`…`joint_6`。预期派生机器人为 **7个刚体、6个活动关节、一个根固定约束**。

下一轮最小动作建议：空旷地面场景、六轴零位初态，经实际参数/接触检查后保持1秒；`joint_2` 用2秒五次多项式从0移动至 **+5°**，其余轴保持；终点保持3秒，按 **dt=1/120秒、720个受控physics steps** 有界结束。位置和解析速度目标同时下发，使用force类型的隐式PD，不用每步写状态实现运动。初态与该动作已有本文离线关节限位/FK/包围盒筛查，但**未获实际加载或无碰撞执行通过**。

这是基本资产与关节运动验证，不是末端IK、全空间可达性、移动/升降协同、构件避障、扫描相机或双视点实施。Phase B保持 **COMPLETE / GPT REVIEW PASS / CLOSED**；Windows组合启动路径及文档规则已审阅通过，本轮未重新验证。新USD已由用户删除，不寻找、不恢复。

证据口径：**文件事实**＝本轮直接读取；**计算结果**＝本轮CPU计算；**候选**＝拟采用的近似或调试参数；**运行待验**＝下一轮才能验证。用户原则同意制定有依据的派生惯性方案，**尚不等于批准本文具体参数、资产生成或仿真运行**。

## 2. 原参数、几何来源与问题

### 2.1 质量和坐标依据

本次定向检查的资产目录只有原URDF与model资源，没有取得可独立确认质量/质心/惯量的厂家资料或CAD质量属性文件。下表质量的依据仅为R中的`mass`，不是厂家已验证质量。`base_link/link_1`的质量及惯量完全重复，`link_5/scanner`也完全重复，进一步说明不能给这些输入加上实物认证含义。

10个有质量link的**原inertial rpy均为(0,0,0)**。原惯量关于各自原质心，坐标轴与所属link平行。20条mesh引用均为本机绝对路径、`scale=(0.001,0.001,0.001)`，visual/collision的origin xyz/rpy均为零。OBJ原坐标按该scale转换一次，得到下文米制尺寸；不再对惯量或导入全局重复乘0.001。

`world`（R:4）和`tool`（R:252）没有inertial，不补质量。visual/collision是同一对象的两种表示，每个link的质量只计一次。未引用的`object_convex_collision.obj`不纳入此机器人的质量或首轮场景。

| link | 原质量 | 原COM xyz | R中mass / inertia / COM行 |
|---|---:|---|---|
| agv | 50 | (0,0,0) | 19 / 20 / 21 |
| elevate | 10 | (0,0,0) | 38 / 39 / 40 |
| base_link | 3.440749380 | (-0.000072769597,-0.01679187012,0.2986854502) | 57 / 58 / 59 |
| link_1 | 3.440749380 | 同base_link | 77 / 78 / 79 |
| link_2 | 5.024380503 | (0,0.003491209523,0.2410487354) | 97 / 98 / 99 |
| link_3 | 2.439584706 | (0,0.023,0.097) | 117 / 118 / 119 |
| link_4 | 2.439584706 | (0,-0.020,-0.046) | 137 / 138 / 139 |
| link_5 | 2.422757896 | (0,0.012,0.096) | 157 / 158 / 159 |
| link_6 | 1.229800857 | (0,0.017,-0.043) | 177 / 178 / 179 |
| scanner | 2.422757896 | (0,0.012,0.096) | 274 / 275 / 276 |

### 2.2 完整惯量数学检查

构造对称矩阵 `I=[[Ixx,Ixy,Ixz],[Ixy,Iyy,Iyz],[Ixz,Iyz,Izz]]`，用CPU float64的`eigvalsh`求升序主惯量λ。正定检查要求λmin>0；物理必要条件还要求 **δ=λ1+λ2−λ3≥0**，不能只看对角元素。

| link | 原六分量 | 升序主惯量λ（约值） | δ | 判定 |
|---|---|---|---:|---|
| agv / elevate，各自 | (1,0,0,1,0,1) | (1,1,1) | 1 | 数学通过，真实参数未核实 |
| base_link / link_1，各自 | (0.017648370,0,0,0.016617391,-0.002218013,1.120163944) | (0.016612933,0.017648370,1.120168402) | -1.085907099 | 正定，但物理必要条件失败 |
| link_2 | (0.136759927,0,0,1.747453457,-0.024189444,0.012535321) | (0.012198120,0.136759927,1.747790658) | -1.598832610 | 同上 |
| link_3 | (0.026159338,0,0,0.024282179,-0.006156370,1.119898350) | (0.024247587,0.026159338,1.119932942) | -1.069526017 | 同上 |
| link_4 | (0.012,0,0,0.221,-0.002,0.004) | (0.003981568,0.012,0.221018432) | -0.205036863 | 同上 |
| link_5 / scanner，各自 | (0.016,0,0,0.015,-0.002,0.213) | (0.014979800,0.016,0.213020200) | -0.182040400 | 同上 |
| link_6 | (0.002,0,0,0.212,0,0.002) | (0.002,0.002,0.212) | -0.208 | 同上 |

结果与旧评估的“八个link异常”一致：**10个原矩阵均正定，8个违反主惯量三角条件**。本轮进一步发现原COM在对应visual AABB外的有elevate、base_link、link_2、link_5：分别是z=0低于0.069500061、z=0.298685450高于0.130006058、y=0.003491210低于0.099999092、z=0.096高于0.078000992。这不是实物COM必错的最终证明（visual可能不含全部物质），但不能保留无法解释的原COM并拼接另一几何中心的惯量。

### 2.3 候选几何与质量分布

选择每个link的**visual AABB均匀实心盒**作为等效质量模型：质量仍取上表暂用值，COM取该盒中心，惯量与COM来自同一分布。没有采用面片有符号体积积分，没有将未验证的封闭性/方向当成可靠体积依据，也没有开发网格修复器。AABB来自缩放/变换后的OBJ顶点；全部顶点和被面引用顶点的极值相同，scanner visual中18个未被面引用顶点不改变极值。

下表`d`为尺寸，`c`为**候选COM（link坐标）**；包围盒min/max可由`c±d/2`复算。文件前缀加`_visual.obj`或`_collision.obj`即实际文件名。

| link / M下文件前缀 | d=(dx,dy,dz)，m | c=(x,y,z)，m | R中visual/collision mesh行 |
|---|---|---|---|
| agv / scanner_sys_agv | (1.054000000,0.860000092,1.184999939) | (0,0.000000015,0.539500031) | 9 / 15 |
| elevate / scanner_sys_elevate | (0.536000015,0.400000031,0.802999878) | (0.036997032,0.000000015,0.471000000) | 28 / 34 |
| base_link / cr12_base | (0.352106980,0.312515137,0.130020522) | (-0.030957100,0.011132325,0.064995797) | 47 / 53 |
| link_1 / cr12_link1 | (0.196384918,0.202754860,0.317719704) | (-0.000008324,0.003624203,0.283859081) | 66 / 73 |
| link_2 / cr12_link2 | (0.185159432,0.183492638,0.934210708) | (-0.000023014,0.191745411,0.369056328) | 86 / 93 |
| link_3 / cr12_link3 | (0.151993362,0.166982697,0.282017288) | (-0.000072464,0.021512238,0.064993309) | 106 / 113 |
| link_4 / cr12_link4 | (0.115942360,0.139041126,0.394194500) | (0.000037994,-0.009180899,-0.141903635) | 126 / 133 |
| link_5 / cr12_link5 | (0.111851364,0.130024048,0.205171005) | (-0.000008404,0.011287979,-0.024584511) | 146 / 153 |
| link_6 / cr12_link6 | (0.104606723,0.104698978,0.054009011) | (-0.000003367,0.000060629,-0.026996205) | 166 / 173 |
| scanner / scanner_sys_scanner | (0.297877563,0.333858490,0.384808167) | (-0.000017059,-0.129429245,0.192403900) | 263 / 270 |

collision在base_link及link_1…6的尺寸与visual一致；elevate/scanner仅导出小数舍入差。AGV collision高度为 **1.240499939m**，上界比visual多55.5mm，因此用于接触筛查的collision尺寸不能无说明替代上述惯性模型。首轮保留源collision，不把质量盒替换为碰撞盒。

这是一种仿真近似，不是实体动力学辨识，也不因包住外形就“保守安全”。等效密度范围约46.55–2079.06kg/m³（AGV46.55、elevate58.08、scanner63.31），反映包围盒包含空腔/空空间、质量来源未认证；不能当作材料密度。AGV的1.185m高整盒尤其粗略，但首版根固定，不借此认证底盘动态响应。该模型拟用于有限关节功能调试，是否可用仍待导入与驱动验证；动力学精度、硬件额定能力或更大动作需更可靠参数。

## 3. 可审阅的推荐惯量与固定组合并

### 3.1 逐link候选值

对各盒：

`c=(vmin+vmax)/2`，`d=vmax−vmin`；

`Ic=(m/12) diag(dy²+dz², dx²+dz², dx²+dy²)`。

质量取2.1表、COM取2.3表；以下关于**候选COM**、沿本link轴表达，**inertial rpy=(0,0,0)**。每行完整六分量为`(Ixx,0,0,Iyy,0,Izz)`。这同时替换原COM和惯量，不逐个修补非法特征值；AGV/elevate也使用同一自洽近似，不将原单位矩阵作为已证真值保留。

| link | Ixx | Iyy | Izz | λmin / δ（均>0） |
|---|---:|---:|---:|---|
| agv | 8.932604220 | 10.479753564 | 7.710483990 | 7.710483990 / 6.163334646 |
| elevate | 0.670674024 | 0.776754017 | 0.372746701 | 0.372746701 / 0.266666707 |
| base_link | 0.032850855 | 0.040395734 | 0.063552085 | 0.032850855 / 0.009694504 |
| link_1 | 0.040731403 | 0.040002395 | 0.022845592 | 0.022845592 / 0.022116584 |
| link_2 | 0.379516244 | 0.379773521 | 0.028452047 | 0.028452047 / 0.028194770 |
| link_3 | 0.021837733 | 0.020865714 | 0.010365227 | 0.010365227 / 0.009393207 |
| link_4 | 0.035520707 | 0.034323317 | 0.006663129 | 0.006663129 / 0.005465739 |
| link_5 | 0.011912175 | 0.011024733 | 0.005939185 | 0.005939185 / 0.005051744 |
| link_6 | 0.001422352 | 0.001420373 | 0.002244842 | 0.001420373 / 0.000597883 |
| scanner | 0.052399976 | 0.047810779 | 0.040418170 | 0.040418170 / 0.035828972 |

### 3.2 合并方法与最终两个聚合刚体

对组内成员在组坐标中的变换`(Ri,ti)`，先求`ci'=Ri ci+ti`，再计算：

`M=Σmi`，`C=Σ(mi ci')/M`，`di=ci'−C`；

`IC=Σ[Ri Ii Riᵀ + mi ((di·di)E − di diᵀ)]`。

这是关于**合并质心**的完整张量，保留非零交叉项。质心整体换世界坐标时，不再对关于质心的惯量重复加平行轴项。

基础组以agv frame为坐标：agv、elevate、base_link的平移分别为`(0,0,0)`、`(0,0,0.314)`、`(0.105,0,1.062)`，旋转均为单位阵。冻结的q0=0来自升降合法下限，避免引入额外高度选择或主动伺服负载；不是将`fix_base`误当升降锁定。末端组以link_6 frame为坐标：tool为单位变换，scanner为零平移、`Rz(2.356194490192345)=Rz(135°)`，必须先旋转scanner的COM和张量。其变换后COM为`(0.091532360,0.091508234,0.192403900)`。

| 最终刚体组（保留名称） | 建议质量 | 建议COM（组坐标） | 建议完整六分量（关于COM、组轴） |
|---|---:|---|---|
| agv+elevate+base_link → **agv** | 63.440749380 | (0.009847510,0.000603783,0.610060757) | (11.110953937,-0.002458907,-0.196418282,12.797724006,-0.019800414,8.173585187) |
| link_6+tool+scanner → **link_6** | 3.652558753 | (0.060712673,0.060718218,0.118532826) | (0.097615839,-0.009122867,-0.016382307,0.097627014,-0.016366536,0.056319555) |

基础组主惯量`(8.160423576,11.124029205,12.797810348)`、δ=6.486642433；末端组主惯量`(0.044211263,0.100606849,0.106744296)`、δ=0.038073816，均正定且满足必要约束。另以每盒8个二阶矩精确求积点复核聚合结果，惯量矩阵最大差分别约`1.78e-15`、`2.78e-17 kg·m²`，不是导入测试。

最终另外5个刚体为link_1…link_5，直接使用3.1和2.3表。最终7体总质量仍为 **82.860365324kg**，其中活动臂含scanner质量为19.419615944kg；world/tool不另计。最终派生文件只写聚合体惯量，不能再保留带质量的elevate/base_link/scanner子体交给importer重复累加。

## 4. 派生资产生成、固定关系与导入设置

### 4.1 下一轮拟生成的独立路径

拟用目录`T/assets/rokeaCR12/derived/fixed_lift0_v1/`：

- `cr12_fixed_lift0.urdf`：预合并、参数明确的派生输入；本次未生成。
- `usd/cr12_fixed_lift0.usd`及转换器实际需要的同目录引用层：本次未生成；不放AgentRead，不复制原mesh。

派生URDF的mesh引用改为相对该URDF的`../../model/<原文件名>.obj`，统一斜杠；原文件的E盘绝对路径不修改。生成前逐个resolve并核对确实指回原20条mesh，不靠工作目录拼接。转换后检查USD的实际引用和加载路径，不以URDF相对路径正确代替USD可移植性确认。初版派生USD针对本仓库布局；原生转换若产生绝对引用要记录，必要修复限定在派生资产内。

结构处理顺序：

1. 在内存中读取原文件，计算候选参数；向新路径写派生文件，已存在则停止覆盖并使用清楚版本后缀。
2. 派生版移除无质量`world`及`joint_agv`。原world→agv的`z=0.053`由场景根位姿**应用一次**，不再藏进所有顶点或添加第二个world固定。
3. 将joint_0固定于q0=0并在生成阶段合并基础三体；`joint_1`重接agv，其origin改为 **(0.105,0,1.062)**，轴仍Z，其余臂关节变换不改。
4. 预合并link_6、tool、scanner；visual/collision的origin按相同刚体变换合成，保留各份几何表示和唯一合成惯量。派生URDF中不保留这两个内部固定关节及被合并的物理link。
5. 将米制关节/COM/惯量写入；mesh仍保持scale=0.001。预期URDF只有7个物理link和6个revolute，**无内部fixed joints**。
6. 导入后如需保留安装frame，在实际link_6刚体prim下建立`tool`纯Xform（单位变换）及其子`scanner`纯Xform（Rz135°）；禁止附加RigidBody/Mass/Joint。这些frame与保留的scanner几何要对齐，不再计质量。相机光心本轮不定义。elevate/base_link的装配关系由上述变换保留，必要时只作纯frame读回。

### 4.2 本地接口与明确覆盖关系

仓库`VERSION=2.1.0`、Isaac Lab扩展metadata=0.36.23；本机URDF importer为 **2.3.10**。安装目录缩写`U/`＝`C:/isaacenvs/isaac45_harl/Lib/site-packages/isaacsim/extscache/isaacsim.asset.importer.urdf-2.3.10+106.4.0.wx64.r.cp310/`（本机源码路径，不是交付副本）。

| 设置/接口 | 推荐值与理由 | 本地源码锚点 |
|---|---|---|
| converter | `UrdfConverter`，只读设计；生成USD需下一轮App后调用 | `L/sim/converters/urdf_converter.py:70,84` |
| `fix_base` / `root_link_name` | `True` / `"agv"`；只由importer创建一个world→agv固定 | cfg `:90,93`；converter `:80,126` |
| `merge_fixed_joints` | **False**，因为派生URDF已预合并且没有内部fixed；不依赖native再次合并或保存frame | cfg `:102`；converter `:123` |
| 惯量 | 采用派生文件给定mass/COM/完整张量，不由密度重算 | `U/docs/CHANGELOG.md:95–98`：已有惯量始终导入，旧开关弃用 |
| `link_density` | `0.0`；仅为缺失质量备用设置。生成前禁止7体缺mass/inertial，读回发现缺失即停止，不能让默认密度补齐 | cfg `:99`；`U/scripts/ui/UrdfOptionWidget.py:173` |
| 米制与Z-up | distance_scale=1.0；up_vector=(0,0,1)；USD stage再读回metersPerUnit=1、upAxis=Z | converter `:108`；`U/scripts/extension.py:164` |
| 几何 | `collision_from_visuals=False`，`collider_type="convex_hull"`，`replace_cylinders_with_capsules=False` | cfg `:114–129`；converter `:118–134` |
| 自碰撞 | `self_collision=True`；相邻安装连接与固定组内部接触按5.4处理 | converter `:128` |
| drive | `JointDriveCfg(drive_type="force",target_type="position",gains=PDGainsCfg(...))`，显式采用5.3表 | cfg `:71–86`；converter `:145–194,272–300` |
| 转换输出 | `make_instanceable=False`便于初版检查；明确`usd_dir/usd_file_name`，必要时`force_usd_conversion=True`，仅用于尚未有产物的新版本目录，不覆盖已有派生文件 | `AssetConverterBaseCfg:18,25,35,41`；不清理旧目录 |
| spawn覆盖 | `mass_props=None`、`fix_root_link=None`；不递归覆盖已写7体质量、不另造固定约束 | `L/sim/spawners/from_files/from_files.py:242`；`L/sim/schemas/schemas.py:129–154,408–425` |

**重要接口限制**：当前`UrdfConverterCfg`没有`import_inertia_tensor`、`up_axis`字段；不写不存在的配置项。下一轮可在准备入口内使用一个薄的项目内subclass，仅覆盖`_get_urdf_import_config()`：调用super后显式`set_import_inertia_tensor(True)`及`set_up_vector(0,0,1)`，本地安装UI分别在`:156,164`使用这些API。旧惯量setter已弃用，显式调用用于表达意图，**实际是否采用仍由导入读回裁定**；不能用False自动修复原非法惯量。wrapper原始单位/场景设置不改，installed packages不改。native核心内部没有本轮可验证的C++实现，不能用Python配置存在保证结果。

原URDF的`dynamics damping=0.7`保留为原资料，不把它称为摩擦或最终PD damping；生成/运行的PD按明确表覆盖。原effort/velocity/位置limits在派生URDF中保留，运行时采用更小的**调试上限**，不宣称更改实机额定能力。转换器对旋转PD把每rad值乘π/180后写USD；ImplicitActuator/Tensor接口仍传rad单位值，**不得再手工换算一次**。

### 4.3 导入后必须实际读回

USD层核对default prim、所有RigidBody/ArticulationRootAPI位置、唯一根固定joint及其body绑定、7体/6活动关节、所有collision启用情况、纯tool/scanner frame、metersPerUnit/upAxis和引用资源。预计外层路径`/World/CR12`；内部articulation root prim和shape路径由导入实物枚举，**不假定一定是某个拼出来的字符串**。若多root、漏体、仍有joint_0、重复scanner质量或单位不符，停止本次加载，不能用运行时偷偷改质量掩盖。

**根位姿与固定anchor不能各自假定正确**：本地spawn源码只明确传递/设置Xform（`L/sim/spawners/from_files/from_files.py:221–227`），没有足够证据证明importer生成的world固定anchor会自动随spawn偏移校准，此行为为UNKNOWN。下一轮在spawn完成、首次物理初始化前，识别现有唯一FixedJoint中缺失body relation的世界侧，核对两侧joint frame的世界位姿一致，即世界侧anchor等于`T_world_body × T_body_joint`。若不一致，仅在初始化场景层校准该现有joint的世界侧localPos/localRot后复核，不另建约束。刚体侧局部frame为恒等时，anchor应随agv落在z=0.053；非恒等时必须合成局部frame。运行期不再改变root或anchor。此检查属于待实施的装配一致性步骤，尚未实测。

初始化并应用actuator后还要读最终PhysX值：

- `Articulation.is_fixed_base/num_joints/num_bodies/joint_names/body_names`（`L/assets/articulation/articulation.py:115–147`），通过`find_joints(...,preserve_order=True):224`建立名称映射，期望顺序为joint_1…6，但不假定native数组顺序。
- `root_physx_view.get_masses()/get_coms()/get_inertias()`；本地Tensor API `.../isaacsim/extsPhysics/omni.physics.tensors/omni/physics/tensors/impl/api.py:2071,2123,2149`。COM pose相对body，raw quaternion为**xyzw**；惯量给在**COM局部frame**，9个元素按row-major构造矩阵。用COM旋转将其变为本报告body轴：`Ibody=Rcom Icom Rcomᵀ`，再比较关于同一个COM的张量，不加一次无关平行轴项。USD则用`physics:diagonalInertia`与`physics:principalAxes`重建，不能直接比较三个对角数与本报告六分量；已从USD重建到body轴的矩阵不再重复乘COM旋转。
- 同一Tensor API的`get_dof_limits/stiffnesses/dampings/max_forces/max_velocities`（`:744,807,833,859,911`）及摩擦/armature；`articulation.py:1360–1382`会在actuator设置时覆盖参数，因此既看USD，也看最终Tensor结果。
- 参数一致性的候选容差：质量相对1e-5（绝对底线1e-6kg），COM绝对1e-5m，惯量矩阵`atol=1e-6 kg·m², rtol=1e-4`，K/D/limits相对1e-4；质量总和和正定/三角条件另查。容差用于float32/转换舍入，不能容纳自动重算成另一套质量分布。

## 5. 最小独立关节驱动方案

### 5.1 拟新增文件和启动复用

下一轮只需少量文件（**本次均未创建**）：

| 拟新增位置 | 职责 |
|---|---|
| `scripts/environments/prepare_cr12_fixed_asset.py` | 原资产只读、派生URDF计算/写出；经明确模式选择后在App中转换USD、补纯frame和读回；薄converter subclass放此处，无新通用框架 |
| `source/isaaclab_assets/isaaclab_assets/robots/rokea_cr12.py` | 可复用ArticulationCfg、6轴调试K/D/limits、期望组参数与本报告版本标识；App后导入，不改已有机器人配置 |
| `scripts/environments/run_cr12_joint_drive.py` | 一机器人、地面、照明、有限目标序列、实际状态/接触检查、关闭结果；无需gym/RL/MRTA，也不创建完整扫描executor空壳 |

正式入口不依赖AgentRead日目录中的脚本。启动顺序沿用已接受路径：解析App参数 → `_windows_runtime_startup.prepare_windows_runtime_args` → Windows/CUDA共用准备 → AppLauncher → Isaac/Articulation及设备配置。当前`view_scan_assignment.py:8–18`顶层只有标准库和纯helper，`:299`有main guard；可从同目录**仅导入**其`_prepare_cuda_before_app:51`，不调用viewer.main，不启动legacy环境。这是对已有私有函数的窄依赖，报告明确记录；本次及建议首轮不为此重构已接受viewer/train/play。不要复用依赖viewer.main全局torch的`_verify_cuda_after_app`来制造隐藏依赖。

实际入口使用harl Python、UTF8=1、GUI、`device=cuda:0`，省略kit_args取得Windows缺省D3D12；记录实际experience/backend。GUI viewport不等于实现扫描相机，保持enable_cameras=false、无video。URDF纯计算模式在App/CUDA导入前完成并退出；只有经下一轮授权的USD模式才创建App。

### 5.2 六轴映射、初态与离线筛查

| 关节 | 轴（joint局部） | parent→joint origin，m | 原位置限位rad | 原velocity rad/s / effort Nm |
|---|---|---|---|---|
| joint_1 | Z | 派生agv下(0.105,0,1.062) | ±3.0543 | 2.094395 / 300 |
| joint_2 | Y | link_1下(0,0,0.35) | ±2.9671 | 2.094395 / 300 |
| joint_3 | Y | link_2下(0,0,0.76) | ±3.0543 | 3.1415926 / 300 |
| joint_4 | Z | link_3下(0,0,0.54) | ±3.0543 | 4.084070 / 300 |
| joint_5 | Y | link_4下(0,-0.15,0) | ±3.0543 | 4.1887901 / 300 |
| joint_6 | Z | link_5下(0,0,0.123) | ±3.0543 | 4.1887901 / 300 |

来源R:202–248；所有joint origin rpy=0。候选初态`q=(0,0,0,0,0,0), dq=0`、agv世界pose=`(0,0,0.053), quat(wxyz)=(1,0,0,0)`。零位不是未经检查的默认：6轴均严格在原limits内；按原变换和collision顶点计算，AGV最低z=0，其他mesh不穿地面；base_link frame世界位置`(0.105,0,1.115)`，scanner frame零位位置`(0.105,-0.15,2.888)`，均与一次应用root高度一致。零位可能不适合未来IK，首轮只做关节控制，不将其当通用工作姿态。

对名义`joint_2=0…5°`、其余零位，按0.05°间隔计算101个FK状态，转换各collision局部包围盒8角到世界，排除同一刚体组和直接相邻安装对后，未出现非相邻AABB相交。最小间距约 **19.338mm**，为link_4/link_6在5°附近。最大相关角点半径1.83560m，每半采样间隔的参考位移界约0.801mm；此处不据此认证实际运动。

另对11个名义角度（间隔0.5°），叠加6轴各±0.5°误差角点，共704个姿态，仍未检出非相邻AABB相交，最小约 **16.142mm**。这是有限角点筛查，**不是整个连续误差盒的证明**，也未包括PhysX凸包烹饪/接触offset和实际跟踪行为。下一轮须在真实状态及碰撞模型上继续检查，不能把“候选合法”写成加载/无碰撞PASS。

### 5.3 驱动数值、依据和运行期下发

推荐force position drive + `ImplicitActuatorCfg`。用候选质量模型在零位计算冻结其他轴时的轴等效惯量：

`J_i=Σ[a_iᵀ Rk Ik Rkᵀ a_i + mk (||rk||²−(a_i·rk)²)]`，

重力广义力矩`τg_i=Σ a_i·[rk×mk(0,0,-9.81)]`，总和仅含该轴下游body；scanner按其实际安装旋转计入。以下J和重力是模型估算，非电机/减速器识别，不含已知厂家转子惯量。

| 轴 | 零位J，kg·m² | 名义0→5°路径重力力矩绝对值峰值估计，Nm | stiffness，Nm/rad | damping，Nm·s/rad | effort_limit_sim，Nm |
|---|---:|---:|---:|---:|---:|
| joint_1 | 0.405887645 | 0 | 200 | 20 | 20 |
| joint_2 | 18.794490640 | 15.342877 | 4000 | 550 | 60 |
| joint_3 | 3.448809055 | 6.640395 | 2000 | 166 | 30 |
| joint_4 | 0.158322694 | 0.585306 | 200 | 12 | 10 |
| joint_5 | 0.336662855 | 2.870320 | 1000 | 37 | 10 |
| joint_6 | 0.083248887 | 0.189619 | 150 | 7 | 5 |

全部轴`velocity_limit_sim=0.2 rad/s`；原URDF较高limits保留为原资料，以上是**此小幅实验的仿真调试限制**，不是新的实机额定能力。K按有限重力负载和约0.5°误差目标选取，D近似`2√(KJ)`；多轴耦合存在，不能称整机已临界阻尼。joint_1的J在5°时增至约0.609838，说明并非恒定惯量。上述表须随质量模型版本一致使用，不借添加任意armature、减质量或关重力求稳定。

预计静态重力偏差joint_2约`15.342877/4000=0.003836rad=0.220°`，joint_3约0.190°，joint_5约0.164°，因此不提出与候选PD矛盾的“零误差”验收。2秒5°五次目标峰速度 **0.0818123rad/s**、峰加速度 **0.1259583rad/s²**，joint_2惯性加速项约2.37Nm，60Nm限制相对15.34Nm重力与该项有调试余量；仍未证明耦合/接触情况下不饱和。5°处质量矩阵第2列约`(0.539059,18.794491,7.425941,0.940900,1.406109,-0.358243)`，其余保持轴也承受耦合，不能忽略。

目标定义：初始1秒保持；接着2秒令`s=(t−1)/2`、`h=10s³−15s⁴+6s⁵`，`q2_ref=(5π/180)h`，`dq2_ref=(5π/180)(30s²−60s³+30s⁴)/2`；结束后q2保持5°、dq2=0，其他轴全程q_ref=0/dq_ref=0。必须同时下发位置和解析速度，否则D2乘峰速度约45Nm的额外阻尼会改变设计条件。

初始化允许一次写root/joint初态；运行期仅`set_joint_position_target`、`set_joint_velocity_target` → `write_data_to_sim()` → `sim.step(render=False)` → `robot.update(dt)` → 每个ContactSensor的`update(dt,force_recompute=True)` → 读取实际q/dq/body状态及本步接触守卫。每两个physics ticks单独`sim.render()`，不靠默认`sim.step()`混合推进物理与渲染。不循环写joint/root state、不独立移动scanner。`L/assets/articulation/articulation.py:473,882,906,173,202`分别对应状态/目标/写入/更新接口；传感器刷新见`L/sensors/sensor_base.py:197–205`。目标setter不自动限幅，soft_joint_pos_limits也不是物理强制限位。使用`L/actuators/actuator_cfg.py:79,96`的`effort_limit_sim/velocity_limit_sim`字段；旧`velocity_limit`对隐式驱动被忽略（`L/actuators/actuator_pd.py:79–89`）。

原damping=0.7不作为Coulomb摩擦系数。初版不人工增加摩擦/armature；读取导入值并记录，若和未声明摩擦/转子惯量的假设明显不符则停止核查。隐式actuator的computed/applied_torque是近似量（`:134–140`），不得当成实机力矩测量。

### 5.4 场景和碰撞边界

只放一个固定CR12、地面和照明，暂不加入构件。保持`gravity=(0,0,-9.81)`、collider启用、自碰撞启用；以原collision mesh为几何输入，初版每份采用convex hull，不改原mesh。候选`contact_offset=0.002m`、`rest_offset=0`，读回实际值；该设置不代表几何精度已验证。固定组内的重叠表示同一刚体的多个形状；允许相邻连接的安装接触以及agv—地面支撑。直接相邻6对的joint `physics:collisionEnabled`须核对为false以避免铰接安装面自撞，非相邻body对保持可碰撞；不扩大为全机器人关闭碰撞。

运动前核对实际body变换、cook后碰撞范围、根/地面关系；运行期按实际body位姿检查非相邻碰撞包围盒和地面高度，出现非相邻盒重叠即停止待精查（允许保守误报，不继续穿过）。启用`UsdFileCfg.activate_contact_sensors=True`，按body建立单对多的ContactSensor过滤矩阵，只列禁止接触对象；不能用一个多body过滤器或净合力为0证明无碰撞。入口自行对禁止pair的法向接触向量范数作停机判断，候选阈值 **0.1N单步**；该阈值是数值检测阈值，不是安全力限，也不能用它接受肉眼可见穿透。

本地依据：`L/sensors/contact_sensor/contact_sensor.py:33–60,280,341`、`contact_sensor_cfg.py:26–50`；`force_threshold`字段只服务接触时间统计，不会自动停机。独立场景的`robot.update`不会刷新ContactSensor，须按5.3逐步强制更新，不能重复读旧过滤矩阵。首轮禁止接触=非相邻body之间、所有活动臂体与地面；允许对不要计入失败矩阵。若首态有异常接触，不在运行中禁用碰撞绕过；先结束并定位派生几何/安装/过滤错误。这里没有主动避障规划，也不声称机器人—构件路径安全。

## 6. 下一轮有限验证计划（本次未执行）

### 6.1 顺序、配置与预算

1. **离线派生URDF**：按审阅参数计算/预合并/写入新路径；核对7体6轴、总质量、完整惯量、原mesh引用和frame变换。CPU准备预算30秒；不创建App。原文件不写入。
2. **单次派生USD导入**：明确harl Python，GUI/D3D12/CUDA启动处理不变，App建立后调用上述薄converter。读回USD、唯一固定关系及引用；失败即结束，不带错误模型进入驱动。App阶段上限180秒，总墙钟360秒（含关闭）。这一进程不做关节运动。
3. **一次基本驱动GUI运行**：同样启动处理；`SimulationCfg(dt=1/120,render_interval=2,device="cuda:0",gravity=(0,0,-9.81))`，建议TGS、articulation position/velocity iterations=8/2作为固定候选，不临时修改全局求解器求通过。地面/机器人/接触报告构造、初始化、最终参数读回后，从清楚基线执行1+2+3秒序列。App上限180秒，总墙钟360秒，允许正常辅助进程关闭时间；不使用headless替代。

工作目录均为`E:\Project\IsaacLab_HARL`，解释器为`C:\isaacenvs\isaac45_harl\python.exe`，外层使用`D:\miniconda3\Scripts\conda.exe run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u ...`。具体新CLI按下一轮实现，以下是**实施后拟定命令**，目前文件/参数尚不存在，不能当作已经执行：

```powershell
& D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python scripts/environments/prepare_cr12_fixed_asset.py --stage urdf
& D:\miniconda3\Scripts\conda.exe run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/prepare_cr12_fixed_asset.py --stage usd --device cuda:0 --info
& D:\miniconda3\Scripts\conda.exe run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/run_cr12_joint_drive.py --device cuda:0 --physics_steps 720 --info
```

这三个入口模式必须将资产版本、路径和参数来源打印到各自记录；不从用户共享配置悄悄切换模式。下一轮若需外层进程监督，复用安全Job/输出排空方法，只启动目标入口、计时与收尾；必要的一次性适配脚本放该轮证据目录`repro/`，不让正式入口依赖旧AgentRead监督器，也不开发通用启动框架。

### 6.2 实际physics计数和结果判据

720指**受控物理步数**，控制每physics tick一次，通过`sim.step(render=False)`推进，渲染每2步单独`sim.render()`；不等于旧viewer的120 env.step，也不等于720打印/渲染帧。本地现有相同调用范式见`L/envs/direct_marl_env.py:375–382`。初始化`sim.reset()`可能包含初始化更新，其计数单列；准备阶段若出现超过预期的物理推进要记录/停止，不能混入动作成功数。

初始化及读回完成后记录`current_time_step_index/current_time`基线，核对受控阶段实际增量 **720步 / 6秒**，累计时间允许1e-4秒舍入差。`L/sim/simulation_context.py:530–555`暂停恢复路径可能额外physics推进，故不能只计Python调用；暂停、stop、提前关窗或计数偏差均记本次未完成。预算由外层独立计时，不受阻塞读取/GUI暂停拖死。

| 检查项 | 候选通过/停止条件 |
|---|---|
| 资产参数 | 4.3读回一致；7body、6DOF、唯一固定根；无joint_0 DOF；无重复scanner质量。任一不符，不运动 |
| 初态 | q零位、dq零、限位内；实际collider/安装接触合理。非有限量、非法root/frame或异常接触即停 |
| 实际运动 | joint_2实际位移达到约5°，终点至少4.5°；不是只看到target更新。所有axis状态来自PhysX读回 |
| 全过程跟踪 | 任一轴`abs(q_actual−q_ref)>0.5°`或`abs(dq_actual)>0.25rad/s`即停；原硬限位越界超过1e-3rad立即停，不靠修改目标/阈值继续 |
| 最后一秒保持 | 每轴位置误差≤0.5°、速度绝对值≤0.01rad/s；joint_1/3/4/5/6保持零位。不把正常0.2°左右PD静态偏差误判为必须零误差 |
| 固定关系 | agv的link frame pose（不以COM pose代替）相对初态平移≤1e-4m、旋转≤1e-4rad；升降frame相对agv固定变换误差≤1e-5m/rad。结构上无升降DOF，不把target=0称锁定 |
| 接触/几何 | 禁止pair接触超过5.4阈值，或实际非相邻包围盒相交、活动臂几何穿地，立即停并保留pair/阶段。AGV正常地面支撑单列 |
| 无进展/异常 | ramp阶段1秒时joint_2距起点仍<1°，或NaN/Inf、持续发散、非法参数、资源异常，立即结束；不无限等待 |
| 工作与退出 | 足额physics/time、全部判据完成后写work_completed；资源关闭错误单列，App close前flush事实；内部失败即使exit0也不通过。实际Python/外层退出、无超时和无残留所属进程共同判断 |

0.5°全过程界是待审的固定验收条件，不因第一次失败而事后放宽。若局部PD调试获下一轮明确授权，最多一次新进程重试：仅在确认为无碰撞、无模型错误且跟踪/振荡问题时，K在表值的0.8–1.25倍内、D围绕`2√(KJ)`的0.8–1.2倍调整，保留首轮失败与改动理由；effort/速度上限、目标、重力、碰撞和通过阈值不随意改变。模型/单位/根绑定/异常接触/原生GPU故障不走该自动调参分支。导入/驱动全部需要新授权，本轮没有使用重试额度。

原始记录只需每次命令/console/对应Kit日志、简洁参数读回和动作摘要（起点、终点、最大误差/速度/漂移、接触/失败、实际计数/时间、关闭/退出）；不保存逐tick全量张量，不做新ledger或大型矩阵。后续证据首选`logs/scan_assignment/YYYYMMDD_cr12_joint_drive/attempt_01/`，该目录受忽略规则影响，报告明确其本地可获取性；资产保存在自身目录。无需相机数据或checkpoint。

## 7. 本次实际做过什么、未做什么

执行了适用规则/当前交接/主题导航读取，按主题定向读旧资产评估及已接受启动报告的复用章节；读取原URDF、20条引用OBJ的顶点/面引用、必要本地converter/actuator/articulation/contact/physics API源码。没有重读Phase B系列、重跑Windows或解析历史原始运行记录。

实际解释器核对命令：

```powershell
& D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python -c "import sys; print(sys.executable); print(sys.flags.utf8_mode)"
```

结果为harl Python、UTF8 mode=1。计算通过同一绝对Conda命令的`python -c`在内存中执行XML/OBJ解析与NumPy **1.26.4 CPU float64**代码，没有保存分析脚本或JSON；未导入torch、Isaac、pxr或converter。主要操作为缩放/刚体变换、min/max、`eigvalsh`、平行轴合并、FK及雅可比质量/重力估算，关键输入、公式和数值已列正文。未使用网格体积或未知厂家参数补齐。没有运行失败或仿真重试记录。

本轮离线数学结果确认：原8个必要条件失败；10个盒候选及两个合并组满足相应数学条件；总质量保持、合并公式独立复核一致；给定小幅参考和误差角点的有限几何筛查未见非相邻AABB交叠。**这些不等价于导入正确、物理驱动稳定或实体精度PASS。**

只新增本文，并小范围更新REPORT_INDEX和TASK_PROGRESS。原URDF/mesh及既有dirty worktree均保留，未生成派生URDF/USD、未创建运行配置或独立场景文件、未改启动补丁/学习代码/依赖/驱动/共享配置，未启动Isaac/CUDA/渲染/仿真/训练/checkpoint，未执行Git写操作或历史清理。

## 8. 待审决定与下一步

只需审阅三项相互衔接的具体决定：

1. 是否接受本文原质量暂用、visual均匀盒COM/惯量及两固定组完整张量，作为**首版功能调试**参数；后续更可靠质量属性到来时另版替换，不倒写成厂家真值。
2. 是否接受升降q0=0、CPU预合并7body/6DOF、唯一根固定和纯tool/scanner frame的派生结构，以及显式导入/最终读回方式。
3. 是否接受joint_2的5°/6秒序列、6轴PD/调试上限、接触/误差阈值和有限运行预算，作为下一轮实施与授权范围。

没有必须等待厂家资料才能继续写方案的阻断；具体模型可信度、native导入结果及耦合控制性能仍有上述限制。完成审阅后再另行授权资产生成与有限关节验证；通过这一步后才讨论末端控制/单视点采集。原有“到位→开相机→本次实际数据→关相机→下一点”目标不变，本轮未扩展成功条件。

## 辅助证据对应表

下列源文件/已存报告用于复核，本轮未新增附件、脚本、JSON或证据包。仓库内相对链接从本文目录解析；本机安装源码只在当前环境可访问。

| 结论/检查项 | 文件位置 | 关键字段或定位 | 用途 |
|---|---|---|---|
| 原质量、COM、惯量、尺度/关节树 | [原始URDF](../../../assets/rokeaCR12/rokea_cr12_7DOF.urdf) | 本文2.1/2.3行号；joint_0:189、joint_base:196、臂轴:202–248、scanner固定:279 | 可重读原值；不等于参数真实 |
| visual/collision尺寸 | [原始model目录](../../../assets/rokeaCR12/model/) | 2.3具体文件名，OBJ的v/f；例如cr12_link2_visual的Y极小/极大顶点行2017/216、Z极小/极大1112/1532 | scale后min/max和均匀盒复算；不使用体积积分 |
| converter字段与覆盖 | [UrdfConverterCfg](../../../../../../../../source/isaaclab/isaaclab/sim/converters/urdf_converter_cfg.py)、[UrdfConverter](../../../../../../../../source/isaaclab/isaaclab/sim/converters/urdf_converter.py) | 4.2设置表中的符号/行号 | 方案API依据；本轮未实例化 |
| importer版本、native设置边界 | 本机`U/config/extension.toml:13`、`U/scripts/extension.py:156,164`、`U/docs/CHANGELOG.md:12–13,95–98` | 2.3.10；惯量/up-vector setter及历史行为 | 不能用UI/native默认替代读回；没有复制安装包 |
| 实际驱动/读回接口 | [Articulation](../../../../../../../../source/isaaclab/isaaclab/assets/articulation/articulation.py)、[执行器配置](../../../../../../../../source/isaaclab/isaaclab/actuators/actuator_cfg.py) | 4.3/5.3所列符号；本机Tensor API路径见4.3 | 核对位置/速度target与初始化state的区别、参数单位 |
| 接触检测限制 | [ContactSensor](../../../../../../../../source/isaaclab/isaaclab/sensors/contact_sensor/contact_sensor.py) | 单body对多body过滤、force_matrix_w | 支持后续明确接触判据，不代表已有避障 |
| 已接受启动处理 | [Windows实施与验证报告](WINDOWS_RUNTIME_BACKEND_IMPLEMENTATION_AND_VALIDATION_REPORT.md)；[viewer源码](../../../../../../../../scripts/environments/view_scan_assignment.py) | 报告2.2；源码_prepare_cuda_before_app/main guard | 仅复用已接受顺序，不重验或修改 |
| 独立扫描执行边界 | [单机双视点静态评估](../20260928/SINGLE_ROBOT_TWO_VIEWPOINT_IMPLEMENTATION_ASSESSMENT.md) | 运动/相机/生命周期复用边界；旧USD待提供已被后续状态取代 | 避免将本轮基本驱动扩成扫描实现 |
