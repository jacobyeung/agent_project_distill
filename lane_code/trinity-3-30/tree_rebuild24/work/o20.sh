export TZ=UTC; date -u +%TZ; X=/project/community/jjyeung/okh7/x_22c714e1; J=173964
squeue -u $USER -h -o "%i %P %j %T %M"; sacct -j $J -n -o JobID,State,Elapsed | head -6; pgrep -af "w.sh" | head -3; tail -3 $X/o/${J}_x/w.log; ls $X/o/$J | tr '\n' ' '; echo; df -BG /project/community | tail -1 | awk '{print "FREE",$4}'
