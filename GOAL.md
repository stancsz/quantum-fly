# ACTIVE GOAL: 修复研究证据完整性与本地可复现性

Status: active
Owner: Steward contract plus Builder execution record in this file
Opened: 2026-09-11

## Outcome

把 Quantum Fly 从“仅在当前机器上可运行的有界原型”推进到“可由独立使用者从受控输入重建并审计结果的本地研究基线”。本目标优先修复会改变实验结论或破坏证据链的问题，不建立投资有效性、量子优势或 production readiness 主张。

## Why

独立审查确认现有 20 项测试通过、Python 模块可编译、当前机器的 quickstart 前置条件满足，但仍存在四类关键缺口：交易成本计算与换手语义不一致；缓存数据的来源和下载时间可能被错误标注；Git、ship gate 与 ignored receipts 无法形成可移植的证据链；实验对照和 runtime 防护不足。若不先修复这些问题，继续扩大模型、连接组或 agent 数量只会放大不可审计结果。

## Source of truth

- [README.md](README.md)
- [docs/EXPERIMENT_PLAN.md](docs/EXPERIMENT_PLAN.md)
- [docs/DATA_RECEIPT.md](docs/DATA_RECEIPT.md)
- [docs/RESEARCH_BOUNDARY.md](docs/RESEARCH_BOUNDARY.md)
- [docs/AGENT_PROTOCOL.md](docs/AGENT_PROTOCOL.md)
- [quantum_fly/backtest.py](quantum_fly/backtest.py)
- [quantum_fly/market.py](quantum_fly/market.py)
- [quantum_fly/connectome.py](quantum_fly/connectome.py)
- [quantum_fly/agent.py](quantum_fly/agent.py)
- [scripts/quickstart.py](scripts/quickstart.py)
- [scripts/ship_gate.py](scripts/ship_gate.py)

## Steward-owned contract

### Acceptance criteria

以下项目只有在代码、自动测试和对应运行证据同时存在时才能勾选。不得用文档声明替代实际验证。

- [ ] 回测成本改为按实际持仓变化计算，明确首期建仓、换仓和退出的成本规则；learning reward、PnL、turnover 使用同一持仓语义。新增数值回归测试，至少覆盖恒定持仓不重复收费、反向换仓、零持仓和 validation/test 冻结。
- [ ] FRED cache 与实际请求 URL、日期范围、内容 SHA256、首次下载时间和验证时间绑定。已有 cache 与请求不匹配时必须明确失败或重新获取，不得把读取时间写成下载时间。新增完全离线的 stale-cache、URL mismatch、损坏内容和缺失列测试。
- [ ] MaleCNS 数据准备有可重跑的获取或导入流程及机器可读 manifest。quickstart 在运行前验证精确文件名、大小、SHA256 和必需 schema；缺失、重复匹配、错误版本或损坏文件产生明确错误。不得把“文件存在”当作数据完整性证明。
- [ ] 独立使用者可在干净环境按文档完成安装、获取或验证数据、运行最小 bounded 实验并生成 receipt。验证记录解释哪些输入可公开重建、哪些本地文件因大小或许可不进入 Git，以及如何核对生成结果，不能依赖未说明的本机历史状态。
- [ ] 建立真实 Git 基线，使源代码、测试、文档和 verifier 可追踪；`.mochu/VERIFIER_BASELINE` 指向存在的 commit。ship gate 不在未明确请求时覆盖 canonical research receipts，验证器生成临时输出时使用隔离目录并清理锁。提交、推送和公开发布仍需用户明确授权。
- [ ] 可复现环境明确 Python 版本、核心依赖和 quantum extra 的解析版本。CI 或等价 clean-environment 验证覆盖安装、20 项以上现有测试、quantum extra 路径、compile/import 和 quickstart 的无数据失败路径。`pip check` 只能作为辅助证据。
- [ ] 结构与模型比较加入至少一个强且透明的经典基线，并预先定义选择规则。报告多时期或多资产结果、seed 分布、置信区间或其他明确不确定性估计；连接组最低 ID 子集不得被描述为代表性样本。负结果必须保留。
- [ ] runtime 对 `max_seconds`、queue size、payload/state 大小和非有限数值执行显式边界验证。JSONL append、dedupe、queue 和 task state 在并发访问下有一致性测试；非协作 executor 超时后仍可能继续运行的限制必须在 API 与文档中保持可见。
- [ ] loader 和数值边界拒绝不明确输入：缺失或重复 Feather 文件、非有限 graph weight/state、错误持久化 schema 和超限 JSON 均有明确失败测试，不泄漏不必要的本地路径或凭据内容。
- [ ] 项目元数据达到可共享研究代码的最低标准：选择软件许可证，补充安装与平台说明、CLI entry point、依赖更新策略和安全报告边界。若尚未决定许可证，则不得声称仓库可公开复用或开放协作已经就绪。
- [ ] 独立完成一次 fresh verification，把每项已勾选 acceptance 映射到具体命令和非 ignored 的摘要证据。最终 assessment 必须分别给出 local research、public reproducibility、unattended runtime、investment claims 和 production use 的 go/no-go，不得用单一“完成”覆盖不同能力层级。

