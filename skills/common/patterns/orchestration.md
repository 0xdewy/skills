# Orchestration Contract

Use `execution-contract.md` for general safety and validation. For parallel
work:

1. Decompose only independent work and state the worker/wave budget.
2. Create output directories first; give each worker one owned path and exact
   acceptance/verification contract.
3. Keep coordination state single-writer. Workers never edit shared status.
4. Dispatch ready work once, validate artifacts at the phase gate, and rerun
   only failed slices.
5. Checkpoint accepted work and `next_action` before advancing so interruption
   is resumable.
6. Integrate centrally and revert only coordinator-created patches or snapshots.
