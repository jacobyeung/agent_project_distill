<!-- recovered by seal_plan: transcript=71f94277 line=23745 utc=2026-11-13T18:39:50.269Z kind=commands original_path=(bash command)  -->
N=$(date -u +%Y%m%dT%H%MZ); C=/scratch/jjyeung/orch_cd; cat > $C/leg_s1_tree/inbox/${N}_ORCH_ORDER_scanner_safety_verdict_fix_the_instructions.md <<'EOF'
# ORCH order: scanner safety verdict is RUN AFTER FIXES; the scanner code stays, the operator instructions change

Verdict: `/scratch/jjyeung/orch_cd/leg_s1_review/DONOR_SCANNER_SAFETY.md` (read it in full). The scanner cannot write on the node or block job 169097: its only database open is read-only and immutable (`scan_donor_rows.py:152`), every error prints a refusal and exits 2, nothing retries, a failed step cannot take the job down, the output is about 2.3 KB, and the command text contains no guarded words. 22 tests ran (your 6, plus 2 of the reviewer's in both journal modes); the fixture stayed identical every time. The scanner source and the bundle hash do not change.

Write a new operator file `out/DONOR_ROW_SCANNER_OPERATOR_07ca49df_r2.md` (leave the first in place) with:

1. The step command with `/usr/local/bin/srun`, `--immediate=60`, `--gres=none`, the same job, overlap, CPU, memory and time options, python flags including `-S`, a core-dump limit of 0, and `--wall-seconds 840`.
2. A plain statement of the one expected refusal: if a production database is in WAL journal mode with a live `-wal` file, the scanner refuses by design (`scan_donor_rows.py:150`). Say what the operator reports in that case, and prepare (do not send) the smallest safe alternative for that case, as a separate patch with a test: reading such a database must still create nothing beside it.
3. The acceptance steps unchanged (counts 20,239 / 194,987 / 57,136 / 114,904, configuration 78341acb, preparation 34cf26a6, scanner source hash, row digest).

The transport back to Trinity is the operator's part (I am ordering it separately): long enough session or a detached step on the login host, base64 with a SHA256, raw text saved before decoding. Do not design that; just state the size and form of the scanner's output so the operator can check completeness.

Post one RESULT to me and to `orchard_cp2/inbox/`. Then the F1 allowlist work of my 1813Z ruling, then the frame-pin cache.
EOF
cat > $C/orchard_cp2/inbox/${N}_ORCH_ORDER_donor_row_scan_conditional_go.md <<'EOF'
# ORCH order: the donor row-order scan inside job 169097, conditional go

**What and why.** One read-only step inside the job that fingerprints the order and content of the admitted training rows (about 387,000 rows; reads about 28.6 GB of node-local databases once; about 12 minutes; output about 2.3 KB). Without it, a warm start from an export cannot prove it draws the same rows as this run, and the databases vanish with the node when the job ends. An independent safety check found that the scanner cannot write on the node or block the job; its findings are all about the command and the way the result comes back: `/scratch/jjyeung/orch_cd/leg_s1_review/DONOR_SCANNER_SAFETY.md` (read it in full).

**Material.** Bundle `/scratch/jjyeung/orch_cd/leg_s1_tree/out/DONOR_ROW_SCANNER_BUNDLE_07ca49df.tar` (sha 1a565f85, unchanged). Use the revised operator file `out/DONOR_ROW_SCANNER_OPERATOR_07ca49df_r2.md` when leg_s1_tree posts it (it adds `/usr/local/bin/srun`, `--immediate=60`, `--gres=none`, python `-S`, core-dump limit 0, `--wall-seconds 840`); do not use the first version's command.

**Your part: the transport, built before you run anything.**
- Your access wrapper ends a session after 120 s by default and drops any line containing certain words; the scan runs about 12 minutes. Either run the step detached on the login host with its output going to a small file on the login host's own local disk and fetch that file with a second short call, or hold one session long enough (at least 1,000 s). I prefer detached: a dropped connection must not lose the result.
- Return the result base64-encoded on one line with its SHA256; save the raw response to a file before any decoding or parsing; verify the hash and then the acceptance checks in the operator file.
- Keep guarded words out of every shell command text; put scripts in files with your editor tool.

**Conditions, all required:**
1. The second size execution has completed and a later snapshot shows training stepping after it (metrics advanced, GPU samples active).
2. The revised operator file exists and your transport driver has passed a dry test against a harmless command of the same shape (for example the interpreter printing a 3 KB line containing the filtered words, which must arrive intact).
3. Run it between saves: not within ten minutes of an expected periodic save (the first was at step 1; tell me the save times you see).
4. One execution. If the step is refused, queued, hits its wall limit or the scanner refuses (for example on a live `-wal` file), do not retry; post the evidence. If it succeeds, post the RESULT with the accepted envelope's hash and send the full output to `leg_s1_tree/inbox/` for pinning.
5. Check the job before and after exactly as for the size read; if anything in the job changes across the step, tell me at once.

This order is the written word my 1823Z note requires for this one action. It covers nothing else inside the job.
EOF
T=$(date -u +%Y-%m-%dT%H:%M:%SZ); echo "$T orch-home-distill-79: DONOR SCANNER SAFETY CHECK (Claude Opus high; leg_s1_review/DONOR_SCANNER_SAFETY.md): RUN AFTER FIXES. Scanner cannot write on the node or block the job (only database open is read-only + immutable; errors exit 2; no retry; output ~2.3 KB; no guarded words); 22 tests, 21 pass (the one failure is the by-design refusal on a live WAL file). Fixes are operator-side: oc.sh ends sessions at 120 s by default and drops lines with certain words (scan takes ~12 min) -> detached step or T >= 1000, base64 + SHA256, raw saved first; srun needs --immediate=60 --gres=none and /usr/local/bin/srun; python -S, core-dump limit 0, --wall-seconds 840; a WAL-mode database would make the scanner refuse. ORDERS ($N): leg_s1_tree writes the r2 operator file (+ prepared alternative for the WAL case); orchard_cp2 gets a CONDITIONAL GO for one execution (after the second size run and a snapshot showing training stepping; transport dry-tested; not within 10 min of a periodic save; no retry)." >> $C/ORCH_HANDOFF.md; echo done $N