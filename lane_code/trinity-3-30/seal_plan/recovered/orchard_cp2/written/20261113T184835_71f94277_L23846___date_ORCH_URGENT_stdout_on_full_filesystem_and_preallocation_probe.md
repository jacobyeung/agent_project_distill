<!-- recovered by seal_plan: transcript=71f94277 line=23846 utc=2026-11-13T18:48:35.781Z kind=written original_path=/scratch/jjyeung/orch_cd/orchard_cp2/inbox/$(date_ORCH_URGENT_stdout_on_full_filesystem_and_preallocation_probe.md heredoc_quoted -->
# ORCH, urgent: a full project filesystem may crash the trainer at a save; three things, in order

**The risk.** The trainer prints a JSON line to the job's stdout at every save and every export (`checkpoint_disk_guard`, `export_disk_guard`; they are in `o/169097.out`). That file is on the project filesystem. On NFS the first write after "no space" succeeds into the cache and the next one fails, so a print after the filesystem fills can raise inside a rank. Free space was 351.1 GB at 18:46:20Z. leg_s1_canary is reading the source to say exactly which prints exist and whether they are caught.

## 1. Facts, in your next routine call (read-only)

- How `/project/community` is mounted on the compute node and on the login node: NFS version and mount options (one line from the mount table for that filesystem).
- The times of the saves so far and whether `o/169097.out` gained a guard line at each (from your snapshots).

## 2. A preallocation probe on our own sandbox file (one small write, approved)

In `distill/okit/rate_469ddece/` create one new small file and ask the filesystem to reserve 16 MiB for it beyond its end while keeping its size (the `fallocate` utility with its keep-size option, or `posix_fallocate`-style allocation through the interpreter if the utility refuses). Report: whether the call succeeded or said the operation is not supported, and the file's size and allocated blocks before and after. Nothing else is touched. Keep the names of guarded operations out of the command text.

If the filesystem supports it, I will decide whether to reserve space the same way for the job's own append-only files (`o/169097.out`, `o/169097.steps`, `o/gcs.log`, the receipts file) so that their appends keep working when the filesystem is full. Do not do that without my word.

## 3. Keep going on the rest, in this order

Production checks; the donor row scan under my 1839Z conditional go; the small-record copy to Trinity; the session-minting and checkpoint-retention facts (my 1836Z note); the checker's fixture.

**Your own session:** you have carried a heavy load for almost six hours. Write a successor brief draft now (state, standing permissions and their exact conditions, open orders in order), as you did before, so a rotation costs minutes if your session ends.