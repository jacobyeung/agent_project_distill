from pathlib import Path
import json
B=Path(__file__).resolve().parent
def load(p):return json.loads(p.read_text())
coverage=load(B/'DELTA_COVERAGE.json')
print('unobserved_kit',[r for r in coverage['kit']['statements'] if not r['observed']])
binding=load(B/'proofs/v2h/BINDING.json')
print('union',binding['union']);print('pro_rata',binding['pro_rata'])
plan=load(B/'proofs/census/PLAN_RUN.json')
print('coverage_cell',plan['cells']['coverage']);print('ceiling_cuts',plan['allocation']['cuts'])
for p in sorted((B/'proofs').rglob('TESTS.json')):
    if any('before' in part or part=='mutant' for part in p.parts):continue
    value=load(p)
    if not value['successful']:print('FAILED',p)
