set -e; export TZ=UTC; date -u +%TZ; X=/project/community/jjyeung/okh7/x_22c714e1; cd $X
F=$(df -BG --output=avail /project/community | tail -1 | tr -dc 0-9); echo FREE_GIB $F; [ "$F" -ge 20 ] || { echo BELOW_FLOOR_20; exit 1; }
test ! -e e3 && test ! -e s24m4z10e3; mkdir -m 700 s24m4z10e3 && tar xf s24m4z10e3.tar -C s24m4z10e3 && cd s24m4z10e3
B=$(sha256sum -c MANIFEST.sha 2>&1 | grep -vc ': OK$' || true); [ "$B" = 0 ] || { echo BAD $B; exit 1; }
mv e3 $X/e3; cd $X; sha256sum e3/* | cut -c1-80; ls -ld n_s
squeue -u $USER -h -o "%j" | grep -q 86b407cde192 && { echo QUEUED; exit 1; }
sbatch --hold $X/e3/e3.sh; sleep 5; squeue -u $USER -o "%.10i %.10P %.24j %.8T %.10M %R"
