# A06 抓取易碎食材

在闭合过冲受限的工况下拾取鸡蛋、草莓或豆腐。验收终态：身份正确、脱离原支撑、保持稳定，并以食材专用标准证实完整。

**当前本体未授权**（材料专用窄力窗与损伤验证）。轴向力随接触位置变化；无名指、小指和拇指旋转未标定，没有本机逐手通道绝对力批准；right.hand.tactile.available=false，无指面触觉阵列，轴向计数不能定位接触。放行条件：选择明确接受相对计数的材料变体并验证完整性，或取得要求绝对力的逐手逐通道批准。依据：DATASHEET_DECLARED、THIRD_PARTY_MEASURED、UNCALIBRATED、NEEDS_VALIDATION。

[机读用例](../cases/A06.yaml)

## 计划与证据边界

| 节点 | 图修订 | 前驱或互斥入口 | 能力与组合 | 并行组／父项 | 准入条件 | 退出检查 |
| --- | --- | --- | --- | --- | --- | --- |
| bind | 本图 | 本修订入口 | s2.select · S2_INTERNAL | 无／无 | 候选对象与材料验收标准可核对 | 实例和标准可区分 |
| grasp | 本图 | bind | fragile_acquire · PROVIDER_COMPOSITE | 无／无 | 实际手、通道、材料工况与所需单位均获批准 | 入口证据覆盖实际承载通道 |
| lift | 本图 | grasp | move_payload · ATOMIC | 无／无 | 握稳且保持令牌有效，载荷包络允许提升 | 物件随手而非留在台面 |
| inspect | 本图 | lift | measure_condition · ATOMIC | 无／无 | 物件已提升并稳定保持，材料标准可用 | 损伤标准与可见证据对应 |

新图触发条件：证据工况改变后重新选择变体；不自动放宽力窗。

能力发现：s2.select（内部节点）；fragile_acquire（需新建）；move_payload（已有卡）；measure_condition（目录模板）。

阶段授权：bind：条件授权（只绑定候选身份与材料标准）；grasp：当前本体未授权（入口证据覆盖实际承载通道）；lift：条件授权（仅假设已取得合格材料保持令牌的后继；不放行本例受阻的获取）；inspect：当前本体未授权（损伤标准与可见证据对应）。

## 分轨与占用

| 阶段 | 标签 | S0 与组合 | 交接依据 |
| --- | --- | --- | --- |
| bind | ST | BALANCE · 观察 | 绑定材料批次与标准 |
| grasp | G | hand.acquire_slow · 材料变体未批准 | 不能在无验证时转入持续保持 |
| lift | TL、H | RETENTION · carry-with-support 仍需材料授权 | 沿用同一材料和接触工况 |
| inspect | I、H | RETENTION · 无新增驱动 | 未知时先安全放回 |

各阶段九轨的 owner、访问和三类掩码见机读 simo。G 结束于取得控制；I 依据材料标准看裂纹、压痕或破碎，不能从 G 的终态代推。

## 验证检查点

声明边界：grasp、inspect。终局成功边界：inspect。

| 阶段 | SUCCESS | FAILED | UNKNOWN | 恢复 |
| --- | --- | --- | --- | --- |
| grasp | 允许相对计数的已验证变体取得控制 | 确认闭合压碎目标 | 饱和或不可辨别滑移 | 维持安全状态并补证 |
| inspect | 按所选材料标准完整且已安全提升 | 明确蛋壳裂纹、果肉压损或豆腐破碎 | 背面不可见且无合格替代证据 | 换视角或按合格能力放回 |

## 故障与偏序

| 注入边界 | 预期记录 | 必须先发生 | 禁止结果 |
| --- | --- | --- | --- |
| F06a · grasp：卡要求绝对力而实际承载通道未标定 | Resolver 阻塞；无创建调用；保留所缺批准范围 | 校验手、通道、标定修订与工况先于任何派发 | 用第三方拟合或电流直接代替 N |
| F06b · inspect：食材背面遮挡且载荷信号已饱和 | Verifier 对完整性记 UNKNOWN；记录无效通道掩码 | 安全支撑先于换视角 | 未见裂纹即判完整 |

