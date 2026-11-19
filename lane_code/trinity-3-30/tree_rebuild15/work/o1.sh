export TZ=UTC; date -u +%TZ; X=/project/community/jjyeung/okh7/x_22c714e1
cat $X/j.sh; echo ====; sed -n 1,40p $X/n/job.sh; echo ====; ls -la $X | head -40; squeue -u $USER -h -o "%i %P %j %T %M" | head
