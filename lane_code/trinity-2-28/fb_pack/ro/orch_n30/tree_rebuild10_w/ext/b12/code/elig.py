"""Eligibility of scenes: the kit's own scene filter (student_pilot.s1_exclusions.Exclusions with the sealed dev-S1 969cdb56
and benchmark v2 3119aa4a lists) plus the 80 withheld rooms (634820b4) by alias, canonical and room."""
import sys, json, hashlib, re
sys.path.insert(0, '/scratch/jjyeung/orch_n30/rows_rebuild/work/tree/src')
from student_pilot.s1_exclusions import Exclusions
K = '/scratch/jjyeung/orch_n30/rows_rebuild/work/s0/pull/m/k/'
def pin(p):
    return {'path': p, 'sha256': hashlib.sha256(open(p, 'rb').read()).hexdigest()}
DEV = pin(K + 'dev_scene_exclusions.json'); BEN = pin(K + 'benchmark_scene_exclusions.json')
assert DEV['sha256'].startswith('969cdb56') and BEN['sha256'].startswith('3119aa4a')
WH = '/scratch/jjyeung/orch_n30/rows_rebuild/work/withheld/WITHHELD_ROOMS_80.json'
assert hashlib.sha256(open(WH, 'rb').read()).hexdigest().startswith('634820b4')
class Elig:
    def __init__(self):
        self.ex = Exclusions(DEV, BEN)
        w = json.load(open(WH))
        self.wa = {a for v in w['aliases'].values() for a in v} | set(w['rooms'])
    def reasons(self, alias, canonical=None):
        ds, sc = alias.split('/', 1)
        row = {'dataset': ds, 'scene': sc, 'provenance': {'canonical': canonical} if canonical else {}}
        r = [k for k, v in self.ex.matches(row).items() if v]
        names = {alias}
        if canonical:
            names.add(canonical)
            m = re.match(r'scannet/(scene\d+)_\d+', canonical)
            if m: names.add('scannet/' + m.group(1))
            names.add({'scannet': 'd1', 'scannetppv2': 'd2', 'scannetpp': 'd2', 'arkitscenes': 'd3'}[canonical.split('/')[0]] + '/' + canonical.split('/')[1])
        if names & self.wa: r.append('withheld80')
        return r
if __name__ == '__main__':
    W = '/scratch/jjyeung/orch_n30/b12_cntapp/work/'
    import collections
    am = json.load(open('/scratch/jjyeung/orch_n30/rows_a2/work/alias_map.json')); am.update(json.load(open(W + 'd3_token_map.json')))
    fm = json.load(open(W + 'framemap_scene_frames.json')); pins = json.load(open(W + 'v5_scene_pins.json'))
    e = Elig(); out = {}; c = collections.Counter()
    for a in fm:
        r = e.reasons(a, am.get(a)); out[a] = dict(canonical=am.get(a), inpool=a in pins, nframes=len(fm[a]), excluded=r)
        c[(a[:2], 'pool' if a in pins else 'extra', 'named' if am.get(a) else 'unnamed', ','.join(r) or 'eligible')] += 1
    for k, v in sorted(c.items()): print(k, v)
    json.dump(out, open(W + 'ELIGIBILITY_SCENES.json', 'w'), indent=0)
