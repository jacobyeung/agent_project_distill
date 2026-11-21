export TZ=UTC; X=/project/community/jjyeung/okh7/x_22c714e1; J=173964
sacct -j $J -n -o JobID,State,ExitCode,Start,End,NodeList | head -3
ls -la $X/o/$J $X/o/${J}_x; echo ---j2.log; tail -40 $X/o/$J/j2.log | cut -c1-400; echo ---j2.err; tail -20 $X/o/$J/j2.err | cut -c1-400; echo ---w.log; cat $X/o/${J}_x/w.log | cut -c1-300 | head -40; ls -la $X/j/ | tail -5
