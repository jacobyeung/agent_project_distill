"""Frozen selector, frozen G3T programs, and scoring-only mask counterfactuals."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from kitlib import *
os.environ['CUDA_VISIBLE_DEVICES']=''
import argparse,collections,itertools,types,copy
import linker as O,features as F,setlib as S,set_features as SF,pair_features as PF,selector_geom as SG
import programs as PR,prog_v2 as V,lane_geometry as L,devs1_pricing as DP,binding as B,tplib as T
F.MAX_PIXELS=300;SG.STEP=2;PF.MAXPTS=1500;PF.REPROJ_D=3.0
MODELS=json.loads((HERE/'vendor/MODELS.json').read_text())
def probability(tag,f):
 m=MODELS[tag];x=np.array([f[k] for k in m['features']])
 if not np.isfinite(x).all():raise ValueError('Nonfinite selector feature')
 z=np.dot((x-np.array(m['mean']))/m['scale'],m['coef'])+m['intercept']
 return float(1/(1+np.exp(-np.clip(z,-700,700))))

def candidates(c,raw,head):
 """Reuse the trained E1 linker, all candidates, and portable no-prior feature functions."""
 geo=PR.load_heads(head);grids=O.lift_grid(geo)
 by={n:O.link(O.lift(raw,n,geo,floor=c.get("cache_contract",{}).get("link_instance_floor",.3),prior=None,grids=grids)[0],n) for n in c['names']};O.scene_candidates(by,geo)
 sc=F.Scene.__new__(F.Scene);sc.raw=raw;sc.geo=geo;sc._masks={};F.H,F.W=c['hw']
 out={}
 for name in c['names']:
  ph=c['names'][name];cs=[]
  for cd in sorted((O.candidate_json(x) for x in by[name]),key=lambda x:(-x['features']['peak'],x['id'])):
   f=cd['features'];mem=[]
   for p in cd['proposals']:
    slot=p['frame']-1;ii,ins=sorted(enumerate(raw['frames'][str(slot)]['phrases'][ph]['instances']),key=lambda x:-x[1]['score'])[p['index']]
    if abs(ins['score']-p['score'])>1e-7:raise ValueError('Linker/raw proposal mismatch')
    mem.append(dict(slot=slot,ii=ii,mask_ref=dict(phrase=ph,instance_index=ii)))
   cs.append(dict(mask_ref=mem[0]['mask_ref'],candidate_id=cd['id'],peak=f['peak'],presence=f['best_presence'],support=f['support'],exclusivity_margin=f['exclusivity_margin'],members=mem))
  if not cs:out[name]=[];continue
  g=dict(object_id=c['scene']+'::'+name,scene=c['scene'],name=name,candidates=cs)
  rr=F.object_rows(g,sc,{k:collections.defaultdict(lambda:.5) for k in ('base','t0')},{'base':{},'t0':{}},collections.defaultdict(lambda:.5),{},np.random.default_rng(17))
  SF.set_features(rr,g)
  for r,cc in zip(rr,cs):
   r['members']=cc['members'];r['masks']={m['slot']+1:decode(raw['frames'][str(m['slot'])]['phrases'][ph]['instances'][m['ii']]['mask'])[::2,::2] for m in cc['members']};r['p']=probability('accept',r['features'])
  out[name]=rr
 return out

def selected(cs,geom,count=False,oracle=False):
 if not cs:return [],[]
 probs={c['candidate_id']:c['p'] for c in cs};cm={c['candidate_id']:c['masks'] for c in cs}
 chosen=([c for c in cs if c['y']] if oracle else S.accept(cs,probs,.15 if count else 2.))
 if not chosen:return [],[]
 ids=[c['candidate_id'] for c in chosen]
 if not count:
  # Label oracle unions accepted candidates, matching selector price3.
  return [SG.union([(i,cm[i]) for i in ids],probs)],ids
 gg={i:PF.geom_of(geom,cm[i]) for i in ids};pair={};blocked=set()
 for a,b in itertools.combinations(chosen,2):
  i,j=a['candidate_id'],b['candidate_id'];f=PF.pair_features(a,b,cm[i],cm[j],gg[i],gg[j],geom);pair[i,j]=pair[j,i]=probability('pairs',f)
  if f['n_disjoint']>0:blocked.update(((i,j),(j,i)))
 groups=S.merge_learned(ids,lambda i,j:pair[i,j],.2,lambda i,j:(i,j) in blocked)
 return [SG.union([(i,cm[i]) for i in group],probs) for group in groups],ids

def base_geometry(depth,pose,Ks):
 b=PR.GTSource.__new__(PR.GTSource);b.depth=depth;b.c2w=pose;b.K=Ks[0];b.Kinv=np.linalg.inv(b.K);b.valid=np.ones(32,bool);b.H,b.W=depth.shape[1:];b.ids=[];b.labels=[];b.obb={};b.inst=np.full(depth.shape,-1,np.int32);return b

def context(base,depth,pose,Ks,objects,absolute=False):
 """Price overlapping instance masks independently through the unchanged frozen Fused class."""
 L.install();L.G.ROOM_VOTE=(2,.05)
 ctx=L.ctx(base,depth,pose,Ks,'frozen',absolute);mapping={};n=0
 for name,insts in objects.items():
  mapping[name.lower()]=[]
  for frames in insts:
   bb=copy.copy(base);bb.inst=np.full(depth.shape,-1,np.int32)
   for k,m in frames.items():
    if m.shape!=depth.shape[1:]:raise ValueError('Mask/depth raster mismatch')
    bb.inst[k-1][m]=n
   one=L.ctx(bb,depth,pose,Ks,'frozen',absolute).fused
   ctx.fused.pts.update(one.pts);ctx.fused.px.update(one.px);mapping[name.lower()].append(n);n+=1
 ctx.ids=lambda name:mapping.get(name.lower(),[])
 return ctx

def predict(q,ctx):
 pred=None;err=q.get('binding_error')
 if not err:
  try:
   if q['question_type']=='object_rel_distance' and B.re.search(r'\b(farthest|furthest)\b',q['question'],B.re.I):
    parsed=T.parse_vsi(q['program']);target=V.boxes_of(ctx,parsed['target']);ds=[V.bdist(ctx,target,bs) if target and (bs:=V.boxes_of(ctx,n)) else -np.inf for n in parsed['cands']];pred=T.letter_of(q['options'],parsed['cands'][int(np.argmax(ds))]) if np.isfinite(ds).any() else None
   else:pred,_=V.run_vsi(q['program'],ctx)
   pred=B.convert(V.finalize(q['question_type'],pred,ctx.fixes),q['question_type'],q['unit'])
   if isinstance(pred,(float,np.floating)) and not np.isfinite(pred):raise ValueError('Nonfinite program answer')
  except (ValueError,KeyError,IndexError,ZeroDivisionError) as e:err=type(e).__name__+': '+str(e);pred=None
 return pred,err

def diagnostic_objects(c,raw,cs,gt):
 ground=PR.GTGround(gt)
 if c['scene'].startswith('scannet/'):V.use_vocab(ground)
 full={};proposed={};ever={};ev={}
 for name,cands in cs.items():
  ids=ground.instances(name);full[name]=[{k:gt.inst[k-1]==i for k in range(1,33) if (gt.inst[k-1]==i).any()} for i in ids]
  hit=collections.defaultdict(dict);ph=c['names'][name]
  for k in range(1,33):
   gs=[(i,gt.inst[k-1]==i) for i in ids];props=[decode(p['mask'])[::2,::2] for p in raw['frames'][str(k-1)]['phrases'][ph]['instances']]
   matches=SF.match_ids([(i,m) for i,m in gs if m.any()],props)
   for i in matches:hit[i][k]=gt.inst[k-1]==i
  proposed[name]=list(hit.values());ever[name]=[f for i,f in zip(ids,full[name]) if i in hit]
  for cc in cands:
   match=[max((SF.iou(m,gt.inst[k-1]==i) for i in ids),default=0.) for k,m in cc['masks'].items()];cc['y']=int(np.mean(np.array(match)>.5)>=.5)
  ev[name]=dict(gt_instances=len(ids),ever_proposed=len(hit),gt_visible_frame_instances=sum(int(m.sum()>=154) for fs in full[name] for m in fs.values()),proposed_visible_frame_instances=sum(int(m.sum()>=154) for fs in proposed[name] for m in fs.values()),candidate_labels={x['candidate_id']:x['y'] for x in cands})
 return full,proposed,ever,ev

def run(a):
 m=json.loads(Path(a.manifest).read_text());validate_manifest(m);msha=sha(a.manifest)
 if getattr(a,'head_pins',None):
  for pin in json.loads(Path(a.head_pins).read_text()):
   if sha(Path(a.exports)/pin['relative'])!=pin['sha256']:raise ValueError('Tower head SHA256 mismatch')
 out=scratch(a.out);out.mkdir(parents=True,exist_ok=True)
 tasks=rows(a.items)
 if m.get('items_sha256') and sha(a.items)!=m['items_sha256']:raise ValueError('Item list SHA256 mismatch')
 by=collections.defaultdict(list)
 for q in tasks:by[q['scene']].append(q)
 gtmap={x['scene']:x for x in rows(a.gt_captures)} if a.gt_captures else {}
 allrows=[];allev=[]
 pricing_binding=digest(dict(manifest=msha,items=sha(a.items),gt_captures=sha(a.gt_captures) if a.gt_captures else None,head_pins=sha(a.head_pins) if getattr(a,'head_pins',None) else None,code={p.name:sha(p) for p in [Path(__file__),HERE/'kitlib.py',*sorted((HERE/'vendor').glob('*.py'))]},models=sha(HERE/'vendor/MODELS.json')))
 for c in m['captures']:
  if a.scene and c['scene']!=a.scene:continue
  sid=c['scene'].replace('/','__');rawpath=Path(a.cache)/(sid+'.npz');raw=validate_cache(load_cache(rawpath),c,msha,a.allow_stub)
  journal=rows(Path(a.cache)/(sid+'.journal.jsonl'))
  if not journal or journal[-1].get('event')!='complete' or journal[-1].get('sha256')!=sha(rawpath):raise ValueError('Candidate commit journal mismatch')
  gt_sha=sha(gtmap[c['scene']]['pricing_gt']) if c['scene'] in gtmap else None
  committed=out/(sid+'.price_complete.json')
  if committed.exists():
   receipt=json.loads(committed.read_text())
   if receipt['binding']!=pricing_binding or receipt['gt_sha256']!=gt_sha or receipt['raw_sha256']!=sha(rawpath) or receipt['rows_sha256']!=sha(out/(sid+'.jsonl')) or receipt['selected_sha256']!=sha(out/(sid+'.selected.npz')):raise ValueError('Pricing resume receipt mismatch')
   allrows+=rows(out/(sid+'.jsonl'));allev.append(receipt['diagnostic']);print('resume priced',c['scene'],flush=True);continue
  h=Path(a.exports)/('heads_'+c['group']+'_vcd')/(sid+'.npz')
  with np.load(h,allow_pickle=False) as z:
   if not np.array_equal(z['anchor_frame_indices'],c['anchor_indices']):raise ValueError('Selector head/PLAN frame mismatch')
  ds,scene=c['scene'].split('/');hw=tuple(x//2 for x in c['hw']);SG.H,SG.W=hw
  depth,pose,Ks=DP.tower_raw(a.exports,ds,scene,c['group'],'g3t',c['anchor_indices'],hw)
  if not np.isfinite(depth).all() or not np.isfinite(pose).all() or (depth<0).any():raise ValueError('Invalid tower geometry')
  geom=SG.GeomTower(h);cs=candidates(c,raw,h)
  unique={};count={};sel={};count_sel={}
  for name,cc in cs.items():unique[name],sel[name]=selected(cc,geom);count[name],count_sel[name]=selected(cc,geom,True)
  from sam_backend import rle_encode
  masks_out=dict(schema='devs1-selected-masks-v1',scene=c['scene'],frame_indices=c['anchor_indices'],raw_sha256=sha(rawpath),model_sha256=sha(HERE/'vendor/MODELS.json'),unique_candidates=sel,count_candidates=count_sel,stub=raw.get('stub',False),unique={n:[{str(k):rle_encode(mask) for k,mask in fs.items()} for fs in instances] for n,instances in unique.items()},counting={n:[{str(k):rle_encode(mask) for k,mask in fs.items()} for fs in instances] for n,instances in count.items()})
  save_cache(out/(sid+'.selected.npz'),masks_out)
  arms={'predicted':(unique,count)};diag={};base=base_geometry(depth,pose,Ks)
  if c['scene'] in gtmap:
   gt,_=L.load_base(gtmap[c['scene']]['pricing_gt'],c['anchor_indices'])
   if gt.inst.shape!=depth.shape:raise ValueError('GT diagnostic raster mismatch')
   full,prop,ever,diag=diagnostic_objects(c,raw,cs,gt)
   oracle_u={n:selected(cc,geom,oracle=True)[0] for n,cc in cs.items()};oracle_c={n:selected(cc,geom,count=True,oracle=True)[0] for n,cc in cs.items()}
   arms.update(oracle_accept=(oracle_u,oracle_c),gt_proposed=(prop,prop),gt_ever_proposed=(ever,ever),gt=(full,full))
  capture_rows=[]
  for arm,(u,cnt) in arms.items():
   contexts={}
   for q in by[c['scene']]:
    counting=q['question_type']=='object_counting';absolute=q['question_type']=='object_abs_distance';key=counting,absolute
    if key not in contexts:contexts[key]=context(base,depth,pose,Ks,cnt if counting else u,absolute)
    pred,err=(None,'No linked candidate for a required operand') if arm in ('predicted','oracle_accept') and any(not cs.get(n.lower()) for n in q['operands']) else predict(q,contexts[key]);score=T.score(q['question_type'],pred,q['released_answer_in_options']) if q['released_answer_in_options'] is not None else None
    capture_rows.append(dict(qid=q['qid'],type=q['question_type'],dataset=ds,scene=c['scene'],room=q['room'],stratum=q['stratum'],fixed=q['fixed'],source='g3t',policy='frozen',arm=arm,pred=pred,score=score,no_answer=pred is None,error=err,stub=raw.get('stub',False),released_answer=q['released_answer_in_options'],selected={n:(count_sel if counting else sel).get(n.lower(),[]) for n in q['operands']} if arm=='predicted' else None))
  write_rows(out/(sid+'.jsonl'),capture_rows);allrows+=capture_rows
  allev.append(dict(scene=c['scene'],objects=diag,gt_available=bool(diag),raw_sha256=sha(rawpath)))
  dump(out/(sid+'.price_complete.json'),dict(binding=pricing_binding,gt_sha256=gt_sha,raw_sha256=sha(rawpath),rows_sha256=sha(out/(sid+'.jsonl')),selected_sha256=sha(out/(sid+'.selected.npz')),diagnostic=allev[-1]))
  print('priced',c['scene'],len(capture_rows),flush=True)
 write_rows(out/'PER_ITEM.jsonl',allrows);write_rows(out/'MASK_DIAGNOSTICS.jsonl',allev)
 dump(out/'COMPLETE.json',dict(manifest_sha256=msha,per_item_sha256=sha(out/'PER_ITEM.jsonl'),diagnostics_sha256=sha(out/'MASK_DIAGNOSTICS.jsonl'),rows=len(allrows),captures=len(allev),stub=bool(a.allow_stub),models_sha256=sha(HERE/'vendor/MODELS.json')))

def main():
 p=argparse.ArgumentParser(__doc__)
 for n in ['manifest','items','cache','exports','out']:p.add_argument('--'+n,required=True)
 p.add_argument('--head-pins',required=True);p.add_argument('--gt-captures');p.add_argument('--scene');p.add_argument('--allow-stub',action='store_true',help='Tests only; route tool refuses these rows')
 run(p.parse_args())
if __name__=='__main__':main()
