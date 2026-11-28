# A04 行走、停稳与抓取

到达物件附近并在稳定站姿下抓取。验收终态：到达、稳定支撑、目标在手和安全保持均有实测证据。

**当前本体未授权**（实机步态支撑证据及腿臂动态组合；静稳站姿获取单独审查）。行走仅仿真已覆盖；实机惯性与足接触估计均未获准，步态与上身并发也无批准组合。放行条件：验证本机支撑路径；并行另需获准的动态耦合守卫。依据：DATASHEET_DECLARED、NEEDS_VALIDATION。

[机读用例](../cases/A04.yaml) · [既有走通](../../walkthroughs.md#w5-行走和上肢抓取)

## 计划与证据边界

| 节点 | 图修订 | 前驱或互斥入口 | 能力与组合 | 并行组／父项 | 准入条件 | 退出检查 |
| --- | --- | --- | --- | --- | --- | --- |
| walk | 本图 | 本修订入口 | locomote · ATOMIC | 无／无 | 仿真支撑输入合格且仿真运动包络已绑定；实机阻塞 | 有基座定位与支撑证据 |
| stand | 本图 | walk | s2.barrier · BARRIER | 无／无 | 步态调用已终止，等待核验腿轨实际处置 | 实测稳定且旧 grant 失效 |
| grasp | 本图 | stand | acquire_object · ATOMIC | 无／无 | 站稳、L 已释放且右侧站姿抓取获准 | 对象身份与物手关系正确 |

新图触发条件：跌倒或支撑丢失先对账；重新规划只允许合格的串行分支。

能力发现：locomote（目录模板）；s2.barrier（内部节点）；acquire_object（已有卡）。

阶段授权：walk：当前本体未授权（有基座定位与支撑证据）；stand：条件授权（独立站姿可核验；从实机步态退出的正向分支缺获准的前驱）；grasp：条件授权（从已验证静稳站姿开始，只核准独立上肢获取）。

## 分轨与占用

| 阶段 | 标签 | S0 与组合 | 交接依据 |
| --- | --- | --- | --- |
| walk | x.locomote | support.walk · 无实机组合；仿真域单独受理；实机拒绝；envelope_policy_ref=simulation_only.walk.corridor@1 | 步态结束取得 L 的 RELEASED |
| stand | PN | support.balance · 串行屏障 | 恢复运动须新准入 |
| grasp | G | hand.acquire_slow · 站姿单臂准入 | 握稳转 RETENTION |

各阶段九轨的 owner、访问和三类掩码见机读 simo。LO 只标基座位移；停止后 L 的平衡不再标 LO，上身 G/TL 单独分轨。

## 验证检查点

声明边界：stand、grasp。终局成功边界：grasp。

| 阶段 | SUCCESS | FAILED | UNKNOWN | 恢复 |
| --- | --- | --- | --- | --- |
| stand | 到达且 L 已归还、支撑稳定 | 实测偏离路径或跌倒 | 定位中断，无法确认支撑 | 保持保护并重新测量 |
| grasp | 站稳后确认目标在手 | 物体确认留在原地 | 身体已停但身份不可见 | 待补证，不提交成功 |

## 故障与偏序

| 注入边界 | 预期记录 | 必须先发生 | 禁止结果 |
| --- | --- | --- | --- |
| F04a · walk：活跃阶段内 Monitor 重启，首次有效刷新前跌倒 | 规则层直达 S0；UNKNOWN 基线 Event 可双空；S2 暂冻本体待派项；对账选中 exec.walk，封住 RA 待派项；不能虚构同时在跑的上肢抓取 | S0 实际范围及所有权对账先于选择取消对象；新鲜刷新还须核对保护代际 | 凭空构造阶段；用历史上下文取消无关执行 |
| F04b · walk：仿真姿态子句已 ARMED 后足接触消失 | S0 收紧；S2 收到 LOST 与 CANCEL_AFFECTED | 请求 SLOW 先于覆盖丢失中断 | 把实机从未可用的足接触标为 LOST |

## 上下文、记忆与监测

Context：将仿真部署与实机的可用性分开；视图按 boot_id 和 epoch 失效。 Memory：保留真实保护范围、恢复凭证与空窗前后的证据来源。

| 需求 | 关注点与证据 | D9 映射 | 上限 |
| --- | --- | --- | --- |
| MR-01 | 无意图时的跌倒 · 确定性支撑／惯性基线与 S0 回执 | baseline/fall@1（其他危险依部署登记的基线硬规则） | STOP_LATCHED |
| MR-04 | 步态中足接触通路失效 · 仿真姿态和足接触流 | generic/posture_balance@1 | SLOW |
| MR-03 | 运动离开本阶段批准走廊 · 参考系一致的姿态、方向与扫掠区 | generic/motion_envelope@1 | SLOW |
| MR-05 | 持物滑移、载荷转移或非预期接触 · 绑定手的原始计数、指位和物手相对运动 | generic/contact_force_envelope@1 | SOFT_HOLD |

## 数据与迁移

仿真：仿真覆盖步态支撑流先有效后丢失。遥操作：只采获准站姿上肢动作，未授权步态不采。跨本体：可迁移上身接近；足接触来源、地面和载荷分布不能照搬。

缺口：E04、C02、M01。[登记依据](../gaps.md)

## 测试向量

| 故障 | 初态 | 检查的记录 | 偏序 |
| --- | --- | --- | --- |
| F04a | 仿真阶段存活，重启实例尚无任何阶段记录或执行句柄。；到达物件附近并在稳定站姿下抓取；串行仿真行走中，仅腿轨有步态执行 exec.walk；RA 由 S0 维持，存在待派上肢项。Event 检测范围仅 L，回执实际保护 L、RA。两路送达可换序。 | irq = 协议 irq Event/detection/intent_status → UNKNOWN；fence = 适配器 fence 派发记录/状态 → 本体待派已冻结；ids = 协议 irq Event/interrupt/affected_execution_ids → []；contexts = 协议 irq Event/detection/phase_contexts → []；cancel = 协议 irq Event/interrupt/disposition → CANCEL_AFFECTED；receipt = 协议 applied ProtectionReceipt/scope/resource_ids（集合相等） → ["L", "RA"]；scope_source = 适配器 selection 取消选择/依据 → S0 回执实际资源与当前所有权；selected = 适配器 selection 取消选择/执行 → ["exec.walk"]；receipt_cause = 协议 applied ProtectionReceipt/event_ref → event.baseline-fall-idle；detected = 协议 irq Event/scope/resource_ids → ["L"]；owners = 适配器 owners 当前所有权/腿轨执行 → exec.walk；arm_owner = 适配器 owners 当前所有权/右臂 → S0 维持；outbox = 适配器 selection 取消选择/新封锁待派资源 → ["RA"] | irq ≺ fence；receipt ≺ selected；fence ≺ selected；owners ≺ selected |
| F04b | 仿真支撑与足接触样本有效，姿态子句曾布防。；到达物件附近并在稳定站姿下抓取 | slow = 适配器 slow 本地保护请求/level → SLOW；irq = 协议 irq Event/interrupt/reason_code → monitor/clause_coverage_lost | slow ≺ irq |

## 契约记录

| 对象 | 字段 | 具体检查 |
| --- | --- | --- |
| BodyProfile | sensors、compatible_combinations | 拒绝未批准实机支撑 |
| Event | detection、interrupt | 基线 UNKNOWN 时按 S0 回执选范围 |
| Execution | core_evidence、leases | 核实腿轨与上身所有权 |