## 上下文、记忆与监测

Context：缓存食材类型、实际手、承载通道、接触部位依据与校零状态。 Memory：保存原始计数及逐通道有效位；跨食材批次不复用批准。

| 需求 | 关注点与证据 | D9 映射 | 上限 |
| --- | --- | --- | --- |
| MR-05 | 闭合过冲及保持下限 · 指位、轴向计数、视觉形变及批准记录 | generic/contact_force_envelope@1 | SOFT_HOLD |
| MR-02 | 相邻外观相似食材 · 可区分的实例锚点 | generic/target_identity@1 | SLOW |
| MR-01 | 独立基线核验跌倒、碰撞或危险闯入 · 合格的本体／世界证据与 S0 实际保护回执 | baseline/fall@1（其他危险依部署登记的基线硬规则） | STOP_LATCHED |
| MR-03 | 运动离开本阶段批准走廊 · 参考系一致的姿态、方向与扫掠区 | generic/motion_envelope@1 | SLOW |

## 数据与迁移

仿真：分开模拟压碎、滑落与信号饱和，材料模型只作标签候选。遥操作：原生示教补充易损材质损伤标注。跨本体：臂段可迁移；刚体夹爪数据不能充当柔软食材的接触真值。

缺口：M03、C01、E01、M01。[登记依据](../gaps.md)

## 测试向量

| 故障 | 初态 | 检查的记录 | 偏序 |
| --- | --- | --- | --- |
| F06a | 选择必须核验绝对力的材料变体，受力指无适用转换及批准。；在闭合过冲受限的工况下拾取鸡蛋、草莓或豆腐 | metric = 适配器 metric 证据批准/适用性 → 无匹配通道批准；gate = 适配器 gate 解析记录/状态 → 阻塞 | metric ≺ gate |
| F06b | 相对计数变体已获工况验证，提升后需重新检验完整性。；在闭合过冲受限的工况下拾取鸡蛋、草莓或豆腐 | mask = 适配器 mask 观测质量/材料可见性 → 背面遮挡；check = 协议 check Verification/verdict → UNKNOWN | mask ≺ check |

## 逐轨时间线

| 阶段 | E | LA | RA | LH | RH | W | L | S2 | MON |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bind | 观察·S1/OBSERVE | 稳定·S0/MAINTAINED | 稳定·S0/MAINTAINED | 稳定·S0/MAINTAINED | 稳定·S0/MAINTAINED | 稳定·S0/MAINTAINED | 平衡·S0/MAINTAINED | ST·S2/RECORD | 基线·MON/RECORD |
| grasp | 观察·S1/OBSERVE | 稳定·S0/MAINTAINED | G·S1/DRIVE | 稳定·S0/MAINTAINED | G·S1/DRIVE | 稳定·S0/MAINTAINED | 平衡·S0/MAINTAINED | 任务记录·S2/RECORD | 基线·MON/RECORD |
| lift | 观察·S1/OBSERVE | 稳定·S0/MAINTAINED | TL·S1/DRIVE | 稳定·S0/MAINTAINED | H·S0/DEPEND | TL·S1/DRIVE | 平衡·S0/MAINTAINED | 任务记录·S2/RECORD | 基线·MON/RECORD |
| inspect | 观察·S1/OBSERVE | 稳定·S0/MAINTAINED | 稳定·S0/MAINTAINED | 稳定·S0/MAINTAINED | H·S0/MAINTAINED | 稳定·S0/MAINTAINED | 平衡·S0/MAINTAINED | I·S2/RECORD | 基线·MON/RECORD |

并行活动分支合并已批准绑定。默认稳定为 S0 本地守持；接管确认前屏蔽写轴。

## 契约记录

| 对象 | 字段 | 具体检查 |
| --- | --- | --- |
| Capability | semantics、limits | 通道用途和低速配置另验 |
| BodyProfile | sensors、s0_profiles | 未标定通道不能换算绝对力 |
| Verification | predicates、evaluated_at | 按食材标准检查完整性 |
