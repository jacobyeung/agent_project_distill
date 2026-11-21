export TZ=UTC; X=/project/community/jjyeung/okh7/x_22c714e1; J=173964
grep -v '_cgroup_procs_check\|unable to read' $X/o/${J}_x/w.log | cut -c1-300 | tail -60; echo ---; head -c 1500 $X/o/$J/j2.err; echo; echo ---; head -30 $X/o/$J/j2.log | cut -c1-300; ls $X/j | grep 1739 ; sed -n 40,110p $X/j7.py
