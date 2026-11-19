set -euo pipefail; S=/project/community/jjyeung/okh7/813f42db/r7
cat > $S/d2b.py <<'PYEOF'
"""B (room) variant. Login-node reproduction of the pure-Python checks of a/5.py and the GPU path that need no staged
environment. Usage: dry2.py PACKAGE WORKDIR. Prints one JSON report; exit 1 on any failure."""
import ast, hashlib, io, json, runpy, sys, tarfile
from pathlib import Path

P = Path(sys.argv[1]); W = Path(sys.argv[2]); W.mkdir(mode=0o700, exist_ok=True)
sha = lambda b: hashlib.sha256(b).hexdigest()
R = {}; bad = []
def check(name, ok, detail=None):
    R[name] = dict(ok=bool(ok), **({'detail': detail} if detail is not None else {}))
    if not ok: bad.append(name)

pub = json.loads((P/'0.json').read_text()); pk = json.loads((P/'PACKAGE.json').read_text())
payload = (P/'0.tgz').read_bytes()
# a/5.py main, before stage
check('5.payload_sha', sha(payload) == pub['payload_sha256'])
check('5.package_descriptor', all(sha((P/n).read_bytes()) == h for n, h in pk['files'].items()))
check('5.sequence_is_a6', pk['files']['a/6.py'] == sha((P/'a/6.py').read_bytes()))
with tarfile.open(fileobj=io.BytesIO(payload)) as t:
    pay = {m.name: t.extractfile(m).read() for m in t.getmembers() if m.isfile()}
for n, d in pay.items():
    if n.startswith('orchard_h10/'):
        f = W/'pay'/n; f.parent.mkdir(parents=True, exist_ok=True); f.write_bytes(d)
sys.path.insert(0, str(W/'pay'))
cfg = json.loads(pay['9.json'])
check('5.plan_sha', sha(json.dumps(cfg, sort_keys=True, separators=(',', ':')).encode()) == pub['plan_sha256'])
for rel, pin in cfg['payload_pins'].items():
    if sha(pay[rel]) != pin['sha256']: bad.append('payload_pin ' + rel)
check('stage.payload_pins', not [b for b in bad if b.startswith('payload_pin')], len(cfg['payload_pins']))
inputs = json.loads((P/'a/1.json').read_text())
from orchard_h10 import export_pins
try:
    pins = export_pins.load(inputs, P); check('5.export_pins_load_validate', True)
except Exception as e:
    pins = json.loads((P/'a/export.json').read_text()); check('5.export_pins_load_validate', False, repr(e))
check('prepare.no_optional', not inputs.get('optional'))
check('prepare.types_room', inputs.get('types') == ['room_size_estimation'], inputs.get('types'))
# stage slot 5: preparation files must exist under d/ (else prepare falls back to the 544 META copies and refuses)
prep_arch = inputs['archives'][-1]
raw = Path(prep_arch['parts'][0]['path']).read_bytes()
with tarfile.open(fileobj=io.BytesIO(raw)) as t:
    prep = {m.name: t.extractfile(m).read() for m in t.getmembers()}
want = {s['path']: s for s in pins['preparation'].values()}
check('prepare.prep_members', set(prep) == set(want), sorted(prep))
check('prepare.prep_pins', all(sha(prep[p]) == s['sha256'] and len(prep[p]) == s['bytes'] for p, s in want.items() if p in prep))
check('prepare.prep_vs_binding', all(pins['preparation'][k]['sha256'] == v for k, v in cfg['export_binding']['preparation_sha256'].items()))
check('admit.export_binding', all(pins.get(k) == cfg['export_binding'][k] for k in ('run', 'step', 'member_directory', 'lineage', 'object')))
check('admit.archive0', pins.get('archive_sha256') == inputs['archives'][0]['sha256'] == '795ef9ef7e59bf37443c14a4d3a7e734eabcb2fd5fcb289ad3d77ae7096e283b')
# stage policy scripts against ORCHARD_ASSETS, read from the a3.tar slot
assets = json.loads(pay['orchard_h10/vendor/ORCHARD_ASSETS.json'])
a3 = [a for a in inputs['archives'] if a['sha256'].startswith('05dc8f79')]
check('stage.a3_slot_present', len(a3) == 1)
with tarfile.open(a3[0]['parts'][0]['path']) as t:
    q = {m.name.lstrip('./'): t.extractfile(m).read() for m in t.getmembers() if m.isfile()}
