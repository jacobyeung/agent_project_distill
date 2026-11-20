export TZ=UTC; date -u +%TZ; X=/project/community/jjyeung/okh7/x_22c714e1
squeue -u $USER -h -o "%i %P %j %T" | grep -E "24d9b8e2" && { echo QUEUED; exit 1; }
cd $X && [ "$(sha256sum qd/SHA256SUMS.txt | cut -c1-16)" = e7f3239497a8c7a8 ] && sbatch -p advanced $X/jd2.sh && sbatch $X/jd2.sh; sleep 20
squeue -u $USER -o "%.10i %.10P %.24j %.8T %.10M %.12b %R"
