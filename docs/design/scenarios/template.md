# 场景编写模板

每个阶段用稳定的 id 命名，注明所需动作和预期的物理结果。先填 [机读约束](scenario.schema.json)，再从同一用例写评审页。用例中的事件顺序是断言，不是实测时序。成功涉及受理、终止、物理效果和当前意图四项，查询超时或遮挡时保留 UNKNOWN。

| 字段 | 两档共用的填写规则 |
|---|---|
| scenario_id、tier、revision、title | 如 A21 或 B21；全局序号不重复。内容变化升修订。 |
| baseline_refs | 总仓、两个子仓提交号，目录修订，本体标识及修订。 |
| goal、success_definition、ambiguity | 写可观察的终态、最容易混淆的动作和判界方法。 |
| phases | 每行写阶段目的、目录码、能力、S0 状态、验证判据、监测需求、故障引用及授权。受阻行仍写预期的拒绝边界。 |
| authorization | 实机结论、作用范围、理由、出处标签与放行条件。仿真覆盖单列。 |
| monitor_needs | MR 编号、场景证据、可请求的最高处置或纯复核、既有 D9 名称。 |
| faults | 标识、注入边界、注入内容、可见记录、必须满足的偏序以及禁止结果。 |
| protocol_checks | 逐例列出公共对象、字段及其能区分的结果。 |
| coverage、gap_refs | 逐项注明组件和感知需求的覆盖状态，登记缺口 ID。动素矩阵由阶段码和阶段覆盖状态产生。 |

## A 档追加字段

| 字段 | 填写与评审 |
|---|---|
| extends_walkthrough、evidence_refs | 已有走通用仓根相对路径加锚点，独立例填“独立用例”；列可离线核验的基线文件。 |
| capabilities、dag | 区分已发布卡、目录模板、待建卡和内部节点。列出准入条件、前驱、并行组、屏障、展开父节点与重规划触发；重规划创建新图修订。 |
| simo | 每阶段按 E、LA、RA、LH、RH、W、L、S2、MON 记录标签、责任方、访问及观测／动作／缺失掩码；FD 是瞬时点，LO 对应目录 x.locomote。决策与事件道只作记录。 |
| occupancy | 每阶段列资源、占用方式、组合准入、维持令牌、交接或退出边界。 |
| verification_boundaries、checkpoints | 明列检查点集合及终局成功边界，每个边界恰有一条对应记录。每个物理检查点独立写 SUCCESS、FAILED、UNKNOWN 的证据与补证／恢复分支。 |
| context、memory | 当前可见状态与失效规则；跨阶段保留的历史、来源与目标修订。 |
| training | 标签边界、按轨掩码、仿真适用面、原生遥操作和跨本体迁移限制。 |
| test_vectors | given 给初态，when 引用故障，expected_records 是各方可核验记录，ordering 约束偏序，forbidden_outcomes 是负断言。 |

## 转成测试

先解析 YAML，拒绝重复键、非字符串键及非 JSON 值，再按 tier 只命中一个分支。加载基线契约，按阶段为向量绑定观测、调用及资源；故障由模拟器或消息适配器在指定边界注入。对保留的记录检查偏序，允许事件和 S0 回执换序送达。效果证据与执行终态分开判断。向量 assertions 以 source 区分协议报文和适配器观测，以 record 标识同一报文实例，以 alias 命名该实例的字段断言；完整 JSON Pointer 与 JSON 类型的期望值均须核对。可选的中间态仅在采到时断言。对应协议实例须先通过固定修订的整份 schema 校验；before 用别名对约束先后。中文记录类型属于测试适配器的局部观察点，协议类型使用基线字段。phase.authorization 只能取授权三态，适用条件写入 authorization_note。A02 用 graph_revision 切分修订，depends_on_one_of 只等待选定分支。B 档升为 A 档并补入向量后才进入集成测试候选。

公开 DAG 的依赖只引用公开节点；simo 的 replay_segments 记录同一封装调用内部可选的回放分段。混合授权的择一任务在 scope_branches 中逐项列出范围、完整分支及授权状态。资源处置断言用 select.array_path 和 resource_id 唯一选行，再以 path 读取行内字段；资源集合用 compare_as=set 比较，顺序不影响判定。
