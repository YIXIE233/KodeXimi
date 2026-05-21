# 03. KodeXimi 完整产品设计

## 3.1 完整产品目标

完整产品不是增加更多任务类型，而是提高长期使用质量：

- 安装方便。
- 项目启用/关闭明确。
- Codex 入口稳定。
- Kimi worker 可复用。
- 并行和依赖调度可控。
- usage 可统计。
- review 可批量。
- 失败可恢复。
- 多项目可维护。

## 3.2 产品架构

```text
Codex Integration Layer
KodeXimi Runtime Core
Worker Layer
Evidence / Review Layer
Product UX / Operations Layer
```

完整产品加入：

- Codex plugin/tool。
- Codex hook。
- Worker pool。
- Scheduler / queue。
- Path lock manager。
- Batch / DAG。
- Deep doctor。
- Usage reporting。
- HTML review report。
- Repair/rebuild。
- Optional git_worktree_mode / materialized_workspace_mode。

## 3.3 Codex plugin

提供：

```text
/kodeximi:run
/kodeximi:status
/kodeximi:review
/kodeximi:rework
/kodeximi:usage
/kodeximi:batch
```

或 typed tool API：

```text
delegate_task(task_spec)
get_review_package(job_id)
submit_review_decision(job_id, decision)
get_pending_jobs()
get_usage(job_id)
```

作用：

- 减少 Codex 手写 CLI 错误。
- 减少忘记 review。
- 隐藏路径和 job 细节。
- 提升真实长期使用的流程质量。

## 3.4 Codex hook

完整产品需要 hook：

1. pre-task hook：复杂任务前检查项目是否启用 KodeXimi。
2. pre-edit hook：Codex 准备直接修改执行面文件时提醒是否应走 KodeXimi。
3. pending-review hook：有 needs_review job 时提醒先 review。

hook 是 guardrail，不是 prison。它减少绕过，不应让普通简单问答被卡死。

## 3.5 完整并行

### 独立并行

写集合不重叠即可并行。

### 资源受限并行

限制：

- max_parallel_workers
- max_kimi_processes
- max_cpu / max_runtime
- max_project_jobs

### DAG 并行

支持：

```json
{
  "jobs": [
    {"id": "monthly", "task_spec": "monthly.json"},
    {"id": "quarterly", "task_spec": "quarterly.json", "depends_on": ["monthly"]}
  ]
}
```

规则：

- 无依赖先跑。
- 依赖成功后跑。
- 上游 failed/blocked 时下游 blocked。
- 支持 per-job review 或 batch review。

## 3.6 完整 execution modes

### direct_project_mode

方便模式，低隔离。

### git_worktree_mode

为 job 创建 Git worktree，Kimi 在 worktree 内修改，review 后 merge/apply patch。

适合并行和人类接管。

### materialized_workspace_mode

复制允许输入，Kimi 在独立 workspace 执行，输出 patch/artifacts，再 apply 回原项目。

适合敏感任务，但工程复杂。

推荐演进：

```text
direct_project_mode -> git_worktree_mode -> materialized_workspace_mode
```

## 3.7 完整 evidence

增加：

- manifest.json
- runtime-checks.json
- VERIFY_RAW/
- portable review package
- HTML review report

## 3.8 完整 usage

增加：

- per job usage
- per attempt usage
- per batch usage
- per project usage
- Codex-side usage if available
- cost estimate
- cache hit summary
- rework cost
- cost per accepted job

命令：

```powershell
kodeximi usage job-001
kodeximi usage batch batch-001
kodeximi usage project --since 30d
kodeximi usage export --format csv
```

## 3.9 完整失败恢复

命令：

```powershell
kodeximi repair job-001
kodeximi rebuild
kodeximi doctor --deep
kodeximi cancel job-001
kodeximi kill-orphans
```

增加状态：

- inconsistent
- stale
- cancellation_requested

恢复原则：

- DB 与 evidence 不一致时进入 inconsistent。
- rebuild 从 manifest 恢复。
- 证据缺失则 blocked。
- 进程丢失则 failed_runtime。
