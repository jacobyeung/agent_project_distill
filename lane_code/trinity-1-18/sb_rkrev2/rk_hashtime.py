"""Time the gpu_run prerequisite rehash (verify_inputs over the merged CPU-stage inputs) of the delivered kit."""
import json, sys, time
sys.path.insert(0, '/scratch/jjyeung/orch_n30/sb_rkrev2/kit/scripts')
import gates
recs = {}
for n in ['S0', 'DRYRUN', 'K1_REPRODUCTION', 'TESTS']:
    gates.merge_inputs(recs, json.load(open(f'/scratch/jjyeung/orch_n30/sb_rkfix/out/{n}.json'))['input_sha256'])
t = time.monotonic(); err = None
try:
    gates.verify_inputs(recs)
except Exception as e:
    err = repr(e)[:200]
r = dict(files=len(recs), seconds=time.monotonic() - t, error=err)
print(json.dumps(r)); json.dump(r, open('/scratch/jjyeung/orch_n30/sb_rkrev2/out/RK_HASHTIME.json', 'w'))
