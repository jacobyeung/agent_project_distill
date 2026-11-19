"""Confirm saved dry evidence and preserve the exact executed validator source."""
import hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parent
d=json.loads((root/'out/DRYRUN.json').read_text())
assert d['status']=='PASS' and d['passed']
assert all(c['passed'] for c in d['tests']+d['stored_label_parity'])
assert all(c['passed'] for c in d['corrected_label_parity'].values())
assert d['A0_candidates_argmax_replay']['matched']==d['A0_candidates_argmax_replay']['total']==149
p=root/'validate_dry.py'
old=p.read_text().replace('json.dumps(R.clean(', 'json.dumps(').replace('])),indent=2))', ']),indent=2))')
expected=d['input_sha256'][str(p)]
assert hashlib.sha256(old.encode()).hexdigest()==expected
folder=root/'out/executed_sources';folder.mkdir(exist_ok=True)
(folder/('validate_dry_'+expected+'.py')).write_text(old)
result=dict(status='PASS',saved_dry_status=d['status'],executed_validator_sha256=expected,
    input_sha256={str(root/'out/DRYRUN.json'):hashlib.sha256((root/'out/DRYRUN.json').read_bytes()).hexdigest(),
                  str(Path(__file__).resolve()):hashlib.sha256(Path(__file__).read_bytes()).hexdigest()})
(root/'out/DRY_CONFIRMATION.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
