set -e; export TZ=UTC; date -u +%TZ; X=/scratch/jjyeung/orch_n30/tree_rebuild29/work/fix22/dry/fakeX2/x; cd $X; SUBMIT=${SUBMIT:-0}
# Stage the mode-r candidate for tree 6fa18a6e1d7d8306d7317688447da24b0aef7e202b45171ad5765440d7d61226 beside the reviewed kits (pattern of tree_rebuild22/work/o12.sh), then submit rcj mode r if SUBMIT=1.
F=$(df -BG --output=avail /scratch | tail -1 | tr -dc 0-9); echo FREE_GIB $F; [ "$F" -ge 20 ] || { echo BELOW_FLOOR; exit 1; }
test -f s29r.tar.part && test ! -e s29r.tar && test ! -e s29r && test ! -e c_f2da65dcr || { echo EXISTS; exit 1; }
squeue -u $USER -h -o "%j" | grep -q d1efc29326c7 && { echo QUEUED; exit 1; }
[ "$(sha256sum qd/SHA256SUMS.txt | cut -c1-16)" = 8ae781f4cd655a53 ] || { echo REVIEWED_QD_CHANGED; exit 1; }
for f in x.py:7fe00c24ecf605cb rcj.sh:b23393f2db4dfe65 pc.py:bd87252b711f9a2b nd.py:d7055420a7096bc1 ch.py:c931ab55d8f6e4d6 f.json:8be6cc6338406fa1 ps.py:6945292e167d9f60 P_SAMPLE_I.json:fff742bb8ca70d50; do [ "$(sha256sum rcj/${f%%:*} | cut -c1-16)" = "${f##*:}" ] || { echo "BAD reviewed rcj/$f"; exit 1; }; done
[ "$(sha256sum s29r.tar.part | cut -c1-64)" = 8f21e0f1bb087b02b049f69a20aabada78f66079cfda9bb3dffaba83028c04e6 ] || { echo TAR_BAD; exit 1; }
mv s29r.tar.part s29r.tar; mkdir -m 700 s29r && tar xf s29r.tar -C s29r && echo "S29R files $(find s29r -type f | wc -l)"
for f in $(ls s29r/u); do [ "$(sha256sum s29r/u/$f | cut -c1-64)" = "$f" ] || { echo "U HASH BAD $f"; exit 1; }; if [ -e u/$f ]; then cmp -s u/$f s29r/u/$f || { echo "U DIFF $f"; exit 1; }; else cp s29r/u/$f u/$f && echo "U ADDED $f"; fi; done
mkdir -m 700 c_f2da65dcr && cp -a qd c_f2da65dcr/qd && cp -a s29r/qd/. c_f2da65dcr/qd/
cd c_f2da65dcr/qd; for f in $(find . -type f | sed 's#^\./##'); do case $f in BUILD.json|SHA256SUMS.txt) ;; *) grep -q "  $f\$" SHA256SUMS.txt || { echo "EXTRA $f"; exit 1; } ;; esac; done
[ "$(sha256sum SHA256SUMS.txt | cut -c1-64)" = f2da65dcebc8563168b952c1bd6042d7c13c2af6707eb8145e029ef0f0d606b4 ] && [ "$(sha256sum -c SHA256SUMS.txt 2>&1 | grep -vc ': OK$')" = 0 ] && [ -z "$(find . -name __pycache__)" ] || { echo CAND_SEAL_BAD; exit 1; }
[ "$(sha256sum k/t_e047002134f979bd.tar | cut -c1-64)" = 416115a19ca9aeeed5e952662810a051d918333326285441111f7b03a6d91d03 ] || { echo CAND_TREE_TAR_BAD; exit 1; }
echo "CAND c_f2da65dcr/qd seal $(sha256sum SHA256SUMS.txt | cut -c1-16) files $(find . -type f | wc -l)"
cd $X; mkdir -m 700 c_f2da65dcr/rcj && cp -a rcj/. c_f2da65dcr/rcj/ && cp -a s29r/rcj/. c_f2da65dcr/rcj/
for f in x.py:7fe00c24ecf605cb pc.py:bd87252b711f9a2b nd.py:f50488211a6a696c ch.py:4d52623879231860 f.json:8be6cc6338406fa1 ps.py:6945292e167d9f60 P_SAMPLE_I.json:fff742bb8ca70d50 ; do [ "$(sha256sum c_f2da65dcr/rcj/${f%%:*} | cut -c1-16)" = "${f##*:}" ] || { echo "BAD cand rcj/$f"; exit 1; }; done
cp s29r/rcj_c.sh c_f2da65dcr/rcj.sh; chmod 700 c_f2da65dcr/rcj.sh; [ "$(sha256sum c_f2da65dcr/rcj.sh | cut -c1-64)" = 7261ffc352b06e5bd0ed6b2d446b2745a4da75a971bb3c3a7cf1a0d605c4f223 ] || { echo RCJ_SH_BAD; exit 1; }
grep -n "^ROOT=\|^H=" c_f2da65dcr/rcj.sh; [ "$(diff rcj/rcj.sh c_f2da65dcr/rcj.sh | grep -c '^[<>]')" = 8 ] || { echo RCJ_SH_DIFF_BAD; exit 1; }
echo "CAND rcj.sh $(sha256sum c_f2da65dcr/rcj.sh | cut -c1-16)"
if [ "$SUBMIT" = 1 ]; then cd c_f2da65dcr/qd && sbatch --job-name=a15_cot_apd1efc29326c7 ../rcj.sh r; sleep 15; fi
squeue -u $USER -o "%.10i %.10P %.24j %.8T %.10M %R"
