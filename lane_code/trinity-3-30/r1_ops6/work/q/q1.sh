export TZ=UTC
date -u +%FT%TZ
squeue -u $USER -o '%i %j %P %T %M %l %R %b' 2>&1 | head -30
sacct -u $USER -S 2026-11-18T11:00 -X -o JobID,JobName%22,Partition,State,Start,End,Elapsed 2>&1 | head -40
K=/project/community/jjyeung/okh7
ls -la $K/r/673bc60f 2>&1 | head
ls -la $K/x_69d2930d/runs/673bc60f/m200 2>&1 | head
ls $K | head -80 | tr '\n' ' '
