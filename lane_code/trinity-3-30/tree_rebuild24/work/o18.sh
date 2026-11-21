export TZ=UTC; date -u +%TZ; X=/project/community/jjyeung/okh7/x_22c714e1; J=173964
squeue -u $USER -h -o "%i %P %j %T %M"; sacct -j $J -X -n -o State,End,ExitCode; ls $X/o/$J | tr '\n' ' '; echo; grep -v "verified through\|staged$\|KITX_OK" $X/o/$J/j2.log 2>/dev/null | tail -4 | cut -c1-200; df -BG /project/community | tail -1 | awk '{print "FREE",$4}'
