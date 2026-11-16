KH=/project/community/jjyeung/okh7/x_3b862883; date -u
TZ=UTC squeue -u jjyeung -p general -o '%.10i %.20j %.8T %.10M %.20S %R' 2>&1
TZ=UTC sacct -j 170050 -X -n -o JobID,State,Start,Elapsed,NodeList 2>&1
ls -la $KH/o/ 2>&1 | tail -12
for f in $KH/o/170050.a.steps $KH/o/170050.steps $KH/o/170050.err $KH/o/170050.repack.log; do [ -f $f ] && { echo "== $f"; tail -8 $f; }; done
TZ=UTC sstat -j 170050.batch -n -o AveCPU,MaxRSS,MaxDiskRead,MaxDiskWrite 2>&1
