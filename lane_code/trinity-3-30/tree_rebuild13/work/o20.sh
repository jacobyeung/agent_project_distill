set -e; export TZ=UTC; X=/project/community/jjyeung/okh7/x_22c714e1
squeue -u $USER -h -o "%i %P %j %T" | grep cbee11a6 && { echo "MY JOB QUEUED"; exit 1; }
cd $X/q; echo "q seal $(sha256sum SHA256SUMS.txt | cut -c1-16) bad $(sha256sum -c SHA256SUMS.txt 2>&1 | grep -vc ': OK$') files $(find . -type f | wc -l) pyc $(find . -name __pycache__ | wc -l)"
sha256sum $X/j.sh $X/l.json | cut -c1-16
ls /project/community/jjyeung/okh7/l_94a76bda/in/e00 >/dev/null && cd $X && sbatch $X/j.sh; sleep 5; squeue -u $USER -o "%.10i %.10P %.24j %.8T %.10M %R"
