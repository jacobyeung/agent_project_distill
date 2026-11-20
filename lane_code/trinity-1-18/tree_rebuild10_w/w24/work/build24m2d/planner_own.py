from common import *
from unittest.mock import patch
import shutil
sys.path.insert(0,str(kit(sys.argv[1] if len(sys.argv)>1 else 'q')/'b'))
import pl,z,i
name=sys.argv[1] if len(sys.argv)>1 else 'q'
F=D/('planner_own_'+name);F.mkdir();k=F/'kit'
mutable={'p.json','c0.json','r.json','h.json','l.json','BUILD.json','SHA256SUMS.txt'}
def transport(a,b):
 if Path(a).name in mutable:return shutil.copyfile(a,b)
 os.link(a,b);return b
shutil.copytree(kit(name),k,copy_function=transport)
node=F/'node';node.mkdir();u=F/'target/u';u.mkdir(parents=True)
def up(value):
 raw=value if isinstance(value,bytes) else (json.dumps(value)+'\n').encode()
 h=hashlib.sha256(raw).hexdigest();(u/h).write_bytes(raw);return dict(path='u/'+h,sha256=h)
index=up({});manifest=up(dict(index=dict(name='i.json',sha256=index['sha256']),files=[]))
rp=J.write(F/'receipt.json',dict(pins=dict(full_weights=manifest)))
raw=b'SQL fixture database';db=node/'s/aws/u/ap/8865619b/u/db';db.parent.mkdir(parents=True);db.write_bytes(raw);dh=J.sha(db)
catalog=node/'s/aws/u/ap/8865619b/u/catalog';catalog.write_bytes(b'catalog fixture');ch=J.sha(catalog)
stream=up(dict(database=dict(path='/unavailable/original/rows.sqlite',sha256=dh)))
original=up(dict(database=dict(path='/absent/original',sha256='f'*64)))
selected=up(dict(regenerated_sha256='1'*64,inputs_pinned=dict(routing_base=stream,routing_database=dict(path='/not/a/source',sha256=dh))))
(node/'routing_selection.json').write_bytes((u/selected['sha256']).read_bytes())
cap(k,'k/c0.json',{})
code=json.loads((k/'k/c0.json').read_text())['sha256']
spec=dict(namespace='/tmp/q',code_sha256=code,n_root=str(F/'target'),step=600,
 uploads=[dict(sha256=p.name,bytes=p.stat().st_size) for p in u.iterdir()])
cap(k,'k/p.json',spec);cap(k,'k/r.json',dict(routing_base=original));cap(k,'k/h.json',dict(binaries=['bash'],routing_selection=selected))
cap(k,'k/l.json',dict(staged_inputs=dict(files=[dict(destination='u/db',sha256=dh,bytes=len(raw)),dict(destination='u/catalog',sha256=ch,bytes=catalog.stat().st_size)])))
cfg=dict(streams={'routing':original},r1_training={'persisted_files':{}},s1_routing={'catalog':{ch:'/unavailable/original/catalog.json'}})
resolved=dict(archive=None,small_files={},receipt=dict(rp,bytes=Path(rp['path']).stat().st_size),config=cfg,paths={},request={},tar_sha256='0'*64,tar_bytes=0,parts=[])
own=node/'dr/p/q/base/rows.sqlite';own.parent.mkdir(parents=True);own.write_bytes(raw)
cap(k,'k/l.json',dict(staged_inputs=dict(files=[dict(destination='u/catalog',sha256=ch,bytes=catalog.stat().st_size)])))
resolved['kit_sha256']=reseal(k);records=[]
for mode in ('q',):
 root=node/mode;root.mkdir()
 with patch.dict(os.environ,Q_ROOT=str(node)),patch.object(i,'refresh',side_effect=lambda request,root:request):
  request,paths,stage=pl.plan_payload(k,resolved,root,regeneration=mode=='r')
 value=J.load(root/'plan.json');assert not any(n.startswith('f/') for n in value['entries'])
 assert paths[dh]==str(own) and paths[ch]==str(catalog)
 assert value['config']['s1_routing']['catalog'][ch]==str(root/'q/u'/ch)
 assert not (root/'q').exists()
 from launch_r1.entry import stage_host
 from student_pilot import r1_coverage
 from student_pilot.r1_persisted import scope
 # Run the native substitution and host recording; copying is a separate tested hook.
 host={}
 with scope(paths),patch.object(r1_coverage,'routing_request',return_value=True):
  effective=stage_host(value['config'],root/'q',request,root/'q',stage=lambda entries,directory:None,result=host)
 assert effective['streams']['routing']['sha256']==stream['sha256']
 assert host['routing_substituted'] and host['routing_substitution']['routing']['original_sha256']==original['sha256']
 assert host['routing_substitution']['routing']['substituted_sha256']==stream['sha256']
 J.write(root/'host.json',host)
 records.append(dict(mode=mode,authenticated_database=True,authenticated_catalog=True,no_literal_extra=True,fresh_q=True,native_host_records_substitution=True))
J.write(D/'QD_OWN_SELECTION_TESTS.json',dict(status='PASS',records=records,boundary='Pool producer only; native planner, source hash checks, localization and temporary-path checks execute.'))
print('complete q/r planning: staged database and catalog; no literal extras PASS')
