export TZ=UTC; date -u +%TZ; X=/project/community/jjyeung/okh7/x_22c714e1
st=$(squeue -j 173056 -h -o %T 2>/dev/null); g=$(squeue -u $USER -p general -h -o %i | wc -l); echo "173056=$st general_ours=$g"
if [ "$st" = "PENDING" ] && [ "$g" = "0" ]; then scancel 173056 && sleep 3 && sbatch -p general $X/j.sh; fi
sleep 5; squeue -u $USER -o '%.10i %.10P %.22j %.8T %.10M %R'