check('stage.vnice_sha', sha(q['q/vnice.sh']) == assets['vnice_sha256'])
check('stage.terminator_sha', sha(q['q/terminator.sh']) == assets['terminator_sha256'])
pol = json.loads(q['q/policy.json'])
check('stage.policy_receipt', pol.get('vnice') == inputs['policy']['vnice'] and pol.get('terminator') == inputs['policy']['terminator'] and pol.get('authorized') is True)
env = json.loads(q['q/env.json'])
R['prepare.env_receipt_versions'] = dict(ok=True, detail=env.get('versions'))
# bundle guard (a/5.py check_bundle_guard) and bundle 0.py
batch = (P/'BATCH.sh').read_text()
lines = [l for l in batch.splitlines() if l.startswith('b=bytes.fromhex(')]
braw = bytes.fromhex(ast.literal_eval(ast.parse(lines[0]).body[0].value.args[0]))
with tarfile.open(fileobj=io.BytesIO(braw)) as t:
    bm = {m.name: t.extractfile(m).read() for m in t.getmembers()}
check('guard.inventory', len(lines) == 1 and set(bm) == {'0.py', '0.json', '7.py'})
check('guard.descriptor', json.loads(bm['0.json']) == pub)
check('guard.operator', bm['7.py'] == (P/'a/6.py').read_bytes())
check('guard.tmp_token', ("'a'+j+%r" % pub['token']) in batch)
# post-prepare settings check in a/5.py and a/6.py prepare (settings come from 9.json via prepare.run)
s = dict(stage1_select_rule=cfg.get('stage1_select_rule', 'null_argmax'), perception_memo=cfg.get('perception_memo', 'off'),
         perception_memo_modules=cfg['perception_memo_modules'], perception_memo_verify_ids=cfg.get('perception_memo_verify_ids', []))
s['types'] = inputs.get('types')
check('5.settings_rule', s['stage1_select_rule'] == 'candidates_argmax' and s['perception_memo'] == 'on'
      and s['types'] == ['room_size_estimation'] and s['perception_memo_modules'] == ['g3t'] and s['perception_memo_verify_ids'] == [], s)
op = runpy.run_path(str(P/'a/6.py'), run_name='dry')
check('6.rule_in_RULES', s['stage1_select_rule'] in op['RULES'])
d = op['descriptors'](str(P))
check('6.descriptor', len(d) == 1 and d[0]['stage1_select_rule'] == 'candidates_argmax' and d[0]['perception_memo'] == 'on' and d[0]['expected'] == 134 and d[0]['types'] == [4])
mem = op['memory_bound']()
check('6.memory_fits', mem['fits'] is True and mem['basis'] == 'fixed_g3t_shapes' and mem['sam_measurement_required'] is False)
items = json.loads(pay['items/room134.json'])['items']
from collections import Counter
c = Counter(r['question_type'] for r in items)
check('6.items_134', sum(c.values()) == 134 and c['room_size_estimation'] == 134, dict(c))
check('6.full_reader_items_in_payload', all(n in pay for n in ('items/room134.json',)))
# GPU submission path (8.py submit -> BATCH.sh -> bundle 0.py -> job.main): pins it reads
check('sub.job_name', ("a15_cot_ap" + pub['token']) in json.loads((P/'2.json').read_text())['argv'][-1] if (P/'2.json').exists() else False)
R['failed'] = bad; R['passed'] = not bad
print(json.dumps(R, indent=1, sort_keys=True))
sys.exit(0 if not bad else 1)
PYEOF
P=/project/community/jjyeung/okh7/a15_cot_apd50ba921ef1f4
/usr/bin/python3 -c "import json;d=json.load(open('$S/dry_B.out'));print('DRY_B',d['passed'],d['problems'],[(a['slot'],a['sha256'],a['parts']) for a in d['archives']],d['resolved_slot'])"
/usr/bin/python3 -I -s -B $S/d2b.py $P $S/w2B > $S/dry2_B.out 2>&1; echo rc=$?; /usr/bin/python3 -c "import json;d=json.load(open('$S/dry2_B.out'));print('FAILED',d['failed']);print({k:v for k,v in d.items() if k not in ('failed','passed') and not v['ok']})"
