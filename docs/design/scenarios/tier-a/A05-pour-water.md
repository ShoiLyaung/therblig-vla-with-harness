# A05 把壶中液体倒入杯内

从已标识的壶向目标杯倾倒，到达目标液位后将壶放回。验收终态：杯内液位符合目标标准、无可见溢出、壶直立且有支撑。

**当前本体未授权**（倾倒时液位、溢出及偏载包络；普通站姿壶柄获取单独审查）。没有已发布的倾倒卡、液位验证路径及批准的偏载包络。放行条件：取得液位与溢出证据标准、匹配载荷工况及倾倒变体审批。依据：DATASHEET_DECLARED、NEEDS_VALIDATION、THIRD_PARTY_MEASURED、UNCALIBRATED。

[机读用例](../cases/A05.yaml)

## 计划与证据边界

| 节点 | 图修订 | 前驱或互斥入口 | 能力与组合 | 并行组／父项 | 准入条件 | 退出检查 |
| --- | --- | --- | --- | --- | --- | --- |
| plan | 本图 | 本修订入口 | s2.expand · EXPANDABLE | 无／无 | 任务修订、目标杯与液位标准已确认 | 目标杯与液位标准已绑定 |
| pick | 本图 | plan | acquire_object · ATOMIC | 无／plan | 壶柄身份、握取包络与接近条件成立 | 壶柄身份与接触分别确认 |
| carry | 本图 | pick | move_payload · ATOMIC | 无／plan | 壶柄保持令牌有效且载荷组合获准 | 壶体到达且路径清空 |
| transfer | 本图 | carry | s2.expand · EXPANDABLE | 无／plan | 已至杯旁，液位与溢出观测路径已按本变体验证 | 液位标准、杯口与壶嘴已绑定 |
| align | 本图 | transfer | align_for_use · ATOMIC | 无／transfer | 壶与杯口身份新鲜且姿态可比较 | 壶嘴与杯口关系合格 |
| pour | 本图 | align | pour_liquid · PROVIDER_COMPOSITE | 无／transfer | 杯口对位通过且模拟倾倒工况获准 | 液位与溢出分别验证 |
| restage | 本图 | pour | stage_for_next_use · ATOMIC | 无／plan | 流已停止且壶已回正，原支撑区域可见 | 流已停止，壶底与支撑区域已对准 |
| rest | 本图 | restage | release_to_support · ATOMIC | 无／plan | 已确认支撑，右手接管路径有效 | 壶直立、受支撑且手已脱离 |

新图触发条件：溢出或液位未知转入回正与安全检查子图。

能力发现：s2.expand（内部节点）；acquire_object（已有卡）；move_payload（已有卡）；align_for_use（目录模板）；pour_liquid（需新建）；release_to_support（目录模板）；stage_for_next_use（目录模板）。

阶段授权：plan：条件授权（仅目标分解）；pick：条件授权（静态获取壶柄，须核对工况）；carry：条件授权（站姿且偏载仍在既有搬运包络内）；transfer：条件授权（仅图展开并保持已核准的壶柄令牌）；align：条件授权（仅静态杯口定位、对位；不授权倾倒）；pour：当前本体未授权（液位与溢出分别验证）；restage：条件授权（已回正且停止流动的条件下预置；本任务实际前驱倾倒受阻）；rest：条件授权（独立证实支撑后接管；本任务实际前驱倾倒受阻）。

## 分轨与占用

| 阶段 | 标签 | S0 与组合 | 交接依据 |
| --- | --- | --- | --- |
| plan | PN | BALANCE · 无身体写入 | 只生成子图 |
| pick | G | hand.acquire_slow · 单臂准入 | 保持令牌绑定壶 |
| carry | TL、H | RETENTION · carry-with-support | 搬运期间保持手部 |
| transfer | PN、H | BALANCE · 无身体写入 | 原壶柄保持跨越展开，不生成新 grant |
| align | P、H | COMPLIANCE · 需要当前杯口容差 | 沿用壶柄保持 |
| pour | U、H | RETENTION、COMPLIANCE · 需批准偏载包络 | 壶回正后检查流已停止 |
| restage | PP、H | RETENTION · 站姿单臂准入 | 保留 RH 依赖 |
| rest | RL | COMPLIANCE · 带撤出变体独立核准 | 接管并消费令牌 |

