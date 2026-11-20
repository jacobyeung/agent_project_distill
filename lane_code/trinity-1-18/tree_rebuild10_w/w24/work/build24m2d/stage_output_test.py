from common import *
from unittest.mock import patch
import shutil
sys.path.insert(0,str(kit(sys.argv[1] if len(sys.argv)>1 else 'q')/'b'))
import pl,z,i
name=sys.argv[1] if len(sys.argv)>1 else 'q'
F=D/'stage_output';F.mkdir();k=F/'kit'
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
resolved['kit_sha256']=reseal(k);records=[]

# Authenticate a complete, small reconstruction recipe. Only production pin
# constants are substituted in the fixture module; the planner/hook are native.
genraw=b'SQL reconstructed output fixture';genh=hashlib.sha256(genraw).hexdigest()
recipe=up(dict(inputs={'catalog':{ch:'/unavailable/catalog'}},legacy=stream,division=index,base_model=index))
base=up(dict(database={'path':'/unavailable/obsolete.sqlite','sha256':genh},materialization=recipe))
pconfig=up(dict(streams={'routing':base},remove_files=[],dev_scene_exclusions=index,benchmark_scene_exclusions=index))
cfg['streams']['routing']=base;cfg['r1_training']['p_run']={'config':pconfig}
spec['uploads']=[dict(sha256=p.name,bytes=p.stat().st_size) for p in u.iterdir()]
cap(k,'k/p.json',spec);cap(k,'k/r.json',{'routing_base':base})
resolved.update(config=cfg,kit_sha256=reseal(k))
import types
module=types.ModuleType('fixture_pl')
source=(kit(name)/'b/pl.py').read_text().replace('ca0616dbc67cf9a257774b43a9d5b134957b3f3ce0451e6bf5378f3d7d0c1984',base['sha256']).replace('4e8e6c04e697d8f12ecd9d705e197e94f73f4a9dc508b7a9e9b4f36487336f84',genh)
exec(compile(source,'fixture_pl','exec'),module.__dict__)
root=node/'r';root.mkdir()
with patch.dict(os.environ,Q_ROOT=str(node)),patch.object(i,'refresh',side_effect=lambda request,root:request):
 request,paths,stage=module.plan_payload(k,resolved,root,regeneration=True)
plan=J.load(root/'plan.json');assert genh not in paths and 'u/'+genh not in plan['entries']
assert plan['generated']=={genh:str(root/'q/base/rows.sqlite')}
import rb
from student_pilot.p3_provenance import pinned
from student_pilot.r1_persisted import scope
calls=[]
def generate(config,directory):
 assert J.sha(pinned(stream))==stream['sha256']
 assert J.sha(pinned({'path':'/no/host/fallback','sha256':dh}))==dh
 output=Path(directory)/'base/rows.sqlite';assert not output.exists()
 output.parent.mkdir();output.write_bytes(genraw);z.checked(output,genh);calls.append('reconstruct');return output
(root/'q').mkdir()
with scope(paths),patch.object(z,'copy_resolved_payload'),patch.object(rb,'reconstruct',generate):
 try:
  stage(plan['entries'],root/'q')
  assert pinned({'path':'/absent/original','sha256':genh}).read_bytes()==genraw
 finally:stage.close()
assert calls==['reconstruct']
J.write(D/'STAGE_OUTPUT_TESTS.json',dict(status='PASS',unavailable_output_omitted_from_staging=True,all_inputs_authenticated=True,generated_pin_resolves_after_hook=True,scope_closed=True,boundaries=['Production receipt/database constants replaced by fixture hashes','Export-payload copier boundary','Native reconstruction tested independently; hook producer boundary writes a checked fixture output']))
print('complete mode-r planning and staged reconstruction scope PASS')
