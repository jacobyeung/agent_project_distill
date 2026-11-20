X=/project/community/jjyeung/okh7/x_22c714e1; cd $X || exit 1; TZ=UTC date +%TZ
ls -la; ls -la jn.sh 2>&1; ls rcj; sha256sum rcj/* 2>/dev/null | head -30; ls -d c_* ; for d in c_*; do ls $d; done; ls -t o | head -10; ls -la j | tail -6
for k in q n qd; do echo "$k $(sha256sum < $k/SHA256SUMS.txt | cut -c1-64)"; done