### Constraints / invariants

- 保留原 completed goal 的历史记录，不回写或弱化其当时的 acceptance 含义；本目标只建立新的证据层级。
- 所有 market feature、reward、position 和 cost 必须保持时间因果；validation/test 不参与训练、调参或阈值选择。
- receipt 必须区分 observed、derived、assumed 和 unavailable，并记录代码 revision、输入 hash、配置、随机种子、时间切分和运行环境。
- 数据、网页、模型输出、缓存和持久化 state 都是不可信输入。无 live brokerage、账户、凭据、订单、公开发帖或任意命令执行。
- LeanRouter 仍只作为可选模型 API 顾问。一次成功调用不能证明长期可靠性、模型质量或成本优势。
- 保持 bounded、CLI-first 和可审计。不要引入 dashboard、通用 agent framework 或与验收无关的基础设施。
- 保护 dirty worktree 和 repository boundary。只修改当前目标授权的文件；不得使用 `git add -A`。commit、push、deployment、publication 和 destructive data replacement 需要用户明确授权。

### Non-goals

- 不证明盈利能力、投资建议价值、量子优势、真实生物动力学或完整全脑可执行性。
- 不接入券商、交易账户、实盘订单、资金或私有策略。
- 不通过增加 Fly 数量、量子比特、数据规模或模型复杂度来替代正确性与复现性修复。
- 不要求在本目标内建立公共云服务、GUI 或通用 Codex/Claude executor。

### Escalation conditions

- 软件许可证、公开数据再分发方式或是否创建首个 Git commit 需要用户作产品或法律选择。
- 验证流程需要外部账号、付费 API、受限数据、公开发布或不可逆动作。
- 正确成本语义与预期研究协议存在无法从现有文档消解的冲突。
- fresh reproduction 所需资源超过当前明确的 bounded 预算，且无法用更小 fixture 保留验收意义。

## Builder-owned execution record

### Current approach

按证据风险排序执行：先修复交易成本和 cache provenance，再建立数据 manifest 与 clean reproduction，随后修复 Git/verifier 基线和 runtime 输入边界，最后扩展统计对照与共享元数据。每个切片先增加会失败的针对性测试，再实现并生成隔离 receipt。

### Current progress

- [ ] 修复 turnover-based cost 与一致的 reward/PnL 语义。
- [ ] 修复 cache provenance 和离线数据完整性测试。
- [ ] 增加 MaleCNS manifest、校验和可重跑数据准备流程。
- [ ] 建立 clean install、clean input 和 receipt reproduction 验证。
- [ ] 建立可用 Git/verifier baseline，并让 ship gate 保持验证隔离。
- [ ] 固定环境并覆盖 optional quantum 路径。
- [ ] 增加更强基线、不确定性报告和更广时间/资产证据。
- [ ] 加固 runtime 并发、预算与持久化输入边界。
- [ ] 完成许可证、CLI 和共享文档决策。
- [ ] 独立执行最终 acceptance mapping。

### Validation baseline

2026-09-11 独立审查观察到：`.venv\Scripts\python.exe -m pytest -q` 为 20 passed，`compileall` 通过，`python -m scripts.quickstart --check` 通过，`pip check` 报告无 broken requirements。这些结果只证明当前机器上的基础实现可运行，不满足上述新 acceptance。

### Discoveries

