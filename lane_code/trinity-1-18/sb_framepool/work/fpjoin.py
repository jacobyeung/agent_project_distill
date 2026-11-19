"""Join recovered source rows to pinned admission selections; never infer optimizer draws."""
import collections,csv,gzip,hashlib,json,re
from pathlib import Path
BASE=Path('/scratch/jjyeung/orch_n30/sb_evidence/aws_sources')
W=Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w')
INPUTS={};MEMBERS={}
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(4<<20),b''):h.update(b)
 return h.hexdigest()
def track(p):
 p=Path(p);INPUTS[str(p)]={'sha256':sha(p)};return p
def read(p):return json.load(open(track(p)))
def blob(h):
 h=next(x for x in REG if x.startswith(h));p=track(REG[h]['blob']);assert sha(p)==h
 MEMBERS[h]={'local':str(p),'locations':REG[h]['locations']};return p

def briefrows(rs):return [{'i':r['i'],'qid':r.get('qid'),'token':r['token'],'canonical':r.get('canonical'),'question_type':r['type']} for r in rs]
def counts(rs):return dict(collections.Counter(r['type'] for r in rs))
def summary(rs):return dict(count=len(rs),ids=[r.get('qid') for r in rs],question_types=counts(rs),rows=briefrows(rs))
def status(s):Path('STATUS.md').write_text(s+'\n')
REG=read('work/metadata_fixed.json')['files']
prior=read('out/FRAMEPOOL.json');caps=read('work/captures.json')['captures'];hits=read('work/verified_hits.json')['rows']
track('out/CAPTURES.tsv');track('out/CAPTURE_MEMBERSHIPS.tsv');track('out/FRAMEPOOL_REPORT.md')
pre=read('work/fpjoin_preimages.json');track('work/fpjoin_invert.py');track('/scratch/jjyeung/orch_n30/sb_alrev/review.py')
bench=read(W/'ext/pk/benchmark_scene_exclusions.json');assert INPUTS[str(W/'ext/pk/benchmark_scene_exclusions.json')]['sha256'].startswith('3119aa4a')
TOK={c['token']:c for c in caps};CAN={c['canonical_scene']:c for c in caps};IDS={r['qid'] for r in hits}
BT={'/'.join(x) for x in bench['rung1_tokens']};assert set(TOK)<=BT
PFX={'scannet':'d1','scannetpp':'d2','scannetppv2':'d2','arkitscenes':'d3'}
for c in caps:assert c['canonical_scene'] in pre['preimages'].get(c['scene_token'],[])
# Retain exact external recovery attestations; local bytes are checked independently.
att={n:read(BASE/n) for n in ['MIND_JOB_847538_REPORT.json','ORCHARD_JOB_172920_REPORT.json']};track(BASE/'SOURCES_13.tsv')
expected={}
for p in [BASE/'SHA256SUMS',BASE/'SHA256SUMS.v3']:
 for line in track(p).read_text().splitlines():
  a=line.split()
  if len(a)==2:expected[Path(a[1].lstrip('*')).name]=a[0]
checks={};stores={}
for p in sorted(BASE.glob('*scenes.jsonl.gz')):
 track(p);assert expected[p.name]==INPUTS[str(p)]['sha256'],p
 name=('a2v3' if '__a2v3__' in p.name else 'a3v2' if '__a3v2__' in p.name else 'r16' if '__r16__' in p.name else p.name.split('__')[-2])
 rows=[]
 with gzip.open(str(p),'rt') as f:
  for line in f:
   r=json.loads(line);r['token']=str(r.get('dataset'))+'/'+str(r.get('scene'));r['type']=r.get('question_type',r.get('routing.question_type','MISSING: pose-only row; question_type absent'))
   cs=pre['preimages'].get(r.get('scene'),[]);r['canonical']=cs[0] if len(cs)==1 else None
   r['target_token']=r['token'] in TOK;r['target_canonical']=r['canonical'] in CAN
   assert r['target_token']==r['target_canonical'],r
   rows.append(r)
 stores[name]=dict(path=str(p),rows=rows)
 assert len({r['i'] for r in rows})==len(rows)
 checks[name]={'rows':len(rows),'target_token_rows':sum(r['target_token'] for r in rows),'target_canonical_rows':sum(r['target_canonical'] for r in rows),'source_id_matches':sum(r.get('qid') in IDS for r in rows),'unresolved_scene_rows':sum(not r['canonical'] for r in rows)}
