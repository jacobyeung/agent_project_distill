from pathlib import Path
import json
L=Path(__file__).resolve().parents[2]; B=L/'work/n1fix2'
for name in ('work/build9fix/PACKET_INPUTS.json','work/build9fix/inputs/config.json','work/build9fix/kits/r1/k/h.json'):
    p=L/name;v=json.loads(p.read_text())
    if name.endswith('config.json'):
        v={k:v.get(k) for k in ('remove_files','scene_division','extent_receipt','r1_training')}
    print(name,json.dumps(v)[:12000])
for folder in ('work','work/build9fix/kits','work/contracts_r6/packet_root/work','work/build9fix/proofs/packet'):
    print(folder,[p.name for p in (L/folder).iterdir()])
