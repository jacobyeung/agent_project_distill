N=/scratch/jjyeung/orch_n30/k1_ops3/work/partb/build7
cd $N && date -u +%FT%TZ; cat evidence/B7D_START.txt evidence/B7D_END.txt 2>/dev/null; cat evidence/B7D_OUTER.rc evidence/B7D_COLLECT.rc 2>/dev/null; cat evidence/B7D_NSDEPTH.rc 2>/dev/null
python3 -c "
import json; r=json.load(open('out/RESULT.json'))
print({k:(v if not isinstance(v,str) else v[:200]) for k,v in r.items() if k not in ('evidence_runs','coverage_files')})
print('runs', r.get('evidence_runs'))"
echo "=== namespace.log (v2)"; tail -c 700 out/namespace.log
echo "=== batch_diagnostic"; tail -c 900 out/batch_diagnostic.log
for f in $(ls -t evidence/NSDEPTH_batch_*.log 2>/dev/null | head -2); do echo "== $f"; head -c 1500 $f; echo; done
base64 -w0 packet/a7e31d84.sh > /tmp/k1ops6_batch.b64; wc -c /tmp/k1ops6_batch.b64
cat /tmp/k1ops6_batch.b64 | timeout 120 ssh -o ConnectTimeout=20 -o BatchMode=yes trinity-3-30.ib "cat > /scratch/jjyeung/orch_n30/k1_ops6/work/a7e31d84.d1553118.sh.b64 && echo COPY_OK"
