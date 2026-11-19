"""Pin build 21, port the ordered series, and prove exact zero-fuzz replay without Git."""
import ast
import difflib
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = Path('/scratch/jjyeung/orch_n30/so_xstore/in/tree21b')
BASE = PACKAGE/'work/tree_r1'
TREE = ROOT/'work/b21_final/work/tree_r1'
OUT = ROOT/'out/patches_b21'
VERIFY = ROOT/'work/b21_final_replay'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
pins = dict(line.split('  ', 1)[::-1] for line in (PACKAGE/'out/TREE_FILES.sha256').read_text().splitlines())
seal = json.loads((PACKAGE/'out/TREE_SEAL.json').read_text())
digest = hashlib.sha256(json.dumps(pins, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
assert digest == seal['tree_sha256'] == 'b262e7a757d93e2485a523765916507b2bf3305fe3213cffca100007d19f2ce8'
assert len(pins) == 936
TREE.mkdir(parents=True)
OUT.mkdir(exist_ok=True)
VERIFY.mkdir()
for relative, expected in pins.items():
    source = BASE/relative
    assert sha(source) == expected, relative
    target = TREE/relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    shutil.copymode(source, target)
print(f'BASE_PIN_PASS: {len(pins)} files; seal {digest}', flush=True)
manifest = json.loads((ROOT/'out/patches/manifest.json').read_text())
ported = {}
all_paths = set()
for name, item in manifest.items():
    if not name.endswith('.diff'):
        continue
    before = {p:(TREE/p).read_text() if (TREE/p).exists() else '' for p in item['paths']}
    command = ['patch','--batch','--fuzz=0','--no-backup-if-mismatch','-p1','-i',str(ROOT/'out/patches'/name)]
    result = subprocess.run(command, cwd=TREE, capture_output=True, text=True)
    print('PORT '+name+'\n'+result.stdout+result.stderr+'EXIT='+str(result.returncode), flush=True)
    assert result.returncode == 0
    parts = []
    for relative, old in before.items():
        new = (TREE/relative).read_text()
        parts.extend(difflib.unified_diff(old.splitlines(True), new.splitlines(True),
                     fromfile='a/'+relative if old else '/dev/null', tofile='b/'+relative))
        if relative not in all_paths and old:
            path = VERIFY/relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(old)
        all_paths.add(relative)
    payload = ''.join(parts).encode()
    (OUT/name).write_bytes(payload)
    ported[name] = dict(sha256=hashlib.sha256(payload).hexdigest(), bytes=len(payload), paths=item['paths'],
                       base_pin=seal['tree_sha256'])
    replay = subprocess.run(['patch','--batch','--fuzz=0','-p1','-i',str(OUT/name)],
                            cwd=VERIFY, capture_output=True, text=True)
    print('REPLAY '+name+'\n'+replay.stdout+replay.stderr+'EXIT='+str(replay.returncode), flush=True)
    assert replay.returncode == 0 and 'offset' not in replay.stdout and 'fuzz' not in replay.stdout
for relative in all_paths:
    assert (TREE/relative).read_bytes() == (VERIFY/relative).read_bytes(), relative
    ast.parse((TREE/relative).read_text(), filename=relative)
for relative, expected in pins.items():
    if relative not in all_paths:
        assert sha(TREE/relative) == expected, relative
ported['_application'] = dict(method='Apply 01, 02, 03, 04 in order with patch --batch --fuzz=0 -p1; exact-context build-21 diffs.',
    input_root=str(BASE), tested_tree=str(TREE), base_pin=seal,
    package_sha256='fb9de190d0da8ed0727f2132d4c08ac4737a65a7aed3226d6ab4cbe1f65ebf59',
    package_pin_source=str(PACKAGE/'READY'), defaults=manifest['_application']['defaults'],
    input_sha256={p:pins.get(p) for p in sorted(all_paths)},
    output_sha256={p:sha(TREE/p) for p in sorted(all_paths)},
    test_method='See REPORT.md Coordinator command; local runner uses SO_TEST_TREE='+str(TREE))
candidate = dict(pins, **ported['_application']['output_sha256'])
ported['_application']['candidate_source_tree_sha256'] = hashlib.sha256(json.dumps(candidate, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
ported['_application']['candidate_source_files'] = len(candidate)
(OUT/'manifest.json').write_text(json.dumps(ported, indent=2)+'\n')
# The package omits these read-only fixtures. They live outside the sealed source.
fixtures = Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w21/work')
for relative in ('base/tree_b01ce449','build15/inputs','build_n1/inputs'):
    target = TREE.parent/relative
    target.parent.mkdir(parents=True, exist_ok=True)
    assert (fixtures/relative).is_dir(), relative
    target.symlink_to(fixtures/relative, target_is_directory=True)
print(f'PORT_PROOF: 4 patches, {len(all_paths)} touched files; zero fuzz and zero offsets on replay; other base files unchanged', flush=True)
print('FIXTURES: three read-only links beside tree_r1, outside sealed source', flush=True)
