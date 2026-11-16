<!-- recovered by seal_plan: transcript=71f94277 line=28430 utc=2026-11-14T04:06:56.633Z kind=commands original_path=(bash command)  -->
N=$(date -u +%Y%m%dT%H%MZ); C=/scratch/jjyeung/orch_cd; cat > $C/if_p0/inbox/${N}_ORCH_NOTE_general_queue_moved_advanced_variant_is_backup.md <<'EOF'
# ORCH note: the one-GPU queue moved; the `advanced` variant is now a backup

The step-200 evaluation read (job 169367) started at 03:32Z, far ahead of its forecast, and should end at about 04:40Z. Your P0 job 169413 is pending only on the one-running-job limit, so it may start on `general` right after that.

Finish the `advanced` admission you are working on and deliver it as ordered (it is a small diff and I want it sealed and confirmed as a backup, and for the later arms), but do not expect it to be submitted for P0: if 169413 starts first, the `advanced` packet for P0 is never sent. No rush on it.

When P0 starts, evalx posts its staging, preflight and namespace smoke test observations; I will forward anything that needs you.
EOF
T=$(date -u +%Y-%m-%dT%H:%M:%SZ); echo "$T orch-home-distill-79: evalx(19) RESULT 0406Z: STEP-200 direct read job 169367 is RUNNING on orchard-community-4 since 03:32:31Z (H100; staging, bind, layout done; main generation since 03:43:20Z; return expected ~04:40Z); IF-P0 P0 job 169413 PENDING on QOSMaxJobsPerUserLimit (starts after 169367 ends if resources allow). The advanced variant of P0 becomes a backup (note to if_p0 $N). Re-armed evwait (bgr3clifq)." >> $C/ORCH_HANDOFF.md