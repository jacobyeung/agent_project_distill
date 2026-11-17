import json
import sys
from pathlib import Path

from eat1.run import main
from eat1.toy.adversarial import build_adversarial

ROOT = Path(__file__).resolve().parent
work = ROOT / 'fixture'
if not (work / 'move.jsonl').exists():
    build_adversarial(work)
for variant in sys.argv[1:]:
    out = ROOT / 'results' / variant
    items = work / ('items.jsonl' if variant in ('shared_heads', 'two_item_control') else 'move.jsonl')
    if variant == 'shared_heads_depth':
        items = work / 'depth.jsonl'
    main(['--reader', 'probes_r5.variants:make_reader', '--reader-kwargs',
          json.dumps(dict(workdir=str(work), variant=variant)), '--items', str(items),
          '--out', str(out), '--allowlist-extra', str(ROOT.parent/'eat1/toy/allowlist_toy.json'),
          '--code-root', str(ROOT), '--sandbox', '--perturb'])
    report = json.loads((out/'EAT1_REPORT.json').read_text())
    item = json.loads((out/'ITEMS.jsonl').read_text().splitlines()[0])
    print(json.dumps(dict(variant=variant, overall=report['overall'], claim_grade=report['claim_grade'],
                         clauses={k:v['status'] for k,v in report['clauses'].items()},
                         offenders={k:v['offenders'] for k,v in report['clauses'].items() if v['status'] != 'PASS'},
                         output=item['output'])), flush=True)
