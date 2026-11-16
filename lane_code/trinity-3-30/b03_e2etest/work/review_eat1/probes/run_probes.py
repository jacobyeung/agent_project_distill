import json
import sys
from pathlib import Path

from eat1 import run as R
from eat1.artifact import write_manifest
from eat1.toy.build import build
from eat1.toy.model import MODULES
from probes.variants import make_reader

ROOT = Path(__file__).resolve().parent
WORK = ROOT/'fixture'


def main():
    info = build(WORK, items_per_type=1)
    (WORK/'outside.dat').write_text('2.0\n')
    (WORK/'artifact'/'policy.dat').write_text('{"scale": 0.37}\n')
    write_manifest(WORK/'artifact'/'ARTIFACT.json', WORK/'artifact',
                   {'weights.pt': 'lm', 'policy.dat': 'config'}, MODULES)
    items = [json.loads(line) for line in Path(info['items']).read_text().splitlines()]
    (WORK/'move.jsonl').write_text(json.dumps(items[0])+'\n')
    (WORK/'depth.jsonl').write_text(json.dumps(items[1])+'\n')
    names = sys.argv[1:] or ['round', 'conversion', 'config', 'comparison', 'table', 'lazy',
        'assigned', 'empty', 'readonly', 'readwrite', 'native', 'mapped', 'child', 'rewrite',
        'answer', 'omitted', 'disappear']
    results = {}
    for variant in names:
        if variant == 'memo':
            import torch
            reader = make_reader(WORK, 'memo')
            proof_items = []
            with torch.no_grad():
                for i in range(50):
                    frame = torch.randn(12)
                    memo = reader.model.tower(frame)
                    live = reader.model.tower(frame)
                    proof_items.append(dict(id=i, live=live.tolist(), cached=memo.tolist()))
            (WORK/'memo_proof.json').write_text(json.dumps(dict(
                schema='eat1-cache-proof-v1', items=proof_items)))
        out = ROOT/'results'/variant
        print('PROBE', variant, flush=True)
        R.main(['--reader', 'probes.variants:make_reader', '--reader-kwargs',
                json.dumps(dict(workdir=str(WORK), variant=variant)),
                '--items', str(WORK/('depth.jsonl' if variant == 'memo' else 'move.jsonl')), '--out', str(out),
                '--allowlist-extra', str(ROOT.parent/'eat1/toy/allowlist_toy.json'),
                '--code-root', str(ROOT), '--pythonpath', str(ROOT.parent),
                '--sandbox', '--perturb'])
        report = json.loads((out/'EAT1_REPORT.json').read_text())
        row = json.loads((out/'ITEMS.jsonl').read_text().splitlines()[0])
        results[variant] = dict(overall=report['overall'],
            clauses={k:v['status'] for k,v in report['clauses'].items()},
            output=row['output'], perturbation=report['perturbation'], per_type=report['per_type'])
        print(json.dumps(results[variant]), flush=True)
    (ROOT/'results'/'SUMMARY.json').write_text(json.dumps(results, indent=2)+'\n')


if __name__ == '__main__':
    main()
