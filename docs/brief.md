# 项目意图（元提示原文）

> 状态：用户本人撰写的目标陈述，**不是设计结论**。
> 收录日期：2026-11-27

---

我的想法是通过动素Therbligs（[https://web.mit.edu/allanmc/www/Therblgs.pdf](https://web.mit.edu/allanmc/www/Therblgs.pdf)）的概念去训练VLA，然后通过一个harness插件（例如做一个codex插件或者dsh插件）来接入上层的大模型，调用GPT-6.2 Astra这类大模型去进行任务的规划、拆解成能调用动素VLA（TherbligsVLA）来执行的子动作（即动素）。

# 总体设计
参考[https://arxiv.org/pdf/2611.18359v1](https://arxiv.org/pdf/2611.18359v1) Latest Agentic Robotics Survey 这篇文章中对现代 Agentic Robotics 的设计。

- 我的插件层就是**System 2**，是一个 Embodied harness 需要考虑（Context manager、Tool interface、Planner、Memory）。这个Harness需要考虑LangGraph的设计，形成一套Agent Loop。
- 动素VLA（TherbligsVLA）是我们的System 1，需要考虑如何设计与训练
- 底层在本地通过运行一个轻量、快速的VLM作为监测器（monitor），观察机器人自身状态、物理信息，向上层模型反应异常，提出重新规划、修正
- 更底层 System 0 ，它应该同时与**System 2和System 1** 有关联

# 大致设计思路以及一些我能想到的细节（不局限，可以进行补充与扩展）
- 动素的定义，需要考虑与System 2 的 Tool interface 对接，设计接口，设计理念可以通过（[https://web.mit.edu/allanmc/www/Therblgs.pdf](https://web.mit.edu/allanmc/www/Therblgs.pdf)）的18种动素作为蓝图，需具备扩展性与鲁棒性
  - 例如使用Use、装配Assemble，对于不同物体的适配是很宽泛的，两种思路：
      1. 让上层 planner 对这类动素进行进一步的拆解，需要上层负责规划的LangGraph具有递归、层次的设计。
      2. 对于特定的一些动作/技能封装为skills，通过 MoE 的路由机制（例如AdaMoE）直接由经过这类任务动作数据训练过的VLA完成。
  - 例如Plan，其实应该与上层**System 2**有紧密的联系
  - 还有例如对齐、预对齐是更关注Action的细节 （甚至 force 和 tactical，如果有传感器的话）；而找东西、抓东西除了Action本身，同时也更关注视觉模态的语义理解，识别物品/颜色/形状/位置、用VLA抓东西，这个过程本身需要巧妙构思上层模型与下层模型的分工与协调，哪些任务是上层模型System 2 需要做的，哪些动作是下层模型System 1需要做的，甚至如果抓错了，monitor 应该怎么去干预并反馈、修正。（应该先对整个实现流程进行设计，而不是直接开始工作）
  - 因为我们System 1训练的是动素，所以需要考虑训练好的模型中，指令的语义必须能有效激活VLA对应的能力和动作的参数（比如我要去拿一个物品A，上层模型下达指令后，我不希望模型去执行去抓旁边B，也不希望模型开始），除了从上一条说的如何从整个系统的层面去考虑怎么设计，训练过程中也需要考虑如何强化、优化这个方面的能力
  - 动素的设计是非常重要且关键的，动素概念是我们整套设计的core concept
  - 对于数据集、任务场景、硬件/仿真
  - 我们需要对现有的主流数据集进行搜集、整理、预处理
  - 我们的硬件设备和仿真机器人选择的是Unitree G1（29DoF）+Inspire hand（RH56DFX）
  - 仿真环境我们选择的是本机`/home/sl/research/.runtime/isaac-sim-6.2.0-lab-3.0.0\`
  - VLA目前打算用openpi π0.5作为baseline(/home/sl/research/baseline/openpi) ，Isaac-GR00T N1.7作为备选(/home/sl/research/baseline/Isaac-GR00T)
  - 优先搜集尽可能原生兼容的数据集（Unitree G1（29DoF）+Inspire hand（RH56DFX））
  - 需要多元、复杂的任务场景去训练VLA对于子动作和语义理解的泛化能力，任务场景越多越好，可以先整理目前主流的具身智能人物场景
  - **适当考虑“跨本体数据迁移”和“仿真示范生成”**  的工作，但具体的扩展范围需要考虑迁移、生成的成本，也是尽可能挑选有迁移价值的任务进行。
    - 例如优先考虑 Unitree G1 对于原生夹爪或者三指Dex的数据集，可以先对训练目标进行归类，比如我想训练的任务不关注手部动作，那我可以mask掉手部输入输出数据然后开始训练其他部分（例如手臂/上身/下肢）；对于需要关注手部动作的训练目标，可以尝试通过CEI这类的**跨本体数据迁移**工作进行数据的生成，然后再训练。
  - 在训练阶段，我们得考虑如何去训练动素VLA（是采用对数据集进行切片、指令标注、预处理直接训练每种动素的功能；还是说不切片，直接用指令标注，然后使用降噪的方法去训练指令语义与动作噪声的关系）
  - 还有比如对于某些动素，例如pick&place的训练，Transport Loaded过程中我们只训练身体腰部以上关节、而且不关注手指（手指属于Grasp关注的焦点）。我们需要在训练前对任务进行解构和mask，而且这套解构、重组的流程能与System 2推理时一致，即数据训练、推理的共轭，任务解构、组合的共轭。
  - 比如对于pick & place的任务，如果我们选择了拆分的实现流程，那比如在抓到东西（Grasp）后，把物体移动到目标位置的过程（Transport Loaded）中，抓取的维持在Move过程中应该由 System 0 来完成，它本质是一套不需要**System 2和System 1**介入的闭环控制。
  - 上一条的情况在更复杂的情况下应该考虑如何递归、异步、并行的设计。比如我要考虑下肢一边通过policy移动的时候、上肢一边用VLA去抓东西（或者是拿好东西了用System 0维持抓握）；双手任务：左手去拉开一个抽屉，右手同时去抓准备放到抽屉里的东西；双手协同：左手拿簸箕，右手拿扫帚去扫一个物体，左手要对准扫帚扫过来的方向……

所以当前第一步，先从[https://web.mit.edu/allanmc/www/Therblgs.pdf ](https://web.mit.edu/allanmc/www/Therblgs.pdf)和 [https://arxiv.org/pdf/2611.18359v1](https://arxiv.org/pdf/2611.18359v1)  这两篇文章入手，分析18个动素的意义与设计，考虑动素的概念如何对我们整个系统的关键部分进行抽象（Abstraction），并设计整个系统的架构（architecture）也就是System 2（Context manager、Tool interface、Planner、Memory）  System 1  System 0。
