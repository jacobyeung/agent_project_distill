"""Replay available source filters; refuse to label source offsets as prepared offsets."""
from common import *
import sqlite3,resource,collections
resource.setrlimit(resource.RLIMIT_AS,(36*1024**3,36*1024**3))
track(__file__)
import torch
torch.set_num_threads(16)
from student_pilot.row_removals import Removals,row_keys
from student_pilot.r1_population import family
from student_pilot.r1_direction_twins import Binding,dimensions
from student_pilot.r1_coverage import WordingExclusion
from student_pilot.r1_launch22 import validate_removals
from student_pilot.r1_training import row_check
from student_pilot.s1_exclusions import Exclusions
from student_pilot.r0_exclusion import reserve
from student_pilot.carrier_c1_routing import load_exclusions,excluded
from student_pilot.r1_counting import admit
from student_pilot.extent_receipt import required
cfg=config();card=P.load(resolve(cfg['r2_sampling']['card']))
validate_removals(cfg);removals=Removals(cfg['remove_files'])
print('Authenticating twins and room authority',flush=True)
twins=Binding(cfg);resolve(twins.spec['source_map'])
wording=WordingExclusion(cfg['r1_training']['wording_exclusion'],cfg['r1_training']['camera_wording_exclusion'])
scenes=Exclusions(cfg['dev_scene_exclusions'],cfg['benchmark_scene_exclusions'])
held=P.load(resolve(cfg['exclude_qids']));benchmark=load_exclusions(cfg['exclusions']);r0=reserve();track(T/'student_pilot/r0_scenes.json')
stages=['raw']+['remove_'+str(i) for i in range(12)]+['room','scene','held_qid','benchmark','wording','row_check','r0','counting']
counts={s:collections.Counter() for s in stages};hashes={s:{} for s in stages};refusals=collections.Counter();examples={};source_counts=collections.Counter()
root=W/'work/source';root.mkdir(exist_ok=True);dbpath=root/'eligible_vqa.sqlite'
assert not dbpath.exists();dest=sqlite3.connect(dbpath);dest.execute('CREATE TABLE rows(i INTEGER PRIMARY KEY,row TEXT NOT NULL,target TEXT NOT NULL,cell TEXT NOT NULL,source TEXT NOT NULL,source_i INTEGER NOT NULL,row_sha256 TEXT NOT NULL)')
allgroups={c['type']:[] for c in card['cells'] if c['stream']=='vqa'};direction_count=0;all_count=0
extent_rows=0;missing_stage=[]
def stage(s,k,ident):
 counts[s][k]+=1
 if k not in hashes[s]:hashes[s][k]=hashlib.sha256()
 hashes[s][k].update(ident)
def refuse(stage_name,row,e):
 key=stage_name+':'+str(e);refusals[key]+=1;examples.setdefault(key,row['qid'])
def process(row,target,source,i):
 global direction_count,all_count,extent_rows
 k=family(row,'vqa');source_counts[source]+=1;h=P.digest(row)
 ident=P.encoded([source,i,row['qid'],h]).encode()+b'\n';stage('raw',k,ident)
 keys=row_keys(row)
 for n,removed in enumerate(removals.keys):
  if keys&removed:refuse('remove_'+str(n),row,'listed');return
  stage('remove_'+str(n),k,ident)
 status,canonical,_=twins.strict.status(row)
 if status=='unresolved':
  canonical,_=twins.tiered.canonical(row)
  if canonical:
   room=twins.strict.room(canonical);status='r0' if room in twins.strict.r0 else 'k1_heldout' if room in twins.strict.k1 else 'ok'
 if status!='ok':refuse('room',row,status);return
 stage('room',k,ident)
 if scenes.excluded(row):refuse('scene',row,'excluded');return
 stage('scene',k,ident)
 if row['qid'] in held.get('vqa',[]):refuse('held_qid',row,'excluded');return
 stage('held_qid',k,ident)
 if excluded(benchmark,row['dataset']+'/'+row['scene'],canonical):refuse('benchmark',row,'excluded');return
 stage('benchmark',k,ident)
 for name,fn in [('wording',lambda:wording.check(row)),('row_check',lambda:row_check(row,'vqa')),('r0',lambda:r0.check(row,'vqa')),('counting',lambda:admit(row,k))]:
  try:fn()
  except (ValueError,KeyError,TypeError) as e:refuse(name,row,e);return
  stage(name,k,ident)
 if required(row,'vqa'):extent_rows+=1
 if k not in allgroups:refuse('unassigned',row,k);return
 allgroups[k].append(all_count)
 dest.execute('INSERT INTO rows VALUES(?,?,?,?,?,?,?)',(all_count,P.encoded(row),P.encoded(target),k,source,i,h));all_count+=1
 if k in ('direction','facing_pairs'):direction_count+=1
print('Streaming VQA filters',flush=True)
conn=sqlite3.connect(resolve(twins.spec['source_database']).as_uri()+'?mode=ro&immutable=1',uri=True)
for i,raw,target in conn.execute('SELECT i,row,target FROM rows ORDER BY i'):
 process(json.loads(raw),json.loads(target),'store_v7',i)
 if (i+1)%50000==0:print('source rows',i+1,flush=True)
conn.close()
for i,row in enumerate(twins.rows()):process(row,{},'twins',i)
dest.commit();dest.close();track(dbpath)
# Hashes bind ordered source identities, not unknown final native offsets.
result=dict(status='SOURCE_FILTERS_REPLAYED_PRODUCTION_MISSING',scope='All supplied VQA source rows after listed metadata filters. Frame-host rebuild, frame admission and native post-filter offsets are MISSING.',source_counts=dict(source_counts),eligible_vqa=all_count,eligible_direction_rows=direction_count,
 stages={s:{k:dict(rows=counts[s][k],ordered_identity_sha256=hashes[s][k].hexdigest()) for k in sorted(counts[s])} for s in stages},
 refusals=[dict(stage_error=k,rows=v,first_qid=examples[k]) for k,v in sorted(refusals.items())],
 database=dict(path=str(dbpath),sha256=P.sha256(dbpath)),cells={k:len(v) for k,v in allgroups.items()},extent_required_rows=extent_rows,
 removal_files=cfg['remove_files'],card=cfg['r2_sampling']['card'],production_offset_status='MISSING',
 missing_training_host=[cfg['streams'][s] for s in ('pointing','pose','routing')])
write('out/SOURCE_RECONSTRUCTION.json',result)
write('work/source/source_indices.json',dict(scope='SOURCE_FILTER_REPLAY_OFFSETS_ONLY_NOT_PRODUCTION',cells=allgroups,database=result['database']))
(W/'STATUS.md').write_text(f'Available VQA source filtering is complete: {all_count} rows, including {direction_count} direction/facing rows. SOURCE_RECONSTRUCTION.json records per-stage counts and hashes. The production all-cell gate remains MISSING because native pointing, pose and routing populations and prepared offsets are absent. PATCH_PRIOR applies without fuzz to the exact reconstructed 189df6ac seal.\n')
print('eligible',all_count,'direction',direction_count,'cells',{k:len(v) for k,v in allgroups.items()},'refusals',sum(refusals.values()),flush=True)
