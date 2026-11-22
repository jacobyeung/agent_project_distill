export TZ=UTC; date -u +%TZ
I=/project/community/jjyeung/okh7/l_94a76bda/in
echo "== in"; ls -l $I 2>&1 | awk 'NR>1 && $1 !~ /^d/ {n++; s+=$5} END {printf "files %d bytes %.0f\n", n, s}'
ls -l $I 2>&1 | awk 'NR>1 {printf "%s:%s;", $9, $5}' | fold -w 1800 | head -8; echo
echo "== in/cr"; ls -l $I/cr 2>&1 | awk 'NR>1 {n++; s+=$5} END {printf "files %d bytes %.0f\n", n, s}'
ls -l $I/cr 2>&1 | awk 'NR>1 {printf "%s:%s;", $9, $5}' | fold -w 1800 | head -40; echo
echo "== model dir"; ls -l /project/community/jjyeung/okh7/l_3d48eea0 2>&1 | awk 'NR>1 {n++; s+=$5} END {printf "files %d bytes %.0f\n", n, s}'
