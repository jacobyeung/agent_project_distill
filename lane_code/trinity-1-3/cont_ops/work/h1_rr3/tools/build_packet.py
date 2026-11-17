import copy,hashlib,importlib.util,io,json,os,sys,tarfile
from pathlib import Path
H=Path(__file__).resolve().parents[1];D=Path('/scratch/jjyeung/orch_n30/review_h1pkt/work/d0');sys.path.insert(0,str(H/'tools'))
import derive_kit_h1 as dk
s=dk.sha
w=dk.write
T=H/'build/tree';T.mkdir(exist_ok=False)
# Preserve sealed executable modes; the supplied transport tar flattens its modes.
with tarfile.open(D/'kitfull/k/t_b01ce449beffe35b.tar') as tf:
 sealed_modes={m.name:m.mode for m in tf if m.isfile()}
# Read only the pinned archive.
with tarfile.open(H/'source/h1_1_code.tar') as tf:
 for m in tf:
  if m.isfile() and m.name.startswith('tree/'):
   n=m.name[5:];p=T/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(tf.extractfile(m).read());p.chmod(sealed_modes.get(n,0o644))
(T/'auth').mkdir();(T/'auth/R0_ROOMS.txt').write_bytes((H/'source/code/auth/R0_ROOMS.txt').read_bytes())
p=T/'student_pilot/h1_r0.py';txt=p.read_text();assert txt.count('parents[2]')==1
p.write_text(txt.replace('parents[2]','parents[1]'))
p=T/'student_pilot/carrier_c1_run.py';txt=p.read_text();assert txt.count('int(stop[0] or ')==2
p.write_text(txt.replace('int(stop[0] or ',"int(stop[0] or (output/('stop.'+os.environ.get('SLURM_JOB_ID','local')+'.request')).exists() or "))
files={str(p.relative_to(T)):s(p) for p in sorted(T.rglob('*')) if p.is_file()};tree=dk.digest(files);name='t_'+tree[:16]+'.tar'
# Exactly source_seal.archive's regular-file-only sorted PAX tar convention.
for dest in [H/'payload'/name,H/'evidence/rebuilt.tar']:
 with tarfile.open(dest,'x') as tf:
  for n in sorted(files):
   p=T/n;m=tarfile.TarInfo(n);m.size=p.stat().st_size;m.mode=0o755 if os.access(p,os.X_OK) else 0o644
   tf.addfile(m,io.BytesIO(p.read_bytes()))
assert s(H/'payload'/name)==s(H/'evidence/rebuilt.tar')
sys.path.insert(0,str(T))
from student_pilot.p3_provenance import source_files
sources={str(p.relative_to(T)):s(p) for p in source_files([T/'student_pilot/carrier_c1_run.py'])}
# The sealed pin used the same bounded closure for both fields.
basepin=json.loads((D/'kitfull/k/7.json').read_text());assert basepin['sources']==basepin['operation_sources']
code=dict(schema='c1-sealed-source-v1',commit='sha256:'+tree,tree_sha256=tree,files=files,sources=sources,operation_sources=sources,archive=dict(path=dk.KIT_LOGICAL+name,sha256=s(H/'payload'/name)))
w(H/'payload/7.json',code)
# Tokens are opaque, deterministic task identifiers; fresh targets must still be checked on Orchard.
tok={k:hashlib.sha256(('20261116-h1-1-'+k).encode()).hexdigest()[:8] for k in ['run','kit','root','store','job']}
w(H/'TOKENS_H1.json',tok)
IN='/project/community/jjyeung/okh7/i_'+tok['store']+'/'
over=json.loads((D/'a2/v5b/over_local.json').read_text())
over.update(run_key=tok['run'],kit_key=tok['kit'],persistent_run_root='/project/community/jjyeung/okh7/r/'+tok['root'])
over['config'].update(h1=dk.H1,milestones=[100,200],scheduled_sampling=dk.SAMPLING,recipe=dict(milestones=[100,200],scheduled_sampling=dk.SAMPLING))
# Copy only the listed small closure records into this packet; map those to opaque Orchard names.
paths={v['path'] for v in over['add_k'].values()} | set(over['content'].values()) | set(over['sealed_docs']) | {over['e00_listing']}
localmap={};remotemap={}
for path in sorted(paths):
 p=Path(path.replace('/scratch/jjyeung/orch_n30/cont_ops/work/d0',str(D)));p=p if p.is_absolute() else D/'a2'/p;n='d_'+s(p)[:16]+'.json';dest=H/'payload'/n
 dest.write_bytes(p.read_bytes());localmap[path]=str(dest);remotemap[str(dest)]=IN+n
for v in over['add_k'].values():v['path']=localmap[v['path']]
over['content']={h:localmap[p] for h,p in over['content'].items()};over['sealed_docs']=[localmap[p] for p in over['sealed_docs']];over['e00_listing']=localmap[over['e00_listing']]
# Only the small VQA receipt receives a new physical source. Shared row store and m544 archive stay read-only.
for e in over['deployment']['extra']:
 if e['parts']==['/project/community/jjyeung/okh7/i_bb09a77d/vb5.json']:
  e['parts']=[IN+'d_'+e['sha256'][:16]+'.json']
