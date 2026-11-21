export TZ=UTC; X=/project/community/jjyeung/okh7/x_22c714e1
sacct -j 173964 -n -P -o JobID,JobName%20,State,ExitCode,Start,End,Elapsed,MaxRSS,MaxDiskWrite,MaxDiskRead | head -20
echo ===wlog; grep -v '_cgroup_procs_check\|unable to read' $X/o/173964_x/w.log | tail -80; echo ===wsh; cat $X/o/173964_x/w.sh; echo ===y; cat $X/o/173964_y/ls.txt $X/o/173964_y/r.log; ls -la $X/o/173964_y/ev $X/o/173964_y/live
echo ===j2full; head -c 2500 $X/o/173964/j2.log
