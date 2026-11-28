# A08 折叠毛巾或衣物

将布料折至指定轮廓并平放。验收终态：目标角点配对、折边关系及放置区域均符合标准 Q，双手退出后形态仍保持。

**当前本体未授权**（可变形物的双手协同与形态检验）。目录可描述操作，但未发布获准的双手折叠变体及遮挡下验证标准。放行条件：建立材质与关键点标准，验证双臂组合、接触与松手后的形态证据。依据：NEEDS_VALIDATION。

[机读用例](../cases/A08.yaml)

## 计划与证据边界

| 节点 | 图修订 | 前驱或互斥入口 | 能力与组合 | 并行组／父项 | 准入条件 | 退出检查 |
| --- | --- | --- | --- | --- | --- | --- |
| find | 本图 | 本修订入口 | locate_candidates · ATOMIC | 无／无 | 折叠目标、布料实例与地标标准已绑定 | 可见角点区分且观测新鲜 |
| left | 本图 | find | acquire_object · ATOMIC | 取两角／无 | 左角可见且双臂取角组合批准 | 左角随手移动 |
| right | 本图 | find | acquire_object · ATOMIC | 取两角／无 | 右角可见且双臂取角组合批准 | 右角随手移动 |
| fold | 本图 | left、right | fold_fabric · PROVIDER_COMPOSITE | 无／无 | 两角已证实受控、协调变体与避碰条件获准 | 成对地标与折边标准同时成立 |
| lay | 本图 | fold | place_fabric · PROVIDER_COMPOSITE | 无／无 | 折边验证通过且支撑面可见 | 双手退出且形态仍稳定 |
| inspect | 本图 | lay | measure_condition · ATOMIC | 无／无 | 双手已安全退出，折后观测与标准匹配 | 关键点配对与区域合格 |

新图触发条件：布角失配或松手后反弹则从新观测展开新修订。

能力发现：locate_candidates（目录模板）；acquire_object（已有卡）；fold_fabric（需新建）；place_fabric（需新建）；measure_condition（目录模板）。

阶段授权：find：条件授权（仅可观察可辨布角；验收所需地标配对与复核路径待验证）；left：当前本体未授权（左角随手移动）；right：当前本体未授权（右角随手移动）；fold：当前本体未授权（成对地标与折边标准同时成立）；lay：当前本体未授权（双手退出且形态仍稳定）；inspect：条件授权（仅检查输入质量与 UNKNOWN；遮挡下的正向形态验收仍受阻）。

## 分轨与占用

| 阶段 | 标签 | S0 与组合 | 交接依据 |
| --- | --- | --- | --- |
| find | SH、FD、ST | BALANCE · 纯观察 | 记录布料实例及地标对应 |
| left | G | COMPLIANCE · 需批准柔性双臂工况 | 左手转保持 |
| right | G | COMPLIANCE · 需批准柔性双臂工况 | 右手转保持 |
| fold | TL、P、H | RETENTION、COMPLIANCE · 需双臂协调变体 | 保留两侧保持至稳定支撑 |
| lay | PP、RL | COMPLIANCE · 双手退出须独立批准 | 确认台面支撑后同步协调放手 |
| inspect | I | BALANCE · 纯观察 | 保留缺失地标标记 |

各阶段九轨的 owner、访问和三类掩码见机读 simo。携带布角移位是 TL，按当前折边地标和标准 Q 对位是 P，手的保持记 H；为后续收纳摆放才是 PP。

## 验证检查点

声明边界：fold、inspect。终局成功边界：inspect。

| 阶段 | SUCCESS | FAILED | UNKNOWN | 恢复 |
| --- | --- | --- | --- | --- |
| fold | 目标角配对与折边拓扑可见且合格 | 明确配错角或折向相反 | 外轮廓正确但隐藏角不可见 | 局部取证或重抓，保留先前未知 |
| inspect | 松手后地标与轮廓仍符合 Q | 松手后明显展开或偏出区域 | 遮挡或材质纹理不足以区分布层 | 换视角或请求人工核验 |

## 故障与偏序

| 注入边界 | 预期记录 | 必须先发生 | 禁止结果 |
| --- | --- | --- | --- |
| F08 · fold：一角滑出视野，二维外轮廓似已对齐 | S1 记录可见区和保持处置；Verifier 对隐藏角配对记 UNKNOWN | 重观测布角与支撑先于提交；必要时换图重抓 | 从矩形轮廓断言夹层平整 |

