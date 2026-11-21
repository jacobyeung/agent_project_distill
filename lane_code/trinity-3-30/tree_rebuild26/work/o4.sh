export TZ=UTC; X=/project/community/jjyeung/okh7/x_22c714e1; J=174081
sacct -j $J -n -P -o JobID,State,ExitCode,Elapsed,NodeList | head -4
ls -la $X/o/$J $X/o/${J}_live; echo ---j2.log; cat $X/o/$J/j2.log | cut -c1-300; echo ---j2.err; head -c 1500 $X/o/$J/j2.err; echo ---live; cd $X/o/${J}_live && for f in *; do echo "## $f"; head -c 1800 $f | cut -c1-200; echo; done; du -sb .
