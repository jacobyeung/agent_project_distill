"""Login-node reproduction of the pure-Python checks of a/5.py and the GPU path that need no staged
environment. Usage: dry_own.py PACKAGE WORKDIR. Python 3.6 stdlib only.
Adapted from dry2.py for the tower-and-own camera operator."""
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
# The filled staging input retains the five-type payload inventory. The operator
# selects only its three camera types below.
check('prepare.types_all_five', inputs.get('types') == cfg['order'], inputs.get('types'))
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
import re as _re
_rev = _re.search(r"^REVIEWED_ARCHIVE_SHA256 = '([0-9a-f]{64})'$", (P/'a/4.py').read_text(), _re.M).group(1)
check('admit.archive0', pins.get('archive_sha256') == inputs['archives'][0]['sha256'] == _rev, _rev[:8])
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
check('5.settings_rule', s['stage1_select_rule'] == 'candidates_argmax' and s['perception_memo'] == 'on'
      and s['perception_memo_modules'] == ['g3t'] and s['perception_memo_verify_ids'] == [], s)
op = runpy.run_path(str(P/'a/6.py'), run_name='dry')
check('6.rule_in_RULES', s['stage1_select_rule'] in op['RULES'])
d = op['descriptors'](str(P))
check('6.descriptor', d == [dict(arms=['tower', 'own'], modes=['none'],
      stage1_select_rule='candidates_argmax', save_own_depth=False,
      perception_memo='on', perception_memo_modules=['g3t'],
      perception_memo_verify_ids=[], types=[0, 1, 2], expected=900)])
mem = op['memory_bound']()
check('6.memory_fits', mem['fits'] is True and mem['basis'] == 'fixed_g3t_shapes' and mem['sam_measurement_required'] is False)
items = json.loads(pay['items/devs1_routed.json'])['items']
from collections import Counter
c = Counter(r['question_type'] for r in items)
camera = ['camera_displacement', 'camera_rotation', 'camera_movement_direction']
selected = [r for r in items if r['question_type'] in camera]
check('6.items_450_reads_900', len(selected) == len(set(r['id'] for r in selected)) == 450
      and all(c[k] == 150 for k in camera) and len(selected)*len(d[0]['arms']) == d[0]['expected'] == 900, dict(c))
check('6.types_order', d[0]['types'] == [0, 1, 2] and [cfg['order'][t] for t in d[0]['types']] == camera)
check('6.schedule', op['SCHEDULE'] == ((0, 0), (0, 1), (0, 2)))
# Execute the real prepare and worker_args functions without loading model code.
# Only MODES and settings are needed from perception_memo; both are pure stdlib.
import types
memo_ast = ast.parse(pay['b/e2e_reader/perception_memo.py'].decode())
memo_ast.body = [n for n in memo_ast.body if
    (isinstance(n, ast.FunctionDef) and n.name == 'settings') or
    (isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'MODES' for t in n.targets))]
memo = types.ModuleType('e2e_reader.perception_memo')
exec(compile(memo_ast, 'perception_memo.settings', 'exec'), memo.__dict__)
sys.modules['e2e_reader'] = types.ModuleType('e2e_reader')
sys.modules['e2e_reader.perception_memo'] = memo
settings_path = W/'settings.json'; settings_path.write_text(json.dumps(s))
item_path = W/'items.json'; item_path.write_bytes(pay['items/devs1_routed.json'])
config = dict(package=str(W/'pay'), output=str(W/'workers'), settings=str(settings_path),
    plan_sha256=pub['plan_sha256'], inputs_sha256=sha((P/'a/1.json').read_bytes()),
    operator_sha256=sha((P/'a/6.py').read_bytes()), export_pin=str(P/'a/export.json'),
    export='dry-export', binding='dry-binding', items=str(item_path))
configs = op['prepare'](config)
from orchard_h10.runner import control, worker_args
workers = []
for i, worker in sorted(configs.items()):
    control(worker)
    check('6.worker_config_%d' % i, worker['types'] == camera and worker['arms'] == ['tower', 'own']
          and worker['modes'] == ['none'] and worker['single_worker'] is False)
    for t, kind in enumerate(camera):
        args = worker_args(dict(config=worker, type=t, index=0, cards=1, stop_at=1, finish_by=2))
        arg = lambda name: args[args.index(name)+1]
        check('6.worker_%d_%d' % (i, t), arg('--types') == kind and arg('--arms') == 'tower,own'
              and arg('--modes') == 'none' and arg('--shard') == '0/1' and '--type-journals' not in args
              and arg('--out') == str(Path(worker['output'])/'metadata/journals'/str(t)/'0')
              and arg('--stop-file') == str(W/'workers/metadata/STOP'))
        workers.append((i, t))
check('6.per_type_workers', workers == list(op['SCHEDULE']))
# GPU submission path (8.py submit -> BATCH.sh -> bundle 0.py -> job.main): pins it reads
check('sub.job_name', ("a15_cot_ap" + pub['token']) in json.loads((P/'2.json').read_text())['argv'][-1] if (P/'2.json').exists() else False)
R['failed'] = bad; R['passed'] = not bad
print(json.dumps(R, indent=1, sort_keys=True))
sys.exit(0 if not bad else 1)
