from pathlib import Path
import json,hashlib,shutil,tarfile,sys,subprocess,ast,base64
J=Path.cwd();D=J/'work/build24m4z5';E=J/'out/e3'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for n in ('b/pc.py','b/pc.sh','b/o.py','k/y.json'):shutil.copy2(J/'out/kit_n'/n,J/'out/kit_n_go'/n)
rows=[]
for root in ('out/kit_n','out/kit_n_go'):
 k=J/root
 manifest=''.join(sha(p)+'  '+str(p.relative_to(k))+'\n' for p in sorted(k.rglob('*')) if p.is_file() and p.name not in ('BUILD.json','SHA256SUMS.txt'))
 (k/'SHA256SUMS.txt').write_text(manifest)
 v=json.loads(base64.b64decode(json.loads((k/'BUILD.json').read_text())['payload']));old=v['kit_sha256'];v['kit_sha256']=sha(k/'SHA256SUMS.txt')
 raw=(json.dumps(v,sort_keys=True,indent=2)+'\n').encode()
 (k/'BUILD.json').write_text(json.dumps(dict(encoding='base64-json',payload=base64.b64encode(raw).decode(),sha256=hashlib.sha256(raw).hexdigest()),sort_keys=True)+'\n')
 r=subprocess.run([sys.executable,'-I','-s','-B',str(k/'b/v.py'),str(k)],capture_output=True,text=True)
 assert r.returncode==0,(r.stdout,r.stderr);assert r.stdout.strip()==v['kit_sha256']
 for p in (k/'b').glob('*.py'):ast.parse(p.read_text(),str(p))
 rows.append(dict(kit=root,old=old,new=v['kit_sha256'],GO=v['GO'],checker=r.stdout.strip()))
 if (J/'work/enospc5/kit').exists():
  for n in ('b/pc.py','b/pc.sh','b/o.py','k/y.json','BUILD.json','SHA256SUMS.txt'):shutil.copy2(J/'out/kit_n'/n,J/'work/enospc5/kit'/n)
for n in ('b/pc.py','b/pc.sh','b/o.py','k/y.json','BUILD.json','SHA256SUMS.txt'):
 shutil.copy2(J/'out/kit_n'/n,J/'work/build24/kits/n'/n)
with tarfile.open(E/'k.tgz','w:gz') as t:
 for p in sorted((J/'out/kit_n').rglob('*')):
  if p.is_file():t.add(p,arcname=str(p.relative_to(J/'out/kit_n')),recursive=False)
assert (E/'k.tgz').stat().st_size<5_000_000
(E/'pins.json').write_text(json.dumps({n:sha(E/n) for n in ('e3.py','observe.py','run.sh','k.tgz')},indent=2)+'\n')
for p in E.glob('*.py'):ast.parse(p.read_text(),str(p))
for p in (E/'e3.sh',E/'run.sh',J/'out/jn3.sh',J/'out/kit_n/b/pc.sh'):subprocess.run(['bash','-n',str(p)],check=True)
(D/'FINAL_SEALS.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows))
