set -e; export TZ=UTC; X=/project/community/jjyeung/okh7/x_22c714e1; cd $X; date -u +%TZ
F=$(df -BG --output=avail /project/community | tail -1 | tr -dc 0-9); echo FREE_GIB $F; [ "$F" -ge 1 ] || { echo LOW; exit 1; }
[ "$(sha256sum s34_n_go.tar.part | cut -c1-16)" = 163cf1974bc753ed ]
test ! -e s34; mkdir s34; tar xf s34_n_go.tar.part -C s34; mv s34_n_go.tar.part s34_n_go.tar
cd s34/n_go; B=$(sha256sum -c SHA256SUMS.txt 2>&1 | grep -vc ': OK$' || true); echo "staged seal $(sha256sum SHA256SUMS.txt | cut -c1-64) bad $B lines $(wc -l < SHA256SUMS.txt) files $(find . -type f | wc -l) pyc $(find . -name __pycache__ | wc -l)"
[ "$B" = 0 ] && [ "$(sha256sum SHA256SUMS.txt | cut -c1-16)" = 7e23bbddb052a6f3 ]
sha256sum BUILD.json k/t_e047002134f979bd.tar k/y.json k/c.json k/n.json k/p.json k/j.json b/a.py b/pf.py | cut -c1-16,66-
cd $X; [ "$(sha256sum n/SHA256SUMS.txt | cut -c1-16)" = 929ab2139b6dd408 ] || { echo OLD_N_UNEXPECTED; exit 1; }
test -e u/a7682dae68defb91ed5e19120e8f53c149016d70728c417c817c6c408020a22a
test ! -e a24m4z12/n_929ab213; mv n a24m4z12/n_929ab213 && mv s34/n_go n
echo "FINAL X/n seal $(sha256sum n/SHA256SUMS.txt | cut -c1-64) bad $(cd n && sha256sum -c SHA256SUMS.txt 2>&1 | grep -vc ': OK$' || true) files $(find n -type f | wc -l)"
[ "$(sha256sum n/SHA256SUMS.txt | cut -c1-16)" = 7e23bbddb052a6f3 ] && [ "$(sha256sum jn7.sh | cut -c1-16)" = 98edfd9e1f30f4ba ] && echo JN7_OK
sbatch --hold $X/jn7.sh; sleep 10; squeue -u $USER -h -o "%i %P %j %T %M %R"
