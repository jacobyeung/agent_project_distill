N=/scratch/jjyeung/orch_n30/k1_ops3/work/partb/build7
cd $N && date -u +%FT%TZ; cat evidence/B7B_START.txt evidence/B7B_END.txt 2>/dev/null; for f in evidence/B7_NSDEPTH_MAPPEDROOT.rc evidence/B7_NS2.rc evidence/B7_DEPTH_NS2.rc evidence/B7_NSDEPTH_NS2.rc; do echo "$f $(cat $f 2>/dev/null)"; done
echo "=== NSDEPTH mapped root"; tail -c 2500 evidence/B7_NSDEPTH_MAPPEDROOT.log
echo "=== NS2"; python3 -c "
import json
t=open('evidence/B7_NS2.log').read().strip().splitlines()[-1]; d=json.loads(t)
print('passed',d['passed'],'run',d['run']); [print(' ',k,v) for k,v in d['cases'].items()]" 2>&1 | head -12
R=$(cat evidence/B7_NS2.run 2>/dev/null); tail -c 1500 $R/failure.log 2>/dev/null; tail -c 1500 $R/success/bootstrap_failure.log 2>/dev/null
echo "=== NSDEPTH NS2"; tail -c 2500 evidence/B7_NSDEPTH_NS2.log
echo "=== DEPTH NS2 summary"; grep -E '"equals_production_pin"|carrier_c1_692|schema_and_backing|production_verifier' evidence/B7_DEPTH_NS2.log | head -12
