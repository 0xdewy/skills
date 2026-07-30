# Verbosity Reducer

Find constructs with a shorter, equally readable and maintainable equivalent.

Inputs: goal `{{codebase_goal}}`; iteration `{{iteration}}`; files
`{{file_list}}`.

Prioritize redundant temporaries, boilerplate covered by standard libraries,
literal-building sequences, repeated simple guards, and disabled code. Skip
style-only changes, dense one-liners, explicit state enumerations, project-wide
conventions, comments, and changes with zero net savings. Show before/after and
always include a patch. Follow `references/common-findings.md`, use
`category: "verbosity"`, and write `{{output_path}}`.
