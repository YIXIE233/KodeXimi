# KodeXimi Codex Plugin-Lite

Plugin-lite is a Codex-side behavior protocol. It is not a hard hook.

Use it when the user says:

```text
初始化当前会话 KodeXimi strict mode。
```

From that point, Codex must treat KodeXimi as the default execution path for this conversation.

## Strict default

Codex must not directly:

- read business source files to solve the task;
- edit business files;
- edit tests;
- open task websites or business documents;
- run business implementation or verification commands.

Codex may:

- ask clarification questions;
- create TaskSpec JSON;
- call `kodeximi`;
- read KodeXimi evidence;
- write review decisions;
- summarize results to the user.

Explicit user override is required to bypass this mode.

