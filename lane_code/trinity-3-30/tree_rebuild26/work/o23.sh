set -e; export TZ=UTC; X=/project/community/jjyeung/okh7/x_22c714e1; cd $X; date -u +%TZ
[ "$(sha256sum s26fix2/n_go/SHA256SUMS.txt | cut -c1-16)" = 06d9a1b50d48f602 ] || { echo STAGED_BAD; exit 1; }
B=$(cd s26fix2/n_go && sha256sum -c SHA256SUMS.txt 2>&1 | grep -vc ': OK$' || true); [ "$B" = 0 ] || { echo STAGED_BAD $B; exit 1; }
F=$(df -BG --output=avail /project/community | tail -1 | tr -dc 0-9); echo FREE_GIB $F; [ "$F" -ge 20 ] || { echo BELOW_FLOOR_20; exit 1; }
scancel 174085; echo "scancel 174085 at $(date -u +%TZ)"
for i in $(seq 1 24); do s=$(squeue -j 174085 -h -o %T 2>/dev/null); [ -z "$s" ] && break; sleep 5; done; echo "174085 left queue: '$s' $(sacct -j 174085 -n -X -o State,ExitCode,Elapsed | head -1)"
test ! -e a24m4z12/n_b44a4915; mv n a24m4z12/n_b44a4915 && mv s26fix2/n_go n
echo "FINAL X/n seal $(sha256sum n/SHA256SUMS.txt | cut -c1-64) bad $(cd n && sha256sum -c SHA256SUMS.txt 2>&1 | grep -vc ': OK$' || true) files $(find n -type f | wc -l)"
[ "$(sha256sum n/SHA256SUMS.txt | cut -c1-16)" = 06d9a1b50d48f602 ] && [ "$(sha256sum jn6.sh | cut -c1-16)" = 0c0e5d3b35cbb580 ]
[ -z "$(squeue -u $USER -h -p advanced -o %i)" ] || echo "NOTE advanced still shows a job of ours"
sbatch --hold $X/jn6.sh; sleep 3; squeue -u $USER -h -o "%i %P %j %T %r"
