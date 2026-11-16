import json
import sys
from pathlib import Path

from eat1.run import main
from eat1.toy.adversarial import build_adversarial
from eat1.artifact import write_manifest
from eat1.toy.model import MODULES

ROOT = Path(__file__).resolve().parent
for variant in sys.argv[1:]:
    work = ROOT/('unprojection_fixture' if variant.startswith('unproject_') else 'fixture')
    if not (work/'move.jsonl').exists():
        build_adversarial(work)
        if variant.startswith('unproject_'):
            write_manifest(work/'artifact/ARTIFACT.json', work/'artifact', {'weights.pt': 'lm'},
                           dict(MODULES, unproject=dict(role='fixed_math', name='unproject')))
    out = ROOT/'results'/variant
    main(['--reader', 'probes_r4.variants:make_reader', '--reader-kwargs',
          json.dumps(dict(workdir=str(work), variant=variant)), '--items', str(work/'move.jsonl'),
          '--out', str(out), '--allowlist-extra', str(ROOT.parent/'eat1/toy/allowlist_toy.json'),
          '--code-root', str(ROOT), '--sandbox', '--perturb'])
    report = json.loads((out/'EAT1_REPORT.json').read_text())
    print(json.dumps(dict(variant=variant, overall=report['overall'], claim_grade=report['claim_grade'],
                         clauses={k:v['status'] for k,v in report['clauses'].items()},
                         offenders={k:v['offenders'] for k,v in report['clauses'].items() if v['status'] != 'PASS'})),
          flush=True)
