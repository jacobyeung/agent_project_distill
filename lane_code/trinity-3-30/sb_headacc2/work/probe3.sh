set -u
R=/scratch/jjyeung/orch_n30; M=/scratch/jjyeung/n30_mirror
echo "@@@ host"; hostname -s; date -u +%FT%TZ
echo "@@@ kobj_track"; cat $R/sb_kobj/out/BLOCKER_track.md 2>&1; echo; cat $R/sb_kobj/STATUS.md; echo; [ -f $R/sb_kobj/out/REPORT.md ] && head -c 9000 $R/sb_kobj/out/REPORT.md; cat $R/sb_kobj/out/dryrun.log 2>&1 | head -20
/usr/bin/python3 - <<'PYEOF'
import json
for L in ('sb_kobj','sb_ktow','sb_kbox'):
    try:
        d=json.load(open('/scratch/jjyeung/orch_n30/%s/out/DRYRUN.json'%L))
        def walk(x, pre='', depth=0):
            if isinstance(x, dict):
                for k,v in x.items():
                    if k in ('status','passed','blocker','reason','blockers','missing','verdict','error') or (isinstance(v,str) and ('BLOCK' in v or 'MISSING' in v)):
                        print(L, pre+k, '=', str(v)[:400])
                    if depth<3: walk(v, pre+k+'.', depth+1)
        walk(d)
    except Exception as e: print(L, 'ERR', e)
