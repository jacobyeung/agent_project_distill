export TZ=UTC; date -u +%TZ; X=/project/community/jjyeung/okh7/x_22c714e1
[ "$(squeue -u $USER -h -o "%j" | grep -c 24d9b8e2)" = 1 ] && cd $X && sbatch $X/jd4.sh; sleep 15
squeue -u $USER -o "%.10i %.10P %.24j %.8T %.10M %.12b %R"
