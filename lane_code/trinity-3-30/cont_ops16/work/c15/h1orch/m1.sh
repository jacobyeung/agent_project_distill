export TZ=UTC
K=/project/community/jjyeung/okh7/x_4b3114cf; J=170527
date -u +%TZ
squeue -j $J -h -o "%i %T %M %N %R %S" 2>&1
ls -la --time-style=+%H:%M:%S $K/o 2>&1 | tail -n 12 | awk '{print $1,$5,$6,$7}'
for f in $K/o/$J.err $K/o/$J.w.steps $K/o/$J.steps; do test -f $f && { echo "== $f"; tail -n 6 $f | cut -c1-300; }; done