## 上下文、记忆与监测

Context：记录布角持久身份、正反面、折线和目标区域；折叠后旧位置失效。 Memory：存档折前后观测、可见区和地标对应，区分观测与仿真真值。

| 需求 | 关注点与证据 | D9 映射 | 上限 |
| --- | --- | --- | --- |
| MR-02 | 布角错配或同色重叠 · 轮廓与可复核的布角观测 | generic/target_identity@1 | SLOW |
| MR-05 | 一侧布边脱手 · 手物相对运动及逐手载荷 | generic/contact_force_envelope@1 | SOFT_HOLD |
| MR-01 | 独立基线核验跌倒、碰撞或危险闯入 · 合格的本体／世界证据与 S0 实际保护回执 | baseline/fall@1（其他危险依部署登记的基线硬规则） | STOP_LATCHED |

## 数据与迁移

仿真：用布网格真值评分，给策略的只有可观测输入。遥操作：采集真实褶皱、材质差异及遮挡下的 UNKNOWN 标注。跨本体：迁移地标关系和粗略臂段，不迁移仿真接触或另一种布料的张力阈值。

缺口：M04、E05、M01。[登记依据](../gaps.md)

## 测试向量

| 故障 | 初态 | 检查的记录 | 偏序 |
| --- | --- | --- | --- |
| F08 | 布角已部分折合；标准 Q 要求核实成对角点。；将布料折至指定轮廓并平放 | corner = 适配器 corner 地标观测/隐藏角 → 不可见；check = 协议 check Verification/verdict → UNKNOWN | corner ≺ check |

## 逐轨时间线

| 阶段 | E | LA | RA | LH | RH | W | L | S2 | MON |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| find | SH/FD@t·S1/OBSERVE | 稳定·S0/MAINTAINED | 稳定·S0/MAINTAINED | 稳定·S0/MAINTAINED | 稳定·S0/MAINTAINED | 稳定·S0/MAINTAINED | 平衡·S0/MAINTAINED | ST·S2/RECORD | 基线·MON/RECORD |
| left | 观察·S1/OBSERVE | G·S1/DRIVE | 稳定·S0/MAINTAINED | G·S1/DRIVE | 稳定·S0/MAINTAINED | 稳定·S0/MAINTAINED | 平衡·S0/MAINTAINED | 任务记录·S2/RECORD | 基线·MON/RECORD |
| right | 观察·S1/OBSERVE | 稳定·S0/MAINTAINED | G·S1/DRIVE | 稳定·S0/MAINTAINED | G·S1/DRIVE | 稳定·S0/MAINTAINED | 平衡·S0/MAINTAINED | 任务记录·S2/RECORD | 基线·MON/RECORD |
| fold | 观察·S1/OBSERVE | TL/P·S1/DRIVE | TL/P·S1/DRIVE | H·S0/DEPEND | H·S0/DEPEND | 稳定·S0/MAINTAINED | 平衡·S0/MAINTAINED | 任务记录·S2/RECORD | 基线·MON/RECORD |
| lay | 观察·S1/OBSERVE | PP·S1/DRIVE | PP·S1/DRIVE | RL·S1/TAKEOVER | RL·S1/TAKEOVER | 稳定·S0/MAINTAINED | 平衡·S0/MAINTAINED | 任务记录·S2/RECORD | 基线·MON/RECORD |
| inspect | 观察·S1/OBSERVE | 稳定·S0/MAINTAINED | 稳定·S0/MAINTAINED | 稳定·S0/MAINTAINED | 稳定·S0/MAINTAINED | 稳定·S0/MAINTAINED | 平衡·S0/MAINTAINED | I·S2/RECORD | 基线·MON/RECORD |

并行活动分支合并已批准绑定。默认稳定为 S0 本地守持；接管确认前屏蔽写轴。

## 契约记录

| 对象 | 字段 | 具体检查 |
| --- | --- | --- |
| Invocation | targets、observation_refs | 地标可见性绑定观测 |
| Result | outputs、evidence | 保留可见轮廓与遮挡区 |
| Verification | verdict、supersedes | 补证后新增结论 |
