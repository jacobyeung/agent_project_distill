set -e; export TZ=UTC; X=/project/community/jjyeung/okh7/x_22c714e1; cd $X; date -u +%TZ
F=$(df -BG --output=avail /project/community | tail -1 | tr -dc 0-9); echo FREE_GIB $F; [ "$F" -ge 3 ] || { echo BELOW_FLOOR_3; exit 1; }
[ "$(sha256sum s28fix/n_go/SHA256SUMS.txt | cut -c1-16)" = 9e809db4e0817adf ]
B=$(cd s28fix/n_go && sha256sum -c SHA256SUMS.txt 2>&1 | grep -vc ': OK$' || true); [ "$B" = 0 ] || { echo STAGED_BAD $B; exit 1; }
[ "$(sha256sum n/SHA256SUMS.txt | cut -c1-16)" = 4e29bdfb8754e85f ] || { echo OLD_N_UNEXPECTED; exit 1; }
[ -z "$(squeue -u $USER -h -p advanced -o %i)" ] || { echo ADVANCED_BUSY; squeue -u $USER -h -p advanced; exit 1; }
test ! -e a24m4z12/n_4e29bdfb; mv n a24m4z12/n_4e29bdfb && mv s28fix/n_go n
echo "FINAL X/n seal $(sha256sum n/SHA256SUMS.txt | cut -c1-64) bad $(cd n && sha256sum -c SHA256SUMS.txt 2>&1 | grep -vc ': OK$' || true) files $(find n -type f | wc -l)"
[ "$(sha256sum n/SHA256SUMS.txt | cut -c1-16)" = 9e809db4e0817adf ] && [ "$(sha256sum jn7.sh | cut -c1-16)" = 98edfd9e1f30f4ba ] && echo JN7_OK
sbatch --hold $X/jn7.sh; sleep 10; squeue -u $USER -h -o "%i %P %j %T %M %R"
