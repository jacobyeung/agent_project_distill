"""Read-only local input audit. Run: python -B verify_inputs.py > input_checks.txt"""
import hashlib
import json
import os
from pathlib import Path
import numpy as np

W = Path(__file__).resolve().parent
ROOT = Path('/scratch/jjyeung')
ledger = []
def sha(p):
    p = Path(p)
    if not str(p.resolve()).startswith('/scratch/'):
        raise RuntimeError('Nonlocal input: ' + str(p))
    h = hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda: f.read(8 << 20), b''):
            h.update(b)
    d = h.hexdigest()
    ledger.append(f'{d}  {p}')
    return d

def check(p, prefix='', suffix=''):
    p = Path(p)
    if not p.is_file():
        print('MISSING', p, flush=True)
        return None
    d = sha(p)
    ok = d.startswith(prefix) and d.endswith(suffix)
    print('MATCH' if ok else 'MISMATCH', d, p, flush=True)
    return d

fixed = [
 ('geo_bakeoff_kit/KIT_SEAL.json', '0ef8fe08', '5141'),
 ('orch_n30/geo_k1/k1towers/k1_infer.py', 'b1d731b6', ''),
 ('orch_n30/geo_k1/k1towers/k1_convert.py', 'e2748156', ''),
 ('orch_n30/geo_k1/harness/harness.py', '0edcd586', ''),
 ('orch_cd/leg_s1_tree/work/tree_s1_admissionfix_168872/trace_format/room_v314.py', '37c8d5fc', '1d07'),
 ('orch_n30/k1_ops3/work/codex_arkit_timing/K1_MANIFEST.arkit_timing.json', '91a2dbf9', 'de7c'),
 ('orch_n30/b10_reserve/out/qsets/R0_QUESTIONS_dev_f32.jsonl', 'b4e278f2', 'a181'),
 ('orch_n30/b10_reserve/out/qsets/R0_QUESTIONS_rl_f32.jsonl', '5c4034f9', 'd834'),
]
for p, a, b in fixed:
    check(ROOT/p, a, b)
check(W/'evidence/direct_m200_room134.json', 'c9b5994c', '319d')
check(W/'evidence/score_room_pricing.py', '6a32018c', '8bfe')
for p in ['geo_bakeoff_kit/work/kit_env.sh', 'orch_n30/geo_k1/k1towers/kitcheck.py',
          'orch_n30/geo_k1/harness/k1_price.py', 'orch_n30/b10_reserve/code/gen_questions.py']:
    check(ROOT/p)

kit = ROOT/'geo_bakeoff_kit'
seal = json.loads((kit/'KIT_SEAL.json').read_text())
bad = []
for rel, expected in seal['files'].items():
    p = kit/rel
    if not p.is_file() or sha(p) != expected:
        bad.append(rel)
print('KIT sealed files', len(seal['files']), 'bad', bad, flush=True)
sha(kit/'assets/downloads.jsonl')
downloads = [json.loads(s) for s in (kit/'assets/downloads.jsonl').read_text().splitlines()]
for model in ('moge2', 'mapanything', 'da3', 'pi3x', 'moge3'):
    fn = 'model.pt' if model.startswith('moge') else 'model.safetensors'
    p = kit/'assets'/model/fn
    rec = next((r for r in downloads if r['path'].endswith(f'/{model}/{fn}') and r['verified_expected_sha256']), None)
    d = check(p)
    print('WEIGHT', model, 'verified', bool(rec and d == rec['sha256'] and p.stat().st_size == rec['bytes']), flush=True)

b = ROOT/'orch_n30/b10_reserve'
manifest_path = b/'out/FRAMES_MANIFEST.json'
sha(manifest_path)
manifest = json.loads(manifest_path.read_text())
questions = {}
for split in ('dev', 'rl'):
    questions[split] = [r for r in map(json.loads, (b/f'out/qsets/R0_QUESTIONS_{split}_f32.jsonl').read_text().splitlines())
                        if r['question_type'] == 'room_size_estimation']
