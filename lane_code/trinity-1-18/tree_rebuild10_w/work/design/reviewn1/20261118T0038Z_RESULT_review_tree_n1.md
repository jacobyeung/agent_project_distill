# RESULT review_treen1: builds n1 + 9fix (seal 64a2ea92, package a1cb13de) GO AFTER FIXES
- Verdict: events/tree_rebuild/REVIEW_VERDICT_TREE_N1.md. Evidence: trinity-1-3:/scratch/jjyeung/orch_n30/review_treen1/work/ (F1_*.json, F5.json, F6*.json, PEXPORT.json, ADMIT_SEQ.json, mut/, restage_r1/).
- F1–F6 are fixed. Seal and kit restage are byte-identical. Suites match the builder: r2 413/413; generator and cp2 have the same failing IDs.
- Must fix N1 before any P→N handover. P's export format refuses without a receipt, and the continuation receipt is compared only with N's own config. The test does not use P's format, and its LR assertion is tautological. N1 does not block an N launch from step 544.
- Add tests (N2): an absent, not held-out scene; own probability 0.1; the frame-count clause for one-line rooms.
- Low: N3 (U+200B status), N4 (R1 reader skips R0 reserve; v7 has 0 hits), N5 (no per-job /tmp assertion).
- Open items: none blocks. The distance cell is cut to 5.90 rows per step; the orchestrator must accept that or bind more rows.
