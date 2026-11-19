"""Compare per-test outcomes and failure causes of the affected suites, base vs patched."""
from pathlib import Path
import re, json
from collections import Counter
W = Path(__file__).resolve().parent
import sys
SUITE = sys.argv[1] if len(sys.argv) > 1 else 'suite'
LINE = re.compile(r'^(test\w*) \(([\w.]+)\)(?: \(.*\))? \.\.\. (ok|FAIL|ERROR|skipped.*|expected failure|unexpected success)', re.M)
HEAD = re.compile(r'^(FAIL|ERROR): (\S+) \(([^)]+)\)', re.M)
def parse(t):
    out, causes = {}, {}
    for log in sorted((W/SUITE/t).glob('*.log')):
        s = log.read_text(errors='replace')
        for name, cls, res in LINE.findall(s): out[cls+'.'+name] = res.split()[0]
        for blk in re.split(r'^={70}\n', s, flags=re.M)[1:]:
            m = HEAD.match(blk)
            if not m: continue
            last = [l for l in blk.split('-'*70)[1].strip().splitlines() if l.strip()][-1] if '-'*70 in blk else ''
            key = m.group(3)+'.'+m.group(2) if not m.group(2).startswith('tests.') else m.group(2)
            causes.setdefault(key, []).append(re.sub(r'tree_\w+', 'tree_X', last)[:200])
            out.setdefault(key, m.group(1))
        tail = re.findall(r'^(Ran \d+ tests.*|OK.*|FAILED.*)$', s, re.M)
        out['__summary__.'+log.stem] = ' '.join(tail)
    return out, causes
res = {}
for b, c in (('A', 'C'), ('A2', 'C2')):
    ob, cb = parse(b); oc, cc = parse(c)
    tests = sorted(set(ob) | set(oc))
    diff = {k: (ob.get(k), oc.get(k)) for k in tests if ob.get(k) != oc.get(k)}
    cause_diff = {k: (cb.get(k), cc.get(k)) for k in set(cb) | set(cc) if sorted(cb.get(k, [])) != sorted(cc.get(k, []))}
    res[b+'_vs_'+c] = dict(base_outcomes=dict(Counter(v for k, v in ob.items() if not k.startswith('__'))),
                           patched_outcomes=dict(Counter(v for k, v in oc.items() if not k.startswith('__'))),
                           outcome_differences=diff, cause_differences=cause_diff,
                           base_causes=dict(Counter(x for v in cb.values() for x in v).most_common(8)))
(W/('R6_'+SUITE.upper()+'.json')).write_text(json.dumps(res, indent=1)); print(json.dumps(res, indent=1)[:6000])
