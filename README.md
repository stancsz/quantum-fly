# 量子果蝇 Quantum Fly

当前唯一的持续工程目标记录在 [GOAL.md](GOAL.md)。它汇总了已验证能力、未完成缺口、验收条件和不可逾越的边界。

量子果蝇是一个面向股票与投资组合研究的实验性项目。研究想法是把公开发布的雄性果蝇连接组作为决策层的结构启发，再结合运行在经典计算机上的量子模拟，探索投资组合决策在扰动、参数噪声和抽样变化下的稳定性。

这里的“量子稳定性”是项目提出的研究术语，不是已经确立的科学能力。当前建议的操作性定义是：在给定评估协议下，投资组合决策对市场扰动、模型参数噪声和抽样变化的敏感程度。正式定义、度量方式和是否有实际研究价值，都需要通过实验确定。

## 研究边界

- 连接组中的解剖连接数据不等于可直接执行的神经动力学。若要运行模型，必须另外明确节点状态、连接权重、时间更新、输入编码、训练目标和读出机制。
- 项目不声称存在量子优势、真实生物学复现、稳定盈利能力或投资建议价值。
- 所有结论应建立在离线、时间顺序正确的回测和样本外评估上，并报告交易成本、数据泄漏检查、随机种子和失败结果。
- 当前阶段只定义研究问题和验证路径，不把已下载的连接组数据接入模拟器，也不实现交易系统。

## 拟议流程

```text
市场特征 -> 受连接组启发的稀疏决策模型 -> 量子模拟的优化/稳定性评估
         -> 投资组合信号 -> 离线评估
```

“连接组启发”与“量子模拟”的精确耦合方式是待测试的问题，而不是预先接受的结论。实验应至少比较经典基线、仅连接组结构、仅量子模拟、组合模型，以及随机打乱或度数匹配拓扑等对照组。

## 数据来源与规模提示

Janelia 的雄性果蝇中枢神经系统下载页报告了完整片段连接图约 1.1 GB、突触位置约 12.7 GB、突触伙伴对约 6.8 GB、神经递质预测约 2.7 GB。这些是可选的独立表，不代表必须一次性下载的单一数据包：

