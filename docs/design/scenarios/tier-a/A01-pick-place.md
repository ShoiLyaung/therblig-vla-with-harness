# A01 单臂拾放红杯

将场景内绑定的红杯移到指定架位。验收终态：最新修订下同一杯由架面支撑，手已脱离且回撤未扰动杯位。

**条件授权**（站姿单臂与保持交接）。轴向计数不能识别杯色或支撑面。放行条件：站姿准入、低速闭合、同手有效空载基线及独立视觉支撑证据。依据：DATASHEET_DECLARED、NEEDS_VALIDATION。

[机读用例](../cases/A01.yaml) · [既有走通](../../walkthroughs.md#w1-单臂拾放红杯)

## 计划与证据边界

| 节点 | 图修订 | 前驱或互斥入口 | 能力与组合 | 并行组／父项 | 准入条件 | 退出检查 |
| --- | --- | --- | --- | --- | --- | --- |
| find | 本图 | 本修订入口 | locate_candidates · ATOMIC | 无／无 | 场景与目标描述已冻结 | 杯身份和观测源一致 |
| approach | 本图 | find | move_unloaded · ATOMIC | 无／无 | 目标已定位、禁选物新鲜且空手路径获准 | 到位且杯未动 |
| acquire | 本图 | approach | acquire_object · ATOMIC | 无／无 | 已到预抓位且身份一致、hand.acquire_slow 可用 | 身份与相对运动同证 |
| carry | 本图 | acquire | move_payload · ATOMIC | 无／无 | 右手保持令牌有效且搬运组合已核准 | 杯离桌并随臂移动 |
| stage | 本图 | carry | stage_for_next_use · ATOMIC | 无／无 | 载荷到架旁且架面可复核 | 架面可见且姿态合格 |
| release | 本图 | stage | release_to_support · ATOMIC | 无／无 | 已证实稳定支撑，依赖方已满足接管条件 | 观察架面支撑与分离 |
| withdraw | 本图 | release | move_unloaded · ATOMIC | 无／无 | 有空手与清空路径证据 | 架位稳定且手已清空 |

新图触发条件：旧调用仍活动则等待；确认已静稳后才生成新尝试。

能力发现：locate_candidates（目录模板）；move_unloaded（目录模板）；acquire_object（已有卡）；move_payload（已有卡）；stage_for_next_use（目录模板）；release_to_support（目录模板）。

阶段授权：find：条件授权（杯身份和观测源一致）；approach：条件授权（到位且杯未动）；acquire：条件授权（身份与相对运动同证）；carry：条件授权（杯离桌并随臂移动）；stage：条件授权（架面可见且姿态合格）；release：条件授权（观察架面支撑与分离）；withdraw：条件授权（架位稳定且手已清空）。

部署不变量：S2 和 Monitor 固定同一登记修订，按 evaluator_ref 的 revision 与 digest 核验评估器；S2 不等待 Monitor 布防。

## 分轨与占用

| 阶段 | 标签 | S0 与组合 | 交接依据 |
| --- | --- | --- | --- |
| find | SH、FD、ST | BALANCE · 纯观察 | 冻结 scene_id 与排除列表 |
| approach | TE | BALANCE · 独立单臂准入 | 空手到位后交还 RA |
| acquire | G | hand.acquire_slow · 独立单臂准入 | 握稳后交给 hand.retain |
| carry | TL、H | RETENTION、BALANCE · carry-with-support | 登记保持令牌 |
| stage | PP、H | RETENTION · 站姿单臂准入 | 保留 RH 依赖 |
| release | RL | COMPLIANCE · 带撤出变体独立核准 | 接管并消费令牌 |
| withdraw | TE | BALANCE · 独立单臂准入 | 核对空手再撤 |

各阶段九轨的 owner、访问和三类掩码见机读 simo。取得控制的 G 以 acquired 点结束；RH 在 RA 的 TL 区间保持 H，不参加手指动作损失。

## 验证检查点

声明边界：acquire、withdraw。终局成功边界：withdraw。

| 阶段 | SUCCESS | FAILED | UNKNOWN | 恢复 |
| --- | --- | --- | --- | --- |
| acquire | 红杯身份与握稳证据同属一次调用 | 观察到握住邻杯 | 仅有轴向变化而目标被挡 | 维持负载并换视角 |
| withdraw | 观察到红杯在架且回撤后稳定 | 确认红杯仍在桌上或已跌落 | 架面遮挡，无法看清支撑关系 | 补证后追加 Verification |

## 故障与偏序

| 注入边界 | 预期记录 | 必须先发生 | 禁止结果 |
| --- | --- | --- | --- |
| F01 · acquire：创建回包丢失 | S2 记调用视图 UNKNOWN；D8 原键回查 ADMITTED 后读取 Execution 和 core_evidence | 冻结调用先于创建；确认旧执行与资源处置先于冲突派发 | 再次物理抓取；以超时断言未受理 |
| F01b · acquire：力子句从未布防，原宽限在空窗中届满；保留期内续租时力输入已恢复 | 同一保护请求和 Event 引用相同事件、保护 ID；CANCEL_AFFECTED 指明 contact_force_envelope 的 GRACE_EXPIRED；S2 持久预算已尽，同条件申请拒绝；随后独立的新证据证明工况改变，仅在对账后重新评估新尝试；S0 独立回执的 event_ref 和 protection_id 与该中断相符，送达先后均可 | 先请求本地收紧再发布 Event；同条件预算用尽先于拒绝；新证据先于按变化条件重新规划 | 以续租重置宽限；预算用尽仍原样重派；把重复的旧证据当作新证据 |

## 上下文、记忆与监测

Context：缓存目标锚点、架面与禁选实例；视角变更时重验新鲜度。 Memory：保留原 invocation_id、D8 查询记录与令牌消费历史。

| 需求 | 关注点与证据 | D9 映射 | 上限 |
| --- | --- | --- | --- |
| MR-02 | 错杯趋近 · 实体锚点、禁选物与接近轨迹 | generic/target_identity@1 | SLOW |
| MR-05 | 提起后滑移 · 同手计数趋势和物手相对位移 | generic/contact_force_envelope@1 | SOFT_HOLD |
| MR-01 | 独立基线核验跌倒、碰撞或危险闯入 · 合格的本体／世界证据与 S0 实际保护回执 | baseline/fall@1（其他危险依部署登记的基线硬规则） | STOP_LATCHED |

## 数据与迁移

仿真：对照创建回包正常与丢失轨迹。遥操作：配对记录原生手闭合与离桌时刻。跨本体：迁移空载臂轨，屏蔽不匹配手指轴。

缺口：E01、E02、M01。[登记依据](../gaps.md)

## 测试向量

| 故障 | 初态 | 检查的记录 | 偏序 |
| --- | --- | --- | --- |
| F01 | 调用已发且供应方已受理，查询原执行时仍在运行。；将场景内绑定的红杯移到指定架位；偏序只比较 S2 收到的两次读取响应。 | lookup_read = 协议 lookup_read InvocationLookup/status → ADMITTED；execution_read = 协议 execution_read Execution/state → RUNNING | lookup_read ≺ execution_read |
| F01b | 同次启动、原阶段已占用；重试计数跨 attempt 持久保存，同条件预算已耗尽。 | hold = 适配器 req 本地保护请求/level → SOFT_HOLD；cause = 适配器 req 本地保护请求/event_ref → event.required-clause-unarmed-grace-expired；requested = 适配器 req 本地保护请求/protection_id → protect.required-clause-unarmed-grace-expired；event = 协议 irq Event/event_id → event.required-clause-unarmed-grace-expired；link = 协议 irq Event/protection_ref → protect.required-clause-unarmed-grace-expired；disp = 协议 irq Event/interrupt/disposition → CANCEL_AFFECTED；expiry = 协议 irq Event/detection/clause_failures/0/failure → GRACE_EXPIRED；slot = 协议 irq Event/detection/clause_failures/0/clause_id → contact_force_envelope；spent = 适配器 spent 重试预算/同条件 → 已耗尽；deny = 适配器 deny 派发记录/同条件新调用 → 未派发；changed = 适配器 changed 证据复测/工况 → 变化已核实；replan = 适配器 replan 新尝试/入口 → 变化条件已对账；receipt_event = 协议 applied ProtectionReceipt/event_ref → event.required-clause-unarmed-grace-expired；receipt_id = 协议 applied ProtectionReceipt/protection_id → protect.required-clause-unarmed-grace-expired | hold ≺ event；spent ≺ deny；changed ≺ replan |

## 契约记录

| 对象 | 字段 | 具体检查 |
| --- | --- | --- |
| Invocation | invocation_id、start_deadline | 原身份和原截止执行 D8 对账 |
| Execution | invocation_id、leases | 按原调用归集授权 |
| Result | resource_dispositions、quiescence | 保持与释放各自可核对 |
