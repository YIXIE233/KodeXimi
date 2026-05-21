# 01. KodeXimi 思考演进

## 1.1 初始动机

最初的问题不是“做一个多 agent 平台”，而是一个很实际的工作流问题：

- Codex 是当前主要入口。
- Codex 适合理解需求、判断边界、最终 review。
- Kimi CLI 适合长上下文执行、批量读写文件、跑命令。
- 但目前二者之间没有稳定的主从协议。

所以最初设想是：

```text
Codex 作为主控
Kimi 作为 worker
中间有一个 runtime 管理任务、证据、状态、usage
```

## 1.2 第一轮偏重安全和兜底

早期讨论很快被带到安全、兜底、Wire/Print fallback、SQLite/JSONL、Post-run gate、sandbox、materialized workspace 等问题。

这不是白费，因为它暴露了很多真实工程风险：

- `--print` / `--quiet` 的自动审批风险。
- Wire 协议稳定性风险。
- ReadFile / Glob 可能不可预审批。
- Kimi 不能修改 `.kodeximi` 控制面。
- VERIFY 不能由 Kimi 自证。
- review accept 需要防止 evidence 漂移。
- direct_project_mode 没有强读隔离。

但后来意识到：如果继续围绕安全兜底转，核心产品逻辑会被掩盖。KodeXimi 的本质不是安全沙盒，而是 Codex-Kimi 的委托执行和证据回收系统。

阶段结论：

```text
安全和边界需要有最低限度，但不能让它们取代主线。
主线是：TaskSpec -> Kimi attempt -> runtime VERIFY/diff/usage -> Codex review。
```

## 1.3 第二轮回到架构和工作流

之后将 KodeXimi 重新定义为：

```text
Codex-first delegated execution runtime
```

核心抽象变成：

- TaskSpec：Codex 定义任务、边界、成功标准。
- Kimi bounded attempt：Kimi 在边界内连续执行。
- Evidence Package：RESULT、VERIFY、diff-summary、usage。
- Review decision：Codex 决定 accepted / rework / failed / blocked。
- Attempt：同一个 logical job 下的多轮返工。

这轮明确了：

- Codex 不能每一步微观遥控 Kimi。
- Kimi 不能做最终验收。
- KodeXimi 不是模型路由系统；它只管理跨 harness 的委托执行。
- usage 第一版就要做。

## 1.4 对审稿意见的吸收

多个审稿模型提出了相似意见，其中最有价值的包括：

### VERIFY 不能由 Kimi 自写

许多审稿意见指出，Kimi 写 `VERIFY.md` 相当于运动员给自己计时。最终设计吸收为：

```text
Kimi 写 RESULT.md；
KodeXimi runtime 根据真实命令生成 VERIFY.md。
```

### Rework 应该是同一 job 多 attempt

早期有 child job 和 same-job attempt 两种方案。最终共识：

```text
用户心智是“一个任务返工了几轮”，不是“一堆任务链”。
因此采用 same-job multiple attempts。
```

### direct_project_mode 不能声称强隔离

最终表述：

```text
direct_project_mode 是 low-isolation convenience mode。
ReadFile / Glob 主要是 observable，不是 enforceable。
```

### Plugin / hook 不是 v0.1 质量主链路，但完整产品需要

最终分层：

- 最小保质量版：CLI-first，可不做完整 Codex plugin/hook。
- 完整产品版：需要 plugin/hook 提升触发稳定性和防绕过能力。

### Usage 不能后置

用户明确指出 usage 第一版就要有。最终设计保留轻量 usage：

```text
per-job / per-attempt usage；
source；quality；raw token_usage；duration。
```

## 1.5 当前最终定位

KodeXimi 的最终定位：

```text
一个 Codex-first、Kimi-worker 的本地委托执行 runtime。
```

它第一版回答：

> Codex 能不能把一个明确 code_edit 执行块交给 Kimi，并通过 runtime evidence 和 usage 判断这次委托是否成功、是否值得？

它不回答：

- 每个 internal step 应该给谁做。
- 如何做强/弱模型动态路由。
- 如何做完整企业沙盒。
- 如何成为通用多 agent 平台。

