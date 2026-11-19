"""Behaviour probes on the extracted kit copy (./kit); writes only under ./kit/tmp and ./out."""
import json, socket, sys, tempfile, time, uuid
from pathlib import Path
H = Path(__file__).resolve().parent
sys.path.insert(0, str(H / 'kit/scripts'))
import adapter, common, gates
import score_room_pricing as sc
W = common.W; assert W == H / 'kit', W
out = {}
# 1. Resume across runs: same capture, same prediction, new run_id / card / host.
d = Path(tempfile.mkdtemp(dir=W / 'tmp')) / 'cap'; d.mkdir()
b = dict(host='h', card_uuid='GPU-a', run_id='run1', model='da3', frames=[1, 2], item_slots=[0, 1], settings={'seed': 0})
(d / 'pred.npz').write_bytes(b'x'); common.write(d / 'DONE.json', dict(binding=b, pred_sha256=common.sha(d / 'pred.npz')), {'f': 'x'})
res = {}
for k, v in [('run_id', 'run2'), ('card_uuid', 'GPU-b'), ('host', 'h2')]:
    try:
        res[k] = common.resume(d, dict(b, **{k: v}))
    except RuntimeError as e:
        res[k] = 'RuntimeError: ' + str(e)[:40]
out['resume_new_run_same_prediction'] = res
# 2. Interrupted capture: STARTED.json only (what gpu_run leaves after a kill, deadline or OOM).
d2 = Path(tempfile.mkdtemp(dir=W / 'tmp')) / 'cap2'
common.write(d2 / 'STARTED.json', dict(binding=b), {'f': 'x'})
try:
    out['resume_started_only'] = common.resume(d2, b)
except RuntimeError as e:
    out['resume_started_only'] = 'RuntimeError: ' + str(e)[:50]
# 3. Real torch UUID format: str(torch.cuda.get_device_properties(0).uuid) is bare 8-4-4-4-12 hex.
hexid = str(uuid.uuid4()); note_uuid = 'GPU-' + hexid
sample = dict(unix_time=time.time() - 301, gpu_uuid=note_uuid, process_count=0, input_sha256={str(H / 'rk_probe.py'): common.sha(H / 'rk_probe.py')})
note = dict(decision='GO', host='hx', run_id='r', gpu_uuid=note_uuid, manifest_sha256='m', code_sha256='c', settings_sha256=common.digest(gates.SETTINGS),
            max_gpu_seconds=5400, allocation_samples=[sample, dict(sample, unix_time=time.time() - 1)])
try:
    gates.authorize(note, 'r', 'm', 'c', dict(uuid=hexid, total_memory=51_527_024_640), 1, note_uuid, 'hx'); out['authorize_torch_uuid'] = 'accepted'
except PermissionError as e:
    out['authorize_torch_uuid'] = 'PermissionError: ' + str(e)
# 4. R0-dev comparisons the shipped S3 path emits (arms price.py writes).
direct = common.read(W / 'evidence/direct_m200_room134.json')['rows']
arms = ['da3_f32+R0', 'da3_f32+T10', 'da3_u94+R0', 'da3_u94+T10']
rows = [dict(id=r['id'], arm=a, area_m2=r['direct'] / (sc.FT2 if r['unit'] == 'ft2' else 1), refusal=None) for r in direct if r['set'] == 'R0-dev' for a in arms]
t = sc.score(direct, rows, 'da3_f32+R0', 5)
out['r0dev_paired_comparisons_in_table'] = sorted(k for k, v in t['sets']['R0-dev']['arms'].items() if 'paired_minus_direct' in v)
# 5. Host string the GO note must equal.
out['socket_gethostname'] = socket.gethostname()
# 6. test_refusal_preserved never reaches the T10 trim.
calls = []
orig = adapter.trim
adapter.trim = lambda *a, **k: calls.append(1) or orig(*a, **k)
class Geo:
    valid = __import__('numpy').array([True]); frame_of = lambda _, k: k
out['refusal_test_T10'] = adapter.price(Geo(), 'T10')['refusal']; out['refusal_test_trim_calls'] = len(calls)
adapter.trim = orig
# 7. Pre-launch rehash volume in gpu_run.prerequisites (bytes of every listed input).
tot = n = 0
for name in ['S0', 'DRYRUN', 'K1_REPRODUCTION', 'TESTS']:
    for p in common.read(common.W.parent.parent / 'sb_roomkit/out' / f'{name}.json')['input_sha256']:
        if Path(p).is_file():
            tot += Path(p).stat().st_size; n += 1
out['prerequisite_rehash'] = dict(files=n, gib=tot / 2**30)
print(json.dumps(out, indent=1))
json.dump(out, open(H / 'out/RK_PROBE.json', 'w'), indent=1)
