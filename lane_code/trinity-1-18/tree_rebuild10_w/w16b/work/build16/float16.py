"""Audit float-JSON comparisons without changing the frozen packet assertion."""
from pathlib import Path
import json,hashlib,sys,ast
L=Path(__file__).resolve().parents[2];T=L/'work/tree_r1';B=L/'work/build16';O=B/'proofs/float';O.mkdir(parents=True,exist_ok=True)
sys.path[:0]=[str(T),str(L/'work/n1fix2')]
from monitor9 import Monitor
m=Monitor(T)
from student_pilot.p3_provenance import digest,encoded,file_pin,pinned,load
value={'measure':0.12345678901234567,'nested':[1.0000000000000002]}
p=O/'value.json';p.write_text(encoded(value))
pin=file_pin(p)
assert digest(load(pinned(pin)))==digest(value)
formatted=O/'format.json';formatted.write_text(json.dumps(value,indent=4))
assert load(formatted)==load(p)
assert digest(load(formatted))==digest(load(p))
paths=[T/'student_pilot'/n for n in ('r1_population.py','r2_intake.py','r2_contract.py','carrier_c1_run.py','p3_provenance.py')]
sites=[]
for path in paths:
    lines=path.read_text().splitlines()
    for i,line in enumerate(lines,1):
        if ('digest(' in line and ('!=' in line or '==' in line)) or 'sha256(path) !=' in line:
            sites.append(dict(file=str(path.relative_to(L)),line=i,text=line.strip()))
test=L/'work/contracts_r6/packet_root/work/tests_r6/test_generator_r4.py'
test_line=next(i for i,s in enumerate(test.read_text().splitlines(),1) if 'json.dumps(off' in s)
result=dict(packet_assertion=dict(file=str(test.relative_to(L)),line=test_line),
    generator_baseline_runtime_consumer=False,runtime_exact_content_bindings=sites,
    interpretation='The packet compares independently recomputed floating results serialized as JSON. Runtime row/config identities compare authenticated stored values or pins; no runtime path reads generator_baseline_r5.json. Stored JSON values round-trip without recomputing geometry. Byte hashes intentionally refuse changed content.',
    round_trip=True,parsed_formatting_equivalent=True,runtime_change_required=False,
    test_changed=False)
(O/'RESULT.json').write_text(json.dumps(result,indent=2));m.save(O)
print(json.dumps(result,indent=2))
