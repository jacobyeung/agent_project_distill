<!-- recovered by seal_plan: transcript=71f94277 line=14573 utc=2026-11-12T18:41:53.507Z kind=commands original_path=(bash command)  -->
cd /scratch/jjyeung/orch_cd; T=$(date -u +%Y%m%dT%H%MZ); cat > orchard_cp2/inbox/${T}_ORCH_GO_AMENDED_submit_now_probe_in_parallel.md <<EOF
# ORCH ($T): GO amended: submit the leg NOW to hold its place in the queue; run the probe in parallel

Slurm's estimate for advanced is now 04:03Z tomorrow, and estimates have been unreliable in both directions (168749 started four minutes after an estimate of four hours). Queue age is worth more than waiting for the probe, and a pending job costs nothing.
1. **Now:** lines 1, 2, 3, 5 and 6 of my 1838Z GO hold by your 1840Z RESULT. Mint the export sessions, place sess.json, rerun full b/a.py (line 7), then submit once: \`cd /home/jjyeung/okit && env -u TK_JOB_START sbatch /home/jjyeung/okit/j/7bbb848f.sh\`. NOTE with the job id and estimate.
2. **Probe (line 4) in parallel:** submit the general-partition probe as soon as leg_s1_tree's script and sbatch line arrive (one line in main's log, 1-minute checks, RESULT probe with four verdicts).
   - Probe PASS: nothing to do; say so in the RESULT.
   - Probe shows a traceback while the leg is still pending: \`scontrol hold <leg job>\` at once (it keeps its age), then BLOCKER to me and leg_s1_tree.
   - Probe shows a traceback while the leg is running: BLOCKER to me at once with the failing module and where the leg is (preflight, staging, mode p, training); do not stop the leg yourself unless it is still before the mode p receipt, in which case cancel it (nothing is saved yet) and say so.
3. If the leg starts before the probe has run, its own preflight is the first check: report its PASS line or its failure within the first minutes.
Everything after the submit is as the 1838Z GO states.
EOF
echo "$(date -u +%FT%TZ) orch-home-distill-79: GO AMENDED (orchard_cp2/inbox/${T}_ORCH_GO_AMENDED_submit_now_probe_in_parallel.md): fresh test-only estimate for advanced is 2026-11-13T04:03Z (aanis' four 4-GPU jobs ahead); submit the leg now from kit dda73081 to hold queue age; the compute-node probe runs in parallel; probe traceback while pending -> scontrol hold; while running -> BLOCKER (cancel only before the mode p receipt)." >> ORCH_HANDOFF.md