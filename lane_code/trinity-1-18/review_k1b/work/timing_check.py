import sys,json,math,random,statistics
sys.dont_write_bytecode=True
TREE='/scratch/jjyeung/orch_cd/leg_s1_tree/work/tree_s1_admissionfix_168872'
sys.path.insert(0,TREE)
from student_pilot.s1_routing import Frames
from student_pilot.trace_targets import patch_times
W='/scratch/jjyeung/orch_n30/k1_ops3/work/'
OLD=json.load(open(W+'codex_finalize_v2/K1_MANIFEST.finalized.json'))
NEW=json.load(open(W+'codex_arkit_timing/K1_MANIFEST.arkit_timing.json'))
rates=json.load(open(W+'kit07ca49df/k/frame_rates.json'))
tok={}
for l in open('/scratch/jjyeung/orch_cd/k1_ops/work/CANON_TOKENS.jsonl'):
    r=json.loads(l); tok.setdefault(r['canonical'],r['s'])
wa={}
for l in open(W+'WA_OUT.jsonl'):
    r=json.loads(l); wa[r['s']]=r
plan=json.load(open('/scratch/jjyeung/orch_cd/k1_ops/work/D3_FETCH_PLAN.json'))
K=('fps','timestamps','total_num_frames')
# 1. diff
def walk(a,b,p,out):
    if type(a)!=type(b): out.append(p);return
    if isinstance(a,dict):
        for k in set(a)|set(b):
            if k not in a or k not in b: out.append(p+'/'+k)
            else: walk(a[k],b[k],p+'/'+k,out)
    elif isinstance(a,list):
        if len(a)!=len(b): out.append(p);return
        for i,(x,y) in enumerate(zip(a,b)): walk(x,y,p+'/'+str(i),out)
    elif a!=b: out.append(p)
d=[];walk(OLD,NEW,'',d)
top=[x for x in d if not x.startswith('/captures/')]
cap=[x for x in d if x.startswith('/captures/')]
import collections,re
leaf=collections.Counter(re.sub(r'^/captures/\d+/','',x).split('/timestamps')[0]+('/timestamps' if '/timestamps' in x else '') for x in cap)
idx={int(x.split('/')[2]) for x in cap}
print('DIFF top-level paths:',sorted(top)[:20],len(top))
print('DIFF capture leaf kinds:',dict(leaf))
print('DIFF captures changed:',len(idx),'all arkit:',all(OLD['captures'][i]['canonical'].startswith('arkitscenes/') for i in idx))
for k in set(OLD)|set(NEW):
    if OLD.get(k)!=NEW.get(k): print('  top key differs:',k)
if OLD.get('k1_finalize')!=NEW.get('k1_finalize'):
    a,b=OLD['k1_finalize'],NEW['k1_finalize']
    print('  k1_finalize keys old',sorted(a),'new',sorted(b))
    for k in set(a)|set(b):
        if a.get(k)!=b.get(k): print('   k1_finalize.'+k,'differs; new value keys:',list(b.get(k).keys()) if isinstance(b.get(k),dict) else str(b.get(k))[:200])
ark=[c for c in NEW['captures'] if c['canonical'].startswith('arkitscenes/')]
cov=[c for c in ark if 'd3/'+tok[c['canonical']] in rates['by_scene']]
unc=[c for c in ark if c not in cov]
print('arkit',len(ark),'covered',len(cov),'uncovered',len(unc))
def reader(c,fps_authority):
    t=tok[c['canonical']];pins=[c['dense_frames'][s] for s in c['anchor_slots']]
    fr=Frames.__new__(Frames)
    fr.frames={('d3',t,p['index']):dict(path=p['path'],sha256=p['sha256']) for p in pins}
    fr.plan={'v':{}};fr.fps={};fr.pins={}
    fr.authority=fps_authority;fr.dataset_fps={}
    si=dict(c['model_row']['student_input']);si.update(fps=None,timestamps=None,total_num_frames=None)
    res,prov=fr.resolve({'student_input':si,'frames_pending':{'d':'d3','s':t,'i':c['anchor_indices']}})
    # and the reader must accept the manifest values as a source row
    res2,_=fr.resolve({'student_input':c['model_row']['student_input'],'frames_pending':{'d':'d3','s':t,'i':c['anchor_indices']}})
    patch_times(dict(c['model_row']['student_input']))
    return res,prov