- `quantum_fly/backtest.py` 当前按 `costs * abs(signal)` 每期收费，而同一比较另外计算 position turnover；成本、reward 与 turnover 语义尚未对齐。
- `quantum_fly/market.py` 在 cache 已存在时仍使用调用方传入 URL 和当前时间生成 provenance，无法证明缓存实际来源与首次下载时间。
- 当前 branch `mochu/docs-quickstart` 尚无 commit，所有项目文件均为 untracked；`.mochu/VERIFIER_BASELINE` 不存在，现有 ship gate 无法建立 verifier tamper baseline。
- `data/` 与 `outputs/` 被 gitignore，但当前 quickstart 只检查三个文件是否存在和基础 import；fresh clone 无法仅依靠版本化仓库重建现有 acceptance evidence。
- runtime 的 queue、dedupe 和 JSONL append 没有并发一致性保护；executor deadline 来自 payload，缺少 finite positive 上界验证。
- 当前实验仍限于一个 S&P 500 proxy、最低排序 segment 子集、少量 seeds 和较弱 no-graph 对照，不足以支持结构或模型选择。

### Runtime evidence

- 当前本地测试基线：20 passed in 6.42s。
- 当前项目 venv：NumPy 2.5.3、PyArrow 25.0.1、pytest 9.1.1；`pip check` 通过。
- 已有 ignored receipts 可作为历史输入核对，但在被重新生成并绑定 Git revision 前，不作为本 active goal 的可移植完成证据。

### Remaining gap

上述 acceptance criteria 均未完成。下一步从 transaction-cost 数值回归测试和 cache provenance 离线测试开始，不先扩大模型、数据或 agent 规模。

---

# COMPLETED GOAL: 可验证的会说话多 Fly 研究循环

Status: complete
Owner: Steward contract plus Builder execution record in this file
Last reviewed: 2026-09-11

## Outcome

把量子果蝇发展为一个可扩展的研究 agent：Fly 用实际连接组启发的数值核心和持久状态提出有证据的判断，能够与人类、其他 Fly、协调器、研究执行器和模型顾问双向通信，并通过时间正确的实验持续产生可复现的正面或负面研究证据。

本目标允许从一个 Fly、较少成员或简单聚合开始。三 specialist 加 coordinator 是候选架构，不是固定 agent 数量。目标是证明可扩展的研究循环，不是证明某个成员数量、queen 隐喻、连接图或量子步骤有效。

## Capability boundary

本目标完成后，当前真正可用的层级是“可复现的研究原型”：有界的 MaleCNS 扫描与子图研究、因果回测和结构对照、可选 PennyLane 评分、本地持久消息与多 Fly fixture loop，以及带 receipt 的 LeanRouter smoke 调用，都可以按命令、测试和 runtime receipt 重跑。完成本 GOAL 不等于这些路径已经成为运营服务。

以下主张仍未建立：运营上可靠的软件、长期稳定性、模型质量或成本优势、通用工具执行、完整全脑 materialization、量子优势、盈利能力和 production readiness。研究 receipt、回测或一次成功的模型调用都不是投资建议，也不证明投资有效性。若要建立其中任何更强的主张，必须由 Steward 先定义一个独立、较小且有对应运行证据的新 goal；不得通过改写本 GOAL 的完成含义来覆盖这些缺口。

## Why

当前仓库已有真实 MaleCNS 数据、稀疏图路径、市场 proxy、PennyLane smoke test、有限 paper backtest 和本地 typed CLI，但这些仍是分离的演示。需要把模型推理、只读研究工具、证据 trace、人类可读答复和可复现实验连接起来，同时保留私人策略与公开研究核心的边界。

## Source of truth

- [README.md](README.md)
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- [docs/AGENT_PROTOCOL.md](docs/AGENT_PROTOCOL.md)
- [docs/DATA_RECEIPT.md](docs/DATA_RECEIPT.md)
- [docs/EXPERIMENT_PLAN.md](docs/EXPERIMENT_PLAN.md)
- [docs/HYPOTHESES.md](docs/HYPOTHESES.md)
- [docs/HIVE_MIND.md](docs/HIVE_MIND.md)
- [outputs/local-research-run.json](outputs/local-research-run.json)
- [outputs/fly-conversation.jsonl](outputs/fly-conversation.jsonl)

## Steward-owned contract

### Acceptance criteria

每一项都必须有可复现命令、测试或运行 receipt。复选框只在当前证据满足该项边界时勾选，剩余项目保持未完成。