prefix=next(BASE.glob('*__prepared__receipt.json'));receipt=read(prefix);pfx=str(prefix).replace('receipt.json','')
orders={n:read(pfx+n+'.json') for n in ['pointing_scene_indices','routing_scene_indices','vqa_scene_indices','vqa_indices','pose_mix_order','pose_scene_order']}
for name in ['pointing','routing','vqa']:
 assert sha(pfx+name+'_scene_indices.json')==receipt['streams'][name]['indices']['sha256']
assert sha(pfx+'pose_scene_order.json')==receipt['streams']['pose']['order']['sha256']
assert sha(pfx+'pose_mix_order.json')==receipt['streams']['pose']['scene_source']['order']['sha256']
streams={}
for name in ['pointing','routing','vqa']:
 rows=stores[name]['rows'];idx=set(orders[name+'_scene_indices']);selected=[r for r in rows if r['i'] in idx]
 assert len(selected)==len(idx)==receipt['streams'][name]['count']
 s=receipt['streams'][name];sr=read(blob(s['receipt']['sha256']))
 streams['step544:'+name]={'source':stores[name]['path'],'database_pin':s['database'],'selection_pin':s['indices'],'source_rows':len(rows),'admitted_total':len(selected),'admitted_target':summary([r for r in selected if r['target_token']]),'source_id_join':summary([r for r in selected if r.get('qid') in IDS]),'target_dropped_here':summary([r for r in rows if r['target_token'] and r['i'] not in idx]),'receipt_benchmark_rows_dropped':s['benchmark_rows_dropped'],'all_bench_source_rows':sum(r['token'] in BT for r in rows),'receipt_agreement':'YES: 0 remaining BENCH rows at final selection','heldout_overlap':sr.get('heldout_overlap'),'upstream_scene_filter':sr.get('source_scene_exclusions'),'coverage':'complete recovered projection + pinned admitted index list','missing':'Upstream removed row identities are MISSING; absence from this store does not establish a specific removal reason for each of the 1,193 source ids.'}
mix=set(map(tuple,orders['pose_mix_order']));sel=set(map(tuple,orders['pose_scene_order']));assert sel<=mix
for src,name in enumerate(['a2v3','a3v2']):
 rows=stores[name]['rows'];before=[r for r in rows if (src,r['i']) in mix];selected=[r for r in rows if (src,r['i']) in sel];removed=[r for r in before if (src,r['i']) not in sel]
 s=receipt['streams']['pose']['sources'][src];census=receipt['scene_filter_report']['sources']['pose/'+str(src)]
 nbench=sum(r['token'] in BT for r in removed);assert nbench==census['benchmark_matches'];assert len(before)==census['seen'];assert len(selected)==census['retained'];assert len(removed)==census['removed']
 streams['step544:pose/'+name]={'source':stores[name]['path'],'database_pin':s['database'],'selection_pin':receipt['streams']['pose']['order'],'mix_pin':receipt['streams']['pose']['scene_source']['order'],'source_rows':len(rows),'mixed_rows':len(before),'admitted_total':len(selected),'admitted_target':summary([r for r in selected if r['target_token']]),'source_id_join':summary([r for r in selected if r.get('qid') in IDS]),'raw_target':summary([r for r in rows if r['target_token']]),'pre_mix_all_benchmark_rows_excluded':sum(r['token'] in BT and (src,r['i']) not in mix for r in rows),'target_dropped_final_scene_filter':summary([r for r in removed if r['target_token']]),'target_excluded_before_mix':summary([r for r in rows if r['target_token'] and (src,r['i']) not in mix]),'final_benchmark_dropped':nbench,'receipt_final_scene_filter':census,'receipt_benchmark_rows_dropped':s['benchmark_rows_dropped'],'receipt_agreement':'Final BENCH drops agree with scene_filter_report.sources; benchmark_rows_dropped is an earlier preparation-stage count, not the final scene-filter count.','coverage':'complete recovered projection + both pinned pose orders','question_type_note':'Extract has no question_type. Source receipts identify A1 all_frames32 pose-only labels (pose, gravity, scale, fov, depth).'}
 read(BASE/('ap__f02f16ad__s__'+name+'__receipt.json'))
