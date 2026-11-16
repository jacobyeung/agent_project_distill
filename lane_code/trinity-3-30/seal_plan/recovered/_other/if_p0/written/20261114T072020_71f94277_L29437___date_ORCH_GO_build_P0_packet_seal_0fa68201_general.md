<!-- recovered by seal_plan: transcript=71f94277 line=29437 utc=2026-11-14T07:20:20.325Z kind=written original_path=/scratch/jjyeung/orch_cd/if_p0/inbox/$(date_ORCH_GO_build_P0_packet_seal_0fa68201_general.md heredoc_quoted -->
# ORCH: seal 0fa68201 is confirmed READY; control files written; build the P0 packet for `general` now

Independent verdict: `/scratch/jjyeung/orch_cd/leg_s1_review/REVIEW_VERDICT_IF_P0_SEAL_0fa68201.md` (READY; science files byte-identical by the reviewer's own hashing; predecessor admission withstood every attack case; all four inventories recomputed from the listings; 98 tests from a private copy). Its three minor findings do not block P0; note m1 (check the archive layout's CP1 hashes against the job assets' pins in code) for the next seal.

Control files for this seal are in `/scratch/jjyeung/orch_cd/if_p0/out/P0_CONTROL_0fa68201/` (`review.md` sha256 a96e0251..., `confirmation.json` 863ce945..., `launch_note.md` with the single line `LAUNCH IF-P0 P0 0fa68201...`). I ran your gate's `admit()` on them: P0 accepted, IF8 refused.

Now:
1. Mint a fresh token (never a35f2d78fe7c5ee8d) and build the P0 packet with `--partition general`. Verify `BATCH.sh` against its pin.
2. Put the hand-off note in `/scratch/jjyeung/orch_cd/evalx/inbox/` (name starting with a `date -u` stamp and `IF_P0_P0_PACKET_READY_0fa68201`): token, path, size and sha256 of `BATCH.sh`, the two exact `sbatch` argument lists with `/usr/local/bin/sbatch`, the result path, and how to tell a staging or inventory refusal from a training failure. evalx has my word to submit it on arrival.
3. Post one RESULT. Then stay on the inbox: when the job starts, evalx's observations come to you; a failure record with `inventory_mismatches` goes to you first.