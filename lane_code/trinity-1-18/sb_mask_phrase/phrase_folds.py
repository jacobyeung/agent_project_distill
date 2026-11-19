"""out/PHRASE_FOLDS.json from out/DECISION.json (bash run.sh phrase_folds.py): the chosen arm's policy per fold and name.
Other kits price each row under the policy of the fold that held its room out; PHRASE_SET.json is the all-room refit."""
import hashlib, json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE/'out'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    decision = json.loads((OUT/'DECISION.json').read_text())
    names = [p['name'] for p in json.loads((OUT/'PHRASE_SET.json').read_text())['names']]
    arm = decision['chosen_arm']
    changed = decision['fold_choices'][arm] if arm else {}
    rows = []
    for fold in ['0', '1', '2', '3', '4']:
        for n in sorted(names):
            v = changed.get(fold, {}).get(n, 'raw')
            phrase = n if v == 'raw' else v.split(':', 1)[1]
            rows.append(dict(fold=int(fold), name=n, policy=v, phrases=[phrase] if v == 'raw' or v.startswith('q:') else [n, phrase]))
    out = dict(arm=arm, rule='the part 1 fold rule on the other four folds (DECISION.json fold_evidence)', folds=rows,
               changed=[r for r in rows if r['policy'] != 'raw'], bars_sha256=decision['bars_file']['sha256'],
               input_sha256={str(OUT/'DECISION.json'): sha(OUT/'DECISION.json'), str(OUT/'PHRASE_SET.json'): sha(OUT/'PHRASE_SET.json'),
                             str(HERE/'phrase_folds.py'): sha(HERE/'phrase_folds.py')})
    (OUT/'PHRASE_FOLDS.json').write_text(json.dumps(out, indent=1)+'\n')
    print(len(rows), [(r['fold'], r['name'], r['policy']) for r in out['changed']])


if __name__ == '__main__':
    main()
