set -e; export TZ=UTC; date -u +%TZ; X=/project/community/jjyeung/okh7/x_22c714e1
KS="q n qd"
test -d $X/s24m4j && test ! -e $X/a24m4j
echo S24M4J $(find $X/s24m4j -type f | wc -l)
mkdir -m 700 $X/a24m4j
for K in $KS; do cd $X/s24m4j/$K; for f in $(find . -type f | sed "s#^\./##"); do mkdir -p $X/$K/$(dirname $f); if [ -e $X/$K/$f ]; then mkdir -p $X/a24m4j/over_$K/$(dirname $f); mv $X/$K/$f $X/a24m4j/over_$K/$f; fi; mv $f $X/$K/$f; done; done
for K in $KS; do cd $X/$K; for f in $(find . -type f | sed 's#^\./##'); do case $f in BUILD.json|SHA256SUMS.txt) ;; *) grep -q "  $f\$" SHA256SUMS.txt || { mkdir -p $X/a24m4j/extra_$K/$(dirname $f); mv $f $X/a24m4j/extra_$K/$f; echo "moved extra $K/$f"; } ;; esac; done
 echo "$K seal $(sha256sum SHA256SUMS.txt | cut -c1-16) bad $(sha256sum -c SHA256SUMS.txt 2>&1 | grep -vc ': OK$') files $(find . -type f | wc -l) lines $(wc -l < SHA256SUMS.txt) pyc $(find . -name __pycache__ | wc -l)"; sha256sum -c SHA256SUMS.txt 2>&1 | grep -v ": OK$" | head -5; done
cd $X; echo "left in s24m4j: $(find s24m4j -type f | wc -l)"; sha256sum jd2.sh dbb2.py | cut -c1-16; ls u | wc -l
grep -c . qd/k/a.json >/dev/null; python3 -c "import json;d=json.load(open('$X/qd/k/a.json'));print('qd GO',d.get('GO'))"; python3 -c "import json;d=json.load(open('$X/n/k/a.json'));print('n GO',d.get('GO'))"
test ! -e $X/rcj && mkdir -m 700 $X/rcj && mv $X/s24m4j/rcj/rcj.sh $X/s24m4j/rcj/x.py $X/rcj/ && sha256sum $X/rcj/* | cut -c1-16; mkdir -p $X/j; ls $X/s24m4j/*
for K in q n qd; do echo "$K $(sha256sum $X/$K/SHA256SUMS.txt | cut -c1-16)"; done
