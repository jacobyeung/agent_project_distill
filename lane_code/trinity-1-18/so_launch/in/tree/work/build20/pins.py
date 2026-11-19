from pathlib import Path
import json
L=Path(__file__).resolve().parents[2];E=L.parent/'ext/pwrap'
v=json.loads((E/'k/0.json').read_text())
for k,x in v.items():
    if isinstance(x,dict): print(k,{a:b for a,b in x.items() if not isinstance(b,(dict,list))})
    elif isinstance(x,list):print(k,'entries',len(x))
    else:print(k,x)
print('manifest lines',len((E/'SHA256SUMS.txt').read_text().splitlines()))
print('listing', (E/'LISTING_k_arm_runs.txt').read_text()[:3500])
for name in ('r1_ops7/exq.sh','r1_ops7/exw.sh'):
    print(name,(E/name).read_text()[:4500])
