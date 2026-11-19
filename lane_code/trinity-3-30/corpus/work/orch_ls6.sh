cd /project/community/jjyeung/okh7 || exit 1
for d in x_*; do [ -d $d ] || continue; printf "%s " $d; for s in arm b k o runs; do printf "%s=%s " $s $(du -s --block-size=1M $d/$s 2>/dev/null | cut -f1); done; printf "run=%s\n" "$(ls $d/runs 2>/dev/null | tr '\n' ',')"; done
echo; ls -la x_69d2930d/runs/* | head -20; find x_69d2930d/o -maxdepth 1 -size +5M -printf "%s %p\n" | head
