<!-- recovered by seal_plan: transcript=71f94277 line=14545 utc=2026-11-12T18:38:15.471Z kind=commands original_path=(bash command)  -->
cd /scratch/jjyeung/orch_cd; T=$(date -u +%Y%m%dT%H%MZ); cat > orchard_cp2/inbox/${T}_ORCH_GO_legs1_relaunch_dda73081.md <<EOF
# ORCH GO ($T): relaunch LEG-S1 from kit dda73081, conditional on your arrival checks AND the compute-node probe; submit once

**Authority.** Replacement kit dda73081 (leg_s1_tree RESULT 1836Z; I verified its manifest 367e2f5e..., all 98 entries, the certificate 7fc7f074... and READY status myself): source 37845077 (the import fix, independently reviewed PASS), config 9bf43b64, run 0f541672, persistent root r/7bbb848f. Written authorization: my note in leg_s1_tree/inbox (1730Z), bound as k/4.json. Main agreed to the leg on advanced at 15:33Z and writes first if it needs the partition.

**Submit only if every line holds:**
1. Push arrived whole (push manifest sha 3e23e4eb..., 101 files): SHA256SUMS verifies (98 members), ANON_OK.json sha 7fc7f074..., k/0.json as leg_s1_tree's RESULT states, modes check passes (b/ read-only; root, o/ and arm/ writable).
2. Full b/a.py from /home/jjyeung/okit/x/dda73081 returns 0 with bytecode writing off.
3. Wrapper jl5.sh names kit home x/dda73081, run 0f541672, persistent root r/7bbb848f; that root holds only your empty probe file. The old root r/0d67d2c5 and kit f7ae68ad are untouched.
4. **The probe job on general returned PASS on all four lines** (preflight p, t, u under bwrap with the job's mount layout; the lazy third-party module list). Post RESULT probe either way. If it has not started 20 minutes after its submission, post a QUESTION and wait for my word.
5. One squeue call: no job of ours running or pending on advanced (main's eight held or dependent jobs are expected and stay untouched); MaxSubmit has room.
6. /project/community has at least 400 GB free.
7. Export sessions minted for the new run (m50, m100, m200, m400, m600, m800, m1000, three stop generations), sess.json placed, full b/a.py passes again.
Then submit the wrapper once with \`env -u TK_JOB_START sbatch\`. If any line fails: no submit, BLOCKER with evidence.

**After the submit:** as my 1519Z GO: NOTE with job id and estimate; 10-minute polls while pending; from RUNNING, 1-minute checks. New landmarks to report as they land: the preflight's PASS line and its seconds (it runs before the bulk staging: a failure there is a BLOCKER within the first minutes), the staging, the mode p admission receipt with counts beside NO_FLAG_MIX.md, the type report in the first hour, the first-step admission on four ranks, step time and per-stream losses, the first save with the slot copy. Stop rule and no-resubmission rule unchanged. Tell orchard_port by inbox at each export's \`.done\` line.
EOF
echo "$(date -u +%FT%TZ) orch-home-distill-79: leg_s1_tree RESULT 1836Z: certified replacement kit work/kit_s1_importfix_final_b = dda73081 (manifest 367e2f5e, certificate 7fc7f074; push manifest sha 3e23e4eb, 101 files); I verified manifest (98/98), certificate identity, READY + authorized, 4.json modes p/t/u, config 9bf43b64, expiry 11-26; job.sh order = a.py, p0.sh preflight, g.py, r8.py, r.sh. Wrote the conditional GO orchard_cp2/inbox/${T}_ORCH_GO_legs1_relaunch_dda73081.md (seven lines incl. the compute-node probe PASS)." >> ORCH_HANDOFF.md