X=/project/community/jjyeung/okh7/x_22c714e1; date -u +%TZ
sha256sum $X/rcj/* 
for k in q n qd; do (cd $X/$k && echo "$k check: $(nice -n 10 sha256sum -c --quiet SHA256SUMS.txt 2>&1 | head -3 | tr '\n' ' ') rc=$? files=$(wc -l < SHA256SUMS.txt)"); done
ls -t $X/o | head -3; J=$(ls -t $X/o | head -1); echo "latest $J"; ls -la $X/o/$J | head -40; ls $X/jn.sh 2>&1
