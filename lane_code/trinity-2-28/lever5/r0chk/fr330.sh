F=/scratch/jjyeung/frames64; ls $F | head -5 >&2
for s in 0658da5bc0 4291be3b44 48da625e8c 4f144c7489 5334a4164a 5a269ba6fe 5d591ff74d 8d0f714398 a66af39cef af112b8903 c0b3c65080 d3b7d054c4 d6702c681d; do d=$(ls -d $F/*/$s $F/$s $F/*/*/$s 2>/dev/null | head -1); [ -z "$d" ] && { echo "MISSING $s" >&2; continue; }; n=$(ls $d | wc -l); fs=$(ls $d | sed -n "1p;$((n/2))p;${n}p"); for f in $fs; do echo "$d/$f"; done; done > /tmp/l5_fr.txt
tar cf - -T /tmp/l5_fr.txt
