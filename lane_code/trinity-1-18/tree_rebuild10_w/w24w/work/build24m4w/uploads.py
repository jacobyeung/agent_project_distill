from pathlib import Path
import sys,json,shutil
L=Path(__file__).resolve().parents[2];D=L/'work/build24m4w';sys.path.insert(0,str(D))
from seal import *
from launch_r1.build import verify
base=z.load(L/'work/build24m4s/BASELINE.json');t=z.load(L/'out/UPLOADS_24M4T.json')
assert t['baseline_kit_seals']=={n:base['kits'][n] for n in ('q','n','qd')}
assert t['baseline_rcj']==base['rcj']
seals={n:verify(kit(n)) for n in NAMES}
def files(k):return {str(p.relative_to(k)):dict(sha256=z.sha(p),bytes=p.stat().st_size,mode=p.stat().st_mode&511) for p in k.rglob('*') if p.is_file()}
current={n:files(kit(n)) for n in NAMES};rows=[];optional=[]
def entry(name,p,old=None):
 return dict(name=name,relative_path=str(p.relative_to(L)),local_path=str(p),
  action='replace' if old else 'add',baseline_sha256=old,sha256=z.sha(p),bytes=p.stat().st_size,
  mode=format(p.stat().st_mode&511,'04o'),transfer='local-upload')
for n in NAMES:
 assert current[n].keys()==base['files'][n].keys()
 for rel,v in sorted(current[n].items()):
  if v!=base['files'][n][rel]:
   (optional if n=='n_go' else rows).append(entry(n+'/'+rel,kit(n)/rel,base['files'][n][rel]['sha256']))
for name,h in base['rcj'].items():
 p=L/'out/rcj'/name
 if z.sha(p)!=h:rows.append(entry('rcj/'+name,p,h))
for p in (D/'u').iterdir():rows.append(entry('u/'+p.name,p))
rows.sort(key=lambda v:v['name']);optional.sort(key=lambda v:v['name'])
assert [v['name'] for v in rows if v['name'].startswith('rcj/')]==['rcj/ch.py','rcj/x.py']
assert len([v for v in rows if v['name'].startswith('u/')])==1
up=dict(schema='cpu-publication-delta-v1',build='24m4v',baseline='Reviewed Orchard overlay',
 baseline_kit_seals=t['baseline_kit_seals'],baseline_rcj=t['baseline_rcj'],
 tree_sha256=z.load(D/'SEALS.json')['tree'],kit_seals={n:seals[n] for n in ('q','n','qd')},
 files=rows,total_files=len(rows),total_bytes=sum(v['bytes'] for v in rows),GO=False,uploaded=False,launched=False,
 over_5MB=[dict(name=v['name'],bytes=v['bytes']) for v in rows if v['bytes']>5000000],
 config_delta='r1_training.extent_pool_sources plus source/config seals; c072905b unchanged',
 u_composition='Run apply_24m4v.py on the 24m4u workspace; it preserves that workspace\'s x/nd/ps/pc helpers. This upload list describes the standalone 24m4v bytes.')
write(L/'out/UPLOADS_24M4V.json',up);(L/'out/UPLOADS_24M4V.list').write_text(''.join(v['name']+'\n' for v in rows))
write(L/'out/UPLOADS_24M4V_GO.json',dict(schema='optional-kit-overlay-v1',build='24m4v',baseline_kit_seal=base['kits']['n_go'],kit_seal=seals['n_go'],files=optional,total_files=len(optional),total_bytes=sum(v['bytes'] for v in optional),applied=False,uploaded=False,launched=False))
(L/'out/UPLOADS_24M4V_GO.list').write_text(''.join(v['name']+'\n' for v in optional))
replay=D/'upload_replay';replay.mkdir()
def copy(p,q):q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q);q.chmod(p.stat().st_mode&511)
for n in NAMES:
 for rel,v in base['files'][n].items():
  current_file=kit(n)/rel
  candidates=[current_file]+[L/'attic'/b/current_file.relative_to(L) for b in ('build24m4w','build24m4t','build24m4s')]
  p=next((a for a in candidates if a.is_file() and z.sha(a)==v['sha256']),None)
  assert p is not None,(n,rel,v)
  copy(p,replay/n/rel);assert (replay/n/rel).stat().st_mode&511==v['mode']
 assert verify(replay/n)==base['kits'][n]
for name,h in base['rcj'].items():
 p=L/'out/rcj'/name
 candidates=[p]+[L/'attic'/b/'out/rcj'/name for b in ('build24m4w','build24m4t')]
 p=next(a for a in candidates if a.is_file() and z.sha(a)==h);copy(p,replay/'rcj'/name)
for item in rows+optional:
 q=replay/item['name']
 if q.exists():
  a=L/'attic/build24m4w/upload_replay'/item['name'];a.parent.mkdir(parents=True,exist_ok=True);q.rename(a)
 copy(L/item['relative_path'],q)
for n in NAMES:assert verify(replay/n)==seals[n] and files(replay/n)==current[n]
assert files(replay/'rcj')==files(L/'out/rcj')
for v in rows:assert z.sha(replay/v['name'])==v['sha256']
write(D/'DELTA_REPLAY.json',dict(status='PASS',ordinary_files=len(rows),optional_files=len(optional),exact_bytes_modes=True,baseline_kit_seals=t['baseline_kit_seals'],kits=seals,over_5MB=up['over_5MB']))
print(json.dumps(dict(status='PASS',files=len(rows),bytes=up['total_bytes'],optional=len(optional),over_5MB=up['over_5MB']),indent=2))
