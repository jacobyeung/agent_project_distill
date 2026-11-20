set -e; export TZ=UTC; date -u +%TZ; X=/project/community/jjyeung/okh7/x_22c714e1
KS="q n qd"
test -d $X/s24m4m && test ! -e $X/a24m4m
echo S24M4M $(find $X/s24m4m -type f | wc -l)
mkdir -m 700 $X/a24m4m
if [ -d $X/s24m4m/u ]; then for f in $(cd $X/s24m4m && find u -type f); do b=$(basename $f); h=$(sha256sum $X/s24m4m/$f | cut -c1-64); [ "$h" = "$b" ] || { echo "U HASH BAD $f"; exit 1; }; if [ -e $X/$f ]; then cmp -s $X/s24m4m/$f $X/$f || { echo "DIFFERS $f"; exit 1; }; else mv $X/s24m4m/$f $X/$f; fi; done; fi
for K in $KS; do cd $X/s24m4m/$K; for f in $(find . -type f | sed "s#^\./##"); do mkdir -p $X/$K/$(dirname $f); if [ -e $X/$K/$f ]; then mkdir -p $X/a24m4m/over_$K/$(dirname $f); mv $X/$K/$f $X/a24m4m/over_$K/$f; fi; mv $f $X/$K/$f; done; done
for K in $KS; do cd $X/$K; for f in $(find . -type f | sed 's#^\./##'); do case $f in BUILD.json|SHA256SUMS.txt) ;; *) grep -q "  $f\$" SHA256SUMS.txt || { mkdir -p $X/a24m4m/extra_$K/$(dirname $f); mv $f $X/a24m4m/extra_$K/$f; echo "moved extra $K/$f"; } ;; esac; done
 echo "$K seal $(sha256sum SHA256SUMS.txt | cut -c1-16) bad $(sha256sum -c SHA256SUMS.txt 2>&1 | grep -vc ': OK$') files $(find . -type f | wc -l) lines $(wc -l < SHA256SUMS.txt) pyc $(find . -name __pycache__ | wc -l)"; done
cd $X/s24m4m/rcj; mkdir -p $X/a24m4m/over_rcj; for f in *; do [ -e $X/rcj/$f ] && mv $X/rcj/$f $X/a24m4m/over_rcj/$f; mv $f $X/rcj/$f; done; sha256sum $X/rcj/* | cut -c1-16
cd $X; echo "left in s24m4m: $(find s24m4m -type f | wc -l)"; ls u | wc -l
export TZ=UTC; date -u +%TZ; X=/project/community/jjyeung/okh7/x_22c714e1; cd $X
squeue -u $USER -h -o "%j" | grep -q d1efc29326c7 && { echo QUEUED; exit 1; }
for f in x.py:9b68e5168b7b692a rcj.sh:b23393f2db4dfe65 pc.py:1fc1c7a883a952aa ps.py:6945292e167d9f60 P_SAMPLE_I.json:fff742bb8ca70d50; do [ "$(sha256sum rcj/${f%%:*} | cut -c1-16)" = "${f##*:}" ] || { echo "BAD rcj/$f"; exit 1; }; done
cd qd && [ "$(sha256sum SHA256SUMS.txt | cut -c1-16)" = 7d358ff593334f17 ] && [ "$(sha256sum -c SHA256SUMS.txt 2>&1 | grep -vc ': OK$')" = 0 ] && sbatch --job-name=a15_cot_apd1efc29326c7 ../rcj/rcj.sh r; sleep 15
squeue -u $USER -o "%.10i %.10P %.24j %.8T %.10M %R"
