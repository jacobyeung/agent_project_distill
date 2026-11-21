export TZ=UTC; date -u +%TZ; X=/project/community/jjyeung/okh7/x_22c714e1; J=173964; O=$X/o/$J
squeue -u $USER -o "%.10i %.10P %.24j %.8T %.10M %R"; sacct -j $J -X -n -o State,End,ExitCode; ls $O | head -30; ls $O/live 2>/dev/null | head; tail -5 $O/live/*.log 2>/dev/null | cut -c1-250 | tail -12; df -BG /project/community | tail -1
