set -e; export TZ=UTC; X=/project/community/jjyeung/okh7/x_22c714e1; cd $X; date -u +%TZ
F=$(df -BG --output=avail /project/community | tail -1 | tr -dc 0-9); echo FREE_GIB $F; [ "$F" -ge 1 ] || { echo LOW; exit 1; }
[ "$(sha256sum up33.tar.part | cut -c1-16)" = df778cf3e494f0d6 ]
test ! -e s33n; mkdir s33n; tar xf up33.tar.part -C s33n; mv up33.tar.part up33.tar
[ "$(sha256sum s33n/s33n_n_go.tar | cut -c1-16)" = b0c03db32dadc4a8 ]
tar xf s33n/s33n_n_go.tar -C s33n
U=u/a7682dae68defb91ed5e19120e8f53c149016d70728c417c817c6c408020a22a
[ "$(sha256sum s33n/a7682dae68defb91ed5e19120e8f53c149016d70728c417c817c6c408020a22a | cut -c1-16)" = a7682dae68defb91 ]
if [ -e $U ]; then echo U_EXISTS; else cp s33n/a7682dae68defb91ed5e19120e8f53c149016d70728c417c817c6c408020a22a $U; fi
echo "U sha $(sha256sum $U | cut -c1-64) bytes $(stat -c %s $U)"
cd s33n/n_go; B=$(sha256sum -c SHA256SUMS.txt 2>&1 | grep -vc ': OK$' || true); echo "staged seal $(sha256sum SHA256SUMS.txt | cut -c1-64) bad $B lines $(wc -l < SHA256SUMS.txt) files $(find . -type f | wc -l) pyc $(find . -name __pycache__ | wc -l)"
[ "$B" = 0 ] && [ "$(sha256sum SHA256SUMS.txt | cut -c1-16)" = 929ab2139b6dd408 ]
sha256sum BUILD.json k/t_e047002134f979bd.tar k/y.json k/c.json k/n.json k/p.json k/j.json | cut -c1-16,66-
cd $X; [ "$(sha256sum n/SHA256SUMS.txt | cut -c1-16)" = 9e809db4e0817adf ] || { echo OLD_N_UNEXPECTED; exit 1; }
test ! -e a24m4z12/n_9e809db4; mv n a24m4z12/n_9e809db4 && mv s33n/n_go n
echo "FINAL X/n seal $(sha256sum n/SHA256SUMS.txt | cut -c1-64) bad $(cd n && sha256sum -c SHA256SUMS.txt 2>&1 | grep -vc ': OK$' || true) files $(find n -type f | wc -l)"
[ "$(sha256sum n/SHA256SUMS.txt | cut -c1-16)" = 929ab2139b6dd408 ] && [ "$(sha256sum jn7.sh | cut -c1-16)" = 98edfd9e1f30f4ba ] && echo JN7_OK
sbatch --hold $X/jn7.sh; sleep 10; squeue -u $USER -h -o "%i %P %j %T %M %R"
