# TaskSpec Guide

Use schema version `0.1`.

Do not use shell command strings for verification. Use argv arrays and supported templates.

Minimal code-edit shape:

```json
{
  "schema_version": "0.1",
  "task_type": "code_edit",
  "goal": "Describe the bounded change.",
  "context_hints": {
    "required_files": ["path/to/file.py"],
    "optional_globs": []
  },
  "write_policy": {
    "modify_files": ["path/to/file.py"],
    "create_files": [],
    "delete_files": [],
    "allow_globs": [],
    "deny_globs": [".git/**", ".kodeximi/**", ".env", ".env.*", "**/*.key", "**/*.pem"]
  },
  "verification": {
    "commands": [
      {
        "id": "file_exists",
        "type": "file_exists",
        "path": "path/to/file.py"
      }
    ]
  },
  "limits": {
    "attempt_timeout_seconds": 900,
    "max_attempts": 2
  }
}
```

Inventory-only shape for strict mode when Codex does not know the right files:

```json
{
  "schema_version": "0.1",
  "task_type": "inventory",
  "goal": "Find candidate files related to the user request. Do not edit business files.",
  "context_hints": {
    "required_files": [],
    "optional_globs": ["**/*.py", "README.md"]
  },
  "write_policy": {
    "modify_files": [],
    "create_files": [],
    "delete_files": [],
    "allow_globs": [],
    "deny_globs": [".git/**", ".kodeximi/**", ".env", ".env.*", "**/*.key", "**/*.pem"]
  },
  "verification": {
    "commands": []
  },
  "limits": {
    "attempt_timeout_seconds": 600,
    "max_attempts": 1
  }
}
```

In strict mode, if Codex lacks enough project context, it should create an `inventory` task instead of reading business files directly.
