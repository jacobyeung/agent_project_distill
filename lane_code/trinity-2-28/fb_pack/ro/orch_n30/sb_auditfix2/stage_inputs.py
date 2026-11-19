"""Stage the exact local authorities used by the reproducibility tests."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = Path('/scratch/jjyeung/orch_n30')
inputs = {}
def read(path):
    data = path.read_bytes()
    inputs[str(path)] = {'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}
    return data

def copy(source, target):
    data = read(source)
    target.write_bytes(data)
    return {'path': target.name, 'sha256': hashlib.sha256(data).hexdigest()}

read(Path(__file__).resolve())
review = SOURCE/'sb_alrev/REVIEW_VERDICT.md'
copy(review, ROOT/'reference/REVIEW_VERDICT.md')
for name in ('audit.py', 'validate.py', 'enumerate_candidates.py', 'finish_candidates.py', 'recover_k1.py'):
    copy(SOURCE/'sb_alias2/work'/name, ROOT/'reference'/name)
result = json.loads(read(SOURCE/'tree_rebuild10_w/w18/work/build18/proofs/rooms/RESULT.json'))
manifest = {'schema': 'store-room-audit-inputs-v1', 'authority': {}, 'lists': {}}
for name, pin in result['audit_after']['authority'].items():
    actual = copy(Path(pin['path']), ROOT/'inputs/lists'/('authority_'+name+'.raw'))
    assert actual['sha256'] == pin['sha256']
    manifest['authority'][name] = actual
candidates = json.loads(read(SOURCE/'sb_alias2/work/CANDIDATE_SCENES_FINAL.json'))
for name, prefix, field in [('R0','bdb5d402','text'), ('withheld-80','634820b4','rooms'),
                            ('BENCH v2','3119aa4a','physical_groups'), ('dev-S1','969cdb56','physical_groups'),
                            ('K1','4d4736cf','heldout_captures')]:
    source = candidates['list_pins'][prefix]
    actual = copy(Path(source['path']), ROOT/'inputs/lists'/(prefix+'.raw'))
    assert actual['sha256'] == source['sha256']
    manifest['lists'][name] = dict(actual, field=field)
manifest['alias_map'] = copy(SOURCE/'sb_alias2/out/TIERED_ALIAS_MAP.json', ROOT/'inputs/lists/TIERED_ALIAS_MAP.raw')
for name in ('r1_rooms.py','p3_provenance.py','r1_persisted.py','carrier_c1_routing.py'):
    copy(SOURCE/'tree_rebuild10_w/w18/work/tree_r1/student_pilot'/name, ROOT/'inputs/tree_r1/student_pilot'/name)
manifest['inputs'] = inputs
(ROOT/'inputs/lists/manifest.json').write_text(json.dumps(manifest, indent=2, sort_keys=True)+'\n')
(ROOT/'STATUS.md').write_text('The exact w18 Rooms source, its authority files, the five list documents, and the reviewed tiered alias map are staged locally with SHA256 pins. The source audit and helpers are preserved under reference/. Implementation and regression tests are in progress.\n')
print('Staged authorities, lists, alias map, and w18 source.')
