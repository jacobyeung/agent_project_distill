"""Snapshot bounded local evidence; never import or write into another lane."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
W = Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w')
KIT = Path('/scratch/jjyeung/orch_n30/sb_records/out/kit/inputs')
inputs = {}

def copy(src, label, expected=None):
    src = Path(src)
    raw = src.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    if expected:
        assert sha == expected, (src, sha, expected)
    dest = ROOT / 'work' / label
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(raw)
    inputs[label] = dict(path=str(src), sha256=sha, bytes=len(raw), snapshot=str(dest.relative_to(ROOT)))
    return dest

sealpath = copy(W/'w20/out/TREE_SEAL.json', 'inputs/tree_seal.json')
seal = json.loads(sealpath.read_text())
assert seal['tree_sha256'].startswith('780ca7b4')
copy(W/'w21/out/TREE_SEAL.json', 'inputs/w21_inherited_seal.json')
for name in ('carrier_c1_run.py', 'c1_pose_mix.py', 's1_exclusions.py', 's1_scene_census.py',
             'carrier_c1_routing.py', 'carrier_c1_sweep.py', 'p3_provenance.py',
             'r1_persisted.py', 'r0_exclusion.py', 'r0_scenes.json', 'r1_rooms.py',
             'r1_routing.py', 'r1_population.py', 'r1_training.py', 'r2_policy.py'):
    copy(W/'w20/work/tree_r1/student_pilot'/name, 'code/student_pilot/'+name,
         seal['files']['student_pilot/'+name])
(ROOT/'work/code/student_pilot/__init__.py').write_text('')
copy(W/'w20/work/build20/inputs/config.json', 'inputs/config_b20.json')
copy(W/'w20/work/n1fix2/inputs/config.json', 'inputs/config_n1fix2.json')
prefixes = dict(mix='8957d119', a2_receipt='30612832', a3_receipt='1e7b491b',
                a2_projection='84a3fab0', a3_projection='31582e35', benchmark='3119aa4a',
                dev='a1869ae2', p_receipt='0664bb17', p_mix_order='d8d33340',
                p_scene_order='3cb1ccf5', source_attestation='773ba292', eval_rooms='267efeb1')
for label, prefix in prefixes.items():
    matches = list(KIT.glob(prefix+'*'))
    assert len(matches)==1, (label, matches)
    p=matches[0]
    copy(p, 'inputs/'+label+(''.join(p.suffixes) if label.endswith('projection') else p.suffix), p.name.split('_')[0])
copy(W/'ext/preceipts/rc3/SHA256SUMS.txt', 'inputs/P_SHA256SUMS.txt')
for label, rel in [('a2_receipt_rc3','a2v3/receipt.json'),('a3_receipt_rc3','a3v2/receipt.json'),('division','a3v2/division.json')]:
    copy(W/'ext/preceipts/rc3/u/ap/f02f16ad/s'/rel, 'inputs/'+label+'.json')
for label, src in [('review','/scratch/jjyeung/orch_n30/sb_recrev/REVIEW_VERDICT.md'),
                   ('review_numbers','/scratch/jjyeung/orch_n30/sb_recrev/notes/recrev_out.json'),
                   ('framepool','/scratch/jjyeung/orch_n30/sb_framepool/out/FPJOIN.json'),
                   ('receipt_graph','/scratch/jjyeung/orch_n30/sb_records/out/RECEIPT_GRAPH.json')]:
    copy(src, 'inputs/'+label+Path(src).suffix)
cap=W/'w21/work/build21/proofs/capacity'
for label,rel in [('fixture_receipt','400/p_prepare/receipt.json'),('fixture_order','400/p_prepare/pose_scene_order.json'),
                  ('fixture_mix','pose.json')]:
    copy(cap/rel,'inputs/'+label+'.json')
manifest = dict(inputs=inputs, command='python3 work/stage.py',
                script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
(ROOT/'work/SNAPSHOT.json').write_text(json.dumps(manifest, indent=2)+'\n')
(ROOT/'STATUS.md').write_text('Stage 2: The copied pose-filter code matches every build-20 seal pin. Both full raw SQLite stores are MISSING in the supplied recovery; their complete scene projections and attested original hashes are present. The only build-21 pose order found binds capacity-test stores, not receipt 8957d119. The CPU proof will evaluate N’s mandatory scene filter on all projected raw rows and keep the exact production order hash MISSING.\n')
print('Snapshotted',len(inputs),'inputs; sealed tree',seal['tree_sha256'])
