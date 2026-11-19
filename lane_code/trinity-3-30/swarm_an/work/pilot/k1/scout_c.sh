set -u
W=/scratch/jjyeung/orch_n30
echo "== /scratch/jjyeung/k1"; ls -la /scratch/jjyeung/k1 | head -30
echo "== /scratch/jjyeung/k1_frames"; ls /scratch/jjyeung/k1_frames | head -12; echo "count $(ls /scratch/jjyeung/k1_frames | wc -l)"
d=$(ls -d /scratch/jjyeung/k1_frames/* | head -1); echo "-- $d"; ls -la $d | head -12; echo "n $(ls $d | wc -l)"
e=$(ls -d $d/* 2>/dev/null | head -1); [ -d "$e" ] && { echo "-- $e"; ls -la $e | head -8; echo "n $(ls $e | wc -l)"; }
echo "== find CAPTURES.json / K1_ROWSETS (depth 3)"
find /scratch/jjyeung/k1 $W/geo_k1 $W/k1_ops8 $W/k1_rules -maxdepth 3 \( -name 'CAPTURES.json' -o -name 'K1_ROWSETS*' -o -name '*HELDOUT*' -o -name '*heldout*' -o -name '*SPLIT*' \) 2>/dev/null | head -30
echo "== geo_k1"; ls $W/geo_k1 | head -30
echo "== k1_ops8"; ls $W/k1_ops8 | head -30
