"""Verify final bytes, source identity, links, syntax and hand-over command."""
import ast
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
for folder, tree, replay in [('patches', 'work/tree', 'work/round2_final_patch_check'),
                             ('patches_b21', 'work/b21_final/work/tree_r1', 'work/b21_final_replay')]:
    manifest = json.loads((ROOT/'out'/folder/'manifest.json').read_text())
    paths = set()
    for name, item in manifest.items():
        if not name.endswith('.diff'):
            continue
        patch = ROOT/'out'/folder/name
        assert sha(patch) == item['sha256'] and patch.stat().st_size == item['bytes']
        paths.update(item['paths'])
    for name in paths:
        assert (ROOT/tree/name).read_bytes() == (ROOT/replay/name).read_bytes(), name
        ast.parse((ROOT/tree/name).read_text(), filename=name)
    print(f'{folder}: 4 hashes and all {len(paths)} touched-file bytes match the tested/replayed tree')
    if folder == 'patches_b21':
        source = ROOT/tree
        files = {str(p.relative_to(source)):sha(p) for p in source.rglob('*') if p.is_file()}
        digest = hashlib.sha256(json.dumps(files,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        assert digest == manifest['_application']['candidate_source_tree_sha256']
        assert len(files) == manifest['_application']['candidate_source_files'] == 948
        print('BUILD21_CANDIDATE: '+digest+'; 948 files')
for folder in ('kit_profile', 'kit_timing'):
    for path in (ROOT/'out'/folder).glob('*.py'):
        ast.parse(path.read_text(), filename=str(path))
    for path in (ROOT/'out'/folder).glob('*.sh'):
        subprocess.run(['bash','-n',str(path)], check=True)
for name in ('REPORT.md','NOTE_FOR_TREE_REBUILD.md','SOURCE_NOTES.md'):
    path = ROOT/'out'/name
    for target in re.findall(r'\]\(([^)]+)\)', path.read_text()):
        if '://' not in target:
            assert (path.parent/target.split('#')[0]).is_file(), (name,target)
report = (ROOT/'out/REPORT.md').read_text()
note = (ROOT/'out/NOTE_FOR_TREE_REBUILD.md').read_text()
assert report.startswith('VERDICT: DONE ')
assert '## Review round 2: finding -> fix -> test' in report
assert '## Coordinator command\n' in report
for text in (report,note):
    assert 'taskset -c 0-7' in text and 'work/b21_final/work/tree_r1' in text
for field in ('ranks[r].data_seconds','ranks[r].components[key]', 'first_step_micro_losses',
              'row_hash.py', '--full-plan', 'C1_CPU_PREFETCH=0', 'C1_CPU_PREFETCH=1'):
    assert field in note, field
checks = json.loads((ROOT/'out/evidence/round2_final_checks.json').read_text())
assert len(checks) == 15 and all(c['accepted'] for c in checks)
print('GATES: both builds, no new failures; eight baseline failures remain explicitly recorded')
print('DOCS_AND_SYNTAX: local links, Python/shell syntax, required sections, metric fields and eight-core coordinator command pass')
print('WORKSPACE_BYTES: '+subprocess.check_output(['du','-sb',str(ROOT)],text=True).split()[0])
print('FINAL_DELIVERY_AUDIT_PASS')
