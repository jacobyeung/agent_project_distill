from common import *
raw=base64.b64decode(json.loads((kit('q')/'k/c0.json').read_text())['payload'])
h=hashlib.sha256(raw).hexdigest();p=D/'generated/u'/h;p.parent.mkdir(parents=True,exist_ok=True)
if not p.exists():p.write_bytes(raw)
entry=dict(bytes=len(raw),opaque_name='u/'+h,sha256=h)
for name in ('q','n','n_go','qd'):
 k=kit(name);cfg=J.load(k/'k/n.json');cfg['code']=dict(path='u/'+h,sha256=h);cap(k,'k/n.json',cfg)
 spec=J.load(k/'k/p.json');assert spec['code_sha256']==h
 if not any(v['sha256']==h for v in spec['uploads']):spec['uploads'].append(entry)
 spec['pin_paths'][h]=spec['namespace']+'/u/'+h;cap(k,'k/p.json',spec)
 # Detach mutable seal files before resealing, since tests retain hard links.
 for part in ('BUILD.json','SHA256SUMS.txt'):replace(k/part,(k/part).read_bytes())
 print(name,reseal(k))
 if name!='n_go':
  path=D/('UPLOADS_'+name+'.json');v=J.load(path)
  if not any(x['sha256']==h for x in v['files']):v['files'].append(dict(entry,local_path=str(p),needed_minimal=True))
  v['total_bytes']=sum(x['bytes'] for x in v['files']);J.write(path,v)
J.write(D/'SOURCE_PIN_UPDATE.json',dict(status='PASS',sha256=h,bytes=len(raw),field='k/n.json:code',runtime_code_unchanged=True))
