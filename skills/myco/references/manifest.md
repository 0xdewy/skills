# Desired-state manifest

Use one manifest per repository reconciliation. The CLI derives the repository
identity from the canonical `--repo` path; `project.key` is a human-readable
stable label rather than the storage identity.

```json
{
  "version": 1,
  "project": {
    "key": "skills",
    "title": "Agent Skills",
    "workflow": ["Backlog", "Ready", "In Progress", "Review", "Done"]
  },
  "tasks": [
    {
      "key": "skills/myco#cli:reconcile",
      "title": "Reconcile code findings with Myco",
      "description": "Maintain native Project and Task posts without UI automation.",
      "status": "Review",
      "evidence": [
        "skills/myco/scripts/myco.ts",
        "bash -n skills/myco/scripts/myco"
      ],
      "closed": false
    }
  ]
}
```

## Contract

- `version`: must be `1`.
- `project.key`: non-empty stable label used in reports.
- `project.title`: non-empty Myco Project title.
- `project.workflow`: ordered, unique, non-empty column names.
- `tasks`: unique task objects. An empty list is valid and changes nothing else.
- `tasks[].key`: stable provenance key; never derive it solely from the title.
- `tasks[].title`: non-empty card title.
- `tasks[].description`: optional short rationale or acceptance condition.
- `tasks[].status`: one of `project.workflow`.
- `tasks[].evidence`: optional strings such as `path:line`, test ids, or commands.
- `tasks[].closed`: optional boolean. Omission preserves the current closed state
  for existing cards and creates new cards as open.

The CLI owns only cards carrying its provenance marker or recorded in its local
mapping. It updates the declared fields, creates missing declared cards, and
leaves omitted or unmanaged cards untouched. It never deletes posts.
