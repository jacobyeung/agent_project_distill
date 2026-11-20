K=/scratch/jjyeung/orch_n30/nvkey1/work
echo 24 > $K/ctl/INFLIGHT
date -u +%T; tail -3 $K/runner.log; cat $K/meter/METER.json; wc -l $K/out/3*.jsonl $K/out/41*.jsonl
cd /scratch/jjyeung/orch_n30
find tree_rebuild15_w24l tr16_rev24l4r tr16_rev24l4s tr17_rev24l4c tr17_rev24l4t fb_pack/ro -maxdepth 7 \( -iname '*protected*' -o -iname '*exclusion*' -o -iname '*REVSI_SCENE*' -o -iname '*withheld*' -o -iname '*heldout*' \) 2>/dev/null | grep -v __pycache__ | head -40
