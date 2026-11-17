# Task: second one-line fix in H1-0 package b01ec87a6f29b (CPU only), same method as REPORT_terminator.md

Workspace: /scratch/jjyeung/orch_n30/h10_stage/work/k330 (K = k330/kit). Same hard rules as BRIEF_terminator.md: no git, ssh, network, GPU, kills or deletion; write only inside k330.

## Bug
On the Orchard login node `sbatch` lives in /usr/local/bin. operator.py submit() (payload member `8.py`, source K/orchard_h10/operator.py) runs sbatch with
`env={'PATH':'/usr/bin:/bin',...}`, so `A_N=1 A_T=05:00:00 bash SUBMIT.cmd --test-only` fails: FileNotFoundError 'sbatch'.

## Fix (only this)
Change that env PATH to `'/usr/local/bin:/usr/bin:/bin'` in both K/orchard_h10/operator.py and payload `8.py` (exact byte replacement, once). Nothing else changes; the terminator repin already in K/orchard_h10/package stays.

## How
1. Generalize K/orchard_h10/repin_terminator.py (or add K/orchard_h10/repin_operator.py) to rebuild from the CURRENT package (0.tgz ecfad90f..., plan 5ef2094e...) with `8.py` replaced; update payload_pins['8.py'] only; same emitters as before. Self-test: no-change rebuild reproduces the current 8 files byte-for-byte. Back up the current package to K/orchard_h10/package_ecfad90f/ first.
2. Verify: 919 other members byte-identical; 9.json differs only in payload_pins['8.py']; the new 8.py equals K/orchard_h10/operator.py byte-for-byte; load_helpers + verify_config pass; opacity checks pass; `python -c` compile of 8.py passes. Rerun the 4 package checks you ran last time (kit/logs/t10/package_checks.log method) into kit/logs/t11/.
3. Append to k330/REPORT_terminator.md a section (<=15 lines): new 0.tgz sha+bytes, plan sha, PACKAGE.json and its five file hashes, check results, changed files.
