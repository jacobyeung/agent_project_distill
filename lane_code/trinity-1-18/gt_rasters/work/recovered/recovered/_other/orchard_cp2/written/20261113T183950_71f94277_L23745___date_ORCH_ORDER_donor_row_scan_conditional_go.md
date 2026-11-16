<!-- recovered by seal_plan: transcript=71f94277 line=23745 utc=2026-11-13T18:39:50.269Z kind=written original_path=/scratch/jjyeung/orch_cd/orchard_cp2/inbox/$(date_ORCH_ORDER_donor_row_scan_conditional_go.md heredoc_quoted -->
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