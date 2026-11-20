set -e; export TZ=UTC; date -u +%TZ; X=/project/community/jjyeung/okh7/x_22c714e1
KS="q n qd"
test -d $X/s24m4w && test ! -e $X/a24m4w && ! squeue -u $USER -h -o "%j" | grep -q a15_cot_ap
echo S24M4W $(find $X/s24m4w -type f | wc -l)
mkdir -m 700 $X/a24m4w
if [ -d $X/s24m4w/u ]; then for f in $(cd $X/s24m4w && find u -type f); do b=$(basename $f); h=$(sha256sum $X/s24m4w/$f | cut -c1-64); [ "$h" = "$b" ] || { echo "U HASH BAD $f"; exit 1; }; if [ -e $X/$f ]; then cmp -s $X/s24m4w/$f $X/$f || { echo "DIFFERS $f"; exit 1; }; else mv $X/s24m4w/$f $X/$f; fi; done; fi
for K in $KS; do cd $X/s24m4w/$K; for f in $(find . -type f | sed "s#^\./##"); do mkdir -p $X/$K/$(dirname $f); if [ -e $X/$K/$f ]; then mkdir -p $X/a24m4w/over_$K/$(dirname $f); mv $X/$K/$f $X/a24m4w/over_$K/$f; fi; mv $f $X/$K/$f; done; done
for K in $KS; do cd $X/$K; for f in $(find . -type f | sed 's#^\./##'); do case $f in BUILD.json|SHA256SUMS.txt) ;; *) grep -q "  $f\$" SHA256SUMS.txt || { mkdir -p $X/a24m4w/extra_$K/$(dirname $f); mv $f $X/a24m4w/extra_$K/$f; echo "moved extra $K/$f"; } ;; esac; done
 echo "$K seal $(sha256sum SHA256SUMS.txt | cut -c1-16) bad $(sha256sum -c SHA256SUMS.txt 2>&1 | grep -vc ': OK$') files $(find . -type f | wc -l) lines $(wc -l < SHA256SUMS.txt) pyc $(find . -name __pycache__ | wc -l)"; done
cd $X/s24m4w/rcj; mkdir -p $X/a24m4w/over_rcj; for f in *; do [ -e $X/rcj/$f ] && mv $X/rcj/$f $X/a24m4w/over_rcj/$f; mv $f $X/rcj/$f; done; sha256sum $X/rcj/* | cut -c1-16
cd $X; echo "left in s24m4w: $(find s24m4w -type f | wc -l)"; ls u | wc -l
