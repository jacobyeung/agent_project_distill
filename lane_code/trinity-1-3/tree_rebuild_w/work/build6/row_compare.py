import hashlib,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build6';sys.path.insert(0,str(L/'work/tree_r1'))
from student_pilot.source_seal import inventory
from student_pilot.p3_provenance import digest
seal=digest(inventory(L/'work/contracts_r6/tree_copy'))
assert seal=='ba346bd9e8ba41ed0cd77fea5ae494df544b959ff9f80731f83d761f51a32343',seal
a=json.loads((B/'proofs/rows_build5/RESULTS.json').read_text());b=json.loads((B/'proofs/rows/RESULTS.json').read_text())
results=[]
for old,new in zip(a['families'],b['families'],strict=True):
    assert old['family']==new['family'] and old['sha256']==new['sha256']
    results.append(dict(family=new['family'],source=new['source'],rows=new['rows'],
        off_equals_build5=old['arms']['False']==new['arms']['False'],
        off=new['arms']['False'],on=new['arms']['True'],on_equals_off=new['arms']['True']==new['arms']['False']))
(B/'proofs/rows/PARITY.json').write_text(json.dumps(dict(build5_source='work/contracts_r6/tree_copy',build5_seal=seal,
    scope='Real packed-row producer/reader and pinned grammar. Frame-list placeholders carry only the source frame count; no RGB or scene admission is inferred.',families=results),indent=2)+'\n')
assert all(r['off_equals_build5'] and r['on_equals_off'] and r['on']['admitted']==r['rows'] for r in results)
print(json.dumps(results))
