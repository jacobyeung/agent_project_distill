export TZ=UTC; date -u +%TZ; X=/project/community/jjyeung/okh7/x_22c714e1; squeue -u $USER -o "%.10i %.10P %.24j %.8T %.10M %R"; sacct -j 173911,173912 -X -n -o JobID,State,End,ExitCode
ls -l $X/o/173911 2>&1 | head; test -f $X/o/173911/E2.json && head -c 2500 $X/o/173911/E2.json; echo
ls $X/o/173912 2>&1 | tr '\n' ' ' | head -c 1500; echo; tail -3 $X/o/173912/j2.log 2>/dev/null | cut -c1-200; df -BG --output=avail /project/community | tail -1
