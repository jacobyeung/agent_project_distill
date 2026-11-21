import ast,base64,hashlib,json,os,sys
from pathlib import Path
L=Path.cwd();D=L/'work/build24m4z8b';K=L/'out/kit_qdp'
sys.path[:0]=[str(K/'b'),str(L/'work/tree_r1c')];import z
S=Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/work/d173912/173912')
record=json.loads((D/'PIN.json').read_bytes());seal=record['output']['seal'];spec=z.load(K/'k/p.json')
u={s.split()[1]:int(s.split()[0]) for s in (L/'inputs/u_list.txt').read_text().splitlines() if s.strip()}
h=record['selection']['sha256'];sel=S/'routing_selection.json';dest=L/'out/u'/h;dest.parent.mkdir(exist_ok=True)
if not dest.exists():dest.write_bytes(sel.read_bytes())
assert z.sha(dest)==h
rows=[]
def add(p,n):
 rows.append(dict(name=n,local_path=str(p),relative_path=str(p.relative_to(L)),bytes=p.stat().st_size,sha256=z.sha(p),mode=format(p.stat().st_mode&511,'04o'),action='add'))
for p in sorted(K.rglob('*')):
 if p.is_file():add(p,'qp_'+seal[:8]+'/'+str(p.relative_to(K)))
add(dest,'u/'+h)
for name in ('jd7.sh','j7.py','pp/pp.sh'):add(L/'out'/name,name)
assert all(r['bytes']<5_000_000 for r in rows)
files=[]
for r in spec['uploads']:
 state='upload' if r['sha256']==h else 'present'
 if state=='present':assert u[r['sha256']]==r['bytes']
 files.append(dict(name='u/'+r['sha256'],sha256=r['sha256'],bytes=r['bytes'],state=state,readers=['b/pl.py:24','b/pl.py:67','b/z.py:473'] if r['sha256']==h else ['b/pl.py:67','b/z.py:473']))
resolved=json.loads((S/'k_r.json').read_bytes())['_resolved']
reads=dict(seal=seal,uploads=files,already_present=len(files)-1,new_files=1,
 small_files=[dict(sha256=h,bytes=r['bytes'],member=r['member'],source='existing handover archive',reader='b/pl.py:51-63') for h,r in resolved['small_files'].items()],
 archive=resolved['archive'],receipt=resolved['receipt'],external_metadata=resolved['external_metadata'],
 regenerated=[dict(sha256=record['selection']['base_sha256'],bytes=837255168,path='dr/p/q/base/rows.sqlite',reader='b/pl.py:135-138',why='mode r reconstructs before mode q; not in pool u'),
 dict(sha256=record['selection']['selection_receipt_sha256'],path='p/q/sc/p/p/receipt.json',reader='b/pl.py:244; launch_r1/entry.py:280',why='current scene and selection recipe generates locally'),
 dict(sha256=record['selection']['database_sha256'],bytes=849543168,pool_present=u[record['selection']['database_sha256']]==849543168,path='p/q/selection/rows.sqlite',reader='launch_r1/entry.py:280',why='native build regenerates; selection compact digest authenticates output')],
 scope='Inventory sizes are checked against the supplied Orchard listing; remote bytes are checked only at runtime. Source receipt paths in the selection are historical provenance, not new upload requirements.')
(D/'READ_CLOSURE.json').write_text(json.dumps(reads,indent=2)+'\n')
# Every static file-reading site in the entry and selection-dependent call chain.
sites=[]
for rel in ['b/z.py','b/a.py','b/pl.py','b/px.py','b/i.py','b/sc.py','b/rb.py','b/rg.py','b/f0.py','b/rv.py','b/h.py','b/cs.py']:
 p=K/rel
 for n in ast.walk(ast.parse(p.read_text())):
  if isinstance(n,ast.Call) and (isinstance(n.func,ast.Name) and n.func.id in ('load','checked','pinned','metadata_at') or isinstance(n.func,ast.Attribute) and n.func.attr in ('read_text','read_bytes','open','extractfile')):
   sites.append(dict(file='out/kit_qdp/'+rel,line=n.lineno,expression=ast.unparse(n),source='kit control, existing pool, or generated job-local input; concrete pool objects in READ_CLOSURE.json'))
for rel in ('launch_r1/entry.py','launch_r1/production_proof.py','student_pilot/r1_population.py','student_pilot/r1_loader.py'):
 p=L/'work/tree_r1c'/rel
 for n in ast.walk(ast.parse(p.read_text())):
  if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id in ('load','pinned','prepared'):
   sites.append(dict(file='work/tree_r1c/'+rel,line=n.lineno,expression=ast.unparse(n),source='authenticated staged inputs or generated node-local receipts; no additional selection upload'))
(D/'READ_SITES.json').write_text(json.dumps(sites,indent=2)+'\n')
v=dict(schema='discovery-uploads-v1',build='24m4z8b',GO=False,launch_authorized=False,kit_dir='qp_'+seal[:8],kit_seal=seal,
 source_kit_seal=record['source']['seal'],files=rows,total_files=len(rows),total_bytes=sum(r['bytes'] for r in rows),over_5MB=[],
 already_staged=files[:-1] if False else [r for r in files if r['state']=='present'],selection=record['selection'],authorization=record['authorization'],
 local_only=['out/pin_discovery.py'],untouched=['q','n','n_go','qd','rcj'],uploaded=False,launched=False)
(L/'out/UPLOADS_24M4Z8B.json').write_text(json.dumps(v,indent=2)+'\n');(L/'out/UPLOADS_24M4Z8B.list').write_text(''.join(r['name']+'\n' for r in rows))
print(json.dumps(dict(files=len(rows),bytes=v['total_bytes'],kit_dir=v['kit_dir'],present=len(files)-1)))
