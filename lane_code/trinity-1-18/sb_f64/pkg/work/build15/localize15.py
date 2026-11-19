from pathlib import Path
import json,hashlib
L=Path(__file__).resolve().parents[2];B=L/'work/build15';rows=[]
def local(x):
    if isinstance(x,dict):
        result={k:local(v) for k,v in x.items()}
        if set(result)=={'path','sha256'}:
            for prefix in ('/scratch/jjyeung/orch_n30/tree_rebuild_w/w14/','/scratch/jjyeung/orch_n30/tree_rebuild10_w/w14/'):
                if result['path'].startswith(prefix):
                    p=L/result['path'][len(prefix):]
                    if p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()==result['sha256']:
                        rows.append(dict(original=result['path'],local=str(p),sha256=result['sha256']))
                        result['path']=str(p)
        return result
    if isinstance(x,list):return [local(v) for v in x]
    return x
p=B/'inputs/kit_config.json';p.write_text(json.dumps(local(json.loads(p.read_text())),indent=2)+'\n')
(B/'LOCAL_PINS.json').write_text(json.dumps(rows,indent=2))
if (B/'kits').exists():(B/'kits').rename(B/'retained_kits_attempt')
print('Localized verified metadata pins:',len(rows))
