set -e; export TZ=UTC; X=/project/community/jjyeung/okh7/x_22c714e1; cd $X; date -u +%TZ; D=$X/t_e7c1a94b3d20
scancel 174112 || true; sleep 3; squeue -j 174112 -h -o %T 2>/dev/null || true
sbatch -p debug --gres=gpu:1 --cpus-per-task=4 --mem=32G -t 00:10:00 --no-requeue --job-name=a15_cot_ape7c1a94b3d20 -o $D/s.log -e $D/s.err --wrap "bash $D/r.sh $D $X/s27fix/n_go" || echo DEBUG_SUBMIT_FAIL
F=$(df -BG --output=avail /project/community | tail -1 | tr -dc 0-9); echo FREE_GIB $F; [ "$F" -ge 3 ] || { echo BELOW_FLOOR_3; exit 1; }
[ "$(sha256sum s27fix/n_go/SHA256SUMS.txt | cut -c1-16)" = 4e29bdfb8754e85f ]
B=$(cd s27fix/n_go && sha256sum -c SHA256SUMS.txt 2>&1 | grep -vc ': OK$' || true); [ "$B" = 0 ] || { echo STAGED_BAD $B; exit 1; }
[ "$(sha256sum n/SHA256SUMS.txt | cut -c1-16)" = 06d9a1b50d48f602 ] || { echo OLD_N_UNEXPECTED; exit 1; }
[ -z "$(squeue -u $USER -h -p advanced -o %i)" ] || { echo ADVANCED_BUSY; squeue -u $USER -h -p advanced; exit 1; }
test ! -e a24m4z12/n_06d9a1b5; mv n a24m4z12/n_06d9a1b5 && mv s27fix/n_go n
echo "FINAL X/n seal $(sha256sum n/SHA256SUMS.txt | cut -c1-64) bad $(cd n && sha256sum -c SHA256SUMS.txt 2>&1 | grep -vc ': OK$' || true) files $(find n -type f | wc -l)"
[ "$(sha256sum n/SHA256SUMS.txt | cut -c1-16)" = 4e29bdfb8754e85f ] && [ "$(sha256sum jn6.sh | cut -c1-16)" = 0c0e5d3b35cbb580 ] && echo JN6_OK
sbatch --hold $X/jn6.sh; sleep 15; squeue -u $USER -h -o "%i %P %j %T %M %R"
