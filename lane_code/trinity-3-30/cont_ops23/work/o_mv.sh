K=/project/community/jjyeung/okh7; SP=$K/ae71c903
for R in dd982cd5c4b250002a564 dc863c3e6b41d0002a4ca; do
  if test -d $SP/$R && ! test -e ${SP}_fetched/$R; then mv $SP/$R ${SP}_fetched/$R && echo "moved $R"; else echo "not moved $R: $(ls -d $SP/$R ${SP}_fetched/$R 2>&1 | tr '\n' ' ')"; fi
done
ls $SP; sha256sum ${SP}_fetched/dd982cd5c4b250002a564/result.tar.gz
