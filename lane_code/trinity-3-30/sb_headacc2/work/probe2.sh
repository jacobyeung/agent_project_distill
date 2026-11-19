set -u
R=/scratch/jjyeung/orch_n30; M=/scratch/jjyeung/n30_mirror
echo "@@@ host"; hostname -s; date -u +%FT%TZ
echo "@@@ k1_split"; ls -la $R/k1_ops3/work/k1_split/ 2>&1 | head -30; ls -la $R/k1_ops3/work/kc_guard/guard_downstream/analyses/ $R/k1_ops3/work/kc_guard/guard_downstream/analyses/primary_296 2>&1 | head -40
echo "@@@ envs"; ls /scratch/jjyeung/envs/ 2>&1 | head -40
for p in /scratch/jjyeung/envs/*/bin/python; do echo "--- $p"; timeout 90 $p -c 'import torch,safetensors,numpy;print("torch",torch.__version__,"numpy",numpy.__version__,"cuda_build",torch.version.cuda)' 2>&1 | tail -1; done
grep -o '"python[^,]*,\|"interpreter[^,]*,\|"env[^,]*,' /scratch/jjyeung/k1/run_tower_sam_2.preflight.json | head -5; head -c 1500 /scratch/jjyeung/k1/run_tower_sam_2.preflight.json; echo
echo "@@@ reader_sha"; for d in $R/b04host3/reader_bs/e2e_reader $R/b04host3/b04_e2ehook/e2e_reader $R/b04host3/b04_e2ehook/b/e2e_reader; do [ -d $d ] && sha256sum $d/grounding.py $d/stage1.py $d/geometry.py; done; sha256sum $R/b04host3/tree_rebuild/work/base/tree_b01ce449/student_pilot/routed_candidates.py; ls $R/b04host3 | head -40 | tr '\n' ' '; echo; grep -n 'sys.path\|READER\|^import\|^from\|ROOT\|TREE' $R/b04host3/lift_price/harness/lift_price.py | head -40; cat $R/b04host3/lift_price/harness/run.sh
echo "@@@ kobj"; cat $R/sb_kobj/STATUS.md; echo; cat $R/sb_kobj/config/BARS.json 2>&1 | head -c 6000; echo; ls -la $R/sb_kobj/code $R/sb_kobj/inputs $R/sb_kobj/config $R/sb_kobj/scripts $R/sb_kobj/out 2>&1 | head -80; sha256sum $R/sb_kobj/inputs/*.md 2>&1 | head
echo "@@@ kbox"; cat $R/sb_kbox/STATUS.md; echo; cat $R/sb_kbox/decisions.py; sha256sum $R/sb_kbox/*.md
echo "@@@ ktow"; cat $R/sb_ktow/STATUS.md; echo; ls -la $R/sb_ktow/out $R/sb_ktow/configs $R/sb_ktow/scripts $R/sb_ktow/inputs 2>&1 | head -60; [ -f $R/sb_ktow/out/REPORT.md ] && head -c 9000 $R/sb_ktow/out/REPORT.md; sha256sum $R/sb_ktow/inputs/*.md 2>&1 | head
echo "@@@ py"
/usr/bin/python3 - <<'PYEOF'
import json, collections, hashlib, os, glob
R='/scratch/jjyeung/orch_n30'
def sha_ids(ids): return hashlib.sha256('\n'.join(sorted(ids)).encode()).hexdigest()
labs=[json.loads(l) for l in open('/scratch/jjyeung/n30_mirror/gt_audit/gt_audit/work/k1audit/K1_LABELS_CORRECTED.jsonl')]
print('labels', len(labs), collections.Counter((r['split'], r['convention']) for r in labs))
reg={s:[r['id'] for r in labs if r['split']==s and r['corrected'] is not None] for s in ('train','heldout')}
for s,ids in reg.items(): print('registered', s, len(ids), 'captures', len({r['capture'] for r in labs if r['id'] in set(ids)}), 'sha256_sorted_ids', sha_ids(ids))
exc=collections.Counter((r['split'], r['capture'], r['convention']) for r in labs if r['corrected'] is None)
print('excluded', dict(exc))
man=json.load(open(R+'/k1_ops3/work/codex_arkit_timing/K1_MANIFEST.arkit_timing.json'))
print('manifest keys', list(man.keys())[:20])
caps=man['captures']; c=caps[0]
def short(v):
    if isinstance(v, list): return ('list', len(v), short(v[0]) if v else None)
    if isinstance(v, dict): return {k: short(x) for k,x in list(v.items())[:14]}
    return str(v)[:90]
print('capture keys', {k: short(v) for k,v in c.items()})
labcap={}
for r in labs: labcap.setdefault(r['id'], r)
rooms=collections.defaultdict(set); ncap=collections.Counter(); mrows=collections.Counter(); miss=0
idcap={}
for c in caps:
    for r in c['rows']:
        if r['type']=='object_abs_distance':
            rid=r.get('row_id', r.get('id')); idcap[rid]=c
            mrows[c['k1_split']]+=1
            if rid not in labcap: miss+=1
print('manifest distance rows', dict(mrows), 'not in labels', miss, 'row keys', list(caps[0]['rows'][0].keys())[:30])
for s,ids in reg.items():
    cs={ (idcap[i].get('capture') or idcap[i].get('capture_id') or idcap[i].get('id')) for i in ids if i in idcap}
    rm={ idcap[i]['room'] for i in ids if i in idcap}
    print('registered', s, 'in manifest', sum(i in idcap for i in ids), 'captures', len(cs), 'rooms', len(rm), 'datasets', collections.Counter(idcap[i].get('dataset') for i in ids if i in idcap))
# split registry
for f in glob.glob(R+'/k1_ops3/work/k1_split/*.json')[:6]:
    try:
        d=json.load(open(f)); print('k1_split', os.path.basename(f), hashlib.sha256(open(f,'rb').read()).hexdigest(), {k: short(v) for k,v in (d.items() if isinstance(d, dict) else [('list', d)])})
    except Exception as e: print('k1_split', f, e)
# reprice GT arm ids
rows=[]
for p in sorted(glob.glob('/scratch/jjyeung/n30_mirror/tower_redecide/work/reprice/caps_corrected/*.json')): rows.extend(json.load(open(p))['items'])
for s in ('train','heldout'):
    ids={r['row_id'] for r in rows if r['type']=='object_abs_distance' and r['split']==s and r['arm']=='GT'}
    print('reprice GT', s, len(ids), 'equal registered', ids==set(reg[s]), 'arms', sorted({r['arm'] for r in rows})[:12])
gd=[json.loads(l) for l in open(R+'/k1_ops3/work/e3gd/out/PER_ITEM.jsonl')]
print('e3gd arms', collections.Counter((r['arm'], r['split']) for r in gd if r['type']=='object_abs_distance'))
print('e3gd keys', list(gd[0].keys()))
# selector tables
cr=R+'/b04host3/b04_e2ehook/heads/selector/data/caps_raw'
fs=sorted(os.listdir(cr)); print('caps_raw', len(fs), fs[:3])
capid=lambda c: c.get('capture') or c.get('capture_id') or c.get('id')
print('capture id example', capid(caps[0]), caps[0].get('digest'), caps[0].get('k1_split'))
# one tower/own npz
import numpy as np
dg=[d for d in os.listdir('/scratch/jjyeung/k1/run_tower_sam_2') if os.path.isdir('/scratch/jjyeung/k1/run_tower_sam_2/'+d)][:1]
for d in dg:
    z=np.load('/scratch/jjyeung/k1/run_tower_sam_2/'+d+'/tower.npz', allow_pickle=True); print('tower.npz', {k:(z[k].shape, str(z[k].dtype)) for k in z.files})
    for q in ('/scratch/jjyeung/k1/own_170235/native/probe/'+d+'/own.npz', '/scratch/jjyeung/k1/run_convert_2/'+d+'/geometry.npz'):
        if os.path.exists(q):
            z=np.load(q, allow_pickle=True); print(q.split('/')[-1], {k:(z[k].shape, str(z[k].dtype)) for k in z.files})
        else: print('MISSING', q)
    print(os.listdir('/scratch/jjyeung/k1/run_convert_2/'+d)[:20])
# R0 frames manifest
fm=json.load(open(R+'/b10_reserve/out/FRAMES_MANIFEST.json')); print('FRAMES_MANIFEST', {k: short(v) for k,v in list(fm.items())[:12]})
q32=[json.loads(l) for l in open(R+'/b10_reserve/out/qsets/R0_QUESTIONS_dev_f32.jsonl')]
q64=[json.loads(l) for l in open(R+'/b10_reserve/out/qsets/R0_QUESTIONS_dev_f64.jsonl')]
s32={}; s64={}
for r in q32: s32.setdefault(r['scene'], set()).add(tuple(r['frame_indices']))
for r in q64: s64.setdefault(r['scene'], set()).add(tuple(r['frame_indices']))
ov=[]; un=[]; srt=0
for sc in s32:
    a=list(s32[sc])[0]; b=list(s64.get(sc, [()]))[0]
    ov.append(len(set(a)&set(b))); un.append(len(set(a)|set(b))); srt+= (list(a)==sorted(a))
print('R0 scenes', len(s32), 'one set per scene', all(len(v)==1 for v in s32.values()), all(len(v)==1 for v in s64.values()), 'f32 len', collections.Counter(len(list(v)[0]) for v in s32.values()), 'f64 len', collections.Counter(len(list(v)[0]) for v in s64.values()))
print('overlap f32&f64 per scene', collections.Counter(ov), 'union', collections.Counter(un), 'f32 sorted', srt)
ex=[r for r in q32 if r['question_type']=='obj_appearance_order'][0]; print('appearance gt', json.dumps(ex['gt'])[:500], 'frame_indices', ex['frame_indices'][:8])
ex=[r for r in q32 if r['question_type']=='object_counting'][0]; print('counting', json.dumps({k:ex[k] for k in ex if k!='frame_indices'})[:600])
ex=[r for r in q32 if r['question_type']=='object_size_estimation'][0]; print('size', json.dumps({k:ex[k] for k in ex if k!='frame_indices'})[:500])
print('counting truth dist', sorted(collections.Counter(str(r['answer']) for r in q32 if r['question_type']=='object_counting').items())[:20])
names=collections.defaultdict(set)
import re
print('R0 summary', json.dumps(json.load(open(R+'/b10_reserve/out/qsets/R0_QUESTIONS_SUMMARY.json')))[:900])
PYEOF
echo "@@@ end"
