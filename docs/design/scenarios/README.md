# D12 架构检验场景集

用这套语料检查规划、能力准入、控制所有权、保护和三值验证如何串成一次可追溯的任务。A 档有逐轨、逐节点和故障断言；B 档用阶段表拓宽覆盖面。当前是设计审查，未运行机器人或仿真任务。

固定基线：总仓 `67c066d`、Harness `ed2eb4b`、策略仓 `99b37bf`、目录 `0.2.0`、本体 `g1-inspire@3`。每个 YAML 独立保存这组引用。W5 行走仅有仿真设计覆盖，实机支撑受阻。简报由 S2 先推后派；子句布防只记 Monitor 本地。

## 阅读入口

[模板](template.md) · [JSON Schema](scenario.schema.json) · [逐轨分类](classification.md) · [三张覆盖矩阵](coverage.md) · [缺口登记](gaps.md)

## 用例索引

| 编号 | 用例 | 机读 | 实机授权范围见各页 |
| --- | --- | --- | --- |
| A01 | [单臂拾放红杯](tier-a/A01-pick-place.md) | [YAML](cases/A01.yaml) | 条件授权 |
| A02 | [纠正红蓝杯目标](tier-a/A02-correct-target.md) | [YAML](cases/A02.yaml) | 条件授权 |
| A03 | [并行开抽屉并放入物件](tier-a/A03-drawer.md) | [YAML](cases/A03.yaml) | 条件授权 |
| A04 | [行走、停稳与抓取](tier-a/A04-walk-grasp.md) | [YAML](cases/A04.yaml) | 当前本体未授权 |
| A05 | [把壶中液体倒入杯内](tier-a/A05-pour-water.md) | [YAML](cases/A05.yaml) | 当前本体未授权 |
| A06 | [抓取易碎食材](tier-a/A06-fragile-grasp.md) | [YAML](cases/A06.yaml) | 当前本体未授权 |
| A07 | [向人交接物件](tier-a/A07-handover.md) | [YAML](cases/A07.yaml) | 当前本体未授权 |
| A08 | [折叠毛巾或衣物](tier-a/A08-fold-towel.md) | [YAML](cases/A08.yaml) | 当前本体未授权 |
| B09 | [插头或 USB 插入](tier-b.md#b09-插头或-usb-插入) | [YAML](cases/B09.yaml) | 当前本体未授权 |
| B10 | [翻转螺丝刀后拧紧](tier-b.md#b10-翻转螺丝刀后拧紧) | [YAML](cases/B10.yaml) | 当前本体未授权 |
| B11 | [使用刀具切菜](tier-b.md#b11-使用刀具切菜) | [YAML](cases/B11.yaml) | 当前本体未授权 |
| B12 | [开门并通过](tier-b.md#b12-开门并通过) | [YAML](cases/B12.yaml) | 当前本体未授权 |
| B13 | [双臂抱箱上楼](tier-b.md#b13-双臂抱箱上楼) | [YAML](cases/B13.yaml) | 当前本体未授权 |
| B14 | [持续推车](tier-b.md#b14-持续推车) | [YAML](cases/B14.yaml) | 当前本体未授权 |
| B15 | [杂乱箱中按标签分拣药盒](tier-b.md#b15-杂乱箱中按标签分拣药盒) | [YAML](cases/B15.yaml) | 当前本体未授权 |
| B16 | [抓取透明玻璃杯](tier-b.md#b16-抓取透明玻璃杯) | [YAML](cases/B16.yaml) | 当前本体未授权 |
| B17 | [传送带拾取](tier-b.md#b17-传送带拾取) | [YAML](cases/B17.yaml) | 当前本体未授权 |
| B18 | [清桌并装洗碗机](tier-b.md#b18-清桌并装洗碗机) | [YAML](cases/B18.yaml) | 当前本体未授权 |
| B19 | [受推扰或人员动物闯入](tier-b.md#b19-受推扰或人员动物闯入) | [YAML](cases/B19.yaml) | 当前本体未授权 |
| B20 | [整理线缆并插接](tier-b.md#b20-整理线缆并插接) | [YAML](cases/B20.yaml) | 当前本体未授权 |

## 授权与扩充

已授权（待实测）只用于已批准的限定组合；条件授权须逐项核验证据与实际 S0 准入；当前本体未授权的分支以拒绝或仿真记录作为设计检验。验证状态、传感器可用位和运行时样本质量分别检查。独立仿真策略不会改变实机批准范围。

新增场景从全局下一编号起，填写固定基线、YAML 与对应页面，至少注入一个故障，补本体授权、三张矩阵与缺口归属。B 档成为集成测试目标时补齐 A 档字段并保留原编号的迁移记录。发现缺口先给区分反例：可表达则记录，小修当轮落地并标 ID，架构变更给备选并等裁决。涉及监测简报通道的差异登记给 D9，由其所有者处理。
