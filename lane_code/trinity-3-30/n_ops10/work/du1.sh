O=/project/community/jjyeung/okh7; R=$O/x_22c714e1/o/n10_du_0915Z.txt
echo "DU1 start $(date -u +%FT%TZ)"; df -B1 /project/community | tail -1
ls -la --time-style=+%FT%H:%MZ $O | head -80
( echo "start $(date -u +%FT%TZ)"; cd $O && for d in * .[!.]*; do [ -e "$d" ] || continue; nice -n 19 ionice -c3 du -s -B1M "$d" 2>/dev/null; done; echo "== x_22c714e1"; cd $O/x_22c714e1 && for d in * .[!.]*; do [ -e "$d" ] || continue; nice -n 19 ionice -c3 du -s -B1M "$d" 2>/dev/null; done; echo "end $(date -u +%FT%TZ)" ) > $R.part 2>&1 && mv $R.part $R &
echo "DU1 launched pid $! -> $R"
