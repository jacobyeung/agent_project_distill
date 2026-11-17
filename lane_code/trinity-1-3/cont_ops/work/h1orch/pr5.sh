export TZ=UTC
K=/project/community/jjyeung/okh7/x_3fdda0fb; J=170669
sacct -j $J -X -n -o JobID,State,ExitCode,Start,End,Partition,MaxRSS 2>&1 | head
sacct -j $J -n -o JobID,State,MaxRSS 2>&1 | head
squeue -u jjyeung -o '%i %j %P %T %M %R' 2>&1
squeue -p advanced -h -o '%i %u %j %T %b %R' 2>&1 | head -20
ls -la $K/o | tail -20
for f in $K/o/$J.proof.json; do test -s $f && { echo "== $f"; cut -c1-3000 $f; echo; }; done
for f in $K/o/$J.w.steps $K/o/$J.steps $K/o/$J.proof.log $K/o/$J.proof.err $K/o/$J.err; do test -s $f && { echo "== $f"; tail -n 12 $f | cut -c1-300; }; done
O=/project/community/jjyeung/okh7; B=$O/i_1be16f28; ls -la $B | head -30
df -h /project/community 2>&1 | tail -1
