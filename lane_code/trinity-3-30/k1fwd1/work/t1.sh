K=/scratch/jjyeung/orch_n30/k1_ops3
echo "== k1_ops3"; ls $K; ls $K/work | head -80; echo "== partb"; ls -la $K/work/partb | head -60
echo "== SUBMIT7"; head -c 4000 $K/work/partb/SUBMIT7.out
echo "== ledger"; grep -n "b7e31d84\|170235\|d1553118" $K/work/ORCHARD_LEDGER.jsonl | cut -c1-800
echo "== kit"; ls -la $K/kc/k1_build/work/kit_k1a; ls $K/kc/k1_build/work | head -50
echo "== ret"; R=/scratch/jjyeung/k1/own_170235; ls -la $R; ls $R/native/probe | head -3; ls $R/native/probe | wc -l; ls $R/logs | head; cat $R/COMPLETE.json | head -c 2000; d=$(ls $R/native/probe | head -1); ls -la $R/native/probe/$d; cat $R/native/probe/$d/PHASE_COMPLETE.json | head -c 2000; ls $R/native; du -sh $R
echo "== sb_own400"; ls -la /scratch/jjyeung/orch_n30/sb_own400 /scratch/jjyeung/orch_n30/sb_own400/in 2>&1
