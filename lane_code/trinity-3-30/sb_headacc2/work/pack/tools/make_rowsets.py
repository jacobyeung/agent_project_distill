"""Run on trinity-1-18 inside /scratch/jjyeung/n30_mirror/sb_headacc2 (lane sb_headacc2). Writes K1_ROWSETS/ from the pinned
corrected-label file and manifest, checks them against the registered GT set and the stored pricing rows, and prints sha256s.
File content of every list: sorted ids joined by a newline, no trailing newline (sha256 of the file = sha256 of that string)."""
import json, collections, hashlib, os, glob, sys
R = '/scratch/jjyeung/orch_n30'
LAB = '/scratch/jjyeung/n30_mirror/gt_audit/gt_audit/work/k1audit/K1_LABELS_CORRECTED.jsonl'
MAN = R + '/k1_ops3/work/codex_arkit_timing/K1_MANIFEST.arkit_timing.json'
GTS = R + '/k1_ops3/work/gt_sets/GT_SET_PRIMARY_296.json'
CR = R + '/b04host3/b04_e2ehook/heads/selector/data/caps_raw'
OUT = 'K1_ROWSETS'; os.makedirs(OUT, exist_ok=True)
def fsha(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()
def put(name, ids):
    s = '\n'.join(sorted(ids)); open(OUT + '/' + name, 'w').write(s)
    print('ROWSET', name, len(ids), fsha(OUT + '/' + name))
labs = [json.loads(l) for l in open(LAB)]
man = json.load(open(MAN)); caps = man['captures']; room = {c['canonical']: c['room'] for c in caps}
print('INPUT', LAB, fsha(LAB)); print('INPUT', MAN, fsha(MAN)); print('INPUT', GTS, fsha(GTS))
have = {f[:-8].replace('__', '/', 1) for f in os.listdir(CR)}
nor = sorted({r['capture'] for r in labs if r['corrected'] is None})
for s, tag in (('train', 'TRAIN'), ('heldout', 'HELDOUT')):
    reg = [r for r in labs if r['split'] == s and r['corrected'] is not None]
    put('K1_%s_%d.txt' % (tag, len(reg)), [r['id'] for r in reg])
    sub = [r for r in reg if r['capture'] in have]
    put('K1_%s_TABLES_%d.txt' % (tag, len(sub)), [r['id'] for r in sub])
    cs = [c['canonical'] for c in caps if c['k1_split'] == s and c['canonical'] not in nor]
    put('K1_CAPTURES_%s_%d.txt' % (tag, len(cs)), cs)
    print('COUNTS', s, 'rows', len(reg), 'captures', len({r['capture'] for r in reg}), 'rooms', len({room[r['capture']] for r in reg}),
          '| table rows', len(sub), 'captures', len({r['capture'] for r in sub}), 'rooms', len({room[r['capture']] for r in sub}),
          '| by dataset', dict(collections.Counter(r['dataset'] for r in reg)), '| convention', dict(collections.Counter(r['convention'] for r in reg)))
exc = [dict(id=r['id'], capture=r['capture'], split=r['split'], reason='no GT raster on disk (convention no_raster); capture outside GT_SET_PRIMARY_296') for r in labs if r['corrected'] is None]
json.dump(sorted(exc, key=lambda r: r['id']), open(OUT + '/K1_EXCLUSIONS.json', 'w'), indent=1); print('ROWSET K1_EXCLUSIONS.json', len(exc), fsha(OUT + '/K1_EXCLUSIONS.json'), dict(collections.Counter((r['split'], r['capture']) for r in exc)))
g = json.load(open(GTS)); gc = set(g['captures']) if isinstance(g, dict) and 'captures' in g else None
allc = {c['canonical'] for c in caps}
print('CHECK GT_SET_PRIMARY_296 keys', list(g.keys())[:12] if isinstance(g, dict) else type(g), 'n', len(gc) if gc else None, '== manifest minus no_raster:', gc == allc - set(nor) if gc else None)
# stored pricing rows
rows = []
for p in sorted(glob.glob('/scratch/jjyeung/n30_mirror/tower_redecide/work/reprice/caps_corrected/*.json')): rows.extend(json.load(open(p))['items'])
for s in ('train', 'heldout'):
    ids = {r['row_id'] for r in rows if r['type'] == 'object_abs_distance' and r['split'] == s and r['arm'] == 'GT'}
    print('CHECK reprice GT rows', s, len(ids), '== registered:', ids == {r['id'] for r in labs if r['split'] == s and r['corrected'] is not None})
# R0 join: is ID_MAP source_line 0- or 1-based?
import gzip
q32 = [json.loads(l) for l in open(R + '/b10_reserve/out/qsets/R0_QUESTIONS_dev_f32.jsonl')]
d = [json.loads(l) for l in gzip.open('pack/DIRECT_R1_200_R0dev.jsonl.gz')]
for base in (0, 1):
    ok = sum(1 for r in d if 0 <= r['source_line'] - base < len(q32) and q32[r['source_line'] - base]['qid'] == r['qid'] and q32[r['source_line'] - base]['question'] == r['question'])
    print('CHECK R0 join base', base, ok, 'of', len(d))
qc = collections.Counter(r['qid'] for r in q32); print('CHECK R0 f32 items', len(q32), 'distinct qids', len(qc), 'repeated', {k: v for k, v in qc.items() if v > 1})
print('INPUT R0 f32', fsha(R + '/b10_reserve/out/qsets/R0_QUESTIONS_dev_f32.jsonl'), 'f64', fsha(R + '/b10_reserve/out/qsets/R0_QUESTIONS_dev_f64.jsonl'), 'FRAMES_MANIFEST', fsha(R + '/b10_reserve/out/FRAMES_MANIFEST.json'))
print('R0 subtypes', dict(collections.Counter((r['question_type'], r.get('subtype')) for r in q32 if r['question_type'] in ('object_rel_distance', 'object_counting', 'object_size_estimation', 'object_abs_distance', 'obj_appearance_order'))))
print('R0 abs distance units', dict(collections.Counter(r.get('unit') for r in q32 if r['question_type'] == 'object_abs_distance')), 'size units', dict(collections.Counter(r.get('unit') for r in q32 if r['question_type'] == 'object_size_estimation')))
names = collections.Counter()
import re
ex = [r for r in q32 if r['question_type'] == 'object_abs_distance'][0]; print('R0 abs example', json.dumps({k: ex[k] for k in ex if k != 'frame_indices'})[:700])
ex = [r for r in q32 if r['question_type'] == 'object_rel_distance'][0]; print('R0 rel example', json.dumps({k: ex[k] for k in ex if k != 'frame_indices'})[:700])
# gt_audit box schema
K = '/scratch/jjyeung/n30_mirror/gt_audit/gt_audit/work/k1audit/'
def short(v, d=0):
    if isinstance(v, list): return ['list', len(v), short(v[0], d + 1) if v and d < 3 else None]
    if isinstance(v, dict): return {k: short(x, d + 1) for k, x in list(v.items())[:10]} if d < 3 else 'dict[%d]' % len(v)
    return str(v)[:80]
for f in ('K1_BOX_AUDIT.json', 'box_measurements.json'):
    try:
        b = json.load(open(K + f)); print('SCHEMA', f, fsha(K + f), json.dumps(short(b))[:1500])
    except Exception as e: print('SCHEMA', f, 'ERR', e)
print('SCHEMA K1_ROW_AUDIT.jsonl', open(K + 'K1_ROW_AUDIT.jsonl').readline()[:900])
for p in (R + '/b04host3/b04_e2ehook/heads/selector/work/run_iso/selector_head.safetensors', R + '/k1_ops3/work/e3gd/out/FITS.json', R + '/k1_ops3/work/e3gd/out/PER_ITEM.jsonl', '/scratch/jjyeung/n30_mirror/tower_redecide/work/pose_k1.py'):
    print('INPUT', p, fsha(p))
