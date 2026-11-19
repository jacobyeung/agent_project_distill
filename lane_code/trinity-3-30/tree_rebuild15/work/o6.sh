export TZ=UTC; date -u +%TZ; X=/project/community/jjyeung/okh7/x_22c714e1
sacct -j 173353 -n -X -o JobID,State,Elapsed,ExitCode,NodeList | head -2; cat $X/j/a15_cot_ap97f8b3c867_173353.log 2>/dev/null | head -40; ls -la $X/o/173349
test -f $X/o/173349/q.log && tail -c 3000 $X/o/173349/q.log
