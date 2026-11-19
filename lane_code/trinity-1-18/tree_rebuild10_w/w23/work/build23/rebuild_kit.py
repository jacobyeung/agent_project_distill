"""Regenerate the minimal kit from the authenticated build-21g upload inventory."""
from pathlib import Path
import base64,hashlib,json,shutil,sys
L=Path(__file__).resolve().parents[2];B=L/'work/build21';D=L/'work/build23';T=L/'work/tree_r1';K=B/'kits/q';A=L/'attic/build23'
sys.path[:0]=[str(T),str(B)]
import joblib as J
from student_pilot.p3_provenance import digest,file_pin,source_files
from student_pilot.source_seal import create,inventory,archive,check_archive
from launch_r2.build import capsule_json
def cap(name,value):(K/name).write_bytes(capsule_json(value))
old=J.load(A/'UPLOADS.json')
if not (A/'q').exists():shutil.copytree(K,A/'q')
uploads={}
for item in old['files']:
    if item['opaque_name'].startswith('u/'):
        p=B/'upload'/item['opaque_name']
        if not p.is_file():p=Path(item['local_path'])
        assert J.sha(p)==item['sha256']
        uploads[item['sha256']]={**item,'local_path':str(p)}
def upload(p):
    v=dict(local_path=str(p),opaque_name='u/'+J.sha(p),sha256=J.sha(p),bytes=p.stat().st_size)
    uploads[v['sha256']]=v;return file_pin(p)
cfg=J.load(A/'q/k/n.json');card=J.load(A/'mix.json')
for cell in card['cells']:
    if cell['stream']=='routing':cell.update(rows_per_step=0,ceiling_rows_per_step=0)
for name in ('coverage_distance','coverage_units','camera_wording'):
    if not any(c['type']==name for c in card['cells']):card['cells'].append(dict(type=name,stream='routing',rows_per_step=0,ceiling_rows_per_step=0))
card['cells'].append(dict(type='routing_base',stream='routing',rows_per_step=64))
J.write(B/'inputs/mix.json',card);mix=upload(B/'inputs/mix.json')
real=L.parent/'ext/m400real';run=J.load(real/'r.json')
runtime=J.load(real/('files'+run['config']['path']))
base=runtime['streams']['routing']
assert base['sha256']=='ca0616dbc67cf9a257774b43a9d5b134957b3f3ce0451e6bf5378f3d7d0c1984'
base_path=real/('files'+base['path']);assert J.sha(base_path)==base['sha256']
base_value=J.load(base_path)
assert base_value['database']['sha256']=='4e8e6c04e697d8f12ecd9d705e197e94f73f4a9dc508b7a9e9b4f36487336f84'
upload(base_path)
cfg['r1_training'].update(routing_slices='deferred_first_boundary',mix=mix)
cfg['r1_training'].pop('routing_inputs',None)
cfg['r1_training']['row_slice_inputs']={}
cfg['streams']['routing']=base;cfg['s1_routing']=runtime['s1_routing']
pending_population=B/'inputs/pending_population.json'
J.write(pending_population,dict(schema='r1-population-v1',complete=False,after_all_filters=False,
    card_sha256=mix['sha256'],counts={c['type']:0 for c in card['cells']},evidence=[mix,base]))
