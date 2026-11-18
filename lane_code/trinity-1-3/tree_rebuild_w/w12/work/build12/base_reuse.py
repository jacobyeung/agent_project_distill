from pathlib import Path
import hashlib,json,sys
L=Path(__file__).resolve().parents[2];B=L/'work/build12';N=L/'work/n1fix2'
sys.path.insert(0,str(L/'work/tree_r1'))
from student_pilot.source_seal import inventory
old=L/'work/build9fix/test_runner.py';new=N/'test_runner.py'
equivalent=old.read_text().replace('work/build9fix','work/n1fix2')==new.read_text()
base=inventory(L/'work/base/tree_b01ce449');fixtures=inventory(L/'fixtures');groups=[]
for group in ('generator','legacy','r2'):
    path=N/'inherited/suite_base'/group/'GROUP_RECEIPT.json';row=json.loads(path.read_text())
    good=(row['inputs']['source']==base and row['inputs']['fixtures']==fixtures and row['inputs']['runner_sha256']==hashlib.sha256(old.read_bytes()).hexdigest())
    groups.append(dict(group=group,equal=good,receipt=str(path.relative_to(L)),sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
result=dict(equivalent_runner=equivalent,groups=groups,reusable=equivalent and all(r['equal'] for r in groups))
(B/'BASE_REUSE.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if result['reusable']:
    p=N/'package.py';s=p.read_text();needle="    env['R2_TREE']=str(path)"
    insert="""    if variant=='base':
        prior=L/'work/n1fix2/inherited'
        original_runner=L/'work/build9fix/test_runner.py'
        current_runner=L/'work/n1fix2/test_runner.py'
        assert original_runner.read_text().replace('work/build9fix','work/n1fix2')==current_runner.read_text()
        receipts=[]
        for group in ('generator','legacy','r2'):
            old=json.loads((prior/'suite_base'/group/'GROUP_RECEIPT.json').read_text())
            assert old['inputs']['source']==base_before and old['inputs']['fixtures']==fixtures_before
            assert old['inputs']['runner_sha256']==hashlib.sha256(original_runner.read_bytes()).hexdigest()
            receipts.append(dict(group=group,inputs=old['inputs']))
        output=L/'work/build12/proofs/n1/suite_base';output.mkdir(exist_ok=True)
        for name in ('results.json','source_hashes.json'):
            (output/name).write_bytes((prior/'proofs/suite_base'/name).read_bytes())
        (output/'RESUME_RECEIPT.json').write_text(json.dumps(dict(complete=True,groups=receipts,runner_equivalence='Exact source, fixture and normalized runner equality.')))
        results[variant]=dict(resumed=True,result=str(output/'results.json'))
        continue
"""
    assert needle in s;p.write_text(s.replace(needle,insert+needle))
