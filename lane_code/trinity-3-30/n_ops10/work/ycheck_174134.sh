X=/project/community/jjyeung/okh7/x_22c714e1
echo "YCHECK $(date -u +%FT%TZ)"; sha256sum $X/n/SHA256SUMS.txt $X/n/k/y.json $X/n/b/a.py $X/n_s/sess_174134.json 2>&1 | sed 's#/project/community/jjyeung/okh7/x_22c714e1/##'
grep -E ' k/y\.json$' $X/n/SHA256SUMS.txt
TZ=UTC squeue -j 174134 -h -o '%i|%T|%r|%S' 2>&1
