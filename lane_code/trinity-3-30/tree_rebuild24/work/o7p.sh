export TZ=UTC; date -u +%TZ; X=/project/community/jjyeung/okh7/x_22c714e1; J=173963
squeue -u $USER -o "%.10i %.10P %.24j %.8T %.10M %R"; sacct -j $J -X -n -o State,End,ExitCode; ls -la $X/o/$J; head -c 3000 $X/o/$J/p0.json; echo; df -BG /project/community | tail -1
