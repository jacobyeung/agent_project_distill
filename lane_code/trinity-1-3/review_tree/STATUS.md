# review_tree STATUS (trinity-1-3)
DONE. Verdict NOT READY on a1f559e2 and 3b ba0c6ebf (withheld rooms closed in 3b on CPU): out/REVIEW_VERDICT_TREE.md (copied to events folder with evidence/).
Inputs in work/: pkg tar (39b2b5db verified), base.tar (845b1789), rows/slices (30 files from trinity-1-13, pre-a41ba191), rec/.
Harnesses: work/h (mk.py envelope builder, run_intake.py, mutate.py, mutcov.py, probe_bank.py); staging runs work/stage2 (no numpy) and work/stage3 (p1cpu shim).
Removal candidates (no deletion done): work/stage, work/stage2, work/stage3, work/t_run, work/lane3, work/h/repro, work/base, work/p (all reviewer scratch, ~1.7 GB).
