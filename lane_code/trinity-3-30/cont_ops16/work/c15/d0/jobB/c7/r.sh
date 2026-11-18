export TZ=UTC; P=/project/community/jjyeung/okh7/ae71c903/a4cadd8934b
date -u +%T; squeue -h -j 170320 -o '%i %T %M %S %N %r' 2>&1; sacct -n -X -j 170320 -o State,ExitCode,Elapsed -P 2>&1 | head -2; ls -la --time-style=+%T $P 2>&1 | tail -8