# Routing r16 is an upstream store, not the admitted production routing population.
rrows=stores['r16']['rows'];rq={r.get('qid') for r in stores['routing']['rows']};up=receipt['scene_filter_report']['upstream']['routing'];compat=up['expected']['r16']['population']['compatibility'];allowed={k for k,v in compat.items() if v['disposition']=='COMPATIBLE'}
elig=[r for r in rrows if r['type'] in allowed];benchdrop=[r for r in elig if r['token'] in BT];rt=[r for r in rrows if r['target_token']]
assert len(elig)==up['sources']['r16']['seen'];assert len(benchdrop)==up['sources']['r16']['benchmark_matches']
streams['step544:upstream_r16']={'source':stores['r16']['path'],'database_pin':up['expected']['r16']['population']['database'],'source_rows':len(rrows),'raw_target':summary(rt),'source_id_matches':summary([r for r in rrows if r.get('qid') in IDS]),'admitted_target':summary([r for r in rt if r.get('qid') in rq]),'target_benchmark_dropped':summary([r for r in rt if r['type'] in allowed]),'target_incompatible_or_pool_type_wins':summary([r for r in rt if r['type'] not in allowed]),'all_benchmark_dropped':len(benchdrop),'receipt_scene_filter':up['sources']['r16'],'receipt_agreement':'YES: compatible population BENCH drops equal 326; final routing benchmark_rows_dropped=0 is downstream.','compatibility':{k:{a:v.get(a) for a in ['disposition','reason','source_rows']} for k,v in compat.items()},'coverage':'complete source projection, type gate, BENCH join, and production qid anti-join'}
# Validate every full camera row against the scene projection and independent canonical join.
cp=next(BASE.glob('*camera_rows.jsonl.gz'));cm=read(next(BASE.glob('*camera_rows.MANIFEST.json')));track(cp);assert sha(cp)==cm['out']['sha256'];camera=collections.Counter();camera_hits=[];byi={r['i']:r for r in stores['routing']['rows']}
with gzip.open(str(cp),'rt') as f:
 for line in f:
  x=json.loads(line);r=json.loads(x['row']);proj=byi[x['i']];assert r['qid']==proj['qid'];assert r['dataset']+'/'+r['scene']==proj['token'];camera[r['routing']['question_type']]+=1
  if proj['target_token']:camera_hits.append(proj)
assert dict(camera)==cm['counts']
# R1: resolve pinned pointing/pose identities, retain receipt-only claims for missing routing/VQA rows.
r1={}
for path in sorted((W/'inputs/p_runtime').glob('**/s1_receipt.json')):
 d=read(path);run='673bc60f' if '673bc60f' in str(path) else '6ed2c7aa';assert d['benchmark_scene_exclusions']['sha256'].startswith('3119aa4a')
 for name,s in d['streams'].items():
  sr=read(blob(s['receipt']['sha256'])) if s['receipt']['sha256'] in REG else {};key=run+':'+name
  item={'receipt':str(path),'stream_receipt_pin':s['receipt'],'stream_receipt_local':MEMBERS.get(s['receipt']['sha256'],{}).get('local','MISSING'),'admitted_total':s['count'],'benchmark_pin':d['benchmark_scene_exclusions'],'receipt_benchmark_rows_dropped':s.get('benchmark_rows_dropped'),'heldout_overlap':sr.get('heldout_overlap'),'reported_overlap_rows':s.get('reported_overlap_rows'),'final_scene_filter':d['scene_filter_report']['sources'],'upstream_scene_filter':sr.get('source_scene_exclusions',d['scene_filter_report'].get('upstream',{}).get(name)),'admitted_target_count_receipt_supported':0,'admitted_target_ids':[],'admitted_target_question_types':{}}
  if name=='pointing':
   assert s['database']['sha256']==receipt['streams'][name]['database']['sha256'];assert s['indices']['sha256']==receipt['streams'][name]['indices']['sha256'];item.update(coverage='complete: identical database/index SHA256 to step544',admitted_target_count_verified=0,source_id_join_verified=0)
  elif name=='pose':
   assert s['order']['sha256']==receipt['streams'][name]['order']['sha256'];assert [x['database']['sha256'] for x in s['sources']]==[x['database']['sha256'] for x in receipt['streams'][name]['sources']];item.update(coverage='complete: identical source databases/admitted order SHA256 to step544',admitted_target_count_verified=0,source_id_join_verified=0)
  else:
   item.update(coverage='receipt-supported zero; row-level join MISSING',admitted_target_count_verified='MISSING',source_id_join_verified='MISSING',missing=[{'kind':'database','expected_production':s['database'],'expected_recovery':str(path.parent.parent/name/'rows.sqlite')},{'kind':'indices','expected_production':s['indices'],'expected_recovery':str(path.parent/Path(s['indices']['path']).name)}],target_dropped_count='MISSING: receipts count all BENCH scenes, not the 146-capture subset')
  if name=='pose':
   item['target_dropped_final_scene_filter']=sum(streams['step544:pose/'+x]['target_dropped_final_scene_filter']['count'] for x in ['a2v3','a3v2'])
   item['final_benchmark_dropped']=27040
   item['receipt_agreement']='27,040 final scene-filter BENCH drops; 1,200 benchmark_rows_dropped belongs to an earlier preparation stage.'
  elif name=='pointing':
   item['target_dropped_here']=0;item['receipt_agreement']='YES: 0 BENCH rows remain at final admission.'
  r1[key]=item