PYEOF
echo "@@@ ktow_report"; cat $R/sb_ktow/STATUS.md; echo; [ -f $R/sb_ktow/out/REPORT.md ] && head -c 9000 $R/sb_ktow/out/REPORT.md; cat $R/sb_ktow/configs/kit.json 2>&1 | head -c 1500; echo
echo "@@@ reader_g"; cat $R/b04host3/reader_bs/e2e_reader/grounding.py
echo "@@@ reader_s"; cat $R/b04host3/reader_bs/e2e_reader/stage1.py
echo "@@@ reader_ls"; (cd $R/b04host3/reader_bs && sha256sum e2e_reader/*.py); ls $R/b04host3/reader_bs $R/b04host3/b04_e2ehook | head -60 | tr '\n' ' '; echo; (cd $R/b04host3/b04_e2ehook && sha256sum heads/selector/*.py heads/selector/sl118/*.py heads/selector/work/run_iso/selector_head.* 2>&1 | head -40)
echo "@@@ misc"; ls /scratch/jjyeung/devs1_frames 2>&1 | head -3; ls /scratch/jjyeung/devs1_frames 2>/dev/null | wc -l; ls /scratch/jjyeung/k1/own_170235/native/probe | wc -l; ls /scratch/jjyeung/k1/run_convert_2 | wc -l; ls /scratch/jjyeung/k1/run_tower_sam_2 | wc -l; ls $R/k1_ops3/work/kc_guard/guard_downstream/analyses/primary_296/tables | head -8; ls $R/k1_ops3/work/kc_guard/guard_downstream/analyses/primary_296/tables | wc -l; ls $R/e3_geom/work/harness 2>&1 | head -20; ls $R/e3_geom/out 2>&1 | head; nproc; free -g | head -2; df -h /scratch | tail -1
echo "@@@ py"
/usr/bin/python3 - <<'PYEOF'
import json, collections, hashlib, os, glob, gzip
R='/scratch/jjyeung/orch_n30'
def sha_ids(ids): return hashlib.sha256('\n'.join(sorted(ids)).encode()).hexdigest()
labs=[json.loads(l) for l in open('/scratch/jjyeung/n30_mirror/gt_audit/gt_audit/work/k1audit/K1_LABELS_CORRECTED.jsonl')]
man=json.load(open(R+'/k1_ops3/work/codex_arkit_timing/K1_MANIFEST.arkit_timing.json'))
caps=man['captures']
bysplit=collections.defaultdict(list)
for c in caps: bysplit[c['k1_split']].append(c['canonical'])
print('manifest captures', {k:len(v) for k,v in bysplit.items()}, 'sha all', sha_ids([c['canonical'] for c in caps]))
nor=sorted({r['capture'] for r in labs if r['convention']=='no_raster'}); print('no_raster captures', nor, [next(c['k1_split'] for c in caps if c['canonical']==x) for x in nor])
for s,v in bysplit.items():
    keep=[x for x in v if x not in nor]; print('capture registry', s, len(keep), sha_ids(keep))
print('row types', collections.Counter((c['k1_split'], r['type']) for c in caps for r in c['rows']))
print('gt path roots', collections.Counter(os.path.dirname(c['gt']['path']) if c.get('gt') else None for c in caps))
print('gt exists', collections.Counter(bool(c.get('gt')) and os.path.exists(c['gt']['path']) for c in caps))
print('gt missing caps', [c['canonical'] for c in caps if not (c.get('gt') and os.path.exists(c['gt']['path']))][:12])
T=R+'/k1_ops3/work/kc_guard/guard_downstream/analyses/primary_296/tables'
for f in sorted(os.listdir(T))[:12]:
    p=T+'/'+f
    if f.endswith('.json') and os.path.getsize(p)<3e6:
        d=json.load(open(p)); print('tables', f, (list(d.keys())[:14] if isinstance(d, dict) else ('list', len(d))))
        if isinstance(d, dict):
            for k in ('captures','capture_ids','included','excluded','gt_set','n_captures'):
                if k in d: print('   ', k, str(d[k])[:600])
cr=R+'/b04host3/b04_e2ehook/heads/selector/data/caps_raw'
have={f[:-8].replace('__','/',1) for f in os.listdir(cr)}
print('caps_raw', len(have), 'in manifest', len(have & {c['canonical'] for c in caps}), 'by split', collections.Counter(c['k1_split'] for c in caps if c['canonical'] in have))
room={c['canonical']:c['room'] for c in caps}
for s in ('train','heldout'):
    ids=[r['id'] for r in labs if r['split']==s and r['corrected'] is not None]
    sub=[r['id'] for r in labs if r['split']==s and r['corrected'] is not None and r['capture'] in have]
    capsub={r['capture'] for r in labs if r['split']==s and r['corrected'] is not None and r['capture'] in have}
    print('table rows', s, len(sub), 'of', len(ids), 'captures', len(capsub), 'rooms', len({room[x] for x in capsub}), 'sha', sha_ids(sub))
    missing=collections.Counter(r['capture'] for r in labs if r['split']==s and r['corrected'] is not None and r['capture'] not in have)
    print('   registered captures without table', len(missing), dict(list(missing.items())[:8]))
z=json.load(gzip.open(cr+'/'+sorted(os.listdir(cr))[0])); print('caps_raw keys', (list(z.keys())[:20] if isinstance(z, dict) else type(z)))
if isinstance(z, dict):
    for k,v in list(z.items())[:12]: print('   ', k, str(v)[:260])
import numpy as np
dd=sorted(os.listdir('/scratch/jjyeung/k1/run_convert_2'))[0]
cj=json.load(open('/scratch/jjyeung/k1/run_convert_2/'+dd+'/candidates.json')); print('candidates.json keys', list(cj.keys())[:20]); print('   phrases', str(cj.get('phrases'))[:300]); print('   contract', str({k:cj[k] for k in cj if k not in ('frames','phrases')})[:600])
g=[c for c in caps if c.get('gt') and os.path.exists(c['gt']['path'])][0]
zz=np.load(g['gt']['path'], allow_pickle=True); print('gt npz', g['canonical'], {k:(zz[k].shape, str(zz[k].dtype)) for k in zz.files})
print('capture anchor_slots', g['anchor_slots'][:12], 'anchor_indices', g['anchor_indices'][:6], 'dense idx', [d['index'] for d in g['dense_frames'][:8]], 'fi', g['model_row']['student_input']['frame_indices'][:6])
ok=sum(all(c['dense_frames'][s]['sha256']==c['model_row']['student_input']['frames'][k]['sha256'] for k,s in enumerate(c['anchor_slots'])) for c in caps); inc=sum(list(c['anchor_slots'])==sorted(c['anchor_slots']) for c in caps)
print('anchor sha match captures', ok, 'anchor_slots increasing', inc, 'of', len(caps))
cnt=collections.Counter(len(v) for c in caps for v in c.get('gt_name_ids',{}).values()); print('gt_name_ids instances per name', dict(cnt))
for p in (R+'/e3_geom/out/FITS.json', R+'/e3_geom/work/harness/out/FITS.json', R+'/k1_ops3/work/e3gd/out/FITS.json'):
    if os.path.exists(p): print('FITS', p, hashlib.sha256(open(p,'rb').read()).hexdigest(), open(p).read()[:700])
PYEOF
echo "@@@ end"
