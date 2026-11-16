import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
R = ROOT.parent
suite = {}
for path in sorted((R/'tmp').glob('eat1_*/runs/*/EAT1_REPORT.json')):
    report = json.loads(path.read_text())
    key = path.parent.name if path.parents[2].name.startswith('eat1_adv_') else 'toy/'+path.parent.name
    suite[key] = dict(path=str(path.relative_to(R)), overall=report['overall'],
        clauses={k:v['status'] for k,v in report['clauses'].items()},
        rules={k: sorted({o.get('rule') or o.get('kind') or o.get('file') for o in v['offenders']})
               for k,v in report['clauses'].items()},
        claim_grade=report.get('claim_grade'))
    if path.parent.name == 'memo':
        suite['memo']['proof'] = report['clauses']['A5']['cache_proof']
        suite['memo']['claim_needs_live_run'] = report['clauses']['A5']['claim_needs_live_run']
    if path.parent.name == 'empty_trace':
        suite['empty_trace']['strace'] = report['clauses']['A1']['strace']
(ROOT/'suite_evidence.json').write_text(json.dumps(suite, indent=2)+'\n')
for name, entry in suite.items():
    print('T', name, entry['overall'], json.dumps({k:entry['rules'][k] for k,v in entry['clauses'].items() if v != 'PASS'}))

outputs = {}
for path in sorted((ROOT/'results').glob('*/EAT1_REPORT.json')):
    report = json.loads(path.read_text())
    item = json.loads((path.parent/'ITEMS.jsonl').read_text().splitlines()[0])
    outputs[path.parent.name] = item['output']
    print('P', path.parent.name, report['overall'], 'answer=', item['output']['answer'],
          'response=', item['output']['calls'][0]['response'], 'claim_grade=',report['claim_grade'])
print('diagnostic_equals_control', outputs['diagnostic'] == outputs['control'])
print('maximum_head_equals_abs_head', outputs['maximum_head'] == outputs['abs_head'])

from probes_r4.variants import make_reader
for name in ('config', 'class_config', 'tensor_config'):
    reader = make_reader(ROOT/'fixture', name)
    head = reader.model.perception.move_head
    print(name, 'scale=',head.calibration.scale, 'state_dict_keys=', list(head.state_dict()),
          'buffers=',list(head.named_buffers()))

checks = []
for line in (R/'COPY_FILES.sha256').read_text().splitlines():
    expected, name = line.split(maxsplit=1)
    actual = hashlib.sha256((R/name).read_bytes()).hexdigest()
    checks.append(expected == actual)
print('kit_hashes',sum(checks),'/',len(checks))
assert all(checks)
files = [p for p in R.rglob('*') if p.is_file()]
print('workspace_bytes',sum(p.stat().st_size for p in files))
