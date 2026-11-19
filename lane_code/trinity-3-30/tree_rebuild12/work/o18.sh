export TZ=UTC; X=/project/community/jjyeung/okh7/x_22c714e1; cd $X
sha256sum j.sh | cut -c1-16; squeue -u $USER -h -o '%i %P %j %T' ; sbatch $X/j.sh; sleep 5; squeue -u $USER -o '%.10i %.10P %.22j %.8T %.10M %R'