- [x] LeanRouter 实际模型调用已成功完成，且 receipt 记录模型、请求、响应、延迟、错误和资源；默认 `minimax/minimax-m3` 请求在 staging router 返回 HTTP 200 与内容 `READY`，`router_advice` 记录了 request ID、请求体、响应、约 23.568 秒延迟和 process working-set snapshots。此前的 timeout/`provider_unavailable` probes 仍保留为失败证据，不能被成功样本覆盖或解释成普遍稳定性证明。
- [x] 人类可通过 CLI 提问当前 assessment、缺失 evidence 和下一步建议；实际 reply trace 区分 observed、interpretation、hypothesis、as-of 和 limitations，不把模板答复冒充一般模型对话。UI 和一般模型对话仍不在已验证范围。
- [x] 双向协议支持持久 log、message/correlation ID、幂等去重、bounded queue、真实 in-flight timeout、restart/replay 和可验证 cancel；证据限于预注册、协作式的本地 runtime，不能外推到任意外部进程。
- [x] 至少一个明确白名单的只读研究 executor 可真实执行并返回 URL、时间、内容 hash、evidence refs、实际动作和失败状态；当前已验证 Janelia HTTP adapter，Codex/Claude Code adapter 仍未标为可用。
- [x] Fly、Fly-to-Fly、coordinator-to-executor 和 human-to-Fly 路径在本地 bounded runtime 可用：typed peer relay、allowlisted Janelia request 和 scoped human question 均有测试/receipt；没有 advisor、账户、凭据、交易或公开发布权限。
- [x] 运行一个持久 communicating agent loop，而不只是离线 specialist 和 queen 数值函数；synthetic fixture smoke 已证明成员状态、bounded step history、消息和 evidence refs 可重启恢复，真实 MaleCNS 多成员运行仍未证明。
- [x] 真实官方 connectome loader 支持明确的 segment 选择、ID 完整性、稀疏图、neurotransmitter unknowns 和 bounded-memory receipt；完整下载文件已通过 streaming validation receipt 证明可逐批扫描，记录 151,856,684 rows、0 invalid endpoints、约 1.24 GB peak Windows working set、约 1.25 MB Python allocation peak、1.311 秒和 0 scan failures。没有把 streaming scan 称为 whole-brain graph materialization。
- [x] reward/readout 更新在严格因果的训练段发生，验证和 test 冻结；receipt 记录成本、engineering credit 规则和负面结果。当前是简化 compact readout 工程规则，没有生物学或 trading efficacy 证明。
- [x] 历史评估已扩展到 2022-2025 FRED S&P 500 proxy 的四个 chronological walk-forward folds、seeds 0/1/2、现有因果 leakage test，以及 train-only exposure-matched structure controls、成本、turnover、drawdown 和 resource receipts；仍不是多资产或 trading efficacy 证明。
- [x] 在选择 agent 数量与 coordinator 结构前，已用同一 bounded 2024 history、三 seeds 比较单 Fly、三个独立 Fly/simple mean、独立 coordinator state 和 no-graph mean ablation，并记录质量、相关输出、资源和风险；结果不构成 3+1 或 queen 有益证明。
- [x] PennyLane 4-qubit analytic/finite-shot 路径与经典协调器现在使用相同四值 connectome input，并记录 held-out paired outputs、analytic/finite-shot outputs、wall time 和 Python allocation receipt；没有宣称 quantum advantage 或 speedup。
- [x] 结果可诚实接受负实验：system-Python quantum unavailability、mixed walk-forward/structure results 和 LeanRouter `provider_unavailable` 均保留为失败或限制 receipt；没有用 mock 取代真实 integration，也没有宣称盈利、量子优势、稳定策略、完整生物 fidelity 或临床/生产能力。
- [x] 当前公开研究边界符合 [docs/OPEN_COLLABORATION.md](docs/OPEN_COLLABORATION.md)：仓库不公开发布，`data/` 与 `outputs/` 保持 gitignored，个人策略、专有数据和执行系统明确可私有；软件许可证和贡献条款仍未选择，按本目标 non-goal 保持开放。

### Constraints / invariants

