set -e; export TZ=UTC; X=/project/community/jjyeung/okh7/x_22c714e1; cd $X; date -u +%TZ
F=$(df -BG --output=avail /project/community | tail -1 | tr -dc 0-9); echo FREE_GIB $F; [ "$F" -ge 3 ] || { echo LOW; exit 1; }
squeue -u $USER -h -o "%i %P %j %T %M %R"
[ "$(sha256sum b35.tar.part | cut -c1-64)" = 22c5a563307b0d4ddbd20298ca34fd1bcde0a79acd1ef897a359ac12d4f2e7ab ] && echo BUNDLE_OK
test ! -e in35; mkdir in35; tar xf b35.tar.part -C in35; mv b35.tar.part in35/b35.tar
cd in35; sha256sum s35_n_go.tar jn8.sh u_da19* | cut -c1-16,66-
[ "$(sha256sum s35_n_go.tar | cut -c1-64)" = 3c3b91ebda00a4278f4e50ffe0774d79233c2413482e0d202dd95e7811f2b404 ]
[ "$(sha256sum jn8.sh | cut -c1-64)" = 2de401bd4370b13ebaf50663f7f1bbd9f924c1fd5f90b1762dbd76662388c684 ]
cd $X
U1=da19bb3ad9e9227e12bc28161713ae6a1f2a680e559039e290caa2cff0bc6eca
if [ -e u/$U1 ]; then echo "U1 present"; else cp in35/u_$U1 u/$U1.part && chmod 0644 u/$U1.part && mv u/$U1.part u/$U1 && echo "U1 placed"; fi
[ "$(sha256sum u/$U1 | cut -c1-64)" = $U1 ] && echo U1_OK
U2=c672ad47b28d05d81e524baddb6d164f0f41c0b23a8cf0a1f49bfd045e93ec46
if [ -e u/$U2 ]; then echo "U2 present"; else cp o/174415/routing_selection.json u/$U2.part && chmod 0644 u/$U2.part && mv u/$U2.part u/$U2 && echo "U2 placed"; fi
[ "$(sha256sum u/$U2 | cut -c1-64)" = $U2 ] && echo U2_OK
echo "u 4e8e6c04: $(ls u | grep -c '^4e8e6c04')  ca0616db: $(ls u | grep -c '^ca0616db')"
[ "$(ls u | grep -c '^4e8e6c04')" = 1 ] && [ "$(ls u | grep -c '^ca0616db')" = 1 ]
test ! -e s35; mkdir s35; tar xf in35/s35_n_go.tar -C s35
cd s35/n_go; B=$(sha256sum -c SHA256SUMS.txt 2>&1 | grep -vc ': OK$' || true); echo "staged seal $(sha256sum SHA256SUMS.txt | cut -c1-64) bad $B lines $(wc -l < SHA256SUMS.txt) files $(find . -type f | wc -l) pyc $(find . -name __pycache__ | wc -l)"
[ "$B" = 0 ] && [ "$(sha256sum SHA256SUMS.txt | cut -c1-64)" = ea058fed0495be92fd22c71546fd1bbab449970c566319fc857ddd2a6a551591 ]
cd $X; [ "$(sha256sum n/SHA256SUMS.txt | cut -c1-16)" = 7e23bbddb052a6f3 ] || { echo OLD_N_UNEXPECTED; exit 1; }
test ! -e a24m4z12/n_7e23bbdd; test ! -e jn8.sh
mv n a24m4z12/n_7e23bbdd && mv s35/n_go n
echo "FINAL X/n seal $(sha256sum n/SHA256SUMS.txt | cut -c1-64) bad $(cd n && sha256sum -c SHA256SUMS.txt 2>&1 | grep -vc ': OK$' || true) lines $(wc -l < n/SHA256SUMS.txt) files $(find n -type f | wc -l) pyc $(find n -name __pycache__ | wc -l)"
echo "v.py: $(python3 -B -I -s n/b/v.py n 2>&1 | tail -2)"
test ! -e n/k/t_e047002134f979bd.tar && echo OLD_TREE_TAR_GONE
cp in35/jn8.sh jn8.sh; [ "$(sha256sum jn8.sh | cut -c1-64)" = 2de401bd4370b13ebaf50663f7f1bbd9f924c1fd5f90b1762dbd76662388c684 ] && echo JN8_OK
[ "$(sha256sum n/SHA256SUMS.txt | cut -c1-64)" = ea058fed0495be92fd22c71546fd1bbab449970c566319fc857ddd2a6a551591 ] || { echo SEAL_BAD; exit 1; }
sbatch --hold $X/jn8.sh; sleep 10; squeue -u $USER -h -o "%i %P %j %T %M %R"; date -u +%TZ
