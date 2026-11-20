from common import *
import copy, shutil
from student_pilot.source_seal import inventory,archive,check_archive
from student_pilot.p3_provenance import digest,source_files
from student_pilot.carrier_c1_run import identity
files=inventory(T);seal=digest(files)
assert seal==J.load(D/'TREE_CPRIME.json')['after']
arc=D/'t.tar';archive(T,arc,files,compress=True)
check_archive(dict(path=str(arc),sha256=J.sha(arc)),files)
sources={str(p.relative_to(T)):J.sha(p) for p in source_files([T/'student_pilot/carrier_c1_run.py'])}
pins={};seals={}
for name in NAMES:
 k=kit(name);old={r:J.load(k/r) for r in ('k/7.json','k/c0.json','k/c.json','k/n.json','k/a.json','k/p.json','BUILD.json')}
 source=old['k/a.json']['source'];replace(k/source['path'],arc.read_bytes())
 for rel in ('k/7.json','k/c0.json'):
  v=copy.deepcopy(old[rel]);v.update(files=files,sources=sources,commit='sha256:'+seal,tree_sha256=seal)
  v['operation_sources']=sources if old[rel]['operation_sources'] else {}
  v['archive']['sha256']=J.sha(arc);cap(k/rel,v)
 oldcode=old['k/p.json']['code_sha256'];newcode=J.load_raw(k/'k/c0.json')['sha256']
 spec=copy.deepcopy(old['k/p.json']);spec['code_sha256']=newcode;cap(k/'k/p.json',spec)
 for rel in ('k/c.json','k/n.json'):
  cfg=copy.deepcopy(old[rel])
  if rel=='k/c.json':cfg['code']['sha256']=J.sha(k/'k/7.json')
  else:cfg['code']=dict(path='u/'+newcode,sha256=newcode)
  if name=='qd':cfg['r1_training']['init_policy']='step400_export_weights_fresh_v1'
  assert cfg.get('min_pixels') is None and cfg.get('max_pixels') is None and cfg['frame_count']==32
  cap(k/rel,cfg)
 v=copy.deepcopy(old['k/a.json']);v['source'].update(sha256=J.sha(arc),tree_sha256=seal);assert v['GO']==(name=='n_go');cap(k/'k/a.json',v)
 v=copy.deepcopy(old['BUILD.json']);v['source_seal']=seal;v['config_sha256']=J.sha(k/'k/c.json');cap(k/'BUILD.json',v)
 seals[name]=reseal(k)
 pins[name]=dict(archive=dict(before=source,after=J.load(k/'k/a.json')['source']),
  code_file=dict(before=old['k/c.json']['code'],after=J.load(k/'k/c.json')['code']),
  runtime_code=dict(before=oldcode,after=newcode),
  configs={rel:dict(before_identity=identity(old[rel]),identity=identity(J.load(k/rel)),payload_sha256=J.load_raw(k/rel)['sha256'],file_sha256=J.sha(k/rel)) for rel in ('k/c.json','k/n.json')},
  source_maps={rel:{field:digest(J.load(k/rel)[field]) for field in ('files','sources','operation_sources')} for rel in ('k/7.json','k/c0.json')},
  changed_files={str(p.relative_to(k)):J.sha(p) for p in k.rglob('*') if p.is_file() and J.load(D/'BASE_FILES.json')[name].get(str(p.relative_to(k)),{}).get('sha256')!=J.sha(p)})
J.write(D/'DEPENDENT_PINS.json',pins);J.write(D/'SEALS.json',seals)
print('SEALED',seals,flush=True)
