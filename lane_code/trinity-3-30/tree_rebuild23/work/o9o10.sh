set -e; export TZ=UTC; date -u +%TZ; X=/project/community/jjyeung/okh7/x_22c714e1
F=$(df -BG --output=avail /project/community | tail -1 | tr -dc 0-9); echo FREE_GIB $F; [ "$F" -ge 20 ] || { echo BELOW_FLOOR; exit 1; }
KS="q n qd"
test -d $X/s24m4y2 && test ! -e $X/a24m4y2 && ! squeue -u $USER -h -o "%j" | grep -q a15_cot_ap
echo S24M4Y2 $(find $X/s24m4y2 -type f | wc -l)
mkdir -m 700 $X/a24m4y2
if [ -d $X/s24m4y2/u ]; then for f in $(cd $X/s24m4y2 && find u -type f); do b=$(basename $f); h=$(sha256sum $X/s24m4y2/$f | cut -c1-64); [ "$h" = "$b" ] || { echo "U HASH BAD $f"; exit 1; }; if [ -e $X/$f ]; then cmp -s $X/s24m4y2/$f $X/$f || { echo "DIFFERS $f"; exit 1; }; else mv $X/s24m4y2/$f $X/$f; fi; done; fi
for K in $KS; do cd $X/s24m4y2/$K; for f in $(find . -type f | sed "s#^\./##"); do mkdir -p $X/$K/$(dirname $f); if [ -e $X/$K/$f ]; then mkdir -p $X/a24m4y2/over_$K/$(dirname $f); mv $X/$K/$f $X/a24m4y2/over_$K/$f; fi; mv $f $X/$K/$f; done; done
for K in $KS; do cd $X/$K; for f in $(find . -type f | sed 's#^\./##'); do case $f in BUILD.json|SHA256SUMS.txt) ;; *) grep -q "  $f\$" SHA256SUMS.txt || { mkdir -p $X/a24m4y2/extra_$K/$(dirname $f); mv $f $X/a24m4y2/extra_$K/$f; echo "moved extra $K/$f"; } ;; esac; done
 echo "$K seal $(sha256sum SHA256SUMS.txt | cut -c1-16) bad $(sha256sum -c SHA256SUMS.txt 2>&1 | grep -vc ': OK$') files $(find . -type f | wc -l) lines $(wc -l < SHA256SUMS.txt) pyc $(find . -name __pycache__ | wc -l)"; done
cd $X/s24m4y2/rcj; mkdir -p $X/a24m4y2/over_rcj; for f in *; do [ -e $X/rcj/$f ] && mv $X/rcj/$f $X/a24m4y2/over_rcj/$f; mv $f $X/rcj/$f; done; sha256sum $X/rcj/* | cut -c1-16
cd $X; echo "left in s24m4y2: $(find s24m4y2 -type f | wc -l)"; ls u | wc -l
export TZ=UTC; date -u +%TZ; X=/project/community/jjyeung/okh7/x_22c714e1; cd $X
F=$(df -BG --output=avail /project/community | tail -1 | tr -dc 0-9); echo FREE_GIB $F; [ "$F" -ge 20 ] || { echo BELOW_FLOOR; exit 1; }
squeue -u $USER -h -o "%j" | grep -q d1efc29326c7 && { echo QUEUED; exit 1; }
for f in x.py:7fe00c24ecf605cb rcj.sh:b23393f2db4dfe65 pc.py:bd87252b711f9a2b nd.py:d7055420a7096bc1 ch.py:c931ab55d8f6e4d6 f.json:8be6cc6338406fa1 ps.py:6945292e167d9f60 P_SAMPLE_I.json:fff742bb8ca70d50; do [ "$(sha256sum rcj/${f%%:*} | cut -c1-16)" = "${f##*:}" ] || { echo "BAD rcj/$f"; exit 1; }; done
for K in q:df93cfba9769ca82 n:797255ae1421d27f qd:8ae781f4cd655a53; do [ "$(sha256sum ${K%%:*}/SHA256SUMS.txt | cut -c1-16)" = "${K##*:}" ] && [ "$(cd ${K%%:*} && sha256sum -c SHA256SUMS.txt 2>&1 | grep -vc ': OK$')" = 0 ] || { echo "BAD kit $K"; exit 1; }; done
cd qd && sbatch --job-name=a15_cot_apd1efc29326c7 ../rcj/rcj.sh r; sleep 15
squeue -u $USER -o "%.10i %.10P %.24j %.8T %.10M %R"
