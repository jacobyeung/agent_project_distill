from pathlib import Path
import sys
L=Path(__file__).resolve().parents[2];D=L/'work/build24'
sys.path[:0]=[str(D),str(L/'work/tree_r1'),str(L/'work/build21')]
import joblib as J
from kit import reseal
records=J.load(D/'KIT.json')
for name in ('q','n'):
    k=D/'kits'/name;(k/'b/z.py').write_bytes((D/'joblib.py').read_bytes());seal=reseal(k)
    doc=J.load(D/('UPLOADS_'+name+'.json'))
    for item in doc['files']:
        if item['opaque_name'].startswith(name+'/'):
            p=Path(item['local_path']);item.update(sha256=J.sha(p),bytes=p.stat().st_size)
    doc['total_bytes']=sum(x['bytes'] for x in doc['files']);J.write(D/('UPLOADS_'+name+'.json'),doc)
    records[name].update(kit_seal=seal,upload_bytes=doc['total_bytes'])
J.write(D/'KIT.json',records)
