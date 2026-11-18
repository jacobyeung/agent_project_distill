"""R0 exposure check of the unit rows bound on vehicle P (units_p_slice_v3 rows.jsonl): same resolver as r0_exposure.py."""
import json, re, hashlib, collections
EV = '/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/b10_reserve/'
P = '/scratch/jjyeung/orch_n30/rows_r1/out/units_p_slice_v3/rows.jsonl'
r0 = [l.strip() for l in open(EV + 'R0_ROOMS.txt') if l.strip()]
native = {r.split('/', 1)[1]: r for r in r0}
HEX = re.compile(r'(?<![0-9a-f])[0-9a-f]{10}(?![0-9a-f])')
SCN = re.compile(r'scene\d{4}')
amap = {}
for p in ('/scratch/jjyeung/orch_n30/rows_a2/work/alias_map.json', '/scratch/jjyeung/orch_n30/b12_cntapp/work/d3_token_map.json'):
    amap.update(json.load(open(p)))
for k, v in json.load(open('/scratch/jjyeung/orch_n30/b12_cntapp/work/ELIGIBILITY_SCENES.json')).items():
    if v.get('canonical'):
        amap.setdefault(k, v['canonical'])
n = 0
hits = []
how = collections.Counter()
first = None
for line in open(P):
    if not line.strip():
        continue
    r = json.loads(line)
    n += 1
    if first is None:
        first = {k: (v if len(json.dumps(v)) < 120 else json.dumps(v)[:120] + '...') for k, v in r.items()}
    alias = str(r.get('dataset')) + '/' + str(r.get('scene'))
    can = amap.get(alias)
    text = can if can else json.dumps({k: v for k, v in r.items() if k not in ('target', 'student_input')})
    how['alias_map' if can else 'raw_text'] += 1
    for tok in set(HEX.findall(text)) | set(SCN.findall(text)):
        if tok in native:
            hits.append(dict(row=n, room=native[tok]))
out = dict(path=P, sha256=hashlib.sha256(open(P, 'rb').read()).hexdigest(), rows=n, resolved_by=dict(how), r0_hits=len(hits), hits=hits[:10], first_row=first)
json.dump(out, open('R0_EXPOSURE_UNITS_P.json', 'w'), indent=1)
print(json.dumps(out)[:1800])
