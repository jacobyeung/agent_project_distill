"""Close the qualification receipts and write the delivery report."""
from pathlib import Path
import json
import subprocess
import sys

L = Path(__file__).resolve().parents[2]
B = L / 'work/n1fix'
def read(name):
    return json.loads((B / name).read_text())

assert all(r['status'] == 'complete' and r['returncode'] == 0 for r in read('FINAL_STEPS.json'))
assert read('proofs/suite_tree/results.json')['complete']
assert all(r['outcome'] == 'passed' for r in read('proofs/packet/results.json').values())
assert all(r['clean_pass'] and r['caught'] and not r['errors'] for r in read('proofs/mutations/RESULT.json')['results'])
assert read('proofs/prepared_guards/RESULT.json')['status'] == 'PASS'
assert read('proofs/prepared_guards/SAMPLER_IDENTITY.json')['status'] == 'PASS'
comparison = read('SUITE_COMPARISON.json')
gaps = read('GAPS.json')
unexpected = [r for r in comparison['failures'] if not r['preexisting'] and 'BF16' not in r['cause']]
result = dict(cpu_gaps=len(gaps), unexpected_regressions=len(unexpected),
              r2_failures=comparison['r2_failures'], complete=not gaps and not unexpected and not comparison['r2_failures'],
              supplemental_proofs=['proofs/prepared_guards/RESULT.json', 'proofs/prepared_guards/SAMPLER_IDENTITY.json'])
(B / 'FINAL_CHECK.json').write_text(json.dumps(result, indent=2) + '\n')
assert result['complete'], result
for name in ('report', 'verify_delivery', 'storage'):
    subprocess.run([sys.executable, '-I', '-s', '-B', str(B / (name + '.py'))], cwd=L, check=True)
print(json.dumps(result))
