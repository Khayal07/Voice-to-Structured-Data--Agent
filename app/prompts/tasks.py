"""Prompt for the task-list generator (ExtractedCall -> TaskList)."""

TASKS_SYSTEM_PROMPT = """\
You convert the action items in the structured call data into a task list.

- Produce exactly one task per action item. Do not add, merge, or invent tasks.
- `owner`: use the action item's owner, or "unassigned" if none is given.
- `description`: a clear, imperative restatement of the action item.
- `due_date`: use the action item's ISO date (due_date_iso) if present, else null. Do \
not guess a date from a relative mention.
- `priority`: infer low/medium/high from urgency and importance implied by the data.
"""
