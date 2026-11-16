<!-- recovered by seal_plan: transcript=71f94277 line=24440 utc=2026-11-13T19:49:04.962Z kind=written original_path=/scratch/jjyeung/orch_cd/orchard_cp2/inbox/$(date_ORCH_NOTE_scanner_acceptor_updated.md heredoc_quoted -->
# ORCH note: use the updated off-node acceptor for the donor scan's result

leg_s1_tree's RESULT of 19:47Z (`/scratch/jjyeung/orch_cd/leg_s1_tree/events/20261113T1947Z_RESULT_warm_start_review2_fixes_07ca49df.md`): the acceptor bundled with the scanner drops the scanner's source hash, and the fixed consumer now refuses an envelope without it.

- The scan itself is unchanged: same bundle (sha 1a565f85), same r2 operator file, same command inside the job.
- For acceptance on Trinity, run `/scratch/jjyeung/orch_cd/leg_s1_tree/work/warm_start_review2fix_07ca49df/accept_scan.py` on the retained full scanner capture, with the r2 guide's existing arguments. Keep the full raw capture; do not convert or re-create it, and never backfill a hash.
- Send the full capture and the accepted envelope to `leg_s1_tree/inbox/`; it compares the routing and VQA streams with its local digests (routing da0668d0..., VQA fdb4e41f...).

Also from your 19:46Z snapshot: the job's output file gained a guard line at 19:44:06Z, so the step-50 save or export has printed safely. Post the step-50 RESULT (save time, export upload, receipts) as soon as the upload shows.