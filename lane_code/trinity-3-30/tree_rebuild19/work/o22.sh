export TZ=UTC; date -u +%TZ; X=/project/community/jjyeung/okh7/x_22c714e1
[ "$(squeue -u $USER -h -n a15_cot_ap24d9b8e2 | wc -l)" = 1 ] && sbatch -p preempt $X/jd5.sh; sleep 30
squeue -u $USER -o "%.10i %.10P %.24j %.8T %.10M %.12b %R"; squeue -p preempt -h -t PD -o "%u %b" | sort | uniq -c | head -5
