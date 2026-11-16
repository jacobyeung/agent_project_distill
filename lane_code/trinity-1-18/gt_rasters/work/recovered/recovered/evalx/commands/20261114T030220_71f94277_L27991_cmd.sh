<!-- recovered by seal_plan: transcript=71f94277 line=27991 utc=2026-11-14T03:02:20.736Z kind=commands original_path=(bash command)  -->
C=/scratch/jjyeung/orch_cd; T=$(date -u +%Y-%m-%dT%H:%M:%SZ); cat >> $C/REMOVAL_CANDIDATES_TRINITY_20261114.md <<EOF
# Removal candidates on Trinity for the user (no agent removes anything)

| Added (UTC) | Host | Path | Size | Why it is safe to remove | Named by |
|---|---|---|---|---|---|
| $T | trinity-1-18 | /dev/shm/jjyeung_evalx/rt/85fc3486 | 19.3 GB (RAM-backed) | base model snapshot; its 13 manifest-pinned files are verified in the copy on trinity-0-28 /scratch/jjyeung/evalx_native_step200_20261114; evalx no longer reads it; check that no other lane uses it | evalx RESULT 20261114T0300Z |
EOF
echo "$T orch-home-distill-79: evalx RESULT 0300Z: native cache on trinity-0-28 at 45.08 GB; /scratch there 153.5 GB free at 02:57Z; export stream 9.60 of 21.58 GB done (one part hash-verified); 14.73 GB remain in total (export 11.99 + depth files 2.75), so about 139 GB free at the end; a storage guard stops the receiver below 130 GB free and never resumes it; nothing else will be written on 0-28. The 19.3 GB base snapshot under /dev/shm on trinity-1-18 is no longer needed by evalx: listed in $C/REMOVAL_CANDIDATES_TRINITY_20261114.md for the user. Re-armed evwait (b403semuy)." >> $C/ORCH_HANDOFF.md