- LeanRouter 只负责模型 API 调用；Codex、Claude Code 或其他 runtime 才能作为 executor。不得把 `http://127.0.0.1:4000/` 当作 Quantum Fly UI，且其 API/path/auth/model compatibility 必须实测。
- 共享 immutable graph 可以复用，动态 state 和 learning history 默认独立。模块数量可配置，不能为满足隐喻而增加 agent。
- 连接组 contact-count weight、transmitter sign 和 dynamics choice 必须分开记录。segment 行数不能称 neuron count。不得为“生物 fidelity”或“queen consciousness”制造证据。
- 所有 market input 按时间因果处理，评估使用 train/validation/test 或 walk-forward。任何 reward 只能在结果发生后进入训练状态，held-out evaluation 冻结。
- 工具请求必须有 scope、budget、deadline、evidence refs 和实际动作记录。无 live brokerage、账户、凭据、订单、公开发帖或后台挖掘。
- 研究数据、模型输出和工具文本都是不可信输入。LLM 不能直接执行任意命令或授予权限。API spend、内存、时间和队列必须有界。
- 保持 lean。不要引入通用 agent framework、dashboard、治理 bureaucracy 或不支持目标的抽象。
- 数据 CC-BY、上游 MIT attribution 和未来软件许可证彼此分开处理。保留 dirty worktree，不 commit、push 或 publication，除非另有明确授权。

### Non-goals

- 不把量子果蝇变成保证盈利的交易系统，也不建立 live brokerage 或自动交易账户集成。实盘是另一个需要明确授权的目标。
- 不要求意识、主观体验、自传式 thought 或真实果蝇社会 hive mind。
- 不要求完整生物动力学、完整 connectome 一次性适配硬件，或把 anatomical wiring 直接当作 trained weights。
- 不把社区贡献者的时间或计算用于维护者私人交易策略；公开协作只服务于可复现研究假设和证据。
- 不在本目标内选择最终软件许可证、贡献协议或商业模式。

### Escalation conditions

- LeanRouter 需要缺失的账号、模型选择、权限或外部配置，且现有安全机制无法证明兼容性。
- 真实 executor 需要超出白名单范围的访问、凭据、外部发布、账户或不可逆动作。
- 目标要求改变上述 acceptance、non-goal、数据许可或公开策略边界。
- 全图或多 agent 运行的资源风险超过已测预算，且无法通过有界子集或更小 agent 数量保留可验证结果。

## Builder-owned execution record

### Current approach

先保留已经通过的单网络真实子集和本地 CLI，再逐步把协议、router、executor、持久状态和多成员实验接通。优先使用显式模板与结构化 trace，模型顾问只有在真实可用时才加入语言生成。

### Current progress

- [x] 官方 MaleCNS v1.0 三个 Feather 文件下载、大小、SHA256、schema 和行数 receipt。
- [x] 稀疏 4,096 segment / 前 10M weight-row 本地研究 run，输出持久化。
- [x] FRED 2024 S&P 500 proxy 的因果特征、训练/validation/test paper backtest、成本和独立状态 prototype。
- [x] PennyLane 4-qubit analytic 与 finite-shot smoke。
- [x] Mermaid 候选架构和双向协议文档。
- [x] 本地 CLI assessment、Janelia 白名单只读 research request、JSONL trace、correlation、dedupe、显式 cancel。
- [x] 本地 allowlisted research lifecycle 的 bounded FIFO、持久 pending replay、协作式 in-flight timeout 和 pending cancel；这些只证明受控本地 runtime，不证明外部 executor 或不可协作进程可被强制终止。
- [x] 一个可重启的本地 communicating Fly loop smoke：三个成员共享 immutable fixture graph、各自持有 state/readout，通过 bounded typed messages 发送信号给 coordinator，并持久化 step history 和 evidence refs；这不是实际 MaleCNS 全图或市场有效性证明。
- [x] bounded backtest receipt 显式记录 next-return credit、成本、观测滞后、训练 cutoff 和 validation/test readout frozen；仍不是多时期、多 seed 或交易 efficacy 证明。
- [x] bounded structure comparison receipt 覆盖 single/three-mean/three-coordinator/no-graph、seeds 0/1/2、validation/test metrics、turnover、drawdown、member correlation/disagreement 和 tracemalloc timing；仍只有一个 2024 proxy period。
- [x] rolling walk-forward receipt 覆盖 2022-2025 的 1,003 valid closes、4 folds、三个 seeds 和 train-only exposure normalization；仍明确限制为一个 S&P 500 index proxy。
- [x] PennyLane project-venv receipt covers analytic, 1,000-shot finite-shot, held-out analytic and classical paired outputs on the same connectome signal boundary, with timing and resource fields; no speedup claim.
- [x] LeanRouter adapter now records selected model, request ID/body, timeout, response or error, latency and process working-set snapshots; default `minimax/minimax-m3` live success is captured in `outputs/leanrouter-default-probe.json`, while prior failures remain recorded.
- [x] full official weight-file streaming validation receipt covers every downloaded row without retaining a whole graph; the graph-construction boundary remains bounded at 4,096 selected segments/10M scanned rows.
- [x] human assessment CLI receipt 显式返回 observed、interpretation、hypothesis、as-of、missing evidence、limitations 和 proposed next action；这不是一般模型对话或 UI proof。
- [x] local message paths now include scoped human-to-Fly questions, bounded Fly-to-Fly peer signals, coordinator-to-allowlisted-executor requests and structured human assessment; peer APIs expose no arbitrary command or permission field.
- [x] 本 GOAL 的 acceptance criteria 已全部由当前 receipts、测试和 live probes 证明；Status 可进入完成审计。

