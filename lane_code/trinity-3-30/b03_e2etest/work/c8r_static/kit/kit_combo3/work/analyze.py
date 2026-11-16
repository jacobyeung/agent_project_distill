"""Read-only candidate audit and GT-grant repricing with the frozen executor."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from kitlib import *
import price_masks as P
import route_table as RT
import collections,copy,argparse
CAUSES=['no_visible_pixels','below_program_size','few_views','lexical_mismatch','presence_gate','unresolved']

def relation(prompt,label):
 a,b=normalize_phrase(prompt),normalize_phrase(label)
 if a=='ceiling light' and b=='ceiling':return 'annotation_binding_suspect'
 if a==b:return 'exact'
 if a=='table' and b=='desk':return 'query_coarser'
 if {a,b}=={'trash bin','trash can'}:return 'synonym'
 if a in b:return 'query_coarser'
 if b in a:return 'query_finer'
 if {a,b} in ({'sofa','couch'},{'tv','television'},{'refrigerator','fridge'}):return 'synonym'
 return 'other_vocab_mapping'

def cause(r):
 if not r['visible_frames']:return 'no_visible_pixels'
 if r['largest_pixels']<154:return 'below_program_size'
 if r['usable_frames']<=2:return 'few_views'
 if r['prompt_relation']!='exact':return 'lexical_mismatch'
 if r['presence_max_visible']<.2:return 'presence_gate'
 return 'unresolved'

def audit_capture(c,raw,gt,selected,tasks):
 ground=P.PR.GTGround(gt)
 if c['scene'].startswith('scannet/'):P.V.use_vocab(ground)
 labels=dict(zip(map(int,gt.ids),gt.labels));result=[];full={};ever={};stats=[];missing=[]
 for name,ph in c['names'].items():
  ids=ground.instances(name);full[name]=[];ever[name]=[]
  qs=[q for q in tasks if name in [n.lower() for n in q['operands']]]
  if not ids:missing.append(dict(scene=c['scene'],name=name,qids=[q['qid'] for q in qs]))
  rr={}
  for i in ids:
   fs={k:gt.inst[k-1]==i for k in range(1,33) if (gt.inst[k-1]==i).any()};full[name].append(fs)
   areas=[int(m.sum()) for m in fs.values()];best=max(fs,key=lambda k:fs[k].sum()) if fs else None
   ds=gt.depth[best-1][fs[best]] if best else np.array([]);ds=ds[np.isfinite(ds)&(ds>0)]
   distance=float(np.linalg.norm(np.asarray(gt.obb[i]['centroid'])-gt.c2w[best-1,:3,3])) if best and i in gt.obb else None
   fill=None;edge=None
   if best:
    yy,xx=np.where(fs[best]);fill=float(len(xx)/((xx.max()-xx.min()+1)*(yy.max()-yy.min()+1)));edge=bool(xx.min()==0 or yy.min()==0 or xx.max()==gt.W-1 or yy.max()==gt.H-1)
   pres=[raw['frames'][str(k-1)]['phrases'][ph]['presence'] for k in fs]
   rr[i]=dict(scene=c['scene'],dataset=c['scene'].split('/')[0],name=name,prompt=ph,instance_id=i,label=labels[i],prompt_relation=relation(ph,labels[i]),qids=[q['qid'] for q in qs],primary_qids=[q['qid'] for q in qs if q['stratum']=='primary'],visible_frames=len(fs),usable_frames=sum(a>=154 for a in areas),largest_pixels=max(areas,default=0),largest_pixels_input=max(areas,default=0)*4,largest_slot=best-1 if best else None,distance_camera_m=distance,median_surface_depth_m=float(np.median(ds)) if len(ds) else None,occlusion='unavailable',bbox_fill_proxy=fill,touches_border_proxy=edge,presence_max_visible=max(pres,default=0.),presence_mean_visible=float(np.mean(pres)) if pres else None,matched_frames=[],best_iou=0.,best_score=None,best_joint=None,matched_max_score=None,matched_max_joint=None,accepted_unique_frames=[],accepted_count_frames=[],frames=[])
  for k in range(1,33):
   rec=raw['frames'][str(k-1)]['phrases'][ph];props=rec['instances'];pm=[decode(p['mask'])[::2,::2] for p in props];gms=[(i,gt.inst[k-1]==i) for i in ids if (gt.inst[k-1]==i).any()]
   hits=set(P.SF.match_ids(gms,pm));valid_props=set()
   for i,m in gms:
    r=rr[i];ious=[P.SF.iou(m,p) for p in pm];j=int(np.argmax(ious)) if ious else None;v=max(ious,default=0.)
    valid_props.update(jj for jj,x in enumerate(ious) if x>.5)
    if v>r['best_iou']:r.update(best_iou=v,best_score=props[j]['score'],best_joint=props[j]['joint_score'])
    if i in hits:
     r['matched_frames'].append(k-1);r['matched_max_score']=max(r['matched_max_score'] or 0,max(p['score'] for p,x in zip(props,ious) if x>.5));r['matched_max_joint']=max(r['matched_max_joint'] or 0,max(p['joint_score'] for p,x in zip(props,ious) if x>.5))
    for key,field in [('unique','accepted_unique_frames'),('counting','accepted_count_frames')]:
     if any(str(k) in fs and P.SF.iou(m,decode(fs[str(k)]))>.5 for fs in selected.get(key,{}).get(name,[])):r[field].append(k-1)
    r['frames'].append(dict(slot=k-1,frame_index=c['anchor_indices'][k-1],pixels=int(m.sum()),iou=v,matched=i in hits,presence=rec['presence'],retained=len(props),above_floor=rec['n_above_floor'],score=props[j]['score'] if j is not None else None,joint=props[j]['joint_score'] if j is not None else None,cap_saturated=rec['n_above_floor']>c.get('cache_contract',{}).get('cap',10)))
   stats.append(dict(scene=c['scene'],dataset=c['scene'].split('/')[0],name=name,slot=k-1,gt_visible=len(gms),gt_usable=sum(int(m.sum())>=154 for i,m in gms),matched=len(hits),matched_usable=sum(i in hits and int(m.sum())>=154 for i,m in gms),proposals=len(pm),matched_proposals=len(valid_props)))
  for i,fs in zip(ids,full[name]):
   r=rr[i];r['ever_proposed']=bool(r['matched_frames']);r['matched_frames_count']=len(r['matched_frames']);r['accepted_unique']=bool(r['accepted_unique_frames']);r['accepted_count']=bool(r['accepted_count_frames']);r['cause']=None if r['ever_proposed'] else cause(r);result.append(r)
   if r['ever_proposed']:ever[name].append(fs)
 return result,full,ever,stats,missing

def contexts_for_sets(c,gt,full,records,exports):
 ds,scene=c['scene'].split('/');depth,pose,Ks=P.DP.tower_raw(exports,ds,scene,c['group'],'g3t',c['anchor_indices'],gt.inst.shape[1:]);base=P.base_geometry(depth,pose,Ks)
 contexts={};idx={};n=0
 for name,fs in full.items():
  rs=[r for r in records if r['name']==name]
  for r in rs:idx[name,r['instance_id']]=n;n+=1
 for absolute in (False,True):contexts[absolute]=P.context(base,depth,pose,Ks,full,absolute)
 return contexts,idx

def run(a):
 out=Path(a.out);out.mkdir(parents=True,exist_ok=True);m=json.loads(Path(a.manifest).read_text());P.validate_manifest(m);gtmap={r['scene']:r for r in rows(a.gt_captures)};tasks=rows(a.items);by=collections.defaultdict(list)
 for q in tasks:by[q['scene']].append(q)
 allr=[];allstats=[];missing=[];cf=[];parity=[];base_rows=rows(a.baseline_program);baseline={(r['qid'],r['arm']):r for r in base_rows};msha=sha(a.manifest)
 for c in m['captures']:
  if c['scene'] not in gtmap:continue
  sid=c['scene'].replace('/','__');raw=P.validate_cache(load_cache(Path(a.cache)/(sid+'.npz')),c,msha);gt,_=P.L.load_base(gtmap[c['scene']]['pricing_gt'],c['anchor_indices']);sel=load_cache(Path(a.selected)/(sid+'.selected.npz'))
  rs,full,ever,stats,miss=audit_capture(c,raw,gt,sel,by[c['scene']]);allr+=rs;allstats+=stats;missing+=miss
  ctxs,idx=contexts_for_sets(c,gt,full,rs,a.exports)
  for arm in ['gt_ever_proposed','gt']+CAUSES:
   mapping={n:[] for n in full}
   for r in rs:
    if arm=='gt' or r['ever_proposed'] or r['cause']==arm:mapping[r['name']].append(idx[r['name'],r['instance_id']])
   for q in by[c['scene']]:
    ctx=copy.copy(ctxs[q['question_type']=='object_abs_distance']);ctx.ids=lambda name,mp=mapping:mp.get(name.lower(),[])
    pred,err=P.predict(q,ctx);score=P.T.score(q['question_type'],pred,q['released_answer_in_options']) if q['released_answer_in_options'] is not None else None
    r=dict(baseline[q['qid'],'gt'],arm=arm,pred=pred,score=score,no_answer=pred is None,error=err);cf.append(r)
    if arm in ('gt','gt_ever_proposed'):
     old=baseline[q['qid'],arm];parity.append(dict(qid=q['qid'],arm=arm,equal=(score==old['score'] and pred==old['pred']),old_score=old['score'],score=score))
  write_rows(out/(sid+'.instances.jsonl'),rs);print('audited',c['scene'],len(rs),flush=True)
 write_rows(out/'PER_INSTANCE.jsonl',allr);write_rows(out/'FRAME_METRICS.jsonl',allstats);write_rows(out/'UNBOUND_OPERANDS.jsonl',missing);write_rows(out/'CAUSE_PER_ITEM.jsonl',cf);dump(out/'REPRICE_PARITY.json',dict(rows=len(parity),mismatches=[r for r in parity if not r['equal']]))
 if any(not r['equal'] for r in parity):raise ValueError('GT repricing parity failed')
 direct=json.loads(Path(a.direct).read_text());baseline_route=RT.build(tasks,direct,base_rows);dump(out/'BASELINE_ROUTE.json',baseline_route)
 comparisons={};direct_ids={x["key"].removeprefix("devrows:") for x in direct["rows"]}
 for arm in CAUSES:
  replacements={r['qid']:r for r in cf if r['arm']==arm};program=[dict(replacements[r['qid']],arm='predicted') if r['arm']=='predicted' and r['qid'] in replacements else r for r in base_rows];d=RT.build(tasks,direct,program);dump(out/('GRANT_'+arm+'.json'),d)
  vals=[]
  for dataset,typ in sorted({(r['dataset'],r['type']) for r in d['table']}):
   keep=[r for r in cf if r['arm']==arm and r['stratum']=='primary' and r['qid'] in direct_ids and r['type']==typ and (dataset=='All' or r['dataset']==dataset)]
   v=RT.interval([(r['room'],baseline[r['qid'],'gt_ever_proposed']['score'],r['score']) for r in keep])
   if v:vals.append(dict(dataset=dataset,type=typ,**v))
  comparisons[arm]=vals
 dump(out/'CAUSE_CONTRASTS.json',comparisons)
 dump(out/'AUDIT_COMPLETE.json',dict(captures=sum(c['scene'] in gtmap for c in m['captures']),instances=len(allr),never=sum(not r['ever_proposed'] for r in allr),manifest_sha256=msha))

if __name__=='__main__':
 p=argparse.ArgumentParser()
 for n in ['manifest','items','cache','selected','gt-captures','exports','baseline-program','direct','out']:p.add_argument('--'+n,required=True)
 run(p.parse_args())
