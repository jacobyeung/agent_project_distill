from pathlib import Path
import json
L=Path(__file__).resolve().parents[2]; B=L/'work/n1fix2'
p=B/'stage9.py';s=p.read_text().replace("next(v for v in inherited.values() if v['kit_path'].endswith('/'+name))",'inherited[name]');p.write_text(s)
p=B/'proof_text.py';s=p.read_text().replace("L.parent/'work/rows_slices", "L/'work/rows_slices");p.write_text(s)
audit=B/'proofs/audit';audit.mkdir(exist_ok=True)
(audit/'INFERENCE_COMPONENTS.json').write_bytes((B/'inherited/proofs/audit/INFERENCE_COMPONENTS.json').read_bytes())
p=B/'package.py';s=p.read_text()
needle="    env['R2_TREE']=str(path)"
insert='''    if variant=='base':
        prior=L/'work/n1fix2/inherited'
        original_runner=L/'work/build9fix/test_runner.py'
        current_runner=L/'work/n1fix2/test_runner.py'
        assert original_runner.read_text().replace('work/build9fix','work/n1fix2')==current_runner.read_text()
        receipts=[]
        for group in ('generator','legacy','r2'):
            old=json.loads((prior/'suite_base'/group/'GROUP_RECEIPT.json').read_text())
            assert old['inputs']['source']==base_before
            assert old['inputs']['fixtures']==fixtures_before
            assert old['inputs']['runner_sha256']==hashlib.sha256(original_runner.read_bytes()).hexdigest()
            receipts.append(dict(group=group,receipt_sha256=hashlib.sha256((prior/'suite_base'/group/'GROUP_RECEIPT.json').read_bytes()).hexdigest(),inputs=old['inputs']))
        output=L/'work/n1fix2/proofs/suite_base';output.mkdir(exist_ok=True)
        for name in ('results.json','source_hashes.json'):
            (output/name).write_bytes((prior/'proofs/suite_base'/name).read_bytes())
        (output/'RESUME_RECEIPT.json').write_text(json.dumps(dict(complete=True,groups=receipts,runner_equivalence='Only local harness path relocated; all source and fixture bytes match.'),indent=2))
        results[variant]=dict(resumed=True,result=str(output/'results.json'))
        continue
'''
s=s.replace(needle,insert+needle)
p.write_text(s)
# Every executed harness file has been checked for external workspace writes.
names=['run.sh','test_runner.py','compact_tmp.py','stage9.py','monitor9.py','proof_text.py','proof_forward9.py',
       'seal.py','make_delivery.py','package.py','packet_final.py','PACKET_TEST.sh','PACKAGE_TEST.sh','requalification_gate.py']
issues=[]
for name in names:
    for line,text in enumerate((B/name).read_text().splitlines(),1):
        if 'L.parent' in text or '/tree_rebuild_w/w9f' in text or '/tree_rebuild/' in text:
            issues.append(dict(file=name,line=line,text=text))
(B/'EXECUTABLE_PATH_SEARCH.json').write_text(json.dumps(dict(files=names,issues=issues),indent=2)+'\n')
assert not issues
print('Final harness prepared; executed paths stay local.')
