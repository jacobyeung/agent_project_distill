X=/project/community/jjyeung/okh7/x_22c714e1; cd $X/q; h=$(grep " k/r.json$" SHA256SUMS.txt | cut -c1-64); echo want $h
for c in $X/a24/q_23d/k/r.json $X/a23/k/r.json $X/a21g/k/r.json $X/a21e/k/r.json $X/a21c/k/r.json $X/a23s/q/k/r.json $X/n/k/r.json; do [ -e $c ] && echo "$(sha256sum $c | cut -c1-64) $c"; done