各阶段九轨的 owner、访问和三类掩码见机读 simo。倾壶使液体转移标 U；倾倒前对准杯口才是 P。减轻的轴向载荷不能独立证明液体进入目标杯。

## 验证检查点

声明边界：align、pour、rest。终局成功边界：rest。

| 阶段 | SUCCESS | FAILED | UNKNOWN | 恢复 |
| --- | --- | --- | --- | --- |
| align | 杯口和壶嘴位置同步可见 | 壶嘴对准其他容器 | 遮挡导致杯口候选不唯一 | 维持直立并补证 |
| pour | 目标杯液位达标且溢出检查通过 | 确认流入错误容器或越界洒出 | 只有壶体减载、液面不可见 | 确认流已停，对杯与托盘分别取证 |
| rest | 壶已由原支撑面承载且脱手 | 壶倾倒或仍挂在手上 | 支撑面不可见 | 复核支撑与手部处置 |

## 故障与偏序

| 注入边界 | 预期记录 | 必须先发生 | 禁止结果 |
| --- | --- | --- | --- |
| F05 · pour：壶嘴遮住液面且托盘出现液滴 | S1 保留姿态及观测来源；Verifier 将目标液位谓词记 UNKNOWN；尚未证实托盘液滴越界 | 确认安全停止倾倒先于换视角；补证后再决定是否继续 | 凭壶重量下降提交达标；盲目追加倾倒 |
| F05b · pour：独立托盘观测证实溢出越界，目标液面仍被遮挡 | 液位谓词 UNKNOWN；无越界溢出谓词 FALSE；本段 effect_holds 为 FALSE，verdict 为 FAILED | 取得越界反证先于失败判定 | 以一个未知液位谓词覆盖已证实的反证 |

## 上下文、记忆与监测

Context：分别记录源壶、目标杯、目标液位标准与托盘范围；壶姿变化使旧液位读数过期。 Memory：保留首次倾倒与回正的观测窗口、溢出区域和补证修订。

| 需求 | 关注点与证据 | D9 映射 | 上限 |
| --- | --- | --- | --- |
| MR-03 | 倾角偏离批准包络 · 壶体姿态、杯口几何 | generic/motion_envelope@1 | SLOW |
| MR-05 | 握持滑移与正常减载混淆 · 指位、相对运动与载荷趋势 | generic/contact_force_envelope@1 | SOFT_HOLD |
| MR-06 | 液体溢出 · 不同新帧的溢出证据，逐项批准的视觉持续策略 | generic/people_workspace@1 | SOFT_HOLD |
| MR-01 | 独立基线核验跌倒、碰撞或危险闯入 · 合格的本体／世界证据与 S0 实际保护回执 | baseline/fall@1（其他危险依部署登记的基线硬规则） | STOP_LATCHED |
| MR-02 | 对象锚点、参考图像与当前接近对象不符 · 独立的实例定位与当前运动方向 | generic/target_identity@1 | SOFT_HOLD |
| MR-04 | 支撑或载荷改变后姿态不稳 · 独立合格的惯性与支撑证据 | generic/posture_balance@1 | STOP_LATCHED |

## 数据与迁移

仿真：液面遮挡、正常减载与滑移分开注入。遥操作：记录真实反光、挂液与回正后的残流用于评估。跨本体：迁移臂部对位，液体动力学和力通道单独验证。

缺口：M02、C01、M01。[登记依据](../gaps.md)

## 测试向量

