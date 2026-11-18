"""SIZE_UNITS_DEV_S1.json: the unit each dev-S1 object-size question asks for (metric or imperial), from the question text
of the D0 m100 main journals (rule of h1size.py / pr_data.py: first unit word found; then a bare cm, mm or m token).
usage: build_size_units.py OUT.json"""
import glob, hashlib, json, re, sys
C = '/scratch/jjyeung/orch_n30/cont_ops/work'
J = sorted(glob.glob(C + '/h1read/kit/build/af35386aa3e/fetched/x/main/a0/results/budget_2048/*/items_a0.jsonl'))
U = [('centimet', 'cm'), ('millimet', 'mm'), ('meter', 'm'), ('metre', 'm'), ('inch', 'in'), ('feet', 'ft'), ('foot', 'ft'), ('yard', 'yd')]
KIND = dict(cm='metric', mm='metric', m='metric', **{'in': 'imperial', 'ft': 'imperial', 'yd': 'imperial'})
out = {}
for f in J:
    for l in open(f):
        d = json.loads(l)
        if d.get('question_type') != 'object_size_estimation':
            continue
        q = d['question'].lower(); u = None
        for k, v in U:
            if k in q:
                u = v; break
        else:
            for v in ('cm', 'mm', 'm'):
                if re.search(r'\b%s\b' % v, q):
                    u = v; break
        if u is None:
            raise SystemExit('no unit in ' + d['id'])
        if out.setdefault(d['id'], KIND[u]) != KIND[u]:
            raise SystemExit('unit differs across journals ' + d['id'])
src = {f: hashlib.sha256(open(f, 'rb').read()).hexdigest() for f in J}
x = dict(schema='pooled-rule-size-units-v1', rule=__doc__.split('\n')[0], sources=src, items=out,
         counts={k: sum(1 for v in out.values() if v == k) for k in ('metric', 'imperial')})
s = json.dumps(x, indent=1, sort_keys=True) + '\n'
open(sys.argv[1], 'w').write(s)
print(x['counts'], hashlib.sha256(s.encode()).hexdigest())
