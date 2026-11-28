# A02 纠正红蓝杯目标

纠正原有拾放任务，改将蓝杯送到目标架位。验收终态：蓝杯处于新目标位置，红杯及旧结果均未提交到新修订。

**条件授权**（认证纠正输入后的空手回撤与蓝杯站姿拾放；持物未知载荷恢复分支当前本体未授权）。麦克风有规格声明但本机流未验证，未知载荷不能走普通搬运入口。放行条件：空手分支须认证输入、证实已空手、冲突资源结清且经 S0 重新准入；持物分支还需获准的未知载荷恢复能力。依据：DATASHEET_DECLARED、NEEDS_VALIDATION。

[机读用例](../cases/A02.yaml) · [既有走通](../../walkthroughs.md#w2-错物与用户纠正)

## 计划与证据边界

| 节点 | 图修订 | 前驱或互斥入口 | 能力与组合 | 并行组／父项 | 准入条件 | 退出检查 |
| --- | --- | --- | --- | --- | --- | --- |
| red | rev1 | 本修订入口 | acquire_object · ATOMIC | 无／无 | 旧目标修订有效且预抓准入已通过 | 旧修订证据只供历史 |
| reconcile | rev2 | 本修订入口 | s2.reconcile · S2_INTERNAL | 无／无 | 纠正、中断或游标缺口使旧分支隔离 | 权威意图与所有权均可定位 |
| restore | rev2 | reconcile | safe_putback_unknown_payload · PROVIDER_COMPOSITE | 无／无 | 仅有持物证据且未知载荷在恢复包络内 | 所选恢复调用的公开 Result 证实安全退出、手已空且冲突资源逐项处置已结清 |
| retreat | rev2 | reconcile | move_unloaded · ATOMIC | 无／无 | 仅有空手证据且路径清空 | 无接触且工作区清空 |
| new | rev2 | 择一：restore／retreat | acquire_object · ATOMIC | 无／无 | 验证所选 restore 或 retreat 的公开 Result、空手实测和逐资源处置；蓝杯已绑定且红杯禁选 | 独立核对蓝杯在手 |
| blue_carry | rev2 | new | move_payload · ATOMIC | 无／无 | 蓝杯已取得且保持令牌有效 | 杯离桌并随臂移动 |
| blue_stage | rev2 | blue_carry | stage_for_next_use · ATOMIC | 无／无 | 到达目标架旁且支撑区可核对 | 架面可见且姿态合格 |
| blue_release | rev2 | blue_stage | release_to_support · ATOMIC | 无／无 | 已证实蓝杯支撑面，允许接管 | 观察架面支撑与分离 |

rev1 → rev2：认证纠正建立新图；rev1 不再派发。跨修订只导入原 invocation_id 与执行句柄、取消状态、静稳证据、逐轨处置及现有载荷令牌。

新图触发条件：纠正生成新图修订，新图只消费旧执行的处置证据。

能力发现：acquire_object（已有卡）；s2.reconcile（内部节点）；safe_putback_unknown_payload（需新建）；move_unloaded（目录模板）；move_payload（已有卡）；stage_for_next_use（目录模板）；release_to_support（目录模板）。

阶段授权：red：条件授权（旧修订证据只供历史）；reconcile：条件授权（权威意图与所有权均可定位）；restore：当前本体未授权（一次封装调用，未知载荷包络及恢复能力未获准）；retreat：条件授权（无接触且工作区清空）；new：条件授权（仅所选恢复调用的公开 Result 与逐资源处置核实后才可派发）；blue_carry：条件授权（杯离桌并随臂移动）；blue_stage：条件授权（架面可见且姿态合格）；blue_release：条件授权（观察架面支撑与分离）。

## 分轨与占用

| 阶段 | 标签 | S0 与组合 | 交接依据 |
| --- | --- | --- | --- |
| red | G | COMPLIANCE · 独立单臂准入 | 保留原执行句柄 |
| reconcile | PN、H | RETENTION 或安全保持 · 取消后核对 | 读取原执行而非重建 |
| restore | TL、PP、H、RL | RETENTION 转 COMPLIANCE · 需已批准未知载荷包络 | 支撑确认后原子接管并放手，公开 Result 核对手及臂的最终处置 |
| retreat | TE | BALANCE · 互斥恢复分支 | 空手证据先于撤离 |
| new | ST、G | hand.acquire_slow · 仅已选恢复分支完成 | 红杯进入禁选集合 |
| blue_carry | TL、H | RETENTION、BALANCE · carry-with-support | 登记保持令牌 |
| blue_stage | PP、H | RETENTION · 站姿单臂准入 | 保留 RH 依赖 |
| blue_release | RL | COMPLIANCE · 带撤出变体独立核准 | 接管并消费令牌 |

各阶段九轨的 owner、访问和三类掩码见机读 simo。ST 由 S2 重绑实体，抬起未知载荷放回是 TL/PP/RL，不是继续旧 G。

## 验证检查点

声明边界：reconcile、new、blue_release。终局成功边界：blue_release。

| 阶段 | SUCCESS | FAILED | UNKNOWN | 恢复 |
| --- | --- | --- | --- | --- |
| reconcile | 权威意图、停稳与处置一致 | 权威对账记录证明旧修订仍可派发，与应生效的修订围栏矛盾 | 缺口且未能核实当前目标 | 保留隔离并经宿主确认 |
| new | 新修订的新鲜身份与握稳证据确认被控制的是绑定蓝杯 | 明确抓到禁选红杯 | 手中杯身份不明 | 补证并用新修订继续安放 |
| blue_release | 新修订证实蓝杯在指定架位，支撑转移并脱手 | 红杯被放置或蓝杯明确掉落 | 杯色或承载面不可见 | 保持原提交边界并补证 |

## 故障与偏序

| 注入边界 | 预期记录 | 必须先发生 | 禁止结果 |
| --- | --- | --- | --- |
| F02a · reconcile：持久流的缺口跨过保留边界，纠正观测缺失 | S2 冻结旧 outbox；确认权威意图并补处理可回放段后记录 resync_checkpoint | 确认目标、完成身体对账先于解封 | 由已停稳推断新目标 |
| F02b · reconcile：取消已受理后本地停止故障，S0 权威账本证实右臂和右手尚未结清 | 仅待确认时可读 STOPPING；故障终态为 FAILED 且 cancel.state=ACCEPTED；控制摘要 stable=false，未结清资源保持 QUARANTINED；匹配原故障与资源的恢复证据先于重用 | 隔离可早于终态；核验恢复证据先于重新使用右侧资源 | 未获稳定证据便把 STOPPING 强制改为 FAILED；根据 FAILED 释放未结清资源 |
| F02c · reconcile：撤销红杯简报后 Monitor 重启，先送达启动误差界以外的旧刷新 | 旧简报在启动围栏丢弃；独立基线照常运行；仍存活蓝杯阶段的合格新鲜刷新按首发重装 | 认证并比较本地映射 sent_at 先于安装；END／REVOKE 按绑定与序号处理 | 用 issued_at 替代启动围栏的 sent_at；把前次启动回收水位带入新实例 |

## 上下文、记忆与监测

Context：按目标修订隔离证据；空手与持物恢复分支互斥；旧图红杯调用仅提供对账证据；新图择一消费 restore 或 retreat 的公开 Result 和资源处置，未选分支不参与汇合。 Memory：冻结取消幂等键，保留旧结果及重同步检查点。

| 需求 | 关注点与证据 | D9 映射 | 上限 |
| --- | --- | --- | --- |
| MR-08 | 认证纠正与普通追加请求分流 · 话语观测、身份、旧修订 | 持续语音观测、认证纠正与基线停止词 | SOFT_HOLD |
| MR-02 | 旧目标成为禁选对象 · 新锚点与旧目标历史 | generic/target_identity@1 | SOFT_HOLD |
| MR-01 | 独立基线核验跌倒、碰撞或危险闯入 · 合格的本体／世界证据与 S0 实际保护回执 | baseline/fall@1（其他危险依部署登记的基线硬规则） | STOP_LATCHED |
| MR-05 | 持物滑移、载荷转移或非预期接触 · 绑定手的原始计数、指位和物手相对运动 | generic/contact_force_envelope@1 | SOFT_HOLD |

## 数据与迁移

仿真：注入丢失观测和迟到结果。遥操作：采集同布局交换杯色的配对操作。跨本体：迁移接近轨；语音认证与实体身份重新标注。

缺口：E01、E03、M01。[登记依据](../gaps.md)

## 测试向量

| 故障 | 初态 | 检查的记录 | 偏序 |
| --- | --- | --- | --- |
| F02a | 旧修订仍有待派项；权威输入源保有认证纠正，当前事件段已过保留期。；把红杯任务修订为拾取蓝杯 | confirmed = 适配器 confirmed 用户输入/意图状态 → 已确认；resume = 适配器 resume 检查点/恢复状态 → 允许新修订派发 | confirmed ≺ resume |
| F02b | 原执行已有活动授权，S1 已受理取消；在停止过程中注入控制器故障并取得 S0 的逐资源处置。；观测窗分两段：先验证故障后隔离持续；后续有合格恢复记录且 S0 重新准入时才检查重用。 | pending = 协议 pending Execution/state → STOPPING（若采到中间态）；end = 协议 fault Execution/state → FAILED；accepted = 协议 fault Execution/cancel/state → ACCEPTED；stable = 协议 fault Execution/result/evidence/controller_summary/stable → false；hand = 协议 fault Execution/result/resource_dispositions[resource_id=RH]/resource_id → RH；unsettled = 协议 fault Execution/result/resource_dispositions[resource_id=RH]/disposition → QUARANTINED；fence = 适配器 fence 资源对账/处置 → 仍隔离；cleared = 适配器 cleared 恢复核验/依据 → 匹配原故障和资源的 S0 恢复凭据；reuse = 适配器 reuse 再准入/资源 → RH；authoritative = 适配器 s0_stop 本地停止账本/RH处置 → 未结清，隔离 | cleared ≺ reuse |
| F02c | 同一次启动中，较晚签发阶段的回收水位曾挡住未见过的早期蓝杯简报；蓝杯阶段仍有效。 | drop = 适配器 drop 本地离线审计/旧快照 → 启动围栏丢弃；fresh = 适配器 fresh 本地离线审计/蓝杯阶段 → 新实例按首发安装 | drop ≺ fresh |

## 逐轨时间线

| 阶段 | E | LA | RA | LH | RH | W | L | S2 | MON |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| red | 观察·S1/OBSERVE | 稳定·S0/MAINTAINED | G·S1/DRIVE | 稳定·S0/MAINTAINED | G·S1/DRIVE | 稳定·S0/MAINTAINED | 平衡·S0/MAINTAINED | 任务记录·S2/RECORD | 基线·MON/RECORD |
| reconcile | 观察·S1/OBSERVE | 稳定·S0/MAINTAINED | 稳定·S0/MAINTAINED | 稳定·S0/MAINTAINED | H（持物分支）·S0/MAINTAINED | 稳定·S0/MAINTAINED | 平衡·S0/MAINTAINED | PN·S2/RECORD | 基线·MON/RECORD |
| restore | 观察·S1/OBSERVE | 稳定·S0/MAINTAINED | TL/PP·S1/DRIVE | 稳定·S0/MAINTAINED | H·S0/DEPEND | 稳定·S0/MAINTAINED | 平衡·S0/MAINTAINED | 任务记录·S2/RECORD | 基线·MON/RECORD |
| restore 内部回放：restore_release | 观察·S1/OBSERVE | 稳定·S0/MAINTAINED | RL·S1/DRIVE | 稳定·S0/MAINTAINED | RL·S1/TAKEOVER | 稳定·S0/MAINTAINED | 平衡·S0/MAINTAINED | 任务记录·S2/RECORD | 基线·MON/RECORD |
| retreat | 观察·S1/OBSERVE | 稳定·S0/MAINTAINED | TE·S1/DRIVE | 稳定·S0/MAINTAINED | 稳定·S0/MAINTAINED | 稳定·S0/MAINTAINED | 平衡·S0/MAINTAINED | 任务记录·S2/RECORD | 基线·MON/RECORD |
| new | 观察·S1/OBSERVE | 稳定·S0/MAINTAINED | G·S1/DRIVE | 稳定·S0/MAINTAINED | G·S1/DRIVE | 稳定·S0/MAINTAINED | 平衡·S0/MAINTAINED | ST·S2/RECORD | 基线·MON/RECORD |
| blue_carry | 观察·S1/OBSERVE | 稳定·S0/MAINTAINED | TL·S1/DRIVE | 稳定·S0/MAINTAINED | H·S0/DEPEND | TL·S1/DRIVE | 平衡·S0/MAINTAINED | 任务记录·S2/RECORD | 基线·MON/RECORD |
| blue_stage | 观察·S1/OBSERVE | 稳定·S0/MAINTAINED | PP·S1/DRIVE | 稳定·S0/MAINTAINED | H·S0/DEPEND | 稳定·S0/MAINTAINED | 平衡·S0/MAINTAINED | 任务记录·S2/RECORD | 基线·MON/RECORD |
| blue_release | 观察·S1/OBSERVE | 稳定·S0/MAINTAINED | RL·S1/DRIVE | 稳定·S0/MAINTAINED | RL·S1/TAKEOVER | 稳定·S0/MAINTAINED | 平衡·S0/MAINTAINED | 任务记录·S2/RECORD | 基线·MON/RECORD |

并行活动分支合并已批准绑定。默认稳定为 S0 本地守持；接管确认前屏蔽写轴。

## 契约记录

| 对象 | 字段 | 具体检查 |
| --- | --- | --- |
| Event | interrupt、evidence_refs | 认证纠正引用先前话语 |
| Execution | cancel、state | 取消受理与实际静稳分别检查 |
| Verification | goal_revision、supersedes | 旧修订不得提交新进度 |
