"""Static pin-closure audit of the K1 own job: does every {path,sha256} pin reachable from the
production receipt resolve to a file that stage_job stages, with the same sha256?"""
import json, sys, hashlib
from pathlib import PurePosixPath as P
W = '/scratch/jjyeung/orch_n30/k1_ops6'
SJ, FSW, AP, PROJECT = '/scratch/jjyeung', '/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung', '/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap', '/project/community/jjyeung'
cfgA = json.load(open(W + '/src118/build/packet/CONFIG.json'))
A = cfgA['assets']
WITH_DEPTH = '--with-depth' in sys.argv
def logical(member):
    for pre, base in (('sj/', SJ), ('fsw/', FSW), ('m/ap/', AP), ('project/', PROJECT)):
        if member.startswith(pre): return base + '/' + member[len(pre):]
    return None
staged = {}  # logical path -> (sha or None, source)
def add(path, sha, src): staged[str(P(path))] = (sha, src)
for r in json.load(open(W + '/work/export_list.json')):
    if r['type'] == '0': add(cfgA['export_destination'] + '/' + r['name'], None, 'export')
for k, v in cfgA['anchors']['members'].items(): add('/scratch/jjyeung/k1_frames/' + k, v['sha256'], 'anchors')
for role, item in (('a2', A['small_objects'][1]), ('a3', cfgA['code']), ('a30', A['small_objects'][3])):
    for k, v in item['members'].items():
        L = logical(k)
        if L: add(L, v['sha256'], role)
model = json.load(open(W + '/model/fsw/ap/e84d901c/arm/frozen/6f27ae81/model.json'))
for k, v in model['files'].items(): add(model['root'] + '/' + k, v, 'base')
for k, v in A['tree_sources'].items(): add(A['tree_root'] + '/' + k, v, 'trainer')
add(A['trainer_logical_archive'], A['trainer']['sha256'], 'trainer_link')
if WITH_DEPTH:
    for i, d in enumerate(A['depth']): add(d['logical_path'], d['sha256'], 'depth_%d' % i)
# Pins reachable from the production receipt.
meta = W + '/meta/'
def L2local(path):
    """Where I hold a local copy of a staged logical JSON (metadata tar, code bundle, export JSONs)."""
    for pre, base in (('fsw/', FSW), ('sj/', SJ)):
        if path.startswith(base + '/'):
            for root in (W + '/meta/', W + '/bundle/', W + '/model/'):
                cand = root + pre + path[len(base) + 1:]
                try: open(cand).close(); return cand
                except OSError: pass
    return None
export_json = {cfgA['export_destination'] + '/' + r['name']: r['content'] for r in json.load(open(W + '/work/export_list.json')) if 'content' in r}
extra = {FSW + '/ap/97a6a3eb/runs/b19c1200/train/step_400/heads.json': open(W + '/audit/heads.json').read()}
def content(path):
    if path in export_json: return export_json[path]
    if path in extra: return extra[path]
    loc = L2local(path)
    return open(loc).read() if loc else None
pins, seen_files = [], set()
def walk(o, where):
    if isinstance(o, dict):
        if isinstance(o.get('path'), str) and isinstance(o.get('sha256'), str):
            pins.append((o['path'], o['sha256'], where))
        for k, v in o.items(): walk(v, where + '.' + str(k))
    elif isinstance(o, list):
        for i, v in enumerate(o): walk(v, where + '[%d]' % i)
def visit(path, label):
    if path in seen_files: return
    seen_files.add(path)
    text = content(path)
    if text is None or not path.endswith('.json'): return
    try: obj = json.loads(text)
    except Exception: return
    n0 = len(pins)
    walk(obj, label)
    for p, s, w in pins[n0:]:
        if p.endswith('.json'): visit(p, p.rsplit('/', 1)[-1])
m2 = json.load(open(W + '/src118/build/manifest_v2/a40fbc19.json'))
for name in ('config', 'data_receipt', 'artifact'):
    pins.append((m2['gpu'][name]['path'], m2['gpu'][name]['sha256'], 'manifest.gpu.' + name))
    visit(m2['gpu'][name]['path'], name)
visit(A['model_manifest']['path'], 'model_manifest')
visit(cfgA['export_destination'] + '/m544/artifact.json', 'export_artifact')
visit(cfgA['export_destination'] + '/m544/full_weights/full_weights.json', 'full_weights')
rows = {}
for p, s, w in pins:
    key = (p, s)
    st = staged.get(str(P(p))) if p.startswith('/') else None
    if st is None: status = 'NOT_STAGED'
    elif st[0] is None or st[0] == s: status = 'STAGED_' + st[1] + ('' if st[0] else '_shaunknown')
    else: status = 'STAGED_SHA_DIFFERS_' + st[1]
    rows.setdefault(key, [status, []])[1].append(w)
out = sorted(((v[0], k[0], k[1][:8], v[1]) for k, v in rows.items()))
for status, p, s, ws in out:
    print(status, p, s, 'refs=%d' % len(ws), ws[0][:90])
print('TOTAL pins', len(rows), 'NOT_STAGED', sum(1 for r in out if r[0] == 'NOT_STAGED'), 'SHA_DIFFERS', sum(1 for r in out if 'DIFFERS' in r[0]))
