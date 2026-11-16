import sys,json,math,random,hashlib
from pathlib import Path
sys.dont_write_bytecode=True
TREE='/scratch/jjyeung/orch_cd/leg_s1_tree/work/tree_s1_admissionfix_168872'
sys.path.insert(0,TREE)
from student_pilot.s1_routing import Frames
import cv2
W='/scratch/jjyeung/orch_n30/k1_ops3/work/'
F=json.load(open(W+'codex_finalize_v2/K1_MANIFEST.finalized.json'))
tok={}
for l in open('/scratch/jjyeung/orch_cd/k1_ops/work/CANON_TOKENS.jsonl'):
    r=json.loads(l); tok.setdefault(r['canonical'],r['s'])
d12={r['s']:r for r in json.load(open('/scratch/jjyeung/orch_cd/k1_ops/work/D12_MP4S.json'))}
wd={json.loads(l)['s']:json.loads(l) for l in open(W+'WD_OUT.jsonl')}
G={'scannet':'d1','scannetpp':'d2','arkitscenes':'d3'}
# all 138: closed form
bad=[]
for c in F['captures']:
    ds=c['canonical'].split('/')[0]; si=c['model_row']['student_input']
    if ds=='arkitscenes':
        if any(si[k] is not None for k in ('fps','timestamps','total_num_frames')) or c.get('timing_source')!='null': bad.append(('arkit_not_null',c['canonical']))
        continue
    t=tok[c['canonical']]; o=d12[t]
    exp_ts=[i/o['fps'] for i in c['anchor_indices']]
    if si['fps']!=float(o['fps']) or si['total_num_frames']!=o['n'] or len(si['timestamps'])!=32 or any(not math.isclose(a,b,rel_tol=1e-12,abs_tol=0) for a,b in zip(si['timestamps'],exp_ts)) or o['n']!=wd[t]['meta_n'] or o['fps']!=wd[t]['fps'] or si['frame_indices']!=c['anchor_indices'] or max(c['anchor_indices'])>=o['n']:
        bad.append(('timing',c['canonical']))
print('closed-form check over 300 captures; bad =',bad)
# ten captures: reader's own Frames.resolve with state built here, plus cv2 on the staged mp4
random.seed(17)
pool=[c for c in F['captures'] if not c['canonical'].startswith('arkitscenes/')]
pick=random.sample([c for c in pool if c['canonical'].startswith('scannet/')],5)+random.sample([c for c in pool if c['canonical'].startswith('scannetpp/')],5)
for c in pick:
    g=G[c['canonical'].split('/')[0]]; t=tok[c['canonical']]; o=d12[t]
    pins=[c['dense_frames'][s] for s in c['anchor_slots']]
    fr=Frames.__new__(Frames)
    fr.frames={(g,t,p['index']):dict(path=p['path'],sha256=p['sha256']) for p in pins}
    fr.plan={'v':{t:{'g':g,'raw_n':o['n']}}}; fr.fps={g+'/'+t:wd[t]['fps']}; fr.dataset_fps={}; fr.authority=None; fr.pins={}
    si=dict(c['model_row']['student_input']); si.update(fps=None,timestamps=None,total_num_frames=None)
    res,prov=fr.resolve({'student_input':si,'frames_pending':{'d':g,'s':t,'i':c['anchor_indices']}})
    # also feed the finalized values back as the source row: reader must accept them
    fr.resolve({'student_input':c['model_row']['student_input'],'frames_pending':{'d':g,'s':t,'i':c['anchor_indices']}})
    fin=c['model_row']['student_input']
    mp4='/scratch/jjyeung/k1/src'+o['mp4']
    cap=cv2.VideoCapture(mp4); cfps=cap.get(cv2.CAP_PROP_FPS); cn=int(cap.get(cv2.CAP_PROP_FRAME_COUNT)); cap.release()
    same=(res['fps']==fin['fps'] and res['timestamps']==fin['timestamps'] and res['total_num_frames']==fin['total_num_frames'])
    print(c['canonical'],t,'reader==finalized',same,'fps',fin['fps'],'cv2_fps',round(cfps,4),'n',fin['total_num_frames'],'cv2_n',cn,'src',prov['fps_source'],'mp4_exists',Path(mp4).exists())
