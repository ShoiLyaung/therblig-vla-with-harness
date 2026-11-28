# A07 向人交接物件

在允许的交接区域把物件交到指定接收者手中。验收终态：接收方已独立承载、机器人已脱手且撤出，身份与目标修订一致。

**当前本体未授权**（近人区域、接收方承载与放手）。当前档案没有已批准的近人交接 profile；视觉触碰不等于接收者已承载。放行条件：独立审批近人 profile、限定区域和接收方证据；核验实际切换与丢失响应。依据：NEEDS_VALIDATION。

[机读用例](../cases/A07.yaml)

## 计划与证据边界

| 节点 | 图修订 | 前驱或互斥入口 | 能力与组合 | 并行组／父项 | 准入条件 | 退出检查 |
| --- | --- | --- | --- | --- | --- | --- |
| profile | 本图 | 本修订入口 | s2.profile · S2_INTERNAL | 无／无 | 物件已安全保持，有独立批准域供解析；本机缺该域应拒绝 | ModeStatus 与实测配置一致 |
| present | 本图 | profile | handover_present · PROVIDER_COMPOSITE | 无／无 | 仅在假设的批准域实际切入后进入 | 接收手与物件相对位置适合交接 |
| wait | 本图 | present | s2.barrier · BARRIER | 无／无 | 呈递就位且给予方仍有有效保持令牌 | 接触、承载与身份都成立 |
| release | 本图 | wait | handover_release · PROVIDER_COMPOSITE | 无／无 | 接收方身份与独立承重证据均满足，允许接管 | 接收方承载且物件未掉落 |

新图触发条件：目标人或工作区改变则撤销旧阶段并另建安全回收图。

能力发现：s2.profile（内部节点）；handover_present（需新建）；s2.barrier（内部节点）；handover_release（需新建）。

阶段授权：profile：当前本体未授权（ModeStatus 与实测配置一致）；present：当前本体未授权（接收手与物件相对位置适合交接）；wait：当前本体未授权（仅等待与维持的逻辑可复核；人体承重路径尚缺）；release：当前本体未授权（接收方承载且物件未掉落）。

## 分轨与占用

| 阶段 | 标签 | S0 与组合 | 交接依据 |
| --- | --- | --- | --- |
| profile | PN、H | 近人工作域（未发布），经 SWITCH_PROFILE 请求切入 · 当前无此白名单 profile | 模式申请期间保留给予方持物令牌 |
| present | TL、PP、H | RETENTION · 需批准近人站姿包络 | 持物令牌在呈递期间有效 |
| wait | UD、H | RETENTION、POSE_HOLD · 保持阶段无 S1 驱动 | 保留握持并核对接收者 |
| release | RL、TE | COMPLIANCE · 需批准安全退出 | 原子接管后才开放，撤离再验证 |

各阶段九轨的 owner、访问和三类掩码见机读 simo。呈递是 PP，等待承接是 UD；给予侧 RL 可与对方 G 重叠，对方手不是本体训练动作轨。

## 验证检查点

声明边界：wait、release。终局成功边界：release。

| 阶段 | SUCCESS | FAILED | UNKNOWN | 恢复 |
| --- | --- | --- | --- | --- |
| wait | 独立观察确认对方承重且身份正确 | 对方已撤手或换人 | 手遮挡，无法区分触碰与承重 | 维持 RETENTION，等待或退回 |
| release | 与本体分离且接收方持续持稳 | 物件跌落或交给非目标人 | 脱离可见而接收方支撑不可见 | 核对接收方，禁止盲目再放 |

## 故障与偏序

| 注入边界 | 预期记录 | 必须先发生 | 禁止结果 |
| --- | --- | --- | --- |
| F07 · wait：接收者触碰后撤手，语言说已拿稳 | 保持令牌有效；Verifier 对转移不予成功；未满足支撑守卫则不派 release | 确认实际接收支撑先于 TAKEOVER；实测脱手先于提交 | 用口头确认替代承载；用模式请求直接放手 |

