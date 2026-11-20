export TZ=UTC; date -u +%TZ; X=/project/community/jjyeung/okh7/x_22c714e1
squeue -u $USER -h -o "%i %P %j %T" | grep -E "24d9b8e2" && { echo QUEUED; exit 1; }
cd $X && [ "$(sha256sum qd/SHA256SUMS.txt | cut -c1-16)" = 259c14de1ff04938 ] && [ "$(sha256sum jd4.sh | cut -c1-16)" = 3059f049d2070fd0 ] && sbatch -p advanced $X/jd4.sh; sleep 20
squeue -u $USER -o "%.10i %.10P %.24j %.8T %.10M %.12b %R"; squeue -p advanced -h -o "%u %T %b %N" | sort | uniq -c | head
