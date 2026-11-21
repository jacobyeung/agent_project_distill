set -e; export TZ=UTC; X=/project/community/jjyeung/okh7/x_22c714e1; cd $X; date -u +%TZ
F=$(df -BG --output=avail /project/community | tail -1 | tr -dc 0-9); echo FREE_GIB $F; [ "$F" -ge 20 ] || { echo BELOW_FLOOR_20; exit 1; }
[ -z "$(squeue -u $USER -h -p advanced -o %i)" ] || { echo OUR_ADVANCED_JOB_EXISTS; exit 1; }
[ "$(sha256sum jn6.sh | cut -c1-16)" = 0c0e5d3b35cbb580 ] || { echo JN6_BAD; exit 1; }
[ "$(sha256sum n/SHA256SUMS.txt | cut -c1-16)" = 3f55530cc3874ed3 ] && [ "$(sha256sum q/SHA256SUMS.txt | cut -c1-16)" = ece78fea6daa3acb ] || { echo KIT_BAD; exit 1; }
B=$(cd n && sha256sum -c SHA256SUMS.txt 2>&1 | grep -vc ': OK$' || true); [ "$B" = 0 ] || { echo N_BAD $B; exit 1; }
sbatch --hold $X/jn6.sh
sleep 5; squeue -u $USER -h -o "%i %P %j %T %r %b"
