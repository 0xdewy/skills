# Shrinkray Final Report Template

Read `session.json` and all `iter_*_loc.json` files, then print this report:

```
╔══════════════════════════════════════╗
║         SHRINKRAY REPORT             ║
╚══════════════════════════════════════╝
Iterations completed : N
Starting LOC         : XXXX
Final LOC            : YYYY  (-ZZ% / -NN lines)
Tests                : NN/NN passing  (was NN/NN)
Note: All changes are in the working tree. Review with `git diff` and commit when ready.

Lines removed by category:
  Dead code removed   : N lines (N items)
  Ghost files deleted : N files (N lines)
  Code consolidated   : N lines (N deduplication sites)
  Verbosity reduced   : N lines (N rewrites)
  ─────────────────────────────────────
  Total               : N lines removed

Reverted (broke tests): N changes
Skipped (safety):       N changes

Remaining (not applied, needs human review):
  [medium] path/to/file — description
  [low]    path/to/file — description

Recommendation:
  <"Codebase is minimal." | "N items require human review." | specific advice>
```

Then emit: `DONE: <WORKSPACE> — N lines removed across M iterations (-Z% LOC reduction)`
