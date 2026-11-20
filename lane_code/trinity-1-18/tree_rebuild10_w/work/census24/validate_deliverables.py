import ast
import collections
import json
import resource
from pathlib import Path

resource.setrlimit(resource.RLIMIT_AS, (15 << 30, 15 << 30))
c = Path.cwd()
data = json.loads((c / 'CENSUS.json').read_text())
rows = data['rows']
checks = {}
def require(name, value):
    checks[name] = bool(value)
    assert value, name

require('row_count', len(rows) == data['counts']['rows'])
require('unique_ids', len({r['id'] for r in rows}) == len(rows))
require('mark_counts', dict(collections.Counter(r['mark'] for r in rows)) == data['counts']['by_mark'])
require('verdict_counts', dict(collections.Counter(r['verdict'] for r in rows)) == data['counts']['by_verdict'])
require('new_stricter_verdicts', all(r['verdict'] in {'PASSES', 'REFUSES', 'UNDECIDED offline'} for r in rows if r['mark'] in {'NEW', 'STRICTER'}))
require('unknown_deciders', all(r.get('deciding_input') and r.get('condition') for r in rows if r['verdict'] == 'UNDECIDED offline'))
require('same_p_sites', all(r['p_sites'] for r in rows if r['mark'] == 'SAME'))
require('new_no_p_site', all(not r['p_sites'] for r in rows if r['mark'] == 'NEW'))
require('phase_membership', all(r['phases'] for r in rows))
names = {n for r in rows for n in r['names']}
require('pixel_family', {'processor_resolution_pin_missing', 'processor_resolution_range', 'frame_count_must_be_32_or_64', 'training_frame_layout_mismatch', 'reader_training_layout_mismatch', 'row_training_frame_count_mismatch'} <= names)
require('refusal_set', {r['file'] + ':' + str(r['line']) for r in rows if r['verdict'] == 'REFUSES'} == {'b/pl.py:20', 'student_pilot/b7_inputs.py:37', 'student_pilot/r1_handover.py:186'})
line_counts = {name: len((c / name).read_text().splitlines()) for name in ('CENSUS.md', 'CANARY.md', 'FINAL.md')}
require('line_caps', line_counts['CENSUS.md'] < 400 and line_counts['CANARY.md'] < 60 and line_counts['FINAL.md'] < 15)
require('canary_first_line', (c / 'CANARY.md').read_text().startswith('CANARY c'))
final_first = (c / 'FINAL.md').read_text().splitlines()[0]
require('final_counts', final_first.startswith('REFUSES 3 rows:') and 'UNDECIDED 628 rows:' in final_first)
require('final_all_unknown_ids', all(r['id'] in final_first for r in rows if r['verdict'] == 'UNDECIDED offline'))
texts = {}
raise_lines = {}
for r in rows:
    file = r['file']
    path = (c / 'n_go_j.sh' if file == 'k/j.json (decoded launch shell)' else
            Path(data['launch_kit']) / 'job.sh' if file == 'job.sh' else
            Path(data['launch_kit']).parent / 'kit_qd' / file.removeprefix('qd/') if file.startswith('qd/') else
            Path(data['launch_kit']) / file if file.startswith('b/') else
            Path(data['tree_c']) / file)
    if path not in texts:
        texts[path] = path.read_text().splitlines()
        if path.suffix == '.py':
            raise_lines[path] = {n.lineno for n in ast.walk(ast.parse(path.read_text())) if isinstance(n, ast.Raise)}
    require('source:' + r['id'], 1 <= r['line'] <= len(texts[path]))
    if r['kind'] == 'raise':
        require('raise:' + r['id'], r['line'] in raise_lines[path])
for name in ('scan_sources.py', 'build_census.py', 'offline_checks.py', 'offline_more.py', 'metadata_checks.py', 'supplemental_checks.py'):
    ast.parse((c / name).read_text())
require('scripts_parse', True)
total = sum(p.stat().st_size for p in c.rglob('*') if p.is_file())
require('under_2GB', total < 2_000_000_000)
result = dict(status='PASS', rows=len(rows), counts=data['counts'], line_counts=line_counts, bytes=total, assertions=len(checks), checks=checks,
              limitations='Structural report validation only; no additional production, GPU, weight, row, namespace or network check ran.')
(c / 'VALIDATION.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({k:v for k,v in result.items() if k != 'checks'}, indent=2))
