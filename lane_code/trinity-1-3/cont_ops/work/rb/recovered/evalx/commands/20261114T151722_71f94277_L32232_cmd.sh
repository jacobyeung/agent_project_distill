<!-- recovered by seal_plan: transcript=71f94277 line=32232 utc=2026-11-14T15:17:22.819Z kind=commands original_path=(bash command)  -->
N=$(date -u +%Y%m%dT%H%MZ); cat > /scratch/jjyeung/orch_cd/evalx/inbox/${N}_ORCH_RULING_pilot4_queue_refusal.md <<'EOF'
# ORCH ruling on the pilot-4 queue refusal

The refusal was right: the account is shared with main, and main has priority. Main's protected jobs (167739, 167857 to 167861, 167894, 168278) may include one that was waiting for `advanced` behind our production job and started when it ended.

1. Authorized: in your next batched observation call, one read-only listing of this account's jobs on every partition (job id, partition, state, reason, start time, time limit, node, GPU count), saved to a file before any validation. No other new call.
2. Then decide by this rule and act without asking again:
   - **An unlisted job is RUNNING or PENDING on `advanced`:** do not submit to `advanced`. Submit the pilot's `general` fallback packet instead (token ee49236ff, family e2374d64), allowing 169526 and 169530. I have written its control files: `/scratch/jjyeung/orch_cd/leg_s1_review/NATIVE_PILOT_CONTROL_ee49236ff/`. In the same call hold 169530 with exactly `scontrol hold 169530`, and release it with exactly `scontrol release 169530` once the pilot is RUNNING or finished, so the pilot takes the card when the final stop read ends.
   - **The only unlisted jobs are on other partitions (for example `preempt`) and `advanced` shows none of this account's jobs:** submit the `advanced` packet e3e6c6421 as ordered, with those job ids added to the allowance, and name them in your event.
   - **Anything else** (an unlisted job on `general`, or a job you cannot classify): submit nothing and send me the listing.
3. One event with the listing's rows, what you submitted, and the states.
EOF
R=/scratch/jjyeung/orch_cd/leg_s1_review; C=$R/NATIVE_PILOT_CONTROL_ee49236ff; FAM=e2374d642151d63d18e88920f9a0aa7ae861b4aefe588bfde27bee29362ab2ec; test -e $C && { echo exists; exit 1; }; mkdir $C; cp $R/NATIVE_PILOT_CONTROL_e3e6c6421/REVIEW.json $C/REVIEW.json; T=$(date -u +%Y-%m-%dT%H:%MZ); cat > $C/ORDER.md <<EOF
# ORCH launch order: Orchard native routed-read PILOT, step 200 (fourth attempt, general fallback)

Issued $T by orchestrator orch-home-distill-79. One job, one submission, partition general, token ee49236ff, family seal e2374d64, step-200 export artifact baccafbf. Standard pilot mode (P1 to P3, five geometry captures, ten item pairs); it must not enter the scored read. Queue allowance for this submission: ALLOW 169526 169530. Valid only under the condition in my ruling of the same time: an unlisted job of this account is running or pending on the advanced partition, and the advanced packet e3e6c6421 has not been submitted. This order covers this packet only.

LAUNCH EVALX NATIVE pilot 200 general ee49236ff $FAM baccafbf216a7d708cfaf67f6ec6ef4e20692fa45b88c52809580f986c3d1204
EOF
echo "- $(date -u +%Y-%m-%dT%H:%MZ) evalx BLOCKER 1516Z: pilot 4 (advanced, e3e6c6421) refused before sbatch: an unlisted same-account job in the combined general+advanced queue (probably one of main's). Ruled (inbox ${N}_ORCH_RULING_pilot4_queue_refusal.md): one read-only account listing; if an unlisted job is on advanced -> submit the general fallback ee49236ff (control files leg_s1_review/NATIVE_PILOT_CONTROL_ee49236ff/) and hold P0 169530 until the pilot runs; if only on other partitions -> advanced as ordered; else send me the listing." >> /scratch/jjyeung/orch_cd/ORCH_HANDOFF.md; ls $C