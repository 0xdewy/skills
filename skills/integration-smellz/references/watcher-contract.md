# Hosted watcher reviews

Use this adaptation only when a watcher supplies an immutable snapshot,
`scope.json`, and an explicit stage/output contract. The host owns scheduling,
model roles, freshness checks, report validation, and publication. Skill use
does not authorize posting or launching nested reviewers.

Review the complete issue and discussion, plus linked bodies, reviews, pinned
revisions, and relevant check results. Title/state alone does not establish
what landed or what was tested. Use the supplied snapshot consistently; do not
refetch the same issue merely to satisfy the manual workflow. Needed additional
evidence may be fetched read-only and saved in the supplied workspace. Never
modify source snapshots or the reviewed checkout.

Apply every lens in `references/review-contract.md` yourself, in one pass,
Pareto first. A Pareto finding (what to delete, collapse, or reuse, and the
cost avoided) is a finding.

## Stage and artifact ownership

- Scouts supply only source-backed leads in the host's lead packet. They do
  not write a formal report, coverage, severity, completion, or readiness verdict.
- Strong reviewers verify independently before seeing scout leads, then
  adjudicate every lead with source evidence, including rejected ones.
- Produce the exact requested stage JSON artifact and schema. Do not substitute
  `INTEGRATION_REVIEW.md`, the manual finding schema, or a `DONE` line. Standalone
  ledger/checker artifacts are optional supporting evidence only when useful
  and allowed by the host; they are not mandatory stage deliverables.

Coverage must cite the original snapshot sources listed for each area in
`scope.json`. Excerpts and supplemental live evidence may support those sources,
not replace them. Keep inspected and unreviewed areas distinct. A zero-finding
report with unreviewed evidence is partial.

Historical CI and acceptance results are source evidence, not commands the
reviewer ran. For completed reviewer checks, save captured output under the
host's `checks/` directory and record the exact terminal command and actual
terminal exit code. Use pipefail for pipelines and wait for background checks;
a successful wrapper does not establish a successful test. Do not claim tests
passed from a started job or tool invocation alone. PM checks can be empty.

## PM review versus product completion

Inspect acceptance conditions, contradictions, missing required dependencies,
stale claims, and gates whose success cannot be determined. Do not invent
deadlines, owners, unsupported features, or extra release requirements.
Already documented release blockers and product limits are not new defects.
Pending release work is not itself a review coverage gap: a review can be
complete while candidate integration is blocked or release evidence is pending.
Review gaps identify a material integration conclusion that missing evidence
prevents assessing. Optional unrun checks are limitations, not completion blockers.
Do not execute a PM issue's entire release checklist merely to finish reviewing.

Each issue finding quotes a current issue passage, explains a concrete
consequence, and gives a small source-supported correction. Cross-repo code
evidence supplements that quote. Report a contradictory readiness claim or
untracked integration defect, not the mere existence of a documented blocker.
