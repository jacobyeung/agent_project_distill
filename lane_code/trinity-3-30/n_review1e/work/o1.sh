X=/project/community/jjyeung/okh7/x_22c714e1; cd $X || exit 1
date -u +%TZ; ls -la $X | head -50; ls -la $X/rcj 2>&1 | head; ls -t $X/o | head -8
for k in q n qd; do echo "$k $(sha256sum < $k/SHA256SUMS.txt | cut -c1-64) $(stat -c %y $k/SHA256SUMS.txt)"; done
ls -la jn.sh jd5.sh 2>&1
