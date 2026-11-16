export TZ=UTC; KH=/project/community/jjyeung/okh7/x_8417c021; J=170109
date -u +%FT%TZ; squeue -j $J -o '%i %T %M %N' 2>&1 | tail -1
cat $KH/o/$J.a.steps 2>&1 | tail -5; tail -4 $KH/o/$J.steps 2>&1; tail -c 400 $KH/o/$J.err 2>&1
