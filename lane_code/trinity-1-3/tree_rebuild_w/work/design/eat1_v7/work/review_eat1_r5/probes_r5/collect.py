"""Summarize saved reports and verify the independent probes' evidence."""
import hashlib
import json
from pathlib import Path

import torch

from eat1.run import state_tensors
from eat1.toy.adversarial import EXPECT
from probes_r5.variants import make_reader

ROOT = Path(__file__).resolve().parent
R = ROOT.parent
suite = {}
for path in sorted((R/'tmp').glob('eat1_*/runs/*/EAT1_REPORT.json')):
    report = json.loads(path.read_text())
    key = path.parent.name if path.parents[2].name.startswith('eat1_adv_') else 'toy/'+path.parent.name
    suite[key] = dict(path=str(path.relative_to(R)), overall=report['overall'],
        clauses={k:v['status'] for k,v in report['clauses'].items()},
        rules={k: sorted({o.get('rule') or o.get('kind') or o.get('file') for o in v['offenders']})
               for k,v in report['clauses'].items()}, claim_grade=report.get('claim_grade'))
(ROOT/'suite_evidence.json').write_text(json.dumps(suite, indent=2)+'\n')
for name, entry in suite.items():
    print('T', name, entry['overall'], json.dumps({k:entry['rules'][k] for k,v in entry['clauses'].items() if v != 'PASS'}))
checked = {name: (suite[name]['overall'] == 'PASS' if clause is None else suite[name]['clauses'][clause] == 'FAIL')
           for name, clause in EXPECT.items() if name in suite}
print('adversarial_expected', sum(checked.values()), '/', len(EXPECT), 'available=', len(checked))

outputs = {}
for path in sorted((ROOT/'results').glob('*/EAT1_REPORT.json')):
    report = json.loads(path.read_text())
    item = json.loads((path.parent/'ITEMS.jsonl').read_text().splitlines()[0])
    outputs[path.parent.name] = item['output']
    print('P', path.parent.name, report['overall'], 'answer=', item['output']['answer'],
          'response=', item['output']['calls'][0]['response'], 'claim_grade=', report['claim_grade'])
print('diagnostic_length_equals_control', outputs['diagnostic_length'] == outputs['control'])
for variant in ('two_item_control', 'shared_heads'):
    for line in (ROOT/'results'/variant/'ITEMS.jsonl').read_text().splitlines():
        item = json.loads(line)
        print(variant, item['id'], 'answer=', item['output']['answer'])
reader = make_reader(ROOT/'fixture', 'shared_heads')
head = reader.model.perception.depth_head
print('shared_heads_depth_scale', head.calibration.scale, 'state_dict_keys=', list(head.state_dict()),
      'buffers=', list(head.named_buffers()))

reader = make_reader(ROOT/'fixture', 'slots_tensor')
head = reader.model.perception.move_head
print('slots_tensor', 'scale=', head.calibration.scale.item(), 'state_dict_keys=', list(head.state_dict()),
      'buffers=', list(head.named_buffers()),
      'captured_preexisting=', id(head.calibration.scale) in {id(t) for t in state_tensors(reader)})
reader = make_reader(ROOT/'fixture', 'sign_choice')
item = json.loads((ROOT/'fixture/move.jsonl').read_text())
from eat1.toy.reader import read_frames
with torch.no_grad():
    feats = reader.model.perception(read_frames(item['frames']))['feats']
    head = reader.model.perception.move_head
    print('sign_choice_candidates', head(torch.cat([feats[1], feats[0]])).item(),
          head(torch.cat([feats[0], feats[1]])).item())

checks = []
for line in (R/'COPY_FILES.sha256').read_text().splitlines():
    expected, name = line.split(maxsplit=1)
    checks.append(expected == hashlib.sha256((R/name).read_bytes()).hexdigest())
print('kit_hashes', sum(checks), '/', len(checks))
assert all(checks)
print('workspace_bytes', sum(p.stat().st_size for p in R.rglob('*') if p.is_file()))
