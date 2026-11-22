set -e; export TZ=UTC; date -u +%TZ; X=/scratch/jjyeung/orch_n30/tree_rebuild29/work/fix22/dry/fakeX4/x; cd $X; SUBMIT=${SUBMIT:-0}
# Stage the mode-r candidate for tree 02fd9a95ebd9719c596b39ac80e5247b92c1d6673d6cc2f4956c70b902718041 beside the reviewed kits (pattern of tree_rebuild22/work/o12.sh), then submit rcj mode r if SUBMIT=1.
F=$(df -BG --output=avail /scratch | tail -1 | tr -dc 0-9); echo FREE_GIB $F; [ "$F" -ge 20 ] || { echo BELOW_FLOOR; exit 1; }
test -f s29r2.tar.part && test ! -e s29r2.tar && test ! -e s29r2 && test ! -e c_eb8145adr || { echo EXISTS; exit 1; }
squeue -u $USER -h -o "%j" | grep -q d1efc29326c7 && { echo QUEUED; exit 1; }
[ "$(sha256sum qd/SHA256SUMS.txt | cut -c1-16)" = 8ae781f4cd655a53 ] || { echo REVIEWED_QD_CHANGED; exit 1; }
for f in x.py:7fe00c24ecf605cb rcj.sh:b23393f2db4dfe65 pc.py:bd87252b711f9a2b nd.py:d7055420a7096bc1 ch.py:c931ab55d8f6e4d6 f.json:8be6cc6338406fa1 ps.py:6945292e167d9f60 P_SAMPLE_I.json:fff742bb8ca70d50; do [ "$(sha256sum rcj/${f%%:*} | cut -c1-16)" = "${f##*:}" ] || { echo "BAD reviewed rcj/$f"; exit 1; }; done
[ "$(sha256sum s29r2.tar.part | cut -c1-64)" = f4be6cbddfedbb9f95f793d4d469d74cbf1b6dd4bfb780f0c036ae6294cc25a9 ] || { echo TAR_BAD; exit 1; }
mv s29r2.tar.part s29r2.tar; mkdir -m 700 s29r2 && tar xf s29r2.tar -C s29r2 && echo "S29R files $(find s29r2 -type f | wc -l)"
for f in $(ls s29r2/u); do [ "$(sha256sum s29r2/u/$f | cut -c1-64)" = "$f" ] || { echo "U HASH BAD $f"; exit 1; }; if [ -e u/$f ]; then cmp -s u/$f s29r2/u/$f || { echo "U DIFF $f"; exit 1; }; else cp s29r2/u/$f u/$f && echo "U ADDED $f"; fi; done
mkdir -m 700 c_eb8145adr && cp -a qd c_eb8145adr/qd && cp -a s29r2/qd/. c_eb8145adr/qd/
cd c_eb8145adr/qd; for f in $(find . -type f | sed 's#^\./##'); do case $f in BUILD.json|SHA256SUMS.txt) ;; *) grep -q "  $f\$" SHA256SUMS.txt || { echo "EXTRA $f"; exit 1; } ;; esac; done
[ "$(sha256sum SHA256SUMS.txt | cut -c1-64)" = eb8145ad00f59f9621443259477d8d95a2b25ea027a986e24dc8fcfff6c2663e ] && [ "$(sha256sum -c SHA256SUMS.txt 2>&1 | grep -vc ': OK$')" = 0 ] && [ -z "$(find . -name __pycache__)" ] || { echo CAND_SEAL_BAD; exit 1; }
[ "$(sha256sum k/t_e047002134f979bd.tar | cut -c1-64)" = 30c4d56426af1a3c4f7420430ab4771e38476863394b1cb059c5fc305332fff2 ] || { echo CAND_TREE_TAR_BAD; exit 1; }
echo "CAND c_eb8145adr/qd seal $(sha256sum SHA256SUMS.txt | cut -c1-16) files $(find . -type f | wc -l)"
cd $X; mkdir -m 700 c_eb8145adr/rcj && cp -a rcj/. c_eb8145adr/rcj/ && cp -a s29r2/rcj/. c_eb8145adr/rcj/
for f in x.py:7fe00c24ecf605cb pc.py:bd87252b711f9a2b nd.py:e30e75812f405100 ch.py:3e0228432d44d23e f.json:8be6cc6338406fa1 ps.py:6945292e167d9f60 P_SAMPLE_I.json:fff742bb8ca70d50 ; do [ "$(sha256sum c_eb8145adr/rcj/${f%%:*} | cut -c1-16)" = "${f##*:}" ] || { echo "BAD cand rcj/$f"; exit 1; }; done
cp s29r2/rcj_c.sh c_eb8145adr/rcj.sh; chmod 700 c_eb8145adr/rcj.sh; [ "$(sha256sum c_eb8145adr/rcj.sh | cut -c1-64)" = 167ecc865d38d0538eedb4610bbeaf6a2d2affb3c4c72af4b4d5ac71ecde4f5d ] || { echo RCJ_SH_BAD; exit 1; }
grep -n "^ROOT=\|^H=" c_eb8145adr/rcj.sh; [ "$(diff rcj/rcj.sh c_eb8145adr/rcj.sh | grep -c '^[<>]')" = 7 ] || { echo RCJ_SH_DIFF_BAD; exit 1; }
echo "CAND rcj.sh $(sha256sum c_eb8145adr/rcj.sh | cut -c1-16)"
if [ "$SUBMIT" = 1 ]; then cd c_eb8145adr/qd && sbatch --job-name=a15_cot_apd1efc29326c7 ../rcj.sh r; sleep 15; fi
squeue -u $USER -o "%.10i %.10P %.24j %.8T %.10M %R"
