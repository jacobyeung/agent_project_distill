set -u
W=/scratch/jjyeung/orch_n30
echo "== find CAPTURES.json depth 4"; find $W/geo_k1 /scratch/jjyeung/k1/src /scratch/jjyeung/k1/tools $W/k1_ops8 $W/k1_rules -maxdepth 4 \( -name 'CAPTURES*.json' -o -name 'K1_ROWSETS*' -o -name 'PILOT300*' -o -name '*anchor*' \) 2>/dev/null | head -30
echo "== geo_k1/out"; ls -la $W/geo_k1/out | head -40
echo "== geo_k1/stage"; ls $W/geo_k1/stage | head -20
echo "== decide_heldout_once.json"; head -c 1500 $W/geo_k1/out/decide_heldout_once.json; echo
echo "== run_convert_2"; ls /scratch/jjyeung/k1/run_convert_2 | head -5; d=$(ls -d /scratch/jjyeung/k1/run_convert_2/*/ | head -1); ls -la $d | head -12
echo "== k1/src"; find /scratch/jjyeung/k1/src -maxdepth 2 | head -30
echo "== k1/tools"; ls -la /scratch/jjyeung/k1/tools | head