- [Janelia 数据下载页](https://male-cns.janelia.org/download/)
- [Google Research 关于雄性果蝇全脑连接组的介绍](https://research.google/blog/a-connectomics-milestone-mapping-the-complete-male-fruit-fly-brain/)

下载页标示数据为 CC-BY。项目软件许可证尚未选择。实际资源需求取决于模拟器、神经元状态表示、稀疏存储、数值精度和量子线路量子比特数。若使用状态向量模拟，内存通常会随量子比特数指数增长，因此目前不能据此承诺某种硬件一定能完成完整模拟。用户提到的可能配置约为 RTX 5070 Ti 16 GB 显存和 48 GB 内存，只能作为未来实验规划信息，不能视为已验证的最低要求或成功运行证明。

## 文档

- [研究假设](docs/HYPOTHESES.md)
- [实验计划](docs/EXPERIMENT_PLAN.md)
- [上游设计审查与复用记录](docs/UPSTREAM_REVIEW.md)
- [MaleCNS v1.0 数据接收凭证](docs/DATA_RECEIPT.md)
- [多网络协作设计](docs/HIVE_MIND.md)
- [三模块与协调模块架构](docs/ARCHITECTURE.md)
- [Fly 双向通信协议](docs/AGENT_PROTOCOL.md)
- [开放协作边界](docs/OPEN_COLLABORATION.md)
- [研究边界](docs/RESEARCH_BOUNDARY.md)

## 当前最小实现

仓库现在包含一个离线 Python 骨架：显式稀疏图边界、有限市场特征编码、图 readout、透明的经典基线和可选的 PennyLane 评分模块。PennyLane 初始设计使用 4 个量子比特、1 到 2 个浅层、CPU `default.qubit` 和解析期望值；有限 shots 只作为后续扰动评估接口。`tests/` 使用一个明确标注的合成 fixture，它既不是生物连接组，也不是市场验证数据。

当前可用的本地端到端命令是 `python -m scripts.quickstart`。它先检查官方 MaleCNS 数据文件和基础 Python 依赖，再使用 4,096 个排序注释 segment 和权重表前 10,000,000 行，结合缓存的 FRED 2024 S&P 500 指数输入，输出经典基线、连接组路径、可选的 4-qubit PennyLane 分数和资源 receipt 到 `outputs/local-research-run.json`。如果没有安装 `pennylane` extra，receipt 会明确记录 quantum outputs unavailable，同时仍保存经典/连接组结果。这是有边界的 smoke test，不是全脑运行或金融验证。使用 `python -m scripts.quickstart --check` 可只检查前置条件。

上游设计审查固定在 `stonkfly` 和 `flycoinrh` 的具体 revision，采取选择性设计复用，不导入整个仓库。钱包、代币发行、浏览器、语音、直播、经纪和完整连接组运行时均不在当前范围。

已从 Janelia 官方 MaleCNS v1.0 来源下载完整 segment-to-segment connection-weight graph、神经元注释和每神经元神经递质预测。原始 Feather 文件位于 gitignored 的 `data/malecns-v1.0/raw/`，校验、schema 和行数见数据接收凭证。当前下载不等于已接入模拟器，也不等于已完成生物动力学或市场验证。

项目计划开放模拟引擎、接口和评估工具，让社区自愿运行可复现实验、比较基线和消融，并分享带设置和数据来源的正面或负面结果。维护者单独承担个人策略开发与交易。个人策略、专有数据和执行系统可保持私有；具体软件许可证和贡献条款尚未选择，详见[开放协作边界](docs/OPEN_COLLABORATION.md)。

仓库现在有一个 transport-neutral 的本地消息协议和可重启多 Fly loop，用于 bounded synthetic fixture plumbing 与白名单研究请求。协议把数值核心、状态记忆、消息适配器和 executor 分开；LeanRouter 只作为候选模型 API 顾问，不等同于执行运行时。外部聊天桥接、通用执行器和真实连接组多成员评估仍未实现。LeanRouter 已有一次带 receipt 的 bounded live success，但此前的 timeout 和 provider failure 也仍存在，因此不能把这次成功理解为长期稳定性或普遍可用性证明。

当前最小 CLI 可运行：`python -m scripts.fly_chat "当前评估是什么，缺少什么证据？"`。它从持久化研究 receipt 生成结构化答复，也支持 `research 官方 connectome source` 触发唯一白名单的 Janelia 只读请求。`scripts.run_fly_loop` 提供 bounded 多 Fly state/message smoke，包含 scoped human question 和 peer signal API。消息 trace 默认写入 `outputs/fly-conversation.jsonl`。LeanRouter 当前已确认路由存在，但 live model probes 返回 provider failure、timeout 或 HTTP 500，因此不会静默伪造模型答复或降级为模型成功。

结构比较可用 `python -m scripts.run_structure_comparison --max-nodes 4096 --max-source-edges 10000000 --seeds 0 1 2` 运行，比较 single Fly、three-member mean、独立 coordinator state 和 no-graph ablation。它只产生 bounded 研究 receipt，不做 promotion 或盈利结论。

## 项目状态

### 当前真正可用的能力

当前项目可作为可复现的研究原型使用：可以重跑有界的 MaleCNS 数据扫描与子图研究、因果回测、结构对照、可选的 PennyLane 评分、本地持久消息与多 Fly fixture loop，以及带 request ID 和资源快照的 LeanRouter smoke 调用。每项能力都应以对应 receipt、命令和限制说明为准。

### 仍未建立的主张

本项目尚未证明它是运营上可靠的软件，也尚未证明模型质量、成本表现、通用工具执行、完整全脑 materialization、量子优势、盈利能力或 production readiness。它不是投资建议，回测和研究 receipt 也不构成投资建议。已完成的 [GOAL.md](GOAL.md) 只表示本轮有界研究目标的 acceptance 已由当前证据满足，不是对长期稳定性、普遍模型可用性或投资有效性的承诺。

当前没有为了制造路线图而创建后续 active goal。若要主张运营可靠性、投资有效性或 production readiness，应先由 Steward 单独定义一个更小、可独立验证的新 goal，并为其指定相应的运行、失败恢复、质量、成本和时间外样本证据。
