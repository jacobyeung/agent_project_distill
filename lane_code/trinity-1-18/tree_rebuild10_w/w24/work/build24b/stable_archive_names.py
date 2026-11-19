from pathlib import Path
import sys
L=Path(__file__).resolve().parents[2];D=L/'work/build24b';B=L/'work/build24';sys.path[:0]=[str(D),str(B),str(L/'work/tree_r1')]
import joblib as J
from kit import cap,reseal
records=J.load(D/'KIT.json')
for name in ('q','n'):
 k=B/'kits'/name;control=J.load(k/'k/a.json');oldrel=J.load(L/'attic/build24b'/('kit_'+name)/'k/a.json')['source']['path'];newrel=control['source']['path']
 assert oldrel!=newrel and not (k/oldrel).exists();(k/newrel).rename(k/oldrel)
 control['source']['path']=oldrel;cap(k,'k/a.json',control)
 sealfile=J.load(k/'k/7.json');sealfile['archive']['path']=oldrel;cap(k,'k/7.json',sealfile)
 cfg=J.load(k/'k/c.json');cfg['code']['sha256']=J.sha(k/'k/7.json');cap(k,'k/c.json',cfg)
 records[name]['kit_seal']=reseal(k)
 doc=J.load(D/('UPLOADS_'+name+'.json'))
 for x in doc['files']:
  if x['opaque_name']==name+'/'+newrel:x['opaque_name']=name+'/'+oldrel;x['local_path']=str(k/oldrel)
  if x['opaque_name'].startswith(name+'/'):
   p=Path(x['local_path']);x.update(bytes=p.stat().st_size,sha256=J.sha(p))
 doc['total_bytes']=sum(x['bytes'] for x in doc['files']);J.write(D/('UPLOADS_'+name+'.json'),doc);J.write(B/('UPLOADS_'+name+'.json'),doc)
J.write(D/'KIT.json',records);J.write(B/'KIT.json',records)
p=D/'kit.py';s=p.read_text().replace("target=k/'k'/('t_'+tree[:16]+'.tar')", "target=k/control['source']['path']");p.write_text(s)
(D/'upload').rename(L/'attic/build24b/upload_superseded')
for name in ('UPLOADS_24B.json','UPLOADS_24B.list'):(L/'out'/name).rename(L/'attic/build24b'/name)
print(records)
