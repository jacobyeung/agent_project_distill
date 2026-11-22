export TZ=UTC; date -u +%TZ; squeue -j 174378 -h -o '%i|%T|%N|%M'; sacct -j 174378 -X -n -P -o State,Elapsed
grep -v 'error:' ~/a15o/f23/main_174378.out | sed -n '/== run 4 ranks/,$p' | cut -c1-900 | head -30; ls ~/a15o/f23/o_174378 2>/dev/null
