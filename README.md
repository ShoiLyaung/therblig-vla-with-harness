# Therblig 双仓库架构

**Multi-Repository Architecture（多仓库架构）+ Plugin-based Architecture（插件化架构）+ Contract-first Design（接口契约优先设计）。**

> **vla-harness = Orchestration / Execution Plane**\
> **therblig-vla = Policy / Primitive Skill Plane**\
> `policy-interface-protocol` 是两者之间的**稳定接口契约（Contract）**，独立于具体语言、实现与宿主。

采用 **Polyrepo + Hexagonal Architecture（六边形架构）**，把 System 1 和 System 2 设计成两个可以独立开发、独立发布、自由组合的组件：

- 替换 VLA，而不修改 Harness。
- 替换上层 Agent Host（如 Codex、DSH）或编排实现，而不修改 VLA。
- 基于统一接口开发自己的 VLA 或 Harness。

参考 [Envisioning Agentic Robotics 的 Figure 3](https://arxiv.org/html/2611.18359v1#S2.F3)。

```text
                        User
                         │
                         ▼
┌────────────────────────────────────────────────┐
│ System 2 · Reasoning & Orchestration           │
│                                                │
│ Agent Host (Codex / DSH / Custom Agent)        │
│                 ⇅                              │
│ Host Adapter · Integration Boundary            │
│                 ⇅                              │
│ vla-harness · Orchestration / Execution        │         ┌───────────────────────┐
│   Planner (LangGraph Agent Loop)               │◄────────┤ Real-time Event       │
│     ⇅ Foundation Model (reasoning backend)     │观测/中断│ Monitor               │
│   Context Manager · Memory · Verifier          │         │                       │
│   Tool Interface · Policy Registry             │         │                       │
│   Executor                   阶段简报／周期刷新│────────►│ lightweight VLM       │
└────────────────────────────────────────────────┘         │ + rule detectors      │
   ⇅ policy-interface-protocol       ┊                     │ safety rules          │
┌───────────────────────────────┐    ┊                     │                       │
│ System 1 · Skills & Callable  │    ┊  optional           │ watches: User,        │
│ Policies                      │    ┊  direct call        │ Robot body,           │
│                               │    ┊  (bounded           │ Physical world        │
│ therblig-vla · OpenVLA        │    ┊  mode               │                       │
│ Custom Policy Adapter         │    ┊  requests)          └──┬────────────────────┘
└───────────────────────────────┘    ┊                        │        ▲
   ⇅ control target / measured state ┊                        │        │
                                     ▼                        │        │ observation
┌────────────────────────────────────────────────┐ immediate  │        │
│ System 0 · Body Interface & Local Real-Time    │◄───────────┘        │
│ Control                                        │ reaction            │
│ Robot Driver / Simulator / Device Interface    │ (stop / slow)       │
│ Local Control Loop · State Feedback · Limits   │                     │
└────────────────────────────────────────────────┘                     │
                        ⇅                                              │
            Robot Body (sensors / actuators) ──────────────────────────┤
                        ⇅                                              │
              Physical World / Environment ────────────────────────────┘
```

图中向下传递任务与控制目标，向上返回观测、执行状态，形成闭环。System 2 由 `vla-harness` 与其调用的基础模型构成：Harness 内的 Planner 以 LangGraph 风格的 Agent Loop 负责任务分解与重规划，基础模型作为可替换的推理后端；Codex、DSH 等宿主只通过 Adapter 接入。`therblig-vla` 是 System 1 的一种可替换实现，其他策略通过适配器接入同一协议。

三个 System 之外并行运行一个 **Real-time event monitor**（本地轻量 VLM 和/或规则检测器），高频观察 User、Robot body 与 Physical world。S2 经它获取用户、身体与环境的观测数据；safety rules 驻留在 monitor 中，触发时一方面直接让 S0 立即做出保护动作（如停止、减速），不等待 S2；另一方面向 S2 发出 interrupt，由 S2 取消当前调用并重规划，期间 S0 保持身体稳定。S2 还可经 Tool interface 对 S0 发起 optional direct call，仅限有界的模式请求（如保持、减速、停止、切换控制模式）。另外，实际机器人控制有实时性要求。System 2 负责高层规划、监控和重规划；System 1 负责低延迟策略推理与动作序列执行；System 0 负责设备驱动与本地实时控制。LLM 推理延迟不应直接决定底层控制周期。

# 两个仓库的职责边界

技能调用主路径为 **S2 ⇄ S1 ⇄ S0**：向下委托目标或提交控制目标，向上反馈观测、运行状态与证据。旁路有四条：S2 → Monitor 的阶段简报，Monitor → S2 的观测数据与 interrupt，Monitor → S0 按 safety rules 触发的即时保护，以及 S2 → S0 的 optional direct call。

| 层或组件 | 负责 | 边界 |
|---|---|---|
| S2：宿主 Adapter | 把 Codex、DSH 等宿主的用户请求与工具调用映射到 Harness Core。 | 不承担任务分解与重规划；宿主依赖留在 Adapter 内。 |
| S2：Harness Core | Planner（LangGraph Agent Loop：理解目标、分解任务、选择下一步、恢复与重规划）、Context、Policy Registry、Resolver、工具调用、执行协调、Memory 与任务验证。 | 调用基础模型作推理后端；不承担模型训练，不参与机器人高频控制。 |
| S1：策略服务 | 根据观测推理动作，在委托子任务内执行策略或局部技能组合，检查局部条件并返回结果和证据。 | 不改变上层目标，不接管任务级编排。 |
| S0：Controller / Driver | 设备驱动、本地实时控制、实测状态反馈、控制限位及本地保护；可受理 S2 的有界模式请求，以及 monitor 按 safety rules 触发的即时保护。 | 控制与保护不能等待 S2 的网络请求或 LLM 推理完成；保留最终控制权。 |
| Real-time event monitor | 高频观察 User、Robot body 与 Physical world；按 safety rules 直接触发 S0 即时保护。向 S2 提供观测数据，需要重新评估时发出 interrupt；不确认简报，不报告自身监测状态。 | 位于三个 System 之外，不被调用即可发信号；不进入任务级规划。 |

`therblig-vla` 同时提供可导入的研究组件和独立运行时；其他 VLA、程序策略或独立服务可在满足契约后替换它。通用的 `vla-harness` 不负责训练具体 VLA。

这里最重要的设计原则是：

`vla-harness` 不应该知道 Therblig 是什么，它只知道：

```text
Task/Plan
Event/Interrupt
Policy
Capability
Observation
Action
Execution
Verification
Memory
```

动素语义由 S1 提供者在 Capability 描述中以通用语义字段声明，Harness 按字段读取用于规划、解析与验证，而不在核心代码中写死动素。动素的分类采用多维属性表，同一张表推出 S2 工具集、训练标注词表与 S0 需维持的状态。

反之，`therblig-vla` 也不应该知道 Harness 是 Codex 、 Claude 还是 DSH，它只需要能够：

```text
receive structured task
→ infer primitive action
→ execute / predict action
→ return structured result
```

这样以后完全可以出现：

```text
Claude / Codex / DSH / OpenHands / custom agent
             │
             ▼
          adapter
             │
             ▼
       vla-harness
             │
             ▼
therblig-vla / OpenVLA / Custom Policy
```

## 扩展入口

| 开发者要接入什么 | 实现哪一侧 |
|---|---|
| 新模型后端 | 在 `therblig-vla` 内实现 `BaseVLAPolicy`，注册到本地模型表，即可复用独立运行时做推理与实验。每种动素单独声明参数、前置条件、预期效果、观测与动作空间，可绑定不同模型。 |
| 独立策略服务 | 用任意语言实现协议服务，发布能力、所需观测和机器人要求。Harness 的 Policy Registry 发现服务，再按能力与当前设备匹配策略。 |
| 新 Agent 宿主 | 用 Adapter 将宿主工具调用映射到 Core 的提交任务、查询、取消操作。Codex MCP Server 与 DSH 插件各自维护宿主依赖。 |
| 独立 Harness | 实现同版协议的客户端即可调用现有 S1 服务。宿主、规划和记忆可自行选择。 |

## 跨仓调用

以下为执行型能力的候选 HTTP/JSON 接口。
预测接口、monitor 事件和 S2→S0 有界模式请求已裁决为同一契约版本内的可选 profile（`prediction`、`monitor-events`、`body-modes`）；任务与持久记忆归 S2，S1 只接收调用切片；执行、取消、可知状态和验证结果各自演进。HTTP 操作在评审通过后再绑定，见[决策登记](docs/design/README.md#决策登记)。

| 端点 | 用途 |
|---|---|
| `GET /v1/health` | 检查服务可用性。 |
| `GET /v1/capabilities` | 读取能力标识、策略版本、参数、观测模态、动作空间和适用设备，判断本次任务能否派发。 |
| `POST /v1/executions` | 携带协议版本、任务标识、能力标识、参数及超时与安全约束，申请执行。受理后保存服务返回的 `execution_id`。 |
| `GET /v1/executions/{id}` | 取得进度、终态、结果及观测证据。查询超时后按原句柄对账，再决定是否重试。 |
| `POST /v1/executions/{id}/cancel` | 请求停止。冲突的下一步须等本地运行时确认停止、释放相应资源后再派发。 |
| `POST /v1/predictions` | 仅返回预测动作。 |

观测携带采集时间和来源，空间量注明参考系及单位。S1 根据本地观测更新动作目标，S0 负责伺服与限幅。S2 的 Executor 跟踪调用，Verifier 根据观测判定效果。例如，目标是拿起红杯，执行已结束而相机仍看见红杯留在桌上，效果判为失败。若桌面被遮挡且缺乏其他证据，效果记为未知。

# 目录与契约验证

Harness 采用独立 Python Core 与顶层宿主 Adapter 的组织方式；Adapter 按需独立打包并允许不同语言。目录按职责划分，允许 MVP 合并小模块，不要求一次性创建所有占位模块：

| 仓库 | 路径 | 内容 |
|---|---|---|
| `vla-harness` | `contracts/v1/` | 公共 schemas、HTTP 绑定及协议示例；与 Python 实现分离。`openapi.yaml` 定义 HTTP 操作，引用 `schemas/` 中的对象定义，`examples/` 提供两端共用的样例。协议独立版本化，客户端与服务端各在 `tests/contract/` 校验同版契约。 |
| `vla-harness` | `packages/harness-core/src/vla_harness/` | Core、Context、Planner、Tools、Policy Client/Registry、Resolver、Memory、Verifier 与策略协议绑定。 |
| `vla-harness` | `adapters/codex-mcp/`、`dsh-plugin/` | 宿主 Adapter（Codex、DSH 及其他宿主适配器），按宿主需要独立组织语言和打包。 |
| `therblig-vla` | `therbligs/` | primitive catalog 及语义 schema。 |
| `therblig-vla` | `src/therblig_vla/semantics/`、`policies/` | 语义对象、策略接口、注册与加载。 |
| `therblig-vla` | `src/therblig_vla/inference/`、`runtime/` | 推理与局部动作执行；不包含上层 Agent Loop。 |
| `therblig-vla` | `src/therblig_vla/environments/` | 仿真、机器人与设备接口适配。 |
| `therblig-vla` | `src/therblig_vla/protocol/`、`api/` | 公共契约映射与 HTTP 服务入口。 |
| `therblig-vla` | `src/therblig_vla/datasets/`、`training/`、`evaluation/` | 研究与评估组件。 |
| 两仓库 | `docs/`、`tests/`、`examples/` | 架构与协议说明、契约及集成验证、最小接入示例。 |

同一单元格中的后续短目录名与首个目录具有相同父目录。统一用 `environments/` 承载机器人与仿真适配，避免同时采用含义重叠的目录命名。

契约验证覆盖能力与输入兼容、结构化调用、状态与取消语义、结果和证据，以及替换策略提供者或宿主 Adapter 后闭环仍成立。Python 实现测试不能代替公共契约测试；两个仓库分别验证对同一协议版本的兼容性。

验收时，分别用现有 Harness 调用独立实现的策略服务，用独立客户端调用 `therblig-vla`。两组均检查能力发现、执行回执、状态查询、取消与结果证据。
