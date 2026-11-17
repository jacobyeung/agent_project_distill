# Cross-family review request

Review package `e47d0593fefec` before any submission. This file requests the orchestrator's review; no reviewer was launched or messaged.

1. Check `PATCH.diff` against bf94 and `FILE_SHA256_DIFF.tsv`. Admission, restore, scorers, statistics, items, caps, and dependency inventories must remain byte-identical.
2. Check null-rule AST equivalence, default-off snapshots, candidate indexing and ties, per-call diagnostics, and all three own/tower wiring paths. Confirm the planted ignored-tower-rule variant fails.
3. Check journal resume, tower reuse, wrapper settings identities, and report pairing. Different rules or partial journals with different bindings must never combine.
4. Inspect the sealed external batch bootstrap, `tower_sequence.py`, `node_check.py`, and their descriptor hashes. Production admission, staging, isolation, caps, and return must still execute. Confirm the full node CPU receipt is mandatory.
5. Inspect the 600-run replay, expected eight geometry errors, seven remaining pairs, 31 passing b04 tests with 13 missing-fixture non-passes, EAT-1 scoped delta, and own-versus-own report self-check.
6. Review the estimate: 7.61 read-hours plus overhead cannot fit the unchanged five-hour cap. The command prioritizes both distance reads and returns partial coverage. Full camera/room evidence is not promised.
7. Check opaque placement, H100 proof, pending `jjy_*` stop condition, SFT/544 pins, unchanged staged archives, and the five-hour one-GPU command.

No real CPU model read, live restore, full node CPU check, or GPU read has passed locally. Approval must not describe those as validated. Report outcomes and any required fixes to the orchestrator; do not submit from this review.
