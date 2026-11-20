K=/scratch/jjyeung/orch_n30/nvkey1/work; cd $K || exit 1
echo "== $(date -u +%T) $(wc -l < out/60_v6bA_first30.jsonl) A, $(wc -l < out/61_v6bN_first30.jsonl) N, $(cat queue/62_v6bI_first30.jsonl 2>/dev/null | wc -l) I queued, $(cat out/62_v6bI_first30.jsonl 2>/dev/null | wc -l) I out; $(tail -1 v6b/chain.log)"
grep -c '"status": 504' meter/CALLS.jsonl; tail -2 runner.log | cut -c1-160; cat meter/METER.json; echo
echo "== FILE"; cat v2/O4_ALIAS_CANDIDATES.jsonl
