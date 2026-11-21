import importlib.util,json,sys
from pathlib import Path
L=Path.cwd();D=L/'work/build24m4z8b';S=Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/work/d173912/173912')
sp=importlib.util.spec_from_file_location('pin_discovery',L/'out/pin_discovery.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
F=D/'pin_checks';F.mkdir()
a=dict(kit=L/'out/kit_qd',selection=S/'routing_selection.json',answer=L/'inputs/ORCH_2258Z.md',selection_sha256=m.SEL,answer_sha256=m.ANSWER,output=F/'kit',record=F/'record.json',receipt=S/'receipt.json',db_bytes=S/'db_bytes.json')
r=m.pin(**a);assert r['python_bytes_identical'] is True;expected=m.inventory(L/'out/kit_qdp');assert m.inventory(F/'kit')==expected
cases=[]
for name,changes,code in [('selection',dict(selection_sha256='0'*64),'SELECTION_DIFFERS'),('authorization',dict(answer=L/'inputs/ORCH_2256Z.md'),'AUTHORIZATION_DIFFERS'),('receipt',dict(receipt=S/'db_bytes.json'),'RECEIPT_DIFFERS')]:
 b=dict(a,output=F/name,record=F/(name+'.json'));b.update(changes)
 try:m.pin(**b)
 except ValueError as e:assert str(e)==code;cases.append(dict(case=name,error=str(e)))
 else:raise AssertionError(name)
 assert not b['output'].exists() and not b['record'].exists()
(D/'PIN_TESTS.json').write_text(json.dumps(dict(status='OK',deterministic_kit=True,seal=r['output']['seal'],negative=cases),indent=2)+'\n')
print('Pin reproducible; changed selection, authorization and receipt all refused')
