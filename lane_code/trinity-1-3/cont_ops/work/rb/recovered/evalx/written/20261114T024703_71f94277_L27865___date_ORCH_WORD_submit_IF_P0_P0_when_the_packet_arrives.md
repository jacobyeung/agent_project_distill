<!-- recovered by seal_plan: transcript=71f94277 line=27865 utc=2026-11-14T02:47:03.790Z kind=written original_path=/scratch/jjyeung/orch_cd/evalx/inbox/$(date_ORCH_WORD_submit_IF_P0_P0_when_the_packet_arrives.md heredoc_quoted -->
# ORCH word: submit the IF-P0 baseline arm (P0) as soon as its packet hand-off is in your inbox

The operator's held QoS line shows the `general` cap is one running GPU and one node per user, not a count of submitted jobs, so jobs may wait in the queue behind your 169367 and gain age.

Lane if_p0 is building the P0 packet now and will put a hand-off note in your inbox (name containing `IF_P0_P0_PACKET_READY`: token, path, size and sha256 of `BATCH.sh`, the two exact `sbatch` argument lists, the result path). When it arrives:
1. Verify `BATCH.sh` against the stated sha256.
2. Check the queue and main's notices as you do before every submission. Main has priority on Orchard: if main has anything queued or running on `general`, do not submit and tell me.
3. Send the identical `BATCH.sh` bytes to `sbatch` standard input twice, as the hand-off says: first with `--test-only`, then the real submission, once. No retry.
4. Post one RESULT with the job id and Slurm's forecast in UTC. After that, treat it like your own jobs: one observation when it starts (staging phases, the preflight and the namespace smoke test), one when it ends, and fetch the bounded result archive from `/home/jjyeung/okit/ifp0_results/<token>/` into `/scratch/jjyeung/orch_cd/if_p0/inbox_results/<token>/` (hash it against `EXIT.json`), then tell me and lane if_p0's inbox.

This word covers arm P0 of seal 8d5bdd730bebb9b317f7d4aa715cfe06981f698eceed13af81f3232d07cd3a90 only. Your own job 169367 keeps its place; do not cancel or reorder anything.