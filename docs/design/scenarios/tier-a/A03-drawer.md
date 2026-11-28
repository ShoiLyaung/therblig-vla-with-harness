# A03 并行开抽屉并放入物件

左手开抽屉，右手拾物并放入。验收终态：确认物件位于抽屉内部、脱手且右臂已退出扫掠区。

**条件授权**（站姿并行打开与获取、屏障后的双侧扶持组合）。并发许可取决于具体角色、开度和扶持姿态。放行条件：逐调用核验安装关系、左右令牌、实际开度与扫掠区。依据：DATASHEET_DECLARED、NEEDS_VALIDATION、THIRD_PARTY_MEASURED、UNCALIBRATED。

[机读用例](../cases/A03.yaml) · [既有走通](../../walkthroughs.md#w3-两臂并行打开抽屉并放入物品)

## 计划与证据边界

| 节点 | 图修订 | 前驱或互斥入口 | 能力与组合 | 并行组／父项 | 准入条件 | 退出检查 |
| --- | --- | --- | --- | --- | --- | --- |
| open | 本图 | 本修订入口 | open_drawer · PROVIDER_COMPOSITE | 开抽屉与取物／无 | 抽屉身份和左把手可达、左支准入有效 | 抽屉开度已实测 |
| reach | 本图 | 本修订入口 | move_unloaded · ATOMIC | 开抽屉与取物／无 | 物件与右臂走廊已绑定，与左支组合获准 | 预抓位合格 |
| get | 本图 | reach | acquire_object · ATOMIC | 开抽屉与取物／无 | 右臂到位且身份、握取配置已核准 | 物件身份与握持均可证 |
| join | 本图 | open、get | s2.barrier · BARRIER | 无／无 | 左右支均交出实际处置与新鲜效果 | 开度、通行与支撑同时有效 |
| insert | 本图 | join | move_payload_guarded_drawer · ATOMIC | 无／无 | B1 打开且三项保持引用可登记 | 物件通过入口 |
| stage | 本图 | insert | stage_for_next_use_guarded_drawer · ATOMIC | 无／无 | 搬入位置及两左依赖仍有效 | 内部支撑可用 |
| exit | 本图 | stage | release_to_support_guarded_drawer · ATOMIC | 无／无 | 承载面成立且右手可接管，撤出路径获准 | 确认物件脱手且右臂已退出 |

新图触发条件：抽屉回弹后新图重新测量开度及扶持令牌。

能力发现：open_drawer（已有卡）；move_unloaded（目录模板）；acquire_object（已有卡）；s2.barrier（内部节点）；move_payload_guarded_drawer（目录模板）；stage_for_next_use_guarded_drawer（目录模板）；release_to_support_guarded_drawer（目录模板）。

阶段授权：open：条件授权（抽屉开度已实测）；reach：条件授权（预抓位合格）；get：条件授权（物件身份与握持均可证）；join：条件授权（开度、通行与支撑同时有效）；insert：条件授权（物件通过入口）；stage：条件授权（内部支撑可用）；exit：条件授权（确认物件脱手且右臂已退出）。

## 分轨与占用

| 阶段 | 标签 | S0 与组合 | 交接依据 |
| --- | --- | --- | --- |
| open | U | COMPLIANCE · independent-arms-approach | 结束后取得左臂姿态与左手扶持令牌 |
| reach | TE | BALANCE · independent-arms-approach | 释放接近授权 |
| get | G | hand.acquire_slow · independent-arms | 右手移交保持，释放右臂 |
| join | PN、UD、H | RETENTION、POSE_HOLD · 双侧保持 | B1 核实两左令牌与右载荷；LA 的 H(扶持) 与 LH 的拉手保持分别留证 |
| insert | TL、H | RETENTION、BALANCE · insertion-with-guarded-drawer | 注册两项左依赖及右载荷依赖 |
| stage | PP、H | POSE_HOLD · staging-with-guarded-drawer | 交接期间保持驻留保护 |
| exit | RL、H | COMPLIANCE · release-with-guarded-drawer | 清空后才解除左依赖 |

各阶段九轨的 owner、访问和三类掩码见机读 simo。U 描述开启机构；右臂等待 B1 为 UD，但持物手仍为 H。

## 验证检查点

声明边界：join、exit。终局成功边界：exit。

| 阶段 | SUCCESS | FAILED | UNKNOWN | 恢复 |
| --- | --- | --- | --- | --- |
| join | 开度、物件身份、令牌和通行证据均有效 | 明确闭合或拿错物件 | 任一令牌状态或开口不可证 | 停在屏障，核对每项依赖 |
| exit | 区内留物且右臂已清空 | 物件跌出或抽屉夹住右臂 | 物件被挡无法定位 | 保持扶持，安全取证 |

## 故障与偏序

| 注入边界 | 预期记录 | 必须先发生 | 禁止结果 |
| --- | --- | --- | --- |
| F03 · join：屏障期间右手力流一直缺失，必需子句宽限到期 | S0 收到 SOFT_HOLD；Event 用 brief.barrier 和 right_retention 定位；S2 隔离屏障与后继 | 按占用起算且沿用宽限先于 GRACE_EXPIRED；收到相关保护先于再次准入 | 伪造 execution_id；放掉左侧扶持 |

## 上下文、记忆与监测

Context：缓存左右支修订与耦合扫掠区；回弹使开度和通行证据失效。 Memory：记录屏障等待原因及各手独立证据，不把并行终态合并为同一 grant。

| 需求 | 关注点与证据 | D9 映射 | 上限 |
| --- | --- | --- | --- |
| MR-03 | 抽屉回弹进入右臂扫掠域 · 开度与右臂位置 | generic/motion_envelope@1 | STOP_LATCHED |
| MR-05 | 两手保持下限独立失效 · left.hand.force 与 right.hand.force 各自关联子句 | generic/contact_force_envelope@1 | SOFT_HOLD |
| MR-01 | 独立基线核验跌倒、碰撞或危险闯入 · 合格的本体／世界证据与 S0 实际保护回执 | baseline/fall@1（其他危险依部署登记的基线硬规则） | STOP_LATCHED |
| MR-02 | 对象锚点、参考图像与当前接近对象不符 · 独立的实例定位与当前运动方向 | generic/target_identity@1 | SOFT_HOLD |
| MR-07 | 停滞、超窗或屏障等待 · 实测进展及当前阶段的时钟依据 | generic/progress_duration@1 | REEVALUATE |

## 数据与迁移

仿真：对调左右支达到屏障的顺序。遥操作：保留扶持和撤出全过程的双手状态。跨本体：单臂数据不能生成双臂耦合许可。

缺口：E01、E02、M01。[登记依据](../gaps.md)

## 测试向量

| 故障 | 初态 | 检查的记录 | 偏序 |
| --- | --- | --- | --- |
| F03 | B1 双手已被本阶段维持，右力流未出现，原宽限将到期。；左手开抽屉，右手拾物并放入 | hold = 适配器 hold 本地保护请求/level → SOFT_HOLD；irq = 协议 irq Event/interrupt/reason_code → monitor/required_clause_unarmed；disposition = 协议 irq Event/interrupt/disposition → CANCEL_AFFECTED；execs = 协议 irq Event/interrupt/affected_execution_ids → []；node = 协议 irq Event/detection/phase_contexts/0/plan_node_id → node.join；brief = 协议 irq Event/detection/clause_failures/0/brief_id → brief.barrier；side = 协议 irq Event/detection/clause_failures/0/clause_id → right_retention；missing = 协议 irq Event/detection/clause_failures/0/missing_stream_refs → ["right.hand.force"]；affected = 协议 irq Event/scope/resource_ids → ["RH"]；phase_brief = 协议 irq Event/detection/phase_contexts/0/brief_id → brief.barrier；phase_clause = 协议 irq Event/detection/phase_contexts/0/clause_ids → ["right_retention"]；failure = 协议 irq Event/detection/clause_failures/0/failure → GRACE_EXPIRED | hold ≺ irq |

## 契约记录

| 对象 | 字段 | 具体检查 |
| --- | --- | --- |
| Capability | semantics、body_requirements | 扶持变体含两项左侧依赖 |
| Invocation | bindings、handoff_refs | 逐阶段绑定保持令牌 |
| Result | resource_dispositions | 实测清空后才可退出 |
