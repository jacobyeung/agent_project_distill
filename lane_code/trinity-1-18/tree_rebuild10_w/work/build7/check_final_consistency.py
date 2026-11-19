"""Cross-check published counts and pins against the completed proof receipts."""
import json
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build7'
def read(name):return json.loads((B/name).read_text())
verified=read('FINAL_VERIFICATION.json');final=read('FINAL_STATE.json')
expected={row['arm']:row['kit_sha256'] for row in read('proofs/review/KIT_READCHECK.json')}
for arm,result in verified['kits'].items():
 assert result['sha256']==expected[arm]
 assert result['scan']['status']=='CLEAN'
assert final['tree_seal']==verified['tree_seal']
comparison=read('SUITE_COMPARISON.json')
assert final['package']=={k:comparison[k] for k in final['package']}
assert final['coverage']==read('CHANGED_COVERAGE.json')['classes']
assert final['supplemental_followup']['latest_case_outcomes']==read('FOLLOWUP_RESULTS.json')['latest_counts']
report=(L/'out/BUILD7_REPORT.md').read_text()
assert verified['tree_seal'] in report and verified['delivery']['sha256'] in report
assert all(value in report for value in expected.values())
assert 'FINAL_VERIFICATION.json' in report
assert (L/'out/DESIGN_RECORD_tree_rebuild_20261115.md').read_text().count('\n## Build 7\n')==1
assert 'GO=false' in (L/'out/PRELAUNCH_CARD.md').read_text()
assert 'running' not in (B/'STATUS.md').read_text()
record=dict(status='PASS',tree_seal=verified['tree_seal'],kits=expected,
            limitations='Consistency of delivery records only; acceptance remains BLOCKED.')
(B/'FINAL_CONSISTENCY.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record))