### Discoveries and decisions

- LeanRouter root、models 和 chat route 可达，但两个列出的模型 smoke call 都返回 `provider_unavailable`，不能据此宣称模型集成成功；root cause 保留给 owning task 只读诊断。
- 2026-09-11 fresh request-correlated probes using `openrouter/minimax/minimax-m3` and `gpt-6-astra` each timed out at about 10 seconds despite root/models staying healthy; this is additional failure evidence, not a root-cause conclusion.
- 2026-09-11 extended 45-second staging probe (`outputs/leanrouter-long-probe.json`) reached all three advertised/configured model IDs and received HTTP 503 `provider_unavailable` after 15.341-21.469 seconds; the response explicitly reported `slider_allocated=false`. No model response was generated, so the LeanRouter acceptance remains open.
- 2026-09-11 follow-up staging probe using the configured default `minimax/minimax-m3` and the project `router_advice` adapter returned HTTP 200 with served model `minimax/minimax-m3`, assistant content `READY`, request ID correlation, 23.568-second latency, and before/after process working-set values; this proves one bounded live model call, not general provider reliability.
- Advertised alternate route probes did not provide a working fallback: `/v1/responses` returned HTTP 500 in 0.067 seconds and `/v1/messages` timed out after 10.004 seconds for `minimax/minimax-m3`.
- 只读诊断显示 router 在线且 routing config 为 base `openrouter/minimax/minimax-m3`、frontier_percent=0、gemini_percent=0。原始 Fly 失败请求没有 request correlation；其他日志中的 `expert_no_phase` 或大上下文 `ContextBudgetExceeded` 不能套用为本次小请求的根因。adapter 已改为默认使用 API advertised ID `minimax/minimax-m3`，并允许 `QUANTUM_FLY_ROUTER_MODEL` 或显式 model 覆盖；三个 IDs 仍需 live success proof。
- 当前唯一真实 executor 是 Janelia 官方页白名单 HTTP adapter。Codex/Claude Code CLI 存在于本机，但其作为项目 executor 尚未建立受控、可复现的集成路径。
- 当前 run 的 S&P 500 index 是 proxy，不是 SPY ETF，也不是投资有效性证据。
- 当前 queen test 结果未改善简单 baseline，agent 数量和 coordinator 结构必须由匹配预算的边际实验决定。
- Python `tracemalloc` 不是整个进程的峰值内存，当前 resource receipt 明确只称 Python allocation peak；未来 resource receipt 必须区分整个进程峰值。
- Python 线程不能安全强制杀死；runtime 在 deadline 时先持久化 `timed_out` 并触发 cooperative cancel，executor 必须在安全边界检查 context。此行为有单元测试，不能外推为任意外部 runtime 的 cancel 证明。
- communicating loop 的首个 receipt 使用明确标注的 synthetic fixture graph；它证明 restart/state/message plumbing，不把 fixture 结果升级成 connectome 或 trading evidence。
- 本次真实数据 rerun 在 PennyLane 未安装时先前会中止；脚本已改为继续保存 classical/connectome/backtest receipt，并将 analytic 与 held-out quantum outputs 记录为 `unavailable`。这保留了负环境证据，不满足 quantum comparison acceptance。
- backtest 的 `engineering_credit` 与 `rewards` 现在显式相等，并记录 `credit_observed_at=t+1` 和 `validation_and_test_readout_frozen=true`；这加强因果审计，但不替代 walk-forward 和多时期验证。
- structure comparison 的 4,096-segment receipt 显示单 Fly、mean、coordinator 和 no-graph 的结果不同且 seed 间有差异；没有自动 promotion，保留 mixed/negative evidence。
- full scan receipt initially reported no process peak because the Windows API handle was not typed correctly; fixed the process-handle typing and reran, obtaining a 1,242,943,488-byte peak working set. Python tracemalloc remains a separate allocation metric.
- walk-forward folds use a 20-close causal warmup and derive exposure matching scales only from each fold's training records; validation/test never determine the scale.
- The system Python lacks PennyLane, while the repository `.venv` has the optional extra; quantum verification therefore uses `.venv\Scripts\python.exe` and records the interpreter boundary rather than treating a skipped system test as quantum evidence.
- Negative-result handling is explicit: unavailable dependencies and mixed/negative comparisons stay in receipts and limitations, while no result is promoted to profitability, quantum advantage, or biological fidelity.
- Boundary review confirms `docs/OPEN_COLLABORATION.md`, `.gitignore`, and current receipts keep public research, CC-BY source attribution, private strategy data, and execution systems separate; there is no publication or upload mechanism in this repository.
- assessment envelope 曾只从顶层 payload 读取 `as_of_time`，导致 structured observed as-of 未传播到协议 envelope；已改为从 payload 或 observed 读取，并由 test 与 CLI receipt 验证。
- peer relay and human question APIs intentionally accept only bounded typed fields; command-like content can remain untrusted text/evidence labels but has no execution field or dispatch path.

