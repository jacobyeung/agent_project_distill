"""Run from R: python -B -m probes_r3.run_probes NAME ..."""
import json
import sys
from pathlib import Path
from eat1 import run
from eat1.toy.adversarial import build_adversarial

ROOT = Path(__file__).resolve().parent


def main():
    fixture = ROOT/'fixture'
    if not (fixture/'move.jsonl').exists():
        build_adversarial(fixture)
    for name in sys.argv[1:]:
        out = ROOT/'results'/name
        extra = []
        if name == 'relu6':
            allow = ROOT/'allow_relu6.json'
            allow.write_text(json.dumps({'declared_constants': [dict(file='probes_r3/variants.py',
                function='ReLU6Head.forward', value=6, reason='ReLU6 activation bound; an architecture constant, not a fitted policy.')]}))
            extra = ['--allowlist-extra', str(allow)]
        run.main(['--reader', 'probes_r3.variants:make_reader', '--reader-kwargs',
                  json.dumps(dict(workdir=str(fixture), variant=name)), '--items', str(fixture/'move.jsonl'),
                  '--out', str(out), '--allowlist-extra', str(ROOT.parent/'eat1/toy/allowlist_toy.json'),
                  '--sandbox', '--perturb', '--code-root', str(ROOT)]+extra)
        report = json.loads((out/'EAT1_REPORT.json').read_text())
        item = json.loads((out/'ITEMS.jsonl').read_text())
        print(json.dumps(dict(name=name, overall=report['overall'], claim_grade=report['claim_grade'],
            output=item['output'], failures={k: c['offenders'] for k, c in report['clauses'].items()
                                            if c['status'] != 'PASS'})), flush=True)


if __name__ == '__main__':
    main()
