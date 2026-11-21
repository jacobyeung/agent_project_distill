set -e; export TZ=UTC; date -u +%TZ; X=/project/community/jjyeung/okh7/x_22c714e1; cd $X
F=$(df -BG --output=avail /project/community | tail -1 | tr -dc 0-9); echo FREE_GIB $F; [ "$F" -ge 20 ] || { echo BELOW_FLOOR_20; exit 1; }
[ "$(sha256sum s24m4z12a.tar | cut -c1-16)" = ef17f2dce632a1e4 ] || { echo TAR_BAD; exit 1; }
test ! -e s24m4z12a && test ! -e a24m4z12; squeue -u $USER -h | grep -q . && { echo JOBS_RUNNING; exit 1; }
mkdir -m 700 s24m4z12a && tar xf s24m4z12a.tar -C s24m4z12a && cd s24m4z12a
B=$(sha256sum -c MANIFEST.sha 2>&1 | grep -vc ': OK$' || true); echo MANIFEST_BAD $B; [ "$B" = 0 ]
for k in q n n_go; do echo "$k seal $(sha256sum $k/SHA256SUMS.txt | cut -c1-16) bad $(cd $k && sha256sum -c SHA256SUMS.txt 2>&1 | grep -vc ': OK$' || true)"; done
echo "--- X/q vs armed q"; diff <(cd $X/q && find . -type f | sort | xargs sha256sum) <(cd q && find . -type f | sort | xargs sha256sum) | grep '^[<>]' | awk '{print $1,$3}' | cut -c1-60 || true
echo "--- X/n vs armed n_go"; diff <(cd $X/n && find . -type f | sort | xargs sha256sum) <(cd n_go && find . -type f | sort | xargs sha256sum) | grep '^[<>]' | awk '{print $1,$3}' | cut -c1-60 || true
U=u/a49f117f60add326e1ef3e8eb2b92a73ec299425e8efb477fa9e84d462789e73; cmp $U $X/$U && echo U_SAME
cd $X; mkdir -m 700 a24m4z12
mv q a24m4z12/q && mv s24m4z12a/q q
mv n a24m4z12/n && mv s24m4z12a/n_go n
mv s24m4z12a/n a24m4z12/n_armed_go_false
for k in q n; do echo "FINAL X/$k seal $(sha256sum $k/SHA256SUMS.txt | cut -c1-64) bad $(cd $k && sha256sum -c SHA256SUMS.txt 2>&1 | grep -vc ': OK$' || true) files $(find $k -type f | wc -l) pyc $(find $k -name __pycache__ | wc -l)"; done
ls -ld q n a24m4z12/*; sha256sum n/k/a.json q/BUILD.json n/BUILD.json | cut -c1-90; date -u +%TZ
