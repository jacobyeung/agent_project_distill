<!-- recovered by seal_plan: transcript=71f94277 line=23745 utc=2026-11-13T18:39:50.269Z kind=written original_path=/scratch/jjyeung/orch_cd/leg_s1_tree/inbox/$(date_ORCH_ORDER_scanner_safety_verdict_fix_the_instructions.md heredoc_quoted -->
# ORCH order: scanner safety verdict is RUN AFTER FIXES; the scanner code stays, the operator instructions change

Verdict: `/scratch/jjyeung/orch_cd/leg_s1_review/DONOR_SCANNER_SAFETY.md` (read it in full). The scanner cannot write on the node or block job 169097: its only database open is read-only and immutable (`scan_donor_rows.py:152`), every error prints a refusal and exits 2, nothing retries, a failed step cannot take the job down, the output is about 2.3 KB, and the command text contains no guarded words. 22 tests ran (your 6, plus 2 of the reviewer's in both journal modes); the fixture stayed identical every time. The scanner source and the bundle hash do not change.

Write a new operator file `out/DONOR_ROW_SCANNER_OPERATOR_07ca49df_r2.md` (leave the first in place) with:

1. The step command with `/usr/local/bin/srun`, `--immediate=60`, `--gres=none`, the same job, overlap, CPU, memory and time options, python flags including `-S`, a core-dump limit of 0, and `--wall-seconds 840`.
2. A plain statement of the one expected refusal: if a production database is in WAL journal mode with a live `-wal` file, the scanner refuses by design (`scan_donor_rows.py:150`). Say what the operator reports in that case, and prepare (do not send) the smallest safe alternative for that case, as a separate patch with a test: reading such a database must still create nothing beside it.
3. The acceptance steps unchanged (counts 20,239 / 194,987 / 57,136 / 114,904, configuration 78341acb, preparation 34cf26a6, scanner source hash, row digest).

The transport back to Trinity is the operator's part (I am ordering it separately): long enough session or a detached step on the login host, base64 with a SHA256, raw text saved before decoding. Do not design that; just state the size and form of the scanner's output so the operator can check completeness.

Post one RESULT to me and to `orchard_cp2/inbox/`. Then the F1 allowlist work of my 1813Z ruling, then the frame-pin cache.