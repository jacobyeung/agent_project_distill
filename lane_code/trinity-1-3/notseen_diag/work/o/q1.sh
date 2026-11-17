export TZ=UTC; date -u +%FT%TZ; hostname
W=/project/community/jjyeung/okh7/e6fc152498; T=b01ec87a6f29b00029ad2; P=/project/community/jjyeung/okh7/ae71c903/$T
ls -la $W/r2/sj/h10sub3_$T $W/r2/sj/h10ret_$T
ls -la $W/r2/sj/h10ret_$T/* | head -30
tar tzvf $P/result.tar.gz | awk '{print $3, $6}' | head -80
ls -la $W/p446 | head -40
cd $W/p446 && find . -maxdepth 3 -type d | head -60
cd $W/p446 && grep -rn --include=*.py -e "not seen" . | cut -c1-220 | head -60
