from pathlib import Path
import json,hashlib
L=Path(__file__).resolve().parents[2];M=L/'work/merge11';B=L/'work/n1fix2'
src=L.parent/'wn2/work/n1fix2/proofs/extent_admission/units/samples.json'
if not src.is_file():src=L.parent/'w9f/work/build9fix/proofs/extent_admission/units/samples.json'
rows=json.loads(src.read_text());assert len(rows)<=200
dst=M/'proofs/n1/input_samples/units/samples.json';dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(src.read_bytes())
for name in ('proof_r1_edges9.py','proof_contract_closure.py','proof_mix_edges9.py'):
    p=B/name;p.write_text(p.read_text().replace('proofs/n1/extent_admission/units/samples.json','proofs/n1/input_samples/units/samples.json'))
for name in ('gate_edges','r1_edges','prepared_guards','kit_scope'):(M/'proofs/n1'/name).mkdir(parents=True,exist_ok=True)
(M/'BOUNDED_INPUTS.json').write_text(json.dumps(dict(source=str(src),sha256=hashlib.sha256(src.read_bytes()).hexdigest(),rows=len(rows),current=str(dst.relative_to(L))),indent=2)+'\n')
print('Bounded unit-row proof inputs are staged.')
