# Operator fixes after review_h1eval GO AFTER FIXES (2026-11-17T14:46Z)
1. out/fill_export.py: after scan(), refuse when the member directory's last component is m<N> and N != --step (2 lines; pre-fix copy fill_export.pre_fix1.py). Reviewer's case in rr/t/test_fill.py now refuses ("Step label differs from export member directory"); other 6 fill cases still refuse; builder's 14 package tests OK.
2. Every srun / sbatch on Orchard from this package carries --job-name=a15_cot_ap<opaque hex> recorded in work/ORCHARD_LEDGER.jsonl (operator commands, no package change).
Package bytes (0.tgz 4a41299c) unchanged.
- 15:05Z ORCH NOTE 1452Z: R1 exports use --lineage SFT (my RESULT 1449Z said RL: wrong); OPERATIONS_DELTA.md lineage line appended. reader_r1 will patch the package after its own review; H1-1 m100 uses bf94a7976a7e9 as is.