direct = json.loads((W/'evidence/direct_m200_room134.json').read_text())['rows']
dr = {r['id']: r for r in direct if r['set'] == 'R0-dev'}
qr = {r['qid']: r for r in questions['dev']}
print('R0-dev item IDs equal', set(dr)==set(qr), 'items', len(qr), 'unique scenes', len({r['scene'] for r in qr.values()}), flush=True)
print('R0-dev label/room disagreements', [(i, dr[i]['gt'], q['gt']['area_m2']) for i, q in qr.items()
      if i not in dr or dr[i]['room'] != 'scannetpp/'+q['scene'] or dr[i]['gt'] != float(q['answer'])], flush=True)
print('R0-rl first two', [r['scene'] for r in sorted(questions['rl'], key=lambda x:x['scene'])[:2]], flush=True)
bad = []; frame_count = 0; bytes_read = 0
for canonical, entry in sorted(manifest['scenes'].items()):
    scene = canonical.split('/')[1]
    p = b/'out/frame_manifests'/f'{scene}.json'
    if not p.is_file():
        bad.append(('MISSING', str(p))); continue
    if sha(p) != entry['manifest_sha256']:
        bad.append(('manifest hash', str(p)))
    sm = json.loads(p.read_text())
    for index, expected in sm['frames'].items():
        p = b/'frames/scannetpp'/scene/f'{int(index):06d}.png'
        if not p.is_file():
            bad.append(('MISSING', str(p))); continue
        frame_count += 1; bytes_read += p.stat().st_size
        if sha(p) != expected:
            bad.append(('frame hash', str(p)))
    for q in [q for rows in questions.values() for q in rows if q['scene']==scene]:
        expected_union = set(q['frame_indices']) | set(np.floor(np.linspace(0,q['total_num_frames']-1,64)).astype(int).tolist())
        if expected_union != set(map(int,sm['frames'])):
            bad.append(('frame union', scene))
print('R0 frames', frame_count, 'scenes', len(manifest['scenes']), 'bytes', bytes_read, 'bad', bad, flush=True)

k1 = json.loads((ROOT/fixed[5][0]).read_text())
r0_scenes = {'scannetpp/'+q['scene'] for rows in questions.values() for q in rows}
print('K1/R0 question-scene overlap', sorted(r0_scenes & {c['canonical'] for c in k1['captures']}), flush=True)
for c in k1['captures']:
    if c['canonical'] not in ('scannetpp/067e2e4e61', 'scannetpp/036bce3393'):
        continue
    bad = []
    for f in c['dense_frames']:
        p = Path(f['path'])
        if not p.is_file() or sha(p) != f['sha256']:
            bad.append(str(p))
    key = hashlib.sha256(json.dumps(c, sort_keys=True, allow_nan=False).encode()).hexdigest()
    pd = ROOT/'orch_n30/geo_k1/pred_gpu/da3'/key[:16]
    done = json.loads((pd/'DONE.json').read_text())
    print('S1 K1', c['canonical'], 'split', c['k1_split'], 'frames', len(c['dense_frames']), 'bad', bad,
          'prediction_hash_ok', sha(pd/'pred.npz')==done['pred_sha256'], 'seconds', done.get('seconds'),
          'peak', done.get('peak_allocated_bytes'), flush=True)
    sha(pd/'DONE.json')
for p, pattern in [('orch_n30/geo_k1/geom/da3_native','*.npz'), ('orch_n30/geo_k1/harness/out_merged_mdp','*.json')]:
    print('COUNT', p, len(list((ROOT/p).glob(pattern))), flush=True)
st = os.statvfs(W)
print('Scratch free GB', st.f_bavail*st.f_frsize/1e9, flush=True)
print('MemAvailable', next(s.strip() for s in Path('/proc/meminfo').read_text().splitlines() if s.startswith('MemAvailable:')), flush=True)
(W/'LOCAL_INPUT_SHA256.txt').write_text('\n'.join(ledger)+'\n')
(W/'STATUS.md').write_text('Stage 2: Completed local file hashes, kit seal and checkpoint verification, R0 frame and question checks, K1 dry-run input checks, and scorer self-test. Results are in input_checks.txt and scorer_self_test.txt; the original remote evidence remains unchanged. CPU conversion, resume/device behavior, and statistical assessment are next.\n')
