from pathlib import Path
import ast,hashlib,io,json,tarfile,shutil
W=Path(__file__).resolve().parent.parent;R=W/'out2';G=R/'gates';G.mkdir(exist_ok=True)
def put(p,b):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
def js(p,v):put(p,(json.dumps(v,indent=2,sort_keys=True)+'\n').encode())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def localize(s):
 s=s.replace('/scratch/jjyeung/orch_n30/reader_r1/work/fix7',str(R/'bases'))
 s=s.replace('/scratch/jjyeung/orch_n30/reader_r1/work/b1p/in/repin',str(G/'lost/repin'))
 s=s.replace('/scratch/jjyeung/orch_n30/reader_r1/work',str(G/'lost/reader'))
 return s
for k,label in [('b1','A'),('b2','B')]:
 base=R/'bases'/k;deliver=R/label;old=W/'out'/k
 for mode in ('base','release'):
  o=G/mode/k;o.mkdir(parents=True,exist_ok=True);source=base if mode=='base' else deliver
  for n in ('src',):
   if not (o/n).exists():(o/n).symlink_to(source/n,target_is_directory=True)
  for p in (source/'package').rglob('*'):
   if p.is_file():put(o/'package'/p.relative_to(source/'package'),p.read_bytes())
  for p in source.iterdir():
   if p.is_file() and p.suffix in ('.py','.json','.tgz'):put(o/p.name,p.read_bytes())
  for n in ('unpack_return.py','tower_pair.py','b1_report.py','gap.py','room_pair.py'):
   p=old/n
   if p.exists():put(o/n,p.read_bytes())
  for n in ('tests','work/tmp','checks','original'):(o/n).mkdir(parents=True,exist_ok=True)
  put(o/'TOKEN',(json.loads((source/'package/0.json').read_text())['token']+'\n').encode())
  put(o/'READ_PLAN.json',(old/('original/READ_PLAN.json' if mode=='base' else 'READ_PLAN.json')).read_bytes())
  if mode=='base':
   put(o/'original/0.tgz',(base/'0.tgz').read_bytes())
  else:
   put(o/'original/0.tgz',(base/'0.tgz').read_bytes())
   cfg=json.loads((deliver/'src/9.json').read_text());binding=cfg['export_binding'];inp=json.loads((base/'inputs_tower.json').read_text());pin=json.loads((base/'export_544.json').read_text())
   pin.update({n:binding[n] for n in ('run','step','member_directory','lineage','object','config_sha256')});pin['archive_sha256']=inp['archives'][0]['sha256']
   for n,h in binding['preparation_sha256'].items():pin['preparation'][n]['sha256']=h
   for n in ('artifact','heads','full_weights'):inp['files'][n]['path']=inp['files'][n]['path'].replace('/m544/','/m200/')
   js(o/'export_544.json',pin);js(o/'package/a/export.json',pin)
   inp['export_pin']=dict(path='a/export.json',bytes=(o/'package/a/export.json').stat().st_size,sha256=sha(o/'package/a/export.json'))
   js(o/'inputs_tower.json',inp);js(o/'package/a/1.json',inp)
  # Copy only test/helper source, preserving assertions. Release sources survive separately.
  for sub in ('tests','work'):
   paths={p.name:p for p in (old/sub).glob('*.py')}
   if mode=='release':paths.update({p.name:p for p in (W/'release'/k/sub).glob('*.py')})
   if sub=='work':paths.setdefault('test_memo.py',W/'out/b1/work/test_memo.py')
   for n,p in paths.items():put(o/sub/n,localize(p.read_text()).encode())
  for n in ('test_tower_pair.py','test_b1_report.py'):
   if (old/n).exists():put(o/n,localize((old/n).read_text()).encode())
  if mode=='base' and k=='b2':
   # Recovered release room fixtures select the baseline's null rule here.
   for n in ('test_room_pair.py','test_room_pair_labels.py'):
    s=(W/'release/b2/work'/n).read_text().replace("stage1_select_rule='candidates_argmax'","stage1_select_rule='null_argmax'").replace("('stage1_select_rule','null_argmax')","('stage1_select_rule','candidates_argmax')")
    put(o/'work'/n,s.encode())
  if mode=='release' and k=='b2':put(o/'room_pair.py',(W/'release/b2/room_pair.py').read_bytes())
  # Recover the production source and step-544 metadata from delivered T1/T2.
  p=o/'tests/test_package.py';s=p.read_text();s=s.replace("PROD=ROOT.parent/'b1g/out/src'","PROD=SRC")
  s=s.replace("PROD=Path("+repr(str(G/'lost/repin/out/production'))+")","PROD=SRC")
  s=s.replace("cls.old=read(Path("+repr(str(G/'lost/repin'))+")/'in/prod_pkg/a/1.json')","cls.old=read(OUT/'inputs_tower.json');cls.old.pop('export_pin',None)")
  put(p,s.encode())
 # Bases need plan and TOKEN for scoring metadata.
 put(base/'READ_PLAN.json',(old/'original/READ_PLAN.json').read_bytes())
 put(base/'TOKEN',(json.loads((base/'package/0.json').read_text())['token']+'\n').encode())
# Global suite entrypoints take a b1/b2 fixture directory argument.
for name in ('test_release_package.py','release_bundle.py','bundle_regression.py'):
 s=localize((W/name).read_text())
 if name=='test_release_package.py':
  s=s.replace("W=O.parents[1]", "W=Path("+repr(str(R))+')')
  s=s.replace("W/'out'/O.name", "W/('A' if O.name=='b1' else 'B')")
 put(G/name,s.encode())
# A guard's original/0.tgz was the predecessor with only its token changed;
# recover this fixture from the delivered base as documented by BUILD.json.
for k in ('b1','b2'):
 o=G/'base'/k
 with tarfile.open(o/'0.tgz') as t:files={m.name:t.extractfile(m).read() for m in t}
 cfg=json.loads(files['9.json']);cfg['token']='abcdef0123456';files['9.json']=json.dumps(cfg,sort_keys=True).encode()
 with tarfile.open(o/'original/0.tgz','w:gz') as t:
  for n,b in files.items():m=tarfile.TarInfo(n);m.size=len(b);t.addfile(m,io.BytesIO(b))
# Recover a legacy operator-at-6 collision fixture. The old transport bundle is lost;
# only the slot collision under test is reproduced, using delivered sequence bytes.
for k in ('b1','b2'):
 base=R/'bases'/k;boot=R/'bases'/('boot' if k=='b1' else 'boot2');boot.mkdir(exist_ok=True)
 for n,src in [('6.py','tower_sequence.py'),('0.py','tower_bootstrap.py')]:put(boot/n,(base/src).read_bytes())
 put(boot/'0.json',(base/'package/0.json').read_bytes())
 raw=io.BytesIO()
 with tarfile.open(fileobj=raw,mode='w:gz') as t:
  for p in sorted(boot.iterdir()):b=p.read_bytes();m=tarfile.TarInfo(p.name);m.size=len(b);t.addfile(m,io.BytesIO(b))
 p=G/'lost/reader'/('b1g' if k=='b1' else 'b2r')/'out/package/BATCH.sh'
 put(p,("b=bytes.fromhex("+repr(raw.getvalue().hex())+")\n").encode())
# Base guard looks for boot beneath its own fixture parent.
for n in ('boot','boot2'):
 if not (G/'base'/n).exists():(G/'base'/n).symlink_to(R/'bases'/n,target_is_directory=True)
print('gate fixtures prepared')
