set -e; export TZ=UTC; date -u +%TZ; X=/project/community/jjyeung/okh7/x_22c714e1; cd $X; test -f s24m4w.tar.part && test ! -e s24m4w.tar && test ! -e s24m4w && test ! -e c_b434e746w || { echo EXISTS; exit 1; }
squeue -u $USER -h -o "%j" | grep -q d1efc29326c7 && { echo QUEUED; exit 1; }
mv s24m4w.tar.part s24m4w.tar
[ "$(sha256sum s24m4w.tar | cut -c1-64)" = 0a5d0df80a6305c84825d961165c43de38cd1f948d7cdc4560f1ec8955123655 ] || { echo TAR BAD; exit 1; }
mkdir -m 700 s24m4w && tar xf s24m4w.tar -C s24m4w && echo S 24m4w $(find s24m4w -type f | wc -l)
if [ -d s24m4w/u ]; then for f in $(ls s24m4w/u); do if [ -e u/$f ]; then cmp -s u/$f s24m4w/u/$f || { echo U DIFF $f; exit 1; }; else cp s24m4w/u/$f u/$f && echo U ADDED $f; fi; done; fi
mkdir -m 700 c_b434e746w && cp -a qd c_b434e746w/qd && cp -a s24m4w/qd/. c_b434e746w/qd/
cd c_b434e746w/qd; for f in $(find . -type f | sed 's#^\./##'); do case $f in BUILD.json|SHA256SUMS.txt) ;; *) grep -q "  $f\$" SHA256SUMS.txt || { echo "EXTRA $f"; exit 1; } ;; esac; done
[ "$(sha256sum SHA256SUMS.txt | cut -c1-64)" = b434e7461861219b06180d596b595c6bac026c5f70a92096a3ab19ad30e1f0c1 ] && [ "$(sha256sum -c SHA256SUMS.txt 2>&1 | grep -vc ': OK$')" = 0 ] && [ -z "$(find . -name __pycache__)" ] || { echo CAND SEAL BAD; exit 1; }
echo CAND c_b434e746w/qd seal $(sha256sum SHA256SUMS.txt | cut -c1-16) files $(find . -type f | wc -l)
cd $X; mkdir -m 700 c_b434e746w/rcj && cp -a rcj/. c_b434e746w/rcj/ && if [ -d s24m4w/rcj ]; then cp -a s24m4w/rcj/. c_b434e746w/rcj/; fi; echo CAND RCJ; (cd c_b434e746w/rcj && sha256sum * | cut -c1-16,65-); RS=$X/rcj/rcj.sh; [ -f s24m4w/rcj/rcj.sh ] && RS=$X/s24m4w/rcj/rcj.sh; sed "s#^ROOT=/project/community/jjyeung/okh7/x_22c714e1/qd\$#ROOT=$X/c_b434e746w/qd#; s#^H=/project/community/jjyeung/okh7/x_22c714e1/rcj\$#H=$X/c_b434e746w/rcj#" $RS > c_b434e746w/rcj.sh; chmod 700 c_b434e746w/rcj.sh; grep -n "^ROOT=\|^H=" c_b434e746w/rcj.sh; diff rcj/rcj.sh c_b434e746w/rcj.sh | wc -l
for f in x.py:d8517333228a4cac pc.py:bd87252b711f9a2b nd.py:eb0ba92e7e989752 ch.py:16d7210bbca556a0 f.json:37cbc05d134a0129 ps.py:6945292e167d9f60 P_SAMPLE_I.json:fff742bb8ca70d50; do [ "$(sha256sum rcj/${f%%:*} | cut -c1-16)" = "${f##*:}" ] || { echo "BAD rcj/$f"; exit 1; }; done
[ "$(sha256sum qd/SHA256SUMS.txt | cut -c1-16)" = 221d17824d467daa ] || { echo REVIEWED QD CHANGED; exit 1; }
cd c_b434e746w/qd && sbatch --job-name=a15_cot_apd1efc29326c7 ../rcj.sh r; sleep 15
squeue -u $USER -o "%.10i %.10P %.24j %.8T %.10M %R"
