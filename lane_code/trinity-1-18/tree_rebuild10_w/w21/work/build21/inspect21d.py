from pathlib import Path
import base64,hashlib,json,sys
L=Path(__file__).resolve().parents[2];B=L/'work/build21';sys.path.insert(0,str(B))
import joblib as J
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()
for doc in ('k/7.json','k/c0.json'):
    v=J.load(B/'kits/q'/doc)
    for key in ('files','sources','operation_sources'):
        if key in v:print(doc,key,digest(v[key]))
v=J.load(B/'kits/q/k/s.json')
for key,entry in v['entries'].items():
    content=json.loads(base64.b64decode(entry['payload']))
    print('ENTRY',key,'sha',entry['sha256'],'room_rule',repr(content.get('room_rule')))
v=J.load(B/'kits/q/k/n.json')
for path in [('benchmark_scene_exclusions',),('dev_scene_exclusions',),('r1_training','wording_exclusion'),('s1_routing','catalog')]:
    item=v
    for part in path:item=item[part]
    print(path,json.dumps(item))