random.seed(23)
print('--- 10 covered: reader with sealed frame_rates.json as authority')
for c in random.sample(cov,10):
    res,prov=reader(c,rates);si=c['model_row']['student_input']
    eq={k:res[k]==si[k] for k in K}
    print(c['canonical'],tok[c['canonical']],eq,'fps',si['fps'],'n',si['total_num_frames'],'src',prov['fps_source'],'lb',prov['total_num_frames_lower_bound'])
def slope(pts):
    n=len(pts);mx=sum(i for i,_ in pts)/n;my=sum(t for _,t in pts)/n
    return sum((i-mx)*(t-my) for i,t in pts)/sum((i-mx)**2 for i,_ in pts)  # sec per index
print('--- 10 derived: my least-squares fps from WA per-frame source timestamps')
for c in random.sample(unc,10):
    t=tok[c['canonical']];fr={r[0]:r[5] for r in wa[t]['frames']}
    dense=[f['index'] for f in c['dense_frames']]
    pts=[(i,fr[i]) for i in dense];spi=slope(pts);fps_raw=1/spi;fps=float(round(fps_raw))
    ts=[i/fps for i in c['anchor_indices']];n=max(c['anchor_indices'])+1
    si=c['model_row']['student_input']
    resid=max(abs((tt-pts[0][1])-(i-pts[0][0])*spi) for i,tt in pts)
    # reader with a one-scene authority at my fps
    res,prov=reader(c,{'schema':'s1-fps-authority-v1','by_scene':{'d3/'+t:fps}})
    print(c['canonical'],t,'lsq_fps',round(fps_raw,5),'mine==manifest',dict(fps=fps==si['fps'],ts=all(math.isclose(a,b,rel_tol=1e-12) for a,b in zip(ts,si['timestamps'])) and len(si['timestamps'])==32,n=n==si['total_num_frames']),'reader==manifest',all(res[k]==si[k] for k in K),'max_resid_s',round(resid,4))
print('--- gaps over all 162: consecutive dense samples whose elapsed time exceeds index spacing at 10 Hz by >0.15 s (1.5 periods), WA and plan')
gaps=[];worst=(0,None)
for c in ark:
    t=tok[c['canonical']];fr={r[0]:r[5] for r in wa[t]['frames']};need={r[0]:r[1] for r in plan[t]['need']}
    fps=c['model_row']['student_input']['fps']
    if fps!=10.0: gaps.append((c['canonical'],'fps',fps))
    dense=[f['index'] for f in c['dense_frames']]
    for src,m in (('wa',fr),('plan',need)):
        for a,b in zip(dense,dense[1:]):
            ex=(m[b]-m[a])-(b-a)/fps
            if abs(ex)>abs(worst[0]):worst=(ex,(c['canonical'],src,a,b))
            if ex>0.15 or ex< -0.15: gaps.append((c['canonical'],src,a,b,round(ex,4)))
    n=c['model_row']['student_input']['total_num_frames']
    if n!=max(c['anchor_indices'])+1: gaps.append((c['canonical'],'n',n))
    if max(dense)>=n: gaps.append((c['canonical'],'dense_beyond_n',max(dense),n))
print('gap/irregularity rows:',len(gaps),gaps[:20]);print('largest |excess|:',worst)
cnt=collections.Counter(max(f['index'] for f in c['dense_frames'])-max(c['anchor_indices']) for c in ark)
print('max(dense)-max(anchor) distribution over 162:',sorted(cnt.items())[:10])
