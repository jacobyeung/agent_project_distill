N=/scratch/jjyeung/orch_n30/k1_ops3/work/partb/build7
cd $N
python3 -c "
import json; r=json.load(open('out/RESULT.json'))
print({k:(v if not isinstance(v,str) else v[:300]) for k,v in r.items() if k not in ('evidence_runs','coverage_files')})
print('runs', r.get('evidence_runs'))"
echo "=== namespace.log tail"; tail -c 1500 out/namespace.log
echo "=== batch.log tail"; tail -c 800 out/batch.log
echo "=== batch_diagnostic.log tail"; tail -c 2500 out/batch_diagnostic.log
echo "=== mounts.log tail"; tail -c 600 out/mounts.log