population=upload(pending_population)
pending_indices=B/'inputs/pending_indices.json'
J.write(pending_indices,dict(population_sha256=population['sha256'],cells={c['type']:[] for c in card['cells']}))
cfg['r2_sampling']=dict(schema='r1-sampling-v1',card=mix,population=population,indices=upload(pending_indices))
for name in ('config.json','kit_config.json'):J.write(B/'inputs'/name,cfg)
cap('k/n.json',cfg)
files=inventory(T);seal=digest(files)
control=J.load(K/'k/a.json');oldtar=K/control['source']['path']
saved=A/'q'/control['source']['path']
if oldtar.exists():oldtar.rename(A/('retained_'+oldtar.name))
target=K/'k'/('t_'+seal[:16]+'.tar')
if not target.exists():archive(T,target,files,compress=True)
check_archive(file_pin(target),files)
source=dict(path=str(target.relative_to(K)),sha256=J.sha(target),tree_sha256=seal)
closure={str(p.relative_to(T)):J.sha(p) for p in source_files([T/'student_pilot/carrier_c1_run.py'])}
code=dict(schema='c1-sealed-source-v1',commit='sha256:'+seal,tree_sha256=seal,files=files,archive={k:source[k] for k in ('path','sha256')},sources=closure,operation_sources=closure)
cap('k/7.json',code)
spec=J.load(K/'k/p.json');ns=spec['namespace']
qcode=create(T,target,closure,{},archive_path=ns+'/t.tar')
raw=(json.dumps(qcode,sort_keys=True,indent=2)+'\n').encode()
(K/'k/c0.json').write_text(json.dumps(dict(encoding='base64',payload=base64.b64encode(raw).decode(),sha256=hashlib.sha256(raw).hexdigest())))
spec['code_sha256']=hashlib.sha256(raw).hexdigest()
spec['uploads']=[{k:v for k,v in x.items() if k!='local_path'} for x in uploads.values()]
spec['pin_paths']={h:ns+'/u/'+h for h in uploads}
cap('k/p.json',spec)
control['source']=source;cap('k/a.json',control)
portable=J.load(K/'k/c.json');portable['r1_training'].update(routing_slices='deferred_first_boundary',row_slice_inputs={})
portable['r1_training'].pop('routing_inputs',None)
portable['r2_sampling']={k:(dict(v,path=spec['pin_paths'][v['sha256']]) if isinstance(v,dict) else v)
                         for k,v in cfg['r2_sampling'].items()}
portable['streams']['routing']=dict(base,path=ns+'/u/'+base['sha256'])
portable['r1_training']['mix']['sha256']=mix['sha256'];portable['code']=dict(path='k/7.json',sha256=J.sha(K/'k/7.json'))
cap('k/c.json',portable)
stage=J.load(K/'k/s.json');bound=portable['r1_training']['mix']['path'];raw=(B/'inputs/mix.json').read_bytes()
stage['entries']={bound:dict(payload=base64.b64encode(raw).decode(),sha256=hashlib.sha256(raw).hexdigest())}
cap('k/s.json',stage)
value=J.load(K/'k/8.json');value['report_sha256']=mix['sha256'];cap('k/8.json',value)
host=J.load(K/'k/h.json');host.pop('routing_inputs',None)
host['steps']=[s for s in host['steps'] if s!='r1_routing.compose_native'];cap('k/h.json',host)
request=J.load(K/'k/r.json');request.pop('routing_inputs',None);request['routing_base']=base;cap('k/r.json',request)
(K/'b/z.py').write_bytes((B/'joblib.py').read_bytes())
manifest={str(p.relative_to(K)):J.sha(p) for p in K.rglob('*') if p.is_file() and p.name not in ('SHA256SUMS.txt','BUILD.json')}
(K/'SHA256SUMS.txt').write_text(''.join(f'{h}  {n}\n' for n,h in sorted(manifest.items())))
record=J.load(K/'BUILD.json');record.update(GO=False,kit_sha256=J.seal(K),source_seal=seal)
cap('BUILD.json',record)
all_uploads=list(uploads.values())+[dict(local_path=str(p),opaque_name='q/'+str(p.relative_to(K)),bytes=p.stat().st_size,sha256=J.sha(p)) for p in K.rglob('*') if p.is_file()]
J.write(B/'UPLOADS.json',dict(files=all_uploads,total_bytes=sum(x['bytes'] for x in all_uploads)))
J.write(L/'out/TREE_SEAL.json',dict(tree_sha256=seal,files=len(files)))
(L/'out/TREE_FILES.sha256').write_text(''.join(f'{h}  {n}\n' for n,h in sorted(files.items())))
# Exact source-map exemptions remain pinned to the generated inventories.
p=B/'naming21.py';s=p.read_text();start=s.index('SOURCE_SEALS={');end=s.index('\nINPUT_IDENTITIES=',start)
pins={(doc,key):digest(J.load(K/doc)[key]) for doc in ('k/7.json','k/c0.json') for key in ('files','sources','operation_sources')}
s=s[:start]+'SOURCE_SEALS='+repr(pins)+'\n'+s[end:];p.write_text(s)
J.write(D/'KIT.json',dict(GO=False,tree_seal=seal,kit_seal=J.seal(K),routing_base=base,database=base_value['database'],types=base_value['types'],uploads=len(all_uploads),bytes=sum(x['bytes'] for x in all_uploads)))
print(json.dumps(J.load(D/'KIT.json'),indent=2))
