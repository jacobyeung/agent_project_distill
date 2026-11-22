J=174369
export TZ=UTC; date -u +%TZ; X=/project/community/jjyeung/okh7/x_22c714e1; O=$X/o/$J
squeue -u $USER -o "%.10i %.10P %.24j %.8T %.10M %R"; sacct -j $J -X -n -o State,Start,End,ExitCode
grep -v "KITX_OK\|remove_list\|pool_source\|archive members verified\|staged$" $X/j/$J.log | tail -12 | cut -c1-300
test -f $O/db_bytes.json && head -c 1200 $O/db_bytes.json; ls -l $O 2>/dev/null | head -60