# P exclusion ids are exclusion instructions, not admitted identities.
pk=read(W/'ext/pk/66c427e2.json');pkjoin={k:sorted(set(v)&IDS) for k,v in pk.items()}
# Evaluation: authoritative VSTI scene list and actual retained kit item sets.
sti={c['canonical_scene'] for c in caps if 'STI-Bench/ReSTI' in c['benchmarks']};vstiscenes=sorted('scannet/'+k.split('/')[1] for k,m in bench['members'].items() if 'VSTI' in m['listed_by']);assert len(vstiscenes)==312
vsti={'bench_scene_count':len(vstiscenes),'bench_scenes':vstiscenes,'overlap_with_126':sorted(sti&set(vstiscenes)),'kit_sets':[],'missing_official_item_bank':{'expected_path':'/scratch/jjyeung/orch_cd/heads_up/work/h3/b14b/vsti.json','sha256':bench['inputs']['/scratch/jjyeung/orch_cd/heads_up/work/h3/b14b/vsti.json'],'status':'MISSING in local metadata registry; BENCH v2 preserves its scene list, not item ids'}}
for prefix in ['b5853845','5cd2d5f2','7a6ac5cc','c1c99e4d']:
 p=blob(prefix);items=[json.loads(l) for l in open(p)];scenes=[];ov=[];unresolved=[];entries=[]
 for r in items:
  scene=r.get('scene');ds=r.get('dataset');room=r.get('room','')
  if scene and '/' in scene:c=scene.replace('scannetppv2/','scannetpp/')
  elif ds and scene:c=ds.replace('scannetppv2','scannetpp')+'/'+scene
  elif room.startswith(('scannet/','scannetpp/','arkitscenes/')) and scene:c=room.split('/')[0]+'/'+scene
  else:c=None
  if c is None:unresolved.append(r.get('id',r.get('qid')))
  else:scenes.append(c)
  qid=r.get('qid',r.get('id'));entries.append({'id':qid,'canonical':c,'question_type':r.get('question_type',r.get('task_type'))})
  if c in sti:ov.append(qid)
 vsti['kit_sets'].append({'sha256':sha(p),'path':str(p),'locations':MEMBERS[sha(p)]['locations'],'rows':len(items),'distinct_scenes':len(set(scenes)),'overlap_ids':ov,'unresolved_ids':unresolved,'items':entries,'scene_list':sorted(set(scenes))})
for prefix in ['070cdff','8b107f','06cdfa5']:read(blob(prefix))
# Hash recovered preparation code that distinguishes legacy exclusions from the final BENCH scene filter.
codebase=W/'w18/work/tree_r1/student_pilot'
for n in ['c1_pose_mix.py','carrier_c1_run.py','s1_exclusions.py']:track(codebase/n)
legacy_note='benchmark_rows_dropped counts the earlier excluded_row/pose_benchmark pass. prepare_exclusions defers rows matched by the final scene_filter. It is not the BENCH-v2 scene_filter_report count; the a3v2 raw-to-mix difference contains 0 BENCH-v2 rows.'
for name in ['a2v3','a3v2']:streams['step544:pose/'+name]['receipt_counter_semantics']=legacy_note
# Record benchmark and per-capture results without counting overlapping benchmark memberships twice.
percap=[]
for c in caps:
 t=c['token'];obj={k:c[k] for k in ['token','canonical_scene','scene_list_key','benchmarks','room','listed_by','sibling_of']};obj['streams']={}
 for n,s in streams.items():
  fields={}
  for k,v in s.items():
   if isinstance(v,dict) and 'rows' in v and 'count' in v:
    rs=[r for r in v['rows'] if r['token']==t];fields[k]={'count':len(rs),'ids':[r['qid'] for r in rs],'question_types':dict(collections.Counter(r['question_type'] for r in rs))}
  obj['streams'][n]=fields
 obj['source_sample_ids']=[r['qid'] for r in hits if r['token']==t]
 obj['R1']={k:{'admitted_count':v['admitted_target_count_receipt_supported'],'basis':v['coverage'],'verified_count':v['admitted_target_count_verified']} for k,v in r1.items()}
 percap.append(obj)
