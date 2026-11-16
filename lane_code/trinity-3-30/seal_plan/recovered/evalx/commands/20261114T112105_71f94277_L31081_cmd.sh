<!-- recovered by seal_plan: transcript=71f94277 line=31081 utc=2026-11-14T11:21:05.872Z kind=commands original_path=(bash command)  -->
N=$(date -u +%Y%m%dT%H%MZ); cat > /scratch/jjyeung/orch_cd/if_p0/inbox/${N}_ORCH_TASK_P0_169491_failed_on_load_guard_fix_and_reseal.md <<'EOF'
# ORCH task: P0 job 169491 failed in `prepare` on the CPU load guard; fix, audit every guard, reseal

Job 169491 passed the runtime check and failed in `prepare`: `RuntimeError: Node load 8.83 is above the lane's conservative CPU guard`. The node is shared by design: our own four-GPU training job runs on it, so its load is always high. evalx holds the authenticated failed return (`/scratch/jjyeung/orch_cd/evalx/out/FAILED_RETURN_P0_AUTHENTICATED_S23.json` names it; ask evalx by inbox note if the files are not yet under `inbox_results/a6061d03c58ae2dbf/`).

1. Remove the node-load guard from every phase of the Orchard job (prepare, train, read, packaging). It protects shared Trinity nodes; it has no meaning inside a Slurm allocation.
2. Audit every other environment-dependent refusal in every phase the job runs, from `prepare` to the result archive: load, free memory, free disk, thread counts, GPU state, wall-clock guards, host names, paths. For each, write one line: where it is, what it compares, and what it will see in the real job, using the values recorded in the three failed returns (the node has 48+ busy CPUs, 800 GiB memory mostly file cache, one allocated H100 of eight, a private /tmp). Remove or correct any that a correct shared node could trip. Keep the allocation check and the time-budget guards.
3. Add a CPU test that runs each phase's guards against an environment record taken from the real returns.
4. Reseal as a new kit folder; give me the runtime diff against 799a21dd and the test counts in one RESULT. The science files must stay byte-identical (the 207-file table). I confirm the diff myself if it only removes guards; then you build the `general` and `advanced` packets.
5. The step-timing fix from your 1037Z finding may go into this seal too, since the seal changes anyway. Nothing else from the next-seal list.

This is the third job that failed before training, each one stage later. Treat item 2 as the way to make it the last.
EOF
cat > /scratch/jjyeung/orch_cd/evalx/inbox/${N}_ORCH_ORDER_after_two_failures.md <<'EOF'
# ORCH order after the failures of 169501 and 169491

1. Native pilot: no new submission, no code change, no gate change. An independent debugger is reading the return and the reader's call detection now (brief `/scratch/jjyeung/orch_cd/leg_s1_review/BRIEF_DEBUG_NATIVE_PILOT_PARITY_169501.md`); it reads your files read-only. If you already know from the code how calls are detected during generation (decoded text or token ids) and what the same probe decoded to against the parent, put it in three lines in your step-400 packet event; do not start a separate investigation.
2. P0: make sure the failed return's files are under `/scratch/jjyeung/orch_cd/if_p0/inbox_results/a6061d03c58ae2dbf/` with a one-line note in if_p0's inbox. if_p0 fixes and reseals; you submit nothing until I send a new order.
3. Finish the step-400 packet first. The `general` slot is idle until I order the next job.
EOF
echo "- $(date -u +%Y-%m-%dT%H:%MZ) evalx RESULT 1117Z: BOTH jobs failed. Native pilot 169501: model loaded (96 s, 21.6 GB) then parity gate failed: P1-P3 true but camera_call false (probe 'Read the camera pose at Frame 1 using <pose frame=1>' decoded 33 tokens '< frame=1> < turn=0> < zoom=1.000> </ turn> </ frame>' with zero calls). P0 169491: runtime check passed, prepare refused on the CPU node-load guard (load 8.83). Actions: Opus xhigh debugger on the parity cause (brief leg_s1_review/BRIEF_DEBUG_NATIVE_PILOT_PARITY_169501.md -> DEBUG_NATIVE_PILOT_PARITY_169501.md); if_p0 ordered to remove the load guard, audit every environment guard, reseal; evalx: no resubmission, finish step-400 packet." >> /scratch/jjyeung/orch_cd/ORCH_HANDOFF.md