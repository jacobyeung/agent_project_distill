"""Bind exact Orchard output bytes; derive locally with explicit fixture authority."""
import copy, json, sys
from pathlib import Path
H = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(H/'tools'), str(H/'build/tree'), str(H/'build/fx/b')]
import derive_kit_h1 as dk
from student_pilot.carrier_c1_run import validate
from d import contract
def load(p): return json.loads(p.read_text())
w = dk.write
before = H/'evidence/fix8_before'
ids = load(before/'ids.json')
over = load(before/'build/over_local.json')
e = H/'evidence/fix7_selection/orchard_equal_6c18a2bf/o'
assert dk.sha(e/'r.json') == 'eac5f9f01587803b2402f80cc310b75ec1f960270a6bc059416b1e1407b1e7c9'
assert dk.sha(e/'q.json') == 'e48ab85bb9364aab228da7b23033605935e384761f76b0e6527c5e221b1c14b4'
pins = {}
for src in ('r.json', 'q.json'):
    p = H/'payload'/('d_'+dk.sha(e/src)[:16]+'.json')
    p.write_bytes((e/src).read_bytes())
    pins[src] = dict(path=str(p), sha256=dk.sha(p))
over['add_k'].pop('pool_selection_aa128e6f.json')
name = 'pool_selection_eac5f9f0.json'
over['add_k'][name] = pins['r.json']
over['add_k']['selection_equality.json'] = pins['q.json']
over['selection_equality'] = pins['q.json']
route = over['config']['s1_routing']
route['selection'] = dict(path=dk.KIT_LOGICAL+name, sha256=pins['r.json']['sha256'])
route['catalog'].pop(dk.SELECTION_REFERENCE)
route['catalog'][pins['r.json']['sha256']] = route['selection']['path']
dk.validate_selection_equality(over)
oldlaunch = load(H/'build/fx_seed/k/launch.json')
cfg = load(H/'build/fx_seed'/oldlaunch['config']['file'])
cfg['s1_routing'].update(copy.deepcopy(route))
validate(cfg)
ident = dk.identity(cfg)
cont = dk.digest(contract(oldlaunch, cfg))
assert cont == ids['contract']
for n in ('4.json', 'review.json', 'staging.json'):
    v = load(before/'payload'/n)
    v['config_sha256'] = ident
    if 'admission_contract_sha256' in v: v['admission_contract_sha256'] = cont
    w(H/'payload'/n, v)
    over['add_k'][n] = dict(path=str(H/'payload'/n), sha256=dk.sha(H/'payload'/n))
for n in ('over_local.json', 'over_seed.json'): w(H/'build'/n, over)
w(H/'build/over_fx.json', dict(over, fixture=True))
# This retained source is incomplete and explicitly marked FIXTURE. Never change
# the shipped deriver's production authority or claim a production launch here.
fixture = H/'evidence/derivation/empty'
authority = dk.SEALED_MANIFEST
try:
    dk.SEALED_MANIFEST = dk.sha(fixture/'SHA256SUMS.txt')
    dst = H/'build/fx'
    if dst.exists(): dst.rename(H/'build/fx_r7')
    result = dk.derive(fixture, dst, dict(over, fixture=True))
finally:
    dk.SEALED_MANIFEST = authority
actual = load(dst/'k'/(result['config_key']+'.json'))
validate(actual)
assert dk.identity(actual) == ident and actual['s1_routing']['selection'] == route['selection']
remote = load(before/'payload/over.json')
remote['config']['s1_routing'] = route
remote['add_k'] = copy.deepcopy(over['add_k'])
for pin in remote['add_k'].values(): pin['path'] = '/project/community/jjyeung/okh7/i_1be16f28/'+Path(pin['path']).name
remote['selection_equality'] = remote['add_k']['selection_equality.json']
w(H/'payload/over.json', remote)
ids.update(identity=ident, contract=cont, config_key=result['config_key'], fixture_manifest=result['manifest_sha256'])
w(H/'ids.json', ids)
w(H/'evidence/fix8_admission/derivation.json', dict(result, production_source_manifest=authority,
    local_fixture_manifest=dk.sha(fixture/'SHA256SUMS.txt'), selection=pins['r.json'], equality=pins['q.json']))
assert (H/'payload/jb.sh').read_bytes() == (before/'payload/jb.sh').read_bytes()
assert (H/'EXPORT_OBJECTS.txt').read_bytes() == (before/'EXPORT_OBJECTS.txt').read_bytes()
print(json.dumps(ids, indent=2))
