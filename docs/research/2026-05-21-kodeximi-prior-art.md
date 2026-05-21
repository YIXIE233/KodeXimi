# 2026-05-21 KodeXimi 参考项目与可借鉴内容

本文件只保留 KodeXimi 相关参考。模型路由相关论文、项目和搜索结果已经拆到独立私有仓库 `step-level-harness-routing-notes`。

## Codex / Codex CLI

参考：<https://github.com/openai/codex>

KodeXimi 借鉴点：

- Codex 作为用户入口、controller、reviewer。
- Codex 适合理解需求、定义边界、做最终验收和向用户解释。
- KodeXimi v0.1 不改 Codex 内部 loop，只通过本地 CLI 接入。

## Kimi CLI

参考：<https://github.com/MoonshotAI/kimi-cli>

KodeXimi 借鉴点：

- Kimi CLI 作为 external worker harness。
- 使用 system `kimi --wire` 获取 ToolCall、StatusUpdate、Approval 等事件。
- 使用 `--agent-file` 定义 worker 身份。
- 使用受控 `--skills-dir` 降低 skill 污染，但不把它当完整隔离。

## Kimi command docs

参考：<https://moonshotai.github.io/kimi-cli/en/reference/kimi-command.html>

KodeXimi 借鉴点：

- `--wire` 作为 v0.1 production transport。
- `--print` / `--quiet` 因自动审批语义，不作为自动 fallback。
- `--agent-file` 和 `--skills-dir` 是 worker profile 的基础。

## Kimi Agent SDK

参考：<https://github.com/MoonshotAI/kimi-agent-sdk>

此前本地验证结论：PyPI SDK 0.0.5 绑定较旧的 `kimi-cli` 1.12.x / Wire 1.3，而本机 system Kimi 是 1.44.x / Wire 1.10。SDK API 更顺手，但 runtime 能力落后。

KodeXimi 决策：

- v0.1 不以 SDKTransport 作为生产默认。
- 后续可重新验证 SDK 是否追平 system Kimi。

## Kimi Agent Rust / kimi-agent-rs

参考：<https://github.com/MoonshotAI/kimi-agent-rs>

借鉴点：

- 说明 Wire 是 Kimi 生态中可见的协议层。
- 也提示协议兼容需要跟随 Kimi CLI 真实行为。
- KodeXimi 应加 WorkerEvent adapter，避免业务层直接依赖 raw Wire 字段。

## kimi-plugin-cc

多轮审稿中反复提到的参考项目。它的可借鉴模块包括：

- Wire client。
- Approval dispatcher。
- Job lifecycle。
- SQLite / event log。
- one process per job。
- cancel / timeout / orphan handling。

KodeXimi 不应直接照搬整体架构，因为它面向 Claude-first/plugin 生态，而 KodeXimi 是 Codex-first、Evidence-first。

## codex-plugin-cc / cc-plugin-codex 类项目

可借鉴点：

- delegate/status/result/cancel/review 类生命周期。
- 主 harness 委托外部 worker 后需要显式 result/review gate。
- 完整产品版需要 Codex plugin/tool，而 v0.1 可 CLI-first。

## Claude Code subagents / Roo Boomerang / Aider Architect Mode

这些项目或功能说明 block-level delegation、主模型/子任务、强模型规划/次模型执行已经有产品实践。

对 KodeXimi 的借鉴：

- 委托应是 bounded block，不应被 controller 微观遥控。
- 子任务/worker 应隔离上下文，只返回压缩结果。
- 但 KodeXimi 不做多 agent 团队，也不做平等桥梁。

## ReWOO / LLMCompiler / LangGraph / OpenAI Agents SDK

这些属于更通用的 workflow、trace、handoff 或 tool DAG 参考。

对 KodeXimi 的借鉴限于：

- 分离 planner/worker/solver 的价值。
- trace 和 usage 对判断成本收益的重要性。
- 工具调用和依赖未来可图式化。

但这些不进入 v0.1 主线。

