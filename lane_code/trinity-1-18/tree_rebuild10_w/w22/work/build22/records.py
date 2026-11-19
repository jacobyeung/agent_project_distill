from pathlib import Path
import sys,json,datetime
L=Path(__file__).resolve().parents[2];D=L/'work/build22';I=D/'inputs'
sys.path[:0]=[str(L/'work/tree_r1'),str(L/'work/build21')]
import joblib as J
from student_pilot.p3_provenance import file_pin,load,pinned
from student_pilot.s1_exclusions import Exclusions
print(datetime.datetime.now(datetime.timezone.utc).isoformat())
events=Path('/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/tree_rebuild')
optional=[]
for name in ('RESULT','RESULT.json','RESULT.md'):
 p=events/name
 try:
  with p.open() as f:raw=f.read(100000)
 except FileNotFoundError:optional.append(dict(path=str(p),exists=False))
 else:optional.append(dict(path=str(p),exists=True,sha256=J.sha(p),text=raw))
J.write(D/'OPTIONAL.json',dict(timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),checks=optional,
 status='first boundary',reason='No reviewed hand-over RESULT with an exact input path and SHA-256 was available through the named RESULT paths; directory listing/search is prohibited.',
 slices=['hard-direction answer-prior weights','relative-count procedure family']))
cfg=load(I/'config.json');v=cfg['r1_training']
v['not_present_slots']=['heads_gf1_connector','heads_frame_embeddings']
source=Path('/scratch/jjyeung/orch_n30/sb_pfrev/RECORD_TEXT.md')
assert J.sha(source)=='e1429ccd67d72e195b9e8b55c7fd5a393ff8585e0a7c1b8ff849db379738b708'
p=I/'pose_record.md';p.write_bytes(source.read_bytes())
record=load(pinned(v['component_rows']));record['inputs'].append(file_pin(p))
record['proven']['pose_family_record']=dict(text=p.read_text(),source=file_pin(p),pose_receipt=cfg['streams']['pose'])
evidence=load('/scratch/jjyeung/orch_n30/sb_pfrev/notes/pfrev_out.json')
print('pose evidence keys',list(evidence))
rule=Exclusions(cfg['dev_scene_exclusions'],cfg['benchmark_scene_exclusions'])
targets=next(x for x in evidence.values() if isinstance(x,list) and len(x)==23 and isinstance(x[0],dict) and 'raw_index' in x[0])
checks=[]
for r in targets:
 ds,scene=r['token'].split('/',1);assert rule.excluded(dict(qid=r['qid'],dataset=ds,scene=scene))
 checks.append(dict(qid=r['qid'],raw_index=r['raw_index'],source=r['source'],token=r['token'],excluded=True))
record['proven']['pose_family_record']['native_exclusion_check']=dict(rows=23,excluded=23,source=file_pin('/scratch/jjyeung/orch_n30/sb_pfrev/notes/pfrev_out.json'))
record['unproven']['N_pose_admitted_indices']='First boundary: N has not prepared; exact admitted indices and raw pose databases are absent on Trinity.'
v['component_rows']=J.write(I/'component_rows.json',record)
J.write(I/'config.json',cfg)
J.write(D/'POSE.json',dict(record=file_pin(p),checks=checks,exact_N_admitted_indices='MISSING',
 conclusion='All 23 reviewed source qids hit N\'s native BENCH exclusion. This is not an exact admitted-index proof.',GO=False))
