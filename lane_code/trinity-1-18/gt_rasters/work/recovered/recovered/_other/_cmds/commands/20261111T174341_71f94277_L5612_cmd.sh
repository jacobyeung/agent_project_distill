<!-- recovered by seal_plan: transcript=71f94277 line=5612 utc=2026-11-11T17:43:41.159Z kind=commands original_path=(bash command)  -->
cd /scratch/jjyeung/orch_cd; T=$(date -u +%Y%m%dT%H%MZ); cat > dose_pool/inbox/${T}_ORCH_ANSWER_t1_size.md <<'EOF'
# ORCH ANSWER (T1 size): yes, with a raised cap of 27 GB for T1 only, in two halves
Good that you stopped and re-measured. /scratch has 148 GB free and other lanes will still write about 15 GB, so:
1. First half: the assets of the first 440 scenes of your list (about 9.5 GB), one stream at 5 MB/s, then their raycast and renders. Check `df -BG /scratch` before the pull, before the raycast and before the renders; stop and post a BLOCKER if free space is below 110 GB at any check.
2. Second half only if /scratch still has at least 115 GB free after the first half's GT.npz files are written; otherwise stop there and report.
3. The instance meshes are needed only for the raycast. When a half's GT.npz files are verified (count, a read-back of each, the parity check you ran on scene0011_00 for five scenes), list that half's mesh files with their total size in out/T1_REMOVABLE.md so the user can remove them; you delete nothing.
4. Everything else in my USER_ANSWER note stands (one stream, the governor, no retry loop). Post a NOTE at the start of each half and one RESULT at the end with rows per type.
EOF
echo "$(date -u +%Y-%m-%dT%H:%MZ) tick 17:43Z: all lanes alive; evwait re-armed. dose_pool QUESTION t1_size: T1 needs ~26 GB on 2-18 /scratch (instance meshes 18.9 GB, GT.npz 7 GB), not 4.6 GB; approved with a 27 GB cap in two halves, free-space checks (stop below 110 GB; second half only at >=115 GB), mesh files listed for the user after the raycast." >> ORCH_HANDOFF.md