### Validation baseline

历史验证基线为 `python -m pytest -q` 的 11 passed，以及项目此前的 7 passed 和 4 passed 记录。这些是当前代码快照的基线，不代表本 GOAL 完成，也不代表全系统 integration。最近 CLI 运行实际成功的是模板/trace assessment 和 Janelia 白名单 research；LeanRouter 实际模型调用失败并已如实记录。

2026-09-11 最新验证：`python -m pytest -q` 为 15 passed, 1 skipped（PennyLane 未安装时的可选 extra）；`python -m scripts.fly_chat "请研究官方 connectome source" --trace outputs/goal-protocol-smoke.jsonl` 返回 allowlisted Janelia `task_result`，44,208 bytes，SHA256 `51144922891ccdc5da2490d55b39ef69222134ed6944bbff2766379e403ad3c`。新增 protocol tests 覆盖 bounded queue、restart pending replay、specific-task execution、cooperative in-flight timeout、pending cancel 和 loop restart/state restoration。
2026-09-11 最新验证：system Python `python -m pytest -q` 为 19 passed, 1 skipped，project venv `.venv\Scripts\python.exe -m pytest -q` 为 20 passed；`python -m scripts.fly_chat "当前评估是什么，缺少什么证据？" --trace outputs/goal-assessment-smoke-2.jsonl` 返回带顶层 `as_of_time=2024-12-31` 的结构化 assessment，包含 hypothesis、limitations 和 proposed next action。`python -m scripts.fly_chat "请研究官方 connectome source" --trace outputs/goal-protocol-smoke.jsonl` 返回 allowlisted Janelia `task_result`，44,208 bytes，SHA256 `51144922891ccdc5da2490d55b39ef69222134ed6944bbff2766379e403ad3c`。新增 protocol tests 覆盖 bounded queue、restart pending replay、specific-task execution、cooperative in-flight timeout、pending cancel、loop restart/state restoration、Fly-to-Fly relay 和 human-to-Fly question。

同日真实数据 rerun：project venv `.venv\Scripts\python.exe -m scripts.run_local_research` 成功退出，约 44.429 秒，4,096 selected segments，扫描 10,000,000 weight rows，160,053 retained edges，ID integrity 全部为 true，Python tracemalloc peak 约 108 MB；receipt 包含 analytic、1,000-shot finite-shot、held-out paired quantum/classical outputs、输入相同边界和 timings。`python -m scripts.run_structure_comparison --max-nodes 4096 --max-source-edges 10000000 --seeds 0 1 2 --output outputs/structure-comparison.json` 成功退出，报告四种结构、三 seeds、validation/test metrics、资源和 mixed results，结构比较约 5.646 秒，Python tracemalloc peak `3930165` bytes。

同一日期的 loop 验证：连续运行 `scripts.run_fly_loop` 的 2024-01-02 与 2024-01-03 steps 后，第二次从 `outputs/goal-fly-loop-state.json` 恢复为 step 2，并返回三个独立 member signals、coordinator aggregate、interpretation、hypothesis、limitations 和 `quantum_fly/fixture.py` evidence ref。restart/state restoration 由 `test_communicating_loop_persists_independent_members_and_restarts` 覆盖。

