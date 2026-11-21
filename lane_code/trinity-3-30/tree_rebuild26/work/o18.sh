set -e; export TZ=UTC; X=/project/community/jjyeung/okh7/x_22c714e1; cd $X; date -u +%TZ
[ "$(sha256sum s26fix_n_go.tar | cut -c1-16)" = c141b9c53701e1aa ] || { echo TAR_BAD; exit 1; }
squeue -j 174085 -h -o '%T %r' | grep -q JobHeldUser || { echo NOT_HELD; exit 1; }
test ! -e s26fix && test ! -e a24m4z12/n_3f55530c; mkdir -m 700 s26fix && tar xf s26fix_n_go.tar -C s26fix
echo "staged seal $(sha256sum s26fix/n_go/SHA256SUMS.txt | cut -c1-16) bad $(cd s26fix/n_go && sha256sum -c SHA256SUMS.txt 2>&1 | grep -vc ': OK$' || true)"
[ "$(sha256sum s26fix/n_go/SHA256SUMS.txt | cut -c1-16)" = b44a4915a0f2bf17 ]
echo "diff vs X/n:"; diff <(cd n && find . -type f | sort | xargs sha256sum) <(cd s26fix/n_go && find . -type f | sort | xargs sha256sum) | grep '^[<>]' | awk '{print $1,$3}' || true
mv n a24m4z12/n_3f55530c && mv s26fix/n_go n
echo "FINAL X/n seal $(sha256sum n/SHA256SUMS.txt | cut -c1-64) bad $(cd n && sha256sum -c SHA256SUMS.txt 2>&1 | grep -vc ': OK$' || true) files $(find n -type f | wc -l) pyc $(find n -name __pycache__ | wc -l)"
sha256sum n/b/a.py n/k/a.json n/k/y.json | cut -c1-80; ls -ld n; squeue -j 174085 -h -o '%i %T %r'; date -u +%TZ