## 上下文、记忆与监测

Context：记录指定接收者及许可区域，明确谁的语音可改目标；入口假设物件已由 S0 安全维持，令牌与实际手、载荷和工况一致。 Memory：保留交接意图、批准修订、承接证据与实际放手时刻。

| 需求 | 关注点与证据 | D9 映射 | 上限 |
| --- | --- | --- | --- |
| MR-06 | 非指定人员进入交接区 · 接收者身份、手位与工作区边界 | generic/people_workspace@1 | STOP_LATCHED |
| MR-05 | 接收者触碰但未承重 · 机器人载荷变化及独立承载证据 | generic/contact_force_envelope@1 | SOFT_HOLD |
| MR-08 | 临时纠正接收者 · 认证话语与活动修订 | 持续语音观测、认证纠正与基线停止词 | SOFT_HOLD |
| MR-01 | 独立基线核验跌倒、碰撞或危险闯入 · 合格的本体／世界证据与 S0 实际保护回执 | baseline/fall@1（其他危险依部署登记的基线硬规则） | STOP_LATCHED |
| MR-03 | 运动离开本阶段批准走廊 · 参考系一致的姿态、方向与扫掠区 | generic/motion_envelope@1 | SLOW |

## 数据与迁移

仿真：在仿真注入靠近、触碰、承载、撤手四种不同边界。遥操作：取得近人授权后才可收集接收方同步标签。跨本体：跨本体可复用意图与呈递方向，不能复用人体安全距离或手力标定。

缺口：C03、E01、M01。[登记依据](../gaps.md)

## 测试向量

| 故障 | 初态 | 检查的记录 | 偏序 |
| --- | --- | --- | --- |
| F07 | 仅在假设获批的仿真交接域内，给方仍持有物件。；在允许的交接区域把物件交到指定接收者手中 | withdrawn = 适配器 withdrawn 承接观测/接收手 → 已撤离；gate = 适配器 gate 释放守卫/结论 → 维持握持 | withdrawn ≺ gate |

## 逐轨时间线

| 阶段 | E | LA | RA | LH | RH | W | L | S2 | MON |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| profile | 观察·S1/OBSERVE | 稳定·S0/MAINTAINED | 稳定·S0/MAINTAINED | 稳定·S0/MAINTAINED | H·S0/MAINTAINED | 稳定·S0/MAINTAINED | 平衡·S0/MAINTAINED | PN·S2/RECORD | 基线·MON/RECORD |
| present | 观察·S1/OBSERVE | 稳定·S0/MAINTAINED | TL/PP·S1/DRIVE | 稳定·S0/MAINTAINED | H·S0/DEPEND | 稳定·S0/MAINTAINED | 平衡·S0/MAINTAINED | 任务记录·S2/RECORD | 基线·MON/RECORD |
| wait | 观察·S1/OBSERVE | 稳定·S0/MAINTAINED | UD·S0/MAINTAINED | 稳定·S0/MAINTAINED | H·S0/MAINTAINED | 稳定·S0/MAINTAINED | 平衡·S0/MAINTAINED | 任务记录·S2/RECORD | 基线·MON/RECORD |
| release | 观察·S1/OBSERVE | 稳定·S0/MAINTAINED | RL/TE·S1/DRIVE | 稳定·S0/MAINTAINED | RL·S1/TAKEOVER | 稳定·S0/MAINTAINED | 平衡·S0/MAINTAINED | 任务记录·S2/RECORD | 基线·MON/RECORD |

并行活动分支合并已批准绑定。默认稳定为 S0 本地守持；接管确认前屏蔽写轴。

## 契约记录

| 对象 | 字段 | 具体检查 |
| --- | --- | --- |
| ModeRequest | mode、profile_id、expected_protection_epoch | 白名单与实际切换分开 |
| Invocation | bindings、handoff_refs | 守卫成立才可接管 |
| Result | effects_reported、evidence | 脱手和接收承载均须有据 |