### Runtime evidence

- `outputs/local-research-run.json`：project-venv 最新约 44.429 秒、4,096 segments、前 10M weight rows、160,053 edges、ID integrity、2024 FRED history、backtest metrics、causal learning receipt 和 paired PennyLane/classical coordinator comparison；不包含 quantum advantage claim。
- `outputs/fly-conversation.jsonl`：human question 到 coordinator task result，以及 coordinator 到 allowlisted Janelia executor 的 correlation chain。
- Janelia research receipt：官方页面 44,208 bytes，SHA256 `51144922891ccdc5da2490d55b39ef69222134ed6944bbff2766379e403ad3c`。
- LeanRouter probe：`GET /` 和 `GET /v1/models` 成功；`POST /v1/chat/completions` 返回 `provider_unavailable`，未成功生成模型答复。
- LeanRouter success receipt：`outputs/leanrouter-default-probe.json` used the configured default `minimax/minimax-m3` through `FlyCoordinator.router_advice`; it returned HTTP 200, served model `minimax/minimax-m3`, assistant content `READY`, request ID `req-47a05ea2993e4d409d1d6d7a8ba56087`, 23.568 seconds latency, and before/after working-set snapshots. This is one bounded live success, not a stability or production-readiness claim.
- Fresh `outputs/leanrouter-goal-probe.json` receipt: all three `POST /v1/chat/completions` calls with explicit request IDs timed out at 10.026, 10.006 and 10.019 seconds for `gpt-6-astra`, advertised `minimax/minimax-m3`, and configured alias `openrouter/minimax/minimax-m3`; no model response was generated. The probe records request bodies, errors, 30.052-second wall time and process working-set snapshots.
- Alternate live route evidence: `POST /v1/responses` returned HTTP 500 in 0.067 seconds, while `POST /v1/messages` timed out in 10.004 seconds. Neither generated a model response.
- `outputs/goal-protocol-smoke.jsonl`：真实 Janelia 请求的 `question -> research_request -> running -> task_result` correlation chain；该临时 receipt 可重跑，不等同于通用 executor integration。
- `outputs/goal-assessment-smoke-2.jsonl`：human assessment 的结构化 reply trace，包含 as-of、观察、解释、假设、限制、缺失 evidence 和 next action。
- `outputs/goal-fly-loop.jsonl` 与 `outputs/goal-fly-loop-state.json`：两步 synthetic fixture loop 的 member/coordinator trace 和持久 state；用于证明 plumbing，不是 connectome 或 market result。
- `outputs/structure-comparison.json`：4,096-segment/10M-row bounded structure comparison receipt；可用于结构选择前的对照，不是 profitability 或 promotion evidence。
- `outputs/full-connectome-scan.json`：完整 1.05 GB weight Feather streaming validation，151,856,684 rows、0 invalid endpoints、peak working set、Python allocation peak 和 wall time；不是 whole-graph runtime proof。
- `outputs/walk-forward-comparison.json`：2022-2025、1,003 valid closes、4 chronological folds、seeds 0/1/2、four structure classes、raw and train-only exposure-matched metrics；不是 multi-asset validation。
- `outputs/leanrouter-goal-probe.json`：request-correlated three-model LeanRouter failure receipt with model IDs, request bodies, timeout errors, latency and process working-set snapshots; no successful model response.
- `outputs/leanrouter-long-probe.json`: extended staging request-correlated probe for the same three model IDs; all returned HTTP 503 `provider_unavailable` with route reason `standard_routine` and `slider_allocated=false`, including response latency and process working-set snapshots.
- `outputs/leanrouter-default-probe.json`: successful default-model `router_advice` receipt with request ID, request body, HTTP 200 response, served model, `READY` content, latency, timeout, and process working-set snapshots.

### Remaining gap

LeanRouter 成功模型调用现已由 `outputs/leanrouter-default-probe.json` 证明，但应继续把它限定为一个 bounded live sample；不要把一次成功升级成稳定性、质量、成本或生产 readiness 结论。也不要把“可运行模板答复”升级成一般对话、把当前 research adapter 升级成通用 executor，或把 bounded scan/4,096 selection 升级成 whole-brain 结论。
