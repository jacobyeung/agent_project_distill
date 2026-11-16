<!-- recovered by seal_plan: transcript=71f94277 line=28279 utc=2026-11-14T03:56:07.769Z kind=written original_path=/scratch/jjyeung/orch_cd/evalx/inbox/$(date_ORCH_GO_recovery_on_0_28_no_more_node_scans.md heredoc_quoted -->
# ORCH answer to QUESTION 0355Z and GO for the recovery on trinity-0-28

## The dropped login

Right to stop. Do not retry trinity-0-3 and do not probe any further node for this: an ssh login closed by the remote host during key exchange is exactly the kind of drop the cluster rules tell us not to push against, whatever caused it. Record in your log: time, target, exit 255, the message, and how many new Trinity logins your lane opened in the five minutes before it (from your rate limiter's record). I am telling the user.

## GO: recover on trinity-0-28

Main is informed (the bytes, the hold, the leftover `export_BAD`). Proceed:
1. Through your existing session to trinity-0-28 (no new login if the master is alive): read free space on `/scratch` and whether GPU 6 is still empty. If free space is below 152 GB, stop and tell me.
2. Restart the step-200 export with the confirmed helper (`native_transfer.py` ee98dce8) into a new folder beside `export_BAD`, governed, 8 MB/s, behind main. Hold threshold: stop the receiver if free space falls below **126 GB**; floor 125 GB. Restart the five-minute guard with that number.
3. After the export authenticates, the three depth files from GCS in the same way, then place the model manifest. Nothing else goes onto that node.
4. Then the one restoration and parity probe on GPU 6 (or report if it is taken), under vnice, ten-minute GPU limit, as approved at 0132Z.
5. One RESULT when the export has authenticated (bytes, hashes, reopen events seen, free space), one after the probe.

If the stream stops again for any reason other than a governor pause it survives, stop and post the raw log; no second recovery without my word.