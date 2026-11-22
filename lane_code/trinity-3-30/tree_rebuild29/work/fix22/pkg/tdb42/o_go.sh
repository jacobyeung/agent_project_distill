set -e; export TZ=UTC; date -u +%TZ; X=/project/community/jjyeung/okh7/x_22c714e1; cd $X; SUBMIT=${SUBMIT:-0}
# Stage the mode-r candidate for tree db42866fd9e8d0090276686527e8ebd8837ab2a9401609d81039b8784187f034 beside the reviewed kits (pattern of tree_rebuild22/work/o12.sh), then submit rcj mode r if SUBMIT=1.
F=$(df -BG --output=avail /project/community | tail -1 | tr -dc 0-9); echo FREE_GIB $F; [ "$F" -ge 20 ] || { echo BELOW_FLOOR; exit 1; }
test -f s29r2.tar.part && test ! -e s29r2.tar && test ! -e s29r2 && test ! -e c_01d9f931r || { echo EXISTS; exit 1; }
squeue -u $USER -h -o "%j" | grep -q d1efc29326c7 && { echo QUEUED; exit 1; }
[ "$(sha256sum qd/SHA256SUMS.txt | cut -c1-16)" = 8ae781f4cd655a53 ] || { echo REVIEWED_QD_CHANGED; exit 1; }
for f in x.py:7fe00c24ecf605cb rcj.sh:b23393f2db4dfe65 pc.py:bd87252b711f9a2b nd.py:d7055420a7096bc1 ch.py:c931ab55d8f6e4d6 f.json:8be6cc6338406fa1 ps.py:6945292e167d9f60 P_SAMPLE_I.json:fff742bb8ca70d50; do [ "$(sha256sum rcj/${f%%:*} | cut -c1-16)" = "${f##*:}" ] || { echo "BAD reviewed rcj/$f"; exit 1; }; done
[ "$(sha256sum s29r2.tar.part | cut -c1-64)" = 1f6747f0ab21f4c666d2a3fc5d62ff856de7e050577a5ad3107e9d8099846679 ] || { echo TAR_BAD; exit 1; }
mv s29r2.tar.part s29r2.tar; mkdir -m 700 s29r2 && tar xf s29r2.tar -C s29r2 && echo "S29R files $(find s29r2 -type f | wc -l)"
for f in $(ls s29r2/u); do [ "$(sha256sum s29r2/u/$f | cut -c1-64)" = "$f" ] || { echo "U HASH BAD $f"; exit 1; }; if [ -e u/$f ]; then cmp -s u/$f s29r2/u/$f || { echo "U DIFF $f"; exit 1; }; else cp s29r2/u/$f u/$f && echo "U ADDED $f"; fi; done
mkdir -m 700 c_01d9f931r && cp -a qd c_01d9f931r/qd && cp -a s29r2/qd/. c_01d9f931r/qd/
cd c_01d9f931r/qd; for f in $(find . -type f | sed 's#^\./##'); do case $f in BUILD.json|SHA256SUMS.txt) ;; *) grep -q "  $f\$" SHA256SUMS.txt || { echo "EXTRA $f"; exit 1; } ;; esac; done
[ "$(sha256sum SHA256SUMS.txt | cut -c1-64)" = 01d9f9310bf696c6d4f5873de05863aa07674b71116de2d3b11ba262b3928770 ] && [ "$(sha256sum -c SHA256SUMS.txt 2>&1 | grep -vc ': OK$')" = 0 ] && [ -z "$(find . -name __pycache__)" ] || { echo CAND_SEAL_BAD; exit 1; }
[ "$(sha256sum k/t_e047002134f979bd.tar | cut -c1-64)" = f5db525fc8efcf69c99ec43fd29ba029f6fd54fc0465c0431780643ecf8e47d5 ] || { echo CAND_TREE_TAR_BAD; exit 1; }
echo "CAND c_01d9f931r/qd seal $(sha256sum SHA256SUMS.txt | cut -c1-16) files $(find . -type f | wc -l)"
cd $X; mkdir -m 700 c_01d9f931r/rcj && cp -a rcj/. c_01d9f931r/rcj/ && cp -a s29r2/rcj/. c_01d9f931r/rcj/
for f in x.py:7fe00c24ecf605cb pc.py:bd87252b711f9a2b nd.py:acd40fd59145d7f4 ch.py:0b2fb5b04f1692d8 f.json:8be6cc6338406fa1 ps.py:6945292e167d9f60 P_SAMPLE_I.json:fff742bb8ca70d50 ; do [ "$(sha256sum c_01d9f931r/rcj/${f%%:*} | cut -c1-16)" = "${f##*:}" ] || { echo "BAD cand rcj/$f"; exit 1; }; done
cp s29r2/rcj_c.sh c_01d9f931r/rcj.sh; chmod 700 c_01d9f931r/rcj.sh; [ "$(sha256sum c_01d9f931r/rcj.sh | cut -c1-64)" = 2da5cad3ebda3648f5ea96f5615756cb052f069747b218e104936a26f1d36ddb ] || { echo RCJ_SH_BAD; exit 1; }
grep -n "^ROOT=\|^H=" c_01d9f931r/rcj.sh; [ "$(diff rcj/rcj.sh c_01d9f931r/rcj.sh | grep -c '^[<>]')" = 7 ] || { echo RCJ_SH_DIFF_BAD; exit 1; }
echo "CAND rcj.sh $(sha256sum c_01d9f931r/rcj.sh | cut -c1-16)"
if [ "$SUBMIT" = 1 ]; then cd c_01d9f931r/qd && sbatch --job-name=a15_cot_apd1efc29326c7 ../rcj.sh r; sleep 15; fi
squeue -u $USER -o "%.10i %.10P %.24j %.8T %.10M %R"
