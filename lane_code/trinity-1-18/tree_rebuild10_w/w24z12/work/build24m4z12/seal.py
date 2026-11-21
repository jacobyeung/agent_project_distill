from pathlib import Path
import json,hashlib,shutil,subprocess,sys,tarfile,base64
J=Path.cwd();D=J/'work/build24m4z12';K=J/'out/kit_n'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
rows=[]
for k in (K,J/'out/kit_n_go',J/'work/build24/kits/n'):
 old=sha(k/'SHA256SUMS.txt')
 if k!=K:
  for n in ('b/pc.py',):shutil.copyfile(K/n,k/n)
 files=sorted(p for p in k.rglob('*') if p.is_file() and p.name not in ('SHA256SUMS.txt','BUILD.json'))
 (k/'SHA256SUMS.txt').write_text(''.join(sha(p)+'  '+str(p.relative_to(k))+'\n' for p in files))
 v=json.loads((k/'BUILD.json').read_text())
 if 'payload' in v:v=json.loads(base64.b64decode(v['payload']))
 v['kit_sha256']=sha(k/'SHA256SUMS.txt')
 raw=(json.dumps(v,sort_keys=True,indent=2)+'\n').encode()
 (k/'BUILD.json').write_text(json.dumps(dict(encoding='base64-json',payload=base64.b64encode(raw).decode(),sha256=hashlib.sha256(raw).hexdigest()),sort_keys=True)+'\n')
 result=subprocess.run([sys.executable,'-I','-s','-B',str(k/'b/v.py'),str(k)],capture_output=True,text=True)
 assert result.returncode==0 and result.stdout.strip()==v['kit_sha256'],result.stderr
 rows.append(dict(kit=str(k.relative_to(J)),old=old,new=v['kit_sha256'],own_checker=result.stdout.strip()))
(D/'SEALS.json').write_text(json.dumps(rows,indent=2)+'\n')
E=J/'out/e3'
if (E/'k.tgz').exists():(E/'k.tgz').rename(J/'attic'/('e3_k_'+sha(E/'k.tgz')[:10]+'.tgz'))
with tarfile.open(E/'k.tgz','w:gz') as t:
 for p in sorted(K.rglob('*')):
  if p.is_file():t.add(p,arcname=str(p.relative_to(K)),recursive=False)
names=['e3.py','observe.py','run.sh','k.tgz','trinity.py','trinity.sh','readback.py']
(E/'pins.json').write_text(json.dumps({n:sha(E/n) for n in names},indent=2)+'\n')
print(json.dumps(rows))
