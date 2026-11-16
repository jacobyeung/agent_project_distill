"""Print one trend table per set (dev twins, ReVSI backward) over every milestone in out/m*/."""
import glob, json, os, re
OUT = os.environ.get('OUTROOT') or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'out')
for kind, title in (('dev', 'dev twins (150)'), ('revsi', 'ReVSI backward (33)')):
    rows = []
    for p in glob.glob(f'{OUT}/m*/{kind}*.summary.json'):
        s = json.load(open(p)); step = int(re.search(r'/m(\d+)/', p).group(1))
        rows.append((step, s))
    if not rows: continue
    print(f'### {title}: away classes by milestone\n')
    print('| step | level | n | a | b | c | d | e | f |\n|---|---|---|---|---|---|---|---|---|')
    for step, s in sorted(rows, key=lambda x: x[0]):
        for lv, c in list(s['by_level'].items()) + [('all', dict(s['overall'], n=s['n']))]:
            print(f"| {step} | {lv} | {c['n']} | " + ' | '.join(str(c.get(k, 0)) for k in 'abcdef') + ' |')
    print()