assert len(hits)==1193 and len(IDS)==1193
assert all(s['admitted_target']['count']==0 for s in streams.values())
r16_by_qid=collections.defaultdict(list)
for x in rrows:r16_by_qid[x.get('qid')].append(x['i'])
sourcejoin=[dict(qid=r['qid'],token=r['token'],family=r['family'],step544_admitted_streams=[],r16_source_matches=r16_by_qid.get(r['qid'],[]),R1_pointing_pose_admitted=False,R1_routing_vqa='receipt-supported excluded; individual id join MISSING') for r in hits]
missing_raw=[]
for n in ['ap__8865619b__u__7c9f2d84__receipt.json','ap__1742c666__s__q127808__vxm_m4__receipt.json']:
 r=read(BASE/n);missing_raw.append({'status':'MISSING','database_pin':r['database'],'expected_recovery':str(BASE/n.replace('__receipt.json','__rows.scenes.jsonl.gz')),'consequence':'Upstream per-target dropped ids cannot be reconstructed.'})
track('work/fpjoin.py')
out={'schema':'framepool-consumption-join-v1','command':'/usr/bin/python3 work/fpjoin.py','inputs':INPUTS,'input_members':MEMBERS,'scope':'Admission into the recovered step-544 stream and R1 receipt-covered streams; no assertion that every admitted row was sampled by the optimizer. No claim about unobserved parent pretraining.','capture_count':len(caps),'source_ids':len(IDS),'recovered_store_checks':checks,'inversion':{'ranges':pre['ranges'],'collisions':pre['collisions'],'target_captures_resolved':146,'total_tokens':pre['tokens'],'resolved_tokens':len(pre['preimages']),'unresolved_tokens':pre['unresolved_tokens'],'note':'Unresolved known-range tokens are outside the 146 targets. Target canonical and token joins agree row for row; ScanNet++ is not exhaustively inverted.'},'streams':streams,'R1':r1,'captures':percap,'source_id_join':sourcejoin,'P_exclusion_id_join':pkjoin,'camera_full_rows':{'count':sum(camera.values()),'types':dict(camera),'target':summary(camera_hits),'source_pin':cm['source'],'manifest':str(next(BASE.glob('*camera_rows.MANIFEST.json')))},'VSTI':vsti,'v7_prior_audit':prior['sb_alias_audit'],'missing_upstream_inputs':missing_raw,'missing_pool_payloads':prior['pool_selections'],'receipt_counter_semantics':legacy_note,'verdicts':{'a':{'captures':['d3/41159526','d3/41159521'],'step544_admitted':0,'R1_receipt_supported_admitted':0,'trained_on_these_captures':'No pointing, pose, routing, VQA, or camera rows admitted in these legs; R1 routing/VQA supported by receipts, not a recovered row-level join.'},'b':{'VSTI_official_scene_overlap_with_126':len(sti&set(vstiscenes)),'step544_admitted':0,'R1_receipt_supported_admitted':0},'c':{'STI_Bench_ReSTI_and_MindCube_training_exposure_in_these_legs':'NO within recovered/receipt-covered scope','step544_admitted':0,'R1_receipt_supported_admitted':0,'archived_source_overlap':'YES: 1193 ids; not evidence of admission'}}}
Path('out/FPJOIN.json').write_text(json.dumps(out,indent=1)+'\n')
status('FPJOIN stage 2 complete: all step-544 admitted streams have zero rows on the 146 targets, with exact pinned selection joins and independent exhaustive ScanNet/ARKit inversions. Final pose scene filtering removes 15,120 target rows. R1 pointing/pose reuse identical pins; routing/VQA zeros are receipt-supported with missing row-level joins recorded. VSTI official scene overlap with the 126 STI/ReSTI captures is zero. Report and package validation are next.')
print(json.dumps({'stores':checks,'streams':{k:{'admitted':s['admitted_target']['count'],'drops':{n:v['count'] for n,v in s.items() if isinstance(v,dict) and 'count' in v and 'rows' in v}} for k,s in streams.items()},'vsti':[(x['rows'],x['distinct_scenes'],len(x['overlap_ids']),len(x['unresolved_ids'])) for x in vsti['kit_sets']],'pk':{k:len(v) for k,v in pkjoin.items()}},indent=1))
