"""Re-pin only the downstream patch; verify deployment paths through the copy."""
import difflib
import hashlib
import json
from pathlib import Path
import sys
import subprocess

ROOT = Path(__file__).resolve().parent
OLD = Path('/scratch/jjyeung/orch_n30/k1_ops3/kc/k1_build/work/kit_k1a')
KIT = ROOT / 'kc/k1_build/work/kit_k1a'
E = ROOT / 'evidence'
FILES = ['work/gt_set.py', 'work/k1_pipeline.py', 'work/k1_cli.py',
         'work/refit/train.py', 'work/k1_report.py']
MANIFEST = Path('/scratch/jjyeung/orch_n30/k1_ops3/work/codex_arkit_timing/K1_MANIFEST.arkit_timing.json')


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def mapped(path):
    p = Path(path)
    return KIT / p.relative_to(OLD) if p.is_relative_to(OLD) else p


def main():
    snapshot = E / 'frozen_inputs_before.json'
    if not snapshot.exists() and (E / 'identity_proof.json').exists():
        prior = json.loads((E / 'identity_proof.json').read_text())
        write(snapshot, dict(manifest_sha256=prior['manifest_sha256'],
                             sets={name: value['sha256'] for name, value in prior['frozen_gt_sets'].items()}))
    pins = json.loads((OLD / 'out/DEPENDENCIES.json').read_text())
    for p, expected in pins.items():
        assert sha(p) == expected, p
    changes = {}
    diff = []
    for name in FILES:
        key = str(OLD / name)
        changes[key] = dict(before=pins.get(key), after=sha(KIT / name))
        pins[key] = changes[key]['after']
        before = (OLD / name).read_text().splitlines(True) if (OLD / name).exists() else []
        diff.extend(difflib.unified_diff(before, (KIT / name).read_text().splitlines(True),
                                         fromfile='a/' + name, tofile='b/' + name))
    write(ROOT / 'DEPENDENCIES.json', pins)
    write(KIT / 'out/DEPENDENCIES.json', pins)
    diff.extend(difflib.unified_diff((OLD / 'out/DEPENDENCIES.json').read_text().splitlines(True),
                                    (KIT / 'out/DEPENDENCIES.json').read_text().splitlines(True),
                                    fromfile='a/out/DEPENDENCIES.json', tofile='b/out/DEPENDENCIES.json'))
    (ROOT / 'gtset.diff').write_text(''.join(diff))
    write(E / 'new_pins.json', changes)
    for p, expected in pins.items():
        assert sha(mapped(p)) == expected, p
    sys.path.insert(0, str(KIT / 'native_kit'))
    import bindings as B
    after = dict(sources=B.source_identity(), producer=sha(KIT / 'work/k1_phases.py'))
    write(E / 'identity_after.json', after)
    before = json.loads((E / 'identity_before.json').read_text())
    assert before == after
    deployed = {str(OLD / Path(p).relative_to(KIT)) if Path(p).is_relative_to(KIT) else p: v
                for p, v in after['sources'].items()}
    assert all(sha(p) == v for p, v in deployed.items())
    original = json.loads(subprocess.check_output([
        sys.executable, '-B', '-c',
        'import sys,json;sys.path.insert(0,' + repr(str(OLD / 'native_kit')) + ');'
        'import bindings as B;print(json.dumps(dict(sources=B.source_identity(),producer=B.sha('
        + repr(str(OLD / 'work/k1_phases.py')) + '))))'
    ], text=True))
    write(E / 'identity_original.json', original)
    assert original == dict(sources=deployed, producer=after['producer'])
    original_files = json.loads((E / 'copied_files.json').read_text())
    for name, expected in original_files.items():
        assert sha(OLD / name) == expected, name
        if name.startswith('native_kit/') or name in ['work/k1_phases.py', 'out/K1_RULES.json', 'out/K1_RULES.sha256']:
            assert sha(KIT / name) == expected, name
    binding = json.loads((ROOT / 'real_phase_copies/BINDING.json').read_text())
    m = json.loads(MANIFEST.read_text())
    assert binding['sources'] == deployed
    assert binding['producer_sha256'] == after['producer']
    assert binding['manifest_sha256'] == B.digest(m)
    sets = {}
    sys.path.insert(0, str(KIT / 'work'))
    import gt_set as G
    for name in ['GT_SET_PRIMARY_296.json', 'GT_SET_SENSITIVITY_300.json']:
        p = ROOT.parent / 'gt_sets' / name
        x = json.loads(p.read_text())
        captures, meta = G.select(m, G.load(p, sensitivity='SENSITIVITY' in name))
        sets[name] = dict(meta, expected_rows=sum(len(c['rows']) for c in captures),
                         train_captures=sum(c['k1_split'] == 'train' for c in captures),
                         heldout_captures=sum(c['k1_split'] == 'heldout' for c in captures))
    assert sets['GT_SET_PRIMARY_296.json']['n'] == sets['GT_SET_PRIMARY_296.json']['pinned'] == 296
    assert sets['GT_SET_SENSITIVITY_300.json']['n'] == 300
    assert sets['GT_SET_SENSITIVITY_300.json']['unpinned'] == 4
    if snapshot.exists():
        assert json.loads(snapshot.read_text()) == dict(manifest_sha256=sha(MANIFEST),
            sets={name: value['sha256'] for name, value in sets.items()})
    write(E / 'identity_proof.json', dict(
        same_location_identity_before_after_equal=True, deployment_source_identity=deployed,
        phase_binding_source_producer_manifest_equal=True, original_kit_unchanged=True,
        protected_files_unchanged=True, verified_deployment_pins=len(pins),
        producer_sha256=after['producer'], manifest_sha256=sha(MANIFEST),
        manifest_digest=B.digest(m), frozen_gt_sets=sets, changed_files=changes))
    print('PASS: identities, original kit, manifest binding, protected files, and', len(pins), 'mapped deployment pins')


if __name__ == '__main__':
    main()
