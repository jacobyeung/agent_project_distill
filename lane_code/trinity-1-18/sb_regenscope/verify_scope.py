"""Verify scope artifacts and provenance without executing dataset generators."""
from pathlib import Path
import collections
import hashlib
import json

root = Path(__file__).resolve().parent
report_path = root/'out/REGEN_SCOPE.json'
x = json.loads(report_path.read_text())
md = (root/'out/REGEN_SCOPE.md').read_bytes()
assert len(md.splitlines()) == x['report_lines'] <= 60
assert hashlib.sha256(md).hexdigest() == x['report_sha256']
for p, pin in x['input_sha256'].items():
    h = hashlib.sha256()
    size = 0
    with Path(p).open('rb') as f:
        for block in iter(lambda: f.read(1024*1024), b''):
            h.update(block)
            size += len(block)
    assert (h.hexdigest(), size) == (pin['sha256'], pin['bytes']), p
rasters = [r for group in x['rasters']['groups'].values() for r in group]
assert len(rasters) == len({r['expected_mirror'] for r in rasters}) == 307
assert all(r['pin_matches_v3'] and len(r['sha256']) == 64 for r in rasters)
assert collections.Counter(r['dataset'] for r in rasters) == {'scannet': 80, 'scannetppv2': 227}
packs = x['direction_packs']
assert len(packs) == len({p['expected_path'] for p in packs}) == 11
assert sum(p['affected_rows'] for p in packs) == 93370
assert sum(p['pinned_sha256'] is not None for p in packs) == 8
scenes = set()
for p in packs:
    assert p['affected_scenes'] == sorted(set(p['affected_scenes']))
    assert len(p['affected_scenes']) == p['affected_scene_count']
    assert collections.Counter(s.split('/')[0] for s in p['affected_scenes']) == p['dataset_scene_counts']
    assert p['unresolved_canonical_rows'] == 0
    if p['pinned_sha256']:
        assert Path(p['expected_path']).name.startswith(p['pinned_sha256'][:16])
    scenes.update(p['affected_scenes'])
assert sorted(scenes) == x['direction_unique_affected_scenes']
assert len(scenes) == x['direction_unique_affected_scene_count'] == 1979
consumer = next(v for p, v in x['generators']['VSTI_row_consumer']['files'].items() if p.endswith('/generate.py'))
assert consumer['sha256'] == 'fceb45e6bee7aff7d8c4b388cdf0caf269c1141b42d06c24c6833d23afabcb88'
result = '\n'.join([
    '$ PYTHONDONTWRITEBYTECODE=1 python verify_scope.py',
    f'PASS: {x["report_lines"]} report lines; 307 unique raster pins; 11 packs; 93,370 direction rows; 1,979 canonical captures.',
    f'PASS: {len(x["input_sha256"])} complete input SHA256 and byte counts; report SHA256; all raster pins match v3.',
    'PASS: 8 full pack SHA256 pins; 3 explicitly MISSING; exact affected-scene counts and unions.',
    'This checks scope integrity, not GT regeneration or raw-dataset availability.',
    f'REGEN_SCOPE.md sha256 {hashlib.sha256(md).hexdigest()}',
    f'REGEN_SCOPE.json sha256 {hashlib.sha256(report_path.read_bytes()).hexdigest()}',
])+'\n'
(root/'evidence/VALIDATION.txt').write_text(result)
print(result, end='')
(root/'STATUS.md').write_text(
    'Complete: out/REGEN_SCOPE.md (53 lines) and out/REGEN_SCOPE.json scope the 307 missing rasters and 11 direction packs. '
    'Verification passed the counts, exact affected-scene lists, all 31 input hashes, all raster v3 pins, eight full pack pins and report integrity. '
    'The recommendation is PARTIAL: recover missing generators and raw/frame/instance manifests before regeneration; three pack hashes and unsupported storage/compute estimates remain MISSING. '
    'Only local metadata reads, scoped searches, named-directory checks and workspace writes ran; no regeneration, fetch, network, SSH, Git or GPU use occurred.\n')
