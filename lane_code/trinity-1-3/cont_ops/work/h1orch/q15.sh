export TZ=UTC
date -u +%TZ
squeue -u jjyeung -h -o '%i %j %T %E %r' | cut -c1-200
sacct -u jjyeung -S 2026-11-16T18:00 -X -n -o JobID,JobName%28,Partition,State,Start,End | tail -15
