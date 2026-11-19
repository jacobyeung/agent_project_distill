from pathlib import Path
import json,sys
L=Path(__file__).resolve().parents[2]; B=L/'work/build21'; E=L.parent/'ext/m400real'
sys.path[:0]=[str(B),str(L/'work/tree_r1')]
import joblib as J
manifest=J.load(E/'MANIFEST.json')
for x in manifest['files']:
    if x['sha256'].startswith('ca0616db'):
        p=E/('files'+x['path']);v=J.load(p)
        print('P routing',p,json.dumps(v,indent=2))
cfg=J.load(B/'kits/q/k/n.json')
print('CONFIG',json.dumps({k:cfg.get(k) for k in ('s1_routing','streams','r1_training','code')},indent=2))
print('CARD',json.dumps(J.load(B/'inputs/mix.json'),indent=2))
