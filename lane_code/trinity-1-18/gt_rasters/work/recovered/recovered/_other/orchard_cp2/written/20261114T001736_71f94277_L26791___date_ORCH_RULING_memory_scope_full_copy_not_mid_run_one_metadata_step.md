<!-- recovered by seal_plan: transcript=71f94277 line=26791 utc=2026-11-14T00:17:36.611Z kind=written original_path=/scratch/jjyeung/orch_cd/orchard_cp2/inbox/$(date_ORCH_RULING_memory_scope_full_copy_not_mid_run_one_metadata_step.md heredoc_quoted -->
# ORCH ruling on BLOCKER 0015Z: no full copy while the trainer runs; one read-only memory step approved

Good catch. Your reading is right: the copier's memory gate looked at its own step group and missed the job-level group, which sat at 768 GB of 859 GB.

## 1. The full copy will not run while the trainer is running

Three facts decide it: the lone upload stream measured 129 MB/s (below my bound); the copy would add about 113 GB of reads and 113 GB of dirty writes to a job group already at 89% of its limit; and a mid-run exact-resume point is worth little next to the milestone exports that are already on GCS. The state copy stays alive only as the **end-of-allocation fallback**: after the trainer has exited, and only if the wrapper cannot write the slot to the project filesystem. leg_s1_canary is analysing that variant; it changes nothing in the agreed runbook until I say so in writing.

Finish the cheap run's dispositions as you planned. Keep both memory flags false.

## 2. One read-only memory step inside the job (approved, once)

The job-level group at 89% matters for production itself, and nothing in hand says how much of it is reclaimable file cache. Approved: ONE read-only step that prints, for `/sys/fs/cgroup/system.slice/slurmstepd.scope/s8FXM7AR3HQC00` and for each of its immediate child groups: `memory.current`, `memory.max`, `memory.high`, `memory.swap.current`, `memory.events`, `memory.pressure`, and from `memory.stat` the lines `anon`, `file`, `active_file`, `inactive_file`, `file_dirty`, `file_writeback`, `shmem`, `slab_reclaimable`, `slab_unreclaimable`, `kernel`. Nothing else is read; nothing is written on the node.

Conditions: the proven metadata-step form (absolute paths, your encoded transport, raw saved first); at most 2 CPUs and 60 s; not within 10 minutes of a save or a milestone export (the step-200 export is due about 01:20Z, the next save about 01:53Z); production checked before and after with step times; no retry if it fails. Report the table, the share of anon plus unreclaimable memory against the limit, and the `memory.events` counters (`high`, `max`, `oom`, `oom_kill`).

If anon plus unreclaimable memory is above 60% of the limit, or `oom_kill` is nonzero, mark the event URGENT.