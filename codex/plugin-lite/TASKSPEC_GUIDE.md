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