over['code_tree']=dict(archive=dict(path=str(H/'payload'/name),sha256=s(H/'payload'/name)),pin=dict(path=str(H/'payload/7.json'),sha256=s(H/'payload/7.json')))
remotemap[str(H/'payload'/name)]=IN+name;remotemap[str(H/'payload/7.json')]=IN+'7.json'
# Bind the seed authorization before deriving; source changes never inherit 4.json.
base_key=json.loads((D/'kitfull/k/1.json').read_text())['0']
seed_cfg=json.loads((D/'kitfull/k'/(base_key+'.json')).read_text())
for field in ('output','preparation_output'):seed_cfg[field]=seed_cfg[field].rsplit('/',1)[0]+'/'+tok['run']
for field,value in over['config'].items():
 if field in ('streams','s1_routing','init_artifact','scheduled_sampling'):seed_cfg[field].update(value)
 elif field=='recipe':
  seed_cfg[field]['milestones']=value['milestones'];seed_cfg[field]['scheduled_sampling'].update(value['scheduled_sampling'])
 else:seed_cfg[field]=copy.deepcopy(value)
seed_cfg['code']=dict(path=dk.KIT_LOGICAL+'7.json',sha256=s(H/'payload/7.json'))
auth=json.loads((D/'jobB/4b.json').read_text())
auth.update(config_sha256=dk.identity(seed_cfg),source_revision=code['commit'],wall_seconds=46800,production_go_granted=False)
auth['conditions']=[x.replace(' and canary-2 resume','') for x in auth['conditions']]
w(H/'payload/4.json',auth)
over['add_k']['4.json']=dict(path=str(H/'payload/4.json'),sha256=s(H/'payload/4.json'))
w(H/'build/over_seed.json',over)
w(H/'build/path_map.json',remotemap)
res=dk.derive(D/'kitfull',H/'build/fx_seed',dict(over,fixture=True));w(H/'evidence/fx_seed.json',res)
sys.path.insert(0,str(H/'build/fx_seed/b'))
from d import contract
cfg=json.loads((H/'build/fx_seed/k'/ (res['config_key']+'.json')).read_text());launch=json.loads((H/'build/fx_seed/k/launch.json').read_text())
ident=dk.identity(cfg);cont=dk.digest(contract(launch,cfg))
auth=json.loads((D/'jobB/4b.json').read_text());auth.update(config_sha256=ident,source_revision=code['commit'],wall_seconds=46800,production_go_granted=False)
auth['conditions']=[x.replace(' and canary-2 resume','') for x in auth['conditions']]
auth['scope']='Conditional binding; separate submission approval and new-source review are required.'
auth['admission_contract_sha256']=cont
w(H/'payload/4.json',auth)
review=dict(verdict='PENDING',reviewer=None,source_revision=code['commit'],config_sha256=ident,admission_contract_sha256=cont,admission_scope='pinned-template-and-native-data-derivation',attestation='Independent review of this code tree and runtime changes is required. CPU fixtures do not establish production admission.')
staging=dict(status='PENDING',source_revision=code['commit'],config_sha256=ident,missing=['orchard-inventory-verification'],project_community_write_bytes=0,scope='Read-only verification only; upload and derivation writes are outside this claim.')
w(H/'payload/review.json',review);w(H/'payload/staging.json',staging)
for n in ['4.json','review.json','staging.json']:
 over['add_k'][n]=dict(path=str(H/'payload'/n),sha256=s(H/'payload'/n));remotemap[str(H/'payload'/n)]=IN+n
w(H/'build/over_local.json',over);w(H/'build/over_fx.json',dict(over,fixture=True))
res=dk.derive(D/'kitfull',H/'build/fx',dict(over,fixture=True));w(H/'evidence/fx.json',res)
assert res['config_identity']==ident
remote=json.loads(json.dumps(over))
for v in remote['add_k'].values():v['path']=remotemap[v['path']]
remote['content']={h:remotemap[p] for h,p in remote['content'].items()};remote['sealed_docs']=[remotemap[p] for p in remote['sealed_docs']];remote['e00_listing']=remotemap[remote['e00_listing']]
for v in remote['code_tree'].values():v['path']=remotemap[v['path']]
remote['status']='BLOCKED';w(H/'payload/over.json',remote)
w(H/'build/path_map.json',remotemap)
ms=['m1','m50','m100','m200','m400','m600','m800','m1000','mstop','mstopB','mstopC']
(H/'EXPORT_OBJECTS.txt').write_text(''.join(f'q8/8865619b/{tok["run"]}_{m}.tar.part{i:02d}-of-04\n' for m in ms for i in range(4)))
w(H/'ids.json',dict(identity=ident,contract=cont,config_key=res['config_key'],code_pin=s(H/'payload/7.json'),tree=tree,trainer=dict(file=name,bytes=(H/'payload'/name).stat().st_size,sha256=s(H/'payload'/name)),tokens=tok,job_name='a15_cot_ap'+tok['job'],fixture_manifest=res['manifest_sha256']))
print((H/'ids.json').read_text())
