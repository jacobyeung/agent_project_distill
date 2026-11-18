KH=/project/community/jjyeung/okh7/x_3b862883; date -u +%T
TZ=UTC sacct -j 170050 -X -n -o State,Elapsed,ExitCode 2>&1
ls -la --time-style=+%T $KH/o/ | awk 'NR>3 {print $5, $6, $7}' | grep -v wtest
tail -3 $KH/o/170050.steps; tail -c 400 $KH/o/170050.err
