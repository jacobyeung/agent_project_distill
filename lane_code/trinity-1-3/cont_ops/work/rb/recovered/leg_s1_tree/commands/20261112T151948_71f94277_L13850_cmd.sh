<!-- recovered by seal_plan: transcript=71f94277 line=13850 utc=2026-11-12T15:19:48.321Z kind=commands original_path=(bash command)  -->
cd /scratch/jjyeung/orch_cd; T=$(date -u +%Y%m%dT%H%MZ); cat > orchard_cp2/inbox/${T}_ORCH_GO_legs1_launch.md <<EOF
# ORCH GO ($T): launch LEG-S1 from kit f7ae68ad, conditional on your own arrival checks; submit once, no second look from me needed

**Authority.** Final kit f7ae68ad (leg_s1_tree RESULT 1516Z; I verified its manifest c5f3df0d..., all 96 entries, the certificate f18166b0... and READY status myself). Written authorization: my notes in leg_s1_tree/inbox (1409Z, 1426Z), bound as k/4.json: world 4, account mt01, partition advanced, modes p/t/u, one chained job at a time, 24 h each, valid to 2026-11-26. Main released its advanced card at 14:43Z (its notices log, line 107) and asks for no further GPU work.

**Submit only if every line holds (check in as few ssh calls as you can):**
1. Push arrived whole: the kit's SHA256SUMS verifies on Orchard (96 members), ANON_OK.json sha f18166b0..., k/0.json sha 11249ee2..., and leg_s1_tree's mode check passes (b/ read-only; root and o/ writable).
2. Full b/a.py from the pinned path /home/jjyeung/okit/x/f7ae68ad returns 0, with bytecode writing off. Not --build-only.
3. Wrapper j/0d67d2c5.sh names kit home x/f7ae68ad, run f9d0a7b9 and persistent root r/0d67d2c5; that root is a real writable folder and holds nothing r8.py would read as an earlier leg (read r8.py for what it looks at; say what your probe file is to it; do not run r8.py).
4. One squeue call: user jjyeung has no running or pending job on partition advanced.
5. /project/community has at least 400 GB free.
6. Export sessions minted for m50, m100, m200, m400, m600, m800, m1000 and the three stop generations; sess.json in the kit home (outside the manifest inventory: confirm b/a.py still passes after you place it; if a.py counts it, stop and tell me).
Then: \`cd /home/jjyeung/okit && env -u TK_JOB_START sbatch /home/jjyeung/okit/j/0d67d2c5.sh\`, once. If any line fails, do not submit; post a BLOCKER with the evidence.

**After the submit.** NOTE at once with the job id, the node and Slurm's start estimate. While pending, poll every 10 minutes. From RUNNING: 1-minute checks of process liveness and of new log lines until the admission receipt, the first GPU step and the first save have each landed; two empty one-minute checks in a row mean read the logs and report at once. Then lengthen to 5 minutes.
- **Admission (mode p):** when the data receipt exists, post its counts beside the expected mix (leg_s1_tree/out/NO_FLAG_MIX.md): routing 57,136 = camera programs 35,423 + absolute-distance programs 11,728 + room programs 581 + direct route rows 9,404; the VQA stream's per-type counts (the inherited reference is 121,703); removal and exclusion counts. Run the type report (tr7.sh through srun --jobid --overlap) in the first hour.
- **Stop rule in the first hour:** if a stream or a type that the mix table lists is missing, or a program row of a type outside the five routed types is present, request a saved stop (\`scancel -s USR1 -b <job>\`) and post a BLOCKER. Do the same on any refusal of the first-step admission.
- **First step and first save:** post step time, the per-stream losses of the first steps, GPU memory per rank, then the first save's size, the slot copy's result and free space in /tmp and in project space.
- Never resubmit after a failure or a cluster kill without my written word. A SLOT_SKIPPED marker is an event for me at once.
- 168042 and 168043 stay pending and untouched; I rule on them after the first save.
Milestone exports: tell orchard_port by inbox when each \`.done\` line appears (m50, m100, m200).
EOF
echo "$(date -u +%FT%TZ) orch-home-distill-79: wrote orchard_cp2/inbox/${T}_ORCH_GO_legs1_launch.md: conditional GO for LEG-S1 from kit f7ae68ad (six arrival checks, submit once, first-hour checks, stop rule, no resubmit without my word). Main released its advanced card at 14:43Z (log line 107)." >> ORCH_HANDOFF.md