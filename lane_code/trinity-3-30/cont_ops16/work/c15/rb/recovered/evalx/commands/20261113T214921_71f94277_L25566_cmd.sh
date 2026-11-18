<!-- recovered by seal_plan: transcript=71f94277 line=25566 utc=2026-11-13T21:49:21.695Z kind=commands original_path=(bash command)  -->
N=$(date -u +%Y%m%dT%H%MZ); C=/scratch/jjyeung/orch_cd; cat > $C/evalx/inbox/${N}_ORCH_URGENT_mount_fix_confirmed_go_corrected_step50.md <<'EOF'
# ORCH, urgent: mount fix confirmed; submit the corrected step-50 rehearsal now, once

I read `ORCHARD_MOUNT_FIX.patch` (742196ff, 78 lines, `orchard_job.py` only), verified the seven pins and digest 5fade132 against packet 951f2f2b, and ran your mount, launcher, return and review-finding tests (34 pass). Receipt: `/scratch/jjyeung/orch_cd/leg_s1_review/ORCHARD_LAUNCHER_RECEIPT_MOUNT_FIX.json`.

**Go:** one corrected step-50 rehearsal submission with a new token and intent, the queue check and the notices line in the same call, as before. Report the job id when it starts; report at once if it refuses, with the storage evidence it now retains.

When it has passed staging and its first generation phase (the path is then proven as far as the read itself), tell me; the step-100 decision read stays pre-authorized once on the rehearsal proving the path and the operator's step-100 attestation.
EOF
T=$(date -u +%Y-%m-%dT%H:%M:%SZ); echo "$T orch-home-distill-79: evalx RESULT 2146Z: mount-id fix ready (packet work/milestone/ORCHARD_MOUNT_CONFIRMATION_REQUEST.json sha 951f2f2b; seven-file digest 5fade132; diff ORCHARD_MOUNT_FIX.patch sha 742196ff, orchard_job.py only). I CONFIRMED: read the 78-line diff (mount selected by the work directory's kernel mnt_id from /proc/self/fdinfo; same predicates; refusal evidence retained), pins and digest verified, 34 tests pass. Wrote leg_s1_review/ORCHARD_LAUNCHER_RECEIPT_MOUNT_FIX.json. GO ($N): one corrected step-50 rehearsal with a new intent. Project free 454.9 GB at 21:44Z." >> $C/ORCH_HANDOFF.md; echo done $N; ls -t $C/orchard_cp2/events | head -n 2