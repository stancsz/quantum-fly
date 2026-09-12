# 量子果蝇 Quantum Fly

### 果蝇的大脑连接图，能否帮助我们构建更稳健的投资组合实验？

[English](README.md) · [研究假设](docs/HYPOTHESES.md) · [实验计划](docs/EXPERIMENT_PLAN.md) · [当前目标](GOAL.md)

量子果蝇是一个面向开放、可复现实验的研究原型，把三种不寻常的元素放在同一个可检验框架中：

- 以公开发布的雄性果蝇连接组作为结构启发
- 使用明确经典基线的因果离线投资组合实验
- 把小规模量子模拟作为可检验的评分与稳定性组件

项目不是要制造一个神奇的交易机器人，而是要提出一个更严格的问题：**当市场、参数和样本发生变化时，哪些决策仍然成立？**

如果你也对这个问题感兴趣，欢迎 fork 项目，替换其中一个组件，保留同样的对照实验，然后分享哪里失效了。负面结果同样有价值。

> [!IMPORTANT]
> 这是实验性研究原型，不是投资建议。项目不声称存在量子优势、生物学复现、稳定盈利、全脑运行或生产就绪能力。

## 为什么值得探索

大多数投资组合模型从常见架构出发，再优化表现。量子果蝇从稳健性与可证伪性出发。

项目把果蝇连接组作为稀疏结构先验，然后检验这种结构是否真的优于简单方法。任何有趣结果都必须与经典基线、无图消融、随机拓扑、度数匹配对照、多随机种子、因果时间切分和交易成本进行比较。

**量子稳定性**是项目提出的研究假设，不是已经确立的科学能力。这里的操作性含义是：在明确的评估协议下，测量投资组合决策对市场扰动、模型参数噪声和抽样变化的敏感程度。

## 目前可以运行什么

仓库包含一个可复现的离线 Python 研究骨架：

- 有界的 MaleCNS 连接组扫描与子图实验
- 有限市场特征编码与稀疏递归图状态
- 透明的经典基线与无图消融
- 因果历史评估与 walk-forward 工具
- 可选的 4-qubit PennyLane 评分路径
- single Fly、three-member 与 coordinator 结构比较
- 持久化、类型明确的本地 Fly 消息和研究 receipt
- 带 request ID 且明确记录失败的 LeanRouter smoke probe

默认 fixture 是合成数据。当前真实数据路径使用官方 MaleCNS 数据的有界子集，以及缓存的 FRED 2024 S&P 500 指数输入。一次成功运行只证明该次有界实验完成。

## 快速开始

需要 Python 3.10 或更高版本，以及[数据接收凭证](docs/DATA_RECEIPT.md)中列出的官方 MaleCNS 文件。

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[test,quantum]"
python -m scripts.quickstart --check
python -m scripts.quickstart
python -m pytest
```

运行结果会保存为机器可读的 `outputs/local-research-run.json`。如果没有安装 PennyLane，receipt 会明确标记量子输出不可用，同时仍保存经典与连接组结果。

其他常用入口：

```powershell
# 向基于本地 receipt 的研究接口询问还缺少什么证据
python -m scripts.fly_chat "当前评估是什么，缺少什么证据？"

# 比较 single Fly、three-member mean、coordinator state 和 no-graph 对照
python -m scripts.run_structure_comparison --max-nodes 4096 --max-source-edges 10000000 --seeds 0 1 2

# 运行有界的多 Fly 消息与状态循环
python -m scripts.run_fly_loop
```

## 系统如何连接

```text
市场特征
   |
   v
连接组启发的稀疏状态 ----------> 经典对照
   |                                |
   v                                |
可选量子评分                         |
   |                                |
   +-------------> 投资组合信号 <----+
                         |
                         v
             因果离线评估、成本与扰动
```

连接组结构与量子模拟之间的精确耦合方式，本身就是待研究的问题。项目不会预先假定它有效。

## Fork 后做一个可证伪实验

一个有价值的 fork 应只改变一个因素，并保留对照组。可以从这些实验开始：

1. 用度数匹配的随机图替换连接组拓扑。
2. 用参数量匹配的经典模型替换量子评分器。
3. 用更少的 Fly 模块对比 three-member coordinator。
4. 在不改变评估窗口的情况下增加一个因果市场特征。
5. 在不同硬件或不同随机种子上复现一个负面结果。

发布结果时，请附上命令、配置、随机种子、数据来源、运行时间、资源使用和失败记录。你可以提交带 receipt 的 issue，或发起一个范围清晰的小型 pull request。最有价值的贡献，也可能是证明某个精彩想法行不通的实验。

项目软件采用 [MIT License](LICENSE)。重新分发研究结果或数据前，还请阅读[开放协作边界](docs/OPEN_COLLABORATION.md)；MaleCNS 数据仍需遵守独立的 CC BY 署名要求。

## 研究规则

- 解剖连接不等于可执行的神经动力学。节点状态、权重、更新、输入、目标和 readout 必须另行定义。
- 回测必须采用时间顺序正确的切分，并报告成本、数据泄漏检查、随机种子和失败结果。
- 本地测试、smoke call 或研究 receipt 不能证明运营可靠性。
- 任何结果都不应被描述为投资建议或稳定盈利证据。
- 模拟量子组件不能证明量子加速或量子优势。

## 项目地图

- [GOAL.md](GOAL.md)：已验证能力、未完成缺口、验收条件和硬边界
- [研究假设](docs/HYPOTHESES.md)：可以被实验拒绝的主张
- [实验计划](docs/EXPERIMENT_PLAN.md)：基线、消融和评估协议
- [系统架构](docs/ARCHITECTURE.md)：多 Fly 与 coordinator 设计
- [Agent 协议](docs/AGENT_PROTOCOL.md)：组件之间的有界通信
- [数据接收凭证](docs/DATA_RECEIPT.md)：MaleCNS 来源、schema、校验和规模
- [研究边界](docs/RESEARCH_BOUNDARY.md)：当前证据能证明什么，不能证明什么
- [开放协作](docs/OPEN_COLLABORATION.md)：公开研究与私人工作的边界

## 数据与署名

项目使用 Janelia 官方发布的 [MaleCNS v1.0 数据](https://male-cns.janelia.org/download/)。上游页面将数据标记为 CC BY。原始数据保存在 gitignored 的 `data/malecns-v1.0/raw/` 目录。预期文件和验证详情见 [DATA_RECEIPT.md](docs/DATA_RECEIPT.md)。

量子果蝇还很早期，也足够奇怪，但它刻意保持可检验。**Fork 这个问题，不要复制结论。**
