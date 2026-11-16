<!-- recovered by seal_plan: transcript=71f94277 line=22994 utc=2026-11-13T17:20:30.157Z kind=written original_path=/scratch/jjyeung/orch_cd/orchard_cp2/inbox/20261113T1720Z_ORCH_ANSWER_size_read_inside_job_approved.md  -->
# ORCH answer (2026-11-13T17:20Z): the read-only size step inside job 169097 is approved, with timing and limits

Approved, because the answer changes two decisions that need hours of notice: the free space the wrapper's guard will require, and whether the slot copy fits the last hour (a slot twice the reference size would not, at 275 MB/s write and 163 MB/s re-read).

## When

- **Not during admission or the first step.** Wait until the final data receipt is observed and step 1 has been recorded, so the step cannot coincide with the launch probe, model load or the first optimizer step.
- **One step then.** If no complete checkpoint exists yet at that time, a **second identical step** is approved once the first complete checkpoint is recorded, so that the two measurements together give the wrapper's real `need` (latest complete checkpoint, `inputs/`, `binding.json`, hard links counted at each name). No third step without a new answer.

## Limits

- `srun --jobid=169097 --overlap`, one task, one CPU, 1 GiB, no GPU, a one-minute step time limit, lowest CPU and IO priority.
- Metadata only (names, sizes, link counts, modification times), your ten-second budget and entry cap, an incomplete lower bound if the budget ends. No payload read, no hash, no write anywhere on the node, no signal, nothing left running.
- Record the exact command, the step id, its exit state and the job's state before and after in the snapshot. If the step is refused, queued or fails, do not retry; report it.
- Check the job's log tail and GPU utilisation line before and after the step; if anything in the job changes across it, tell me at once.

## Then

Post one RESULT with: `inputs/` bytes and file count, the checkpoint's bytes if seen, the resulting `need + 20 GB`, and the slot write and re-read times at the measured rates. Update the runbook's last-hour budget and the free-space alarm floor (alarm at `need + 20 GB` plus 100 GB) from those numbers.
