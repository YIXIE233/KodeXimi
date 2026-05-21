# 2026-05-21 KodeXimi 关键结论与验证清单

## 1. 关键结论

1. KodeXimi 值得做，但必须收紧为 Codex-first block delegation runtime。
2. 它不应伪装成模型路由系统、安全沙盒或多 agent OS。
3. 最小保质量版必须保留 TaskSpec、Kimi bounded attempt、runtime VERIFY、diff-summary、usage、needs_review、review decide、rework。
4. Codex-side plugin/hook 可以不进 v0.1，但完整产品需要。
5. Kimi agent-file、controlled skills-dir、RawWire approval/boundary 不能省。
6. Usage 第一版就记录，但可以只人工查询。
7. direct_project_mode 是 low-isolation convenience mode，不能声称强隔离。
8. 第一版只支持 code_edit 和互不影响的并行需求。

## 2. v0.1 验证清单

### 环境验证

- `kodeximi doctor` 可检测 system Kimi。
- `kimi --wire` 可 initialize。
- agent-file dry run 可启动。
- Git Bash 可用。
- SQLite 可写。

### 单 job 验证

- TaskSpec 校验生效。
- TASK.md 正确生成。
- Kimi 写 RESULT.md。
- KodeXimi 写 VERIFY.md。
- KodeXimi 写 diff-summary.md。
- KodeXimi 写 usage.json。
- 状态进入 needs_review。
- Codex review decide accepted 生效。
- review decide rework 生成 attempt 002。

### 质量验证

- VERIFY 不是 Kimi 自写。
- diff-summary 能列出实际变化。
- Kimi 不修改 `.kodeximi` 控制面。
- forbidden path 写入被拒绝或至少被发现。
- max_attempts 生效。
- usage quality 能区分 exact / partial / unavailable。

### 并行验证

- 两个 write set 不重叠任务可并行。
- write set 冲突任务拒绝并行。
- 并行任务 evidence 独立。
- 一个任务失败不污染另一个任务。

## 3. 对照实验建议

对同一批 5-10 个 code_edit 任务跑：

```text
A: Codex-only
B: Codex + KodeXimi + Kimi
```

记录：

- task_success
- verification_pass
- rework_count
- Kimi token usage
- attempt duration
- Codex review burden
- diff size
- unexpected changes
- manual intervention count

判断标准：

- KodeXimi 不应明显降低质量。
- Kimi attempt usage 必须可见。
- Rework 不应爆炸。
- Codex review 能基于 evidence 做出清楚判断。
- 如果成本/时间无收益，应限制 KodeXimi 适用场景。
