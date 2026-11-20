from common import *
from unittest.mock import patch
import shutil
sys.path.insert(0,str(kit('q')/'b'))
import pl,z,i
F=D/'planner';F.mkdir();k=F/'kit'
mutable={'p.json','c0.json','r.json','h.json','l.json','BUILD.json','SHA256SUMS.txt'}
def transport(a,b):
 if Path(a).name in mutable:return shutil.copyfile(a,b)
 os.link(a,b);return b
shutil.copytree(kit('q'),k,copy_function=transport)
node=F/'node';node.mkdir();u=F/'target/u';u.mkdir(parents=True)
def up(value):
 raw=value if isinstance(value,bytes) else (json.dumps(value)+'\n').encode()
 h=hashlib.sha256(raw).hexdigest();(u/h).write_bytes(raw);return dict(path='u/'+h,sha256=h)
index=up({});manifest=up(dict(index=dict(name='i.json',sha256=index['sha256']),files=[]))
rp=J.write(F/'receipt.json',dict(pins=dict(full_weights=manifest)))
raw=b'SQL fixture database';db=node/'s/aws/u/ap/8865619b/u/db';db.parent.mkdir(parents=True);db.write_bytes(raw);dh=J.sha(db)
catalog=node/'s/aws/u/ap/8865619b/u/catalog';catalog.write_bytes(b'catalog fixture');ch=J.sha(catalog)
stream=up(dict(database=dict(path='/unavailable/original/rows.sqlite',sha256=dh)))
selected=up(dict(regenerated_sha256='1'*64))
cap(k,'k/c0.json',{})
code=json.loads((k/'k/c0.json').read_text())['sha256']
spec=dict(namespace='/tmp/q',code_sha256=code,n_root=str(F/'target'),step=600,
 uploads=[dict(sha256=p.name,bytes=p.stat().st_size) for p in u.iterdir()])
cap(k,'k/p.json',spec);cap(k,'k/r.json',dict(routing_base=stream));cap(k,'k/h.json',dict(binaries=['bash'],routing_selection=selected))
cap(k,'k/l.json',dict(staged_inputs=dict(files=[dict(destination='u/db',sha256=dh,bytes=len(raw)),dict(destination='u/catalog',sha256=ch,bytes=catalog.stat().st_size)])))
cfg=dict(streams={'routing':stream},r1_training={'persisted_files':{}},s1_routing={'catalog':{ch:'/unavailable/original/catalog.json'}})
resolved=dict(archive=None,small_files={},receipt=dict(rp,bytes=Path(rp['path']).stat().st_size),config=cfg,paths={},request={},tar_sha256='0'*64,tar_bytes=0,parts=[])
resolved['kit_sha256']=reseal(k);records=[]
for mode in ('r','q'):
 root=node/mode;root.mkdir()
 with patch.dict(os.environ,Q_ROOT=str(node)),patch.object(i,'refresh',side_effect=lambda request,root:request):
  request,paths,stage=pl.plan_payload(k,resolved,root,regeneration=mode=='r')
 value=J.load(root/'plan.json');assert not any(n.startswith('f/') for n in value['entries'])
 assert paths[dh]==str(db) and paths[ch]==str(catalog)
 assert value['config']['s1_routing']['catalog'][ch]==str(root/'q/u'/ch)
 assert not (root/'q').exists()
 records.append(dict(mode=mode,authenticated_database=True,authenticated_catalog=True,no_literal_extra=True,fresh_q=True))
J.write(D/'PLANNER_TESTS.json',dict(status='PASS',records=records,boundary='Pool producer only; native planner, source hash checks, localization and temporary-path checks execute.'))
print('complete q/r planning: staged database and catalog; no literal extras PASS')
