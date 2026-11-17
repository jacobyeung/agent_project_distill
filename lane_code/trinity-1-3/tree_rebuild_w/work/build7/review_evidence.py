"""Read frozen source and staged kits; produce review inventories only."""
import collections,hashlib,json,re,sys
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build7';T=L/'work/tree_r1'
sys.path.insert(0,str(T))
from student_pilot.p3_provenance import load
from launch_r2.build import verify,scan
from student_pilot.response_spec import sha256
from student_pilot.r2_portable import bound
P=B/'proofs/review';P.mkdir(parents=True,exist_ok=True)
results=[]
for arm in ('a2','a0'):
 root=B/'kits'/arm;launch=load(root/'k/launch.json');cfg=load(root/launch['config']['file'])
 assert launch['production_authorized'] is False
 assert cfg['b7_inputs']['init'] is None
 assert cfg['b7_inputs']['response_spec']['sha256']==sha256()
 assert cfg['routing_policy']=='both-path-20261116'
 inputs=cfg['b7_inputs']
 zero=load(root/'k/0.json');plan=load(bound(zero['staging'],root))
 old_sources=[]
 def visit(v,where=''):
  if isinstance(v,dict):
   for k,x in v.items():visit(x,where+'/'+str(k))
  elif isinstance(v,list):
   for i,x in enumerate(v):visit(x,where+'/'+str(i))
  elif isinstance(v,str) and 'okit/in/e00' in v:
   key=where.removeprefix('/entries/').split('/archive/',1)[0]
   entry=plan['entries'].get(key,{})
   old_sources.append(dict(field=where,value=v,member=entry.get('member'),sha256=entry.get('sha256'),
      qualification='The supplied kit audit explicitly verifies the bank and training-scene members in this archive.'))
 visit(plan)
 results.append(dict(arm=arm,kit_sha256=verify(root),scan=scan(root),launch=launch,
  layout={k:inputs[k] for k in ('max_pixels','min_pixels','frame_count','frame_layout','frame_markers')},
  trainable_modules=inputs['trainable_modules'],weight_scale=inputs['weight_scale'],
  staging_entries=len(plan['entries']),retained_e00_references=old_sources,
  claim_reader=cfg['claim_reader'],read_order=cfg['read_order'],routing_policy=cfg['routing_policy'],
  blockers=cfg['b7_blockers'],empty_lists=[dict(index=i,**p) for i,p in enumerate(cfg['remove_files']) if p['sha256']==hashlib.sha256(b'').hexdigest()]))
(P/'KIT_READCHECK.json').write_text(json.dumps(results,indent=2)+'\n')
records=[]
for line in (L/'out/RECORDS_TO_REGENERATE.md').read_text().splitlines():
 if not line.startswith('| EVIDENCE_'):continue
 name=line.split('|')[1].strip()
 direct=name in ('EVIDENCE_init_m544.json','EVIDENCE_heads_pose.json','EVIDENCE_heads_depth.json','EVIDENCE_heads_frame_embeddings.json')
 conditional=name in ('EVIDENCE_depth_init_vc.json','EVIDENCE_heads_gf1_connector.json')
 records.append(dict(record=name,init_dependency='direct' if direct else 'conditional' if conditional else 'no automatic dependency; independently requalify its own inputs',
  reason=('Binds the selected export or a head loaded from it; filename is historical, not a selection.' if direct else
   'Rebind if this component is inherited from the selected export; external fixed initialization remains separately pinned.' if conditional else
   'Selection alone does not change this record, but its source/model pins still require verification.')))
(P/'INIT_DEPENDENCIES.json').write_text(json.dumps(dict(source='out/RECORDS_TO_REGENERATE.md',records=records),indent=2)+'\n')
lines=[]
for name in ('launch_s1/b/r.sh','launch_s1/b/w.py','student_pilot/stop_control.py','student_pilot/carrier_c1_run.py','launch_r2/staging.py'):
 for number,line in enumerate((T/name).read_text().splitlines(),1):
  if any(s in line for s in ('K3','R1_STOP_FILE','stop_file','requested(','stop_after_step','export_at_stop')):
   lines.append(dict(file=name,line=number,text=line.strip()))
(P/'STOP_PATH.json').write_text(json.dumps(lines,indent=2)+'\n')
patterns=[]
for name in ('student_pilot/geometry_profiles.py','student_pilot/carrier_c1_routing.py','trace_format/box_v313.py','student_pilot/tower_scale.py','student_pilot/tower_scale_rule.py','student_pilot/carrier_c1_decode.py','student_pilot/carrier_c1_batch_decode.py'):
 for n,line in enumerate((T/name).read_text().splitlines(),1):
  if re.search(r'heading unavailable|not seen|box unavailable|gravity|percentile|degrees\(|error:|tau|tower_scale|tool_response',line):
   patterns.append(dict(file=name,line=n,text=line.strip()))
(P/'RESPONSE_RULE_SOURCES.json').write_text(json.dumps(patterns,indent=2)+'\n')
print(json.dumps(dict(kits=len(results),init_records=len(records),rule_locations=len(patterns))))
