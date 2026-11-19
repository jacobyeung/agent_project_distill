from pathlib import Path
import ast,gzip,hashlib,io,json,re,tarfile
W=Path(__file__).resolve().parent.parent;R=W/'out2'
def sha(b):return hashlib.sha256(b).hexdigest()
def put(p,b):
 p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
def unpack(b):
 with tarfile.open(fileobj=io.BytesIO(b)) as t:
  assert all(m.isfile() and not m.name.startswith('/') and '..' not in Path(m.name).parts for m in t)
  return {m.name:t.extractfile(m).read() for m in t}
def tarbytes(files):
 buf=io.BytesIO()
 with gzip.GzipFile(fileobj=buf,mode='wb',mtime=0) as gz:
  with tarfile.open(fileobj=gz,mode='w') as t:
   for n,b in sorted(files.items()):
    m=tarfile.TarInfo(n);m.size=len(b);m.mode=0o600;t.addfile(m,io.BytesIO(b))
 return buf.getvalue()
def apply(raw,section):
 lines=raw.decode().splitlines();out=[];pos=0;ls=section.splitlines();i=0
 while i<len(ls):
  if not ls[i].startswith('@@ '):i+=1;continue
  m=re.match(r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@',ls[i]);assert m,ls[i]
  start=int(m[1]);oldn=int(m[2] or 1);newn=int(m[4] or 1);target=start-1 if oldn else start
  out+=lines[pos:target];pos=target;i+=1;used=made=0
  while used<oldn or made<newn:
   s=ls[i];i+=1;assert s[:1] in ' +-',(s,used,oldn)
   if s[0] in ' -':assert lines[pos]==s[1:],(lines[pos],s);pos+=1;used+=1
   if s[0] in ' +':out.append(s[1:]);made+=1
 out+=lines[pos:];return ('\n'.join(out)+'\n').encode()
proof=[]
for k,label,t in [('b1','A','T1'),('b2','B','T2')]:
 old=W/'out'/k;dest=R/label;base=R/'bases'/k
 delivery=unpack((W/'in/bases'/t/'1.tgz').read_bytes());payload=unpack(delivery['0.tgz'])
 for n,b in delivery.items():put(base/'package'/n,b)
 for n,b in payload.items():put(base/'src'/n,b)
 put(base/'0.tgz',delivery['0.tgz'])
 for n,v in [('inputs_tower.json','a/1.json'),('export_544.json','a/export.json'),('node_check.py','a/5.py'),('tower_sequence.py','a/6.py'),('PACKAGE.json','PACKAGE.json')]:put(base/n,delivery[v])
 line=next(s for s in delivery['BATCH.sh'].decode().splitlines() if s.startswith('b=bytes.fromhex('));bundle=unpack(bytes.fromhex(ast.literal_eval(ast.parse(line).body[0].value.args[0])))
 put(base/'tower_bootstrap.py',bundle['0.py'])
 text=(old/'PATCH.diff').read_text().replace(' }--- base/',' }\n--- base/')
 sections=re.split(r'(?m)^--- ',text)[1:]
 operator={}
 for sec in sections:
  lines=sec.splitlines();target=lines[1][4:];group,n=target.split('/',1)
  if group=='payload':
   raw=payload[n]
   if n=='9.json':raw=json.dumps(json.loads(raw),indent=2,sort_keys=True).encode()
   raw=apply(raw,sec)
   if n=='9.json':raw=json.dumps(json.loads(raw),sort_keys=True).encode()
   payload[n]=raw
  elif group=='delivery':delivery[n]=apply(delivery.get(n,b''),sec)
  elif group=='operator':
   operator[n]=(old/n).read_bytes() if (old/n).exists() else (W/'out/b1'/n).read_bytes()
 for n,b in payload.items():put(dest/'src'/n,b)
 raw=tarbytes(payload);delivery['0.tgz']=raw
 public=json.loads(delivery['0.json']);assert sha(raw)==public['payload_sha256'],(k,sha(raw),public)
 for n,h in json.loads(delivery['PACKAGE.json'])['files'].items():assert sha(delivery[n])==h,(k,n)
 for n,b in delivery.items():put(dest/'package'/n,b)
 put(dest/'0.tgz',raw);put(dest/'1.tgz',tarbytes(delivery))
 for p in old.iterdir():
  if p.is_file() and p.name not in ('0.tgz','1.tgz') :put(dest/p.name,p.read_bytes())
 for n,b in operator.items():put(dest/n,b)
 put(dest/'TOKEN',(public['token']+'\n').encode())
 # Reverse the operator diff to recover base fill without any outside path reads.
 fillsec=next(s for s in sections if s.splitlines()[1]=='+++ operator/fill_export.py')
 ls=fillsec.splitlines();rev=[]
 for line in ls:
  if line.startswith('@@ '):
   m=re.match(r'@@ -(\d+(?:,\d+)?) \+(\d+(?:,\d+)?) @@(.*)',line);line='@@ -'+m[2]+' +'+m[1]+' @@'+m[3]
  elif line.startswith('+') and not line.startswith('+++'):line='-'+line[1:]
  elif line.startswith('-') and not line.startswith('---'):line='+'+line[1:]
  rev.append(line)
 put(base/'fill_export.py',apply(operator['fill_export.py'],'\n'.join(rev)))
 rec=dict(package=label,token=public['token'],files={})
 for n in ('0.tgz','1.tgz','PACKAGE.json','READ_PLAN.json'):
  wanted=re.search(r'\| '+re.escape(n)+r' \| `([a-f0-9]{64})`', (old/'REPORT.md').read_text())[1]
  actual=sha((dest/n).read_bytes());rec['files'][n]=dict(expected=wanted,actual=actual,identical=actual==wanted)
 proof.append(rec)
 print(json.dumps(rec))
put(R/'BYTE_IDENTITY.json',(json.dumps(proof,indent=2)+'\n').encode())
# Only these two explicitly named external settings files are read.
settings=Path('/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/reader_r1/files')
for n,prefix in [('R1_READ_SETTINGS_PLAN_ENTRY.json','4493ee34'),('R1_READER_SETTINGS_0.json','2c3cc6b4')]:
 b=(settings/n).read_bytes();assert sha(b).startswith(prefix);put(R/'pins'/n,b)
