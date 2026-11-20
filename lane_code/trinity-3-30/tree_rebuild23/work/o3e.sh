J=173881
export TZ=UTC; date -u +%TZ; X=/project/community/jjyeung/okh7/x_22c714e1; J=${J:?}; O=$X/o/$J
squeue -u $USER -o "%.10i %.10P %.24j %.8T %.10M %R"; sacct -j $J -X -n -o State,End,ExitCode
grep -v "KITX_OK\|remove_list\|pool_source\|archive members verified\|staged$" $X/j/$J.log | tail -12 | cut -c1-300
test -f $O/timings.json && cat $O/timings.json | head -30; test -f $O/db_bytes.json && head -c 1200 $O/db_bytes.json; ls $O/rd0 2>/dev/null
test -f $O/proc_check.json && head -c 1500 $O/proc_check.json; echo; ls -l $O | head -40
