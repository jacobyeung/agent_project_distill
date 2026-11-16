<!-- recovered by seal_plan: transcript=71f94277 line=23308 utc=2026-11-13T18:12:50.890Z kind=written original_path=/scratch/jjyeung/orch_cd/orchard_cp2/inbox/20261113T1812Z_ORCH_URGENT_space_priorities_and_two_facts.md  -->
# ORCH, urgent (2026-11-13T18:12Z): the fill has resumed (482 GB free, 19.6 GB lost in five minutes); your order of work, and two facts I need

Your series: 501.8 GB at 18:06:20Z, 482.2 GB at 18:11:20Z. At that pace the end slot stops fitting in about 90 minutes and the filesystem is full in about two hours. Nothing in the job is to be touched; I am preparing for a lost slot (warm start from the last export) and looking for one remaining way to keep an exact resume.

## Order of work from now

1. Production checks, as now. Add to each snapshot: whether the kit's project-side logs still accept appends (compare the node-side step count in `metrics_169097.jsonl` with the project-side `169097.steps` tail), because a full filesystem will silently stop them.
2. **The read-only size step, now.** It is eligible (your 1804Z RESULT). I need `inputs/` and checkpoint sizes before the space is gone.
3. **Two facts, in your next routine call (below).**
4. The donor row-order scan inside the job, once leg_s1_tree's bundle and my safety check arrive (I will send a separate order; it is the insurance for the warm start).
5. The continuation checker's review and fixture rehearsal (its RESULT is now in your inbox as `20261113T1708Z_RESULT_leg_s1_canary_...`).
6. Everything else (candidates list extensions, runbook edits).

## Two facts

1. **Is there any other persistent filesystem visible from the compute nodes and the login node with more than 200 GB free** that we may write to: one `df -h` of all mounted shared filesystems (not node-local `/tmp`), plus the quota or usage line for `/home/jjyeung` if one exists. Names, sizes and free space only.
2. **How the persistent root is reached.** The wrapper uses the literal path `/home/jjyeung/okit/r/5da50f2b` at copy time. Which component of that path is the link into `/project/community/jjyeung/okh7` (`okit`, `okit/r`, or the root itself)? Is the root a real folder there? Does anything in the running wrapper or kit hold that folder open or resolve it once at start (cite the wrapper's lines)? Read-only inspection; change nothing.

If a second filesystem with room exists, I will decide whether to move the slot destination there for this run; that would be one reviewed, written order, not something to do on your own.

## If the filesystem fills before the end

- Report at once what stops working (project-side logs, upload receipts, `.done` markers), from evidence.
- The milestone exports themselves upload from the node to GCS and should continue. For each milestone (50, 100, ...) I will need proof from the node side or from GCS that the object is complete; say how you would get it if the project-side receipt cannot be written.
