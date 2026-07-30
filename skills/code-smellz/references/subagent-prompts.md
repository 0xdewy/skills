# Code Smellz Role Index

Load `references/common-findings.md` plus only the active role prompt:

| Role | Prompt | Owned output |
|---|---|---|
| Bug Hunter | `references/bug-hunter.md` | `findings-bugs.json` |
| Code Minimizer | `references/code-minimizer.md` | `findings-simplify.json` |
| Architecture Optimizer | `references/architecture-optimizer.md` | `findings-architecture.json` |
| Security Auditor | `references/security-auditor.md` | `findings-security.json` |

For the post-architecture minimizer pass, reuse `references/code-minimizer.md` with
`{{file_list}}` limited to architecture-modified files and output
`findings-simplify-2.json`. Create every output path before dispatch and pass
the resolved path as `{{output_path}}`.
