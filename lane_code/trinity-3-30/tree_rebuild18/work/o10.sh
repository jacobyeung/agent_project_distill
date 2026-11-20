export TZ=UTC; date -u +%TZ; X=/project/community/jjyeung/okh7/x_22c714e1; P=/project/community/jjyeung/okh7/x_ee227714
D=$X/u/e5be8157d855b4c9f611876b7fde5d0c7d8bd11def319e15c00e37daef2c3536
if [ ! -e $D ]; then h=$(sha256sum $P/k/t_b83a8a35d420815b.tar | cut -c1-64); [ "$h" = e5be8157d855b4c9f611876b7fde5d0c7d8bd11def319e15c00e37daef2c3536 ] && cp $P/k/t_b83a8a35d420815b.tar $D.part && mv $D.part $D && chmod 0400 $D && echo COPIED; fi
ls -l $D; sha256sum $D | cut -c1-16; ls $X/u | grep -c .; ls $X/u | grep 7a910565; grep -l 7a910565 $P/SHA256SUMS* 2>/dev/null; grep 7a910565 $P/SHA256SUMS* 2>/dev/null | head -3
