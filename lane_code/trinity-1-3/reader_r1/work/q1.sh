P=/project/community/jjyeung/e09e45fda45db
TZ=UTC squeue -j 170854 -h -o '%i %T %M %R' 2>/dev/null; sacct -j 170854 -n -X -o state,elapsed,exitcode 2>/dev/null | head -2
tail -c 600 $P/a/cpu_check.log 2>/dev/null; ls $P/a/c 2>/dev/null
