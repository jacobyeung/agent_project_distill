set -e; export TZ=UTC; date -u +%TZ; X=/project/community/jjyeung/okh7/x_22c714e1
squeue -u $USER -h -o "%i %P %j %T" | grep -E "24d9b8e2" && { echo "DISCOVERY QUEUED/RUNNING; stop"; exit 1; }
test -d $X/s24m3 && test ! -e $X/a24m3
echo S24M3 $(find $X/s24m3 -type f | wc -l)
mkdir -m 700 $X/a24m3
for f in $(cd $X/s24m3 && find u -type f); do b=$(basename $f); h=$(sha256sum $X/s24m3/$f | cut -c1-64); [ "$h" = "$b" ] || { echo "U HASH BAD $f"; exit 1; }; if [ -e $X/$f ]; then cmp -s $X/s24m3/$f $X/$f || { echo "DIFFERS $f"; exit 1; }; else mv $X/s24m3/$f $X/$f; fi; done
for K in q n qd; do cd $X/s24m3/$K; for f in $(find . -type f | sed "s#^\./##"); do mkdir -p $X/$K/$(dirname $f); if [ -e $X/$K/$f ]; then mkdir -p $X/a24m3/over_$K/$(dirname $f); mv $X/$K/$f $X/a24m3/over_$K/$f; fi; mv $f $X/$K/$f; done; done
for K in q n qd; do cd $X/$K; for f in $(find . -type f | sed 's#^\./##'); do case $f in BUILD.json|SHA256SUMS.txt) ;; *) grep -q "  $f\$" SHA256SUMS.txt || { mkdir -p $X/a24m3/extra_$K/$(dirname $f); mv $f $X/a24m3/extra_$K/$f; echo "moved extra $K/$f"; } ;; esac; done
 echo "$K seal $(sha256sum SHA256SUMS.txt | cut -c1-16) bad $(sha256sum -c SHA256SUMS.txt 2>&1 | grep -vc ': OK$') files $(find . -type f | wc -l) lines $(wc -l < SHA256SUMS.txt) pyc $(find . -name __pycache__ | wc -l)"; sha256sum -c SHA256SUMS.txt 2>&1 | grep -v ": OK$" | head -5; done
cd $X; echo "left in s24m3: $(find s24m3 -type f | wc -l)"; sha256sum jd2.sh dbb2.py | cut -c1-16; ls u | wc -l
grep -c . qd/k/a.json >/dev/null; python3 -c "import json;d=json.load(open('$X/qd/k/a.json'));print('qd GO',d.get('GO'))"; python3 -c "import json;d=json.load(open('$X/n/k/a.json'));print('n GO',d.get('GO'))"
