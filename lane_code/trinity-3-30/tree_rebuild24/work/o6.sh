set -e; export TZ=UTC; date -u +%TZ; X=/project/community/jjyeung/okh7/x_22c714e1; cd $X
F=$(df -BG --output=avail /project/community | tail -1 | tr -dc 0-9); echo FREE_GIB $F; [ "$F" -ge 20 ] || { echo BELOW_FLOOR_20; exit 1; }
test ! -e s24m4z8b && test ! -e qp_11386117 && test ! -e jd7.sh && test ! -e j7.py && test ! -e pp
mkdir -m 700 s24m4z8b && tar xf s24m4z8b.tar -C s24m4z8b && cd s24m4z8b && sha256sum -c MANIFEST.sha | grep -vc ': OK$' || true
B=$(sha256sum -c MANIFEST.sha 2>&1 | grep -vc ': OK$' || true); [ "$B" = 0 ] || { echo BAD $B; exit 1; }
U=u/a49f117f60add326e1ef3e8eb2b92a73ec299425e8efb477fa9e84d462789e73; if [ -e $X/$U ]; then cmp $U $X/$U && echo U_SAME; else mv $U $X/$U; echo U_ADDED; fi
mv qp_11386117 jd7.sh j7.py pp $X/; cd $X
echo "qp seal $(sha256sum qp_11386117/SHA256SUMS.txt | cut -c1-16) bad $(cd qp_11386117 && sha256sum -c SHA256SUMS.txt 2>&1 | grep -vc ': OK$') pyc $(find qp_11386117 -name __pycache__ | wc -l)"
sha256sum jd7.sh j7.py pp/pp.sh | cut -c1-80; echo left $(find s24m4z8b -type f | wc -l)
squeue -u $USER -h -o "%j" | grep -q 8ad01bf06cd3 && { echo QUEUED; exit 1; }
[ "$(sha256sum qp_11386117/SHA256SUMS.txt | cut -c1-16)" = 1138611744d623dc ] && sbatch $X/pp/pp.sh; sleep 15
squeue -u $USER -o "%.10i %.10P %.24j %.8T %.10M %R"
