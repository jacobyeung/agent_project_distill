W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; Z=$W/w24z
date -u +%TZ; ls $Z $Z/out $Z/work 2>&1 | head -40
J=$(ls $Z/work/enospc/decoded_j.sh 2>/dev/null || ls $Z/work/*/decoded_j.sh 2>/dev/null | head -1); echo "J=$J"; sha256sum $J
grep -n 'o\.py\|pc\.sh\|pc\.py\|ep\.py\|rooms_rc\|status=' $J | head -40
echo "== j.sh 400-445"; sed -n 400,445p $J | cut -c1-300
echo "== original pc.sh"; cat $W/w24y2/out/kit_n_go/b/pc.sh
echo "== pc.py session_bytes"; grep -n 'def session_bytes' -A 14 $W/w24y2/out/kit_n_go/b/pc.py
