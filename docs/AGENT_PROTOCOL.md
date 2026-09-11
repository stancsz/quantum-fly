# Fly 双向通信协议

本协议是 transport-neutral 的最小本地实现。它让 Fly 模块能够向人类报告状态、请求研究支持并接收控制，也让多个 Fly、协调器和执行器交换有边界的证据。当前实现提供 CLI、JSONL trace、重复消息去重、bounded FIFO、持久 pending replay、协作式 deadline/cancel、一个可重启的本地多 Fly loop 和一个白名单官方来源 adapter；外部聊天桥接和通用执行器集成仍未实现。

## Agent 的组成

一个 Fly agent 由四部分组成：

1. 数值核心，例如稀疏状态更新和 readout。
2. 状态与任务记忆，保存时间、配置、证据引用和负面发现。
3. 类型化消息适配器，把状态和请求转换成协议消息。
4. 动作与请求生命周期，跟踪 accepted、running、result、failed 和 cancelled。

语言不是连接组本身的能力。消息可由固定模板渲染，也可由可选的 LLM 辅助改写，但必须把 measured state、interpretation 和 hypothesis 分开。不能伪造自传式“想法”、感受或 earned confidence。

## 面向人的可读表达

“会说话的果蝇”在工程上指可读的状态和意图报告，不是读取真实主观意识。每次面向人的简报尽量包含：观察到的信号、当前候选判断、不确定性或模块分歧、缺失证据，以及建议的下一步动作或请求。

例如，在存在明确的缺失数据检测和请求生成规则时，可以生成：“我缺少成交量数据，建议补齐后重新评估。”这里的“我”只是 agent 标签，文本必须由结构化 trace 生成，并能回链到时间、输入和 evidence refs。没有检测规则就不能臆造需求。自然语言回复和问题仍使用同一消息协议，文字转语音只是未来的可选展示 adapter，不在当前范围。

## 消息包络

所有消息只需包含这些字段：

```json
{
  "protocol_version": "fly/0.1",
  "type": "status",
  "message_id": "msg-example-001",
  "correlation_id": null,
  "sender": "trend-fly",
  "recipient": "human:local",
  "event_time": "2026-09-11T16:00:00Z",
  "as_of_time": "2024-12-31T00:00:00Z",
  "payload": {},
  "evidence_refs": ["outputs/local-research-run.json"]
}
```

研究或执行请求可额外带 `budget` 和 `deadline`。`payload` 不应隐式授予权限。消息内容和检索到的网页内容都是不可信数据，不能单独执行任意命令或访问账户。

## 最小消息类型

- `status`：报告状态、资源、已知限制或材料变化。
- `question`：请求人类澄清偏好或研究选择。
- `research_request`：请求执行器或顾问完成有范围的研究。
- `task_result`：返回结果、证据引用、负面发现和资源使用。
- `feedback_control`：显式 `pause`、`resume` 或 `cancel`。
- `ack` 与 `error`：确认接收或报告失败原因。

示例请求只说明协议形状，不代表真实任务或结果：

```json
{
  "protocol_version": "fly/0.1",
  "type": "research_request",
  "message_id": "msg-example-002",
  "correlation_id": "msg-example-001",
  "sender": "queen-candidate",
  "recipient": "executor:local",
  "event_time": "2026-09-11T16:01:00Z",
  "as_of_time": "2024-12-31T00:00:00Z",
  "payload": {"task": "比较固定均值与模块聚合", "scope": "offline"},
  "evidence_refs": [],
  "budget": {"max_seconds": 120, "max_cost_unknown": true},
  "deadline": "2026-09-11T16:05:00Z"
}
```

结果必须说明实际执行了什么：

```json
{
  "protocol_version": "fly/0.1",
  "type": "task_result",
  "message_id": "msg-example-003",
  "correlation_id": "msg-example-002",
  "sender": "executor:local",
  "recipient": "queen-candidate",
  "event_time": "2026-09-11T16:02:00Z",
  "as_of_time": "2024-12-31T00:00:00Z",
  "payload": {"state": "failed", "reason": "illustrative only"},
  "evidence_refs": ["outputs/example-receipt.json"]
}
```

## 通信路径与生命周期

协议支持四条路径：人类 ↔ Fly、Fly ↔ Fly、Fly ↔ coordinator，以及 coordinator ↔ executor/advisor。当前本地 loop 已对前三类和 allowlisted executor 提供 typed 实现。Fly 之间只交换有界的 signal、evidence ref、disagreement 和 request，不共享无限状态。请求流程为 `request -> accepted -> running -> result`，也可以到 `failed` 或 `cancelled`。

实现应有超时、重复消息去重、幂等 message id 和有界队列。当前本地 runtime 对预注册 executor 使用 persisted FIFO；重启后会重放仍为 accepted 的请求。deadline 会立即记录 `timed_out` 并发出 cooperative cancel。Python 无法安全强制终止任意线程，因此 executor 必须在安全边界检查 cancel/deadline context，不能把它描述成对外部 runtime 的强制 kill。相同状态的主动通知应合并或限速。Fly 可以主动报告材料变化、未解决分歧、缺失数据或实验完成，但不应持续闲聊。

人类在项目 UI、CLI 或聊天桥接中的输入，可被路由为 command、preference 或明确 research task。真正的工具执行由 executor 在已分配范围内完成。协议不自动支持实盘交易、公开发帖、账户访问或凭据获取。

## 执行器、顾问与 LeanRouter

Codex、Claude Code 等执行运行时是候选 executor，不假设其接口已经接入。它们负责网页研究、数据获取、代码和实验动作；Fly 只提出范围明确的请求并接收证据化结果。LeanRouter 只负责模型 API 调用，不能被当作执行运行时。`http://127.0.0.1:4000/` 是用户提供的本地推理候选地址，当前未验证 API 路径、认证、协议或兼容性。

数值核心与消息适配器之间应保留 bridge，消息层可选用模板或 LeanRouter 顾问辅助语言表达，但模型输出不能替代证据或权限判断。资源、API spend 和执行范围都应在 request 和 result 中记录。

## 记忆与审计

记忆条目应保存来源、时间、成本、请求动作、实际执行动作、证据引用和负面结果。它们用于复现和纠错，不用于制造人格连续性。传输方式先保持简单的本地 JSON 或事件适配器，外部系统通过独立 adapter 接入，不固定 agent 数量或框架。
