"""K1 build7 rehearsal check: the staged depth files resolve exactly as carrier_c1.load_depth_stage1 reads them."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import job_support as H

S, R, NS, J = H.native()
case = Path(sys.argv[1])
ctx = json.loads((case / 'CONTEXT.json').read_text())
root = Path(ctx['stage'])
if ctx['mode'] == 'namespace':
    root = Path(ctx['tmp']) / root.relative_to('/tmp')
cfg = json.loads((HERE / 'packet/CONFIG.json').read_text())
manifest = json.loads((HERE / 'manifest_v2/a40fbc19.json').read_text())
out = dict(case=str(case), mode=ctx['mode'], stage=str(root), files=[])
mapping = {}
for i, item in enumerate(cfg['assets']['depth']):
    phys = NS.physical(root, item['logical_path'])
    row = dict(index=i, logical=item['logical_path'], physical=str(phys), is_file=phys.is_file())
    if phys.is_file():
        digest = H.sha(phys)
        row.update(bytes=phys.stat().st_size, sha256=digest, equals_production_pin=digest == item['sha256'])
    out['files'].append(row)
    mapping[item['logical_path']] = str(phys)
a01 = json.loads((case / 'a01.json').read_text())
out['a01_depth_records'] = {k: v for k, v in a01.items() if k.startswith('depth_')}
verifiers = json.loads((case / 'VERIFIERS.json').read_text())
paths = [d['path'] for d in cfg['assets']['depth']]
out['depth_transport_verifiers'] = [v for v in verifiers if any(p in json.dumps(v['role']) for p in paths)]
gcfg = manifest['gpu']['config']
staged_cfg = NS.physical(root, gcfg['path'])
out['prepared_config'] = dict(path=gcfg['path'], staged=str(staged_cfg), equals_pin=H.sha(staged_cfg) == gcfg['sha256'])
depth_init = json.loads(staged_cfg.read_text())['depth_init']
out['depth_init'] = depth_init
tree = NS.physical(root, cfg['assets']['tree_root'])
sys.path.insert(0, str(tree))
from student_pilot.p3_provenance import load, pinned
import student_pilot.p3_provenance as prov
out['p3_provenance_file'] = prov.__file__
import phase_worker as PW
with PW.metadata_mapping(mapping):
    artifact = load(pinned(depth_init))
    out['carrier_c1_692_pinned_depth_init'] = 'passed'
    out['schema_and_backing_ok'] = (artifact.get('schema') == 'p3-head-artifact-v1'
                                    and artifact.get('feature_backing') == 'decoupled_vc')
    for name, pin in (('encoder_copy.weights', artifact['encoder_copy']['weights']), ('weights', artifact['weights'])):
        row = dict(path=pin['path'], resolves_to_staged_file=Path(pin['path']).is_file(),
                   staged_as=mapping.get(pin['path']))
        try:
            pinned(pin)
            row['pinned'] = 'passed'
        except ValueError as error:
            row['pinned'] = 'raised on stand-in bytes (expected in rehearsal): ' + str(error)[:60]
        out[name] = row
H.dump(case / 'DEPTH_CHECK.json', out)
print(json.dumps(out, indent=1))
