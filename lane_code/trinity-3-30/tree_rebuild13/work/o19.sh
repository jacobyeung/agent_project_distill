set -e; X=/project/community/jjyeung/okh7/x_22c714e1; cd $X/q; cp -p $X/a23/k/r.json k/r.json
for K in q n; do cd $X/$K; echo "$K seal $(sha256sum SHA256SUMS.txt | cut -c1-16) bad $(sha256sum -c SHA256SUMS.txt 2>&1 | grep -vc ': OK$') files $(find . -type f | wc -l) lines $(wc -l < SHA256SUMS.txt) pyc $(find . -name __pycache__ | wc -l)"; done
ls $X/s24 $X/s24c; find $X/s24 -type f | wc -l; find $X/s24c -type f | wc -l
