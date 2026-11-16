<!-- recovered by seal_plan: transcript=71f94277 line=28207 utc=2026-11-14T03:46:18.500Z kind=written original_path=/scratch/jjyeung/orch_cd/if_p0/inbox/$(date_ORCH_TASK_admit_advanced_partition_single_job.md heredoc_quoted -->
# ORCH task: admit the `advanced` partition for the same single one-GPU job, and prepare a second P0 packet for it

## Why

P0 is queued on `general` as job 169413 (token a35f2d78fe7c5ee8d) with a Slurm forecast of 17:59Z, behind the step-200 evaluation read (16:33Z), and it would then hold the one-GPU partition for four hours ahead of the step-400 and final reads. The production leg releases our cap on the `advanced` partition (four GPUs on one node per user, 24-hour limit) when its job ends, at about 15:00Z. P0 can run there as an ordinary single job with one GPU; nothing packed, no job steps.

## Change (smallest possible)

Admit partition `advanced` beside `general` wherever the kit binds the partition: the `sbatch` argument list, `allocation()`, `card()` if it checks the partition, the child environment and the job context, and `validate_context`. The context records the partition the job actually ran in; the launcher takes the partition as an explicit argument limited to those two names, and the packet is bound to it (a packet built for one partition refuses in the other). Everything else is unchanged: one node, one task, eight CPUs, at least 200 GiB, one H100, twelve hours, no requeue, the same preflight order, the same result return.

Check one thing on paper and tell me: on `advanced` the job may land on a node where our own production job ran or another user's jobs run; your mount proof, card check ("one empty 80-GB H100") and free-space floor must hold there exactly as on `general`. If the card check requires the card to be empty, say what it does when a neighbour job uses the other cards of the node (it must only look at its own assigned card).

## Deliver

1. New seal with the diff against 8d5bdd73 (runtime and tests separately), the test count and the rehearsal result.
2. The exact control files I must rewrite for the new seal (same three as before; I will reuse the review text with one more paragraph for this diff).
3. After my confirmation and new control files: a second packet for `advanced` with a fresh token, and an updated hand-off for evalx with both argument lists. Never reuse token a35f2d78fe7c5ee8d.
4. State how duplicates are prevented: the `general` job 169413 stays queued until the `advanced` job has been accepted and has passed its preflight; then I order 169413 cancelled. If 169413 starts first, the `advanced` packet is not submitted. Your kit cannot enforce this; say so and leave it to my orders.