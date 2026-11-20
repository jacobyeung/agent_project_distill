X=/project/community/jjyeung/okh7/x_22c714e1; date -u +%TZ
for k in q n qd; do echo "$k $(sha256sum < $X/$k/SHA256SUMS.txt | cut -c1-64)"; done; ls -la $X/rcj; ls -t $X/o | head -3; J=$(ls -t $X/o | head -1); ls -la $X/o/$J | head -30; ls $X/jn.sh 2>&1
