set -e; export TZ=UTC; date -u +%TZ; X=/project/community/jjyeung/okh7/x_22c714e1; cd $X; test -f s24m4x2.tar.part && test ! -e s24m4x2.tar && test ! -e s24m4x2 && test ! -e c_8ae781f4x || { echo EXISTS; exit 1; }
squeue -u $USER -h -o "%j" | grep -q d1efc29326c7 && { echo QUEUED; exit 1; }
mv s24m4x2.tar.part s24m4x2.tar
[ "$(sha256sum s24m4x2.tar | cut -c1-64)" = 2138f327d14d17751a6236cc188cf22c5d8b15cd998c0860a32507bc7272fcb6 ] || { echo TAR BAD; exit 1; }
mkdir -m 700 s24m4x2 && tar xf s24m4x2.tar -C s24m4x2 && echo S 24m4x2 $(find s24m4x2 -type f | wc -l)
if [ -d s24m4x2/u ]; then for f in $(ls s24m4x2/u); do if [ -e u/$f ]; then cmp -s u/$f s24m4x2/u/$f || { echo U DIFF $f; exit 1; }; else cp s24m4x2/u/$f u/$f && echo U ADDED $f; fi; done; fi
mkdir -m 700 c_8ae781f4x && cp -a qd c_8ae781f4x/qd && cp -a s24m4x2/qd/. c_8ae781f4x/qd/
cd c_8ae781f4x/qd; for f in $(find . -type f | sed 's#^\./##'); do case $f in BUILD.json|SHA256SUMS.txt) ;; *) grep -q "  $f\$" SHA256SUMS.txt || { echo "EXTRA $f"; exit 1; } ;; esac; done
[ "$(sha256sum SHA256SUMS.txt | cut -c1-64)" = 8ae781f4cd655a53108b8b0966ecb3a41a5679b19e70d4ddadb472a88bae2784 ] && [ "$(sha256sum -c SHA256SUMS.txt 2>&1 | grep -vc ': OK$')" = 0 ] && [ -z "$(find . -name __pycache__)" ] || { echo CAND SEAL BAD; exit 1; }
echo CAND c_8ae781f4x/qd seal $(sha256sum SHA256SUMS.txt | cut -c1-16) files $(find . -type f | wc -l)
cd $X; mkdir -m 700 c_8ae781f4x/rcj && cp -a rcj/. c_8ae781f4x/rcj/ && if [ -d s24m4x2/rcj ]; then cp -a s24m4x2/rcj/. c_8ae781f4x/rcj/; fi; echo CAND RCJ; (cd c_8ae781f4x/rcj && sha256sum * | cut -c1-16,65-); RS=$X/rcj/rcj.sh; [ -f s24m4x2/rcj/rcj.sh ] && RS=$X/s24m4x2/rcj/rcj.sh; sed "s#^ROOT=/project/community/jjyeung/okh7/x_22c714e1/qd\$#ROOT=$X/c_8ae781f4x/qd#; s#^H=/project/community/jjyeung/okh7/x_22c714e1/rcj\$#H=$X/c_8ae781f4x/rcj#" $RS > c_8ae781f4x/rcj.sh; chmod 700 c_8ae781f4x/rcj.sh; grep -n "^ROOT=\|^H=" c_8ae781f4x/rcj.sh; diff rcj/rcj.sh c_8ae781f4x/rcj.sh | wc -l
for f in x.py:d8517333228a4cac pc.py:bd87252b711f9a2b nd.py:eb0ba92e7e989752 ch.py:16d7210bbca556a0 f.json:37cbc05d134a0129 ps.py:6945292e167d9f60 P_SAMPLE_I.json:fff742bb8ca70d50; do [ "$(sha256sum rcj/${f%%:*} | cut -c1-16)" = "${f##*:}" ] || { echo "BAD rcj/$f"; exit 1; }; done
[ "$(sha256sum qd/SHA256SUMS.txt | cut -c1-16)" = 221d17824d467daa ] || { echo REVIEWED QD CHANGED; exit 1; }
cd c_8ae781f4x/qd && sbatch --job-name=a15_cot_apd1efc29326c7 ../rcj.sh r; sleep 15
squeue -u $USER -o "%.10i %.10P %.24j %.8T %.10M %R"
