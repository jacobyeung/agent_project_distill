from pathlib import Path
import json,re
L=Path(__file__).resolve().parents[2];B=L/'work/n1fix2';M=L/'work/merge11'
for p in B.iterdir():
    if p.is_file() and p.suffix=='.py':
        s=p.read_text().replace("B/'kits/","L/'work/merge11/kits/").replace('work/n1fix2/kits','work/merge11/kits')
        p.write_text(s)
for name in ('mix_checks9','mix_edges9','mix_accounting9','extent_conflict9','gate_edges9','r1_edges9','prepared9','contract_closure','registry_closure','kit_scope'):
    p=B/('proof_'+name+'.py')
    assert p.is_file()
    assert not re.search(r"(?:Path\(|open\()['\"]/(?:home|data)",p.read_text()),str(p)
print('All selected proof and kit paths are local.')
