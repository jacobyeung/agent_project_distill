"""Run with python -B -m probes_r2.run_probes [variant ...]."""
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
    extra = ROOT/'allow.json'
    extra.write_text(json.dumps({'native_units': {'cm': 'Head output has native centimetre units.'}}))
    for name in sys.argv[1:] or ['numeric', 'printf', 'integer', 'instance', 'class_policy', 'units',
                                'direct', 'bookkeeping', 'native_units', 'answer_work', 'clamp', 'permute',
                                'constructor_table', 'local_threshold', 'fields', 'empty_trace']:
        out = ROOT/'results'/name
        options = []
        variant = name
        if name == 'empty_trace':
            variant = 'printf'
            empty = ROOT/'empty.log'
            empty.write_text('')
            options = ['--strace-log', str(empty)]
        run.main(['--reader', 'probes_r2.variants:make_reader', '--reader-kwargs',
                  json.dumps(dict(workdir=str(fixture), variant=variant)), '--items', str(fixture/'move.jsonl'),
                  '--out', str(out), '--allowlist-extra', str(ROOT.parent/'eat1/toy/allowlist_toy.json'),
                  '--allowlist-extra', str(extra), '--sandbox', '--perturb', '--code-root', str(ROOT)]+options)
        report = json.loads((out/'EAT1_REPORT.json').read_text())
        item = json.loads((out/'ITEMS.jsonl').read_text())
        summary = dict(name=name, overall=report['overall'], claim_grade=report['claim_grade'],
                       output=item['output'], failures={k: c['offenders'] for k, c in report['clauses'].items()
                                                       if c['status'] != 'PASS'})
        print(json.dumps(summary), flush=True)


if __name__ == '__main__':
    main()