| 故障 | 初态 | 检查的记录 | 偏序 |
| --- | --- | --- | --- |
| F05 | 目标杯液面被挡，托盘液滴尚未确认为越界。本向量只评价液位谓词；若独立证实越界，整段 effect_holds 为 FALSE，verdict 为 FAILED。 | level = 适配器 level 观测质量/液面 → 遮挡；check = 协议 check Verification/predicates/0/value → UNKNOWN；criterion = 协议 check Verification/predicates/0/predicate/id → generic/target_level@1 | level ≺ check |
| F05b | 杯中液面遮挡，托盘边界与反证观测已独立核对。 | spill = 适配器 tray 托盘观测/越界 → 已证实；liquid = 协议 check Verification/predicates/0/value → UNKNOWN；no_spill = 协议 check Verification/predicates/1/value → FALSE；effect = 协议 check Verification/checks/effect_holds → FALSE；failed = 协议 check Verification/verdict → FAILED | spill ≺ failed |

## 逐轨时间线

| 阶段 | E | LA | RA | LH | RH | W | L | S2 | MON |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| plan | 观察·S1/OBSERVE | 稳定·S0/MAINTAINED | 稳定·S0/MAINTAINED | 稳定·S0/MAINTAINED | 稳定·S0/MAINTAINED | 稳定·S0/MAINTAINED | 平衡·S0/MAINTAINED | PN·S2/RECORD | 基线·MON/RECORD |
| pick | 观察·S1/OBSERVE | 稳定·S0/MAINTAINED | G·S1/DRIVE | 稳定·S0/MAINTAINED | G·S1/DRIVE | 稳定·S0/MAINTAINED | 平衡·S0/MAINTAINED | 任务记录·S2/RECORD | 基线·MON/RECORD |
| carry | 观察·S1/OBSERVE | 稳定·S0/MAINTAINED | TL·S1/DRIVE | 稳定·S0/MAINTAINED | H·S0/DEPEND | TL·S1/DRIVE | 平衡·S0/MAINTAINED | 任务记录·S2/RECORD | 基线·MON/RECORD |
| transfer | 观察·S1/OBSERVE | 稳定·S0/MAINTAINED | 稳定·S0/MAINTAINED | 稳定·S0/MAINTAINED | H·S0/MAINTAINED | 稳定·S0/MAINTAINED | 平衡·S0/MAINTAINED | PN·S2/RECORD | 基线·MON/RECORD |
| align | 观察·S1/OBSERVE | 稳定·S0/MAINTAINED | P·S1/DRIVE | 稳定·S0/MAINTAINED | H·S0/DEPEND | 稳定·S0/MAINTAINED | 平衡·S0/MAINTAINED | 任务记录·S2/RECORD | 基线·MON/RECORD |
| pour | 观察·S1/OBSERVE | 稳定·S0/MAINTAINED | U·S1/DRIVE | 稳定·S0/MAINTAINED | H·S0/DEPEND | 稳定·S0/MAINTAINED | 平衡·S0/MAINTAINED | 任务记录·S2/RECORD | 基线·MON/RECORD |
| restage | 观察·S1/OBSERVE | 稳定·S0/MAINTAINED | PP·S1/DRIVE | 稳定·S0/MAINTAINED | H·S0/DEPEND | 稳定·S0/MAINTAINED | 平衡·S0/MAINTAINED | 任务记录·S2/RECORD | 基线·MON/RECORD |
| rest | 观察·S1/OBSERVE | 稳定·S0/MAINTAINED | RL·S1/DRIVE | 稳定·S0/MAINTAINED | RL·S1/TAKEOVER | 稳定·S0/MAINTAINED | 平衡·S0/MAINTAINED | 任务记录·S2/RECORD | 基线·MON/RECORD |

并行活动分支合并已批准绑定。默认稳定为 S0 本地守持；接管确认前屏蔽写轴。

## 契约记录

| 对象 | 字段 | 具体检查 |
| --- | --- | --- |
| Capability | parameter_schema、result_schema | 冻结容器、目标杯与标准 |
| Result | outputs、evidence | 液位、溢出及回正是独立事实 |
| Verification | predicates、verdict | 遮挡保留未知 |
