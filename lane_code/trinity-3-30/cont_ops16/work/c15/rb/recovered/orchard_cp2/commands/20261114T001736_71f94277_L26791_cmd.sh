<!-- recovered by seal_plan: transcript=71f94277 line=26791 utc=2026-11-14T00:17:36.611Z kind=commands original_path=(bash command)  -->
N=$(date -u +%Y%m%dT%H%MZ); C=/scratch/jjyeung/orch_cd; cat > $C/orchard_cp2/inbox/${N}_ORCH_RULING_memory_scope_full_copy_not_mid_run_one_metadata_step.md <<'EOF'
# ORCH ruling on BLOCKER 0015Z: no full copy while the trainer runs; one read-only memory step approved

Good catch. Your reading is right: the copier's memory gate looked at its own step group and missed the job-level group, which sat at 768 GB of 859 GB.

## 1. The full copy will not run while the trainer is running

Three facts decide it: the lone upload stream measured 129 MB/s (below my bound); the copy would add about 113 GB of reads and 113 GB of dirty writes to a job group already at 89% of its limit; and a mid-run exact-resume point is worth little next to the milestone exports that are already on GCS. The state copy stays alive only as the **end-of-allocation fallback**: after the trainer has exited, and only if the wrapper cannot write the slot to the project filesystem. leg_s1_canary is analysing that variant; it changes nothing in the agreed runbook until I say so in writing.

Finish the cheap run's dispositions as you planned. Keep both memory flags false.

## 2. One read-only memory step inside the job (approved, once)

The job-level group at 89% matters for production itself, and nothing in hand says how much of it is reclaimable file cache. Approved: ONE read-only step that prints, for `/sys/fs/cgroup/system.slice/slurmstepd.scope/s8FXM7AR3HQC00` and for each of its immediate child groups: `memory.current`, `memory.max`, `memory.high`, `memory.swap.current`, `memory.events`, `memory.pressure`, and from `memory.stat` the lines `anon`, `file`, `active_file`, `inactive_file`, `file_dirty`, `file_writeback`, `shmem`, `slab_reclaimable`, `slab_unreclaimable`, `kernel`. Nothing else is read; nothing is written on the node.

Conditions: the proven metadata-step form (absolute paths, your encoded transport, raw saved first); at most 2 CPUs and 60 s; not within 10 minutes of a save or a milestone export (the step-200 export is due about 01:20Z, the next save about 01:53Z); production checked before and after with step times; no retry if it fails. Report the table, the share of anon plus unreclaimable memory against the limit, and the `memory.events` counters (`high`, `max`, `oom`, `oom_kill`).

If anon plus unreclaimable memory is above 60% of the limit, or `oom_kill` is nonzero, mark the event URGENT.
EOF
cat > $C/leg_s1_canary/inbox/${N}_ORCH_ADDENDUM_memory_scope_finding_and_end_of_allocation_variant.md <<'EOF'
# ORCH addendum to the 0004Z task: the memory gate missed the job-level group; analyse the end-of-allocation variant

**New fact** (operator BLOCKER 0015Z; evidence `/scratch/jjyeung/orch_cd/orchard_cp2/out/STATE_COPY_CHEAP_169097_b9bfe98f/memory_scope_failure.json`): the helper sampled only its own step group (`.../step_5/user`, 18.7 MB of an 859 GB limit). The job-level ancestor `.../s8FXM7AR3HQC00` has the same limit and was at 768 GB (89.4%), above the copier's 85% threshold. Allocation identity came back UNAVAILABLE, so trainer membership is unauthenticated. I have approved one read-only step that will print the job group's anon/file breakdown and event counters; the operator will post it.

**My ruling:** the full copy does not run while the trainer runs. It survives only as the end-of-allocation fallback: after the trainer has exited, and only if the wrapper cannot write the slot to the project filesystem.

**So change the task's emphasis.** Items 1 and 2 of the 0004Z task stand (what the cheap run proves; duration by phase). Replace items 3 to 5 with:
3. The memory gate: which group must be sampled (the highest-usage finite ancestor, every finite ancestor, or anon plus unreclaimable memory instead of `memory.current`), the right threshold once file cache is separated, and how the helper authenticates that the trainer is in, or has left, that group.
4. The end-of-allocation variant: where it would sit in the runbook (`orchard_cp2/out/RUNBOOK_END_OF_ALLOCATION_469ddece.md`, budget `out/FINAL_HOUR_BUDGET_169097_20261113T234025Z.json`); the time it needs at the measured rates against the time left after the final save, pack and export; what it must check first (trainer exited, final checkpoint complete, slot refused for space); and whether it fits without changes. If it does not fit: the smallest change (concurrent part uploads as the kit's exporter does at 310 to 433 MB/s; one verification pass), with lines touched and what needs re-review.
5. Your recommendation, and what you would build. Build nothing until I answer.
EOF
T=$(date -u +%Y-%m-%dT%H:%M:%SZ); echo "$T orch-home-distill-79: orchard_cp2 BLOCKER 0015Z: cheap copy's five server objects pass independent generation-bound confirmation (record sha 80168c2c), but FULL-COPY ADMISSION FAILS THE MEMORY CHECKS: the helper sampled only its step group; the job-level cgroup .../s8FXM7AR3HQC00 was at 767,968,198,656 of 858,993,459,200 B (89.4%, above the copier's 85%); allocation identity UNAVAILABLE (out/STATE_COPY_CHEAP_169097_b9bfe98f/memory_scope_failure.json sha 06661000). No anon/file breakdown in hand. RULING ($N): the full copy never runs while the trainer runs; it survives only as the end-of-allocation fallback (after trainer exit, only if the slot cannot be written); ONE read-only in-job memory step approved (job cgroup and children: current, max, high, events, pressure, stat lines; 2 CPUs, 60 s, not within 10 min of a save or export, no retry; URGENT if anon+unreclaimable > 60% of the limit or oom_kill nonzero). ADDENDUM to leg_s1_canary ($N): analyse the memory gate and the end-of-allocation variant; build nothing. Re-armed evwait (b24m9e3ks)." >> $C/ORCH_HANDOFF.md; echo $N