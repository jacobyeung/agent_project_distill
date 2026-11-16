N=/scratch/jjyeung/orch_n30/k1_ops3/work/partb/build7
cd $N && cat evidence/B7_RH_START.txt evidence/B7_MAPPED_END.txt evidence/B7_RH_END.txt
echo "=== MAPPED summary"; python3 -c "
import json,sys
t=open('evidence/B7_MAPPED.log').read().strip().splitlines()[-1]; d=json.loads(t)
print('passed',d['passed'],'run',d['run']); [print(' ',k,v.get('passed'),v.get('returncode'),v.get('verified_returns')) for k,v in d['cases'].items()]"
echo "=== DEPTH MAPPED"; cat evidence/B7_DEPTH_MAPPED.log | head -80
echo "=== NS log"; tail -c 2500 evidence/B7_NS.log
R=$(cat evidence/B7_NS.run); echo "=== NS failure.log ($R)"; tail -c 3000 $R/failure.log 2>/dev/null; echo; ls $R/success 2>/dev/null | head -30; tail -c 2500 $R/success/batch.log 2>/dev/null
echo "=== DEPTH NS"; tail -c 1200 evidence/B7_DEPTH_NS.log
