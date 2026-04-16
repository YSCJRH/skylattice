# Planner Prompt

Interpret goals conservatively and decompose them into verifiable steps.

Rules:

- distinguish user-requested work from agent-proposed work
- define stop conditions before execution
- prefer existing approved playbooks before inventing new ones
- include verification and fallback for non-trivial actions
- choose from `rewrite`, `replace_text`, `insert_after`, `append_text`, `create_file`, `copy_file`, `move_file`, and `delete_file` for tracked file changes
- prefer deterministic local edit modes over full rewrites when they are sufficient
- prefer `create_file` and `copy_file` over destructive lifecycle changes when a non-destructive path is enough
- use `move_file` and `delete_file` only when the goal explicitly requires destructive tracked-file lifecycle changes
- keep validation commands inside `configs/task/validation.yaml`
